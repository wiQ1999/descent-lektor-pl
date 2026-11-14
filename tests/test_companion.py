import collections
import json
import os
import sqlite3

import numpy as np
import pytest
import soundfile as sf

from lektor import db
from lektor.companion import app as A
from lektor.companion import config as C
from lektor.companion import director as D
from lektor.companion.library import FEATS, LIST_GAP, LOOT, Library
from lektor.companion.player import CLOSE_FADE_S, FADE_S, Mixer, NullPlayer

SR = 24000
FRAGMENTS = {           # id: (tekst, sekundy)
    'f_hello': ('Witaj w gospodzie.', 1.0),
    'f_enemy': ('Wróg atakuje', 0.5),
    'f_bandit': ('bandyta', 0.25),
    'f_witch': ('czarna wiedźma', 0.25),
    'f_three': ('trzy', 0.25),
    'f_goal': ('Znajdź klucz.', 0.5),
    'f_found': ('Zdobywasz', 0.5),
    'f_choice': ('Idziemy dalej.', 0.5),
    'f_goal2': ('Wróć do wioski.', 0.5),
    'f_of4': ('z czterech', 0.25),
    'f_say': ('Ruszajmy.', 0.5),
    'f_say_brynn': ('Ruszajmy.', 0.5),
    'f_loot_head': ('Do ekwipunku trafia:', 0.5),
    'f_gold': ('złoto', 0.25),
    'f_fifteen': ('piętnaście', 0.25),
    'f_potion': ('mikstura zdrowia', 0.25),
    'f_keli': ('Keli', 0.25),
    'f_answer': ('Stara wieża czeka na nas.', 0.5),
    'f_answer_line': ('Stara wieża czeka na nas, przyjacielu.', 0.5),
    'f_map_name': ('Cena wiedzy', 0.25),
    'f_map_desc': ('Stara wieża czeka.', 0.5),
    'f_feat': ('Wyzwanie ukończone!', 0.5),
}
LINES = [   # klucz, kategoria, przełącznik, tts, tekst
    ('HELLO', 'narracja', 'narracja', 1, 'Witaj w gospodzie.'),
    ('SPAWN', 'walka_teren', 'walka_teren', 1, 'Wróg atakuje {0}'),
    ('SPAWN_MULTI', 'walka_teren', 'walka_teren', 1, 'Wróg atakuje {0}'),
    ('COUNT', 'komunikaty_questu', 'komunikaty_questu', 1, '{0}'),
    ('GOAL', 'cele', 'cele', 1, 'Znajdź klucz.'),
    ('GOAL2', 'cele', 'cele', 1, 'Wróć do wioski.'),
    ('NEW_GOAL', 'komunikaty_questu', 'komunikaty_questu', 1, '{0}'),
    ('LOOT', 'nagrody', 'nagrody', 1, 'Zdobywasz {0}'),
    ('CHOICE_A', 'okna_wyboru', 'okna_wyboru', 1, 'Idziemy dalej.'),
    ('ANSWER', 'okna_wyboru', 'okna_wyboru', 1, 'Stara wieża czeka na nas.'),
    ('ANSWER_LINE', 'dialog', 'dialogi', 1, 'Stara wieża czeka na nas, przyjacielu.'),
    ('CUTSCENE', 'narracja', 'narracja', 0, 'Przerywnik.'),
    ('ACT', 'aktywacje', 'aktywacje', 1, 'Wróg atakuje {0}'),
    ('GOAL_COUNT', 'cel_misji', 'cele', 1, 'Znajdź klucz ({0}/4)'),
    ('UI_CONTINUE', 'opcja_wyboru', 'okna_wyboru', 1, 'Kontynuuj'),
    ('SAY', 'dialog', 'dialogi', 1, 'Ruszajmy.'),
    ('SAY#brynn', 'dialog', 'dialogi', 1, 'Ruszajmy.'),
    ('TREASURE', 'system_nagroda', 'nagrody', 1, '{0} {1}'),
    ('MAP_NAME', 'opis_misji', 'opis_misji', 1, 'Cena wiedzy'),
    ('MAP_DESC', 'opis_misji', 'opis_misji', 1, 'Stara wieża czeka.'),
    ('DOTS', 'dialog', 'dialogi', 1, '…'),
    ('UI_FEAT_COMPLETED', 'system_nagroda', 'nagrody', 1, 'Wyzwanie ukończone!'),
]
SEGMENTS = [    # klucz, idx, rodzaj, luka, typ luki, fragment, pauza po
    ('HELLO', 0, 'text', None, None, 'f_hello', 0.3),
    ('SPAWN', 0, 'text', None, None, 'f_enemy', 0.1),
    ('SPAWN', 1, 'slot', 0, 'EntityName', None, 0.0),
    ('SPAWN_MULTI', 0, 'text', None, None, 'f_enemy', 0.1),
    ('SPAWN_MULTI', 1, 'slot', -1, 'EntityName', None, 0.0),
    ('COUNT', 0, 'slot', 0, 'VariableInt', None, 0.0),
    ('GOAL', 0, 'text', None, None, 'f_goal', 0.0),
    ('GOAL2', 0, 'text', None, None, 'f_goal2', 0.0),
    ('NEW_GOAL', 0, 'slot', 0, 'LocalizationKey', None, 0.0),
    ('LOOT', 0, 'text', None, None, 'f_found', 0.1),
    ('LOOT', 1, 'slot', 0, 'RawText', None, 0.0),
    ('CHOICE_A', 0, 'text', None, None, 'f_choice', 0.0),
    ('ANSWER', 0, 'text', None, None, 'f_answer', 0.0),
    ('ANSWER_LINE', 0, 'text', None, None, 'f_answer_line', 0.0),
    ('ACT', 0, 'text', None, None, 'f_enemy', 0.1),
    ('ACT', 1, 'slot', 0, 'EntityName', None, 0.0),
    ('GOAL_COUNT', 0, 'text', None, None, 'f_goal', 0.1),
    ('GOAL_COUNT', 1, 'slot', 0, 'VariableInt', None, 0.06),
    ('GOAL_COUNT', 2, 'text', None, None, 'f_of4', 0.0),
    ('SAY', 0, 'text', None, None, 'f_say', 0.0),
    ('SAY#brynn', 0, 'text', None, None, 'f_say_brynn', 0.0),
    ('TREASURE', 0, 'slot', 1, 'RawText', None, 0.0),
    ('MAP_NAME', 0, 'text', None, None, 'f_map_name', 0.0),
    ('MAP_DESC', 0, 'text', None, None, 'f_map_desc', 0.0),
    ('DOTS', 0, 'text', None, None, None, 0.0),
    ('UI_FEAT_COMPLETED', 0, 'text', None, None, 'f_feat', 0.0),
]
VALUES = [
    ('SPAWN', 0, 'ENEMY_BANDIT', 'f_bandit'), ('SPAWN', 0, 'ENEMY_WITCH', 'f_witch'), ('SPAWN', 0, 'HERO_KEHLI', 'f_keli'),
    ('SPAWN_MULTI', -1, 'ENEMY_BANDIT', 'f_bandit'), ('SPAWN_MULTI', -1, 'ENEMY_WITCH', 'f_witch'),
    ('COUNT', 0, '3', 'f_three'),
    ('NEW_GOAL', 0, 'GOAL', None),
    ('ACT', 0, 'ENEMY_BANDIT', 'f_bandit'),
    ('GOAL_COUNT', 0, '3', 'f_three'),
    ('UI_ENEMYDEFENSIVE_REMINDER', 0, 'ENEMY_DEFEND_ZEALOT', 'f_bandit'),
    (LOOT, 0, 'do ekwipunku trafia', 'f_loot_head'), (LOOT, 0, 'złoto', 'f_gold'), (LOOT, 0, '15', 'f_fifteen'),
    (LOOT, 0, 'mikstura zdrowia', 'f_potion'),
    (FEATS, 0, 'HERO_KEHLI_NAME', 'f_keli'), (FEATS, 0, 'FEAT_X_DESC', 'f_map_name'),
]


