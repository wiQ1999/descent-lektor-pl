"""Przegląd wszystkich grafów NodeCanvas: typy grafów, typy węzłów, typy akcji/warunków + po 1 przykładzie."""
import sys, os, json, collections, UnityPy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scan = json.load(open(os.path.join(ROOT, 'work', 'out', 'class_scan.json'), encoding='utf-8'))
paths = [p for p, v in scan.items() if v.get('graphs')]
gtypes = collections.Counter(); ntypes = collections.Counter(); tasks = collections.Counter()
examples = {}
def walk_tasks(v):
    if isinstance(v, dict):
        t = v.get('$type')
        if t: yield t, v
        for x in v.values(): yield from walk_tasks(x)
    elif isinstance(v, list):
        for x in v: yield from walk_tasks(x)
for p in paths:
    env = UnityPy.load(os.path.join(ROOT, p))
    for o in env.objects:
        if o.type.name != 'MonoBehaviour': continue
        t = o.read_typetree()
        g = t.get('_serializedGraph') or t.get('boundGraphSerialization')
        if not g: continue
        j = json.loads(g)
        gtypes[j.get('type')] += 1
        for n in j.get('nodes', []):
            nt = n.get('$type'); ntypes[nt] += 1
            examples.setdefault(nt, n)
            for tt, tv in walk_tasks({k: v for k, v in n.items() if k != '$type'}):
                tasks[tt] += 1; examples.setdefault(tt, tv)
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write('GRAPH TYPES %s\n' % gtypes.most_common())
    f.write('NODE TYPES\n'); [f.write('  %6d %s\n' % (n, k)) for k, n in ntypes.most_common()]
    f.write('TASK TYPES\n'); [f.write('  %6d %s\n' % (n, k)) for k, n in tasks.most_common()]
    f.write('EXAMPLES\n')
    for k, v in examples.items():
        f.write('## %s\n%s\n' % (k, json.dumps(v, ensure_ascii=False)[:1500]))
