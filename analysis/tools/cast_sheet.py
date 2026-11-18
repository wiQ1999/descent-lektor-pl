"""Zestawienie głosów wydania do odsłuchu (E17, D108): każdy głos aktu 1 z opisem postaci, portretem z gry
(d3/storymessagecharacters) i dwiema próbkami z gotowego audio wydania. Strona i pliki leżą w
analysis/work/compare/<wydanie>_cast/ (poza Git, D76). Na konsolę idą tylko liczby.

    .venv/Scripts/python -I analysis/tools/cast_sheet.py [--release m4] [--acts 1]

Na stronie użytkownik zaznacza głosy do zmiany i kopiuje listę do czatu. Zaznaczenia pamięta przeglądarka.
"""
import argparse
import collections
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from lektor import dashboard, db, direction as D, paths, progress  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
TOOLS = os.path.dirname(os.path.abspath(__file__))

# Portrety okien dialogu: nazwa tekstury w d3/storymessagecharacters -> głos
TEXTURES = {
    'AlysRaine_Dialogue': 'alys', 'Arden_Dialogue': 'arden', 'Astarra_Dialogue': 'astarra',
    'BaronGilliam_Dialogue': 'gilliam', 'BaronGreigory_Dialogue': 'greigory', 'BaronTrevalyn_Dialogue': 'trevalyn',
    'BaronZachareth_Dialogue': 'zachareth', 'BaronessAdelynn_Dialogue': 'adelynn', 'BaronessGrace_Dialogue': 'grace',
    'BaronessMagrit_Dialogue': 'magrit', 'BaronessPryor_Dialogue': 'pryor', 'BloodSister_Dialogue': 'nekrul',
    'Brynn_Dialogue': 'brynn', 'Button_Dialogue': 'button', 'Chance_Dialogue': 'chance',
    'CountReneyr_Dialogue': 'reneyr', 'CountessDucard_Dialogue': 'ducard', 'Delphyndra_Dialogue': 'delphyndra',
    'DragonHybrid_Dialogue': 'xenith', 'Drys_Dialogue': 'drys', 'ElderMok_Dialogue': 'mok',
    'Galaden_Dialogue': 'galaden', 'Greysdon_Dialogue': 'greysdon', 'Herbie_Dialogue': 'herbie',
    'Kathryn_Dialogue': 'kathryn', 'Kehli_Dialogue': 'kehli', 'LTRand_Dialogue': 'ltrand', 'Laurel_Dialogue': 'laurel',
    'Levirax_Dialogue': 'levirax', 'MasterBruli_Dialogue': 'bruli', 'MasterFlint_Dialogue': 'flint',
    'MasterGalgoraz_Dialogue': 'galgoraz', 'Meza_Dialogue': 'meza', 'Morant_Dialogue': 'morant',
    'NaraTheFang_Dialogue': 'nara', 'Navoth_Dialogue': 'navoth', 'OutlawPrince_Dialogue': 'outlaw',
    'Ronan_Dialogue': 'ronan', 'SirBalthain_Dialogue': 'balthain', 'Syrus_Dialogue': 'syrus',
    'Vaerix_Dialogue': 'vaerix', 'Veta_Dialogue': 'veta', 'Vraskhar_Dialogue': 'vraskhar', 'Waiqar_Dialogue': 'waiqar',
}
SHARED_PORTRAIT = {'nv_siostra_krwi': 'nekrul'}     # typ wroga z tym samym portretem co postać z imieniem

HERO = 'Bohater drużyny (postać grywalna). Klon głosu z polskiego dubbingu gry.'
OWN = {     # postacie bez opisu w plikach projektu głosu (D06, D19)
    'narrator': 'Narrator opowieści i głos systemowy: cele, łup, komunikaty, opisy. Klon z polskiego dubbingu, '
                'jedno tempo poza narracją scen (D107).',
    'brynn': HERO, 'syrus': HERO, 'galaden': HERO, 'vaerix': HERO, 'chance': HERO,
    'kehli': HERO + ' Referencja sklejona z trzech klipów (D67).',
    'nekrul': 'Ne’Krul, siostra krwi, złoczyńczyni. Klon z okrzyków z dubbingu (D19).',
    'xenith': 'Xenith, smocza hybryda, złoczyńca. Klon z okrzyków z dubbingu (D19, D68).',
}
SECTIONS = (
    ('narrator', 'Narrator'),
    ('hero', 'Bohaterowie: dubbing'),
    ('clone', 'Złoczyńcy: klon OmniVoice z okrzyków albo monologów z gry'),
    ('eleven', 'Postacie bez dubbingu: ElevenLabs'),
    ('design', 'Postacie bez dubbingu: projekt OmniVoice'),
    ('nv', 'Mówcy bez imienia w oknach narratora: projekt OmniVoice z profilu postaci'),
)
HEROES = ('brynn', 'syrus', 'kehli', 'vaerix', 'chance', 'galaden')


