"""Kandydaci głosów E20 (D114) po odsłuchu całej gry: nowe głosy, poprawki jakości, klony i oczyszczona referencja.

Profile w analysis/tools/voice_designs_e20.json (rodzaj, opisy OmniVoice, własne zdanie w stylu postaci jak w D41: profil leży w publicznym repo, więc bez tekstu gry; obróbka).
- new: kilka opisów × dwa ziarna i wariant z obróbką; na stronę idą trzy kandydatury najdalej od całej obsady.
- fix: ten sam profil bez szeptu, trzy ziarna; kandydatury najbliżej obecnej barwy, z żywszą intonacją.
- clone: klon referencji `src` (Ne'Krul, Levirax) z obróbką, przy Levirax także projekty.
- clean: referencja `src` odszumiona w trzech siłach (Gilliam).
Każdy kandydat czyta też kwestię z gry (tę samą co próbka 1 w zestawieniu m4_cast), żeby było słychać głos w grze.
Strona: portret z gry (postać albo typ wroga), opis, obecny głos i głosy zbyt podobne; wybór A–C, „bez zmian”, „żaden nie pasuje”,
kandydat „niepoprawny” z uwagą i uwaga do postaci.

    <omni> -I analysis/tools/recast_e20.py design     # <omni> = "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"
    .venv/Scripts/python -I analysis/tools/recast_e20.py choose
    <omni> -I analysis/tools/recast_e20.py lines
    .venv/Scripts/python -I analysis/tools/recast_e20.py page
    .venv/Scripts/python -I analysis/tools/recast_e20.py adopt nv_x=B gilliam=A nv_y=-

Wyniki w analysis/work/compare/e20_recast/ (poza Git).
"""
import hashlib
import html
import json
import os
import shutil
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, '..', '..', 'src'))
from lektor import paths  # noqa: E402

if os.environ.get('LEKTOR_WORK'):      # uruchomienie z worktree: referencje i audio leżą w głównej kopii
    paths.ROOT = os.path.dirname(os.path.dirname(os.path.abspath(paths.WORK)))
paths.use('m4')
ROOT = paths.ROOT
ROUND = int(sys.argv[sys.argv.index('--round') + 1]) if '--round' in sys.argv else 1
R1 = os.path.join(paths.WORK, 'compare', 'e20_recast')
OUT = R1 if ROUND == 1 else os.path.join(R1, 'r%d' % ROUND)
_DESIGNS = json.load(open(os.path.join(TOOLS, 'voice_designs_e20%s.json' % ('' if ROUND == 1 else '_r%d' % ROUND)),
                          encoding='utf-8'))
VOICES = {k: v for k, v in _DESIGNS.items() if not k.startswith('_')}
GROUPS = _DESIGNS.get('_groups', {})       # wrogowie o tej samej nazwie: jeden głos wybrany z istniejących
SEEDS = {'new': (7, 29), 'fix': (7, 29, 53), 'clone': (7, 29)} if ROUND == 1 else \
    {'new': (11, 37), 'fix': (11, 37, 61), 'clone': (11, 37)}
CPS = 12.5
MAX_CER = 0.10
F0_RANGE = {'male': (55, 240), 'female': (120, 430)}
LETTERS = 'ABCDEFGHIJKL'


def load(name, default=None):
    path = os.path.join(OUT, name)
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    json.dump(data, open(os.path.join(OUT, name), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def refs():
    return json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))


def denoise(y, sr, strength):
    """Odszumianie widmowe: profil szumu z 10% najcichszych ramek, odejmowanie z podłogą, łagodny filtr >7,5 kHz."""
    import numpy as np
    from scipy import signal
    f, t, S = signal.stft(y, sr, nperseg=1024, noverlap=768)
    mag, ph = np.abs(S), np.angle(S)
    energy = mag.sum(axis=0)
    quiet = mag[:, energy <= np.quantile(energy, 0.1)]
    noise = np.median(quiet, axis=1, keepdims=True)
    clean = np.maximum(mag - strength * noise, 0.08 * mag)
    clean[f > 7500] *= 0.5
    _, out = signal.istft(clean * np.exp(1j * ph), sr, nperseg=1024, noverlap=768)
    out = out[:len(y)].astype(np.float32)
    return out * (np.abs(y).max() / (np.abs(out).max() + 1e-9))


def growl(y, sr, amount):
    """Ryk i chropowatość potwora: warstwa oktawę niżej i nasycenie tanh."""
    import librosa
    import numpy as np
    low = librosa.effects.pitch_shift(y, sr=sr, n_steps=-12)
    out = y + amount * 0.8 * low
    drive = 1 + 4 * amount
    out = np.tanh(drive * out / (np.abs(out).max() + 1e-9)) / np.tanh(drive)
    return out.astype(np.float32)


def process(y, sr, fx):
    import librosa
    import numpy as np
    import npc_voices as N
    out = y
    if fx.get('shift'):
        out = librosa.effects.pitch_shift(out, sr=sr, n_steps=fx['shift'])
    if fx.get('growl'):
        out = growl(out, sr, fx['growl'])
    if fx.get('tremor'):
        out = N.tremble(out, sr, fx['tremor'])
    if fx.get('rasp'):
        out = N.roughen(out, sr, fx['rasp'])
    return (out * (0.9 / (np.abs(out).max() + 1e-9))).astype(np.float32)


