"""Pliki końcowe E3 (.venv): wybrane podejścia przycięte i wyrównane głośnościowo, manifest, lista do odsłuchu.

Głośność (D04): każdy fragment do jednego poziomu (LUFS), a różnice między kategoriami (głośniejsza walka) daje
companion przez wzmocnienie kategorii z manifestu, bo jeden fragment bywa w kwestiach różnych kategorii.
Lista odsłuchu (D38): fragmenty odrzucone po ponownym podejściu i losowe 5% pozostałych. Strona i plik ocen
zawierają teksty gry, więc leżą tylko w analysis/work/.
"""
import html
import json
import os
import random

from . import db, paths
from . import direction as D
from .synth import take_path

LUFS = -20.0
PEAK = 0.99
EDGE = (0.03, 0.05)     # zostawiona cisza przed i po mowie (s); pauzy między fragmentami dokłada companion
CATEGORY_GAIN_DB = {'walka_teren': 2.0}     # D04: komunikaty walki głośniej
LISTEN_MAX = 30         # odsłuch ma być krótki: po jednym fragmencie z głosu, reszta losowo (D72)
LISTEN_SEED = 3


def trim(y, sr):
    import librosa
    if len(y) < sr // 10:
        return y
    _, (a, b) = librosa.effects.trim(y, top_db=40, frame_length=1024, hop_length=256)
    return y[max(0, a - int(EDGE[0] * sr)): b + int(EDGE[1] * sr)]


def level(y, sr):
    import numpy as np
    import pyloudnorm
    loud = pyloudnorm.Meter(sr, block_size=min(0.4, len(y) / sr)).integrated_loudness(y) if len(y) > sr // 20 else -np.inf
    if np.isfinite(loud):
        y = pyloudnorm.normalize.loudness(y, loud, LUFS)
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    return (y / peak * PEAK if peak > PEAK else y), (round(float(loud), 1) if np.isfinite(loud) else None)


def finalize():
    import soundfile as sf
    choice = json.load(open(os.path.join(paths.AUDIO, 'choice.json'), encoding='utf-8'))
    out_dir = os.path.join(paths.AUDIO, 'final')
    os.makedirs(out_dir, exist_ok=True)
    frags, rates = {}, set()
    for fid, c in sorted(choice.items()):
        y, sr = sf.read(take_path(fid, c['take']), dtype='float32')
        rates.add(sr)
        y, loud = level(trim(y, sr), sr)
        sf.write(os.path.join(out_dir, fid + '.wav'), y, sr, subtype='PCM_16')
        frags[fid] = {'file': 'final/%s.wav' % fid, 'seconds': round(len(y) / sr, 3), 'take': c['take'],
                      'voice': c['voice'], 'speed': c['speed'], 'source_lufs': loud, 'problems': c['problems'],
                      'model': D.ELEVEN_MODEL if D.take_engine(c['take']) == 'elevenlabs' else D.MODEL_ID}
    if len(rates) > 1:
        raise ValueError('Podejścia mają różne próbkowanie: %s' % sorted(rates))
    manifest = {'model': D.MODEL_ID, 'sample_rate': sr, 'lufs': LUFS, 'category_gain_db': CATEGORY_GAIN_DB,
                'fragments': frags}
    json.dump(manifest, open(os.path.join(paths.AUDIO, 'manifest.json'), 'w', encoding='utf-8'), indent=1)
    return manifest


def listen_list(choice):
    """Próbka do odsłuchu bez fragmentów odrzuconych przez automat."""
    rest = sorted(f for f, c in choice.items() if not c['problems'])
    random.Random(LISTEN_SEED).shuffle(rest)
    voices = {}
    for f in rest:
        voices.setdefault(choice[f]['voice'], f)
    picked = list(voices.values())[:LISTEN_MAX]
    others = [f for f in rest if f not in set(picked)]
    return sorted(picked + others[:LISTEN_MAX - len(picked)])


