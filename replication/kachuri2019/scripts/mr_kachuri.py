"""Replication of Kachuri et al. 2019 (Int J Epidemiol 48:751), TL -> lung & head-and-neck cancer.

Instruments (8, as in the paper):
  7 literature SNPs (ACYP2, PXK, TERC, NAF1, OBFC1, ZNF676, RTEL1). Kachuri used r2=1 proxies for
    ACYP2/NAF1/ZNF676; we use the r2=1 originals so the TL effects come straight from Zhang 2015 Table 2.
  1 multi-allelic 5p15.33 score built from deep sequencing (not public). Its TL and cancer associations
    are taken from Kachuri Table 3, so this instrument is NOT rebuilt from public data.
Outcomes: McKay 2017 lung GWAS (GCST004748/4744/4750); OncoArray oral+pharyngeal cancer, two European
  sets (GCST012234, GCST012235) combined by fixed-effect meta-analysis.
Usage: python3 mr_kachuri.py <zhang_exposure.tsv> <raw_dir> <results_dir>
"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common"))
from mr_methods import ivw, egger, weighted_median, se_from_p, se_from_ci, harmonise, fixed_meta, fmt

exp_path, raw_dir, res_dir = sys.argv[1:4]

KACHURI_SNPS = ["rs11125529", "rs6772228", "rs10936599", "rs7675998", "rs9420907", "rs412658", "rs755017"]
# outcome-file aliases: instrument -> list of (rsid in outcome file, allele in that file matching the long allele)
ALIASES = {
    "rs10936599": [("rs11711621", "C")],    # TERC proxy, r2=1 EUR; C<->C by freq (0.77) and lung betas
    "rs412658":   [("rs1277401554", "T")],  # same position/alleles, different ID in the HNC files
}
REF_LONG_FREQ = {"rs6772228": 0.946}  # PXK long allele T: McKay EUR freq (1000G MAF of A = 0.01)

# 5p15.33 score from Kachuri Table 3 (TL: beta 0.14 SD ~ 1 kb, SE 0.02)
P5 = {"bx": 0.14, "sx": 0.02, "lung_all": (1.04, 1.01, 1.07), "lung_adeno": (1.06, 1.03, 1.10),
      "lung_squam": (1.03, 0.98, 1.07), "hnc": (0.95, 0.90, 1.00)}

TARGETS = {  # Kachuri Table 4: IVW and weighted median (ML in parentheses in the text)
    "lung_all":   {"ivw": (1.39, 1.21, 1.60, 3.7e-6), "wm": (1.37, 1.12, 1.67, 2.0e-3), "ml": (1.41, 1.20, 1.65, 2.0e-5)},
    "lung_adeno": {"ivw": (1.83, 1.51, 2.22, 5.5e-10), "wm": (1.63, 1.23, 2.16, 6.5e-4), "ml": (1.92, 1.51, 2.45, 1.3e-7)},
    "lung_squam": {"ivw": (1.04, 0.83, 1.29, 0.74), "wm": (1.09, 0.82, 1.46, 0.57), "ml": (1.04, 0.83, 1.29, 0.74)},
    "hnc":        {"ivw": (0.90, 0.70, 1.15, 0.41), "wm": (0.71, 0.51, 0.98, 0.04), "ml": (0.90, 0.70, 1.15, 0.39)},
}

ex = pd.read_csv(exp_path, sep="\t").set_index("snp").loc[KACHURI_SNPS].reset_index()
ex["se_kb"] = se_from_p(ex.beta_kb, ex.p)
print("== Instruments: 7 literature SNPs (TL effects from Zhang 2015 Table 2) + 5p15.33 score (Kachuri Table 3) ==")
print(ex[["snp", "locus", "long_allele", "beta_kb", "se_kb"]].round(4).to_string(index=False), "\n")


def load(path):
    d = pd.read_csv(path, sep="\t").rename(columns={"variant_id": "snp"})
    return d.set_index("snp")


def aligned(tab, snp, long_allele, label):
    """Return (by, sy, note) for one instrument from one outcome table, using aliases if needed."""
    for rsid, la in [(snp, long_allele)] + ALIASES.get(snp, []):
        if rsid in tab.index:
            r = tab.loc[rsid]
            sign, note = harmonise(r.effect_allele, r.other_allele, float(r.effect_allele_frequency),
                                   r.beta, la, REF_LONG_FREQ.get(snp))
            if sign is None:
                return None, None, f"{label}: {snp} {note}"
            via = "" if rsid == snp else f" via proxy {rsid}"
            msg = f"{label}: {snp}{via}" + (f" [{note}]" if note else "")
            return sign * float(r.beta), float(r.standard_error), msg
    return None, None, f"{label}: {snp} MISSING (no proxy available)"


raw = {f.split("_GCST")[0]: load(os.path.join(raw_dir, f)) for f in sorted(os.listdir(raw_dir)) if f.endswith(".tsv")}
outcomes = {"lung_all": ["lung_all"], "lung_adeno": ["lung_adeno"], "lung_squam": ["lung_squam"],
            "hnc": ["hnc_setA", "hnc_setB"]}

rows = []
for oc, sources in outcomes.items():
    print(f"==================== {oc}  ({' + '.join(sources)}) ====================")
    recs = []
    for _, e in ex.iterrows():
        bys, sys_ = [], []
        for s in sources:
            b, s_, note = aligned(raw[s], e.snp, e.long_allele, s)
            if note and ("proxy" in note or "[" in note or "MISSING" in note or "dropped" in note):
                print("  [harmonise]", note)
            if b is not None:
                bys.append(b); sys_.append(s_)
        if bys:
            b, s_ = fixed_meta(bys, sys_)
            recs.append({"snp": e.snp, "locus": e.locus, "bx": e.beta_kb, "by": b, "sy": s_})
    d = pd.DataFrame(recs)
    or5, lo5, hi5 = P5[oc]
    d5 = pd.concat([d, pd.DataFrame([{"snp": "5p15.33_score", "locus": "5p15.33", "bx": P5["bx"],
                                       "by": np.log(or5), "sy": se_from_ci(lo5, hi5)}])], ignore_index=True)
    d5["wald_or"] = np.exp(d5.by / d5.bx)
    print(d5.round(4).to_string(index=False))
    d5.to_csv(os.path.join(res_dir, f"harmonised_{oc}.tsv"), sep="\t", index=False)

    for setname, dd in [("8 IVs (7 public + published 5p15.33)", d5), ("7 public SNPs only", d)]:
        bx, by, sy = dd.bx.values, dd.by.values, dd.sy.values
        b, se, p, q, df = ivw(bx, by, sy)
        br, ser, pr, _, _ = ivw(bx, by, sy, random=True)
        wm = weighted_median(bx, by, sy)
        eg = egger(bx, by, sy)
        print(f"  -- {setname}: {len(dd)} instruments")
        print(f"     IVW fixed   {fmt(b, se, p)}   | Cochran Q={q:.1f} df={df} P={__import__('scipy').stats.chi2.sf(q, df):.2g}")
        print(f"     IVW mult-RE {fmt(br, ser, pr)}")
        print(f"     W. median   {fmt(*wm)}")
        print(f"     MR-Egger    {fmt(eg['slope'], eg['slope_se'], eg['slope_p'])}; intercept {eg['intercept']:.4f} (P={eg['int_p']:.2g})")
        key = "8iv" if setname.startswith("8") else "7snp"
        rows += [(oc, key, "IVW_fixed", b, se, p), (oc, key, "IVW_multRE", br, ser, pr),
                 (oc, key, "Weighted_median", *wm), (oc, key, "MR_Egger", eg["slope"], eg["slope_se"], eg["slope_p"])]
    print()

res = pd.DataFrame(rows, columns=["outcome", "instruments", "method", "beta", "se", "p"])
res["or"], res["lo"], res["hi"] = np.exp(res.beta), np.exp(res.beta - 1.96 * res.se), np.exp(res.beta + 1.96 * res.se)
res.to_csv(os.path.join(res_dir, "mr_results.tsv"), sep="\t", index=False)

print("== Replication scorecard (OR per 1 kb TL; 8 instruments as in the paper) ==")
print(f"{'outcome':<12}{'method':<8}{'published':<28}{'replicated':<28}{'dir':<5}{'sig':<5}{'pub OR in our CI'}")
for oc, t in TARGETS.items():
    for m, col in [("ivw", "IVW_fixed"), ("wm", "Weighted_median")]:
        po, plo, phi, pp = t[m]
        r = res[(res.outcome == oc) & (res.instruments == "8iv") & (res.method == col)].iloc[0]
        same_dir = (np.sign(np.log(po)) == np.sign(r.beta)) if pp < 0.05 else True
        same_sig = (pp < 0.05) == (r.p < 0.05)
        inside = r.lo <= po <= r.hi
        print(f"{oc:<12}{m:<8}{po:.2f} ({plo:.2f}-{phi:.2f}) P={pp:.1g}".ljust(48) +
              f"{r['or']:.2f} ({r.lo:.2f}-{r.hi:.2f}) P={r.p:.1g}".ljust(28) +
              f"{'Y' if same_dir else 'N':<5}{'Y' if same_sig else 'N':<5}{'Y' if inside else 'N'}")
