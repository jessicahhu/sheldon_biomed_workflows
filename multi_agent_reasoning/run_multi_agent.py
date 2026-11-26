"""Two-agent MR replication: a RESEARCHER does the analysis and a CHECKER reviews every step.

Same experiment as blind_agent/run_agent.py (same question files, blinded data, macOS sandbox with
no network and no access to /Users, same leak check, same report format). The only change is a second
model that reviews the researcher's work:

  researcher  gets the question + data files (nothing else) and the run_python tool, exactly as in the
              single-agent baseline. Its system prompt adds one paragraph saying a reviewer will comment.
  checker     gets the question + data description (no files, no tools, no internet). After every
              researcher turn it sees that turn's narration, code and output, and replies
              "VERDICT: OK" or "VERDICT: CONCERN" with reasons. Its reply is passed to the researcher with
              the tool results. When the researcher writes its final report, the checker reviews that too;
              on CONCERN the researcher gets up to MAX_REPORT_REVISIONS chances to revise.

The checker keeps its own running conversation, so it remembers earlier steps.

Usage (from the repo root or this folder):
  uv run --python 3.12 --with anthropic python multi_agent_reasoning/run_multi_agent.py blind_agent/questions/paper_1.json
  ... --researcher-model claude-haiku --checker-model claude-haiku     (both default to claude-haiku)

Outputs go to multi_agent_reasoning/runs/<question_id>/<researcher>+<checker>_<timestamp>/:
  report.md, result.json      as in the baseline (result.json is the researcher's final answer)
  transcript.md               researcher turns interleaved with checker reviews
  checker_reviews.json        every checker verdict, for counting how often it objected
  sent_to_agent/              exactly what each agent received
"""
import argparse, json, os, re, shutil, sys, tempfile, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "blind_agent"))
import anthropic  # noqa: E402
import run_agent as ra  # noqa: E402  (reuse sandbox, blinding, leak check, report rendering)

MAX_TURNS = 60
MAX_REPORT_REVISIONS = 2
CHECKER_OUTPUT_CHARS = 8000  # tool output shown to the checker per step (researcher sees up to 20,000)

RESEARCHER_SYSTEM = ra.SYSTEM + """

A second analyst (the reviewer) checks your work. After each of your turns you will receive the \
reviewer's comments together with your tool results. Take each concern seriously: fix it if it is \
right, or explain briefly why you disagree. The reviewer also reads your final report and may ask \
for revisions. Do not simply defer: you are responsible for the analysis being correct.
"""

CHECKER_SYSTEM = """You are a careful biomedical statistician reviewing another analyst's work, step \
by step, as it happens. The analyst is answering a research question from public summary-level data \
files, using Python. You cannot run code or see the files yourself; you see the research question, \
the data description, and for each step the analyst's narration, the code it ran and the output.

For each step, check whether the analysis is valid and makes sense:
- Is the method appropriate for the question and the data, and correctly implemented (formulas, \
weights, standard errors, units, transformations)?
- Are the data being handled correctly (matching records, alignment of alleles or effect directions, \
missing or duplicated records, assumptions about independence)?
- Do the numbers in the output look plausible, and does the analyst's interpretation follow from them?
- Has the analyst skipped a check that this kind of analysis needs?

Rules:
- Base your review only on what you are shown and on general methodological knowledge. Do not rely on \
remembered results from published papers, and never suggest what the answer "should" be.
- Be specific and brief: point to the line or number that is wrong and say how to fix it.
- Do not raise a concern just to have something to say. If the step is sound, say so.

Start every reply with exactly one line, either "VERDICT: OK" or "VERDICT: CONCERN", then at most \
a few short bullet points."""


def call(client, model, system, messages, tools=None):
    kw = dict(model=model, max_tokens=16000, system=system, messages=messages)
    if tools:
        kw["tools"] = tools
    try:
        return client.messages.create(**kw)
    except anthropic.BadRequestError as e:  # same gateway quirk as the baseline runner
        if "must end with a user message" not in str(e) or messages[-1]["role"] != "user":
            raise
        last = messages[-1]["content"]
        if isinstance(last, list):
            last.append({"type": "text", "text": "Continue."})
        return client.messages.create(**kw)


