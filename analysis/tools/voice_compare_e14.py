"""Arkusz obsady E14 (D83): nowe postacie bez dubbingu w ElevenLabs i OmniVoice, złoczyńcy z okrzyków w OmniVoice.

Kroki (z katalogu głównego; <omni> = "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"):
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py portrait   # portrety z kopii gry, imiona postaci
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py context    # kwestie postaci do opisu (plik w work/)
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py pick       # 2 losowe fragmenty na postać, koszt
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py refs       # referencje złoczyńców z dubbingu (Whisper)
    <omni> -I analysis/tools/voice_compare_e14.py design                    # projekty OmniVoice: opis × ziarno
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py choose     # najlepsze ziarno (ASR, F0)
    <omni> -I analysis/tools/voice_compare_e14.py clone                     # oba fragmenty głosem OmniVoice
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py status     # które próbki ElevenLabs już są
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py score      # automat E3 dla wszystkich próbek
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet      # strony arkusza z szablonu voice_compare.html
Runda 2 (uwagi z arkusza, D84): podglądy `el2` przez MCP do …/<głos>/design2/, potem
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py refs2      # referencje wariantów złoczyńców
    <omni> -I analysis/tools/voice_compare_e14.py clone2                    # klony wariantów
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py score      # ocenia też rundę 2
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet2     # strony r2n, r2z, r2w i runda2.html

Opisy głosów są w voice_designs_e14.json. Próbki ElevenLabs powstają przez MCP (skill `elevenlabs`):
text_to_voice z opisem `el` i tekstem `<głos>#design` z lines.json do analysis/work/elevenlabs/audio/e14/<głos>/design/,
create_voice_from_preview z najlepszego podglądu (`status` go wskazuje), potem text_to_speech eleven_v4 drugiego fragmentu
do analysis/work/elevenlabs/audio/e14/<głos>/v4/. Wyniki w analysis/work/compare/e14/ (nieśledzone).
Na konsolę trafiają same liczby i identyfikatory, bez tekstów gry.
"""
import glob
import json
import os
import random
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lektor import paths  # noqa: E402

WORK = os.path.join(ROOT, 'analysis', 'work')
OUT = os.path.join(WORK, 'compare', 'e14')
OMNI = os.path.join(OUT, 'omni')
EL_AUDIO = os.path.join(WORK, 'elevenlabs', 'audio', 'e14')
DB = os.path.join(WORK, 'lektor', 'm3.sqlite')
M2_DB = os.path.join(WORK, 'lektor', 'm2.sqlite')
M2_AUDIO = os.path.join(WORK, 'audio', 'm2')
DESIGNS = os.path.join(ROOT, 'analysis', 'tools', 'voice_designs_e14.json')
SEED = 20261108
MIN_WORDS = 7
MAX_CHARS = 220             # drugi fragment (eleven_v4) i fragmenty złoczyńców
DESIGN_CHARS = (100, 320)   # text_to_voice wymaga 100–1000 znaków; pierwszy fragment czyta podgląd projektu
DESIGN_RATE, V4_RATE = 1.0, 0.44
SEEDS = (5, 17, 29)
MAX_CER = 0.10
F0_RANGE = {'female': (140, 330), 'male': (65, 190)}
GAP_S = 0.5

# Głos → identyfikatory mówcy (scope.M3_VOICES). Nowe postacie: projekt ElevenLabs i OmniVoice (D83).
NEW = {'magrit': ('BARONESSMAGRIT',), 'alys': ('ALYS',), 'greigory': ('GREIGORY',), 'button': ('BUTTON',),
       'laurel': ('LAUREL',), 'arden': ('ARDEN',), 'veta': ('VETA',), 'trevalyn': ('TREVALYN',),
       'balthain': ('SIRBALTHAIN',), 'ducard': ('COUNTESSDUCARD',), 'waiqar': ('WAIQAR',), 'morant': ('MORANT',),
       'pryor': ('PRYOR',), 'delphyndra': ('DELPHYNDRA',), 'nara': ('NARA',), 'grace': ('GRACE',), 'meza': ('MEZA',),
       'drys': ('DRYS',)}
# Złoczyńcy z okrzykami w dubbingu: klon OmniVoice (QA E14). Źródło referencji: lektor monologu, inaczej okrzyki.
VILLAINS = {'zachareth': ('BARONZACHARETH',), 'reneyr': ('RENEYR', 'SHADOW_RENEYR'), 'levirax': ('LEVIRAX',),
            'greysdon': ('GREYSDON',), 'navoth': ('NAVOTH',), 'vraskhar': ('VRASKHAR',),
            'gilliam': ('GILLIAM', 'GILLIAM_EVIL')}
TEXTURES = {'drys': 'Drys_Dialogue.png'}   # postać bez wpisu w storymessagecharacters, sam portret
VILLAIN_SOURCES = {'zachareth': ('DLE04_4_Betrayal_Zachareth_VoiceOver.wav',), 'reneyr': ('DLE04_4_Betrayal_Reneyr_VoiceOver.wav',),
                   'levirax': ('Levirax_VoiceOver.wav',), 'greysdon': ('Greysdon_Spawn_2.wav', 'Greysdon_Spawn_1.wav')}
MIX_GAP_S = 0.3
MAX_REF_S = 10.0
# Głosy już w obsadzie (do porównania, bez ocen): ElevenLabs z E13 i klony złoczyńców z dubbingu.
CHOSEN = ('adelynn', 'ronan', 'astarra', 'kathryn', 'ltrand', 'bruli', 'herbie', 'mok', 'outlaw', 'flint', 'galgoraz',
          'nekrul', 'xenith')
