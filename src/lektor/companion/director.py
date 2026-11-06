"""Zasady odtwarzania zdarzeń pluginu (E4).

  okno wiadomości (open) i fabularne (shown)  przerywa bieżące audio i gra od razu (D03, D45)
  zamknięcie grającego okna                   zatrzymuje jego audio; wybrana opcja (choice_key, bez back) gra
                                              odpowiedź bohatera (D20), a okno otwarte w jej trakcie czeka (D48);
                                              guzik ogólny („Kontynuuj”) nie gra (D64), a odpowiedź, którą powtarza
                                              następna kwestia, milknie i tekst czyta okno (D72)
  cel misji, aktywacja wroga, opis misji      czekają w kolejce na ciszę (D45); nowszy cel zastępuje starszy,
                                              zamknięta aktywacja wypada z kolejki, a cel odczytany już w oknie
                                              (wartość luki) nie gra drugi raz; ten sam cel ze zmienionym
                                              licznikiem gra sam licznik (D64); nowszy opis zastępuje starszy
  scena, stop                                 zatrzymują wszystko
  przełącznik kategorii wyłączony (D21)       okno nie gra, ale zatrzymuje audio poprzedniego okna

Każde zdarzenie dostaje czas odbioru (`recv`, perf_counter). Opóźnienie startu to czas od odbioru do wyjścia
pierwszej próbki z przetwornika, opóźnienie przerwania to czas od odbioru zdarzenia do wyciszenia.
"""
import collections
import dataclasses
import itertools
import re
import time

from .player import CLOSE_FADE_S, FADE_S

WINDOWS = ('message', 'story')
QUEUED = ('objective', 'activation', 'details')
SETTLE = 0.35           # cisza po zdarzeniu okna, zanim ruszy kolejka: zamknięcie i nowe okno przychodzą razem
DUP_S = 30.0            # cel odczytany w oknie w tym czasie nie gra ponownie
DETAILS_GAP = 0.35      # między nazwą a opisem celu na mapie
HERO_KEY = re.compile(r'^HERO_([A-Z]+)_NAME$')


@dataclasses.dataclass
class Item:
    token: int
    src: str            # message | story | choice | objective | activation | details
    wid: int            # id okna z pluginu (cel: None)
    key: str
    u: object           # library.Utterance
    recv: float
    requeued: bool = False


def speaking_hero(ev):
    """Głos bohatera mówiącego w oknie fabularnym: pole name_key mówiącej postaci (HERO_BRYNN_NAME → brynn)."""
    for c in ev.get('characters') or []:
        m = HERO_KEY.match(c.get('name_key') or '')
        if m and c.get('speaking'):
            return m.group(1).lower()
    return None


