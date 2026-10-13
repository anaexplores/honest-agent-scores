"""Sensitivity of the ICC ~ pass@1 slope and of Q5 to defective tasks, weak configurations and trial choice.

Variants: TB 4.0; TB 2.0 first 5 trials; TB 2.0 without the tasks changed in 2.1; TB 2.0 with 5 random trials
(seeds 1 and 2); TB 2.0 with the relaxed selection rule (>= 5 trials on >= 88 of 89 tasks). Each with and without
configurations at pass@1 < 0.1. For each: OLS intercept and slope,
bootstrap 95% intervals over configurations (2,000) and over tasks (300), and the Q5 p-value (2,000 simulations).

    python icc_slope_sensitivity.py --tb40 data/tb40_trials.csv --tb20 data/tb20_trials.csv \
        --tb21-changed data/tb21_changed_tasks.json --out results/icc_slope_sensitivity.json
"""
import argparse
import json
import random
from statistics import mean

import q5_icc_heterogeneity as q5
from common import load_trials, write_json
from prep_tb20 import read_tb20, select


def load20(path, mode, seed=0, drop=frozenset(), allow_missing=0):
    raw, all_tasks = read_tb20(path)
    keep, tasks = select(raw, all_tasks, allow_missing)
    tasks = [t for t in tasks if t not in drop]  # sorted: deterministic order for random sampling
    raw = {c: {t: [1 if float(x or 0) >= 1 else 0 for x in raw[c][t]] for t in tasks} for c in keep}
    rnd = random.Random(seed)
    return {c: {t: (raw[c][t][:5] if mode == 'first' else rnd.sample(raw[c][t], 5)) for t in tasks} for c in keep}


def fit(x, y):
    mx, my = mean(x), mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return my - b * mx, b


def stats(S, nsim=2000):
    out = {}
    for cut in (0.0, 0.1):
        ms = [m for m in sorted(S) if mean(x for t in S[m] for x in S[m][t]) >= cut]
        tasks = sorted(next(iter(S.values())))
        p1 = {m: mean(x for t in tasks for x in S[m][t]) for m in ms}
        icc = {m: q5.icc_anova([S[m][t] for t in tasks]) for m in ms}
        a, b = fit([p1[m] for m in ms], [icc[m] for m in ms])
        rnd = random.Random(5); bc, bt = [], []
        for _ in range(2000):
            mm = [rnd.choice(ms) for _ in ms]
            if len({round(p1[m], 6) for m in mm}) > 2:
                bc.append(fit([p1[m] for m in mm], [icc[m] for m in mm])[1])
        for _ in range(300):
            tt = [rnd.choice(tasks) for _ in tasks]
            bt.append(fit([mean(x for t in tt for x in S[m][t]) for m in ms], [q5.icc_anova([S[m][t] for t in tt]) for m in ms])[1])
        bc.sort(); bt.sort()
        p = q5.test(S, ms, mean, random.Random(20261012), nsim=nsim)['p']
        out[f'pass1>={cut}'] = {'n': len(ms), 'n_tasks': len(tasks), 'intercept': round(a, 3), 'slope': round(b, 3),
                                'slope_ci_by_configs': [round(bc[int(.025 * len(bc))], 3), round(bc[int(.975 * len(bc)) - 1], 3)],
                                'slope_ci_by_tasks': [round(bt[7], 3), round(bt[292], 3)], 'q5_p': p}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tb40', required=True); ap.add_argument('--tb20', required=True)
    ap.add_argument('--tb21-changed', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    drop = frozenset(json.load(open(a.tb21_changed, encoding='utf-8'))['tasks'])
    res = {}
    for label, S in [('TB4.0', load_trials(a.tb40)),
                     ('TB2.0 first5', load20(a.tb20, 'first')),
                     ('TB2.0 first5 without tasks changed in 2.1', load20(a.tb20, 'first', drop=drop)),
                     ('TB2.0 random5 seed1', load20(a.tb20, 'random', seed=1)),
                     ('TB2.0 random5 seed2', load20(a.tb20, 'random', seed=2)),
                     ('TB2.0 first5 relaxed selection (>= 88 tasks)', load20(a.tb20, 'first', allow_missing=1))]:
        res[label] = stats(S)
        print(label, json.dumps(res[label]), flush=True)
    write_json(res, a.out)


if __name__ == '__main__':
    main()
