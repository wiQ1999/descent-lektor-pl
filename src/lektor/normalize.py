"""Normalizacja tekstu PL do syntezy.

  - znaczniki TMP (<i>, <b>, <style>, <sprite>, <color>) usunięte, terminy <link=TERM_X> zastąpione słowem;
  - ikony glosariusza (obrażenia, zmęczenie, sukces, wzmocnienie, zdrowie) zamienione na rzeczowniki
    w formie zależnej od liczby i przypadka;
  - cyfry zamienione na słowa z odmianą: przypadek z przyimka, rodzaj z rzeczownika po liczbie;
  - wzorce gry: „na str. 29”, kafelki „10B”, liczniki „(2/4)”, zakresy „2-4”, „Tom 7”;
  - dopiski reżyserskie wielkimi literami („X WYBIERA…”) usunięte;
  - luki {n} zostają bez zmian (wypełnia je companion, D16).

Prototyp z E0: analysis/tools/normalize_pl.py (teraz importuje ten moduł).
"""
import re

# ---------- liczebniki ----------

UNITS = ['zero', 'jeden', 'dwa', 'trzy', 'cztery', 'pięć', 'sześć', 'siedem', 'osiem', 'dziewięć', 'dziesięć',
         'jedenaście', 'dwanaście', 'trzynaście', 'czternaście', 'piętnaście', 'szesnaście', 'siedemnaście',
         'osiemnaście', 'dziewiętnaście']
TENS = {2: 'dwadzieścia', 3: 'trzydzieści', 4: 'czterdzieści', 5: 'pięćdziesiąt', 6: 'sześćdziesiąt',
        7: 'siedemdziesiąt', 8: 'osiemdziesiąt', 9: 'dziewięćdziesiąt'}
HUNDREDS = {1: 'sto', 2: 'dwieście', 3: 'trzysta', 4: 'czterysta', 5: 'pięćset', 6: 'sześćset', 7: 'siedemset',
            8: 'osiemset', 9: 'dziewięćset'}
# Przypadki zależne (gen/dat/loc/ins) dla 5–19 i dziesiątek: „pięciu”, „dwudziestu”…
OBLIQUE = {5: 'pięciu', 6: 'sześciu', 7: 'siedmiu', 8: 'ośmiu', 9: 'dziewięciu', 10: 'dziesięciu', 11: 'jedenastu',
           12: 'dwunastu', 13: 'trzynastu', 14: 'czternastu', 15: 'piętnastu', 16: 'szesnastu', 17: 'siedemnastu',
           18: 'osiemnastu', 19: 'dziewiętnastu', 20: 'dwudziestu', 30: 'trzydziestu', 40: 'czterdziestu',
           50: 'pięćdziesięciu', 60: 'sześćdziesięciu', 70: 'siedemdziesięciu', 80: 'osiemdziesięciu',
           90: 'dziewięćdziesięciu'}
INS_5PLUS = {k: v[:-1] + 'oma' for k, v in OBLIQUE.items()}  # pięcioma, dwudziestoma

# Rodzaje: m (męskorzeczowy), ma (męskożywotny), mp (męskoosobowy), f, n, pt (plurale tantum).
ONE = {
    'nom': {'m': 'jeden', 'ma': 'jeden', 'mp': 'jeden', 'f': 'jedna', 'n': 'jedno', 'pt': 'jedne'},
    'acc': {'m': 'jeden', 'ma': 'jednego', 'mp': 'jednego', 'f': 'jedną', 'n': 'jedno', 'pt': 'jedne'},
    'gen': {'m': 'jednego', 'ma': 'jednego', 'mp': 'jednego', 'f': 'jednej', 'n': 'jednego', 'pt': 'jednych'},
    'dat': {'m': 'jednemu', 'ma': 'jednemu', 'mp': 'jednemu', 'f': 'jednej', 'n': 'jednemu', 'pt': 'jednym'},
    'loc': {'m': 'jednym', 'ma': 'jednym', 'mp': 'jednym', 'f': 'jednej', 'n': 'jednym', 'pt': 'jednych'},
    'ins': {'m': 'jednym', 'ma': 'jednym', 'mp': 'jednym', 'f': 'jedną', 'n': 'jednym', 'pt': 'jednymi'},
}
TWO_FOUR = {
    2: {'gen': 'dwóch', 'dat': 'dwóm', 'loc': 'dwóch', 'ins': 'dwoma', 'ins_f': 'dwiema'},
    3: {'gen': 'trzech', 'dat': 'trzem', 'loc': 'trzech', 'ins': 'trzema'},
    4: {'gen': 'czterech', 'dat': 'czterem', 'loc': 'czterech', 'ins': 'czterema'},
}


