"""Two-sample MR replication of Zhang et al. 2015 (Hum Mol Genet 24:5356), TL -> lung cancer.

Exposure: Zhang Table 2 (kb TL per long allele; SE back-derived from the reported P).
Outcome:  McKay et al. 2017 ILCCO/OncoArray lung GWAS (GWAS Catalog GCST004748/4744/4750).
Effect scale: OR per 1000 bp (1 kb) longer leukocyte TL, matching Zhang.

Each workflow stage prints what it decided, so the log doubles as the audit trail.
Usage: python3 -I mr.py <exposure.tsv> <raw_outcome_dir> <results_dir>
"""
import sys, glob, os, json
import numpy as np, pandas as pd
from scipy import stats

exp_path, raw_dir, res_dir = sys.argv[1:4]
COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}
rng = np.random.default_rng(2015)

# Published targets (Zhang 2015 Table 3, IVW; text gives adeno as 2.78 (2.16-3.58) - internal inconsistency)
TARGETS = {
    "lung_all":   {"or": 1.65, "lo": 1.39, "hi": 1.96, "p": 1.3e-8},
    "lung_adeno": {"or": 2.87, "lo": 2.20, "hi": 3.74, "p": 6.3e-15},
    "lung_squam": {"or": 1.04, "lo": 0.79, "hi": 1.36, "p": 0.79},
    "lung_adeno_noTERT": {"or": 2.00, "lo": 1.48, "hi": 2.70, "p": 6.6e-6},
}


def ivw(bx, by, sy, random=False):
    """First-order IVW (Burgess 2013), the formula in Zhang Methods. Optional multiplicative RE."""
    w = bx**2 / sy**2
    b = np.sum(bx * by / sy**2) / np.sum(bx**2 / sy**2)
    se = 1 / np.sqrt(np.sum(w))
    ratio = by / bx
    q = np.sum(w * (ratio - b) ** 2)
    df = len(bx) - 1
    if random and df > 0:
        se *= np.sqrt(max(1.0, q / df))
    p = 2 * stats.norm.sf(abs(b / se))
    return b, se, p, q, df


def egger(bx, by, sy):
    s = np.sign(bx); bx, by = np.abs(bx), by * s          # orient to positive exposure effect
    X = np.column_stack([np.ones_like(bx), bx]); W = np.diag(1 / sy**2)
    XtWX = X.T @ W @ X; coef = np.linalg.solve(XtWX, X.T @ W @ by)
    resid = by - X @ coef; df = len(bx) - 2
    sigma2 = max(1.0, (resid**2 / sy**2).sum() / df)
    se = np.sqrt(np.diag(np.linalg.inv(XtWX)) * sigma2)
    p = 2 * stats.t.sf(np.abs(coef / se), df)
    return {"intercept": coef[0], "int_se": se[0], "int_p": p[0], "slope": coef[1], "slope_se": se[1], "slope_p": p[1]}


def wmedian_point(ratio, w):
    o = np.argsort(ratio); r, w = ratio[o], w[o] / w.sum()
    cum = np.cumsum(w) - 0.5 * w
    i = np.searchsorted(cum, 0.5)
    if i == 0:
        return r[0]
    if i == len(r):
        return r[-1]
    return r[i - 1] + (r[i] - r[i - 1]) * (0.5 - cum[i - 1]) / (cum[i] - cum[i - 1])


def weighted_median(bx, by, sy, nboot=2000):
    ratio = by / bx; ratio_se = sy / np.abs(bx); w = 1 / ratio_se**2
    est = wmedian_point(ratio, w)
    boots = [wmedian_point(rng.normal(by, sy) / bx, w) for _ in range(nboot)]
    se = np.std(boots, ddof=1)
    return est, se, 2 * stats.norm.sf(abs(est / se))


def fmt(b, se, p):
    return f"OR {np.exp(b):.2f} ({np.exp(b-1.96*se):.2f}-{np.exp(b+1.96*se):.2f}), P={p:.2g}"


# ---- Stage 3/4: instruments + strength ----
ex = pd.read_csv(exp_path, sep="\t")
ex["z"] = stats.norm.isf(ex.p / 2)
ex["se_kb"] = ex.beta_kb / ex.z
ex["F_approx"] = ex.z**2  # F ~ z^2 per SNP
print("== Instruments (Zhang Table 2; SE back-derived from P) ==")
print(ex[["snp", "locus", "long_allele", "beta_kb", "se_kb", "F_approx", "used_in_zhang"]].round(4).to_string(index=False))
ex = ex[ex.used_in_zhang == "yes"].copy()
print(f"Kept {len(ex)} SNPs (Zhang excluded rs7726159, rs412658 for LD). Min F ~ {ex.F_approx.min():.0f} -> no weak instruments.\n")

