"""Podział okien narratora na głosy postaci i jedno tempo narratora (E16, D101). Zdania testowe własne."""
from lektor import build as B
from lektor import direction as D
from lektor import speakers as S


def kinds(text):
    return [(k, t) for k, t, _ in S.split(text)]


def test_dialogue_with_attribution_after():
    assert kinds('– Ruszamy o świcie – mówi Brynn. – Nie ma na co czekać.') == [
        ('s', 'Ruszamy o świcie'), ('n', 'mówi Brynn.'), ('s', 'Nie ma na co czekać.')]


def test_dash_inside_narration_is_not_speech():
    assert kinds('Strażnik – sądząc po zbroi – służy tu od lat.') == [('n', 'Strażnik – sądząc po zbroi – służy tu od lat.')]


def test_speech_after_sentence_end():
    assert kinds('Kowal odkłada młot. – Gotowe, panie.') == [('n', 'Kowal odkłada młot.'), ('s', 'Gotowe, panie.')]


def test_guess_name_after_and_continuation():
    pieces = S.split('– Idziemy – mówi Syrus – a potem odpoczniemy.')
    assert [v for v, _ in S.guess('X', pieces)] == ['syrus', 'syrus']


def test_guess_slot_after_is_hero_from_argument():
    pieces = S.split('– Uważaj – szepcze {0}.')
    assert S.guess('X', pieces, ['VariableString'])[0] == ('arg:0', 'luka po')
    assert S.guess('X', pieces, ['EntityName'])[0] == ('enemy:0', 'luka po')


def test_parts_merge_and_punctuation():
    text = '– Ruszamy o świcie, – mówi Brynn. – Nie ma na co czekać.'
    assert S.parts('K', text, {'K': ['brynn', 'brynn']}) == [
        ('brynn', 'Ruszamy o świcie.'), ('narrator', 'Mówi Brynn.'), ('brynn', 'Nie ma na co czekać.')]


def test_parts_override_narrator_and_per_piece():
    text = '– Raz – mówi ktoś. – Dwa.'
    assert S.parts('K', text, {'K': 'narrator'}) is None
    assert S.parts('K', text, {'K': {'pieces': ['nv_gap', 'narrator', 'nv_gap']}}) == [
        ('nv_gap', 'Raz.'), ('narrator', 'Mówi ktoś.'), ('nv_gap', 'Dwa.')]


def test_parts_without_speech_is_none():
    assert S.parts('K', 'Droga prowadzi przez las.', {}) is None


def test_overrides_file_has_only_known_voice_forms():
    for key, v in S.load_overrides().items():
        voices = v['pieces'] if isinstance(v, dict) else [v] if isinstance(v, str) else v
        assert all(x == 'narrator' or x.startswith(('arg:', 'nv_')) or x.isalpha() for x in voices), key


def test_split_voices_makes_hero_versions(monkeypatch):
    monkeypatch.setattr(B.speakers, 'load_overrides', lambda: {'K': ['arg:0']})
    r = {'key': 'K', 'tts': 1, 'voice': 'narrator', 'category': 'zdarzenie', 'group': 'travel_act1',
         'text_raw': '– Uważaj – szepcze {0}.', 'args': [{'type': 'VariableString'}], 'hero_variant': []}
    out = B.split_voices([r], 't1')
    assert r['hero_variant'] == ['ARG:0'] and r['split'][0] == ('narrator', 'Uważaj.')
    brynn = next(x for x in out if x['key'] == 'K#brynn')
    assert brynn['split'][0] == ('brynn', 'Uważaj.') and brynn['split'][1][0] == 'narrator'
    assert len(out) == 1 + len(B.scope.HEROES)


def test_split_voices_only_in_test_release_and_groups(monkeypatch):
    monkeypatch.setattr(B.speakers, 'load_overrides', lambda: {})
    r = {'key': 'K', 'tts': 1, 'voice': 'narrator', 'category': 'zdarzenie', 'group': 'travel_act2',
         'text_raw': '– Idziemy – mówi Syrus.', 'args': [], 'hero_variant': []}
    assert 'split' not in B.split_voices([dict(r)], 't1')[0]
    assert B.split_voices([dict(r, group='travel_act1')], 'm3')[0].get('split') is None
    assert B.split_voices([dict(r, group='travel_act1')], 't1')[0]['split'][0] == ('syrus', 'Idziemy.')


def test_narrator_one_tempo_in_test_release():
    r = {'speed': 1.23, 'group': 'town', 'category': 'zdarzenie'}
    assert B.piece_speed(r, 'narrator', 'x' * 40, 't1') == D.SPEED_MAX
    assert B.piece_speed(r, 'narrator', 'x' * 40, 'm3') == 1.23
    assert B.piece_speed(dict(r, group='travel_act2'), 'narrator', 'x', 't1') == 1.23    # poza zakresem testu bez zmian
    assert B.piece_speed(dict(r, speed=None), 'narrator', 'x', 't1') is None              # narracja scen: tempo naturalne
    assert B.piece_speed(r, 'brynn', 'x' * 40, 't1') == 1.23                               # postać: rampa D34
    assert B.piece_speed(dict(r, split=[('brynn', 'x')]), 'brynn', 'x' * 40, 't1') == D.tempo('zdarzenie', 40)[0]


def test_ability_records_from_weapon_and_trinket_models():
    """E16 (D101): nazwy i opisy zdolności broni i talizmanów jako kwestie z przełącznikiem 'zdolnosci'."""
    from lektor import abilities as A

    class Game:
        files = {'d3/weapons/sword': 1, 'd3/items': 2, 'd3/enemies': 3}

        def behaviours(self, name):
            weapon = {'KeyName': 'W_NAME', 'KeyDesc': 'W_DESC', 'Chance': 1, 'EffectTiming': 0, 'ShowPostAttackMessage': 1}
            trinket = {'KeyName': 'T_NAME', 'AbilityKey': 'T_DESC', 'AbilityType': 2}
            return {'d3/weapons/sword': [(None, weapon, 'X'), (None, weapon, 'X')], 'd3/items': [(None, trinket, 'Y')],
                    'd3/enemies': [(None, dict(weapon, KeyName='E_NAME'), 'Z')]}[name]
    terms = {k: {'text': 'Tekst %s.' % k} for k in ('W_NAME', 'W_DESC', 'T_NAME', 'E_NAME')}
    assert A.keys(Game()) == [('T_NAME', 'T_DESC'), ('W_NAME', 'W_DESC')]
    recs = A.records(Game(), terms, {'W_DESC'})
    assert [r['key'] for r in recs] == ['T_NAME', 'W_NAME']        # w bazie już jest, bez tekstu: pominięte
    assert {r['toggle'] for r in recs} == {'zdolnosci'} and {r['voice'] for r in recs} == {'narrator'}
