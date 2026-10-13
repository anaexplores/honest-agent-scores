"""Download the Terminal-Bench 2.0 trial outcomes (optional: data/tb20_trials.csv is already included).

Source: Hugging Face dataset yoonholee/terminalbench-trajectories (Apache-2.0), via the datasets-server API,
100 rows per page. Keeps task_name, agent, model, reward, trial_name, trial_id and the source row index
(trajectories and token counts are dropped).

Two checks:
- every page must contain exactly the requested row indices (the server has been seen to return a different
  page than the one requested; such pages are retried), and no row index may appear twice;
- duplicated trials in the source are removed: a trial is identified by (agent, model, trial_name). Some
  configurations list every trial twice, the second copy without trial_id and started_at; the copy with
  more metadata is kept (the first one on ties). The script prints how many rows were removed per configuration
  and stops if two copies of one trial disagree on the reward.

    python fetch_tb20_trials.py --out data/tb20_trials.csv
"""
import argparse
import csv
import json
import time
import urllib.request
from collections import Counter

BASE = 'https://datasets-server.huggingface.co/rows?dataset=yoonholee%2Fterminalbench-trajectories&config=default&split=train'
PAGE = 100
COLS = ['task_name', 'agent', 'model', 'reward', 'trial_name', 'trial_id', 'source_row']


def get_page(off, total=None, tries=8):
    want = list(range(off, off + PAGE if total is None else min(off + PAGE, total)))
    for t in range(1, tries + 1):
        try:
            j = json.loads(urllib.request.urlopen(f'{BASE}&offset={off}&length={PAGE}', timeout=60).read())
            if 'error' in j:
                raise RuntimeError(j['error'])
            got = [r['row_idx'] for r in j['rows']]
            if total is not None and got != want:
                raise RuntimeError(f'offset {off}: server returned rows {got[:1]}..{got[-1:]} (wrong page)')
            return j
        except Exception as e:
            if t == tries:
                raise
            print(f'retry {t}: {e}', flush=True)
            time.sleep(2 * t + (8 * t if '429' in str(e) else 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', required=True); ap.add_argument('--throttle', type=float, default=1.2)
    a = ap.parse_args()
    total = get_page(0)['num_rows_total']
    rows, off = [], 0
    while off < total:
        rows += [dict({c: r['row'].get(c) for c in COLS[:-1] + ['started_at']}, source_row=r['row_idx'])
                 for r in get_page(off, total)['rows']]  # trajectories are dropped right away
        off += PAGE
        time.sleep(a.throttle)
    idx = [r['source_row'] for r in rows]
    assert idx == list(range(total)), 'row indices are not exactly 0..total-1'

    keep, removed = {}, Counter()
    for r in rows:
        key = (r['agent'], r['model'], r['trial_name'])
        if key not in keep:
            keep[key] = r
            continue
        old = keep[key]
        if str(old['reward']) != str(r['reward']):
            raise SystemExit(f'copies of {key} disagree on reward: rows {old["source_row"]} and {r["source_row"]}')
        if bool(r.get('trial_id')) + bool(r.get('started_at')) > bool(old.get('trial_id')) + bool(old.get('started_at')):
            keep[key] = r
        removed[f"{r['agent']} | {r['model']}"] += 1
    out = sorted(keep.values(), key=lambda r: r['source_row'])
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(COLS)
        for r in out:
            w.writerow(['' if r.get(c) is None else r[c] for c in COLS])
    print(f'source rows {total}; duplicated trials removed {sum(removed.values())}; written {len(out)}')
    for c, n in sorted(removed.items()):
        print(f'  {n:5d}  {c}')


if __name__ == '__main__':
    main()
