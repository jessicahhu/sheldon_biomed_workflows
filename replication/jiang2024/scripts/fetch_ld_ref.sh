#!/bin/bash
# Download the MRC-IEU 1000G LD reference (1kg.v3.tgz, 1.57 GB) in parallel byte ranges (server is ~35 KB/s per connection)
# and keep only the EUR plink files. Usage: fetch_ld_ref.sh <out_dir> [n_parts]
set -euo pipefail
OUT=$1; N=${2:-12}; URL=http://fileserve.mrcieu.ac.uk/ld/1kg.v3.tgz
SIZE=$(curl -sI $URL | awk 'tolower($1)=="content-length:"{print $2+0}')
CH=$(( (SIZE + N - 1) / N )); mkdir -p "$OUT/parts"
for i in $(seq 0 $((N-1))); do
  a=$((i*CH)); b=$(( (i+1)*CH - 1 )); [ $b -ge $SIZE ] && b=$((SIZE-1))
  ( until [ -f "$OUT/parts/$i" ] && [ $(stat -f %z "$OUT/parts/$i") -eq $((b-a+1)) ]; do
      curl -s --retry 5 -r $a-$b -o "$OUT/parts/$i" $URL || sleep 5; done ) &
done
wait
cat $(for i in $(seq 0 $((N-1))); do echo "$OUT/parts/$i"; done) > "$OUT/1kg.v3.tgz"
[ $(stat -f %z "$OUT/1kg.v3.tgz") -eq $SIZE ] && rm -r "$OUT/parts"
tar -xzf "$OUT/1kg.v3.tgz" -C "$OUT" EUR.bed EUR.bim EUR.fam && rm "$OUT/1kg.v3.tgz"
ls -la "$OUT"
