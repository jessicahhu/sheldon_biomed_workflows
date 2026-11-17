# Paper card: kachuri2019_tl_lung_hnc

| Field | Value |
|---|---|
| paper_id | kachuri2019_tl_lung_hnc |
| citation | Kachuri L, Saarela O, Bojesen SE, et al. Mendelian randomization and mediation analysis of leukocyte telomere length and risk of lung and head and neck cancers. *Int J Epidemiol* 2019;48(3):751–766. doi:10.1093/ije/dyy140, PMC6659464 |
| exposure | Leukocyte TL (qPCR); literature SNP effects scaled to kbp; 5p15.33 score in TL Z-score (≈1 kbp) |
| exposure_scale | Per 1000 bp increase |
| outcomes | Lung (all, adeno, squamous, small cell); HNC (all, oral cavity, oropharynx); strata by smoking, age ≤50, non-drinkers |
| population | Exposure: European TL GWAS (Codd 2013, Mangino 2012, Pooley 2013) + Toronto/Copenhagen sequencing (n=2,051). Outcome: European OncoArray |
| sample_sizes | Lung 16,396/13,013 (adeno 5,690; squamous 4,045); HNC 4,415/5,013 |
| design | Two-sample summary MR (βY from individual-level OncoArray), plus counterfactual mediation for 5p15.33 |
| data_public | Partly. Literature SNP effects public; 5p15.33 per-variant data from n=2,051 sequencing is not; OncoArray per-SNP estimates not published, so we use public McKay 2017 (lung) and OncoArray oral/pharynx GWAS (GCST012234/5) |
| code_public | Absent |
| headline_claim | Genetically longer TL increases lung cancer risk, mainly adenocarcinoma, not squamous or HNC; the 5p15.33 instrument acts on lung cancer through TL (no direct effect). |

## Stage-by-stage decisions (what the paper did)

| # | Stage | Kachuri 2019 |
|---|---|---|
| 1 | Frame | Causal OR per 1 kbp TL, lung and HNC with histology and smoking strata |
| 2 | Data sources | OncoArray individual-level data (lung 23 studies, HNC 11), European ancestry; models adj. age, sex, study, 10 PCs |
| 3 | Select instruments | 7 replicated literature loci (P<5e-8 + replication) using genotyped-only SNPs with r²≈1 proxies (ACYP2, NAF1, ZNF676) + **new 14-variant 5p15.33 score**. Drops TERT rs2736100, CTC1 and ZNF208 relative to Zhang |
| 4 | Instrument strength | 5p15.33 score F=35.8, R²=1.49%; checked not associated with smoking or pack-years |
| 5 | Extract outcome | Directly estimated in OncoArray (no proxies needed) |
| 6 | Harmonise | Not described |
| 7 | Primary estimate | Maximum likelihood (primary), IVW (secondary) |
| 8 | Sensitivity | Weighted median, weighted mode, funnel asymmetry, pack-years adjustment, smoking/age strata |
| 9 | Adjust/decompose | **Mediation**: 5p15.33 direct effect OR 1.00 (0.95–1.04), indirect via TL 1.05 (1.01–1.08). Up to 40% of the TERT-locus lung association is mediated by TL |
| 10 | Report & conclude | Positive for lung/adeno, null squamous/small cell/HNC; addresses 5p15.33 pleiotropy with mediation rather than exclusion |

## Ground truth (Table 4, all subjects)

| Outcome | ML | IVW | Weighted median |
|---|---|---|---|
| Lung | 1.41 (1.20–1.65) | 1.39 (1.21–1.60) | 1.37 (1.12–1.67) |
| Adenocarcinoma | 1.92 (1.51–2.45) | 1.83 (1.51–2.22) | 1.63 (1.23–2.16) |
| Squamous | 1.04 (0.83–1.29) | 1.04 (0.83–1.29) | 1.09 (0.82–1.46) |
| HNC | 0.90 (0.70–1.15)* | 0.90 (0.70–1.15) | **0.71 (0.51–0.98), P=0.04** |

\*Abstract and Results text give the HNC ML CI as **0.70–1.05**, but Table 4 gives **0.70–1.15**. Same kind of text/table inconsistency as Zhang 2015. Score against the table.

## Replication (2026-11-12; full log in results/run_log.txt)

| Outcome | Method | Published | Replicated | Direction | Significance | Published OR in our CI |
|---|---|---|---|---|---|---|
| Lung | IVW | 1.39 (1.21–1.60) | **1.42 (1.27–1.59)** | ✓ | ✓ | ✓ |
| Lung | WM | 1.37 (1.12–1.67) | 1.41 (1.22–1.64) | ✓ | ✓ | ✓ |
| Adeno | IVW | 1.83 (1.51–2.22) | **1.88 (1.62–2.17)** | ✓ | ✓ | ✓ |
| Adeno | WM | 1.63 (1.23–2.16) | 1.72 (1.41–2.12) | ✓ | ✓ | ✓ |
| Squamous | IVW | 1.04 (0.83–1.29) | **1.02 (0.85–1.21)** | ✓ | ✓ | ✓ |
| Squamous | WM | 1.09 (0.82–1.46) | 1.02 (0.80–1.28) | ✓ | ✓ | ✓ |
| HNC | IVW | 0.90 (0.70–1.15) | **0.80 (0.62–1.03)** | ✓ | ✓ | ✓ |
| HNC | WM | 0.71 (0.51–0.98), P=0.04 | 0.76 (0.56–1.04), P=0.08 | ✓ | ✗ | ✓ |

With only the 7 public SNPs (no published 5p15.33 row): lung 1.47 (1.28–1.68), adeno 2.15 (1.78–2.59), squamous 0.92 (0.74–1.15), HNC 0.90 (0.63–1.27). Conclusions unchanged.

### Decisions logged
- **5p15.33 score not rebuilt.** Its 14 variants are mostly ultra-rare (EAF ~0.001) and come from a non-public sequencing study, so its TL and cancer associations were taken from Kachuri Table 3. This is the one place the replication uses the paper's own numbers.
- **Proxies:** we used Zhang's original SNPs for ACYP2/NAF1/ZNF676, which have r²=1 with Kachuri's genotyped proxies (1000G CEU). TERC rs10936599 is missing from both HNC files, so we used rs11711621 (r²=1), with alleles mapped by frequency and confirmed by matching lung betas. ZNF676 rs412658 appears in the HNC files as rs1277401554 (same position and alleles).
- **Palindromic PXK rs6772228 (A/T) is strand-flipped in the HNC files** (labelled A at freq 0.95 vs T at 0.95 in lung). Resolved by frequency; the HNC frequency column was verified to describe the effect allele for non-palindromic SNPs. HNC IVW is 0.80 with the correct flip, 0.85 with PXK dropped, and 0.92 with naive letter matching. All are null, but the instrument-level picture changes.
- **HNC outcome** = fixed-effect meta of two European OncoArray sets (4,839/5,257), close to the paper's 4,415/5,013.
- **Lung outcome** is the McKay 2017 meta-analysis, a superset of Kachuri's OncoArray lung sample. It overlaps the data used for zhang2015, so the two replications aren't independent.
- **Not replicated:** ML estimator, smoking/age strata, small cell, oral vs oropharynx subsites, and the mediation analysis.
