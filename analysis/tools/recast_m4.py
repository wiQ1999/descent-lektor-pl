"""Zmiana głosów po odsłuchu zestawienia m4 (E17, D109): nowi kandydaci OmniVoice dla mówców bez imienia.

Uwagi z odsłuchu (2026-11-18): głosy „generyczne” (OmniVoice opisuje głos tylko płcią, wiekiem i wysokością), za
słabe szepty, słaba jakość i pary zbyt podobnych głosów. Każdy profil ma dwa opisy × dwa ziarna i własne zdanie
w stylu postaci (nie tekst gry). Krok `choose` dokłada do każdej próbki wariant przetworzony (przesunięcie tonu
i formantów, chrypa, drżenie), mierzy CER, F0 i barwę, a na stronę odsłuchu idą trzy kandydatury najdalsze od
wszystkich głosów obsady, także od obecnego głosu tej postaci. Pierwsza to wybór automatu.

    <omni> -I analysis/tools/recast_m4.py design      # <omni> = "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"
    .venv/Scripts/python -I analysis/tools/recast_m4.py choose     # warianty, ASR, F0, barwa → choice.json
    .venv/Scripts/python -I analysis/tools/recast_m4.py page       # index.html (także projekty ElevenLabs)
    .venv/Scripts/python -I analysis/tools/recast_m4.py adopt nv_x=B ...   # wybór z odsłuchu → refs.json

Wyniki w analysis/work/compare/m4_recast/ (nieśledzone).
"""
import glob
import hashlib
import html
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor import paths  # noqa: E402

OUT = os.path.join(ROOT, 'analysis', 'work', 'compare', 'm4_recast')
EL_DIR = os.path.join(ROOT, 'analysis', 'work', 'elevenlabs', 'audio', 'm4_recast')
SEEDS = (5, 41)
CPS = 12.5
MAX_CER = 0.10
F0_RANGE = {'male': (60, 230), 'female': (130, 420)}

