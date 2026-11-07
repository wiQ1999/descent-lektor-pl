"""Ocena automatyczna i materiały do odsłuchu porównania TTS (E0).

Dla każdego modelu z work/bakeoff/<model>/gen.json:
  - ASR (Whisper large-v3-turbo): CER, WER, ucięta końcówka, powtórzone słowa;
  - podobieństwo głosu (VoiceEncoder Chatterboxa) do neutralnej referencji;
  - tempo (znaki tekstu na sekundę audio) i akcent jako rozrzut wysokości głosu (odchylenie F0 w półtonach);
  - najlepsze z kilku podejść (najniższy CER, potem podobieństwo);
  - wyrównanie głośności do -20 LUFS (raz, w miejscu).
Wyjście (nieśledzone): work/bakeoff/eval.json, INDEX.md, index.html (odtwarzacze + oceny), oceny.csv.
Na stdout: zbiorcze liczby bez treści gry (do analysis/BAKEOFF.md). Statystyki modeli liczone są tylko
z zadań wspólnych dla wszystkich modeli; warianty jednego modelu (runda 2) podsumowuje --variants.

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/bakeoff_eval.py [--no-asr]
  .venv/Scripts/python -I analysis/tools/bakeoff_eval.py --page r2 --models omnivoice --variants A P1 P2 P3 P4
"""
import argparse
import csv
import html
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts_bench as TB  # noqa: E402  (HF_HOME, norm_words, edit_distance)

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

ROOT = TB.ROOT
BAKE = os.path.join(ROOT, 'work', 'bakeoff')
MODELS = ['chatterbox2', 'chatterbox3', 'xtts', 'omnivoice']
LABELS = {'chatterbox2': 'Chatterbox v2 (dostrojony, fp32)', 'chatterbox3': 'Chatterbox v3',
          'xtts': 'XTTS-v2', 'omnivoice': 'OmniVoice'}
VARIANT_LABELS = {'A': 'referencja neutralna', 'B': 'referencja emocjonalna', 'T2': 'zdania osobno, pauza 0,5 s',
                  'T3': 'zdania osobno, pauza 0,4 s, tempo 0,9', 'N1': 'nazwa fonetycznie',
                  'N2': 'nazwa po angielsku, wklejona', 'S': 'sklejone z fragmentów (D16)',
                  'Q': 'cytat głosem bohaterki + narrator (D20)'}
LUFS = -20.0


def job_text(job):
    return ' '.join(p['text'] for p in job['pieces'])


def asr_all(records, jobs):
    from transformers import pipeline
    import librosa
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', torch_dtype=torch.float16,
                   device='cuda')
    for rec in records:
        if 'cer' in rec:
            continue
        y, sr = sf.read(os.path.join(ROOT, rec['wav']), dtype='float32')
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        hyp = asr({'raw': y, 'sampling_rate': 16000}, return_timestamps=True,
                  generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']
        ref_w, hyp_w = TB.norm_words(job_text(jobs[rec['job']])), TB.norm_words(hyp)
        rec['asr'] = hyp.strip()
        rec['wer'] = round(TB.edit_distance(ref_w, hyp_w) / max(1, len(ref_w)), 3)
        ref_c, hyp_c = ' '.join(ref_w), ' '.join(hyp_w)
        rec['cer'] = round(TB.edit_distance(ref_c, hyp_c) / max(1, len(ref_c)), 3)
        rec['missing_tail'] = bool(ref_w) and ref_w[-1] not in set(hyp_w[-4:])
        print('asr', rec['model'], rec['name'], rec['cer'], file=sys.stderr, flush=True)


def similarity_all(records, set_data, jobs):
    import librosa
    from huggingface_hub import hf_hub_download
    from chatterbox.models.voice_encoder import VoiceEncoder
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()

    def emb(path):
        e = ve.embeds_from_wavs([librosa.load(path, sr=16000)[0]], sample_rate=16000)[0]
        return e / np.linalg.norm(e)
    refs = {}
    for rec in records:
        if 'spk_sim' in rec:
            continue
        voice = jobs[rec['job']]['pieces'][0]['voice']
        voice = set_data['ref_voice'].get(voice, voice)
        if voice not in refs:
            refs[voice] = emb(os.path.join(ROOT, set_data['refs'][voice]['neutralny']['wav']))
        rec['spk_sim'] = round(float(emb(os.path.join(ROOT, rec['wav'])) @ refs[voice]), 3)


def prosody_all(records, jobs):
    import librosa
    for rec in records:
        if 'f0_sd' in rec:
            continue
        y, sr = librosa.load(os.path.join(ROOT, rec['wav']), sr=16000)
        f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr, frame_length=1024)
        f0 = f0[voiced & np.isfinite(f0)]
        rec['f0_sd'] = round(float(np.std(12 * np.log2(f0 / np.median(f0)))), 2) if len(f0) > 10 else None
        rec['cps'] = round(len(job_text(jobs[rec['job']])) / max(rec['audio_s'], 1e-3), 1)


