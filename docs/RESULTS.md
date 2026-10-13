# Results

Analysis plan: [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) (fixed before each analysis was run). An internal critical review of the conclusions was done before publication; the wording below is the weakened form that survived it. Results labelled **exploratory** were not in the plan and were chosen after seeing the data.

**Verdict.** No effect was detected with 10 model x harness configurations and 66 tasks. The claim that defects or repeats change which agent is best is **not supported, but not ruled out**: the tests have little power against an effect of one or two rank places. One candidate effect on a single pair is exploratory.

## Data

- Per-trial Terminal-Bench 4.0 results are public on Harbor Hub: each public job page returns all trials page by page. `scripts/fetch_tb40_trials.py` writes `data/tb40_trials.csv`.
- 10 submissions x 330 trials = 3,300. Checks: successes match the leaderboard for all 10; trial ids match the lists in the submission files.
- All 10 jobs use one task set (`dataset_version sha256:39d9f44b...`). That this is exactly the 4.0.0 version Epoch reviewed (2026-09-04) is a strong inference from the leaderboard and dates, not stated by a source.
- 11 submissions were private on Harbor Hub and are not included; selection by public availability is possible.
- 124 of 3,300 trials (3.8%) ended with an error, 49 of them timeouts; per leaderboard rules they count as 0, which penalises pass^5 more than pass@1.
- The `attempt` field is 1 for every trial, so independence of repeats within a task cannot be checked.
- Cross-check with an earlier ICC estimate on this benchmark: ICC for Fable 5.1 = 0.5074 and Gemini 3.8 Flash = 0.377, identical to four decimals.

## Q1. Do Epoch's defect flags change the ranking? (`results/q1_q3_defects.json`)

Removing the 30 flagged tasks gives 3 rank inversions; removing 30 random tasks gives a median of 1 and a 95th percentile of 3; **p = 0.116**. Three pairs flip, none significantly on the 36 remaining tasks. Separately (exploratory, `results/exploratory_checks.json`): false positives only (19 tasks) give 1 inversion, p = 0.81; false negatives only (11 tasks) give 0 inversions.

- Wording: the defects change the ranking **no more than removing random tasks**; this test cannot detect a shift of one or two places.
- Every configuration gains 3 to 17 points on the unflagged tasks, but because the flagged tasks are **harder** (pooled success 0.27), not because the score was "corrected". An absolute "clean score" without reweighting is misleading.
- **Exploratory** (chosen after the fact, 1 pair of 45, no multiplicity correction): Fable 5.1 vs GPT-6 Sol is +8.5 points on all tasks and -3.9 on the unflagged ones; the paired shift is **-12.4 points, 95% CI [-21.9, -3.8]**. GPT-6 Sol gains the most (+16.7 points); it does particularly badly on the flagged tasks (FP 0.37, FN 0.16). A candidate to check on new data, not a conclusion.

## Q2. Do the defects inflate the repeat correlation (ICC)?

Median ICC goes from 0.522 to 0.532; the difficulty-matched null range is [-0.072, +0.067]; p = 0.60. Per configuration, changes range from -0.12 to +0.09.

- Wording: **a drop in median ICC of more than about 0.07 due to the defects is ruled out**; a small effect is not. Limitation from the internal review: difficulty is matched on the pooled success rate, while the ICC of binary outcomes depends on each configuration's own rate; for weak configurations (11-19% success) the null is matched less well.
- The ICC of about 0.5 on TB 4.0 is not explained by task defects within this precision. Median across these 10 configurations: 0.52.

## Q3. Who benefits from false positives?

All 10 configurations succeed **less** often on false-positive tasks than on unflagged ones (by 2 to 29 points); the difference does not vary between configurations significantly (p = 0.40).

- Wording: **false-positive tasks are on average harder than unflagged tasks.** It does **not** follow that nobody exploits the defects: a false positive is a hole in the verifier that may affect some trials, and mean success rates cannot see it; trajectories would be needed. Identical signs across configurations reflect that models agree on which tasks are hard; they are not 10 independent pieces of evidence. Consistent with the contributor's claim of fewer than 3% of runs affected, but not proof of it.

## Q4. Does reliability on repeats change the ranking? (`results/q4_repeats.json`)

The rankings by pass^5 and by pass@1 nearly coincide; four pairs reverse, none significantly.

- The ratio pass^5 / pass@1 varies widely: Opus 5.5 0.72, GPT-6.1 Sol 0.68, GPT-6 Sol 0.61, Fable 5.1 0.50, GLM 5.3 Flash 0.34, Qwen 3.8 Max 0.17, Muse Spark 0.10.
- **Exploratory:** Fable 5.1 and GPT-6.1 Sol are equal on pass@1 (0.579 vs 0.582) but differ on pass^5 (0.29 vs 0.39): -10.6 points, 95% CI [-22.7, +1.5], not significant. The planned criterion (reversed order) did not cover this "equal pass@1" case; that is a weakness of the design, noted by the internal review.
- The units compared are model x harness x effort configurations (claude-code, codex, mini-swe-agent, muse-code), not models.

