"""Q5: is the repeat correlation (ICC) a property of the model x harness configuration, or noise?

Statistic V = variance of per-configuration ICC (one-way ANOVA). Null: each configuration keeps its own
pass@1 while all share one ICC; per-task success probabilities pi_t ~ Beta(mean = pass@1, ICC), then k = 5
Bernoulli trials per task. 5,000 simulations. Robustness: median as the common ICC; dropping configurations
with pass@1 < 0.13.

    python q5_icc_heterogeneity.py --trials data/tb40_trials.csv --out results/q5_icc_tb40.json
"""
import argparse
import random
from statistics import mean, median, pvariance

from common import load_trials, write_json

K, NSIM, SEED = 5, 5000, 20261012


def icc_anova(groups):
    k = len(groups[0]); n = len(groups)
    grand = sum(map(sum, groups)) / (n * k)
    msb = k * sum((sum(g) / k - grand) ** 2 for g in groups) / (n - 1)
    msw = sum((x - sum(g) / k) ** 2 for g in groups for x in g) / (n * (k - 1))
    den = msb + (k - 1) * msw
    return (msb - msw) / den if den > 0 else 0.0


def sim_groups(rnd, p, icc, n):
    s = 1 / icc - 1  # alpha + beta
    a, b = p * s, (1 - p) * s
    out = []
    for _ in range(n):
        pi = rnd.betavariate(a, b)
        out.append([1 if rnd.random() < pi else 0 for _ in range(K)])
    return out


def test(S, models, center, rnd, nsim=NSIM):
    tasks = sorted(next(iter(S.values())))
    obs = {m: icc_anova([S[m][t] for t in tasks]) for m in models}
    p1 = {m: mean(x for t in tasks for x in S[m][t]) for m in models}
    c = center(list(obs.values()))
    v_obs = pvariance(list(obs.values()))
    vs = []
    for _ in range(nsim):
        vs.append(pvariance([icc_anova(sim_groups(rnd, p1[m], c, len(tasks))) for m in models]))
    vs.sort()
    return {'icc': {m: round(obs[m], 4) for m in models}, 'pass1': {m: round(p1[m], 4) for m in models},
            'icc_center': round(c, 4), 'V_obs': round(v_obs, 5), 'V_null_median': round(vs[nsim // 2], 5),
            'V_null_p95': round(vs[int(0.95 * nsim)], 5), 'p': sum(1 for v in vs if v >= v_obs) / nsim}


def analyze(S):
    rnd = random.Random(SEED)
    allm = sorted(S)
    strong = [m for m in allm if mean(x for t in S[m] for x in S[m][t]) >= 0.13]
    return {'main_mean_center': test(S, allm, mean, rnd),
            'robust_median_center': test(S, allm, median, rnd),
            'robust_drop_weakest': dict(test(S, strong, mean, rnd), models=strong)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    write_json(analyze(load_trials(a.trials)), a.out)


if __name__ == '__main__':
    main()
