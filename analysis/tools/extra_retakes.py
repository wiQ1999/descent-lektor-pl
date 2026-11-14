"""Dodatkowe ponowne podejścia po limicie `select` (E16, D101): retake.json z odrzuconych, nieprzejętych fragmentów
zakresu testu (scope.TEST_GROUPS). Ucięta końcówka: podejście wolniej, jak w `select`. Fragmenty przejęte z poprzedniego
wydania zostają bez zmian. Na konsolę idzie tylko liczba fragmentów.

    .venv/Scripts/python -I analysis/tools/extra_retakes.py [--release t1]
    "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I -m lektor generate --release t1 --retake
    .venv/Scripts/python -I -m lektor evaluate --release t1
    .venv/Scripts/python -I -m lektor select --release t1      # potem znowu ten skrypt, do zera albo trzech rund
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from lektor import db, paths, scope  # noqa: E402
from lektor.evaluate import RETAKE_SLOWER  # noqa: E402


def retakes(release):
    paths.use(release)
    groups = set(scope.TEST_GROUPS[release])
    choice = json.load(open(os.path.join(paths.AUDIO, 'choice.json'), encoding='utf-8'))
    inherited = json.load(open(os.path.join(paths.AUDIO, 'inherited.json'), encoding='utf-8'))
    con = db.connect(paths.DB)
    grp = {r['key']: r['grp'] for r in con.execute('SELECT key, grp FROM lines')}
    frag_groups = collections.defaultdict(set)
    for q in ('SELECT key, fragment FROM segments', 'SELECT key, fragment FROM slot_values'):
        for r in con.execute(q):
            if r['fragment']:
                # wartości bez kwestii (@LOOT, @FEATS) liczą się do 'system', jak w progress.in_groups
                frag_groups[r['fragment']].add(grp.get(r['key'].split('#')[0]) or 'system')
    last = collections.Counter()
    for line in open(os.path.join(paths.AUDIO, 'takes.jsonl'), encoding='utf-8'):
        t = json.loads(line)
        last[t['fragment']] = max(last[t['fragment']], t['take'])
    out = {}
    for fid, c in choice.items():
        if not c['problems'] or fid in inherited or not frag_groups[fid] & groups or last[fid] >= 100:
            continue    # podejścia od 101 to ElevenLabs (E13)
        speed = c['speed']
        if 'koncowka' in c['problems']:
            s = speed or 1.0
            speed = round(max(min(0.9, s), s - RETAKE_SLOWER), 2)
        out[fid] = [last[fid] + 1, speed]
    json.dump(out, open(os.path.join(paths.AUDIO, 'retake.json'), 'w', encoding='utf-8'), indent=1)
    return len(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--release', default='t1', choices=sorted(scope.TEST_GROUPS))
    print(retakes(ap.parse_args().release))
