"""Build the blind-agent data files for Jiang 2024 (paper_3 forward, paper_3b reverse) and the two question JSONs.

Option (a): the agent gets un-clumped instruments plus LD reference genotypes, so it must do instrument
selection itself. Files are written to data/agent/{forward,reverse}/ with neutral names and columns.

  forward: exposure = TL variants at p<5e-8 (all 38,506 rows, duplicates and chrX kept as in the source);
           outcomes = 17 cancer GWAS restricted to those rsIDs; LD = genotypes for those rsIDs in the panel.
  reverse: exposures = 17 cancer GWAS restricted to p<1e-5; outcome = TL stats for the union of those
           rsIDs; LD = genotypes for that union.

LD genotype file format: snp, chr, pos, a1, a2, then `genotypes`: one character per reference individual
(503 European-ancestry 1000 Genomes samples), = count of a1 (0/1/2), 9 = missing.

Usage: python3 -I make_agent_files.py <jiang2024 dir> <blind_agent/questions dir>
"""
import csv, gzip, json, os, subprocess, sys
import pandas as pd

ROOT, QDIR = map(os.path.abspath, sys.argv[1:3])
D = f"{ROOT}/data"; A = f"{D}/agent"
PLINK, REF = f"{ROOT}/tools/plink/plink", f"{D}/ld_ref/EUR"
for sub in ("forward", "reverse"):
    os.makedirs(f"{A}/{sub}", exist_ok=True)

NAMES = {  # internal key -> neutral file stem / human label
    "lymphoid_haem_all": ("any_lymphoid_or_haematopoietic_malignancy", "any primary malignancy of lymphoid, haematopoietic and related tissue"),
    "aml": ("acute_myeloid_leukaemia", "acute myeloid leukaemia"),
    "cml": ("chronic_myeloid_leukaemia", "chronic myeloid leukaemia"),
    "all": ("acute_lymphoblastic_leukaemia", "acute lymphoblastic leukaemia"),
    "cll": ("chronic_lymphocytic_leukaemia", "chronic lymphocytic leukaemia"),
    "leuk_unspec": ("leukaemia_unspecified_cell_type", "leukaemia of unspecified cell type"),
    "myeloma": ("multiple_myeloma", "multiple myeloma"),
    "nhl": ("non_hodgkin_lymphoma", "non-Hodgkin lymphoma (all)"),
    "hodgkin": ("hodgkin_lymphoma", "Hodgkin lymphoma"),
    "follicular": ("nhl_follicular", "follicular lymphoma"),
    "nonfollicular": ("nhl_non_follicular", "non-follicular lymphoma"),
    "dlbcl": ("nhl_diffuse_large_b_cell", "diffuse large B-cell lymphoma"),
    "waldenstrom": ("nhl_lymphoplasmacytic", "lymphoplasmacytic lymphoma / Waldenström macroglobulinaemia"),
    "mantle": ("nhl_mantle_cell", "mantle cell lymphoma"),
    "marginal_zone": ("nhl_marginal_zone", "marginal zone B-cell lymphoma"),
    "t_nk": ("nhl_mature_t_nk", "mature T/NK-cell lymphoma"),
    "nhl_other": ("nhl_other_unspecified", "other and unspecified non-Hodgkin lymphoma"),
}
OUTCOMES = list(csv.DictReader(open(f"{ROOT}/scripts/finngen_outcomes.tsv"), delimiter="\t"))
CANCER_COLS = {"chrom": "chr", "pos": "pos_b38", "rsids": "snp", "ref": "other_allele", "alt": "effect_allele",
               "af_alt": "eaf", "beta": "beta", "sebeta": "se", "pval": "p"}


def load_cancer(key):
    df = pd.read_csv(f"{D}/raw/finngen_r9/{key}.tsv", sep="\t", dtype=str, keep_default_na=False)
    return df[list(CANCER_COLS)].rename(columns=CANCER_COLS)  # variants without an rsID keep snp = ""


