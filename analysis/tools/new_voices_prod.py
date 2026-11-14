"""Głosy mówców bez imienia w wersji produkcyjnej m4 (E17, D107): projekt OmniVoice z profili postaci.

Profil (analysis/tools/voice_designs_prod.json, pole `omni`): płeć, wiek, wysokość i szept oraz własne zdanie w stylu
postaci (nie tekst gry), z kontekstu wszystkich kwestii postaci. Głosy z t1 zostają przy referencjach t1. Każdy profil
ma trzy ziarna; wybór automatem (bez odsłuchu, QA 2026-11-14): najmniejszy CER z wysokością w zakresie płci, a z kilku
dobrych to, które leży najdalej od narratora, obsady (refs.json) i głosów już wybranych.

    <omni> -I analysis/tools/new_voices_prod.py design    # <omni> = "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"
    .venv/Scripts/python -I analysis/tools/new_voices_prod.py choose   # ASR, F0, barwa → choice.json
    .venv/Scripts/python -I analysis/tools/new_voices_prod.py adopt    # referencje do analysis/work/lektor/refs/ i refs.json

Wyniki w analysis/work/compare/prod/ (nieśledzone). Na konsolę idą liczby i identyfikatory.
"""
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import paths  # noqa: E402

OUT = os.path.join(ROOT, 'analysis', 'work', 'compare', 'prod')
SEEDS = (11, 23, 37)
MAX_CER = 0.08
F0_RANGE = {'male': (70, 200), 'female': (140, 400)}
CPS = 12.5      # znaki na sekundę referencji (długość generowania)

DESIGNS = os.path.join(ROOT, 'analysis', 'tools', 'voice_designs_prod.json')
# głos: (płeć, opis OmniVoice, zdanie w stylu postaci, ziarna); tylko profile z polem `omni` (bez głosów z t1).
# `seeds` w profilu: więcej ziaren dla głosu nieudanego albo za bliskiego innym.
VOICES = {v: (d['gender'], d['omni']['instruct'], d['omni']['style_text'], d['omni'].get('seeds', SEEDS))
          for v, d in json.load(open(DESIGNS, encoding='utf-8')).items() if not v.startswith('_') and isinstance(d['omni'], dict)}


def load(name, default=None):
    path = os.path.join(OUT, name)
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    json.dump(data, open(os.path.join(OUT, name), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def design():
    import npc_voices as N
    model = N.load_omnivoice()
    N.tokenizer_to_cpu(model)
    os.makedirs(os.path.join(OUT, 'scan'), exist_ok=True)
    scan = load('scan.json', {})
    for voice, (gender, instruct, text, seeds) in VOICES.items():
        for seed in seeds:
            name = '%s_s%d' % (voice, seed)
            wav = os.path.join(OUT, 'scan', name + '.wav')
            old = scan.get(name)
            if old and (old['instruct'], old['text']) == (instruct, text) and os.path.exists(wav):
                continue        # ten sam profil: próbka i pomiary zostają
            N.synth(model, wav, text, seed, instruct=instruct, duration=round(len(text) / CPS, 2))
            scan[name] = {'voice': voice, 'seed': seed, 'instruct': instruct, 'wav': paths.rel(wav), 'text': text}
            save('scan.json', scan)


def choose():
    import librosa
    import numpy as np
    import torch
    from huggingface_hub import hf_hub_download
    from chatterbox.models.voice_encoder import VoiceEncoder
    import npc_voices as N
    scan = load('scan.json')
    asr = N.load_asr()
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()

    def emb(y):
        e = ve.embeds_from_wavs([y], sample_rate=16000)[0]
        return e / np.linalg.norm(e)
    for c in scan.values():
        if 'cer' in c or c['voice'] not in VOICES:
            continue        # pomiary z poprzedniego przebiegu
        y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=16000)
        gender = VOICES[c['voice']][0]
        c['cer'] = round(N.cer(c['text'], asr({'raw': y, 'sampling_rate': 16000},
                                              generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']), 3)
        f0 = librosa.pyin(y, fmin=60, fmax=250 if gender == 'male' else 500, sr=16000)[0]
        c['f0'] = round(float(np.nanmedian(f0)), 0)
        c['emb'] = emb(y).tolist()
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    taken = {v: emb(librosa.load(os.path.join(ROOT, r['wav']), sr=16000)[0])     # narrator, obsada i głosy t1
             for v, r in refs.items() if v not in VOICES and r.get('wav') and os.path.exists(os.path.join(ROOT, r['wav']))}
    chosen = {}
    for voice in VOICES:
        lo, hi = F0_RANGE[VOICES[voice][0]]
        gender, instruct, text, seeds = VOICES[voice]
        mine = [n for n, c in scan.items() if c['voice'] == voice and c['seed'] in seeds
                and (c['instruct'], c['text']) == (instruct, text)]
        ok = [n for n in mine if scan[n]['cer'] <= MAX_CER and lo <= scan[n]['f0'] <= hi] or \
             sorted(mine, key=lambda n: scan[n]['cer'])[:1]

        def nearest(n):
            return max(float(np.dot(scan[n]['emb'], e)) for e in taken.values())
        best = min(ok, key=nearest)
        sim = nearest(best)
        taken[voice] = np.array(scan[best]['emb'])
        chosen[voice] = best
        print('%-14s %s  sim %.3f' % (voice, '  '.join('s%d CER %.2f F0 %3.0f%s' % (
            scan[n]['seed'], scan[n]['cer'], scan[n]['f0'], '*' if n == best else ' ') for n in sorted(mine)), sim))
    names = list(taken)
    sims = [(float(np.dot(taken[a], taken[b])), a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    sims = [x for x in sims if x[1] in VOICES or x[2] in VOICES]
    print('najbliższe pary:', ', '.join('%s~%s %.3f' % (a, b, s) for s, a, b in sorted(sims, reverse=True)[:8]))
    save('scan.json', scan)
    save('choice.json', chosen)


def adopt():
    import soundfile as sf
    scan, chosen = load('scan.json'), load('choice.json')
    path = os.path.join(paths.REFS, 'refs.json')
    refs = json.load(open(path, encoding='utf-8'))
    for voice, name in chosen.items():
        c = scan[name]
        wav = os.path.join(paths.REFS, voice + '.wav')
        shutil.copyfile(os.path.join(ROOT, c['wav']), wav)
        refs[voice] = {'wav': paths.rel(wav), 'text': c['text'], 'seconds': round(sf.info(wav).duration, 2),
                       'source': 'E17 (D107): projekt OmniVoice „%s”, ziarno %d' % (c['instruct'], c['seed']),
                       'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
        print('%-14s %-22s %5.1f s' % (voice, name, refs[voice]['seconds']))
    json.dump(refs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    commands = {'design': design, 'choose': choose, 'adopt': adopt}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    commands[sys.argv[1]]()
