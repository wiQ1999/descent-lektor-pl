"""Arkusz porównawczy głosów (E11): OmniVoice wobec modeli ElevenLabs, z dubbingiem jako wzorcem.

Polecenia (z katalogu głównego, w .venv):
    .venv/Scripts/python -I analysis/tools/voice_compare.py pick     # losuje kwestie, szacuje koszt
    .venv/Scripts/python -I analysis/tools/voice_compare.py status   # które próbki ElevenLabs już są
    .venv/Scripts/python -I analysis/tools/voice_compare.py score    # automat E3 dla wszystkich próbek
    .venv/Scripts/python -I analysis/tools/voice_compare.py sheet    # strony arkusza do odsłuchu i ocen

Wyniki w analysis/work/compare/e11/ (nieśledzone). Na konsolę trafiają same liczby, bez tekstów gry.
Próbki ElevenLabs powstają przez MCP (skill `elevenlabs`) w analysis/work/elevenlabs/audio/e11/<głos>/<wariant>/<n>/.
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
# Modele ElevenLabs z polskim (list_models 2026-11-07). Stawka None: niezmierzona, w szacunku 1,0 (skill).
MODELS = {'eleven_v4': 0.44, 'eleven_v4_turbo': None, 'eleven_v3': None, 'eleven_v3_conversational': None,
          'eleven_multilingual_v2': None, 'eleven_flash_v2_5': None, 'eleven_turbo_v2_5': None}
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


def el_files(voice, variant, n):
    return sorted(glob.glob(os.path.join(EL_AUDIO, voice, variant, str(n), '*.mp3')))


def status():
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    missing = 0
    for voice in DESIGNED:
        for variant in VARIANTS:
            missing += not el_files(voice, variant, 0)
    print('brakujące próbki ElevenLabs: %d' % missing)


def clips():
    """Wszystkie próbki arkusza: (głos, numer kwestii albo None, wariant, plik)."""
    lines = load_json(os.path.join(OUT, 'lines.json'))['lines']
    out = []
    for voice in DUBBED:
        out.append((voice, None, 'dubbing', os.path.join(REFS, voice + '.wav')))
        for n, line in enumerate(lines[voice]):
            out.append((voice, n, 'omnivoice', line['omnivoice']))
    for voice in DESIGNED:
        for n, line in enumerate(lines[voice]):
            out.append((voice, n, 'omnivoice', line['omnivoice']))
        out += [(voice, None, variant, f) for variant in VARIANTS for f in el_files(voice, variant, 0)[:1]]
    return lines, out


def score():
    sys.path.insert(0, os.path.join(ROOT, 'analysis', 'tools', 'elevenlabs'))
    from lektor import evaluate, paths
    from score_samples import median_f0
    paths.use('m2')
    refs = load_json(os.path.join(REFS, 'refs.json'))
    scorer = evaluate.Scorer(refs)
    lines, items = clips()
    scores = load_json(os.path.join(OUT, 'scores.json'), {})
    for voice, n, variant, path in items:
        sid = '%s|%s|%s' % (voice, n, variant)
        if sid in scores:
            continue
        if variant == 'dubbing':
            scores[sid] = {'f0': median_f0(path)}
            continue
        text = lines[voice + '#design'] if voice in DESIGNED and n is None else lines[voice][n]['text']
        r = scorer(path, text, voice, 1.0)
        row = {k: (float(r[k]) if hasattr(r[k], 'item') else r[k]) for k in ('cer', 'tail_cut', 'sim', 'cps_ratio', 'seconds')
               if k in r}
        row['f0'] = median_f0(path)
        scores[sid] = row
        print(sid.split('|')[0], variant, {k: row.get(k) for k in ('cer', 'sim', 'f0')}, flush=True)
        json.dump(scores, open(os.path.join(OUT, 'scores.json'), 'w', encoding='utf-8'), indent=1)
    json.dump(scores, open(os.path.join(OUT, 'scores.json'), 'w', encoding='utf-8'), indent=1)
    print('ocenione próbki: %d' % len(scores))


if __name__ == '__main__':
    commands = {'pick': pick, 'status': status, 'score': score}
    if len(sys.argv) != 2 or sys.argv[1] not in commands and sys.argv[1] != 'sheet':
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1] == 'sheet':
        raise SystemExit('sheet: strony arkusza powstaną po decyzji o modelach i wariantach (E11, D77)')
    else:
        commands[sys.argv[1]]()