# głos: płeć, dwa opisy OmniVoice, zdanie w stylu postaci, obróbka wariantu (shift: półtony z formantami,
# rasp/tremor: siła 0–1), uwaga z odsłuchu, głosy zbyt podobne (do porównania na stronie).
VOICES = {
    'nv_fof_kapitan': ('male', ['male, middle-aged, very low pitch', 'male, elderly, very low pitch'],
                       'Trzymać mury, choćby do świtu! Moja pani, bełty się kończą, ludzie padają z nóg, ale nikt stąd nie ucieknie.',
                       {'shift': -2}, 'niska barwa, nie generyczny', []),
    'nv_baelziffar': ('male', ['male, middle-aged, very low pitch', 'male, elderly, low pitch'],
                      'Ha, ha! Słyszysz ich, Galadenie? Wołają cię, a ty znowu przyjdziesz za późno. Zawsze za późno, mój mały rycerzu.',
                      {'shift': -3, 'rasp': 0.35}, 'dobry, ale zbyt podobny do wysłannika', ['nv_sq1_wyslannik']),
    'nv_straznik': ('male', ['male, middle-aged, low pitch', 'male, elderly, moderate pitch'],
                    'Nie... nie dam rady wstać. Noga... Zostawcie mnie tu, tylko zamknijcie za sobą drzwi. Proszę, idźcie już.',
                    {'tremor': 0.6}, 'zmęczony, ranny, nie generyczny', []),
    'nv_gont': ('female', ['female, young adult, moderate pitch', 'female, middle-aged, low pitch'],
                'Ha! Tę klingę hartowałam trzy dni i trzy noce. Pokaż mi kowala, który zrobi lepszą, a oddam mu swój młot.',
                {'rasp': 0.25}, 'zbyt podobna do wiedźmy', ['nv_sq1_wiedzma']),
    'nv_q11_pacjentka': ('female', ['female, elderly, moderate pitch', 'female, middle-aged, high pitch'],
                         'Och, przepraszam, ciągle ziewam. Ten napar jest okropnie gorzki, ale noga już mniej boli. Spójrzcie na mój haft!',
                         {'shift': 1}, 'słaba jakość dźwięku', []),
    'nv_q10_jezdziec': ('male', ['male, young adult, high pitch', 'male, middle-aged, high pitch'],
                        'Czas na mnie, przyjaciele. Alerion niecierpliwie bije skrzydłami. Niech wiatr wam sprzyja, do zobaczenia!',
                        {'shift': 2}, 'wyższy ton, nie generyczny', []),
    'nv_q14_kucharz': ('male', ['male, middle-aged, moderate pitch', 'male, elderly, high pitch'],
                       'Pff! Gulasz? To nie gulasz, to obraza dla garnka. Dajcie mi porządną kuchnię, a pokażę wam, co znaczy gotować!',
                       {'shift': 1}, 'słaba jakość dźwięku, inny głos', []),
    'nv_wiesniak': ('male', ['male, elderly, low pitch', 'male, middle-aged, moderate pitch'],
                    'Dzięki wam, dobrzy ludzie! Myślałem, że już po mnie. Wracam do żony, niech no tylko zobaczy, że żyję!',
                    {'tremor': 0.4}, 'generyczny', []),
    'nv_q12_duch': ('female', ['female, middle-aged, low pitch', 'female, elderly, moderate pitch'],
                    'Słyszę wasze kroki, słyszę wasze serca. Forthyn sprzedał mnie za srebro, więc niech zgniją wszyscy jego synowie.',
                    {'rasp': 0.45}, 'za cichy: syk zamiast szeptu', []),
    'nv_q14_wskrzeszeniec': ('male', ['male, elderly, high pitch', 'male, elderly, moderate pitch'],
                             'Legion wzywa... Kości pamiętają marsz. Nie śpię, nie jem, tylko idę tam, gdzie każe mi mój pan.',
                             {'tremor': 0.7}, 'za cichy, mniej szeptu', []),
    'nv_bandyta': ('male', ['male, middle-aged, very low pitch', 'male, young adult, low pitch'],
                   'Hej, wy tam! Rzucać sakiewki, bo poleje się krew! Na nich, chłopaki! Brać ich, ha, ha!',
                   {'rasp': 0.5, 'shift': -1}, 'barbarzyńskie okrzyki, nie generyczny', []),
    'nv_lisb_wartownik_a': ('male', ['male, young adult, high pitch', 'male, teenager, moderate pitch'],
                            'Znowu warta, znowu ten sam korytarz. Wiesz, ile bym dał za kufel piwa i ciepłe łóżko? Nudy, mówię ci.',
                            {'shift': 1}, 'odróżnialny od drugiego wartownika', ['nv_lisb_wartownik_b']),
    'nv_lisb_zwiadowca': ('male', ['male, middle-aged, low pitch', 'male, young adult, moderate pitch'],
                          'Melduję, pani! Wróg w sile dwudziestu włóczni idzie wąwozem od zachodu. Będą tu przed zmrokiem.',
                          {'rasp': 0.3}, 'generyczny', []),
    'nv_q14_stronnik': ('male', ['male, young adult, high pitch', 'male, middle-aged, moderate pitch'],
                        'Słuchajcie, słuchajcie! Baron Zachareth przesyła wieści! Wszyscy wierni mają stawić się przy bramie!',
                        {'shift': 1}, 'generyczny', []),
    'nv_q3_herszt': ('male', ['male, elderly, low pitch', 'male, middle-aged, very low pitch'],
                     'No proszę, bohaterowie. Ładne zbroje, ciekawe, ile za nie dostanę, kiedy już będziecie leżeć w błocie.',
                     {'rasp': 0.35, 'shift': -1}, 'generyczny', []),
    'nv_wiezien': ('male', ['male, young adult, moderate pitch', 'male, middle-aged, high pitch'],
                   'Wolny? Naprawdę wolny? Bogowie, myślałem, że zgniję w tej celi. Nie zapomnę wam tego, przysięgam!',
                   {'tremor': 0.3}, 'generyczny', []),
    'nv_gnom': ('male', ['male, middle-aged, high pitch', 'male, elderly, high pitch'],
                'Ojej, ojej, ostrożnie z tym wózkiem! Ma w sobie najdelikatniejsze tryby na całym gościńcu, słowo gnoma!',
                {'shift': 2}, 'zbyt robotyczny', []),
    'nv_q11_bandyta_nekromanta': ('male', ['male, middle-aged, low pitch', 'male, elderly, moderate pitch'],
                                  'Umarli nie narzekają, nie żądają zapłaty i nie uciekają z pola walki. Wstańcie, moi drodzy. Do roboty.',
                                  {'rasp': 0.3}, 'bez szeptu', []),
    'nv_q11_mlody_ork': ('male', ['male, young adult, low pitch', 'male, young adult, very low pitch'],
                         'Co tu robicie? Obcy nie mają tu wstępu. Pokaż ręce... No dobra, może jednak nie jesteście z tych złych.',
                         {'rasp': 0.4, 'shift': -1}, 'ork: lekko chropowaty, niski', []),
    'nv_q11_rodzic': ('male', ['male, middle-aged, moderate pitch', 'male, elderly, low pitch'],
                      'Dzieci są całe, dzięki niebiosom. Książę obiecał, że nas ochroni, i dotrzymał słowa. Teraz możemy odpocząć.',
                      {'shift': -1}, 'generyczny', []),
    'nv_q13_hybryda': ('male', ['male, middle-aged, very low pitch', 'male, elderly, very low pitch'],
                       'Xenith wzywa! Zbierać się przy bramie, natychmiast! Kto się spóźni, ten pożałuje, że wykluł się z jaja.',
                       {'rasp': 0.5, 'shift': -2}, 'generyczny', []),
    'nv_q3_bandyta_skrzynia': ('male', ['male, young adult, moderate pitch', 'male, middle-aged, high pitch'],
                               'Fuks, ten szczur, zawsze mu się trafia najlepsze. Ale ta skrzynia jest moja, słyszysz? Moja, nie jego!',
                               {'rasp': 0.4}, 'podły bandyta, syczący głos', []),
}
# ElevenLabs (postacie bez dubbingu): nowe projekty 2026-11-18, opisy w D109.
ELEVEN = {'laurel': ['adelynn', 'ltrand'], 'ltrand': ['adelynn', 'laurel'], 'ducard': ['adelynn', 'laurel', 'ltrand']}


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
    for voice, (gender, instructs, text, fx, note, near) in VOICES.items():
        for d, instruct in enumerate(instructs, 1):
            for seed in SEEDS:
                name = '%s_d%d_s%d' % (voice, d, seed)
                wav = os.path.join(OUT, 'scan', name + '.wav')
                old = scan.get(name)
                if old and (old['instruct'], old['text']) == (instruct, text) and os.path.exists(wav):
                    continue
                N.synth(model, wav, text, seed, instruct=instruct, duration=round(len(text) / CPS, 2))
                scan[name] = {'voice': voice, 'seed': seed, 'instruct': instruct, 'wav': paths.rel(wav), 'text': text}
                save('scan.json', scan)


