"""Zakres milestone 1: prolog (CUTSCENE_01) i Q1 aktu 1 — lista kluczy, znaki, placeholdery, rozkład na głosy.

Grupy kluczy:
  cutscene_01  napisy CutsceneModel CUTSCENE_01 (displayAt),
  story_q1     sceny fabularne d3/act1 „TANGERINE Q1 …” (Intro, Outro Win, Outro Lose),
  scene_q1     wszystkie grafy ze sceny d3/quests/box1/story/q1 (także współdzielone kopie Default*),
  enemies_q1   modele i grafy wrogów, do których scena Q1 odwołuje się wprost (SpawnEnemy → EnemyModel),
  system       grafy globalne d3/gamereq (koniec rundy, atak, aktywacje, łup) — używane w każdym queście.
Klucz trafia do pierwszej grupy z tej kolejności.

Wejście: work/out/{pl_terms.json,lines.jsonl,key_categories.json} + kopie bundli.
Wyjście: work/out/m1_scope.json (bez tekstów) i tabela Markdown na stdout.

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/m1_scope.py > analysis/M1_SCOPE_keys.md
"""
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLES = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')
OUT = os.path.join(ROOT, 'work', 'out')
Q1_BUNDLE = 'd3/quests/box1/story/q1'
STORY_PREFIX = 'TANGERINE Q1 '
CUTSCENE_ID = 'CUTSCENE_01'
GROUPS = ('cutscene_01', 'story_q1', 'scene_q1', 'enemies_q1', 'system')
HEROES = {'BRYNN', 'SYRUS', 'KEHLI', 'VAERIX', 'GALADEN', 'CHANCE',
          'VARIABLE_HERO1', 'VARIABLE_HERO2', 'VARIABLE_HERO3', 'VARIABLE_HERO4'}
NARRATOR_CATS = {'narracja_fabularna', 'komunikat_questu', 'zdarzenie', 'napisy_cutscenek', 'quest_niepowiazany',
                 'fabula_niepowiazana'}
TAG = re.compile(r'<[^>]+>')
PH = re.compile(r'\{\d+\}')
ITALIC = re.compile(r'<i>(.*?)</i>', re.S)


def clean(s):
    return re.sub(r'\s+', ' ', TAG.sub('', PH.sub('XXXXXX', s))).strip()


def bundle_files():
    m = json.load(open(os.path.join(BUNDLES, 'manifest.dat'), encoding='utf-8'))
    return {b['name']: b['filename'] for b in m['bundleInfos']}


def script_class(o, cache):
    t = o.read_typetree()
    sp = t.get('m_Script', {})
    k = (sp.get('m_FileID'), sp.get('m_PathID'))
    if k not in cache:
        try:
            cache[k] = o.read().m_Script.read().m_ClassName
        except Exception:
            cache[k] = '?'
    return cache[k], t


def scan_q1(path):
    """Hashe grafów (jak w extract_lines.py), napisy i odwołania do obiektów z innych bundli (PPtr) ze sceny Q1."""
    hashes, strings, refs = set(), set(), set()
    for o in UnityPy.load(path).objects:
        if o.type.name != 'MonoBehaviour':
            continue
        t = o.read_typetree()
        g = t.get('_serializedGraph') or t.get('boundGraphSerialization')
        if g:
            hashes.add(hashlib.sha1(g.encode('utf-8')).hexdigest()[:12])
            strings.update(re.findall(r'"([A-Z][A-Z0-9_]{3,})"', g))
            externals = o.assets_file.externals
            for p in t.get('_objectReferences') or t.get('boundGraphObjectReferences') or []:
                if p.get('m_FileID', 0) > 0:
                    cab = os.path.basename(externals[p['m_FileID'] - 1].path).lower()
                    refs.add((cab, p['m_PathID']))
        strings.update(re.findall(r"'([A-Z][A-Z0-9_]{3,})'", repr(t)))
    return hashes, strings, refs


