"""Download the Terminal-Bench 2.0 trial outcomes (optional: data/tb20_trials.csv is already included).

Source: Hugging Face dataset yoonholee/terminalbench-trajectories (Apache-2.0), via the datasets-server API.
Keeps only task_name, agent, model, reward (trajectories and token counts are dropped). 52,104 rows, 100 per page.

    python fetch_tb20_trials.py --out data/tb20_trials.csv
"""
import argparse
import csv
import json
import time
import urllib.request

BASE = 'https://datasets-server.huggingface.co/rows?dataset=yoonholee%2Fterminalbench-trajectories&config=default&split=train'
PAGE = 100


def get_page(off, tries=6):
    for t in range(1, tries + 1):
        try:
            j = json.loads(urllib.request.urlopen(f'{BASE}&offset={off}&length={PAGE}', timeout=60).read())
            if 'error' in j:
                raise RuntimeError(j['error'])
            return j
        except Exception as e:
            if t == tries:
                raise
            time.sleep(2 * t + (8 * t if '429' in str(e) else 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', required=True); ap.add_argument('--throttle', type=float, default=1.2)
    a = ap.parse_args()
    first = get_page(0)
    total = first['num_rows_total']
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        f.write('task_name,agent,model,reward\n')  # unquoted header, as in the included file
        w = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        off, page = 0, first
        while True:
            for r in page['rows']:
                row = r['row']
                w.writerow([row.get('task_name'), row.get('agent'), row.get('model'), row.get('reward')])
            off += PAGE
            if off >= total:
                break
            time.sleep(a.throttle)
            page = get_page(off)
    print(f'wrote {total} rows')


if __name__ == '__main__':
    main()
