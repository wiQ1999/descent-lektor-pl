"""Podział kwestii: zdania, szablony {n} (D16), opcje z cytatem (D20)."""
import pytest

from lektor import segment as S

DMG = '<link=TERM_DAMAGE>X</link>'


def test_split_keeps_all_text():
    text = ' '.join('Zdanie numer %s jest tutaj, żeby test miał treść.' % w for w in 'abcdefghijkl')
    chunks = S.split_sentences(text)
    assert ' '.join(chunks) == text
    assert all(len(c) <= S.LONG for c in chunks)


def test_split_merges_short_sentences():
    assert S.split_sentences('Tak. Dobrze, idziemy dalej razem w ciemność lasu.') == \
        ['Tak. Dobrze, idziemy dalej razem w ciemność lasu.']


def test_split_long_only_above_limit():
    short = 'Krótka kwestia. Druga.'
    assert S.split_long(short) == [short]
    long = ('Długie zdanie, które powtarzamy wiele razy. ' * 10).strip()
    assert len(S.split_long(long)) > 1


def test_template_pieces_with_number_and_name():
    pieces = S.template_pieces('Zadaj {0} %s wrogowi {1}.' % DMG, ['VariableInt', 'EntityName'])
    assert [p['kind'] for p in pieces] == ['text', 'slot', 'text', 'slot']
    assert pieces[0]['text'] == 'Zadaj'
    assert pieces[1] == {'kind': 'slot', 'arg': 0, 'type': 'VariableInt', 'prev': 'Zadaj',
                         'noun': '\x01TERM_DAMAGE\x01'}
    assert pieces[2]['text'] == 'wrogowi'
    assert pieces[3]['type'] == 'EntityName' and pieces[3]['tail'] == '.'


def test_template_punctuation_merges():
    pieces = S.template_pieces('Atakuje {0}! Uważaj, {1}.', ['EntityName', 'VariableString'])
    assert [p['kind'] for p in pieces] == ['text', 'slot', 'text', 'slot']
    assert pieces[1]['tail'] == '!' and pieces[2]['text'] == 'Uważaj,'
    assert pieces[3]['tail'] == '.'


def test_template_list_slot():
    pieces = S.template_pieces('Pojawiają się: {n}.', ['EntityName'])
    assert pieces[1]['arg'] == -1 and pieces[1]['type'] == 'EntityName'


def test_template_text_is_normalized():
    pieces = S.template_pieces('Weź 2 karty i daj je {0}.', ['VariableString'])
    assert pieces[0]['text'] == 'Weź dwie karty i daj je'


@pytest.mark.parametrize('value, prev, noun, expected', [
    (1, None, None, 'jeden'),
    (3, 'Zadaj', '\x01TERM_DAMAGE\x01', 'trzy obrażenia'),
    (5, 'Zadaj', '\x01TERM_DAMAGE\x01', 'pięć obrażeń'),
    (2, None, 'karty', 'dwie karty'),
    (5, 'do', 'pól', 'pięciu pól'),
])
def test_number_value_text(value, prev, noun, expected):
    assert S.number_value_text(value, prev, noun) == expected


@pytest.mark.parametrize('text, expected', [
    ('– Idę pierwszy – mówi Syrus.', ('Idę pierwszy.', 'Mówi Syrus.', 'syrus')),
    ('„Zostańmy tutaj” – proponuje Brynn.', ('Zostańmy tutaj.', 'Proponuje Brynn.', 'brynn')),
    ('– Zgoda – odpowiada Galadenowi Vaerix.', ('Zgoda.', 'Odpowiada Galadenowi Vaerix.', 'vaerix')),
    ('– Za mną – woła Fuks.', ('Za mną.', 'Woła Fuks.', 'chance')),
    ('"Ruszajmy", mówi ktoś.', ('Ruszajmy.', 'Mówi ktoś.', None)),
    ('Otwórz drzwi.', None),
])
def test_choice_parts(text, expected):
    assert S.choice_parts(text) == expected
