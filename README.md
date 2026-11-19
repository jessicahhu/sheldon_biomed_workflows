# SHELDON Biomedical Workflows: Mendelian Randomization

Can an LLM agent, given only a research question and public data, reach the answer a published paper did? And does an expert-written workflow help?

- **Workflow:** two-sample summary-data Mendelian randomization (MR), written as a 10-stage procedure in [`blind_agent/workflows/mr.md`](blind_agent/workflows/mr.md).
- **Evaluation:** questions from published MR papers that use public GWAS data. The agent never sees the paper. Answers are scored on direction, significance and effect size.
- **Comparison:** the same agent and questions, with and without the workflow, for a stronger and a weaker model (Claude Sonnet 5, Claude Haiku).
- **Course context:** CS224V project, building on SHELDON. The target is 20–30 questions; 4 are done so far (3 papers) and another (a 2026 paper) is being replicated.

## Evaluation questions

| ID | Paper | Question | Public data |
|---|---|---|---|
| `paper_1` | Zhang et al. 2015, *Hum Mol Genet* | Does longer telomere length raise lung cancer risk, and does it differ by subtype? | McKay 2017 lung GWAS (GCST004748/4744/4750) |
| `paper_2` | Kachuri et al. 2019, *Int J Epidemiol* | Same, plus head-and-neck cancer | Above + OncoArray oral/pharyngeal GWAS (GCST012234/5) |
| `paper_3` | Jiang et al. 2024, *Cancer Res Commun* | Does longer telomere length raise risk of 17 haematologic malignancies? (OR per SD) | OpenGWAS `ieu-b-4879` (UK Biobank TL GWAS) + FinnGen R9 |
| `paper_3b` | Same paper, reverse direction | Does genetic liability to each malignancy change telomere length? | Same |
| *(pending)* | Wang et al. 2026, *Naunyn-Schmiedebergs Arch Pharmacol* | Does use of common drug classes (aspirin, opioids, antithrombotics, thyroid drugs; statins and diabetes drugs as nulls) change lung cancer risk? | UK Biobank medication-use GWAS (GCST90018981–95) + McKay 2017 lung GWAS |

