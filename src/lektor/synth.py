"""Generowanie fragmentów M1 w OmniVoice (E3). Uruchamiać w środowisku OmniVoice:

  %LOCALAPPDATA%/LektorPL/envs/omnivoice/Scripts/python -I -m lektor generate [--limit N] [--voices ...]

Przyspieszenia względem E0 (bez zmiany modelu i ustawień próbkowania):
  - fp32 zamiast fp16: GTX 1650 Ti nie ma rdzeni tensorowych, a mnożenie macierzy w fp16 jest na niej
    5,5× wolniejsze niż w fp32 (0,38 wobec 2,1 TFLOPS);
  - tokenizer audio (0,8 GB w fp32) po zakodowaniu referencji idzie na CPU, żeby model w fp32 zmieścił się
    w 4 GB bez spadania do pamięci systemowej; dekodowanie na CPU trwa tyle samo (ok. 1,5 s);
  - gałąź bez warunku (CFG) liczona osobno, bez dopełniania do długości gałęzi z warunkiem.

Podejścia (D38): głosy bohaterów 3, pozostałe 1. Stan po każdym podejściu trafia do takes.jsonl, więc
przerwany wsad wznawia się od miejsca przerwania. Strażnik (D12) zatrzymuje wsad, gdy RTF albo VRAM
wskazują na spadanie do pamięci systemowej.
"""
import json
import math
import os
import shutil
import sys
import time

from . import db, paths
from . import direction as D

HEROES = ('brynn', 'syrus', 'galaden', 'vaerix', 'kehli', 'chance')
HERO_TAKES = 3
MANY_TAKES = (*HEROES, 'ronan')     # referencja Ronana ma urywane frazy, które czasem dają powtórzenia (QA E7)
MAX_RTF = 8.0           # po przyspieszeniach RTF ok. 2,5; powyżej 8 przez kilka fragmentów: pamięć systemowa
MAX_VRAM_GB = 3.7
SLOW_LIMIT = 5
SILENT_S = 0.35         # wynik z samym dopełnieniem ciszy (2 × 0,1 s) to pusty wynik
SILENT_RETRIES = 8      # teksty z 1–3 znaków bywają ciszą zależnie od ziarna: kolejne ziarna


def takes_for(voice):
    return HERO_TAKES if voice in MANY_TAKES and D.engine(voice) == 'omnivoice' else 1


def seed_for(fid, take, retry=0):
    return (int(fid[:8], 16) + 7919 * take + 104729 * retry) % (2 ** 31)


def take_path(fid, take):
    return os.path.join(paths.AUDIO, 'takes', '%s_t%d.wav' % (fid, take))


TAKE_LOGS = {'omnivoice': 'takes.jsonl', 'elevenlabs': 'takes_eleven.jsonl'}   # osobne pliki: oba silniki działają naraz


def take_log(engine='omnivoice'):
    return os.path.join(paths.AUDIO, TAKE_LOGS[engine])


def load_state():
    """{(fragment, podejście): wpis} z dzienników obu silników (M1 i M2 mają podejścia ElevenLabs w takes.jsonl).
    Urwany ostatni wiersz po przerwaniu procesu pomijamy: to podejście powstanie jeszcze raz."""
    out = {}
    for name in TAKE_LOGS.values():
        p = os.path.join(paths.AUDIO, name)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding='utf-8'):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            out[r['fragment'], r['take']] = r
    return out


