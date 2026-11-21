"""Próbki E20 (D114) do odsłuchu: tempo narracji scen i Vaerixa oraz warianty efektów (lektor.effects).

Tempo w dwóch wariantach obok obecnego nagrania:
- model: OmniVoice czyta od nowa; narracja scen z tempem 1,4 jak okna narratora, Vaerix z tempem fragmentu × 1,2;
- WSOLA: przyspieszenie gotowego pliku (companion.control.stretch); narracja scen o stosunek zn./s okien narratora
  do scen w akcie 1, Vaerix × 1,2.
Efekty: duch (Kathryn, smok z Q13) i głos w głowie (Baelziffar) na gotowych plikach aktu 1.

    .venv/Scripts/python -I analysis/tools/e20_samples.py pick
    <omni> -I analysis/tools/e20_samples.py gen        # <omni> = "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"
    .venv/Scripts/python -I analysis/tools/e20_samples.py page [--effects]     # --effects: tylko efekty (runda 2)

Wyniki w analysis/work/compare/e20_probki/ (poza Git). Na konsolę idą tylko liczby.
"""
import collections
import html
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from lektor import db, paths, progress  # noqa: E402

if os.environ.get('LEKTOR_WORK'):      # uruchomienie z worktree: referencje i audio leżą w głównej kopii
    paths.ROOT = os.path.dirname(os.path.dirname(os.path.abspath(paths.WORK)))
paths.use('m4')
OUT = os.path.join(paths.WORK, 'compare', 'e20_probki')
PICKS = os.path.join(OUT, 'picks.json')
VAERIX_FACTOR = 1.2
SCENE_SPEED = 1.4
EFFECTS = {'kathryn': ('ghost_b2', 'ghost_b3', 'ghost_c2', 'ghost_c3'), 'nv_q13_smok': ('ghost_b2', 'ghost_b3', 'ghost_c2', 'ghost_c3'),
           'nv_baelziffar': ('mind_d', 'mind_e', 'mind_f', 'mind_g')}    # runda 2 (2026-11-21); runda 1: ghost_a–c, mind_a–c
FX_LABELS = {'ghost_a': 'duch eteryczny', 'ghost_b': 'duch z zaświatów (warstwa niżej)', 'ghost_c': 'widmo (pogłos narastający)',
             'mind_a': 'w głowie: blisko, podwojony', 'mind_b': 'demon: oktawa niżej i szept', 'mind_c': 'telepatia: modulacja i echo',
             'ghost_b2': 'z zaświatów, słabiej', 'ghost_b3': 'z zaświatów, najsłabiej', 'ghost_c2': 'widmo, słabiej',
             'ghost_c3': 'widmo, najsłabiej', 'mind_d': 'chór szeptów wokół głosu', 'mind_e': 'wnętrze czaszki: stłumiony, pulsujący',
             'mind_f': 'piekielny: niżej, nasycenie, narastanie', 'mind_g': 'echo w myślach: ciemniejące powtórzenia'}
COUNT = {'scene': 5, 'window': 2, 'vaerix': 5, 'kathryn': 3, 'nv_q13_smok': 2, 'nv_baelziffar': 3}


def candidates(con):
    man = json.load(open(os.path.join(paths.AUDIO, 'manifest.json'), encoding='utf-8'))['fragments']
    pkg = progress.packages(con)
    for r in con.execute('SELECT id, voice, speed, text, chars FROM fragments'):
        m = man.get(r['id'])
        if m and not m['problems'] and progress.act(pkg.get(r['id'], 'system')) == 1:
            yield dict(fid=r['id'], voice=r['voice'], speed=r['speed'], text=r['text'], chars=r['chars'],
                       file=m['file'], seconds=m['seconds'], grp=pkg.get(r['id'], 'system'))


def spread(cands, n, lo, hi):
    """n fragmentów o długości lo–hi znaków, najpierw z różnych grup, od najdłuższych do krótszych."""
    cands = sorted((c for c in cands if lo <= c['chars'] <= hi), key=lambda c: (-c['chars'], c['fid']))
    out, groups = [], set()
    for c in cands:
        if c['grp'] not in groups and len(out) < n:
            out.append(c)
            groups.add(c['grp'])
    out += [c for c in cands if c not in out][:n - len(out)]
    return out


