"""Indeksuje bundle (StreamingAssets + cache LocalLow): nazwa AssetBundle, kontenery, typy obiektów."""
import sys, os, json, collections, UnityPy
from UnityPy.enums import ClassIDType

def index(path):
    env = UnityPy.load(path)
    info = {'path': path, 'size': os.path.getsize(path), 'bundle_name': None, 'containers': [], 'types': {}}
    c = collections.Counter()
    for o in env.objects:
        c[o.type.name] += 1
        if o.type == ClassIDType.AssetBundle:
            d = o.read()
            info['bundle_name'] = d.m_AssetBundleName if hasattr(d, 'm_AssetBundleName') else getattr(d, 'm_Name', None)
            info['containers'] = sorted({k for k, _ in d.m_Container})
    info['types'] = dict(c)
    return info

roots = sys.argv[2:]
res = []
for r in roots:
    for dp, dn, fn in os.walk(r):
        for f in fn:
            if f in ('__info', 'manifest.dat'): continue
            p = os.path.join(dp, f)
            try:
                res.append(index(p))
            except Exception as e:
                res.append({'path': p, 'error': str(e)})
            print(len(res), end='\r', file=sys.stderr)
json.dump(res, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('done', len(res), file=sys.stderr)
