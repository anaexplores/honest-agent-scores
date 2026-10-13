"""Check your own leaderboard: run the study's tests on any per-trial results.

Input: a CSV with columns model, task, reward (reward >= 1 counts as a success; empty counts as 0), with at
least 5 trials per task for every model. Models are any unit you compare (model x harness x effort).
Optional: a JSON list of known defective tasks (keys false_positive / false_negative).

Runs:
  * ranking by pass@1 and pass^5;
  * Q1-Q3 (if --defects): does removing defective tasks change the ranking more than removing random tasks?
  * Q4: does ranking by pass^5 differ from pass@1 beyond noise?
  * Q5: does the repeat correlation (ICC) differ between models beyond noise?
  * power: how large a difference your number of tasks can resolve.

    python check_leaderboard.py --trials my_trials.csv [--defects my_defects.json] --out-dir report/
Writes report/report.json and report/report.md. Uses the same code, seeds and settings as the study.
"""
import argparse
import os
import sys
from collections import defaultdict

from common import load_trials, load_defects, write_json
import q1_q3_defects
import q4_repeats
import q5_icc_heterogeneity
import power_table

K = 5


def normalise(S):
    """Keep tasks where every model has >= K trials; use the first K trials of each."""
    models = sorted(S)
    tasks = sorted(set.intersection(*({t for t, v in S[m].items() if len(v) >= K} for m in models)))
    dropped = sorted(set().union(*(set(S[m]) for m in models)) - set(tasks))
    out = defaultdict(dict)
    for m in models:
        for t in tasks:
            out[m][t] = S[m][t][:K]
    return out, tasks, dropped


def fmt_pct(x):
    return f'{100 * x:.1f}%'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--defects'); ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    S, tasks, dropped = normalise(load_trials(a.trials))
    if len(S) < 3 or len(tasks) < 10:
        sys.exit(f'Need at least 3 models and 10 tasks with >= {K} trials each; got {len(S)} models, {len(tasks)} tasks.')
    rep = {'models': len(S), 'tasks': len(tasks), 'trials_per_task': K, 'tasks_dropped_for_missing_trials': dropped}
    md = [f'# Leaderboard check', '', f'{len(S)} models x {len(tasks)} tasks x {K} trials.'
          + (f' {len(dropped)} tasks dropped because some model had fewer than {K} trials.' if dropped else ''), '']

    q4 = q4_repeats.analyze(S); rep['q4_repeats'] = q4
    md += ['## Ranking', '', '| model | pass@1 | pass^5 | pass^5 / pass@1 |', '|---|---|---|---|']
    for m in q4['rank_pass1']:
        p = q4['per_model'][m]
        md.append(f"| {m} | {fmt_pct(p['pass@1'])} | {fmt_pct(p['pass^5'])} | {p['ratio_pass5_to_pass1']} |")

    pw = power_table.analyze(S); rep['power'] = pw
    row = next(r for r in pw['table'] if r['tasks'] == len(tasks))
    md += ['', '## How much your benchmark can resolve', '',
           f"With {len(tasks)} tasks, a pass@1 difference smaller than about **{row['pass1_tie_halfwidth_pp']} points** between two models "
           f"is within noise (median 95% interval half-width across pairs); pass^5 differences below about **{row['pass^5_tie_halfwidth_pp']} points** likewise. "
           f"To detect a difference with 80% power you need about {row['pass1_mdd80_pp']} points (pass@1).", '',
           '| tasks | pass@1 tie zone (+- pp) | pass^5 tie zone (+- pp) |', '|---|---|---|']
    for r in pw['table']:
        md.append(f"| {r['tasks']} | {r['pass1_tie_halfwidth_pp']} | {r['pass^5_tie_halfwidth_pp']} |")

    if a.defects:
        FP, FN = load_defects(a.defects)
        FP &= set(tasks); FN &= set(tasks)
        if FP or FN:
            q1 = q1_q3_defects.analyze(S, FP, FN); rep['q1_q3_defects'] = q1
            v = q1['q1']
            md += ['', '## Do known defects change the ranking? (Q1-Q3)', '',
                   f"Removing the {len(FP | FN)} flagged tasks causes {v['inversions_obs']} rank inversions; removing the same number of random tasks "
                   f"gives a median of {v['null_median']} (95th percentile {v['null_p95']}); p = {v['p']}. "
                   + ('**The ranking changes more than chance.**' if v['verdict_changes_ranking'] else 'No change beyond chance was detected (this test cannot detect a shift of one or two places).'),
                   f"Median ICC with and without flagged tasks: {q1['q2']['icc_median_all']} vs {q1['q2']['icc_median_clean']} (null 95% range of the change {q1['q2']['null_delta_ci95']})."]

    sig = [p for p in q4['reversed_pairs'] if p['passk_significant'] and p['k'] == 5]
    md += ['', '## Does reliability on repeats change the ranking? (Q4)', '',
           f"{len(q4['reversed_pairs'])} pairs change order between pass@1 and pass^3/pass^5; {len(sig)} of them significantly for pass^5."]

    q5 = q5_icc_heterogeneity.analyze(S); rep['q5_icc'] = q5
    m5 = q5['main_mean_center']
    md += ['', '## Do models differ in how correlated their repeats are? (Q5)', '',
           f"ICC by model ranges from {min(m5['icc'].values())} to {max(m5['icc'].values())}; variance {m5['V_obs']} vs null median {m5['V_null_median']}; p = {m5['p']}. "
           'Caution: in the study, such differences on Terminal-Bench 2.0 disappeared once defective tasks and the weakest models were removed. '
           'Audit tasks before claiming that one agent is more reliable than another.']
    write_json(rep, os.path.join(a.out_dir, 'report.json'))
    with open(os.path.join(a.out_dir, 'report.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