def design():
    import soundfile as sf
    import npc_voices as N
    model = N.load_omnivoice()
    N.tokenizer_to_cpu(model)
    os.makedirs(os.path.join(OUT, 'scan'), exist_ok=True)
    scan = load('scan.json', {})
    r = refs()

    def add(name, **entry):
        scan[name] = {k: v for k, v in entry.items()}
        save('scan.json', scan)

    def fresh(name, key):
        old = scan.get(name)
        return not (old and old.get('key') == key and os.path.exists(os.path.join(paths.WORK, old['wav'])))

    for voice, p in VOICES.items():
        text = p['text']
        if p['kind'] == 'clean':        # kandydatami są same referencje po odszumieniu
            src = r[p['src']]
            y, sr = sf.read(os.path.join(ROOT, src['wav']), dtype='float32')
            for i, fx in enumerate(p['fx'], 1):
                name = '%s_dn%d' % (voice, i)
                wav = os.path.join(OUT, 'scan', name + '.wav')
                sf.write(wav, denoise(y, sr, fx['denoise']), sr, subtype='PCM_16')
                add(name, voice=voice, seed=0, instruct='referencja %s, odszumianie %.1f' % (p['src'], fx['denoise']),
                    wav=os.path.relpath(wav, paths.WORK), text=src['text'], key='dn%.1f' % fx['denoise'], fx={'base': True})
            continue
        if p['kind'] == 'clone':
            src = r[p['src']]
            prompt = model.create_voice_clone_prompt(os.path.join(ROOT, src['wav']), src['text'])
            speed = (src.get('style') or {}).get('speed')
            # z clone_instructs klon dostaje opis OmniVoice (np. młodszy kuzyn), bez niego czysty klon
            for d, instruct in enumerate(p.get('clone_instructs') or [None], 1):
                for seed in p.get('seeds') or SEEDS['clone']:
                    name = '%s_klon%s_s%d' % (voice, '' if instruct is None else str(d), seed)
                    key = '%s|%s|%s|%s' % (src['sha'], text, speed, instruct)
                    if fresh(name, key):
                        wav = os.path.join(OUT, 'scan', name + '.wav')
                        N.synth(model, wav, text, seed, voice_clone_prompt=prompt, **({'speed': speed} if speed else {}),
                                **({'instruct': instruct} if instruct else {}))
                        add(name, voice=voice, seed=seed, instruct='klon %s%s' % (p['src'], ', ' + instruct if instruct else ''),
                            wav=os.path.relpath(wav, paths.WORK), text=text, key=key, clone=True)
        seeds = p.get('seeds') or SEEDS['fix' if p['kind'] == 'fix' else 'new']
        for d, instruct in enumerate(p['instructs'], 1):
            for seed in seeds:
                name = '%s_d%d_s%d' % (voice, d, seed)
                key = '%s|%s' % (instruct, text)
                if fresh(name, key):
                    wav = os.path.join(OUT, 'scan', name + '.wav')
                    N.synth(model, wav, text, seed, instruct=instruct, duration=round(len(text) / CPS, 2))
                    add(name, voice=voice, seed=seed, instruct=instruct, wav=os.path.relpath(wav, paths.WORK), text=text,
                        key=key)


def game_line(voices):
    """Kwestia z gry dla każdego głosu: ta sama co próbka 1 w zestawieniu m4_cast (lektor cast_sheet.samples)."""
    import cast_sheet
    from lektor import db
    picked = cast_sheet.samples(db.connect(paths.DB), [1, 2, 3])[0]
    out = {}
    con = db.connect(paths.DB)
    for v in voices:
        if picked.get(v):
            s = picked[v][0]
            speed = con.execute('SELECT speed FROM fragments WHERE id = ?', (s['fragment'],)).fetchone()['speed']
            out[v] = {'fragment': s['fragment'], 'text': s['text'], 'key': s['key'], 'speed': speed}
    return out