def _small(n, case, gender, last):
    """0–99. `last` = czy to ostatni człon liczebnika (w złożonych „jeden” się nie odmienia)."""
    if n == 1:
        return ONE[case][gender] if last else 'jeden'
    if n in (2, 3, 4):
        if case in ('nom', 'acc'):
            if gender == 'mp':
                return TWO_FOUR[n]['gen']
            return 'dwie' if (n == 2 and gender == 'f') else UNITS[n]
        if case == 'ins' and n == 2 and gender == 'f':
            return TWO_FOUR[2]['ins_f']
        return TWO_FOUR[n][case]
    if n < 20:
        if n == 0 or case in ('nom', 'acc') and gender != 'mp':
            return UNITS[n]
        return INS_5PLUS[n] if case == 'ins' else OBLIQUE[n]
    tens, unit = divmod(n, 10)
    if case in ('nom', 'acc') and gender != 'mp':
        head = TENS[tens]
    else:
        head = INS_5PLUS[tens * 10] if case == 'ins' else OBLIQUE[tens * 10]
    return head if unit == 0 else head + ' ' + _small(unit, case, gender, last)


def cardinal(n, case='nom', gender='m'):
    """Liczebnik główny 0–999 w przypadku i rodzaju (wystarcza dla tekstów gry)."""
    if n >= 1000:
        return ' '.join(UNITS[int(d)] for d in str(n))
    h, rest = divmod(n, 100)
    parts = []
    if h:
        parts.append(HUNDREDS[h])  # odmiana setek pominięta (w grze nie występuje)
    if rest or not h:
        parts.append(_small(rest, case, gender, True))
    return ' '.join(parts)


ORD_UNITS = ['', 'pierwsz', 'drug', 'trzec', 'czwart', 'piąt', 'szóst', 'siódm', 'ósm', 'dziewiąt', 'dziesiąt',
             'jedenast', 'dwunast', 'trzynast', 'czternast', 'piętnast', 'szesnast', 'siedemnast', 'osiemnast',
             'dziewiętnast']
ORD_TENS = {2: 'dwudziest', 3: 'trzydziest', 4: 'czterdziest', 5: 'pięćdziesiąt', 6: 'sześćdziesiąt',
            7: 'siedemdziesiąt', 8: 'osiemdziesiąt', 9: 'dziewięćdziesiąt'}


def _ord_word(stem, case, gender):
    soft = stem.endswith(('g', 'k', 'c'))  # drugi, trzeci
    i = 'i' if soft else 'y'
    endings = {
        ('nom', 'm'): i, ('nom', 'f'): 'a', ('nom', 'n'): 'ie' if soft else 'e',
        ('gen', 'f'): 'iej' if soft else 'ej', ('loc', 'f'): 'iej' if soft else 'ej',
        ('acc', 'f'): 'ą', ('gen', 'm'): 'iego' if soft else 'ego', ('loc', 'm'): 'im' if soft else 'ym',
    }
    return stem + endings.get((case, gender), i)


def ordinal(n, case='nom', gender='m'):
    if n < 20:
        return _ord_word(ORD_UNITS[n], case, gender)
    tens, unit = divmod(n, 10)
    head = _ord_word(ORD_TENS[tens], case, gender)
    return head if unit == 0 else head + ' ' + _ord_word(ORD_UNITS[unit], case, gender)


# ---------- rzeczowniki ----------

