"""Generowanie próbek porównania TTS (E0) dla jednego kandydata. Uruchamiane w środowisku danego modelu.

Czyta work/bakeoff/set.json (bakeoff_set.py) i zapisuje work/bakeoff/<model>/<zadanie>_t<k>.wav oraz gen.json
(czas generowania, RTF, szczyt pamięci GPU). Istniejące pliki są pomijane, więc przebieg można wznowić.
Zadania z polem models (warianty P rundy 2) generuje tylko wskazany model, z parametrami z pola gen.

Kandydaci i środowiska (D27):
  chatterbox2  Chatterbox Multilingual v2 (0.1.7), fp32, cfg 0,3, exaggeration z emocji   .venv
  chatterbox3  Chatterbox Multilingual v3 (GitHub master), domyślne generate()          %LOCALAPPDATA%/LektorPL/envs/chatterbox3
  xtts         XTTS-v2 (coqui-tts), wagi na licencji CPML                                 %LOCALAPPDATA%/LektorPL/envs/xtts
  omnivoice    OmniVoice (k2-fsa), fp16, 32 kroki                                          %LOCALAPPDATA%/LektorPL/envs/omnivoice

Uruchomienie (z katalogu głównego repozytorium):
  <python środowiska> -I analysis/tools/bakeoff_gen.py <model> [--only F01_A ...] [--force]
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('HF_HOME', os.path.join(ROOT, 'work', 'hf_cache'))
BAKE = os.path.join(ROOT, 'work', 'bakeoff')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

CFG = 0.3


def trim(wav, sr):
    import librosa
    if len(wav) < sr // 10:
        return wav
    _, (a, b) = librosa.effects.trim(wav, top_db=40, frame_length=1024, hop_length=256)
    return wav[max(0, a - int(0.03 * sr)): b + int(0.05 * sr)]


class Chatterbox:
    """v2: nasza ścieżka z tts_bench (fp32, cfg 0,3, offload modułów kondycjonowania).
    v3: oficjalne generate() z kodu master, ten sam offload i te same parametry cfg/exaggeration."""
    native_speed = False

    def __init__(self, version, set_data):
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        import tts_bench as TB
        self.TB, self.version, self.set = TB, version, set_data
        if version == 3:
            self.model = ChatterboxMultilingualTTS.from_pretrained(device='cuda', t3_model='v3')
        else:
            self.model = ChatterboxMultilingualTTS.from_pretrained(device='cuda')
        self.sr = self.model.sr
        self.conds = {}
        cache = os.path.join(BAKE, 'conds', 'chatterbox%d' % version)
        os.makedirs(cache, exist_ok=True)
        from chatterbox.mtl_tts import Conditionals
        for voice, by_emo in set_data['refs'].items():
            for emo, ref in by_emo.items():
                exag = set_data['emotions'][emo]['exag']
                p = os.path.join(cache, '%s__%s.pt' % (voice, emo))
                if os.path.exists(p):
                    self.conds[voice, emo] = Conditionals.load(p, map_location='cuda').to('cuda')
                else:
                    self.model.prepare_conditionals(os.path.join(ROOT, ref['wav']), exaggeration=exag)
                    self.model.conds.save(p)
                    self.conds[voice, emo] = self.model.conds
        TB.offload_conditioning(self.model)

    def synth(self, text, voice, emo, lang, speed=None):
        cond = self.conds[voice, emo]
        if self.version == 3:
            self.model.conds = cond
            wav = self.model.generate(text, language_id=lang, exaggeration=self.set['emotions'][emo]['exag'],
                                      cfg_weight=CFG)
            return wav.squeeze(0).numpy()
        return self._synth_v2(cond, text, lang)

    def _synth_v2(self, cond, text, lang):
        import torch.nn.functional as F
        from chatterbox.mtl_tts import punc_norm, drop_invalid_tokens
        m = self.model
        tt = m.tokenizer.text_to_tokens(punc_norm(text), language_id=lang).to(m.device)
        tt = torch.cat([tt, tt], dim=0)
        tt = F.pad(F.pad(tt, (1, 0), value=m.t3.hp.start_text_token), (0, 1), value=m.t3.hp.stop_text_token)
        with torch.inference_mode():
            tokens = m.t3.inference(t3_cond=cond.t3, text_tokens=tt, max_new_tokens=self.TB.MAX_NEW_TOKENS,
                                    temperature=0.8, cfg_weight=CFG, repetition_penalty=2.0, min_p=0.05, top_p=1.0)[0]
            tokens = drop_invalid_tokens(tokens).to(m.device)
            wav, _ = m.s3gen.inference(speech_tokens=tokens, ref_dict=cond.gen)
            wav = wav.squeeze(0).detach().cpu().numpy()
            return m.watermarker.apply_watermark(wav, sample_rate=m.sr)


class Xtts:
    native_speed = True

    def __init__(self, set_data):
        from huggingface_hub import snapshot_download
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts as XttsModel
        if os.environ.get('LEKTOR_CPML_ACCEPTED') != '1':
            sys.exit('Wagi XTTS-v2 są na licencji CPML (niekomercyjnej). Uruchom z LEKTOR_CPML_ACCEPTED=1 dopiero po zgodzie użytkownika.')
        ckpt = snapshot_download('coqui/XTTS-v2')
        config = XttsConfig()
        config.load_json(os.path.join(ckpt, 'config.json'))
        self.model = XttsModel.init_from_config(config)
        self.model.load_checkpoint(config, checkpoint_dir=ckpt, use_deepspeed=False)
        self.model.cuda().eval()
        self.sr = 24000
        self.latents = {}
        for voice, by_emo in set_data['refs'].items():
            for emo, ref in by_emo.items():
                self.latents[voice, emo] = self.model.get_conditioning_latents(audio_path=[os.path.join(ROOT, ref['wav'])])

    def synth(self, text, voice, emo, lang, speed=None):
        gpt_cond, spk = self.latents[voice, emo]
        out = self.model.inference(text, lang, gpt_cond, spk, temperature=0.7, speed=speed or 1.0,
                                   enable_text_splitting=False)
        return np.asarray(out['wav'], dtype=np.float32)


class OmniVoiceBackend:
    native_speed = True

    def __init__(self, set_data):
        from omnivoice import OmniVoice
        self.model = OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cuda:0', dtype=torch.float16)
        self.sr = self.model.sampling_rate
        self.prompts = {}
        for voice, by_emo in set_data['refs'].items():
            for emo, ref in by_emo.items():
                if not ref.get('text'):
                    sys.exit('Brak transkrypcji referencji %s/%s: uruchom bakeoff_set.py --transcribe' % (voice, emo))
                ref = ref.get('short', ref)  # narrator: wycinek z transkrypcją zgodną z audio (--short-prompts)
                self.prompts[voice, emo] = self.model.create_voice_clone_prompt(os.path.join(ROOT, ref['wav']), ref['text'])

    def synth(self, text, voice, emo, lang, speed=None, **gen):
        wav = self.model.generate(text=text, language=lang, voice_clone_prompt=self.prompts[voice, emo], speed=speed,
                                  **gen)[0]
        return np.asarray(wav, dtype=np.float32).reshape(-1)


def make_backend(name, set_data):
    if name == 'chatterbox2':
        return Chatterbox(2, set_data)
    if name == 'chatterbox3':
        return Chatterbox(3, set_data)
    if name == 'xtts':
        return Xtts(set_data)
    if name == 'omnivoice':
        return OmniVoiceBackend(set_data)
    sys.exit('nieznany model: ' + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model', choices=['chatterbox2', 'chatterbox3', 'xtts', 'omnivoice'])
    ap.add_argument('--only', nargs='*', help='identyfikatory zadań, np. F01_A')
    ap.add_argument('--force', action='store_true', help='generuj ponownie istniejące próbki (z --only)')
    a = ap.parse_args()
    set_data = json.load(open(os.path.join(BAKE, 'set.json'), encoding='utf-8'))
    ref_voice = set_data['ref_voice']
    out_dir = os.path.join(BAKE, a.model)
    os.makedirs(out_dir, exist_ok=True)
    gen_path = os.path.join(out_dir, 'gen.json')
    results = json.load(open(gen_path, encoding='utf-8')) if os.path.exists(gen_path) else {}

    t0 = time.perf_counter()
    backend = make_backend(a.model, set_data)
    load_s = time.perf_counter() - t0
    sr = backend.sr
    backend.synth('Rozgrzewka.', 'narrator', 'neutralny', 'pl')  # pierwsze wywołanie kompiluje jądra CUDA
    torch.cuda.reset_peak_memory_stats()

    for job in set_data['jobs']:
        if a.only and job['id'] not in a.only or a.model not in job.get('models', [a.model]):
            continue
        speed = job['post'].get('speed')
        for take in range(job['takes']):
            name = '%s_t%d' % (job['id'], take + 1)
            path = os.path.join(out_dir, name + '.wav')
            if os.path.exists(path) and name in results and not a.force:
                continue
            torch.manual_seed(job['seed'] + take)
            np.random.seed(job['seed'] + take)
            parts, gen_s = [], 0.0
            torch.cuda.reset_peak_memory_stats()
            for p in job['pieces']:
                voice = ref_voice.get(p['voice'], p['voice'])
                torch.cuda.synchronize()
                t = time.perf_counter()
                wav = backend.synth(p['text'], voice, p['emotion'], p['lang'],
                                    speed=speed if backend.native_speed else None, **job.get('gen', {}))
                torch.cuda.synchronize()
                gen_s += time.perf_counter() - t
                parts += [trim(np.asarray(wav, dtype=np.float32), sr), np.zeros(int(p['gap'] * sr), np.float32)]
            wav = np.concatenate(parts[:-1])
            if speed and not backend.native_speed:
                from style_samples import wsola
                wav = wsola(wav, speed, sr)
            peak = np.max(np.abs(wav)) or 1.0
            if peak > 0.99:
                wav = wav / peak * 0.99
            sf.write(path, wav, sr, subtype='PCM_16')
            audio_s = len(wav) / sr
            results[name] = {'job': job['id'], 'take': take + 1, 'wav': os.path.relpath(path, ROOT).replace(os.sep, '/'),
                             'audio_s': round(audio_s, 2), 'gen_s': round(gen_s, 2), 'rtf': round(gen_s / max(audio_s, 1e-3), 3),
                             'peak_mib': round(torch.cuda.max_memory_allocated() / 2 ** 20)}
            json.dump(results, open(gen_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(a.model, name, results[name]['audio_s'], 's, RTF', results[name]['rtf'], file=sys.stderr, flush=True)
    meta_path = os.path.join(out_dir, 'meta.json')
    json.dump({'model': a.model, 'load_s': round(load_s, 1), 'sr': sr, 'torch': torch.__version__,
               'gpu': torch.cuda.get_device_name(0)}, open(meta_path, 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
