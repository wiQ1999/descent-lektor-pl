"""Odczyt kopii gry przez UnityPy (tylko odczyt): teksty PL, grafy NodeCanvas, modele wrogów i przerywniki.

Logika przeniesiona z analysis/tools/extract_lines.py, m1_scope.py i analyze.py.
"""
import csv
import hashlib
import io
import json
import os
import re
from collections import defaultdict

from . import paths

STORY_NODES = {'StoryMessageNode', 'MultipleChoiceStoryMessageNode', 'StoryVirtueChoiceNode'}
COMBAT_NODES = {'DisplayEnemyActivation', 'SpawnEnemy', 'SpawnRandomEnemies', 'SpawnRandomEnemy', 'EnemySelectMessageNode'}
EVENT_KINDS = {'story_event', 'travelevents', 'narrativeevents', 'cityevents', 'worldmap'}


class Game:
    """Dostęp do bundli z kopii gry; każdy bundel jest wczytywany najwyżej raz."""

    def __init__(self, bundles=paths.BUNDLES):
        import UnityPy
        self._unitypy = UnityPy
        self.dir = bundles
        m = json.load(open(os.path.join(bundles, 'manifest.dat'), encoding='utf-8'))
        self.files = {b['name']: b['filename'] for b in m['bundleInfos']}
        self._class_cache = {}

    def manifest_hash(self):
        with open(os.path.join(self.dir, 'manifest.dat'), 'rb') as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:12]

    def objects(self, name):
        return self._unitypy.load(os.path.join(self.dir, self.files[name])).objects

    def behaviours(self, name):
        """(obiekt, typetree, klasa skryptu) dla MonoBehaviour z bundla."""
        for o in self.objects(name):
            if o.type.name != 'MonoBehaviour':
                continue
            t = o.read_typetree()
            sp = t.get('m_Script', {})
            k = (sp.get('m_FileID'), sp.get('m_PathID'))
            if k not in self._class_cache:
                try:
                    self._class_cache[k] = o.read().m_Script.read().m_ClassName
                except Exception:
                    self._class_cache[k] = '?'
            yield o, t, self._class_cache[k]

    def terms(self):
        """Klucz → {text (PL), en, sources}. Źródła: CSV z loc/pl i loc/en oraz zasoby I2."""
        terms = {}

        def add(key, text, src, en=None):
            e = terms.setdefault(key, {'text': text, 'en': en, 'sources': []})
            if text and not e['text']:
                e['text'] = text
            if en and not e['en']:
                e['en'] = en
            e['sources'].append(src)

        for name in self.files:
            if not (name in ('loc/pl', 'loc/en', 'localization') or name.startswith('qloc/')):
                continue
            for o in self.objects(name):
                if o.type.name == 'TextAsset' and name in ('loc/pl', 'loc/en'):
                    d = o.read()
                    for r in list(csv.reader(io.StringIO(d.m_Script)))[1:]:
                        if len(r) < 4:
                            continue
                        if name == 'loc/pl':
                            add(r[0], r[3], 'csv:' + d.m_Name)
                        else:
                            terms.setdefault(r[0], {'text': '', 'en': None, 'sources': []})['en'] = r[3]
                elif o.type.name == 'MonoBehaviour':
                    t = o.read_typetree()
                    src = t.get('mSource')
                    if not src:
                        continue
                    langs = [lang['Code'] for lang in src['mLanguages']]
                    if 'pl' not in langs:
                        continue
                    pi, ei = langs.index('pl'), langs.index('en') if 'en' in langs else None
                    for tm in src['mTerms']:
                        tl = tm['Languages']
                        add(tm['Term'], tl[pi] if pi < len(tl) else '', 'i2:' + t['m_Name'],
                            tl[ei] if ei is not None and ei < len(tl) else None)
        return terms

    def graphs(self, name):
        """Grafy NodeCanvas z bundla: dict(bundle, owner, hash, graph, refs). refs to odwołania PPtr do innych bundli."""
        for o, t, _ in self.behaviours(name):
            g = t.get('_serializedGraph')
            owner = t.get('m_Name')
            if not g:
                g = t.get('boundGraphSerialization')
                if not g:
                    continue
                try:
                    owner = o.read().m_GameObject.read().m_Name
                except Exception:
                    owner = ''
            refs = set()
            externals = o.assets_file.externals
            for p in t.get('_objectReferences') or t.get('boundGraphObjectReferences') or []:
                if p.get('m_FileID', 0) > 0:
                    refs.add((os.path.basename(externals[p['m_FileID'] - 1].path).lower(), p['m_PathID']))
            yield {'bundle': name, 'owner': owner, 'hash': hashlib.sha1(g.encode('utf-8')).hexdigest()[:12],
                   'graph': json.loads(g), 'refs': refs}

    def enemy_models(self, terms):
        """{id modelu: {bundle, ref, keys}} dla EnemyModel z bundli d3/enemies/*."""
        out = {}
        for name in self.files:
            if not name.startswith('d3/enemies/'):
                continue
            for o, t, cls in self.behaviours(name):
                if cls == 'EnemyModel' and t.get('_id'):
                    out[t['_id']] = {'bundle': name, 'ref': (o.assets_file.name.lower(), o.path_id),
                                     'keys': sorted({s for s in walk_strings(t) if s in terms}),
                                     'theme': t.get('ThemeTraits', 0), 'random': bool(t.get('IsRandomEligible'))}
        return out

    def cutscene_keys(self, cutscene_id):
        for name in self.files:
            if not name.startswith('d3/cutscenes/'):
                continue
            for _, t, cls in self.behaviours(name):
                if cls == 'CutsceneModel' and t.get('_id') == cutscene_id:
                    return [s['subtitleKeyName'] for s in t.get('Subtitles', [])]
        return []


