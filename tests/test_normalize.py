"""Normalizacja: znaczniki, ikony i liczby z odmianą. Zdania testowe są własne, nie z gry."""
import pytest

from lektor.normalize import cardinal, clean_markup, normalize, ordinal

DMG = '<link=TERM_DAMAGE>X</link>'


@pytest.mark.parametrize('text, expected', [
    ('Zadaj 2 %s.' % DMG, 'Zadaj dwa obrażenia.'),
    ('Zadaj 5 %s.' % DMG, 'Zadaj pięć obrażeń.'),
    ('Zyskujesz 1 %s.' % DMG, 'Zyskujesz jedno obrażenie.'),
    ('Weź 1 kartę.', 'Weź jedną kartę.'),
    ('Otwórz 2 drzwi.', 'Otwórz dwoje drzwi.'),
    ('Przeczytaj akapit na str. 12.', 'Przeczytaj akapit na stronie dwunastej.'),
])
def test_numbers_agree_with_nouns(text, expected):
    assert normalize(text) == expected


def test_markup_removed():
    assert normalize('<b>Uwaga</b>: <color=#fff>idź</color>.') == 'Uwaga: idź.'
    assert '\x01' not in normalize('Masz %s.' % DMG)


def test_icon_kept_as_token_for_agreement():
    assert clean_markup('2 %s' % DMG) == '2 \x01TERM_DAMAGE\x01'


def test_slots_preserved():
    assert normalize('Masz {0} i {1}.') == 'Masz {0} i {1}.'


def test_stage_directions_dropped():
    assert normalize('SZEPCZE CICHO Tak.') == 'Tak.'


def test_line_breaks_become_sentences():
    assert normalize('Pierwsze\nDrugie') == 'Pierwsze. Drugie'
    assert normalize('Pytanie?\nOdpowiedź') == 'Pytanie? Odpowiedź'


def test_number_words():
    assert cardinal(21) == 'dwadzieścia jeden'
    assert cardinal(2, 'acc', 'f') == 'dwie'
    assert cardinal(5, 'gen') == 'pięciu'
    assert ordinal(3) == 'trzeci'
