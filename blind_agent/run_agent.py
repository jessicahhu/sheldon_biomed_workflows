"""Run an LLM agent on one research question, blind to the source paper (via a LiteLLM gateway).

The agent gets ONLY: the research question, a neutral data description, and the public data
files (renamed, with paper-identifying columns removed). It analyses them with a `run_python`
tool. That code runs on this Mac inside a macOS sandbox (sandbox-exec) that:
  - can read/write only its own scratch folder (a copy of the data files),
  - cannot read anything under /Users (so not paper_card.md, results/, this repo, your home),
  - has no network access, so it can't look the paper up.
The model gets no web tools either.

Before anything is sent, every byte (prompts, file names, file contents) is scanned for
paper-identifying terms (authors, journal, DOI/PMC IDs, GWAS Catalog accessions, consortium
names, published effect sizes). Any hit aborts the run.

Setup: put these in blind_agent/.env
  ANTHROPIC_API_KEY=<your LiteLLM key>
  LITELLM_BASE_URL=<gateway URL, e.g. https://your-gateway.example.edu>
  MODEL=<model name on the gateway>          (see: python run_agent.py --list-models)

Usage:
  python run_agent.py --list-models
  python run_agent.py questions/paper_1.json
  python run_agent.py questions/paper_1.json --workflow workflows/mr.md
  python run_agent.py questions/paper_1.json --model <other gateway model>

Outputs go to runs/<question_id>/<model>_<condition>_<timestamp>/:
  report.md       1. Results  2. Methodology (step by step)  3. Conclusion  4. Code actually run
  transcript.md   full record: the agent's narration, every script, and every output it saw
  result.json     the final structured answer, for scoring
  sent_to_agent/  exactly what the agent received (prompts + data files)
  agent_workdir/  the agent's scratch folder at the end (its scripts and any files it wrote)
"""
import argparse, csv, io, json, os, re, shutil, subprocess, sys, tempfile, time, traceback
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
VENV = HERE / ".sandbox_venv"
MAX_TURNS = 40
TOOL_TIMEOUT_S = 180

TOOLS = [{
    "name": "run_python",
    "description": (
        "Run a Python 3 script in your working directory, which contains the data files. "
        "numpy, pandas, scipy and statsmodels are installed. No internet access. Files you write "
        "persist between calls. Returns stdout and stderr (truncated to 20,000 characters). "
        "Print everything you want to see."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Complete Python script to run."},
            "purpose": {"type": "string", "description": "One sentence: what this step does and why."},
        },
        "required": ["code", "purpose"],
    },
}]

# Anything matching these must never reach the agent. Questions can add more via "blocked_terms".
BLOCKED_TERMS = [
    r"zhang", r"kachuri", r"doherty", r"burgess", r"pierce", r"saarela", r"bojesen", r"mckay",
    r"hum\s*mol\s*genet", r"int\s*j\s*epidemiol", r"ddv252", r"dyy140", r"PMC\d+", r"\bdoi\b",
    r"GCST\d+", r"GAME-?ON", r"TRICL", r"ILCCO", r"OncoArray", r"paper_card", r"used_in",
    r"\b2\.87\b", r"\b2\.78\b", r"\b1\.65\b", r"\b1\.83\b", r"\b1\.92\b", r"\b1\.41\b", r"\b1\.39\b",
]

SYSTEM = """You are a careful biomedical data analyst. You will be given a research question and \
public summary-level data files, which are in your working directory. Answer the question from \
the data alone: use the run_python tool to inspect the files and run every analysis yourself.

Rules:
- Do not rely on remembered results from published papers. If you recognise the study the data \
comes from, say so in your report, but base every number you report on your own computation.
- Before each analysis step, say in one or two sentences what you are about to do and why.
- When you make a judgement call (dropping a SNP, aligning alleles, choosing a method), state the \
choice and the reason.

When finished, write a final report using EXACTLY these four headings, in this order:

## Results
A markdown table of every effect estimate you computed (columns: outcome, method, estimate, \
95% CI, p-value, number of instruments), followed by one sentence per outcome giving the headline.

## Methodology
Numbered steps, in the order you did them. For each step: what you did, which file(s) and \
method you used, what checks you ran, what you found, and any decision you made and why.

## Conclusion
A direct answer to the research question, naming which numbered step(s) each claim rests on, \
plus limitations and caveats.

## Final answer (JSON)
A fenced ```json block containing a list with one object per outcome, keys: outcome, \
primary_method, or, ci_low, ci_high, p, n_instruments, direction ("increased risk" | \
"decreased risk" | "null").
"""

SECTIONS = ["Results", "Methodology", "Conclusion", "Final answer (JSON)"]


# ---------------------------------------------------------------- config
def load_env():
    """Read blind_agent/.env (KEY=value lines). Values there override the environment."""
    cfg = {k: os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "LITELLM_BASE_URL", "MODEL")}
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip("'\"")
    return cfg