def choose():
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from huggingface_hub import hf_hub_download
    from chatterbox.models.voice_encoder import VoiceEncoder
    import npc_voices as N
    scan = load('scan.json')
    r1_scan = json.load(open(os.path.join(R1, 'scan.json'), encoding='utf-8')) if ROUND > 1 else {}
    for p in VOICES.values():       # kandydaci z rundy 1 bez obróbki, które odsłuch chwalił poza trzaskami
        for n in p.get('keep', []):
            scan['r1_' + n] = {**r1_scan[n], 'kept': True}
    for name, c in list(scan.items()):        # warianty z obróbką
        p = VOICES.get(c['voice'])
        if not p or c.get('fx') or p['kind'] == 'clean':
            continue
        for i, fx in enumerate(p.get('fx', []), 1):
            new = '%s_fx%d' % (name, i)
            wav = os.path.join(OUT, 'scan', new + '.wav')
            key = c['key'] + '|' + json.dumps(fx, sort_keys=True)
            if new not in scan or scan[new].get('key') != key:
                y, sr = sf.read(os.path.join(paths.WORK, c['wav']), dtype='float32')
                sf.write(wav, process(y, sr, fx), sr, subtype='PCM_16')
                scan[new] = {**{k: v for k, v in c.items() if k not in ('cer', 'f0', 'f0_sd', 'emb', 'rms')},
                             'wav': os.path.relpath(wav, paths.WORK), 'fx': fx, 'key': key,
                             'instruct': c['instruct'] + ', ' + ', '.join('%s %s' % kv for kv in fx.items())}
    asr = N.load_asr()
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()

    def emb(y):
        e = ve.embeds_from_wavs([y], sample_rate=16000)[0]
        return e / np.linalg.norm(e)
    for c in scan.values():
        if 'cer' in c:
            continue
        y, _ = librosa.load(os.path.join(paths.WORK, c['wav']), sr=16000)
        g = VOICES[c['voice']]['g']
        c['cer'] = round(N.cer(c['text'], asr({'raw': y, 'sampling_rate': 16000},
                                              generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']), 3)
        f0 = librosa.pyin(y, fmin=50, fmax=260 if g == 'male' else 520, sr=16000)[0]
        f0 = f0[np.isfinite(f0)]
        c['f0'] = round(float(np.median(f0)), 0) if len(f0) else 0.0
        c['f0_sd'] = round(float(np.std(12 * np.log2(f0 / np.median(f0)))), 2) if len(f0) > 10 else 0.0
        c['emb'] = emb(y).tolist()
    save('scan.json', scan)
    r = refs()
    taken = {v: emb(librosa.load(os.path.join(ROOT, x['wav']), sr=16000)[0])
             for v, x in r.items() if x.get('wav') and os.path.exists(os.path.join(ROOT, x['wav']))}
    r1_choice = json.load(open(os.path.join(R1, 'choice.json'), encoding='utf-8')) if ROUND > 1 else {}
    chosen = {}
    for voice, p in VOICES.items():
        mine = [n for n, c in scan.items() if c['voice'] == voice and not c.get('kept')]
        kept = [n for n, c in scan.items() if c['voice'] == voice and c.get('kept')]
        rejected = [np.array(r1_scan[c['name']]['emb']) for c in r1_choice.get(voice, [])
                    if c['name'] in r1_scan and 'r1_' + c['name'] not in scan]
        if p['kind'] == 'clean':
            chosen[voice] = [{'name': n, 'score': None} for n in sorted(mine)][:3]
            continue
        lo, hi = F0_RANGE[p['g']]
        ok = [n for n in mine if scan[n]['cer'] <= MAX_CER and lo <= scan[n]['f0'] <= hi] or \
            sorted(mine, key=lambda n: scan[n]['cer'])[:6]
        ok = [n for n in ok if not any(float(np.dot(scan[n]['emb'], e)) > 0.97 for e in rejected)] or ok     # bez powtórek odrzuconych
        current = taken.get(voice)
        if p['kind'] == 'fix' and current is not None:
            def score(n):      # bliżej obecnej barwy i żywsza intonacja (robotyczny głos ma płaską melodię)
                return -(float(np.dot(scan[n]['emb'], current)) + 0.02 * scan[n]['f0_sd'])
            limit = 0.97
        else:
            # od rundy 2 także daleko od kandydatów odrzuconych w poprzedniej rundzie
            others = [e for v, e in taken.items() if v != voice or p['kind'] == 'new'] + rejected

            def score(n):
                return max(float(np.dot(scan[n]['emb'], e)) for e in others)
            limit = 0.93
        ranked = sorted(ok, key=score)
        if p['kind'] == 'clone':        # pierwszy kandydat to klon (prośba z odsłuchu), potem reszta
            ranked = sorted(ranked, key=lambda n: not scan[n].get('clone'))
        picks = list(kept)              # zachowani z rundy 1 idą zawsze, obok trzech nowych
        for n in ranked:
            if len(picks) == 3 + len(kept):
                break
            if all(float(np.dot(scan[n]['emb'], scan[q]['emb'])) < limit for q in picks):
                picks.append(n)
        picks += [n for n in ranked if n not in picks][:3 + len(kept) - len(picks)]
        chosen[voice] = [{'name': n, 'score': None if n in kept else
                          round(-score(n) if p['kind'] == 'fix' else score(n), 3)} for n in picks]
        if p['kind'] == 'new':
            taken['new:' + voice] = np.array(scan[picks[0]]['emb'])
        print('%-24s %s' % (voice, '  '.join('%s CER %.2f F0 %3.0f sd %.1f' % (
            c['name'].replace(voice + '_', ''), scan[c['name']]['cer'], scan[c['name']]['f0'], scan[c['name']]['f0_sd'])
            for c in chosen[voice])))
    save('choice.json', chosen)
    save('lines.json', game_line(list(VOICES)))


def lines():
    """Kwestia z gry czytana przez każdego kandydata (klon z jego referencji), tempo fragmentu."""
    import npc_voices as N
    from lektor import synth
    scan, chosen, glines = load('scan.json'), load('choice.json'), load('lines.json')
    import torch
    model = N.load_omnivoice()
    os.makedirs(os.path.join(OUT, 'linie'), exist_ok=True)
    done = load('lines_done.json', {})
    todo = []
    for voice, cands in chosen.items():
        g = glines.get(voice)
        if not g:
            continue
        for i, c in enumerate(cands):
            s = scan[c['name']]
            name = '%s_%s' % (voice, LETTERS[i])
            key = '%s|%s|%s' % (c['name'], s.get('key'), g['fragment'])
            wav = os.path.join(OUT, 'linie', name + '.wav')
            if not (done.get(name) == key and os.path.exists(wav)):
                todo.append((name, key, wav, g, model.create_voice_clone_prompt(os.path.join(paths.WORK, s['wav']), s['text'])))
    # jak lektor.synth: referencje zakodowane, tokenizer na CPU i gałąź CFG bez dopełniania; bez tego model w fp32
    # wychodzi poza 4 GB i spada do pamięci systemowej (runda 1: ok. 210 s na kwestię zamiast kilku)
    model.audio_tokenizer.to('cpu')
    torch.cuda.empty_cache()
    model._generate_iterative = synth.generate_iterative_unpadded.__get__(model)
    for name, key, wav, g, prompt in todo:
        N.synth(model, wav, g['text'], synth.seed_for(g['fragment'], 1), voice_clone_prompt=prompt,
                **({'speed': g['speed']} if g['speed'] else {}))
        done[name] = key
        save('lines_done.json', done)


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--card:#fff;--line:#e3e0d8;--accent:#9a3412}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecebe6;--muted:#a3a19a;--card:#1e1e1c;--line:#34332f;--accent:#fb923c}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;padding:16px;max-width:1150px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:6px 0}
.cand{border:1px solid var(--line);border-radius:8px;padding:8px;flex:1 1 320px;min-width:0}
.cand.auto{border-color:var(--accent)}
.muted{color:var(--muted);font-size:13px} audio{width:100%;max-width:340px;height:34px}
q{display:block;font-size:13px;margin:4px 0}
h2{margin:4px 0;font-size:17px} h3{margin:26px 0 4px}
button{font:inherit;padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
#out{white-space:pre-wrap;font-family:monospace;font-size:13px}
.lab{font-size:12px;color:var(--muted);margin-top:4px}
.who{display:grid;grid-template-columns:120px 1fr;gap:14px;margin-bottom:8px}
.pic{width:120px;height:120px;border-radius:6px;background:var(--line);display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px;text-align:center;overflow:hidden}
.pic img{width:100%;height:100%;object-fit:cover;object-position:top}
.desc{margin:2px 0 6px}
.pick{display:flex;flex-wrap:wrap;gap:4px 16px;margin:8px 0 4px;font-size:14px}
.cand.bad{border-color:#b91c1c;background:color-mix(in srgb,#b91c1c 8%,var(--card))}
.cand.sel{outline:2px solid var(--accent)}
textarea{width:100%;font:inherit;font-size:13px;margin-top:6px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
.cand textarea{display:none}.cand.bad textarea{display:block}
.gray{font-size:12px;color:var(--muted)}
@media (max-width:600px){.who{grid-template-columns:1fr}.pic{width:96px;height:96px}}
"""
ENEMY_TABS = {     # mówcy, którzy są typem wroga: portret z karty wroga (d3/enemies/_portraits)
    'nv_fae': 'Fae_Tab', 'nv_bandyta': 'Bandit_Tab', 'nv_a2q3_bandyta': 'Bandit_Tab', 'nv_q3_herszt': 'Bandit_Boss_Tab',
    'nv_fanatyk': 'Zealot_Tab', 'nv_widmo': 'Specter_Tab', 'nv_siostra_krwi': 'Blood Sister_Tab'}


def enemy_portraits(out_dir):
    """{głos: plik} portretów typu wroga z kopii gry (tylko analysis/work)."""
    import UnityPy
    from lektor import game as G
    want = set(ENEMY_TABS.values())
    env = UnityPy.load(os.path.join(paths.BUNDLES, G.Game().files['d3/enemies/_portraits']))
    saved = set()
    for o in env.objects:
        if o.type.name == 'Texture2D':
            d = o.read()
            if d.m_Name in want and d.m_Name not in saved:
                d.image.save(os.path.join(out_dir, d.m_Name.replace(' ', '_') + '.png'))
                saved.add(d.m_Name)
    return {v: t.replace(' ', '_') + '.png' for v, t in ENEMY_TABS.items() if t in saved}


SECTIONS = (('new', 'Nowe głosy'), ('clone', 'Klony z obróbką'), ('clean', 'Oczyszczona referencja'),
            ('fix', 'Ten sam profil, lepsza jakość'))


def page():
    import soundfile as sf
    from lektor import effects, finalize
    scan, chosen, glines = load('scan.json'), load('choice.json'), load('lines.json')
    r = refs()
    for sub in ('obecne', 'kandydaci', 'linie_poziom'):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    cast = os.path.join(paths.WORK, 'compare', 'm4_cast', 'samples')
    e = html.escape

    def leveled(src, dst, fx=None):
        y, sr = sf.read(src, dtype='float32')
        y = finalize.trim(y, sr)
        if fx:
            y = effects.apply(y, sr, fx)
        sf.write(dst, finalize.level(y, sr)[0], sr, subtype='PCM_16')

    def audio(rel):
        return '<audio controls preload="none" src="%s"></audio>' % e(rel)

    import cast_sheet
    desc = cast_sheet.descriptions()[0]
    pic_src = os.path.join(paths.WORK, 'compare', 'm4_cast', 'portraits')     # portrety z gry (cast_sheet)
    os.makedirs(os.path.join(OUT, 'portrety'), exist_ok=True)

    enemy = enemy_portraits(os.path.join(OUT, 'portrety'))

    def portrait(voice):
        if voice in enemy:
            return '<img src="portrety/%s" alt="Portret typu wroga: %s" title="portret typu wroga" loading="lazy">' % (
                e(enemy[voice]), e(voice))
        for v in (voice, cast_sheet.SHARED_PORTRAIT.get(voice)):
            src = v and os.path.join(pic_src, v + '.png')
            if src and os.path.exists(src):
                shutil.copyfile(src, os.path.join(OUT, 'portrety', v + '.png'))
                return '<img src="portrety/%s.png" alt="Portret: %s" loading="lazy">' % (e(v), e(voice))
        return 'brak portretu w grze'

    def current(voice):
        src = os.path.join(cast, voice + '_1.wav')
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(OUT, 'obecne', voice + '.wav'))
            return audio('obecne/%s.wav' % voice)
        x = r.get(voice)
        if x and os.path.exists(os.path.join(ROOT, x['wav'])):
            shutil.copyfile(os.path.join(ROOT, x['wav']), os.path.join(OUT, 'obecne', voice + '.wav'))
            return audio('obecne/%s.wav' % voice)
        return '<span class="muted">brak</span>'

    body, n_cards = '', 0
    for kind, title in SECTIONS:
        cards = []
        for voice, p in VOICES.items():
            if p['kind'] != kind or voice not in chosen:
                continue
            g = glines.get(voice)
            cands = []
            first = next((i for i, c in enumerate(chosen[voice]) if not scan[c['name']].get('kept')), 0)
            for i, c in enumerate(chosen[voice]):
                s = scan[c['name']]
                L = LETTERS[i]
                shutil.copyfile(os.path.join(paths.WORK, s['wav']), os.path.join(OUT, 'kandydaci', '%s_%s.wav' % (voice, L)))
                line = ''
                lw = os.path.join(OUT, 'linie', '%s_%s.wav' % (voice, L))
                if os.path.exists(lw):
                    leveled(lw, os.path.join(OUT, 'linie_poziom', '%s_%s.wav' % (voice, L)))
                    line = '<div class="lab">kwestia z gry</div>' + audio('linie_poziom/%s_%s.wav' % (voice, L))
                    if p.get('fx_final'):
                        leveled(lw, os.path.join(OUT, 'linie_poziom', '%s_%s_fx.wav' % (voice, L)), p['fx_final'])
                        line += '<div class="lab">kwestia z gry z efektem %s</div>' % e(p['fx_final']) + \
                            audio('linie_poziom/%s_%s_fx.wav' % (voice, L))
                cands.append('<div class="cand%s" data-l="%s"><b>%s</b>%s'
                             '<div class="muted">%s · CER %s · F0 %s Hz · melodia %s st</div>%s'
                             '<div class="gray">zdanie z projektu głosu (referencja modelu)</div>%s'
                             '<label class="gray"><input type="checkbox" class="bad"> niepoprawny</label>'
                             '<textarea placeholder="Co jest nie tak z kandydatem %s?"></textarea></div>' % (
                                 ' auto' if i == first else '', L, L, ' (z rundy 1, bez obróbki)' if s.get('kept') else
                                 ' (propozycja automatu)' if i == first else '',
                                 e(s['instruct']), s.get('cer', '–'), s.get('f0', '–'), s.get('f0_sd', '–'),
                                 line, audio('kandydaci/%s_%s.wav' % (voice, L)), L))
            near = ''.join('<div class="row"><code>%s</code> %s</div>' % (e(n), current(n)) for n in p.get('near', []))
            quote = '<q>%s</q>' % e(g['text']) if g else ''
            picks = ''.join('<label><input type="radio" name="%s" value="%s"> %s</label>' % (voice, L, L)
                            for L in LETTERS[:len(cands)])
            picks += ('<label><input type="radio" name="%s" value="-"> bez zmian (obecny głos)</label>'
                      '<label><input type="radio" name="%s" value="0"> żaden nie pasuje</label>' % (voice, voice))
            cards.append('<div class="card" data-voice="%s"><div class="who"><div class="pic">%s</div><div>'
                         '<h2>%s</h2><div class="desc">%s</div><div class="muted">Twoja uwaga z odsłuchu gry: %s</div>'
                         '</div></div>'
                         '<div class="row"><span class="muted">obecny głos, kwestia z gry:</span> %s</div>%s%s'
                         '<div class="row">%s</div><div class="pick"><b>Wybór:</b>%s</div>'
                         '<textarea class="note" placeholder="Uwaga do postaci (opcjonalnie)"></textarea></div>' % (
                             e(voice), portrait(voice), e(voice), e(desc.get(voice, '–')), e(p['note']), current(voice),
                             quote, ('<div class="muted">głosy zbyt podobne:</div>' + near) if near else '',
                             ''.join(cands), picks))
        if cards:
            body += '<h3>%s (%d)</h3>%s' % (e(title), len(cards), ''.join(cards))
            n_cards += len(cards)
    script = """
<script>
const KEY='recast-e20';
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function store(s){try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
const st=load();
function get(v){let x=st[v];if(typeof x==='string')x={pick:x};return st[v]=x||{pick:'',bad:{},note:''}}
function put(){store(st);count()}
function count(){const all=document.querySelectorAll('.card').length;
 const n=[...document.querySelectorAll('.card')].filter(c=>get(c.dataset.voice).pick).length;
 document.getElementById('cnt').textContent='wybrano: '+n+' / '+all}
document.querySelectorAll('.card').forEach(card=>{const v=card.dataset.voice,s=get(v);s.bad=s.bad||{};
 const mark=()=>card.querySelectorAll('.cand').forEach(c=>c.classList.toggle('sel',c.dataset.l===s.pick));
 card.querySelectorAll('input[type=radio]').forEach(r=>{r.checked=s.pick===r.value;
  r.addEventListener('change',()=>{s.pick=r.value;mark();put()})});
 card.querySelectorAll('.cand').forEach(c=>{const L=c.dataset.l,cb=c.querySelector('input.bad'),ta=c.querySelector('textarea');
  const b=s.bad[L];cb.checked=!!b;ta.value=(b&&b.note)||'';c.classList.toggle('bad',cb.checked);
  cb.addEventListener('change',()=>{if(cb.checked)s.bad[L]={note:ta.value};else delete s.bad[L];c.classList.toggle('bad',cb.checked);put()});
  ta.addEventListener('input',()=>{s.bad[L]={note:ta.value};put()})});
 const note=card.querySelector('textarea.note');note.value=s.note||'';
 note.addEventListener('input',()=>{s.note=note.value;put()});mark()});
document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})));
const LAB={'-':'bez zmian','0':'żaden nie pasuje'};
function copyList(){const lines=[];
 document.querySelectorAll('.card').forEach(c=>{const v=c.dataset.voice,s=get(v);
  let t=v+'='+(s.pick||'?')+(LAB[s.pick]?' ('+LAB[s.pick]+')':'');
  if((s.note||'').trim())t+=' — '+s.note.trim().replace(/\\s+/g,' ');
  lines.push(t);
  Object.entries(s.bad||{}).sort().forEach(([L,b])=>lines.push('  '+L+' niepoprawny'+((b.note||'').trim()?': '+b.note.trim().replace(/\\s+/g,' '):'')))});
 const t='Wybór głosów E20:\\n'+lines.join('\\n');document.getElementById('out').textContent=t;
 try{navigator.clipboard.writeText(t)}catch(e){}}
count();
</script>"""
    if ROUND > 1:
        script = script.replace("KEY='recast-e20'", "KEY='recast-e20-r%d'" % ROUND).replace(
            'Wybór głosów E20:', 'Wybór głosów E20, runda %d:' % ROUND)
    rnd = '' if ROUND == 1 else ', runda %d' % ROUND
    doc = ('<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Głosy E20%s</title><style>%s</style></head><body><h1>Głosy E20: kandydaci%s</h1>'
           '<p class="muted">Postać z portretem z gry i opisem. Każdy kandydat czyta tę samą kwestię z gry co obecny głos '
           '(wyrównaną do −20 LUFS jak w paczce), a pod nią jest zdanie, z którego model zaprojektował głos. Kandydat z dopiskiem „propozycja automatu” to '
           'propozycja automatu: przy nowych głosach najdalej od całej obsady (od rundy 2 także od odrzuconych), przy '
           'poprawkach najbliżej obecnej barwy z żywszą melodią. Kandydaci „z rundy 1, bez obróbki” to wersje bez trzasków '
           'kandydatów chwalonych w rundzie 1. Wybierz kandydata, „bez zmian” albo „żaden nie pasuje”; kandydata możesz oznaczyć jako '
           'niepoprawnego z uwagą. Stan zapisuje się w przeglądarce. Na końcu kliknij „Kopiuj wybór” i wklej go do czatu.</p>'
           '<p class="muted" id="cnt"></p>'
           '%s<p><button onclick="copyList()">Kopiuj wybór</button></p><div id="out"></div>%s</body></html>'
           % (rnd, CSS, rnd, body, script))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(doc)
    print('strona: %s, głosów: %d' % (os.path.join(OUT, 'index.html'), n_cards))


def adopt(args):
    import soundfile as sf
    scan, chosen = load('scan.json'), load('choice.json')
    path = os.path.join(paths.REFS, 'refs.json')
    r = refs()
    for arg in args:
        voice, letter = arg.split('=')
        if letter == '-':
            continue
        c = scan[chosen[voice][LETTERS.index(letter)]['name']]
        wav = os.path.join(paths.REFS, voice + '.wav')
        shutil.copyfile(os.path.join(paths.WORK, c['wav']), wav)
        old = r.get(voice) or {}
        entry = {'wav': paths.rel(wav), 'text': c['text'], 'seconds': round(sf.info(wav).duration, 2),
                 'source': 'E20 (D114): %s „%s”, ziarno %d, wybór z odsłuchu %s' % (
                     'odszumiona referencja' if VOICES[voice]['kind'] == 'clean' else 'projekt OmniVoice',
                     c['instruct'], c['seed'], letter),
                 'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
        if old.get('style') and (VOICES[voice]['kind'] == 'clean' or c.get('clone')):
            entry['style'] = old['style']       # tempo klonu z dubbingu zostaje
        r[voice] = entry
        print('%-24s %s %5.1f s' % (voice, letter, entry['seconds']))
    json.dump(r, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def group_plan():
    """Grupy wrogów o tej samej nazwie (.venv): opcje to obecne głosy członków i kandydaci rundy 1 bez obróbki,
    kwestie to dwie najdłuższe kwestie z gry członków grupy."""
    r = refs()
    r1 = json.load(open(os.path.join(R1, 'scan.json'), encoding='utf-8'))
    members = [m for spec in GROUPS.values() for m in spec['members']]
    glines = game_line(members)
    plan = {}
    for g, spec in GROUPS.items():
        opts = [{'label': 'obecny głos %s' % m, 'wav': os.path.join(ROOT, r[m]['wav']), 'text': r[m]['text'], 'member': m}
                for m in spec['members'] if m in r]
        opts += [{'label': 'kandydat rundy 1 %s (%s, ziarno %d)' % (n, r1[n]['instruct'], r1[n]['seed']),
                  'wav': os.path.join(paths.WORK, r1[n]['wav']), 'text': r1[n]['text'], 'scan': n} for n in spec['r1']]
        lines = sorted({glines[m]['fragment']: glines[m] for m in spec['members'] if m in glines}.values(),
                       key=lambda x: -len(x['text']))[:2]
        plan[g] = {'title': spec['title'], 'members': spec['members'], 'options': opts, 'lines': lines}
        print('%-8s opcje %d, kwestie %d' % (g, len(opts), len(lines)))
    save('groups.json', plan)


def group_lines():
    """Każda opcja grupy czyta kwestie grupy (środowisko OmniVoice)."""
    import torch
    import npc_voices as N
    from lektor import synth
    plan = load('groups.json')
    model = N.load_omnivoice()
    os.makedirs(os.path.join(OUT, 'grupy'), exist_ok=True)
    todo = []
    for g, spec in plan.items():
        for k, o in enumerate(spec['options'], 1):
            prompt = None
            for i, line in enumerate(spec['lines'], 1):
                wav = os.path.join(OUT, 'grupy', '%s_%d_%d.wav' % (g, k, i))
                if os.path.exists(wav):
                    continue
                prompt = prompt or model.create_voice_clone_prompt(o['wav'], o['text'])
                todo.append((wav, line, prompt))
    model.audio_tokenizer.to('cpu')        # jak lektor.synth: bez spadania do pamięci systemowej
    torch.cuda.empty_cache()
    model._generate_iterative = synth.generate_iterative_unpadded.__get__(model)
    for wav, line, prompt in todo:
        N.synth(model, wav, line['text'], synth.seed_for(line['fragment'], 1), voice_clone_prompt=prompt,
                **({'speed': line['speed']} if line['speed'] else {}))


def group_page():
    import soundfile as sf
    import cast_sheet
    from lektor import finalize
    plan = load('groups.json')
    desc = cast_sheet.descriptions()[0]
    e = html.escape
    os.makedirs(os.path.join(OUT, 'grupy_poziom'), exist_ok=True)
    body = ''
    for g, spec in plan.items():
        quotes = ''.join('<q>%d. %s</q>' % (i, e(x['text'])) for i, x in enumerate(spec['lines'], 1))
        who = ''.join('<li><code>%s</code> %s</li>' % (e(m), e(desc.get(m, '–'))) for m in spec['members'])
        opts = ''
        for k, o in enumerate(spec['options'], 1):
            auds = ''
            for i in range(1, len(spec['lines']) + 1):
                src = os.path.join(OUT, 'grupy', '%s_%d_%d.wav' % (g, k, i))
                if os.path.exists(src):
                    y, sr = sf.read(src, dtype='float32')
                    sf.write(os.path.join(OUT, 'grupy_poziom', os.path.basename(src)),
                             finalize.level(finalize.trim(y, sr), sr)[0], sr, subtype='PCM_16')
                    auds += '<div class="lab">kwestia %d</div><audio controls preload="none" src="grupy_poziom/%s"></audio>' % (
                        i, os.path.basename(src))
            opts += ('<div class="cand" data-l="%d"><label><input type="radio" name="%s" value="%d"> <b>%d</b></label> '
                     '<span class="muted">%s</span>%s<label class="gray"><input type="checkbox" class="bad"> niepoprawna</label>'
                     '<textarea placeholder="Co jest nie tak z opcją %d?"></textarea></div>') % (k, g, k, k, e(o['label']), auds, k)
        body += ('<div class="card" data-voice="%s"><h2>%s</h2><div class="muted">Członkowie grupy, każdy dostanie wybrany '
                 'głos:</div><ul>%s</ul><div class="muted">Kwestie z gry czytane przez każdą opcję:</div>%s'
                 '<div class="row">%s</div><div class="pick"><b>Wybór:</b> numer opcji powyżej · '
                 '<label><input type="radio" name="%s" value="0"> żadna nie pasuje</label></div>'
                 '<textarea class="note" placeholder="Uwaga do grupy (opcjonalnie)"></textarea></div>') % (
            e(g), e(spec['title']), who, quotes, opts, e(g))
    doc = ('<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,'
           'initial-scale=1"><title>Grupy wrogów E20</title><style>%s</style></head><body><h1>Grupy wrogów E20: jeden głos '
           'na typ wroga</h1><p class="muted">Opcje to obecne głosy członków grupy i kandydaci z rundy 1 bez obróbki. Każda '
           'opcja czyta te same kwestie z gry (wyrównane do −20 LUFS). Wybierz numer opcji, możesz oznaczyć opcję jako '
           'niepoprawną z uwagą. Na końcu „Kopiuj wybór” i wklej do czatu.</p><p class="muted" id="cnt"></p>%s'
           '<p><button onclick="copyList()">Kopiuj wybór</button></p><div id="out"></div>%s</body></html>') % (
        CSS, body, GROUP_SCRIPT)
    open(os.path.join(OUT, 'grupy.html'), 'w', encoding='utf-8').write(doc)
    print('strona: %s' % os.path.join(OUT, 'grupy.html'))


GROUP_SCRIPT = r"""
<script>
const KEY='recast-e20-grupy';
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
const st=load();function put(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){};count()}
function get(v){return st[v]=st[v]||{pick:'',bad:{},note:''}}
function count(){const c=[...document.querySelectorAll('.card')];
 document.getElementById('cnt').textContent='wybrano: '+c.filter(x=>get(x.dataset.voice).pick).length+' / '+c.length}
document.querySelectorAll('.card').forEach(card=>{const v=card.dataset.voice,s=get(v);
 const mark=()=>card.querySelectorAll('.cand').forEach(c=>c.classList.toggle('sel',c.dataset.l===s.pick));
 card.querySelectorAll('input[type=radio]').forEach(r=>{r.checked=s.pick===r.value;r.addEventListener('change',()=>{s.pick=r.value;mark();put()})});
 card.querySelectorAll('.cand').forEach(c=>{const L=c.dataset.l,cb=c.querySelector('input.bad'),ta=c.querySelector('textarea');
  const b=s.bad[L];cb.checked=!!b;ta.value=(b&&b.note)||'';c.classList.toggle('bad',cb.checked);
  cb.addEventListener('change',()=>{if(cb.checked)s.bad[L]={note:ta.value};else delete s.bad[L];c.classList.toggle('bad',cb.checked);put()});
  ta.addEventListener('input',()=>{s.bad[L]={note:ta.value};put()})});
 const note=card.querySelector('textarea.note');note.value=s.note||'';note.addEventListener('input',()=>{s.note=note.value;put()});mark()});
document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})));
function copyList(){const lines=[];document.querySelectorAll('.card').forEach(c=>{const v=c.dataset.voice,s=get(v);
 let t=v+'='+(s.pick||'?')+(s.pick==='0'?' (żadna nie pasuje)':'');if((s.note||'').trim())t+=' — '+s.note.trim().replace(/\s+/g,' ');lines.push(t);
 Object.entries(s.bad||{}).sort().forEach(([L,b])=>lines.push('  '+L+' niepoprawna'+((b.note||'').trim()?': '+b.note.trim().replace(/\s+/g,' '):'')))});
 const t='Grupy wrogów E20:\n'+lines.join('\n');document.getElementById('out').textContent=t;try{navigator.clipboard.writeText(t)}catch(e){}}
