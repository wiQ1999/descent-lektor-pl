"""Dashboard stanu dialogów: python -I -m lektor dashboard [--serve [PORT]] [--out PLIK]

Czyta bazy kwestii wszystkich wydań (analysis/work/lektor/<wydanie>.sqlite) i stan audio (manifest.json,
inherited.json, dzienniki podejść) i składa jedną stronę HTML: każda misja osobno, reszta treści w kategoriach.

Miarą jest kwestia (klucz okna) z bazy odniesienia, czyli wydania o najszerszej bazie. Kwestia jest w wydaniu:
  gotowa        gdy wszystkie jej fragmenty są w manifest.json (pliki końcowe po `finalize`),
  wygenerowana  gdy wszystkie mają podejście albo są przejęte, ale czekają na ocenę i `finalize`.
Wartości luk {n} (nazwy wrogów, łup, cele) liczymy osobno, po wartości. Wersja elementu to wydanie z największym
pokryciem, a przy remisie starsze (nowsze tylko przejęło jego audio). Strona ma tytuły wydarzeń z gry, więc leży tylko w analysis/work/ (D75).
Bez GPU i sieci; `--serve` liczy stan przy każdym odświeżeniu strony.
"""
import html
import json
import os
import pathlib
import re
import sqlite3
import time

from . import paths

OUT = os.path.join(paths.WORK, 'dashboard', 'index.html')
PORT = 47811
REFRESH_S = 60
VALUES = '@values'      # element z wartościami luk (poza kwestiami)
READY, MADE = 0, 1
SECTIONS = (('a1_main', 'Akt 1: misje główne'), ('a1_side', 'Akt 1: misje poboczne'),
            ('a2_main', 'Akt 2: misje główne'), ('a2_side', 'Akt 2: wątki poboczne'),
            ('other', 'Pozostałe treści według kategorii'))
CATEGORIES = ('Sceny fabularne', 'Wydarzenia aktu 1', 'Wydarzenia aktu 2', 'Podróże', 'Miasto i mapa', 'Wrogowie',
              'Przedmioty i zdolności', 'System i łup', 'Inne')
GROUP_NAMES = {'welcome_home': 'Scena po Q1', 'pre_q678': 'Scena przed Q6–Q8', 'pre_q9': 'Scena przed Q9',
               'cutscene_01': 'Przerywnik 1', 'travel_act1': 'Podróże aktu 1', 'travel_act2': 'Podróże aktu 2',
               'city': 'Wydarzenia w mieście, akt 1', 'city_act2': 'Wydarzenia w mieście, akt 2',
               'town': 'Lokacje mapy, akt 1', 'town_act2': 'Lokacje mapy, akt 2', 'map': 'Opisy celów na mapie',
               'enemies': 'Wrogowie', 'gear': 'Przedmioty i zdolności', 'a2_terrain': 'Teren aktu 2',
               'events': 'Wydarzenia fabularne', 'system': 'Komunikaty systemowe',
               VALUES: 'Wartości luk (nazwy wrogów, łup, cele)'}
STEPS = (('story_q1', 'wstęp i zakończenie'), ('scene_q1', 'scena'))


def element(group):
    """(sekcja, id elementu, etykieta, kolejność). Misja to jeden element, pozostałe grupy trafiają do kategorii."""
    if group in ('story_q1', 'scene_q1'):
        return 'a1_main', 'a1_q1', 'Q1', 1
    m = re.fullmatch(r'(?:a1_)?q(\d+)', group)
    if m:
        return 'a1_main', 'a1_q' + m.group(1), 'Q' + m.group(1), int(m.group(1))
    m = re.fullmatch(r'a1_sq(\d+)', group)
    if m:
        return 'a1_side', group, 'SQ' + m.group(1), int(m.group(1))
    m = re.fullmatch(r'a2_q(\d+)', group)
    if m:
        return 'a2_main', group, 'Q%s%s' % (m.group(1), ' (wstęp)' if m.group(1) == '0' else ''), int(m.group(1))
    m = re.fullmatch(r'a2_ss(\d+)', group)
    if m:
        return 'a2_side', group, 'SS' + m.group(1), int(m.group(1))
    return 'other', category(group), category(group), CATEGORIES.index(category(group))


