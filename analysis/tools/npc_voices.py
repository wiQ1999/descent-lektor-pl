"""Projektowanie głosów postaci NPC (OmniVoice voice design) i strona odsłuchu do QA obsady.

OmniVoice opisuje głos tylko płcią, wiekiem i wysokością. Charakter postaci nadajemy referencją: własnym
zdaniem napisanym w stylu postaci (nie tekstem gry) i tempem. Klony przejmują sposób mówienia z referencji.
Opis postaci bierzemy z portretu z okna dialogu (d3/storymessagecharacters, tekstura *_Dialogue).

Postać z dubbingu (Kehli, D55) zamiast projektu ma zestawy klipów: `mix` skleja je w referencje z transkrypcją.

Kroki dla rundy QA (wyniki prywatne w analysis/work/lektor/voice_design/e7/<runda>/):
  .venv/Scripts/python -I analysis/tools/npc_voices.py portrait r1         # portrety z kopii gry
  <omnivoice>/Scripts/python -I analysis/tools/npc_voices.py scan r1       # kandydaci: opis × ziarno
  .venv/Scripts/python -I analysis/tools/npc_voices.py mix r1              # referencje z klipów dubbingu
  .venv/Scripts/python -I analysis/tools/npc_voices.py select r1           # ASR, F0, 4 różne barwy, kwestie z gry
  .venv/Scripts/python -I analysis/tools/npc_voices.py rasp r1b            # warianty z chrypą (runda z polem rasp)
  <omnivoice>/Scripts/python -I analysis/tools/npc_voices.py clone r1      # kwestie z gry na kandydata + index.html
  .venv/Scripts/python -I analysis/tools/npc_voices.py stats r1            # F0 kwestii każdego kandydata
  .venv/Scripts/python -I analysis/tools/npc_voices.py adopt r1 astarra astarra_d1_s5   # wybór z QA → refs.json

Strona odsłuchu pokazuje też głosy już wybrane, żeby rodzaj głosu się nie powtarzał. Po wyborze w innej rundzie
stronę odświeża `refresh r2` (bez modelu).
<omnivoice> = %LOCALAPPDATA%/LektorPL/envs/omnivoice
"""
import html
import json
import os
import re
import sys
import time
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import direction as D  # noqa: E402
from lektor import paths  # noqa: E402

