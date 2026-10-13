# Data

| Data | Source | License / terms | Retrieved | In this repository | How to get it |
|---|---|---|---|---|---|
| Terminal-Bench 4.0 per-trial results (3,300 trials: 10 configurations x 66 tasks x 5) | Public job pages on Harbor Hub, linked from the leaderboard at [harbor-framework/terminal-bench](https://github.com/harbor-framework/terminal-bench/tree/main/leaderboard/submissions) | Leaderboard repository: Apache-2.0. Trial results on Harbor Hub belong to the submitters; the [Harbor Hub terms](https://hub.harborframework.com/terms) (updated 2026-07-10) grant no public license and do not address third-party redistribution. | 2026-10-12 | **Not included.** The list of the 10 submissions, their job ids and the SHA-256 of the CSV are in `data/tb40_submissions.json`. | `python scripts/fetch_tb40_trials.py --manifest data/tb40_submissions.json --out data/tb40_trials.csv` (the script checks the SHA-256) |
| Terminal-Bench 2.0 trial outcomes (52,104 trials; columns task_name, agent, model, reward) | Hugging Face [yoonholee/terminalbench-trajectories](https://huggingface.co/datasets/yoonholee/terminalbench-trajectories) | Apache-2.0 | 2026-08-04 (dataset last modified 2026-03-09) | `data/tb20_trials.csv` (trajectories and token counts dropped) | Included; or `python scripts/fetch_tb20_trials.py --out data/tb20_trials.csv` |
| Defective tasks in Terminal-Bench 4.0.0 (19 false positives, 11 false negatives) | [Epoch AI Benchmark Review](https://epoch.ai/benchmarks/terminal-bench-4/review), review dated 2026-09-04 | Facts (task names) with attribution | 2026-10-12 | `data/epoch_defects_tb40.json` | Included |
| Tasks changed in Terminal-Bench 2.1 (28) | [Terminal-Bench 2.1 release notes](https://www.tbench.ai/news/terminal-bench-2-1) | Facts (task names) with attribution | 2026-10-12 | `data/tb21_changed_tasks.json` | Included |

## Notes

- **Availability risk.** The Terminal-Bench 4.0 trials stay with Harbor Hub. On 2026-10-12, 11 of the 21 leaderboard submissions were already private there, and the remaining 10 can become private at any time. If `fetch_tb40_trials.py` fails or the checksum differs, the published results in `results/` cannot be recomputed from scratch; the aggregate outputs remain.
- **Which trials count.** A trial counts as a success when reward >= 1. Errored trials (124 of 3,300, of which 49 timeouts) have no reward and count as failures, as on the leaderboard. This penalises pass^5 more than pass@1.
- **Repeat independence.** The `attempt` field is 1 for every trial, so whether the 5 trials of a task ran independently cannot be checked from the data.
- **Benchmark version.** All 10 jobs report the same task-set hash (`sha256:39d9f44b...`). That this is exactly the version Epoch reviewed (4.0.0) is inferred from the leaderboard and the dates, not stated by a source.
- **Selection.** Only public submissions could be used; if public and private submissions differ systematically, the sample is biased.