def category(group):
    if group in ('welcome_home', 'cutscene_01') or group.startswith(('pre_', 'a1_scene_')):
        return 'Sceny fabularne'
    if group.startswith(('event_', 'a1_event_')) or group == 'events':
        return 'Wydarzenia aktu 1'
    if group.startswith('a2_se'):
        return 'Wydarzenia aktu 2'
    if group.startswith('travel_'):
        return 'Podróże'
    if group.startswith(('city', 'town')) or group == 'map':
        return 'Miasto i mapa'
    if group == 'enemies':
        return 'Wrogowie'
    if group in ('gear', 'a2_terrain'):
        return 'Przedmioty i zdolności'
    return 'System i łup' if group in ('system', VALUES) else 'Inne'


def title_groups(key):
    """Grupy, których tytułem może być klucz nazwy celu z mapy (E2A_…_NAME, EC1_…, A2SE01_…)."""
    m = re.match(r'(A2)?(SE|SS|EC|E)(\d+)([A-Z]?)_', key)
    if not m:
        return ()
    act2, kind, num, letter = m.group(1), m.group(2).lower(), m.group(3), m.group(4).lower()
    if act2:
        return ('a2_%s%s' % (kind, num),)
    return ('event_%s%s%s' % (kind, num, letter), 'a1_event_%s%s' % (num, letter))


def group_label(group, titles):
    if group in GROUP_NAMES:
        return GROUP_NAMES[group]
    m = re.fullmatch(r'(?:a1_)?event_(?:e(?=\d))?(\w+)', group) or re.fullmatch(r'a2_(se\d+)', group)
    code = m.group(1).upper() if m else group
    return '%s: %s' % (code, titles[group]) if group in titles else code


def inputs(release):
    """Pliki, z których liczymy stan wydania."""
    audio = os.path.join(paths.WORK, 'audio', release)
    names = ('manifest.json', 'inherited.json', 'takes.jsonl', 'takes_eleven.jsonl', 'run_state.json')
    return os.path.join(paths.OUT, release + '.sqlite'), {n: os.path.join(audio, n) for n in names}


def signature():
    """Zmienia się, gdy zmieni się którykolwiek plik wejściowy (pamięć podręczna trybu --serve)."""
    out = []
    for release in paths.RELEASES:
        db_path, files = inputs(release)
        for p in (db_path, *files.values()):
            if os.path.exists(p):
                st = os.stat(p)
                out.append((p, st.st_mtime_ns, st.st_size))
    return tuple(out)


def read_json(path, default):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):       # brak pliku albo zapis w toku: następne odświeżenie go przeczyta
        return default


def take_fragments(path):
    out = set()
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                try:
                    out.add(json.loads(line)['fragment'])
                except (ValueError, KeyError):
                    continue        # urwany ostatni wiersz po przerwaniu procesu
    return out


def load(release):
    """Stan wydania albo None, gdy nie ma bazy: kwestie z fragmentami, wartości luk, fragmenty gotowe i wygenerowane."""
    db_path, files = inputs(release)
    if not os.path.exists(db_path):
        return None
    con = sqlite3.connect(pathlib.Path(db_path).as_uri() + '?mode=ro', uri=True)
    try:
        lines = {k: (g, set()) for k, g in con.execute('SELECT key, grp FROM lines WHERE tts = 1')}
        for k, f in con.execute('SELECT key, fragment FROM segments WHERE fragment IS NOT NULL'):
            if k in lines:
                lines[k][1].add(f)
        values = {}
        for v, f in con.execute('SELECT value, fragment FROM slot_values WHERE fragment IS NOT NULL'):
            values.setdefault(v, set()).add(f)
        titles = {}
        for k, text in con.execute("SELECT key, text_raw FROM lines WHERE grp = 'map' AND key LIKE '%\\_NAME' ESCAPE '\\'"):
            for g in title_groups(k):
                titles.setdefault(g, text)
        meta = dict(con.execute("SELECT k, v FROM meta WHERE k IN ('built_at')"))
    finally:
        con.close()
    final = set(read_json(files['manifest.json'], {}).get('fragments', {}))
    made = final | set(read_json(files['inherited.json'], {}))
    for name in ('takes.jsonl', 'takes_eleven.jsonl'):
        made |= take_fragments(files[name])
    logs = [os.path.getmtime(files[n]) for n in ('takes.jsonl', 'takes_eleven.jsonl') if os.path.exists(files[n])]
    return {'id': release, 'lines': {k: v for k, v in lines.items() if v[1]}, 'values': values, 'titles': titles,
            'final': final, 'made': made, 'built_at': json.loads(meta['built_at']) if 'built_at' in meta else None,
            'state': read_json(files['run_state.json'], None), 'last_take': max(logs) if logs else None}


