"""Score a blind-agent result.json for paper_3 (forward) or paper_3b (reverse) against our replication and the paper.
Direction = estimate above/below 1; significance = p < 0.05. Agent outcome labels are mapped by keyword.
Usage: python3 -I score_agent.py <jiang2024 dir> <run dir> [<run dir> ...]
"""
import json, os, re, sys
import numpy as np, pandas as pd

ROOT = os.path.abspath(sys.argv[1])
PUB_F = {"lymphoid_haem_all": (1.651, 2.69e-8), "aml": (1.488, 0.384), "cml": (1.583, 0.322), "all": (2.690, 0.041),
         "cll": (2.155, 0.005), "leuk_unspec": (2.779, 0.021), "myeloma": (1.845, 0.024), "nhl": (1.737, 0.009),
         "hodgkin": (1.697, 0.014), "follicular": (1.358, 0.151), "nonfollicular": (1.583, 1.98e-4), "dlbcl": (1.599, 0.017),
         "waldenstrom": (8.940, 0.002), "mantle": (2.874, 0.017), "marginal_zone": (0.809, 0.653), "t_nk": (0.517, 0.057),
         "nhl_other": (1.603, 0.013)}
PUB_R = {"lymphoid_haem_all": (0.998, 0.725), "aml": (1.000, 0.943), "cml": (1.004, 0.241), "all": (1.000, 0.995),
         "cll": (1.000, 0.782), "leuk_unspec": (1.000, 0.857), "myeloma": (0.999, 0.674), "nhl": (1.002, 0.526),
         "hodgkin": (1.003, 0.171), "follicular": (1.000, 0.929), "nonfollicular": (1.000, 0.977), "dlbcl": (0.999, 0.788),
         "waldenstrom": (np.nan, np.nan), "mantle": (0.999, 0.586), "marginal_zone": (0.996, 0.092), "t_nk": (1.000, 0.990),
         "nhl_other": (0.997, 0.264)}
RULES = [  # order matters: most specific first
    ("nonfollicular", r"non.?follicular"), ("follicular", r"follicular"), ("dlbcl", r"diffuse|dlbcl"),
    ("waldenstrom", r"lymphoplasm|waldenstr"), ("mantle", r"mantle"), ("marginal_zone", r"marginal"),
    ("t_nk", r"t/nk|t.nk|nk.cell"), ("nhl_other", r"other|unspecified.*(non.?hodgkin|nhl)"),
    ("leuk_unspec", r"unspecified"), ("lymphoid_haem_all", r"any|haematopoietic|hematopoietic"),
    ("aml", r"acute myeloid|\baml\b"), ("cml", r"chronic myeloid|\bcml\b"), ("all", r"acute lympho|^all\b"),
    ("cll", r"chronic lympho|\bcll\b"), ("myeloma", r"myeloma"), ("hodgkin", r"^(?!.*non).*hodgkin"),
    ("nhl", r"non.?hodgkin|\bnhl\b"),
]


def key(label):
    s = label.lower().replace("_", " ")
    for k, pat in RULES:
        if re.search(pat, s):
            return k
    return None


rep = pd.read_csv(f"{ROOT}/results/mr_results.tsv", sep="\t")
for run in sys.argv[2:]:
    run = os.path.abspath(run)
    q = "paper_3b" if "paper_3b" in run else "paper_3"
    direction = "reverse" if q == "paper_3b" else "forward"
    pub = PUB_R if q == "paper_3b" else PUB_F
    r = rep[rep.direction == direction].set_index("outcome")
    res = json.load(open(f"{run}/result.json"))
    print(f"\n### {q} — {os.path.basename(run)}\n")
    print("| Outcome | Agent | n IV | Replication | Paper | Dir vs rep | Sig vs rep | Dir vs paper | Sig vs paper |")
    print("|---|---|---|---|---|---|---|---|---|")
    tot = {"dr": [0, 0], "sr": [0, 0], "dp": [0, 0], "sp": [0, 0]}
    seen = set()
    for a in res:
        k = key(a["outcome"]); seen.add(k)
        o, p = a.get("or"), a.get("p")
        if k is None or o is None or p is None:
            print(f"| {a['outcome']} | not estimated | {a.get('n_instruments')} | | | | | | |"); continue
        ro = np.exp(r.loc[k, "ivw_b"]) if k in r.index and pd.notna(r.loc[k].get("ivw_b")) else np.nan
        rp = r.loc[k, "ivw_p"] if pd.notna(ro) else np.nan
        po, pp = pub[k]
        marks = []
        for (ref_o, ref_p), dk, sk in (((ro, rp), "dr", "sr"), ((po, pp), "dp", "sp")):
            if np.isnan(ref_o):
                marks += ["–", "–"]; continue
            s = (p < 0.05) == (ref_p < 0.05)
            tot[sk][0] += s; tot[sk][1] += 1
            if q == "paper_3b":  # all effects ~1.00: direction is noise, score significance only
                marks += ["–", "✓" if s else "✗"]; continue
            d = (o > 1) == (ref_o > 1)
            tot[dk][0] += d; tot[dk][1] += 1
            marks += ["✓" if d else "✗", "✓" if s else "✗"]
        fmt = lambda x, y: "–" if np.isnan(x) else f"{x:.3f} (p={y:.2g})"
        print(f"| {k} | {o:.3f} ({a.get('ci_low', float('nan')):.3f}–{a.get('ci_high', float('nan')):.3f}), p={p:.2g} | "
              f"{a.get('n_instruments')} | {fmt(ro, rp)} | {fmt(po, pp)} | " + " | ".join(marks) + " |")
    missing = set(pub) - seen
    if missing:
        print(f"\nNot reported by agent: {', '.join(sorted(missing))}")
    if q == "paper_3b":
        print("\n**Score (significance only):** vs replication {}/{}, vs paper {}/{}".format(*tot["sr"], *tot["sp"]))
    else:
        print("\n**Score vs replication:** direction {}/{}, significance {}/{}.  **vs paper:** direction {}/{}, significance {}/{}".format(
            *tot["dr"], *tot["sr"], *tot["dp"], *tot["sp"]))