all_rows, log = [], {}
for f in sorted(glob.glob(os.path.join(raw_dir, "*.tsv"))):
    outcome = os.path.basename(f).rsplit("_GCST", 1)[0]
    oc = pd.read_csv(f, sep="\t").rename(columns={"variant_id": "snp"})
    d = ex.merge(oc, on="snp", how="left")
    print(f"==================== {outcome} ({os.path.basename(f)}) ====================")

    # ---- Stage 5: extraction ----
    missing = d[d.beta.isna()].snp.tolist()
    print(f"[extract] {len(d) - len(missing)}/{len(d)} SNPs found; missing: {missing or 'none'} (proxies needed if any)")
    d = d.dropna(subset=["beta"]).copy()

    # ---- Stage 6: harmonise to the long-TL allele ----
    notes = []
    for i, r in d.iterrows():
        ea, oa, la = r.effect_allele.upper(), r.other_allele.upper(), r.long_allele.upper()
        pal = COMP.get(ea) == oa
        if la == ea:
            sign = 1
        elif la == oa:
            sign = -1
        elif la in (COMP.get(ea), COMP.get(oa)):
            sign = 1 if COMP[la] == ea else -1; notes.append(f"{r.snp}: strand flip")
        else:
            sign = np.nan; notes.append(f"{r.snp}: allele mismatch, dropped")
        d.loc[i, "by"] = sign * r.beta
        d.loc[i, "palindromic"] = pal
        d.loc[i, "eaf_long"] = r.effect_allele_frequency if sign == 1 else 1 - r.effect_allele_frequency
        if pal:
            notes.append(f"{r.snp}: PALINDROMIC {ea}/{oa}; long allele {la} has outcome freq "
                         f"{d.loc[i,'eaf_long']:.2f} - strand cannot be confirmed without exposure-study allele freq")
    d = d.dropna(subset=["by"])
    for n in notes:
        print("[harmonise]", n)

    bx, by, sy = d.beta_kb.values, d.by.values, d.standard_error.values
    d["ratio_or"] = np.exp(by / bx)
    print("[per-SNP] Wald ratio OR per kb:")
    print(d[["snp", "locus", "by", "standard_error", "p_value", "ratio_or"]].round(4).to_string(index=False))

    # ---- Stage 7: primary estimate ----
    b, se, p, q, df = ivw(bx, by, sy)
    br, ser, pr, _, _ = ivw(bx, by, sy, random=True)
    qp = stats.chi2.sf(q, df)
    print(f"[IVW fixed  ] {fmt(b, se, p)}   <- Zhang's primary method")
    print(f"[IVW mult-RE] {fmt(br, ser, pr)}")
    print(f"[Cochran Q  ] Q={q:.1f}, df={df}, P={qp:.2g}")

    # ---- Stage 8: sensitivity ----
    eg = egger(bx, by, sy)
    wm = weighted_median(bx, by, sy)
    print(f"[MR-Egger   ] {fmt(eg['slope'], eg['slope_se'], eg['slope_p'])}; intercept {eg['intercept']:.4f} (P={eg['int_p']:.2g})")
    print(f"[W. median  ] {fmt(*wm)}")
    print("[leave-one-out IVW]")
    loo = {}
    for k in range(len(d)):
        m = np.arange(len(d)) != k
        bb, ss, pp, _, _ = ivw(bx[m], by[m], sy[m])
        loo[d.snp.iloc[k]] = (bb, ss, pp)
        print(f"   drop {d.snp.iloc[k]:<11} ({d.locus.iloc[k]:<6}) {fmt(bb, ss, pp)}")
    pal_mask = ~d.palindromic.values.astype(bool)
    bnp, senp, pnp, _, _ = ivw(bx[pal_mask], by[pal_mask], sy[pal_mask])
    print(f"[no palindromic] {fmt(bnp, senp, pnp)}")

    rows = [(outcome, "IVW_fixed", b, se, p), (outcome, "IVW_multRE", br, ser, pr),
            (outcome, "MR_Egger", eg["slope"], eg["slope_se"], eg["slope_p"]),
            (outcome, "Weighted_median", *wm), (outcome, "IVW_no_palindromic", bnp, senp, pnp)]
    if "rs2736100" in loo:
        rows.append((outcome + "_noTERT", "IVW_fixed", *loo["rs2736100"]))
    all_rows += rows
    d.to_csv(os.path.join(res_dir, f"harmonised_{outcome}.tsv"), sep="\t", index=False)
    log[outcome] = {"Q": q, "Q_df": df, "Q_p": qp, "egger_intercept": eg["intercept"], "egger_int_p": eg["int_p"]}
    print()

# ---- Stage 10: compare to published ----
res = pd.DataFrame(all_rows, columns=["outcome", "method", "beta", "se", "p"])
res["or"] = np.exp(res.beta); res["lo"] = np.exp(res.beta - 1.96 * res.se); res["hi"] = np.exp(res.beta + 1.96 * res.se)
res.to_csv(os.path.join(res_dir, "mr_results.tsv"), sep="\t", index=False)
json.dump(log, open(os.path.join(res_dir, "diagnostics.json"), "w"), indent=2, default=float)

print("== Replication scorecard (IVW fixed, OR per 1 kb TL) ==")
print(f"{'outcome':<20}{'published':<28}{'replicated':<28}{'dir':<5}{'sig':<5}{'pub OR in our CI'}")
for k, t in TARGETS.items():
    r = res[(res.outcome == k) & (res.method == "IVW_fixed")]
    if r.empty:
        continue
    r = r.iloc[0]
    same_dir = np.sign(np.log(t["or"])) == np.sign(r.beta) if t["p"] < 0.05 else True
    same_sig = (t["p"] < 0.05) == (r.p < 0.05)
    inside = r.lo <= t["or"] <= r.hi
    print(f"{k:<20}{t['or']:.2f} ({t['lo']:.2f}-{t['hi']:.2f}) P={t['p']:.1g}   "
          f"{r['or']:.2f} ({r.lo:.2f}-{r.hi:.2f}) P={r.p:.1g}   {'Y' if same_dir else 'N':<5}{'Y' if same_sig else 'N':<5}{'Y' if inside else 'N'}")
