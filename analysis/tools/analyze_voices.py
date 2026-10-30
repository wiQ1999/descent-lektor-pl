"""Analiza polskich nagrań głosowych (z extract_voices.py) i wybór referencji do klonowania zero-shot.

Dla każdego pliku: czas czystej mowy (detekcja energii), poziom tła w pauzach, płaskość widma tła
(niska = tonalne tło, czyli prawdopodobnie muzyka), F0 (pYIN), głośność mowy, przesterowanie.
Charakter kwestii (spokojna / podniesiona / krzyk) liczony względem mediany danego mówcy.
Przerywniki łączy z napisami CutsceneModel (SoundEventName → zdarzenie Wwise → media; displayAt).

Wejście: work/voices/index.json, work/voices/wav/**, SoundbanksInfo.xml, bundle d3/cutscenes/*.
Wyjście (prywatne): work/voices/analysis.json, work/voices/refs/*.wav (+ refs.json z listą źródeł).

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/analyze_voices.py
"""
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import librosa
import numpy as np
import soundfile as sf
import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICES = os.path.join(ROOT, 'work', 'voices')
BUNDLES = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')
AUDIO = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'Audio', 'GeneratedSoundBanks', 'Windows')
OUT = os.path.join(ROOT, 'work', 'out')
SR = 16000
HOP = 160            # 10 ms
WIN = 480            # 30 ms
SPEECH_REL_DB = 30   # mowa: ramki nie niżej niż 30 dB pod szczytem…
SPEECH_ABS_DB = -50  # …i powyżej -50 dBFS
GAP_MERGE = 0.25     # pauzy krótsze niż 250 ms należą do segmentu mowy
NAME_FIX = {'Vearix': 'Vaerix', 'Nekrul': 'NeKrul'}
CALM_KINDS = {'QuestSelect', 'HeroSelect', 'GainTreasure', 'QuestWon', 'FeatComplete', 'QuestLost', 'Spawn', 'Taunt'}
REF_MIN, REF_MAX = 12.0, 18.0


