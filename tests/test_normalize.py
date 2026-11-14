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


def test_pronounce_spells_name_phonetically():
    from lektor.normalize import pronounce
    assert pronounce('Kehli i kehli, KEHLI oraz Kehlik.') == 'Keli i keli, KELI oraz Kelik.'
    assert pronounce('Bez zmian: Akehli.') == 'Bez zmian: Akehli.'


def test_number_words():
    assert cardinal(21) == 'dwadzieścia jeden'
    assert cardinal(2, 'acc', 'f') == 'dwie'
    assert cardinal(5, 'gen') == 'pięciu'
    assert ordinal(3) == 'trzeci'


ADV, SUCC, ACT = '<link=TERM_ADVANTAGE>\uf5de</link>', '<link=TERM_SUCCESS>\uf5e8</link>', '<link=TERM_ACTIONS>\uf5e4</link>'


@pytest.mark.parametrize('text, expected', [
    ('Za każdy %s zamieniony na %s weź kartę.' % (ADV, SUCC), 'Za każdy potencjał zamieniony na sukces weź kartę.'),
    ('Dodaj 1 i 1 %s.' % ADV, 'Dodaj jeden i jeden potencjał.'),
    ('1 %s: Zaatakuj.' % ACT, 'jedna akcja: Zaatakuj.'),
    ('2 %s: Zaatakuj.' % ACT, 'dwie akcje: Zaatakuj.'),
    ('Możesz wykonać 1 %s z karty.' % ACT, 'Możesz wykonać jedną akcję z karty.'),
    ('Wróg przyjmuje {1} \uf5e5.', 'Wróg przyjmuje {1} obrażenia.'),
])
def test_icons_without_word_get_glossary_name(text, expected):
    """D103: plus (potencjał), akcja i glif ikony bez linku glosariusza."""
    assert normalize(text) == expected


@pytest.mark.parametrize('text, expected', [
    ('Stary róg \uf5e2', 'ulepszony Stary róg'),
    ('Szara peleryna \uf5e2', 'ulepszona Szara peleryna'),
    ('Kamienne lusterko \uf5e2', 'ulepszone Kamienne lusterko'),
    ('Gogle nocy \uf5e2', 'ulepszone Gogle nocy'),
    ('Rękojeść nocy \uf5e2', 'ulepszona Rękojeść nocy'),
    ('Masz: Szara peleryna \uf5e2, Stary róg i Gogle nocy \uf5e2.', 'Masz: ulepszona Szara peleryna, Stary róg i ulepszone Gogle nocy.'),
])
def test_upgrade_icon_becomes_adjective_before_name(text, expected):
    """D103: ikona ulepszenia po nazwie przedmiotu, przymiotnik w rodzaju nazwy."""
    assert normalize(text) == expected
