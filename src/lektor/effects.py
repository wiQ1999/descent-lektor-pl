"""Efekty na audio głosu (E20, D114): łańcuch per głos, wypalany w pliku końcowym przez finalize.

Tylko numpy, scipy i librosa z .venv; paczka gracza ich nie potrzebuje, bo dostaje gotowe pliki. Efekt działa
na przyciętym podejściu przed wyrównaniem głośności. Każdy wariant jest deterministyczny (stałe ziarno szumu
pogłosu), więc ten sam fragment daje zawsze ten sam plik.

Warianty:
    ghost_a  duch eteryczny: chorus, pogłos 1,8 s, lekko przycięty dół
    ghost_b  duch z zaświatów: ghost_a + warstwa o 5 półtonów niżej i dłuższy, ciemniejszy pogłos
    ghost_c  widmo: pogłos odwrócony (narastanie przed słowem) i chorus, sucha mowa ciszej
    mind_a   głos w głowie: blisko i sucho, podwojenie z odstrojeniem, krótkie wczesne odbicia, pasmo zawężone
    mind_b   demon w głowie: warstwa oktawę niżej i szept z tej samej mowy, krótkie odbicia
    mind_c   telepatia: lekka modulacja kołowa, flanger i echo 140 ms
Runda 2 (2026-11-21): ghost_b2/b3 i ghost_c2/c3 to ghost_b i ghost_c słabiej (2 mocniej, 3 najsłabiej), z ogonem
najwyżej 0,35 s po mowie wyciszanym na końcu; mind_d–mind_g to nowe propozycje głosu w głowie (opisy przy funkcjach).
Runda 11 (2026-11-24): serpent_a/serpent_b to wężowa wymowa: wydłużone i głośniejsze głoski syczące.
"""
import numpy as np

SEED = 20114


def _sos(kind, freq, sr, order=2):
    from scipy.signal import butter
    return butter(order, freq, btype=kind, fs=sr, output='sos')


def _filt(y, kind, freq, sr, order=2):
    from scipy.signal import sosfilt
    return sosfilt(_sos(kind, freq, sr, order), y).astype(np.float32)


def _ir(sr, seconds, pre_delay=0.02, damp=4000.0, seed=SEED):
    """Pogłos syntetyczny: szum z wykładniczym zanikiem (−60 dB po `seconds`), przyciemniany z czasem."""
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    t = np.arange(n) / sr
    noise = rng.standard_normal(n).astype(np.float32) * np.exp(-6.9 * t / seconds).astype(np.float32)
    half = n // 2       # druga połowa ogona ciemniejsza: wysokie tony gasną szybciej
    noise[half:] = _filt(noise[half:], 'lowpass', damp / 2, sr)
    noise = _filt(noise, 'lowpass', damp, sr)
    ir = np.concatenate([np.zeros(int(pre_delay * sr), np.float32), noise])
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)


def _conv(y, ir):
    from scipy.signal import fftconvolve
    return fftconvolve(y, ir)[:len(y) + len(ir) - 1].astype(np.float32)


def _mod_delay(y, sr, base_ms, depth_ms, rate_hz, phase=0.0):
    """Opóźnienie modulowane sinusem (chorus/flanger), interpolacja liniowa."""
    n = np.arange(len(y))
    d = (base_ms + depth_ms * np.sin(2 * np.pi * rate_hz * n / sr + phase)) * sr / 1000.0
    idx = n - d
    i0 = np.clip(np.floor(idx).astype(int), 0, len(y) - 1)
    i1 = np.clip(i0 + 1, 0, len(y) - 1)
    frac = (idx - np.floor(idx)).astype(np.float32)
    out = y[i0] * (1 - frac) + y[i1] * frac
    out[idx < 0] = 0.0
    return out.astype(np.float32)


def _chorus(y, sr, mix=0.35):
    a = _mod_delay(y, sr, 18, 4, 0.31)
    b = _mod_delay(y, sr, 24, 5, 0.23, phase=1.7)
    return (1 - mix) * y + mix * 0.5 * (a + b)


def _shift(y, sr, steps):
    import librosa
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=steps).astype(np.float32)


