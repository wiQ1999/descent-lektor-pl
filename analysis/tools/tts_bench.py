"""Benchmark Chatterbox Multilingual (PL) na lokalnym GPU: 20 kwestii z zakresu Q1, warianty fp32/fp16 × cfg_weight.

Etapy:
  1. Kondycjonowanie głosu (narrator + 2 bohaterów) liczone raz i zapisywane do work/bench/conds/<głos>.pt.
  2. Generowanie: 8 dialogów, 6 narracji, 6 komunikatów questu (2 długie dzielone na zdania).
     Pomiary: czas T3 / S3Gen / znak wodny, długość audio, RTF, szczytowe VRAM (allocated/reserved),
     wymuszone EOS z AlignmentStreamAnalyzer, brak EOS (ucięcie na max_new_tokens), OOM.
  3. Kontrola ASR (Whisper large-v3-turbo, fp16): CER/WER względem tekstu, powtórzone i brakujące słowa.
  4. Podobieństwo głosu (VoiceEncoder): kosinus embeddingu próbki do nagrania referencyjnego.

fp16 oznacza T3 (model językowy, ~0,5 mld parametrów) w half precision; S3Gen i VoiceEncoder zostają w fp32.
Domyślnie po policzeniu kondycjonowania tokenizer S3, CAMPPlus i VoiceEncoder idą na CPU (−0,5 GB VRAM);
bez tego fp32 na karcie 4 GB wychodzi poza VRAM (--no-offload odtwarza zachowanie biblioteki).
Wagi i cache Hugging Face: work/hf_cache (poza repozytorium). Próbki WAV: work/bench/<wariant>/.

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/tts_bench.py            # generowanie + ASR
  .venv/Scripts/python -I analysis/tools/tts_bench.py --asr-only # tylko ponowna ocena istniejących WAV (ASR + głos)
  .venv/Scripts/python -I analysis/tools/tts_bench.py --sim-only # tylko podobieństwo głosu
"""
import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('HF_HOME', os.path.join(ROOT, 'work', 'hf_cache'))
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402

OUT = os.path.join(ROOT, 'work', 'out')
BENCH = os.path.join(ROOT, 'work', 'bench')
REFS = os.path.join(ROOT, 'work', 'voices', 'refs')
VOICES = {'narrator': 'narrator.wav', 'syrus': 'syrus.wav', 'brynn': 'brynn.wav'}
VARIANTS = [('fp32', 0.5), ('fp32', 0.3), ('fp16', 0.5), ('fp16', 0.3)]
MAX_NEW_TOKENS = 1000   # wartość wpisana na sztywno w ChatterboxMultilingualTTS.generate
SEED = 1234
TAG = re.compile(r'<[^>]+>')
PUA = re.compile('[-]')
PH = re.compile(r'\{\d+\}')
SAMPLE_NAMES = ['Syrus', 'Brynn', 'Galaden', 'Vaerix']


class WarnCounter(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def spoken(text):
    """Tekst do syntezy: bez znaczników i ikon, placeholdery zastąpione przykładowymi imionami."""
    i = iter(SAMPLE_NAMES * 3)
    text = PH.sub(lambda m: next(i), text)
    text = PUA.sub('', TAG.sub('', text))
    return re.sub(r'\s+', ' ', text).strip()


def split_sentences(text, min_len=40, max_len=260):
    parts = re.split(r'(?<=[.!?…])\s+', text)
    chunks = []
    for p in parts:
        if chunks and (len(chunks[-1]) < min_len or len(p) < min_len // 2) and len(chunks[-1]) + len(p) < max_len:
            chunks[-1] += ' ' + p
        else:
            chunks.append(p)
    return chunks


def pick_lines():
    """8 dialogów (4 Syrus, 4 Brynn), 6 narracji, 6 komunikatów questu (4 średnie + 2 długie > 400 znaków)."""
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(OUT, 'm1_scope.json'), encoding='utf-8'))['rows']

    def spread(rs, n):
        if len(rs) <= n:
            return rs
        step = len(rs) / n
        return [rs[int(i * step)] for i in range(n)]

    sel = []
    for spk, voice in (('SYRUS', 'syrus'), ('BRYNN', 'brynn')):
        rs = [r for r in rows if r['category'] == 'dialog' and r['speakers'] == [spk] and 30 <= r['chars'] <= 220]
        sel += [(r, 'dialog', voice) for r in spread(rs, 4)]
    rs = [r for r in rows if r['category'] == 'narracja_fabularna' and 60 <= r['chars'] <= 420]
    sel += [(r, 'narracja', 'narrator') for r in spread(rs, 6)]
    qm = [r for r in rows if r['category'] == 'komunikat_questu' and r['group'] == 'scene_q1']
    mid = [r for r in qm if 100 <= r['chars'] <= 260]
    long_ = sorted([r for r in qm if r['chars'] > 400], key=lambda r: -r['chars'])
    sel += [(r, 'komunikat', 'narrator') for r in spread(mid, 4)]
    sel += [(r, 'komunikat_dlugi', 'narrator') for r in long_[:2]]
    lines = []
    for i, (r, cat, voice) in enumerate(sel, 1):
        txt = spoken(terms[r['key']]['text'])
        chunks = split_sentences(txt) if cat == 'komunikat_dlugi' else [txt]
        lines.append({'id': '%02d' % i, 'key': r['key'], 'category': cat, 'voice': voice, 'chars': len(txt), 'chunks': chunks})
    return lines


