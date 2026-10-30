"""Statystyki do REPORT.md: kategorie kwestii, mówcy, znaki PL, znaczniki, placeholdery.

Wejście: work/out/pl_terms.json, work/out/lines.jsonl (z extract_lines.py) + bundle z kopii roboczej.
Wyjście: work/out/stats.json (tylko liczby i nazwy kluczy/mówców, bez pełnych tekstów).
"""
import json
import os
import re
from collections import Counter, defaultdict

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLES = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')
OUT = os.path.join(ROOT, 'work', 'out')
DEV_BUNDLES = ('d3/quests/enemy tool', 'd3/quests/obstacle course')
STORY = {'StoryMessageNode', 'MultipleChoiceStoryMessageNode', 'StoryVirtueChoiceNode'}
EVENT_KINDS = {'story_event', 'travelevents', 'narrativeevents', 'cityevents', 'worldmap'}
COMBAT_NODES = {'DisplayEnemyActivation', 'SpawnEnemy', 'SpawnRandomEnemies', 'SpawnRandomEnemy', 'EnemySelectMessageNode'}

TAG = re.compile(r'<[^>]+>')
PH = re.compile(r'\{\d+\}')
PUA = re.compile('[-]')
ITALIC = re.compile(r'<i>(.*?)</i>', re.S)


def clean(s, name_len=6):
    s = PH.sub('X' * name_len, s)
    s = PUA.sub('', TAG.sub('', s))
    return re.sub(r'\s+', ' ', s).strip()


def spoken_italic(s):
    """Tylko fragmenty <i>…</i> (warstwa fabularna komunikatu); reszta to zwykle reguły."""
    return ' '.join(clean(m) for m in ITALIC.findall(s))


def load_characters():
    m = json.load(open(os.path.join(BUNDLES, 'manifest.dat'), encoding='utf-8'))
    fn = next(b['filename'] for b in m['bundleInfos'] if b['name'] == 'd3/storymessagecharacters')
    chars = {}
    for o in UnityPy.load(os.path.join(BUNDLES, fn)).objects:
        if o.type.name == 'MonoBehaviour':
            t = o.read_typetree()
            if t.get('_id'):
                chars[t['_id']] = {'asset': t['m_Name'], 'name_key': t.get('KeyName'), 'act': t.get('_act')}
    return chars


def model_key_refs(terms):
    """Klucze PL wskazywane przez modele (ScriptableObject/MonoBehaviour) poza grafami: napisy cutscenek, log kampanii itd."""
    m = json.load(open(os.path.join(BUNDLES, 'manifest.dat'), encoding='utf-8'))
    scan = json.load(open(os.path.join(OUT, 'class_scan.json'), encoding='utf-8'))
    want = {'CutsceneModel', 'NarrativeEventModel', 'CityEventModel', 'TravelEventModel', 'QuestModel',
            'GameFactsModel', 'CampaignModel', 'LegendModel', 'FeatModel', 'EnemyModel', 'StoryCharacterModel'}
    refs = defaultdict(set)
    byfile = {b['filename']: b['name'] for b in m['bundleInfos']}

    def walk(v, path):
        if isinstance(v, dict):
            for k, x in v.items():
                yield from walk(x, path + '.' + k)
        elif isinstance(v, list):
            for x in v:
                yield from walk(x, path + '[]')
        elif isinstance(v, str) and v in terms:
            yield path, v

    for path, v in scan.items():
        if not set(v.get('classes', {})) & want:
            continue
        env = UnityPy.load(os.path.join(BUNDLES, os.path.basename(path)))
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                cls = o.read().m_Script.read().m_ClassName
            except Exception:
                continue
            if cls not in want:
                continue
            t = o.read_typetree()
            for p, key in walk(t, ''):
                refs['%s%s' % (cls, re.sub(r'^\.', ':', p))].add(key)
    return {k: sorted(v) for k, v in refs.items()}