def _forms(sg_nom, sg_gen, pl_nom, pl_gen, gender, sg_acc=None, sg_loc=None, pl_loc=None, sg_ins=None, pl_dat=None):
    return {'gender': gender, 'sg': {'nom': sg_nom, 'gen': sg_gen, 'acc': sg_acc or sg_nom, 'loc': sg_loc or sg_nom,
                                      'ins': sg_ins or sg_nom, 'dat': sg_nom},
            'pl': {'nom': pl_nom, 'gen': pl_gen, 'acc': pl_nom, 'loc': pl_loc or pl_gen, 'ins': pl_nom,
                   'dat': pl_dat or pl_nom}}


# Ikony glosariusza: <link=TERM_X>(glif PUA)</link>.
ICONS = {
    'TERM_DAMAGE': _forms('obrażenie', 'obrażenia', 'obrażenia', 'obrażeń', 'n', sg_loc='obrażeniu',
                          pl_loc='obrażeniach', pl_dat='obrażeniom'),
    'TERM_FATIGUE': _forms('punkt zmęczenia', 'punktu zmęczenia', 'punkty zmęczenia', 'punktów zmęczenia', 'm',
                           sg_loc='punkcie zmęczenia', pl_loc='punktach zmęczenia', pl_dat='punktom zmęczenia'),
    'TERM_SUCCESS': _forms('sukces', 'sukcesu', 'sukcesy', 'sukcesów', 'm', sg_loc='sukcesie', pl_loc='sukcesach',
                           pl_dat='sukcesom'),
    'TERM_SURGE': _forms('wzmocnienie', 'wzmocnienia', 'wzmocnienia', 'wzmocnień', 'n', sg_loc='wzmocnieniu',
                         pl_loc='wzmocnieniach', pl_dat='wzmocnieniom'),
    'TERM_HEALTH_DIAL': _forms('punkt zdrowia', 'punktu zdrowia', 'punkty zdrowia', 'punktów zdrowia', 'm',
                               sg_loc='punkcie zdrowia', pl_loc='punktach zdrowia', pl_dat='punktom zdrowia'),
}
ICON_DEFAULT = {'TERM_DAMAGE': ('pl', 'nom'), 'TERM_SUCCESS': ('pl', 'nom'), 'TERM_SURGE': ('sg', 'acc'),
                'TERM_FATIGUE': ('pl', 'nom'), 'TERM_HEALTH_DIAL': ('pl', 'nom')}
ABBREV_TERMS = {'TERM_EXPERIENCE': _forms('punkt doświadczenia', 'punktu doświadczenia', 'punkty doświadczenia',
                                          'punktów doświadczenia', 'm')}

# Rodzaj rzeczowników po liczbach w tekstach M1 (forma z tekstu → rodzaj, przypadek domyślny formy).
NOUN_GENDER = {
    'kart': 'f', 'karc': 'f', 'akcj': 'f', 'skrzyni': 'f', 'kolumn': 'f', 'figurk': 'f', 'arkad': 'f', 'bram': 'f',
    'barykad': 'f', 'studni': 'f', 'kości': 'f', 'kością': 'f', 'rund': 'f', 'tur': 'f', 'ran': 'f',
    'pól': 'n', 'pola': 'n', 'pole': 'n', 'podłoż': 'n', 'drzew': 'n', 'obrażeń': 'n', 'obrażenia': 'n',
    'żeton': 'm', 'stół': 'm', 'regał': 'm', 'kocioł': 'm', 'pulpit': 'm', 'klucz': 'm', 'raz': 'm', 'stan': 'm',
    'punkt': 'm', 'kafel': 'm',
    'bohater': 'mp', 'wrog': 'mp', 'wróg': 'mp',
    'schod': 'pt', 'drzwi': 'pt',
}
CASE_BY_PREP = {'do': 'gen', 'od': 'gen', 'z': 'gen', 'ze': 'gen', 'bez': 'gen', 'dla': 'gen', 'około': 'gen',
                'o': 'acc', 'przez': 'acc', 'w': 'loc', 'we': 'loc', 'po': 'loc', 'przy': 'loc'}
