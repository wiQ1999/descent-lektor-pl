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
Runda 3 (D87): trzy opisy `el3` (a, b, c) przez MCP do …/<głos>/design3<a|b|c>/, potem `score` i
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet3     # strony r3n, r3w i runda3.html
Runda 4 (D88): pięć opisów `el4` (a–e) Delphyndry do …/delphyndra/design4<a–e>/, potem `score` i
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet4     # strona r4n i runda4.html
Runda 5 (D89): pięć opisów `el5` do …/delphyndra/design5<a–e>/, potem `score`, `fx5` (efekt smoka), znowu `score` i
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet5     # strona r5n i runda5.html
Runda 6 (D90): pięć opisów `el6` (wielka, krwiożercza smoczyca, bez efektu) do …/delphyndra/design6<a–e>/, `score` i
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet6     # strona r6n i runda6.html
Runda 7 (D91): Delphyndra jako mieszanka Leviraxa i próbki C z rundy 6 (klon OmniVoice):
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py refs7      # referencje mieszane (Whisper, granice słów)
    <omni> -I analysis/tools/voice_compare_e14.py clone7                    # kwestie Delphyndry z mieszanek
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py score      # ocenia też mieszanki
    <omni> -I analysis/tools/voice_compare_e14.py retake7                   # inne ziarna dla nagrań z błędem automatu
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py score      # potem pick7: najlepsze podejście
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet7     # strona r7n i runda7.html
Runda 8 (D92): nowy profil `el8` z portretu (bestia) przez MCP do …/delphyndra/design8a/ i trzy różne klony Leviraxa:
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py refs8      # referencje Leviraxa z obróbką (ton, warczenie, syk)
    <omni> -I analysis/tools/voice_compare_e14.py clone8                    # kwestie Delphyndry z trzech referencji
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py score      # potem retake8, score, pick8 jak w rundzie 7
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet8     # strona r8n i runda8.html
Runda 9 (D93): klon B z rundy 8 poprawiony (przepróbkowanie zamiast wokodera, instrukcja „female”):
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py refs9      # cztery referencje (przepróbkowanie, tchnienie)
    <omni> -I analysis/tools/voice_compare_e14.py clone9                    # potem score, retake9, score, pick9
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py eq9        # barwa jak B: korektor na nagraniach, potem score
    .venv/Scripts/python -I analysis/tools/voice_compare_e14.py sheet9     # strona r9n i runda9.html

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


# --- runda 3 (QA 2026-11-08) -----------------------------------------------------------------------------------------
# Postacie z oceną 1 w rundzie 2: trzy wyraźnie różne opisy `el3` (a, b, c), każdy to jedno text_to_voice
# do …/<głos>/design3<a|b|c>/. Z trzech podglądów opisu arkusz bierze najlepszy według automatu, z F0 w zakresie płci.
R3_EL = ('delphyndra', 'nara', 'meza')
R3_VARIANTS = 'abc'
R3_CER_OK = 0.02            # poniżej tego CER podglądy uznajemy za równe
R3_F0_TARGET = {'female': 200, 'male': 110}   # niski, ale wyraźnie kobiecy głos (Delphyndra z rundy 2 miała 98 Hz)
# Runda 4 (D88): Delphyndra nadal nie pasuje, pięć bardzo różnych opisów `el4` (a–e) do …/design4<a–e>/.
# Runda 5 (D89): pięć opisów `el5` głosu głębokiego i chropawego; obok każdego ta sama próbka z efektem smoka (dragon_fx).
R4_EL = ('delphyndra',)
R4_VARIANTS = 'abcde'
R5_EL = ('delphyndra',)
R5_VARIANTS = 'abcde'
# Runda 6 (D90): opis wprost „wielka, krwiożercza smoczyca”, bez efektu; część głosów z rundy 5 brzmiała jak męskie.
R6_EL = ('delphyndra',)
R6_VARIANTS = 'abcde'
# Runda 8 (D92): jeden opis `el8` z nowego profilu (zwierzęca, mroczna bestia); arkusz pokazuje wszystkie trzy podglądy.
R8_EL = ('delphyndra',)
R8_VARIANTS = 'a'
ROUNDS_EL = ((3, R3_EL, R3_VARIANTS), (4, R4_EL, R4_VARIANTS), (5, R5_EL, R5_VARIANTS), (6, R6_EL, R6_VARIANTS),
             (8, R8_EL, R8_VARIANTS))
# Zakres i cel F0 (Hz) podglądu: runda 5 głęboko, ale nie męsko (98 Hz z rundy 2); runda 6 wyraźnie kobieco.
ROUND_F0 = {5: (120, 330, 140), 6: (160, 330, 190), 8: (120, 330, 170)}
FX = os.path.join(OUT, 'fx')
DRAGON_FX = {'semitones': -3, 'sub_gain': 0.35, 'sub_hz': 300, 'drive': 3.0, 'grit': 0.35,
             'rt60_s': 1.6, 'reverb': 0.22, 'predelay_s': 0.025}


def el_previews3(voice, var, rnd=3):
    return sorted(glob.glob(os.path.join(EL_AUDIO, voice, 'design%d%s' % (rnd, var), '*.mp3')))


def best_preview3(scores, voice, var, gender, rnd=3):
    lo, hi = F0_RANGE[gender]
    target = R3_F0_TARGET[gender]
    if rnd in ROUND_F0:
        lo, hi, target = ROUND_F0[rnd]
    cands = [(f, scores.get('%s|preview%d%s|%s' % (voice, rnd, var, os.path.basename(f))))
             for f in el_previews3(voice, var, rnd)]
    cands = [(f, s) for f, s in cands if s and 'cer' in s]
    return min(cands, key=lambda c: (bool(c[1].get('tail_cut')), c[1].get('missing', 0) >= 2,
                                     not lo <= (c[1].get('f0') or 0) <= hi, c[1]['cer'] > R3_CER_OK,
                                     abs((c[1].get('f0') or 0) - target)), default=None)


def fx_path(voice, rnd, var):
    return os.path.join(FX, '%s_r%d%s_fx.wav' % (voice, rnd, var))


def items3():
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    out = [('%s|preview%d%s|%s' % (v, rnd, var, os.path.basename(f)), v, f, r2_text(lines, v))
           for rnd, voices, variants in ROUNDS_EL for v in voices for var in variants for f in el_previews3(v, var, rnd)]
    out += [('%s|fx5%s|1' % (v, var), v, fx_path(v, 5, var), r2_text(lines, v))
            for v in R5_EL for var in R5_VARIANTS if os.path.exists(fx_path(v, 5, var))]
    return out


