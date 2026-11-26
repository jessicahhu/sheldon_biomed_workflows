"""Mine a workflow from agent run traces with a strong model, for a weaker model to follow.

The strong model ("miner") reads scored traces from TRAINING papers only: every completed run (single agent
or researcher + checker, any model) with its Results, Methodology and Conclusion, the checker's concerns,
and which outcomes it got right or wrong against the target. It writes a general step-by-step workflow:
what successful runs did that failing runs didn't, and the pitfalls to check for.

Held-out design: the test paper's traces are never shown. Papers 1 and 2 share the same lung cancer GWAS
and exposure SNPs, so they always go in the same fold:
  fold A: --train paper_1 paper_2 --test paper_3
  fold B: --train paper_3         --test paper_1 paper_2

Leak checks on the mined workflow (any hit aborts and nothing is saved as a workflow):
  - every blocked term for the test paper(s), plus the global list in blind_agent/run_agent.py
  - any rsID (rs + digits): the workflow must be general, not SNP-specific

Usage:
  uv run --python 3.12 --with anthropic python workflow_distillation/mine_workflow.py \
      --train paper_1 paper_2 --test paper_3 --out workflow_distillation/workflows/mined_p1p2.md
Writes <out> plus <out stem>_manifest.json (traces used, their scores, model, prompt size) and
<out stem>_prompt.txt (exactly what the miner received).
"""
import argparse, json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "blind_agent"))
sys.path.insert(0, str(ROOT / "multi_agent_reasoning"))
import run_agent as ra  # noqa: E402
from score import score_run  # noqa: E402

MINER_SYSTEM = """You are an expert in statistical genetics and Mendelian randomization (MR), and in \
designing analysis procedures for less capable AI analysts.

You will read traces of AI agents attempting MR analyses on public summary-level data. Each trace shows \
the research question, what the agent did (its methodology and results), what a reviewing agent \
objected to (if there was one), and a SCORE: for each outcome, whether the agent's effect direction and \
statistical significance matched the target answer.

Your job: find the patterns that separate correct runs from incorrect ones, and turn them into a \
step-by-step WORKFLOW that a weaker AI analyst can follow on a NEW MR question with different data \
(different exposures, outcomes and SNPs).

Requirements for the workflow:
- General, not tied to these studies. Do NOT mention any specific SNP (rsID), gene, locus, drug, disease, \
dataset, or any numeric result from these traces. Generic statistical thresholds and formulas are fine.
- Concrete and checkable: for each stage, say exactly what to do, what to check, and what to record. \
Where agents made a specific mistake, give the correct procedure explicitly (e.g. the exact formula) and \
a sanity check that would catch the mistake.
- Prioritise: put the checks that most often decided correct vs incorrect answers first and mark them.
- Be honest about judgement calls: where the traces show two defensible choices that change the answer, \
tell the analyst to run both and report both, rather than pretending one is always right.
- Written for a weaker model: short imperative steps, no long explanations.

Output ONLY the workflow, in markdown, starting with a level-1 heading."""

SECTIONS_KEEP = ("1. Results", "2. Methodology", "3. Conclusion")
MAX_CONCERNS = 8


def condition_of(d):
    if "_baseline_" in d.name:
        return f"single agent ({d.name.split('_baseline_')[0]})"
    r, c = d.name.split("_")[0].split("+")
    return f"researcher {r} + checker {c}"