class Checker:
    def __init__(self, client, model, question_prompt):
        self.client, self.model = client, model
        self.messages = []
        self.intro = ("You will review an analysis of the following question.\n\n" + question_prompt
                      + "\n\n---\n\n")
        self.reviews = []

    def review(self, kind, body):
        content = (self.intro if not self.messages else "") + body
        self.messages.append({"role": "user", "content": content})
        resp = call(self.client, self.model, CHECKER_SYSTEM, self.messages)
        text = "".join(b.text for b in resp.content if b.type == "text").strip() or "VERDICT: OK"
        self.messages.append({"role": "assistant", "content": text})
        verdict = "CONCERN" if re.search(r"VERDICT:\s*CONCERN", text, re.I) else "OK"
        self.reviews.append({"n": len(self.reviews) + 1, "kind": kind, "verdict": verdict, "text": text})
        return verdict, text


def format_step(texts, steps):
    parts = []
    if texts:
        parts.append("Analyst's narration:\n" + "\n".join(texts))
    for i, (purpose, code, out) in enumerate(steps, 1):
        if len(out) > CHECKER_OUTPUT_CHARS:
            out = out[:CHECKER_OUTPUT_CHARS] + f"\n[... output truncated for review, {len(out)} chars total]"
        parts.append(f"Script {i} purpose: {purpose}\n```python\n{code}\n```\nOutput:\n```text\n{out}\n```")
    return "\n\n".join(parts)


