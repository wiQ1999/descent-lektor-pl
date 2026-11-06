"""Kwestia z bazy E2 -> wypowiedź: fragmenty audio z pauzami, z lukami {n} wypełnionymi wartościami (D16).

Wartość luki rozpoznajemy po kluczu z argumentu pluginu (`as_key`, bez znacznika `<sprite=N>`; boss ma alias
w nawiasie). Gdy gra zwraca sam znacznik `<EntityName>`, porównujemy wyświetlaną nazwę z tekstami fragmentów
wartości tej luki (E1_HOOK.md). Wartość będąca kluczem innej kwestii (np. cel misji) odtwarza audio tej kwestii.
Brakującą wartość pomijamy i zapisujemy jako brak (D44).
"""
import difflib
import json
import os
import re
import sqlite3
from collections import OrderedDict
from dataclasses import dataclass, field

from .. import normalize as N

SPRITE = re.compile(r'<sprite=\d+>')
KEY = re.compile(r'\b[A-Z][A-Z0-9_]+\b')
LIST_GAP = 0.15         # między wartościami listy {n} (np. kilku wrogów)
LOOT = '@LOOT'          # slot_values: teksty listy łupu (D51)
LOOT_WORDS = 12         # najdłuższy kawałek łupu w słowach
LOOT_SKIP = {'i'}       # spójnik między pozycjami listy
REPEAT_RATIO = 0.85     # początek kwestii tak podobny do wybranej opcji to powtórka (D72)
REPEAT_SLACK = 4        # kwestia bywa o słowo dłuższa
REPEAT_MIN = 12         # krótszy tekst opcji może trafić w kwestię przypadkiem
GENERIC_CHOICES = {'kontynuuj'}     # guzik bez treści: bez odczytu (D64)
MAX_DEPTH = 2           # wartość luki, która jest kwestią z własnymi lukami
CACHE = 512             # fragmentów audio w pamięci
# Gra podmienia tę aktywację na wariant bez nazwy, gdy nazwa wroga nie rozwiązuje się (UIGame.ShowEnemyActivation).
CONFUSION = ('ENEMY_CONFUSION_ACTIVATION_02', 'ENEMY_CONFUSION_ACTIVATION_01')


@dataclass
class Utterance:
    key: str
    category: str = None
    toggle: str = None
    pieces: list = field(default_factory=list)      # [[fragment, pauza po (s)], ...]
    missing: list = field(default_factory=list)     # braki: 'klucz', 'audio', 'luka:<typ>'
    via: str = None                                 # 'key' | 'text' | None (brak w bazie)
    tts: bool = True                                # False: przerywnik z dubbingiem gry (D14), bez lektora
    nested: list = field(default_factory=list)      # klucze kwestii odczytanych jako wartość luki (np. cel misji)

    @property
    def complete(self):
        return self.via is not None and self.tts and bool(self.pieces) and not self.missing


def squash(text):
    return ' '.join(re.sub(r'[^\w]+', ' ', (text or '').lower()).split())


def value_keys(arg):
    """Kandydaci na wartość luki z argumentu pluginu, w kolejności prób."""
    raw = (arg.get('as_key') or '').strip()
    if arg.get('type') == 'VariableInt':
        return [str(arg.get('value') or raw).strip()]
    raw = SPRITE.sub('', raw).strip()
    return [] if raw.startswith('<') else KEY.findall(raw)


