"""Podział kwestii na fragmenty do syntezy.

  - długie kwestie: zdania sklejane do LONG znaków;
  - szablony {n} (D16): stałe kawałki tekstu i luki, które companion wypełnia fragmentami wartości;
    luka liczbowa (VariableInt) przed rzeczownikiem albo ikoną obejmuje też ten rzeczownik, bo jego forma
    zależy od liczby („dwa obrażenia”, „pięć obrażeń”);
  - wybrana opcja (D20): cytat głosem bohatera i opis głosem narratora.
"""
import re

from . import normalize as N

LONG = 260          # dłuższe kwestie dzielimy na zdania
SLOT = re.compile(r'\{(\d|n)\}')   # {n}: lista wszystkich argumentów (DEFAULT_SPAWN_ENEMY_MULTI)
PUNCT_ONLY = re.compile(r'^[\s.,;:!?…–-]*$')
LEAD_PUNCT = re.compile(r'^[.,;:!?…]+\s*')
NUMBER_VALUES = range(0, 21)


def split_sentences(text, min_len=40, max_len=LONG):
    """Zdania; krótkie doklejane do sąsiednich, dopóki kawałek nie przekracza max_len."""
    parts = re.split(r'(?<=[.!?…])\s+', text)
    chunks = []
    for p in parts:
        if chunks and (len(chunks[-1]) < min_len or len(p) < min_len // 2) and len(chunks[-1]) + len(p) < max_len:
            chunks[-1] += ' ' + p
        else:
            chunks.append(p)
    return [c for c in chunks if c]


def split_long(text):
    return split_sentences(text) if len(text) > LONG else [text]


def template_pieces(raw, arg_types=()):
    """Szablon z lukami → [{'kind': 'text', 'text'} | {'kind': 'slot', 'arg', 'type', 'prev', 'noun'}].

    Kawałki tekstu są znormalizowane. Sama interpunkcja dokleja się do poprzedniego kawałka."""
    clean = N.clean_markup(raw)
    parts = SLOT.split(clean)  # tekst, numer luki, tekst, ...
    out = []
    for i in range(0, len(parts), 2):
        text = parts[i]
        if out and out[-1]['kind'] == 'slot' and out[-1]['type'] == 'VariableInt':
            fm = N.FOLLOW.match(text)
            if fm and (fm.group(1) or N.noun_gender(fm.group(2))):
                out[-1]['noun'] = fm.group(0).strip()
                text = text[fm.end():]
        norm = N.normalize(text)
        lead = LEAD_PUNCT.match(norm)
        if lead and out and out[-1]['kind'] == 'slot' and not PUNCT_ONLY.match(norm):
            out[-1]['tail'] = out[-1].get('tail', '') + lead.group(0).strip()  # „{0}! Uważaj” → luka + „Uważaj”
            norm = norm[lead.end():]
        if norm and PUNCT_ONLY.match(norm) and out:
            if out[-1]['kind'] == 'text':
                out[-1]['text'] += norm
            else:
                out[-1]['tail'] = out[-1].get('tail', '') + norm
        elif norm:
            out.append({'kind': 'text', 'text': norm})
        if i + 1 < len(parts):
            arg = int(parts[i + 1]) if parts[i + 1].isdigit() else -1
            prev = N.PREV.search(text)
            types = arg_types[max(arg, 0):][:1]
            out.append({'kind': 'slot', 'arg': arg, 'type': types[0] if types else None,
                        'prev': prev.group(1) if prev else None, 'noun': None})
    return out


def number_value_text(value, prev=None, noun=None):
    """Tekst luki liczbowej: liczba w formie zgodnej z przyimkiem przed luką i rzeczownikiem po niej."""
    if not noun:
        return N.cardinal(int(value))
    head = (prev + ' ') if prev else ''
    text = N.normalize(head + str(value) + ' ' + noun)
    if prev and text.lower().startswith(prev.lower() + ' '):
        text = text[len(prev) + 1:]
    return text


# Opcje wyboru (D20): „– Idę pierwszy – mówi Syrus.” albo „„…” – proponuje Brynn.”
QUOTE_PATTERNS = [
    re.compile(r'^[–-]\s*(?P<q>.+?)\s*[–-]\s*(?P<d>.+)$'),
    re.compile(r'^„(?P<q>.+?)”\s*[,–-]?\s*(?P<d>.*)$'),
    re.compile(r'^"(?P<q>.+?)"\s*[,–-]?\s*(?P<d>.*)$'),
]
# Polskie imiona bohaterów w opisie opcji (odmiana przez końcówki) → głos.
HERO_NAMES = {'Brynn': 'brynn', 'Syrus': 'syrus', 'Galaden': 'galaden', 'Vaerix': 'vaerix', 'Kehli': 'kehli',
              'Fuks': 'chance'}
HERO_NAME_RE = re.compile(r'\b(%s)\w*' % '|'.join(HERO_NAMES))


def choice_parts(text):
    """(cytat, opis, głos bohatera albo None) dla opcji z cytatem; None, gdy opcja nie ma cytatu."""
    for pat in QUOTE_PATTERNS:
        m = pat.match(text.strip())
        if not m:
            continue
        quote = m.group('q').rstrip(',').strip()
        if quote and quote[-1] not in '.!?…':
            quote += '.'
        desc = m.group('d').strip()
        if desc:
            desc = desc[0].upper() + desc[1:]
        # Mówca stoi w mianowniku („odpowiada Galadenowi Vaerix” → Vaerix); bez mianownika bierzemy pierwsze imię.
        names = HERO_NAME_RE.finditer(desc)
        hero = sorted(names, key=lambda m: m.group(0) != m.group(1))[:1]
        return quote, desc, HERO_NAMES[hero[0].group(1)] if hero else None
    return None