def render_transcript(log):
    out = []
    for kind, s in log:
        if kind == "text":
            out.append(s)
        elif kind == "purpose":
            out.append(f"\n**Step purpose:** {s}")
        elif kind == "code":
            out.append(f"```python\n{s}\n```")
        elif kind == "output":
            out.append(f"```text\n{s}\n```\n")
        elif kind == "checker":
            out.append("> **Checker:**\n" + "\n".join("> " + l for l in s.splitlines()) + "\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--researcher-model", default="claude-haiku")
    ap.add_argument("--checker-model", default="claude-haiku")
    args = ap.parse_args()

    cfg = ra.load_env()
    qpath = Path(args.question).resolve()
    q = json.loads(qpath.read_text())
    files = ra.prepare_files(q, qpath.parent)
    prompt = f"Research question: {q['question']}\n\nData:\n{q['data_description']}"

    payload = {"researcher system prompt": RESEARCHER_SYSTEM, "checker system prompt": CHECKER_SYSTEM,
               "user prompt": prompt, **{f"file {k}": v for k, v in files.items()}}
    payload.update({f"file name {k}": k for k in files})
    hits = ra.leak_check(payload, q.get("blocked_terms", []))
    if hits:
        print("ABORTED: paper-identifying content would be sent:", file=sys.stderr)
        for label, term, snip in hits:
            print(f"  [{label}] matched /{term}/: ...{snip}...", file=sys.stderr)
        sys.exit(1)

    tag = lambda m: re.sub(r"[^A-Za-z0-9._-]+", "-", m)
    run_dir = HERE / "runs" / q["id"] / (f"{tag(args.researcher_model)}+{tag(args.checker_model)}"
                                         f"_{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}")
    sent = run_dir / "sent_to_agent"
    sent.mkdir(parents=True)
    (sent / "researcher_system_prompt.txt").write_text(RESEARCHER_SYSTEM)
    (sent / "checker_system_prompt.txt").write_text(CHECKER_SYSTEM)
    (sent / "user_prompt.txt").write_text(prompt)

    ra.ensure_venv()
    workdir = Path(tempfile.mkdtemp(prefix="multi_agent_", dir="/private/tmp")).resolve()
    for name, text in files.items():
        (sent / name).write_text(text)
        (workdir / name).write_text(text)
    (workdir / ".sandbox.sb").write_text(ra.sandbox_profile(workdir))

    client = ra.make_client(cfg)
    checker = Checker(client, args.checker_model, prompt)
    messages = [{"role": "user", "content": prompt}]
    log, step, final_text, revisions = [], 0, "", 0
    try:
        for _ in range(MAX_TURNS):
            resp = call(client, args.researcher_model, RESEARCHER_SYSTEM, messages, ra.TOOLS)
            messages.append({"role": "assistant", "content": resp.content})
            texts, steps, results = [], [], []
            for b in resp.content:
                if b.type == "text" and b.text.strip():
                    texts.append(b.text)
                    final_text += "\n" + b.text  # like the baseline: last occurrence of each heading wins
                    log.append(("text", b.text))
                elif b.type == "tool_use":
                    step += 1
                    code, purpose = b.input.get("code", ""), b.input.get("purpose", "")
                    print(f"  step {step}: {purpose}", file=sys.stderr)
                    out = ra.run_python(code, workdir, step)
                    log += [("purpose", purpose), ("code", code), ("output", out)]
                    steps.append((purpose, code, out))
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})

            if resp.stop_reason == "tool_use":
                verdict, review = checker.review("step", format_step(texts, steps))
                print(f"    checker: {verdict}", file=sys.stderr)
                log.append(("checker", review))
                results.append({"type": "text", "text": "Reviewer's comments on this step:\n\n" + review})
                messages.append({"role": "user", "content": results})
                continue

            # Researcher stopped calling tools: treat this turn as its final report.
            report = "\n".join(texts)
            verdict, review = checker.review(
                "final_report", "The analyst has written its FINAL REPORT. Check that every number "
                "matches the computed outputs above, that the conclusions follow, and that earlier "
                "concerns were resolved.\n\n" + report)
            print(f"    checker on final report: {verdict}", file=sys.stderr)
            log.append(("checker", review))
            if verdict == "CONCERN" and revisions < MAX_REPORT_REVISIONS:
                revisions += 1
                messages.append({"role": "user", "content":
                                 "Reviewer's comments on your final report:\n\n" + review +
                                 "\n\nAddress these (run more analysis if needed), then write the complete "
                                 "final report again with all four headings."})
                continue
            break
        else:
            print(f"Warning: stopped after {MAX_TURNS} turns without a final report.", file=sys.stderr)
    except BaseException:
        msg = traceback.format_exc()
        (run_dir / "FAILED.txt").write_text(msg)
        (run_dir / "transcript.md").write_text(render_transcript(log))
        (run_dir / "checker_reviews.json").write_text(json.dumps(checker.reviews, indent=2))
        print(msg, f"\nRUN FAILED - error saved to {run_dir / 'FAILED.txt'}", file=sys.stderr)
        sys.exit(1)
    finally:
        shutil.copytree(workdir, run_dir / "agent_workdir", ignore=shutil.ignore_patterns(".sandbox.sb"))
        shutil.rmtree(workdir, ignore_errors=True)

    condition = f"researcher+checker ({args.checker_model})"
    sections = ra.split_sections(final_text)
    missing = [s for s in ra.SECTIONS if s not in sections]
    if missing:
        print(f"Warning: report is missing sections: {missing}", file=sys.stderr)
    (run_dir / "report.md").write_text(ra.render_report(q, condition, args.researcher_model, sections,
                                                         [e for e in log if e[0] != "checker"], final_text))
    (run_dir / "transcript.md").write_text(render_transcript(log))
    (run_dir / "checker_reviews.json").write_text(json.dumps(checker.reviews, indent=2))
    js = sections.get("Final answer (JSON)", "")
    if "```json" in js:
        (run_dir / "result.json").write_text(js.split("```json", 1)[1].split("```", 1)[0].strip() + "\n")
    n_concern = sum(r["verdict"] == "CONCERN" for r in checker.reviews)
    print(f"Checker raised concerns on {n_concern}/{len(checker.reviews)} reviews; "
          f"{revisions} report revision(s). Saved to {run_dir}")


if __name__ == "__main__":
    main()