def main():
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    L = [json.loads(l) for l in open(os.path.join(OUT, 'lines.jsonl'), encoding='utf-8')]
    L = [r for r in L if r['bundle'] not in DEV_BUNDLES]
    chars = load_characters()

    # --- kategoria klucza (priorytet: dialog > narracja > zdarzenie > quest > walka > cel > wybór > system)
    prio = ['dialog', 'narracja_fabularna', 'zdarzenie', 'komunikat_questu', 'walka_teren', 'cel_misji',
            'opcja_wyboru', 'system_nagroda']
    cat_of = {}
    key_info = defaultdict(lambda: {'graphs': set(), 'speakers': set(), 'kinds': set(), 'node_types': set(),
                                    'conds': set(), 'old': True})
    for r in L:
        role = r['role']
        if role.startswith('other'):
            continue
        k = r['key']
        if role == 'choice':
            c = 'opcja_wyboru'
        elif role == 'objective':
            c = 'cel_misji'
        elif r['node_type'] in STORY:
            c = 'dialog' if r['speakers'] else 'narracja_fabularna'
        elif r['node_type'] == 'GiveTreasure' or r['kind'] == 'system':
            c = 'system_nagroda'
        elif r['kind'] in ('enemy', 'item', 'terrain') or r['node_type'] in COMBAT_NODES:
            c = 'walka_teren'
        elif r['kind'] in EVENT_KINDS:
            c = 'zdarzenie'
        else:
            c = 'komunikat_questu'
        if k not in cat_of or prio.index(c) < prio.index(cat_of[k]):
            cat_of[k] = c
        ki = key_info[k]
        ki['graphs'].add(r['graph']); ki['kinds'].add(r['kind']); ki['node_types'].add(r['node_type'])
        ki['speakers'].update(r['speakers']); ki['conds'].update(r['conds'])
        if not re.search(r'\bOLD\b', r['owner'] or ''):
            ki['old'] = False

    # --- klucze spoza grafów
    refs = model_key_refs(terms)
    model_keys = {}
    for field, keys in refs.items():
        for k in keys:
            if k not in cat_of:
                model_keys.setdefault(k, field)
    for k, field in model_keys.items():
        cls = field.split(':')[0]
        cat_of[k] = {'CutsceneModel': 'napisy_cutscenek'}.get(cls, 'model:' + cls)
    for k, t in terms.items():
        if k in cat_of:
            continue
        srcs = ' '.join(t['sources'])
        if 'Story' in srcs or 'csv:StoryAct' in srcs:
            cat_of[k] = 'fabula_niepowiazana'
        elif 'Glossary' in srcs:
            cat_of[k] = 'glosariusz_zasady'
        elif 'Enemy' in srcs:
            cat_of[k] = 'wrogowie_opisy'
        elif 'i2:' in srcs and 'csv:' not in srcs:
            cat_of[k] = 'quest_niepowiazany'
        else:
            cat_of[k] = 'ui_system'

    # --- statystyki znaków
    cats = defaultdict(lambda: {'keys': 0, 'chars_raw': 0, 'chars_clean': 0, 'chars_italic': 0, 'empty_pl': 0})
    for k, c in cat_of.items():
        t = terms.get(k, {}).get('text') or ''
        s = cats[c]
        s['keys'] += 1
        if not t:
            s['empty_pl'] += 1
        s['chars_raw'] += len(t)
        s['chars_clean'] += len(clean(t))
        s['chars_italic'] += len(spoken_italic(t))

    # --- mówcy
    spk = defaultdict(lambda: {'lines': 0, 'chars': 0})
    for k, ki in key_info.items():
        if cat_of.get(k) != 'dialog':
            continue
        n = clean(terms[k]['text'])
        for s in ki['speakers'] or {'?'}:
            spk[s]['lines'] += 1
            spk[s]['chars'] += len(n)
    speakers = []
    for sid, v in sorted(spk.items(), key=lambda x: -x[1]['lines']):
        ch = chars.get(sid, {})
        nk = ch.get('name_key')
        speakers.append({'id': sid, 'asset': ch.get('asset'), 'name_key': nk,
                         'name_pl': (terms.get(nk) or {}).get('text') if nk else None,
                         'name_en': (terms.get(nk) or {}).get('en') if nk else None, **v})
    multi = sum(1 for k, ki in key_info.items() if cat_of.get(k) == 'dialog' and len(ki['speakers']) > 1)

    # --- znaczniki i placeholdery (wszystkie kwestie fabularne + komunikaty)
    tag_c, ph_c, pua_c, var_c = Counter(), Counter(), Counter(), Counter()
    story_cats = {'dialog', 'narracja_fabularna', 'zdarzenie', 'komunikat_questu', 'walka_teren', 'opcja_wyboru', 'cel_misji'}
    for k, c in cat_of.items():
        if c not in story_cats:
            continue
        t = terms.get(k, {}).get('text') or ''
        for m in re.findall(r'<(/?[a-zA-Z]+)(=[^>]*)?>', t):
            tag_c[m[0] + ('=' + m[1][1:].split('>')[0][:20] if m[1] and m[0] == 'style' else '')] += 1
        ph_c['{n}'] += len(PH.findall(t))
        pua_c['glyph'] += len(PUA.findall(t))
        if re.search(r'\w\((a|y|e|ą|o|em|aś|eś|łaś|łeś)\)', t):
            var_c['nawias_rodzaj'] += 1
        if re.search(r'\w+/\w+', clean(t)) and not re.search(r'https?://', t):
            var_c['ukosnik'] += 1
        if '[i2' in t or '{[' in t:
            var_c['i2_param'] += 1
    arg_types = Counter(a for r in L if r['role'] == 'message' for a in r['arg_types'] if a)
    name_suffix = Counter()
    for r in L:
        if r['node_type'] in STORY and r['role'] == 'message' and r['node_name']:
            m = re.match(r'^\d+([A-Z]{1,2})$', r['node_name'])
            if m:
                name_suffix[m.group(1)] += 1

    hero_cond_keys = sum(1 for k, ki in key_info.items() if any(c.startswith('HERO:') for c in ki['conds']))
    stats = {
        'terms_total': len(terms), 'terms_with_pl': sum(1 for t in terms.values() if t['text']),
        'categories': dict(cats), 'speakers': speakers, 'dialog_multi_speaker_keys': multi,
        'tags': tag_c.most_common(30), 'placeholders': dict(ph_c), 'glyphs': dict(pua_c),
        'variant_patterns': dict(var_c), 'arg_types': arg_types.most_common(), 'node_name_suffix': name_suffix.most_common(20),
        'keys_with_hero_condition': hero_cond_keys,
        'old_only_keys': sum(1 for k, ki in key_info.items() if ki['old']),
        'model_ref_fields': {f: len(v) for f, v in refs.items()},
        'background_types': Counter(r['background'] for r in L if r['background']).most_common(40),
        'graphs_by_kind': Counter(),
    }
    graphs = json.load(open(os.path.join(OUT, 'graphs.json'), encoding='utf-8'))
    stats['graphs_by_kind'] = Counter(g['kind'] for g in graphs if g['bundle'] not in DEV_BUNDLES)
    json.dump(stats, open(os.path.join(OUT, 'stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(cat_of, open(os.path.join(OUT, 'key_categories.json'), 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
