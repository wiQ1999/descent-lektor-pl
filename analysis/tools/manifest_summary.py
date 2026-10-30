import json, sys, collections
m = json.load(open(sys.argv[1], encoding='utf-8'))
print('keys:', list(m.keys()))
bi = m['bundleInfos']
print('bundles:', len(bi), 'published:', sum(b.get('published') for b in bi))
groups = collections.Counter(b['name'].split('/')[0] for b in bi)
print(groups.most_common())
for b in bi:
    n = b['name']
    if any(k in n.lower() for k in ('loc', 'lang', 'text', 'string', 'polish', 'dialog', 'scenario', 'quest', 'story', 'campaign')):
        print(n, b['filename'], b['fileSize'], b.get('published'), len(b['assets']), b['assets'][:3])
