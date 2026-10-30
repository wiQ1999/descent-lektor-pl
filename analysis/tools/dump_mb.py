"""Zrzuca typetree wybranych MonoBehaviour z bundla (skrócone stringi) do pliku JSON-lines."""
import sys, json, UnityPy
path, out, limit = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5
name_filter = sys.argv[4] if len(sys.argv) > 4 else ''

def trim(v, n=160):
    if isinstance(v, str): return v[:n]
    if isinstance(v, list): return [trim(x, n) for x in v[:8]] + (['...+%d' % (len(v)-8)] if len(v) > 8 else [])
    if isinstance(v, dict): return {k: trim(x, n) for k, x in v.items()}
    return v

env = UnityPy.load(path)
scripts = {}
with open(out, 'w', encoding='utf-8') as f:
    n = 0
    for o in env.objects:
        if o.type.name != 'MonoBehaviour': continue
        try:
            t = o.read_typetree()
        except Exception as e:
            f.write('ERR %s\n' % e); continue
        try:
            sc = o.read().m_Script.read().m_ClassName
        except Exception:
            sc = '?'
        scripts[sc] = scripts.get(sc, 0) + 1
        if name_filter and name_filter not in (t.get('m_Name') or '') and name_filter != sc: continue
        if n < limit:
            f.write(json.dumps({'script': sc, 'pathid': o.path_id, 'tree': trim(t)}, ensure_ascii=False) + '\n'); n += 1
    f.write('SCRIPTS ' + json.dumps(scripts) + '\n')