## Q5. Does the repeat correlation differ between configurations beyond noise? (`results/q5_icc_*.json`, `results/icc_slope_sensitivity.json`, `results/q5_task_removal_control.json`, `results/q5_task_removal_matched.json`)

Null: each configuration keeps its own pass@1, one common ICC, beta-binomial trials.

**Correction (2026-10-13).** The first published TB 2.0 numbers came from a defective download (wrong pages for 1,700 rows, and trials that the source lists twice; see [DATA.md](../DATA.md)). Every TB 2.0 number below is recomputed on the corrected data. The selection rule of the analysis plan (5 trials on all 89 tasks) now applies as written: 60 configurations x 89 tasks (previously 63 x 88 under a relaxed rule that the download error had forced; see [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md)).

| Data | Configurations x tasks | p | Was (defective data) |
|---|---|---|---|
| TB 4.0 | 10 x 66 | 0.075 | 0.075 |
| TB 2.0, first 5 trials (**main test**) | 60 x 89 | **0.0022** | 0.0014 |
| same, median as the common ICC | 60 x 89 | 0.0016 | 0.0018 |
| same, without configurations at pass@1 < 0.13 | 57 x 89 | < 0.0002 (0 of 5,000) | < 0.0002 |
| TB 2.0, 5 random trials (seed 1 / 2) | 60 x 89 | 0.002 / 0.002 | 0.0055 / 0.008 |
| TB 2.0, relaxed selection (>= 88 tasks) | 75 x 78 | < 0.0005 (0 of 2,000) | - |
| TB 2.0 without the 28 tasks changed in 2.1 | 60 x 61 | 0.047 | 0.05 (27 tasks) |
| same, without configurations at pass@1 < 0.1 | 57 x 61 | 0.25 | 0.30 |

The main test and its two robustness checks were planned and use 5,000 simulations; the other TB 2.0 rows were added after the first result was seen and use 2,000. The old "random trials" rows were biased: in 11 configurations the duplicated trials made "5 random trials" partly the same trial twice.

- **By the plan, Q5 is supported** on TB 2.0 (p = 0.0022), and the result holds for the choice of trials, the selection rule, the centre of the null and removing the weakest configurations (without them the differences are stronger, not weaker).
- **It weakens only when the 28 tasks changed in TB 2.1 are removed**: p = 0.047 with all configurations and 0.25 when the weak configurations are also removed. This 0.25 is one of four combinations chosen after the fact (all tasks or without changed tasks, x all configurations or without weak ones); the other three give p <= 0.047.
- **It does not show that ICC is the same for every configuration on that subset.** On the same 57 x 61 subset the ICC still rises with pass@1 (slope 0.12, 95% CI over configurations [0.01, 0.23]; over tasks [-0.10, 0.30]). The test there is inconclusive, not negative. The null "ICC is constant at every pass@1" is also false by construction (ICC rises with pass@1), so a small p alone says only "ICC is not constant".
- **Control for power (exploratory, `scripts/q5_task_removal_control.py`).** Removing tasks lowers the power of the test, so removing 28 random tasks (200 draws, 1,000 simulations each) was compared with removing the 28 changed tasks (also with 1,000 simulations, hence 0.055 here against 0.047 in the table above):

| Configurations | p, changed tasks removed | p, random 28 removed: median [5%, 95%] | Random removals with p at least as large |
|---|---|---|---|
| all (60) | 0.055 | 0.013 [0.001, 0.065] | 9.5% |
| without pass@1 < 0.1 (57) | 0.229 | 0.009 [0.000, 0.169] | 3.5% |

  Removing the changed tasks weakens the differences more than removing most random sets of tasks, so these tasks carry much of the ICC heterogeneity. But they are also much **harder** than a random set (pooled success 0.29, against 0.39-0.52 for 90% of random sets), and no random draw matched their difficulty, so this control alone cannot tell "broken" from "hard".
- **Difficulty-matched control (exploratory, `scripts/q5_task_removal_matched.py`).** Each draw removes 28 unchanged tasks matched one-to-one to the changed tasks by pooled success (nearest unchanged task, without replacement, changed tasks visited in random order; 200 draws, 1,000 simulations each):

