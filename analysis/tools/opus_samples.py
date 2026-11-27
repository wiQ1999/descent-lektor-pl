"""Próbki do odsłuchu: audio paczki w Opus zamiast FLAC (mniejsza paczka, D117).

Bierze ok. 30 fragmentów m4 z różnych głosów (narrator, bohaterowie, złoczyńcy, ElevenLabs, efekty, mówcy bez imienia),
koduje plik FLAC z paczki w Ogg Opus w kilku przepływnościach (soundfile/libsndfile, ta sama biblioteka co w companionie)
i dekoduje go z powrotem do WAV, czyli do tego, co zagrałby companion. Strona pokazuje oryginał i warianty obok siebie,
z trybem ślepego testu, oraz szacunek rozmiaru audio całej gry dla każdej przepływności.

    .venv/Scripts/python -I analysis/tools/opus_samples.py

Wyniki w analysis/work/compare/opus/ (poza Git). Na konsolę idą tylko liczby.
"""
import html
import io
import json
import os
import random
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from lektor import paths  # noqa: E402

if os.environ.get('LEKTOR_WORK'):
    paths.ROOT = os.path.dirname(os.path.dirname(os.path.abspath(paths.WORK)))
paths.use('m4')
OUT = os.path.join(paths.WORK, 'compare', 'opus')
# compression_level libsndfile dla Opus -> przepływność (zmierzone na mowie 24 kHz mono, 2026-11-27)
VARIANTS = (('opus24', 'Opus 24 kb/s', 0.935), ('opus32', 'Opus 32 kb/s', 0.90), ('opus48', 'Opus 48 kb/s', 0.838))
GROUPS = (
    ('Narrator', [('narrator', 'long'), ('narrator', 'long'), ('narrator', 'mid'), ('narrator', 'short')]),
    ('Bohaterowie (klony dubbingu)', [('brynn', 'mid'), ('syrus', 'mid'), ('kehli', 'mid'), ('galaden', 'shout'),
                                      ('chance', 'mid'), ('vaerix', 'shout')]),
    ('Złoczyńcy i postacie z dubbingiem', [('zachareth', 'mid'), ('vraskhar', 'mid'), ('xenith', 'mid')]),
    ('ElevenLabs', [('magrit', 'mid'), ('laurel', 'mid'), ('galgoraz', 'mid'), ('button', 'mid'), ('astarra', 'mid')]),
    ('Głosy z efektem', [('kathryn', 'mid'), ('levirax_e', 'mid'), ('nv_q13_smok', 'mid'), ('nv_baelziffar', 'mid')]),
    ('Mówcy bez imienia', [('nv_ocella', 'mid'), ('nv_a2q8_ogrodniczka', 'mid'), ('nv_fof_kapitan', 'mid')]),
)
RANGES = {'long': (8.0, 14.0), 'mid': (3.0, 8.0), 'short': (0.5, 1.2), 'shout': (2.0, 8.0)}


def pick(frags, texts):
    rng = random.Random(27)
    used, out = set(), []
    for title, wants in GROUPS:
        for voice, kind in wants:
            lo, hi = RANGES[kind]
            cands = sorted(fid for fid, m in frags.items() if m['voice'] == voice and not m['problems'] and fid not in used
                           and lo <= m['seconds'] <= hi and (kind != 'shout' or '!' in texts.get(fid, '')))
            if not cands:
                continue
            fid = rng.choice(cands)
            used.add(fid)
            out.append((title, voice, fid))
    return out


def encode(y, sr, level):
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, y, sr, format='OGG', subtype='OPUS', compression_level=level)
    size = len(buf.getvalue())
    buf.seek(0)
    z, zsr = sf.read(buf, dtype='float32')
    return z, zsr, size


