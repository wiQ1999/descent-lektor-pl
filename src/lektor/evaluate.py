"""Ocena automatyczna podejść E3 i wybór najlepszego (D38). Uruchamiać w .venv (Whisper, VoiceEncoder Chatterboxa).

Dla każdego podejścia z takes.jsonl:
  - ASR (Whisper large-v3-turbo): CER, ucięta końcówka (ostatnie słowo tekstu poza końcem transkrypcji)
    i zgubiony fragment (najdłuższy ciąg słów tekstu bez odpowiednika w transkrypcji);
  - podobieństwo barwy do referencji głosu (VoiceEncoder);
  - tempo: znaki na sekundę mowy (bez ciszy na brzegach) wobec tempa oczekiwanego z D34.
Wyniki trafiają do evals.jsonl (wznawianie). select() wybiera podejście dla każdego fragmentu (choice.json)
i zapisuje odrzucone do ponownego podejścia (retake.json: fragment -> [podejście, tempo]).
"""
import json
import os
import re
import sys
import unicodedata

from . import db, paths
from .normalize import cardinal
from .synth import inherited, load_state, take_path, takes_for

ASR_MODEL = 'openai/whisper-large-v3-turbo'
REF_CPS = 10.3          # naturalne tempo referencji dubbingu (znaki na sekundę), speed 1,2 daje ok. 12,1
MAX_CER = 0.08          # fragmenty od SHORT znaków; krótsze (nazwy, wartości) ASR myli częściej
MAX_CER_SHORT = 0.25
SHORT = 30
MAX_LOST = 6            # tyle znaków z rzędu bez odpowiednika w transkrypcji (bez spacji) to zgubiony fragment
SIM_DROP = 0.08         # barwa: odrzucenie poniżej mediany głosu minus SIM_DROP
SIM_MIN_S = 2.5         # krótsze nagrania mają w VoiceEncoderze systematycznie niższe podobieństwo
MIN_SPEECH_S = 0.15     # mniej mowy to pusty wynik (model czasem milczy przy tekstach z 1–3 znaków)
CPS_RANGE = (0.6, 1.6)  # tempo poza tym zakresem względem oczekiwanego (fragmenty od 15 znaków)
RETAKE_SLOWER = 0.1     # ucięta końcówka: ponowne podejście wolniej (D34)
END_RMS, END_GAP = 0.08, 0.11   # mowa urwana przy końcu pliku (speech_end)
MAX_PAUSE = 1.2         # pauza w środku kwestii (s); na podejściach M2 najdłuższa zdrowa ma ok. 1 s
RETAKES = 3             # tyle ponownych podejść, zanim fragment trafi na listę odsłuchu (D38, E7)


def words(s):
    s = re.sub(r'\d+', lambda m: cardinal(int(m.group())), unicodedata.normalize('NFC', s.lower()))
    return re.sub(r'[^\w ]', ' ', s).split()


def distance(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1]


def similar(a, b):
    return distance(a, b) <= max(1, len(a) // 3)


def missing_run(ref, hyp):
    """Najdłuższy ciąg słów tekstu usuniętych w wyrównaniu słów (podobne formy liczą się jako trafienie)."""
    n, m = len(ref), len(hyp)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = i
    for j in range(1, m + 1):
        D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (not similar(ref[i - 1], hyp[j - 1])))
    i, j, run, best = n, m, 0, 0
    while i > 0:
        if j > 0 and D[i][j] == D[i - 1][j - 1] + (not similar(ref[i - 1], hyp[j - 1])):
            lost = not similar(ref[i - 1], hyp[j - 1])
            i, j = i - 1, j - 1
        elif j > 0 and D[i][j] == D[i][j - 1] + 1:
            j -= 1
            continue
        else:
            lost = True
            i -= 1
        run = run + 1 if lost else 0
        best = max(best, run)
    return best


