"""Przegląd wypowiedzi postaci w kwestiach narratora (E16, D101).

  .venv/Scripts/python -I analysis/tools/speakers_review.py [--db analysis/work/lektor/m3.sqlite] [--groups ...]

Zapisuje analysis/work/out/t1/speakers_review.txt (tekst gry: tylko w analysis/work) z podziałem każdej kwestii
narratora z zakresu testu na narrację i wypowiedzi, propozycją automatu i bieżącym nadpisaniem
z src/lektor/data/speakers_t1.json. Na konsolę idą tylko liczby.
"""
import argparse
import collections
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import scope, speakers  # noqa: E402
from lektor.normalize import clean_markup  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(ROOT, 'analysis', 'work', 'lektor', 'm3.sqlite'))
    ap.add_argument('--groups', nargs='*', default=scope.TEST_GROUPS['t1'])
    ap.add_argument('--out', default=os.path.join(ROOT, 'analysis', 'work', 'out', 't1', 'speakers_review.txt'))
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    over = speakers.load_overrides()
    out, stats = [], collections.Counter()
    for r in con.execute("SELECT * FROM lines WHERE voice = 'narrator' AND tts = 1 AND category != 'opcja_wyboru' "
                         "AND key NOT LIKE '%#%' ORDER BY rowid"):
        if r['grp'] not in a.groups:
            continue
        pieces = speakers.split(clean_markup(r['text_raw']))
        if not any(p[0] == 's' for p in pieces):
            continue
        types = [x.get('type') for x in json.loads(r['args'] or '[]')]
        guess = speakers.guess(r['key'], pieces, types)
        stats['kwestie'] += 1
        stats['wypowiedzi'] += len(guess)
        stats['bez mówcy'] += sum(1 for v, _ in guess if not v)
        o = over.get(r['key'])
        stats['nadpisane'] += o is not None
        out.append('### %s | %s | %s | args=%s | nadpisanie=%s' % (r['key'], r['grp'], r['category'], types, json.dumps(o)))
        it = iter(guess)
        for i, (kind, t, para) in enumerate(pieces):
            if kind == 's':
                v, why = next(it)
                out.append('  S%-2d p%d [%s %s] %s' % (i, para, v, why, t))
            else:
                out.append('  n%-2d p%d %s' % (i, para, t))
        out.append('')
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write('\n'.join(out))
    print(dict(stats), os.path.relpath(a.out, ROOT))


if __name__ == '__main__':
    main()
