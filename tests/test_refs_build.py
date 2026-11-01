"""Cięcie referencji (D33) i składanie części kwestii (D16, D20)."""
from lektor import build, refs
from lektor import segment as S


def words(*spec):
    return [(t, a, b) for t, a, b in spec]


def test_cut_span_ends_on_sentence_within_limit():
    w = words((' Pierwsze', 0.5, 1.0), (' zdanie.', 1.0, 2.0), (' Drugie', 2.3, 3.5), (' zdanie', 3.5, 5.0),
              (' trwa.', 5.0, 6.0), (' Trzecie', 6.5, 9.0), (' za', 9.0, 10.0), (' długie.', 10.0, 12.0))
    first, last, start, end = refs.cut_span(w, 12.5)
    assert (first, last) == (0, 4)
    assert abs(start - 0.45) < 1e-9 and abs(end - 6.15) < 1e-9


def test_cut_span_skips_cut_first_word():
    w = words(('ciej', 0.0, 0.3), (' mowy.', 0.3, 1.0), (' Nowe', 1.2, 2.0), (' zdanie', 2.0, 4.0), (' tutaj.', 4.0, 6.0))
    first, last, start, _ = refs.cut_span(w, 7.0)
    assert (first, last) == (2, 4) and abs(start - 1.15) < 1e-9


def test_cut_span_falls_back_to_pause():
    w = words((' Bez', 0.0, 2.0), (' kropki', 2.0, 5.0), (' tu', 5.4, 8.0), (' wcale', 8.0, 11.0))
    _, last, _, end = refs.cut_span(w, 11.0)
    assert last == 1 and abs(end - 5.15) < 1e-9


def line(key, category, text, voice='narrator', args=()):
    from lektor.normalize import normalize
    return {'key': key, 'category': category, 'text_raw': text, 'text_norm': normalize(text), 'voice': voice,
            'args': list(args)}


def test_choice_hero_from_key():
    assert build.choice_hero('Q1_SYRUS_AMBITION_2') == 'syrus'
    assert build.choice_hero('Q1_DOOR_CHOICE') is None


def test_line_parts_choice_quote_and_description():
    r = line('Q1_SYRUS_TEST', 'opcja_wyboru', '– Idziemy – mówi on cicho.')
    assert build.line_parts(r) == [('quote', 'syrus', 'Idziemy.'), ('desc', 'narrator', 'Mówi on cicho.')]


def test_line_parts_choice_without_quote_is_narrator():
    r = line('Q1_DOOR', 'opcja_wyboru', 'Otwórz drzwi.', voice='syrus')
    assert build.line_parts(r) == [('text', 'narrator', 'Otwórz drzwi.')]


def test_line_parts_template_splits_long_text():
    long = ('Bardzo długie zdanie szablonu, które się powtarza. ' * 8).strip()
    r = line('X', 'komunikat_questu', long + ' Teraz {0}.', args=[{'type': 'EntityName', 'ref': 'EnemyGUID'}])
    parts = build.line_parts(r)
    assert parts[-1][0] == 'slot' and sum(p[0] == 'text' for p in parts) > 1
    assert all(len(p[2]) <= S.LONG for p in parts if p[0] == 'text')


def test_value_texts_numbers_cover_range():
    slot = {'type': 'VariableInt', 'prev': 'Zadaj', 'noun': '\x01TERM_DAMAGE\x01'}
    texts = build.value_texts(slot, {}, 'X', {}, {}, set())
    assert list(texts) == [str(v) for v in S.NUMBER_VALUES]
    assert (texts['1'], texts['2'], texts['5']) == ('jedno obrażenie', 'dwa obrażenia', 'pięć obrażeń')
    # Zwykły rzeczownik zostaje w formie z szablonu; liczebnik dostaje jego rodzaj.
    plain = build.value_texts({'type': 'VariableInt', 'prev': None, 'noun': 'karty'}, {}, 'X', {}, {}, set())
    assert plain['2'] == 'dwie karty'


def test_value_texts_strip_sprites_and_reuse_lines():
    values = {'entity': ['ENEMY_A_SING', 'Q1_LINE'], 'vars': {}, 'name_vars': [], 'objectives': []}
    terms = {'ENEMY_A_SING': {'text': '<sprite=0>Bandyta'}, 'Q1_LINE': {'text': 'Kwestia.'}}
    texts = build.value_texts({'type': 'EntityName'}, {}, 'X', values, terms, {'Q1_LINE'})
    assert texts == {'ENEMY_A_SING': 'Bandyta', 'Q1_LINE': None}
