"""Kwestia z bazy E2 -> wypowiedź: fragmenty audio z pauzami, z lukami {n} wypełnionymi wartościami (D16).

Wartość luki rozpoznajemy po kluczu z argumentu pluginu (`as_key`, bez znacznika `<sprite=N>`; boss ma alias
w nawiasie). Gdy gra zwraca sam znacznik `<EntityName>`, porównujemy wyświetlaną nazwę z tekstami fragmentów
wartości tej luki (E1_HOOK.md). Wartość będąca kluczem innej kwestii (np. cel misji) odtwarza audio tej kwestii.
Brakującą wartość pomijamy i zapisujemy jako brak (D44).
"""
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
        self.frag_text = {r['id']: r['text'] for r in con.execute('SELECT id, text FROM fragments')}
        con.close()
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
            if line['tts'] and not any(s['kind'] == 'slot' for s in self.segments.get(key, [])):
                self.by_text.setdefault(squash(line['text_norm']), key)
        self._cache = OrderedDict()

    # ---------- rozwiązywanie ----------

    def resolve(self, key, args=(), text=None, depth=0):
        if key == CONFUSION[0] and text and '<EntityName>' in text:
            key = CONFUSION[1]
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
        shown = squash(N.normalize(N.clean_markup(SPRITE.sub('', arg.get('value') or ''))))
        for fid in table.values():
            if fid and shown and squash(self.frag_text.get(fid)) == shown:
                self._add(u, fid)
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