def inherited():
    """Fragmenty przejęte z poprzedniego wydania: {id: wpis z choice.json}."""
    p = os.path.join(paths.AUDIO, 'inherited.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def inherit(con, source=None):
    """Wybrane podejścia fragmentów o tym samym id (głos z SHA referencji, tekst, tempo) z poprzedniego wydania."""
    src = os.path.join(paths.WORK, 'audio', source or paths.PREVIOUS[paths.RELEASE])
    choice = json.load(open(os.path.join(src, 'choice.json'), encoding='utf-8'))
    ids = {r['id'] for r in con.execute('SELECT id FROM fragments')}
    out = {f: c for f, c in choice.items() if f in ids}
    os.makedirs(os.path.join(paths.AUDIO, 'takes'), exist_ok=True)
    for fid, c in out.items():
        dst = take_path(fid, c['take'])
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(src, 'takes', os.path.basename(dst)), dst)
    with open(os.path.join(paths.AUDIO, 'inherited.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)
    return out


def generate_iterative_unpadded(self, task, gen_config):
    """Kopia OmniVoice._generate_iterative (08be0b4) z gałęzią bez warunku liczoną osobno.

    Oryginał liczy obie gałęzie w jednej paczce, a gałąź bez warunku (sam cel) dopełnia do długości gałęzi
    z warunkiem (styl, tekst, referencja, cel). Osobny przebieg daje te same pozycje i maski bez dopełnienia."""
    import torch
    from omnivoice.models.omnivoice import _get_time_steps, _gumbel_sample
    B, C = task.batch_size, self.config.num_audio_codebook
    mask_id = self.config.audio_mask_id
    inputs = [self._prepare_inference_inputs(task.texts[i], task.target_lens[i], task.ref_texts[i],
                                             task.ref_audio_tokens[i], task.langs[i], task.instructs[i],
                                             gen_config.denoise) for i in range(B)]
    c_lens, t_lens = [x['input_ids'].size(2) for x in inputs], task.target_lens

    def batch(lens, part):
        L = max(lens)
        ids = torch.full((B, C, L), mask_id, dtype=torch.long, device=self.device)
        am = torch.zeros((B, L), dtype=torch.bool, device=self.device)
        att = torch.zeros((B, 1, L, L), dtype=torch.bool, device=self.device)
        for i, x in enumerate(inputs):
            n = lens[i]
            ids[i, :, :n], am[i, :n] = part(x['input_ids'], n), part(x['audio_mask'], n)
            att[i, :, :n, :n] = True
            if L > n:
                pad = torch.arange(n, L, device=self.device)
                att[i, :, pad, pad] = True
        return ids, am, att

    c_ids, c_am, c_att = batch(c_lens, lambda t, n: t)
    u_ids, u_am, u_att = batch(t_lens, lambda t, n: t[..., -n:])
    tokens = torch.full((B, C, max(t_lens)), mask_id, dtype=torch.long, device=self.device)
    steps = _get_time_steps(t_start=0.0, t_end=1.0, num_step=gen_config.num_step, t_shift=gen_config.t_shift).tolist()
    schedules = []
    for t_len in t_lens:
        total = rem = t_len * C
        sched = []
        for s in range(gen_config.num_step):
            k = rem if s == gen_config.num_step - 1 else min(math.ceil(total * (steps[s + 1] - steps[s])), rem)
            sched.append(int(k))
            rem -= int(k)
        schedules.append(sched)
    layer_ids = torch.arange(C, device=self.device).view(1, -1, 1)
    for s in range(gen_config.num_step):
        c_all = self(input_ids=c_ids, audio_mask=c_am, attention_mask=c_att).logits.to(torch.float32)
        u_all = self(input_ids=u_ids, audio_mask=u_am, attention_mask=u_att).logits.to(torch.float32)
        for i in range(B):
            k = schedules[i][s]
            if k <= 0:
                continue
            c_len, t_len = c_lens[i], t_lens[i]
            pred, scores = self._predict_tokens_with_scoring(c_all[i:i + 1, :, c_len - t_len:c_len, :],
                                                             u_all[i:i + 1, :, :t_len, :], gen_config)
            scores = scores - layer_ids * gen_config.layer_penalty_factor
            if gen_config.position_temperature > 0.0:
                scores = _gumbel_sample(scores, gen_config.position_temperature)
            sample = tokens[i:i + 1, :, :t_len]
            scores.masked_fill_(sample != mask_id, -float('inf'))
            _, top = torch.topk(scores.flatten(), k)
            flat = sample.flatten()
            flat[top] = pred.flatten()[top]
            sample.copy_(flat.view_as(sample))
            tokens[i:i + 1, :, :t_len] = sample
            c_ids[i:i + 1, :, c_len - t_len:c_len] = sample
            u_ids[i:i + 1, :, :t_len] = sample
    return [tokens[i, :, :t_lens[i]] for i in range(B)]


class Synth:
    """baseline=True odtwarza ustawienia z E0 (fp16, tokenizer na GPU, gałąź bez warunku z dopełnieniem)."""

    def __init__(self, voices, refs, unpadded=True, baseline=False):
        import torch
        from omnivoice import OmniVoice
        os.environ.setdefault('HF_HOME', paths.HF_HOME)
        dtype = torch.float16 if baseline else torch.float32
        self.model = OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cuda:0', dtype=dtype)
        self.sr = self.model.sampling_rate
        self.prompts = {v: self.model.create_voice_clone_prompt(os.path.join(paths.ROOT, refs[v]['wav']), refs[v]['text'])
                        for v in voices}
        self.instruct = {v: style(refs[v]).get('instruct') for v in voices}      # instrukcja obok klonu (D94)
        if baseline:
            return
        self.model.audio_tokenizer.to('cpu')
        torch.cuda.empty_cache()
        if unpadded:
            self.model._generate_iterative = generate_iterative_unpadded.__get__(self.model)

    def __call__(self, text, voice, speed, seed):
        import numpy as np
        import torch
        torch.manual_seed(seed)
        kw = {'instruct': self.instruct[voice]} if self.instruct.get(voice) else {}
        wav = self.model.generate(text=text, language='pl', voice_clone_prompt=self.prompts[voice], speed=speed,
                                  num_step=D.MODEL['num_step'], guidance_scale=D.MODEL['guidance_scale'], **kw)[0]
        return np.asarray(wav, dtype=np.float32).reshape(-1)


def style(ref):
    return (ref or {}).get('style') or {}


def styled_speed(speed, ref):
    """Tempo podejścia: tempo fragmentu × mnożnik stylu klonu (D94). Mnożnik łączy tempo postaci i wydłużenie
    referencji, bo OmniVoice liczy długość wyniku z tempa referencji. Bez stylu tempo zostaje bez zmian."""
    f = style(ref).get('speed')
    return speed if not f else round((speed or 1.0) * f, 2)


def jobs(con, voices=None, retake=None, refs=None, order=None):
    """(fragment, podejście, tekst, głos, tempo) do wygenerowania. retake: {fragment: (podejście, tempo)}; tempo
    ponownego podejścia pochodzi z zapisanego podejścia, więc styl już w nim jest. order: {fragment: klucz
    kolejności} (m3: kolejność gry, lektor.progress), domyślnie głos i id. Głosy ElevenLabs (D80) generuje lektor.eleven."""
    refs = refs or {}
    rows = con.execute('SELECT id, voice, speed, text FROM fragments ORDER BY voice, id').fetchall()
    if order:
        rows.sort(key=lambda r: order.get(r['id'], (99,)))
    for r in rows:
        if D.engine(r['voice']) != 'omnivoice' or voices and r['voice'] not in voices:
            continue
        if retake is not None:
            if r['id'] in retake:
                take, speed = retake[r['id']]
                yield r['id'], take, r['text'], r['voice'], speed
            continue
        for take in range(1, takes_for(r['voice']) + 1):
            yield r['id'], take, r['text'], r['voice'], styled_speed(r['speed'], refs.get(r['voice']))


def generate(limit=None, voices=None, retake_file=None):
    import soundfile as sf
    import torch
    con = db.connect(paths.DB)
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    retake = None
    if retake_file:
        retake = {k: tuple(v) for k, v in json.load(open(retake_file, encoding='utf-8')).items()}
    state = load_state()
    done = inherit(con) if paths.RELEASE in paths.PREVIOUS else {}
    order = None
    if paths.RELEASE == 'm3':
        from . import progress
        order = {f: progress.rank(g) for f, g in progress.packages(con).items()}
    todo = [j for j in jobs(con, voices, retake, refs, order) if (j[0], j[1]) not in state and j[0] not in done]
    if limit:
        todo = todo[:limit]
    print('do wygenerowania: %d podejść, %d znaków' % (len(todo), sum(len(j[2]) for j in todo)), file=sys.stderr, flush=True)
    if not todo:
        return
    os.makedirs(os.path.join(paths.AUDIO, 'takes'), exist_ok=True)
    synth = Synth(sorted({j[3] for j in todo}), refs)
    log = open(take_log(), 'a', encoding='utf-8')
    slow, t_start, done_chars = 0, time.perf_counter(), 0
    for n, (fid, take, text, voice, speed) in enumerate(todo, 1):
        torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        for retry in range(SILENT_RETRIES):
            seed = seed_for(fid, take, retry)
            wav = synth(text, voice, speed, seed)
            if len(wav) / synth.sr >= SILENT_S:
                break
        gen_s = time.perf_counter() - t0
        sf.write(take_path(fid, take), wav, synth.sr, subtype='PCM_16')
        sec = len(wav) / synth.sr
        vram = torch.cuda.max_memory_reserved() / 2 ** 30
        rec = {'fragment': fid, 'take': take, 'voice': voice, 'speed': speed, 'seed': seed, 'silent_retries': retry,
               'chars': len(text), 'seconds': round(sec, 2), 'gen_s': round(gen_s, 2), 'vram_gb': round(vram, 2),
               'model': D.MODEL_ID}
        log.write(json.dumps(rec) + '\n')
        log.flush()
        done_chars += len(text)
        elapsed = time.perf_counter() - t_start
        left = sum(len(j[2]) for j in todo[n:]) * elapsed / done_chars
        print('%4d/%d %s t%d %-8s %5.1f s audio, RTF %.1f, VRAM %.2f GB, zostało ok. %.1f h' % (
            n, len(todo), fid, take, voice, sec, gen_s / max(sec, 0.1), vram, left / 3600), file=sys.stderr, flush=True)
        slow = slow + 1 if sec > 2 and gen_s / sec > MAX_RTF else 0
        if slow >= SLOW_LIMIT or vram > MAX_VRAM_GB:
            sys.exit('Strażnik: RTF %.1f / VRAM %.2f GB wskazują na pamięć systemową. Wsad zatrzymany, wznowienie '
                     'tą samą komendą.' % (gen_s / max(sec, 0.1), vram))