def _whisper(y, sr):
    """Szept z tej samej mowy: amplituda widma bez wysokości (losowa faza)."""
    import librosa
    rng = np.random.default_rng(SEED)
    S = librosa.stft(y, n_fft=1024, hop_length=256)
    ph = np.exp(2j * np.pi * rng.random(S.shape))
    w = librosa.istft(np.abs(S) * ph, hop_length=256, length=len(y)).astype(np.float32)
    return _filt(w, 'highpass', 1200, sr)


def _pad(y, sr, tail):
    return np.concatenate([y, np.zeros(int(tail * sr), np.float32)])


def _mix(dry, wet):
    n = max(len(dry), len(wet))
    out = np.zeros(n, np.float32)
    out[:len(dry)] += dry
    out[:len(wet)] += wet
    return out


def _rms(y):
    return float(np.sqrt(np.mean(y ** 2)) + 1e-9)


def _wet(dry, wet, ratio):
    """Mokry sygnał o głośności `ratio` względem suchego (RMS)."""
    return wet * (ratio * _rms(dry) / _rms(wet))


def ghost_a(y, sr):
    y = _filt(y, 'highpass', 140, sr)
    c = _chorus(y, sr, 0.35)
    rev = _conv(c, _ir(sr, 1.8, 0.03, 5000))
    return _mix(c, _wet(c, rev, 0.55))


def ghost_b(y, sr):
    y = _filt(y, 'highpass', 120, sr)
    low = _shift(y, sr, -5)
    c = _chorus(y + 0.45 * low, sr, 0.4)
    c = _filt(c, 'lowpass', 6000, sr)
    rev = _conv(c, _ir(sr, 2.8, 0.04, 3500))
    return _mix(c, _wet(c, rev, 0.75))


def ghost_c(y, sr):
    y = _filt(y, 'highpass', 150, sr)
    ir = _ir(sr, 1.2, 0.0, 5000)
    pre = len(ir) - 1
    swell = _conv(_pad(y, sr, 0)[::-1], ir)[::-1]     # odwrócony pogłos: zaczyna się przed słowem
    dry = np.concatenate([np.zeros(pre, np.float32), _chorus(y, sr, 0.3)])
    rev = _conv(dry, _ir(sr, 1.4, 0.02, 4500))
    out = _mix(0.8 * dry, _wet(dry, swell, 0.6))
    return _mix(out, _wet(dry, rev, 0.35))


def mind_a(y, sr):
    y = _filt(_filt(y, 'highpass', 180, sr), 'lowpass', 7000, sr)
    up = _mod_delay(_shift(y, sr, 0.18), sr, 22, 1, 0.5)
    down = _mod_delay(_shift(y, sr, -0.18), sr, 31, 1, 0.4, phase=1.0)
    d = y + 0.45 * (up + down)
    early = _conv(d, _ir(sr, 0.18, 0.004, 6000))
    return _mix(d, _wet(d, early, 0.3))


def mind_b(y, sr):
    y = _filt(y, 'highpass', 100, sr)
    low = _shift(y, sr, -12)
    wh = _whisper(y, sr)
    d = y + _wet(y, low, 0.6) + _wet(y, wh, 0.35)
    early = _conv(d, _ir(sr, 0.25, 0.006, 5000))
    return _mix(d, _wet(d, early, 0.3))


def mind_c(y, sr):
    y = _filt(_filt(y, 'highpass', 220, sr), 'lowpass', 5000, sr)
    n = np.arange(len(y))
    ring = y * np.sin(2 * np.pi * 38 * n / sr).astype(np.float32)
    d = 0.8 * y + 0.25 * ring
    d = 0.6 * d + 0.4 * _mod_delay(d, sr, 3, 2, 0.25)
    echo_n = int(0.14 * sr)
    out = _pad(d, sr, 0.6)
    for k in (1, 2, 3):
        out[k * echo_n:k * echo_n + len(d)] += d * (0.32 ** k)
    return out


def _tail(out, n_dry, sr, keep=0.35, fade=0.25):
    """Ogon efektu po końcu mowy najwyżej `keep` s, ostatnie `fade` s wyciszane cosinusem (bez urwania)."""
    end = min(len(out), n_dry + int(keep * sr))
    out = out[:end].copy()
    f = min(int(fade * sr), end)
    out[end - f:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f))).astype(np.float32)
    return out


