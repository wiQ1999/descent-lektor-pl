"""Tempo i pauzy (D34), przełączniki companiona (D21, D30, D31), klucz cache fragmentu."""
import pytest

from lektor import direction as D


@pytest.mark.parametrize('chars, speed', [(10, 1.2), (80, 1.2), (190, 1.3), (300, 1.4), (1000, 1.4)])
def test_tempo_ramp(chars, speed):
    assert D.tempo('komunikat_questu', chars) == (speed, D.PAUSE)


def test_scene_narration_keeps_natural_tempo():
    assert D.tempo('narracja_fabularna', 500) == (None, D.SCENE_PAUSE)


@pytest.mark.parametrize('category, key, toggle', [
    ('walka_teren', 'ENEMY_ACTIVATION_BANDIT_BASIC', 'aktywacje'),
    ('walka_teren', 'BANDIT_TACTIC_MULTI_SHOT_HINT', 'aktywacje'),
    ('walka_teren', 'DEFAULT_SPAWN_ENEMY', 'walka_teren'),
    ('cel_misji', 'Q1_OBJECTIVE_1', 'cele'),
    ('dialog', 'Q1_SYRUS_DOOR', 'dialogi'),
    ('zdarzenie', 'TRAVEL_57', 'narracja'),
    ('nieznana', 'X', 'ui'),
])
def test_toggle(category, key, toggle):
    assert D.toggle(category, key) == toggle


def test_fragment_id_is_stable():
    # Zmiana formatu klucza unieważnia wygenerowane audio: ta wartość może się zmienić tylko świadomie.
    assert D.fragment_id('narrator@abcdef12', 'Dzień dobry.', 1.2) == '0d54849ee9f32833'
    assert D.fragment_id('syrus', 'Tak.', None) == '8b60964a8ead542b'


def test_fragment_id_depends_on_every_field():
    base = D.fragment_id('narrator', 'Tekst.', 1.2)
    assert base != D.fragment_id('syrus', 'Tekst.', 1.2)
    assert base != D.fragment_id('narrator', 'Tekst!', 1.2)
    assert base != D.fragment_id('narrator', 'Tekst.', 1.25)
    assert base != D.fragment_id('narrator', 'Tekst.', None)
