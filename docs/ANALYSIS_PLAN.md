# Analysis plan

This plan was written before each analysis was run and kept in the author's private version history, with dated additions below. It was not registered on an external preregistration platform, so it should be read as "analysis plan fixed before running the analysis", not as a formal preregistration. Additions made after earlier results were seen are marked with their date and with what was already known at that point.

Date of the original plan: 2026-10-12.

## 1. Questions

- **Q1.** Does removing the Terminal-Bench 4.0 tasks that Epoch AI flagged as defective change the ranking of models more than removing the same number of random tasks?
- **Q2.** Is the repeat correlation (ICC) without the flagged tasks lower than with all tasks, by more than removing random tasks of matched difficulty would cause?
- **Q3 (descriptive).** Who benefits from the defects: does "success on false-positive tasks minus success on unflagged tasks" differ between models?

## 2. Why

A common pitch for an "honest leaderboard" is that cleaning a benchmark of defective tasks would show a different winner. A Terminal-Bench contributor stated that the defects affect fewer than 3% of runs and stay within the published intervals (secondary source). If the ranking does not change, the value of a cleaned score lies in absolute levels, not in who is best. Q2 checks whether an earlier estimate of the repeat correlation on this benchmark (median ICC 0.49 across 13 submissions) is inflated by the defects.

## 3. Data

- 3,300 trials: 10 model x harness configurations x 66 tasks x 5 trials, read from public Harbor Hub job pages on 2026-10-12 (`scripts/fetch_tb40_trials.py`). Check: the number of successes matches the leaderboard for all 10. Eleven other submissions were not public on Harbor Hub and are not included.
- Defects: Epoch AI Benchmark Review of Terminal-Bench 4.0.0 (2026-09-04): 19 false positives (FP) and 11 false negatives (FN). The review is partial, so the other 36 tasks are unreviewed, not known to be clean.

## 4. Method and criteria (fixed before running)

- **Q1.** Rank models by mean success. Distance = number of pairwise inversions (Kendall) between the ranking on all 66 tasks and on the 36 unflagged tasks. Null: 10,000 random sets of 30 tasks removed. p = share of null draws with at least as many inversions.
  - Also: pairs of models whose order flips and whose difference after removal falls outside a 95% bootstrap interval over tasks.
  - **Criterion "defects change the ranking":** p < 0.05 or at least one significantly flipped pair. Otherwise H0: on these 10 configurations the ranking is stable, and the "who is really best" pitch is not supported.
- **Q2.** One-way ANOVA ICC per model; median across models. Null: 10,000 random sets of 30 tasks with mean success matched to the flagged tasks (tolerance +-0.03, pooled across models). **Criterion:** the drop in median ICC lies outside the 95% null range.
- **Q3.** Per model: success on the 19 FP tasks minus success on the 36 unflagged tasks. Descriptive, plus a permutation test of heterogeneity between models. This is not evidence of reward hacking: an FP task also passes an honest solution.

## 4a. Addition (fixed after Q1-Q3, before running Q4)

Q1 returned H0 under its criterion, so the second part of the claim, accounting for repeats, is tested.

- **Q4.** Does ranking by reliability (pass^5, the share of tasks solved in all 5 trials; pass^3 as a check) differ from ranking by pass@1 by more than noise?
  - For each pair whose order by pass@1 and by pass^5 is reversed: bootstrap over tasks (2,000) for the pass^5 difference. **Criterion "repeats change the ranking":** at least one reversed pair whose 95% interval for the pass^5 difference excludes 0 while the pass@1 difference of the same pair is not significant in the opposite direction (otherwise the two orderings are both significant; this also counts and is reported separately).
  - Otherwise H0: on these 10 configurations pass@1 and pass^5 rank alike within noise.

## 4b. Addition 2 (fixed on 2026-10-12 after Q4 and an internal critical review, before running Q5)

The pairwise tests of Q4 have low power (45 pairs, 66 tasks). No second benchmark with public per-trial results for the same models was found in the Harbor ecosystem. Hence one pooled test on the same data.

- **Q5.** Is the repeat correlation (ICC) a property of the model x harness configuration, that is, does it differ between the 10 configurations by more than task sampling explains?
  - Statistic (chosen before running; bootstrapping the SE inside every simulation was too slow): V = variance of the per-configuration ICC.
  - Parametric null: for each configuration, 66 tasks with success probabilities pi_t ~ Beta with mean = that configuration's pass@1 and ICC = the mean ICC across configurations, then 5 Bernoulli trials. Same correlation for all, each at its own success level. 5,000 simulations give the distribution of V; p = share of simulated V >= observed V.
  - Robustness: the same with the median ICC; and without the two weakest configurations (pass@1 < 0.13), where ICC is poorly defined.
  - **Criterion "reliability is a property of the configuration":** p < 0.05. Otherwise H0.
  - Why ICC and not pass^5 / pass@1: that ratio depends mechanically on the pass@1 level (it is lower for weak models at any correlation); ICC depends on the level less, and the null keeps each configuration's level.

## 4c. Replication of Q5 on a second benchmark (fixed on 2026-10-12 after Q5 on TB 4.0, before running)

Q5 on TB 4.0 gave p = 0.075 (H0 under the criterion); without the two weakest configurations, p = 0.029. No second set of public per-trial results for September 2026 models was found (Terminal-Bench 2.1 and Harbor Index jobs were private; other leaderboards publish aggregates only). Q5 is a general question about configurations, so the same models are not needed.

- **Data:** Terminal-Bench 2.0 (89 tasks), Hugging Face `yoonholee/terminalbench-trajectories` (Apache-2.0, last modified 2026-03-09); models up to spring 2026, so tasks and configurations are independent of TB 4.0.
- **Selection (before running):** configuration = agent x model; keep configurations with at least 5 trials on all 89 tasks; use the first 5 trials per task in file order.
  - **Change of selection (after counting coverage, before computing any result):** no configuration met the "all 89 tasks" rule because one task is missing almost everywhere. New rule: configurations with at least 5 trials on at least 88 tasks (63 configurations); tasks = the intersection of their coverage.
  - **Correction (2026-10-13, after the first results were published, before any result on the corrected data was computed):** the missing task was an artefact of our download, not of the dataset: the server returned wrong pages for offsets 3,500-5,199, and the 600 lost rows were mostly `caffe-cifar-10`. The source also lists every trial twice in 11 configurations (see [DATA.md](../DATA.md)). On the corrected, deduplicated data the original rule works: 60 configurations have at least 5 trials on all 89 tasks. Since the only reason for the change no longer holds, the **original rule is restored as the main analysis**; the relaxed rule (at least 88 tasks: 75 configurations x 78 common tasks) is reported as a sensitivity check. The results computed on the defective download are superseded.
- **Test:** the same code and criterion as Q5. Main test: all selected configurations; robustness: without configurations at pass@1 < 0.13.
- **Overall Q5 conclusion:** "reliability is a property of the configuration" is supported if p < 0.05 on TB 2.0 (main test). If p >= 0.05 on TB 2.0, H0 on both benchmarks.

## 5. Limitations known in advance

- 10 configurations, 66 tasks: low power; "no effect detected" is not "no effect".
- Only the defects Epoch found are flagged; the 36 unreviewed tasks may contain defects too, so any effect is underestimated.
- FN tasks may simply be hard: removing hard tasks changes means and ICC by itself, hence the difficulty-matched null in Q2.
