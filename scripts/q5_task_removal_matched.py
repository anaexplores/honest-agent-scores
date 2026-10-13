"""Difficulty-matched control for the Q5 result on TB 2.0 without the tasks changed in TB 2.1 (added after the fact; exploratory).

The random control (q5_task_removal_control.py) removes sets of tasks that are much easier than the changed
tasks, so it cannot tell "broken" from "hard". Here each draw removes 28 UNCHANGED tasks matched one-to-one
to the 28 changed tasks by pooled success (mean over all trials of the 60 configurations): the changed tasks
are visited in a random order and each takes the nearest unchanged task still available (without
replacement; ties broken at random). 200 draws, fixed seed, tasks sorted before sampling. Every Q5 test uses
1,000 simulations, with and without configurations at pass@1 < 0.1, exactly as in the random control.

    python q5_task_removal_matched.py --tb20 data/tb20_trials.csv --tb21-changed data/tb21_changed_tasks.json \
        --out results/q5_task_removal_matched.json
"""
import argparse
import json
import random
from multiprocessing import Pool
from statistics import mean

import q5_task_removal_control as ctl
from common import write_json

NDRAW, SEED = 200, 20261014


def match(changed, unchanged, ps, rnd):
    avail, removed = list(unchanged), []
    for c in rnd.sample(changed, len(changed)):
        d = min(abs(ps[u] - ps[c]) for u in avail)
        u = rnd.choice([u for u in avail if abs(ps[u] - ps[c]) - d < 1e-12])
        avail.remove(u); removed.append((c, u))
    return removed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tb20', required=True); ap.add_argument('--tb21-changed', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    ctl.init(a.tb20)
    S = ctl.S_ALL
    tasks = sorted(next(iter(S.values())))
    changed = sorted(set(json.load(open(a.tb21_changed, encoding='utf-8'))['tasks']) & set(tasks))
    unchanged = [t for t in tasks if t not in changed]
    ps = {t: mean(x for m in S for x in S[m][t]) for t in tasks}
    rnd = random.Random(SEED)
    pairs = [match(changed, unchanged, ps, rnd) for _ in range(NDRAW)]
    draws = [frozenset(u for _, u in p) for p in pairs]
    jobs = [(0, frozenset(changed))] + [(i + 1, d) for i, d in enumerate(draws)]
    with Pool(a.workers, initializer=ctl.init, initargs=(a.tb20,)) as pool:
        res = pool.map(ctl.one, jobs, chunksize=1)
    obs, mat = res[0], res[1:]
    summary = {}
    for cut in ('pass1>=0.0', 'pass1>=0.1'):
        ps_ = sorted(r[cut]['p'] for r in mat)
        summary[cut] = {'p_changed_tasks_removed': obs[cut]['p'], 'n_configs_changed_tasks_removed': obs[cut]['n'],
                        'matched_p_median': ps_[len(ps_) // 2], 'matched_p_q05': ps_[int(.05 * len(ps_))],
                        'matched_p_q95': ps_[int(.95 * len(ps_)) - 1],
                        'share_matched_p_below_0.05': round(sum(p < 0.05 for p in ps_) / len(ps_), 3),
                        'share_matched_p_at_least_changed': round(sum(p >= obs[cut]['p'] for p in ps_) / len(ps_), 3)}
    sr = sorted(r['pooled_success_removed'] for r in mat)
    gap = sorted(mean(abs(ps[c] - ps[u]) for c, u in p) for p in pairs)
    use = sorted(((t, sum(t in d for d in draws)) for t in unchanged), key=lambda x: (-x[1], x[0]))
    write_json({'exploratory': True, 'n_tasks': len(tasks), 'n_removed': len(changed), 'n_draws': NDRAW,
                'nsim': ctl.NSIM, 'seed_matching': SEED, 'n_distinct_matched_sets': len(set(draws)),
                'changed_tasks_removed': changed, 'summary': summary,
                'pooled_success_removed': {'changed_tasks': obs['pooled_success_removed'], 'matched_median': sr[len(sr) // 2],
                                           'matched_q05': sr[int(.05 * len(sr))], 'matched_q95': sr[int(.95 * len(sr)) - 1]},
                'mean_abs_gap_per_pair': {'median': round(gap[len(gap) // 2], 4), 'max': round(gap[-1], 4)},
                'unchanged_task_use_count': {t: n for t, n in use if n},
                'changed_tasks_result': obs,
                'matched_draws': [dict(r, removed=sorted(d), pairs=sorted(p)) for r, d, p in zip(mat, draws, pairs)]}, a.out)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
