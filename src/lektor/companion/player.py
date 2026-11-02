"""Odtwarzanie wypowiedzi: jeden dźwięk naraz, nowy podmienia bieżący (przerwanie, D03).

Player trzyma otwarty strumień sounddevice (D47), więc start i przerwanie czekają tylko na następny blok
(512 próbek przy 24 kHz to ok. 21 ms) i bufor urządzenia. Przerwanie wycisza stary dźwięk w 10 ms, bez trzasku.
Zdarzenia start, end i stopped mają czas szacowanego wyjścia z przetwornika (DAC), z którego liczymy opóźnienia.
NullPlayer robi to samo bez dźwięku (replay i testy): czas trwania wynika z długości audio.
"""
import collections
import threading
import time

FADE_S = 0.01


class Player:
    def __init__(self, sample_rate, device=None, blocksize=512):
        import numpy as np
        import sounddevice as sd
        self.sample_rate = sample_rate
        self.events = collections.deque()       # (token, 'start'|'end'|'stopped', czas perf_counter)
        self._lock = threading.Lock()
        self._cmd = None
        self._buf, self._pos, self._token = None, 0, None
        self._ramp = np.linspace(1.0, 0.0, int(FADE_S * sample_rate), dtype=np.float32)
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
            return self._token is not None or (self._cmd is not None and self._cmd[2] is not None)

    def play(self, audio, token):
        with self._lock:
            self._cmd = (audio, 0, token)

    def stop(self):
        with self._lock:
            self._cmd = (None, 0, None)

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
                if self._buf is not None:
                    old = self._buf[self._pos:self._pos + min(len(self._ramp), frames)]
                    out[:len(old), 0] += old * self._ramp[:len(old)]
                    self.events.append((self._token, 'stopped', dac))
                self._buf, self._pos, self._token = cmd
                if self._token is not None:
                    self.events.append((self._token, 'start', dac))
            if self._buf is None:
                return
            n = min(frames, len(self._buf) - self._pos)
            out[:n, 0] += self._buf[self._pos:self._pos + n]
            self._pos += n
            if self._pos >= len(self._buf):
                self.events.append((self._token, 'end', dac + n / self.sample_rate))
                self._buf, self._token = None, None


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

    def stop(self):
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
