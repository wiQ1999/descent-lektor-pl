"""Projektowanie głosów postaci NPC (OmniVoice voice design) i strona odsłuchu do QA obsady.

OmniVoice opisuje głos tylko płcią, wiekiem i wysokością. Charakter postaci nadajemy referencją: własnym
zdaniem napisanym w stylu postaci (nie tekstem gry) i tempem. Klony przejmują sposób mówienia z referencji.
Opis postaci bierzemy z portretu z okna dialogu (d3/storymessagecharacters, tekstura *_Dialogue).

Kroki (wyniki prywatne w analysis/work/lektor/voice_design/):
  .venv/Scripts/python -I analysis/tools/npc_voices.py portrait           # portrety z kopii gry
  <omnivoice>/Scripts/python -I analysis/tools/npc_voices.py scan          # kandydaci: opis × ziarno
  .venv/Scripts/python -I analysis/tools/npc_voices.py select             # ASR, F0, 4 najbardziej różne barwy
  <omnivoice>/Scripts/python -I analysis/tools/npc_voices.py clone         # 2 kwestie z gry na kandydata + index.html
  .venv/Scripts/python -I analysis/tools/npc_voices.py adopt adelynn adelynn_d1_s11   # wybór z QA → refs.json
<omnivoice> = %LOCALAPPDATA%/LektorPL/envs/omnivoice
"""
import html
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import direction as D  # noqa: E402
from lektor import paths  # noqa: E402

OUT = os.path.join(paths.OUT, 'voice_design')
CHARACTERS = {
    'adelynn': {
        'texture': 'BaronessAdelynn_Dialogue', 'gender': 'female',
        'brief': 'starsza kobieta, szlachcianka, bardzo poukładana; mówi zbyt pewnie siebie, szlacheckim tonem',
        'designs': ['female, elderly, low pitch', 'female, elderly, moderate pitch', 'female, elderly, very low pitch',
                    'female, middle-aged, low pitch'],
        'style_text': 'Oczywiście, że wiem, co robię. Mój ród rządzi tu od pokoleń i nikt nie będzie mnie pouczał.',
        'ref_cps': 9.5,     # wolno i dostojnie
    },
    'ronan': {
        'texture': 'Ronan_Dialogue', 'gender': 'male',
        'brief': 'dojrzały, umięśniony, rosły chłop, wygląda jak wiking; głos waleczny, w szalonym tonie',
        'designs': ['male, middle-aged, very low pitch', 'male, middle-aged, low pitch', 'male, middle-aged, moderate pitch',
                    'male, elderly, very low pitch'],
        'style_text': 'Ha! Niech przyjdą wszyscy naraz! Rozbiję im łby, a potem wypiję za ich zdrowie!',
        'ref_cps': 11.5,    # szybko, z energią
    },
}
SEEDS = (11, 23, 37)
PICK = 4
MAX_CER = 0.10
F0_RANGE = {'female': (140, 330), 'male': (65, 190)}


def gen_settings():
    return {'num_step': D.MODEL['num_step'], 'guidance_scale': D.MODEL['guidance_scale']}


def load_omnivoice():
    import torch
    from omnivoice import OmniVoice
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    return OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cuda:0', dtype=torch.float16)


def synth(model, path, text, seed, **kw):
    import numpy as np
    import soundfile as sf
    import torch
    torch.manual_seed(seed)
    t0 = time.perf_counter()
    wav = np.asarray(model.generate(text=text, language='pl', **kw, **gen_settings())[0], np.float32).reshape(-1)
    sf.write(path, wav, model.sampling_rate, subtype='PCM_16')
    print('%-32s %.1f s audio, %.0f s' % (os.path.basename(path), len(wav) / model.sampling_rate,
                                         time.perf_counter() - t0), file=sys.stderr, flush=True)