def rms_db(y):
    frames = librosa.util.frame(np.pad(y, (WIN // 2, WIN // 2)), frame_length=WIN, hop_length=HOP)
    return 20 * np.log10(np.sqrt((frames ** 2).mean(axis=0)) + 1e-10)


def speech_segments(db):
    thr = max(SPEECH_ABS_DB, db.max() - SPEECH_REL_DB)
    on = db > thr
    segs, start = [], None
    for i, v in enumerate(np.append(on, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            segs.append([start, i])
            start = None
    merged = []
    for s in segs:
        if merged and (s[0] - merged[-1][1]) * HOP / SR < GAP_MERGE:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [(a * HOP / SR, b * HOP / SR) for a, b in merged if (b - a) * HOP / SR >= 0.1], on


def analyze_file(path):
    y_full, sr = sf.read(path, dtype='float32', always_2d=True)
    y_full = y_full.mean(axis=1)
    clip = float(np.mean(np.abs(y_full) >= 0.99))
    peak = float(20 * np.log10(np.abs(y_full).max() + 1e-10))
    y = librosa.resample(y_full, orig_sr=sr, target_sr=SR)
    db = rms_db(y)
    segs, on = speech_segments(db)
    speech = sum(b - a for a, b in segs)
    mask = np.zeros_like(on)
    for a, b in segs:
        mask[int(a * SR / HOP):int(b * SR / HOP)] = True
    pause = db[~mask]
    # ramki pauzy wewnątrz nagrania (bez ciszy przed pierwszą i po ostatniej frazie)
    inner = np.zeros_like(mask)
    if segs:
        inner[int(segs[0][0] * SR / HOP):int(segs[-1][1] * SR / HOP)] = True
    inner_pause = db[inner & ~mask]
    floor = float(np.median(pause)) if pause.size else None
    inner_floor = float(np.median(inner_pause)) if inner_pause.size >= 10 else None
    flat = None
    if inner_pause.size >= 20 and inner_floor is not None and inner_floor > -60:
        S = np.abs(librosa.stft(y, n_fft=1024, hop_length=HOP))[:, :len(mask)]
        sel = (inner & ~mask)[:S.shape[1]]
        flat = float(np.median(librosa.feature.spectral_flatness(S=S[:, sel])))
    # pYIN z krokiem 20 ms i rozdzielczością 0,2 półtonu: ~5× szybciej niż domyślnie, wystarcza do mediany F0
    f0, vflag, _ = librosa.pyin(y, fmin=60, fmax=600, sr=SR, frame_length=1024, hop_length=2 * HOP, resolution=0.2)
    f0v = f0[vflag & ~np.isnan(f0)]
    vmask = mask[::2][:len(vflag)]
    sp_db = db[mask]
    cent = librosa.feature.spectral_centroid(y=y, sr=SR, n_fft=1024, hop_length=HOP)[0][:len(mask)]
    return {
        'speech_s': round(speech, 2), 'segments': [(round(a, 2), round(b, 2)) for a, b in segs],
        'peak_dbfs': round(peak, 1), 'clip_ratio': clip,
        'speech_rms_db': round(float(np.mean(sp_db)), 1) if sp_db.size else None,
        'floor_db': round(floor, 1) if floor is not None else None,
        'inner_pause_db': round(inner_floor, 1) if inner_floor is not None else None,
        'inner_pause_flatness': round(flat, 4) if flat is not None else None,
        'f0_median': round(float(np.median(f0v)), 1) if f0v.size else None,
        'f0_p90': round(float(np.percentile(f0v, 90)), 1) if f0v.size else None,
        'voiced_ratio': round(float(vflag[:len(vmask)][vmask].mean()), 3) if vmask.any() else 0.0,
        'centroid_hz': round(float(np.median(cent[mask[:len(cent)]])), 0) if mask.any() else None,
    }


def cutscene_subtitles():
    """{media_id: {'cutscene', 'event', 'subtitles': [(klucz, displayAt)]}} dla przerywników z polskim VO."""
    ev_media = {}
    for sb in ET.parse(os.path.join(AUDIO, 'SoundbanksInfo.xml')).getroot().iter('SoundBank'):
        if sb.get('Language') == 'Polish' and sb.findtext('ShortName', '').startswith('Voice_Cutscenes'):
            for e in sb.iter('Event'):
                ev_media[e.get('Name')] = [int(x.get('Id')) for refs in e.iter('MediaRefs') for x in refs]
    m = json.load(open(os.path.join(BUNDLES, 'manifest.dat'), encoding='utf-8'))
    res, cache = {}, {}
    for b in m['bundleInfos']:
        if not b['name'].startswith('d3/cutscenes/'):
            continue
        for o in UnityPy.load(os.path.join(BUNDLES, b['filename'])).objects:
            if o.type.name != 'MonoBehaviour':
                continue
            t = o.read_typetree()
            if 'SoundEventName' not in t:
                continue
            for mid in ev_media.get(t['SoundEventName'], []):
                res.setdefault(mid, []).append({'cutscene': t.get('_id'), 'event': t['SoundEventName'],
                                                'subtitles': [(s['subtitleKeyName'], s['displayAt']) for s in t.get('Subtitles', [])]})
    return res


def classify(rows):
    """Charakter kwestii względem mediany mówcy: z-score F0 i głośności mowy."""
    by = defaultdict(list)
    for r in rows:
        by[r['speaker']].append(r)
    for spk, rs in by.items():
        f0 = np.array([r['f0_median'] or np.nan for r in rs], dtype=float)
        ld = np.array([r['speech_rms_db'] if r['speech_rms_db'] is not None else np.nan for r in rs], dtype=float)

        def z(a):
            med = np.nanmedian(a)
            mad = np.nanmedian(np.abs(a - med)) * 1.4826 or 1.0
            return (a - med) / mad
        arousal = np.nan_to_num(0.6 * z(np.log(f0)) + 0.4 * z(ld))
        for r, a in zip(rs, arousal):
            r['arousal'] = round(float(a), 2)
            r['character'] = 'spokojna' if a < 0.75 else 'podniesiona' if a < 2.0 else 'krzyk'


def build_ref(spk, rows, out_path):
    """Referencja 12–18 s: najspokojniejsze, czyste klipy mówcy sklejone z pauzą 0,3 s (lub okno z przerywnika)."""
    cand = [r for r in rows if r['speech_s'] >= 1.0 and r['clip_ratio'] < 1e-4 and r['voiced_ratio'] > 0.35]
    if not cand:  # np. Zachareth: pYIN prawie nie znajduje dźwięcznych ramek (charczenie/efekt), bierzemy co jest
        cand = [r for r in rows if r['speech_s'] >= 1.0 and r['clip_ratio'] < 1e-4]
    pref = [r for r in cand if r['kind'] in CALM_KINDS] or cand
    pref.sort(key=lambda r: (r['arousal'], -r['speech_s']))
    parts, used, total = [], [], 0.0
    for r in pref:
        if total >= REF_MIN:
            break
        y, sr = sf.read(os.path.join(ROOT, r['wav']), dtype='float32', always_2d=True)
        y = y.mean(axis=1)
        a, b = r['segments'][0][0], r['segments'][-1][1]
        seg = y[max(0, int((a - 0.05) * sr)):int((b + 0.1) * sr)]
        if total + len(seg) / sr > REF_MAX:
            continue
        parts += [seg, np.zeros(int(0.3 * sr), dtype='float32')]
        used.append(r['name'])
        total += len(seg) / sr + 0.3
    if not parts:
        return None
    y = np.concatenate(parts[:-1])
    y = y / (np.abs(y).max() + 1e-9) * 10 ** (-1 / 20)
    sf.write(out_path, y, sr, subtype='PCM_16')
    return {'file': os.path.relpath(out_path, ROOT).replace(os.sep, '/'), 'seconds': round(len(y) / sr, 2), 'sources': used}


def narrator_ref(rows, out_path):
    """Najstabilniejsze 12–18 s ciągłej mowy z przerywnika (najniższe tło, najmniejsza zmienność F0)."""
    best = None
    for r in rows:
        if r['group'] != 'cutscenes' or (r['inner_pause_db'] or -99) > -55:
            continue
        segs = r['segments']
        for i in range(len(segs)):
            for j in range(i, len(segs)):
                dur = segs[j][1] - segs[i][0]
                if dur > REF_MAX:
                    break
                if dur >= REF_MIN:
                    score = (r['inner_pause_db'] or -90) + 5 * abs(r['arousal'])
                    if best is None or score < best[0]:
                        best = (score, r, segs[i][0], segs[j][1])
    if not best:
        return None
    _, r, a, b = best
    y, sr = sf.read(os.path.join(ROOT, r['wav']), dtype='float32', always_2d=True)
    y = y.mean(axis=1)[int(max(0, a - 0.05) * sr):int((b + 0.1) * sr)]
    y = y / (np.abs(y).max() + 1e-9) * 10 ** (-1 / 20)
    sf.write(out_path, y, sr, subtype='PCM_16')
    return {'file': os.path.relpath(out_path, ROOT).replace(os.sep, '/'), 'seconds': round(len(y) / sr, 2),
            'sources': ['%s @ %.1f–%.1f s' % (r['name'], a, b)]}


def main():
    index = json.load(open(os.path.join(VOICES, 'index.json'), encoding='utf-8'))
    subs = cutscene_subtitles()
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    rows = []
    paths = [os.path.join(ROOT, it['wav']) for it in index]
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as ex:
        feats = list(ex.map(analyze_file, paths, chunksize=4))
    for i, (it, ft) in enumerate(zip(index, feats)):
        r = dict(it)
        r['speaker'] = 'narrator' if it['group'] == 'cutscenes' else NAME_FIX.get(it['speaker'], it['speaker'])
        r.update(ft)
        if it['id'] in subs:
            r['cutscenes'] = subs[it['id']]
            keys = [k for k, _ in subs[it['id']][0]['subtitles']]
            chars = sum(len(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', (terms.get(k) or {}).get('text') or '')).strip()) for k in keys)
            r['subtitle_chars'] = chars
            r['chars_per_speech_s'] = round(chars / r['speech_s'], 2) if r['speech_s'] else None
        rows.append(r)
    classify(rows)
    refs_dir = os.path.join(VOICES, 'refs')
    os.makedirs(refs_dir, exist_ok=True)
    refs = {}
    by = defaultdict(list)
    for r in rows:
        by[r['speaker']].append(r)
    for spk, rs in by.items():
        out = os.path.join(refs_dir, spk.lower() + '.wav')
        refs[spk] = narrator_ref(rs, out) if spk == 'narrator' else build_ref(spk, rs, out)
    json.dump(rows, open(os.path.join(VOICES, 'analysis.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(refs, open(os.path.join(refs_dir, 'refs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nreferencje:', {k: (v or {}).get('seconds') for k, v in refs.items()})


if __name__ == '__main__':
    main()