def status(need, rel):
    """READY, MADE albo None dla zbioru fragmentów w wydaniu."""
    return READY if need <= rel['final'] else MADE if need <= rel['made'] else None


def collect():
    """Dane strony: wydania, sekcje z elementami i grupami, pokrycie gry w dowolnym wydaniu."""
    rels = [r for r in map(load, paths.RELEASES) if r]
    if not rels:
        return {'releases': [], 'sections': [], 'reference': None, 'total': 0, 'any': 0}
    ref = max(rels, key=lambda r: (len(r['lines']), paths.RELEASES.index(r['id'])))
    ids = [r['id'] for r in rels]
    groups, covered = {}, 0

    def count(group, per_release):
        g = groups.setdefault(group, {'total': 0, 'rel': {i: [0, 0] for i in ids}})
        g['total'] += 1
        for rid, st in per_release.items():
            if st is not None:
                g['rel'][rid][st] += 1
        return READY in per_release.values()

    for key, (group, _) in ref['lines'].items():
        covered += count(group, {r['id']: status(r['lines'][key][1], r) for r in rels if key in r['lines']})
    for value in ref['values']:
        covered += count(VALUES, {r['id']: status(r['values'][value], r) for r in rels if value in r['values']})

    elements = {}
    for group, g in groups.items():
        section, eid, label, order = element(group)
        e = elements.setdefault((section, eid), {'label': label, 'order': order, 'total': 0,
                                                 'rel': {i: [0, 0] for i in ids}, 'groups': []})
        e['total'] += g['total']
        for i in ids:
            e['rel'][i] = [a + b for a, b in zip(e['rel'][i], g['rel'][i])]
        e['groups'].append({'label': dict(STEPS).get(group) or group_label(group, ref['titles']), 'id': group, **g})
    sections = []
    for sid, title in SECTIONS:
        rows = sorted((e for (s, _), e in elements.items() if s == sid), key=lambda e: e['order'])
        for e in rows:
            e['groups'].sort(key=lambda g: g['label'])
            if len(e['groups']) < 2:
                e['groups'] = []
        if rows:
            sections.append({'title': title, 'rows': rows})
    total = sum(g['total'] for g in groups.values())
    releases = [{'id': r['id'], 'built_at': r['built_at'], 'state': r['state'], 'last_take': r['last_take'],
                 'ready': sum(g['rel'][r['id']][READY] for g in groups.values()),
                 'made': sum(g['rel'][r['id']][MADE] for g in groups.values())} for r in rels]
    return {'releases': releases, 'sections': sections, 'reference': ref['id'], 'total': total, 'any': covered}


def best(row):
    """(wydanie, gotowe, wygenerowane) z największym pokryciem; None, gdy nic nie powstało. Przy remisie starsze:
    w nim dialogi powstały, a nowsze wydania tylko je przejęły."""
    rid, (ready, made) = max(row['rel'].items(), key=lambda x: (x[1][READY], x[1][MADE]))
    return (rid, ready, made) if ready or made else None


def pct(part, total):
    """Procent jako tekst: 100 tylko przy komplecie, a ślad pracy nigdy nie wygląda jak zero."""
    if not total or not part:
        return '0%'
    p = 100 * part / total
    return '100%' if part == total else '<1%' if p < 1 else '%d%%' % min(99, round(p))


def num(n):
    return '{:,}'.format(n).replace(',', ' ')


def meter(ready, made, total, label=''):
    w = lambda n: '%.2f' % (100 * n / total if total else 0)
    tip = '%s gotowe: %s z %s%s' % (label, num(ready), num(total), ', wygenerowane bez finalizacji: %s' % num(made) if made else '')
    return ('<span class="meter" role="img" aria-label="{t}" title="{t}"><i class="ok" style="width:{a}%"></i>'
            '<i class="mid" style="width:{b}%"></i></span>').format(t=html.escape(tip.strip()), a=w(ready), b=w(made))


