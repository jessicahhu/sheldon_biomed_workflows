"""List every completed run (single agent, workflow, researcher + checker) with its scores, then totals.

Usage: python3 multi_agent_reasoning/list_runs.py
"""
from collections import defaultdict
from pathlib import Path

from score import score_run

ROOT = Path(__file__).resolve().parent.parent
SHORT = {"claude-sonnet-5": "Sonnet", "claude-haiku": "Haiku", "glm-5.3": "GLM", "claude-opus-5.5": "Opus"}
WORKFLOWS = {"baseline": "none", "mr": "expert", "mined": "mined (Opus)"}
ORDER = ["Haiku alone", "Sonnet alone", "GLM alone", "Haiku + Haiku checker", "Haiku + Sonnet checker",
         "Sonnet + Haiku checker", "Sonnet + Sonnet checker", "Haiku + GLM checker", "GLM + Haiku checker"]

rows, pending = [], 0
for d in sorted(ROOT.glob("blind_agent/runs/paper_*/*")) + sorted(ROOT.glob("multi_agent_reasoning/runs/paper_*/*")):
    if not (d / "result.json").exists():
        pending += 1
        continue
    if "+" in d.name:
        r, c = d.name.split("_")[0].split("+")
        setup, wf = f"{SHORT.get(r, r)} + {SHORT.get(c, c)} checker", "none"
    else:
        m, cond = d.name.split("_")[:2]
        setup, wf = f"{SHORT.get(m, m)} alone", WORKFLOWS.get(cond, cond)
    sc = score_run(d)
    rows.append((setup, wf, d.parent.name, sum(x[2] for x in sc), sum(x[3] for x in sc), len(sc)))

rank = lambda s: ORDER.index(s) if s in ORDER else len(ORDER)
rows.sort(key=lambda r: (rank(r[0]), r[1] != "none", r[1], r[2]))
print("| # | Agents | Workflow | Paper | Direction | Significance |\n|---|---|---|---|---|---|")
for i, (s, w, p, dd, ss, n) in enumerate(rows, 1):
    print(f"| {i} | {s} | {w} | {p.replace('paper_', 'P')} | {dd}/{n} | {ss}/{n} |")

agg = defaultdict(lambda: [0, 0, 0, 0, set()])
for s, w, p, dd, ss, n in rows:
    a = agg[(s, w)]; a[0] += dd; a[1] += ss; a[2] += n; a[3] += 1; a[4].add(p.replace("paper_", ""))
print("\n| Agents | Workflow | Runs | Papers | Direction | Significance |\n|---|---|---|---|---|---|")
for (s, w), (dd, ss, n, runs, ps) in sorted(agg.items(), key=lambda kv: (rank(kv[0][0]), kv[0][1] != "none", kv[0][1])):
    print(f"| {s} | {w} | {runs} | {', '.join(sorted(ps))} | {dd}/{n} ({dd/n:.0%}) | {ss}/{n} ({ss/n:.0%}) |")
print(f"\n{len(rows)} completed runs; {pending} without a result.json (in progress, failed or stopped).")
