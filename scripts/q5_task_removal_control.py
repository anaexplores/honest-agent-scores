"""Control for the Q5 result on TB 2.0 without the tasks changed in TB 2.1 (added after the fact; exploratory).

Removing any tasks lowers the power of the Q5 test, so a larger p without the changed tasks may only mean
fewer tasks. Control: remove the same number of RANDOM tasks (200 draws, fixed seed, tasks sorted before
sampling) and compare the Q5 p-values with the p from removing the changed tasks. Both with and without
configurations at pass@1 < 0.1 (the cut is applied on the remaining tasks, as in icc_slope_sensitivity.py).
Every Q5 test here uses 1,000 simulations, including the one on the changed tasks, so all p-values share one
resolution. Also reported: pooled success on the removed tasks, since removing hard or easy tasks changes ICC.

    python q5_task_removal_control.py --tb20 data/tb20_trials.csv --tb21-changed data/tb21_changed_tasks.json \
        --out results/q5_task_removal_control.json
"""
import argparse
import json
import random
from multiprocessing import Pool
from statistics import mean

import q5_icc_heterogeneity as q5
from common import write_json
from icc_slope_sensitivity import load20

NDRAW, NSIM, SEED = 200, 1000, 20261013
S_ALL = None


def init(path):
    global S_ALL
    S_ALL = load20(path, 'first')


def one(job):
    i, removed = job
    S = {m: {t: v for t, v in S_ALL[m].items() if t not in removed} for m in S_ALL}
    out = {'pooled_success_removed': round(mean(x for m in S_ALL for t in removed for x in S_ALL[m][t]), 4)}
    for cut in (0.0, 0.1):
        ms = [m for m in sorted(S) if mean(x for t in S[m] for x in S[m][t]) >= cut]
        r = q5.test(S, ms, mean, random.Random(SEED + i), nsim=NSIM)
        out[f'pass1>={cut}'] = {'n': len(ms), 'p': r['p'], 'V_obs': r['V_obs']}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tb20', required=True); ap.add_argument('--tb21-changed', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    init(a.tb20)
    tasks = sorted(next(iter(S_ALL.values())))
    changed = sorted(set(json.load(open(a.tb21_changed, encoding='utf-8'))['tasks']) & set(tasks))
    rnd = random.Random(SEED)
    draws = [frozenset(rnd.sample(tasks, len(changed))) for _ in range(NDRAW)]
    jobs = [(0, frozenset(changed))] + [(i + 1, d) for i, d in enumerate(draws)]
    with Pool(a.workers, initializer=init, initargs=(a.tb20,)) as pool:
        res = pool.map(one, jobs, chunksize=1)
    obs, rand = res[0], res[1:]
    summary = {}
    for cut in ('pass1>=0.0', 'pass1>=0.1'):
        ps = sorted(r[cut]['p'] for r in rand)
        summary[cut] = {'p_changed_tasks_removed': obs[cut]['p'], 'n_configs_changed_tasks_removed': obs[cut]['n'],
                        'random_p_median': ps[len(ps) // 2], 'random_p_q05': ps[int(.05 * len(ps))],
                        'random_p_q95': ps[int(.95 * len(ps)) - 1],
                        'share_random_p_below_0.05': round(sum(p < 0.05 for p in ps) / len(ps), 3),
                        'share_random_p_at_least_changed': round(sum(p >= obs[cut]['p'] for p in ps) / len(ps), 3)}
    sr = sorted(r['pooled_success_removed'] for r in rand)
    write_json({'exploratory': True, 'n_tasks': len(tasks), 'n_removed': len(changed), 'n_draws': NDRAW, 'nsim': NSIM,
                'changed_tasks_removed': changed, 'summary': summary,
                'pooled_success_removed': {'changed_tasks': obs['pooled_success_removed'], 'random_median': sr[len(sr) // 2],
                                           'random_q05': sr[int(.05 * len(sr))], 'random_q95': sr[int(.95 * len(sr)) - 1]},
                'changed_tasks_result': obs, 'random_draws': [dict(r, removed=sorted(d)) for r, d in zip(rand, draws)]}, a.out)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