def _ghost_b(y, sr, low_mix, rev_s, wet):
    n = len(y)
    y = _filt(y, 'highpass', 120, sr)
    c = _chorus(y + low_mix * _shift(y, sr, -5), sr, 0.3)
    c = _filt(c, 'lowpass', 7000, sr)
    rev = _conv(c, _ir(sr, rev_s, 0.03, 4000))
    return _tail(_mix(c, _wet(c, rev, wet)), n, sr)


def ghost_b2(y, sr):
    return _ghost_b(y, sr, 0.3, 1.6, 0.45)


def ghost_b3(y, sr):
    return _ghost_b(y, sr, 0.18, 1.2, 0.3)


def _ghost_c(y, sr, swell_mix, rev_mix, chorus):
    n = len(y)
    y = _filt(y, 'highpass', 150, sr)
    ir = _ir(sr, 0.8, 0.0, 5000)
    pre = len(ir) - 1
    swell = _conv(y[::-1], ir)[::-1]
    dry = np.concatenate([np.zeros(pre, np.float32), _chorus(y, sr, chorus)])
    rev = _conv(dry, _ir(sr, 1.0, 0.02, 4500))
    out = _mix(_mix(dry, _wet(dry, swell, swell_mix)), _wet(dry, rev, rev_mix))
    lead = int(0.25 * sr)       # narastanie najwyżej 0,25 s przed słowem
    out = out[max(0, pre - lead):]
    return _tail(out, n + min(pre, lead), sr)


def ghost_c2(y, sr):
    return _ghost_c(y, sr, 0.35, 0.22, 0.2)


def ghost_c3(y, sr):
    return _ghost_c(y, sr, 0.22, 0.15, 0.15)


def mind_d(y, sr):
    """Chór szeptów: sucha mowa i trzy szepty z niej, odstrojone i lekko opóźnione, jak głosy wokół myśli."""
    y = _filt(y, 'highpass', 120, sr)
    wh = _whisper(y, sr)
    out = y.copy()
    for ms, steps, g in ((35, 0.5, 0.22), (60, -0.7, 0.2), (90, 1.2, 0.16)):
        layer = _shift(wh, sr, steps)
        d = int(ms * sr / 1000)
        out[d:] += _wet(y, layer, g)[:len(y) - d]
    return out


def mind_e(y, sr):
    """Wnętrze czaszki: stłumiony, bliski głos, ciasne odbicia 80 ms i powolne pulsowanie."""
    from scipy.signal import iirpeak, lfilter
    y = _filt(_filt(y, 'highpass', 90, sr), 'lowpass', 3200, sr)
    b, a = iirpeak(420, 2.0, fs=sr)
    y = y + 0.6 * lfilter(b, a, y).astype(np.float32)
    n = np.arange(len(y))
    y = y * (1 - 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.5 * n / sr))).astype(np.float32)
    room = _conv(y, _ir(sr, 0.08, 0.002, 2500))
    return _mix(y, _wet(y, room, 0.45))


def mind_f(y, sr):
    """Piekielny: całość 3 półtony niżej, nasycenie tanh w tle i krótkie narastanie przed słowem."""
    n = len(y)
    low = _shift(_filt(y, 'highpass', 80, sr), sr, -3)
    sat = np.tanh(4.0 * low / (np.max(np.abs(low)) + 1e-9)).astype(np.float32)
    d = low + _wet(low, _filt(sat, 'lowpass', 5000, sr), 0.35)
    ir = _ir(sr, 0.4, 0.0, 4000)
    pre = len(ir) - 1
    swell = _conv(d[::-1], ir)[::-1]
    out = _mix(np.concatenate([np.zeros(pre, np.float32), d]), _wet(d, swell, 0.3))
    return _tail(out[pre - int(0.15 * sr):], n + int(0.15 * sr), sr)


def mind_g(y, sr):
    """Echo w myślach: dwa powtórzenia po 230 ms, coraz ciemniejsze i niższe, sucha mowa na wierzchu."""
    n = len(y)
    out = _pad(y, sr, 0.8)
    rep = y
    for k in (1, 2):
        rep = _filt(_shift(rep, sr, -0.6), 'lowpass', 3500 / k, sr)
        d = int(0.23 * k * sr)
        out[d:d + n] += _wet(y, rep, 0.38 / k)
    return _tail(out, n, sr, keep=0.5, fade=0.3)


