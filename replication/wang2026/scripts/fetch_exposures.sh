#!/bin/bash
# Stream the six UK Biobank drug-use GWAS (GWAS Catalog harmonised files, GRCh38; ~380 MB gz each)
# and keep only rows with P < 5e-6 (the most lenient threshold Wang 2026 used).
# Also writes the 1000 Genomes EUR sample list used for LD clumping.
# Usage: bash fetch_exposures.sh <exposure_dir> <ld_dir>
set -euo pipefail
OUT="$1"; LD="$2"; mkdir -p "$OUT" "$LD"
B=https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90018001-GCST90019000
for g in GCST90018995 GCST90018994 GCST90018982 GCST90018990 GCST90018989 GCST90018981; do
  ( curl -s --retry 3 "$B/$g/harmonised/$g.h.tsv.gz" | gunzip -c \
      | awk -F'\t' 'NR==1 || ($8!="NA" && $8+0 < 5e-6)' > "$OUT/$g.p5e6.tsv" \
    && echo "$g: $(($(wc -l < "$OUT/$g.p5e6.tsv")-1)) rows with P<5e-6" ) &
done
curl -s https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/integrated_call_samples_v3.20130502.ALL.panel \
  | awk '$3=="EUR"{print $1}' > "$LD/eur.txt"
wait