def listen(engine=None):
    """listen/index.html z odtwarzaczami i ocenami (eksport do CSV), listen/lista.csv. engine: tylko głosy tego silnika
    (E13: odsłuch postaci w ElevenLabs)."""
    con = db.connect(paths.DB)
    manifest = json.load(open(os.path.join(paths.AUDIO, 'manifest.json'), encoding='utf-8'))
    choice = json.load(open(os.path.join(paths.AUDIO, 'choice.json'), encoding='utf-8'))
    sample = listen_list({f: c for f, c in choice.items() if engine is None or D.engine(c['voice']) == engine})
    text = {r['id']: r['text'] for r in con.execute('SELECT id, text FROM fragments')}
    where = {}
    for r in con.execute('SELECT s.fragment, s.key, l.category FROM segments s JOIN lines l ON l.key = s.key '
                         'WHERE s.fragment IS NOT NULL ORDER BY s.key'):
        where.setdefault(r['fragment'], []).append('%s (%s)' % (r['key'], r['category']))
    for r in con.execute('SELECT fragment, key, value FROM slot_values ORDER BY key'):
        where.setdefault(r['fragment'], []).append('%s: %s' % (r['key'], r['value']))
    out_dir = os.path.join(paths.AUDIO, 'listen')
    os.makedirs(out_dir, exist_ok=True)

    def card(fid, group):
        m, c = manifest['fragments'][fid], choice[fid]
        keys = where.get(fid, [])
        opts = ''.join('<option value="%s">%s</option>' % (v, lab) for v, lab in (
            ('', ''), ('ok', 'dobrze'), ('wymowa', 'błąd wymowy'), ('tresc', 'zgubione lub dodane słowa'),
            ('glos', 'zmiana głosu'), ('tempo', 'tempo'), ('inne', 'inne')))
        return ('<div class="card"><div class="head"><b>%s</b> · %s · tempo %s · %s</div><blockquote>%s</blockquote>'
                '<audio controls preload="none" src="../%s"></audio><div class="meta">%s · CER %s · barwa %s · %s zn./s · '
                'podejść %s%s</div><div class="rate"><select data-id="%s" data-k="ocena">%s</select>'
                '<input type="text" placeholder="uwagi" data-id="%s" data-k="note"></div></div>') % (
            fid, m['voice'], m['speed'] or 'naturalne', group, html.escape(text[fid]), m['file'],
            html.escape('; '.join(keys[:3]) + (' i %d innych' % (len(keys) - 3) if len(keys) > 3 else '')),
            c['cer'], c['sim'], c['cps'], c['takes'], ' · <span class="bad">%s</span>' % ', '.join(c['problems'])
            if c['problems'] else '', fid, opts, fid)

    rows = ['<h2>Próbka z każdego głosu (%d)</h2>' % len(sample)] + [card(f, 'losowe') for f in sample]
    page = HTML.replace('{{ROWS}}', '\n'.join(rows)).replace('{{N}}', str(len(sample)))
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(page)
    return os.path.join(out_dir, 'index.html'), len(sample)


HTML = """<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Odsłuch M1</title><style>
:root{--bg:#fafaf8;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#e3e2dc;--accent:#2f5d8a;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a29b;--card:#20201e;--line:#34332f;--accent:#7fb0e0;--bad:#f2b8b5}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:900px;margin:0 auto;padding:16px}h1{font-size:22px}h2{margin-top:32px;font-size:17px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;margin:10px 0}
.head{font-size:13px;color:var(--muted)}.head b{color:var(--fg)}.meta{color:var(--muted);font-size:12px}.bad{color:var(--bad)}
.head,.meta{overflow-wrap:anywhere}
blockquote{margin:6px 0;padding:4px 10px;border-left:3px solid var(--line)}audio{width:100%;margin:4px 0}
.rate{display:flex;gap:8px;align-items:center}.rate input{flex:1}
select,input[type=text]{padding:4px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:center;z-index:1}
button{padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
</style></head><body><main>
<h1>Odsłuch M1 (E3)</h1>
<p>{{N}} fragmentów: najpierw odrzucone przez automat po ponownym podejściu, potem losowa próbka reszty. Dla każdego wybierz ocenę; uwagi są opcjonalne. Oceny zapisują się w przeglądarce. Na końcu kliknij „Eksportuj oceny” i podaj mi ścieżkę pobranego pliku.</p>
<div class="bar"><button id="exp">Eksportuj oceny</button><span id="cnt"></span></div>
{{ROWS}}
</main><script>
const KEY='lektor-e3-odsluch';let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const els=document.querySelectorAll('[data-id]');
function count(){document.getElementById('cnt').textContent=Object.values(st).filter(v=>v.ocena).length+' / {{N}} ocenionych'}
els.forEach(el=>{const v=(st[el.dataset.id]||{})[el.dataset.k];if(v!==undefined)el.value=v;
 el.addEventListener('change',()=>{(st[el.dataset.id]=st[el.dataset.id]||{})[el.dataset.k]=el.value;
 try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){};count()})});count();
document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})));
document.getElementById('exp').onclick=()=>{const rows=[['fragment','ocena','uwagi']];
 for(const [id,v] of Object.entries(st)){rows.push([id,v.ocena||'',(v.note||'').replace(/[;\\n]/g,' ')])}
 const blob=new Blob(['\\ufeff'+rows.map(r=>r.join(';')).join('\\n')],{type:'text/csv'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='odsluch_e3.csv';a.click()};
</script></body></html>"""
