"""Nowe głosy paczki testowej E16 (D101): postacie bez imienia w oknach narratora (nv_* w src/lektor/data/speakers_t1.json).

Głosy są losowe z projektu OmniVoice (płeć, wiek, wysokość, szept), bez portretu i bez QA obsady: to test podziału
okien na głosy. Każdy głos ma własne zdanie w stylu postaci (nie tekst gry) i trzy ziarna; wybór ziarna to najmniejszy
CER z wysokością w zakresie płci, a z kilku dobrych to, które leży najdalej od narratora i głosów już wybranych.

    <omni> -I analysis/tools/new_voices_t1.py design    # <omni> = "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"
    .venv/Scripts/python -I analysis/tools/new_voices_t1.py choose   # ASR, F0, barwa → choice.json
    .venv/Scripts/python -I analysis/tools/new_voices_t1.py adopt    # referencje do analysis/work/lektor/refs/ i refs.json

Wyniki w analysis/work/compare/t1/ (nieśledzone). Na konsolę idą liczby i identyfikatory.
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

OUT = os.path.join(ROOT, 'analysis', 'work', 'compare', 't1')
SEEDS = (11, 23, 37)
MAX_CER = 0.08
F0_RANGE = {'male': (70, 200), 'female': (140, 400)}
CPS = 12.5      # znaki na sekundę referencji (długość generowania)

# głos: (płeć, opis OmniVoice, zdanie w stylu postaci)
VOICES = {
    'nv_bandyta': ('male', 'male, young adult, high pitch',
                   'Oddawaj sakiewkę, póki jestem miły. Nikt cię tu nie usłyszy, a mój nóż jest dzisiaj wyjątkowo niecierpliwy.'),
    'nv_wiesniak': ('male', 'male, elderly, moderate pitch',
                    'Całe życie orałem tę ziemię i nigdy nie widziałem takiej trwogi. Ludzie znikają nocą, a rano nikt nic nie wie.'),
    'nv_straznik': ('male', 'male, middle-aged, low pitch',
                    'Trzymałem wartę przy bramie przez trzy zimy. Rany się zagoją, ale ten krzyk z ciemności zostanie ze mną na zawsze.'),
    'nv_wiezien': ('male', 'male, young adult, moderate pitch',
                   'Myślałem, że już po mnie. Trzymali nas w klatkach jak zwierzęta, a ja liczyłem każdy oddech do świtu.'),
    'nv_orban': ('male', 'male, middle-aged, high pitch',
                 'Wszystko mi zabrali, rozumiesz? Dom, pole, rodzinę! Teraz to ja zabiorę coś wam, zobaczycie, wszystko!'),
    'nv_fanatyk': ('male', 'male, young adult, low pitch',
                   'Ogień oczyści ten świat z grzechu. Śmiejcie się, póki możecie, bo wkrótce wszyscy padniecie na kolana.'),
    'nv_eurth': ('female', 'female, middle-aged, low pitch',
                 'Kości pamiętają więcej niż ludzie. Podejdź bliżej, kochanie, i pozwól, że opowiem ci, jak smakuje strach.'),
    'nv_ynfernael': ('male', 'male, elderly, very low pitch, whisper',
                     'Słyszę każdą twoją myśl. Twoja wola jest krucha jak szkło, a ja mam całą wieczność, by ją złamać.'),
    'nv_fae': ('female', 'female, child, very high pitch',
               'Raz, dwa, trzy, szukasz ty! Kwiatek żółty, kwiatek mój, a kto złapie, ten ma rój! Hop i nie ma mnie!'),
    'nv_xain': ('male', 'male, young adult, very low pitch',
                'Służyłem wiernie, dopóki honor miał jakieś znaczenie. Moja włócznia nie zna strachu, ale zna wstyd.'),
    'nv_widmo': ('female', 'female, elderly, low pitch, whisper',
                 'Długi trzeba spłacać, zawsze i wszędzie. Ja pamiętam każdą przysięgę, nawet tę, o której zapomniałeś.'),
    'nv_nekromanta': ('male', 'male, elderly, low pitch, whisper',
                      'Śmierć to tylko drzwi, a ja mam do nich klucz. Do zobaczenia wkrótce, mój drogi, bardzo wkrótce.'),
    'nv_gnom': ('male', 'male, teenager, very high pitch',
                'Stać, stać, tędy nie wolno! Trwa uroczystość, a wy depczecie po kwiatach. Proszę iść dookoła, uprzejmie proszę!'),
    'nv_gap': ('female', 'female, middle-aged, moderate pitch',
               'Słyszeliście, co się stało u młynarza? Podobno w nocy coś wyło pod oknami, a rano psy nie chciały wyjść z budy.'),
    'nv_ork': ('male', 'male, middle-aged, very low pitch',
               'Mój topór widział niejedną bitwę. Barbarzyńcy krążą blisko, ale krwawią tak samo jak każdy inny wróg.'),
    'nv_uchodzca': ('female', 'female, young adult, high pitch',
                    'Nie podchodźcie bliżej! Mamy widły i nie zawahamy się ich użyć. Straciliśmy już wszystko, co mieliśmy.'),
    'nv_glos': ('male', 'male, elderly, high pitch',
                'Hej, ty tam, tak, właśnie ty! Chodź no tu do mnie, nie bój się, staruszek nie gryzie, no chodźże wreszcie!'),
    'nv_protektor': ('male', 'male, middle-aged, moderate pitch',
                     'Cytadela potrzebuje każdego miecza. Byłem rekrutem, gdy mury jeszcze lśniły, i wierzę, że znów zalśnią.'),
    'nv_gont': ('female', 'female, young adult, low pitch',
                'Runiczne odłamki śpiewają, jeśli tylko umiesz słuchać. Ciekawe, prawda? Większość magów nawet nie próbuje.'),
    'nv_kowalka': ('female', 'female, middle-aged, very low pitch',
                   'Dobra stal nie kłamie. Pokaż mi ostrze, a powiem ci, kto je wykuł i ile razy uratowało komuś życie.'),
}


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
    for voice, (gender, instruct, text) in VOICES.items():
        for seed in SEEDS:
            name = '%s_s%d' % (voice, seed)
            wav = os.path.join(OUT, 'scan', name + '.wav')
            if not os.path.exists(wav):
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
        y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=16000)
        gender = VOICES[c['voice']][0]
        c['cer'] = round(N.cer(c['text'], asr({'raw': y, 'sampling_rate': 16000},
                                              generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']), 3)
        f0 = librosa.pyin(y, fmin=60, fmax=250 if gender == 'male' else 500, sr=16000)[0]
        c['f0'] = round(float(np.nanmedian(f0)), 0)
        c['emb'] = emb(y).tolist()
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    taken = {'narrator': emb(librosa.load(os.path.join(ROOT, refs['narrator']['wav']), sr=16000)[0])}
    chosen = {}
    for voice in VOICES:
        lo, hi = F0_RANGE[VOICES[voice][0]]
        mine = [n for n, c in scan.items() if c['voice'] == voice]
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
    print('najbliższe pary:', ', '.join('%s~%s %.3f' % (a, b, s) for s, a, b in sorted(sims, reverse=True)[:5]))
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
                       'source': 'E16 (D101): projekt OmniVoice „%s”, ziarno %d' % (c['instruct'], c['seed']),
                       'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
        print('%-14s %-22s %5.1f s' % (voice, name, refs[voice]['seconds']))
    json.dump(refs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    commands = {'design': design, 'choose': choose, 'adopt': adopt}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    commands[sys.argv[1]]()