def window_scene_ratio(cands):
    acc = collections.defaultdict(lambda: [0, 0.0])
    for c in cands:
        if c['voice'] == 'narrator' and c['seconds'] > 1.5:
            k = 'scene' if c['speed'] is None else 'window'
            acc[k][0] += c['chars']
            acc[k][1] += c['seconds']
    return round((acc['window'][0] / acc['window'][1]) / (acc['scene'][0] / acc['scene'][1]), 3)


def pick():
    con = db.connect(paths.DB)
    cands = list(candidates(con))
    by = collections.defaultdict(list)
    for c in cands:
        if c['voice'] == 'narrator':
            by['scene' if c['speed'] is None else 'window'].append(c)
        else:
            by[c['voice']].append(c)
    out = {'ratio': window_scene_ratio(cands), 'items': []}
    for kind, (lo, hi) in (('scene', (120, 260)), ('window', (120, 260)), ('vaerix', (70, 220)),
                           ('kathryn', (40, 220)), ('nv_q13_smok', (40, 220)), ('nv_baelziffar', (40, 220))):
        for c in spread(by[kind], COUNT[kind], lo, hi):
            out['items'].append(dict(c, kind=kind))
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(PICKS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wybrane: %s, stosunek zn./s okna/sceny: %.3f' % (
        dict(collections.Counter(i['kind'] for i in out['items'])), out['ratio']))


def gen():
    import soundfile as sf
    from lektor import synth
    picks = json.load(open(PICKS, encoding='utf-8'))
    jobs = [i for i in picks['items'] if i['kind'] in ('scene', 'vaerix')]
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    s = synth.Synth(sorted({i['voice'] for i in jobs}), refs)
    os.makedirs(os.path.join(OUT, 'gen'), exist_ok=True)
    for i in jobs:
        speed = SCENE_SPEED if i['kind'] == 'scene' else round(i['speed'] * VAERIX_FACTOR, 2)
        y = s(i['text'], i['voice'], speed, synth.seed_for(i['fid'], 1))
        sf.write(os.path.join(OUT, 'gen', i['fid'] + '.wav'), y, s.sr)
        print('%s %s tempo %.2f: %.1f s' % (i['kind'], i['fid'], speed, len(y) / s.sr), flush=True)


