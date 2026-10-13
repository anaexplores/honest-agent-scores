"""Prepare Terminal-Bench 2.0 trials for the ICC tests (same format as the TB 4.0 file).

A configuration = agent x model. Kept (main rule, as in the analysis plan): configurations with >= 5 trials
on all 89 tasks; the first 5 trials per task in source order. With --allow-missing 1 (sensitivity check):
configurations with >= 5 trials on all but at most one task; tasks = the intersection of their coverage.
(The first published version used the relaxed rule because one task seemed missing almost everywhere;
that was a download error, see DATA.md and docs/ANALYSIS_PLAN.md.)

    python prep_tb20.py --trials data/tb20_trials.csv --out data/tb20_q5_trials.csv
"""
import argparse
import csv
from collections import defaultdict


def read_tb20(path):
    """data/tb20_trials.csv -> {'agent | model': {task: [reward, ...]}} in source order, and the set of all tasks."""
    raw = defaultdict(lambda: defaultdict(list)); tasks = set()
    for r in csv.DictReader(open(path, encoding='utf-8')):
        raw[f"{r['agent']} | {r['model']}"][r['task_name']].append(r['reward']); tasks.add(r['task_name'])
    return raw, tasks


def select(raw, all_tasks, allow_missing=0):
    """Configurations with >= 5 trials on all but `allow_missing` tasks, and the sorted common tasks."""
    full5 = {c: {t for t, v in raw[c].items() if len(v) >= 5} for c in raw}
    keep = [c for c in sorted(raw) if len(full5[c]) >= len(all_tasks) - allow_missing]
    return keep, sorted(set.intersection(*(full5[c] for c in keep)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--allow-missing', type=int, default=0)
    a = ap.parse_args()
    raw, all_tasks = read_tb20(a.trials)
    keep, tasks = select(raw, all_tasks, a.allow_missing)
    print(f'configs total {len(raw)}; tasks total {len(all_tasks)}; eligible {len(keep)}; common tasks {len(tasks)}')
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['model', 'task', 'reward'])
        for c in keep:
            for t in tasks:
                for x in raw[c][t][:5]:
                    w.writerow([c, t, x])


if __name__ == '__main__':
    main()
