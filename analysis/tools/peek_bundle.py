import sys, UnityPy, collections
for path in sys.argv[1:]:
    env = UnityPy.load(path)
    print('==', path.split('/')[-1], 'files:', list(env.files.keys())[:3])
    c = collections.Counter(o.type.name for o in env.objects)
    print('  types:', c.most_common(12))
    for o in env.objects:
        if o.type.name in ('TextAsset', 'MonoBehaviour', 'MonoScript'):
            try:
                if o.type.name == 'TextAsset':
                    d = o.read()
                    s = d.m_Script if isinstance(d.m_Script, str) else bytes(d.m_Script).decode('utf-8', 'replace')
                    print('  TextAsset', d.m_Name, len(s))
                elif o.type.name == 'MonoScript':
                    d = o.read(); print('  MonoScript', d.m_ClassName, d.m_Namespace)
                else:
                    t = o.read_typetree()
                    print('  MB', t.get('m_Name'), list(t.keys())[:15])
            except Exception as e:
                print('  ERR', o.type.name, e)