def dragon_fx(y, sr, p=DRAGON_FX):
    """Efekt wielkiego smoka: ton niżej z formantami (większe gardło), warstwa basu oktawę niżej, chrypa i pogłos jaskini."""
    import librosa
    import numpy as np
    from scipy import signal
    main = librosa.effects.pitch_shift(y, sr=sr, n_steps=p['semitones'])
    sub = librosa.effects.pitch_shift(y, sr=sr, n_steps=-12)
    sub = signal.sosfilt(signal.butter(4, p['sub_hz'], 'low', fs=sr, output='sos'), sub)
    x = main + p['sub_gain'] * sub
    x = (1 - p['grit']) * x + p['grit'] * np.tanh(p['drive'] * x) / np.tanh(p['drive'])
    n = int(p['rt60_s'] * sr)
    ir = np.random.default_rng(1).standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir = signal.sosfilt(signal.butter(2, 5000, 'low', fs=sr, output='sos'), ir)
    ir = np.concatenate([np.zeros(int(p['predelay_s'] * sr)), ir / np.sqrt(np.sum(ir ** 2))])
    wet = signal.fftconvolve(x, ir)[:len(x) + int(0.6 * sr)]
    out = np.pad(x, (0, len(wet) - len(x))) + p['reverb'] * wet
    return (0.95 * out / np.max(np.abs(out))).astype(np.float32)


def fx5():
    """Wersje z efektem smoka dla podglądu wybranego z każdego opisu rundy 5."""
    import librosa
    import soundfile as sf
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    os.makedirs(FX, exist_ok=True)
    for v in R5_EL:
        for var in R5_VARIANTS:
            best = best_preview3(scores, v, var, specs[v]['gender'], 5)
            dst = fx_path(v, 5, var)
            if best and not os.path.exists(dst):
                y, sr = librosa.load(best[0], sr=44100, mono=True)
                sf.write(dst, dragon_fx(y, sr), sr, subtype='PCM_16')
                print(v, var, preview_id(best[0]), 'efekt', flush=True)


def variant_clips(scores, specs, voice, rnd, variants, fx=False):
    """Najlepszy podgląd z każdego opisu rundy, na ślepo (litery A… w losowej kolejności); z fx także wersja z efektem."""
    clips = []
    for var in variants:
        best = best_preview3(scores, voice, var, specs[voice]['gender'], rnd)
        if best:
            clips.append({'label': 'Opis %s: %s' % (var, specs[voice]['el%d_label' % rnd][var]), 'kind': 'el%d%s' % (rnd, var),
                          'files': [best[0]], 'metrics': best[1], 'desc': specs[voice]['el%d' % rnd][var],
                          'voice_id': preview_id(best[0]), 'var': var})
    random.Random('%d-r%d-%s' % (SEED, rnd, voice)).shuffle(clips)
    out = []
    for c, letter in zip(clips, 'ABCDE'):
        c['id'] = letter
        out.append(c)
        if fx and os.path.exists(fx_path(voice, rnd, c['var'])):
            out.append({**c, 'id': letter + '-efekt', 'label': c['label'] + ' + efekt smoka', 'kind': c['kind'] + 'fx',
                        'files': [fx_path(voice, rnd, c['var'])],
                        'metrics': scores.get('%s|fx%d%s|1' % (voice, rnd, c['var']), {}),
                        'desc': 'Efekt: ton niżej o %d półtony, bas oktawę niżej, chrypa i pogłos jaskini. ' % -DRAGON_FX['semitones']
                                + c['desc']})
    for c in out:
        c.pop('var', None)
    return out


DELPHYNDRA_ROUNDS = {
    4: {'variants': R4_VARIANTS, 'qa': ('qa3', 3), 'title': 'Runda 4: Delphyndra, pięć wariantów',
        'intro': 'Pięć bardzo różnych opisów głosu potężnej smoczycy (A–E, kolejność losowa). Każda próbka to podgląd projektu, '
                 'który czyta oba fragmenty. Na górze Levirax, druga smoczyca w grze, żeby głosy się nie myliły. '
                 'Oceń A–E, odsłoń etykiety i wybierz wariant albo „Żaden”.',
        'index': 'Delphyndra po rundzie 3 nadal nie pasuje: pięć bardzo różnych opisów głosu potężnej smoczycy.'},
    5: {'variants': R5_VARIANTS, 'qa': ('qa4', 4), 'title': 'Runda 5: Delphyndra, głos głęboki i chropawy', 'fx': True,
        'intro': 'Pięć opisów głębokiego, chropawego głosu smoczycy (A–E, kolejność losowa); każdy także w wersji z efektem smoka '
                 '(np. „A-efekt”: ton niżej, bas, chrypa, pogłos). Na górze Levirax dla porównania. Oceń próbki, odsłoń etykiety '
                 'i wybierz wariant albo „Żaden”.',
        'index': 'Delphyndra po rundzie 4: głos ma być głęboki i chropawy jak smok z filmu. Pięć opisów ElevenLabs, każdy także '
                 'z efektem smoka zrobionym lokalnie.'},
    6: {'variants': R6_VARIANTS, 'qa': ('qa5', 5), 'title': 'Runda 6: Delphyndra, wielka krwiożercza smoczyca',
        'intro': 'Pięć opisów, które wprost mówią: wielka, krwiożercza smoczyca o kobiecym głosie (A–E, kolejność losowa). '
                 'Bez efektu. Na górze Levirax dla porównania. Oceń A–E, odsłoń etykiety i wybierz wariant albo „Żaden”.',
        'index': 'Delphyndra po rundzie 5: głosy nie przypominały smoka, a część brzmiała jak męska. Pięć opisów z „wielką, '
                 'krwiożerczą smoczycą” wprost w zapytaniu i z wyraźnie kobiecym głosem.'},
}


