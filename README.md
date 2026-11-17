# CS224V: Expert Analysis Workflows for a Scientific Agent

## Project

- **Question:** Given a research question and a public dataset, can an AI agent pick and run the right analysis and reach the answer an expert would? Teams build on SHELDON, a scientific reasoning agent that proposes competing hypotheses and gathers evidence to tell them apart.
- **Approach:** Write an expert analysis workflow as a step-by-step procedure the agent follows. Each step lists its checks and what to report, and the agent records which step supports each conclusion.
- **Tracks:** (A) survival analysis on TCGA Pan-Cancer clinical data, (B) differential expression on GEO count matrices, (C) risk-of-bias trial appraisal against Cochrane judgments, (D) learning a workflow automatically from the agent's failures, e.g. by adapting Self-Guided Self-Play. Teams can also propose their own workflow and dataset.
- **Evaluation:** 20–30 research questions whose answers come from published papers that used public data. The agent gets the question and the data but not the paper. Its answer is scored on direction, significance and effect size (or gene overlap, or domain-level agreement for track C).
- **Quarter goal:** A written workflow, the evaluation set, and a measurement of how often the agent is correct with and without the workflow. For track D, a learned workflow compared against a hand-written one.

## This repo: two-sample Mendelian randomization (MR)

This repo builds a workflow for **two-sample summary-data Mendelian randomization**. It starts by hand-replicating published MR papers on public GWAS summary statistics, which gives the evaluation set its ground truth. It also shows which stage decisions (instrument selection, proxies, palindromic SNPs, sensitivity analyses) the workflow has to cover.

```
replication/
  common/mr_methods.py      Shared estimators: IVW (fixed / mult. RE), MR-Egger, weighted median,
                            harmonisation, SE-from-P/CI, fixed-effect meta-analysis
  zhang2015/                Zhang et al. 2015 (Hum Mol Genet): telomere length -> lung cancer
  kachuri2019/              Kachuri et al. 2019 (Int J Epidemiol): telomere length -> lung & head-and-neck cancer
    paper_card.md           Paper metadata, the paper's decisions across 10 workflow stages,
                            ground-truth estimates, our replication scorecard and logged decisions
    data/                   Exposure SNP effects (from the paper) and raw/ outcome GWAS extracts
    scripts/                Fetch + analysis scripts
    results/                mr_results.tsv, harmonised_*.tsv, run_log.txt (stage-by-stage audit trail)
```

Outcome data come from the GWAS Catalog: McKay 2017 ILCCO/OncoArray lung (GCST004748 / 004744 / 004750) and OncoArray oral/pharyngeal cancer (GCST012234 / 012235).

### Running

```bash
cd replication/zhang2015
bash scripts/fetch_outcomes.sh data/raw          # streams lung GWAS, keeps instrument SNPs only
python3 -I scripts/mr.py data/exposure_zhang2015_table2.tsv data/raw results

cd ../kachuri2019
python3 scripts/mr_kachuri.py ../zhang2015/data/exposure_zhang2015_table2.tsv data/raw results
```

Requires Python 3 with `numpy`, `pandas` and `scipy`.

### Replication status (2026-11-12)

| Paper | Outcomes | Direction | Significance | Published OR in our 95% CI |
|---|---|---|---|---|
| Zhang 2015 (IVW) | lung all / adeno / squamous / adeno w/o TERT | 4/4 | 4/4 | 3/4 (lung overall: 1.43 vs 1.65, TERT SNP missing from the outcome file) |
| Kachuri 2019 (IVW + WM) | lung all / adeno / squamous / HNC | 8/8 | 7/8 (HNC weighted median P=0.08 vs 0.04) | 8/8 |

Caveats: both replications use the same McKay 2017 lung data, so they aren't independent. Kachuri's 5p15.33 score comes from non-public sequencing data, so its estimates are taken from the paper's Table 3 rather than rebuilt. See each `paper_card.md` for everything not replicated.

## References

- Joshi, Shethia, Lam. *Sheldon: Reasoning through Dual Search over Hypotheses and Observation Spaces* (submitted).
- Liu et al. *An Integrated TCGA Pan-Cancer Clinical Data Resource…* Cell 2018.
- NCBI GEO: https://www.ncbi.nlm.nih.gov/geo/
- *Cochrane Handbook for Systematic Reviews of Interventions* (RoB 2).
- Bailey, Wen, Dong, Hashimoto, Ma. *Scaling Self-Play with Self-Guidance.* arXiv:2604.20209, 2026.
- Zhang et al. *Genetic determinants of telomere length and risk of common cancers: a Mendelian randomization study.* Hum Mol Genet 2015.
- Kachuri et al. *Mendelian randomization and mediation analysis of leukocyte telomere length and risk of lung and head and neck cancers.* Int J Epidemiol 2019.
