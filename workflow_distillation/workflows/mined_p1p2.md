# MR Workflow for Summary-Level Data (Wald ratio / IVW based)

Follow the stages in order. Items marked **[CRITICAL]** most often separated correct answers from wrong ones. Record every decision in a log table.

---

## Stage 0. Ground rules

1. Re-import every library and reload or recompute every data object at the top of every script. Assume each script runs in a fresh process. Save intermediate tables to disk (CSV) and reload them.
2. **[CRITICAL]** Report a result for **every outcome the question asks about**, even if it is underpowered, noisy or "unreliable". Never drop an outcome from the report. Label weak results "inconclusive" instead.
3. The primary estimator is IVW. Do not make weighted median or MR-Egger the primary estimate (see Stage 6).

---

## Stage 1. Inspect the files

For each file, record:
- Column names. The SNP ID column may differ between files (e.g. `snp` vs `variant_id`).
- Number of rows.
- Whether chromosome, position, allele frequency (EAF), beta and SE are present.

Then build a coverage table: exposure SNP × outcome file → present / absent / present under another ID.

For every outcome file, list:
- Exposure SNPs that are missing.
- Rows whose IDs are not in the exposure file. These are candidate proxies or aliases.

Check that the arithmetic closes. The number of missing exposure SNPs versus the number of extra rows tells you how many missing SNPs could possibly be proxied.

---

## Stage 2. Resolve SNP identity (aliases, proxies, duplicates)

Use chromosome:position plus alleles as the authoritative key, not the rsID alone.

1. **Alias.** Same chromosome, same position, same allele pair as an exposure SNP → treat it as the same SNP under a different ID. Use it.
2. **Redundant proxy.** A row a few kb from an exposure SNP that is already directly matched in the same file → **drop it**. Never count one locus twice.
3. **True proxy for a missing SNP.** A nearby, distinct SNP with no LD/phase information supplied:
   - Primary analysis: exclude it, because its phase is unverified.
   - Sensitivity analysis: include it.
   - Report both.
4. **Deduplication rule.** When a locus has both a direct match and a proxy, keep the direct match. After deduplicating, verify that the rows you kept are the original exposure SNPs, not the proxies.
5. Record the final instrument list for each outcome. Instrument sets may differ between outcomes; that is acceptable.

---

## Stage 3. Allele harmonisation **[CRITICAL]**

1. Harmonise **row by row, separately in each outcome file**. The same SNP can be coded with a different effect allele in different files.
2. For each row:
   - If outcome effect_allele == exposure effect (e.g. "increasing") allele → keep beta.
   - If outcome other_allele == exposure allele → beta = −beta, and EAF = 1 − EAF.
   - If neither allele matches, try the complement strand. If still no match → drop the SNP and log it.
3. Assert: zero unmatched rows and zero NaNs after harmonisation.
4. **Palindromic SNPs (A/T or C/G) [CRITICAL].**
   - Compare the harmonised EAF of the SNP across all outcome files, and against the exposure EAF if one is given.
   - If one file shows EAF ≈ 1 − (EAF in the other files), treat that file as strand-flipped. Reverse your letter-based flip decision for that file.
   - If EAF is near 0.5 (roughly 0.42–0.58), strand cannot be resolved. Exclude the SNP from the primary analysis.
   - **Always run the analysis with and without each palindromic SNP and report both.** In small instrument sets this single SNP can flip the direction of a null estimate.
5. Cross-file sanity check:
   - For every SNP, harmonised EAFs should agree across outcome files of the same ancestry (within about ±0.1).
   - Flag any SNP whose Wald ratio has the opposite sign in one outcome file versus closely related files. Re-check its alleles before calling it pleiotropy.

---

## Stage 4. Exposure SEs and instrument strength

1. If exposure SEs are missing, derive them from beta and p:
   - `z = scipy.stats.norm.isf(p/2)`
   - `SE = |beta| / z`
   - **Never** use `norm.ppf(1 − p/2)`. For p < about 1e-16 it returns inf, giving SE = 0.
2. Check that all derived SEs are finite and > 0.
3. Compute F = (beta/SE)² per SNP. Flag any SNP with F < 10.
4. Alternatively, ignore exposure SE entirely (the NOME approximation). That is acceptable. State which choice you made.

---

## Stage 5. LD / independence

1. Flag pairs on the same chromosome **within ~1 Mb**, or annotated to the same gene/locus.
   - Do NOT treat two SNPs as correlated just because they share a chromosome. Pairs tens of Mb apart are independent.
2. For each flagged pair:
   - Primary analysis: keep all SNPs.
   - Sensitivity analyses: drop the SNP with the larger p-value. Then drop the other one instead.
   - Report all of these.
   - Actually compare the p-values in code. Do not just pick by sort order.
   - If one SNP of the pair is absent from an outcome file, keep the other SNP for that outcome. Pruning is per outcome.
3. Optional: run a correlation-aware (GLS) IVW over assumed ρ values (e.g. 0, 0.3, 0.6, 0.9) as a bounding exercise.

---

## Stage 6. MR estimation **[CRITICAL — the most common source of wrong significance]**

