"""How many tasks does a benchmark need to tell two agents apart?

For every pair of configurations in a trials file, a bootstrap over tasks (2,000 draws) gives the standard error
of the difference in pass@1 and in pass^k at the observed number of tasks N0. Assuming new tasks are drawn from
the same population, the standard error scales as sqrt(N0 / N). The table reports, for each N, the median across
pairs of:
  - the 95% interval half-width of the difference (1.96 * SE): differences smaller than this look like ties;
  - the minimum detectable difference at 80% power and alpha = 0.05 ((1.96 + 0.84) * SE).
This is an approximation: it ignores that harder or easier task mixes change the variance, and it treats the
k trials per task as given.

    python power_table.py --trials data/tb40_trials.csv --out results/power_table.json
"""
import argparse
import random
from math import comb, sqrt
from statistics import median

from common import load_trials, write_json

SEED, B = 20261013, 2000
NS = [50, 66, 100, 150, 200, 300, 500, 1000]


def analyze(S, k=5, ns=NS):
    rnd = random.Random(SEED)
    ms = sorted(S); ts = sorted(next(iter(S.values()))); n0 = len(ts)
    p1 = lambda m, T: sum(sum(S[m][t]) for t in T) / (k * len(T))
    pk = lambda m, T: sum(comb(sum(S[m][t]), k) / comb(k, k) for t in T) / len(T)
    se1, sek = [], []
    for i, a in enumerate(ms):
        for b in ms[i + 1:]:
            d1, dk = [], []
            for _ in range(B):
                T = [rnd.choice(ts) for _ in ts]
                d1.append(p1(a, T) - p1(b, T)); dk.append(pk(a, T) - pk(b, T))
            sd = lambda v: sqrt(sum((x - sum(v) / len(v)) ** 2 for x in v) / (len(v) - 1))
            se1.append(sd(d1)); sek.append(sd(dk))
    s1, sk = median(se1), median(sek)
    rows = []
    for n in sorted(set(ns + [n0])):
        f = sqrt(n0 / n)
        rows.append({'tasks': n,
                     'pass1_tie_halfwidth_pp': round(100 * 1.96 * s1 * f, 1), 'pass1_mdd80_pp': round(100 * 2.80 * s1 * f, 1),
                     f'pass^{k}_tie_halfwidth_pp': round(100 * 1.96 * sk * f, 1), f'pass^{k}_mdd80_pp': round(100 * 2.80 * sk * f, 1)})
    return {'observed_tasks': n0, 'trials_per_task': k, 'pairs': len(se1),
            'median_se_pass1_at_observed': round(s1, 4), f'median_se_pass^{k}_at_observed': round(sk, 4),
            'assumption': 'SE scales as sqrt(N_observed / N); new tasks drawn from the same population', 'table': rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    write_json(analyze(load_trials(a.trials)), a.out)


if __name__ == '__main__':
    main()
