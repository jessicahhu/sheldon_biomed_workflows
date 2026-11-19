"""Replication of Wang et al. 2026 (Naunyn-Schmiedeberg's Arch Pharmacol 399:9871), drug use -> lung cancer.

Exposure: UK Biobank self-reported medication-use GWAS (Sakaue 2021 atlas; GWAS Catalog GCST900189xx).
Outcome:  McKay 2017 lung cancer, overall (GCST004748; 29,266 cases / 56,450 controls).
Instruments: built by build_instruments.py (P<5e-8 or 5e-6, clump r2<0.001/10 Mb, F>10).
Harmonisation (paper): drop palindromic SNPs and SNPs absent from the outcome (no proxies).
Estimators match TwoSampleMR: IVW (multiplicative random effects), ML, weighted median, MR-Egger.

Usage: python3 mr_wang.py <instrument_dir> <outcome_raw_dir> <published_results.tsv> <results_dir>
"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common"))
from mr_methods import ivw, egger, weighted_median, max_likelihood, COMP

inst_dir, raw_dir, pub_path, res_dir = sys.argv[1:5]
DRUGS = {"salicylic_acid": "GCST90018995", "opioids": "GCST90018994", "antithrombotic": "GCST90018982",
         "thyroid": "GCST90018990", "statins": "GCST90018989", "diabetes_drugs": "GCST90018981"}
pub = pd.read_csv(pub_path, sep="\t")
pub["acc"] = pub.gwas_id.str.replace("ebi-a-", "")


def harmonise(ex, out, drop_palindromic=True):
    """TwoSampleMR-style: align outcome to exposure effect allele; returns aligned table + notes."""
    m = ex.merge(out, left_on="rsid", right_on="variant_id", suffixes=("", "_out"))
    rows, notes = [], []
    for _, r in m.iterrows():
        ea, oa = r.effect_allele.upper(), r.other_allele.upper()
        eo, oo = r.effect_allele_out.upper(), r.other_allele_out.upper()
        pal = COMP.get(ea) == oa
        if pal:
            maf = min(r.effect_allele_frequency, 1 - r.effect_allele_frequency)
            if drop_palindromic or maf > 0.42:
                notes.append(f"{r.rsid}: palindromic {ea}/{oa} -> dropped"); continue
            # TwoSampleMR action=2: infer strand from frequency
            same = (r.effect_allele_frequency - 0.5) * (r.effect_allele_frequency_out - 0.5) > 0
            sign = (1 if eo == ea else -1) * (1 if same else -1)
        elif (eo, oo) == (ea, oa) or (eo, oo) == (COMP.get(ea), COMP.get(oa)):
            sign = 1
        elif (eo, oo) == (oa, ea) or (eo, oo) == (COMP.get(oa), COMP.get(ea)):
            sign = -1
        else:
            notes.append(f"{r.rsid}: alleles {ea}/{oa} vs {eo}/{oo} -> dropped"); continue
        rows.append({"rsid": r.rsid, "bx": r.beta, "sx": r.standard_error,
                     "by": sign * r.beta_out, "sy": r.standard_error_out})
    return pd.DataFrame(rows), notes


def run(h):
    bx, sx, by, sy = (h[c].to_numpy(float) for c in ("bx", "sx", "by", "sy"))
    b, se, p, q, df = ivw(bx, by, sy, random=True)
    res = {"IVW": (b, se, p)}
    res["ML"] = max_likelihood(bx, sx, by, sy)
    res["WM"] = weighted_median(bx, by, sy)
    e = egger(bx, by, sy)
    res["Egger"] = (e["slope"], e["slope_se"], e["slope_p"])
    from scipy import stats
    diag = {"Q": q, "Q_df": df, "Q_p": stats.chi2.sf(q, df), "egger_int": e["intercept"], "egger_int_p": e["int_p"]}
    return res, diag


os.makedirs(res_dir, exist_ok=True)
pub_methods = {"IVW": "Inverse variance weighted", "ML": "Maximum likelihood", "WM": "Weighted median", "Egger": "MR Egger"}
rows, comp = [], []
for name, acc in DRUGS.items():
    ex = pd.read_csv(os.path.join(inst_dir, f"instruments_{name}.tsv"), sep="\t")
    out = pd.read_csv(os.path.join(raw_dir, f"lung_all_{name}.tsv"), sep="\t")
    out = out.rename(columns={c: c + "_out" for c in ("effect_allele", "other_allele", "beta", "standard_error",
                                                      "effect_allele_frequency")})
    h, notes = harmonise(ex, out)
    missing = sorted(set(ex.rsid) - set(out.variant_id))
    res, diag = run(h)
    pu = pub[pub.acc == acc].set_index("method")
    print(f"== {name} ({acc}): {len(ex)} instruments (P<{ex.threshold.iloc[0]:g}), {len(missing)} missing from outcome, "
          f"{len(notes)} dropped at harmonisation -> {len(h)} used (paper: {int(pu.nsnp.iloc[0])})")
    for n in notes:
        print("   ", n)
    for meth, (b, se, p) in res.items():
        pr = pu.loc[pub_methods[meth]]
        lo, hi = np.exp(b - 1.959964 * se), np.exp(b + 1.959964 * se)
        rows.append({"drug": name, "method": meth, "nsnp": len(h), "beta": b, "se": se, "p": p,
                     "or": np.exp(b), "lo": lo, "hi": hi})
        print(f"   {meth:6s} ours OR {np.exp(b):.3f} ({lo:.3f}-{hi:.3f}) P={p:.2g}   "
              f"paper {pr['or']:.3f} ({pr.or_lci:.3f}-{pr.or_uci:.3f}) P={pr.p:.2g}")
        if meth == "IVW":
            comp.append({"drug": name, "paper_nsnp": int(pu.nsnp.iloc[0]), "our_nsnp": len(h),
                         "paper_or": f"{pr['or']:.3f} ({pr.or_lci:.3f}-{pr.or_uci:.3f})", "paper_p": pr.p,
                         "our_or": f"{np.exp(b):.3f} ({lo:.3f}-{hi:.3f})", "our_p": p,
                         "direction": np.sign(b) == np.sign(pr.b),
                         "significance_p05": (p < 0.05) == (pr.p < 0.05),
                         "paper_or_in_our_ci": lo <= pr["or"] <= hi})
    print(f"   Q={diag['Q']:.1f} df={diag['Q_df']} P={diag['Q_p']:.2g} (paper IVW Q P={pu.loc['Inverse variance weighted'].Q_p:.2g}); "
          f"Egger intercept {diag['egger_int']:.4f} P={diag['egger_int_p']:.2g} "
          f"(paper {pu.loc['Inverse variance weighted'].egger_intercept:.4f} P={pu.loc['Inverse variance weighted'].egger_p:.2g})")
    h2, _ = harmonise(ex, out, drop_palindromic=False)
    b2, se2, p2, *_ = ivw(*(h2[c].to_numpy(float) for c in ("bx", "by", "sy")), random=True)
    print(f"   sensitivity, keep palindromic SNPs with MAF<0.42 (TwoSampleMR default): n={len(h2)} "
          f"IVW OR {np.exp(b2):.3f} ({np.exp(b2-1.96*se2):.3f}-{np.exp(b2+1.96*se2):.3f}) P={p2:.2g}\n")
    h.to_csv(os.path.join(res_dir, f"harmonised_{name}.tsv"), sep="\t", index=False)

pd.DataFrame(rows).to_csv(os.path.join(res_dir, "mr_results.tsv"), sep="\t", index=False)
c = pd.DataFrame(comp)
c.to_csv(os.path.join(res_dir, "comparison_ivw.tsv"), sep="\t", index=False)
print(c.to_string(index=False))