def lost_chars(ref, hyp):
    """Najdłuższy ciąg znaków tekstu usuniętych w wyrównaniu bez spacji. Odporny na inny podział na słowa w ASR
    (scalone albo rozdzielone wyrazy), który w wyrównaniu słów wygląda jak zgubione słowa."""
    a, b = ''.join(ref), ''.join(hyp)
    n, m = len(a), len(b)
    D = [list(range(m + 1))] + [[i] + [0] * m for i in range(1, n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
    i, j, run, best = n, m, 0, 0
    while i > 0:
        if j > 0 and D[i][j] == D[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            run, i, j = 0, i - 1, j - 1
        elif j > 0 and D[i][j] == D[i][j - 1] + 1:
            j -= 1
        else:
            run, i = run + 1, i - 1
            best = max(best, run)
    return best


def tail_cut(ref, hyp):
    """Ostatnie słowo tekstu nie występuje w końcówce transkrypcji. Krótkie słowo („i”) musi się zgadzać dokładnie (D43)."""
    if not ref:
        return False
    last = ref[-1]
    return last not in hyp[-3:] if len(last) <= 2 else not any(similar(last, h) for h in hyp[-4:])


def speech_end(y, sr=16000):
    """(poziom mowy w ostatnich 30 ms wobec głośnej mowy, cisza do końca pliku w s). Na M1: naturalny koniec opada
    do ok. 0,04 przy 0,14 s ciszy, a mowa urwana na granicy wygenerowanego fragmentu kończy się ponad 0,08 przy 0,1 s."""
    import librosa
    import numpy as np
    speech, (_, end) = librosa.effects.trim(y, top_db=40, frame_length=256, hop_length=64)
    frame = int(0.03 * sr)
    if len(speech) < 6 * frame:
        return 0.0, 1.0
    rms = librosa.feature.rms(y=speech, frame_length=frame, hop_length=frame // 2, center=False)[0]
    return round(float(rms[-1] / (np.percentile(rms, 90) + 1e-9)), 3), round((len(y) - end) / sr, 3)


def longest_pause(y, sr=16000):
    """Najdłuższa cisza między odcinkami mowy (s)."""
    import librosa
    spans = librosa.effects.split(y, top_db=35, frame_length=512, hop_length=128)
    return round(max(((b[0] - a[1]) / sr for a, b in zip(spans, spans[1:])), default=0.0), 2)


def expected_cps(speed):
    return REF_CPS * (speed or 1.0)


def text_checks(text, hyp):
    ref_w, hyp_w = words(text), words(hyp)
    ref_c, hyp_c = ' '.join(ref_w), ' '.join(hyp_w)
    missing = missing_run(ref_w, hyp_w)
    return {'cer': round(distance(ref_c, hyp_c) / max(1, len(ref_c)), 3), 'tail_cut': tail_cut(ref_w, hyp_w),
            'missing': missing, 'lost': lost_chars(ref_w, hyp_w) if missing >= 2 else 0}


class Scorer:
    def __init__(self, refs):
        import numpy as np
        import torch
        from huggingface_hub import hf_hub_download
        from transformers import pipeline
        from chatterbox.models.voice_encoder import VoiceEncoder
        os.environ.setdefault('HF_HOME', paths.HF_HOME)
        self.np = np
        self.asr = pipeline('automatic-speech-recognition', model=ASR_MODEL, dtype=torch.float16, device='cuda')
        self.ve = VoiceEncoder()
        self.ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu',
                                           weights_only=True))
        self.ve.eval()
        self.refs = {v: self.embed(self.load(os.path.join(paths.ROOT, r['wav']))) for v, r in refs.items()}

    @staticmethod
    def load(path):
        import librosa
        return librosa.load(path, sr=16000)[0]

    def embed(self, y):
        e = self.ve.embeds_from_wavs([y], sample_rate=16000)[0]
        return e / self.np.linalg.norm(e)

    def __call__(self, path, text, voice, speed):
        import librosa
        y = self.load(path)
        speech = librosa.effects.trim(y, top_db=40)[0].size / 16000 if y.size > 1600 else y.size / 16000
        hyp = '' if speech < MIN_SPEECH_S else self.asr(   # Whisper na ciszy zmyśla zdanie
            {'raw': y, 'sampling_rate': 16000}, generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']
        out = {'asr': hyp.strip(), **text_checks(text, hyp), 'speech_s': round(speech, 2),
               'cps': round(len(text) / max(speech, 0.05), 1), 'cps_ratio': round(len(text) / max(speech, 0.05) / expected_cps(speed), 2)}
        out['sim'] = round(float(self.embed(y) @ self.refs[voice]), 3) if speech >= 1.5 else None
        out['end_rms'], out['end_gap'] = speech_end(y)
        out['pause'] = longest_pause(y)
        return out


def load_evals():
    p = os.path.join(paths.AUDIO, 'evals.jsonl')
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            r = json.loads(line)
            out[r['fragment'], r['take']] = r
    return out


def evaluate():
    con = db.connect(paths.DB)
    texts = {r['id']: r['text'] for r in con.execute('SELECT id, text FROM fragments')}
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    done = load_evals()
    todo = [t for k, t in load_state().items() if k not in done]
    print('do oceny: %d podejść' % len(todo), file=sys.stderr, flush=True)
    if not todo:
        return
    score = Scorer(refs)
    with open(os.path.join(paths.AUDIO, 'evals.jsonl'), 'a', encoding='utf-8') as log:
        for n, t in enumerate(todo, 1):
            r = {'fragment': t['fragment'], 'take': t['take'], 'voice': t['voice'], 'speed': t['speed'], 'chars': t['chars'],
                 **score(take_path(t['fragment'], t['take']), texts[t['fragment']], t['voice'], t['speed'])}
            log.write(json.dumps(r, ensure_ascii=False) + '\n')
            log.flush()
            if n % 50 == 0:
                print('ocena %d/%d' % (n, len(todo)), file=sys.stderr, flush=True)


def problems(e, sim_median):
    """Powody odrzucenia podejścia (pusta lista: zaakceptowane)."""
    if e['speech_s'] < MIN_SPEECH_S:
        return ['cisza']
    out = []
    if e['cer'] > (MAX_CER if e['chars'] >= SHORT else MAX_CER_SHORT):
        out.append('cer')
    if e['tail_cut'] or (e.get('end_rms', 0) >= END_RMS and e.get('end_gap', 1) <= END_GAP):
        out.append('koncowka')
    if e['lost'] >= MAX_LOST:
        out.append('zgubiony_fragment')
    if e['sim'] is not None and e['speech_s'] >= SIM_MIN_S and e['sim'] < sim_median[e['voice']] - SIM_DROP:
        out.append('barwa')
    if e['chars'] >= 15 and not CPS_RANGE[0] <= e['cps_ratio'] <= CPS_RANGE[1]:
        out.append('tempo')
    if e.get('pause', 0) > MAX_PAUSE:
        out.append('pauza')
    return out


def select():
    """choice.json: wybrane podejście każdego fragmentu; retake.json: fragmenty bez zaakceptowanego podejścia,
    które nie miały jeszcze ponownego podejścia (po nim trafiają na listę odsłuchu)."""
    import statistics
    con = db.connect(paths.DB)
    texts = {r['id']: r['text'] for r in con.execute('SELECT id, text FROM fragments')}
    evals = {k: e for k, e in load_evals().items() if e['fragment'] in texts}   # bez fragmentów usuniętych z bazy
    for e in evals.values():    # reguły tekstowe liczone od nowa z zapisanej transkrypcji (bez ponownego ASR)
        e.update(text_checks(texts[e['fragment']], e['asr']))
    sims = {}
    for e in evals.values():
        if e['sim'] is not None and e['speech_s'] >= SIM_MIN_S:
            sims.setdefault(e['voice'], []).append(e['sim'])
    sim_median = {v: statistics.median(s) for v, s in sims.items()}
    sim_median.update({v: 0.0 for v in {e['voice'] for e in evals.values()} - set(sim_median)})
    by_frag = {}
    for e in evals.values():
        e['problems'] = problems(e, sim_median)
        by_frag.setdefault(e['fragment'], []).append(e)
    choice, retake = {}, {}
    for fid, es in by_frag.items():
        best = min(es, key=lambda e: (len(e['problems']) > 0, round(e['cer'] / 0.02), -(e['sim'] or 0), e['take']))
        choice[fid] = {'take': best['take'], 'voice': best['voice'], 'speed': best['speed'], 'problems': best['problems'],
                       'cer': best['cer'], 'sim': best['sim'], 'cps': best['cps'], 'takes': len(es)}
        if best['problems'] and len(es) < takes_for(best['voice']) + RETAKES:
            speed = best['speed']
            if 'koncowka' in best['problems']:
                speed = round(max(0.9, (speed or 1.0) - RETAKE_SLOWER), 2)
            retake[fid] = [max(e['take'] for e in es) + 1, speed]
    for fid, c in inherited().items():     # fragmenty z poprzedniego wydania zostają takie, jak je wybrano
        if fid in texts:
            choice[fid] = c
            retake.pop(fid, None)
    json.dump(choice, open(os.path.join(paths.AUDIO, 'choice.json'), 'w', encoding='utf-8'), indent=1)
    json.dump(retake, open(os.path.join(paths.AUDIO, 'retake.json'), 'w', encoding='utf-8'), indent=1)
    reasons = {}
    for c in choice.values():
        for p in c['problems']:
            reasons[p] = reasons.get(p, 0) + 1
    bad = sum(1 for c in choice.values() if c['problems'])
    print('fragmenty: %d, zaakceptowane: %d, odrzucone: %d %s, do ponownego podejścia: %d; mediany barwy: %s' % (
        len(choice), len(choice) - bad, bad, reasons, len(retake),
        {v: round(m, 3) for v, m in sorted(sim_median.items())}), file=sys.stderr)
    return choice, retake
