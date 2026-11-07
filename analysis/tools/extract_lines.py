"""Ekstrakcja kwestii PL z Descent: Legends of the Dark (kopia robocza, tylko odczyt).

Wejście: work/game/.../StreamingAssets/bundles (kopie bundli) + work/out/class_scan.json.
Wyjście (nieśledzone): work/out/pl_terms.json, work/out/lines.jsonl, work/out/graphs.json.

Uruchomienie (z katalogu głównego repozytorium): .venv/Scripts/python -I analysis/tools/extract_lines.py
"""
import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLES = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')
OUT = os.path.join(ROOT, 'work', 'out')

STORY_NODES = {'FFG.D3.DTNodes.StoryMessageNode', 'FFG.D3.DTNodes.MultipleChoiceStoryMessageNode',
               'FFG.D3.DTNodes.StoryVirtueChoiceNode'}


def load_manifest():
    m = json.load(open(os.path.join(BUNDLES, 'manifest.dat'), encoding='utf-8'))
    return {b['filename']: b for b in m['bundleInfos']}


def load_pl_terms(manifest):
    """Klucz -> {text, en, sources}. Źródła: CSV z loc/pl + wszystkie I2 LanguageSourceAsset."""
    terms = {}

    def add(key, text, src, en=None):
        e = terms.setdefault(key, {'text': text, 'en': en, 'sources': []})
        if text and not e['text']:
            e['text'] = text
        if en and not e['en']:
            e['en'] = en
        e['sources'].append(src)

    for fn, b in manifest.items():
        name = b['name']
        if not (name == 'loc/pl' or name == 'loc/en' or name.startswith('qloc/') or name == 'localization'):
            continue
        env = UnityPy.load(os.path.join(BUNDLES, fn))
        for o in env.objects:
            if o.type.name == 'TextAsset' and name in ('loc/pl', 'loc/en'):
                d = o.read()
                rows = list(csv.reader(io.StringIO(d.m_Script)))
                for r in rows[1:]:
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
                langs = [l['Code'] for l in src['mLanguages']]
                if 'pl' not in langs:
                    continue
                pi, ei = langs.index('pl'), langs.index('en') if 'en' in langs else None
                for tm in src['mTerms']:
                    L = tm['Languages']
                    add(tm['Term'], L[pi] if pi < len(L) else '', 'i2:' + t['m_Name'],
                        L[ei] if ei is not None and ei < len(L) else None)
    return terms


def gameobject_name(o):
    try:
        return o.read().m_GameObject.read().m_Name
    except Exception:
        return ''


def iter_graphs(manifest, scan):
    """Zwraca (bundle_name, container, owner_name, graph_json) dla wszystkich grafów NodeCanvas."""
    for path, v in scan.items():
        if not v.get('graphs'):
            continue
        fn = os.path.basename(path)
        b = manifest.get(fn, {})
        bname = b.get('name') or v.get('bundle_name') or fn
        container = (b.get('assets') or [''])[0]
        env = UnityPy.load(os.path.join(BUNDLES, fn))
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            t = o.read_typetree()
            g = t.get('_serializedGraph')
            owner = t.get('m_Name')
            if not g:
                g = t.get('boundGraphSerialization')
                if not g:
                    continue
                owner = gameobject_name(o)
            yield bname, container, owner, g


def speaker_info(node):
    s = node.get('_settings') or {}
    speakers, present = [], []
    for i in range(1, 5):
        c = s.get('Character_%d' % i) or {}
        cid = c.get('_characterId')
        if cid:
            present.append(cid)
            if c.get('IsSpeaking'):
                speakers.append(cid)
    return speakers, present, s.get('BackgroundType')


def iter_strings(v, path='', ptype=''):
    """(ścieżka, wartość, $type najbliższego obiektu-przodka) dla każdego stringa."""
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
    if ct == 'CheckHeroVirtue':
        return 'VIRTUE'
    if ct == 'CheckProductOwned':
        return 'PRODUCT'
    if ct == 'CheckCurrentLanguage':
        return 'LANGUAGE'
    return None


def edge_labels(node, n_children):
    """Etykiety kolejnych wyjść węzła warunkowego (ConditionNode: tak/nie, MultipleConditionNode: i-ty warunek)."""
    t = node.get('$type', '')
    if t.endswith('.ConditionNode'):
        lab = condition_label(node.get('_condition'))
        return [lab, 'NOT ' + lab] if lab else [None, None]
    if t.endswith('.MultipleConditionNode'):
        return [condition_label(c) for c in node.get('conditions', [])] + [None] * n_children
    return [None] * n_children


def order_nodes(g):
    """DFS od węzła głównego (pierwszy w liście); zwraca {id: (seq, [warunki z bezpośrednich gałęzi])}."""
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
    order = {}
    seq = 0
    for root in [n.get('$id') for n in nodes if n.get('$id')]:
        stack = [root]
        while stack:
            nid = stack.pop()
            if nid in order:
                continue
            order[nid] = (seq, sorted(conds.get(nid, ())))
            seq += 1
            stack.extend(reversed(out_edges.get(nid, [])))
    return order


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


def main():
    manifest = load_manifest()
    scan = json.load(open(os.path.join(OUT, 'class_scan.json'), encoding='utf-8'))
    terms = load_pl_terms(manifest)
    json.dump(terms, open(os.path.join(OUT, 'pl_terms.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('PL terms:', len(terms), 'with PL text:', sum(1 for t in terms.values() if t['text']), file=sys.stderr)

    seen = {}
    graphs = []
    lines = open(os.path.join(OUT, 'lines.jsonl'), 'w', encoding='utf-8')
    nlines = 0
    for bname, container, owner, gjson in iter_graphs(manifest, scan):
        h = hashlib.sha1(gjson.encode('utf-8')).hexdigest()[:12]
        if h in seen:
            seen[h]['instances'] += 1
            continue
        g = json.loads(gjson)
        meta = {'graph': h, 'bundle': bname, 'container': container, 'owner': owner, 'instances': 1,
                'kind': source_kind(bname), 'nodes': len(g.get('nodes', []))}
        seen[h] = meta
        graphs.append(meta)
        order = order_nodes(g)
        for n in g.get('nodes', []):
            nid = n.get('$id')
            ntype = n.get('$type', '')
            seq, conds = order.get(nid, (None, []))
            speakers, present, bg = speaker_info(n) if ntype in STORY_NODES else ([], [], None)
            msg = n.get('_message') or {}
            args = [a.get('ArgType') for a in msg.get('_arguments', []) or []]
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
                    role = 'other:%s:%s' % (ptype.split('.')[-1][:40], re.sub(r'\[\d+\]', '[]', path)[-40:])
                rec = {'graph': h, 'bundle': bname, 'owner': owner, 'kind': meta['kind'], 'node': nid,
                       'node_type': ntype.split('.')[-1], 'node_name': n.get('_name'), 'seq': seq,
                       'conds': conds, 'role': role, 'key': val, 'speakers': speakers,
                       'present': present, 'background': bg, 'arg_types': args if role == 'message' else []}
                lines.write(json.dumps(rec, ensure_ascii=False) + '\n')
                nlines += 1
    lines.close()
    json.dump(graphs, open(os.path.join(OUT, 'graphs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('unique graphs:', len(graphs), 'line refs:', nlines, file=sys.stderr)


if __name__ == '__main__':
    main()