def walk_strings(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from walk_strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk_strings(x)
    elif isinstance(v, str):
        yield v


def enemy_models(files, terms):
    """{enemy_id: {'bundle', 'keys'}} z modeli EnemyModel w bundlach d3/enemies/*."""
    res, cache = {}, {}
    for name, fn in files.items():
        if not name.startswith('d3/enemies/'):
            continue
        for o in UnityPy.load(os.path.join(BUNDLES, fn)).objects:
            if o.type.name != 'MonoBehaviour':
                continue
            cls, t = script_class(o, cache)
            if cls == 'EnemyModel' and t.get('_id'):
                res[t['_id']] = {'bundle': name, 'ref': (o.assets_file.name.lower(), o.path_id),
                                 'keys': sorted({s for s in walk_strings(t) if s in terms})}
    return res


def cutscene_keys(files):
    cache = {}
    for name, fn in files.items():
        if not name.startswith('d3/cutscenes/'):
            continue
        for o in UnityPy.load(os.path.join(BUNDLES, fn)).objects:
            if o.type.name != 'MonoBehaviour':
                continue
            cls, t = script_class(o, cache)
            if cls == 'CutsceneModel' and t.get('_id') == CUTSCENE_ID:
                return t, [s['subtitleKeyName'] for s in t.get('Subtitles', [])]
    return None, []


def voice_of(cat, speakers):
    if cat == 'dialog':
        ids = [s.replace('STORY_CHARACTER_', '') for s in speakers]
        if ids and all(i in HEROES for i in ids):
            return 'bohaterowie'
        return 'inny' if ids else 'narrator'
    return 'narrator' if cat in NARRATOR_CATS else 'systemowy'


def main():
    files = bundle_files()
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    cats = json.load(open(os.path.join(OUT, 'key_categories.json'), encoding='utf-8'))
    lines = [json.loads(l) for l in open(os.path.join(OUT, 'lines.jsonl'), encoding='utf-8')]

    q1_hashes, q1_strings, q1_refs = scan_q1(os.path.join(BUNDLES, files[Q1_BUNDLE]))
    enemies = enemy_models(files, terms)
    q1_enemies = sorted(e for e in enemies if e in q1_strings or enemies[e]['ref'] in q1_refs)
    enemy_bundles = {enemies[e]['bundle'] for e in q1_enemies}
    cs_model, cs_keys = cutscene_keys(files)

    group_of, info = {}, defaultdict(lambda: {'speakers': set(), 'owners': set(), 'conds': set(), 'seq': None})

    def add(key, group, rec=None):
        if key not in terms or not terms[key].get('text'):
            return
        group_of.setdefault(key, group)
        if rec:
            ki = info[key]
            ki['speakers'].update(rec['speakers'])
            ki['owners'].add(rec['owner'])
            ki['conds'].update(rec['conds'])
            if rec.get('seq') is not None and (ki['seq'] is None or rec['seq'] < ki['seq']):
                ki['seq'] = rec['seq']

    for k in cs_keys:
        add(k, 'cutscene_01')
    for r in lines:
        if r['bundle'] == 'd3/act1' and r['owner'].startswith(STORY_PREFIX):
            add(r['key'], 'story_q1', r)
    for r in lines:
        if r['graph'] in q1_hashes:
            add(r['key'], 'scene_q1', r)
    for e in q1_enemies:
        for k in enemies[e]['keys']:
            add(k, 'enemies_q1')
    for r in lines:
        if r['kind'] == 'enemy' and r['bundle'] in enemy_bundles:
            add(r['key'], 'enemies_q1', r)
    for r in lines:
        if r['bundle'] == 'd3/gamereq':
            add(r['key'], 'system', r)

    rows = []
    for k, g in group_of.items():
        txt = terms[k]['text']
        cat = cats.get(k, 'brak')
        ki = info[k]
        rows.append({'key': k, 'group': g, 'category': cat, 'voice': voice_of(cat, ki['speakers']),
                     'speakers': sorted(s.replace('STORY_CHARACTER_', '') for s in ki['speakers']),
                     'hero_variant': sorted(c for c in ki['conds'] if c.startswith('HERO:')),
                     'chars': len(clean(txt)), 'chars_italic': len(' '.join(clean(m) for m in ITALIC.findall(txt))),
                     'placeholders': len(set(PH.findall(txt))), 'owners': sorted(ki['owners'])[:3], 'seq': ki['seq']})
    order = {g: i for i, g in enumerate(GROUPS)}
    rows.sort(key=lambda r: (order[r['group']], r['owners'][:1], r['seq'] if r['seq'] is not None else 1e9, r['key']))
    meta = {'q1_graphs': len(q1_hashes), 'q1_enemies': q1_enemies, 'enemy_bundles': sorted(enemy_bundles),
            'cutscene_01': {'sound_event': cs_model.get('SoundEventName') if cs_model else None,
                            'subtitles': [(s['subtitleKeyName'], s['displayAt']) for s in (cs_model or {}).get('Subtitles', [])]}}
    json.dump({'meta': meta, 'rows': rows}, open(os.path.join(OUT, 'm1_scope.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print('| # | Klucz | Grupa | Kategoria | Głos | Mówca | Wariant | Znaki | {n} |')
    print('|---:|---|---|---|---|---|---|---:|---:|')
    for i, r in enumerate(rows, 1):
        print('| %d | `%s` | %s | %s | %s | %s | %s | %d | %s |' % (
            i, r['key'], r['group'], r['category'], r['voice'], ', '.join(r['speakers']) or '–',
            ', '.join(c[5:].rstrip(':').replace('BB', 'bohater z BB') for c in r['hero_variant']) or '–',
            r['chars'], r['placeholders'] or ''))
    s = Counter()
    for r in rows:
        s[(r['group'], 'keys')] += 1
        s[(r['group'], 'chars')] += r['chars']
    print(json.dumps({'meta': meta, 'by_group': {f'{a}.{b}': v for (a, b), v in s.items()}}, ensure_ascii=False),
          file=sys.stderr)


if __name__ == '__main__':
    main()