def check():
    """Automat E3 dla nagrań modelu: CER, ucięta końcówka, brakujące słowa, najdłuższa pauza."""
    from lektor import evaluate
    picks = json.load(open(PICKS, encoding='utf-8'))
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    score = evaluate.Scorer({v: refs[v] for v in ('narrator', 'vaerix')}, fp32=True)
    out = {}
    for i in picks['items']:
        g = os.path.join(OUT, 'gen', i['fid'] + '.wav')
        if i['kind'] in ('scene', 'vaerix') and os.path.exists(g):
            speed = SCENE_SPEED if i['kind'] == 'scene' else round(i['speed'] * VAERIX_FACTOR, 2)
            r = score(g, i['text'], i['voice'], speed)
            out[i['fid']] = r
            print('%s %s cer %.3f tail_cut %s missing %d pause %.2f sim %s' % (
                i['kind'], i['fid'], r['cer'], r['tail_cut'], r['missing'], r['pause'], r['sim']), flush=True)
    json.dump(out, open(os.path.join(OUT, 'check.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


PAGE = '''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Próbki E20</title>
<style>
:root {{ --bg:#fafaf8; --card:#fff; --fg:#1d1d1b; --muted:#6b6b66; --line:#e4e2dc; --accent:#8a3b12; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#18181a; --card:#222225; --fg:#ececea; --muted:#a3a39d; --line:#34343a; --accent:#f0a46c; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:16px 16px 48px; }}
h1 {{ font-size:20px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:28px 0 6px; }}
p.lead, .meta {{ color:var(--muted); font-size:13px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px; margin:10px 0; }}
.card q {{ display:block; font-size:13px; margin-bottom:6px; }}
.row {{ display:grid; grid-template-columns:230px 1fr; gap:10px; align-items:center; margin:4px 0; }}
.row b {{ font-weight:600; font-size:13px; }}
audio {{ width:100%; max-width:440px; height:32px; }}
@media (max-width:600px) {{ .row {{ grid-template-columns:1fr; gap:2px; }} }}
</style></head><body><main>
<h1>Próbki E20: tempo i efekty</h1>
<p class="lead">{lead}</p>
{body}
</main><script>
document.querySelectorAll('audio').forEach(a => a.addEventListener('play', () => document.querySelectorAll('audio').forEach(b => {{ if (b !== a) b.pause(); }})));
</script></body></html>
'''


def page(effects_only=False):
    import soundfile as sf
    from lektor import effects, finalize
    from lektor.companion.control import stretch
    picks = json.load(open(PICKS, encoding='utf-8'))
    ratio = picks['ratio']
    smp = os.path.join(OUT, 'samples')
    os.makedirs(smp, exist_ok=True)
    e = html.escape

    def write(name, y, sr):
        y = finalize.level(y, sr)[0]
        sf.write(os.path.join(smp, name), y, sr, subtype='PCM_16')
        return name, len(y) / sr

    def row(label, name, secs, chars):
        return ('<div class="row"><b>%s</b><div><audio controls preload="none" src="samples/%s"></audio>'
                '<div class="meta">%.1f s · %.1f zn./s</div></div></div>') % (e(label), e(name), secs, chars / secs)

    sections = collections.OrderedDict((k, []) for k in ('scene', 'window', 'vaerix', 'kathryn', 'nv_q13_smok', 'nv_baelziffar'))
    counts = collections.Counter()
    for i in picks['items']:
        if effects_only and i['kind'] not in EFFECTS:
            continue
        y, sr = sf.read(os.path.join(paths.AUDIO, i['file']), dtype='float32')
        fid, rows = i['fid'], []
        rows.append(row('obecne', *write('%s_obecne.wav' % fid, y, sr), i['chars']))
        if i['kind'] in ('scene', 'vaerix'):
            rate = ratio if i['kind'] == 'scene' else VAERIX_FACTOR
            rows.append(row('WSOLA × %.2f' % rate, *write('%s_wsola.wav' % fid, stretch(y, rate, sr), sr), i['chars']))
            g = os.path.join(OUT, 'gen', fid + '.wav')
            if os.path.exists(g):
                gy, gsr = sf.read(g, dtype='float32')
                speed = SCENE_SPEED if i['kind'] == 'scene' else round(i['speed'] * VAERIX_FACTOR, 2)
                rows.append(row('model, tempo %.2f' % speed, *write('%s_model.wav' % fid, finalize.trim(gy, gsr), gsr),
                                i['chars']))
            counts[i['kind']] += 1
        for fx in EFFECTS.get(i['kind'], ()):
            rows.append(row(FX_LABELS[fx], *write('%s_%s.wav' % (fid, fx), effects.apply(y, sr, fx), sr), i['chars']))
            counts[fx] += 1
        sections[i['kind']].append('<div class="card"><q>%s</q>%s<div class="meta"><code>%s</code> · %s · tempo fragmentu %s</div></div>' % (
            e(i['text']), ''.join(rows), e(fid), e(i['grp']), 'naturalne' if i['speed'] is None else '%.2f' % i['speed']))
    titles = {'scene': 'Narracja scen: obecnie tempo naturalne, cel jak w oknach narratora',
              'window': 'Dla porównania: narrator w oknach gry (tempo 1,4, bez zmian)',
              'vaerix': 'Vaerix: o 20% szybciej niż obecnie',
              'kathryn': 'Kathryn: efekt ducha (głos ElevenLabs bez zmian)',
              'nv_q13_smok': 'Smok-duch z Q13: efekt ducha na obecnym głosie (nowy głos przyjdzie w kroku 3)',
              'nv_baelziffar': 'Baelziffar: głos w głowie Galadena'}
    body = ''.join('<h2>%s</h2>%s' % (e(titles[k]), ''.join(v)) for k, v in sections.items() if v)
    if effects_only:
        lead = ('Runda 2 efektów: ghost_b i ghost_c słabiej (wariant 2 mocniej, 3 najsłabiej) z ogonem najwyżej 0,35 s '
                'po mowie, wyciszanym na końcu, oraz cztery nowe propozycje głosu w głowie. Pliki wyrównane do −20 LUFS.')
        name = 'efekty_r2.html'
    else:
        lead = ('Wszystkie pliki przycięte i wyrównane do −20 LUFS jak w paczce. WSOLA dla narracji scen przyspiesza o '
                'stosunek tempa okien do scen w akcie 1 (× %.2f), model czyta od nowa z tempem 1,4.' % ratio)
        name = 'index.html'
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(PAGE.format(lead=e(lead), body=body))
    print('próbki: %s' % dict(counts))
    print(os.path.join(OUT, name))


if __name__ == '__main__':
    if sys.argv[1] == 'page':
        page('--effects' in sys.argv)
    else:
        {'pick': pick, 'gen': gen, 'check': check}[sys.argv[1]]()
