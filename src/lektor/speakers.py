"""Wypowiedzi postaci w tekście narratora (E16, D101): podział na narrację i mowę oraz mówca każdej wypowiedzi.

Dialog w polskim tekście zaczyna się półpauzą: na początku akapitu albo po końcu zdania. Następna półpauza
kończy wypowiedź i otwiera wtrącenie narratora („– mówi Brynn.”). Po wtrąceniu półpauza wraca do mowy, gdy
wtrącenie nie ma w środku końca zdania („– Tutaj chyba nie – odpowiada jeden z uwolnionych – ale…”) albo
kończy się kropką. Półpauza w zwykłej narracji to wtrącenie („ale – sądząc po scenie – traktuje…”).
Cudzysłowy („…”) zostają narracją: to zwykle tytuły, napisy i listy.

Mówcę wskazuje wtrącenie po wypowiedzi albo narracja tuż przed nią (imię postaci), a w kwestiach bez imienia
klucz okna (Q1_BRYNN_DOOR). Automat daje propozycję; ostateczny wybór dla zakresu testu leży w
data/speakers_t1.json (klucz → głos każdej wypowiedzi albo {"pieces": głos każdego kawałka}), przejrzany ręcznie
z kontekstem okna (analysis/tools/speakers_review.py).
Głos 'arg:N': bohater z luki {N}; companion wybiera wersję kwestii w jego głosie (wiersze KLUCZ#bohater).
"""
import json
import os
import re

DASH = re.compile(r'(?:^|(?<=\s))[–—-](?=\s|[^\s\d-])')
SENTENCE_END = re.compile(r'[.!?…]["”»)]*$')
INNER_END = re.compile(r'[.!?…]["”»)]*\s+\S')
PUNCT_ONLY = re.compile(r'^[\s.,;:!?…–—\-„”"«»()]*$')
OVERRIDES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'speakers_t1.json')

# Imiona w tekście → głos. Odmiana: dopasowanie początku słowa (Galadena, Fuksowi).
NAMES = [
    (r'Brynn', 'brynn'), (r'Syrus', 'syrus'), (r'Galaden', 'galaden'), (r'Vaerix', 'vaerix'), (r'Kehli', 'kehli'),
    (r'Fuks', 'chance'), (r'hyrrinx', 'chance'), (r'Ne[’\']Krul', 'nekrul'), (r'Adelynn', 'adelynn'),
    (r'Kathryn', 'kathryn'), (r'Ronan', 'ronan'), (r'Zachareth', 'zachareth'), (r'Reneyr', 'reneyr'),
    (r'L[’\']Trand', 'ltrand'), (r'Bruli', 'bruli'), (r'Flint', 'flint'), (r'Levirax', 'levirax'),
]
NAME_RE = re.compile(r'(?<!\w)(%s)\w*' % '|'.join(n for n, _ in NAMES))
NAME_VOICE = [(re.compile(n), v) for n, v in NAMES]
SLOT = re.compile(r'\{(\d)\}')
KEY_HEROES = {'BRYNN': 'brynn', 'SYRUS': 'syrus', 'GALADEN': 'galaden', 'VAERIX': 'vaerix', 'KEHLI': 'kehli',
              'CHANCE': 'chance'}


def name_voice(word):
    for pat, voice in NAME_VOICE:
        if pat.match(word):
            return voice
    return None


def split(text):
    """[(rodzaj, tekst, akapit)]: 'n' narracja, 's' wypowiedź; akapit: numer akapitu kawałka."""
    out = []
    for i, para in enumerate(text.split('\n')):
        out += [(k, t.strip(), i) for k, t in paragraph(para) if not PUNCT_ONLY.match(t)]
    return out