def sibilant_spans(y, sr, hf=3500.0, ratio=0.6, floor_db=-34.0):
    """Odcinki głosek syczących (s, sz, ś, c): ramki 20 ms co 10 ms z przewagą energii powyżej `hf` i głośnością
    nie niższą niż `floor_db` od najgłośniejszej ramki; odcinki od 30 ms, poszerzone o ramkę z każdej strony."""
    hop, win = int(0.01 * sr), int(0.02 * sr)
    n = max(0, 1 + (len(y) - win) // hop)
    if n == 0:
        return []
    frames = np.stack([y[i * hop:i * hop + win] * np.hanning(win) for i in range(n)])
    spec = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    freqs = np.fft.rfftfreq(win, 1 / sr)
    total = spec.sum(axis=1) + 1e-12
    high = spec[:, freqs >= hf].sum(axis=1) / total
    db = 10 * np.log10(total)
    hit = (high > ratio) & (db > db.max() + floor_db)
    spans, i = [], 0
    while i < n:
        if hit[i]:
            j = i
            while j + 1 < n and hit[j + 1]:
                j += 1
            if j - i + 1 >= 3:
                spans.append((max(0, (i - 1) * hop), min(len(y), (j + 1) * hop + win)))
            i = j + 1
        else:
            i += 1
    return spans


def _stretch_noise(seg, sr, factor, rng):
    """Szum wydłużony `factor` razy: ziarna 20 ms z losowych miejsc odcinka, okno Hanna, krok 5 ms (bez fazowania)."""
    g, hop = int(0.02 * sr), int(0.005 * sr)
    if len(seg) <= g:
        return seg
    out_len = int(len(seg) * factor)
    out = np.zeros(out_len + g, np.float32)
    norm = np.zeros_like(out)
    w = np.hanning(g).astype(np.float32)
    for o in range(0, out_len, hop):
        centre = o / factor
        s = int(np.clip(centre + rng.uniform(-0.005, 0.005) * sr, 0, len(seg) - g))
        out[o:o + g] += seg[s:s + g] * w
        norm[o:o + g] += w
    return out[:out_len] / np.maximum(norm[:out_len], 1e-3)


def _serpent(y, sr, factor, boost):
    """Wężowa wymowa: głoski syczące wydłużone `factor` razy i głośniejsze `boost` razy, reszta bez zmian."""
    rng = np.random.default_rng(SEED)
    fade = int(0.004 * sr)
    ramp = np.linspace(0, 1, fade, dtype=np.float32)
    parts, last = [], 0
    for a, b in sibilant_spans(y, sr):
        parts.append(y[last:a])
        hiss = _stretch_noise(y[a:b].astype(np.float32), sr, factor, rng) * boost
        if len(hiss) > 2 * fade:
            hiss[:fade] *= ramp
            hiss[-fade:] *= ramp[::-1]
        parts.append(hiss)
        last = b
    parts.append(y[last:])
    return np.concatenate(parts).astype(np.float32)


def serpent_a(y, sr):
    """Runda 11 (Levirax): syk węża, głoski syczące 1,8 raza dłuższe i 1,4 raza głośniejsze."""
    return _serpent(y, sr, 1.8, 1.4)


def serpent_b(y, sr):
    """Mocniejszy syk: głoski syczące 2,5 raza dłuższe i 1,7 raza głośniejsze."""
    return _serpent(y, sr, 2.5, 1.7)


VARIANTS = {'serpent_a': serpent_a, 'serpent_b': serpent_b,
            'ghost_a': ghost_a, 'ghost_b': ghost_b, 'ghost_c': ghost_c,
            'ghost_b2': ghost_b2, 'ghost_b3': ghost_b3, 'ghost_c2': ghost_c2, 'ghost_c3': ghost_c3,
            'mind_a': mind_a, 'mind_b': mind_b, 'mind_c': mind_c,
            'mind_d': mind_d, 'mind_e': mind_e, 'mind_f': mind_f, 'mind_g': mind_g}


def apply(y, sr, name):
    """Efekt `name` na sygnale mono float32; wynik bez przesterowania (szczyt ≤ 0,99 przed wyrównaniem)."""
    if not name:
        return y
    out = VARIANTS[name](np.asarray(y, np.float32), sr)
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    return out / peak * 0.99 if peak > 0.99 else out