@pytest.fixture
def lib(tmp_path):
    path = tmp_path / 'm1.sqlite'
    con = sqlite3.connect(path)
    con.executescript(db.SCHEMA)
    con.executemany('INSERT INTO lines (key, category, toggle, voice, tts, text_norm) VALUES (?, ?, ?, "narrator", ?, ?)', LINES)
    con.executemany('INSERT INTO segments (key, idx, kind, arg, arg_type, voice, text, fragment, pause_after) '
                    'VALUES (?, ?, ?, ?, ?, "narrator", NULL, ?, ?)', SEGMENTS)
    con.executemany('INSERT INTO slot_values VALUES (?, ?, ?, ?)', VALUES)
    con.execute('UPDATE lines SET hero_variant = ? WHERE key = ?', ('["ARG:1"]', 'SAY'))   # E16: bohater z luki {1}
    con.executemany('INSERT INTO fragments VALUES (?, "narrator", 1.0, ?, 0, "text")', [(k, t) for k, (t, _) in FRAGMENTS.items()])
    con.commit()
    con.close()
    (tmp_path / 'final').mkdir()
    for fid, (_, sec) in FRAGMENTS.items():
        sf.write(tmp_path / 'final' / ('%s.wav' % fid), np.full(int(sec * SR), 0.1, np.float32), SR, subtype='FLOAT')
    manifest = {'model': 'test', 'sample_rate': SR, 'category_gain_db': {'walka_teren': 6.0},
                'fragments': {fid: {'file': 'final/%s.wav' % fid} for fid in FRAGMENTS}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return Library(str(path), str(tmp_path))


def entity(key, value='x'):
    return {'i': 0, 'type': 'EntityName', 'as_key': key, 'value': value}


def fids(u):
    return [p[0] for p in u.pieces]


# ---------- biblioteka ----------

def test_plain_line(lib):
    u = lib.resolve('HELLO')
    assert u.complete and u.pieces == [['f_hello', 0.3]] and u.toggle == 'narracja'


def test_entity_with_sprite_and_boss_alias(lib):
    assert fids(lib.resolve('SPAWN', [entity('<sprite=0>ENEMY_BANDIT')])) == ['f_enemy', 'f_bandit']
    u = lib.resolve('SPAWN', [entity('<sprite=0>ENEMY_BOSS_1 (ENEMY_WITCH)')])
    assert fids(u) == ['f_enemy', 'f_witch'] and u.complete


def test_entity_marker_matched_by_shown_name(lib):
    u = lib.resolve('SPAWN', [entity('<EntityName>', '<sprite=0><color=red>Czarna wiedźma</color>')])
    assert fids(u) == ['f_enemy', 'f_witch'] and not u.missing


def test_number_value(lib):
    assert fids(lib.resolve('COUNT', [{'i': 0, 'type': 'VariableInt', 'as_key': '3', 'value': '3'}])) == ['f_three']


def test_nested_line_value(lib):
    u = lib.resolve('NEW_GOAL', [{'i': 0, 'type': 'LocalizationKey', 'as_key': 'GOAL', 'value': '...'}])
    assert fids(u) == ['f_goal'] and u.nested == ['GOAL'] and u.complete


def test_counter_reads_number_and_total_only(lib):
    u = lib.counter('GOAL_COUNT', [{'i': 0, 'type': 'VariableInt', 'as_key': '3', 'value': '3'}])
    assert fids(u) == ['f_three', 'f_of4'] and u.complete
    assert lib.counter('GOAL', []) is None


def test_hero_variant_chosen_by_speaker(lib):
    assert fids(lib.resolve('SAY', hero='brynn')) == ['f_say_brynn']
    assert fids(lib.resolve('SAY', hero='syrus')) == ['f_say']
    assert fids(lib.resolve('SAY')) == ['f_say']


def test_hero_variant_chosen_by_slot_argument(lib):
    """E16 (D101): wypowiedź bohatera z luki {1} w oknie narratora: wersja po argumencie, nie po portrecie okna."""
    args = [{'i': 0, 'type': 'EntityName', 'as_key': 'X'}, {'i': 1, 'type': 'VariableString', 'as_key': 'HERO_BRYNN_NAME'}]
    assert fids(lib.resolve('SAY', args, hero='syrus')) == ['f_say_brynn']
    assert fids(lib.resolve('SAY', [args[0]])) == ['f_say']
    assert fids(lib.resolve('SAY', [args[0], {'i': 1, 'as_key': 'HERO_SYRUS_NAME'}])) == ['f_say']


def test_loot_list_from_game_text(lib):
    raw = '\n\nDo ekwipunku trafia: \n  - Złoto (15) i <b>Mikstura zdrowia</b>.'
    u = lib.resolve('TREASURE', [{'i': 0, 'type': 'LocalizationKey', 'as_key': '', 'value': ''},
                                 {'i': 1, 'type': 'RawText', 'as_key': raw, 'value': raw}])
    assert fids(u) == ['f_loot_head', 'f_gold', 'f_fifteen', 'f_potion'] and u.complete


def test_loot_with_unknown_name_is_partial(lib):
    u = lib.resolve('TREASURE', [{}, {'i': 1, 'type': 'RawText', 'value': 'Złoto i Tajemniczy Kielich'}])
    assert fids(u) == ['f_gold'] and u.missing == ['luka:RawText']


def test_empty_slot_is_not_missing(lib):
    u = lib.resolve('NEW_GOAL', [{'i': 0, 'type': 'VariableString', 'as_key': None, 'value': ''}])
    assert not u.missing


def test_line_value_matched_by_shown_text(lib):
    u = lib.resolve('NEW_GOAL', [{'i': 0, 'type': 'VariableString', 'as_key': '', 'value': 'Znajdź klucz.'}])
    assert fids(u) == ['f_goal'] and not u.missing


def test_value_spelled_phonetically_matches_text_from_game(lib):
    u = lib.resolve('SPAWN', [{'i': 0, 'type': 'EntityName', 'as_key': '', 'value': 'Kehli'}])
    assert fids(u)[-1] == 'f_keli' and not u.missing


def test_list_of_all_args(lib):
    u = lib.resolve('SPAWN_MULTI', [entity('<sprite=0>ENEMY_BANDIT'), entity('<sprite=0>ENEMY_WITCH')])
    assert u.pieces == [['f_enemy', 0.1], ['f_bandit', LIST_GAP], ['f_witch', 0.0]]


def test_runtime_value_is_skipped_and_logged(lib):
    u = lib.resolve('LOOT', [{'i': 0, 'type': 'RawText', 'as_key': None, 'value': 'Miecz'}])
    assert fids(u) == ['f_found'] and u.missing == ['luka:RawText'] and not u.complete


def test_unknown_key_falls_back_to_text(lib):
    u = lib.resolve('HELLO_V2', [], '<b>Witaj</b> w gospodzie!')
    assert u.via == 'text' and u.key == 'HELLO' and fids(u) == ['f_hello']
    assert lib.resolve('NOPE', [], None).missing == ['klucz']


def test_cutscene_has_no_narration(lib):
    u = lib.resolve('CUTSCENE')
    assert not u.tts and not u.pieces and not u.complete


def test_audio_concat_gaps_and_category_gain(lib):
    y = lib.audio(lib.resolve('SPAWN', [entity('ENEMY_BANDIT')]), volume=0.5)
    assert len(y) == int(0.5 * SR) + int(0.1 * SR) + int(0.25 * SR)
    assert y[0] == pytest.approx(0.1 * 0.5 * 10 ** (6 / 20), rel=1e-4) and y[int(0.55 * SR)] == 0


# ---------- reżyser ----------

class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


@pytest.fixture
def run(lib):
    clock = Clock()
    log = []
    d = D.Director(lib, NullPlayer(SR, clock), {'nagrody': False}, log=log.append, clock=clock)

    def step(ev=None, dt=0.0):
        clock.t += dt
        if ev:
            d.handle(ev)
        d.tick()
        return d
    step.d, step.log, step.clock = d, log, clock
    return step


def msg(i, key, **kw):
    return {'ev': 'open', 'kind': 'message', 'id': i, 'key': key, **kw}


def close(i, kind='message', **kw):
    return {'ev': 'close', 'kind': kind, 'id': i, **kw}


def playing(d):
    return d.current.key if d.current else None


def test_new_window_interrupts_previous(run):
    run(msg(1, 'HELLO'))
    run(close(1), 0.2)
    d = run(msg(2, 'SPAWN', args=[entity('ENEMY_BANDIT')]))
    assert playing(d) == 'SPAWN' and d.cut == 1
    assert [r['stop_s'] for r in run.log if r['ev'] == 'stopped'] == [0.0]


def test_story_plays_on_shown(run):
    d = run({'ev': 'open', 'kind': 'story', 'id': 5, 'key': 'HELLO'})
    assert playing(d) is None
    d = run({'ev': 'shown', 'kind': 'story', 'id': 5}, 0.4)
    assert playing(d) == 'HELLO' and d.latency['start'] == [0.0]


def test_choice_reply_holds_next_window(run):
    run(msg(1, 'HELLO'))
    run(close(1, choice_key='CHOICE_A'), 0.3)
    d = run(msg(2, 'HELLO'))
    assert playing(d) == 'CHOICE_A' and d.pending.wid == 2
    d = run(dt=0.6)       # odpowiedź (0,5 s) się skończyła: okno 2 gra od początku
    assert playing(d) == 'HELLO' and d.current.wid == 2
    assert run().latency['wait'] == [0.0]


def test_window_closed_while_waiting_is_logged(run):
    run(msg(1, 'HELLO'))
    run(close(1, choice_key='CHOICE_A'), 0.3)
    run(msg(2, 'HELLO'))
    run(msg(3, 'GOAL'), 0.1)
    d = run(close(3), 0.2)
    dropped = [(r['key'], r['reason'], r['reply']) for r in run.log if r['ev'] == 'porzucone']
    assert dropped == [('HELLO', 'nowe_okno', 'CHOICE_A'), ('GOAL', 'zamknięte', 'CHOICE_A')]
    assert d.summary()['dropped_windows'] == {'nowe_okno': 1, 'zamknięte': 1}


def test_skipping_waiting_window_stops_reply_and_reads_next(run):
    run(msg(1, 'HELLO'))
    run(close(1, choice_key='CHOICE_A'), 0.3)
    run(msg(2, 'GOAL'))
    d = run(close(2), 0.2)          # gracz pomija okno testu przed końcem opcji (D100)
    assert playing(d) is None and d.pending is None
    d = run(msg(3, 'GOAL2'))
    assert playing(d) == 'GOAL2' and d.trigger[d.current.token][1]


def test_answer_repeated_by_next_line_is_read_once(run):
    run(msg(1, 'HELLO'))
    run(close(1, choice_key='ANSWER'), 0.3)
    d = run(msg(2, 'ANSWER_LINE'))
    assert playing(d) == 'ANSWER_LINE' and d.pending is None


def test_answer_repeated_by_story_window_stops_before_shown(run):
    run(msg(1, 'HELLO'))
    d = run(close(1, choice_key='ANSWER'), 0.3)
    assert playing(d) == 'ANSWER'
    d = run({'ev': 'open', 'kind': 'story', 'id': 2, 'key': 'ANSWER_LINE'})
    assert playing(d) is None
    d = run({'ev': 'shown', 'kind': 'story', 'id': 2}, 0.1)
    assert playing(d) == 'ANSWER_LINE'


def test_other_line_after_choice_still_waits(lib):
    assert not lib.repeats('CHOICE_A', 'ANSWER_LINE')
    assert lib.repeats('ANSWER', 'ANSWER_LINE')
    assert not lib.repeats('ANSWER', 'NO_SUCH_KEY')


def blocks(mix, n, size=240):
    out = []
    for _ in range(n):
        b = np.zeros(size, dtype=np.float32)
        mix.render(b, 0.0)
        out.append(b)
    return np.concatenate(out)


def test_close_fades_the_voice_out():
    events = collections.deque()
    mix = Mixer(SR, events)
    mix.apply((np.ones(SR * 2, dtype=np.float32), 1, FADE_S), 0.0)
    blocks(mix, 1)
    mix.apply((None, None, CLOSE_FADE_S), 0.0)
    y = blocks(mix, int(CLOSE_FADE_S * SR / 240) + 2)
    assert (1, 'stopped', 0.0) in events
    assert 0.9 < y[0] <= 1.0 and 0.3 < y[len(y) // 2] < 0.7 and y[-1] == 0.0 and mix.tail is None


def test_new_sound_shortens_the_fade():
    mix = Mixer(SR, collections.deque())
    mix.apply((np.ones(SR * 2, dtype=np.float32), 1, FADE_S), 0.0)
    mix.apply((None, None, CLOSE_FADE_S), 0.0)
    mix.apply((np.zeros(SR, dtype=np.float32), 2, FADE_S), 0.0)
    assert len(mix.tail) == int(FADE_S * SR)


def test_back_does_not_play_choice(run):
    run(msg(1, 'HELLO'))
    d = run(close(1, choice_key='CHOICE_A', back=True))
    assert playing(d) is None


def test_generic_button_is_not_read_but_window_is(run):
    d = run(msg(1, 'HELLO'))
    assert playing(d) == 'HELLO'
    d = run(close(1, choice_key='UI_CONTINUE'), 0.3)
    assert playing(d) is None and d.outcomes['choice', 'pełne'] == 0


def test_objective_counter_only_after_first_read(run):
    args = lambda n: [{'i': 0, 'type': 'VariableInt', 'as_key': str(n), 'value': str(n)}]
    d = run({'ev': 'objective', 'key': 'GOAL_COUNT', 'prev_key': 'GOAL', 'args': args(3)}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_goal', 'f_three', 'f_of4']
    d = run(dt=2.0)
    d = run({'ev': 'objective', 'key': 'GOAL_COUNT', 'prev_key': 'GOAL_COUNT', 'args': args(3)}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_three', 'f_of4']


def test_story_uses_voice_of_speaking_hero(run):
    run({'ev': 'open', 'kind': 'story', 'id': 5, 'key': 'SAY'})
    d = run({'ev': 'shown', 'kind': 'story', 'id': 5, 'characters': [
        {'name_key': 'HERO_SYRUS_NAME', 'speaking': False}, {'name_key': 'HERO_BRYNN_NAME', 'speaking': True}]}, 0.4)
    assert [p[0] for p in d.current.u.pieces] == ['f_say_brynn']


def test_details_reads_name_and_description_and_stops_on_close(run):
    d = run({'ev': 'details', 'key': 'MAP_DESC', 'name_key': 'MAP_NAME'}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_map_name', 'f_map_desc']
    d = run({'ev': 'close', 'kind': 'details'}, 0.1)
    assert playing(d) is None


def test_details_newest_replaces_older(run):
    run({'ev': 'details', 'key': 'MAP_DESC', 'name_key': 'MAP_NAME'}, 1.0)
    d = run({'ev': 'details', 'key': 'GOAL'}, 0.1)
    assert playing(d) == 'GOAL'


def test_ability_tiles_read_name_and_description_in_turn_and_stop_on_close(run):
    """E16 (D101): kafelki zdolności w oknie ataku: nazwa i opis, kolejne kafelki po kolei; opis bez klucza po tekście."""
    tiles = [{'name_key': 'MAP_NAME', 'desc_key': 'MAP_DESC'}, {'desc': 'Znajdź klucz.'}]
    d = run({'ev': 'open', 'kind': 'ability', 'id': 7, 'items': tiles}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_map_name', 'f_map_desc'] and [it.key for it in d.queue] == ['?']
    d = run({'ev': 'close', 'kind': 'ability', 'id': 7}, 0.1)
    assert playing(d) is None and not d.queue


def test_defense_in_attack_window_reads_value_fragment_and_stops_on_close(run):
    """D102: obrona wroga z okna ataku gra nagranie wartości luki przypomnienia o obronie (przełącznik zdolności)."""
    d = run({'ev': 'open', 'kind': 'defense', 'id': 8, 'key': 'ENEMY_DEFEND_ZEALOT'}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_bandit'] and d.current.u.toggle == 'zdolnosci'
    d = run({'ev': 'close', 'kind': 'defense', 'id': 8}, 0.1)
    assert playing(d) is None
    d = run({'ev': 'open', 'kind': 'defense', 'id': 9, 'key': 'ENEMY_DEFEND_UNKNOWN'}, 0.1)
    assert d.outcomes['defense', 'brak_klucza'] == 1


def test_completed_feat_reads_header_and_reward_as_loot(run):
    """l14: okno ukończonego wyzwania czyta nagłówek i nagrodę jak listę łupu; zamknięcie zatrzymuje."""
    run.d.toggles['nagrody'] = True
    d = run({'ev': 'open', 'kind': 'feat', 'id': 5, 'name': 'Wyzwanie', 'reward': 'Do ekwipunku trafia: Złoto (15).',
             'replaced': False}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_feat', 'f_loot_head', 'f_gold', 'f_fifteen']
    assert d.outcomes['feat', 'pełne'] == 1
    d = run({'ev': 'close', 'kind': 'feat', 'id': 5}, 0.1)
    assert playing(d) is None
    d = run({'ev': 'open', 'kind': 'feat', 'id': 6, 'reward': 'Wyzwanie zmienione.', 'replaced': True}, 0.1)
    assert d.outcomes['feat', 'brak_klucza'] == 1      # UI_FEAT_REPLACED nie ma w bazie testowej


def test_feat_completion_is_announced_with_hero_and_name(run):
    """l16: w chwili ukończenia wyzwania lektor mówi nagłówek, imię bohatera i nazwę wyzwania."""
    run.d.toggles['nagrody'] = True
    d = run({'ev': 'feat_done', 'kind': 'feat_done', 'id': 3, 'feat': 'FEAT_X', 'desc_key': 'FEAT_X_DESC',
             'hero_key': 'HERO_KEHLI_NAME'}, 1.0)
    assert [p[0] for p in d.current.u.pieces] == ['f_feat', 'f_keli', 'f_map_name']
    d = run({'ev': 'feat_done', 'kind': 'feat_done', 'id': 4, 'desc_key': 'FEAT_Y_DESC'}, 10.0)
    assert d.outcomes['feat_done', 'częściowe'] == 1


def test_objective_waits_and_newest_replaces(run):
    run(msg(1, 'HELLO'))
    run({'ev': 'objective', 'key': 'GOAL'})
    d = run({'ev': 'objective', 'key': 'GOAL2'})
    assert playing(d) == 'HELLO' and [it.key for it in d.queue] == ['GOAL2']
    d = run(dt=1.1)
    assert playing(d) == 'GOAL2'


def test_queue_waits_for_settle_after_window_event(run):
    run({'ev': 'objective', 'key': 'GOAL'})
    run(msg(1, 'HELLO'), 0.0)
    run(close(1), 0.2)
    d = run(dt=0.1)
    assert playing(d) is None
    d = run(dt=D.SETTLE)
    assert playing(d) == 'GOAL'


def test_window_preempts_objective_which_requeues_once(run):
    d = run({'ev': 'objective', 'key': 'GOAL'}, 1.0)
    assert playing(d) == 'GOAL'
    d = run(msg(1, 'HELLO'), 0.1)
    assert playing(d) == 'HELLO' and [it.key for it in d.queue] == ['GOAL'] and d.queue[0].requeued
    run(msg(2, 'HELLO'), 1.5)
    d = run(dt=1.5)
    assert playing(d) == 'GOAL'
    d = run(msg(3, 'HELLO'), 0.1)
    assert not d.queue


def test_closed_activation_leaves_queue(run):
    run(msg(1, 'HELLO'))
    d = run({'ev': 'open', 'kind': 'activation', 'id': 7, 'key': 'ACT', 'args': [entity('ENEMY_BANDIT')]})
    assert [it.key for it in d.queue] == ['ACT']
    d = run(close(7, 'activation'))
    assert not d.queue


def test_toggle_off_stops_previous_window(run):
    run(msg(1, 'HELLO'))
    d = run(msg(2, 'LOOT', args=[{'type': 'RawText'}]), 0.2)
    assert playing(d) is None and d.outcomes['message', 'wyłączone'] == 1


def test_objective_already_read_in_window_is_skipped(run):
    run(msg(1, 'NEW_GOAL', args=[{'i': 0, 'type': 'LocalizationKey', 'as_key': 'GOAL'}]))
    d = run({'ev': 'objective', 'key': 'GOAL'}, 0.1)
    assert not d.queue and d.outcomes['objective', 'w_oknie'] == 1


def test_objective_text_read_in_window_is_skipped(run):
    """D102: okno „Zaktualizowano zadanie: <cel> (1/4)” ma cel w tekście, a nie w luce; zdarzenie celu nie gra."""
    run(msg(1, 'HELLO', text='Zaktualizowano zadanie: <b>Znajdź klucz!</b> (1/4)'))
    d = run({'ev': 'objective', 'key': 'GOAL', 'text': 'Znajdź klucz! (2/4)'}, 0.1)
    assert not d.queue and d.outcomes['objective', 'w_oknie'] == 1
    d = run({'ev': 'objective', 'key': 'GOAL2', 'text': 'Inny cel.'}, 0.1)
    assert [it.key for it in d.queue] == ['GOAL2']


def test_objective_queued_before_window_with_its_text_is_dropped(run):
    run(msg(1, 'HELLO'))
    run({'ev': 'objective', 'key': 'GOAL', 'text': 'Znajdź klucz!'}, 0.1)
    d = run(msg(2, 'HELLO', text='Zaktualizowano zadanie: Znajdź klucz!'), 0.1)
    assert playing(d) == 'HELLO' and not d.queue and d.outcomes['objective', 'w_oknie'] == 1
    run({'ev': 'objective', 'key': 'GOAL2', 'text': 'Znajdź drzwi!'}, 2.0)
    d = run(msg(3, 'HELLO', text='Zaktualizowano zadanie: Znajdź drzwi!'), 0.1)
    assert not d.queue          # cel, który już zaczął grać, nie wraca po przerwaniu


def test_partial_objective_dropped_by_window_keeps_counts_non_negative(run):
    """D103: cel bez wartości luki (wynik częściowe) zdjęty z kolejki przez okno nie psuje licznika pełnych."""
    run(msg(1, 'HELLO'))
    bad = [{'i': 0, 'type': 'VariableInt', 'as_key': '9', 'value': '9'}]
    d = run({'ev': 'objective', 'key': 'GOAL_COUNT', 'args': bad, 'text': 'Znajdź klucz (9/4)'}, 0.1)
    assert d.outcomes['objective', 'częściowe'] == 1
    d = run(msg(2, 'HELLO', text='Zaktualizowano zadanie: Znajdź klucz (9/4)'), 0.1)
    assert not d.queue and d.outcomes['objective', 'częściowe'] == 0 and d.outcomes['objective', 'pełne'] == 0
    assert d.outcomes['objective', 'w_oknie'] == 1

def test_scene_stops_everything(run):
    run(msg(1, 'HELLO'))
    run({'ev': 'objective', 'key': 'GOAL'})
    d = run({'ev': 'scene', 'name': 'x'})
    assert d.idle


def test_summary_coverage(run):
    run(msg(1, 'HELLO'))
    run(msg(2, 'CUTSCENE'))
    run(msg(3, 'NOPE'))
    run(msg(4, 'COUNT', args=[]))
    s = run.d.summary()
    assert s['windows'] == 3 and s['windows_audio'] == 1 and s['coverage'] == pytest.approx(1 / 3, abs=1e-3)
    assert {m['key'] for m in s['missing']} == {'NOPE', 'COUNT'}


def test_line_with_nothing_to_read_is_empty_not_missing(run):
    run(msg(1, 'HELLO'))
    d = run(msg(2, 'DOTS'), 0.2)
    s = d.summary()
    assert playing(d) is None and d.outcomes['message', 'pusta'] == 1
    assert s['windows_empty'] == 1 and s['windows_runtime_only'] == 0 and s['coverage_readable'] == 1.0


# ---------- konfiguracja ----------

def test_config_created_with_defaults_and_merged(tmp_path):
    f = tmp_path / 'c' / 'companion.toml'
    cfg = C.load(str(f))
    assert f.exists() and cfg['port'] == 47810 and all(cfg['toggles'][t] for t in C.TOGGLES)
    f.write_text('volume = 0.5\n[toggles]\nui = false\n', encoding='utf-8')
    cfg = C.load(str(f))
    assert cfg['volume'] == 0.5 and cfg['toggles']['ui'] is False and cfg['toggles']['cele'] is True and cfg['port'] == 47810


def test_config_paths_relative_to_settings_file(tmp_path):
    f = tmp_path / 'paczka' / 'ustawienia.toml'
    f.parent.mkdir()
    f.write_text('db = "dane/m1.sqlite"\naudio = "dane"\n[plugin]\nautostart = true\n', encoding='utf-8')
    cfg = C.load(str(f))
    assert cfg['db'] == str(tmp_path / 'paczka' / 'dane' / 'm1.sqlite') and cfg['audio'] == str(tmp_path / 'paczka' / 'dane')


# ---------- tryb paczki: start z pluginu (D59) ----------

def test_exit_reason_follows_game_and_plugin():
    clock = [0.0]
    link = A.Link(lambda: clock[0])
    assert A.exit_reason(link, 100.0, 0.0, None, 15, 120) is None
    assert A.exit_reason(link, 121.0, 0.0, None, 15, 120) == 'brak_pluginu'
    assert A.exit_reason(link, 5.0, 0.0, False, 15, 120) == 'gra_zamknieta'
    clock[0] = 10.0
    link.set(True)
    assert A.exit_reason(link, 500.0, 0.0, True, 15, 120) is None
    clock[0] = 20.0
    link.set(False)
    assert A.exit_reason(link, 30.0, 0.0, True, 15, 120) is None
    assert A.exit_reason(link, 36.0, 0.0, True, 15, 120) == 'rozlaczenie'
    assert A.exit_reason(link, 10_000.0, 0.0, None, None, None) is None


def test_second_server_on_busy_port_returns_none():
    srv = A.server(0)
    try:
        assert A.server(srv.getsockname()[1]) is None
    finally:
        srv.close()


def test_alive_for_own_and_finished_process():
    import subprocess
    import sys
    assert A.alive(os.getpid())
    p = subprocess.Popen([sys.executable, '-I', '-c', 'pass'])
    p.wait()
    assert not A.alive(p.pid)


def test_serve_exits_when_port_busy(lib, tmp_path):
    srv = A.server(0)
    try:
        cfg = {'port': srv.getsockname()[1], 'db': str(tmp_path / 'm1.sqlite'), 'audio': str(tmp_path), 'toggles': {}}
        assert A.run(cfg, audio=False, quiet=True, logs=str(tmp_path / 'logs')) is None
        assert not (tmp_path / 'logs').exists()
    finally:
        srv.close()


def test_serve_exits_without_plugin(lib, tmp_path):
    cfg = {'port': 0, 'db': str(tmp_path / 'm1.sqlite'), 'audio': str(tmp_path), 'toggles': {t: True for t in C.TOGGLES}}
    out = A.run(cfg, audio=False, quiet=True, logs=str(tmp_path / 'logs'), exit_if_no_client=0.5)
    assert out['reason'] == 'brak_pluginu' and os.path.dirname(out['log']) == str(tmp_path / 'logs')


def test_sound_test_key_is_complete_narration(lib):
    assert A.sample_key(lib) == 'HELLO'


def test_companion_module_help():
    import subprocess
    import sys
    r = subprocess.run([sys.executable, '-I', '-m', 'lektor.companion', '--help'], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0 and '--parent-pid' in r.stdout and '--test' in r.stdout
