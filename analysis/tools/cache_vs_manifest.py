import json, sys, collections, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open(os.path.join(ROOT, 'work', 'out', 'bundle_index.json'), encoding='utf-8'))
man = json.load(open(os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles', 'manifest.dat'), encoding='utf-8'))
byfile = {b['filename']: b for b in man['bundleInfos']}
errs = [i for i in idx if 'error' in i]
print('errors', len(errs), [e['error'][:80] for e in errs[:3]])
sa = [i for i in idx if 'StreamingAssets' in i['path']]
cache = [i for i in idx if 'unity_cache' in i['path']]
print('SA', len(sa), 'cache', len(cache))
extra = []
for c in cache:
    fn = os.path.normpath(c['path']).split(os.sep)[-3]
    if fn not in byfile: extra.append((fn, c))
print('cache not in manifest:', len(extra))
saname = {i.get('bundle_name') for i in sa}
print('extra bundle names also in SA:', sum(1 for fn, c in extra if c.get('bundle_name') in saname))
for fn, c in extra:
    print(fn[:8], c.get('bundle_name'), c.get('size'), len(c.get('containers', [])), (c.get('containers') or [''])[0][:90])