OUT = os.path.join(paths.OUT, 'voice_design')
LINES = os.path.join(paths.WORK, 'out', 'lines.jsonl')
CLIPS = os.path.join(paths.VOICES, 'analysis.json')
CHARACTERS = {
    'astarra': {
        'texture': 'Astarra_Dialogue', 'gender': 'female', 'speaker': 'ASTARRA',
        'brief': 'dojrzała czarodziejka z kosturem, ciemne włosy, surowe spojrzenie, władczy gest; mówi stanowczo i chłodno',
        'designs': ['female, middle-aged, moderate pitch', 'female, middle-aged, low pitch',
                    'female, young adult, low pitch', 'female, young adult, moderate pitch'],
        'style_text': 'Nie przyszłam tu prosić. Wiedza ma swoją cenę, a dziś to ja ją ustalam, więc słuchaj uważnie.',
        'ref_cps': 10.5,
    },
    'adelynn': {
        'texture': 'BaronessAdelynn_Dialogue', 'gender': 'female', 'speaker': 'BARONESS_ADELYNN', 'baseline': True,
        'brief': 'dojrzała baronessa w płaszczu z piór, z mieczem pod ręką; spokojny autorytet, pewność siebie bez krzyku',
        'designs': ['female, middle-aged, low pitch', 'female, middle-aged, moderate pitch',
                    'female, elderly, moderate pitch', 'female, young adult, low pitch'],
        'style_text': 'Proszę wybaczyć, ale tutaj decyzje podejmuję ja. Wysłucham was spokojnie, a potem zrobimy to po mojemu.',
        'ref_cps': 10.5,
    },
    'ronan': {
        'texture': 'Ronan_Dialogue', 'gender': 'male', 'speaker': 'RONAN', 'baseline': True,
        'brief': 'potężny wojownik jak wiking, jasna broda, krzyczy, na ramieniu pandka; głos waleczny, szalony, radosny',
        'designs': ['male, middle-aged, very low pitch', 'male, middle-aged, low pitch',
                    'male, young adult, low pitch', 'male, elderly, low pitch'],
        'style_text': 'Ha! Dawajcie ich tu, wszystkich naraz! Dobra bitka to najlepsza zabawa, a potem piwo dla każdego!',
        'ref_cps': 12.0,
    },
    'kehli': {
        'gender': 'female', 'speaker': 'KEHLI', 'baseline': True, 'lines': 3,
        'brief': 'bohaterka z dubbingu; referencja z klipów o podobnej wysokości, żeby modulacja nie zmieniała się między kwestiami (D55)',
        'mixes': {
            'kehli_srodek': ['Kehli_QuestSelect_3.wav', 'Kehli_DefeatEnemy_3.wav', 'Kehli_QuestLost_4.wav'],
            'kehli_nisko': ['Kehli_DefeatEnemy_1.wav', 'Kehli_DefeatEnemy_6.wav', 'Kehli_QuestLost_1.wav'],
            'kehli_wysoko': ['Kehli_GainTreasure_3.wav', 'Kehli_MajorWound_1.wav', 'Kehli_FeatComplete_4.wav',
                             'Kehli_QuestSelect_2.wav'],
        },
    },
    'kathryn': {
        'texture': 'Kathryn_Dialogue', 'gender': 'female', 'speaker': 'KATHRYN',
        'brief': 'duch młodej kobiety w podartej sukni, rozwiane włosy, otwarte usta; głos smutny, zawodzący, z oddali',
        'designs': ['female, young adult, moderate pitch', 'female, young adult, high pitch',
                    'female, young adult, low pitch', 'female, middle-aged, moderate pitch'],
        'style_text': 'Czemu nikt nie przychodzi? Zimno mi, tak bardzo zimno, a on wciąż nie wraca do domu.',
        'ref_cps': 9.0,
    },
    'ltrand': {
        'texture': 'LTRand_Dialogue', 'gender': 'female', 'speaker': 'LTRAND',
        'brief': 'młoda oficerka w zbroi, miecz na ramieniu, ręka na biodrze; rzeczowa, pewna siebie, głos dowódcy',
        'designs': ['female, young adult, low pitch', 'female, middle-aged, low pitch',
                    'female, young adult, moderate pitch', 'female, middle-aged, moderate pitch'],
        'style_text': 'Trzymać szyk! Znam tę drogę i przeprowadzę was bezpiecznie, tylko bez głupich pomysłów.',
        'ref_cps': 11.5,
    },
    'bruli': {
        'texture': 'MasterBruli_Dialogue', 'gender': 'male', 'speaker': 'MASTERBRULI',
        'brief': 'starszy krępy krasnolud, siwiejąca broda w warkoczach, księga i sakiewki; zrzędliwy, skrupulatny mistrz',
        'designs': ['male, elderly, low pitch', 'male, middle-aged, low pitch',
                    'male, elderly, moderate pitch', 'male, elderly, very low pitch'],
        'style_text': 'Każda moneta ma tu swoją rubrykę. Płacisz z góry albo wynosisz się z mojego warsztatu.',
        'ref_cps': 10.5,
    },
    'galgoraz': {
        'texture': 'MasterGalgoraz_Dialogue', 'gender': 'male', 'speaker': 'MASTERGALGORAZ',
        'brief': 'stary smokowiec w ochrowej szacie, rogi, biała broda, kostur; zamyślony mędrzec i nauczyciel',
        'designs': ['male, elderly, moderate pitch', 'male, elderly, low pitch',
                    'male, elderly, high pitch', 'male, middle-aged, low pitch'],
        'style_text': 'Cierpliwości, młody uczniu. Każda księga otwiera się dopiero temu, kto umie zadać właściwe pytanie.',
        'ref_cps': 9.5,
    },
    'flint': {
        'texture': 'MasterFlint_Dialogue', 'gender': 'male', 'speaker': 'MASTERFLINT',
        'brief': 'krzepki krasnolud kowal, łysy, gęsta ruda broda, młot i fartuch; serdeczny, wesoły, rubaszny',
        'designs': ['male, middle-aged, low pitch', 'male, middle-aged, moderate pitch',
                    'male, young adult, low pitch', 'male, elderly, low pitch'],
        'style_text': 'Ha, dobra robota! Dobry młot i gorące palenisko, a reszta sama się ułoży. Siadaj, przyjacielu!',
        'ref_cps': 11.0,
    },
    'xenith': {
        'gender': 'male', 'speaker': 'DRAGON_HYBRID', 'texture': 'DragonHybrid_Dialogue',
        'brief': 'kapitan hybryd smoka; ma nagrania w dubbingu, więc klon jak Ne’Krul (D19)',
        'mixes': {'xenith_dubbing': ['Xenith_Spawn_2.wav', 'Xenith_Spawn_1.wav']},
    },
    'herbie': {
        'texture': 'Herbie_Dialogue', 'gender': 'male', 'speaker': 'HERBIE',
        'brief': 'chudy wieśniak z kilofem, chytry uśmieszek; gadatliwy cwaniaczek, prosty język',
        'designs': ['male, young adult, moderate pitch', 'male, middle-aged, moderate pitch',
                    'male, young adult, high pitch', 'male, middle-aged, low pitch'],
        'style_text': 'A co tam, panie, ja tam nic nie widziałem! Kopię sobie spokojnie i nikomu nie wadzę.',
        'ref_cps': 12.0,
    },
    'mok': {
        'texture': 'ElderMok_Dialogue', 'gender': 'male', 'speaker': 'ELDERMOK',
        'brief': 'stary orkowy szaman z kosturem z czaszką, kły, świecące oczy; głos niski, chrapliwy, powolny',
        'designs': ['male, elderly, very low pitch', 'male, elderly, low pitch',
                    'male, middle-aged, very low pitch', 'male, elderly, moderate pitch'],
        'style_text': 'Duchy przodków mówią. Słuchaj ich, człowieku, bo gniew góry nie zna litości.',
        'ref_cps': 9.0,
    },
    'outlaw': {
        'texture': 'OutlawPrince_Dialogue', 'gender': 'male', 'speaker': 'OUTLAWPRINCE',
        'brief': 'potężny mężczyzna w ciężkiej zbroi z łańcuchem, czarna broda, wyniosłe spojrzenie; arogancki przywódca',
        'designs': ['male, middle-aged, low pitch', 'male, middle-aged, very low pitch',
                    'male, young adult, low pitch', 'male, middle-aged, moderate pitch'],
        'style_text': 'Ta korona należy do mnie, a kto stanie mi na drodze, ten zawiśnie przy bramie.',
        'ref_cps': 10.5,
    },
}
# Runda 1b (QA 2026-11-04): Ronan niski, z chrypą, mówiący urywanymi frazami.
# Runda 4b (QA 2026-11-05): Galgoraz bardzo stary, kandydaci wyraźnie różni barwą, także od bliskich już wybranych.
ROUND_OVERRIDES = {'r4b': {'galgoraz': {
    'brief': 'stary smokowiec w ochrowej szacie, rogi, biała broda, kostur; bardzo stary mędrzec, głos starczy, drżący',
    'designs': ['male, elderly, very low pitch', 'male, elderly, low pitch', 'male, elderly, moderate pitch',
                'male, elderly, high pitch', 'male, elderly, very high pitch'],
    'seeds': (5, 17, 29, 41, 53, 67), 'f0_max': 240, 'pick': 6, 'avoid': ('bruli', 'herbie', 'flint', 'ronan'),
    'tremor': 0.6, 'style_text': 'Ach... cierpliwości, młody uczniu. Stare księgi... nie lubią pośpiechu. Posłuchaj... i zapamiętaj.',
    'ref_cps': 7.0,
}}, 'r1b': {'ronan': {
    'brief': 'potężny wojownik jak wiking, jasna broda, krzyczy, na ramieniu pandka; głos niski, urywany, z chrypą',
    'designs': ['male, elderly, very low pitch', 'male, middle-aged, very low pitch', 'male, elderly, low pitch'],
    'seeds': (5, 17, 29, 41, 53, 67), 'f0_max': 125, 'rasp': 0.6,
    'style_text': 'Ha! Krew... i stal! Dawaj ich tu. Wszystkich. Naraz! A potem... piwo. Hej!',
    'ref_cps': 7.5,
}}}
ROUNDS = {'r1': ('astarra', 'adelynn', 'ronan', 'kehli'), 'r1b': ('ronan',), 'r4': ('galgoraz', 'flint'), 'r4b': ('galgoraz',), 'r2': ('kathryn', 'ltrand', 'bruli', 'xenith'),
          'r3': ('herbie', 'mok', 'outlaw')}