def trace_text(d, q):
    rep = (d / "report.md").read_text()
    parts = re.split(r"^## ", rep, flags=re.M)
    body = "\n".join("## " + p.strip() for p in parts if p.startswith(SECTIONS_KEEP))
    sc = score_run(d)
    score = "\n".join(f"- {o}: estimate {desc or 'NOT REPORTED'} | direction {'correct' if dd else 'WRONG'}"
                      f" | significance {'correct' if ss else 'WRONG'}" for o, desc, dd, ss in sc)
    concerns = ""
    if (d / "checker_reviews.json").exists():
        rv = [r for r in json.loads((d / "checker_reviews.json").read_text()) if r["verdict"] == "CONCERN"]
        if rv:
            concerns = "\n### Reviewer concerns raised during the run\n" + "\n".join(
                f"- (review {r['n']}) " + re.sub(r"\s+", " ", r["text"].replace("VERDICT: CONCERN", ""))[:500]
                for r in rv[:MAX_CONCERNS])
    return (f"# TRACE: {q['id']} / {condition_of(d)} / {d.name}\n"
            f"**Question:** {q['question']}\n\n**Data given:** {q['data_description']}\n\n"
            f"### Score against the target\n{score}\n\n{body}\n{concerns}\n"), sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", nargs="+", required=True)
    ap.add_argument("--test", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-opus-5.5")
    args = ap.parse_args()
    if set(args.train) & set(args.test) or ({"paper_1", "paper_2"} & set(args.train)
                                            and {"paper_1", "paper_2"} & set(args.test)):
        sys.exit("Train and test overlap (papers 1 and 2 share data, so they must be in the same fold).")

    traces, manifest = [], []
    for qid in args.train:
        q = json.loads((ROOT / "blind_agent/questions" / f"{qid}.json").read_text())
        dirs = sorted((ROOT / "blind_agent/runs" / qid).glob("*_baseline_*")) + \
               sorted((ROOT / "multi_agent_reasoning/runs" / qid).glob("*+*"))
        for d in dirs:
            if not (d / "result.json").exists():
                continue  # failed, stopped or still running
            t, sc = trace_text(d, q)
            traces.append(t)
            manifest.append({"trace": str(d.relative_to(ROOT)), "condition": condition_of(d),
                             "direction_correct": sum(x[2] for x in sc), "significance_correct": sum(x[3] for x in sc),
                             "n_outcomes": len(sc)})
    prompt = (f"Below are {len(traces)} scored traces. Mine them and write the workflow.\n\n"
              + "\n\n---\n\n".join(traces))
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    stem = out.with_suffix("")
    Path(f"{stem}_prompt.txt").write_text(MINER_SYSTEM + "\n\n=====\n\n" + prompt)
    print(f"{len(traces)} traces from {args.train}, prompt {len(prompt):,} chars; calling {args.model}...",
          file=sys.stderr)

    client = ra.make_client(ra.load_env())
    t0 = time.time()
    resp = client.messages.create(model=args.model, max_tokens=16000, system=MINER_SYSTEM,
                                  messages=[{"role": "user", "content": prompt}])
    wf = "".join(b.text for b in resp.content if b.type == "text").strip()

    # Leak checks against the TEST paper(s)
    extra = []
    for qid in args.test:
        extra += json.loads((ROOT / "blind_agent/questions" / f"{qid}.json").read_text()).get("blocked_terms", [])
    hits = ra.leak_check({"mined workflow": wf}, extra + [r"\brs\d{3,}\b"])
    manifest_out = {"model": args.model, "train": args.train, "test": args.test, "n_traces": len(traces),
                    "prompt_chars": len(prompt), "seconds": round(time.time() - t0),
                    "stop_reason": resp.stop_reason, "leak_hits": [h[1] for h in hits], "traces": manifest}
    Path(f"{stem}_manifest.json").write_text(json.dumps(manifest_out, indent=2))
    if hits:
        Path(f"{stem}_REJECTED.md").write_text(wf)
        for label, term, snip in hits:
            print(f"  LEAK [{label}] /{term}/: ...{snip}...", file=sys.stderr)
        sys.exit(f"ABORTED: mined workflow failed the leak check; saved for inspection as {stem}_REJECTED.md")
    out.write_text(wf + "\n")
    print(f"Saved {out} ({len(wf):,} chars, stop_reason={resp.stop_reason})", file=sys.stderr)


if __name__ == "__main__":
    main()