def process(y, sr, fx):
    import librosa
    import numpy as np
    import npc_voices as N
    out = y
    if fx.get('shift'):
        out = librosa.effects.pitch_shift(out, sr=sr, n_steps=fx['shift'])
    if fx.get('tremor'):
        out = N.tremble(out, sr, fx['tremor'])
    if fx.get('rasp'):
        out = N.roughen(out, sr, fx['rasp'])
    return (out * (0.9 / (np.abs(out).max() + 1e-9))).astype(np.float32)


def choose():
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    from huggingface_hub import hf_hub_download
    from chatterbox.models.voice_encoder import VoiceEncoder
    import npc_voices as N
    scan = load('scan.json')
    for name, c in list(scan.items()):        # wariant przetworzony każdej próbki
        if c.get('fx') or c['voice'] not in VOICES:
            continue
        fx = VOICES[c['voice']][3]
        new = name + '_fx'
        wav = os.path.join(OUT, 'scan', new + '.wav')
        if new not in scan or scan[new].get('src_text') != c['text']:
            y, sr = sf.read(os.path.join(ROOT, c['wav']), dtype='float32')
            sf.write(wav, process(y, sr, fx), sr, subtype='PCM_16')
            scan[new] = {**{k: v for k, v in c.items() if k not in ('cer', 'f0', 'emb')}, 'wav': paths.rel(wav),
                         'fx': fx, 'src_text': c['text'],
                         'instruct': c['instruct'] + ', ' + ', '.join('%s %s' % kv for kv in fx.items())}
    asr = N.load_asr()
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(hf_hub_download('ResembleAI/chatterbox', 've.pt'), map_location='cpu', weights_only=True))
    ve.eval()

    def emb(y):
        e = ve.embeds_from_wavs([y], sample_rate=16000)[0]
        return e / np.linalg.norm(e)
    for c in scan.values():
        if 'cer' in c:
            continue
        y, _ = librosa.load(os.path.join(ROOT, c['wav']), sr=16000)
        gender = VOICES[c['voice']][0]
        c['cer'] = round(N.cer(c['text'], asr({'raw': y, 'sampling_rate': 16000},
                                              generate_kwargs={'language': 'polish', 'task': 'transcribe'})['text']), 3)
        f0 = librosa.pyin(y, fmin=55, fmax=250 if gender == 'male' else 500, sr=16000)[0]
        c['f0'] = round(float(np.nanmedian(f0)), 0)
        c['emb'] = emb(y).tolist()
        c['rms'] = round(float(np.sqrt(np.mean(y ** 2))), 4)
    save('scan.json', scan)
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    taken = {v: emb(librosa.load(os.path.join(ROOT, r['wav']), sr=16000)[0])      # cała obsada, także obecne głosy
             for v, r in refs.items() if r.get('wav') and os.path.exists(os.path.join(ROOT, r['wav']))}
    chosen = {}
    for voice in VOICES:
        lo, hi = F0_RANGE[VOICES[voice][0]]
        mine = [n for n, c in scan.items() if c['voice'] == voice]
        ok = [n for n in mine if scan[n]['cer'] <= MAX_CER and lo <= scan[n]['f0'] <= hi] or \
            sorted(mine, key=lambda n: scan[n]['cer'])[:3]

        def nearest(n):
            return max(float(np.dot(scan[n]['emb'], e)) for e in taken.values())
        ranked = sorted(ok, key=nearest)
        picks = []
        for n in ranked:      # trzy kandydatury o różnej barwie
            if all(float(np.dot(scan[n]['emb'], scan[p]['emb'])) < 0.93 for p in picks):
                picks.append(n)
            if len(picks) == 3:
                break
        for n in ranked:
            if len(picks) < 3 and n not in picks:
                picks.append(n)
        chosen[voice] = [{'name': n, 'nearest': round(nearest(n), 3)} for n in picks]
        print('%-26s %s' % (voice, '  '.join('%s CER %.2f F0 %3.0f sim %.3f' % (
            c['name'].replace(voice + '_', ''), scan[c['name']]['cer'], scan[c['name']]['f0'], c['nearest'])
            for c in chosen[voice])))
        taken['new:' + voice] = np.array(scan[picks[0]]['emb'])
    save('choice.json', chosen)


