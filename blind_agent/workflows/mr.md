# Workflow: two-sample Mendelian randomization with summary statistics

Work through the stages below in order. Each stage lists **steps**, the **checks** you must run, and
what to **record**. In your report's Methodology section, label each numbered step with its stage
(e.g. "Stage 6 – Harmonise"). Every claim in your Conclusion must cite the stage(s) it rests on.

Keep a **decision log** as you go: every SNP you drop, replace or flip, and every method choice,
with the reason. If a check fails and you can't resolve it, don't guess. Drop the SNP (or the
analysis), say so, and show the result with and without it.

---

## Stage 1 – Frame the question

**Steps**
1. State the exposure, each outcome (including any subtypes), and the effect scale requested
   (e.g. odds ratio per 1 unit of exposure).
2. List the outcome datasets you will analyse and say which ones measure the same phenotype.

**Record:** exposure, outcomes, effect scale, and the populations the data come from.

---

## Stage 2 – Inspect the data

**Steps**
1. Load every file. Print its columns, number of rows and the first rows.
2. For each file, identify: SNP ID, chromosome, position, effect allele, other allele, effect
   allele frequency (EAF), beta (or OR), standard error, p-value, sample size.
3. Note what is missing (e.g. no exposure standard errors, no EAF, no LD information).

**Checks**
- Betas are on the scale you expect (log-odds for case-control outcomes; if only OR is given,
  beta = ln(OR)).
- Every SNP ID is unique within each file.

**Record:** a table of files × available fields, and every missing field.

---

## Stage 3 – Select instruments

**Steps**
1. Start from the exposure SNPs. Keep those with p < 5×10⁻⁸.
2. **Independence (LD).** Instruments must be independent.
   - If LD information (r²) is provided, keep SNPs with pairwise r² < 0.01 (keep the one with the
     smaller exposure p-value from each correlated pair).
   - If no LD information is provided, treat SNPs on the same chromosome within 1 Mb of each
     other, or annotated to the same locus or gene region, as correlated, and keep only the one
     with the smallest exposure p-value. Do this **before** looking at outcome data, so the choice
     can't be driven by the results.
3. Record the final instrument list. It must be the same for every outcome, except where an
   instrument is missing from an outcome file (Stage 5).

**Checks**
- No two instruments share a locus.
- Your choices didn't depend on the outcome results.

**Record:** each SNP considered, kept or dropped, and why.

---

## Stage 4 – Instrument strength

**Steps**
1. If exposure standard errors are missing, back-derive them from the p-value:
   SE = |beta| / z, where z = Φ⁻¹(1 − p/2). For very small p, compute z with a log-scale function
   (e.g. `scipy.stats.norm.isf(p/2)`) so it doesn't underflow.
2. Compute the per-SNP F-statistic, F = (beta / SE)², and the mean F across instruments.

**Checks**
- Flag any SNP with F < 10 as weak; run a sensitivity analysis without it.

**Record:** F per SNP and mean F; how exposure SEs were obtained.

---

## Stage 5 – Extract outcome associations

**Steps**
1. For each outcome file, look up every instrument by rsID.
2. If an rsID is not found, check whether the same chromosome and position appears under a
   different rsID (a renamed or merged rsID). If so, and the alleles match, it is the same SNP.
3. **Proxies.** If an instrument is truly absent, you may use a proxy SNP only if:
   - r² ≥ 0.8 with the instrument is given in the data or documentation; **or**, if the data
     description says proxies are included but gives no r², the candidate is within 50 kb of
     the missing instrument, is not closer to another instrument, and maps to no locus already
     represented.
   - Never choose a proxy only because it is nearby or has a similar frequency.
   - If no valid proxy exists, drop the instrument for that outcome and record it.
4. If several outcome datasets measure the same phenotype, harmonise each separately (Stage 6),
   then combine them per SNP by fixed-effect inverse-variance meta-analysis before MR. Report the
   per-dataset MR results too.

**Checks**
- Each instrument maps to exactly one outcome row per file.
- Every proxy is listed with its justification.

**Record:** for each outcome, which instruments were found directly, by position, by proxy, or
were missing.

---

