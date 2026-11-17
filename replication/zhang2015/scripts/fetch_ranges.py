"""Pull specific SNP rows from a large position-sorted GWAS Catalog TSV over HTTP byte ranges
(binary search on chromosome, position), instead of downloading the full ~730 MB file.
Usage: python3 -I fetch_ranges.py <url> <out.tsv> chr:pos:rsid [chr:pos:rsid ...]
"""
import sys, urllib.request

url, out, targets = sys.argv[1], sys.argv[2], sys.argv[3:]
CHUNK = 64_000


def get(a, b):
    req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def size():
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def key_at(offset):
    """(chr, pos) of the first full line starting after offset."""
    lines = get(offset, offset + 4000).split("\n")[1:-1]
    f = lines[0].split("\t")
    return (int(f[CI]), int(f[PI]))


header = get(0, 2000).split("\n")[0]
cols = header.split("\t")
RI, CI, PI = cols.index("variant_id"), cols.index("chromosome"), cols.index("base_pair_location")
N = size()
rows = []
for t in targets:
    c, p, rsid = t.split(":"); target = (int(c), int(p))
    lo, hi = 0, N - 5000
    while hi - lo > CHUNK // 2:
        mid = (lo + hi) // 2
        if key_at(mid) < target:
            lo = mid
        else:
            hi = mid
    block = get(max(0, lo - CHUNK), lo + CHUNK)
    hit = [l for l in block.split("\n") if len(l.split("\t")) > RI and l.split("\t")[RI] == rsid]
    if not hit:  # fall back to matching on position (rsid naming can differ)
        hit = [l for l in block.split("\n")[1:-1]
               if len(l.split("\t")) > PI and (l.split("\t")[CI], l.split("\t")[PI]) == (c, p)]
    print(f"{rsid}: {'found' if hit else 'NOT FOUND'}", file=sys.stderr)
    rows += hit[:1]

with open(out, "w") as fh:
    fh.write(header + "\n" + "\n".join(rows) + "\n")