For papers 1–2, the exposure (telomere-length SNP effects) comes from Zhang 2015 Table 2. For paper 3 the agent gets all 38,506 TL variants at p<5e-8 (reverse: each cancer's variants at p<1e-5), unclumped, plus 1000 Genomes EUR reference genotypes, so it must select independent instruments itself (see [replication/jiang2024/paper_card.md](replication/jiang2024/paper_card.md)). Wang 2026 publishes no SNP list, so its instruments are rebuilt from the full exposure GWAS (see [replication/wang2026/paper_card.md](replication/wang2026/paper_card.md)).

## Results

### Scoreboard

Main outcomes only (paper 1: 3, paper 2: 4), 2 runs per paper = 14 estimates per model. Significance is P<0.05, matching the target.

| Model | Condition | Direction | Significance | Where it went wrong |
|---|---|---|---|---|
| Claude Sonnet 5 | Baseline | 13/14 | 14/14 | Harmonisation: palindromic SNP, invented proxy (1 run) |
| Claude Haiku | Baseline | 14/14 | 10/14 | Estimation: wrong IVW standard error (3 of 4 runs) |
| Either | With workflow | *pending* | *pending* | |

Paper 3 is scored separately [below](#claude-sonnet-5-papers-3-and-3b-baseline-and-workflow-2026-11-19) (17 + 16 outcomes, one run per condition); it has the first with-workflow results. All runs passed the contamination check (see [below](#contamination-check)).

### Claude Sonnet 5 (baseline, 2026-11-17)

All values are odds ratios per 1 kb longer telomere length (95% CI). Both paper 1 runs gave identical numbers, so paper 1 shows one Agent column.

**Paper 1: Zhang 2015**

| Outcome | Published | Our replication | Agent | Agent matches published? |
|---|---|---|---|---|
| Lung overall | 1.65 (1.39–1.96) | 1.43 (1.26–1.63) | 1.58 (1.26–1.97) | ✓ |
| Adenocarcinoma | 2.87 (2.20–3.74) | 2.75 (2.35–3.23) | 3.05 (1.99–4.67) | ✓ |
| Squamous | 1.04 (0.79–1.36), null | 0.96 (0.80–1.16), null | 0.96 (0.81–1.14), null | ✓ |
| Adeno, TERT excluded | 2.00 (1.48–2.70) | 2.13 (1.78–2.55) | 2.13 (1.79–2.53) | ✓ |

**Paper 2: Kachuri 2019.** The paper's 5p15.33 instrument is not public, so the target is our 7-SNP replication.

| Outcome | Published (8 instruments) | Our replication (7 SNPs) | Agent run 1 (`112053`) | Agent run 2 (`114051`) |
|---|---|---|---|---|
| Lung overall | 1.39 (1.21–1.60) | 1.47 (1.28–1.68) | 1.46 (1.28–1.66) ✓ | 1.43 (1.19–1.73) ✓ |
| Adenocarcinoma | 1.83 (1.51–2.22) | 2.15 (1.78–2.59) | 2.12 (1.78–2.54) ✓ | 2.00 (1.39–2.88) ✓ |
| Squamous | 1.04 (0.83–1.29), null | 0.92 (0.74–1.15), null | 0.92 (0.75–1.13), null ✓ | 0.92 (0.74–1.15), null ✓ |
| Head-and-neck | 0.90 (0.70–1.15), null | 0.90 (0.63–1.27), null | 1.31 (0.94–1.82), null ✗ direction | 0.89 (0.44–1.79), null ✓ |

Run 1 used fixed-effect IVW with 8 instruments; run 2 used random-effects IVW with 7 (lung) and 6 (head-and-neck) instruments, which is why its intervals are wider. A third paper 2 run (`112033`) was stopped by hand and isn't scored.

**Score:** direction 13/14, significance 14/14. Head-and-neck direction is right in 1 of 2 runs, so the baseline is *inconsistent* rather than reliably wrong. To compare conditions fairly, run each one several times and report how often it gets each outcome right.

**Sonnet's errors.** All were in instrument selection and harmonisation (stages 3, 5, 6); the statistics were right.
- **Kept correlated SNPs** in every run. Zhang dropped 2 for LD; the agent kept all 11 in its primary estimate (paper 1 ran a TERT-excluded check, but only as a sensitivity analysis).
- **Matched palindromic SNP PXK (A/T) on letters, not allele frequency** (paper 2, run 1). It is strand-flipped in the head-and-neck files. Run 2 compared frequencies (0.05 vs 0.95) and corrected it.
- **Invented a proxy SNP** by physical proximity, which counted the ZNF676 locus twice (paper 2, run 1). Run 2 recognised `rs1277401554` as the same position as `rs412658` and used it as a substitute instead.

In run 1, the last two flip the head-and-neck result: 1.31 → 1.04 after fixing PXK → 0.90 after dropping the proxy. The workflow adds explicit rules for all three.

### Claude Haiku, weaker model (baseline, 2026-11-19)

Same experiment: same `run_agent.py`, questions, blinded files, sandbox (no network, no paper) and leak check, with `--model claude-haiku` only. Two runs per paper. ✓/✗ = direction / significance at P<0.05 against the same targets as above.

| Outcome | Target | Haiku run 1 | Haiku run 2 |
|---|---|---|---|
| P1 lung overall | 1.65, sig | 1.58 (1.40–1.77) ✓✓ | 1.59 (1.57–1.60) ✓✓ |
| P1 adenocarcinoma | 2.87, sig | 3.05 (2.63–3.53) ✓✓ | 2.98 (2.94–3.01) ✓✓ |
| P1 squamous | 1.04, null | 0.96 (0.81–1.14) ✓✓ | 0.97 (0.95–0.98), **P=1e-6** ✓✗ |
| P2 lung overall | 1.47, sig | 1.50 (1.48–1.51) ✓✓ | same as run 1 |
| P2 adenocarcinoma | 2.15, sig | 2.22 (2.18–2.25) ✓✓ | same |
| P2 squamous | 0.92, null | 0.93 (0.91–0.95), **P=5e-15** ✓✗ | same |
| P2 head-and-neck | 0.90, null | not pooled; set A 0.95 (P=0.08), set B 0.96 (P=0.18) ✓✓ | pooled 0.96 (0.92–1.00), **P=0.03** ✓✗ |

**Score:** direction 14/14, significance 10/14 (Sonnet 5: 13/14 and 14/14). The two paper 2 runs gave identical lung estimates.

**Haiku's errors are statistical, not harmonisation.**
- **Wrong IVW standard error in 3 of 4 runs.** It weighted each ratio estimate βy/βx by 1/SE_y² in place of βx²/SE_y² (paper 1 run 2 instead used SE = |βy|·SE_y/βx²). With βx ≈ 0.05–0.12 kb this makes the SE roughly 10–20× too small, so null outcomes come out "significant". Point estimates are unaffected, which is why direction is perfect.
- **Never considered strand or palindromic SNPs** (no mention in any transcript). It matched only exact rsIDs, so it used 5 head-and-neck instruments and never used the renamed ZNF676 SNP or the TERC proxy. Avoiding proxies sidestepped Sonnet's double-counting error, partly by luck.
- **No LD handling:** like Sonnet, it kept all 11 SNPs in paper 1.

So the two models fail at different stages: Sonnet at harmonisation (stages 5–6), Haiku at estimation (stage 7). A workflow that spells out the IVW formula should help Haiku more than Sonnet.

### Claude Sonnet 5, papers 3 and 3b (baseline and workflow, 2026-11-19)

Odds ratios per 1 SD longer telomere length (forward) or exp(β) on TL SD per unit log-odds of cancer (reverse). Unlike papers 1–2, the agent must select instruments itself from unclumped GWAS hits plus LD reference genotypes. Scored primarily against our hand replication, because the paper's PhenoScanner filtering can't be reproduced (that service has shut down). One run per condition. Full per-outcome tables: [`replication/jiang2024/results/agent_scores.md`](replication/jiang2024/results/agent_scores.md).

| Question | Condition | Instruments | Direction vs replication | Significance vs replication | Significance vs paper |
|---|---|---|---|---|---|
| `paper_3` forward (17 outcomes) | Hand replication | 139 | — | — | 17/17 |
| | Baseline | 139 | **17/17** | **17/17** | **17/17** |
| | Workflow | 156 | 15/17 | 10/17 | 10/17 |
| `paper_3b` reverse (16 estimable) | Hand replication | 4–35 | — | — | 15/16 |
| | Baseline | 8–58 | n/a (all ≈1.00) | **13/16** | **14/16** |
| | Workflow | 0–6 | n/a | 4/16 (8 not estimated) | 4/16 (8 not estimated) |

Selected forward estimates (IVW OR per SD):

| Outcome | Published | Our replication | Baseline | Workflow |
|---|---|---|---|---|
| All lymphoid/haematopoietic | 1.65 (1.38–1.97) | 1.48 (1.26–1.75) | 1.60 (1.36–1.88) | 1.42 (1.19–1.69) |
| CLL | 2.16 (1.27–3.67) | 3.63 (2.40–5.51) | 3.80 (2.50–5.77) | 3.58 (2.24–5.72) |
| NHL | 1.74 (1.15–2.64) | 1.73 (1.20–2.51) | 1.78 (1.20–2.64) | 1.28 (0.84–1.96), null ✗ |
| Hodgkin | 1.70 (1.12–2.58) | 1.74 (1.19–2.53) | 1.65 (1.13–2.42) | 1.48 (0.98–2.24), null ✗ |
| AML | 1.49 (0.61–3.64), null | 1.95 (0.91–4.15), null | 1.88 (0.87–4.04), null | 1.71 (0.78–3.74), null |

**The workflow made things worse on paper 3.** The agent followed `mr.md` faithfully, but Stage 3's fixed rules, written for papers 1–2 (a handful of literature SNPs), don't fit a genome-wide instrument search:
- **"Keep SNPs with p < 5×10⁻⁸"** discarded most of the reverse data, which the question deliberately supplied at p<1e-5 (the paper's threshold for small cancer GWAS). 8 cancers were left with no instruments. Several others had 1 SNP, whose Wald ratios it reported as significant (p up to 1e-16); all are null in the paper and our replication.
- **"r² < 0.01; without LD information, use a 1 Mb window"** is looser than the standard r²<0.001 within 10 Mb. In the forward run the agent applied the distance rule to the ~34% of variants missing from the LD panel and got 231 "independent" loci instead of ~147, and 7 true effects attenuated to null. The baseline instead excluded variants it could not check for LD.
- **No rule to drop instruments associated with the outcome.** The reverse baseline kept a TERC variant with TL p≈0. It even named it as a "textbook violation of the exclusion restriction" but did not remove it, and reported 2 false positives (DLBCL, non-follicular). The paper's rule (drop instruments with outcome p<5e-8) would have caught it.

Without the workflow, Sonnet's errors were the reverse-direction ones above, plus letter-only matching of palindromic SNPs (harmless here), the same shortcut as the PXK error in paper 2. Next: make Stage 3 defer to the question's threshold, clump at r²<0.001/10 Mb when genotypes are given, add the outcome-association and minimum-instrument rules, then re-run all papers with and without the workflow.

## Contamination check

Did the agent recall the papers instead of analysing the data? Checked across all 8 completed baseline runs (4 Sonnet 5 on 2026-11-18, 4 Haiku on 2026-11-19); no sign that either model did.
- **No paper-identifying text.** The transcripts never mention the authors, journals, consortia (TRICL, ILCCO, OncoArray), accession numbers, "the published study", or any published odds ratio. `run_agent.py` logs every text block the model writes (and extended thinking is off), so there is no hidden reasoning that went unchecked.
- **Every reported number was computed.** Each OR and CI in `result.json` appears in the agent's own code output. No published value is hard-coded in its code (the only matches are 1.96, the 95% z-value, and one 0.90 that is Haiku's own computed CI bound).
- **Its choices don't match the papers'.** Both models kept the two LD-correlated SNPs Zhang dropped. Sonnet run 1 got head-and-neck in the wrong direction and argued a modest positive effect was missed for lack of power, and Haiku called two null outcomes significant. A model reciting the papers would have reported their results.
- **Only general knowledge.** Sonnet cited textbook facts (TERT is a pleiotropic cancer locus, the weighted-median method, Bowden 2016); gene names came from the `locus` column of the input file.

**Caveats.**
- The prompt itself gives hints ("some SNPs may be in LD", "may appear under a different rsID", "high-LD proxies"), which lowers the bar for the harmonisation steps.
- These are 2015/2019 papers, so contamination stays possible in principle. That is why new questions come from papers published in 2026.

**Paper 3 (4 Sonnet 5 runs, 2026-11-19): same checks, also clean.** No transcript mentions the authors, journal, FinnGen, UK Biobank, OpenGWAS, the TL GWAS or any published OR, and all 180 values in the four `result.json` files appear in the agent's own code output. Jiang 2024 is older than the 2026 rule above (it was chosen before that rule), so treat it as a pre-cutoff paper like papers 1–2.

## Repo layout

```
replication/            Hand replications (ground truth for scoring)
  common/mr_methods.py    IVW, MR-Egger, weighted median, harmonisation
  zhang2015/, kachuri2019/
    paper_card.md         Paper's decisions by stage, published numbers, our scorecard
    data/  scripts/  results/
  jiang2024/              TL <-> haematologic cancers, bidirectional (papers 3, 3b)
    scripts/                extract_tl_sig.py, fetch_finngen.py, fetch_ld_ref.sh -> mr_jiang.py;
                            make_agent_files.py (agent files + question JSONs); score_agent.py
    data/agent/             Files sent to the agent. Large downloads (TL VCF, LD panel, PLINK)
                            are git-ignored and rebuilt by the fetch scripts
    results/agent_scores.md Per-outcome scores for the blind agent runs
  wang2026/               In progress: drug use -> lung cancer (2026 paper)
    data/paper_supplement/  Paper's Tables S1-S2 (datasets, all published MR results)
    scripts/                fetch_exposures.sh -> build_instruments.py -> fetch_outcome.sh -> mr_wang.py
blind_agent/            Runs the agent blind to the paper
  run_agent.py
  questions/              paper_1.json, paper_2.json, paper_3.json, paper_3b.json
                          (question + data; paper never sent)
  workflows/mr.md         The workflow
  runs/                   Agent outputs (git-ignored)
```

## Running the agent

1. Create `blind_agent/.env` (git-ignored) with:
   ```
   ANTHROPIC_API_KEY=<LiteLLM key>
   LITELLM_BASE_URL=https://models.genie.stanford.edu/
   MODEL=claude-sonnet-5
   ```
2. Run:
   ```bash
   cd blind_agent
   uv run --python 3.12 --with anthropic python run_agent.py questions/paper_1.json                            # baseline
   uv run --python 3.12 --with anthropic python run_agent.py questions/paper_1.json --workflow workflows/mr.md # with workflow
   uv run --python 3.12 --with anthropic python run_agent.py questions/paper_1.json --model claude-haiku       # other model
   uv run --python 3.12 --with anthropic python run_agent.py --list-models                                    # models on the gateway
   ```

**Output.** Each run writes to `runs/<question>/<model>_<baseline|mr>_<time>/`:
- `report.md`: results, step-by-step methodology, conclusion, and the code actually run.
- `transcript.md`: the full record of the run.
- `result.json`: the final answer, for scoring.
- `sent_to_agent/`: exactly what the agent received.

**Blinding.** The agent only sees the question and renamed data files with paper-identifying columns removed.
- Its code runs in a macOS sandbox that cannot read `/Users` and has no network access.
- A leak check aborts the run if anything sent contains author names, journals, IDs, dataset accessions or published numbers.

**Caveat.** The model may still remember these papers. The code log shows whether it computed its answers itself; see [Contamination check](#contamination-check).

## References

- Zhang C et al. *Hum Mol Genet* 2015;24:5356. doi:10.1093/hmg/ddv252
- Kachuri L et al. *Int J Epidemiol* 2019;48:751. doi:10.1093/ije/dyy140
- Jiang G et al. *Cancer Res Commun* 2024;4:2815. doi:10.1158/2767-9764.CRC-24-0402
- Codd V et al. *Nat Genet* 2021 (UK Biobank TL GWAS, OpenGWAS `ieu-b-4879`); Kurki MI et al. *Nature* 2023 (FinnGen)
- Wang H et al. *Naunyn-Schmiedebergs Arch Pharmacol* 2026;399:9871. doi:10.1007/s00210-025-04967-2
- McKay JD et al. *Nat Genet* 2017 (lung GWAS)
- Sakaue S et al. *Nat Genet* 2021 (UK Biobank medication-use GWAS used by Wang 2026)
- Joshi, Shethia, Lam. *Sheldon: Reasoning through Dual Search over Hypotheses and Observation Spaces* (submitted)