def normalize_loudness(records):
    import pyloudnorm
    for rec in records:
        if rec.get('lufs_normalized'):
            continue
        path = os.path.join(ROOT, rec['wav'])
        y, sr = sf.read(path, dtype='float32')
        meter = pyloudnorm.Meter(sr)
        loud = meter.integrated_loudness(y)
        if np.isfinite(loud):
            y = pyloudnorm.normalize.loudness(y, loud, LUFS)
            peak = np.max(np.abs(y))
            if peak > 0.99:
                y = y / peak * 0.99
            sf.write(path, y, sr, subtype='PCM_16')
        rec['lufs_normalized'] = True


def pick_best(records):
    best = {}
    for rec in records:
        key = (rec['model'], rec['job'])
        score = (rec.get('cer', 1.0), -rec.get('spk_sim', 0.0))
        if key not in best or score < best[key][0]:
            best[key] = (score, rec)
    for rec in records:
        rec['best'] = best[(rec['model'], rec['job'])][1] is rec
    return {k: v[1] for k, v in best.items()}


def summary(records, models, jobs):
    out = {}
    for m in models:
        rs = [r for r in records if r['model'] == m and 'models' not in jobs[r['job']]]
        if not rs:
            continue
        meta_path = os.path.join(BAKE, m, 'meta.json')
        meta = json.load(open(meta_path, encoding='utf-8')) if os.path.exists(meta_path) else {}
        best = [r for r in rs if r['best']]
        med = lambda xs: round(statistics.median(xs), 3) if xs else None  # noqa: E731
        out[m] = {
            'samples': len(rs), 'audio_min': round(sum(r['audio_s'] for r in rs) / 60, 1),
            'rtf_median': med([r['rtf'] for r in rs]), 'rtf_max': max(r['rtf'] for r in rs),
            'peak_mib_max': max(r['peak_mib'] for r in rs), 'load_s': meta.get('load_s'),
            'cer_median_all': med([r['cer'] for r in rs if 'cer' in r]),
            'cer_median_best': med([r['cer'] for r in best if 'cer' in r]),
            'cer_over_10pct_best': sum(1 for r in best if r.get('cer', 0) > 0.10),
            'missing_tail_best': sum(1 for r in best if r.get('missing_tail')),
            'spk_sim_median_best': med([r['spk_sim'] for r in best if 'spk_sim' in r]),
        }
    return out


def variant_summary(best, jobs, model, variants):
    """Mediany dla wariantów jednego modelu, tylko z fragmentów, które mają wszystkie te warianty."""
    by_frag = {}
    for j in jobs.values():
        if j['variant'] in variants and (model, j['id']) in best:
            by_frag.setdefault(j['fragment'], {})[j['variant']] = best[model, j['id']]
    frags = [f for f, vs in by_frag.items() if len(vs) == len(variants)]
    med = lambda xs: round(statistics.median(xs), 3) if xs else None  # noqa: E731
    return {'fragments': len(frags), **{v: {k: med([by_frag[f][v][k] for f in frags if by_frag[f][v].get(k) is not None])
                                           for k in ('cer', 'spk_sim', 'cps', 'f0_sd', 'rtf')} for v in variants}}


