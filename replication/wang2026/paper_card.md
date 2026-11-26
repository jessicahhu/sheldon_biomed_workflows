# Paper card: wang2026_drugs_lung

| Field | Value |
|---|---|
| paper_id | wang2026_drugs_lung |
| citation | Wang H, Zhou B, Ma B, Zhang T, Kong R. Risk insights for clinical medication: a Mendelian randomization study of 23 drugs and lung cancer. *Naunyn-Schmiedeberg's Arch Pharmacol* 2026;399(7):9871–9879. doi:10.1007/s00210-025-04967-2, PMC13152963 (open access, epub 27 Jan 2026) |
| why chosen | Published 2026, so it is less likely to be in the model's training data than the 2015/2019 papers. All data public, full results table in the supplement |
| exposure | Self-reported medication use (23 ATC drug classes), UK Biobank European GWAS (Sakaue 2021 atlas; GWAS Catalog GCST90018980–GCST90019002, via OpenGWAS `ebi-a-`) |
| exposure_scale | Per unit log-odds of medication use (binary exposure) |
| outcome | Lung cancer overall, McKay 2017 (GCST004748; 29,266 cases / 56,450 controls, European) |
| design | Two-sample summary MR, TwoSampleMR + MR-PRESSO |
| data_public | Yes, all of it. The SNP lists are **not** published (Table S2 is results only), so instruments are rebuilt |
| code_public | Absent |
| headline_claim | Salicylates (aspirin) lower and opioids raise lung cancer risk (both Bonferroni-significant); suggestive protective effects for antithrombotics, antihypertensives, β-blockers, thyroid preparations, anilines |
| paper quality note | A drug-wide MR screen of a common kind. Exposure is "reports using the drug", which mixes the drug's effect with the reasons people take it (indication), so the causal reading is weak. Ground truth here is "what this paper's pipeline produces", not established biology |

## Stage-by-stage decisions (what the paper did)

| # | Stage | Wang 2026 |
|---|---|---|
| 1 | Frame | Causal effect of 23 drug classes on lung cancer; OR per log-odds of drug use |
| 2 | Data sources | OpenGWAS `ebi-a-GCST900189xx` (UKB, ~320k) → `ebi-a-GCST004748` |
| 3 | Select instruments | P<5e-8; if <3 IVs, relax to P<5e-6 (applied to peptic-ulcer drugs, opioids, antidepressants). Clump r²<0.001, 10,000 kb (1000G EUR). F>10 |
| 4 | Instrument strength | All F>10 (Fig S1) |
| 5 | Extract outcome | SNPs absent from outcome removed (proxies not mentioned) |
| 6 | Harmonise | **Palindromic SNPs removed** |
| 7 | Primary estimate | IVW (TwoSampleMR: multiplicative random effects) |
| 8 | Sensitivity | ML, weighted median, MR-Egger (+intercept), Cochran's Q, MR-PRESSO outlier removal, leave-one-out |
| 9 | Adjust/decompose | None (no MVMR for smoking, no correction for why people take the drug) |
| 10 | Report & conclude | Bonferroni 0.05/23 → P<0.0022; 0.0022<P<0.05 called "suggestive" |

## Ground truth (Table S2, IVW, lung cancer overall)

Full table for all 23 drugs and 4 methods: [data/paper_supplement/published_results.tsv](data/paper_supplement/published_results.tsv).

| Drug | nSNP | IVW OR (95% CI) | P | Paper's call |
|---|---|---|---|---|
| Salicylic acid & derivatives | 18 | 0.779 (0.676–0.898) | 5.5e-4 | Significant, protective |
| Opioids (P<5e-6 instruments) | 35 | 1.160 (1.065–1.263) | 6.4e-4 | Significant, harmful |
| Antithrombotic agents | 24 | 0.780 (0.656–0.927) | 4.9e-3 | Suggestive; significant after MR-PRESSO |
| Thyroid preparations | 88 | 0.940 (0.901–0.981) | 4.8e-3 | Suggestive |
| HMG-CoA reductase inhibitors (statins) | 76 | 0.950 (0.887–1.017) | 0.14 | Null (negative control) |
| Drugs used in diabetes | 95 | 0.971 (0.931–1.013) | 0.17 | Null (negative control) |

## Replication

Run 2026-11-26; full output in [results/run_log.txt](results/run_log.txt), IVW comparison in `results/comparison_ivw.tsv`.

- **Instruments:** 22 / 46 / 29 / 120 / 104 / 118 after clumping (salicylates, opioids at P<5e-6, antithrombotics, thyroid, statins, diabetes). After dropping SNPs absent from the outcome and palindromic SNPs, 12 / 34 / 21 / 86 / 73 / 92 are used. The paper used 18 / 35 / 24 / 88 / 76 / 95; the difference comes from a different LD reference (1000G phase 3 queried directly, not the OpenGWAS panel).
- **Score against the paper (IVW, multiplicative random effects):** direction 6/6, significance at P<0.05 4/6. All 6 published ORs fall inside our 95% CI.
- **The two significance misses are borderline and depend on palindromic SNPs:**
  - Salicylates: 0.850 (0.719–1.004), P=0.056, against the paper's 0.779, P=0.0005. Keeping palindromic SNPs with MAF<0.42 gives 0.804, P=0.004.
  - Statins: 0.925 (0.859–0.996), P=0.039, against the paper's 0.950, P=0.14.
- **Agent question:** `blind_agent/questions/paper_3.json`. The agent gets the instruments ready-made (see `scripts/make_agent_files.py`).
