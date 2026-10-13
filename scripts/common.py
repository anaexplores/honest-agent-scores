"""Shared I/O helpers. Analysis logic lives in the individual scripts and is unchanged from the original study."""
import csv
import json
from collections import defaultdict


def load_trials(path):
    """Read a trials CSV with columns model, task, reward -> {model: {task: [0/1, ...]}}.

    A trial counts as a success when reward >= 1; an empty reward (errored trial) counts as 0,
    as on the Terminal-Bench leaderboard.
    """
    s = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(path, encoding='utf-8')):
        s[r['model']][r['task']].append(1 if float(r['reward'] or 0) >= 1 else 0)
    return s


def load_defects(path):
    """Read a defect list JSON with keys false_positive and false_negative -> (set, set)."""
    d = json.load(open(path, encoding='utf-8'))
    return set(d.get('false_positive', [])), set(d.get('false_negative', []))


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')
