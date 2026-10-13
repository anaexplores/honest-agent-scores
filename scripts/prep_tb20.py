"""Prepare Terminal-Bench 2.0 trials for the ICC tests (same format as the TB 4.0 file).

A configuration = agent x model. Kept: configurations with >= 5 trials on at least all-but-one of the tasks;
tasks = the intersection of their coverage; the first 5 trials per task in file order.
(The plan first required all 89 tasks; no configuration qualified because one task is missing almost
everywhere, so the rule was relaxed to 88 before any result was computed.)

    python prep_tb20.py --trials data/tb20_trials.csv --out data/tb20_q5_trials.csv
"""
import argparse
import csv
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    S = defaultdict(lambda: defaultdict(list))
    tasks = set()
    for r in csv.DictReader(open(a.trials, encoding='utf-8')):
        S[f"{r['agent']} | {r['model']}"][r['task_name']].append(r['reward'])
        tasks.add(r['task_name'])
    full5 = {c: {t for t, v in S[c].items() if len(v) >= 5} for c in S}
    keep = [c for c in sorted(S) if len(full5[c]) >= len(tasks) - 1]
    tasks = set.intersection(*(full5[c] for c in keep))
    print(f'configs total {len(S)}; eligible {len(keep)}; common tasks {len(tasks)}')
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['model', 'task', 'reward'])
        for c in keep:
            for t in sorted(tasks):
                for x in S[c][t][:5]:
                    w.writerow([c, t, x])


if __name__ == '__main__':
    main()
