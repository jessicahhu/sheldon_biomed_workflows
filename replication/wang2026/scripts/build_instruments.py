"""Build independent instruments for each drug-use GWAS the way Wang 2026 (via TwoSampleMR/OpenGWAS) did:
  P < 5e-8 (relaxed to 5e-6 if fewer than 3 SNPs survive clumping), then LD clumping r2 < 0.001 within
  10,000 kb against 1000 Genomes phase 3 EUR (503 people), then F > 10.

No PLINK: genotypes for the candidate SNPs are pulled straight from the 1000G phase 3 GRCh37 VCFs with
remote bcftools/tabix queries, and clumping is done here (greedy by P, as plink --clump does). SNPs absent
from the reference or with EUR MAF < 0.01 are dropped, like the OpenGWAS clumping reference.

Exposure files are the GWAS Catalog harmonised files (GRCh38), pre-filtered to P < 5e-6 by fetch_exposures.sh.
GRCh37 positions (needed for 1000G and for the lung GWAS) come from the Ensembl GRCh37 REST API.

Usage: python3 build_instruments.py <exposure_dir> <ld_dir> <out_dir>
"""
import sys, os, json, subprocess, urllib.request, time
import numpy as np, pandas as pd

exp_dir, ld_dir, out_dir = (os.path.abspath(a) for a in sys.argv[1:4])  # absolute: bcftools runs with cwd=cache_dir
DRUGS = {  # GWAS Catalog accession -> name (Wang 2026 Table S1)
    "GCST90018995": "salicylic_acid", "GCST90018994": "opioids", "GCST90018982": "antithrombotic",
    "GCST90018990": "thyroid", "GCST90018989": "statins", "GCST90018981": "diabetes_drugs",
}
if len(sys.argv) > 4:  # optional subset of drug names
    DRUGS = {k: v for k, v in DRUGS.items() if v in sys.argv[4:]}
VCF = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr{c}.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz"
R2, KB, MIN_MAF = 0.001, 10_000, 0.01
COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}


