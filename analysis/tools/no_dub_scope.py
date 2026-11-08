"""Postacie bez dubbingu w całej grze: kwestie spoza M2 i szacunek kredytów ElevenLabs.

Kwestia postaci to klucz okna fabularnego z mówcą (dialog, jak w scope.voice_for). Klucz z mówcą z dubbingiem
(bohater, VARIABLE_HERO, Ne'Krul, Xenith) czyta OmniVoice, więc tu nie wchodzi. Tekst przechodzi tę samą
normalizację co fragmenty M2 (normalize + pronounce), a znaki liczymy po deduplikacji tekstu w obrębie postaci.

Wejście: kopia gry (lektor.game), baza M2 (analysis/work/lektor/m2.sqlite).
Wyjście (nieśledzone): work/out/no_dub_lines.jsonl (z tekstami), work/out/no_dub_summary.json.
Na konsolę idą tylko identyfikatory, liczby i nazwy grafów.

Uruchomienie (z katalogu głównego repozytorium): .venv/Scripts/python -I analysis/tools/no_dub_scope.py
"""
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict

from lektor import direction as D
from lektor import game as G
from lektor import paths, scope
from lektor import segment as S
from lektor.normalize import normalize, pronounce

OUT = os.path.join(paths.WORK, 'out')
M2_DB = os.path.join(paths.WORK, 'lektor', 'm2.sqlite')
DUBBED = set(scope.HEROES) | {'BLOOD_SISTER', 'DRAGON_HYBRID'}
# Złoczyńcy z Voice_Villains: tylko okrzyki z planszy, 3–7 s mowy (VOICES.md, D19).
BARKS = {'LEVIRAX', 'GREYSDON', 'VRASKHAR', 'NAVOTH', 'RENEYR', 'SHADOW_RENEYR', 'BARONZACHARETH', 'GILLIAM',
         'GILLIAM_EVIL'}
EL_CAST = {k for k, v in scope.CHARACTER_VOICES.items() if v in D.ELEVEN_VOICES}
DEV_OWNERS = ('Enemy Tool', 'Obstacle Course')
RATE = 0.44         # kredyty na znak eleven_v4 (E9, E11, E13)
RETAKE = 1.07       # ponowne podejścia w E13: +7% kosztu pierwszych podejść
CPS = 13.95         # tempo eleven_v4 w E13, znaki na sekundę mowy
SCENARIO = re.compile(r'\b(S?Q\d+[A-Z]?)\b')


def status(sid):
    if sid in EL_CAST:
        return 'głos EL z E13'
    if sid in BARKS:
        return 'złoczyńca z okrzykami'
    return 'nowa postać'


def act_of(bundle, owner):
    """Akt 2: d3/act2, sceny scenariuszy d3/quests/dle04 i grafy z nazwą „A2 …”."""
    return '2' if 'act2' in bundle or '/dle04/' in bundle or owner.upper().startswith(('ACT 2', 'A2 ')) else '1'


def source(bundle, owner):
    """Grupa źródła: akt i scenariusz albo rodzaj wydarzenia (nazwa grafu, nie tekst gry)."""
    m = SCENARIO.search(owner.upper())
    act = act_of(bundle, owner)
    if bundle.startswith('d3/quests/'):
        return 'akt %s · %s' % (act, bundle.rsplit('/', 1)[-1].upper())
    if m:
        return 'akt %s · %s' % (act, m.group(1))
    kind = G.source_kind(bundle)
    return 'akt %s · %s' % (act, {'story_event': 'sceny i wydarzenia', 'travelevents': 'podróże',
                                  'cityevents': 'miasto', 'narrativeevents': 'wydarzenia',
                                  'worldmap': 'miasto'}.get(kind, kind))