SHEETS = (('n1', 'Nowe postacie (1)', tuple(NEW)[:6]), ('n2', 'Nowe postacie (2)', tuple(NEW)[6:12]),
          ('n3', 'Nowe postacie (3)', tuple(NEW)[12:]), ('z1', 'Złoczyńcy z dubbingu', tuple(VILLAINS)),
          ('w1', 'Głosy już w obsadzie', CHOSEN))


def load_json(path, default=None):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def speakers():
    return {**NEW, **VILLAINS}


# --- portrety i kontekst ---------------------------------------------------------------------------------------------

def portrait():
    """Portrety z okna dialogu (d3/storymessagecharacters) i imiona postaci z lokalizacji."""
    import UnityPy
    from lektor import game as G
    g = G.Game()
    terms = g.terms()
    env = UnityPy.load(os.path.join(paths.BUNDLES, g.files['d3/storymessagecharacters']))
    chars, textures = {}, {}
    for o in env.objects:
        if o.type.name == 'MonoBehaviour':
            t = o.read_typetree()
            if str(t.get('_id', '')).startswith('STORY_CHARACTER_'):
                chars[t['_id'][16:]] = t
        elif o.type.name == 'Texture2D':
            textures.setdefault(o.read().m_Name, o)
    names = {}
    os.makedirs(os.path.join(OUT, 'portraits'), exist_ok=True)
    for voice, ids in speakers().items():
        n = 0
        for sid in ids:
            c = chars.get(sid) or {'KeyName': 'NPC_NAME_' + sid, 'TextureAssetPathDefault': TEXTURES.get(voice, '')}
            names.setdefault(voice, (terms.get(c['KeyName']) or {}).get('text') or voice)
            tex = os.path.splitext(os.path.basename(c['TextureAssetPathDefault']))[0]
            if tex in textures:
                n += 1
                textures[tex].read().image.save(os.path.join(OUT, 'portraits', '%s%s.png' % (voice, '' if n == 1 else '_%d' % n)))
        print('%-10s portrety %d' % (voice, n))
    save_json(os.path.join(OUT, 'names.json'), names)


def context(limit=14):
    """Kwestie każdej postaci (losowa próbka) i misje, w których mówi: materiał do opisu głosu, tylko w work/."""
    con = sqlite3.connect(DB)
    rng = random.Random(SEED)
    out = []
    for voice in speakers():
        rows = con.execute("select grp, text_norm from lines where voice = ? and tts = 1 and category = 'dialog'",
                           (voice,)).fetchall()
        groups = sorted({g for g, _ in rows})
        out.append('## %s (%d kwestii, %d znaków; %s)\n' % (voice, len(rows), sum(len(t) for _, t in rows),
                                                              ', '.join(groups)))
        out += ['- %s' % t for _, t in rng.sample(rows, min(limit, len(rows)))] + ['']
        print('%-10s kwestie %4d, grupy %d' % (voice, len(rows), len(groups)))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'context.md'), 'w', encoding='utf-8').write('\n'.join(out))


# --- losowanie fragmentów --------------------------------------------------------------------------------------------

def fragments(con, voice):
    rows = con.execute("""select distinct f.id, f.text, f.speed from fragments f join segments s on s.fragment = f.id
                          join lines l on l.key = s.key where f.voice = ? and f.kind = 'text' and l.category = 'dialog'
                          order by f.id""", (voice,)).fetchall()
    return [{'fragment': i, 'text': t, 'speed': sp, 'chars': len(t)} for i, t, sp in rows if len(t.split()) >= MIN_WORDS]


def chosen_lines(manifest, con, voice):
    """Dwa fragmenty z gotowym audio M2 (bez problemów automatu) dla głosu już w obsadzie."""
    rows = con.execute("select id, text from fragments where voice = ? and kind = 'text' order by id", (voice,)).fetchall()
    ok = [(i, t) for i, t in rows if i in manifest and len(t.split()) >= MIN_WORDS and len(t) <= MAX_CHARS]
    clean = [r for r in ok if not manifest[r[0]]['problems']] or ok
    two = random.Random('%d-%s' % (SEED, voice)).sample(clean, min(2, len(clean)))
    return [{'fragment': i, 'text': t, 'chars': len(t), 'file': os.path.join(M2_AUDIO, manifest[i]['file'])} for i, t in two]


def pick():
    con = sqlite3.connect(DB)
    out = {}
    for voice in speakers():
        rng = random.Random('%d-%s' % (SEED, voice))
        pool = fragments(con, voice)
        short = [f for f in pool if f['chars'] <= MAX_CHARS]
        first = [f for f in pool if DESIGN_CHARS[0] <= f['chars'] <= DESIGN_CHARS[1]] if voice in NEW else short
        if not first or len(short) < 2:
            raise SystemExit('%s: za mało fragmentów (%d)' % (voice, len(pool)))
        a = rng.choice(first)
        b = rng.choice([f for f in short if f['fragment'] != a['fragment']])
        out[voice] = [a, b]
        if voice in NEW:
            out[voice + '#design'] = a['text']
    m2 = sqlite3.connect(M2_DB)
    manifest = load_json(os.path.join(M2_AUDIO, 'manifest.json'))['fragments']
    for voice in CHOSEN:
        out[voice] = chosen_lines(manifest, m2, voice)
    save_json(os.path.join(OUT, 'lines.json'), {'seed': SEED, 'lines': out})
    design = sum(len(out[v + '#design']) for v in NEW)
    v4 = sum(out[v][1]['chars'] for v in NEW)
    print('głos        znaki 1  znaki 2')
    for v in speakers():
        print('%-11s %7d %8d' % (v, out[v][0]['chars'], out[v][1]['chars']))
    print('\nszacunek kredytów: text_to_voice %.0f (%d znaków) + eleven_v4 %.0f (%d znaków) = %.0f' % (
        design * DESIGN_RATE, design, v4 * V4_RATE, v4, design * DESIGN_RATE + v4 * V4_RATE))


