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


VARIANTS = {'ghost_a': ghost_a, 'ghost_b': ghost_b, 'ghost_c': ghost_c,
            'mind_a': mind_a, 'mind_b': mind_b, 'mind_c': mind_c}


def apply(y, sr, name):
    """Efekt `name` na sygnale mono float32; wynik bez przesterowania (szczyt ≤ 0,99 przed wyrównaniem)."""
    if not name:
        return y
    out = VARIANTS[name](np.asarray(y, np.float32), sr)
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    return out / peak * 0.99 if peak > 0.99 else out
