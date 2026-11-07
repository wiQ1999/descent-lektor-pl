"""Ocenia próbki ElevenLabs tym samym automatem co E3: ASR, końcówka, tempo, barwa wobec referencji i F0.

Uruchamiać w .venv. Wypisuje same liczby, bez tekstów. Przykład:
    .venv/Scripts/python -I analysis/tools/elevenlabs/score_samples.py [plik ...]
Bez plików ocenia audio z analysis/work/elevenlabs/audio i nagranie OmniVoice wskazane w test-line.json.
"""
import glob
import json
import os
import sys

import librosa
import numpy as np

from lektor import evaluate, paths

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
WORK = os.path.join(ROOT, 'analysis', 'work', 'elevenlabs')
FIELDS = ('cer', 'tail_cut', 'missing', 'sim', 'cps_ratio', 'pause', 'seconds')


def median_f0(path):
    y, sr = librosa.load(path, sr=16000, mono=True)
    f0 = librosa.yin(y, fmin=70, fmax=500, sr=sr)
    voiced = f0[librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0][:len(f0)] > 0.01]
    return round(float(np.median(voiced))) if len(voiced) else None


def main():
    paths.use('m2')
    line = json.load(open(os.path.join(WORK, 'test-line.json'), encoding='utf-8'))
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(WORK, 'audio', '*.mp3'))) + [line['omnivoice']]
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    score = evaluate.Scorer(refs)
    rows = {}
    for path in files:
        result = score(path, line['text'], line['voice'], 1.0)
        row = {k: float(result[k]) if isinstance(result[k], np.floating) else result[k] for k in FIELDS if k in result}
        row['f0'] = median_f0(path)
        rows[os.path.basename(path)] = row
        print(os.path.basename(path)[:44], row, flush=True)
    with open(os.path.join(WORK, 'scores.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