LOC_ENDINGS = ('ie', 'ach', 'u', 'ej')
ADJ = re.compile(r'^\w+(?:e|y|i|a|ą|ych|ego|ej|ym|ymi)$')
LETTERS = {'A': 'a', 'B': 'be', 'C': 'ce', 'D': 'de'}
COLLECTIVE = {2: 'dwoje', 3: 'troje', 4: 'czworo', 5: 'pięcioro', 6: 'sześcioro'}


def noun_gender(word):
    w = word.lower()
    for stem in sorted(NOUN_GENDER, key=len, reverse=True):
        if w.startswith(stem):
            return NOUN_GENDER[stem]
    return None


def _case_for(prev_word, noun, n=None):
    p = (prev_word or '').lower()
    w = (noun or '').lower()
    case = CASE_BY_PREP.get(p)
    if p == 'po':
        return 'loc' if n == 1 else 'acc'  # „po jednym żetonie”, ale „po trzy żetony”
    if p in ('z', 'ze') and w.endswith(('ą', 'ami', 'em', 'om', 'iem')):
        return 'ins'  # „z jedną kartą”
    if case == 'loc' and noun and not w.endswith(LOC_ENDINGS):
        case = 'acc'  # „w 2 kafelki”
    if p == 'na':
        case = 'loc' if noun and w.endswith(LOC_ENDINGS) else 'acc'
    return case or 'acc'


def _icon_form(term, n, case):
    f = ICONS.get(term) or ABBREV_TERMS[term]
    if n is None:
        num, c = ICON_DEFAULT.get(term, ('pl', 'nom'))
        return f['pl'][case] if case else f[num][c]
    if n == 1:
        return f['sg'][case]
    if case in ('nom', 'acc') and n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f['pl']['nom']
    return f['pl']['gen'] if case in ('nom', 'acc') else f['pl'][case]


# ---------- normalizacja ----------

ICON_TOKEN = '\u0001%s\u0001'
LINK = re.compile(r'<link=(TERM_[A-Z_]+)>([^<]*)</link>')
TAG = re.compile(r'<[^>]+>')
PUA = re.compile('[-]')
CAPS_DIRECTION = re.compile(r'(?:^|(?<=[\s.…!?]))(?:[A-ZĄĆĘŁŃÓŚŹŻ]{2,}[\s,]+){1,4}[A-ZĄĆĘŁŃÓŚŹŻ]{2,}[.…!]*(?=\s|$)')
NUM = re.compile(r'(?<![\w/{])(\d+)(?![\w}]|\s*/)')
FOLLOW = re.compile(r'\s*(?:\x01(TERM_[A-Z_]+)\x01|([A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+))')
PREV = re.compile(r'([A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)\s*$')


def clean_markup(text):
    """Znaczniki gry → czysty tekst; ikony zostają jako tokeny do odmiany przy liczbach."""
    def link(m):
        term, inner = m.group(1), PUA.sub('', TAG.sub('', m.group(2))).strip()
        if term in ICONS or (term in ABBREV_TERMS and inner.isupper()):
            return ICON_TOKEN % term
        return inner
    text = text.replace('{BR}', '\n')
    text = LINK.sub(link, text)
    text = TAG.sub('', text)
    text = PUA.sub('', text)
    return text


def _case_from_ending(noun, gender, n):
    """Przypadek z końcówki rzeczownika, gdy przed liczbą nie ma przyimka."""
    w = noun.lower()
    if n == 1 and gender in ('m', 'ma', 'n') and w.endswith(('u', 'a')) and not w.endswith('ia'):
        return 'gen'  # „żetony 1 stanu”
    if gender == 'f' and w.endswith('ą') and n == 1:
        return 'ins'
    return 'acc'


