"""Arkusz porównawczy głosów (E11): OmniVoice wobec modeli ElevenLabs, z dubbingiem jako wzorcem.

Polecenia (z katalogu głównego, w .venv):
    .venv/Scripts/python -I analysis/tools/voice_compare.py pick     # losuje kwestie, szacuje koszt
    .venv/Scripts/python -I analysis/tools/voice_compare.py status   # które próbki ElevenLabs już są
    .venv/Scripts/python -I analysis/tools/voice_compare.py score    # automat E3 dla wszystkich próbek
    .venv/Scripts/python -I analysis/tools/voice_compare.py sheet    # strony arkusza do odsłuchu i ocen

Wyniki w analysis/work/compare/e11/ (nieśledzone). Na konsolę trafiają same liczby, bez tekstów gry.
Próbki ElevenLabs powstają przez MCP (skill `elevenlabs`) w analysis/work/elevenlabs/audio/e11/<głos>/<wariant>/0/:
text_to_voice z opisami z voice_designs_e11.json, 3 podglądy na opis. `score` ocenia wszystkie, a `sheet` bierze najlepszy
podgląd z każdego opisu i buduje strony z szablonu voice_compare.html.
"""
import glob
import json
import os
import random
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WORK = os.path.join(ROOT, 'analysis', 'work')
OUT = os.path.join(WORK, 'compare', 'e11')
EL_AUDIO = os.path.join(WORK, 'elevenlabs', 'audio', 'e11')
DB = os.path.join(WORK, 'lektor', 'm2.sqlite')
AUDIO = os.path.join(WORK, 'audio', 'm2')
REFS = os.path.join(WORK, 'lektor', 'refs')
SEED = 20261107
MIN_WORDS = 7           # „dłuższe niż 6 wyrazów”
MAX_CHARS = 220         # górna granica kosztu jednej kwestii
MIN_DESIGN_CHARS = 100  # text_to_voice wymaga 100–1000 znaków tekstu podglądu

# Głosy z dubbingu: wzorcem jest referencja z gry, porównanie bez ElevenLabs (D77). Głosy projektowane (D41):
# oryginału nie ma, porównujemy OmniVoice z wariantami ElevenLabs.
DUBBED = ('narrator', 'brynn', 'syrus', 'galaden', 'vaerix', 'kehli', 'chance', 'nekrul', 'xenith')
DESIGNED = ('adelynn', 'ronan', 'astarra', 'kathryn', 'ltrand', 'bruli', 'herbie', 'mok', 'outlaw', 'flint', 'galgoraz')
NARRATOR_CATEGORIES = ('narracja_fabularna', 'komunikat_questu')
VARIANTS = ('a', 'b', 'c')    # trzy różne opisy głosu postaci bez dubbingu
DESIGN_RATE = 1.0
SHEETS = (('a1', 'Narrator i złoczyńcy', ('narrator', 'nekrul', 'xenith')),
          ('a2', 'Bohaterowie: Brynn, Syrus, Galaden', ('brynn', 'syrus', 'galaden')),
          ('a3', 'Bohaterowie: Vaerix, Kehli, Fuks', ('vaerix', 'kehli', 'chance')),
          ('b1', 'Postacie bez dubbingu (1)', DESIGNED[:6]),
          ('b2', 'Postacie bez dubbingu (2)', DESIGNED[6:]))


def load_json(path, default=None):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


def candidates(con, manifest, voice):
    """Kwestie jednego fragmentu tekstu czytane tym głosem, z gotowym audio bez problemów automatu."""
    rows = con.execute("""
        select l.key, l.category, s.fragment, f.text from lines l join segments s on s.key = l.key
        join fragments f on f.id = s.fragment
        where l.tts = 1 and l.voice = ? and s.kind = 'text' and s.voice = l.voice
          and l.key in (select key from segments group by key having count(*) = 1)
        order by l.key""", (voice,)).fetchall()
    out = []
    for key, category, frag, text in rows:
        m = manifest.get(frag)
        if m and len(text.split()) >= MIN_WORDS and len(text) <= MAX_CHARS:
            out.append({'key': key, 'category': category, 'fragment': frag, 'text': text, 'chars': len(text),
                        'omnivoice': os.path.join(AUDIO, m['file']), 'problems': m['problems']})
    clean = [c for c in out if not c['problems']]
    return clean or out     # Ne'Krul ma jedną kwestię i automat zgłosił w niej problem: arkusz to pokazuje


