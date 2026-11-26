"""Researcher x checker matrix: score every completed run, grouped by condition and paper.

Conditions: single agent (blind_agent/runs, *_baseline_*) and each researcher+checker pair
(multi_agent_reasoning/runs, <researcher>+<checker>_*). Runs without a result.json (failed or stopped)
are skipped and counted.

Usage: python3 multi_agent_reasoning/matrix.py
"""
import json, re
from collections import defaultdict
from pathlib import Path

from score import score_run

ROOT = Path(__file__).resolve().parent.parent
SHORT = {"claude-sonnet-5": "Sonnet", "claude-haiku": "Haiku", "glm-5.3": "GLM"}

cells = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))  # cond -> paper -> [dir, sig, n, runs]
skipped, concerns = defaultdict(int), defaultdict(lambda: [0, 0])
for d in sorted((ROOT / "blind_agent/runs").glob("paper_*/*_baseline_*")) + \
         sorted((ROOT / "multi_agent_reasoning/runs").glob("paper_*/*+*")):
    if d.parent.parent.name == "runs" and "_baseline_" in d.name:
        cond = SHORT.get(d.name.split("_baseline_")[0], d.name) + " alone"
    else:
        r, c = d.name.split("_")[0].split("+")
        cond = f"{SHORT.get(r, r)} + {SHORT.get(c, c)} checker"
    paper = d.parent.name
    if not (d / "result.json").exists():
        skipped[cond] += 1
        continue
    res = score_run(d)
    cell = cells[cond][paper]
    cell[0] += sum(x[2] for x in res); cell[1] += sum(x[3] for x in res); cell[2] += len(res); cell[3] += 1
    if (d / "checker_reviews.json").exists():
        rv = json.loads((d / "checker_reviews.json").read_text())
        concerns[cond][0] += sum(x["verdict"] == "CONCERN" for x in rv); concerns[cond][1] += len(rv)

papers = ["paper_1", "paper_2", "paper_3"]
order = ["Haiku alone", "Sonnet alone", "Haiku + Haiku checker", "Haiku + Sonnet checker",
         "Sonnet + Haiku checker", "Sonnet + Sonnet checker",
         "GLM alone", "Haiku + GLM checker", "GLM + Haiku checker"]
print("| Condition | " + " | ".join(f"{p} dir / sig (runs)" for p in papers) + " | Total dir | Total sig | Concerns |")
print("|---" * (len(papers) + 4) + "|")
for cond in order + [c for c in cells if c not in order]:
    if cond not in cells:
        continue
    row, D, S, N = [], 0, 0, 0
    for p in papers:
        dd, ss, nn, rr = cells[cond].get(p, [0, 0, 0, 0])
        row.append(f"{dd}/{nn} / {ss}/{nn} ({rr})" if nn else "–")
        D, S, N = D + dd, S + ss, N + nn
    cc = concerns.get(cond)
    print(f"| {cond} | " + " | ".join(row) + f" | {D}/{N} ({D/N:.0%}) | {S}/{N} ({S/N:.0%}) | "
          + (f"{cc[0]}/{cc[1]} ({cc[0]/cc[1]:.0%})" if cc and cc[1] else "–") + " |")
if skipped:
    print("\nSkipped (no result.json): " + ", ".join(f"{k}: {v}" for k, v in skipped.items()))
