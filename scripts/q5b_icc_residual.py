"""Q5b (EXPLORATORY, added after the fact): does ICC differ between configurations at EQUAL pass@1?

Null: ICC of a configuration = a + b * pass@1 (one linear relation fitted to the data); trials drawn from a
beta-binomial with that ICC. Statistic: variance of ICC residuals after a linear fit on pass@1 (the fit is
repeated in every simulation).

    python q5b_icc_residual.py --trials data/tb40_trials.csv --nsim 2000 --out results/q5b_residual_tb40.json
"""
import argparse
import random
from statistics import mean, pvariance

from common import load_trials, write_json
from q5_icc_heterogeneity import icc_anova, sim_groups


def resid_var(x, y):
    mx, my = mean(x), mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    a0 = my - b * mx
    return pvariance([c - (a0 + b * a) for a, c in zip(x, y)]), a0, b


def analyze(S, nsim):
    ms = sorted(S); tasks = sorted(next(iter(S.values())))
    p1 = [mean(x for t in tasks for x in S[m][t]) for m in ms]
    icc = [icc_anova([S[m][t] for t in tasks]) for m in ms]
    v_obs, a0, b = resid_var(p1, icc)
    rnd = random.Random(20261012); vs = []
    for _ in range(nsim):
        sim = [icc_anova(sim_groups(rnd, p, min(max(a0 + b * p, 0.02), 0.95), len(tasks))) for p in p1]
        vs.append(resid_var(p1, sim)[0])
    vs.sort()
    return {'exploratory': True, 'n_configs': len(ms), 'fit_icc_vs_pass1': [round(a0, 4), round(b, 4)], 'resid_var_obs': round(v_obs, 5),
            'null_median': round(vs[nsim // 2], 5), 'null_p95': round(vs[int(0.95 * nsim)], 5),
            'p': sum(1 for v in vs if v >= v_obs) / nsim}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--nsim', type=int, default=2000); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    write_json(analyze(load_trials(a.trials), a.nsim), a.out)


if __name__ == '__main__':
    main()