def casting_portraits():
    """Kolumna „Portret i charakter” z tabeli głosów OmniVoice w docs/CASTING.md (postacie E11)."""
    out = {}
    for line in open(os.path.join(ROOT, 'docs', 'CASTING.md'), encoding='utf-8'):
        m = re.match(r'\| `(\w+)` \| `\w+` \| ([^|]+) \| `(?:fe)?male', line)
        if m:
            out.setdefault(m.group(1), m.group(2).strip())
    return out


def descriptions():
    out = {}
    e11 = casting_portraits()
    e14 = json.load(open(os.path.join(TOOLS, 'voice_designs_e14.json'), encoding='utf-8'))
    prod = json.load(open(os.path.join(TOOLS, 'voice_designs_prod.json'), encoding='utf-8'))
    for v, d in list(e14.items()) + list(prod.items()):
        if isinstance(d, dict) and d.get('brief'):
            out[v] = d['brief']
    out.update(e11)
    out.update(OWN)
    return out, prod


def section(voice, refs):
    if voice == 'narrator':
        return 'narrator'
    if voice in HEROES:
        return 'hero'
    if voice.startswith('nv_'):
        return 'nv'
    if D.engine(voice) == 'elevenlabs':
        return 'eleven'
    src = (refs.get(voice) or {}).get('source', '') if isinstance(refs.get(voice), dict) else ''
    return 'design' if src.startswith('projekt') and 'dubbing' not in src else 'clone'


def portraits(out_dir):
    import UnityPy
    from lektor import game as G
    g = G.Game()
    env = UnityPy.load(os.path.join(paths.BUNDLES, g.files['d3/storymessagecharacters']))
    best = {}
    for o in env.objects:
        if o.type.name != 'Texture2D':
            continue
        d = o.read()
        v = TEXTURES.get(d.m_Name)
        if v:
            img = d.image
            if v not in best or img.size[0] * img.size[1] > best[v].size[0] * best[v].size[1]:
                best[v] = img
    os.makedirs(out_dir, exist_ok=True)
    for v, img in best.items():
        img.save(os.path.join(out_dir, v + '.png'))
    return set(best)


def samples(con, acts):
    """Dla każdego głosu do dwóch fragmentów: bez uwag automatu, długość bliska 120 znaków, różne grupy."""
    manifest = json.load(open(os.path.join(paths.AUDIO, 'manifest.json'), encoding='utf-8'))['fragments']
    keep = progress.in_acts(con, acts)
    frag = {r['id']: r for r in con.execute('SELECT id, voice, text, chars FROM fragments')}
    where = {}
    for r in con.execute('SELECT s.fragment, s.key, l.grp FROM segments s JOIN lines l ON l.key = s.key '
                         'WHERE s.fragment IS NOT NULL ORDER BY l.seq'):
        where.setdefault(r['fragment'], (r['key'], r['grp']))
    by_voice = collections.defaultdict(list)
    count = collections.Counter()
    groups = collections.defaultdict(collections.Counter)
    for fid in keep:
        m = manifest.get(fid)
        if not m:
            continue
        v = m['voice']
        count[v] += 1
        key, grp = where.get(fid, ('', 'system'))
        groups[v][grp] += 1
        by_voice[v].append({'fragment': fid, 'file': m['file'], 'problems': m['problems'], 'key': key, 'grp': grp,
                            'text': frag[fid]['text'], 'chars': frag[fid]['chars'], 'seconds': m['seconds']})
    picked = {}
    for v, cands in by_voice.items():
        cands.sort(key=lambda c: (bool(c['problems']), not c['key'], abs(c['chars'] - 120), c['fragment']))
        out = cands[:1]
        rest = [c for c in cands[1:] if c['grp'] != out[0]['grp']] or cands[1:]
        out += rest[:1]
        picked[v] = out
    return picked, count, groups