def write_index(set_data, best, models, stats, page='index', variants=None):
    frag = {f['id']: f for f in set_data['fragments']}
    jobs_by_frag = {}
    for j in set_data['jobs']:
        if (j['variant'] in variants) if variants else ('models' not in j):  # domyślnie tylko zadania wspólne
            jobs_by_frag.setdefault(j['fragment'], []).append(j)
    if page == 'index':
        write_md_csv(frag, jobs_by_frag, best, models, stats)

    def card(fid, j, m, title):
        r = best.get((m, j['id']))
        if not r:
            return ''
        rid = '%s|%s|%s' % (fid, j['variant'], m)
        sel = ''.join('<label>%s <select data-id="%s" data-k="%s"><option></option>%s</select></label>' % (
            lab, html.escape(rid), k, ''.join('<option>%d</option>' % i for i in range(1, 6))) for k, lab in
            (('nat', 'naturalność'), ('wym', 'wymowa'), ('emo', 'emocja')))
        return ('<div class="card"><div class="model">%s</div><audio controls preload="none" src="%s"></audio>'
                '<div class="meta">CER %s · podobieństwo %s · %s s · %s zn./s · F0 ±%s półt.</div><div class="rate">%s</div>'
                '<input type="text" placeholder="uwagi" data-id="%s" data-k="note"></div>' % (
                    html.escape(title), html.escape(os.path.relpath(os.path.join(ROOT, r['wav']), BAKE).replace(os.sep, '/')),
                    r.get('cer'), r.get('spk_sim'), r['audio_s'], r.get('cps'), r.get('f0_sd'), sel, html.escape(rid)))

    rows = []
    for fid, f in frag.items():
        fjobs = jobs_by_frag.get(fid)
        if not fjobs or variants and len(fjobs) < 2:  # przy --variants tylko fragmenty z czymś do porównania
            continue
        rows.append('<section><h2>%s <small>%s · %s · emocja: %s</small></h2><p class="desc">%s</p><blockquote>%s</blockquote>' % (
            fid, html.escape(f['key']), f['voice'], f['emotion'], html.escape(f['desc']), html.escape(f['text'])))
        if len(models) == 1:  # jeden model: warianty obok siebie
            rows.append('<div class="grid">%s</div>' % ''.join(card(fid, j, models[0], '%s · %s' % (
                j['variant'], VARIANT_LABELS.get(j['variant'], j['note']))) for j in fjobs))
        else:
            for j in fjobs:
                rows.append('<h3>%s · %s</h3><div class="grid">%s</div>' % (
                    j['variant'], html.escape(VARIANT_LABELS.get(j['variant'], j['note'])),
                    ''.join(card(fid, j, m, LABELS[m]) for m in models)))
        rows.append('</section>')
    stats_rows = ''.join('<tr><td>%s</td><td>%s</td><td>%s MiB</td><td>%s</td><td>%s</td></tr>' % (
        LABELS[m], s['rtf_median'], s['peak_mib_max'], s['cer_median_best'], s['spk_sim_median_best'])
        for m, s in stats.items())
    page_html = (HTML.replace('{{STATS}}', stats_rows).replace('{{ROWS}}', '\n'.join(rows))
                 .replace('{{KEY}}', 'lektor-bakeoff-oceny' + ('' if page == 'index' else '-' + page))
                 .replace('{{CSV}}', 'oceny_tts.csv' if page == 'index' else 'oceny_%s.csv' % page))
    open(os.path.join(BAKE, page + '.html'), 'w', encoding='utf-8').write(page_html)


