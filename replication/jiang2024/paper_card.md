# Paper card: jiang2024_tl_heme

| Field | Value |
|---|---|
| paper_id | jiang2024_tl_heme |
| citation | Jiang G, Cao L, Wang Y, Li L, Wang Z, Zhao H, Qiu Y, Feng B. Causality between telomere length and the risk of hematologic malignancies: a bidirectional Mendelian randomization study. *Cancer Res Commun* 2024;4(10):2815–2822. doi:10.1158/2767-9764.CRC-24-0402, PMC11513617 |
| exposure | Leukocyte TL (qPCR T/S ratio, log-transformed and Z-standardised), UK Biobank GWAS (Codd 2021), OpenGWAS `ieu-b-4879` |
| exposure_scale | Per 1 SD longer TL (forward). Reverse: per unit log-odds of cancer liability, outcome TL in SD |
| outcomes | FinnGen **R9** (identified by matching Supp. Table S1 case/control counts against the R9 manifest): all lymphoid and haematopoietic malignancies, AML, CML, ALL, CLL, leukaemia of unspecified type, multiple myeloma, Hodgkin, NHL, plus 8 NHL subtypes. UKB leukaemia replication (Supp. Table S4) |
| population | European. Exposure UK Biobank (n=472,174); outcomes Finnish (FinnGen R9) |
| sample_sizes | See table below; cases range from 87 (Waldenström) to 7,519 (all lymphoid/haematopoietic) |
| design | Two-sample bidirectional summary-data MR |
| data_public | **Yes.** `ieu-b-4879` VCF from OpenGWAS (needs free login); FinnGen R9 public bucket (no login) |
| code_public | Absent (TwoSampleMR 0.6.4, R 4.3.1) |
| headline_claim | Longer TL raises risk of lymphoid malignancies (ALL, CLL, myeloma, Hodgkin, NHL and several NHL subtypes), not myeloid (AML, CML); no reverse effect of any malignancy on TL. |

### Outcome map (FinnGen R9)

| Outcome | Phenocode | Cases / controls |
|---|---|---|
| All lymphoid and haematopoietic | CD2_PRIMARY_LYMPHOID_HEMATOPOIETIC_EXALLC | 7,519 / 299,952 (paper says 7,915; see note) |
| AML | C3_AML_EXALLC | 231 / 287,136 |
| CML | CML | 232 / 375,158 |
| ALL | C3_ALL_EXALLC | 184 / 287,136 |
| CLL | C3_CLL_EXALLC | 624 / 287,133 |
| Leukaemia, unspecified | CD2_LEUKAEMIA_NAS_EXALLC | 220 / 299,952 |
| Multiple myeloma | CD2_MULTIPLE_MYELOMA_PLASMA_CELL_EXALLC | 1,249 / 299,952 |
| NHL | C3_NONHODGKIN_EXALLC | 928 / 287,137 |
| Hodgkin | CD2_HODGKIN_LYMPHOMA_EXALLC | 780 / 299,952 |
| Follicular | CD2_FOLLICULAR_LYMPHOMA_EXALLC | 1,081 / 299,952 |
| Non-follicular | CD2_NONFOLLICULAR_LYMPHOMA_EXALLC | 2,602 / 299,952 |
| DLBCL | C3_DLBCL_EXALLC | 1,010 / 287,137 |
| Waldenström | C3_MACROGLOBULINEMIA_EXALLC | 87 / 287,137 |
| Mantle cell | C3_MANTLE_CELL_LYMPHOMA_EXALLC | 199 / 287,137 |
| Marginal zone | C3_MARGINAL_ZONE_LYMPHOMA_EXALLC | 192 / 287,137 |
| Mature T/NK | CD2_TNK_LYMPHOMA_EXALLC | 335 / 299,952 |
| Other/unspecified NHL | CD2_NONHODGKIN_NAS_EXALLC | 1,088 / 299,952 |

Supp. Table S1 lists 7,915 cases for the combined outcome. No FinnGen release has 7,915 (R8 6,610; R9 7,519; R10 8,163), and the R9 control count matches exactly, so 7,915 is a digit-swap typo for 7,519.

## Stage-by-stage decisions (what the paper did)