# --- OmniVoice -------------------------------------------------------------------------------------------------------

def refs():
    """Referencje złoczyńców do 10 s z transkrypcją (cięcie na granicy słów jak lektor.refs, D33)."""
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from transformers import pipeline
    from lektor.refs import cut_span
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    clips = {c['name']: os.path.join(ROOT, 'analysis', c['wav']) for c in load_json(os.path.join(paths.VOICES, 'analysis.json'))}
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', dtype=torch.float16, device='cuda')
    path = os.path.join(OMNI, 'refs.json')
    out = load_json(path, {})
    os.makedirs(os.path.join(OMNI, 'refs'), exist_ok=True)
    for voice in VILLAINS:
        names = VILLAIN_SOURCES.get(voice)
        src = os.path.join(paths.VOICES, 'refs', voice + '.wav')     # okrzyki Spawn z extract_voices.py
        if names and len(names) == 1:
            src = clips[names[0]]
        elif names:                                                   # kilka okrzyków sklejonych krótką ciszą
            parts, sr = [], None
            for n in names:
                y, sr = sf.read(clips[n], dtype='float32')
                parts += [y.mean(axis=1) if y.ndim > 1 else y, np.zeros(int(MIX_GAP_S * sr), np.float32)]
            src = os.path.join(OMNI, 'refs', voice + '_zrodlo.wav')
            sf.write(src, np.concatenate(parts[:-1]), sr, subtype='PCM_16')
        y16, _ = librosa.load(src, sr=16000, mono=True)
        chunks = asr({'raw': y16, 'sampling_rate': 16000}, return_timestamps='word',
                     generate_kwargs={'language': 'polish', 'task': 'transcribe'})['chunks']
        words = [(c['text'], c['timestamp'][0], c['timestamp'][1] or c['timestamp'][0]) for c in chunks]
        total = len(y16) / 16000
        # Okrzyki krótsze niż 10 s bierzemy w całości; tniemy tylko długi monolog (D33).
        first, last, start, end = cut_span(words, total) if total > MAX_REF_S else (0, len(words) - 1, 0.0, total)
        y, sr = sf.read(src, dtype='float32')
        y = (y.mean(axis=1) if y.ndim > 1 else y)[int(start * sr):int(end * sr)]
        fade = int(0.02 * sr)
        y[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        y[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
        wav = os.path.join(OMNI, 'refs', voice + '.wav')
        sf.write(wav, y, sr, subtype='PCM_16')
        out[voice] = {'wav': paths.rel(wav), 'text': ''.join(w[0] for w in words[first:last + 1]).strip(),
                      'seconds': round(len(y) / sr, 2), 'source': '%s @ %.2f–%.2f s' % (os.path.basename(src), start, end)}
        print('%-10s %.1f s, słów %d (%s)' % (voice, out[voice]['seconds'], last + 1 - first, os.path.basename(src)))
    save_json(path, out)


def design():
    """Kandydaci OmniVoice nowych postaci: opis (płeć, wiek, wysokość) i zdanie w stylu postaci, trzy ziarna."""
    import npc_voices as N
    specs = load_json(DESIGNS)
    model = N.load_omnivoice()
    N.tokenizer_to_cpu(model)
    os.makedirs(os.path.join(OMNI, 'scan'), exist_ok=True)
    path = os.path.join(OMNI, 'scan.json')
    out = load_json(path, {})
    for voice in NEW:
        o = specs[voice]['omni']
        for seed in SEEDS:
            name = '%s_s%d' % (voice, seed)
            wav = os.path.join(OMNI, 'scan', name + '.wav')
            if not os.path.exists(wav):
                N.synth(model, wav, o['style_text'], seed, instruct=o['instruct'],
                        duration=round(len(o['style_text']) / o['ref_cps'], 2))
            out[name] = {'voice': voice, 'seed': seed, 'instruct': o['instruct'], 'wav': paths.rel(wav),
                         'text': o['style_text']}
            save_json(path, out)


def choose():
    """Ziarno z najmniejszym CER i wysokością w zakresie płci (jak npc_voices select, bez wyboru kilku barw)."""
    import librosa
    import numpy as np
    import npc_voices as N
    specs = load_json(DESIGNS)
    cands = load_json(os.path.join(OMNI, 'scan.json'))
    asr = N.load_asr()
    for name, c in cands.items():
        y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=16000)
        gender = specs[c['voice']]['gender']
        c['cer'] = round(N.cer(c['text'], asr({'raw': y, 'sampling_rate': 16000}, generate_kwargs={'language': 'polish'})['text']), 3)
        c['f0'] = round(float(np.nanmedian(librosa.pyin(y, fmin=60, fmax=250 if gender == 'male' else 500, sr=16000)[0])), 0)
    refs_ = load_json(os.path.join(OMNI, 'refs.json'), {})
    for voice in NEW:
        lo, hi = F0_RANGE[specs[voice]['gender']]
        mine = sorted((n for n, c in cands.items() if c['voice'] == voice), key=lambda n: (
            not (cands[n]['cer'] <= MAX_CER and lo <= cands[n]['f0'] <= hi), cands[n]['cer']))
        best = cands[mine[0]]
        refs_[voice] = {'wav': best['wav'], 'text': best['text'], 'source': 'projekt: %s, ziarno %d' % (best['instruct'], best['seed']),
                        'cer': best['cer'], 'f0': best['f0']}
        print('%-10s %s' % (voice, '  '.join('s%d CER %.2f F0 %3.0f%s' % (cands[n]['seed'], cands[n]['cer'], cands[n]['f0'],
                                                                           '*' if n == mine[0] else ' ') for n in sorted(mine))))
    save_json(os.path.join(OMNI, 'scan.json'), cands)
    save_json(os.path.join(OMNI, 'refs.json'), refs_)


def clone():
    """Oba fragmenty każdej postaci głosem OmniVoice, w tempie z bazy m3 (D34), ziarno jak w npc_voices."""
    import npc_voices as N
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    refs_ = load_json(os.path.join(OMNI, 'refs.json'))
    model = N.load_omnivoice()
    voices = [v for v in speakers() if v in refs_]
    prompts = {v: model.create_voice_clone_prompt(os.path.join(ROOT, refs_[v]['wav']), refs_[v]['text']) for v in voices}
    N.tokenizer_to_cpu(model)
    os.makedirs(os.path.join(OMNI, 'clips'), exist_ok=True)
    for voice in voices:
        for i, f in enumerate(lines[voice], 1):
            wav = os.path.join(OMNI, 'clips', '%s_%d.wav' % (voice, i))
            if not os.path.exists(wav):
                kw = {'speed': f['speed']} if f.get('speed') else {}
                N.synth(model, wav, f['text'], 1234, voice_clone_prompt=prompts[voice], **kw)


# --- runda 2 (QA 2026-11-08) -----------------------------------------------------------------------------------------
# Postacie bez dubbingu tylko w ElevenLabs (D84). Nowy opis `el2` dla postaci z uwagą; podgląd czyta oba fragmenty
# (Meza: pierwszy, bo drugi go powtarza). Złoczyńcy z uwagą: dwa wyraźnie różne warianty klonu OmniVoice.
R2_EL = ('waiqar', 'morant', 'delphyndra', 'nara', 'meza')
R2_FIRST_ONLY = ('meza',)
R2_VILLAINS = {
    'levirax': (('levirax_v2a', 'monolog jak w rundzie 1, tempo 0,85 (dłuższe końcówki)', {'tempo': 0.85}),
                ('levirax_v2b', 'okrzyki Spawn 2 i Defend 2–3 (spokojniejsze, syczące), tempo 0,85',
                 {'clips': ('Levirax_Spawn_2.wav', 'Levirax_Defend_3.wav', 'Levirax_Defend_2.wav'), 'tempo': 0.85})),
    'gilliam': (('gilliam_v2a', 'okrzyki Defend 3, Defeat 2 i Defend 2 (obrona i porażka)',
                 {'clips': ('Gilliam_Defend_3.wav', 'Gilliam_Defeat_2.wav', 'Gilliam_Defend_2.wav')}),
                ('gilliam_v2b', 'referencja z rundy 1 z drżeniem (strach)', {'tremble': 0.6})),
}
R2_SHEETS = (('r2n', 'Runda 2: nowe warianty ElevenLabs', R2_EL), ('r2z', 'Runda 2: warianty złoczyńców', tuple(R2_VILLAINS)),
             ('r2w', 'Głosy już w obsadzie', None))
R2_ACCEPTED_VILLAINS = ('zachareth', 'reneyr', 'greysdon', 'navoth', 'vraskhar')


def r2_text(lines, voice):
    return lines[voice + '#design'] if voice in R2_FIRST_ONLY else ' '.join(f['text'] for f in lines[voice])


def refs2():
    """Referencje wariantów złoczyńców: okrzyki sklejone z transkrypcją Whispera albo referencja z rundy 1 z drżeniem."""
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from transformers import pipeline
    import npc_voices as N
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    clips = {c['name']: os.path.join(ROOT, 'analysis', c['wav']) for c in load_json(os.path.join(paths.VOICES, 'analysis.json'))}
    r1 = load_json(os.path.join(OMNI, 'refs.json'))
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', dtype=torch.float16, device='cuda')
    out = {}
    for voice, variants in R2_VILLAINS.items():
        for name, label, opt in variants:
            wav = os.path.join(OMNI, 'refs', name + '.wav')
            if 'clips' in opt:
                parts, sr = [], None
                for n in opt['clips']:
                    y, sr = sf.read(clips[n], dtype='float32')
                    parts += [y.mean(axis=1) if y.ndim > 1 else y, np.zeros(int(MIX_GAP_S * sr), np.float32)]
                sf.write(wav, np.concatenate(parts[:-1]), sr, subtype='PCM_16')
                y16, _ = librosa.load(wav, sr=16000, mono=True)
                text = asr({'raw': y16, 'sampling_rate': 16000}, generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text'].strip()
            else:
                y, sr = sf.read(os.path.join(ROOT, r1[voice]['wav']), dtype='float32')
                if opt.get('tremble'):
                    y = N.tremble(y, sr, opt['tremble'])
                sf.write(wav, y, sr, subtype='PCM_16')
                text = r1[voice]['text']
            out[name] = {'voice': voice, 'label': label, 'wav': paths.rel(wav), 'text': text,
                         'tempo': opt.get('tempo', 1.0), 'seconds': round(sf.info(wav).duration, 2)}
            print('%-12s %.1f s, słów %d' % (name, out[name]['seconds'], len(text.split())))
    save_json(os.path.join(OMNI, 'refs2.json'), out)


def clone2():
    import npc_voices as N
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    refs_ = load_json(os.path.join(OMNI, 'refs2.json'))
    model = N.load_omnivoice()
    prompts = {n: model.create_voice_clone_prompt(os.path.join(ROOT, r['wav']), r['text']) for n, r in refs_.items()}
    N.tokenizer_to_cpu(model)
    for name, r in refs_.items():
        for i, f in enumerate(lines[r['voice']], 1):
            wav = os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i))
            if not os.path.exists(wav):
                speed = (f.get('speed') or 1.0) * r['tempo']
                N.synth(model, wav, f['text'], 1234, voice_clone_prompt=prompts[name], **({'speed': speed} if speed != 1.0 else {}))


