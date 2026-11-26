# SHELDON Biomedical Workflows: Mendelian Randomization

Can an LLM agent, given only a research question and public data, reach the answer a published paper did? And does an expert-written workflow help?

- **Workflow:** two-sample summary-data Mendelian randomization (MR), written as a 10-stage procedure in [`blind_agent/workflows/mr.md`](blind_agent/workflows/mr.md).
- **Evaluation:** questions from published MR papers that use public GWAS data. The agent never sees the paper. Answers are scored on direction, significance and effect size.
- **Comparison:** the same agent and questions, with and without the workflow, for a stronger and a weaker model (Claude Sonnet 5, Claude Haiku).
- **Two-agent variant:** a Haiku researcher whose every step is reviewed by a second Haiku checker ([`multi_agent_reasoning/`](multi_agent_reasoning/)).
- **Course context:** CS224V project, building on SHELDON. The target is 20–30 questions; 3 are done so far, one of them from a 2026 paper.

## Evaluation questions

| ID | Paper | Question | Public data |
|---|---|---|---|
| `paper_1` | Zhang et al. 2015, *Hum Mol Genet* | Does longer telomere length raise lung cancer risk, and does it differ by subtype? | McKay 2017 lung GWAS (GCST004748/4744/4750) |
| `paper_2` | Kachuri et al. 2019, *Int J Epidemiol* | Same, plus head-and-neck cancer | Above + OncoArray oral/pharyngeal GWAS (GCST012234/5) |
| `paper_3` | Wang et al. 2026, *Naunyn-Schmiedebergs Arch Pharmacol* | Does use of common drug classes (aspirin, opioids, antithrombotics, thyroid drugs; statins and diabetes drugs as nulls) change lung cancer risk? | UK Biobank medication-use GWAS (GCST90018981–95) + McKay 2017 lung GWAS |

For papers 1–2, the exposure (telomere-length SNP effects) comes from Zhang 2015 Table 2. Wang 2026 publishes no SNP list, so its instruments are rebuilt from the full exposure GWAS (see [replication/wang2026/paper_card.md](replication/wang2026/paper_card.md)).

## Results

### Scoreboard

Main outcomes only (paper 1: 3, paper 2: 4), 2 runs per paper = 14 estimates per model. Significance is P<0.05, matching the target.