| # | Stage | Jiang 2024 |
|---|---|---|
| 1 | Frame | Bidirectional: TL → 17 haematologic outcomes, and each outcome → TL. OR per SD TL |
| 2 | Data sources | TL: `ieu-b-4879` (UKB, 472,174 European). Outcomes: FinnGen R9, "controls excluding all cancers" endpoints. Replication: UKB leukaemia/lymphoid/myeloid on OpenGWAS (linear-probability betas, OR ≈ 1.00x) |
| 3 | Select instruments | Forward: p<5e-8, clump r²<0.001 within 10,000 kb (1000G EUR). Reverse: p<1e-5, same clumping. Drop SNPs with outcome p<5e-8. PhenoScanner v2 to remove SNPs associated with confounding traits (which traits/SNPs not reported) |
| 4 | Instrument strength | F>10 kept, F<10 dropped (per-SNP F; values not reported) |
| 5 | Extract outcome | Not described; nSNP 108–118 across outcomes, so some instruments missing per outcome |
| 6 | Harmonise | "Eliminate strand mismatches"; presumably TwoSampleMR `harmonise_data` defaults (action=2: palindromes with MAF>0.42 dropped) |
| 7 | Primary estimate | IVW (TwoSampleMR; multiplicative random effects with ≥4 SNPs) |
| 8 | Sensitivity | MR-Egger, weighted median, Cochran's Q, Egger intercept, MR-PRESSO global test, leave-one-out, funnel plots |
| 9 | Adjust/decompose | None. No multiple-testing correction (nominal p<0.05 called significant across 17 outcomes) |
| 10 | Report & conclude | Lymphoid malignancies causal, myeloid not; reverse null |

## Ground truth

### Forward: TL → outcome (Tables 1–2), OR per SD longer TL

| Outcome | nSNP | IVW | P | WM | MR-Egger | Q p (IVW) | Egger int. p | PRESSO p |
|---|---|---|---|---|---|---|---|---|
| All lymphoid/haematopoietic | 116 | **1.651 (1.383–1.970)** | 2.69e-8 | 1.917 (1.518–2.420) | 2.083 (1.533–2.829) | <0.001 | 0.073 | 0.008 |
| AML | 112 | 1.488 (0.608–3.640) | 0.384 | 1.746 (0.436–6.991) | 0.546 (0.102–2.924) | 0.307 | 0.170 | 0.297 |
| CML | 115 | 1.583 (0.638–3.930) | 0.322 | 2.938 (0.761–11.345) | 1.318 (0.239–7.273) | 0.106 | 0.804 | 0.112 |
| ALL | 115 | **2.690 (1.040–6.956)** | 0.041 | 2.369 (0.545–10.289) | 10.901 (1.842–64.516) | 0.692 | 0.071 | 0.713 |
| CLL | 115 | **2.155 (1.265–3.671)** | 0.005 | 1.813 (0.819–4.015) | 2.479 (0.884–6.953) | 0.950 | 0.756 | 0.956 |
| Leukaemia, unspecified | 114 | **2.779 (1.164–6.631)** | 0.021 | 4.209 (1.057–16.766) | 1.844 (0.360–9.453) | 0.887 | 0.562 | 0.882 |
| Multiple myeloma | 117 | **1.845 (1.083–3.142)** | 0.024 | 2.661 (1.145–6.187) | 4.001 (1.546–10.352) | 0.198 | 0.058 | 0.191 |
| Hodgkin | 118 | **1.697 (1.115–2.583)** | 0.014 | 1.337 (0.696–2.566) | 1.506 (0.730–3.107) | 0.336 | 0.691 | 0.344 |
| NHL | 117 | **1.737 (1.145–2.636)** | 0.009 | 2.658 (1.323–5.341) | 2.177 (1.064–4.457) | 0.061 | 0.449 | 0.058 |
| Follicular | 108 | 1.358 (0.894–2.062) | 0.151 | 1.439 (0.749–2.763) | 1.132 (0.550–2.333) | 0.073 | 0.547 | 0.083 |
| Non-follicular | 110 | **1.583 (1.243–2.016)** | 1.98e-4 | 1.666 (1.138–2.439) | 1.825 (1.198–2.781) | 0.737 | 0.419 | 0.722 |
| DLBCL | 109 | **1.599 (1.086–2.354)** | 0.017 | 1.750 (0.947–3.234) | 2.129 (1.089–4.163) | 0.789 | 0.309 | 0.807 |
| Waldenström | 110 | **8.940 (2.165–36.922)** | 0.002 | 6.529 (0.842–50.606) | 10.264 (0.861–122.364) | 0.077 | 0.894 | 0.075 |
| Mantle cell | 110 | **2.874 (1.209–6.835)** | 0.017 | 1.582 (0.360–6.956) | 1.608 (0.357–7.256) | 0.743 | 0.358 | 0.743 |
| Marginal zone | 109 | 0.809 (0.321–2.038) | 0.653 | 0.864 (0.190–3.916) | 1.110 (0.222–5.559) | 0.243 | 0.639 | 0.250 |
| Mature T/NK | 110 | 0.517 (0.262–1.019) | 0.057 | 0.709 (0.240–2.097) | 1.391 (0.434–4.460) | 0.382 | 0.044 | 0.379 |
| Other/unspecified NHL | 110 | **1.603 (1.105–2.325)** | 0.013 | 1.349 (0.731–2.490) | 1.387 (0.726–2.651) | 0.915 | 0.594 | 0.915 |

