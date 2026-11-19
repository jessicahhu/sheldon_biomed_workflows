# SHELDON Biomedical Workflows: Mendelian Randomization

Can an LLM agent, given only a research question and public data, reach the answer a published paper did? And does an expert-written workflow help?

- **Workflow:** two-sample summary-data Mendelian randomization (MR), written as a 10-stage procedure in [`blind_agent/workflows/mr.md`](blind_agent/workflows/mr.md).
- **Evaluation:** questions from published MR papers that use public GWAS data. The agent never sees the paper. Answers are scored on direction, significance and effect size.
- **Comparison:** the same agent and questions, with and without the workflow.
- **Course context:** CS224V project, building on SHELDON. The target is 20–30 questions; 2 are done so far and a third (a 2026 paper) is being replicated.

## Evaluation questions

| ID | Paper | Question | Public data |
|---|---|---|---|
| `paper_1` | Zhang et al. 2015, *Hum Mol Genet* | Does longer telomere length raise lung cancer risk, and does it differ by subtype? | McKay 2017 lung GWAS (GCST004748/4744/4750) |
| `paper_2` | Kachuri et al. 2019, *Int J Epidemiol* | Same, plus head-and-neck cancer | Above + OncoArray oral/pharyngeal GWAS (GCST012234/5) |
| *(pending)* | Wang et al. 2026, *Naunyn-Schmiedebergs Arch Pharmacol* | Does use of common drug classes (aspirin, opioids, antithrombotics, thyroid drugs; statins and diabetes drugs as nulls) change lung cancer risk? | UK Biobank medication-use GWAS (GCST90018981–95) + McKay 2017 lung GWAS |

For papers 1–2, the exposure (telomere-length SNP effects) comes from Zhang 2015 Table 2. Wang 2026 publishes no SNP list, so its instruments are rebuilt from the full exposure GWAS (see [replication/wang2026/paper_card.md](replication/wang2026/paper_card.md)).

## Results

All values are odds ratios per 1 kb longer telomere length (95% CI). Agent = Claude Sonnet 5, baseline (no workflow). Each paper has two completed baseline runs; both paper 1 runs gave identical numbers.

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

**Score so far (main outcomes, 2 runs per paper = 14 estimates):** direction 13/14, significance 14/14. Head-and-neck direction is right in 1 of 2 runs, so the baseline is *inconsistent* rather than reliably wrong. With the workflow: *pending*. To compare conditions fairly, run each one several times and report how often it gets each outcome right.

**Baseline agent errors.** All were in instrument selection and harmonisation (stages 3, 5, 6); the statistics were right.
- **Kept correlated SNPs** in every run. Zhang dropped 2 for LD; the agent kept all 11 in its primary estimate (paper 1 ran a TERT-excluded check, but only as a sensitivity analysis).
- **Matched palindromic SNP PXK (A/T) on letters, not allele frequency** (paper 2, run 1). It is strand-flipped in the head-and-neck files. Run 2 compared frequencies (0.05 vs 0.95) and corrected it.
- **Invented a proxy SNP** by physical proximity, which counted the ZNF676 locus twice (paper 2, run 1). Run 2 recognised `rs1277401554` as the same position as `rs412658` and used it as a substitute instead.

In run 1, the last two flip the head-and-neck result: 1.31 → 1.04 after fixing PXK → 0.90 after dropping the proxy. The workflow adds explicit rules for all three.

## Contamination check (baseline runs)

Did the agent recall the papers instead of analysing the data? Checked on 2026-11-18 across all four completed runs; no sign that it did.
- **No paper-identifying text.** The transcripts never mention the authors, journals, consortia (TRICL, ILCCO, OncoArray), accession numbers, "the published study", or any published odds ratio. `run_agent.py` logs every text block the model writes (and extended thinking is off), so there is no hidden reasoning that went unchecked.
- **Every reported number was computed.** Each OR and CI in `result.json` appears in the agent's own code output. No published value is hard-coded in its code (the only match is 1.96, the 95% z-value).
- **Its choices don't match the papers'.** It kept the two LD-correlated SNPs Zhang dropped, and in run 1 it got head-and-neck in the wrong direction and argued a modest positive effect was missed for lack of power. A model reciting Kachuri 2019 would have reported the null.
- **Only general knowledge.** It cited textbook facts (TERT is a pleiotropic cancer locus, the weighted-median method, Bowden 2016); gene names came from the `locus` column of the input file.

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
  wang2026/               In progress: drug use -> lung cancer (2026 paper)
    data/paper_supplement/  Paper's Tables S1-S2 (datasets, all published MR results)
    scripts/                fetch_exposures.sh -> build_instruments.py -> fetch_outcome.sh -> mr_wang.py
blind_agent/            Runs the agent blind to the paper
  run_agent.py
  questions/              paper_1.json, paper_2.json (question + data; paper never sent)
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
   ```

**Output.** Each run writes to `runs/<question>/<model>_<baseline|mr>_<time>/`:
- `report.md`: results, step-by-step methodology, conclusion, and the code actually run.
- `transcript.md`: the full record of the run.
- `result.json`: the final answer, for scoring.
- `sent_to_agent/`: exactly what the agent received.

**Blinding.** The agent only sees the question and renamed data files with paper-identifying columns removed.
- Its code runs in a macOS sandbox that cannot read `/Users` and has no network access.
- A leak check aborts the run if anything sent contains author names, journals, IDs, dataset accessions or published numbers.

**Caveat.** The model may still remember these papers. The code log shows whether it computed its answers itself.

## References

- Zhang C et al. *Hum Mol Genet* 2015;24:5356. doi:10.1093/hmg/ddv252
- Kachuri L et al. *Int J Epidemiol* 2019;48:751. doi:10.1093/ije/dyy140
- McKay JD et al. *Nat Genet* 2017 (lung GWAS)
- Joshi, Shethia, Lam. *Sheldon: Reasoning through Dual Search over Hypotheses and Observation Spaces* (submitted)
