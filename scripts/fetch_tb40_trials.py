"""Download the per-trial Terminal-Bench 4.0 results used in the study (10 public submissions).

Source: the public leaderboard (github.com/harbor-framework/terminal-bench, leaderboard/submissions/*.json) lists,
for each submission, its Harbor Hub job id(s) and trial ids. Trial results (task, reward, error) are read from the
public job pages https://hub.harborframework.com/jobs/<job_id>?page=N (100 trials per page, embedded in the page).

The submission list is pinned in data/tb40_submissions.json; the output is checked against the recorded SHA-256.
Trial data belong to the submitters and are not redistributed here (see DATA.md). Pages can become private at
any time; 11 of 21 submissions already were on 2026-10-12.

    python fetch_tb40_trials.py --manifest data/tb40_submissions.json --out data/tb40_trials.csv
"""
import argparse
import base64
import csv
import hashlib
import json
import re
import sys
import time
import urllib.request

RAW = 'https://raw.githubusercontent.com/harbor-framework/terminal-bench/main/leaderboard/submissions/{name}'
HUB = 'https://hub.harborframework.com/jobs/{job}?page={page}'
UA = {'User-Agent': 'honest-agent-scores/1.0 (public leaderboard analysis)'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8')


def rsc_text(html):
    """Join the self.__next_f.push([1, "..."]) chunks of a Next.js page into one decoded string."""
    return ''.join(json.loads(m.group(1)) for m in re.finditer(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', html))


def trials_page(job, page):
    txt = rsc_text(get(HUB.format(job=job, page=page)))
    i = txt.find('"initialTrials":')
    if i < 0:
        raise RuntimeError(f'no trial data on job {job} page {page} (page may be private)')
    obj, _ = json.JSONDecoder().raw_decode(txt, i + len('"initialTrials":'))
    return obj


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--manifest', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    man = json.load(open(a.manifest, encoding='utf-8'))
    rows = []
    for s in man['submissions']:
        name = s['submission']
        sub = json.loads(get(RAW.format(name=name)))
        src = sub['source_filter']
        want = set(sub['trials'])
        got = []
        for job in sub['source_jobs']:
            page, pages = 1, 1
            while page <= pages:
                obj = trials_page(job, page)
                pages = obj['total_pages']
                got += [(job, t) for t in obj['items']]
                page += 1
                time.sleep(1.0)
        for job, t in got:
            if t['id'] not in want:
                continue
            rows.append({'submission': name, 'model': src.get('model_name'), 'agent': src.get('agent'),
                         'effort': src.get('reasoning_effort'), 'job_id': job, 'trial_id': t['id'],
                         'task': t['task_name'].split('/', 1)[-1], 'attempt': t.get('attempt'),
                         'reward': t.get('reward'), 'error_type': t.get('error_type'),
                         'status': t.get('status'), 'is_scored': t.get('is_scored')})
        n = sum(1 for r in rows if r['submission'] == name)
        succ = sum(1 for r in rows if r['submission'] == name and (r['reward'] or 0) >= 1)
        print(f'{name}: trials {n}/{len(want)} successes {succ} (leaderboard {sub["metrics"].get("successes")})', flush=True)
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    sha = hashlib.sha256(open(a.out, 'rb').read()).hexdigest()
    ok = sha == man['csv_sha256']
    print(f'wrote {len(rows)} rows; sha256 {sha} {"matches" if ok else "DIFFERS FROM"} the manifest')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
