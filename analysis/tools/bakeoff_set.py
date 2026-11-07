"""Zestaw porównawczy TTS (E0): fragmenty, normalizacja, adnotacja emocji, referencje emocjonalne, lista zadań.

Wynik (nieśledzony, z tekstami gry): work/bakeoff/set.json oraz work/bakeoff/refs/<głos>__<emocja>.wav.
Ten sam set.json czytają generatory wszystkich kandydatów (bakeoff_gen.py), więc każdy model dostaje
identyczny tekst, referencje, podział na fragmenty i ziarna losowania.

Uruchomienie (z katalogu głównego repozytorium, .venv):
  .venv/Scripts/python -I analysis/tools/bakeoff_set.py               # fragmenty, referencje, zadania
  .venv/Scripts/python -I analysis/tools/bakeoff_set.py --transcribe  # + transkrypcje referencji (Whisper, GPU)
  .venv/Scripts/python -I analysis/tools/bakeoff_set.py --short-prompts  # krótkie referencje narratora dla OmniVoice
  .venv/Scripts/python -I analysis/tools/bakeoff_set.py --jobs-only   # tylko lista zadań (np. warianty rundy 2)
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_pl import normalize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'work', 'out')
VOICES_DIR = os.path.join(ROOT, 'work', 'voices')
BAKE = os.path.join(ROOT, 'work', 'bakeoff')
REFS = os.path.join(BAKE, 'refs')

# Słownik emocji (D28). exag = exaggeration Chatterboxa; inne modele biorą emocję tylko z referencji.
EMOTIONS = {
    'neutralny': {'opis': 'rzeczowo, równe tempo (UI, reguły, komunikaty)', 'exag': 0.5},  # domyślne w Chatterboxie
    'spokojny': {'opis': 'narracja opisowa, wolniej, miękko', 'exag': 0.4},
    'ciepły': {'opis': 'przyjaźnie, z uśmiechem', 'exag': 0.5},
    'radosny': {'opis': 'entuzjazm, wyższe pobudzenie', 'exag': 0.7},
    'wzruszony': {'opis': 'ciszej, z pauzami, łamiący się głos', 'exag': 0.5},
    'poważny': {'opis': 'niżej, wolniej, z ciężarem', 'exag': 0.45},
    'chłodny': {'opis': 'oschle, z dystansem, gorycz', 'exag': 0.4},
    'napięty': {'opis': 'narracja akcji, napięcie, szybciej', 'exag': 0.6},
    'okrzyk': {'opis': 'głośno, energicznie (walka)', 'exag': 0.8},
}

# Referencje emocjonalne bohaterów: typy okrzyków z dubbingu (work/voices) → emocja; wybór po pobudzeniu (arousal).
HERO_EMOTION_CLIPS = {
    'neutralny': (('HeroSelect', 'QuestSelect'), 'mid'),
    'ciepły': (('GainTreasure', 'GiveTreasure', 'HeroSelect'), 'mid'),
    'radosny': (('QuestWon', 'DefeatEnemy', 'FeatComplete'), 'high'),
    'wzruszony': (('QuestLost',), 'low'),
    'poważny': (('QuestLost', 'QuestSelect'), 'low'),
    'chłodny': (('HeroSelect', 'QuestSelect', 'QuestLost'), 'low'),
    'okrzyk': (('DefeatEnemy', 'MajorWound'), 'high'),
}
# Narrator: fragmenty przerywników o różnym pobudzeniu (spokojny: niskie, napięty: wysokie).
NARRATOR_EMOTION_SOURCES = {
    'spokojny': ('4_Finale_VoiceOver.wav', 1.0, 16.0),
    'napięty': ('DLE04_2_Fulminar_VoiceOver.wav', 1.0, 16.0),
}

# id, klucz, głos, emocja, opis (bez treści), wartości {n}
FRAGMENTS = [
    ('F01', 'TANGERINE_Q1_INTRO_REVISED_02', 'syrus', 'ciepły', 'dialog Syrusa, nazwy własne (Frostgate, Indris)', {}),
    ('F02', 'TANGERINE_Q1_OUTRO_WIN_13', 'brynn', 'wzruszony', 'dialog Brynn, wielokropek, Frostgate', {}),
    ('F03', 'TANGERINE_Q1_OUTRO_WIN_08', 'galaden', 'poważny', 'dialog Galadena, myślnik', {}),
    ('F04', 'TANGERINE_Q1_INTRO_REVISED_22A', 'vaerix', 'chłodny', 'dialog Vaerix, formy neutralne', {}),
    ('F05', 'TANGERINE_Q1_OUTRO_WIN_14', 'syrus', 'radosny', 'okrzyk Syrusa', {}),
    ('F06', 'TANGERINE_Q1_INTRO_REVISED_01', 'narrator', 'spokojny', 'narracja opisowa', {}),
    ('F07', 'Q1_THE_NIGHT_PASSES', 'narrator', 'napięty', 'długi komunikat fabularny, {0} = bohater', {'0': 'Brynn'}),
    ('F08', 'BOOKSHELF_CHOICE_BOTTLES_FALSE_2', 'narrator', 'neutralny', 'kursywa + reguła z liczbami i ikoną', {}),
    ('F09', 'ENEMY_ACTIVATION_BERSERKER_TACTIC_RAMPAGE', 'system', 'neutralny', 'aktywacja wroga, {0} wróg, {1} bohater',
     {'0': 'Berserker', '1': 'Brynn'}),
    ('F10', 'Q1_OBJECTIVE_5', 'system', 'neutralny', 'cel misji z licznikiem', {'0': '2'}),
    ('F11', 'TANGERINE_Q1_INTRO_REVISED_16_17B', 'system', 'neutralny', 'opcja wyboru z cytatem bohaterki (D20)', {}),
    ('F12', 'ENEMY_CONFUSION_ACTIVATION_OFFMAP_2', 'narrator', 'neutralny', 'komunikat z dwoma nazwami wrogów (D16)',
     {'0': 'Berserker', '1': 'Ne’Krul'}),
]
# Głos systemowy (D20) na razie korzysta z referencji narratora; docelowy głos w E7 (D22).
REF_VOICE = {'system': 'narrator'}
# Warianty wymowy nazw (decyzja u): zapis fonetyczny albo nazwa wygenerowana po angielsku i wklejona.
NAMES = {'Frostgate': 'Frostgejt'}

TAKES = 3
SEED = 4242
LONG = 260          # dłuższe kawałki dzielimy na zdania tak samo dla każdego modelu
SENTENCE_GAP = 0.35
PIECE_GAP = 0.06

# Runda 2 (po odsłuchu): OmniVoice szybciej i ze słabszym akcentem (CFG niżej niż domyślne 2,0) dla dialogów
# bohaterów oraz narratora i systemu w trakcie rozgrywki. Narracja scen między rozgrywkami (F06, F11) bez zmian.
PACE_FRAGMENTS = ('F01', 'F02', 'F03', 'F04', 'F05', 'F07', 'F08', 'F09', 'F10', 'F12')
PACE_GAP = 0.25
PACE_VARIANTS = [  # wariant, opis, post (speed), parametry generate() OmniVoice
    ('P1', 'tempo 1,2', {'speed': 1.2}, {}),
    ('P2', 'tempo 1,2, CFG 1,4 (słabszy akcent)', {'speed': 1.2}, {'guidance_scale': 1.4}),
    ('P3', 'tempo 1,35, CFG 1,4', {'speed': 1.35}, {'guidance_scale': 1.4}),
    ('P4', 'jak P2, 16 kroków zamiast 32 (szybsze generowanie)', {'speed': 1.2}, {'guidance_scale': 1.4, 'num_step': 16}),
]


def split_sentences(text, min_len=40, max_len=LONG):
    parts = re.split(r'(?<=[.!?…])\s+', text)
    chunks = []
    for p in parts:
        if chunks and (len(chunks[-1]) < min_len or len(p) < min_len // 2) and len(chunks[-1]) + len(p) < max_len:
            chunks[-1] += ' ' + p
        else:
            chunks.append(p)
    return chunks


def fill(template, values):
    return re.sub(r'\{(\d)\}', lambda m: values.get(m.group(1), m.group(0)), template)


def piece(text, voice, emotion, lang='pl', gap=PIECE_GAP):
    return {'text': text, 'voice': voice, 'emotion': emotion, 'lang': lang, 'gap': gap}


def whole(text, voice, emotion, gap=SENTENCE_GAP):
    """Cała kwestia; długie dzielone na zdania z pauzą jak w docelowym pipeline."""
    chunks = split_sentences(text) if len(text) > LONG else [text]
    return [piece(c, voice, emotion, gap=gap) for c in chunks]


def build_jobs(fragments):
    jobs = []
    for i, f in enumerate(fragments):
        fid, voice, emo, text = f['id'], f['voice'], f['emotion'], f['text']
        seed = SEED + 100 * i

        def job(variant, pieces, takes=1, note='', post=None, models=None, gen=None):
            j = {'id': '%s_%s' % (fid, variant), 'fragment': fid, 'variant': variant, 'note': note,
                 'pieces': pieces, 'takes': takes, 'seed': seed, 'post': post or {}}
            if models:  # zadanie tylko dla wskazanych modeli, z parametrami generowania
                j.update(models=models, gen=gen or {})
            jobs.append(j)
        job('A', whole(text, voice, 'neutralny'), TAKES, 'referencja neutralna')
        if emo != 'neutralny':
            job('B', whole(text, voice, emo), TAKES, 'referencja emocjonalna: ' + emo)
        if voice == 'narrator' and emo != 'neutralny':
            sents = split_sentences(text, min_len=1, max_len=1)
            if len(sents) > 1:
                job('T2', [piece(s, voice, 'neutralny', gap=0.5) for s in sents], 1, 'zdania osobno, pauza 0,5 s')
                job('T3', [piece(s, voice, 'neutralny', gap=0.4) for s in sents], 1,
                    'zdania osobno, pauza 0,4 s, tempo 0,9', {'speed': 0.9})
        for name, phon in NAMES.items():
            if name in text:
                job('N1', whole(text.replace(name, phon), voice, 'neutralny'), 1, 'nazwa zapisana fonetycznie')
                parts = text.split(name)
                pieces = []
                for k, p in enumerate(parts):
                    p = p.strip()
                    if k > 0:
                        tail_gap = SENTENCE_GAP if p[:1] in '.!?' else 0.18 if p[:1] in ',;:' else PIECE_GAP
                        pieces.append(piece(name, voice, 'neutralny', lang='en', gap=tail_gap))
                        p = p.lstrip('.,;: ').strip()
                    if p and p not in '.!?':
                        pieces.append(piece(p, voice, 'neutralny'))
                job('N2', pieces, 1, 'nazwa wygenerowana po angielsku i wklejona')
        if f.get('template_pieces'):
            job('S', [piece(t, voice, 'neutralny') for t in f['template_pieces']], 1,
                'sklejone z fragmentów: szablon + nazwy osobno (D16)')
        if f.get('quote'):
            q, rest, speaker = f['quote']
            job('Q', [piece(q, speaker, 'neutralny', gap=0.15), piece(rest, 'narrator', 'neutralny')], 1,
                'cytat głosem bohaterki, dopowiedzenie narratorem (D20)')
        if fid in PACE_FRAGMENTS:
            for variant, note, post, gen in PACE_VARIANTS:
                job(variant, whole(text, voice, 'neutralny', gap=PACE_GAP), 1, note, post, ['omnivoice'], gen)
    return jobs


def load_fragments():
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    out = []
    for fid, key, voice, emo, desc, values in FRAGMENTS:
        raw = terms[key]['text']
        f = {'id': fid, 'key': key, 'voice': voice, 'emotion': emo, 'desc': desc, 'values': values,
             'text': normalize(fill(raw, values))}
        if fid == 'F12':
            # Szablon dzielimy na stałe kawałki i wartości {n}; każdy kawałek generowany osobno.
            tpl = normalize(raw)
            f['template_pieces'] = [p.strip() for p in re.split(r'(\{\d\})', fill(tpl, {})) if p.strip()]
            merged = []
            for p in f['template_pieces']:
                p = values.get(p[1], p) if re.fullmatch(r'\{\d\}', p) else p
                if merged and re.fullmatch(r'[.,!?…]+', p):
                    merged[-1] += p  # sama interpunkcja dokleja się do poprzedniego kawałka
                else:
                    merged.append(p)
            f['template_pieces'] = merged
        if fid == 'F11':
            m = re.match(r'^–\s*(.+?)\s*–\s*(.+)$', f['text'])
            if m:
                f['quote'] = (m.group(1).rstrip(',') + '.', m.group(2)[0].upper() + m.group(2)[1:], 'brynn')
        out.append(f)
    return out


def build_refs():
    """Referencje emocjonalne: 2–4 okrzyki tego samego typu, sklejone do 6–12 s (bohaterowie)
    albo wycinek przerywnika (narrator). Neutralne referencje to istniejące work/voices/refs/<głos>.wav."""
    import librosa
    import numpy as np
    import soundfile as sf
    os.makedirs(REFS, exist_ok=True)
    clips = json.load(open(os.path.join(VOICES_DIR, 'analysis.json'), encoding='utf-8'))
    sr = 24000
    refs = {}

    def save(name, wav, sources):
        path = os.path.join(REFS, name + '.wav')
        sf.write(path, wav, sr, subtype='PCM_16')
        return {'wav': os.path.relpath(path, ROOT).replace(os.sep, '/'), 'seconds': round(len(wav) / sr, 2),
                'sources': sources}

    for voice in ('syrus', 'brynn', 'galaden', 'vaerix', 'narrator'):
        neutral = os.path.join(VOICES_DIR, 'refs', voice + '.wav')
        refs.setdefault(voice, {})['neutralny'] = {'wav': os.path.relpath(neutral, ROOT).replace(os.sep, '/'),
                                                  'sources': ['work/voices/refs/%s.wav' % voice]}
    for voice in ('syrus', 'brynn', 'galaden', 'vaerix'):
        own = [c for c in clips if c['group'] == 'heroes' and c['speaker'].lower() in (voice, 'vearix' if voice == 'vaerix' else voice)
               and c.get('f0_median') and c.get('speech_s', 0) >= 1.0]
        for emo, (kinds, level) in HERO_EMOTION_CLIPS.items():
            if emo == 'neutralny':
                continue
            pool = [c for c in own if c['kind'].split('_', 1)[-1] in kinds or any(k in c['name'] for k in kinds)]
            key = lambda c: c.get('arousal') or 0.0  # noqa: E731
            pool.sort(key=key, reverse=(level == 'high'))
            if level == 'mid':
                pool.sort(key=lambda c: abs(key(c)))
            wav, used = [], []
            for c in pool:
                y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=sr, mono=True)
                y, _ = librosa.effects.trim(y, top_db=40)
                wav += [y, np.zeros(int(0.25 * sr), np.float32)]
                used.append(c['name'])
                if sum(len(x) for x in wav) / sr >= 9.0 or len(used) >= 4:
                    break
            if used:
                refs[voice][emo] = save('%s__%s' % (voice, emo), np.concatenate(wav[:-1]), used)
    for emo, (name, a, b) in NARRATOR_EMOTION_SOURCES.items():
        y, _ = librosa.load(os.path.join(VOICES_DIR, 'wav', 'cutscenes', name), sr=sr, mono=True, offset=a, duration=b - a)
        refs['narrator'][emo] = save('narrator__' + emo, y, ['%s @ %.1f–%.1f s' % (name, a, b)])
    return refs


def transcribe(refs):
    """Transkrypcje referencji (OmniVoice wymaga ref_text)."""
    import librosa
    import torch
    from transformers import pipeline
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', torch_dtype=torch.float16,
                   device='cuda')
    for voice, by_emo in refs.items():
        for emo, r in by_emo.items():
            y, _ = librosa.load(os.path.join(ROOT, r['wav']), sr=16000, mono=True)
            r['text'] = asr({'raw': y, 'sampling_rate': 16000}, return_timestamps=True,
                            generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text'].strip()
            print(voice, emo, len(r['text']), file=sys.stderr, flush=True)


SHORT_MAX_S = 10.0  # OmniVoice zaleca referencje 3–10 s
SHORT_MIN_S = 4.0


def short_prompts(refs, voices=('narrator',)):
    """Krótkie referencje z transkrypcją zgodną z audio, dla modeli, które jej używają (OmniVoice).

    Referencje narratora to ciągłe wycinki przerywników z muzyką pod spodem, ucięte w środku mowy.
    OmniVoice dostawał transkrypcję niezgodną z audio i przed właściwym tekstem dopowiadał jej końcówkę.
    Tniemy według znaczników czasu słów z Whispera: od początku pierwszego pełnego zdania (gdy nagranie
    zaczyna się w środku mowy) do końca ostatniego zdania, przecinka albo pauzy przed SHORT_MAX_S."""
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from transformers import pipeline
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', torch_dtype=torch.float16,
                   device='cuda')
    for voice in voices:
        for emo, r in refs[voice].items():
            src = os.path.join(ROOT, r['wav'])
            y16, _ = librosa.load(src, sr=16000, mono=True)
            chunks = asr({'raw': y16, 'sampling_rate': 16000}, return_timestamps='word',
                         generate_kwargs={'language': 'polish', 'task': 'transcribe'})['chunks']
            words = [(c['text'], c['timestamp'][0], c['timestamp'][1] or c['timestamp'][0]) for c in chunks]
            nxt = [w[1] for w in words[1:]] + [len(y16) / 16000]
            first = 0
            if words[0][1] < 0.1:  # mowa od pierwszej próbki: pierwsze słowo może być ucięte
                ends = [i for i, w in enumerate(words) if w[0].rstrip().endswith(('.', '!', '?'))]
                if ends and ends[0] + 1 < len(words) and words[ends[0] + 1][1] + SHORT_MIN_S <= SHORT_MAX_S:
                    first = ends[0] + 1
            start = max(0.0, words[first][1] - 0.05)

            def ok(i, marks):
                w = words[i]
                return (w[2] - start <= SHORT_MAX_S and w[2] - start >= SHORT_MIN_S
                        and (w[0].rstrip().endswith(marks) or nxt[i] - w[2] >= 0.15))
            cands = [i for i in range(first, len(words)) if ok(i, ('.', '!', '?'))] or \
                    [i for i in range(first, len(words)) if ok(i, ('.', '!', '?', ',', ';', ':'))] or \
                    [i for i in range(first, len(words)) if words[i][2] - start <= SHORT_MAX_S]
            last = cands[-1]
            end = min(words[last][2] + 0.15, nxt[last])
            y, sr = sf.read(src, dtype='float32')
            y = y[int(start * sr):int(end * sr)]
            fade = int(0.02 * sr)
            y[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
            y[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
            name = '%s__%s__short' % (voice, emo)
            sf.write(os.path.join(REFS, name + '.wav'), y, sr, subtype='PCM_16')
            r['short'] = {'wav': os.path.relpath(os.path.join(REFS, name + '.wav'), ROOT).replace(os.sep, '/'),
                          'text': ''.join(w[0] for w in words[first:last + 1]).strip(),
                          'span': [round(start, 2), round(end, 2)]}
            print(voice, emo, 'krótka referencja %.1f–%.1f s, słów %d' % (start, end, last + 1 - first), file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--transcribe', action='store_true')
    ap.add_argument('--short-prompts', action='store_true',
                    help='tylko dopisz do istniejącego set.json krótkie referencje narratora (OmniVoice)')
    ap.add_argument('--jobs-only', action='store_true', help='przebuduj tylko listę zadań z fragmentów w set.json')
    a = ap.parse_args()
    os.environ.setdefault('HF_HOME', os.path.join(ROOT, 'work', 'hf_cache'))
    os.makedirs(BAKE, exist_ok=True)
    path = os.path.join(BAKE, 'set.json')
    old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    if a.short_prompts or a.jobs_only:
        if a.short_prompts:
            short_prompts(old['refs'])
        else:
            old['jobs'] = build_jobs(old['fragments'])
            print('zadania: %d' % len(old['jobs']))
        json.dump(old, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return
    fragments = load_fragments()
    refs = build_refs()
    for voice, by_emo in old.get('refs', {}).items():  # zachowaj wcześniejsze transkrypcje i krótkie referencje
        for emo, r in by_emo.items():
            if 'text' in r and emo in refs.get(voice, {}) and refs[voice][emo]['wav'] == r['wav']:
                refs[voice][emo].update({k: r[k] for k in ('text', 'short') if k in r})
    if a.transcribe:
        transcribe(refs)
    data = {'emotions': EMOTIONS, 'ref_voice': REF_VOICE, 'fragments': fragments, 'refs': refs,
            'jobs': build_jobs(fragments)}
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n_pieces = sum(len(j['pieces']) * j['takes'] for j in data['jobs'])
    print('fragmenty: %d, zadania: %d, generacji na model: %d, referencje: %d' % (
        len(fragments), len(data['jobs']), n_pieces, sum(len(v) for v in refs.values())))


if __name__ == '__main__':
    main()