def write_md_csv(frag, jobs_by_frag, best, models, stats):
    # INDEX.md
    md = ['# Porównanie TTS: próbki do odsłuchu', '',
          'Każdy wiersz to najlepsze z podejść danego modelu (najniższy CER). Głośność wyrównana do -20 LUFS.',
          'Wygodniej słucha się w `analysis/work/bakeoff/index.html` (odtwarzacze i formularz ocen).', '']
    md += ['| Model | RTF (mediana) | VRAM (max) | CER najlepszych (mediana) | Podobieństwo głosu |', '|---|---:|---:|---:|---:|']
    for m in models:
        s = stats.get(m)
        if s:
            md.append('| %s | %s | %s MiB | %s | %s |' % (LABELS[m], s['rtf_median'], s['peak_mib_max'], s['cer_median_best'],
                                                       s['spk_sim_median_best']))
    md.append('')
    for fid, f in frag.items():
        md += ['## %s · %s · %s · emocja: %s' % (fid, f['key'], f['voice'], f['emotion']), '', f['desc'], '', '> ' + f['text'], '']
        for j in jobs_by_frag.get(fid, []):
            md.append('**%s** (%s)' % (j['variant'], VARIANT_LABELS.get(j['variant'], j['note'])))
            for m in models:
                r = best.get((m, j['id']))
                if r:
                    md.append('- %s: `analysis/%s` · CER %s · podobieństwo %s' % (LABELS[m], r['wav'], r.get('cer'), r.get('spk_sim')))
            md.append('')
    open(os.path.join(BAKE, 'INDEX.md'), 'w', encoding='utf-8').write('\n'.join(md))

    # oceny.csv (do wypełnienia w arkuszu)
    with open(os.path.join(BAKE, 'oceny.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['fragment', 'wariant', 'model', 'plik', 'naturalnosc_1_5', 'wymowa_1_5', 'emocja_1_5', 'uwagi'])
        for fid in frag:
            for j in jobs_by_frag.get(fid, []):
                for m in models:
                    r = best.get((m, j['id']))
                    if r:
                        w.writerow([fid, j['variant'], m, r['wav'], '', '', '', ''])


HTML = """<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Porównanie TTS</title><style>
:root{--bg:#fafaf8;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#e3e2dc;--accent:#2f5d8a}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a29b;--card:#20201e;--line:#34332f;--accent:#7fb0e0}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:22px}h2{margin-top:36px;border-top:1px solid var(--line);padding-top:16px}h2 small{color:var(--muted);font-weight:400;font-size:13px}
h3{font-size:14px;color:var(--accent);margin:18px 0 8px}.desc{color:var(--muted);margin:4px 0}
blockquote{margin:8px 0;padding:8px 12px;border-left:3px solid var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}
.model{font-weight:600}.meta{color:var(--muted);font-size:12px}audio{width:100%;margin:6px 0}
.rate{display:flex;gap:8px;flex-wrap:wrap;font-size:12px}.rate select{margin-left:2px}
input[type=text]{width:100%;box-sizing:border-box;margin-top:6px;padding:4px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px}
table{border-collapse:collapse}td,th{padding:4px 10px;border-bottom:1px solid var(--line);text-align:left}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:center;z-index:1}
button{padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
</style></head><body><main>
<h1>Porównanie TTS (E0)</h1>
<p>Każda karta to najlepsze z podejść danego modelu (najniższy CER), głośność wyrównana. Oceny 1–5 zapisują się w przeglądarce; na końcu kliknij „Eksportuj oceny” i podaj mi ścieżkę pobranego pliku.</p>
<table><tr><th>Model</th><th>RTF (mediana)</th><th>VRAM (max)</th><th>CER (mediana)</th><th>Podobieństwo głosu</th></tr>{{STATS}}</table>
<div class="bar"><button id="exp">Eksportuj oceny</button><span id="cnt"></span></div>
{{ROWS}}
</main><script>
const KEY='{{KEY}}';let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const els=document.querySelectorAll('[data-id]');
function count(){document.getElementById('cnt').textContent=Object.keys(st).length+' ocenionych kart'}
els.forEach(el=>{const v=(st[el.dataset.id]||{})[el.dataset.k];if(v!==undefined)el.value=v;
 el.addEventListener('change',()=>{(st[el.dataset.id]=st[el.dataset.id]||{})[el.dataset.k]=el.value;
 try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){};count()})});count();
document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})));
document.getElementById('exp').onclick=()=>{const rows=[['fragment','wariant','model','naturalnosc','wymowa','emocja','uwagi']];
 for(const [id,v] of Object.entries(st)){rows.push([...id.split('|'),v.nat||'',v.wym||'',v.emo||'',(v.note||'').replace(/[;\\n]/g,' ')])}
 const blob=new Blob(['\\ufeff'+rows.map(r=>r.join(';')).join('\\n')],{type:'text/csv'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='{{CSV}}';a.click()};
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-asr', action='store_true')
    ap.add_argument('--page', default='index', help='nazwa strony odsłuchu; inna niż index nie nadpisuje INDEX.md i oceny.csv')
    ap.add_argument('--models', nargs='*', choices=MODELS, help='tylko te modele na stronie')
    ap.add_argument('--variants', nargs='*', help='tylko te warianty na stronie (i ich podsumowanie), np. A P1 P2')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    set_data = json.load(open(os.path.join(BAKE, 'set.json'), encoding='utf-8'))
    jobs = {j['id']: j for j in set_data['jobs']}
    eval_path = os.path.join(BAKE, 'eval.json')
    old = {(r['model'], r['name']): r for r in json.load(open(eval_path, encoding='utf-8'))} if os.path.exists(eval_path) else {}
    records, models = [], []
    for m in MODELS:
        p = os.path.join(BAKE, m, 'gen.json')
        if not os.path.exists(p):
            continue
        models.append(m)
        for name, g in json.load(open(p, encoding='utf-8')).items():
            prev = old.get((m, name), {})
            if prev.get('gen_s') != g['gen_s']:
                prev = {}  # próbka wygenerowana ponownie: stare pomiary nieaktualne
            records.append(dict(prev, **g, model=m, name=name))
    if not a.no_asr:
        asr_all(records, jobs)
    similarity_all(records, set_data, jobs)
    prosody_all(records, jobs)
    normalize_loudness(records)
    best = pick_best(records)
    json.dump(records, open(eval_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    stats = summary(records, models, jobs)
    page_models = [m for m in models if not a.models or m in a.models]
    write_index(set_data, best, page_models, {m: stats[m] for m in page_models if m in stats}, a.page, a.variants)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if a.variants:
        for m in page_models:
            print(m, json.dumps(variant_summary(best, jobs, m, a.variants), ensure_ascii=False))
    print('odsłuch: analysis/work/bakeoff/%s.html' % a.page, file=sys.stderr)


if __name__ == '__main__':
    main()
