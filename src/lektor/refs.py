"""Referencje głosów dla OmniVoice (D33): wycinek nagrania dubbingu do 10 s z transkrypcją z tego samego odcinka.

Źródła to neutralne referencje z analysis/tools/extract_voices.py (work/voices/refs/<głos>.wav, 11–15 s).
Tniemy według znaczników czasu słów z Whispera na granicy zdania, przecinka albo pauzy. Transkrypcja
niezgodna z audio sprawia, że model przed właściwym tekstem dopowiada jej końcówkę (E0, BAKEOFF.md).
"""
import hashlib
import json
import os
import sys

from . import paths

VOICES = ('narrator', 'syrus', 'brynn', 'galaden', 'vaerix', 'kehli', 'chance', 'nekrul')
MAX_S = 10.0    # OmniVoice zaleca referencje 3–10 s
MIN_S = 4.0
SENTENCE = ('.', '!', '?')
CLAUSE = SENTENCE + (',', ';', ':')
GAP_S = 0.15    # pauza po słowie, na której wolno ciąć


def cut_span(words, total):
    """Odcinek do wycięcia: (pierwsze słowo, ostatnie słowo, start s, koniec s).

    words: [(tekst, początek, koniec)]. Gdy mowa zaczyna się od pierwszej próbki, pierwsze słowo może być
    ucięte, więc zaczynamy od następnego zdania (jeśli zostaje na nie miejsce)."""
    nxt = [w[1] for w in words[1:]] + [total]
    first = 0
    if words[0][1] < 0.1:
        ends = [i for i, w in enumerate(words) if w[0].rstrip().endswith(SENTENCE)]
        if ends and ends[0] + 1 < len(words) and words[ends[0] + 1][1] + MIN_S <= MAX_S:
            first = ends[0] + 1
    start = max(0.0, words[first][1] - 0.05)

    def ok(i, marks):
        w = words[i]
        return MIN_S <= w[2] - start <= MAX_S and (w[0].rstrip().endswith(marks) or nxt[i] - w[2] >= GAP_S)
    idx = range(first, len(words))
    cands = [i for i in idx if ok(i, SENTENCE)] or [i for i in idx if ok(i, CLAUSE)] or \
        [i for i in idx if words[i][2] - start <= MAX_S]
    last = cands[-1]
    return first, last, start, min(words[last][2] + GAP_S, nxt[last])


def build(voices=VOICES):
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from transformers import pipeline
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    os.makedirs(paths.REFS, exist_ok=True)
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', torch_dtype=torch.float16,
                   device='cuda')
    out = {}
    for voice in voices:
        src = os.path.join(paths.VOICES, 'refs', voice + '.wav')
        y16, _ = librosa.load(src, sr=16000, mono=True)
        chunks = asr({'raw': y16, 'sampling_rate': 16000}, return_timestamps='word',
                     generate_kwargs={'language': 'polish', 'task': 'transcribe'})['chunks']
        words = [(c['text'], c['timestamp'][0], c['timestamp'][1] or c['timestamp'][0]) for c in chunks]
        first, last, start, end = cut_span(words, len(y16) / 16000)
        y, sr = sf.read(src, dtype='float32')
        if y.ndim > 1:
            y = y.mean(axis=1)
        y = y[int(start * sr):int(end * sr)]
        fade = int(0.02 * sr)
        y[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        y[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
        wav = os.path.join(paths.REFS, voice + '.wav')
        sf.write(wav, y, sr, subtype='PCM_16')
        out[voice] = {'wav': paths.rel(wav), 'text': ''.join(w[0] for w in words[first:last + 1]).strip(),
                      'seconds': round(len(y) / sr, 2), 'source': '%s @ %.2f–%.2f s' % (paths.rel(src), start, end),
                      'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
        print('%-9s %.1f s, słów %d' % (voice, out[voice]['seconds'], last + 1 - first), file=sys.stderr, flush=True)
    path = os.path.join(paths.REFS, 'refs.json')
    old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    json.dump({**old, **out}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return out
