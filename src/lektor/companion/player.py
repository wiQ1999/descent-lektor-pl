"""Odtwarzanie wypowiedzi: jeden dźwięk naraz, nowy podmienia bieżący (przerwanie, D03).

Player trzyma otwarty strumień sounddevice (D47), więc start i przerwanie czekają tylko na następny blok
(512 próbek przy 24 kHz to ok. 21 ms) i bufor urządzenia. Przerwanie przez nowy dźwięk wycisza stary w 10 ms, bez trzasku.
Zamknięcie okna bez nowego dźwięku wycisza głos łagodnie (D72), a dźwięk, który ruszy w trakcie, skraca wyciszanie do 10 ms.
Zdarzenia start, end i stopped mają czas szacowanego wyjścia z przetwornika (DAC), z którego liczymy opóźnienia.
NullPlayer robi to samo bez dźwięku (replay i testy): czas trwania wynika z długości audio.
"""
import collections
import threading
import time

FADE_S = 0.01
CLOSE_FADE_S = 0.35


class Mixer:
    """Bieżący dźwięk i wyciszany ogon poprzedniego. Bez urządzenia audio, żeby dało się to testować."""

    def __init__(self, sample_rate, events):
        import numpy as np
        self.np = np
        self.sample_rate = sample_rate
        self.events = events
        self.buf, self.pos, self.token = None, 0, None
        self.tail = None

    def _ramp(self, audio, seconds):
        n = min(int(seconds * self.sample_rate), len(audio))
        return audio[:n] * self.np.linspace(1.0, 0.0, n, dtype=self.np.float32)

    def apply(self, cmd, dac):
        audio, token, fade = cmd
        if self.buf is not None:
            self.tail = self._ramp(self.buf[self.pos:], fade)
            self.events.append((self.token, 'stopped', dac))
        elif token is not None and self.tail is not None:
            self.tail = self._ramp(self.tail, FADE_S)
        self.buf, self.pos, self.token = audio, 0, token
        if token is not None:
            self.events.append((token, 'start', dac))

    def render(self, out, dac):
        if self.tail is not None:
            n = min(len(out), len(self.tail))
            out[:n] += self.tail[:n]
            self.tail = self.tail[n:] if n < len(self.tail) else None
        if self.buf is None:
            return
        n = min(len(out), len(self.buf) - self.pos)
        out[:n] += self.buf[self.pos:self.pos + n]
        self.pos += n
        if self.pos >= len(self.buf):
            self.events.append((self.token, 'end', dac + n / self.sample_rate))
            self.buf, self.token = None, None


class Player:
    def __init__(self, sample_rate, device=None, blocksize=512):
        import sounddevice as sd
        self.sample_rate = sample_rate
        self.events = collections.deque()       # (token, 'start'|'end'|'stopped', czas perf_counter)
        self._lock = threading.Lock()
        self._cmd = None
        self._mix = Mixer(sample_rate, self.events)
        dev = int(device) if str(device).isdigit() else (device or None)
        self._stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32', blocksize=blocksize,
                                       latency='low', device=dev, callback=self._callback)
        self._stream.start()

    @property
    def output_latency(self):
        return self._stream.latency

    @property
    def busy(self):
        with self._lock:
            return self._mix.token is not None or (self._cmd is not None and self._cmd[1] is not None)

    def play(self, audio, token):
        with self._lock:
            self._cmd = (audio, token, FADE_S)

    def stop(self, fade=FADE_S):
        with self._lock:
            self._cmd = (None, None, fade)

    def poll(self):
        out = []
        while self.events:
            out.append(self.events.popleft())
        return out

    def close(self):
        self._stream.stop()
        self._stream.close()

    def _callback(self, out, frames, tinfo, status):
        dac = time.perf_counter() + max(0.0, tinfo.outputBufferDacTime - tinfo.currentTime)
        out.fill(0)
        with self._lock:
            cmd, self._cmd = self._cmd, None
            if cmd is not None:
                self._mix.apply(cmd, dac)
            self._mix.render(out[:, 0], dac)


class NullPlayer:
    """Bez dźwięku: start natychmiast, koniec po czasie trwania audio (zegar perf_counter)."""
    output_latency = 0.0

    def __init__(self, sample_rate, clock=time.perf_counter):
        self.sample_rate = sample_rate
        self.clock = clock
        self.events = collections.deque()
        self._token, self._end = None, None

    @property
    def busy(self):
        self._check()
        return self._token is not None

    def play(self, audio, token):
        now = self.clock()
        if self._token is not None:
            self.events.append((self._token, 'stopped', now))
        self._token, self._end = token, now + len(audio) / self.sample_rate
        self.events.append((token, 'start', now))

    def stop(self, fade=FADE_S):
        self._check()
        if self._token is not None:
            self.events.append((self._token, 'stopped', self.clock()))
        self._token = None

    def poll(self):
        self._check()
        out = []
        while self.events:
            out.append(self.events.popleft())
        return out

    def close(self):
        pass

    def _check(self):
        if self._token is not None and self.clock() >= self._end:
            self.events.append((self._token, 'end', self._end))
            self._token = None