For each outcome, with harmonised `bx` (exposure beta) and `by`, `se_y` (outcome beta and SE):

1. **Per-SNP Wald ratio:**
   - `ratio_j = by_j / bx_j`
   - `se_ratio_j = se_y_j / |bx_j|` (first order)
   - Optional second order: `sqrt(se_y²/bx² + by²·se_x²/bx⁴)`
2. **Fixed-effect IVW:**
   - `w_j = 1/se_ratio_j²` (this equals `bx_j²/se_y_j²`)
   - `β = Σ w·ratio / Σ w`. This is identical to `Σ(bx·by/se_y²) / Σ(bx²/se_y²)`; that regression formula is correct, not an error.
   - `SE = 1/sqrt(Σ w)`
   - **Wrong:** weights `1/se_y²` applied to ratios, or `SE = 1/sqrt(Σ 1/se_y²)`. This gives absurdly narrow CIs and false significance.
3. **Heterogeneity:**
   - `Q = Σ w(ratio − β)²`, with df = n − 1
   - p from `chi2.sf(Q, df)`. Do not use `1 − cdf`, which underflows.
   - `I² = max(0, (Q − df)/Q)`
4. **Random-effects IVW:**
   - `SE_RE = SE · sqrt(max(1, Q/df))`, with the same point estimate.
   - Pre-specify: if Q p < 0.05, the primary estimate is random-effects; otherwise fixed-effect. Report both.
5. **Sanity checks that would have caught the bugs:**
   - IVW SE must be ≥ (smallest `se_ratio_j`) / sqrt(n).
   - The CI on the OR scale should not be narrower than what individual SNPs allow. A CI like 1.57–1.60 from about 10 SNPs is a bug.
   - I² > 95% across all outcomes, including one whose SNP ratios look consistent, means your SE or weights are wrong.
   - p = 0 exactly means you must use `norm.logsf`, or report p < 1e-300.
6. **Sensitivity analyses (report; never primary):**
   - **Weighted median.** Weights = 1/se_ratio². Use a parametric bootstrap SE (≥ 10,000 draws) with a fixed seed. It can flip the sign of a near-null effect, so never use it as the headline.
   - **MR-Egger.** Regress `by` on `bx` with weights 1/se_y². Orient alleles so that bx > 0. Include an intercept. Use t-distribution CIs with df = n − 2.
     - Do NOT regress the ratio on bx.
     - With < 10 SNPs, describe it as underpowered. A non-significant intercept is not proof of no pleiotropy.
   - **Leave-one-out** IVW.
   - The palindromic-SNP exclusion, LD and proxy sensitivity analyses from Stages 2, 3 and 5.
7. Convert to the requested scale:
   - `OR = exp(β)`, CI = `exp(β ± 1.96·SE)`. Use t critical values if you choose the small-sample option; state which.
   - Check that the exposure unit matches the question (e.g. per 1 unit vs per SD). Rescale `bx` if needed.

---

## Stage 7. Multiple independent outcome datasets for the same phenotype

1. Analyse each dataset separately.
2. Then pool:
   - Meta-analyse the harmonised per-SNP outcome betas across datasets with fixed-effect inverse variance.
   - Check per-SNP between-study heterogeneity.
   - Run IVW once on the pooled per-SNP betas.
3. Report the separate and pooled results.
4. Pooling only helps if the per-study SEs are correct. If pooling turns two clearly null sets into "significant", re-check Stage 6.

---

## Stage 8. Subtype / outcome contrasts (if asked)

1. `z = (β1 − β2) / sqrt(SE1² + SE2²)`
2. Use the same estimator for both outcomes, e.g. RE vs RE.
3. Do not test a subtype against a combined outcome that contains it.
4. State the assumption that the two samples are independent (no shared controls).

---

## Stage 9. Interpretation and reporting

1. **Direction:**
   - OR > 1 → increased risk.
   - OR < 1 → decreased risk.
   - A CI that includes 1 → "no evidence of association". Still report the point estimate and its direction.
2. **Significance:** base it on the primary estimate. If fixed- and random-effects estimates disagree on significance, report both and name the primary one.
3. **Report table:** outcome, method, OR, 95% CI, p, N instruments. Include rows for:
   - primary analysis,
   - FE / RE,
   - weighted median,
   - MR-Egger,
   - with/without palindromic SNP,
   - with/without proxies,
   - LD sensitivity.
4. **Judgement calls to run both ways and report both:**
   - Palindromic SNP: included vs excluded, or strand-corrected.
   - Unphased proxies: included vs excluded.
   - Correlated same-locus SNPs: kept vs pruned.
   - Fixed- vs random-effects inference.
5. If the sign of an outcome's estimate changes across these choices, say so explicitly. Call that result fragile / inconclusive.
6. Cross-check every number in the write-up against the script output. Fix stale values left over from earlier buggy runs.
7. **Limitations to list:**
   - Derived exposure SEs.
   - LD not verified with a reference panel.
   - Heterogeneity.
   - Egger is underpowered.
   - Instrument attrition.
   - Multiple outcomes tested.