def sheet_delphyndra(rnd):
    """Strona rundy 4–6: opisy Delphyndry na ślepo; dla porównania Levirax (smoczyca z dubbingu)."""
    cfg = DELPHYNDRA_ROUNDS[rnd]
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    v, page_id = 'delphyndra', 'r%dn' % rnd
    clips = variant_clips(scores, specs, v, rnd, cfg['variants'], cfg.get('fx', False))
    lev = specs['levirax']['variant']
    clips.insert(0, {'id': 'orig', 'label': 'Dla porównania: Levirax, smoczyca złoczyńca (klon z dubbingu, wybrany w rundzie 2)',
                     'kind': 'chosen', 'metrics': {}, 'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (lev, i)) for i in (1, 2)]})
    qa_key, qa_round = cfg['qa']
    entry = {'voice': v, 'kind': 'designed', 'clips': clips, 'name': names.get(v, v), 'portrait': portrait_rel(v), 'problems': [],
             'lines': [f['text'] for f in lines[v]], 'decide': ['Wariant %s' % c['id'] for c in clips[1:]] + ['Żaden'],
             'brief': '%s. Uwaga z rundy %d: %s.' % (specs[v]['brief'], qa_round, specs[v][qa_key])}
    for c in entry['clips']:
        files = [f for f in c.pop('files') if f and os.path.exists(f)]
        c['file'] = glue(files, os.path.join(OUT, 'clips', page_id, '%s_%s.wav' % (v, c['id']))) if files else ''
    entry['clips'] = [c for c in entry['clips'] if c['file']]
    page = {'page': page_id, 'title': cfg['title'], 'voices': [entry], 'intro': cfg['intro'],
            'footer': 'Barwa wobec referencji: względem projektu OmniVoice postaci z rundy 1, więc mówi tylko, jak daleko głos jest od niego.'}
    index = {'title': 'E14 · Obsada, runda %d' % rnd, 'file': 'e14r%d_oceny.json' % rnd, 'dir': 'analysis/work/compare/e14/',
             'intro': cfg['index'],
             'notes': ['Każdy opis dał 3 podglądy; arkusz pokazuje jeden według automatu (CER, końcówka, wysokość głosu kobiecego).',
                       'Podglądy nie zajmują miejsc na koncie. Wybrany wariant zapiszemy w miejsce głosu z rundy 1.']}
    if cfg.get('fx'):
        index['notes'].append('Efekt smoka to obróbka lokalna (bez kredytów). Jeśli go wybierzesz, przed generowaniem dodamy go '
                              'do pipeline’u dla kwestii Delphyndry (osobna decyzja).')
    write_round(rnd, page, index)


def write_round(rnd, page, index):
    """Strona jednej postaci z szablonu voice_compare.html i spis runda<rnd>.html z plikiem ocen."""
    import html as H
    template = open(os.path.join(ROOT, 'analysis', 'tools', 'voice_compare.html'), encoding='utf-8').read()
    template = template.replace('href="index.html"', 'href="runda%d.html"' % rnd)
    clips = [c for v in page['voices'] for c in v['clips']]
    nav = [{'page': page['page'], 'title': page['title'], 'ratable': sum(c['id'] != 'orig' for c in clips)}]
    stage = 'E14R%d' % rnd
    body = json.dumps({'mode': 'page', 'stage': stage, 'data': page, 'nav': nav}, ensure_ascii=False).replace('</', '<\\/')
    open(os.path.join(OUT, page['page'] + '.html'), 'w', encoding='utf-8').write(
        template.replace('__TITLE__', H.escape('E14 · ' + page['title'])).replace('__DATA__', body))
    body = json.dumps({'mode': 'index', 'stage': stage, 'nav': nav, 'index': index}, ensure_ascii=False).replace('</', '<\\/')
    open(os.path.join(OUT, 'runda%d.html' % rnd), 'w', encoding='utf-8').write(
        template.replace('__TITLE__', H.escape(index['title'])).replace('__DATA__', body))
    print('nagrania: %d -> %s' % (len(clips), os.path.join(OUT, 'runda%d.html' % rnd)))


def sheet4():
    sheet_delphyndra(4)


def sheet5():
    sheet_delphyndra(5)


def sheet6():
    sheet_delphyndra(6)


# --- runda 7 (D91): Delphyndra jako połączenie Leviraxa i próbki C z rundy 6 ----------------------------------------------
# Referencja OmniVoice to sklejka: początek monologu Leviraxa (klon z dubbingu) i początek podglądu C (ElevenLabs),
# oba przycięte na granicy słowa, z transkrypcją z tych samych wycinków. Proporcja części decyduje o barwie.
R7_SOURCE = ('el6', 'a')        # próbka C z rundy 6 to opis el6 a
# (nazwa, opis, najdłuższy wycinek Leviraxa s, najdłuższy wycinek próbki C s, tempo); monolog ma pauzę 4,6–5,2 s.
R7_MIXES = (('delph_mix_l', 'więcej Leviraxa', 7.5, 2.8, 1.0),
            ('delph_mix_eq', 'po równo', 5.0, 5.0, 1.0),
            ('delph_mix_c', 'więcej próbki C', 3.5, 6.5, 1.0),
            ('delph_mix_eq_slow', 'po równo, tempo 0,85 jak wybrany Levirax (przeciągane końcówki)', 5.0, 5.0, 0.85))
R7_SR = 24000
R7_SEEDS = SEEDS + (41, 53, 67)   # ponowne podejścia mieszanek: kolejne ziarna, gdy pierwsze trzy zawiodą


def r7_preview():
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    return best_preview3(scores, 'delphyndra', R7_SOURCE[1], 'female', 6)[0]


def word_cut(asr, y, sr, seconds):
    """Wycinek od początku do końca ostatniego słowa, które kończy się przed `seconds`, i jego transkrypcja."""
    import librosa
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    out = asr({'raw': y16, 'sampling_rate': 16000}, return_timestamps='word',
              generate_kwargs={'language': 'polish', 'task': 'transcribe'})
    words_ = [c for c in out['chunks'] if c['timestamp'][1] is not None and c['timestamp'][1] <= seconds]
    if not words_:
        raise SystemExit('za krótki wycinek: %.1f s' % seconds)
    end = words_[-1]['timestamp'][1]
    nxt = [c['timestamp'][0] for c in out['chunks'] if c['timestamp'][0] is not None and c['timestamp'][0] >= end]
    end = min(end + 0.08, nxt[0]) if nxt else end + 0.08
    return y[:int(end * sr)], ''.join(c['text'] for c in words_).strip()


def refs7():
    """Referencje mieszane Levirax + próbka C (Whisper ze znacznikami słów, głośność wyrównana)."""
    import librosa
    import numpy as np
    import soundfile as sf
    from lektor.finalize import level
    import npc_voices as N
    lev = load_json(os.path.join(OMNI, 'refs.json'))['levirax']
    y_l, _ = librosa.load(os.path.join(ROOT, lev['wav']), sr=R7_SR, mono=True)
    y_c, _ = librosa.load(r7_preview(), sr=R7_SR, mono=True)
    y_c, _ = librosa.effects.trim(y_c, top_db=40)
    asr = N.load_asr()
    out = {}
    os.makedirs(os.path.join(OMNI, 'refs'), exist_ok=True)
    for name, label, sec_l, sec_c, tempo in R7_MIXES:
        a, t_a = word_cut(asr, y_l, R7_SR, sec_l)
        b, t_b = word_cut(asr, y_c, R7_SR, sec_c)
        y = np.concatenate([level(a, R7_SR)[0], np.zeros(int(MIX_GAP_S * R7_SR), np.float32), level(b, R7_SR)[0]])
        wav = os.path.join(OMNI, 'refs', name + '.wav')
        sf.write(wav, y, R7_SR, subtype='PCM_16')
        out[name] = {'voice': 'delphyndra', 'label': label, 'wav': paths.rel(wav), 'text': t_a + ' ' + t_b, 'tempo': tempo,
                     'seconds': round(len(y) / R7_SR, 2), 'parts_s': [round(len(a) / R7_SR, 2), round(len(b) / R7_SR, 2)],
                     'preview': preview_id(r7_preview())}
        print('%-18s %.1f s (Levirax %.1f s + C %.1f s), słów %d' % (name, out[name]['seconds'], *out[name]['parts_s'],
                                                                     len(out[name]['text'].split())))
    save_json(os.path.join(OMNI, 'refs7.json'), out)


def clone7():
    clone_refs('refs7.json')


def clone_refs(refs_file):
    """Kwestie Delphyndry klonem z referencji rundy (środowisko OmniVoice)."""
    import npc_voices as N
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    refs_ = load_json(os.path.join(OMNI, refs_file))
    model = N.load_omnivoice()
    prompts = {n: model.create_voice_clone_prompt(os.path.join(ROOT, r['wav']), r['text']) for n, r in refs_.items()}
    N.tokenizer_to_cpu(model)
    for name, r in refs_.items():
        for i, f in enumerate(lines[r['voice']], 1):
            wav = os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i))
            if not os.path.exists(wav):
                N.synth(model, wav, f['text'], 1234, voice_clone_prompt=prompts[name], **clone_kw(f, r))