class Library:
    def __init__(self, db, audio_dir):
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        self.lines = {r['key']: dict(r) for r in con.execute('SELECT key, category, toggle, voice, tts, text_norm FROM lines')}
        self.segments = {}
        for r in con.execute('SELECT * FROM segments ORDER BY key, idx'):
            self.segments.setdefault(r['key'], []).append(dict(r))
        self.values = {}
        for r in con.execute('SELECT key, arg, value, fragment FROM slot_values'):
            self.values.setdefault((r['key'], r['arg']), {})[r['value']] = r['fragment']
        self.frag_text = {r['id']: N.pronounce(r['text']) for r in con.execute('SELECT id, text FROM fragments')}
        con.close()
        self.loot = self.values.get((LOOT, 0), {})
        self.generic = {k for k, v in self.lines.items() if v['category'] == 'opcja_wyboru' and squash(v['text_norm']) in GENERIC_CHOICES}
        with open(os.path.join(audio_dir, 'manifest.json'), encoding='utf-8') as fh:
            manifest = json.load(fh)
        self.audio_dir = audio_dir
        self.files = {fid: m['file'] for fid, m in manifest['fragments'].items()}
        self.sample_rate = manifest['sample_rate']
        self.gain_db = manifest.get('category_gain_db', {})
        self.model = manifest.get('model')
        # Zapas, gdy klucza okna nie ma w bazie: kwestie bez luk po znormalizowanym tekście.
        self.by_text = {}
        for key, line in self.lines.items():
            if line['tts'] and '#' not in key and not any(s['kind'] == 'slot' for s in self.segments.get(key, [])):
                self.by_text.setdefault(squash(line['text_norm']), key)
        self._cache = OrderedDict()

    # ---------- rozwiązywanie ----------

    def resolve(self, key, args=(), text=None, depth=0, hero=None):
        if key == CONFUSION[0] and text and '<EntityName>' in text:
            key = CONFUSION[1]
        if hero and '%s#%s' % (key, hero) in self.lines:    # VARIABLE_HERO: wersja w głosie bohatera (D17)
            key = '%s#%s' % (key, hero)
        line, via = self.lines.get(key), 'key'
        if line is None and text:
            found = self.by_text.get(squash(N.normalize(N.clean_markup(text))))
            if found:
                key, line, via = found, self.lines[found], 'text'
        if line is None:
            return Utterance(key, missing=['klucz'])
        u = Utterance(key, line['category'], line['toggle'], via=via, tts=bool(line['tts']))
        if u.tts:
            self._fill(u, key, list(args or []), depth)
        return u

    def repeats(self, option, key):
        """Kwestia zaczyna się tekstem wybranej opcji albo go zawiera (D72)."""
        opt, line = self.lines.get(option), self.lines.get(key)
        if not opt or not line:
            return False
        quote = next((s['text'] for s in self.segments.get(option, []) if s['kind'] == 'quote'), None)
        said, next_line = squash(quote or opt['text_norm']), squash(line['text_norm'])
        if not said or not next_line:
            return False
        head = difflib.SequenceMatcher(None, said, next_line[:len(said) + REPEAT_SLACK]).ratio()
        return head >= REPEAT_RATIO or (len(said) >= REPEAT_MIN and ' %s ' % said in ' %s ' % next_line)

    def counter(self, key, args):
        """Sam licznik celu (D64): luka liczbowa i tekst „z czterech” po niej. None, gdy cel nie ma licznika."""
        segs = self.segments.get(key, [])
        at = next((i for i, s in enumerate(segs) if s['kind'] == 'slot' and s['arg_type'] == 'VariableInt'), None)
        if at is None or segs[at]['arg'] >= len(args):
            return None
        line = self.lines[key]
        u = Utterance(key, line['category'], line['toggle'], via='key')
        self._value(u, key, segs[at], args[segs[at]['arg']] or {}, 0)
        if at + 1 < len(segs) and segs[at + 1]['fragment']:
            self._gap(u, segs[at]['pause_after'] or 0.0)
            self._add(u, segs[at + 1]['fragment'])
        return u

    def _loot(self, u, raw):
        """Lista łupu z tekstu gry (D51): najdłuższe znane kawałki po kolei, liczby z fragmentów liczebników."""
        words = squash(N.clean_markup(SPRITE.sub('', raw or ''))).split()
        i, unknown = 0, 0
        while i < len(words):
            for n in range(min(LOOT_WORDS, len(words) - i), 0, -1):
                fid = self.loot.get(' '.join(words[i:i + n]))
                if fid:
                    self._add(u, fid)
                    self._gap(u, LIST_GAP)
                    i += n
                    break
            else:
                unknown += words[i] not in LOOT_SKIP
                i += 1
        if unknown:
            u.missing.append('luka:RawText')

    def _fill(self, u, key, args, depth):
        for seg in self.segments.get(key, []):
            gap = seg['pause_after'] or 0.0
            if seg['kind'] != 'slot':
                if seg['fragment']:
                    self._add(u, seg['fragment'])
                elif seg['text'] and re.search(r'\w', seg['text']):
                    u.missing.append('audio')
                self._gap(u, gap)
                continue
            vals = args if seg['arg'] < 0 else args[seg['arg']:seg['arg'] + 1]
            if not vals:
                u.missing.append('luka:%s' % seg['arg_type'])
            for i, a in enumerate(vals):
                self._value(u, key, seg, a or {}, depth)
                self._gap(u, LIST_GAP if i < len(vals) - 1 else gap)

    def _value(self, u, key, seg, arg, depth):
        if self.loot and (seg['arg_type'] or arg.get('type')) == 'RawText':
            self._loot(u, arg.get('value'))
            return
        table = self.values.get((key, seg['arg']), {})
        for cand in value_keys(arg):
            if cand not in table:
                continue
            if table[cand]:
                self._add(u, table[cand])
            elif depth < MAX_DEPTH:      # wartość to kwestia z bazy: jej własne audio
                inner = self.resolve(cand, (), None, depth + 1)
                u.pieces += inner.pieces
                u.nested += [cand] + inner.nested
                u.missing += inner.missing if inner.via else ['luka:%s' % seg['arg_type']]
            return
        shown = squash(N.pronounce(N.normalize(N.clean_markup(SPRITE.sub('', arg.get('value') or '')))))
        if not shown and not arg.get('as_key'):
            return      # gra zostawiła lukę pustą (łup bez nagłówka)
        for value, fid in table.items():
            if fid and shown and squash(self.frag_text.get(fid)) == shown:
                self._add(u, fid)
                return
            line = self.lines.get(value) if not fid and shown else None
            if line and squash(line['text_norm']) == shown:     # gra podała tekst wartości będącej kwestią (nazwa celu)
                inner = self.resolve(value, (), None, depth + 1)
                u.pieces += inner.pieces
                u.missing += inner.missing
                return
        u.missing.append('luka:%s' % (seg['arg_type'] or arg.get('type')))

    def _add(self, u, fid):
        if fid in self.files:
            u.pieces.append([fid, 0.0])
        else:
            u.missing.append('audio')

    @staticmethod
    def _gap(u, gap):
        if u.pieces and gap:
            u.pieces[-1][1] = max(u.pieces[-1][1], gap)

    # ---------- audio ----------

    def warm(self):
        """Import soundfile i pierwszy odczyt przy starcie (zimny start to ok. 0,25 s), nie przy pierwszym oknie."""
        if self.files:
            self.audio(Utterance('', pieces=[[next(iter(self.files)), 0.0]]))

    def fragment(self, fid):
        import soundfile as sf
        if fid in self._cache:
            self._cache.move_to_end(fid)
            return self._cache[fid]
        y, _ = sf.read(os.path.join(self.audio_dir, self.files[fid]), dtype='float32')
        self._cache[fid] = y
        if len(self._cache) > CACHE:
            self._cache.popitem(last=False)
        return y

    def audio(self, u, volume=1.0):
        """Sklejone audio wypowiedzi (mono float32) ze wzmocnieniem kategorii (D04) i głośnością."""
        import numpy as np
        parts = []
        for i, (fid, gap) in enumerate(u.pieces):
            parts.append(self.fragment(fid))
            if gap and i < len(u.pieces) - 1:
                parts.append(np.zeros(int(gap * self.sample_rate), np.float32))
        if not parts:
            return np.zeros(0, np.float32)
        gain = volume * 10 ** (self.gain_db.get(u.category, 0.0) / 20)
        y = np.concatenate(parts) * gain
        return np.clip(y, -1.0, 1.0, out=y)
