"""Extract genome-wide significant variants (p < 5e-8, i.e. -log10 p > 7.30103) from the
OpenGWAS ieu-b-4879 VCF (telomere length, UK Biobank, Codd 2021; GRCh37; effect in SD units).
Usage: python3 -I extract_tl_sig.py <ieu-b-4879.vcf.gz> <out.tsv>
"""
import gzip, sys
vcf, out = sys.argv[1:3]
THR = 7.30103
n = kept = 0
with gzip.open(vcf, "rt") as f, open(out, "w") as o:
    o.write("chr\tpos\tsnp\tother_allele\teffect_allele\teaf\tbeta\tse\tp\tn\n")
    for line in f:
        if line[0] == "#":
            continue
        n += 1
        c = line.rstrip("\n").split("\t")
        vals = dict(zip(c[8].split(":"), c[9].split(":")))
        lp = float(vals["LP"])
        if lp <= THR:
            continue
        kept += 1
        o.write("\t".join([c[0], c[1], c[2], c[3], c[4], vals["AF"], vals["ES"], vals["SE"],
                           f"{10**-lp:.3e}", vals.get("SS", "472174")]) + "\n")
print(f"{n} variants read, {kept} with p < 5e-8")