## Stage 6 – Harmonise alleles

Align every outcome beta so it refers to the exposure-increasing allele.

**Steps**
1. **Non-palindromic SNPs** (alleles not A/T or C/G): if the outcome effect allele equals the
   exposure-increasing allele, keep the beta; if it equals the other allele, flip the sign. If
   neither allele matches, try the complementary strand (A↔T, C↔G); if it still doesn't match,
   drop the SNP.
2. **Palindromic SNPs (A/T or C/G).** The allele letters can't tell you the strand, so use
   allele frequencies:
   - If the minor allele frequency is > 0.42, the strand can't be inferred reliably. Drop it.
   - If the exposure EAF is available, align so the EAFs are on the same side of 0.5.
   - If the exposure EAF is not available, compare the EAF of the same letter **across all
     outcome files**. If the same letter is the minor allele in some files and the major allele
     in others, those files are on opposite strands. Align each file to the strand used by the
     majority of files, and say so.
   - Always run a sensitivity analysis excluding palindromic SNPs.
3. Never assume a SNP is non-palindromic. Check the allele letters for every SNP and list the
   palindromic ones explicitly.

**Checks**
- For non-palindromic SNPs, the outcome EAF of the aligned allele should be consistent across
  outcome files. A big inconsistency (e.g. 0.05 vs 0.95) means a strand or allele error. Fix
  it or drop the SNP.
- Print the final harmonised table: SNP, exposure beta, aligned outcome beta, outcome SE, and
  whether it was flipped.

**Record:** the harmonised table and every flip, with the reason.

---

## Stage 7 – Primary estimate

**Steps**
1. Compute per-SNP Wald ratios: beta_outcome / beta_exposure, with SE ≈ SE_outcome / |beta_exposure|.
2. Primary estimate: inverse-variance-weighted (IVW) estimate.
   - Report the fixed-effect IVW.
   - Also report the multiplicative random-effects IVW, with the SE scaled by √(Q/df) when Q/df > 1.
   - State which one you treat as primary and why.
3. Convert to the requested scale (e.g. OR = exp(beta)) with 95% CI and p-value.

**Checks**
- Cochran's Q, its p-value and I² for every outcome.
- Number of instruments per outcome.

**Record:** estimates, CIs, p-values, Q, I², n instruments.

---

## Stage 8 – Sensitivity analyses

Run all of these for every outcome:
1. **Weighted median.** Bootstrap its SE.
2. **MR-Egger.** Report the slope and the intercept (directional pleiotropy test), and note its
   low power with few instruments.
3. **Leave-one-out IVW.** Flag any SNP whose removal moves the estimate across the null or
   changes it by > 20%.
4. **Outlier check.** Identify SNPs that contribute most to Q. If one or more stand out, report
   IVW without them as a sensitivity result. **Do not replace the primary estimate with it.**
5. **Excluding palindromic SNPs and proxies** (from Stages 5–6).

**Checks**
- Do all methods agree in direction?
- Does significance survive the sensitivity analyses?

**Record:** a table of every sensitivity estimate; one sentence on whether the primary result is
robust.

---

## Stage 9 – Interpret

**Steps**
1. For each outcome, give the direction (increased risk / decreased risk / null), the size of the
   effect, and the significance, based on the primary estimate (Stage 7).
2. Compare outcomes. If they differ (e.g. by subtype), say whether the confidence intervals
   overlap.
3. List the MR assumptions and how well each one holds here:
   - relevance (Stage 4),
   - independence (Stage 3),
   - exclusion restriction / pleiotropy (Stage 8).

**Record:** the answer to the question, with the stage(s) supporting each claim.

---

## Stage 10 – Report

Use the report headings required in your instructions:
- **Results:** every estimate from Stages 7–8 in one table.
- **Methodology:** numbered steps labelled by stage, including the decision log.
- **Conclusion:** the answer to the question, with stage citations, then limitations. Always
  cover:
  - missing exposure SEs,
  - unverified LD,
  - proxies and palindromic SNPs,
  - heterogeneity,
  - sample size,
  - ancestry.
- **Final answer (JSON):** use the primary estimate from Stage 7 for each outcome.