def grch37_positions(rsids, cache_path):
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    todo = [r for r in rsids if r not in cache]
    for i in range(0, len(todo), 200):
        body = json.dumps({"ids": todo[i:i + 200]}).encode()
        req = urllib.request.Request("https://grch37.rest.ensembl.org/variation/homo_sapiens", data=body,
                                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        res = json.load(urllib.request.urlopen(req, timeout=120))
        for rs in todo[i:i + 200]:
            maps = [m for m in res.get(rs, {}).get("mappings", [])
                    if m["seq_region_name"] in [str(c) for c in range(1, 23)]]
            cache[rs] = [int(maps[0]["seq_region_name"]), int(maps[0]["start"])] if maps else None
        time.sleep(0.2)
    json.dump(cache, open(cache_path, "w"))
    return cache


def eur_genotypes(chrom, positions, cache_dir):
    """{pos: (ref, alt, dosage array)} for biallelic SNPs at the given GRCh37 positions (EUR only)."""
    path = os.path.join(cache_dir, f"geno_chr{chrom}.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    todo = sorted({p for p in positions if str(p) not in cache})
    if todo:
        # Merge positions <50 kb apart into intervals: one sequential stream per dense region is far
        # faster over HTTP than one random seek per SNP (the HLA region alone has ~20k candidates).
        iv = [[todo[0], todo[0]]]
        for p in todo[1:]:
            if p - iv[-1][1] < 50_000:
                iv[-1][1] = p
            else:
                iv.append([p, p])
        reg = os.path.join(cache_dir, f"regions_{chrom}.txt")
        with open(reg, "w") as f:
            f.writelines(f"{chrom}\t{a}\t{b}\n" for a, b in iv)
        want = set(todo)
        out = subprocess.run(["bcftools", "view", "-H", "-v", "snps", "-m2", "-M2", "-S", os.path.join(ld_dir, "eur.txt"),
                              "-R", reg, VCF.format(c=chrom)], capture_output=True, text=True, check=True,
                             cwd=cache_dir).stdout
        for p in todo:
            cache[str(p)] = None
        for line in out.splitlines():
            f = line.split("\t")
            if int(f[1]) not in want:
                continue
            gts = [g.split(":")[0] for g in f[9:]]
            dos = [int(g[0]) + int(g[2]) for g in gts]
            cache[f[1]] = [f[3], f[4], dos]
        json.dump(cache, open(path, "w"))
    return {int(k): v for k, v in cache.items() if v is not None and int(k) in set(positions)}


def match_ref(row, g):
    """Return dosage aligned to the effect allele, or None if alleles don't match the reference."""
    ref, alt, dos = g
    ea, oa = row.effect_allele.upper(), row.other_allele.upper()
    for flip in (False, True):
        e, o = (COMP.get(ea), COMP.get(oa)) if flip else (ea, oa)
        if (e, o) == (alt, ref):
            return np.array(dos, float)
        if (e, o) == (ref, alt):
            return 2 - np.array(dos, float)
    return None


def clump(df, geno):
    """Greedy plink-style clumping, vectorised per chromosome: take the best remaining SNP as index and
    remove every remaining SNP within KB kb with genotype r2 > R2."""
    keep = []
    for _, d in df.groupby("chr37"):
        d = d.sort_values("p_value").reset_index(drop=True)
        G = np.array([geno[r] for r in d.rsid])
        G = G - G.mean(1, keepdims=True)
        G /= np.linalg.norm(G, axis=1, keepdims=True)  # MAF>=1% filter guarantees non-zero variance
        pos, alive = d.pos37.to_numpy(), np.ones(len(d), bool)
        for i in range(len(d)):
            if not alive[i]:
                continue
            keep.append(d.iloc[i])
            near = alive & (np.abs(pos - pos[i]) <= KB * 1000)
            near[: i + 1] = False
            idx = np.where(near)[0]
            alive[idx[(G[idx] @ G[i]) ** 2 > R2]] = False
    return pd.DataFrame(keep)


os.makedirs(out_dir, exist_ok=True)
cache_dir = os.path.join(ld_dir, "cache"); os.makedirs(cache_dir, exist_ok=True)

# Prefetch EUR genotypes for every P<5e-8 candidate across drugs, one remote bcftools job per chromosome.
from concurrent.futures import ThreadPoolExecutor
allc = pd.concat([pd.read_csv(os.path.join(exp_dir, f"{a}.p5e6.tsv"), sep="\t") for a in DRUGS])
allc = allc[(allc.p_value < 5e-8) & allc.rsid.astype(str).str.startswith("rs")]
pos_all = grch37_positions(sorted(set(allc.rsid)), os.path.join(cache_dir, "rsid_grch37.json"))
by_chr = {}
for v in pos_all.values():
    if v:
        by_chr.setdefault(v[0], set()).add(v[1])
print(f"prefetching genotypes for {sum(map(len, by_chr.values()))} positions on {len(by_chr)} chromosomes", flush=True)
with ThreadPoolExecutor(len(by_chr)) as pool:
    list(pool.map(lambda c: eur_genotypes(c, sorted(by_chr[c]), cache_dir), by_chr))
log = []
for acc, name in DRUGS.items():
    path = os.path.join(exp_dir, f"{acc}.p5e6.tsv")
    ex = pd.read_csv(path, sep="\t", dtype={"chromosome": str})
    ex = ex[ex.rsid.astype(str).str.startswith("rs")].drop_duplicates("rsid")
    for thr in (5e-8, 5e-6):
        cand = ex[ex.p_value < thr].copy()
        pos = grch37_positions(cand.rsid.tolist(), os.path.join(cache_dir, "rsid_grch37.json"))
        cand["chr37"] = cand.rsid.map(lambda r: pos.get(r)[0] if pos.get(r) else np.nan)
        cand["pos37"] = cand.rsid.map(lambda r: pos.get(r)[1] if pos.get(r) else np.nan)
        n0 = len(cand); cand = cand.dropna(subset=["chr37"]).astype({"chr37": int, "pos37": int})
        geno, ok = {}, []
        for c, sub in cand.groupby("chr37"):
            g = eur_genotypes(c, sub.pos37.tolist(), cache_dir)
            for _, r in sub.iterrows():
                d = match_ref(r, g[r.pos37]) if r.pos37 in g else None
                if d is not None and min(d.mean() / 2, 1 - d.mean() / 2) >= MIN_MAF:
                    geno[r.rsid] = d; ok.append(r.rsid)
        inref = cand[cand.rsid.isin(ok)]
        inst = clump(inref, geno)
        inst = inst.assign(F=(inst.beta / inst.standard_error) ** 2)
        inst = inst[inst.F > 10]
        msg = (f"{name} ({acc}) P<{thr:g}: {n0} SNPs, {len(cand)} mapped to GRCh37, {len(inref)} in 1000G EUR "
               f"(MAF>={MIN_MAF}), {len(inst)} after clumping r2<{R2}/{KB}kb and F>10")
        print(msg); log.append(msg)
        if len(inst) >= 3:
            break
    inst.assign(threshold=thr).to_csv(os.path.join(out_dir, f"instruments_{name}.tsv"), sep="\t", index=False)
open(os.path.join(out_dir, "instruments_log.txt"), "w").write("\n".join(log) + "\n")