def pick_lines(pool, voice, rng):
    if voice == 'narrator':
        return [rng.choice([c for c in pool if c['category'] == cat]) for cat in NARRATOR_CATEGORIES]
    if len(pool) <= 2:
        return pool
    for _ in range(200):
        two = rng.sample(pool, 2)
        if voice not in DESIGNED or sum(c['chars'] for c in two) + 1 >= MIN_DESIGN_CHARS:
            return two
    raise SystemExit('%s: brak pary kwestii o długości podglądu' % voice)


def pick():
    con = sqlite3.connect(DB)
    manifest = load_json(os.path.join(AUDIO, 'manifest.json'))['fragments']
    rng = random.Random(SEED)
    chosen = {}
    for voice in DUBBED + DESIGNED:
        chosen[voice] = pick_lines(candidates(con, manifest, voice), voice, rng)
        if voice in DESIGNED:
            chosen[voice + '#design'] = ' '.join(c['text'] for c in chosen[voice])
    os.makedirs(OUT, exist_ok=True)
    json.dump({'seed': SEED, 'lines': chosen}, open(os.path.join(OUT, 'lines.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    design_chars = sum(len(chosen[v + '#design']) for v in DESIGNED)
    print('głos        kwestie  znaki')
    for v in DUBBED + DESIGNED:
        print('%-11s %7d %6d' % (v, len(chosen[v]), sum(c['chars'] for c in chosen[v])))
    design = design_chars * DESIGN_RATE * len(VARIANTS)
    print('\nszacunek kredytów: text_to_voice %.0f (%d postaci x %d opisy, podglądy %d znaków)' % (
        design, len(DESIGNED), len(VARIANTS), design_chars))



NAMES = {'narrator': 'Narrator', 'brynn': 'Brynn', 'syrus': 'Syrus', 'galaden': 'Galaden', 'vaerix': 'Vaerix',
         'kehli': 'Kehli', 'chance': 'Fuks', 'nekrul': "Ne'Krul", 'xenith': 'Xenith', 'adelynn': 'Baronowa Adelynn',
         'ronan': 'Ronan', 'astarra': 'Astarra', 'kathryn': 'Kathryn', 'ltrand': 'Porucznik Rand', 'bruli': 'Mistrz Bruli',
         'herbie': 'Herbie', 'mok': 'Starszy Mok', 'outlaw': 'Książę Banitów', 'flint': 'Mistrz Flint',
         'galgoraz': 'Mistrz Galgoraz'}
PORTRAIT_ROUND = {'adelynn': 'r1', 'ronan': 'r1', 'astarra': 'r1', 'kathryn': 'r2', 'ltrand': 'r2', 'bruli': 'r2',
                  'herbie': 'r3', 'mok': 'r3', 'outlaw': 'r3', 'flint': 'r4', 'galgoraz': 'r4'}
PORTRAITS = os.path.join(WORK, 'lektor', 'voice_design', 'e7')
DESIGNS = os.path.join(ROOT, 'analysis', 'tools', 'voice_designs_e11.json')
GAP_S = 0.5                 # pauza między sklejonymi kwestiami OmniVoice
GAME_CHARS = 1_430_000      # cała gra (D02)
M2_GPU_H, GAME_GPU_H = 16, 110   # OmniVoice na GTX 1650 Ti (ODTWORZENIE.md, E7_AUDIO.md)
GROUPS = (('Narrator', ('narrator',)), ('Bohaterowie z dubbingiem', ('brynn', 'syrus', 'galaden', 'vaerix', 'kehli', 'chance')),
          ('Złoczyńcy z dubbingiem', ('nekrul', 'xenith')), ('Postacie bez dubbingu', DESIGNED))
METRICS = ('cer', 'tail_cut', 'missing', 'sim', 'cps_ratio', 'pause', 'speech_s')
# Runda 2 (D79): zwycięski głos każdej postaci zapisany na koncie, te same kwestie czytane czterema modelami TTS.
R2_AUDIO = os.path.join(WORK, 'elevenlabs', 'audio', 'e11r2')
R2_MODELS = ('eleven_v4', 'eleven_multilingual_v2', 'eleven_flash_v2_5', 'eleven_v3')
# Jeden wariant na postać; przy remisie ocen ten bliższy portretowi i CASTING.md (wybór obsady zostaje otwarty).
R2_VOICES = {'adelynn': 'b', 'ronan': 'b', 'astarra': 'b', 'kathryn': 'a', 'ltrand': 'a', 'bruli': 'a', 'herbie': 'c',
             'mok': 'a', 'outlaw': 'b', 'flint': 'a', 'galgoraz': 'a'}
R2_SHEETS = (('c1', 'Runda 2: modele TTS (1)', DESIGNED[:6]), ('c2', 'Runda 2: modele TTS (2)', DESIGNED[6:]))
# Kredyty na znak z historii konta (E9, E11: 1921 znaków na model).
RATES = {'eleven_v4': 0.44, 'eleven_multilingual_v2': 0.44, 'eleven_flash_v2_5': 0.22, 'eleven_v3': 0.44}


def el_files(voice, variant, n=0):
    return sorted(glob.glob(os.path.join(EL_AUDIO, voice, variant, str(n), '*.mp3')))


def status():
    have = sum(len(el_files(v, x)) for v in DESIGNED for x in VARIANTS)
    missing = ['%s/%s' % (v, x) for v in DESIGNED for x in VARIANTS if not el_files(v, x)]
    print('podglądy ElevenLabs: %d, opisy bez podglądów: %d %s' % (have, len(missing), ' '.join(missing)))


def r2_file(voice, model):
    files = sorted(glob.glob(os.path.join(R2_AUDIO, voice, model, '*.mp3')))
    return files[-1] if files else None


def text_of(lines, voice):
    return ' '.join(c['text'] for c in lines[voice])


def omnivoice_clip(lines, voice):
    """Kwestie OmniVoice sklejone w jedno nagranie, żeby porównywać ten sam tekst co podgląd ElevenLabs."""
    import numpy as np
    import soundfile as sf
    path = os.path.join(OUT, 'clips', 'omnivoice', voice + '.wav')
    if not os.path.exists(path):
        parts, sr = [], None
        for c in lines[voice]:
            y, sr = sf.read(c['omnivoice'], dtype='float32')
            parts += [y, np.zeros(int(GAP_S * sr), np.float32)]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sf.write(path, np.concatenate(parts[:-1]), sr, subtype='PCM_16')
    return path


def items():
    """Nagrania do oceny automatem: (id, głos, rodzaj, plik)."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    out = []
    for voice in DUBBED + DESIGNED:
        out.append(('%s|omnivoice' % voice, voice, 'omnivoice', omnivoice_clip(lines, voice)))
        if voice in DUBBED:
            out.append(('%s|dubbing' % voice, voice, 'dubbing', os.path.join(REFS, voice + '.wav')))
            continue
        for x in VARIANTS:
            out += [('%s|%s|%s' % (voice, x, os.path.basename(f)), voice, x, f) for f in el_files(voice, x)]
        out += [('%s|r2|%s' % (voice, m), voice, 'r2', r2_file(voice, m)) for m in R2_MODELS if r2_file(voice, m)]
    return lines, out


def score():
    sys.path.insert(0, os.path.join(ROOT, 'analysis', 'tools', 'elevenlabs'))
    from lektor import evaluate, paths
    from score_samples import median_f0
    paths.use('m2')
    lines, todo = items()
    path = os.path.join(OUT, 'scores.json')
    scores = load_json(path, {})
    todo = [t for t in todo if t[0] not in scores]
    scorer = evaluate.Scorer(load_json(os.path.join(REFS, 'refs.json'))) if todo else None
    for sid, voice, kind, f in todo:
        row = {}
        if kind != 'dubbing':
            r = scorer(f, text_of(lines, voice), voice, 1.0)
            row = {k: (r[k].item() if hasattr(r[k], 'item') else r[k]) for k in METRICS if k in r}
        row['f0'] = median_f0(f)
        if kind == 'r2':    # czy model TTS zachował głos z podglądu rundy 1
            ref = best_preview(scores, voice, R2_VOICES[voice])[0]
            row['sim_preview'] = round(float(scorer.embed(scorer.load(f)) @ scorer.embed(scorer.load(ref))), 3)
        scores[sid] = row
        print(voice, kind, {k: row.get(k) for k in ('cer', 'tail_cut', 'sim', 'f0')}, flush=True)
        json.dump(scores, open(path, 'w', encoding='utf-8'), indent=1)
    print('ocenione nagrania: %d' % len(scores))


def best_preview(scores, voice, variant):
    """Najlepszy z trzech podglądów opisu: bez uciętej końcówki i dziur, potem najniższy CER."""
    cands = [(f, scores.get('%s|%s|%s' % (voice, variant, os.path.basename(f)))) for f in el_files(voice, variant)]
    cands = [(f, s) for f, s in cands if s and 'cer' in s]
    return min(cands, key=lambda c: (bool(c[1].get('tail_cut')), c[1].get('missing', 0) >= 2, c[1]['cer']), default=None)


def level_copy(src, dst):
    import librosa
    import soundfile as sf
    from lektor.finalize import level
    if not os.path.exists(dst):
        y, sr = librosa.load(src, sr=None, mono=True)
        sf.write(dst, level(y, sr)[0], sr, subtype='PCM_16')
    return os.path.relpath(dst, OUT).replace(os.sep, '/')


def portrait(voice):
    import shutil
    if voice not in PORTRAIT_ROUND:
        return None
    dst = os.path.join(OUT, 'portraits', voice + '.png')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copy(os.path.join(PORTRAITS, PORTRAIT_ROUND[voice], voice + '.png'), dst)
    return 'portraits/%s.png' % voice


def page_data(page, title, voices, lines, scores, designs):
    os.makedirs(os.path.join(OUT, 'clips', page), exist_ok=True)
    out = []
    for voice in voices:
        omni = {'label': 'OmniVoice (lokalnie, obecny głos)', 'kind': 'omnivoice',
                'src': os.path.join(OUT, 'clips', 'omnivoice', voice + '.wav'), 'metrics': scores.get(voice + '|omnivoice', {})}
        if voice in DUBBED:
            entries = [dict(id='orig', label='Oryginał z gry (dubbing, inny tekst)', kind='dubbing',
                            src=os.path.join(REFS, voice + '.wav'), metrics=scores.get(voice + '|dubbing', {})),
                       dict(omni, id='omni')]
        else:
            entries = [omni]
            for x in VARIANTS:
                best = best_preview(scores, voice, x)
                if best:
                    entries.append({'label': 'ElevenLabs, wariant %s' % x, 'kind': 'el_' + x, 'src': best[0],
                                    'metrics': best[1], 'desc': designs[voice][x],
                                    'voice_id': os.path.basename(best[0]).split('_')[2]})
            random.Random('%d-%s' % (SEED, voice)).shuffle(entries)
            for e, letter in zip(entries, 'ABCD'):
                e['id'] = letter
        for e in entries:
            e['file'] = level_copy(e.pop('src'), os.path.join(OUT, 'clips', page, '%s_%s.wav' % (voice, e['id'])))
        out.append({'voice': voice, 'name': NAMES[voice], 'kind': 'dubbed' if voice in DUBBED else 'designed',
                    'portrait': portrait(voice), 'lines': [c['text'] for c in lines[voice]],
                    'problems': sorted({p for c in lines[voice] for p in c['problems']}), 'clips': entries})
    return {'page': page, 'title': title, 'voices': out}


def page_data2(page, title, voices, lines, scores, designs):
    os.makedirs(os.path.join(OUT, 'clips', page), exist_ok=True)
    out = []
    for voice in voices:
        x = R2_VOICES[voice]
        best = best_preview(scores, voice, x)
        entries = [{'label': m, 'kind': m, 'src': r2_file(voice, m),
                    'metrics': dict(scores.get('%s|r2|%s' % (voice, m), {}), rate=RATES[m])} for m in R2_MODELS]
        random.Random('%d-r2-%s' % (SEED, voice)).shuffle(entries)
        for e, letter in zip(entries, 'ABCD'):
            e['id'] = letter
        entries.insert(0, {'id': 'orig', 'label': 'Wzorzec: podgląd z rundy 1 (wariant %s)' % x, 'kind': 'preview',
                           'src': best[0], 'metrics': best[1], 'desc': designs[voice][x]})
        for e in entries:
            e['file'] = level_copy(e.pop('src'), os.path.join(OUT, 'clips', page, '%s_%s.wav' % (voice, e['id'])))
        out.append({'voice': voice, 'name': NAMES[voice], 'kind': 'models', 'portrait': portrait(voice),
                    'lines': [c['text'] for c in lines[voice]], 'problems': [], 'clips': entries})
    intro = ('Każda próbka czyta te same dwie kwestie tym samym głosem ElevenLabs. Próbki A–D to cztery modele TTS '
             'w losowej kolejności. Wzorzec to podgląd z rundy 1 i nie podlega ocenie. Oceń wymowę, naturalność '
             'i zgodność z wzorcem (1 = źle, 5 = bardzo dobrze), potem odsłoń etykiety.')
    return {'page': page, 'title': title, 'intro': intro, 'voices': out}


def costs():
    con = sqlite3.connect(DB)
    chars = dict(con.execute('select voice, sum(chars) from fragments group by voice'))
    total = sum(chars.values())
    groups = [(name, sum(chars.get(v, 0) for v in vs)) for name, vs in GROUPS]
    return {'m2_chars': total, 'game_chars': GAME_CHARS, 'groups': groups,
            'limit': 127047, 'm2_gpu_h': M2_GPU_H, 'game_gpu_h': GAME_GPU_H,
            'rates': [('OmniVoice (lokalnie)', 0, 'brak kredytów, czas GPU')]
            + [(m, RATES[m], 'zmierzona (E11)') for m in R2_MODELS]}


def sheet():
    import html as H
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    designs = load_json(DESIGNS)
    pages = [page_data(p, t, vs, lines, scores, designs) for p, t, vs in SHEETS]
    if all(r2_file(v, m) for v in DESIGNED for m in R2_MODELS):
        pages += [page_data2(p, t, vs, lines, scores, designs) for p, t, vs in R2_SHEETS]
    json.dump(pages, open(os.path.join(OUT, 'sheet.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    template = open(os.path.join(ROOT, 'analysis', 'tools', 'voice_compare.html'), encoding='utf-8').read()
    nav = [{'page': p['page'], 'title': p['title'],
            'ratable': sum(c['id'] != 'orig' for v in p['voices'] for c in v['clips'])} for p in pages]
    for p in pages:
        body = json.dumps({'mode': 'page', 'data': p, 'nav': nav}, ensure_ascii=False).replace('</', '<\\/')
        open(os.path.join(OUT, p['page'] + '.html'), 'w', encoding='utf-8').write(
            template.replace('__TITLE__', H.escape('E11 · ' + p['title'])).replace('__DATA__', body))
    body = json.dumps({'mode': 'index', 'nav': nav, 'costs': costs()}, ensure_ascii=False).replace('</', '<\\/')
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(
        template.replace('__TITLE__', 'E11 · Arkusz porównawczy głosów').replace('__DATA__', body))
    clips = sum(len(v['clips']) for p in pages for v in p['voices'])
    print('strony: %d, nagrania: %d -> %s' % (len(pages) + 1, clips, os.path.join(OUT, 'index.html')))


if __name__ == '__main__':
    commands = {'pick': pick, 'status': status, 'score': score, 'sheet': sheet}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    commands[sys.argv[1]]()