def nvidia_used_mib():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, timeout=10).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return None


def load_conds(model, Conditionals):
    os.makedirs(os.path.join(BENCH, 'conds'), exist_ok=True)
    conds, timing = {}, {}
    for v, fn in VOICES.items():
        p = os.path.join(BENCH, 'conds', v + '.pt')
        t0 = time.perf_counter()
        if os.path.exists(p):
            conds[v] = Conditionals.load(p, map_location='cuda').to('cuda')
            timing[v] = {'cached': True, 's': round(time.perf_counter() - t0, 2)}
        else:
            model.prepare_conditionals(os.path.join(REFS, fn), exaggeration=0.5)
            model.conds.save(p)
            conds[v] = model.conds
            timing[v] = {'cached': False, 's': round(time.perf_counter() - t0, 2)}
    return conds, timing


def offload_conditioning(model):
    """Tokenizer S3 (~470 MiB), CAMPPlus i VoiceEncoder są potrzebne tylko do liczenia kondycjonowania.
    Po zapisaniu conds przenosimy je na CPU; S3Gen.device czyta urządzenie z tokenizera, więc podmieniamy je na flow."""
    type(model.s3gen).device = property(lambda self: next(self.flow.parameters()).device)
    model.s3gen.tokenizer.to('cpu')
    model.s3gen.speaker_encoder.to('cpu')
    model.ve.to('cpu')
    torch.cuda.empty_cache()


def synth(model, cond, text, cfg, dtype):
    """Odpowiednik ChatterboxMultilingualTTS.generate z osobnym pomiarem etapów."""
    from chatterbox.mtl_tts import punc_norm, drop_invalid_tokens
    t3c = cond.t3
    if dtype == torch.float16:
        t3c = type(t3c)(**{k: v for k, v in t3c.__dict__.items()}).to(dtype=torch.float16)
    tt = model.tokenizer.text_to_tokens(punc_norm(text), language_id='pl').to(model.device)
    tt = torch.cat([tt, tt], dim=0)
    tt = F.pad(F.pad(tt, (1, 0), value=model.t3.hp.start_text_token), (0, 1), value=model.t3.hp.stop_text_token)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.inference_mode():
        tokens = model.t3.inference(t3_cond=t3c, text_tokens=tt, max_new_tokens=MAX_NEW_TOKENS, temperature=0.8,
                                    cfg_weight=cfg, repetition_penalty=2.0, min_p=0.05, top_p=1.0)[0]
        n_tokens = int(tokens.numel())
        tokens = drop_invalid_tokens(tokens).to(model.device)
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        wav, _ = model.s3gen.inference(speech_tokens=tokens, ref_dict=cond.gen)
        torch.cuda.synchronize()
        t2 = time.perf_counter()
        wav = wav.squeeze(0).detach().cpu().numpy()
        wav = model.watermarker.apply_watermark(wav, sample_rate=model.sr)
        t3 = time.perf_counter()
    return wav, {'t3_s': t1 - t0, 's3gen_s': t2 - t1, 'watermark_s': t3 - t2, 'speech_tokens': n_tokens,
                 'no_eos': n_tokens >= MAX_NEW_TOKENS}


