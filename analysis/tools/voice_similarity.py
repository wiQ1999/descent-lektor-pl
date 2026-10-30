"""Podobieństwo głosów (embedding VoiceEncoder z Chatterbox): czy przerywniki czyta jeden lektor
i czy któryś bohater/złoczyńca ma ten sam głos. Wynik: work/voices/similarity.json (same liczby).

Uruchomienie (z katalogu głównego repozytorium, po analyze_voices.py):
  .venv/Scripts/python -I analysis/tools/voice_similarity.py
"""
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('HF_HOME', os.path.join(ROOT, 'work', 'hf_cache'))

import librosa  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402
from chatterbox.models.voice_encoder import VoiceEncoder  # noqa: E402

VOICES = os.path.join(ROOT, 'work', 'voices')


def main():
    rows = json.load(open(os.path.join(VOICES, 'analysis.json'), encoding='utf-8'))
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()
    wavs = [librosa.load(os.path.join(ROOT, r['wav']), sr=16000)[0] for r in rows]
    emb = ve.embeds_from_wavs(wavs, sample_rate=16000)
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r['speaker']].append(i)
    cent = {s: emb[ix].mean(axis=0) / np.linalg.norm(emb[ix].mean(axis=0)) for s, ix in by.items()}
    res = {'intra_median': {}, 'nearest_other': {}}
    for s, ix in by.items():
        sims = emb[ix] @ emb[ix].T
        res['intra_median'][s] = round(float(np.median(sims[np.triu_indices(len(ix), 1)])), 3) if len(ix) > 1 else None
        others = sorted(((float(cent[s] @ cent[o]), o) for o in cent if o != s), reverse=True)[:3]
        res['nearest_other'][s] = [(o, round(v, 3)) for v, o in others]
    ci = by['narrator']
    res['cutscenes_vs_centroids'] = {
        rows[i]['name']: sorted(((round(float(emb[i] @ cent[s]), 3), s) for s in cent), reverse=True)[:3] for i in ci}
    json.dump(res, open(os.path.join(VOICES, 'similarity.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