def el_previews2(voice):
    return sorted(glob.glob(os.path.join(EL_AUDIO, voice, 'design2', '*.mp3')))


def best_preview2(scores, voice):
    cands = [(f, scores.get('%s|preview2|%s' % (voice, os.path.basename(f)))) for f in el_previews2(voice)]
    cands = [(f, s) for f, s in cands if s and 'cer' in s]
    return min(cands, key=lambda c: (bool(c[1].get('tail_cut')), c[1].get('missing', 0) >= 2, c[1]['cer']), default=None)


def items2():
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    out = [('%s|preview2|%s' % (v, os.path.basename(f)), v, f, r2_text(lines, v)) for v in R2_EL for f in el_previews2(v)]
    for name, r in load_json(os.path.join(OMNI, 'refs2.json'), {}).items():
        for i, f in enumerate(lines[r['voice']], 1):
            wav = os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i))
            if os.path.exists(wav):
                out.append(('%s|%s|%d' % (r['voice'], name, i), r['voice'], wav, f['text']))
    return out


def sheet2():
    """Strony rundy 2: nowy wariant obok odrzuconego, warianty złoczyńców i wszystkie głosy już w obsadzie."""
    import html as H
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    from voice_compare import NAMES
    names.update({v: NAMES[v] for v in CHOSEN if v in NAMES})
    refs1, refs2_ = load_json(os.path.join(OMNI, 'refs.json')), load_json(os.path.join(OMNI, 'refs2.json'), {})
    pages = []
    for page, title, voices in R2_SHEETS:
        out = []
        if page == 'r2n':
            for v in voices:
                best1, best2 = best_preview(scores, v), best_preview2(scores, v)
                clips = [{'id': 'orig', 'label': 'Runda 1 (wariant z uwagą)', 'kind': 'el1', 'files': [best1[0], el_v4(v)],
                          'metrics': merged(best1[1], scores.get(v + '|v4|2')), 'desc': specs[v]['el']}]
                if best2:
                    clips.append({'id': 'A', 'label': 'Runda 2: nowy opis (podgląd czyta oba fragmenty)', 'kind': 'el2',
                                  'files': [best2[0]], 'metrics': best2[1], 'desc': specs[v]['el2'],
                                  'voice_id': preview_id(best2[0])})
                out.append({'voice': v, 'kind': 'designed', 'clips': clips, 'decide': ['Nowy wariant', 'Runda 1', 'Jeszcze inny'],
                            'brief': '%s. Uwaga z rundy 1: %s.' % (specs[v]['brief'], specs[v]['qa1'])})
        elif page == 'r2z':
            for v in voices:
                clips = [{'id': 'orig', 'label': 'Oryginał z gry (dubbing, inny tekst)', 'kind': 'dubbing',
                          'files': [os.path.join(ROOT, refs1[v]['wav'])], 'metrics': {}, 'desc': 'referencja rundy 1: ' + refs1[v]['source']},
                         {'id': 'r1', 'label': 'Runda 1', 'kind': 'omni1', 'metrics': merged(scores.get(v + '|omni|1'), scores.get(v + '|omni|2')),
                          'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (v, i)) for i in (1, 2)]}]
                for (name, label, _), letter in zip(R2_VILLAINS[v], 'AB'):
                    clips.append({'id': letter, 'label': 'Wariant %s: %s' % (letter, label), 'kind': name,
                                  'metrics': merged(scores.get('%s|%s|1' % (v, name)), scores.get('%s|%s|2' % (v, name))),
                                  'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i)) for i in (1, 2)]})
                note = {'levirax': 'ma bardziej ciągnąć końcówki wyrazów, jak mowa gadów', 'gilliam': 'ma być bardziej przerażony'}[v]
                out.append({'voice': v, 'kind': 'dubbed', 'clips': clips, 'decide': ['Wariant A', 'Wariant B', 'Runda 1', 'Do poprawy'],
                            'brief': '%s. Uwaga z rundy 1: %s.' % (specs[v]['brief'], note)})
        else:
            for v in CHOSEN:
                out.append({'voice': v, 'kind': 'chosen', 'clips': [{'id': 'orig', 'kind': 'chosen', 'metrics': {},
                            'label': 'Obecny głos: ' + ('OmniVoice (klon z dubbingu)' if v in ('nekrul', 'xenith') else 'ElevenLabs (E13)'),
                            'files': [f['file'] for f in lines[v]]}]})
            for v in NEW:
                if v not in R2_EL:
                    best = best_preview(scores, v)
                    out.append({'voice': v, 'kind': 'chosen', 'clips': [{'id': 'orig', 'kind': 'chosen', 'metrics': {},
                                'label': 'Wybrany w rundzie 1: ElevenLabs', 'files': [best[0], el_v4(v)]}]})
            for v in R2_ACCEPTED_VILLAINS:
                out.append({'voice': v, 'kind': 'chosen', 'clips': [{'id': 'orig', 'kind': 'chosen', 'metrics': {},
                            'label': 'Wybrany w rundzie 1: OmniVoice (klon z dubbingu)',
                            'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (v, i)) for i in (1, 2)]}]})
        for entry in out:
            v = entry['voice']
            entry.update(name=names.get(v, v), portrait=portrait_rel(v), problems=[], lines=[f['text'] for f in lines[v]])
            entry.setdefault('brief', '')
            for c in entry['clips']:
                files = [f for f in c.pop('files') if f and os.path.exists(f)]
                c['file'] = glue(files, os.path.join(OUT, 'clips', page, '%s_%s.wav' % (v, c['id']))) if files else ''
            entry['clips'] = [c for c in entry['clips'] if c['file']]
        intro = {'r2n': 'Runda 1 to odrzucony wariant (podgląd i eleven_v4), dla porównania. Próbka A to nowy opis po Twojej '
                        'uwadze; podgląd projektu czyta oba fragmenty. Oceń próbkę A, odsłoń etykiety i wybierz wariant.',
                 'r2z': 'Oryginał z gry i klon z rundy 1 dla porównania. Warianty A i B to dwa różne sposoby poprawy według Twojej uwagi.',
                 'r2w': 'Wszystkie głosy już w obsadzie, także zaakceptowane w rundzie 1. Bez ocen.'}[page]
        pages.append({'page': page, 'title': title, 'intro': intro, 'voices': out,
                      'footer': 'Barwa wobec referencji: względem projektu OmniVoice (nowe postacie) albo dubbingu (złoczyńcy).'})
    template = open(os.path.join(ROOT, 'analysis', 'tools', 'voice_compare.html'), encoding='utf-8').read()
    nav = [{'page': p['page'], 'title': p['title'],
            'ratable': sum(c['id'] != 'orig' for v in p['voices'] for c in v['clips'])} for p in pages]
    index = {'title': 'E14 · Obsada, runda 2', 'file': 'e14r2_oceny.json', 'dir': 'analysis/work/compare/e14/',
             'intro': 'Nowe warianty głosów z uwagami z rundy 1: 5 postaci w ElevenLabs (r2n) i 2 złoczyńców w OmniVoice (r2z). '
                      'Strona r2w ma wszystkie głosy już w obsadzie.',
             'notes': ['Postacie bez dubbingu czyta tylko ElevenLabs (D84), więc runda 2 nie ma OmniVoice dla nowych postaci.',
                       'Nowy wariant zapiszemy na koncie po Twoim wyborze; eleven_v4 sprawdzi go automat w paczce postaci.']}
    for p in pages:
        body = json.dumps({'mode': 'page', 'stage': 'E14R2', 'data': p, 'nav': nav}, ensure_ascii=False).replace('</', '<\\/')
        open(os.path.join(OUT, p['page'] + '.html'), 'w', encoding='utf-8').write(
            template.replace('__TITLE__', H.escape('E14 · ' + p['title'])).replace('__DATA__', body))
    body = json.dumps({'mode': 'index', 'stage': 'E14R2', 'nav': nav, 'index': index}, ensure_ascii=False).replace('</', '<\\/')
    open(os.path.join(OUT, 'runda2.html'), 'w', encoding='utf-8').write(
        template.replace('__TITLE__', H.escape(index['title'])).replace('__DATA__', body).replace('href="index.html"', 'href="runda2.html"'))
    print('strony: %d, nagrania: %d -> %s' % (len(pages) + 1, sum(len(v['clips']) for p in pages for v in p['voices']),
                                               os.path.join(OUT, 'runda2.html')))


# --- ElevenLabs, ocena i arkusz ----------------------------------------------------------------------------------------

def el_previews(voice):
    return sorted(glob.glob(os.path.join(EL_AUDIO, voice, 'design', '*.mp3')))


def el_v4(voice):
    files = sorted(glob.glob(os.path.join(EL_AUDIO, voice, 'v4', '*.mp3')))
    return files[-1] if files else None


def preview_id(path):
    """Identyfikator podglądu z nazwy pliku zapisanej przez serwer MCP (voice_design_<id>_<n>_…)."""
    parts = os.path.basename(path).split('_')
    return parts[2] if len(parts) > 2 else None


def best_preview(scores, voice):
    cands = [(f, scores.get('%s|preview|%s' % (voice, os.path.basename(f)))) for f in el_previews(voice)]
    cands = [(f, s) for f, s in cands if s and 'cer' in s]
    return min(cands, key=lambda c: (bool(c[1].get('tail_cut')), c[1].get('missing', 0) >= 2, c[1]['cer']), default=None)


def status():
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    for voice in NEW:
        best = best_preview(scores, voice)
        print('%-10s podglądy %d  najlepszy %s  eleven_v4 %s' % (
            voice, len(el_previews(voice)), preview_id(best[0]) if best else '-', 'tak' if el_v4(voice) else 'nie'))


def items():
    """Nagrania do oceny automatem: (id, głos, plik, tekst)."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    out = []
    for voice in speakers():
        for i, f in enumerate(lines[voice], 1):
            wav = os.path.join(OMNI, 'clips', '%s_%d.wav' % (voice, i))
            if os.path.exists(wav):
                out.append(('%s|omni|%d' % (voice, i), voice, wav, f['text']))
        if voice in NEW:
            out += [('%s|preview|%s' % (voice, os.path.basename(f)), voice, f, lines[voice + '#design'])
                    for f in el_previews(voice)]
            if el_v4(voice):
                out.append(('%s|v4|2' % voice, voice, el_v4(voice), lines[voice][1]['text']))
    return out


def score():
    sys.path.insert(0, os.path.join(ROOT, 'analysis', 'tools', 'elevenlabs'))
    from lektor import evaluate
    from score_samples import median_f0
    path = os.path.join(OUT, 'scores.json')
    scores = load_json(path, {})
    todo = [t for t in items() + items2() if t[0] not in scores]
    if not todo:
        print('ocenione nagrania: %d' % len(scores))
        return
    # Barwa wobec referencji OmniVoice postaci (projekt albo klon z dubbingu), dla obu silników.
    scorer = evaluate.Scorer({**load_json(os.path.join(paths.REFS, 'refs.json')), **load_json(os.path.join(OMNI, 'refs.json'), {})})
    for sid, voice, f, text in todo:
        r = scorer(f, text, voice, 1.0)
        row = {k: (r[k].item() if hasattr(r[k], 'item') else r[k]) for k in
               ('cer', 'tail_cut', 'missing', 'sim', 'cps_ratio', 'pause', 'speech_s') if k in r}
        row['f0'] = median_f0(f)
        scores[sid] = row
        print(sid.split('|')[0], sid.split('|')[1], {k: row.get(k) for k in ('cer', 'tail_cut', 'sim', 'f0')}, flush=True)
        save_json(path, scores)
    print('ocenione nagrania: %d' % len(scores))


def glue(files, dst):
    """Fragmenty postaci sklejone w jedno nagranie z wyrównaną głośnością (jak arkusz E11)."""
    import librosa
    import numpy as np
    import soundfile as sf
    from lektor.finalize import level
    if not os.path.exists(dst):
        parts, sr = [], 44100
        for f in files:
            y, _ = librosa.load(f, sr=sr, mono=True)
            parts += [level(y, sr)[0], np.zeros(int(GAP_S * sr), np.float32)]
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        sf.write(dst, np.concatenate(parts[:-1]), sr, subtype='PCM_16')
    return os.path.relpath(dst, OUT).replace(os.sep, '/')


def merged(*rows):
    """Wyniki automatu dla sklejki: najgorszy CER i brak słów, ucięta końcówka w którymkolwiek fragmencie."""
    rows = [r for r in rows if r]
    if not rows:
        return {}
    out = {'cer': max(r['cer'] for r in rows), 'tail_cut': any(r.get('tail_cut') for r in rows),
           'missing': max(r.get('missing', 0) for r in rows), 'speech_s': sum(r.get('speech_s', 0) for r in rows)}
    sims = [r['sim'] for r in rows if r.get('sim') is not None]
    f0 = [r['f0'] for r in rows if r.get('f0')]
    if sims:
        out['sim'] = round(min(sims), 3)
    if f0:
        out['f0'] = round(sum(f0) / len(f0))
    return out


def portrait_rel(voice):
    return 'portraits/%s.png' % voice if os.path.exists(os.path.join(OUT, 'portraits', voice + '.png')) else None


def section(page, voice, lines, scores, specs, names):
    clips_dir = os.path.join(OUT, 'clips', page)
    spec = specs.get(voice, {})
    texts = [f['text'] for f in lines[voice]]
    entry = {'voice': voice, 'name': names.get(voice, voice), 'portrait': portrait_rel(voice), 'lines': texts,
             'problems': [], 'brief': spec.get('brief', '')}
    omni = [os.path.join(OMNI, 'clips', '%s_%d.wav' % (voice, i)) for i in (1, 2)]
    omni_metrics = merged(scores.get(voice + '|omni|1'), scores.get(voice + '|omni|2'))
    if voice in NEW:
        best = best_preview(scores, voice)
        clips = []
        if all(map(os.path.exists, omni)):
            clips.append({'label': 'OmniVoice (lokalnie)', 'kind': 'omnivoice', 'files': omni, 'metrics': omni_metrics,
                          'desc': 'opis: %s; zdanie w stylu postaci, ziarno z najmniejszym CER' % spec['omni']['instruct']})
        if best and el_v4(voice):
            clips.append({'label': 'ElevenLabs (projekt + eleven_v4)', 'kind': 'elevenlabs', 'files': [best[0], el_v4(voice)],
                          'metrics': merged(best[1], scores.get(voice + '|v4|2')), 'desc': spec['el'],
                          'voice_id': preview_id(best[0])})
        random.Random('%d-%s' % (SEED, voice)).shuffle(clips)
        for c, letter in zip(clips, 'AB'):
            c['id'] = letter
        entry.update(kind='designed', decide=['ElevenLabs', 'OmniVoice', 'Żaden: popraw opis'])
    elif voice in VILLAINS:
        ref = load_json(os.path.join(OMNI, 'refs.json'), {}).get(voice, {})
        clips = [{'id': 'orig', 'label': 'Oryginał z gry (dubbing, inny tekst)', 'kind': 'dubbing',
                  'files': [os.path.join(ROOT, ref['wav'])] if ref else [], 'metrics': {},
                  'desc': 'referencja: %s' % ref.get('source', '-')},
                 {'id': 'omni', 'label': 'OmniVoice (klon z dubbingu)', 'kind': 'omnivoice', 'files': omni, 'metrics': omni_metrics}]
        entry.update(kind='dubbed', decide=['OmniVoice', 'Do poprawy'])
    else:
        el = voice not in ('nekrul', 'xenith')
        clips = [{'id': 'orig', 'label': 'Obecny głos: %s' % ('ElevenLabs eleven_v4 (E13)' if el else 'OmniVoice (klon z dubbingu)'),
                  'kind': 'chosen', 'files': [f['file'] for f in lines[voice]], 'metrics': {}}]
        entry.update(kind='chosen')
    for c in clips:
        files = [f for f in c.pop('files') if f and os.path.exists(f)]
        c['file'] = glue(files, os.path.join(clips_dir, '%s_%s.wav' % (voice, c['id']))) if files else ''
    entry['clips'] = [c for c in clips if c['file']]
    return entry


def costs(lines):
    design = sum(len(lines[v + '#design']) for v in NEW)
    v4 = sum(lines[v][1]['chars'] for v in NEW)
    return {'design_chars': design, 'v4_chars': v4, 'credits': round(design * DESIGN_RATE + v4 * V4_RATE)}


def sheet():
    import html as H
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    names.update({'nekrul': "Ne'Krul", 'xenith': 'Xenith'})
    from voice_compare import NAMES
    names.update({v: NAMES[v] for v in CHOSEN if v in NAMES})
    intros = {
        'n': 'Każda postać ma jeden opis głosu (z portretu i kwestii). Próbki A i B czytają te same dwa losowe fragmenty: '
             'jedna to OmniVoice (lokalnie), druga ElevenLabs (podgląd projektu czyta fragment 1, eleven_v4 fragment 2). '
             'Kolejność jest losowa. Oceń dopasowanie do postaci i polszczyznę (1 = źle, 5 = bardzo dobrze), odsłoń etykiety, '
             'potem wybierz silnik dla postaci.',
        'z': 'Złoczyńcy mają w grze tylko okrzyki albo monolog. Oryginał to referencja z dubbingu (inny tekst), OmniVoice '
             'czyta dwa losowe fragmenty klonem tego głosu. Oceń podobieństwo i jakość.',
        'w': 'Głosy już w obsadzie, do porównania z nowymi: dwa fragmenty z gotowego audio M2. Bez ocen.'}
    footers = {'n': 'Barwa wobec referencji: względem projektu OmniVoice tej postaci, więc dla ElevenLabs mówi tylko, jak '
                    'daleko głos jest od wersji lokalnej. Wyniki automatu sklejki: gorszy z dwóch fragmentów.',
               'z': 'Barwa wobec referencji: względem wycinka z dubbingu, z którego powstał klon.',
               'w': 'Nagrania z wydania M2, bez ocen.'}
    pages = []
    for page, title, voices in SHEETS:
        data = {'page': page, 'title': title, 'intro': intros[page[0]], 'footer': footers[page[0]],
                'voices': [section(page, v, lines, scores, specs, names) for v in voices]}
        pages.append(data)
    save_json(os.path.join(OUT, 'sheet.json'), pages)
    template = open(os.path.join(ROOT, 'analysis', 'tools', 'voice_compare.html'), encoding='utf-8').read()
    nav = [{'page': p['page'], 'title': p['title'],
            'ratable': sum(c['id'] != 'orig' for v in p['voices'] for c in v['clips'])} for p in pages]
    c = costs(lines)
    notes = ['Próbki ElevenLabs: podgląd projektu (%d znaków) i eleven_v4 (%d znaków), szacunek %d kredytów. '
             'Każda postać ma zapisany głos „Lektor PL - <postać> E14” (miejsca na koncie); głosy odrzucone usuniemy po decyzji.'
             % (c['design_chars'], c['v4_chars'], c['credits']),
             'Złoczyńcy: Zachareth, Reneyr i Levirax mają referencję z monologu, pozostali z okrzyków (3–7 s), więc klon '
             'może brzmieć jak okrzyk.',
             'Ne’Krul i Xenith są już w obsadzie (strona w1).']
    notes += [specs[v]['el_note'] for v in NEW if specs[v].get('el_note')]
    index = {'title': 'E14 · Obsada nowych postaci', 'notes': notes,
             'intro': 'Arkusz rozstrzyga silnik i głos dla 18 nowych postaci bez dubbingu (ElevenLabs albo OmniVoice) '
                      'oraz klony 7 złoczyńców z okrzyków. Strony n1–n3: nowe postacie (na ślepo, A/B). Strona z1: złoczyńcy. '
                      'Strona w1: głosy już w obsadzie do porównania.',
             'file': 'e14_oceny.json', 'dir': 'analysis/work/compare/e14/'}
    for p in pages:
        body = json.dumps({'mode': 'page', 'stage': 'E14', 'data': p, 'nav': nav}, ensure_ascii=False).replace('</', '<\\/')
        open(os.path.join(OUT, p['page'] + '.html'), 'w', encoding='utf-8').write(
            template.replace('__TITLE__', H.escape('E14 · ' + p['title'])).replace('__DATA__', body))
    body = json.dumps({'mode': 'index', 'stage': 'E14', 'nav': nav, 'index': index}, ensure_ascii=False).replace('</', '<\\/')
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(
        template.replace('__TITLE__', H.escape(index['title'])).replace('__DATA__', body))
    clips = sum(len(v['clips']) for p in pages for v in p['voices'])
    print('strony: %d, nagrania: %d -> %s' % (len(pages) + 1, clips, os.path.join(OUT, 'index.html')))


if __name__ == '__main__':
    commands = {'portrait': portrait, 'context': context, 'pick': pick, 'refs': refs, 'design': design, 'choose': choose,
                'clone': clone, 'status': status, 'score': score, 'sheet': sheet, 'refs2': refs2, 'clone2': clone2,
                'sheet2': sheet2}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    commands[sys.argv[1]]()
