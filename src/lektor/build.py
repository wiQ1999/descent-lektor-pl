"""Budowa bazy M1: kopia gry → zakres → normalizacja i podział → fragmenty do syntezy → SQLite."""
import datetime
import json
import os
import re

from . import __version__, abilities, db, paths, scope, speakers
from . import direction as D
from . import game as G
from . import segment as S
from .companion.library import FEATS, LOOT, squash
from .normalize import cardinal, clean_markup, normalize, ordinal, pronounce

PIECE_GAP = 0.06    # sklejanie kawałka szablonu z wartością luki (D16)
QUOTE_GAP = 0.15    # cytat bohatera → opis narratora (D20)
SPRITE = re.compile(r'<sprite[^>]*>')
PARAGRAPH = re.compile(r'\n\s*\n')
NARRATED = re.compile(r'[–—]\s*(?:\w+\s+){0,2}?(?:%s)\w*\b' % speakers.SPEECH_VERBS)     # wtrącenie „– mówi X”
SYSTEM_NOTICE = re.compile(r'^(\*.*\*|Do (waszych|twoich) zasobów\b.*|Zyskuje(cie|sz)\b.*|Zdobywa(cie|sz)\b.*)$', re.S | re.I)
CAPS_TOKEN = re.compile(r'[^\sa-ząćęłńóśźż<>=]*[A-ZĄĆĘŁŃÓŚŹŻ0-9}\x01][^\sa-ząćęłńóśźż<>=]*')
DIRECTION = re.compile(r'\bWYBIERA\b')
ROMAN_VALUES = {'II': 2, 'III': 3, 'IV': 4, 'VI': 6}
ROMAN = re.compile(r'\b(%s)\b' % '|'.join(sorted(ROMAN_VALUES, key=len, reverse=True)))
LOOT_NUMBERS = range(0, 100)
# Wstawka sceniczna (D86): krótki opis zachowania w nawiasie albo gwiazdkach, od małej litery, bez liczb i luk.
INSERT = re.compile(r'\(([^()]{1,120})\)|\*([^*\n]{1,120})\*')
INSERT_LOWER = re.compile(r'^[a-ząćęłńóśźż]')