| Configurations | p, changed tasks removed | p, matched 28 removed: median [5%, 95%] | Matched removals with p at least as large |
|---|---|---|---|
| all (60) | 0.055 | 0.000 [0.000, 0.002] | 0% |
| without pass@1 < 0.1 (57) | 0.229 | 0.000 [0.000, 0.000] | 0% |

  No matched removal gives p above 0.004, so removing equally hard unchanged tasks does not weaken the differences; if anything they get stronger than after removing random (easier) tasks. Difficulty alone therefore does not explain why the changed tasks carry the ICC heterogeneity. Limits: the unchanged tasks include few very hard ones, so the match is imperfect (pooled success 0.34 for the matched sets against 0.29 for the changed tasks; mean gap per pair 0.05) and nearly fixed (only 10 distinct sets in 200 draws; 26 of the 33 tasks used are in every set). The control was added after the result was seen.
- **Still a hypothesis, now with supporting evidence:** broken tasks may create false "reliability differences" between configurations, because different agents pass or fail a defective task deterministically in different ways. The two controls show that the changed tasks carry the heterogeneity beyond their number and their difficulty; they do not show that the defects are the cause, since the changed tasks may differ from the others in other ways, and the analysis is exploratory. Auditing tasks before claiming that one agent is more reliable than another remains a sensible precaution.

**Slope of ICC on pass@1** (bootstrap over configurations and over tasks):

| Data | Slope | CI over configurations | CI over tasks |
|---|---|---|---|
| TB 4.0 | 0.38 | [0.14, 0.64] | [0.11, 0.71] |
| TB 2.0, all (60 x 89) | 0.42 | [0.28, 0.55] | [0.26, 0.59] |
| TB 2.0 without pass@1 < 0.1 | 0.30 | [0.20, 0.39] | [0.12, 0.47] |
| TB 2.0 without changed tasks | 0.24 | [0.09, 0.37] | [0.07, 0.40] |
| TB 2.0 without changed tasks and weak configurations | 0.12 | [0.01, 0.23] | [-0.10, 0.30] |
| TB 2.0, relaxed selection (75 x 78) | 0.43 | [0.30, 0.55] | [0.24, 0.59] |

- The **direction is stable** (stronger configurations have higher ICC); the **size is not**: from 0.12 to 0.43 depending on the changed tasks and weak configurations. A formula "ICC = 0.4 + 0.4 x pass@1" is not supported; it described one data set, not a regularity.
- **Q5b (exploratory):** residual heterogeneity after accounting for pass@1: TB 4.0 p = 0.41, TB 2.0 p = 0.069 (was 0.059); power was not assessed, so "not detected".
- **Exploratory check of the estimator:** with a constant ICC (0.45 or 0.6) the one-way ANOVA estimator is nearly unbiased across pass@1 from 0.1 to 0.8 (shift at most 0.015), so the slope is not an artefact of the estimator in that range.

## Power: how many tasks a benchmark needs (`results/power_table.json`)

Added during publication (not in the analysis plan). From the 45 pairs of TB 4.0 configurations: bootstrap standard error of the difference at 66 tasks, scaled as sqrt(66 / N). Median across pairs.

| Tasks | pass@1 tie zone (+- points) | pass@1 difference detectable with 80% power | pass^5 tie zone (+- points) |
|---|---|---|---|
| 50 | 10.9 | 15.6 | 12.3 |
| 66 | 9.5 | 13.6 | 10.7 |
| 100 | 7.7 | 11.0 | 8.7 |
| 200 | 5.5 | 7.8 | 6.1 |
| 500 | 3.5 | 4.9 | 3.9 |
| 1000 | 2.4 | 3.5 | 2.7 |

Assumption: new tasks come from the same population; different task mixes change the variance.

## What this means

- **A cleaned score does not change the winner on TB 4.0.** Removing Epoch's defective tasks does not change who is best beyond noise. Claiming "the real leader is different" is not supported by these data.
- **Reliability on repeats does not change the ranking either**, though it is interesting descriptively: at equal pass@1, pass^5 can differ by about 1.4 times. With 66 tasks this is not statistically distinguishable.
- **Power is the main lesson.** With 66 tasks, the 95% interval for the difference between two models is about +-9.5 points on pass@1 and wider on pass^5. Any "honest leaderboard" on a single benchmark of this size will mostly show ties. Real resolution needs pooled benchmarks (several hundred tasks) or one's own task set.
- **For the [Agent Reliability Calculator](https://anaexplores.github.io/agent-reliability-calculator/):** a constant ICC preset of about 0.5-0.6 is adequate. ICC rises with pass@1, but the size of that dependence is unstable (slope 0.12 to 0.43 across the checks above), so the calculator should not introduce a formula for it.

## Open questions

- The Fable 5.1 vs GPT-6 Sol shift (-12.4 points) should be checked on later submissions of the same models or after the 10 pending task fixes.
- Trajectories of false-positive tasks are the only way to tell whether models exploit the defects.
- The 11 private submissions could change the picture if they become public.