def walk_strings(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from walk_strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk_strings(x)
    elif isinstance(v, str):
        yield v


def iter_strings(v, path='', ptype=''):
    """(ścieżka, wartość, $type najbliższego obiektu-przodka) dla każdego napisu."""
    if isinstance(v, dict):
        ptype = v.get('$type', ptype)
        for k, x in v.items():
            yield from iter_strings(x, path + '.' + k, ptype)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from iter_strings(x, '%s[%d]' % (path, i), ptype)
    elif isinstance(v, str):
        yield path, v, ptype


def condition_label(c):
    """Etykieta warunku (wariant zależny od bohatera, cnoty, DLC, języka) albo None."""
    c = c or {}
    ct = (c.get('$type') or '').split('.')[-1]
    if ct == 'CheckHeroIsInPlay':
        m = c.get('_modelId') or {}
        if m.get('_value'):
            return 'HERO:' + m['_value']
        idx = (c.get('_playerIndex') or {}).get('_name') or ''
        return 'HERO:' + (('HERO_' + idx.split()[0].upper()) if idx.endswith(' Index') else 'BB:' + idx)
    return {'CheckHeroVirtue': 'VIRTUE', 'CheckProductOwned': 'PRODUCT', 'CheckCurrentLanguage': 'LANGUAGE'}.get(ct)


def edge_labels(node, n_children):
    t = node.get('$type', '')
    if t.endswith('.ConditionNode'):
        lab = condition_label(node.get('_condition'))
        return [lab, 'NOT ' + lab] if lab else [None, None]
    if t.endswith('.MultipleConditionNode'):
        return [condition_label(c) for c in node.get('conditions', [])] + [None] * n_children
    return [None] * n_children


def order_nodes(g):
    """DFS od kolejnych korzeni; {id: (seq, [warunki z bezpośrednich gałęzi])}."""
    nodes = g.get('nodes', [])
    by_id = {n.get('$id'): n for n in nodes if n.get('$id')}
    out_edges = defaultdict(list)
    for c in g.get('connections', []):
        s, t = (c.get('_sourceNode') or {}).get('$ref'), (c.get('_targetNode') or {}).get('$ref')
        if s and t:
            out_edges[s].append(t)
    conds = defaultdict(set)
    for s, targets in out_edges.items():
        for t, lab in zip(targets, edge_labels(by_id.get(s, {}), len(targets))):
            if lab:
                conds[t].add(lab)
    order, seq = {}, 0
    for root in by_id:
        stack = [root]
        while stack:
            nid = stack.pop()
            if nid in order:
                continue
            order[nid] = (seq, sorted(conds.get(nid, ())))
            seq += 1
            stack.extend(reversed(out_edges.get(nid, [])))
    return order


def speaker_info(node):
    s = node.get('_settings') or {}
    speakers = []
    for i in range(1, 5):
        c = s.get('Character_%d' % i) or {}
        if c.get('_characterId') and c.get('IsSpeaking'):
            speakers.append(c['_characterId'])
    return speakers


def message_args(msg):
    """Argumenty {n} komunikatu: typ i odwołanie (klucz albo nazwa zmiennej blackboardu)."""
    out = []
    for a in msg.get('_arguments') or []:
        d = a.get('Data') if isinstance(a.get('Data'), dict) else {}
        kind = a.get('ArgType') or ('LocalizationKey' if '$content' in d else None)
        out.append({'type': kind, 'ref': d.get('$content') or d.get('_name')})
    return out


def find_message(v, key):
    """Komunikat z kluczem w węźle, także w zadaniu węzła akcji (SetObjective trzyma _message w _action)."""
    if isinstance(v, dict):
        if v.get('_key') == key:
            return v
        v = list(v.values())
    if isinstance(v, list):
        for x in v:
            found = find_message(x, key) if isinstance(x, (dict, list)) else None
            if found:
                return found
    return None


def source_kind(bname):
    if bname in ('d3/act1', 'd3/act2'):
        return 'story_event'
    if bname in ('d3/narrativeevents', 'd3/travelevents', 'd3/cityevents'):
        return bname.split('/')[1]
    if bname.startswith('d3/quests/'):
        return 'quest'
    if bname.startswith('d3/enemies/'):
        return 'enemy'
    if bname.startswith('d3/weapons/') or bname == 'd3/items':
        return 'item'
    if bname.startswith(('d3/coreset/', 'd3/dle04/')):
        return 'terrain'
    if bname in ('d3/gamereq', 'd3/ui'):
        return 'system'
    if bname.startswith('d3/worldmap/'):
        return 'worldmap'
    return 'other'


def graph_lines(gr, terms):
    """Odwołania do kluczy z węzłów grafu: rola (message/choice/objective), mówcy, warunki, kolejność, argumenty."""
    g, kind = gr['graph'], source_kind(gr['bundle'])
    order = order_nodes(g)
    for n in g.get('nodes', []):
        ntype = n.get('$type', '').split('.')[-1]
        seq, conds = order.get(n.get('$id'), (None, []))
        msg = n.get('_message') or {}
        for path, val, ptype in iter_strings(n):
            if val not in terms or path.endswith(('$type', '$id', '._name')):
                continue
            if path == '._message._key':
                role = 'message'
            elif path.startswith('._message.Choices'):
                role = 'choice'
            elif ptype.endswith('SetObjective'):
                role = 'objective'
            else:
                continue  # nazwy, warunki i inne odwołania nie są tekstem okna
            yield {'key': val, 'role': role, 'node_type': ntype, 'kind': kind, 'bundle': gr['bundle'],
                   'owner': gr['owner'], 'graph': gr['hash'], 'seq': seq, 'conds': conds,
                   'speakers': speaker_info(n) if ntype in STORY_NODES else [],
                   'args': message_args(msg) if role == 'message' else [],
                   'objective_args': message_args(find_message(n, val) or {}) if role == 'objective' else []}


def category(line):
    """Kategoria odwołania (jak w analysis/tools/analyze.py)."""
    if line['role'] == 'choice':
        return 'opcja_wyboru'
    if line['role'] == 'objective':
        return 'cel_misji'
    if line['node_type'] in STORY_NODES:
        return 'dialog' if line['speakers'] else 'narracja_fabularna'
    if line['node_type'] == 'GiveTreasure' or line['kind'] == 'system':
        return 'system_nagroda'
    if line['kind'] in ('enemy', 'item', 'terrain') or line['node_type'] in COMBAT_NODES:
        return 'walka_teren'
    if line['kind'] in EVENT_KINDS:
        return 'zdarzenie'
    return 'komunikat_questu'


CATEGORY_PRIORITY = ['dialog', 'narracja_fabularna', 'zdarzenie', 'komunikat_questu', 'walka_teren', 'cel_misji',
                     'opcja_wyboru', 'system_nagroda']


def fallback_category(term):
    """Kategoria klucza spoza grafów, z nazw źródeł tekstu."""
    srcs = ' '.join(term['sources'])
    if 'Story' in srcs or 'csv:StoryAct' in srcs:
        return 'fabula_niepowiazana'
    if 'Glossary' in srcs:
        return 'glosariusz_zasady'
    if 'Enemy' in srcs:
        return 'wrogowie_opisy'
    if 'i2:' in srcs and 'csv:' not in srcs:
        return 'quest_niepowiazany'
    return 'ui_system'


TAG = re.compile(r'<[^>]+>')
