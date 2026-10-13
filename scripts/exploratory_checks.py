"""EXPLORATORY checks added after the analysis plan (each labelled exploratory in the results).

1. Defect subsets: ranking inversions after removing only false-positive or only false-negative tasks
   (5,000 random-removal nulls each), and the paired-bootstrap shift for the pair that flipped most.
2. Pairs with near-equal pass@1 (|diff| < 0.03): bootstrap 95% intervals for pass@1 and pass^5 differences.
3. Bias of the one-way ANOVA ICC estimator under a beta-binomial with constant ICC across pass@1 levels.

    python exploratory_checks.py --trials data/tb40_trials.csv --defects data/epoch_defects_tb40.json --out results/exploratory_checks.json
"""
import argparse
import random
from math import comb
from statistics import mean

from common import load_trials, load_defects, write_json
from q5_icc_heterogeneity import icc_anova, sim_groups

SHIFT_PAIR = ('anthropic/claude-fable-5-1', 'openai/gpt-6-sol')


def defect_subsets(S, FP, FN):
    ms = sorted(S); ts = sorted(next(iter(S.values()))); rnd = random.Random(11)
    acc = lambda m, T: sum(sum(S[m][t]) for t in T) / (5 * len(T))
    def inv(a, b): return sum(1 for i in range(len(ms)) for j in range(i + 1, len(ms)) if (a[ms[i]] - a[ms[j]]) * (b[ms[i]] - b[ms[j]]) < 0)
    raw = {m: acc(m, ts) for m in ms}
    out = {}
    for lbl, F in (('false_positive_only', FP), ('false_negative_only', FN)):
        keep = [t for t in ts if t not in F]
        obs = inv(raw, {m: acc(m, keep) for m in ms})
        null = [inv(raw, {m: acc(m, [t for t in ts if t not in set(rnd.sample(ts, len(F)))]) for m in ms}) for _ in range(5000)]
        out[lbl] = {'inversions': obs, 'p': sum(x >= obs for x in null) / 5000, 'null_median': sorted(null)[2500]}
    a, b = SHIFT_PAIR
    F = FP | FN; sh = []
    for _ in range(4000):
        T = [rnd.choice(ts) for _ in ts]; C = [t for t in T if t not in F]
        if not C: continue
        sh.append((acc(a, C) - acc(b, C)) - (acc(a, T) - acc(b, T)))
    sh.sort(); n = len(sh)
    point = (acc(a, [t for t in ts if t not in F]) - acc(b, [t for t in ts if t not in F])) - (raw[a] - raw[b])
    out['paired_shift'] = {'pair': list(SHIFT_PAIR), 'point': round(point, 4),
                           'ci95': [round(sh[int(0.025 * n)], 4), round(sh[int(0.975 * n) - 1], 4)],
                           'note': 'pair chosen after seeing the data (1 of 45 pairs); no multiplicity correction'}
    return out


def equal_pass1_pairs(S):
    ms = sorted(S); ts = sorted(next(iter(S.values()))); rnd = random.Random(7)
    p1 = lambda m, T: sum(sum(S[m][t]) for t in T) / (5 * len(T))
    p5 = lambda m, T: sum(comb(sum(S[m][t]), 5) for t in T) / len(T)
    res = []
    for i, a in enumerate(ms):
        for b in ms[i + 1:]:
            if abs(p1(a, ts) - p1(b, ts)) < 0.03:
                bs = []
                for _ in range(4000):
                    T = [rnd.choice(ts) for _ in ts]; bs.append((p1(a, T) - p1(b, T), p5(a, T) - p5(b, T)))
                d1 = sorted(x for x, _ in bs); d5 = sorted(y for _, y in bs)
                res.append({'a': a, 'b': b, 'diff_pass1': round(p1(a, ts) - p1(b, ts), 4), 'diff_pass1_ci95': [round(d1[100], 3), round(d1[3899], 3)],
                            'diff_pass5': round(p5(a, ts) - p5(b, ts), 4), 'diff_pass5_ci95': [round(d5[100], 3), round(d5[3899], 3)]})
    return res


def estimator_bias():
    r = random.Random(1); out = []
    for icc in (0.45, 0.6):
        for p in (0.1, 0.2, 0.35, 0.5, 0.65, 0.8):
            est = [icc_anova(sim_groups(r, p, icc, 88)) for _ in range(400)]
            out.append({'true_icc': icc, 'pass1': p, 'mean_estimate': round(mean(est), 3)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--trials', required=True); ap.add_argument('--defects', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    S = load_trials(a.trials); FP, FN = load_defects(a.defects)
    write_json({'exploratory': True, 'defect_subsets': defect_subsets(S, FP, FN),
                'equal_pass1_pairs': equal_pass1_pairs(S), 'icc_estimator_bias': estimator_bias()}, a.out)


if __name__ == '__main__':
    main()