def genotypes(snps, out):
    """Write reference genotypes (one char per individual) for the SNPs present in the panel."""
    tmp = f"{out}.tmp"
    pd.Series(sorted(snps)).to_csv(tmp + ".snps", index=False, header=False)
    subprocess.run([PLINK, "--bfile", REF, "--extract", tmp + ".snps", "--recode", "A-transpose",
                    "--out", tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    n = 0
    with open(f"{tmp}.traw") as f, open(out, "w") as o:
        f.readline()
        o.write("snp\tchr\tpos\ta1\ta2\tgenotypes\n")
        for line in f:
            c = line.rstrip("\n").split("\t")
            g = "".join("9" if x == "NA" else x for x in c[6:])
            o.write(f"{c[1]}\t{c[0]}\t{c[3]}\t{c[4]}\t{c[5]}\t{g}\n"); n += 1
    for ext in (".snps", ".traw", ".log", ".nosex"):
        if os.path.exists(tmp + ext): os.remove(tmp + ext)
    return n


# ------------------------------------------------------------------ forward (paper_3)
tl = pd.read_csv(f"{D}/tl_sig_5e8.tsv", sep="\t", dtype=str).drop(columns=["n"])
tl.to_csv(f"{A}/forward/exposure_telomere_length.tsv", sep="\t", index=False)
tl_snps = set(tl["snp"])
fwd_files = {"exposure_telomere_length.tsv": "forward/exposure_telomere_length.tsv"}
for oc in OUTCOMES:
    stem = NAMES[oc["outcome"]][0]
    df = load_cancer(oc["outcome"])
    df = df[df["snp"].str.split(",").apply(lambda xs: any(x in tl_snps for x in xs))]
    df.to_csv(f"{A}/forward/outcome_{stem}.tsv", sep="\t", index=False)
    fwd_files[f"outcome_{stem}.tsv"] = f"forward/outcome_{stem}.tsv"
n = genotypes(tl_snps, f"{A}/forward/ld_reference_genotypes.tsv")
fwd_files["ld_reference_genotypes.tsv"] = "forward/ld_reference_genotypes.tsv"
print(f"forward: {len(tl)} exposure rows, {n} SNPs in LD reference")

# ------------------------------------------------------------------ reverse (paper_3b)
rev_files, need = {}, set()
for oc in OUTCOMES:
    stem = NAMES[oc["outcome"]][0]
    df = load_cancer(oc["outcome"])
    df = df[df["p"].astype(float) < 1e-5]
    df.to_csv(f"{A}/reverse/exposure_{stem}.tsv", sep="\t", index=False)
    rev_files[f"exposure_{stem}.tsv"] = f"reverse/exposure_{stem}.tsv"
    need |= {x for xs in df["snp"] for x in xs.split(",")}
rows = []
with gzip.open(f"{D}/raw/ieu-b-4879.vcf.gz", "rt") as f:
    for line in f:
        if line[0] == "#": continue
        c = line.split("\t", 10)
        if c[2] in need:
            v = dict(zip(c[8].split(":"), c[9].rstrip("\n").split(":")))
            rows.append({"chr": c[0], "pos_b37": c[1], "snp": c[2], "other_allele": c[3], "effect_allele": c[4],
                         "eaf": v["AF"], "beta": v["ES"], "se": v["SE"], "p": f"{10 ** -float(v['LP']):.3e}"})
pd.DataFrame(rows).to_csv(f"{A}/reverse/outcome_telomere_length.tsv", sep="\t", index=False)
rev_files["outcome_telomere_length.tsv"] = "reverse/outcome_telomere_length.tsv"
n = genotypes(need, f"{A}/reverse/ld_reference_genotypes.tsv")
rev_files["ld_reference_genotypes.tsv"] = "reverse/ld_reference_genotypes.tsv"
print(f"reverse: {len(need)} cancer-associated rsIDs, {len(rows)} found in TL GWAS, {n} in LD reference")

# ------------------------------------------------------------------ question JSONs
counts = "\n".join(f"  - {NAMES[o['outcome']][1]}: {int(o['cases']):,} cases / {int(o['controls']):,} controls"
                   for o in OUTCOMES)
LD_DESC = ("ld_reference_genotypes.tsv: genotypes of 503 European-ancestry reference individuals (1000 Genomes) "
           "for every listed variant present in the reference panel. Columns: snp, chr, pos (GRCh37), a1, a2, "
           "genotypes. `genotypes` is a string with one character per individual (same individual order on every "
           "row): the count of a1 (0, 1 or 2), or 9 if missing. Use it to estimate linkage disequilibrium (LD) "
           "between variants. Variants absent from the reference panel have no row.")
CANCER_DESC = ("columns: chr, pos_b38 (GRCh38), snp (rsID; occasionally several, comma-separated), other_allele, "
               "effect_allele, eaf (effect allele frequency), beta (log-odds per effect allele), se, p")
BLOCKED = [r"jiang", r"\bcao\b", r"\bqiu\b", r"\bfeng\b", r"shandong", r"cancer\s*res", r"CRC-24", r"2767-9764",
           r"finn\s*gen", r"\bR9\b", r"open\s*gwas", r"ieu-[ab]", r"mrcieu", r"\bcodd\b", r"UK\s*Biobank", r"\bUKB\b",
           r"\b2\.690\b", r"\b2\.155\b", r"\b1\.845\b", r"\b1\.697\b", r"\b1\.737\b", r"\b1\.651\b", r"\b2\.779\b",
           r"\b8\.940\b", r"\b2\.874\b", r"\b1\.603\b", r"\b1\.599\b"]
SRC = "Jiang et al. 2024, Cancer Res Commun (never sent to the agent; see replication/jiang2024/paper_card.md)"

def rel(p):
    return os.path.relpath(f"{A}/{p}", QDIR)

q3 = {
    "id": "paper_3",
    "source_paper": SRC + ". Forward direction.",
    "question": ("Is genetically predicted longer leukocyte telomere length causally associated with the risk of "
                 "haematologic malignancies? Analyse each of the 17 outcomes provided (overall, leukaemia types, "
                 "myeloma, Hodgkin and non-Hodgkin lymphoma, and non-Hodgkin subtypes). Report each effect as an "
                 "odds ratio per 1 standard deviation longer telomere length."),
    "files": {k: {"from": rel(v)} for k, v in fwd_files.items()},
    "data_description": (
        "exposure_telomere_length.tsv: every variant reaching p < 5e-8 in a genome-wide association study of "
        "leukocyte telomere length in ~470,000 European-ancestry adults. Telomere length was log-transformed and "
        "standardised, so beta is in SD units per copy of effect_allele. Columns: chr, pos (GRCh37), snp, "
        "other_allele, effect_allele, eaf, beta, se, p. These are raw association results, not independent "
        "signals: many variants are in LD with each other.\n"
        f"outcome_*.tsv: case-control GWAS of haematologic malignancies in a European-ancestry population cohort "
        f"(controls exclude all cancer cases), restricted to the variants in the exposure file. {CANCER_DESC}. "
        f"Some exposure variants are missing from the outcome files.\n{counts}\n" + LD_DESC),
    "blocked_terms": BLOCKED,
}
q3b = {
    "id": "paper_3b",
    "source_paper": SRC + ". Reverse direction.",
    "question": ("Does genetic liability to haematologic malignancies causally affect leukocyte telomere length? "
                 "Analyse each of the 17 malignancies provided. Report each effect as exp(beta), where beta is the "
                 "change in telomere length (SD) per unit increase in log-odds of the malignancy; put this value in "
                 "the 'or' field of the final JSON."),
    "files": {k: {"from": rel(v)} for k, v in rev_files.items()},
    "data_description": (
        f"exposure_*.tsv: case-control GWAS of haematologic malignancies in a European-ancestry population cohort "
        f"(controls exclude all cancer cases), restricted to variants with p < 1e-5. {CANCER_DESC}. These are raw "
        f"association results, not independent signals.\n{counts}\n"
        "outcome_telomere_length.tsv: a genome-wide association study of leukocyte telomere length in ~470,000 "
        "European-ancestry adults (log-transformed, standardised; beta in SD per effect allele), restricted to the "
        "variants in the exposure files. Columns: chr, pos_b37 (GRCh37), snp, other_allele, effect_allele, eaf, "
        "beta, se, p. Some exposure variants are missing.\n" + LD_DESC),
    "blocked_terms": BLOCKED,
}
for q in (q3, q3b):
    with open(f"{QDIR}/{q['id']}.json", "w") as f:
        json.dump(q, f, indent=2, ensure_ascii=False); f.write("\n")
print("wrote", f"{QDIR}/paper_3.json", f"{QDIR}/paper_3b.json")