def clone_kw(f, r):
    """Tempo fragmentu z bazy × tempo wariantu × wydłużenie referencji (OmniVoice liczy długość z tempa referencji)
    i instrukcja OmniVoice obok klonu, jeśli wariant ją ma."""
    kw = {}
    speed = (f.get('speed') or 1.0) * r['tempo'] * r.get('ref_stretch', 1.0)
    if speed != 1.0:
        kw['speed'] = speed
    if r.get('instruct'):
        kw['instruct'] = r['instruct']
    return kw


def flagged(refs_file):
    """Nagrania klonów rundy z błędem automatu (CER powyżej progu albo ucięta końcówka): (nazwa, nr fragmentu)."""
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    out = []
    for name, r in load_json(os.path.join(OMNI, refs_file), {}).items():
        for i in (1, 2):
            s = scores.get('%s|%s|%d' % (r['voice'], name, i))
            if s and (s['cer'] > MAX_CER or s.get('tail_cut')):
                out.append((name, i))
    return out


def retake7():
    retake_refs('refs7.json')


def retake_refs(refs_file):
    """Ponowne podejścia z ziarnami R7_SEEDS dla nagrań z błędem (środowisko OmniVoice)."""
    import npc_voices as N
    todo = flagged(refs_file)
    if not todo:
        print('brak nagrań do poprawy')
        return
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    refs_ = load_json(os.path.join(OMNI, refs_file))
    model = N.load_omnivoice()
    prompts = {n: model.create_voice_clone_prompt(os.path.join(ROOT, refs_[n]['wav']), refs_[n]['text']) for n in {n for n, _ in todo}}
    N.tokenizer_to_cpu(model)
    for name, i in todo:
        r, f = refs_[name], lines[refs_[name]['voice']][i - 1]
        for seed in R7_SEEDS:
            wav = os.path.join(OMNI, 'clips', '%s_%d_s%d.wav' % (name, i, seed))
            if not os.path.exists(wav):
                N.synth(model, wav, f['text'], seed, voice_clone_prompt=prompts[name], **clone_kw(f, r))


def pick7():
    pick_refs('refs7.json')


def pick_refs(refs_file):
    """Najlepsze podejście (bez uciętej końcówki, najmniejszy CER) zastępuje nagranie klonu; oryginał zostaje jako _s1234."""
    import shutil
    path = os.path.join(OUT, 'scores.json')
    scores = load_json(path, {})
    for name, i in flagged(refs_file):
        main = os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i))
        key = 'delphyndra|%s|%d' % (name, i)
        backup = os.path.join(OMNI, 'clips', '%s_%d_s1234.wav' % (name, i))
        if not os.path.exists(backup):
            shutil.copyfile(main, backup)
        cands = [(backup, scores.get(key + '|s1234') or scores[key])]
        cands += [(os.path.join(OMNI, 'clips', '%s_%d_s%d.wav' % (name, i, s)), scores.get('%s|s%d' % (key, s))) for s in R7_SEEDS]
        cands = [(f, s) for f, s in cands if s and os.path.exists(f)]
        best = min(cands, key=lambda c: (bool(c[1].get('tail_cut')), c[1]['cer']))
        scores.setdefault(key + '|s1234', scores[key])
        shutil.copyfile(best[0], main)
        scores[key] = best[1]
        print('%-18s fragment %d: %s, CER %.3f' % (name, i, os.path.basename(best[0]), best[1]['cer']))
    save_json(path, scores)