SEEDS = (5, 17, 29)
PICK = 4
MAX_CER = 0.10
F0_RANGE = {'female': (140, 330), 'male': (65, 190)}
MIX_GAP_S = 0.3


def round_dir(rnd, *parts):
    return os.path.join(OUT, 'e7', rnd, *parts)


def gen_settings():
    return {'num_step': D.MODEL['num_step'], 'guidance_scale': D.MODEL['guidance_scale']}


def load_omnivoice():
    """fp32: karta bez rdzeni tensorowych liczy fp16 ok. 5,5× wolniej (lektor.synth)."""
    import torch
    from omnivoice import OmniVoice
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    return OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cuda:0', dtype=torch.float32)


def tokenizer_to_cpu(model):
    import torch
    model.audio_tokenizer.to('cpu')
    torch.cuda.empty_cache()


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


def portrait(rnd):
    import UnityPy
    from lektor import game as G
    g = G.Game()
    env = UnityPy.load(os.path.join(paths.BUNDLES, g.files['d3/storymessagecharacters']))
    want = {CHARACTERS[v]['texture']: v for v in ROUNDS[rnd] if 'texture' in CHARACTERS[v]}
    os.makedirs(round_dir(rnd), exist_ok=True)
    for o in env.objects:
        if o.type.name == 'Texture2D':
            d = o.read()
            if d.m_Name in want:
                d.image.save(round_dir(rnd, want[d.m_Name] + '.png'))
                print(want[d.m_Name], d.image.size)


