"""Build the two data files the blind agent gets for the Wang 2026 question (paper_3).

  exposure_drug_use_instruments.tsv  one row per (drug, instrument SNP): the instruments built by
                                     build_instruments.py, with neutral drug names and GRCh37 positions
  outcome_lung_cancer.tsv            lung cancer GWAS rows for every instrument SNP (all drugs), as fetched
                                     by fetch_outcome.sh

The agent gets the instruments ready-made (as for papers 1-2, where the exposure SNP list was given):
clumping needs an LD reference panel that the sandbox cannot reach.

Usage: python3 make_agent_files.py <instrument_dir> <outcome_raw_dir> <out_dir>
"""
import os, sys
import pandas as pd

inst_dir, raw_dir, out_dir = sys.argv[1:4]
NAMES = {"salicylic_acid": "salicylic_acid_and_derivatives", "opioids": "opioids",
         "antithrombotic": "antithrombotic_agents", "thyroid": "thyroid_preparations",
         "statins": "hmg_coa_reductase_inhibitors", "diabetes_drugs": "drugs_used_in_diabetes"}
os.makedirs(out_dir, exist_ok=True)
ex, out = [], []
for name, label in NAMES.items():
    d = pd.read_csv(os.path.join(inst_dir, f"instruments_{name}.tsv"), sep="\t")
    ex.append(pd.DataFrame({"drug": label, "rsid": d.rsid, "chromosome": d.chr37, "position_grch37": d.pos37,
                            "effect_allele": d.effect_allele, "other_allele": d.other_allele, "beta": d.beta,
                            "standard_error": d.standard_error, "effect_allele_frequency": d.effect_allele_frequency,
                            "p_value": d.p_value}))
    out.append(pd.read_csv(os.path.join(raw_dir, f"lung_all_{name}.tsv"), sep="\t"))
ex = pd.concat(ex)
out = pd.concat(out).drop_duplicates("variant_id").sort_values(["chromosome", "base_pair_location"])
ex.to_csv(os.path.join(out_dir, "exposure_drug_use_instruments.tsv"), sep="\t", index=False)
out.to_csv(os.path.join(out_dir, "outcome_lung_cancer.tsv"), sep="\t", index=False)
print(ex.groupby("drug", sort=False).size().to_string())
print(f"outcome rows: {len(out)} of {ex.rsid.nunique()} unique instrument SNPs")
