"""Dla każdego bundla: liczba MonoBehaviour per klasa skryptu + liczba grafów NodeCanvas (serialized/bound) + TextAssety."""
import sys, os, json, collections, UnityPy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scan(path):
    env = UnityPy.load(path)
    cls = collections.Counter(); graphs = collections.Counter(); texts = []
    script_cache = {}
    for o in env.objects:
        tn = o.type.name
        if tn == 'TextAsset':
            d = o.read(); texts.append((d.m_Name, len(d.m_Script)))
        if tn != 'MonoBehaviour': continue
        try:
            t = o.read_typetree()
        except Exception:
            cls['<no typetree>'] += 1; continue
        sp = t.get('m_Script', {})
        k = (sp.get('m_FileID'), sp.get('m_PathID'))
        if k not in script_cache:
            try: script_cache[k] = o.read().m_Script.read().m_ClassName
            except Exception: script_cache[k] = '?'
        c = script_cache[k]; cls[c] += 1
        if t.get('_serializedGraph'): graphs['serialized'] += 1
        if t.get('boundGraphSerialization'): graphs['bound'] += 1
    return {'classes': dict(cls), 'graphs': dict(graphs), 'texts': texts}

idx = json.load(open(sys.argv[1], encoding='utf-8'))
out = {}
for i, e in enumerate(idx):
    if 'StreamingAssets' not in e['path'] and '--all' not in sys.argv: continue
    try:
        out[e['path']] = dict(scan(os.path.join(ROOT, e['path'])), bundle_name=e['bundle_name'])
    except Exception as ex:
        out[e['path']] = {'error': str(ex), 'bundle_name': e['bundle_name']}
    print(i, end=' ', file=sys.stderr, flush=True)
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