| Model | Condition | Direction | Significance | Where it went wrong |
|---|---|---|---|---|
| Claude Sonnet 5 | Baseline | 13/14 | 14/14 | Harmonisation: palindromic SNP, invented proxy (1 run) |
| Claude Haiku | Baseline | 14/14 | 10/14 | Estimation: wrong IVW standard error (3 of 4 runs) |
| Claude Haiku ×2 | Researcher + checker | 22/28 | 26/28 | Harmonisation: head-and-neck direction wrong in every run (see [below](#two-agent-system-haiku-researcher--haiku-checker-2026-11-26)) |
| Claude Haiku | Expert workflow (`mr.md`) | 14/14 | 14/14 | None on papers 1–2 (see [below](#workflows-expert-vs-mined-by-a-strong-model-2026-11-26)) |

The full matrix, covering every model pairing, both workflows and GLM, is [below](#all-conditions-by-paper-2026-11-26).

**Paper 3 (Wang 2026),** 6 drug classes, 2 runs per condition = 12 estimates, scored against the published IVW results:

| Model | Condition | Direction | Significance | Where it went wrong |
|---|---|---|---|---|
| Claude Haiku | Baseline | 12/12 | 8/12 | Harmonisation: kept palindromic SNPs, so statins and diabetes drugs come out significant |
| Claude Haiku ×2 | Researcher + checker | 12/12 | 8/12 | Same as baseline (see [below](#paper-3-wang-2026-drug-use--lung-cancer-2026-11-26)) |

All runs passed the contamination check (see [below](#contamination-check)).

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

### Two-agent system: Haiku researcher + Haiku checker (2026-11-26)

Can a second model catch the first one's mistakes as they happen? Both agents are Claude Haiku.
- **Researcher:** the baseline set-up, unchanged: the same question, blinded files, sandbox (no network, no paper) and leak check. One added paragraph tells it a reviewer will comment on its work.
- **Checker:** gets the question and data description, but no files, no tools and no internet. After every researcher turn it sees that turn's narration, code and output, and replies `VERDICT: OK` or `VERDICT: CONCERN` with reasons. The reply goes back to the researcher with the tool results. It also reviews the final report, and on a concern it can ask for up to 2 revisions. Like the researcher, it is told not to use remembered published results.

There were 8 runs, 4 per paper, so 28 estimates. They were scored by [`multi_agent_reasoning/score.py`](multi_agent_reasoning/score.py), which uses the same targets as above and reproduces the Haiku baseline's 14/14 and 10/14 exactly.

| Haiku set-up | Runs | Direction | Significance | Runs with every outcome right |
|---|---|---|---|---|
| Single agent (baseline) | 4 | 14/14 (100%) | 10/14 (71%) | 1/4 |
| Researcher + checker | 8 | 22/28 (79%) | 26/28 (93%) | 2/8 |

All values are odds ratios per 1 kb (95% CI). ✓/✗ = direction / significance.

| Outcome | Target | `111840` | `4246` | `4247` | `4333` |
|---|---|---|---|---|---|
| P1 lung overall | 1.43, sig | 1.43 (1.41–1.72) ✓✓ | 1.58 (1.40–1.77) ✓✓ | 1.65 (1.43–1.91) ✓✓ | 1.56 (1.38–1.77) ✓✓ |
| P1 adenocarcinoma | 2.75, sig | 2.08 (1.97–6.91) ✓✓ | 3.05 (2.63–3.53) ✓✓ | 3.08 (2.56–3.70) ✓✓ | 3.03 (2.60–3.54) ✓✓ |
| P1 squamous | 0.96, null | 1.01 (0.82–1.06) ✗✓ | 0.96 (0.81–1.14) ✓✓ | 1.02 (0.82–1.26) ✗✓ | 0.96 (0.81–1.14) ✓✓ |

| Outcome | Target | `111841` | `111843` | `4248` | `4249` |
|---|---|---|---|---|---|
| P2 lung overall | 1.47, sig | 1.27 (1.26–1.27) ✓✓ | 1.45 (1.28–1.66) ✓✓ | 1.44 (1.25–1.67) ✓✓ | 1.41 (1.21–1.65) ✓✓ |
| P2 adenocarcinoma | 2.15, sig | 1.66 (1.64–1.68) ✓✓ | 2.09 (1.75–2.50) ✓✓ | 2.00 (1.63–2.46) ✓✓ | 2.01 (1.42–2.83) ✓✓ |
| P2 squamous | 0.92, null | 0.86 (0.86–0.87), **P≈0** ✓✗ | 0.98 (0.80–1.21) ✓✓ | 0.92 (0.74–1.15) ✓✓ | 0.93 (0.82–1.06) ✓✓ |
| P2 head-and-neck | 0.90, null | **not reported** ✗✗ | A 1.15, B 1.03, null ✗✓ | A 1.17, B 1.10, null ✗✓ | pooled 1.09 (0.64–1.88) ✗✓ |

`111840` reported the weighted median as its primary method rather than IVW. Its asymmetric intervals are bootstrapped.

**The checker fixed Haiku's statistical error.** The wrong IVW standard error survived into the final answer in only 1 of 8 runs (`111841`, with its very narrow intervals), against 3 of 4 in the baseline. In at least two runs (`4247`, `4333`) the checker objected at the IVW step and the researcher rewrote the formula, so null lung outcomes now come out null.

**But the direction got worse, at harmonisation.**
- **Head-and-neck went the wrong way in all 4 paper 2 runs.** Three runs reported an OR above 1 where the target is 0.90; `111841` left it out altogether.
  - The likely cause is rs6772228, an A/T palindromic SNP and the head-and-neck instrument with the largest exposure effect (0.12 kb).
  - Flipping it by allele labels alone gives the opposite sign from our replication, which aligns it the other way.
  - In `4248` the checker told the researcher to flip it by its labels and never mentioned that it is palindromic. Neither agent ever handled palindromic SNPs.
  - **Update (confirmed):** the checker did not cause this error; it exposed it by fixing the standard-error bug. Single Haiku got head-and-neck right only by accident. See [why some setups work better](#why-some-setups-work-better-2026-11-26).
- **The two paper 1 squamous "direction" misses are not real errors.** The ORs are 1.01 and 1.02 (P≈0.85). The published value is 1.04 and our replication is 0.96, so the direction rule is fragile for a null this close to 1.

**How the agents interacted:**
- The checker objected on 4–11 of the 15–28 reviews in each run (25–50%).
- It approved every final report, so no run used a revision. That includes `111841`, which left out an outcome the question asked for. One approval called the report "ready for peer review or publication".
- So the checker is useful while the work is being done and adds nothing at the final review.
- One run (`4247`) clumped correlated SNPs down to 8 instruments, the first run in either condition to handle LD.

**Caveats:**
- This is a small sample (8 runs against 4).
- Paper 1 has 4 runs rather than 2 because some runs were relaunched.
- A run takes about twice as many model calls as the baseline, about 5–10 minutes.

**Contamination.** The same check as below was run on all 8 transcripts and checker logs. There are no author, journal, consortium or accession mentions, and no reference to a published study. `4247`'s lung OR of 1.65 equals the published value, but its own IVW on 8 LD-clumped SNPs printed 1.6529 (1.4301–1.9103) before the number appears anywhere in its text.

### Paper 3: Wang 2026, drug use → lung cancer (2026-11-26)

This is the first question from a 2026 paper, so it is less likely to be in the models' training data. Both conditions were run: single Haiku (`run_agent.py --model claude-haiku`) and Haiku researcher + Haiku checker, 2 runs each.

**What the agent gets.** Wang 2026 publishes no SNP list, so we rebuilt the instruments the paper's way:
- P<5e-8, relaxed to P<5e-6 for opioids as in the paper.
- LD clumping at r²<0.001 within 10 Mb against 1000 Genomes EUR, then F>10.
- The pipeline is in `replication/wang2026/scripts/`.

The agent gets these instruments ready-made, as for papers 1–2, because clumping needs an LD reference panel that the sandbox can't reach. It also gets the lung cancer GWAS rows for those SNPs (389 of 421 SNPs were found). Drug names are neutral, and the leak check blocks the authors, journal, DOI, accession numbers and all 18 published IVW odds ratios and CI bounds.

**Our replication** (`replication/wang2026/results/run_log.txt`) gets 6/6 directions and 4/6 significance calls right. All 6 published ORs fall inside our 95% CIs. The two misses are borderline, and both turn on palindromic SNPs. The paper dropped them, and so does our primary analysis:
- Salicylates: P=0.056 (paper 0.0005). Keeping palindromic SNPs gives P=0.004.
- Statins: P=0.039 (paper 0.14).

**Agent results.** IVW odds ratios per unit log-odds of drug use. The other three runs differ from the first in the second decimal place at most.

| Drug | Published | Our replication | Agents (all 4 runs) | Direction / sig |
|---|---|---|---|---|
| Salicylates | 0.779, P=5e-4 | 0.850, P=0.056 (12 SNPs) | 0.83 (0.72–0.95), P=0.008 (16 SNPs) | ✓✓ |
| Opioids | 1.160, P=6e-4 | 1.177, P=1e-4 (34) | 1.16–1.18, P≤7e-5 (42) | ✓✓ |
| Antithrombotics | 0.780, P=0.005 | 0.768, P=0.002 (21) | 0.75 (0.67–0.85), P=7e-6 (23) | ✓✓ |
| Thyroid | 0.940, P=0.005 | 0.938, P=0.002 (86) | 0.96 (0.94–0.99), P=0.008 (104) | ✓✓ |
| Statins | 0.950, P=0.14, null | 0.925, P=0.039 (73) | 0.93 (0.89–0.98), **P=0.007** (90) | ✓✗ |
| Diabetes drugs | 0.971, P=0.17, null | 0.964, P=0.10 (92) | 0.96 (0.93–1.00), **P=0.03** (108) | ✓✗ |

**All 4 runs did the same analysis, and the checker didn't change it.**
- Every run used fixed-effect IVW on all available SNPs. No run mentions random effects.
- Every run aligned alleles by their labels and kept the palindromic SNPs. That's why they use more SNPs than we do (16 vs 12 for salicylates, 90 vs 73 for statins).
- Keeping them is a defensible choice, and our own pipeline gets the same calls when it keeps them (statins P=0.015, diabetes P=0.022). The paper dropped them, so the agents disagree with it on the two negative-control drugs. The same choice is also why salicylates matches the paper's significance call when our primary analysis doesn't.
- One two-agent run discussed palindromic variants (17 mentions) but still kept them, and its checker approved the alignment as "correct".

**The checker made one real catch and raised one false alarm, both on the IVW standard error.**
- **Real catch (`15308`):** the researcher's SE formula produced standard errors under 0.0001. The checker flagged it ("the standard errors are implausibly small (all < 0.0001)") and the researcher fixed it.
- **False alarm (`15324`):** the researcher's first formula, `sqrt(1 / Σ βx²/σy²)`, was correct. The checker called it a "critical error", while admitting in the same review that the code computes the formula it recommends. Its proposed alternative was the same formula again. The researcher spent 5 steps (8–12) chasing the non-existent bug before returning to the standard formula, so the final answer was unaffected.
- Neither baseline run got the SE wrong on this paper, so the final answers end up the same.
- The checker's other concerns (6 and 7 of 16 reviews) were mostly about code mechanics: missing imports, a typo, a misnamed column.
- As on papers 1–2, it approved both final reports without asking for a revision.

**Reading.**
- On this paper the checker added nothing to the final answer. Haiku on its own already got every direction right and matched our pipeline closely.
- The two significance misses come from one analysis choice, keeping palindromic SNPs. Neither agent questioned it. This is the same blind spot as on paper 2, here costing significance calls rather than a direction.

**Contamination.** There are no author, journal, biobank, consortium or accession mentions in any transcript or checker log, and no published value appears in any agent's code.

### All conditions by paper (2026-11-26)

These are all completed runs as of 2026-11-26. In each pairing, the researcher is named first. Each cell gives direction and significance correct, with the number of runs in brackets. Papers have 3, 4 and 6 outcomes respectively. The run-by-run list comes from `python3 multi_agent_reasoning/list_runs.py`.

| Condition | Paper 1 | Paper 2 | Paper 3 | Total direction | Total significance |
|---|---|---|---|---|---|
| Haiku alone | 6/6, 5/6 (2) | 8/8, 5/8 (2) | 12/12, 8/12 (2) | 26/26 | 18/26 |
| Haiku + expert workflow | 6/6, 6/6 (2) | 8/8, 8/8 (2) | 12/12, 8/12 (2) | 26/26 | **22/26** |
| Haiku + mined workflow | – | – | 12/12, 8/12 (2) | 12/12 | 8/12 |
| Sonnet alone | 6/6, 6/6 (2) | 7/8, 8/8 (2) | 12/12, 7/12 (2) | 25/26 | 21/26 |
| GLM alone | 6/6, 6/6 (2) | failed (2) | not run | 6/6 | 6/6 |
| Haiku + Haiku checker | 10/12, 12/12 (4) | 12/16, 14/16 (4) | 12/12, 8/12 (2) | 34/40 | 34/40 |
| Haiku + Sonnet checker | 6/6, 6/6 (2) | 7/8, 8/8 (2) | 12/12, 7/12 (2) | 25/26 | 21/26 |
| Sonnet + Haiku checker | 6/6, 6/6 (2) | 6/8, 8/8 (2) | 12/12, 6/12 (2) | 24/26 | 20/26 |
| Sonnet + Sonnet checker | 6/6, 6/6 (2) | 6/8, 8/8 (2) | 12/12, 6/12 (2) | 24/26 | 20/26 |
| Haiku + GLM checker | 6/6, 6/6 (2) | 3/4, 4/4 (1) | not run | 9/10 | 10/10 |
| GLM + Haiku checker | 6/6, 6/6 (2) | failed (2) | not run | 6/6 | 6/6 |

**Comparable rows.** Only rows with 2 runs on each of papers 1–3 can be compared directly: Haiku alone, Haiku + expert workflow, Sonnet alone, and the three pairings involving Sonnet. The GLM rows mostly cover paper 1, the easiest, and the mined workflow covers only paper 3.

**Why runs are missing.**
- **"Failed":** with GLM as researcher, all 4 paper 2 runs, alone and with a checker, used the full 16,000-token output limit on turn after turn and returned nothing visible. That's most likely hidden reasoning counting against the limit. Three continue-prompts didn't help, and no answer was produced. These failures appear to have used much of the budget.
- **"Not run":** the gateway key reached its $100 budget during the GLM queue, so the remaining paper 2–3 GLM runs were refused.

### Workflows: expert vs mined by a strong model (2026-11-26)

This experiment is on the branch `workflow-distillation` (folder [`workflow_distillation/`](workflow_distillation/)). Can a strong model turn earlier agent runs into a workflow that a weak model can follow?
- **Mining.** Claude Opus 5.5 read 25 scored traces from papers 1–2: every single-agent and two-agent run, with its methodology, results, checker concerns, and which outcomes it got right or wrong.
- **What it wrote.** A general step-by-step workflow ([`mined_p1p2.md`](workflow_distillation/workflows/mined_p1p2.md)), told not to name any SNP, gene, drug or result.
- **Held out.** The workflow was tested only on paper 3, which shares no data with papers 1–2. Papers 1 and 2 share the lung GWAS, so they're always kept in the same fold.
- **Leak check.** The workflow passed the leak check for paper 3: no blocked terms and no rsIDs.

**The mined workflow matches the expert workflow.** On paper 3 both score 12/12 direction and 8/12 significance, the same as no workflow. Both bring the estimates about 35% closer to the published values: the mean absolute difference in log OR is 0.025 with no workflow, 0.016 with the expert workflow and 0.017 with the mined one. Salicylates, for example, move from 0.83 to 0.78 against a published 0.779.

**The expert workflow helps most on papers 1–2.** It takes Haiku from 10/14 to 14/14 on significance there, because it fixes the standard-error bug, as explained below.

**Haiku followed both workflows closely.** Palindromic SNPs come up 83–129 times in each workflow transcript, against 0 in single-Haiku runs on paper 2.

**The reverse fold is not run yet:** mining from paper 3 and testing on papers 1–2. It was blocked by the budget.

### Why some setups work better (2026-11-26)

Each claim below was checked against the run files.

**1. Checkers and workflows fix Haiku's standard-error bug, and that drives most of Haiku's gains.**
- **The test.** We flagged every estimate whose CI implies a standard error less than half our replication's.
- **Where it shows up.** Flagged estimates appear in 3 of 6 Haiku-alone runs (14 of 29 estimates) and in 1 of 10 Haiku + Haiku checker runs.
- **Where it doesn't.** There are none in any run with a workflow, a Sonnet or GLM checker, or a Sonnet or GLM researcher.
- **What it explains.** Most of the significance gap between Haiku alone and every other setup on papers 1–2 is this one bug.

**2. On paper 2, fixing that bug exposed a hidden alignment error. That's why two-agent runs get head-and-neck wrong.**
- **The problem SNP.** rs6772228 is an A/T palindromic SNP. Its allele frequency is about 0.05 in the lung files but 0.95 in the head-and-neck files, which means the two sources report it on opposite strands.
- **Label alignment points the wrong way.** Aligning it by allele labels alone gives head-and-neck ORs of 1.17 (set A) and 1.12 (set B), the wrong direction. Dropping it gives 0.92 and 0.86, the target direction. Agents' reported values match these calculations exactly. Run `4248` reported A 1.17, B 1.10; the expert-workflow runs reported 0.92 and 0.86 with 4 SNPs.
- **Single Haiku was right by accident.** With the label-based alignment, its *buggy* weights (1/σ² on the ratios) reproduce its reported 0.95 and 0.96 exactly. Those weights ignore the exposure effect size, which down-weights rs6772228, the SNP with the largest exposure effect. Two errors cancelled.
- **Once the formula is fixed, the alignment error decides the sign.** Head-and-neck is wrong or missing in 10 of 11 two-agent paper 2 runs, across all pairings, against 1 of 6 single-agent runs.
- **The one two-agent catch.** It came from a Sonnet checker reviewing Haiku (run `21656`). The checker pointed out the 0.05 vs 0.95 frequency mismatch, the researcher dropped the SNP, and the run scored 4/4. The other Haiku + Sonnet run, and both Sonnet + Sonnet runs, missed it.
- **The expert workflow's palindromic-SNP rule fixed it in both of its runs.**

**3. On paper 3, significance mostly reflects which defensible choice a run made, not competence.**
- **The two choices that decide the calls** are whether palindromic SNPs are kept, and fixed- vs random-effects IVW. Runs fall into three groups:
  - **Haiku with no Sonnet involved:** kept palindromic SNPs and used fixed effects (16 salicylate SNPs), so all 6 drugs come out significant (pattern SSSSSS).
  - **Workflow runs:** used fixed effects with partial palindrome handling (SSSnSn).
  - **Sonnet runs, as researcher or checker:** used random effects with some palindromic SNPs kept (SSSnSS). That's exactly what our own replication gives when it keeps palindromic SNPs.
- **One run reproduced our replication exactly.** A Haiku + Sonnet-checker run used our instrument counts (12 salicylate SNPs, 86 thyroid SNPs) with random effects, and matched our primary analysis pattern (nSSSSn).
- **No choice we tested reaches the paper's pattern (SSSSnn).** Statins come out significant in every run and in our replication. With our rebuilt instruments, about 4 of 6 is the ceiling, so paper 3 can't separate the setups on significance.

**4. Different checkers behave differently, but objecting more isn't the same as catching more.**

| Pairing | Step concerns | Final-report concerns |
|---|---|---|
| Haiku researcher, Haiku checker (10 runs) | 39% | 1 of 11 |
| Haiku researcher, Sonnet checker (6) | 65% | 1 of 7 |
| Haiku researcher, GLM checker (3) | 47% | 2 of 5 |
| Sonnet researcher, Haiku checker (6) | 34% | 2 of 8 |
| Sonnet researcher, Sonnet checker (6) | 40% | 4 of 10 |
| GLM researcher, Haiku checker (2) | 59% | 0 of 2 |

- **Sonnet as checker objects most,** and it made the only palindrome catch. The one confirmed false alarm, a correct IVW formula called a "critical error" on paper 3, came from a Haiku checker.
- **Checkers rarely challenge a final report.** Only Sonnet checking Sonnet does so often.
- **Pairings help Haiku but not Sonnet.**
  - Haiku with any checker beats Haiku alone on significance (Haiku + Sonnet checker 21/26 vs 18/26), because the checker removes the standard-error bug.
  - Sonnet with either checker scores below Sonnet alone (20/26 vs 21/26). The Sonnet pairings get head-and-neck wrong in both paper 2 runs, and Sonnet has no visible bug for a checker to fix.
- **The checker's value depends on what the researcher gets wrong.** It helps when the researcher's errors show up in the code and output (Haiku's standard errors). It adds nothing when the researcher's errors are judgement calls the checker shares (alignment, palindromic SNPs).

**Summary.**
- The setups differ less in how well they reason than in *which* error they make.
- The biggest single gain comes from a domain rule written down explicitly, the palindrome and standard-error checks, whether a human wrote the workflow or Opus mined it.
- Peer review between agents helps only for errors that are visible in what the checker is shown.

### Harness changes on 2026-11-26

These changes affect how some results above were produced:
- **Continue-prompt.** If a turn ends with no tool call and no final JSON answer, the agent is told to continue, up to 3 times, and each prompt is logged in the transcript. Runs started before 14:38 used the old runner.
- **Missing verdicts.** A checker reply with no `VERDICT:` line is now recorded as `NONE`, not OK.
- **Unique folder names.** Baseline run folders now include the process ID, so parallel runs can't collide.
- **Scoring paper 3.** The scorer finds the drug name in any text field of a result row.
- **Results fixed by hand.** Three results were repaired from the agent's own report, each marked inside its `result.json`:
  - `111843` and `21656`: the final JSON was in the transcript, but the old runner didn't parse it.
  - `22947`: unlabelled drug rows, labelled from the report's stated table order. The original is kept as `result.original.json`.

**Next steps (blocked until the gateway budget is raised):**
- Mining fold B: mine from paper 3, test on papers 1–2.
- Haiku + GLM checker on paper 3.
- GLM as researcher with a higher output-token limit.
- More runs per cell, since every cell has 2.
- A planted-error benchmark to measure checker recall and precision directly.

## Contamination check

Did the agent recall the papers instead of analysing the data? Checked across all 8 completed baseline runs (4 Sonnet 5 on 2026-11-18, 4 Haiku on 2026-11-19); no sign that either model did.
- **No paper-identifying text.** The transcripts never mention the authors, journals, consortia (TRICL, ILCCO, OncoArray), accession numbers, "the published study", or any published odds ratio. `run_agent.py` logs every text block the model writes (and extended thinking is off), so there is no hidden reasoning that went unchecked.
- **Every reported number was computed.** Each OR and CI in `result.json` appears in the agent's own code output. No published value is hard-coded in its code (the only matches are 1.96, the 95% z-value, and one 0.90 that is Haiku's own computed CI bound).
- **Its choices don't match the papers'.** Both models kept the two LD-correlated SNPs Zhang dropped. Sonnet run 1 got head-and-neck in the wrong direction and argued a modest positive effect was missed for lack of power, and Haiku called two null outcomes significant. A model reciting the papers would have reported their results.
- **Only general knowledge.** Sonnet cited textbook facts (TERT is a pleiotropic cancer locus, the weighted-median method, Bowden 2016); gene names came from the `locus` column of the input file.

**Caveats.**
- The prompt itself gives hints ("some SNPs may be in LD", "may appear under a different rsID", "high-LD proxies"), which lowers the bar for the harmonisation steps.
- These are 2015/2019 papers, so contamination stays possible in principle. That is why new questions come from papers published in 2026.

## Repo layout

```
replication/            Hand replications (ground truth for scoring)
  common/mr_methods.py    IVW, MR-Egger, weighted median, harmonisation
  zhang2015/, kachuri2019/
    paper_card.md         Paper's decisions by stage, published numbers, our scorecard
    data/  scripts/  results/
  wang2026/               Drug use -> lung cancer (2026 paper)
    data/paper_supplement/  Paper's Tables S1-S2 (datasets, all published MR results)
    scripts/                fetch_exposures.sh -> build_instruments.py -> fetch_outcome.sh -> mr_wang.py
                            -> make_agent_files.py (the agent's two blinded input files)
blind_agent/            Runs the agent blind to the paper
  run_agent.py
  questions/              paper_1.json, paper_2.json, paper_3.json (question + data; paper never sent)
  workflows/mr.md         The workflow
  runs/                   Agent outputs (git-ignored)
multi_agent_reasoning/  Researcher + checker system (reuses blind_agent's sandbox and blinding)
  run_multi_agent.py
  score.py                Scores any run's result.json against the scoreboard targets
  matrix.py, list_runs.py Condition-by-paper table; every completed run with its scores
  runs/                   Outputs, incl. checker_reviews.json (git-ignored)
workflow_distillation/  Branch workflow-distillation: a strong model mines workflows from scored runs
  mine_workflow.py        Held-out mining (papers 1-2 and paper 3 are separate folds) + leak check
  workflows/              Mined workflows, with the exact prompt and a manifest of traces used
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

**Two-agent system.** This uses the same `.env`. Run it from the repo root:
```bash
uv run --python 3.12 --with anthropic python multi_agent_reasoning/run_multi_agent.py blind_agent/questions/paper_1.json
#   --researcher-model / --checker-model   (both default to claude-haiku)
python3 multi_agent_reasoning/score.py multi_agent_reasoning/runs/paper_*/*   # or blind_agent/runs/paper_*/*
```
Each run writes the same files as above, plus `checker_reviews.json` with every verdict. Its `transcript.md` shows the checker's reviews between the researcher's steps.

**Mined workflow.** Mine with Opus from the training papers, then run the weak model with the workflow:
```bash
uv run --python 3.12 --with anthropic python workflow_distillation/mine_workflow.py \
    --train paper_1 paper_2 --test paper_3 --out workflow_distillation/workflows/mined_p1p2.md
cd blind_agent && uv run --python 3.12 --with anthropic python run_agent.py questions/paper_3.json \
    --model claude-haiku --workflow ../workflow_distillation/workflows/mined_p1p2.md
```

**Caveat.** The model may still remember these papers. The code log shows whether it computed its answers itself; see [Contamination check](#contamination-check).

## References

- Zhang C et al. *Hum Mol Genet* 2015;24:5356. doi:10.1093/hmg/ddv252
- Kachuri L et al. *Int J Epidemiol* 2019;48:751. doi:10.1093/ije/dyy140
- Wang H et al. *Naunyn-Schmiedebergs Arch Pharmacol* 2026;399:9871. doi:10.1007/s00210-025-04967-2
- McKay JD et al. *Nat Genet* 2017 (lung GWAS)
- Sakaue S et al. *Nat Genet* 2021 (UK Biobank medication-use GWAS used by Wang 2026)
- Joshi, Shethia, Lam. *Sheldon: Reasoning through Dual Search over Hypotheses and Observation Spaces* (submitted)