def make_client(cfg):
    if not cfg.get("ANTHROPIC_API_KEY") or not cfg.get("LITELLM_BASE_URL"):
        sys.exit("Set ANTHROPIC_API_KEY and LITELLM_BASE_URL in blind_agent/.env")
    key = cfg["ANTHROPIC_API_KEY"]
    # LiteLLM accepts the key as a Bearer token; send it both ways to be safe.
    return anthropic.Anthropic(api_key=key, base_url=cfg["LITELLM_BASE_URL"].rstrip("/"),
                               default_headers={"Authorization": f"Bearer {key}"})


def list_models(cfg):
    import urllib.request
    req = urllib.request.Request(cfg["LITELLM_BASE_URL"].rstrip("/") + "/v1/models",
                                 headers={"Authorization": f"Bearer {cfg['ANTHROPIC_API_KEY']}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        for m in json.load(r).get("data", []):
            print(m.get("id"))


# ---------------------------------------------------------------- data + blinding
def prepare_files(q, qdir):
    """Load each data file under its neutral name, keeping only the allowed columns."""
    out = {}
    for name, spec in q["files"].items():
        text = (qdir / spec["from"]).resolve().read_text()
        keep = spec.get("keep_columns")
        if keep:
            rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=keep, delimiter="\t", extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
            text = buf.getvalue()
        out[name] = text
    return out


def leak_check(payload, extra_terms):
    """payload: {label: text}. Returns a list of (label, term, snippet) for every blocked hit."""
    hits = []
    for label, text in payload.items():
        for term in BLOCKED_TERMS + extra_terms:
            for m in re.finditer(term, text, flags=re.IGNORECASE):
                s = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
                hits.append((label, term, s))
    return hits


# ---------------------------------------------------------------- sandbox
def ensure_venv():
    if not (VENV / "bin" / "python").exists():
        print("Creating sandbox Python environment (one time)...", file=sys.stderr)
        subprocess.run(["uv", "venv", "-q", "--python", "3.12", str(VENV)], check=True)
        subprocess.run(["uv", "pip", "install", "-q", "--python", str(VENV / "bin" / "python"),
                        "numpy", "pandas", "scipy", "statsmodels"], check=True)


def sandbox_profile(workdir):
    venv = VENV.resolve()
    return f"""(version 1)
(allow default)
(deny network*)
(deny file-read-data file-write* (subpath "/Users"))
(allow file-read-data (subpath "{venv}") (subpath "{Path.home()}/.local/share/uv/python"))
(deny file-write* (subpath "/private/tmp") (subpath "/tmp") (subpath "/private/var/folders"))
(allow file-read-data file-write* (subpath "{workdir}"))
"""


def run_python(code, workdir, step):
    script = workdir / f"step_{step:02d}.py"
    script.write_text(code)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(workdir), "TMPDIR": str(workdir),
           "MPLCONFIGDIR": str(workdir), "LANG": "en_US.UTF-8"}  # no API key in the agent's env
    try:
        p = subprocess.run(["sandbox-exec", "-f", str(workdir / ".sandbox.sb"),
                            str(VENV / "bin" / "python"), "-I", script.name],
                           cwd=workdir, env=env, capture_output=True, text=True, timeout=TOOL_TIMEOUT_S)
        out = p.stdout + (f"\n[stderr]\n{p.stderr}" if p.stderr.strip() else "")
        if p.returncode:
            out += f"\n[exit code {p.returncode}]"
    except subprocess.TimeoutExpired:
        out = f"[timed out after {TOOL_TIMEOUT_S}s]"
    return out[:20000] or "[no output]"


# ---------------------------------------------------------------- report rendering
def split_sections(text):
    """Return {heading: body} for the LAST occurrence of each '## <heading>' in text."""
    found = {}
    parts = re.split(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    for i in range(1, len(parts) - 1, 2):
        head = parts[i].strip()
        for want in SECTIONS:
            if head.lower().startswith(want.lower().split(" (")[0]):
                found[want] = parts[i + 1].strip()
    return found


def render_transcript(log):
    out = []
    for kind, s in log:
        if kind == "text":
            out.append(s)
        elif kind == "purpose":
            out.append(f"\n**Step purpose:** {s}")
        elif kind == "code":
            out.append(f"```python\n{s}\n```")
        else:
            out.append(f"```text\n{s}\n```\n")
    return "\n".join(out)


def render_report(q, condition, model, sections, log, final_text):
    lines = [f"# {q['id']} ({model}, {condition})", "", f"**Research question:** {q['question']}", ""]
    for n, name in enumerate(["Results", "Methodology", "Conclusion"], 1):
        body = sections.get(name)
        lines += [f"## {n}. {name}", "", body or "_The agent did not write this section. See transcript.md._", ""]
    lines += ["## 4. Code actually run", "",
              "Every script the agent executed, in order. Full outputs are in transcript.md.", ""]
    step, purpose = 0, ""
    for kind, s in log:
        if kind == "purpose":
            purpose = s
        elif kind == "code":
            step += 1
            lines += [f"**Script {step}:** {purpose}", f"```python\n{s}\n```", ""]
    if not sections:
        lines += ["## Raw agent output (report headings not found)", "", final_text]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--workflow", help="markdown procedure appended to the system prompt")
    ap.add_argument("--model", help="model name on the gateway (default: MODEL in .env)")
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    cfg = load_env()
    if args.list_models:
        return list_models(cfg)
    if not args.question:
        ap.error("question file required")
    model = args.model or cfg.get("MODEL")
    if not model:
        sys.exit("Set MODEL in blind_agent/.env or pass --model (see --list-models)")

    qpath = Path(args.question).resolve()
    q = json.loads(qpath.read_text())

    system = SYSTEM
    condition = "baseline"
    if args.workflow:
        system += "\n\nFollow this analysis workflow step by step:\n\n" + Path(args.workflow).read_text()
        condition = Path(args.workflow).stem

    files = prepare_files(q, qpath.parent)
    prompt = f"Research question: {q['question']}\n\nData:\n{q['data_description']}"

    # --- Blinding check: nothing paper-identifying may be sent ---
    payload = {"system prompt": system, "user prompt": prompt, **{f"file {k}": v for k, v in files.items()}}
    payload.update({f"file name {k}": k for k in files})
    hits = leak_check(payload, q.get("blocked_terms", []))
    if hits:
        print("ABORTED: paper-identifying content would be sent to the agent:", file=sys.stderr)
        for label, term, snip in hits:
            print(f"  [{label}] matched /{term}/: ...{snip}...", file=sys.stderr)
        sys.exit(1)

    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "-", model)
    run_dir = HERE / "runs" / q["id"] / f"{safe_model}_{condition}_{time.strftime('%Y%m%d-%H%M%S')}"
    sent = run_dir / "sent_to_agent"
    sent.mkdir(parents=True)
    (sent / "system_prompt.txt").write_text(system)
    (sent / "user_prompt.txt").write_text(prompt)

    # Agent's scratch folder: outside /Users, contains only the data files
    ensure_venv()
    workdir = Path(tempfile.mkdtemp(prefix="blind_agent_", dir="/private/tmp")).resolve()
    for name, text in files.items():
        (sent / name).write_text(text)
        (workdir / name).write_text(text)
    (workdir / ".sandbox.sb").write_text(sandbox_profile(workdir))

    client = make_client(cfg)
    messages = [{"role": "user", "content": prompt}]
    log, step, final_text = [], 0, ""
    try:
        for _ in range(MAX_TURNS):
            resp = client.messages.create(model=model, max_tokens=16000, system=system,
                                          messages=messages, tools=TOOLS)
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for b in resp.content:
                if b.type == "text" and b.text.strip():
                    log.append(("text", b.text))
                    final_text += "\n" + b.text
                elif b.type == "tool_use":
                    step += 1
                    code, purpose = b.input.get("code", ""), b.input.get("purpose", "")
                    print(f"  step {step}: {purpose}", file=sys.stderr)
                    out = run_python(code, workdir, step)
                    log += [("purpose", purpose), ("code", code), ("output", out)]
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
            if resp.stop_reason == "tool_use":
                messages.append({"role": "user", "content": results})
                continue
            if resp.stop_reason == "max_tokens":
                print("Warning: hit max_tokens; report may be truncated.", file=sys.stderr)
            break
        else:
            print(f"Warning: stopped after {MAX_TURNS} turns without a final report.", file=sys.stderr)
    except BaseException:
        msg = traceback.format_exc()
        if isinstance(sys.exc_info()[1], anthropic.AuthenticationError):
            k = cfg.get("ANTHROPIC_API_KEY") or ""
            msg += f"\nKey: {len(k)} chars, starts '{k[:3]}'. Gateway: {cfg.get('LITELLM_BASE_URL')}\n"
        (run_dir / "FAILED.txt").write_text(msg)
        (run_dir / "transcript.md").write_text(render_transcript(log))
        print(msg, f"\nRUN FAILED - error saved to {run_dir / 'FAILED.txt'}", file=sys.stderr)
        sys.exit(1)
    finally:
        shutil.copytree(workdir, run_dir / "agent_workdir", ignore=shutil.ignore_patterns(".sandbox.sb"))
        shutil.rmtree(workdir, ignore_errors=True)

    sections = split_sections(final_text)
    missing = [s for s in SECTIONS if s not in sections]
    if missing:
        print(f"Warning: agent report is missing sections: {missing}", file=sys.stderr)
    (run_dir / "report.md").write_text(render_report(q, condition, model, sections, log, final_text))
    (run_dir / "transcript.md").write_text(render_transcript(log))
    js = sections.get("Final answer (JSON)", "")
    if "```json" in js:
        (run_dir / "result.json").write_text(js.split("```json", 1)[1].split("```", 1)[0].strip() + "\n")
    print(f"Saved to {run_dir}")


if __name__ == "__main__":
    main()