class Director:
    def __init__(self, library, player, toggles=None, volume=1.0, log=None, clock=time.perf_counter):
        self.lib, self.player = library, player
        self.toggles = toggles or {}
        self.volume = volume
        self.log = log or (lambda rec: None)
        self.clock = clock
        self.current = None
        self.pending = None                     # okno czekające na koniec odpowiedzi z wyboru (D48)
        self.queue = collections.deque()
        self.story_open = {}                    # id -> zdarzenie open (gramy po shown)
        self.nested = {}                        # klucz odczytany jako wartość luki -> czas
        self.last_window = -1e9
        self.items = {}                         # token -> Item
        self.trigger = {}                       # token -> (czas zdarzenia, start od razu)
        self.stop_req = {}                      # token -> czas zdarzenia, które przerwało
        self.started = {}
        self.outcomes = collections.Counter()   # (źródło, wynik)
        self.missing = collections.Counter()    # (źródło, klucz, braki)
        self.latency = {'start': [], 'stop': [], 'wait': []}
        self.cut = 0                            # okna przerwane przed końcem audio
        self._tokens = itertools.count(1)

    # ---------- zdarzenia ----------

    def handle(self, ev, recv=None):
        recv = self.clock() if recv is None else recv
        name, kind = ev.get('ev'), ev.get('kind')
        if name == 'open' and kind == 'message':
            self._window('message', ev, recv)
        elif name == 'open' and kind == 'story':
            self.story_open[ev.get('id')] = ev
            self._drop_repeated_answer(ev.get('key'), recv)
        elif name == 'shown' and kind == 'story':
            op = self.story_open.pop(ev.get('id'), None)
            if op is not None:
                self._window('story', {**op, 'text': ev.get('text') or op.get('text'), 'characters': ev.get('characters')}, recv)
        elif name == 'close' and kind in WINDOWS:
            self._close(kind, ev, recv)
        elif name == 'open' and kind == 'activation':
            self._enqueue('activation', ev, recv)
        elif name == 'close' and kind == 'activation':
            self._withdraw(lambda it: it.src == 'activation' and it.wid == ev.get('id'), recv)
        elif name == 'objective':
            self._enqueue('objective', ev, recv)
        elif name == 'details':
            self._details(ev, recv)
        elif name == 'close' and kind == 'details':
            self._withdraw(lambda it: it.src == 'details', recv)
        elif name in ('scene', 'stop'):
            self.story_open.clear()
            self.queue.clear()
            self.pending = None
            self._stop(recv)

    def tick(self, now=None):
        now = self.clock() if now is None else now
        for token, what, t in self.player.poll():
            self._player_event(token, what, t)
        if self.current is not None:
            return
        if self.pending is not None:
            item, self.pending = self.pending, None
            self._start(item, now, immediate=False)
        elif self.queue and now - self.last_window >= SETTLE:
            self._start(self.queue.popleft(), now, immediate=False)

    @property
    def idle(self):
        return self.current is None and self.pending is None and not self.queue

    # ---------- zasady ----------

    def _utterance(self, src, ev, key):
        args = ev.get('args') or []
        if src == 'objective' and ev.get('prev_key') == key and key in self.lib.lines:
            u = self.lib.counter(key, args)     # ten sam cel, zmieniony licznik (D64)
            if u is not None:
                return u
        return self.lib.resolve(key, args, ev.get('text'), hero=speaking_hero(ev))

    def _make(self, src, ev, recv, key=None):
        key = key or ev.get('key')
        u = self._utterance(src, ev, key)
        item = Item(next(self._tokens), src, ev.get('id'), key, u, recv)
        if not u.tts:
            outcome = 'bez_lektora'
        elif u.via is None:
            outcome = 'brak_klucza'
        elif not self.toggles.get(u.toggle, True):
            outcome = 'wyłączone'
        elif not u.pieces:
            outcome = 'brak_audio'
        elif src == 'objective' and recv - self.nested.get(u.key, -1e9) < DUP_S:
            outcome = 'w_oknie'
        else:
            outcome = 'pełne' if not u.missing else 'częściowe'
        self.outcomes[src, outcome] += 1
        if u.missing:
            self.missing[src, key, tuple(sorted(set(u.missing)))] += 1
        self.log({'ev': 'item', 'token': item.token, 'src': src, 'id': item.wid, 'key': key, 'resolved': u.key,
                  'via': u.via, 'toggle': u.toggle, 'outcome': outcome, 'pieces': len(u.pieces),
                  'missing': sorted(set(u.missing))})
        return item if outcome in ('pełne', 'częściowe') else None

    def _drop_repeated_answer(self, key, recv):
        """Okno otwiera się tuż po wyborze, więc odpowiedź ledwo zaczęła grać: nikt nie usłyszy jej dwa razy (D72)."""
        if self.current is not None and self.current.src == 'choice' and self.lib.repeats(self.current.key, key):
            self.log({'ev': 'repeat', 'token': self.current.token, 'key': self.current.key, 'window': key})
            self._stop(recv, FADE_S)

    def _window(self, src, ev, recv):
        self.last_window = recv
        self._drop_repeated_answer(ev.get('key'), recv)
        item = self._make(src, ev, recv)
        if item is None:
            if self.current is not None and self.current.src in WINDOWS:
                self._stop(recv)
            return
        if self.current is not None and self.current.src == 'choice':
            self.pending = item
            return
        self._start(item, recv)

    def _close(self, kind, ev, recv):
        wid = ev.get('id')
        self.last_window = recv
        self.story_open.pop(wid, None)
        if self.pending is not None and self.pending.wid == wid:
            self.pending = None
        if self.current is not None and self.current.src == kind and self.current.wid == wid:
            self._stop(recv)
        if ev.get('choice_key') and not ev.get('back') and ev['choice_key'] not in self.lib.generic:
            item = self._make('choice', {'id': wid}, recv, key=ev['choice_key'])
            if item is not None:
                self._start(item, recv)

    def _enqueue(self, src, ev, recv):
        if not ev.get('key'):
            return
        item = self._make(src, ev, recv)
        if item is None:
            return
        if src == 'objective':
            self.queue = collections.deque(it for it in self.queue if it.src != 'objective')
            if self.current is not None and self.current.src == 'objective':
                self._start(item, recv)
                return
        self.queue.append(item)

    def _details(self, ev, recv):
        """Opis celu na mapie (D55 pkt 5): nazwa i opis jako jedna wypowiedź, nowszy zastępuje starszy."""
        self._withdraw(lambda it: it.src == 'details', recv)
        keys = [k for k in (ev.get('name_key'), ev.get('key')) if k]
        if not keys:
            return
        item = self._make('details', {'key': keys[-1]}, recv)
        if item is None:
            return
        if len(keys) > 1:
            head = self.lib.resolve(keys[0])
            if head.pieces:
                head.pieces[-1][1] = max(head.pieces[-1][1], DETAILS_GAP)
                item.u.pieces[:0] = head.pieces
        self.queue.append(item)

    def _withdraw(self, match, recv):
        self.queue = collections.deque(it for it in self.queue if not match(it))
        if self.current is not None and match(self.current):
            self._stop(recv)

    def _start(self, item, trigger, immediate=True):
        cur = self.current
        if cur is not None:
            self.stop_req[cur.token] = trigger
            if cur.src in QUEUED and not cur.requeued:
                self.queue.appendleft(dataclasses.replace(cur, token=next(self._tokens), requeued=True))
        t0 = self.clock()
        audio = self.lib.audio(item.u, self.volume)
        self.player.play(audio, item.token)
        self.current = item
        self.items[item.token] = item
        self.trigger[item.token] = (trigger, immediate)
        for key in item.u.nested:
            self.nested[key] = item.recv
        self.log({'ev': 'play', 'token': item.token, 'src': item.src, 'key': item.key, 'seconds': round(len(audio) / self.lib.sample_rate, 2),
                  'prep_ms': round((self.clock() - t0) * 1000, 1), 'immediate': immediate})

    def _stop(self, recv, fade=CLOSE_FADE_S):
        if self.current is None:
            return
        self.stop_req[self.current.token] = recv
        self.player.stop(fade)
        self.current = None

    def _player_event(self, token, what, t):
        item = self.items.get(token)
        if item is None:
            return
        if what == 'start':
            trigger, immediate = self.trigger[token]
            self.started[token] = t
            lat = t - trigger
            self.latency['start' if immediate else 'wait'].append(lat)
            self.log({'ev': 'start', 'token': token, 'src': item.src, 'key': item.key, 'start_s': round(lat, 3), 'immediate': immediate})
        elif what == 'stopped':
            lat = t - self.stop_req.get(token, t)
            self.latency['stop'].append(lat)
            if item.src in WINDOWS:
                self.cut += 1
            self.log({'ev': 'stopped', 'token': token, 'src': item.src, 'key': item.key, 'stop_s': round(lat, 3),
                      'played_s': round(t - self.started.get(token, t), 2)})
        elif what == 'end':
            if self.current is not None and self.current.token == token:
                self.current = None
            self.log({'ev': 'end', 'token': token, 'src': item.src, 'key': item.key, 'played_s': round(t - self.started.get(token, t), 2)})

    # ---------- podsumowanie ----------

    def summary(self):
        def stats(xs):
            if not xs:
                return None
            xs = sorted(xs)
            pick = lambda q: round(xs[min(len(xs) - 1, int(q * len(xs)))], 3)
            return {'n': len(xs), 'p50': pick(0.5), 'p95': pick(0.95), 'max': round(xs[-1], 3)}
        windows = collections.Counter()
        for (src, outcome), n in self.outcomes.items():
            if src in WINDOWS:
                windows[outcome] += n
        total = sum(windows.values()) - windows['bez_lektora']      # przerywniki z dubbingiem gry (D14)
        audio = windows['pełne'] + windows['częściowe']
        # brak_audio: kwestia z samych luk znanych dopiero w grze (łup), pominięta według D44
        readable = total - windows['brak_audio']
        return {
            'windows': total,
            'windows_audio': audio,
            'windows_full': windows['pełne'],
            'windows_runtime_only': windows['brak_audio'],
            'coverage': round(audio / total, 4) if total else None,
            'coverage_readable': round(audio / readable, 4) if readable else None,
            'outcomes': {'%s/%s' % k: v for k, v in sorted(self.outcomes.items())},
            'missing': [{'src': s, 'key': k, 'missing': list(m), 'n': n} for (s, k, m), n in self.missing.most_common()],
            'cut_windows': self.cut,
            'latency': {k: stats(v) for k, v in self.latency.items()},
        }