def portrait():
    import UnityPy
    from lektor import game as G
    g = G.Game()
    env = UnityPy.load(os.path.join(paths.BUNDLES, g.files['d3/storymessagecharacters']))
    want = {c['texture']: v for v, c in CHARACTERS.items()}
    os.makedirs(OUT, exist_ok=True)
    for o in env.objects:
        if o.type.name == 'Texture2D':
            d = o.read()
            if d.m_Name in want:
                d.image.save(os.path.join(OUT, want[d.m_Name] + '.png'))
                print(want[d.m_Name], d.image.size)


def scan():
    model = load_omnivoice()
    os.makedirs(os.path.join(OUT, 'scan'), exist_ok=True)
    out = {}
    for voice, c in CHARACTERS.items():
        for i, instruct in enumerate(c['designs'], 1):
            for seed in SEEDS:
                name = '%s_d%d_s%d' % (voice, i, seed)
                path = os.path.join(OUT, 'scan', name + '.wav')
                if not os.path.exists(path):
                    synth(model, path, c['style_text'], seed, instruct=instruct,
                          duration=round(len(c['style_text']) / c['ref_cps'], 2))
                out[name] = {'voice': voice, 'instruct': instruct, 'seed': seed, 'wav': paths.rel(path)}
    json.dump(out, open(os.path.join(OUT, 'scan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def words(s):
    return re.sub(r'[^\w ]', '', unicodedata.normalize('NFC', s.lower())).split()


def cer(ref, hyp):
    a, b = ' '.join(words(ref)), ' '.join(words(hyp))
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1] / max(1, len(a))


def select():
    """Odrzuca kandydatów z błędami (CER) i wysokością spoza płci, z reszty wybiera PICK najbardziej różnych barw."""
    import librosa
    import numpy as np
    import torch
    from huggingface_hub import hf_hub_download
    from transformers import pipeline
    from chatterbox.models.voice_encoder import VoiceEncoder
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    sys.stdout.reconfigure(encoding='utf-8')
    cands = json.load(open(os.path.join(OUT, 'scan.json'), encoding='utf-8'))
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', dtype=torch.float16,
                   device='cuda')
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()
    for name, c in cands.items():
        y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=16000)
        text = CHARACTERS[c['voice']]['style_text']
        c['cer'] = round(cer(text, asr({'raw': y, 'sampling_rate': 16000}, generate_kwargs={'language': 'polish'})['text']), 3)
        f0 = librosa.pyin(y, fmin=60, fmax=500, sr=16000)[0]
        c['f0'] = round(float(np.nanmedian(f0)), 0)
        e = ve.embeds_from_wavs([y], sample_rate=16000)[0]
        c['emb'] = (e / np.linalg.norm(e)).tolist()
    picked = {}
    for voice, spec in CHARACTERS.items():
        lo, hi = F0_RANGE[spec['gender']]
        ok = sorted((n for n, c in cands.items() if c['voice'] == voice and c['cer'] <= MAX_CER and lo <= c['f0'] <= hi),
                    key=lambda n: cands[n]['cer'])
        chosen = ok[:1]
        while ok and len(chosen) < min(PICK, len(ok)):
            far = max((n for n in ok if n not in chosen), key=lambda n: min(
                1 - float(np.dot(cands[n]['emb'], cands[m]['emb'])) for m in chosen))
            chosen.append(far)
        picked[voice] = chosen
        for n, c in sorted(cands.items()):
            if c['voice'] == voice:
                print('%-18s %-36s CER %.2f  F0 %4.0f Hz %s' % (n, c['instruct'], c['cer'], c['f0'], '*' if n in chosen else ''))
    for c in cands.values():
        c.pop('emb')
    json.dump({'candidates': cands, 'picked': picked}, open(os.path.join(OUT, 'select.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


def pick_lines(con, voice):
    """Dwie kwestie postaci z bazy: krótsza (60–120 znaków) i najdłuższa."""
    rows = con.execute('SELECT s.key, s.text FROM segments s WHERE s.voice = ? AND s.kind = ? ORDER BY length(s.text)',
                       (voice, 'text')).fetchall()
    short = [r for r in rows if 60 <= len(r[1]) <= 120] or rows[:1]
    first = short[len(short) // 2]
    rest = [r for r in rows if r[0] != first[0]]
    return first, rest[-1] if rest else first


def clone():
    model = load_omnivoice()
    sel = json.load(open(os.path.join(OUT, 'select.json'), encoding='utf-8'))
    con = sqlite3.connect(paths.DB)
    os.makedirs(os.path.join(OUT, 'clone'), exist_ok=True)
    rows = []
    for voice, names in sel['picked'].items():
        spec = CHARACTERS[voice]
        lines = pick_lines(con, voice)
        rows.append('<h2 class="who">%s</h2><p>%s</p><img src="%s.png" alt="">' % (
            voice.capitalize(), html.escape(spec['brief']), voice))
        for n, name in enumerate(names, 1):
            c = sel['candidates'][name]
            prompt = model.create_voice_clone_prompt(os.path.join(ROOT, c['wav']), spec['style_text'])
            audio = [c['wav'].split('voice_design/', 1)[1]]
            for i, (key, text) in enumerate(lines):
                path = os.path.join(OUT, 'clone', '%s_%s.wav' % (name, 'ab'[i]))
                if not os.path.exists(path):
                    synth(model, path, text, 1234, voice_clone_prompt=prompt, speed=D.tempo('dialog', len(text))[0])
                audio.append('clone/' + os.path.basename(path))
            rows.append('<section><h3>%s %d</h3><p>%s · ziarno %d · F0 %.0f Hz</p>'
                        '<p>referencja <audio controls src="%s"></audio></p>'
                        '<p><code>%s</code> <audio controls src="%s"></audio></p>'
                        '<p><code>%s</code> <audio controls src="%s"></audio></p></section>' % (
                            voice.capitalize(), n, html.escape(c['instruct']), c['seed'], c['f0'], audio[0],
                            lines[0][0], audio[1], lines[1][0], audio[2]))
    page = ('<!doctype html><meta charset="utf-8"><title>Obsada NPC</title><style>body{font:15px system-ui;'
            'max-width:820px;margin:24px auto;padding:0 16px}section{border:1px solid #ccc;border-radius:8px;'
            'padding:8px 16px;margin:12px 0}audio{vertical-align:middle;width:420px;max-width:100%}'
            'img{width:320px;max-width:100%;display:block}h2.who{margin-top:32px}</style>'
            '<h1>Obsada NPC: Welcome Home (runda 2)</h1><p>Referencja: własne zdanie w stylu postaci z projektu głosu. '
            'Dwie kwestie z gry sklonowane z referencji w tempie rozgrywki (D34).</p>' + ''.join(rows))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)
    print(os.path.join(OUT, 'index.html'))


def adopt(voice, name):
    """Wybrany kandydat → stała referencja postaci w refs.json (jak referencje z dubbingu, D33)."""
    import hashlib
    import shutil
    import soundfile as sf
    c = json.load(open(os.path.join(OUT, 'select.json'), encoding='utf-8'))['candidates'][name]
    os.makedirs(paths.REFS, exist_ok=True)
    wav = os.path.join(paths.REFS, voice + '.wav')
    shutil.copyfile(os.path.join(ROOT, c['wav']), wav)
    path = os.path.join(paths.REFS, 'refs.json')
    refs = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    refs[voice] = {'wav': paths.rel(wav), 'text': CHARACTERS[voice]['style_text'], 'seconds': round(sf.info(wav).duration, 2),
                   'source': 'projekt głosu: %s, ziarno %d (%s)' % (c['instruct'], c['seed'], c['wav']),
                   'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
    json.dump(refs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(voice, refs[voice]['seconds'], refs[voice]['sha'][:8])


if __name__ == '__main__':
    if sys.argv[1] == 'adopt':  # adopt <głos> <kandydat>, np. adopt adelynn adelynn_d1_s11
        adopt(*sys.argv[2:4])
    else:
        {'portrait': portrait, 'scan': scan, 'select': select, 'clone': clone}[sys.argv[1]]()
