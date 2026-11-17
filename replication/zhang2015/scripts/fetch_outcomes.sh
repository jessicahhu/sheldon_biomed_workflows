#!/bin/bash
# Stream McKay et al. 2017 (ILCCO/OncoArray) lung GWAS summary stats from the GWAS Catalog
# and keep only the TL instrument SNPs (Zhang 2015 Table 2, incl. the 2 excluded ones).
set -euo pipefail
OUT="$1"
B=https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST004001-GCST005000
SNPS='rs10936599|rs2736100|rs7726159|rs7675998|rs9420907|rs6772228|rs8105767|rs755017|rs412658|rs3027234|rs11125529'
for pair in GCST004748:lung_all GCST004744:lung_adeno GCST004750:lung_squam; do
  g=${pair%%:*}; name=${pair##*:}
  ( curl -s --retry 3 "$B/$g/${g}_buildGRCh37.tsv" | awk -v re="^($SNPS)$" 'NR==1 || $1 ~ re' > "$OUT/${name}_${g}.tsv" \
    && echo "$name done: $(($(wc -l < "$OUT/${name}_${g}.tsv")-1)) SNPs" ) &
done
wait