def main():
    game = G.Game()
    terms = game.terms()
    refs, seen = defaultdict(list), set()
    for name in sorted(game.files):
        if not name.startswith('d3/'):
            continue
        for gr in game.graphs(name):
            if gr['hash'] in seen or gr['owner'].startswith(DEV_OWNERS):
                continue
            seen.add(gr['hash'])
            for ln in G.graph_lines(gr, terms):
                if ln['role'] == 'message' and ln['node_type'] in G.STORY_NODES and ln['speakers']:
                    refs[ln['key']].append(ln)
    m2 = {r[0]: r[1] for r in sqlite3.connect(M2_DB).execute('SELECT key, voice FROM lines')}

    rows, check = [], defaultdict(int)
    for key, rs in sorted(refs.items()):
        ids = sorted({s.replace('STORY_CHARACTER_', '') for r in rs for s in r['speakers']})
        if any(i in DUBBED or i.startswith('VARIABLE_HERO') for i in ids):
            continue
        raw = (terms.get(key) or {}).get('text')
        if not raw:
            continue
        text = pronounce(normalize(raw)).strip()
        if not re.search(r'\w', text):
            continue
        r0 = min(rs, key=lambda r: (r['bundle'], r['owner']))
        row = {'key': key, 'speaker': ids[0], 'speakers': ids, 'status': status(ids[0]),
               'bundle': r0['bundle'], 'owner': r0['owner'], 'source': source(r0['bundle'], r0['owner']),
               'act': act_of(r0['bundle'], r0['owner']),
               'in_m2': key in m2, 'slots': len(S.SLOT.findall(raw)), 'chars': len(text), 'text': text}
        rows.append(row)
        if key in m2:
            check[m2[key]] += len(text)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'no_dub_lines.jsonl'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)

    todo = [r for r in rows if not r['in_m2']]
    by_speaker, by_source, texts = defaultdict(lambda: defaultdict(int)), defaultdict(lambda: defaultdict(int)), set()
    for r in todo:
        first = (r['speaker'], r['text']) not in texts
        texts.add((r['speaker'], r['text']))
        for agg, k in ((by_speaker, r['speaker']), (by_source, r['source'])):
            agg[k]['keys'] += 1
            agg[k]['fragments'] += first
            agg[k]['chars'] += r['chars'] if first else 0
            agg[k]['slots'] += bool(r['slots'])
            agg[k]['chars_act' + r['act']] += r['chars'] if first else 0
            if agg is by_source:
                agg[k][r['status']] += r['chars'] if first else 0
    speakers = {s: dict(v, status=status(s), credits=round(v['chars'] * RATE)) for s, v in by_speaker.items()}
    totals = defaultdict(lambda: defaultdict(int))
    for s, v in speakers.items():
        for f in ('keys', 'fragments', 'chars', 'slots', 'chars_act1', 'chars_act2'):
            totals[v['status']][f] += v.get(f, 0)
            totals['razem'][f] += v.get(f, 0)
        totals[v['status']]['speakers'] += 1
        totals['razem']['speakers'] += 1
    summary = {
        'rate': RATE, 'retake': RETAKE, 'cps': CPS, 'graphs': len(seen), 'dialog_keys_no_dub': len(rows),
        'in_m2': sum(r['in_m2'] for r in rows), 'm2_check_chars_by_voice': dict(check),
        'speakers': speakers, 'sources': {k: dict(v) for k, v in by_source.items()},
        'totals': {k: dict(v, credits=round(v['chars'] * RATE), credits_retake=round(v['chars'] * RATE * RETAKE),
                           audio_min=round(v['chars'] / CPS / 60, 1)) for k, v in totals.items()},
    }
    json.dump(summary, open(os.path.join(OUT, 'no_dub_summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print('grafy: %d, klucze dialogów bez dubbingu: %d, w M2: %d' % (len(seen), len(rows), summary['in_m2']))
    print('kontrola M2 (znaki wg głosu M2):', dict(check))
    print('\n| mówca | status | klucze | fragmenty | znaki | akt 1 | akt 2 | z luką | kredyty |')
    for s, v in sorted(speakers.items(), key=lambda x: -x[1]['chars']):
        print('| %s | %s | %d | %d | %d | %d | %d | %d | %d |' % (
            s, v['status'], v['keys'], v['fragments'], v['chars'], v.get('chars_act1', 0), v.get('chars_act2', 0),
            v['slots'], v['credits']))
    print('\n| źródło | klucze | fragmenty | znaki |')
    for k, v in sorted(by_source.items()):
        print('| %s | %d | %d | %d |' % (k, v['keys'], v['fragments'], v['chars']))
    print('\n| grupa | postacie | fragmenty | znaki | akt 1 | akt 2 | kredyty | z ponownymi | min audio |')
    for k, v in summary['totals'].items():
        print('| %s | %d | %d | %d | %d | %d | %d | %d | %.1f |' % (
            k, v['speakers'], v['fragments'], v['chars'], v.get('chars_act1', 0), v.get('chars_act2', 0),
            v['credits'], v['credits_retake'], v['audio_min']))


if __name__ == '__main__':
    sys.exit(main())
