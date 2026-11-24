import numpy as np
import pytest

from lektor import effects

SR = 24000


def voice_like(seconds=1.0):
    t = np.arange(int(SR * seconds)) / SR
    env = np.clip(np.sin(np.pi * t / seconds), 0, None)
    return (0.3 * env * (np.sin(2 * np.pi * 140 * t) + 0.4 * np.sin(2 * np.pi * 280 * t))).astype(np.float32)


@pytest.mark.parametrize('name', sorted(effects.VARIANTS))
def test_effect_is_finite_bounded_and_deterministic(name):
    y = voice_like()
    a = effects.apply(y, SR, name)
    b = effects.apply(y, SR, name)
    assert a.dtype == np.float32
    assert np.all(np.isfinite(a))
    assert np.max(np.abs(a)) <= 0.99 + 1e-6
    assert len(a) >= len(y)
    assert np.array_equal(a, b)


def test_serpent_stretches_only_hiss():
    rng = np.random.default_rng(0)
    from scipy.signal import butter, sosfilt
    hiss = sosfilt(butter(4, 4500, 'high', fs=SR, output='sos'), rng.standard_normal(int(0.15 * SR))).astype(np.float32)
    hiss *= 0.3 / np.abs(hiss).max()
    tone = voice_like(0.5)
    y = np.concatenate([tone, hiss, tone])
    spans = effects.sibilant_spans(y, SR)
    assert len(spans) == 1 and abs(spans[0][0] - len(tone)) < 0.03 * SR
    out = effects.apply(y, SR, 'serpent_b')
    grown = len(out) - len(y)
    assert 0.18 * SR < grown < 0.3 * SR       # syk 0,15 s (plus ramki brzegowe) wydłużony 2,5 raza
    assert len(effects.apply(voice_like(), SR, 'serpent_a')) == len(voice_like())     # bez syku bez zmian


def test_no_effect_returns_input():
    y = voice_like()
    assert effects.apply(y, SR, None) is y
