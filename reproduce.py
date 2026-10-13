"""Reproduce every result in results/ from the data.

    python reproduce.py                 # fetch TB 4.0 trials if missing, then run all analyses into results/
    python reproduce.py --quick         # skip the slow TB 2.0 runs (Q5 on 63 configurations, slope sensitivity)
    python reproduce.py --compare DIR   # also compare the new outputs with the JSON files in DIR

Runtime on a laptop: about 5 minutes for TB 4.0 analyses, plus about 40 minutes for the TB 2.0 runs.
Only the Python standard library is needed (3.9+).
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, 'scripts')
D = os.path.join(HERE, 'data')


def run(args, out_dir):
    cmd = [sys.executable, os.path.join(S, args[0])] + [a.replace('{OUT}', out_dir) for a in args[1:]]
    print('$', ' '.join(os.path.relpath(c, HERE) if os.path.isabs(c) else c for c in cmd[1:]), flush=True)
    subprocess.run(cmd, check=True, cwd=S)


def compare(new, ref):
    def close(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
        if isinstance(a, list) and isinstance(b, list):
            return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
        return a == b
    rows = []
    for f in sorted(os.listdir(new)):
        if not f.endswith('.json') or not os.path.exists(os.path.join(ref, f)):
            continue
        same = close(json.load(open(os.path.join(new, f), encoding='utf-8')), json.load(open(os.path.join(ref, f), encoding='utf-8')))
        rows.append((f, same)); print(f"{'MATCH   ' if same else 'DIFFERS '} {f}")
    return all(s for _, s in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=os.path.join(HERE, 'results')); ap.add_argument('--quick', action='store_true')
    ap.add_argument('--compare')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tb40, tb20 = os.path.join(D, 'tb40_trials.csv'), os.path.join(D, 'tb20_trials.csv')
    tb20q5 = os.path.join(D, 'tb20_q5_trials.csv')
    defects, changed = os.path.join(D, 'epoch_defects_tb40.json'), os.path.join(D, 'tb21_changed_tasks.json')
    if not os.path.exists(tb40):
        run(['fetch_tb40_trials.py', '--manifest', os.path.join(D, 'tb40_submissions.json'), '--out', tb40], a.out)
    o = lambda name: os.path.join('{OUT}', name)
    run(['q1_q3_defects.py', '--trials', tb40, '--defects', defects, '--out', o('q1_q3_defects.json')], a.out)
    run(['q4_repeats.py', '--trials', tb40, '--out', o('q4_repeats.json')], a.out)
    run(['q5_icc_heterogeneity.py', '--trials', tb40, '--out', o('q5_icc_tb40.json')], a.out)
    run(['q5b_icc_residual.py', '--trials', tb40, '--out', o('q5b_residual_tb40.json')], a.out)
    run(['exploratory_checks.py', '--trials', tb40, '--defects', defects, '--out', o('exploratory_checks.json')], a.out)
    run(['power_table.py', '--trials', tb40, '--out', o('power_table.json')], a.out)
    if not a.quick:
        run(['prep_tb20.py', '--trials', tb20, '--out', tb20q5], a.out)
        run(['q5_icc_heterogeneity.py', '--trials', tb20q5, '--out', o('q5_icc_tb20.json')], a.out)
        run(['q5b_icc_residual.py', '--trials', tb20q5, '--out', o('q5b_residual_tb20.json')], a.out)
        run(['icc_slope_sensitivity.py', '--tb40', tb40, '--tb20', tb20, '--tb21-changed', changed, '--out', o('icc_slope_sensitivity.json')], a.out)
    if a.compare:
        sys.exit(0 if compare(a.out, a.compare) else 1)


if __name__ == '__main__':
    main()