Table 2's mantle cell and T/NK rows have their heterogeneity/PRESSO columns shifted in the source layout; the values above are read in column order and should be treated as approximate.

### Reverse: outcome → TL (Supp. Tables S2–S3), IVW "OR" (exp of beta on TL SD)

| Exposure | nSNP | IVW | P |
|---|---|---|---|
| All lymphoid/haematopoietic | 29 | 0.998 (0.989–1.008) | 0.725 |
| AML | 9 | 1.000 (0.996–1.004) | 0.943 |
| CML | 4 | 1.004 (0.997–1.011) | 0.241 |
| ALL | 6 | 1.000 (0.996–1.004) | 0.995 |
| CLL | 36 | 1.000 (0.998–1.003) | 0.782 |
| Leukaemia, unspecified | 4 | 1.000 (0.996–1.005) | 0.857 |
| Multiple myeloma | 15 | 0.999 (0.996–1.002) | 0.674 |
| Hodgkin | 14 | 1.003 (0.999–1.007) | 0.171 |
| NHL | 15 | 1.002 (0.996–1.007) | 0.526 |
| Follicular | 24 | 1.000 (0.997–1.003) | 0.929 |
| Non-follicular | 19 | 1.000 (0.993–1.007) | 0.977 |
| DLBCL | 11 | 0.999 (0.993–1.005) | 0.788 |
| Waldenström | 0 | no instruments | — |
| Mantle cell | 5 | 0.999 (0.995–1.003) | 0.586 |
| Marginal zone | 4 | 0.996 (0.992–1.001) | 0.092 |
| Mature T/NK | 5 | 1.000 (0.994–1.006) | 0.990 |
| Other/unspecified NHL | 14 | 0.997 (0.993–1.002) | 0.264 |

Odd features of the reverse analysis: CLL has 36 instruments at p<1e-5 but 6–9 for other leukaemias with similar case counts. The paper does not say whether the p<5e-8 "outcome-associated SNP" exclusion and the PhenoScanner filter (here: SNPs associated with TL) were applied to reverse instruments.

## Replication (2026-11-19; full log in results/run_log.txt)

Pipeline: `extract_tl_sig.py` (VCF → 38,506 rows / 37,958 unique rsIDs at p<5e-8) → `fetch_finngen.py` (17 R9 files, kept TL-significant rsIDs or p<1e-5) → `fetch_ld_ref.sh` (MRC-IEU 1000G EUR, 503 samples, autosomes) → `mr_jiang.py` (PLINK 1.9 clumping, harmonise, MR). Runtime about 1 min after downloads.

**Score: forward direction 16/17, significance 17/17, published OR inside our CI 16/17. Reverse significance 15/16, plus Waldenström not estimable in both.**

### Forward (IVW, OR per SD longer TL)

