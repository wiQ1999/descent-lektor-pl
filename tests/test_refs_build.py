"""Cięcie referencji (D33) i składanie części kwestii (D16, D20)."""
import pytest

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


def test_line_parts_quote_takes_hero_of_the_window_in_m2():
    r = line('E_TEST_31_32A', 'opcja_wyboru', '„Idziemy dalej”.')
    r['speakers'] = ['SYRUS']
    assert build.line_parts(r)[0][1] == 'narrator'      # M1 bez zmian
    assert build.line_parts(r, 'm2')[0][:2] == ('quote', 'syrus')


def test_line_parts_quote_in_npc_window_stays_narrator():
    r = line('E_TEST_13F', 'opcja_wyboru', '„Idziemy dalej”.')
    r['speakers'] = ['MASTERBRULI', 'MASTERFLINT']
    assert build.line_parts(r, 'm2')[0][1] == 'narrator'


def test_line_parts_option_without_quote_stays_narrator_in_m2():
    r = line('E_TEST_18_19K', 'opcja_wyboru', 'Test: otwórz drzwi.', voice='narrator')
    r['speakers'] = ['VAERIX']
    assert build.line_parts(r, 'm2') == [('text', 'narrator', 'Test: otwórz drzwi.')]


def test_line_parts_template_splits_long_text():
    long = ('Bardzo długie zdanie szablonu, które się powtarza. ' * 8).strip()
    r = line('X', 'komunikat_questu', long + ' Teraz {0}.', args=[{'type': 'EntityName', 'ref': 'EnemyGUID'}])
    parts = build.line_parts(r)
    assert parts[-1][0] == 'slot' and sum(p[0] == 'text' for p in parts) > 1
    assert all(len(p[2]) <= S.LONG for p in parts if p[0] == 'text')


@pytest.mark.parametrize('tail', ['Do waszych zasobów dodano 30 sztuk złota.', 'ZYSKUJECIE ZAUFANIE KUPCÓW.',
                                  'Zdobywasz dwa żetony.', '*Do twoich zasobów dodano Płaszcz.*'])
def test_system_tail_splits_game_notice(tail):
    speech, notice = build.system_tail('Bierzcie, ile trzeba.\nI ruszajcie.\n\n' + tail)
    assert speech == 'Bierzcie, ile trzeba.\nI ruszajcie.' and notice == tail.strip('*')


@pytest.mark.parametrize('raw', ['Bierzcie, ile trzeba. Do waszych zasobów dodano złoto.',
                                 'Pierwszy akapit.\n\nDrugi akapit mówi dalej postać.', 'Tylko JEDNO SŁOWO.\n\nOK TAK'])
def test_system_tail_keeps_speech(raw):
    assert build.system_tail(raw) is None


def test_line_parts_game_notice_goes_to_narrator_from_m3():
    r = line('E_TEST_11', 'dialog', 'Bierzcie, ile trzeba.\n\nDo waszych zasobów dodano 30 sztuk złota.', voice='kehli')
    assert [p[1] for p in build.line_parts(dict(r), 'm2')] == ['kehli']   # M1 i M2 bez zmian
    assert build.line_parts(dict(r), 'm3') == [('text', 'kehli', 'Bierzcie, ile trzeba.'),
                                               ('text', 'narrator', 'Do waszych zasobów dodano trzydzieści sztuk złota.')]


def test_line_parts_game_notice_with_slot():
    r = line('E_TEST_12', 'dialog', 'Proszę.\n\nDo waszych zasobów dodano recepturę ({0}).', voice='kehli',
             args=[{'type': 'ItemName', 'ref': 'X'}])
    parts = build.line_parts(r, 'm3')
    assert parts[0] == ('text', 'kehli', 'Proszę.') and {p[1] for p in parts[1:]} == {'narrator'}
    assert any(p[0] == 'slot' for p in parts[1:])


@pytest.mark.parametrize('text, expected', [
    ('Idziemy. ZYSKUJECIE ZAUFANIE KUPCÓW Z MIASTA.', 'Idziemy. Zyskujecie zaufanie kupców z miasta.'),
    ('KAŻDY BOHATER BIERZE 1 ŻETON. POTEM ODPOCZYWA.', 'Każdy bohater bierze 1 żeton. Potem odpoczywa.'),
    ('Krzyczy: OTO NASZE SKARBY!', 'Krzyczy: Oto nasze skarby!'),
    ('POCZĄTEK ROZDZIAŁU „STARA WIEŻA”.', 'Początek rozdziału „stara wieża”.'),
    ('SYRUS WYBIERA…', 'SYRUS WYBIERA…'),
    ('ROZPOCZNIESZ AKT II Z ZAPASAMI.', 'Rozpoczniesz akt drugi z zapasami.'),
    ('Możemy badać i poznać NASZE STARE SEKRETY!', 'Możemy badać i poznać nasze stare sekrety!'),
    ('I wtedy ORK przyszedł.', 'I wtedy ORK przyszedł.'),
    ('ZADAJ \x01TERM_DAMAGE\x01 TERAZ.', 'Zadaj \x01TERM_DAMAGE\x01 teraz.'),
])
def test_caps_to_speech(text, expected):
    assert build.caps_to_speech(text) == expected


def test_line_parts_caps_notice_read_by_narrator_in_m3():
    r = line('E_TEST_13', 'dialog', 'Dziękuję.\n\nZYSKUJECIE ZAUFANIE KUPCÓW Z MIASTA.', voice='kehli')
    assert [p[1] for p in build.line_parts(dict(r), 'm2')] == ['kehli']     # M2 bez zmian
    assert build.line_parts(dict(r), 'm3') == [('text', 'kehli', 'Dziękuję.'),
                                               ('text', 'narrator', 'Zyskujecie zaufanie kupców z miasta.')]


@pytest.mark.parametrize('text, expected', [
    ('(kiwa głową) Chodźmy już.', 'Chodźmy już.'),
    ('Dość tego. (wzdycha) Idziemy dalej.', 'Dość tego. Idziemy dalej.'),
    ('*uśmiecha się* Witaj w domu.', 'Witaj w domu.'),
    ('Weźmiemy linę (na wszelki wypadek), potem ruszymy.', 'Weźmiemy linę (na wszelki wypadek), potem ruszymy.'),
    ('Mamy (2) pochodnie.', 'Mamy (2) pochodnie.'),
    ('Bez wstawek.', 'Bez wstawek.'),
])
def test_drop_inserts(text, expected):
    assert build.drop_inserts(text) == expected


def test_line_parts_insert_dropped_for_character_in_m3():
    r = line('E_TEST_15', 'dialog', '(kiwa głową) Chodźmy już.', voice='kehli')
    assert build.line_parts(dict(r), 'm2') != [('text', 'kehli', 'Chodźmy już.')]    # M2 bez zmian
    assert build.line_parts(dict(r), 'm3') == [('text', 'kehli', 'Chodźmy już.')]
    n = line('E_TEST_16', 'narracja_fabularna', '(kiwa głową) Drzwi się otwierają.')
    assert 'kiwa' in build.line_parts(dict(n), 'm3')[0][2]     # narrator: decyzja w E15 (D86)


def test_line_parts_direction_still_dropped_in_m3():
    r = line('E_TEST_14', 'narracja_fabularna', 'Drzwi się otwierają. GRUPA WYBIERA…')
    assert build.line_parts(dict(r), 'm3') == [('text', 'narrator', 'Drzwi się otwierają.')]


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