def row_html(row, ids, cls='', toggle=''):
    b = best(row)
    cells = ''.join(
        '<td class="rel" title="%s: gotowe %s, wygenerowane %s z %s"><span class="%s">%s</span>%s</td>' % (
            i.upper(), num(r), num(m), num(row['total']), 'full' if r == row['total'] else 'none' if not r else '',
            pct(r, row['total']), meter(r, m, row['total'], i.upper()))
        for i, (r, m) in row['rel'].items())
    if not b:
        version, done = '<span class="tag off">brak</span>', '<td class="done"><b>0%</b></td>'
    else:
        version = '<span class="tag%s">%s</span>' % ('' if b[1] else ' wip', b[0].upper() if b[1] else b[0].upper() + ' w toku')
        done = '<td class="done"><b>%s</b>%s</td>' % (pct(b[1], row['total']), meter(b[1], b[2], row['total'], b[0].upper()))
    return '<tr class="%s"%s><th scope="row">%s</th><td class="n">%s</td><td>%s</td>%s%s</tr>' % (
        cls, toggle, html.escape(row['label']), num(row['total']), version, done, cells)


def when(ts):
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(ts)) if ts else None


def tile(r, total):
    from .bundle import SCOPES
    facts = ['gotowe %s z %s kwestii' % (num(r['ready']), num(total))]
    if r['made']:
        facts.append('%s wygenerowanych czeka na finalizację' % num(r['made']))
    if r['state']:
        facts.append('krok: %s (od %s)' % (r['state'].get('step'), r['state'].get('since')))
    if r['last_take']:
        facts.append('ostatnie podejście: %s' % when(r['last_take']))
    if r['built_at']:
        facts.append('baza z %s' % r['built_at'].replace('T', ' ')[:16])
    return ('<div class="tile"><div class="k">%s</div><div class="v">%s</div>%s<div class="scope">%s</div>'
            '<ul>%s</ul></div>') % (
        r['id'].upper(), pct(r['ready'], total), meter(r['ready'], r['made'], total, r['id'].upper()),
        html.escape(SCOPES.get(r['id'], '')), ''.join('<li>%s</li>' % html.escape(f) for f in facts))


def render(data, refresh=REFRESH_S):
    ids = [r['id'] for r in data['releases']]
    if not ids:
        body = '<p>Brak baz kwestii w <code>%s</code>. Zbuduj bazę: <code>python -I -m lektor build</code>.</p>' % html.escape(paths.OUT)
        return PAGE.replace('{{BODY}}', body).replace('{{REFRESH}}', str(refresh))
    head = '<tr><th scope="col">Element</th><th scope="col" class="n">Kwestie</th><th scope="col">Wersja</th>' \
           '<th scope="col">Wykonanie</th>%s</tr>' % ''.join('<th scope="col" class="rel">%s</th>' % i.upper() for i in ids)
    parts, n = [], 0
    for s in data['sections']:
        total = {'label': 'Razem', 'total': sum(r['total'] for r in s['rows']),
                 'rel': {i: [sum(r['rel'][i][k] for r in s['rows']) for k in (READY, MADE)] for i in ids}}
        rows = []
        for r in s['rows']:
            n += 1
            kids = ''.join(row_html(g, ids, 'kid k%d' % n) for g in r['groups'])
            rows.append(row_html(r, ids, 'top has' if kids else 'top', ' data-k="k%d"' % n if kids else '') + kids)
        parts.append('<section><h2>%s</h2><div class="scroll"><table><thead>%s</thead><tbody>%s</tbody>'
                     '<tfoot>%s</tfoot></table></div></section>' % (
                         html.escape(s['title']), head, ''.join(rows), row_html(total, ids, 'sum')))
    body = ('<div class="hero"><div class="v">%s</div><div>kwestii gry ma gotowe audio w co najmniej jednym wydaniu '
            '(%s z %s)</div></div><div class="tiles">%s</div>'
            '<p class="legend"><span class="meter"><i class="ok" style="width:100%%"></i></span> gotowe (po <code>finalize</code>) '
            '<span class="meter"><i class="mid" style="width:100%%"></i></span> wygenerowane, czeka na ocenę i finalizację '
            '<span class="meter"></span> brak</p>%s'
            '<p class="foot">Stan z %s. Baza odniesienia: %s (%s kwestii i wartości luk). Procent to udział kwestii '
            'z tej bazy, które mają wszystkie fragmenty w wydaniu. Wersja elementu to wydanie z największym pokryciem, '
            'przy remisie starsze (nowsze tylko przejęło jego audio). Wiersz z ▸ rozwija się po kliknięciu.</p>') % (
        pct(data['any'], data['total']), num(data['any']), num(data['total']),
        ''.join(tile(r, data['total']) for r in data['releases']), ''.join(parts),
        time.strftime('%Y-%m-%d %H:%M:%S'), data['reference'].upper(), num(data['total']))
    return PAGE.replace('{{BODY}}', body).replace('{{REFRESH}}', str(refresh))