| Outcome | Published IVW | Replicated IVW | Direction | Significance | Published OR in our CI |
|---|---|---|---|---|---|
| All lymphoid/haematopoietic | 1.65 (1.38–1.97), P=2.7e-08 | **1.48 (1.26–1.75)**, P=3.4e-06 | ✓ | ✓ | ✓ |
| AML | 1.49 (0.61–3.64), P=0.38 | **1.95 (0.91–4.15)**, P=0.084 | ✓ | ✓ | ✓ |
| CML | 1.58 (0.64–3.93), P=0.32 | **1.29 (0.63–2.64)**, P=0.48 | ✓ | ✓ | ✓ |
| ALL | 2.69 (1.04–6.96), P=0.041 | **2.64 (1.23–5.69)**, P=0.013 | ✓ | ✓ | ✓ |
| CLL | 2.15 (1.26–3.67), P=0.005 | **3.63 (2.40–5.51)**, P=1.3e-09 | ✓ | ✓ | ✗ |
| Leukaemia, unspecified | 2.78 (1.16–6.63), P=0.021 | **2.10 (1.05–4.22)**, P=0.036 | ✓ | ✓ | ✓ |
| Multiple myeloma | 1.84 (1.08–3.14), P=0.024 | **1.70 (1.21–2.38)**, P=0.002 | ✓ | ✓ | ✓ |
| NHL | 1.74 (1.15–2.64), P=0.009 | **1.73 (1.20–2.51)**, P=0.0036 | ✓ | ✓ | ✓ |
| Hodgkin | 1.70 (1.11–2.58), P=0.014 | **1.74 (1.19–2.53)**, P=0.0041 | ✓ | ✓ | ✓ |
| Follicular | 1.36 (0.89–2.06), P=0.15 | **1.08 (0.73–1.61)**, P=0.70 | ✓ | ✓ | ✓ |
| Non-follicular | 1.58 (1.24–2.02), P=0.0002 | **1.59 (1.27–1.99)**, P=4.4e-05 | ✓ | ✓ | ✓ |
| DLBCL | 1.60 (1.09–2.35), P=0.017 | **1.46 (1.04–2.07)**, P=0.030 | ✓ | ✓ | ✓ |
| Waldenström | 8.94 (2.17–36.92), P=0.002 | **12.09 (3.47–42.13)**, P=9.1e-05 | ✓ | ✓ | ✓ |
| Mantle cell | 2.87 (1.21–6.83), P=0.017 | **3.57 (1.71–7.47)**, P=0.00073 | ✓ | ✓ | ✓ |
| Marginal zone | 0.81 (0.32–2.04), P=0.65 | **1.18 (0.55–2.55)**, P=0.67 | ✗ (both null) | ✓ | ✓ |
| Mature T/NK | 0.52 (0.26–1.02), P=0.057 | **0.71 (0.40–1.27)**, P=0.25 | ✓ | ✓ | ✓ |
| Other/unspecified NHL | 1.60 (1.10–2.33), P=0.013 | **1.71 (1.24–2.34)**, P=0.00094 | ✓ | ✓ | ✓ |

### Reverse (IVW, exp(beta) on TL SD)

All null as published (IVW p 0.13–0.99), except **NHL: 0.996 (0.991–1.000), P=0.048** vs published 1.002, P=0.53. That is borderline and in the opposite direction from a meaningful effect. Instrument counts after clumping are close to the paper's (e.g. AML 9 vs 9, CML 4 vs 4, ALL 6 vs 6, CLL 35 vs 36, mantle 5 vs 5). Waldenström: 1 SNP, not estimable (paper: 0).

### Decisions logged
- **Instrument count: 139 vs the paper's 108–118.** Clumping gave 150 TL instruments (min F=29.9); 8 are absent from FinnGen R9 and 3 are palindromic with MAF>0.42. The extra ~25 relative to the paper are most likely the SNPs removed by PhenoScanner, which we can't reproduce. The paper's per-outcome counts vary (108–118) while ours are constant at 139, so it also dropped outcome-specific SNPs in a way it doesn't describe.
- **chrX:** none of the TL chrX hits survive, because the reference panel is autosomal (same as the OpenGWAS clumping API).
- **CLL is the one estimate outside the published CI** (3.63 vs 2.16). MR-Egger intercept p=0.024 suggests pleiotropy among the extra instruments; PhenoScanner would plausibly remove SNPs associated with lymphocyte traits. Still significant and same direction.
- **Combined outcome** uses R9's 7,519 cases (supplement's 7,915 treated as a typo; see above).
- **Variant counts** match Supp. Table S1 exactly for most outcomes. Myeloma and CML differ by a few thousand of 20.17M, probably a different file version; instruments unaffected.
- **No proxies** were used for the 8 TL instruments missing from FinnGen.