def _num_phrase(text, m):
    """Zwraca (początek, koniec, zamiennik) dla liczby w m."""
    n = int(m.group(1))
    pm = PREV.search(text[max(0, m.start() - 30):m.start()])
    prev = pm.group(1) if pm else None
    j, words = m.end(), []
    for _ in range(3):
        fm = FOLLOW.match(text, j)
        if not fm:
            break
        words.append(fm)
        j = fm.end()
        if fm.group(1) or noun_gender(fm.group(2)) or not ADJ.match(fm.group(2)):
            break
    target = words[-1] if words else None
    if target is not None and target.group(1):
        term = target.group(1)
        case = _case_for(prev, None, n)
        gender = (ICONS.get(term) or ABBREV_TERMS[term])['gender']
        adj = text[m.end():target.start(1) - 1]
        return m.start(), target.end(), cardinal(n, case, gender) + adj + ' ' + _icon_form(term, n, case)
    noun = target.group(2) if target is not None else None
    gender = noun_gender(noun) if noun else None
    if gender is None:
        return m.start(), m.end(), cardinal(n)
    p = (prev or '').lower()
    case = _case_for(prev, noun, n) if (p in CASE_BY_PREP or p == 'na') else _case_from_ending(noun, gender, n)
    if gender == 'pt' and n >= 2 and case in ('nom', 'acc'):
        return m.start(), m.end(), COLLECTIVE.get(n, cardinal(n))  # „dwoje drzwi”
    return m.start(), m.end(), cardinal(n, case, gender)


def _numbers(text):
    text = re.sub(r'\bna str\.\s*(\d+)', lambda m: 'na stronie ' + ordinal(int(m.group(1)), 'loc', 'f'), text)
    text = re.sub(r'\bstr\.\s*(\d+)', lambda m: 'strona ' + cardinal(int(m.group(1))), text)
    text = re.sub(r'\b([Tt]om)\s+(\d+)', lambda m: m.group(1) + ' ' + ordinal(int(m.group(2))), text)
    text = re.sub(r'\b(\d+)([A-D])\b', lambda m: cardinal(int(m.group(1))) + ' ' + LETTERS[m.group(2)], text)
    text = re.sub(r'\((\d+|\{\d\})\s*/\s*(\d+)\)', lambda m: '(%s z %s)' % (
        cardinal(int(m.group(1))) if m.group(1).isdigit() else m.group(1), cardinal(int(m.group(2)), 'gen')), text)

    def rng(m):
        g = noun_gender(m.group(3)) or 'm'
        return 'od %s do %s %s' % (cardinal(int(m.group(1)), 'gen', g), cardinal(int(m.group(2)), 'gen', g), m.group(3))
    text = re.sub(r'\b(\d+)\s*[-–]\s*(\d+)\s+(\w+)', rng, text)
    out, pos = [], 0
    for m in NUM.finditer(text):
        if m.start() < pos:
            continue
        a, b, rep = _num_phrase(text, m)
        out.append(text[pos:a] + rep)
        pos = b
    return ''.join(out) + text[pos:]


def _icons(text):
    last_case = [None]

    def standalone(m):
        prev = m.group(1) or ''
        if prev.endswith('ych'):
            case = 'gen'
        elif prev.endswith('ym'):
            case = 'dat'
        elif prev in ('i', 'lub', 'albo', 'oraz'):
            case = last_case[0]
        else:
            case = None
        last_case[0] = case
        return (prev + ' ' if prev else '') + _icon_form(m.group(2), None, case)
    return re.sub(r'(?:(\w+)\s+)?\x01(TERM_[A-Z_]+)\x01', standalone, text)


def pronounce(text):
    """Zapis fonetyczny do syntezy (D70): okno gry dalej ma „Kehli”, model czyta „Keli”."""
    return re.sub(r'(?<!\w)KEHL', 'KEL', re.sub(r'(?<!\w)([Kk])ehl', r'\1el', text))


def normalize(text, drop_directions=True):
    text = clean_markup(text or '')
    if drop_directions:
        text = CAPS_DIRECTION.sub('', text)
    text = _numbers(text)
    text = _icons(text)
    text = re.sub(r'\s*\n+\s*', ' ', re.sub(r'([^.!?…:\s])[ \t]*\n', r'\1.\n', text))
    text = re.sub(r'\s+([,.!?…])', r'\1', text)
    return re.sub(r'\s+', ' ', text).strip()