def write(out=None):
    out = out or OUT
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out + '.tmp', 'w', encoding='utf-8') as fh:
        fh.write(render(collect()))
    os.replace(out + '.tmp', out)
    return out


def serve(port=PORT):
    """Strona pod http://127.0.0.1:PORT/, liczona od nowa, gdy zmienił się któryś plik wejściowy."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    cache = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split('?')[0] != '/':
                self.send_error(404)
                return
            sig = signature()
            if cache.get('sig') != sig:
                cache.update(sig=sig, page=render(collect()).encode('utf-8'))
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(cache['page'])))
            self.end_headers()
            self.wfile.write(cache['page'])

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print('Dashboard: http://127.0.0.1:%d/ (Ctrl+C kończy)' % port, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


PAGE = """<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="{{REFRESH}}"><title>Stan dialogów</title><style>
:root{--bg:#fcfcfb;--card:#fff;--fg:#0b0b0b;--fg2:#52514e;--muted:#898781;--line:#e1e0d9;--ok:#2a78d6;--track:#ebeae5}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--card:#222221;--fg:#f0efec;--fg2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--ok:#3987e5;--track:#30302e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}h1{font-size:22px;margin:8px 0 16px}h2{font-size:16px;margin:28px 0 8px}
.hero{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;color:var(--fg2)}.hero .v{font-size:44px;font-weight:650;color:var(--fg);line-height:1}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.tile .k{color:var(--fg2);font-weight:600}.tile .v{font-size:28px;font-weight:650;line-height:1.2}
.tile .meter{width:100%;margin:6px 0}.tile .scope{color:var(--fg2);font-size:12px}
.tile ul{margin:6px 0 0;padding:0;list-style:none;color:var(--muted);font-size:12px}
.meter{display:inline-flex;gap:2px;width:120px;height:8px;border-radius:4px;background:var(--track);overflow:hidden;vertical-align:middle}
.meter i{display:block;height:100%;flex:none}.meter i[style="width:0.00%"]{display:none}.meter .ok{background:var(--ok)}
.meter .mid{background:repeating-linear-gradient(45deg,var(--ok) 0 2px,transparent 2px 5px)}
.legend{color:var(--fg2);font-size:12px;display:flex;gap:6px 8px;align-items:center;flex-wrap:wrap}.legend .meter{width:28px;margin-left:10px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:720px}th,td{padding:6px 10px;text-align:left;border-top:1px solid var(--line);white-space:nowrap}
thead th{border-top:0;color:var(--muted);font-weight:500;font-size:12px}tbody th{font-weight:500}
.n,.rel{text-align:right;font-variant-numeric:tabular-nums}.done{font-variant-numeric:tabular-nums}
.done b{display:inline-block;width:44px;font-weight:600}.done .meter{width:140px}
.rel span:first-child{display:block}.rel .meter{width:56px;height:4px}.rel .none{color:var(--muted)}.rel .full{font-weight:600}
.tag{display:inline-block;padding:1px 8px;border:1px solid var(--line);border-radius:10px;font-size:12px;font-weight:600}
.tag.off{color:var(--muted);font-weight:400}.tag.wip{font-weight:400}
tr.has{cursor:pointer}tr.has th::before{content:"▸ ";color:var(--muted)}tr.has.open th::before{content:"▾ "}
tr.kid{display:none;color:var(--fg2);font-size:13px}tr.kid.show{display:table-row}tr.kid th{padding-left:28px;font-weight:400;white-space:normal}
tfoot th,tfoot td{font-weight:600;border-top:2px solid var(--line)}
.foot{color:var(--muted);font-size:12px;margin-top:24px}code{font-size:12px}
</style></head><body><main><h1>Stan dialogów: Lektor PL</h1>
{{BODY}}
</main><script>
const KEY='lektor-dashboard-open';let open=[];try{open=JSON.parse(sessionStorage.getItem(KEY)||'[]')}catch(e){}
function set(tr,on){tr.classList.toggle('open',on);document.querySelectorAll('tr.'+tr.dataset.k).forEach(k=>k.classList.toggle('show',on))}
document.querySelectorAll('tr.has').forEach(tr=>{if(open.includes(tr.dataset.k))set(tr,true);
 tr.addEventListener('click',()=>{const on=!tr.classList.contains('open');set(tr,on);
  open=on?open.concat(tr.dataset.k):open.filter(k=>k!==tr.dataset.k);try{sessionStorage.setItem(KEY,JSON.stringify(open))}catch(e){}})});
</script></body></html>"""