## Blind agent runs (2026-11-19, Claude Sonnet 5, one run per condition)

Questions: `blind_agent/questions/paper_3.json` (forward) and `paper_3b.json` (reverse), built by `scripts/make_agent_files.py`. The agent gets unclumped instruments (forward: 38,506 TL variants at p<5e-8; reverse: each cancer at p<1e-5), the outcome GWAS restricted to those variants, and 1000G EUR reference genotypes (503 people) to compute LD itself. Leak check: 0 hits. Scored with `scripts/score_agent.py` against this replication (primary target, because the paper's PhenoScanner step can't be reproduced) and the paper. Full per-outcome tables: `results/agent_scores.md`. Run folders (git-ignored): `blind_agent/runs/paper_3*/claude-sonnet-5_{baseline,mr}_20261119-*`.

| Question | Condition | Steps | Clumping | Instruments used | Direction vs rep | Significance vs rep | Significance vs paper |
|---|---|---|---|---|---|---|---|
| paper_3 | Baseline | 24 | r²≥0.001 within 10 Mb; variants missing from the LD panel **excluded** | 147 → 139 | 17/17 | **17/17** | **17/17** |
| paper_3 | Workflow | 47 | r²≥0.01 within 1 Mb; variants missing from panel clumped by distance only | 231 → 156 | 15/17 | 10/17 | 10/17 |
| paper_3b | Baseline | 24 | r²≥0.01 within 1 Mb, at p<1e-5; no-LD pairs treated as dependent | 8–58 | n/a | **13/16** | **14/16** |
| paper_3b | Workflow | 50 | Re-thresholded to p<5e-8, then r²≥0.01 within 1 Mb | 0–6 (8 cancers none) | n/a | 4/16 (8 not estimated) | 4/16 (8 not estimated) |

### Agent decisions and errors by stage

| Stage | Baseline | Workflow |
|---|---|---|
| 2 Inspect | Found GRCh37/38 mismatch → matched on rsID; split multi-rsID rows. Both directions | Same, both directions |
| 3 Select | Forward: correct, conservative (dropped unverifiable SNPs). Reverse: loose clumping, HLA region over-represented | Followed `mr.md`: p<5e-8 cut removed most reverse data; r²<0.01 / 1 Mb distance fallback admitted ~80 extra forward instruments that couldn't be checked for LD |
| 5 Extract | No proxies | Forward used 1 proxy (r²=0.99, from genotypes; valid) |
| 6 Harmonise | Forward: palindromes checked by EAF. Reverse: letters only (no visible harm) | Palindromes MAF>0.42 dropped; sensitivity analysis without palindromes |
| 3/8 Outcome-associated instruments | Reverse kept TERC rs1317082 (TL p≈0); named it as an exclusion-restriction violation but didn't drop it → false positives DLBCL (p=0.0095), non-follicular (p=0.011) | Single-SNP Wald ratios reported as significant: DLBCL and other NHL p=9.5e-17, Hodgkin p=1e-5, myeloma p=8e-5 |
| 10 Report | Reverse conclusion text calls the 2 hits pleiotropy, but the JSON still reports them as effects | Forward: CLL, myeloma, mantle, Waldenström, overall significant; NHL, Hodgkin, ALL, DLBCL, other NHL, unspecified leukaemia attenuated to null |

**Takeaway:** on this paper the workflow hurt. Its Stage 3 thresholds (p<5e-8, r²<0.01, 1 Mb distance fallback) were written for literature-SNP designs and overrode the question's supplied threshold and the agent's own better default. The workflow also has no rule to drop instruments associated with the outcome, and none to flag estimates from fewer than 3 instruments. One run per condition, so variance is unknown.

### Will not be replicated
- **PhenoScanner v2** filtering: service retired; which SNPs the paper removed is not reported.
- **MR-PRESSO**: R-only; can be run separately if needed.
- **UKB replication (Supp. Table S4)**: those are Neale-lab linear-probability GWAS (OR ≈ 1.003), not log-odds; not comparable.
