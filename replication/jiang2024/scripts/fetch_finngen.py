"""Stream FinnGen R9 summary stats (GRCh38) and keep only rows needed for MR:
  (a) variants whose rsID is in the TL p<5e-8 set (forward instruments + clumping flexibility), and
  (b) variants with p < 1e-5 (reverse-direction instruments, the paper's threshold).
Usage: python3 -I fetch_finngen.py <finngen_outcomes.tsv> <tl_sig_5e8.tsv> <out_dir>
"""
import csv, gzip, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
manifest, tl_path, out_dir = sys.argv[1:4]
tl = {r["snp"] for r in csv.DictReader(open(tl_path), delimiter="\t")}
BASE = "https://storage.googleapis.com/finngen-public-data-r9/summary_stats/finngen_R9_{}.gz"

def fetch(row):
    name, code = row["outcome"], row["phenocode"]
    out = f"{out_dir}/{name}.tsv"
    n = k = 0
    with urllib.request.urlopen(BASE.format(code), timeout=120) as r, \
         gzip.open(r, "rt") as f, open(out + ".part", "w") as o:
        header = f.readline()
        o.write(header.lstrip("#"))
        for line in f:
            n += 1
            c = line.split("\t", 8)
            if float(c[6]) < 1e-5 or any(x in tl for x in c[4].split(",")):
                o.write(line); k += 1
    import os; os.replace(out + ".part", out)
    return f"{name} ({code}): {n} read, {k} kept"

rows = list(csv.DictReader(open(manifest), delimiter="\t"))
with ThreadPoolExecutor(6) as ex:
    for msg in ex.map(fetch, rows):
        print(msg, flush=True)