def paragraph(para):
    state, start, pieces = 'n0', 0, []
    for m in DASH.finditer(para):
        before = para[start:m.start()]
        if state == 'n0':
            if para[:m.start()].strip() and not SENTENCE_END.search(para[:m.start()].rstrip()):
                continue    # półpauza w narracji: wtrącenie
            pieces.append(('n', before))
            state = 's'
        elif state == 's':
            pieces.append(('s', before))
            state = 'a'
        else:   # wtrącenie po wypowiedzi
            seg = before.strip()
            if INNER_END.search(seg) and not SENTENCE_END.search(seg):
                continue    # półpauza w środku dłuższej narracji: wtrącenie, nie mowa
            pieces.append(('n', before))
            state = 's'
        start = m.end()
    pieces.append(('s' if state == 's' else 'n', para[start:]))
    return [(k, t) for k, t in pieces if t.strip()]


def speech_text(text):
    """Wypowiedź do syntezy: bez przecinka na końcu, z kropką, gdy nie ma znaku końca zdania."""
    t = text.strip().rstrip(',;:').strip()
    if t and not re.search(r'[.!?…]["”»]*$', t):
        t += '.'
    return t


def narration_text(text):
    t = text.strip()
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t


def first_name(text, last=False):
    found = [v for v in (name_voice(m.group(0)) for m in NAME_RE.finditer(text)) if v]
    return (found[-1] if last else found[0]) if found else None


def guess(key, pieces, arg_types=()):
    """Propozycja głosu każdej wypowiedzi: [(głos albo None, uzasadnienie)]."""
    out, prev = [], {}
    for i, (kind, text, para) in enumerate(pieces):
        if kind != 's':
            continue
        nxt = pieces[i + 1] if i + 1 < len(pieces) else None
        after = nxt[1] if nxt and nxt[0] == 'n' and nxt[2] == para else ''
        before = pieces[i - 1][1] if i and pieces[i - 1][0] == 'n' else ''
        attr = re.split(r'(?<=[.!?…])\s', after, 1)[0] if after else ''
        voice, why = first_name(attr), 'po'
        if not voice and attr:
            m = SLOT.search(attr)
            if m:
                n = int(m.group(1))
                enemy = (list(arg_types[n:n + 1]) or [None])[0] == 'EntityName'
                voice, why = ('enemy:%d' if enemy else 'arg:%d') % n, 'luka po'
        if not voice and para in prev and i and pieces[i - 1][2] == para:
            voice, why = prev[para], 'ciąg'      # ta sama osoba mówi dalej po wtrąceniu
        if not voice and before:
            voice, why = first_name(before, last=True), 'przed'
        if not voice:
            hero = [v for k, v in KEY_HEROES.items() if k in key.split('_')]
            voice, why = (hero[0], 'klucz') if len(hero) == 1 else (None, '?')
        out.append((voice, why))
        prev[para] = voice
    return out


def load_overrides(path=OVERRIDES):
    if not os.path.exists(path):
        return {}
    data = json.load(open(path, encoding='utf-8'))
    return {k: v for k, v in data.items() if not k.startswith('_')}


def parts(key, text, overrides, arg_types=()):
    """[(głos, tekst)] dla kwestii narratora: narracja 'narrator', wypowiedzi głosem z nadpisań (albo automatu,
    gdy klucza nie ma w nadpisaniach). None, gdy kwestia nie ma wypowiedzi albo zostaje w całości narratorowi."""
    pieces = split(text)
    if not any(p[0] == 's' for p in pieces):
        return None
    voices = overrides.get(key)
    if voices is None:
        voices = [v for v, _ in guess(key, pieces, arg_types)]
    if voices == 'narrator':
        return None
    if isinstance(voices, dict):        # głos każdego kawałka, także narracji (półpauza w środku monologu)
        per_piece = voices['pieces']
    else:
        it = iter(voices)
        per_piece = [(next(it, None) or 'narrator') if p[0] == 's' else 'narrator' for p in pieces]
    if not any(v and v != 'narrator' for v in per_piece):
        return None
    out = []
    for (kind, t, _), voice in zip(pieces, per_piece):
        voice = voice or 'narrator'
        out.append((voice, speech_text(t) if voice != 'narrator' else narration_text(t)))
    merged = []
    for voice, t in out:        # sąsiednie kawałki tego samego głosu sklejone w jeden
        if merged and merged[-1][0] == voice:
            merged[-1] = (voice, merged[-1][1] + ' ' + t)
        else:
            merged.append((voice, t))
    return merged