count();
</script>"""


def group_adopt(args):
    """grupa=numer opcji: każdy członek grupy dostaje tę samą referencję (styl obecnego głosu idzie z nim)."""
    import soundfile as sf
    plan = load('groups.json')
    path = os.path.join(paths.REFS, 'refs.json')
    r = refs()
    for arg in args:
        g, k = arg.split('=')
        if k == '0':
            continue
        o = plan[g]['options'][int(k) - 1]
        style = (r.get(o['member']) or {}).get('style') if o.get('member') else None
        src = os.path.join(OUT, 'grupy_zrodlo.wav')
        shutil.copyfile(o['wav'], src)          # źródło może być referencją jednego z członków
        for m in plan[g]['members']:
            wav = os.path.join(paths.REFS, m + '.wav')
            shutil.copyfile(src, wav)
            entry = {'wav': paths.rel(wav), 'text': o['text'], 'seconds': round(sf.info(wav).duration, 2),
                     'source': 'E20 (D114): wspólny głos grupy %s, opcja %s: %s' % (g, k, o['label']),
                     'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
            if style:
                entry['style'] = style
            r[m] = entry
            print('%-26s %s=%s %5.1f s' % (m, g, k, entry['seconds']))
    json.dump(r, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    argv = [a for i, a in enumerate(sys.argv) if a != '--round' and (i == 0 or sys.argv[i - 1] != '--round')]
    cmd = argv[1] if len(argv) > 1 else ''
    if cmd in ('adopt', 'group-adopt'):
        (adopt if cmd == 'adopt' else group_adopt)(argv[2:])
    elif cmd in ('design', 'choose', 'lines', 'page', 'group-plan', 'group-lines', 'group-page'):
        globals()[cmd.replace('-', '_')]()
    else:
        raise SystemExit(__doc__)
