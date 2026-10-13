"""Q4: does ranking by reliability on repeats (pass^k) differ from ranking by pass@1 beyond noise?

For every pair of models whose order by pass@1 and by pass^3 or pass^5 is reversed, a bootstrap over tasks
(2,000 draws) gives a 95% interval for the pass^k difference.

    python q4_repeats.py --trials data/tb40_trials.csv --out results/q4_repeats.json
"""
import argparse
import random
from math import comb

from common import load_trials, write_json

SEED, B = 20261012, 2000


def p1(m, ts):
    return sum(sum(m[t]) for t in ts) / (5 * len(ts))


def pk(m, ts, k):
    # unbiased pass^k with n = 5 trials: C(c, k) / C(5, k), averaged over tasks
    return sum(comb(sum(m[t]), k) / comb(5, k) for t in ts) / len(ts)


def ci(f, ts, rnd):
    v = sorted(f([rnd.choice(ts) for _ in ts]) for _ in range(B))
    return v[int(0.025 * B)], v[int(0.975 * B) - 1]


def analyze(S):
    rnd = random.Random(SEED)
    models = sorted(S); tasks = sorted(next(iter(S.values())))
    per = {m: {'pass@1': round(p1(S[m], tasks), 4), 'pass^3': round(pk(S[m], tasks, 3), 4), 'pass^5': round(pk(S[m], tasks, 5), 4),
               'ratio_pass5_to_pass1': round(pk(S[m], tasks, 5) / p1(S[m], tasks), 3)} for m in models}
    pairs = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            d1 = p1(S[a], tasks) - p1(S[b], tasks)
            for k in (3, 5):
                dk = pk(S[a], tasks, k) - pk(S[b], tasks, k)
                if d1 * dk < 0:
                    lo, hi = ci(lambda ts: pk(S[a], ts, k) - pk(S[b], ts, k), tasks, rnd)
                    lo1, hi1 = ci(lambda ts: p1(S[a], ts) - p1(S[b], ts), tasks, rnd)
                    pairs.append({'a': a, 'b': b, 'k': k, 'diff_pass1': round(d1, 4), 'diff_passk': round(dk, 4),
                                  'passk_ci95': [round(lo, 4), round(hi, 4)], 'pass1_ci95': [round(lo1, 4), round(hi1, 4)],
                                  'passk_significant': lo > 0 or hi < 0, 'pass1_significant': lo1 > 0 or hi1 < 0})
    return {'per_model': per,
            'rank_pass1': sorted(models, key=lambda m: -per[m]['pass@1']),
            'rank_pass5': sorted(models, key=lambda m: -per[m]['pass^5']),
            'reversed_pairs': pairs,
            'verdict_repeats_change_ranking': any(p['passk_significant'] and p['k'] == 5 for p in pairs)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    write_json(analyze(load_trials(a.trials)), a.out)


if __name__ == '__main__':
    main()
