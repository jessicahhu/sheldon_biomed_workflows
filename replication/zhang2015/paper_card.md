# Paper card: zhang2015_tl_lung

| Field | Value |
|---|---|
| paper_id | zhang2015_tl_cancers (anchor outcome: lung adenocarcinoma) |
| citation | Zhang C, Doherty JA, Burgess S, …, Pierce BL. Genetic determinants of telomere length and risk of common cancers: a Mendelian randomization study. *Hum Mol Genet* 2015;24(18):5356–5366. doi:10.1093/hmg/ddv252 |
| exposure | Leukocyte telomere length (qPCR T/S ratio and Southern-blot TRF, rescaled to kb) |
| exposure_scale | Per 1000 bp (1 kb) longer TL |
| outcomes | Breast (all, ER−), colorectal, lung (all, adenocarcinoma, squamous), ovarian (all, clear-cell, endometrioid, serous), prostate (all, aggressive) |
| population | Exposure: European-ancestry TL GWAS (Codd 2013 ENGAGE; Mangino 2012; Pooley 2013). Outcome: European-ancestry GAME-ON consortia (TRICL for lung) |
| sample_sizes | Lung all 12,160/16,838; adeno 3,718/15,871; squamous 3,422/16,015 (9 GWAS). Exposure GWAS N ≈ 37,684 (Codd 2013) |
| design | Two-sample summary-data MR, multi-SNP score; age/sex stratified for lung |
| data_public | Partly. TL SNP effects in Table 2. GAME-ON lung per-SNP results aren't public as such; the superset McKay 2017 ILCCO/OncoArray is public (GCST004748 / 004744 / 004750) |
| code_public | Absent |
| headline_claim | "Our finding that genetic determinants of long TL increase lung adenocarcinoma risk … suggests that longer TL increases lung adenocarcinoma risk. However, caution regarding this causal interpretation is warranted in light of the potential issue of pleiotropy." |

## Stage-by-stage decisions (what the paper did)

| # | Stage | Zhang 2015 |
|---|---|---|
| 1 | Frame | Does genetically long TL change risk of 5 common cancers + subtypes? OR per 1 kb |
| 2 | Data sources | Exposure: 3 published TL GWAS. Outcome: GAME-ON (TRICL lung), fixed-effects meta of contributing GWAS; logistic regression adj. age, sex, PCs, **pack-years (lung)** |
| 3 | Select instruments | Literature lead SNPs at P<5e-8; 11 candidates, **2 dropped for LD** (rs7726159 r²=0.38 with rs2736100; rs412658 r²=0.70 with rs8105767) → 9 SNPs. No formal clumping/reference panel |
| 4 | Instrument strength | Variance explained 0.06–0.2% per SNP; no F reported |
| 5 | Extract outcome | All 9 available except colorectal → SNAP proxies (Table S4) |
| 6 | Harmonise | Not described. **rs6772228 (PXK) is A/T palindromic.** Not addressed |
| 7 | Primary estimate | First-order IVW (fixed effect); likelihood method as a 2nd estimator |
| 8 | Sensitivity | Heterogeneity / goodness-of-fit per cancer (Table S2); exclude SNPs failing fit (TERT for adeno) → OR 2.00 (1.48–2.70), P=6.6e-6; correlation r=0.17 between SNP-TL and SNP-adeno effects |
| 9 | Adjust/decompose | None (no MVMR, no mediation); age/sex stratified for lung |
| 10 | Report & conclude | Positive for adeno, null squamous, suggestive prostate; explicit pleiotropy hedge; names TERT locus as lung-cancer susceptibility region |

## Ground truth for scoring (Table 3, IVW)

| Outcome | OR / kb | 95% CI | P |
|---|---|---|---|
| Lung, all | 1.65 | 1.39–1.96 | 1.3e-8 |
| Lung adenocarcinoma | 2.87* | 2.20–3.74 | 6.3e-15 |
| Lung squamous | 1.04 | 0.79–1.36 | 0.79 |
| Adeno, TERT SNP excluded | 2.00 | 1.48–2.70 | 6.6e-6 |
| Prostate (suggestive) | 1.21 | 0.99–1.46 | 0.06 |

\*Abstract and Results text say **2.78 (2.16–3.58)**, but Table 3 says **2.87 (2.20–3.74)**, with the same P. Score against the table and log the discrepancy; graders should accept either.

## Our replication setup (differences from the paper)

- **Outcome data:** McKay 2017 ILCCO/OncoArray (29,266/56,450 overall; 11,273/55,483 adeno; 7,426/55,627 squamous). This is a **superset** of TRICL, so it's a conceptual replication with ~3× the cases rather than an exact one. Expect the same direction and significance. Effect size may differ.
- **Exposure SE:** not in Table 2, so it's back-derived from P. This doesn't affect first-order IVW (it uses only outcome SE) but matters for F / Steiger.
- **Covariates differ:** Zhang adjusted lung for pack-years. Check McKay 2017 Methods to see whether its summary stats were (TODO).

## Replication result (2026-11-12, IVW fixed effect, OR per 1 kb TL; full log in results/run_log.txt)

| Outcome | Published | Replicated | Direction | Significance | Published OR in our CI |
|---|---|---|---|---|---|
| Lung adenocarcinoma | 2.87 (2.20–3.74) | **2.75 (2.35–3.23)**, P=7e-36 | ✓ | ✓ | ✓ |
| Adeno, TERT excluded | 2.00 (1.48–2.70) | **2.13 (1.78–2.55)**, P=2e-16 | ✓ | ✓ | ✓ |
| Lung squamous | 1.04 (0.79–1.36) | **0.96 (0.80–1.16)**, P=0.70 | ✓ (null) | ✓ | ✓ |
| Lung overall | 1.65 (1.39–1.96) | **1.43 (1.26–1.63)**, P=6e-8 | ✓ | ✓ | ✗ (CIs overlap) |

Decisions logged:
- rs2736100 (TERT) is absent from GCST004748 (overall lung). The best EUR proxy has r²=0.58 (< 0.8), so it was dropped and overall lung uses 8 SNPs. This likely explains the smaller overall OR, since TERT is the strongest positive SNP for adeno.
- rs6772228 (PXK) is A/T palindromic, but the long allele T has frequency 0.95 in the outcome data and is the major allele in 1000G (Ensembl MAF of A = 0.01), so the strand is unambiguous. Kept.
- Adeno has strong heterogeneity (Q=59, df=8, P=7e-10), driven by TERT, as Zhang reported. Random-effects IVW is 2.75 (1.79–4.24), the weighted median is 2.02 (1.56–2.61), and the Egger intercept is ≈0 (P=0.94) but the Egger slope is imprecise.
