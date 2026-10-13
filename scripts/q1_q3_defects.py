"""Q1-Q3: do known task defects change the ranking, the repeat correlation (ICC), or favour some models?

Q1  Ranking: inversions between the ranking on all tasks and on tasks not flagged as defective,
    against a null of removing the same number of random tasks (10,000 draws).
Q2  ICC (one-way ANOVA, per model; median across models) with and without flagged tasks, against a
    null of removing random task sets with matched mean success (+-0.03, pooled across models).
Q3  Per model: success on false-positive tasks minus success on unflagged tasks; permutation test of
    heterogeneity across models (descriptive).

    python q1_q3_defects.py --trials data/tb40_trials.csv --defects data/epoch_defects_tb40.json --out results/q1_q3_defects.json
"""
import argparse
import random
from statistics import median

from common import load_trials, load_defects, write_json

N_NULL, SEED = 10000, 20261012


def acc(m, tasks):
    v = [x for t in tasks for x in m[t]]
    return sum(v) / len(v)


def icc_anova(m, tasks):
    groups = [m[t] for t in tasks]
    k = len(groups[0]); n = len(groups)
    grand = sum(map(sum, groups)) / (n * k)
    msb = k * sum((sum(g) / k - grand) ** 2 for g in groups) / (n - 1)
    msw = sum((x - sum(g) / k) ** 2 for g in groups for x in g) / (n * (k - 1))
    return (msb - msw) / (msb + (k - 1) * msw) if (msb + (k - 1) * msw) > 0 else 0.0


def inversions(a, b):
    ms = list(a)
    return sum(1 for i in range(len(ms)) for j in range(i + 1, len(ms))
               if (a[ms[i]] - a[ms[j]]) * (b[ms[i]] - b[ms[j]]) < 0)


def analyze(S, FP, FN):
    FLAG = FP | FN
    models = sorted(S)
    tasks = sorted(next(iter(S.values())))
    assert all(sorted(S[m]) == tasks and all(len(S[m][t]) == 5 for t in tasks) for m in models)
    assert FLAG <= set(tasks), FLAG - set(tasks)
    clean = [t for t in tasks if t not in FLAG]
    rnd = random.Random(SEED)
    out = {'n_models': len(models), 'n_tasks': len(tasks), 'n_flagged': len(FLAG), 'n_fp': len(FP), 'n_fn': len(FN)}

    # Q1
    raw = {m: acc(S[m], tasks) for m in models}
    cln = {m: acc(S[m], clean) for m in models}
    obs = inversions(raw, cln)
    null = []
    for _ in range(N_NULL):
        drop = set(rnd.sample(tasks, len(FLAG)))
        keep = [t for t in tasks if t not in drop]
        null.append(inversions(raw, {m: acc(S[m], keep) for m in models}))
    p1 = sum(1 for x in null if x >= obs) / N_NULL
    # pairs whose order flips: bootstrap over clean tasks for the clean-task difference
    flips = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            if (raw[a] - raw[b]) * (cln[a] - cln[b]) < 0:
                diffs = []
                for _ in range(2000):
                    bt = [rnd.choice(clean) for _ in clean]
                    diffs.append(acc(S[a], bt) - acc(S[b], bt))
                diffs.sort()
                lo, hi = diffs[50], diffs[1949]
                flips.append({'a': a, 'b': b, 'raw_diff': round(raw[a] - raw[b], 4), 'clean_diff': round(cln[a] - cln[b], 4),
                              'clean_ci95': [round(lo, 4), round(hi, 4)], 'significant': lo > 0 or hi < 0})
    out['q1'] = {
        'per_model': {m: {'raw': round(raw[m], 4), 'clean': round(cln[m], 4), 'delta': round(cln[m] - raw[m], 4),
                          'fp_tasks': round(acc(S[m], sorted(FP)), 4), 'fn_tasks': round(acc(S[m], sorted(FN)), 4)} for m in models},
        'rank_raw': sorted(models, key=lambda m: -raw[m]), 'rank_clean': sorted(models, key=lambda m: -cln[m]),
        'inversions_obs': obs, 'null_median': median(null), 'null_p95': sorted(null)[int(0.95 * N_NULL)], 'p': p1,
        'flipped_pairs': flips,
        'verdict_changes_ranking': p1 < 0.05 or any(f['significant'] for f in flips),
    }

    # Q2
    icc_all = median(icc_anova(S[m], tasks) for m in models)
    icc_cln = median(icc_anova(S[m], clean) for m in models)
    pooled = {t: sum(sum(S[m][t]) for m in models) / (5 * len(models)) for t in tasks}
    target = sum(pooled[t] for t in FLAG) / len(FLAG)
    nd, tries = [], 0
    while len(nd) < N_NULL and tries < 200 * N_NULL:
        tries += 1
        drop = rnd.sample(tasks, len(FLAG))
        if abs(sum(pooled[t] for t in drop) / len(drop) - target) > 0.03:
            continue
        keep = [t for t in tasks if t not in set(drop)]
        nd.append(median(icc_anova(S[m], keep) for m in models) - icc_all)
    nd.sort()
    d_obs = icc_cln - icc_all
    out['q2'] = {
        'icc_median_all': round(icc_all, 4), 'icc_median_clean': round(icc_cln, 4), 'delta_obs': round(d_obs, 4),
        'per_model': {m: [round(icc_anova(S[m], tasks), 4), round(icc_anova(S[m], clean), 4)] for m in models},
        'flagged_mean_success_pooled': round(target, 4), 'null_n': len(nd),
        'null_delta_ci95': [round(nd[int(0.025 * len(nd))], 4), round(nd[int(0.975 * len(nd)) - 1], 4)],
        'p_lower': sum(1 for x in nd if x <= d_obs) / len(nd),
    }

    # Q3: success on FP tasks minus success on unflagged tasks; permutation test of heterogeneity
    def spread(lbl):
        d = [acc(S[m], [t for t in tasks if lbl[t] == 'fp']) - acc(S[m], [t for t in tasks if lbl[t] == 'c']) for m in models]
        mu = sum(d) / len(d)
        return d, sum((x - mu) ** 2 for x in d)
    lbl = {t: ('fp' if t in FP else 'c' if t in clean else 'x') for t in tasks}
    d_obs3, v_obs = spread(lbl)
    pool = [t for t in tasks if lbl[t] != 'x']
    cnt = 0
    for _ in range(N_NULL):
        sh = pool[:]; rnd.shuffle(sh)
        l2 = {t: 'x' for t in tasks}
        for t in sh[:len(FP)]: l2[t] = 'fp'
        for t in sh[len(FP):]: l2[t] = 'c'
        if spread(l2)[1] >= v_obs: cnt += 1
    out['q3'] = {'fp_minus_clean': {m: round(x, 4) for m, x in zip(models, d_obs3)}, 'p_heterogeneity': cnt / N_NULL}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--defects', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    FP, FN = load_defects(a.defects)
    write_json(analyze(load_trials(a.trials), FP, FN), a.out)


if __name__ == '__main__':
    main()
