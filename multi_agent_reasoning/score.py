"""Score result.json files against the targets used in the README scoreboard.

Direction: OR on the same side of 1 as our hand replication. Significance: P<0.05 agrees with the target.
Paper 3 (Wang 2026) is scored against the published IVW results.
Head-and-neck (paper 2): a pooled/meta estimate is scored if the agent gave one; otherwise the separate
set A / set B estimates are scored together (both must be right), as in the README.

Usage: python score.py <run_dir> [<run_dir> ...]     (each run_dir holds a result.json)
"""
import json, sys
from pathlib import Path

# outcome -> (replication OR, significant?)
TARGETS = {
    "paper_1": {"lung_all": (1.43, True), "adeno": (2.75, True), "squam": (0.96, False)},
    "paper_2": {"lung_all": (1.47, True), "adeno": (2.15, True), "squam": (0.92, False), "hnc": (0.90, False)},
    # Wang 2026 Table S2, IVW (published values; see replication/wang2026/paper_card.md)
    "paper_3": {"salicylic": (0.779, True), "opioids": (1.160, True), "antithrombotic": (0.780, True),
                "thyroid": (0.940, True), "statins": (0.950, False), "diabetes": (0.971, False)},
}
DRUG_WORDS = {"salicylic": ("salicyl", "aspirin"), "opioids": ("opioid",), "antithrombotic": ("antithromb",),
              "thyroid": ("thyroid",), "statins": ("hmg", "statin"), "diabetes": ("diabet",)}


def key(name, qid):
    n = name.lower()
    if qid == "paper_3":
        return next((k for k, ws in DRUG_WORDS.items() if any(w in n for w in ws)), None)
    if any(w in n for w in ("head", "neck", "oral", "pharyn", "hnc")):
        if any(w in n for w in ("pool", "meta", "combined")):
            return "hnc"
        if "set a" in n or "set_a" in n:
            return "hnc_a"
        if "set b" in n or "set_b" in n:
            return "hnc_b"
        return "hnc"
    if "adeno" in n:
        return "adeno"
    if "squam" in n:
        return "squam"
    if "lung" in n:
        return "lung_all"
    return None


def score_run(run_dir):
    run_dir = Path(run_dir)
    qid = run_dir.parent.name
    rows = {}
    try:
        res = json.loads((run_dir / "result.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        res = []
    for r in res:
        k = key(str(r.get("outcome", "")), qid)
        if k and k not in rows:  # first estimate per outcome = primary
            rows[k] = r
    if "hnc" not in rows and "hnc_a" in rows and "hnc_b" in rows:
        rows["hnc"] = [rows["hnc_a"], rows["hnc_b"]]
    out = []
    for outcome, (t_or, t_sig) in TARGETS[qid].items():
        r = rows.get(outcome)
        if r is None:
            out.append((outcome, None, False, False))
            continue
        rs = r if isinstance(r, list) else [r]
        d = all((float(x["or"]) > 1) == (t_or > 1) for x in rs)
        s = all((float(x["p"]) < 0.05) == t_sig for x in rs)
        desc = "; ".join(f"{float(x['or']):.2f} ({float(x['ci_low']):.2f}-{float(x['ci_high']):.2f}) "
                         f"P={float(x['p']):.2g}" for x in rs)
        out.append((outcome, desc, d, s))
    return out


if __name__ == "__main__":
    tot_d = tot_s = n = 0
    for rd in sys.argv[1:]:
        print(f"== {rd}")
        for outcome, desc, d, s in score_run(rd):
            n += 1; tot_d += d; tot_s += s
            print(f"  {outcome:9s} {desc or 'MISSING':45s} direction {'✓' if d else '✗'}  sig {'✓' if s else '✗'}")
    print(f"TOTAL direction {tot_d}/{n}, significance {tot_s}/{n}")