def load_refs():
    p = os.path.join(paths.REFS, 'refs.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def voice_tag(voice, refs):
    """Głos w kluczu fragmentu: nazwa, SHA referencji i styl klonu (mnożnik tempa, instrukcja OmniVoice; D94)."""
    r = refs.get(voice)
    recast = '%' + D.ELEVEN_RECAST[voice][1] if voice in D.ELEVEN_RECAST else ''     # D109: nowy profil ElevenLabs
    if not r:
        return voice + recast
    style = r.get('style')
    return voice + '@' + r['sha'][:8] + ('~' + json.dumps(style, sort_keys=True) if style else '') + recast


def choice_hero(key):
    """Bohater z klucza opcji (Q1_SYRUS_…), gdy opis nie podaje imienia."""
    parts = key.split('_')
    return next((v for h, v in scope.HEROES.items() if h in parts), None)


def window_hero(r):
    """Bohater, który mówi w oknie opcji. Mówca NPC to rozmówca, cytat nie należy do niego (D70)."""
    return next((scope.HEROES[s] for s in r['speakers'] if s in scope.HEROES), None)


def system_tail(raw):
    """Komunikat gry doklejony po pustym wierszu do kwestii postaci (nagroda, przychylność): (mowa, komunikat) albo None."""
    paras = [p.strip() for p in PARAGRAPH.split(raw.strip()) if p.strip()]
    if len(paras) < 2:
        return None
    last = paras[-1]
    if SYSTEM_NOTICE.match(last) or (last.isupper() and len(last.split()) >= 3):
        return '\n\n'.join(paras[:-1]), last.strip('*').strip()
    return None


def insert_kind(inner, text, start):
    """'wstawka' albo 'inne' dla tekstu w nawiasie lub gwiazdkach zaczynającego się w `text` od `start`."""
    if re.search(r'\d|\{\d\}', inner) or len(inner.split()) > 8:
        return 'inne'
    return 'wstawka' if INSERT_LOWER.match(inner.strip()) and (sentence_start(text, start) or len(inner.split()) <= 3) \
        else 'inne'


def sentence_start(text, start):
    return not text[:start].strip() or bool(re.search(r'[.!?…:–-]\s*$', text[:start]))


def drop_inserts(text):
    """Kwestia postaci bez wstawek scenicznych na początku zdania (D95): w obu wariantach E15 postać ich nie czyta.
    Krótkie wtrącenie w środku zdania („golema (na wszelki wypadek), …”) to mowa postaci i zostaje."""
    def cut(m):
        inner = m.group(1) or m.group(2)
        return '' if insert_kind(inner, text, m.start()) == 'wstawka' and sentence_start(text, m.start()) else m.group(0)
    out = INSERT.sub(cut, text)
    if out == text:
        return text
    out = re.sub(r'[ \t]+([,.!?…:;])', r'\1', re.sub(r'[ \t]{2,}', ' ', out))
    return re.sub(r'^[ \t]*[,;:–-]?[ \t]*', '', out, flags=re.M).strip()


def caps_to_speech(text):
    """Tekst WIELKIMI literami (komunikat gry, okrzyk) → zwykła pisownia, żeby normalizacja go nie wycięła.

    Wskazówki „X WYBIERA…” zostają wielkimi literami i normalizacja dalej je pomija."""
    tokens = list(re.finditer(r'\S+', text))
    out, pos, i = [], 0, 0
    while i < len(tokens):
        j = i
        while j < len(tokens) and CAPS_TOKEN.fullmatch(tokens[j].group(0)):
            j += 1
        run = tokens[i:j]
        if sum(len(re.sub(r'\x01[^\x01]*\x01|[^A-ZĄĆĘŁŃÓŚŹŻ]', '', t.group(0))) >= 2 for t in run) >= 2:
            a, b = run[0].start(), run[-1].end()
            chunk = text[a:b]
            if not DIRECTION.search(chunk):
                chunk = ROMAN.sub(lambda m: ordinal(ROMAN_VALUES[m.group(0)]), chunk)     # AKT II → akt drugi
                chunk = re.sub(r'\x01[^\x01]*\x01|[^\x01]+', lambda m: m.group(0) if m.group(0)[0] == '\x01' else m.group(0).lower(), chunk)
                start = r'(^|[.!?…:]\s+)' if re.search(r'(^|[.!?…:])\s*$', text[:a]) else r'([.!?…]\s+)'
                chunk = re.sub(start + r'(\W*?)(\w)', lambda m: m.group(1) + m.group(2) + m.group(3).upper(), chunk)
            out.append(text[pos:a] + chunk)
            pos = b
        i = max(j, i + 1)
    return ''.join(out) + text[pos:]


def spoken(r, raw, voice=None):
    """Kopia kwestii do podziału na części: inny tekst i ewentualnie inny głos."""
    return {**r, 'text_raw': raw, 'text_norm': normalize(raw), 'voice': voice or r['voice']}


def line_parts(r, release='m1'):
    """Części kwestii: (rodzaj, głos, tekst albo dane luki).

    W m3 (uwagi z QA E14) komunikat gry doklejony do kwestii postaci czyta narrator, a tekst WIELKIMI literami
    czytamy zwykłą pisownią zamiast go wycinać. Postać nie czyta wstawek scenicznych (D95). M1 i M2 bez zmian."""
    if release in ('m1', 'm2'):
        return speech_parts(r, release)
    if r.get('split'):      # E16 (D101): okno narratora z wypowiedziami postaci, każdy kawałek swoim głosem
        return [p for voice, text in r['split'] for p in speech_parts(spoken(r, caps_to_speech(text), voice), release)]
    character = r['voice'] != 'narrator' and r['category'] != 'opcja_wyboru'
    tail = system_tail(r['text_raw']) if r['category'] == 'dialog' and r['voice'] != 'narrator' else None

    def say(text, voice=None):
        text = clean_markup(text)
        return spoken(r, caps_to_speech(drop_inserts(text) if character and voice is None else text), voice)
    copies = [say(t, v) for t, v in zip(tail, (None, 'narrator'))] if tail else [say(r['text_raw'])]
    parts = [p for c in copies for p in speech_parts(c, release)]
    if not tail:
        r['voice'] = copies[0]['voice']     # opcja wyboru: narrator (D20)
    for c in copies:
        if c.get('note'):
            r['note'] = c['note']
    return parts


def speech_parts(r, release='m1'):
    norm = r['text_norm']
    if r['category'] == 'opcja_wyboru':
        r['voice'] = 'narrator'  # opcja bez cytatu i opis cytatu: narrator (D20)
        choice = S.choice_parts(norm)
        if choice:
            quote, desc, hero = choice
            hero = hero or choice_hero(r['key']) or (window_hero(r) if release != 'm1' else None)
            if not hero:
                r['note'] = 'cytat bez rozpoznanego bohatera'
            parts = [('quote', hero or 'narrator', quote)]
            return parts + ([('desc', 'narrator', desc)] if desc else [])
    if S.SLOT.search(r['text_raw']):
        types = [a['type'] for a in r['args']]
        out = []
        for p in S.template_pieces(r['text_raw'], types):
            if p['kind'] == 'text':
                out += [('text', r['voice'], chunk) for chunk in S.split_long(p['text'])]
            else:
                out.append(('slot', r['voice'], p))
        return out
    return [('text', r['voice'], chunk) for chunk in S.split_long(norm)]


def value_texts(slot, arg, line_key, values, terms, lines):
    """{wartość: tekst albo None} dla luki. None: wartość to klucz kwestii z bazy, companion odtwarza jej audio."""
    if slot['type'] == 'VariableInt':
        return {str(v): S.number_value_text(v, slot['prev'], slot['noun']) for v in S.NUMBER_VALUES}
    out = {}
    for k in scope.slot_keys(slot['type'], arg, line_key, values):
        if k in lines:
            out[k] = None
        elif terms.get(k, {}).get('text'):
            text = normalize(SPRITE.sub('', terms[k]['text'])).strip()
            if text:
                out[k] = text
    return out


def loot_texts(game, terms, release='m2'):
    """{tekst z okna gry (squash): tekst do syntezy} dla listy łupu (D51). Szablony dzielimy na stałe kawałki."""
    out = {str(n): cardinal(n) for n in LOOT_NUMBERS}
    for k in scope.loot_keys(game, terms, scope.release_acts(release)):
        for piece in S.SLOT.split(clean_markup(SPRITE.sub('', terms[k]['text']))):
            if squash(piece) and not piece.isdigit():
                out.setdefault(squash(piece), normalize(piece).strip())
    return {k: v for k, v in out.items() if v}


def split_voices(records, release):
    """E16 (D101): okna narratora z zakresu testu dzielone na narrację i wypowiedzi postaci (speakers_t1.json).
    Wypowiedź bohatera z luki {N} ('arg:N') daje wersje KLUCZ#bohater; companion wybiera ją po argumencie N,
    a kwestia bazowa (bez znanego bohatera) czyta tę wypowiedź narratorem."""
    if not scope.t1_rules(release):
        return records
    overrides = speakers.load_overrides(release=release)
    out = []
    for r in records:
        out.append(r)
        if not (r['tts'] and r['category'] != 'opcja_wyboru' and '#' not in r['key'] and scope.t1_rules(release, r['group'])):
            continue
        # Kwestia postaci z wtrąceniem narratora („– mamrocze Kehli, …”) dzielona jak okno narratora (l15).
        if r['voice'] != 'narrator' and not (r['category'] == 'dialog' and NARRATED.search(clean_markup(r['text_raw']))):
            continue
        types = [a.get('type') for a in r['args']]
        parts = speakers.parts(r['key'], clean_markup(r['text_raw']), overrides, types)
        if not parts:
            continue
        hero_args = sorted({v for v, _ in parts if v.startswith('arg:')})
        r['split'] = [('narrator' if ':' in v else v, t) for v, t in parts]
        if hero_args:
            r['hero_variant'] = sorted(set(r['hero_variant']) | {'ARG:%s' % v.split(':')[1] for v in hero_args})
            for hero in scope.HEROES.values():
                out.append(dict(r, key='%s#%s' % (r['key'], hero),
                                split=[(hero if v.startswith('arg:') else 'narrator' if ':' in v else v, t) for v, t in parts]))
    return out


def piece_speed(r, voice, text, release):
    """Tempo kawałka. E16 (D101): narrator ma jedno tempo (SPEED_MAX) poza narracją scen, a wypowiedź postaci
    w oknie narratora dostaje tempo od długości samej wypowiedzi."""
    if r['speed'] is None or release not in D.ONE_TEMPO or not scope.t1_rules(release, r['group']):
        return r['speed']
    if voice == 'narrator':
        return D.SPEED_MAX
    if r.get('split'):
        return D.tempo(r['category'], len(text))[0]
    return r['speed']


def build(path=None, release='m1', only=None):
    path = path or paths.DB
    base = paths.base(release)
    game = G.Game()
    terms = game.terms(game_order=base == 'm3')
    records, values, info = scope.collect(game, terms, base, only)
    if scope.t1_rules(release):      # E16 (D101): okno zdolności w oknie ataku
        records += abilities.records(game, terms, {r['key'] for r in records})
    records = split_voices(records, release)
    lines = {r['key'] for r in records if r['tts']}
    refs = load_refs()
    fragments, segments, slot_values, entities = {}, [], {}, {}

    def frag(voice, text, speed, kind):
        text = text if release == 'm1' else pronounce(text)
        fid = D.fragment_id(voice_tag(voice, refs), text, speed)
        fragments.setdefault(fid, {'id': fid, 'voice': voice, 'speed': speed, 'text': text, 'kind': kind})
        return fid

    for r in records:
        r['toggle'] = r.get('toggle') or D.toggle(r['category'], r['key'].split('#')[0], r['group'])
        if not r['tts']:
            continue
        r['text_norm'] = normalize(r['text_raw'])
        r['chars'] = len(r['text_norm'])
        r['speed'], r['pause'] = D.tempo(r['category'], r['chars'])
        # Wartości luk są krótkie i wspólne dla wielu kwestii: jedno tempo (D34 dla krótkiego fragmentu).
        value_speed = None if r['speed'] is None else D.SPEED_MIN
        parts = line_parts(r, base)
        for idx, (kind, voice, data) in enumerate(parts):
            nxt = parts[idx + 1][0] if idx + 1 < len(parts) else None
            gap = None if nxt is None else QUOTE_GAP if kind == 'quote' else \
                PIECE_GAP if 'slot' in (kind, nxt) else r['pause']
            seg = {'key': r['key'], 'idx': idx, 'kind': kind, 'voice': voice, 'pause_after': gap}
            if kind == 'slot':
                arg = (r['args'][max(data['arg'], 0):] or [{}])[0]
                seg.update(arg=data['arg'], arg_type=data['type'], text=data.get('tail'))
                texts = value_texts(data, arg, r['key'], values, terms, lines)
                if not texts and data['type'] != 'RawText':
                    r['note'] = 'luka bez znanych wartości (%s): fallback' % data['type']
                for value, text in texts.items():
                    speed = piece_speed(r, voice, text, release) if voice == 'narrator' else value_speed
                    fid = None if text is None else frag(voice, text, speed, 'value')
                    slot_values[r['key'], data['arg'], value] = fid
                    if fid and data['type'] == 'EntityName' and voice == 'narrator':
                        entities[squash(text)] = fid
            elif re.search(r'\w', data):
                seg.update(text=data, fragment=frag(voice, data, piece_speed(r, voice, data, release), kind))
            else:
                seg.update(text=data)   # sama interpunkcja: bez audio, companion robi tylko pauzę
            segments.append(seg)

    if release != 'm1':
        loot_speed = D.SPEED_MAX if release in D.ONE_TEMPO else D.SPEED_MIN
        for value, text in loot_texts(game, terms, base).items():
            slot_values[LOOT, 0, value] = frag('narrator', text, loot_speed, 'value')
        for name, fid in entities.items():      # lista łupu kończy się poleceniem usunięcia wroga (REMOVE_ENTITY)
            slot_values.setdefault((LOOT, 0, name), fid)
    if base == 'm3':        # zapowiedź ukończonego wyzwania (l16): imię bohatera i nazwa wyzwania
        names = {**scope.feat_names(game, terms), **{k: terms[k]['text'] for k in scope.HERO_NAME_KEYS if k in terms}}
        for key, name in names.items():
            text = normalize(clean_markup(name)).strip()
            # poziom wyzwania „Straż przednia II” → „dwa”: OmniVoice gubi albo przekręca rzymskie liczby
            text = ROMAN.sub(lambda m: cardinal(ROMAN_VALUES[m.group(0)]), text)
            if text:
                slot_values[FEATS, 0, key] = frag('narrator', text, loot_speed, 'value')

    meta = {'version': __version__, 'release': release, 'model': D.MODEL, 'model_id': D.MODEL_ID, 'manifest': game.manifest_hash(),
            'built_at': datetime.datetime.now().isoformat(timespec='seconds'), 'scope': info,
            'tempo': {'scene_pause': D.SCENE_PAUSE, 'pause': D.PAUSE, 'speed': [D.SPEED_MIN, D.SPEED_MAX],
                      'chars': [D.SPEED_FROM, D.SPEED_TO]}}
    db.write(path, meta, records, segments, [(*k, f) for k, f in slot_values.items()], fragments, refs)
    return path