def load_scan(rnd):
    path = round_dir(rnd, 'scan.json')
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}


def save_scan(rnd, data):
    json.dump(data, open(round_dir(rnd, 'scan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def scan(rnd):
    model = load_omnivoice()
    tokenizer_to_cpu(model)
    os.makedirs(round_dir(rnd, 'scan'), exist_ok=True)
    out = load_scan(rnd)
    for voice in ROUNDS[rnd]:
        c = CHARACTERS[voice]
        for i, instruct in enumerate(c.get('designs', ()), 1):
            for seed in c.get('seeds', SEEDS):
                name = '%s_d%d_s%d' % (voice, i, seed)
                path = round_dir(rnd, 'scan', name + '.wav')
                if not os.path.exists(path):
                    synth(model, path, c['style_text'], seed, instruct=instruct,
                          duration=round(len(c['style_text']) / c['ref_cps'], 2))
                out[name] = {'voice': voice, 'instruct': instruct, 'seed': seed, 'wav': paths.rel(path)}
                save_scan(rnd, out)


def load_asr():
    import torch
    from transformers import pipeline
    os.environ.setdefault('HF_HOME', paths.HF_HOME)
    return pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', dtype=torch.float16, device='cuda')


def mix(rnd):
    """Referencje z klipów dubbingu: sklejone z krótką ciszą, transkrypcja z tych samych klipów."""
    import librosa
    import numpy as np
    import soundfile as sf
    clips = {c['name']: os.path.join(ROOT, 'analysis', c['wav']) for c in json.load(open(CLIPS, encoding='utf-8'))}
    asr = load_asr()
    out = load_scan(rnd)
    os.makedirs(round_dir(rnd, 'scan'), exist_ok=True)
    for voice in ROUNDS[rnd]:
        for name, parts in CHARACTERS[voice].get('mixes', {}).items():
            audio, texts, sr = [], [], None
            for part in parts:
                y, sr = sf.read(clips[part], dtype='float32')
                y = y.mean(axis=1) if y.ndim > 1 else y
                audio += [y, np.zeros(int(MIX_GAP_S * sr), np.float32)]
                y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
                texts.append(asr({'raw': y16, 'sampling_rate': 16000},
                                 generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text'].strip())
            path = round_dir(rnd, 'scan', name + '.wav')
            sf.write(path, np.concatenate(audio[:-1]), sr, subtype='PCM_16')
            out[name] = {'voice': voice, 'instruct': 'dubbing: ' + ', '.join(p[:-4] for p in parts), 'seed': 0,
                         'wav': paths.rel(path), 'text': ' '.join(texts)}
            print(name, round(sum(len(a) for a in audio[:-1]) / sr, 1), 's', file=sys.stderr, flush=True)
    save_scan(rnd, out)


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


def game_lines(voices):
    """Kwestie z gry na próbki: {głos: [[klucz, tekst], ...]}: średnia (60–120 znaków), najdłuższa, kolejne średnie."""
    from lektor import game as G
    from lektor.normalize import normalize
    terms = G.Game().terms()
    found = {v: {} for v in voices}
    speakers = {'STORY_CHARACTER_' + CHARACTERS[v]['speaker']: v for v in voices}
    with open(LINES, encoding='utf-8') as fh:
        for row in fh:
            r = json.loads(row)
            if len(r['speakers']) == 1 and r['speakers'][0] in speakers and r['key'] in terms:
                text = terms[r['key']].get('text') or ''
                if text and '{' not in text and len(text) <= 260:
                    found[speakers[r['speakers'][0]]][r['key']] = normalize(re.sub(r'<sprite=\d+>', '', text)).strip()
    out = {}
    for voice, lines in found.items():
        rows = sorted(lines.items(), key=lambda kv: (len(kv[1]), kv[0]))
        mid = [r for r in rows if 60 <= len(r[1]) <= 120] or rows[:1]
        picked = [mid[len(mid) // 2], rows[-1]]
        picked += [r for r in mid[::max(1, len(mid) // 3)] if r not in picked]
        out[voice] = [list(r) for r in picked[:CHARACTERS[voice].get('lines', 2)]]
    return out


def select(rnd):
    """Odrzuca kandydatów z błędami (CER) i wysokością spoza płci, z reszty wybiera PICK najbardziej różnych barw."""
    import librosa
    import numpy as np
    import torch
    from huggingface_hub import hf_hub_download
    from chatterbox.models.voice_encoder import VoiceEncoder
    sys.stdout.reconfigure(encoding='utf-8')
    cands = load_scan(rnd)
    asr = load_asr()
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()
    for name, c in cands.items():
        y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=16000)
        spec = CHARACTERS[c['voice']]
        text = c.get('text') or spec['style_text']
        c['cer'] = round(cer(text, asr({'raw': y, 'sampling_rate': 16000}, generate_kwargs={'language': 'polish'})['text']), 3)
        f0 = librosa.pyin(y, fmin=60, fmax=250 if spec['gender'] == 'male' else 500, sr=16000)[0]   # u mężczyzn z chrypą pyin ucieka w górę
        c['f0'] = round(float(np.nanmedian(f0)), 0)
        e = ve.embeds_from_wavs([y], sample_rate=16000)[0]
        c['emb'] = (e / np.linalg.norm(e)).tolist()
    picked = {}
    for voice in ROUNDS[rnd]:
        spec = CHARACTERS[voice]
        lo, hi = F0_RANGE[spec['gender']]
        hi = spec.get('f0_max', hi)
        mine = [n for n, c in cands.items() if c['voice'] == voice]
        ok = sorted((n for n in mine if 'mixes' in spec or (cands[n]['cer'] <= MAX_CER and lo <= cands[n]['f0'] <= hi)),
                    key=lambda n: cands[n]['cer'])
        chosen = ok[:1]
        pick = spec.get('pick', PICK)
        avoid = []
        if spec.get('avoid'):       # kandydaci mają się też różnić od bliskich głosów już wybranych
            refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
            for v in spec['avoid']:
                e = ve.embeds_from_wavs([librosa.load(os.path.join(ROOT, refs[v]['wav']), sr=16000)[0]], sample_rate=16000)[0]
                avoid.append(e / np.linalg.norm(e))
            chosen = []
        while ok and len(chosen) < min(pick, len(ok)):
            far = max((n for n in ok if n not in chosen), key=lambda n: min(
                [1 - float(np.dot(cands[n]['emb'], cands[m]['emb'])) for m in chosen] +
                [1 - float(np.dot(cands[n]['emb'], e)) for e in avoid]))
            chosen.append(far)
        picked[voice] = chosen
        for n in sorted(mine):
            c = cands[n]
            print('%-20s %-40s CER %.2f  F0 %4.0f Hz %s' % (n, c['instruct'][:40], c['cer'], c['f0'], '*' if n in chosen else ''))
    for c in cands.values():
        c.pop('emb')
    json.dump({'candidates': cands, 'picked': picked, 'lines': game_lines(ROUNDS[rnd])},
              open(round_dir(rnd, 'select.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def roughen(y, sr, amount, seed=7):
    """Chrypa: nieregularna modulacja amplitudy (25–70 Hz), szum szczelinowy idący za obwiednią mowy i przesterowanie."""
    import numpy as np
    from scipy import signal
    rng = np.random.default_rng(seed)
    env = signal.sosfiltfilt(signal.butter(2, 40, 'low', fs=sr, output='sos'), np.abs(y))
    flutter = signal.sosfiltfilt(signal.butter(2, (25, 70), 'band', fs=sr, output='sos'), rng.standard_normal(len(y)))
    flutter /= np.abs(flutter).max() + 1e-9
    hiss = signal.sosfiltfilt(signal.butter(2, (1500, 6000), 'band', fs=sr, output='sos'), rng.standard_normal(len(y)))
    hiss /= np.abs(hiss).max() + 1e-9
    out = y * (1 + 0.9 * amount * flutter) + hiss * env * 1.6 * amount
    drive = 1 + 3 * amount
    out = np.tanh(drive * out) / np.tanh(drive)
    return (out * (np.abs(y).max() / (np.abs(out).max() + 1e-9))).astype(np.float32)


def tremble(y, sr, amount, seed=11):
    """Starcze drżenie: nieregularne wibrato i modulacja głośności około 5–7 Hz oraz lekkie tchnienie."""
    import numpy as np
    from scipy import signal
    rng = np.random.default_rng(seed)
    wobble = signal.sosfiltfilt(signal.butter(2, (4.5, 7.5), 'band', fs=sr, output='sos'), rng.standard_normal(len(y)))
    wobble /= np.abs(wobble).max() + 1e-9
    t = np.arange(len(y), dtype=np.float64)
    out = np.interp(t + wobble * amount * 0.004 * sr, t, y) * (1 + 0.5 * amount * wobble)
    env = signal.sosfiltfilt(signal.butter(2, 40, 'low', fs=sr, output='sos'), np.abs(y))
    breath = signal.sosfiltfilt(signal.butter(2, (2000, 7000), 'band', fs=sr, output='sos'), rng.standard_normal(len(y)))
    out = out + breath / (np.abs(breath).max() + 1e-9) * env * 0.8 * amount
    return (out * (np.abs(y).max() / (np.abs(out).max() + 1e-9))).astype(np.float32)


def tremor(rnd):
    """Kandydaci z drżeniem w referencji (klon je przejmuje): pierwsza połowa wybranych."""
    import soundfile as sf
    path = round_dir(rnd, 'select.json')
    sel = json.load(open(path, encoding='utf-8'))
    for voice in ROUNDS[rnd]:
        spec = CHARACTERS[voice]
        names = list(sel['picked'][voice])
        for name in names[:(len(names) + 1) // 2]:
            c = sel['candidates'][name]
            y, sr = sf.read(os.path.join(ROOT, c['wav']), dtype='float32')
            new = name + '_drzenie'
            wav = round_dir(rnd, 'scan', new + '.wav')
            sf.write(wav, tremble(y, sr, spec['tremor']), sr, subtype='PCM_16')
            sel['candidates'][new] = {**c, 'wav': paths.rel(wav), 'instruct': c['instruct'] + ', drżenie w referencji'}
            sel['picked'][voice].append(new)
    json.dump(sel, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def rasp(rnd):
    """Kandydaci z chrypą: referencja przetworzona (klon przejmuje chrypę) i klon przetworzony po wygenerowaniu."""
    import soundfile as sf
    path = round_dir(rnd, 'select.json')
    sel = json.load(open(path, encoding='utf-8'))
    for voice in ROUNDS[rnd]:
        spec = CHARACTERS[voice]
        for name in list(sel['picked'][voice]):
            c = sel['candidates'][name]
            y, sr = sf.read(os.path.join(ROOT, c['wav']), dtype='float32')
            new = name + '_chrypa'
            wav = round_dir(rnd, 'scan', new + '.wav')
            sf.write(wav, roughen(y, sr, spec['rasp']), sr, subtype='PCM_16')
            sel['candidates'][new] = {**c, 'wav': paths.rel(wav), 'instruct': c['instruct'] + ', chrypa w referencji'}
            sel['picked'][voice].append(new)
        first = sel['picked'][voice][0]
        new = first + '_efekt'
        sel['candidates'][new] = {**sel['candidates'][first], 'instruct': sel['candidates'][first]['instruct'] + ', chrypa dodana po wygenerowaniu',
                                  'effect': spec['rasp']}
        sel['picked'][voice].append(new)
    json.dump(sel, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def chosen_voices(rnd):
    """Sekcja strony z głosami już wybranymi (uwaga z QA 2026-11-04): referencja każdego głosu spoza tej rundy."""
    import shutil
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    os.makedirs(round_dir(rnd, 'wybrane'), exist_ok=True)
    rows = []
    for voice, r in sorted(refs.items()):
        if voice in ROUNDS[rnd]:
            continue
        shutil.copyfile(os.path.join(ROOT, r['wav']), round_dir(rnd, 'wybrane', voice + '.wav'))
        rows.append('<p><code>%s</code> <audio controls src="wybrane/%s.wav"></audio></p>' % (voice, voice))
    return '<h2 class="who">Głosy już wybrane</h2><p>Referencje do porównania, żeby rodzaj głosu się nie powtarzał.</p>' + ''.join(rows)


def clone(rnd):
    import soundfile as sf
    model = load_omnivoice()
    sel = json.load(open(round_dir(rnd, 'select.json'), encoding='utf-8'))
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    os.makedirs(round_dir(rnd, 'clone'), exist_ok=True)
    jobs = []
    for voice in ROUNDS[rnd]:
        spec = CHARACTERS[voice]
        names = list(sel['picked'][voice])
        if spec.get('baseline'):
            jobs.append((voice, voice + '_obecny', os.path.join(ROOT, refs[voice]['wav']), refs[voice]['text'], 'obecny głos', 0))
        for name in names:
            c = sel['candidates'][name]
            jobs.append((voice, name, os.path.join(ROOT, c['wav']), c.get('text') or CHARACTERS[c['voice']]['style_text'],
                         c['instruct'], c['f0']))
    prompts = {job[1]: model.create_voice_clone_prompt(job[2], job[3]) for job in jobs}
    tokenizer_to_cpu(model)
    rows, seen = [], set()
    for voice, name, wav, _, label, f0 in jobs:
        spec = CHARACTERS[voice]
        lines = sel['lines'][voice]
        if voice not in seen:
            seen.add(voice)
            img = '<img src="%s.png" alt="">' % voice if 'texture' in spec else ''
            rows.append('<h2 class="who">%s</h2><p>%s</p>%s' % (voice.capitalize(), html.escape(spec['brief']), img))
        audio = []
        for i, (key, text) in enumerate(lines):
            path = round_dir(rnd, 'clone', '%s_%s.wav' % (name, 'abc'[i]))
            if not os.path.exists(path):
                synth(model, path, text, 1234, voice_clone_prompt=prompts[name], speed=D.tempo('dialog', len(text))[0])
                effect = sel['candidates'].get(name, {}).get('effect')
                if effect:
                    y, sr = sf.read(path, dtype='float32')
                    sf.write(path, roughen(y, sr, effect), sr, subtype='PCM_16')
            audio.append('<p><code>%s</code> <audio controls src="clone/%s"></audio></p>' % (key, os.path.basename(path)))
        rows.append('<section><h3>%s</h3><p>%s · F0 referencji %.0f Hz</p>%s</section>' % (
            name, html.escape(label), f0, ''.join(audio)))
    page = ('<!doctype html><meta charset="utf-8"><title>Obsada E7</title><style>body{font:15px system-ui;'
            'max-width:820px;margin:24px auto;padding:0 16px}section{border:1px solid #ccc;border-radius:8px;'
            'padding:8px 16px;margin:12px 0}audio{vertical-align:middle;width:420px;max-width:100%}'
            'img{width:320px;max-width:100%;display:block}h2.who{margin-top:32px}</style>'
            '<h1>Obsada E7: runda ' + rnd[1:] + '</h1><p>Kwestie z gry w tempie rozgrywki (D34).</p>' + ''.join(rows) + chosen_voices(rnd))
    open(round_dir(rnd, 'index.html'), 'w', encoding='utf-8').write(page)
    print(round_dir(rnd, 'index.html'))


def refresh(rnd):
    """Odświeża sekcję głosów już wybranych na gotowej stronie, bez modelu (GPU może liczyć coś innego)."""
    path = round_dir(rnd, 'index.html')
    page = open(path, encoding='utf-8').read().split('<h2 class="who">Głosy już wybrane')[0]
    open(path, 'w', encoding='utf-8').write(page + chosen_voices(rnd))


def stats(rnd):
    """Mediana F0 każdej kwestii kandydata: rozrzut między kwestiami pokazuje niestałą modulację (D55)."""
    import glob
    import librosa
    import numpy as np
    groups = {}
    for path in sorted(glob.glob(round_dir(rnd, 'clone', '*.wav'))):
        y, _ = librosa.load(path, sr=16000)
        f0 = float(np.nanmedian(librosa.pyin(y, fmin=60, fmax=500, sr=16000)[0]))
        groups.setdefault(os.path.basename(path)[:-6], []).append(f0)
    for name, vals in groups.items():
        print('%-22s %s  rozrzut %.0f Hz' % (name, ' '.join('%4.0f' % v for v in vals), max(vals) - min(vals)))


def adopt(rnd, voice, name):
    """Wybrany kandydat → stała referencja postaci w refs.json (jak referencje z dubbingu, D33)."""
    import hashlib
    import shutil
    import soundfile as sf
    c = json.load(open(round_dir(rnd, 'select.json'), encoding='utf-8'))['candidates'][name]
    os.makedirs(paths.REFS, exist_ok=True)
    wav = os.path.join(paths.REFS, voice + '.wav')
    shutil.copyfile(os.path.join(ROOT, c['wav']), wav)
    path = os.path.join(paths.REFS, 'refs.json')
    refs = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    refs[voice] = {'wav': paths.rel(wav), 'text': c.get('text') or CHARACTERS[c['voice']]['style_text'],
                   'seconds': round(sf.info(wav).duration, 2),
                   'source': 'projekt głosu: %s, ziarno %d (%s)' % (c['instruct'], c['seed'], c['wav']),
                   'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
    json.dump(refs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(voice, refs[voice]['seconds'], refs[voice]['sha'][:8])


if __name__ == '__main__':
    for name, change in ROUND_OVERRIDES.get(sys.argv[2], {}).items():
        CHARACTERS[name].update(change)
    if sys.argv[1] == 'adopt':  # adopt <runda> <głos> <kandydat>, np. adopt r1 astarra astarra_d1_s5
        adopt(*sys.argv[2:5])
    else:
        {'portrait': portrait, 'scan': scan, 'mix': mix, 'select': select, 'rasp': rasp, 'tremor': tremor, 'clone': clone,
         'refresh': refresh, 'stats': stats}[sys.argv[1]](sys.argv[2])
