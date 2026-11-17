# SHELDON Biomedical Workflows: Mendelian Randomization

Can an LLM agent, given only a research question and public data, reach the answer a published paper did? And does an expert-written workflow help?

- **Workflow:** two-sample summary-data Mendelian randomization (MR), written as a 10-stage procedure in [`blind_agent/workflows/mr.md`](blind_agent/workflows/mr.md).
- **Evaluation:** questions from published MR papers that use public GWAS data. The agent never sees the paper. Answers are scored on direction, significance and effect size.
- **Comparison:** the same agent and questions, with and without the workflow.
- **Course context:** CS224V project, building on SHELDON. The target is 20–30 questions; 2 are done so far.

## Evaluation questions

| ID | Paper | Question | Public data |
|---|---|---|---|
| `paper_1` | Zhang et al. 2015, *Hum Mol Genet* | Does longer telomere length raise lung cancer risk, and does it differ by subtype? | McKay 2017 lung GWAS (GCST004748/4744/4750) |
| `paper_2` | Kachuri et al. 2019, *Int J Epidemiol* | Same, plus head-and-neck cancer | Above + OncoArray oral/pharyngeal GWAS (GCST012234/5) |

The exposure (telomere-length SNP effects) comes from Zhang 2015 Table 2.

## Results

All values are odds ratios per 1 kb longer telomere length (95% CI). Agent = Claude Sonnet 5, baseline (no workflow).

**Paper 1: Zhang 2015**

| Outcome | Published | Our replication | Agent | Agent matches published? |
|---|---|---|---|---|
| Lung overall | 1.65 (1.39–1.96) | 1.43 (1.26–1.63) | 1.58 (1.26–1.97) | ✓ |
| Adenocarcinoma | 2.87 (2.20–3.74) | 2.75 (2.35–3.23) | 3.05 (1.99–4.67) | ✓ |
| Squamous | 1.04 (0.79–1.36), null | 0.96 (0.80–1.16), null | 0.96 (0.81–1.14), null | ✓ |
| Adeno, TERT excluded | 2.00 (1.48–2.70) | 2.13 (1.78–2.55) | 2.13 (1.79–2.53) | ✓ |

**Paper 2: Kachuri 2019.** The paper's 5p15.33 instrument is not public, so the target is our 7-SNP replication.

| Outcome | Published (8 instruments) | Our replication (7 SNPs) | Agent | Agent matches replication? |
|---|---|---|---|---|
| Lung overall | 1.39 (1.21–1.60) | 1.47 (1.28–1.68) | 1.46 (1.28–1.66) | ✓ |
| Adenocarcinoma | 1.83 (1.51–2.22) | 2.15 (1.78–2.59) | 2.12 (1.78–2.54) | ✓ |
| Squamous | 1.04 (0.83–1.29), null | 0.92 (0.74–1.15), null | 0.92 (0.75–1.13), null | ✓ |
| Head-and-neck | 0.90 (0.70–1.15), null | 0.90 (0.63–1.27), null | 1.31 (0.94–1.82), null | ✗ direction |

**Score so far:** direction 7/8, significance 8/8. With the workflow: *pending*.

**Baseline agent errors.** All were in instrument selection and harmonisation (stages 3, 5, 6); the statistics were right.
- **Kept correlated SNPs** in both papers. Zhang dropped 2 for LD; the agent kept all 11.
- **Matched palindromic SNP PXK (A/T) on letters, not allele frequency.** It is strand-flipped in the head-and-neck files.
- **Invented a proxy SNP** by physical proximity, which counted the ZNF676 locus twice.

The last two flip the head-and-neck result: 1.31 → 1.04 after fixing PXK → 0.90 after dropping the proxy. The workflow adds explicit rules for all three.

## Repo layout

```
replication/            Hand replications (ground truth for scoring)
  common/mr_methods.py    IVW, MR-Egger, weighted median, harmonisation
  zhang2015/, kachuri2019/
    paper_card.md         Paper's decisions by stage, published numbers, our scorecard
    data/  scripts/  results/
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