def run_generation(lines, offload=True):
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, Conditionals
    logging.basicConfig(level=logging.ERROR)
    wc = WarnCounter()
    logging.getLogger('chatterbox').addHandler(wc)
    torch.backends.cuda.matmul.allow_tf32 = False
    base = nvidia_used_mib()
    t0 = time.perf_counter()
    model = ChatterboxMultilingualTTS.from_pretrained(device='cuda')
    load_s = time.perf_counter() - t0
    info = {'gpu': torch.cuda.get_device_name(0), 'torch': torch.__version__, 'cuda': torch.version.cuda,
            'vram_total_mib': torch.cuda.get_device_properties(0).total_memory // 2 ** 20,
            'nvidia_used_before_mib': base, 'nvidia_used_after_load_mib': nvidia_used_mib(),
            'model_load_s': round(load_s, 1), 'allocated_after_load_mib': torch.cuda.memory_allocated() // 2 ** 20}
    conds, info['conds'] = load_conds(model, Conditionals)
    info['offload_conditioning'] = offload
    if offload:
        offload_conditioning(model)
    info['allocated_before_generation_mib'] = torch.cuda.memory_allocated() // 2 ** 20
    # rozgrzewka (kompilacja kerneli CUDA), poza pomiarem
    synth(model, conds['narrator'], 'Rozgrzewka.', 0.5, torch.float32)
    results = []
    for prec, cfg in VARIANTS:
        dtype = torch.float16 if prec == 'fp16' else torch.float32
        model.t3.to(dtype=dtype)
        vdir = os.path.join(BENCH, '%s_cfg%s' % (prec, str(cfg).replace('.', '')))
        os.makedirs(vdir, exist_ok=True)
        for ln in lines:
            torch.manual_seed(SEED + int(ln['id']))
            torch.cuda.reset_peak_memory_stats()
            wc.messages.clear()
            rec = {'variant': os.path.basename(vdir), 'precision': prec, 'cfg_weight': cfg, **{k: ln[k] for k in ('id', 'key', 'category', 'voice', 'chars')},
                   'chunks': len(ln['chunks']), 't3_s': 0.0, 's3gen_s': 0.0, 'watermark_s': 0.0, 'speech_tokens': 0, 'no_eos_chunks': 0}
            pieces = []
            try:
                for ch in ln['chunks']:
                    wav, m = synth(model, conds[ln['voice']], ch, cfg, dtype)
                    pieces += [wav, np.zeros(int(0.25 * model.sr), dtype=np.float32)]
                    for k in ('t3_s', 's3gen_s', 'watermark_s', 'speech_tokens'):
                        rec[k] += m[k]
                    rec['no_eos_chunks'] += int(m['no_eos'])
                audio = np.concatenate(pieces[:-1])
                path = os.path.join(vdir, '%s_%s_%s.wav' % (ln['id'], ln['category'], ln['voice']))
                sf.write(path, audio, model.sr, subtype='PCM_16')
                rec['audio_s'] = round(len(audio) / model.sr, 2)
                rec['gen_s'] = round(rec['t3_s'] + rec['s3gen_s'] + rec['watermark_s'], 2)
                rec['rtf'] = round(rec['gen_s'] / rec['audio_s'], 3) if rec['audio_s'] else None
                rec['wav'] = os.path.relpath(path, ROOT).replace(os.sep, '/')
                rec['oom'] = False
            except torch.cuda.OutOfMemoryError:
                rec['oom'] = True
                torch.cuda.empty_cache()
            rec['peak_allocated_mib'] = torch.cuda.max_memory_allocated() // 2 ** 20
            rec['peak_reserved_mib'] = torch.cuda.max_memory_reserved() // 2 ** 20
            rec['forced_eos'] = sum('forcing EOS' in m for m in wc.messages)
            rec['token_repetition_warnings'] = sum('repetition of token' in m for m in wc.messages)
            for k in ('t3_s', 's3gen_s', 'watermark_s'):
                rec[k] = round(rec[k], 2)
            results.append(rec)
            print(rec['variant'], rec['id'], rec.get('rtf'), rec['peak_allocated_mib'], file=sys.stderr, flush=True)
        info.setdefault('nvidia_used_peak_mib', {})[os.path.basename(vdir)] = nvidia_used_mib()
    del model, conds
    torch.cuda.empty_cache()
    return info, results


def norm_words(s):
    s = s.lower().replace('’', "'")
    s = re.sub(r"[^\w'\s-]", ' ', s)
    return [w for w in re.split(r'[\s-]+', s) if w]


def edit_distance(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev, d[j] = d[j], cur
    return d[-1]


def asr_check(lines, results):
    from transformers import pipeline
    import librosa
    asr = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', torch_dtype=torch.float16, device='cuda')
    text_of = {ln['id']: ' '.join(ln['chunks']) for ln in lines}
    for rec in results:
        if rec.get('oom') or not rec.get('wav'):
            continue
        y, sr = sf.read(os.path.join(ROOT, rec['wav']), dtype='float32')
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        hyp = asr({'raw': y, 'sampling_rate': 16000}, return_timestamps=True,
                  generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']
        ref_w, hyp_w = norm_words(text_of[rec['id']]), norm_words(hyp)
        rec['wer'] = round(edit_distance(ref_w, hyp_w) / max(1, len(ref_w)), 3)
        ref_c, hyp_c = ' '.join(ref_w), ' '.join(hyp_w)
        rec['cer'] = round(edit_distance(ref_c, hyp_c) / max(1, len(ref_c)), 3)
        # powtórzenia: słowo lub para słów powtórzona bezpośrednio w transkrypcji, a nie w tekście
        def reps(ws):
            r = sum(1 for i in range(1, len(ws)) if ws[i] == ws[i - 1] and len(ws[i]) > 2)
            r += sum(1 for i in range(3, len(ws)) if ws[i - 1:i + 1] == ws[i - 3:i - 1])
            return r
        rec['repeated_words'] = max(0, reps(hyp_w) - reps(ref_w))
        tail = set(hyp_w[-6:])
        rec['missing_tail'] = bool(ref_w) and not ({ref_w[-1], ref_w[-2] if len(ref_w) > 1 else ref_w[-1]} & tail)
        rec['words_ref'], rec['words_hyp'] = len(ref_w), len(hyp_w)
        print('asr', rec['variant'], rec['id'], rec['wer'], file=sys.stderr, flush=True)


def speaker_similarity(results):
    """Kosinus embeddingu VoiceEncoder próbki do embeddingu nagrania referencyjnego głosu (barwa, której WER nie mierzy)."""
    import librosa
    from huggingface_hub import hf_hub_download
    from chatterbox.models.voice_encoder import VoiceEncoder
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()

    def emb(path):
        e = ve.embeds_from_wavs([librosa.load(path, sr=16000)[0]], sample_rate=16000)[0]
        return e / np.linalg.norm(e)
    ref = {v: emb(os.path.join(REFS, fn)) for v, fn in VOICES.items()}
    for rec in results:
        if rec.get('wav'):
            rec['spk_sim'] = round(float(emb(os.path.join(ROOT, rec['wav'])) @ ref[rec['voice']]), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--asr-only', action='store_true')
    ap.add_argument('--sim-only', action='store_true', help='tylko podobieństwo głosu do referencji dla istniejących WAV')
    ap.add_argument('--no-offload', action='store_true', help='zostaw tokenizer S3 i VoiceEncoder na GPU (domyślne zachowanie biblioteki)')
    ap.add_argument('--variants', default=None, help='np. fp32:0.5,fp16:0.3 (domyślnie wszystkie 4)')
    a = ap.parse_args()
    if a.variants:
        VARIANTS[:] = [(p, float(c)) for p, c in (v.split(':') for v in a.variants.split(','))]
    os.makedirs(BENCH, exist_ok=True)
    lines = pick_lines()
    json.dump(lines, open(os.path.join(BENCH, 'lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    res_path = os.path.join(BENCH, 'results.json')
    if a.asr_only or a.sim_only:
        d = json.load(open(res_path, encoding='utf-8'))
        info, results = d['info'], d['results']
    else:
        info, results = run_generation(lines, offload=not a.no_offload)
        json.dump({'info': info, 'results': results}, open(res_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not a.sim_only:
        asr_check(lines, results)
    speaker_similarity(results)
    json.dump({'info': info, 'results': results}, open(res_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