def main():
    import soundfile as sf
    man = json.load(open(os.path.join(paths.AUDIO, 'manifest.json'), encoding='utf-8'))['fragments']
    con = sqlite3.connect(paths.DB)
    texts = dict(con.execute('SELECT id, text FROM fragments'))
    picks = pick(man, texts)
    smp = os.path.join(OUT, 'samples')
    os.makedirs(smp, exist_ok=True)
    e = html.escape
    sizes = {k: 0 for k in ['flac'] + [v[0] for v in VARIANTS]}
    secs_total = 0.0
    sections, current = [], None
    for title, voice, fid in picks:
        src = os.path.join(paths.AUDIO, 'flac', fid + '.flac')
        y, sr = sf.read(src, dtype='float32')
        secs = len(y) / sr
        secs_total += secs
        sizes['flac'] += os.path.getsize(src)
        rows = []
        name = fid + '_flac.wav'
        sf.write(os.path.join(smp, name), y, sr, subtype='PCM_16')
        rows.append((name, 'FLAC (obecnie)', os.path.getsize(src) * 8 / secs / 1000))
        for key, label, level in VARIANTS:
            z, zsr, size = encode(y, sr, level)
            sizes[key] += size
            name = '%s_%s.wav' % (fid, key)
            sf.write(os.path.join(smp, name), z, zsr, subtype='PCM_16')
            rows.append((name, label, size * 8 / secs / 1000))
        if title != current:
            sections.append('<h2>%s</h2>' % e(title))
            current = title
        body = ''.join('<div class="row"><b data-label="%s">%s</b><div><audio controls preload="none" src="samples/%s"></audio>'
                       '<div class="meta">%.0f kb/s</div></div></div>' % (e(lb), e(lb), e(n), kb) for n, lb, kb in rows)
        sections.append('<div class="card"><q>%s</q><div class="rows">%s</div><div class="meta"><code>%s</code> · %s · %.1f s</div></div>' % (
            e(texts.get(fid, '')), body, e(fid), e(voice), secs))
    game_secs = sum(m['seconds'] for m in man.values())
    game_flac = sum(os.path.getsize(os.path.join(paths.AUDIO, 'flac', f + '.flac')) for f in man
                    if os.path.exists(os.path.join(paths.AUDIO, 'flac', f + '.flac')))
    est = {k: game_flac * sizes[k] / sizes['flac'] for k in sizes}
    table = ''.join('<tr><td>%s</td><td>%.0f kb/s</td><td>%.2f GB</td><td>%.0f%%</td></tr>' % (
        e(lb), sizes[k] * 8 / secs_total / 1000, est[k] / 1e9, 100 * sizes[k] / sizes['flac'])
        for k, lb in [('flac', 'FLAC (obecnie)')] + [(v[0], v[1]) for v in VARIANTS])
    lead = ('%d fragmentów, każdy jako obecny FLAC i po zakodowaniu w Opus oraz zdekodowaniu tą samą biblioteką co '
            'companion (soundfile). Cała gra: %d fragmentów, %.1f h audio. Rozmiar całej gry szacuję z proporcji próbek.'
            % (len(picks), len(man), game_secs / 3600))
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(PAGE.format(lead=e(lead), table=table, body=''.join(sections)))
    print('próbki: %d, sekundy: %.0f' % (len(picks), secs_total))
    for k in sizes:
        print('%s: %.0f kb/s, cała gra ok. %.2f GB' % (k, sizes[k] * 8 / secs_total / 1000, est[k] / 1e9))
    print(os.path.join(OUT, 'index.html'))


PAGE = '''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Próbki Opus</title>
<style>
:root {{ --bg:#fafaf8; --card:#fff; --fg:#1d1d1b; --muted:#6b6b66; --line:#e4e2dc; --accent:#8a3b12; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#18181a; --card:#222225; --fg:#ececea; --muted:#a3a39d; --line:#34343a; --accent:#f0a46c; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:16px 16px 48px; }}
h1 {{ font-size:20px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:28px 0 6px; }}
p.lead, .meta {{ color:var(--muted); font-size:13px; }}
table {{ border-collapse:collapse; font-size:14px; margin:8px 0; }} td, th {{ padding:4px 12px 4px 0; text-align:left; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px; margin:10px 0; }}
.card q {{ display:block; font-size:13px; margin-bottom:6px; }}
.row {{ display:grid; grid-template-columns:170px 1fr; gap:10px; align-items:center; margin:4px 0; }}
.row b {{ font-weight:600; font-size:13px; }}
.row .meta {{ display:inline; margin-left:8px; }}
audio {{ width:100%; max-width:440px; height:32px; vertical-align:middle; }}
button {{ font:inherit; padding:6px 12px; margin:4px 8px 4px 0; border:1px solid var(--line); border-radius:6px; background:var(--card); color:var(--fg); cursor:pointer; }}
body.blind .row .meta {{ visibility:hidden; }}
@media (max-width:600px) {{ .row {{ grid-template-columns:1fr; gap:2px; }} }}
</style></head><body><main>
<h1>Próbki Opus: audio paczki w mniejszym formacie</h1>
<p class="lead">{lead}</p>
<table><tr><th>Format</th><th>Przepływność</th><th>Audio całej gry</th><th>Wobec FLAC</th></tr>{table}</table>
<p class="meta">Odsłuch najlepiej w słuchawkach. Ślepy test miesza kolejność w każdej karcie i ukrywa nazwy, „Pokaż nazwy” je odsłania.</p>
<button id="blind">Ślepy test</button><button id="reveal">Pokaż nazwy</button>
{body}
</main><script>
const audios = document.querySelectorAll('audio');
audios.forEach(a => a.addEventListener('play', () => audios.forEach(b => {{ if (b !== a) b.pause(); }})));
document.getElementById('blind').onclick = () => {{
  document.body.classList.add('blind');
  document.querySelectorAll('.rows').forEach(box => {{
    const rows = [...box.children];
    for (let i = rows.length - 1; i > 0; i--) {{ const j = Math.floor(Math.random() * (i + 1)); [rows[i], rows[j]] = [rows[j], rows[i]]; }}
    rows.forEach((r, i) => {{ box.appendChild(r); r.querySelector('b').textContent = String.fromCharCode(65 + i); }});
  }});
}};
document.getElementById('reveal').onclick = () => {{
  document.body.classList.remove('blind');
  document.querySelectorAll('.row b').forEach(b => b.textContent = b.dataset.label);
}};
</script></body></html>
'''

if __name__ == '__main__':
    main()
