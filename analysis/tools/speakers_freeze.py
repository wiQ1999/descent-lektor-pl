"""Zamrożenie przeglądu mówców całej gry (produkcja po t1, D107): src/lektor/data/speakers_prod.json.

Dla każdego okna z wypowiedzią (jak speakers_digest.py) głosy = propozycja automatu poprawiona ręcznie
(analysis/work/out/prod/corrections.txt: klucz<TAB>głosy po kolei, N = narrator, P: = głos każdego kawałka,
`narrator` = bez podziału), a klucze zakresu t1 przechodzą z speakers_t1.json (nv_ynfernael → nv_baelziffar).
Sprawdza liczbę głosów wobec wypowiedzi i znane głosy. Na konsolę tylko liczby i klucze.

    .venv/Scripts/python -I analysis/tools/speakers_freeze.py [--check]
"""
import argparse
import collections
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import build, speakers  # noqa: E402
from lektor.normalize import clean_markup  # noqa: E402

PROD = os.path.join(ROOT, 'analysis', 'work', 'out', 'prod')
OUT = os.path.join(ROOT, 'src', 'lektor', 'data', 'speakers_prod.json')
RENAME = {'nv_ynfernael': 'nv_baelziffar'}      # głos z Ynfernaelu w Q2 to Baelziffar (D107)


def corrections():
    out = {}
    for line in open(os.path.join(PROD, 'corrections.txt'), encoding='utf-8'):
        if not line.strip() or line.startswith('#'):
            continue
        key, v = line.rstrip('\n').split('\t')
        if v == 'narrator':
            out[key] = 'narrator'
        elif v.startswith('P:'):
            out[key] = {'pieces': ['narrator' if x == 'N' else x for x in v[2:].split()]}
        else:
            out[key] = ['narrator' if x == 'N' else x for x in v.split()]
    return out


def new_voices():
    return {l.split('|')[0].strip() for l in open(os.path.join(PROD, 'new_voices.txt'), encoding='utf-8')
            if l.strip() and not l.startswith('#')}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--db', default=os.path.join(ROOT, 'analysis', 'work', 'lektor', 't1.sqlite'))
    ap.add_argument('--check', action='store_true', help='tylko sprawdzenie, bez zapisu')
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    known = {r[0] for r in con.execute('SELECT DISTINCT voice FROM fragments')} | new_voices() | set(RENAME.values())
    fix = corrections()
    t1 = speakers.load_overrides()
    out, problems, unknown, none_left, used = {}, [], collections.Counter(), [], set()
    for r in con.execute("SELECT * FROM lines WHERE tts = 1 AND category != 'opcja_wyboru' AND key NOT LIKE '%#%' "
                         "ORDER BY rowid"):
        text = clean_markup(r['text_raw'])
        if not (r['voice'] == 'narrator' or build.NARRATED.search(text) and r['category'] == 'dialog'):
            continue
        pieces = speakers.split(text)
        if not any(p[0] in 'sq' for p in pieces):
            continue
        key = r['key']
        if key in t1:
            v = t1[key]
        elif key in fix:
            v = fix[key]
            used.add(key)
        else:
            types = [x.get('type') for x in json.loads(r['args'] or '[]')]
            v = [g for g, _ in speakers.guess(key, pieces, types)]
            if None in v:
                none_left.append(key)
            v = [g or 'narrator' for g in v]
        if isinstance(v, dict):
            v = {'pieces': [RENAME.get(x, x) for x in v['pieces']]}
            if len(v['pieces']) != len(pieces):
                problems.append('%s: %d kawałków, a jest %d' % (key, len(v['pieces']), len(pieces)))
            names = v['pieces']
        elif isinstance(v, list):
            v = [RENAME.get(x, x) for x in v]
            n = sum(p[0] in 'sq' for p in pieces)
            if len(v) != n:
                problems.append('%s: %d głosów, a wypowiedzi %d' % (key, len(v), n))
            names = v
        else:
            names = []
        for x in names:
            if x != 'narrator' and not x.startswith(('arg:', 'enemy:')) and x not in known:
                unknown[x] += 1
        out[key] = v
    for key in sorted(set(fix) - used):
        problems.append('%s: poprawka bez okna z wypowiedzią' % key)
    print('okna %d, poprawki %d, z t1 %d, automat z None %d' % (len(out), len(used), sum(k in t1 for k in out),
                                                                len(none_left)))
    for p in problems:
        print('BŁĄD', p)
    for x, c in unknown.most_common():
        print('NIEZNANY GŁOS', x, c)
    if none_left:
        print('None:', ' '.join(none_left))
    if a.check or problems or unknown:
        return 1 if problems or unknown else 0
    data = {'_opis': 'D107: głos każdej wypowiedzi w kwestiach narratora całej gry (produkcja po t1); przegląd ręczny '
                     'z kontekstem okna (analysis/tools/speakers_freeze.py). Format jak speakers_t1.json.'}
    data.update(out)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(os.path.relpath(OUT, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
