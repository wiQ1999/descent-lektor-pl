"""Skrócony przegląd mówców w oknach narratora (produkcja po t1): każda kwestia z wypowiedzią w jednym bloku,
narracja skrócona do końca przed wypowiedzią i początku po niej. Tekst gry tylko w analysis/work.

    .venv/Scripts/python -I analysis/tools/speakers_digest.py [--db analysis/work/lektor/t1.sqlite] [--all]
"""
import argparse
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import build, scope, speakers  # noqa: E402
from lektor.normalize import clean_markup  # noqa: E402


def cut(t, n, end=False):
    t = re.sub(r'\s+', ' ', t)
    return t if len(t) <= n else ('…' + t[-n:] if end else t[:n] + '…')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(ROOT, 'analysis', 'work', 'lektor', 't1.sqlite'))
    ap.add_argument('--all', action='store_true', help='także grupy zakresu t1')
    ap.add_argument('--out', default=os.path.join(ROOT, 'analysis', 'work', 'out', 'prod', 'speakers_digest.txt'))
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    skip = set() if a.all else set(scope.TEST_GROUPS['t1'])
    out, n = [], 0
    for r in con.execute("SELECT * FROM lines WHERE tts = 1 AND category != 'opcja_wyboru' AND key NOT LIKE '%#%' "
                         "ORDER BY rowid"):
        text = clean_markup(r['text_raw'])
        if r['grp'] in skip or not (r['voice'] == 'narrator' or build.NARRATED.search(text) and r['category'] == 'dialog'):
            continue
        pieces = speakers.split(text)
        if not any(p[0] in 'sq' for p in pieces):
            continue
        types = [x.get('type') for x in json.loads(r['args'] or '[]')]
        guess = iter(speakers.guess(r['key'], pieces, types))
        n += 1
        out.append('### %d %s | %s | %s%s' % (n, r['key'], r['grp'], r['voice'], ' | args=%s' % types if types else ''))
        for i, (kind, t, para) in enumerate(pieces):
            if kind in 'sq':
                v, why = next(guess)
                out.append('  %s%d [%s/%s] %s' % (kind.upper(), i, v, why, cut(t, 70)))
            else:
                nxt = i + 1 < len(pieces) and pieces[i + 1][0] in 'sq'
                prv = i and pieces[i - 1][0] in 'sq'
                out.append('  n%d %s' % (i, cut(t, 80, end=nxt and not prv) if not (nxt and prv) else cut(t, 110)))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write('\n'.join(out))
    print(n, os.path.relpath(a.out, ROOT))


if __name__ == '__main__':
    main()
