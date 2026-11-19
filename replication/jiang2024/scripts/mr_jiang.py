"""Replication of Jiang et al. 2024 (Cancer Res Commun 4:2815): bidirectional MR, telomere length <-> haematologic cancers.

Exposure: OpenGWAS ieu-b-4879 (UKB TL, SD units, GRCh37). Outcomes: FinnGen R9 (GRCh38), matched by rsID.
Mirrors TwoSampleMR defaults where the paper is silent:
  clumping r2<0.001, 10,000 kb, 1000G EUR (MRC-IEU reference, same panel as the OpenGWAS clumping API);
  harmonise_data action=2 (palindromes inferred from EAF; dropped if MAF>0.42);
  IVW = multiplicative random effects; MR-Egger; weighted median; Cochran's Q.
Forward: TL p<5e-8 instruments; drop SNPs with outcome p<5e-8.
Reverse: cancer p<1e-5 instruments; drop SNPs with TL p<5e-8.
Not done: PhenoScanner filtering (service retired), MR-PRESSO.

Usage: python3 -I mr_jiang.py <jiang2024 dir>
"""
import csv, gzip, os, subprocess, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "common"))
from mr_methods import ivw, egger, weighted_median, COMP

ROOT = os.path.abspath(sys.argv[1])
D, RES = f"{ROOT}/data", f"{ROOT}/results"
PLINK, REF = f"{ROOT}/tools/plink/plink", f"{D}/ld_ref/EUR"
OUTCOMES = list(csv.DictReader(open(f"{ROOT}/scripts/finngen_outcomes.tsv"), delimiter="\t"))
os.makedirs(f"{RES}/clump", exist_ok=True)
log = open(f"{RES}/run_log.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a); print(s); log.write(s + "\n"); log.flush()


def clump(df, tag, p1):
    """PLINK 1.9 clumping; returns the index SNP IDs. SNPs absent from the reference are dropped (as the API does)."""
    f = f"{RES}/clump/{tag}.in"
    df[["snp", "p"]].rename(columns={"snp": "SNP", "p": "P"}).to_csv(f, sep="\t", index=False)
    out = f"{RES}/clump/{tag}"
    subprocess.run([PLINK, "--bfile", REF, "--clump", f, "--clump-p1", str(p1), "--clump-p2", "1",
                    "--clump-r2", "0.001", "--clump-kb", "10000", "--out", out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(out + ".clumped"):
        return []
    return pd.read_csv(out + ".clumped", sep=r"\s+")["SNP"].tolist()


def harmonise(e, o):
    """TwoSampleMR action=2. e/o: dicts with ea, oa, eaf, beta. Returns outcome beta aligned to e.ea, or (None, reason)."""
    ea, oa, eaf = e["ea"].upper(), e["oa"].upper(), e["eaf"]
    oea, ooa, oeaf, ob = o["ea"].upper(), o["oa"].upper(), o["eaf"], o["beta"]
    if len(ea) > 1 or len(oa) > 1 or len(oea) > 1 or len(ooa) > 1:  # indels: require exact allele match
        if (ea, oa) == (oea, ooa): return ob, ""
        if (ea, oa) == (ooa, oea): return -ob, ""
        return None, "indel allele mismatch"
    if COMP[ea] == oa:  # palindromic exposure SNP
        if min(eaf, 1 - eaf) > 0.42:
            return None, "palindromic, MAF>0.42"
        if {oea, ooa} != {ea, oa}:
            return None, "palindromic allele mismatch"
        same_freq = (eaf - 0.5) * ((oeaf if oea == ea else 1 - oeaf) - 0.5) > 0
        sign = 1 if oea == ea else -1
        return (sign if same_freq else -sign) * ob, ("" if same_freq else "palindromic strand flip by EAF")
    if (oea, ooa) == (ea, oa): return ob, ""
    if (oea, ooa) == (oa, ea): return -ob, ""
    if (COMP[oea], COMP[ooa]) == (ea, oa): return ob, "strand flip"
    if (COMP[oea], COMP[ooa]) == (oa, ea): return -ob, "strand flip"
    return None, "allele mismatch"


def run_mr(bx, sx, by, sy):
    bx, sx, by, sy = map(np.asarray, (bx, sx, by, sy))
    r = {"n": len(bx)}
    b, se, p, q, df = ivw(bx, by, sy, random=len(bx) > 3)
    r.update(ivw_b=b, ivw_se=se, ivw_p=p, q=q, q_df=df, q_p=stats.chi2.sf(q, df) if df > 0 else np.nan)
    if len(bx) >= 3:
        wm = weighted_median(bx, by, sy); r.update(wm_b=wm[0], wm_se=wm[1], wm_p=wm[2])
        eg = egger(bx, by, sy); r.update(egger_b=eg["slope"], egger_se=eg["slope_se"], egger_p=eg["slope_p"],
                                         egger_int_p=eg["int_p"])
    return r


def orci(b, se):
    return f"{np.exp(b):.3f} ({np.exp(b - 1.96 * se):.3f}-{np.exp(b + 1.96 * se):.3f})"


def load_finngen(name):
    df = pd.read_csv(f"{D}/raw/finngen_r9/{name}.tsv", sep="\t", dtype={"chrom": str})
    df = df.rename(columns={"alt": "ea", "ref": "oa", "af_alt": "eaf", "sebeta": "se", "pval": "p"})
    df = df.assign(snp=df["rsids"].astype(str).str.split(",")).explode("snp")
    return df[df["snp"].str.startswith("rs")].drop_duplicates("snp").set_index("snp")


# ------------------------------------------------------------------ forward: TL -> cancer
tl = pd.read_csv(f"{D}/tl_sig_5e8.tsv", sep="\t", dtype={"chr": str})
tl = tl.rename(columns={"effect_allele": "ea", "other_allele": "oa"}).drop_duplicates("snp").set_index("snp")
tl_iv = clump(tl.reset_index(), "tl_forward", 5e-8)
say(f"TL: {len(tl)} variants p<5e-8 -> {len(tl_iv)} clumped instruments (r2<0.001, 10 Mb, 1000G EUR)")
say(f"  of which chrX: {int((tl.loc[tl_iv, 'chr'] == 'X').sum())}; min F = {((tl.loc[tl_iv,'beta']/tl.loc[tl_iv,'se'])**2).min():.1f}")
pd.Series(tl_iv).to_csv(f"{RES}/tl_instruments.txt", index=False, header=False)

rows = []
say("\n== Forward: TL (per SD) -> cancer, OR ==")
for oc in OUTCOMES:
    name = oc["outcome"]
    fg = load_finngen(name)
    bx, sx, by, sy, notes = [], [], [], [], {"missing": 0, "outcome p<5e-8": 0}
    harm = []
    for s in tl_iv:
        if s not in fg.index:
            notes["missing"] += 1; continue
        o = fg.loc[s]
        if o["p"] < 5e-8:
            notes["outcome p<5e-8"] += 1; continue
        e = tl.loc[s]
        b, why = harmonise({"ea": e["ea"], "oa": e["oa"], "eaf": e["eaf"]},
                           {"ea": o["ea"], "oa": o["oa"], "eaf": o["eaf"], "beta": o["beta"]})
        if b is None:
            notes[why] = notes.get(why, 0) + 1; continue
        if why: notes[why] = notes.get(why, 0) + 1
        bx.append(e["beta"]); sx.append(e["se"]); by.append(b); sy.append(o["se"])
        harm.append((s, e["ea"], e["beta"], e["se"], b, o["se"], o["p"]))
    pd.DataFrame(harm, columns=["snp", "tl_effect_allele", "bx", "sx", "by", "sy", "p_outcome"]).to_csv(
        f"{RES}/harmonised_forward_{name}.tsv", sep="\t", index=False)
    r = run_mr(bx, sx, by, sy); r.update(direction="forward", outcome=name); rows.append(r)
    say(f"{name:18s} n={r['n']:3d}  IVW {orci(r['ivw_b'], r['ivw_se'])} p={r['ivw_p']:.3g}  "
        f"WM {orci(r['wm_b'], r['wm_se'])}  Egger {orci(r['egger_b'], r['egger_se'])}  "
        f"Qp={r['q_p']:.3f} int_p={r['egger_int_p']:.3f}  [{', '.join(f'{k}={v}' for k, v in notes.items() if v)}]")

# ------------------------------------------------------------------ reverse: cancer -> TL
say("\n== Reverse: cancer (per log-odds) -> TL (SD), exp(beta) ==")
cand = {}
for oc in OUTCOMES:
    fg = load_finngen(oc["outcome"])
    sig = fg[fg["p"] < 1e-5].reset_index()
    cand[oc["outcome"]] = (fg, clump(sig, f"rev_{oc['outcome']}", 1e-5) if len(sig) else [])
need = set().union(*[set(v[1]) for v in cand.values()])
tl_rev = {}
with gzip.open(f"{D}/raw/ieu-b-4879.vcf.gz", "rt") as f:  # one pass to pull TL stats for reverse instruments
    for line in f:
        if line[0] == "#": continue
        c = line.split("\t", 10)
        if c[2] in need:
            v = dict(zip(c[8].split(":"), c[9].rstrip("\n").split(":")))
            tl_rev[c[2]] = {"ea": c[4], "oa": c[3], "eaf": float(v["AF"]), "beta": float(v["ES"]),
                            "se": float(v["SE"]), "p": 10 ** -float(v["LP"])}
for oc in OUTCOMES:
    name = oc["outcome"]; fg, ivs = cand[name]
    bx, sx, by, sy, notes = [], [], [], [], {"missing in TL": 0, "TL p<5e-8": 0}
    for s in ivs:
        if s not in tl_rev:
            notes["missing in TL"] += 1; continue
        t = tl_rev[s]
        if t["p"] < 5e-8:
            notes["TL p<5e-8"] += 1; continue
        e = fg.loc[s]
        b, why = harmonise({"ea": e["ea"], "oa": e["oa"], "eaf": e["eaf"]}, t)
        if b is None:
            notes[why] = notes.get(why, 0) + 1; continue
        bx.append(e["beta"]); sx.append(e["se"]); by.append(b); sy.append(t["se"])
    if len(bx) < 2:
        say(f"{name:18s} clumped={len(ivs)} usable={len(bx)} -> not estimable  [{notes}]")
        rows.append({"direction": "reverse", "outcome": name, "n": len(bx)}); continue
    r = run_mr(bx, sx, by, sy); r.update(direction="reverse", outcome=name); rows.append(r)
    extra = f"WM {orci(r['wm_b'], r['wm_se'])}" if "wm_b" in r else ""
    say(f"{name:18s} clumped={len(ivs):3d} n={r['n']:3d}  IVW {orci(r['ivw_b'], r['ivw_se'])} p={r['ivw_p']:.3g}  {extra}  "
        f"[{', '.join(f'{k}={v}' for k, v in notes.items() if v)}]")

pd.DataFrame(rows).to_csv(f"{RES}/mr_results.tsv", sep="\t", index=False)
say(f"\nWrote {RES}/mr_results.tsv")
