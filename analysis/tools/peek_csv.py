import sys, UnityPy, csv, io
env = UnityPy.load(sys.argv[1])
for o in env.objects:
    if o.type.name != 'TextAsset': continue
    d = o.read()
    s = d.m_Script if isinstance(d.m_Script, str) else bytes(d.m_Script).decode('utf-8', 'replace')
    rows = list(csv.reader(io.StringIO(s)))
    print('==', d.m_Name, 'rows', len(rows), 'header', rows[0][:10])
    for r in rows[1:4]:
        print('   ', [x[:90] for x in r])
