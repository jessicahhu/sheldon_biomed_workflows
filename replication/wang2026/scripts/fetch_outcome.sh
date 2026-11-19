#!/bin/bash
# Pull the instrument SNPs from the McKay 2017 overall lung cancer GWAS (GCST004748, ~730 MB, GRCh37)
# using HTTP byte-range binary search (fetch_ranges.py), one background job per drug.
# Usage: bash fetch_outcome.sh <instrument_dir> <raw_dir>
set -euo pipefail
INST="$1"; RAW="$2"; mkdir -p "$RAW"
URL=https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST004001-GCST005000/GCST004748/GCST004748_buildGRCh37.tsv
HERE=$(cd "$(dirname "$0")" && pwd)
for f in "$INST"/instruments_*.tsv; do
  name=$(basename "$f" .tsv); name=${name#instruments_}
  targets=$(awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)h[$i]=i; next}{print $h["chr37"]":"$h["pos37"]":"$h["rsid"]}' "$f")
  ( python3 -I "$HERE/fetch_ranges.py" "$URL" "$RAW/lung_all_$name.tsv" $targets 2> "$RAW/lung_all_$name.log" \
    && echo "$name: $(grep -c found "$RAW/lung_all_$name.log") requested, $(grep -c 'NOT FOUND' "$RAW/lung_all_$name.log") not found" ) &
done
wait
