"""Pokrycie wydania audio (D96): ile kwestii z wybranych części gry ma wszystkie fragmenty w manifeście.

  .venv/Scripts/python -I analysis/tools/release_coverage.py [--release m3] [--acts 1 3]

Kwestia jest pełna, gdy każdy jej fragment tekstu ma plik w manifeście, a każda luka ma nagraną co najmniej jedną
wartość. Na konsolę idą liczby według paczki (klucze techniczne), lista kwestii z brakami do analysis/work/out/.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

from lektor import db, paths, progress
from lektor import direction as D


def coverage(acts):
    con = db.connect(paths.DB)
    manifest = json.load(open(os.path.join(paths.AUDIO, 'manifest.json'), encoding='utf-8'))
    have = set(manifest['fragments'])
    voices = {r['id']: r['voice'] for r in con.execute('SELECT id, voice FROM fragments')}
    values = defaultdict(list)
    for r in con.execute('SELECT key, arg, fragment FROM slot_values'):
        values[r['key'], r['arg']].append(r['fragment'])
    segs = defaultdict(list)
    for r in con.execute('SELECT key, kind, arg, fragment FROM segments ORDER BY key, idx'):
        segs[r['key']].append(r)
    rows, missing = defaultdict(lambda: [0, 0, 0]), []
    for line in con.execute('SELECT key, grp FROM lines WHERE tts = 1'):
        grp = line['grp'] or 'system'
        if progress.act(grp) not in acts:
            continue
        gaps = []
        for s in segs[line['key']]:
            if s['kind'] == 'slot':
                vals = [f for f in values.get((line['key'], s['arg']), []) if f]
                if vals and not any(f in have for f in vals):
                    gaps.append('luka')
            elif s['fragment'] and s['fragment'] not in have:
                gaps.append(D.engine(voices.get(s['fragment'], '')))
        r = rows[grp]
        r[0] += 1
        r[1] += not gaps
        r[2] += 'elevenlabs' in gaps
        if gaps:
            missing.append({'key': line['key'], 'group': grp, 'missing': sorted(set(gaps))})
    return rows, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', default='m3')
    ap.add_argument('--acts', type=int, nargs='*', default=[1, 3])
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    paths.use(a.release)
    rows, missing = coverage(set(a.acts))
    out = os.path.join(paths.WORK, 'out', '%s_coverage_missing.json' % a.release)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(missing, open(out, 'w', encoding='utf-8'), indent=1)
    total = [sum(r[i] for r in rows.values()) for i in range(3)]
    print('| Paczka | Kwestie | Pełne | Braki ElevenLabs | Inne braki |')
    print('|---|---:|---:|---:|---:|')
    for g in sorted(rows, key=progress.rank):
        r = rows[g]
        if r[0] != r[1]:
            print('| %s | %d | %d | %d | %d |' % (g, r[0], r[1], r[2], r[0] - r[1] - r[2]))
    print('| razem (%d paczek) | %d | %d | %d | %d |' % (len(rows), total[0], total[1], total[2], total[0] - total[1] - total[2]))
    print('kwestie z brakami: %s' % paths.rel(out), file=sys.stderr)


if __name__ == '__main__':
    main()