PAGE = '''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Głosy aktu 1</title>
<style>
:root {{ --bg:#fafaf8; --card:#fff; --fg:#1d1d1b; --muted:#6b6b66; --line:#e4e2dc; --accent:#8a3b12; --mark:#fff1e6; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#18181a; --card:#222225; --fg:#ececea; --muted:#a3a39d; --line:#34343a; --accent:#f0a46c; --mark:#3a2a1f; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; }}
header {{ position:sticky; top:0; z-index:2; background:var(--bg); border-bottom:1px solid var(--line); padding:12px 16px; }}
header h1 {{ margin:0 0 4px; font-size:20px; }}
header p {{ margin:0; color:var(--muted); font-size:13px; }}
.bar {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-top:8px; }}
button {{ font:inherit; padding:6px 12px; border:1px solid var(--line); background:var(--card); color:var(--fg); border-radius:6px; cursor:pointer; }}
button.primary {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
nav a {{ color:var(--accent); font-size:13px; margin-right:10px; }}
main {{ max-width:1100px; margin:0 auto; padding:8px 16px 48px; }}
h2 {{ font-size:17px; margin:28px 0 8px; }}
.card {{ display:grid; grid-template-columns:120px 1fr; gap:14px; background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px; margin:10px 0; }}
.card.flag {{ background:var(--mark); border-color:var(--accent); }}
.pic {{ width:120px; height:120px; border-radius:6px; background:var(--line); display:flex; align-items:center; justify-content:center; color:var(--muted); font-size:12px; text-align:center; overflow:hidden; }}
.pic img {{ width:100%; height:100%; object-fit:cover; object-position:top; }}
.head {{ display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap; }}
.name {{ font-weight:600; font-size:16px; }}
code {{ font-size:12px; color:var(--muted); }}
.meta {{ color:var(--muted); font-size:12px; }}
.desc {{ margin:4px 0 8px; }}
.sample {{ border-top:1px dashed var(--line); padding-top:6px; margin-top:6px; }}
.sample q {{ display:block; font-size:13px; margin-bottom:4px; }}
audio {{ width:100%; max-width:420px; height:32px; }}
label.chg {{ white-space:nowrap; font-size:14px; }}
textarea {{ width:100%; font:inherit; font-size:13px; margin-top:6px; padding:4px 6px; border:1px solid var(--line); border-radius:6px; background:var(--card); color:var(--fg); display:none; }}
.card.flag textarea {{ display:block; }}
#out {{ display:none; width:100%; height:120px; margin-top:8px; }}
@media (max-width:600px) {{ .card {{ grid-template-columns:1fr; }} .pic {{ width:96px; height:96px; }} }}
</style></head><body>
<header><h1>Głosy aktu 1 – wydanie {release}</h1>
<p>{n_voices} głosów, {n_samples} próbek z gotowego audio paczki (akt 1). Zaznacz „do zmiany” i dopisz uwagę, potem „Kopiuj listę” i wklej ją do czatu.</p>
<div class="bar"><button class="primary" id="copy">Kopiuj listę do zmiany</button><span id="cnt" class="meta"></span></div>
<nav>{nav}</nav>
<textarea id="out" readonly></textarea></header>
<main>{body}</main>
<script>
const KEY = 'cast-{release}';
let state = {{}};
try {{ state = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{}}
function save() {{ try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}} count(); }}
function count() {{ const n = Object.values(state).filter(s => s.flag).length; document.getElementById('cnt').textContent = n ? 'do zmiany: ' + n : ''; }}
document.querySelectorAll('.card').forEach(card => {{
  const v = card.dataset.voice, cb = card.querySelector('input'), ta = card.querySelector('textarea');
  const s = state[v] || {{}};
  cb.checked = !!s.flag; ta.value = s.note || ''; card.classList.toggle('flag', cb.checked);
  cb.addEventListener('change', () => {{ state[v] = {{...(state[v] || {{}}), flag: cb.checked}}; card.classList.toggle('flag', cb.checked); save(); }});
  ta.addEventListener('input', () => {{ state[v] = {{...(state[v] || {{}}), note: ta.value}}; save(); }});
}});
document.querySelectorAll('audio').forEach(a => a.addEventListener('play', () => document.querySelectorAll('audio').forEach(b => {{ if (b !== a) b.pause(); }})));
document.getElementById('copy').addEventListener('click', () => {{
  const lines = Object.entries(state).filter(([, s]) => s.flag).map(([v, s]) => '- ' + v + (s.note ? ': ' + s.note.trim() : ''));
  const text = lines.length ? 'Głosy do zmiany:\\n' + lines.join('\\n') : 'Brak głosów do zmiany.';
  const out = document.getElementById('out'); out.style.display = 'block'; out.value = text; out.select();
  try {{ navigator.clipboard.writeText(text); }} catch (e) {{}}
}});
count();
</script></body></html>
'''