def items7():
    """Nagrania klonów Delphyndry z rund 7–9 (z ponownymi podejściami)."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    out = []
    refs_ = {k: v for f in ('refs7.json', 'refs8.json', 'refs9.json') for k, v in load_json(os.path.join(OMNI, f), {}).items()}
    refs_.update({name: {'voice': 'delphyndra'} for name, *_ in R9_POST})
    for name, r in refs_.items():
        for i, f in enumerate(lines[r['voice']], 1):
            wav = os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i))
            if os.path.exists(wav):
                out.append(('%s|%s|%d' % (r['voice'], name, i), r['voice'], wav, f['text']))
            for seed in R7_SEEDS:
                alt = os.path.join(OMNI, 'clips', '%s_%d_s%d.wav' % (name, i, seed))
                if os.path.exists(alt):
                    out.append(('%s|%s|%d|s%d' % (r['voice'], name, i, seed), r['voice'], alt, f['text']))
    return out


def sheet7():
    """Strona rundy 7: cztery mieszanki Levirax + C na ślepo; obie składowe dla porównania."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    refs_ = load_json(os.path.join(OMNI, 'refs7.json'))
    v, lev = 'delphyndra', specs['levirax']['variant']
    clips = [{'label': 'Mieszanka: %s' % r['label'], 'kind': name,
              'metrics': merged(scores.get('%s|%s|1' % (v, name)), scores.get('%s|%s|2' % (v, name))),
              'desc': 'OmniVoice, klon z referencji %.1f s: Levirax %.1f s + próbka C %.1f s, tempo %s.'
                      % (r['seconds'], r['parts_s'][0], r['parts_s'][1], str(r['tempo']).replace('.', ',')),
              'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i)) for i in (1, 2)]} for name, r in refs_.items()]
    for c in clips:
        if c['metrics'].get('cer', 0) > MAX_CER:
            c['desc'] += ' Automat: brakuje słów (CER %.0f%%) mimo %d ponownych podejść z innymi ziarnami.' % (
                100 * c['metrics']['cer'], len(R7_SEEDS))
    random.Random('%d-r7-%s' % (SEED, v)).shuffle(clips)
    for c, letter in zip(clips, 'ABCD'):
        c['id'] = letter
    c_preview = best_preview3(scores, v, R7_SOURCE[1], 'female', 6)
    clips = [{'id': 'orig', 'label': 'Składowa 1: Levirax, smoczyca złoczyńca (klon z dubbingu)', 'kind': 'chosen', 'metrics': {},
              'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (lev, i)) for i in (1, 2)]},
             {'id': 'orig', 'label': 'Składowa 2: próbka C z rundy 6 (ElevenLabs, opis el6 a)', 'kind': 'el6a',
              'metrics': c_preview[1], 'files': [c_preview[0]]}] + clips
    entry = {'voice': v, 'kind': 'designed', 'clips': clips, 'name': names.get(v, v), 'portrait': portrait_rel(v), 'problems': [],
             'lines': [f['text'] for f in lines[v]], 'decide': ['Wariant %s' % c['id'] for c in clips[2:]] + ['Żaden'],
             'brief': '%s. Uwaga z rundy 6: %s.' % (specs[v]['brief'], specs[v]['qa6'])}
    for k, c in enumerate(entry['clips']):
        files = [f for f in c.pop('files') if f and os.path.exists(f)]
        c['file'] = glue(files, os.path.join(OUT, 'clips', 'r7n', '%s_%s%d.wav' % (v, c['id'], k))) if files else ''
    entry['clips'] = [c for c in entry['clips'] if c['file']]
    page = {'page': 'r7n', 'title': 'Runda 7: Delphyndra, Levirax + próbka C', 'voices': [entry],
            'intro': 'Na górze obie składowe: Levirax i próbka C z rundy 6. Niżej cztery mieszanki (A–D, kolejność losowa): klon '
                     'OmniVoice z referencji sklejonej z obu głosów w różnych proporcjach. Oceń A–D, odsłoń etykiety i wybierz '
                     'wariant albo „Żaden”.',
            'footer': 'Barwa wobec referencji: względem projektu OmniVoice postaci z rundy 1, więc mówi tylko, jak daleko głos jest od niego.'}
    index = {'title': 'E14 · Obsada, runda 7', 'file': 'e14r7_oceny.json', 'dir': 'analysis/work/compare/e14/',
             'intro': 'Delphyndra jako połączenie głosu Leviraxa z próbką C z rundy 6: cztery proporcje mieszanki.',
             'notes': ['Mieszanki to klon OmniVoice (lokalnie, bez kredytów), a nie ElevenLabs. Wybór mieszanki zmienia silnik '
                       'Delphyndry z ElevenLabs na OmniVoice (wyjątek od D84), co zapiszemy jako decyzję.',
                       'Delphyndra i Levirax będą brzmiały podobnie, bo mieszanka bierze barwę z Leviraxa.']}
    write_round(7, page, index)


# --- runda 8 (D92): nowy profil z portretu (zwierzęca, mroczna bestia) i trzy wyraźnie różne klony Leviraxa ----------------
# Klon przejmuje z referencji wysokość, chrypę i syk, więc różnice robimy w referencji: ton, warczenie, syk, inne okrzyki.
# (nazwa, opis, referencja z refs.json albo refs2.json, obróbka referencji, tempo)
R8_CLONES = (('delph_lev_olbrzym', 'olbrzymka: monolog Leviraxa 4 półtony niżej (większe gardło), tempo 0,85',
              'levirax', {'semitones': -4}, 0.85),
             ('delph_lev_bestia', 'bestia: monolog 2 półtony niżej z warczeniem i mocną chrypą, tempo 0,9',
              'levirax', {'semitones': -2, 'growl': 0.8}, 0.9),
             ('delph_lev_gad', 'gadzina: ciche, syczące okrzyki (Spawn 2, Defend 3 i 2) z sykiem, tempo 0,8',
              'levirax_v2b', {'hiss': 1.0}, 0.8))


def growl(y, sr, amount):
    """Warczenie: warstwa oktawę niżej (pasmo do 400 Hz) i chrypa z npc_voices (modulacja 25–70 Hz, szum, przester)."""
    import librosa
    from scipy import signal
    import npc_voices as N
    sub = librosa.effects.pitch_shift(y, sr=sr, n_steps=-12)
    sub = signal.sosfilt(signal.butter(4, 400, 'low', fs=sr, output='sos'), sub)
    return N.roughen(y + 0.5 * amount * sub, sr, amount)


def hiss(y, sr, amount, seed=3):
    """Syk: szum 3–9 kHz idący za obwiednią głosek szczelinowych i słabsze tchnienie pod całą mową."""
    import numpy as np
    from scipy import signal
    rng = np.random.default_rng(seed)
    env = lambda x: signal.sosfiltfilt(signal.butter(2, 30, 'low', fs=sr, output='sos'), np.abs(x))
    sib = env(signal.sosfiltfilt(signal.butter(4, 3500, 'high', fs=sr, output='sos'), y))
    noise = signal.sosfiltfilt(signal.butter(2, (3000, 9000), 'band', fs=sr, output='sos'), rng.standard_normal(len(y)))
    noise /= np.abs(noise).max() + 1e-9
    out = y + noise * (4 * sib + 0.4 * env(y)) * amount
    return (out * (np.abs(y).max() / (np.abs(out).max() + 1e-9))).astype(np.float32)


def refs8():
    build_refs(R8_CLONES, 'refs8.json')


def process_ref(y, sr, fx):
    """Obróbka referencji: `semitones` (wokoder fazowy librosa, runda 8), `tape` (przepróbkowanie, runda 9), warczenie, syk, tchnienie."""
    import librosa
    if fx.get('semitones'):
        y = librosa.effects.pitch_shift(y, sr=sr, n_steps=fx['semitones'])
    if fx.get('tape'):
        y = tape(y, sr, fx['tape'])
    if fx.get('growl'):
        y = growl(y, sr, fx['growl'])
    if fx.get('hiss'):
        y = hiss(y, sr, fx['hiss'])
    if fx.get('breath'):
        y = breath(y, sr, fx['breath'])
    return y


def build_refs(clones, refs_file):
    """Referencje klonów: monolog albo okrzyki Leviraxa po obróbce, transkrypcja bez zmian (ta sama mowa, ten sam czas)."""
    import librosa
    import soundfile as sf
    from lektor.finalize import level
    src = {**load_json(os.path.join(OMNI, 'refs.json')), **load_json(os.path.join(OMNI, 'refs2.json'))}
    out = {}
    for name, label, source, fx, tempo in clones:
        r = src[source]
        y0, _ = librosa.load(os.path.join(ROOT, r['wav']), sr=R7_SR, mono=True)
        y = process_ref(y0, R7_SR, fx)
        wav = os.path.join(OMNI, 'refs', name + '.wav')
        sf.write(wav, level(y, R7_SR)[0], R7_SR, subtype='PCM_16')
        out[name] = {'voice': 'delphyndra', 'label': label, 'source': source, 'fx': fx, 'wav': paths.rel(wav),
                     'text': r['text'], 'tempo': tempo, 'seconds': round(len(y) / R7_SR, 2),
                     'ref_stretch': round(len(y) / len(y0), 4), 'instruct': fx.get('instruct')}
        print('%-18s %.1f s z %s, %s' % (name, out[name]['seconds'], source, fx))
    save_json(os.path.join(OMNI, refs_file), out)


def clone8():
    clone_refs('refs8.json')


def retake8():
    retake_refs('refs8.json')


def pick8():
    pick_refs('refs8.json')


def sheet8():
    """Strona rundy 8: trzy podglądy nowego profilu i trzy klony Leviraxa na ślepo; Levirax dla porównania."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    v, lev = 'delphyndra', specs['levirax']['variant']
    clips, dropped = [], []
    for k, f in enumerate(el_previews3(v, 'a', 8), 1):
        s = scores.get('%s|preview8a|%s' % (v, os.path.basename(f)))
        if not s or s.get('tail_cut') or s['cer'] > MAX_CER:
            dropped.append(preview_id(f))
            continue
        clips.append({'label': 'Nowy profil (ElevenLabs), podgląd %d' % k, 'kind': 'el8a', 'metrics': s,
                      'desc': specs[v]['el8']['a'], 'voice_id': preview_id(f), 'files': [f]})
    clips += [clone_clip(scores, v, name, r) for name, r in load_json(os.path.join(OMNI, 'refs8.json')).items()]
    random.Random('%d-r8-%s' % (SEED, v)).shuffle(clips)
    for c, letter in zip(clips, 'ABCDEF'):
        c['id'] = letter
    clips.insert(0, {'id': 'orig', 'label': 'Dla porównania: Levirax, smoczyca złoczyńca (klon z dubbingu)', 'kind': 'chosen',
                     'metrics': {}, 'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (lev, i)) for i in (1, 2)]})
    entry = {'voice': v, 'kind': 'designed', 'clips': clips, 'name': names.get(v, v), 'portrait': portrait_rel(v), 'problems': [],
             'lines': [f['text'] for f in lines[v]], 'decide': ['Wariant %s' % c['id'] for c in clips[1:]] + ['Żaden'],
             'brief': 'Nowy profil: %s. Uwaga z rundy 7: %s.' % (specs[v]['brief'], specs[v]['qa7'])}
    glue_clips(entry, 'r8n')
    page = {'page': 'r8n', 'title': 'Runda 8: Delphyndra, bestia z portretu', 'voices': [entry],
            'intro': 'Nowy profil z portretu: ciężka bestia z kłami i kapiącą śliną, głos zwierzęcy i mroczny. Na górze Levirax '
                     'dla porównania. Niżej (kolejność losowa) trzy podglądy ElevenLabs z nowego opisu i trzy klony Leviraxa '
                     'w OmniVoice: niżej i wolniej, z warczeniem, z sykiem. Oceń, odsłoń etykiety i wybierz wariant albo „Żaden”.',
            'footer': 'Barwa wobec referencji: względem projektu OmniVoice postaci z rundy 1, więc mówi tylko, jak daleko głos jest od niego.'}
    index = {'title': 'E14 · Obsada, runda 8', 'file': 'e14r8_oceny.json', 'dir': 'analysis/work/compare/e14/',
             'intro': 'Delphyndra po rundzie 7: nowy profil z portretu (bestia, nie dama) i trzy wyraźnie różne klony Leviraxa.',
             'notes': ['Klony Leviraxa to OmniVoice (lokalnie, bez kredytów). Wybór klonu zmienia silnik Delphyndry z ElevenLabs '
                       'na OmniVoice (wyjątek od D84), co zapiszemy jako decyzję.',
                       'Podglądy ElevenLabs nie zajmują miejsc na koncie; wybrany zapiszemy w miejsce głosu z rundy 1.']}
    if dropped:
        index['notes'].append('Automat odrzucił podglądy: %s (brak słów albo ucięta końcówka).' % ', '.join(dropped))
    write_round(8, page, index)


def clone_clip(scores, v, name, r):
    """Klip klonu OmniVoice z obu fragmentów, z uwagą, gdy automat nadal widzi brak słów."""
    c = {'label': 'Klon Leviraxa: %s' % r['label'], 'kind': name,
         'metrics': merged(scores.get('%s|%s|1' % (v, name)), scores.get('%s|%s|2' % (v, name))),
         'desc': 'OmniVoice, klon z referencji %.1f s po obróbce, tempo %s.' % (r['seconds'], str(r['tempo']).replace('.', ',')),
         'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i)) for i in (1, 2)]}
    if c['metrics'].get('cer', 0) > MAX_CER:
        c['desc'] += ' Automat: brakuje słów (CER %.0f%%) mimo %d ponownych podejść z innymi ziarnami.' % (
            100 * c['metrics']['cer'], len(R7_SEEDS))
    return c


def glue_clips(entry, page_id):
    """Fragmenty każdego klipu sklejone w jedno nagranie strony; klipy bez plików wypadają."""
    for k, c in enumerate(entry['clips']):
        files = [f for f in c.pop('files') if f and os.path.exists(f)]
        c['file'] = glue(files, os.path.join(OUT, 'clips', page_id, '%s_%s%d.wav' % (entry['voice'], c['id'], k))) if files else ''
    entry['clips'] = [c for c in entry['clips'] if c['file']]


# --- runda 9 (D93): wybrany klon B (olbrzymka) bez robotycznego brzmienia i z kobiecym charakterem ----------------------------
# Wokoder fazowy librosa (runda 8) rozciąga czas i zostawia w referencji metaliczny pogłos, który klon przejmuje. Teraz ton
# obniża samo przepróbkowanie (jak wolniejsza taśma): ton i formanty razem, bez artefaktów, a referencja jest dłuższa.
# Tempo wyrównuje `speed`, bo OmniVoice liczy długość z tempa referencji. PSOLA odpada: pYIN uznaje za dźwięczną tylko
# połowę ramek chropawego głosu Leviraxa. Kobiecy charakter daje instrukcja OmniVoice („female”) obok klonu albo tchnienie.
# (nazwa, opis, referencja, obróbka, tempo); wszystkie z monologu Leviraxa w tempie 0,85 jak B.
R9_CLONES = (('delph_b_czysta', 'B bez artefaktów: ton i gardło 4 półtony niżej jak w B, przepróbkowanie zamiast wokodera',
              'levirax', {'tape': -4}, 0.85),
             ('delph_b_female', 'jak „B bez artefaktów” i instrukcja OmniVoice „female” obok klonu',
              'levirax', {'tape': -4, 'instruct': 'female'}, 0.85),
             ('delph_b_jasniej', 'ton i gardło 3 półtony niżej (odrobinę wyżej niż B) i instrukcja „female”',
              'levirax', {'tape': -3, 'instruct': 'female'}, 0.85),
             ('delph_b_oddech', 'jak „B bez artefaktów” z miękkim tchnieniem w referencji',
              'levirax', {'tape': -4, 'breath': 0.4}, 0.85))
# Po przepróbkowaniu klon jest ciemniejszy od B (środek widma ok. 1600 zamiast 2340 Hz), choć referencje mają podobną
# jasność. Korektor w referencji nic nie zmienia, więc wariant „barwa jak B” to gotowe nagrania z korektorem dopasowanym
# do nagrań B: (nazwa, opis, nagrania źródłowe, nagrania wzorca).
R9_POST = (('delph_b_barwa', 'jak „B bez artefaktów” (te same nagrania) z barwą dopasowaną korektorem do B',
            'delph_b_czysta', 'delph_lev_olbrzym'),)
EQ_MAX_DB = 12      # korektor dopasowania barwy: najwyżej ±12 dB, wygładzenie 1/3 oktawy


def eq_fir(y, target, sr, max_db=EQ_MAX_DB):
    """Filtr liniowo-fazowy, który nadaje `y` średnie widmo (LTAS) nagrania `target`, wygładzone do 1/3 oktawy."""
    import numpy as np
    from scipy import signal
    n = 4096
    _, p_y = signal.welch(y, sr, nperseg=n)
    f, p_t = signal.welch(target, sr, nperseg=n)
    gain_db = 10 * np.log10((p_t + 1e-12) / (p_y + 1e-12))
    smooth = np.array([gain_db[(f >= fc / 2 ** (1 / 6)) & (f <= fc * 2 ** (1 / 6))].mean() if fc > 0 else gain_db[0]
                       for fc in f])
    gain_db = np.clip(smooth - np.median(smooth[(f > 300) & (f < 3000)]), -max_db, max_db)
    return signal.firwin2(1025, f / (sr / 2), 10 ** (gain_db / 20))


def eq9():
    """Nagrania R9_POST: nagrania źródłowe z korektorem z ich wspólnego widma do widma nagrań wzorca (głośność jak przed)."""
    import numpy as np
    import soundfile as sf
    from scipy import signal
    clip = lambda name, i: os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i))
    for name, label, src, target in R9_POST:
        ys = [sf.read(clip(src, i), dtype='float32') for i in (1, 2)]
        sr = ys[0][1]
        fir = eq_fir(np.concatenate([y for y, _ in ys]), np.concatenate([sf.read(clip(target, i), dtype='float32')[0]
                                                                          for i in (1, 2)]), sr)
        for i, (y, _) in enumerate(ys, 1):
            out = signal.fftconvolve(y, fir)[512:512 + len(y)]
            sf.write(clip(name, i), out * np.sqrt(np.mean(y ** 2) / (np.mean(out ** 2) + 1e-12)), sr, subtype='PCM_16')
        print('%-18s z %s, korektor do %s' % (name, src, target))


def tape(y, sr, semitones):
    """Ton i formanty o `semitones` niżej przez samo przepróbkowanie; nagranie wydłuża się o 2^(-semitones/12)."""
    import librosa
    return librosa.resample(y, orig_sr=sr, target_sr=int(round(sr * 2 ** (-semitones / 12))))


def breath(y, sr, amount, seed=13):
    """Miękkie tchnienie: szum 1,5–7 kHz idący za obwiednią mowy."""
    import numpy as np
    from scipy import signal
    rng = np.random.default_rng(seed)
    env = signal.sosfiltfilt(signal.butter(2, 40, 'low', fs=sr, output='sos'), np.abs(y))
    noise = signal.sosfiltfilt(signal.butter(2, (1500, 7000), 'band', fs=sr, output='sos'), rng.standard_normal(len(y)))
    out = y + noise / (np.abs(noise).max() + 1e-9) * env * amount
    return (out * (np.abs(y).max() / (np.abs(out).max() + 1e-9))).astype(np.float32)


def refs9():
    build_refs(R9_CLONES, 'refs9.json')


def clone9():
    clone_refs('refs9.json')


def retake9():
    retake_refs('refs9.json')


def pick9():
    pick_refs('refs9.json')


def sheet9():
    """Strona rundy 9: pięć poprawek klonu B na ślepo; Levirax i B z rundy 8 dla porównania."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    v, lev = 'delphyndra', specs['levirax']['variant']
    refs_ = load_json(os.path.join(OMNI, 'refs9.json'))
    clips = [clone_clip(scores, v, name, r) for name, r in refs_.items()]
    for name, label, src, target in R9_POST:
        c = clone_clip(scores, v, name, {**refs_[src], 'label': label})
        c['desc'] += ' Korektor liniowo-fazowy (najwyżej ±%d dB) z widma tych nagrań do widma nagrań B.' % EQ_MAX_DB
        clips.append(c)
    random.Random('%d-r9-%s' % (SEED, v)).shuffle(clips)
    for c, letter in zip(clips, 'ABCDE'):
        c['id'] = letter
    b = R8_CLONES[0][0]
    clips = [{'id': 'orig', 'label': 'Dla porównania: Levirax, smoczyca złoczyńca (klon z dubbingu)', 'kind': 'chosen',
              'metrics': {}, 'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (lev, i)) for i in (1, 2)]},
             {'id': 'orig', 'label': 'Wybrana w rundzie 8: B, olbrzymka (z robotycznym brzmieniem)', 'kind': b,
              'metrics': merged(scores.get('%s|%s|1' % (v, b)), scores.get('%s|%s|2' % (v, b))),
              'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (b, i)) for i in (1, 2)]}] + clips
    entry = {'voice': v, 'kind': 'designed', 'clips': clips, 'name': names.get(v, v), 'portrait': portrait_rel(v), 'problems': [],
             'lines': [f['text'] for f in lines[v]], 'decide': ['Wariant %s' % c['id'] for c in clips[2:]] + ['Żaden'],
             'brief': '%s. Uwaga z rundy 8: %s.' % (specs[v]['brief'], specs[v]['qa8'])}
    glue_clips(entry, 'r9n')
    page = {'page': 'r9n', 'title': 'Runda 9: Delphyndra, poprawki klonu B', 'voices': [entry],
            'intro': 'Na górze Levirax i wybrana w rundzie 8 olbrzymka (B). Niżej pięć poprawek B (A–E, kolejność losowa): '
                     'obniżenie tonu samym przepróbkowaniem zamiast wokodera, który dawał robotyczny pogłos, i trzy sposoby na kobiecy '
                     'charakter albo dopasowanie barwy do B. Oceń A–E, odsłoń etykiety i wybierz wariant albo „Żaden”.',
            'footer': 'Barwa wobec referencji: względem projektu OmniVoice postaci z rundy 1, więc mówi tylko, jak daleko głos jest od niego.'}
    index = {'title': 'E14 · Obsada, runda 9', 'file': 'e14r9_oceny.json', 'dir': 'analysis/work/compare/e14/',
             'intro': 'Delphyndra: wybrany w rundzie 8 klon B bez robotycznego brzmienia i z odrobiną kobiecego charakteru.',
             'notes': ['Klony to OmniVoice (lokalnie, bez kredytów). Wybór oznacza, że Delphyndrę czyta OmniVoice (wyjątek od D84), '
                       'co zapiszemy jako decyzję.',
                       'Wariant „bez artefaktów” ma ton i gardło jak B; pozostałe dodają jedną zmianę: instrukcję „female”, ton '
                       'pół kroku wyżej, tchnienie albo jasność barwy jak w B.']}
    write_round(9, page, index)


def sheet3():
    """Strony rundy 3: trzy nowe warianty na ślepo obok odrzuconego z rundy 2 i wszystkie głosy już w obsadzie."""
    import html as H
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    specs = load_json(DESIGNS)
    names = load_json(os.path.join(OUT, 'names.json'), {})
    from voice_compare import NAMES
    names.update({v: NAMES[v] for v in CHOSEN if v in NAMES})
    r3n = []
    for v in R3_EL:
        best2 = best_preview2(scores, v)
        clips = variant_clips(scores, specs, v, 3, R3_VARIANTS)
        clips.insert(0, {'id': 'orig', 'label': 'Runda 2 (ocena 1: %s)' % specs[v]['qa2'], 'kind': 'el2',
                         'files': [best2[0]] if best2 else [], 'metrics': best2[1] if best2 else {}, 'desc': specs[v]['el2']})
        r3n.append({'voice': v, 'kind': 'designed', 'clips': clips, 'decide': ['Wariant A', 'Wariant B', 'Wariant C', 'Żaden'],
                    'brief': '%s. Uwaga z rundy 2: %s.' % (specs[v]['brief'], specs[v]['qa2'])})
    chosen = []
    for v in CHOSEN:
        chosen.append({'voice': v, 'label': 'Obecny głos: ' + ('OmniVoice (klon z dubbingu)' if v in ('nekrul', 'xenith') else 'ElevenLabs (E13)'),
                       'files': [f['file'] for f in lines[v]]})
    for v in NEW:
        if v in R3_EL:
            continue
        if v in R2_EL:
            best2 = best_preview2(scores, v)
            chosen.append({'voice': v, 'label': 'Wybrany w rundzie 2: ElevenLabs', 'files': [best2[0]]})
        else:
            chosen.append({'voice': v, 'label': 'Wybrany w rundzie 1: ElevenLabs', 'files': [best_preview(scores, v)[0], el_v4(v)]})
    for v in R2_ACCEPTED_VILLAINS + tuple(R2_VILLAINS):
        name = specs[v].get('variant', v)
        chosen.append({'voice': v, 'label': 'Wybrany: OmniVoice (klon z dubbingu%s)' % (', wariant z rundy 2' if name != v else ''),
                       'files': [os.path.join(OMNI, 'clips', '%s_%d.wav' % (name, i)) for i in (1, 2)]})
    r3w = [{'voice': c['voice'], 'kind': 'chosen', 'clips': [{'id': 'orig', 'kind': 'chosen', 'metrics': {},
                                                             'label': c['label'], 'files': c['files']}]} for c in chosen]
    pages = [{'page': 'r3n', 'title': 'Runda 3: trzy warianty ElevenLabs', 'voices': r3n,
              'intro': 'Każda postać ma trzy nowe opisy głosu (A–C, kolejność losowa). Każda próbka to podgląd projektu, który '
                       'czyta oba fragmenty (Meza: pierwszy). Na górze odrzucony głos z rundy 2 dla porównania. Oceń A–C, '
                       'odsłoń etykiety i wybierz wariant albo „Żaden”.'},
             {'page': 'r3w', 'title': 'Głosy już w obsadzie', 'voices': r3w,
              'intro': 'Wszystkie głosy już w obsadzie, także wybrane w rundzie 2 (Waiqar, Morant, Levirax, Gilliam). Bez ocen.'}]
    for p in pages:
        p['footer'] = 'Barwa wobec referencji: względem projektu OmniVoice postaci (nowe postacie) albo dubbingu (złoczyńcy).'
        for entry in p['voices']:
            v = entry['voice']
            entry.update(name=names.get(v, v), portrait=portrait_rel(v), problems=[], lines=[f['text'] for f in lines[v]])
            entry.setdefault('brief', '')
            for c in entry['clips']:
                files = [f for f in c.pop('files') if f and os.path.exists(f)]
                c['file'] = glue(files, os.path.join(OUT, 'clips', p['page'], '%s_%s.wav' % (v, c['id']))) if files else ''
            entry['clips'] = [c for c in entry['clips'] if c['file']]
    template = open(os.path.join(ROOT, 'analysis', 'tools', 'voice_compare.html'), encoding='utf-8').read()
    template = template.replace('href="index.html"', 'href="runda3.html"')
    nav = [{'page': p['page'], 'title': p['title'],
            'ratable': sum(c['id'] != 'orig' for v in p['voices'] for c in v['clips'])} for p in pages]
    index = {'title': 'E14 · Obsada, runda 3', 'file': 'e14r3_oceny.json', 'dir': 'analysis/work/compare/e14/',
             'intro': 'Trzy wyraźnie różne opisy głosu dla Delphyndry, Nary i Mezy (ocena 1 w rundzie 2). Strona r3w ma '
                      'wszystkie głosy już w obsadzie.',
             'notes': ['Każdy opis dał 3 podglądy; arkusz pokazuje najlepszy według automatu (CER, końcówka, wysokość głosu '
                       'kobiecego), więc odrzucony w rundzie 2 męski podgląd Delphyndry już nie przejdzie.',
                       'Wybrany wariant zapiszemy na koncie w miejsce głosu z rundy 1.']}
    for p in pages:
        body = json.dumps({'mode': 'page', 'stage': 'E14R3', 'data': p, 'nav': nav}, ensure_ascii=False).replace('</', '<\\/')
        open(os.path.join(OUT, p['page'] + '.html'), 'w', encoding='utf-8').write(
            template.replace('__TITLE__', H.escape('E14 · ' + p['title'])).replace('__DATA__', body))
    body = json.dumps({'mode': 'index', 'stage': 'E14R3', 'nav': nav, 'index': index}, ensure_ascii=False).replace('</', '<\\/')
    open(os.path.join(OUT, 'runda3.html'), 'w', encoding='utf-8').write(
        template.replace('__TITLE__', H.escape(index['title'])).replace('__DATA__', body))
    print('strony: %d, nagrania: %d -> %s' % (len(pages) + 1, sum(len(v['clips']) for p in pages for v in p['voices']),
                                               os.path.join(OUT, 'runda3.html')))


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
    todo = [t for t in items() + items2() + items3() + items7() if t[0] not in scores]
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
                'sheet2': sheet2, 'sheet3': sheet3, 'sheet4': sheet4,
                'fx5': fx5, 'sheet5': sheet5, 'sheet6': sheet6, 'refs7': refs7, 'clone7': clone7, 'retake7': retake7,
                'pick7': pick7, 'sheet7': sheet7, 'refs8': refs8, 'clone8': clone8, 'retake8': retake8, 'pick8': pick8,
                'sheet8': sheet8, 'refs9': refs9, 'clone9': clone9,
                'retake9': retake9, 'pick9': pick9, 'eq9': eq9, 'sheet9': sheet9}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    commands[sys.argv[1]]()
