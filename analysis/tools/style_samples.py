"""Próbki porównawcze do odsłuchu (QA decyzji b, c, e, f): tempo narratora, exaggeration według kategorii, głos systemowy.

Model jak w tts_bench.py: Chatterbox Multilingual, fp16, cfg_weight 0,3, offload modułów kondycjonowania.
Seed zależy tylko od kwestii, więc warianty jednej kwestii różnią się wyłącznie parametrem.

Grupy:
  tempo/   10 kwestii narratora: cała kwestia jednym przebiegiem vs zdania osobno z pauzą 0,35 / 0,5 s,
           oraz time-stretch 0,9 (WSOLA) dla obu sposobów; exaggeration 0,4.
  exag/    narracja 0,3/0,4/0,5; dialog 0,4/0,5/0,7; okrzyki 0,5/0,7/0,9; systemowy (narrator) 0,3/0,5.
Wyjście: work/qa_samples/<grupa>/*.wav + work/qa_samples/INDEX.md (z tekstami, nieśledzone).

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/style_samples.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts_bench as TB  # noqa: E402  (ustawia HF_HOME)

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

ROOT = TB.ROOT
QA = os.path.join(ROOT, 'work', 'qa_samples')
CFG = 0.3
DTYPE = torch.float16
HEROES = {'SYRUS': 'syrus', 'BRYNN': 'brynn', 'GALADEN': 'galaden', 'VAERIX': 'vaerix'}
TEMPO_REF = 'work/voices/wav/cutscenes/3_Wings_Of_War_VoiceOver.wav'


def spread(rs, n):
    if n <= 0:
        return []
    if len(rs) <= n:
        return rs
    step = len(rs) / n
    return [rs[int(i * step)] for i in range(n)]


def pick():
    terms = json.load(open(os.path.join(TB.OUT, 'pl_terms.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(TB.OUT, 'm1_scope.json'), encoding='utf-8'))['rows']
    text = {r['key']: TB.spoken(terms[r['key']]['text']) for r in rows}

    def of(cat, lo, hi, voice=None, group=None, pred=lambda t: True):
        return [r for r in rows if r['category'] == cat and lo <= r['chars'] <= hi and (voice is None or r['voice'] == voice)
                and (group is None or r['group'] == group) and pred(text[r['key']])]

    multi = lambda t: len(TB.split_sentences(t)) >= 2  # noqa: E731
    story = of('narracja_fabularna', 150, 420, pred=multi)[:5]
    tempo = story + spread(of('komunikat_questu', 150, 420, group='scene_q1', pred=multi), 10 - len(story))
    hero = lambda r: len(r['speakers']) == 1 and r['speakers'][0] in HEROES  # noqa: E731

    def one_per_hero(rs, n=3):
        """Po jednej kwestii na bohatera (różne głosy), potem dopełnienie rozłożone po liście."""
        picked = [next(r for r in rs if r['speakers'][0] == h) for h in HEROES if any(r['speakers'][0] == h for r in rs)][:n]
        rest = [r for r in rs if r not in picked]
        return picked + spread(rest, n - len(picked))
    calm = [r for r in of('dialog', 40, 200, pred=lambda t: '!' not in t) if hero(r)]
    shout = [r for r in of('dialog', 15, 140, pred=lambda t: '!' in t) if hero(r)]
    exag = []
    exag += [('narracja', r, 'narrator', (0.3, 0.4, 0.5)) for r in spread(of('narracja_fabularna', 80, 260) + of('zdarzenie', 80, 260), 3)]
    exag += [('dialog', r, HEROES[r['speakers'][0]], (0.4, 0.5, 0.7)) for r in one_per_hero(calm)]
    exag += [('okrzyk', r, HEROES[r['speakers'][0]], (0.5, 0.7, 0.9)) for r in one_per_hero(shout)]
    sys_rows = [of(c, 20, 220)[:1] for c in ('ui_system', 'walka_teren', 'cel_misji', 'system_nagroda')]
    sys_rows.append(of('opcja_wyboru', 20, 220, pred=lambda t: '„' in t or '"' in t)[:1])
    exag += [('systemowy', r, 'narrator', (0.3, 0.5)) for rs in sys_rows for r in rs]
    return text, tempo, exag


def wsola(x, speed, sr, frame_ms=30, tol_ms=10):
    """Time-stretch WSOLA: speed < 1 spowalnia bez zmiany wysokości głosu."""
    n = int(sr * frame_ms / 1000) // 2 * 2
    hs, tol = n // 2, int(sr * tol_ms / 1000)
    win = np.hanning(n).astype(np.float32)
    xp = np.concatenate([np.zeros(tol + n, np.float32), x.astype(np.float32), np.zeros(tol + 2 * n, np.float32)])
    frames = int(len(x) / speed / hs) + 1
    y = np.zeros(frames * hs + n, np.float32)
    w = np.zeros_like(y)
    prev = tol + n
    for k in range(frames):
        nominal = tol + n + int(k * hs * speed)
        if k == 0:
            pos = nominal
        else:
            template = xp[prev + hs: prev + hs + n]
            seg = xp[nominal - tol: nominal + tol + n]
            if len(seg) < n + 2 * tol or len(template) < n:
                break
            pos = nominal - tol + int(np.argmax(np.correlate(seg, template, 'valid')))
        y[k * hs: k * hs + n] += win * xp[pos: pos + n]
        w[k * hs: k * hs + n] += win
        prev = pos
    y = y / np.maximum(w, 1e-3)
    return y[: int(len(x) / speed)]


def trim(wav, sr):
    import librosa
    _, (a, b) = librosa.effects.trim(wav, top_db=40, frame_length=1024, hop_length=256)
    return wav[max(0, a - int(0.03 * sr)): b + int(0.05 * sr)]


def main():
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, Conditionals
    from chatterbox.models.t3.modules.cond_enc import T3Cond
    text, tempo, exag = pick()
    TB.VOICES.update({v: v + '.wav' for v in HEROES.values()})
    model = ChatterboxMultilingualTTS.from_pretrained(device='cuda')
    conds, _ = TB.load_conds(model, Conditionals)
    TB.offload_conditioning(model)
    model.t3.to(dtype=DTYPE)
    sr = model.sr

    class Cond:
        def __init__(self, base, e):
            t = base.t3
            self.gen = base.gen
            self.t3 = T3Cond(speaker_emb=t.speaker_emb, cond_prompt_speech_tokens=t.cond_prompt_speech_tokens,
                             emotion_adv=e * torch.ones(1, 1, 1)).to(device='cuda')

    def gen(voice, txt, e, seed):
        torch.manual_seed(seed)
        wav, _ = TB.synth(model, Cond(conds[voice], e), txt, CFG, DTYPE)
        return trim(wav, sr)

    def save(group, name, wav, info):
        os.makedirs(os.path.join(QA, group), exist_ok=True)
        path = os.path.join(QA, group, name + '.wav')
        sf.write(path, wav, sr, subtype='PCM_16')
        info.update(file=os.path.relpath(path, ROOT).replace(os.sep, '/'), duration=round(len(wav) / sr, 2),
                    cps=round(info['chars'] / (len(wav) / sr), 1))
        index.append(info)
        print(group, name, info['duration'], info['cps'], file=sys.stderr, flush=True)

    index = []
    TB.synth(model, Cond(conds['narrator'], 0.5), 'Rozgrzewka.', CFG, DTYPE)
    for i, r in enumerate(tempo, 1):
        t, seed, base = text[r['key']], TB.SEED + 100 + i, {'group': 'tempo', 'key': r['key'], 'chars': len(text[r['key']])}
        whole = gen('narrator', t, 0.4, seed)
        sents = [gen('narrator', s, 0.4, seed) for s in TB.split_sentences(t)]

        def join(p):
            gap = np.zeros(int(p * sr), np.float32)
            return np.concatenate([x for s in sents for x in (s, gap)][:-1])
        nid = 't%02d' % i
        save('tempo', nid + '_a_calosc', whole, dict(base, variant='cała kwestia', text=t))
        save('tempo', nid + '_b_zdania_pauza035', join(0.35), dict(base, variant='zdania, pauza 0,35 s'))
        save('tempo', nid + '_c_zdania_pauza050', join(0.5), dict(base, variant='zdania, pauza 0,5 s'))
        save('tempo', nid + '_d_zdania_pauza040_stretch090', wsola(join(0.4), 0.9, sr), dict(base, variant='zdania, pauza 0,4 s + stretch 0,9'))
        save('tempo', nid + '_e_calosc_stretch090', wsola(whole, 0.9, sr), dict(base, variant='cała kwestia + stretch 0,9'))
    for i, (cat, r, voice, levels) in enumerate(exag, 1):
        t = text[r['key']]
        for e in levels:
            save('exag', 'x%02d_%s_%s_e%s' % (i, cat, voice, str(e).replace('.', '')), gen(voice, t, e, TB.SEED + 200 + i),
                 {'group': 'exag', 'key': r['key'], 'chars': len(t), 'category': cat, 'voice': voice,
                  'variant': 'exaggeration %s' % str(e).replace('.', ','), 'text': t})
    json.dump(index, open(os.path.join(QA, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    write_index(index)


def write_index(index):
    out = ['# Próbki do odsłuchu', '',
           'fp16, cfg_weight 0,3. Odniesienie tempa — oryginalny lektor: `analysis/%s` (9–10 znaków/s z pauzami).' % TEMPO_REF, '']
    for group, title in (('tempo', 'Tempo narratora (exaggeration 0,4)'), ('exag', 'Exaggeration według kategorii')):
        out += ['## ' + title, '']
        last = None
        for it in (x for x in index if x['group'] == group):
            if it['key'] != last:
                head = ('**%s** · %s · %s · ' % (it['key'], it.get('category', 'narracja'), it.get('voice', 'narrator')))
                out += ['', head + (it.get('text') or ''), '']
                last = it['key']
            out.append('- `analysis/%s` · %s · %s s · %s znaków/s' % (it['file'], it['variant'], str(it['duration']).replace('.', ','),
                                                                   str(it['cps']).replace('.', ',')))
        out.append('')
    open(os.path.join(QA, 'INDEX.md'), 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