def card(v, desc, prod, pics, picked, count, groups, refs, labels):
    e = html.escape
    pic_voice = v if v in pics else SHARED_PORTRAIT.get(v) if SHARED_PORTRAIT.get(v) in pics else None
    pic = '<img src="portraits/%s.png" alt="Portret: %s" loading="lazy">' % (pic_voice, e(v)) if pic_voice else 'brak portretu w grze'
    engine = 'ElevenLabs eleven_v4' if D.engine(v) == 'elevenlabs' else 'OmniVoice'
    extra = ''
    p = prod.get(v)
    if isinstance(p, dict) and isinstance(p.get('omni'), dict):
        extra = 'profil: %s' % e(p['omni'].get('instruct', ''))
    elif isinstance(p, dict) and isinstance(p.get('omni'), str):
        extra = 'głos z t1 (E16)'
    top = ', '.join('%s (%d)' % (e(labels(g)), n) for g, n in groups[v].most_common(4))
    smp = ''
    for i, s in enumerate(picked.get(v, ()), 1):
        warn = ' · uwagi automatu: %s' % ', '.join(s['problems']) if s['problems'] else ''
        smp += ('<div class="sample"><q>%s</q><audio controls preload="none" src="samples/%s_%d.wav"></audio>'
                '<div class="meta">%s · <code>%s</code> · %.1f s%s</div></div>') % (
            e(s['text']), e(v), i, e(labels(s['grp'])), e(s['key']), s['seconds'], warn)
    return ('<div class="card" data-voice="{v}"><div class="pic">{pic}</div><div>'
            '<div class="head"><div><span class="name">{v}</span> <span class="meta">{engine}{extra}</span></div>'
            '<label class="chg"><input type="checkbox"> do zmiany</label></div>'
            '<div class="desc">{desc}</div><div class="meta">fragmenty w akcie 1: {n} · najczęściej: {top}</div>'
            '{smp}<textarea placeholder="Co zmienić w tym głosie?"></textarea></div></div>').format(
        v=e(v), pic=pic, engine=engine, extra=(' · ' + extra) if extra else '', desc=e(desc.get(v, '–')),
        n=count[v], top=top, smp=smp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--release', default='m4', choices=paths.RELEASES)
    ap.add_argument('--acts', type=int, nargs='*', default=[1])
    a = ap.parse_args()
    paths.use(a.release)
    out = os.path.join(paths.WORK, 'compare', '%s_cast' % a.release)
    os.makedirs(os.path.join(out, 'samples'), exist_ok=True)
    con = db.connect(paths.DB)
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    desc, prod = descriptions()
    pics = portraits(os.path.join(out, 'portraits'))
    picked, count, groups = samples(con, a.acts)
    titles = {}
    for k, text in con.execute("SELECT key, text_raw FROM lines WHERE grp = 'map' AND key LIKE '%\\_NAME' ESCAPE '\\'"):
        for g in dashboard.title_groups(k):
            titles.setdefault(g, text)
    def labels(g):
        m = re.fullmatch(r'(?:a\d_)?(scene_|story_)?(s?q\d+\w*)', g or '')
        if m:
            return m.group(2).upper() + (' (scena)' if m.group(1) == 'scene_' else '')
        if (g or '').startswith('a1_scene_'):
            return 'Scena: ' + g[len('a1_scene_'):].replace('_', ' ')
        return dashboard.group_label(g or 'system', titles)
    n_samples = 0
    for v, ss in picked.items():
        for i, s in enumerate(ss, 1):
            shutil.copyfile(os.path.join(paths.AUDIO, s['file']), os.path.join(out, 'samples', '%s_%d.wav' % (v, i)))
            n_samples += 1
    by_sec = collections.defaultdict(list)
    for v in count:
        by_sec[section(v, refs)].append(v)
    body, nav = '', ''
    for sid, title in SECTIONS:
        vs = sorted(by_sec.get(sid, ()), key=lambda v: (-count[v], v))
        if not vs:
            continue
        nav += '<a href="#%s">%s (%d)</a>' % (sid, html.escape(title.split(':')[0]), len(vs))
        body += '<h2 id="%s">%s (%d)</h2>' % (sid, html.escape(title), len(vs))
        body += ''.join(card(v, desc, prod, pics, picked, count, groups, refs, labels) for v in vs)
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(PAGE.format(release=a.release, n_voices=len(count), n_samples=n_samples, nav=nav, body=body))
    missing = sorted(v for v in count if v not in desc)
    print('głosy: %d, próbki: %d, portrety: %d, bez opisu: %s' % (
        len(count), n_samples, sum(1 for v in count if v in pics or SHARED_PORTRAIT.get(v) in pics),
        ' '.join(missing) or '0'))
    print(os.path.join(out, 'index.html'))


if __name__ == '__main__':
    main()
