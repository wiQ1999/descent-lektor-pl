"""Budowa bazy M1: kopia gry → zakres → normalizacja i podział → fragmenty do syntezy → SQLite."""
import datetime
import json
import os
import re

from . import __version__, db, paths, scope
from . import direction as D
from . import game as G
from . import segment as S
from .normalize import normalize

PIECE_GAP = 0.06    # sklejanie kawałka szablonu z wartością luki (D16)
QUOTE_GAP = 0.15    # cytat bohatera → opis narratora (D20)
SPRITE = re.compile(r'<sprite[^>]*>')


def load_refs():
    p = os.path.join(paths.REFS, 'refs.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def choice_hero(key):
    """Bohater z klucza opcji (Q1_SYRUS_…), gdy opis nie podaje imienia."""
    parts = key.split('_')
    return next((v for h, v in scope.HEROES.items() if h in parts), None)


def line_parts(r):
    """Części kwestii: (rodzaj, głos, tekst albo dane luki)."""
    norm = r['text_norm']
    if r['category'] == 'opcja_wyboru':
        r['voice'] = 'narrator'  # opcja bez cytatu i opis cytatu: narrator (D20)
        choice = S.choice_parts(norm)
        if choice:
            quote, desc, hero = choice
            hero = hero or choice_hero(r['key'])
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


def build(path=paths.DB):
    game = G.Game()
    terms = game.terms()
    records, values, info = scope.collect(game, terms)
    lines = {r['key'] for r in records if r['tts']}
    refs = load_refs()
    fragments, segments, slot_values = {}, [], {}

    def frag(voice, text, speed, kind):
        tag = voice + ('@' + refs[voice]['sha'][:8] if voice in refs else '')
        fid = D.fragment_id(tag, text, speed)
        fragments.setdefault(fid, {'id': fid, 'voice': voice, 'speed': speed, 'text': text, 'kind': kind})
        return fid

    for r in records:
        r['toggle'] = D.toggle(r['category'], r['key'])
        if not r['tts']:
            continue
        r['text_norm'] = normalize(r['text_raw'])
        r['chars'] = len(r['text_norm'])
        r['speed'], r['pause'] = D.tempo(r['category'], r['chars'])
        # Wartości luk są krótkie i wspólne dla wielu kwestii: jedno tempo (D34 dla krótkiego fragmentu).
        value_speed = None if r['speed'] is None else D.SPEED_MIN
        parts = line_parts(r)
        for idx, (kind, voice, data) in enumerate(parts):
            nxt = parts[idx + 1][0] if idx + 1 < len(parts) else None
            gap = None if nxt is None else QUOTE_GAP if kind == 'quote' else \
                PIECE_GAP if 'slot' in (kind, nxt) else r['pause']
            seg = {'key': r['key'], 'idx': idx, 'kind': kind, 'voice': voice, 'pause_after': gap}
            if kind == 'slot':
                arg = (r['args'][max(data['arg'], 0):] or [{}])[0]
                seg.update(arg=data['arg'], arg_type=data['type'], text=data.get('tail'))
                texts = value_texts(data, arg, r['key'], values, terms, lines)
                if not texts:
                    r['note'] = 'luka bez znanych wartości (%s): fallback' % data['type']
                for value, text in texts.items():
                    slot_values[r['key'], data['arg'], value] = \
                        None if text is None else frag(voice, text, value_speed, 'value')
            elif re.search(r'\w', data):
                seg.update(text=data, fragment=frag(voice, data, r['speed'], kind))
            else:
                seg.update(text=data)   # sama interpunkcja: bez audio, companion robi tylko pauzę
            segments.append(seg)

    meta = {'version': __version__, 'model': D.MODEL, 'model_id': D.MODEL_ID, 'manifest': game.manifest_hash(),
            'built_at': datetime.datetime.now().isoformat(timespec='seconds'), 'scope': info,
            'tempo': {'scene_pause': D.SCENE_PAUSE, 'pause': D.PAUSE, 'speed': [D.SPEED_MIN, D.SPEED_MAX],
                      'chars': [D.SPEED_FROM, D.SPEED_TO]}}
    db.write(path, meta, records, segments, [(*k, f) for k, f in slot_values.items()], fragments, refs)
    return path
