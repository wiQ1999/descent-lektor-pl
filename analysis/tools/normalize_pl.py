"""Prototyp normalizacji z E0. Kod przeniesiony do src/lektor/normalize.py (E2); ten plik tylko go importuje.

Uruchomienie kontrolne (pokazuje wszystkie miejsca z cyframi i ikonami w M1; wynik nieśledzony):
  .venv/Scripts/python -I analysis/tools/normalize_pl.py --m1
"""
import re

from lektor.normalize import *  # noqa: F401,F403
from lektor.normalize import PUA, TAG, normalize  # noqa: F401


def _m1_report():
    import json
    import os
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, 'work', 'out')
    terms = json.load(open(os.path.join(out, 'pl_terms.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(out, 'm1_scope.json'), encoding='utf-8'))['rows']
    n = 0
    for r in rows:
        t = terms[r['key']]['text'] or ''
        if re.search(r'\d|[-]|<link=TERM_(DAMAGE|FATIGUE|SUCCESS|SURGE|HEALTH_DIAL|EXPERIENCE)>|[A-ZŁŚŻ]{3,} [A-ZŁŚŻ]{3,}', t):
            n += 1
            print('%s\n  < %s\n  > %s' % (r['key'], re.sub(r'\s+', ' ', PUA.sub('[ikona]', TAG.sub('', t))), normalize(t)))
    print('kluczy z liczbami lub ikonami: %d' % n)


if __name__ == '__main__':
    import sys
    if '--m1' in sys.argv:
        _m1_report()