AUDIO_CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--card:#fff;--line:#e3e0d8;--accent:#9a3412}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecebe6;--muted:#a3a19a;--card:#1e1e1c;--line:#34332f;--accent:#fb923c}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:1100px;margin:auto}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:6px 0}
.cand{border:1px solid var(--line);border-radius:8px;padding:8px;flex:1 1 300px}
.cand.auto{border-color:var(--accent)}
.muted{color:var(--muted);font-size:13px} audio{width:100%;max-width:320px;height:34px}
code{font-size:13px} h2{margin:4px 0} button{font:inherit;padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
#out{white-space:pre-wrap;font-family:monospace;font-size:13px}
"""


def page():
    scan, chosen = load('scan.json'), load('choice.json')
    refs = json.load(open(os.path.join(paths.REFS, 'refs.json'), encoding='utf-8'))
    for sub in ('obecne', 'kandydaci', 'eleven'):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    def ref_audio(voice):
        r = refs.get(voice)
        if not r or not os.path.exists(os.path.join(ROOT, r['wav'])):
            cast = os.path.join(ROOT, 'analysis', 'work', 'compare', 'm4_cast', 'samples', voice + '_1.wav')
            if not os.path.exists(cast):
                return '<span class="muted">brak</span>'
            shutil.copyfile(cast, os.path.join(OUT, 'obecne', voice + '.wav'))
        else:
            shutil.copyfile(os.path.join(ROOT, r['wav']), os.path.join(OUT, 'obecne', voice + '.wav'))
        return '<audio controls preload="none" src="obecne/%s.wav"></audio>' % voice

    def cast_sample(voice):
        src = os.path.join(ROOT, 'analysis', 'work', 'compare', 'm4_cast', 'samples', voice + '_1.wav')
        if not os.path.exists(src):
            return ref_audio(voice)
        shutil.copyfile(src, os.path.join(OUT, 'obecne', voice + '_kwestia.wav'))
        return '<audio controls preload="none" src="obecne/%s_kwestia.wav"></audio>' % voice

    cards = []
    for voice, (letter_voice) in ((v, v) for v in ELEVEN):
        files = sorted(glob.glob(os.path.join(EL_DIR, voice, 'voice_design_*.mp3')))
        cands = []
        for i, f in enumerate(files):
            letter = 'ABC'[i]
            gid = os.path.basename(f).split('_')[2]
            shutil.copyfile(f, os.path.join(OUT, 'eleven', '%s_%s.mp3' % (voice, letter)))
            cands.append('<div class="cand"><label><input type="radio" name="%s" value="%s"> <b>%s</b></label> '
                         '<span class="muted">id %s</span><br><audio controls preload="none" src="eleven/%s_%s.mp3"></audio></div>'
                         % (voice, letter, letter, gid, voice, letter))
        near = ''.join('<div class="row"><code>%s</code> %s</div>' % (n, cast_sample(n)) for n in ELEVEN[voice])
        cards.append('<div class="card"><h2>%s <span class="muted">ElevenLabs</span></h2>'
                     '<div class="row"><span class="muted">obecny:</span> %s</div>'
                     '<div class="muted">zbyt podobne głosy:</div>%s<div class="row">%s</div>'
                     '<label><input type="radio" name="%s" value="-"> bez zmian</label></div>'
                     % (voice, cast_sample(voice), near, ''.join(cands), voice))
    for voice, cands_info in chosen.items():
        gender, instructs, text, fx, note, near = VOICES[voice]
        cands = []
        for i, c in enumerate(cands_info):
            letter = 'ABC'[i]
            s = scan[c['name']]
            shutil.copyfile(os.path.join(ROOT, s['wav']), os.path.join(OUT, 'kandydaci', '%s_%s.wav' % (voice, letter)))
            cands.append('<div class="cand%s"><label><input type="radio" name="%s" value="%s"%s> <b>%s</b>%s</label>'
                         '<div class="muted">%s · CER %.2f · F0 %.0f Hz · podobieństwo do najbliższego głosu %.2f</div>'
                         '<audio controls preload="none" src="kandydaci/%s_%s.wav"></audio></div>'
                         % (' auto' if i == 0 else '', voice, letter, ' checked' if i == 0 else '', letter,
                            ' (automat)' if i == 0 else '', html.escape(s['instruct']), s['cer'], s['f0'],
                            c['nearest'], voice, letter))
        nearrows = ''.join('<div class="row"><code>%s</code> %s</div>' % (n, ref_audio(n)) for n in near)
        cards.append('<div class="card"><h2>%s</h2><div class="muted">uwaga: %s</div>'
                     '<div class="row"><span class="muted">obecny:</span> %s</div>%s<div class="row">%s</div>'
                     '<label><input type="radio" name="%s" value="-"> bez zmian</label></div>'
                     % (voice, html.escape(note), cast_sample(voice), nearrows, ''.join(cands), voice))
    script = """
<script>
const KEY='recast-m4';
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function store(s){try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
const st=load();
document.querySelectorAll('input[type=radio]').forEach(r=>{if(st[r.name]===r.value)r.checked=true;
 r.addEventListener('change',()=>{const s=load();s[r.name]=r.value;store(s)})});
function copyList(){const names=[...new Set([...document.querySelectorAll('input[type=radio]')].map(r=>r.name))];
 const lines=names.map(n=>{const c=document.querySelector('input[name="'+n+'"]:checked');return '- '+n+': '+(c?c.value:'?')});
 const t='Wybór głosów:\\n'+lines.join('\\n');document.getElementById('out').textContent=t;
 try{navigator.clipboard.writeText(t)}catch(e){}}
</script>"""
    doc = ('<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Nowe głosy m4</title><style>%s</style></head><body><h1>Nowe głosy m4</h1>'
           '<p class="muted">Kandydaci czytają własne zdanie w stylu postaci, nie tekst gry. „Obecny” to próbka z paczki. '
           'Zaznaczony kandydat A to wybór automatu (najdalej od wszystkich głosów obsady). Wybierz i kliknij przycisk na dole.</p>'
           '%s<p><button onclick="copyList()">Kopiuj wybór</button></p><div id="out"></div>%s</body></html>'
           % (AUDIO_CSS, ''.join(cards), script))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(doc)
    print('strona:', paths.rel(os.path.join(OUT, 'index.html')), len(cards), 'głosów')


def adopt(args):
    import soundfile as sf
    scan, chosen = load('scan.json'), load('choice.json')
    path = os.path.join(paths.REFS, 'refs.json')
    refs = json.load(open(path, encoding='utf-8'))
    for arg in args:
        voice, letter = arg.split('=')
        if letter == '-':
            continue
        c = scan[chosen[voice]['ABC'.index(letter)]['name'] if isinstance(chosen[voice], list) else chosen[voice]]
        wav = os.path.join(paths.REFS, voice + '.wav')
        shutil.copyfile(os.path.join(ROOT, c['wav']), wav)
        refs[voice] = {'wav': paths.rel(wav), 'text': c['text'], 'seconds': round(sf.info(wav).duration, 2),
                       'source': 'E17 (D109): projekt OmniVoice „%s”, ziarno %d, wybór z odsłuchu %s' % (c['instruct'], c['seed'], letter),
                       'sha': hashlib.sha1(open(wav, 'rb').read()).hexdigest()}
        print('%-26s %s %5.1f s' % (voice, letter, refs[voice]['seconds']))
    json.dump(refs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'adopt':
        adopt(sys.argv[2:])
    elif cmd in ('design', 'choose', 'page'):
        globals()[cmd]()
    else:
        raise SystemExit(__doc__)
