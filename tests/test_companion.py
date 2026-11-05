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
from lektor.companion.library import LIST_GAP, LOOT, Library
from lektor.companion.player import NullPlayer

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
    'f_map_name': ('Cena wiedzy', 0.25),
    'f_map_desc': ('Stara wieża czeka.', 0.5),
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
    ('CUTSCENE', 'narracja', 'narracja', 0, 'Przerywnik.'),
    ('ACT', 'aktywacje', 'aktywacje', 1, 'Wróg atakuje {0}'),
    ('GOAL_COUNT', 'cel_misji', 'cele', 1, 'Znajdź klucz ({0}/4)'),
    ('UI_CONTINUE', 'opcja_wyboru', 'okna_wyboru', 1, 'Kontynuuj'),
    ('SAY', 'dialog', 'dialogi', 1, 'Ruszajmy.'),
    ('SAY#brynn', 'dialog', 'dialogi', 1, 'Ruszajmy.'),
    ('TREASURE', 'system_nagroda', 'nagrody', 1, '{0} {1}'),
    ('MAP_NAME', 'opis_misji', 'opis_misji', 1, 'Cena wiedzy'),
    ('MAP_DESC', 'opis_misji', 'opis_misji', 1, 'Stara wieża czeka.'),
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
]
VALUES = [
    ('SPAWN', 0, 'ENEMY_BANDIT', 'f_bandit'), ('SPAWN', 0, 'ENEMY_WITCH', 'f_witch'),
    ('SPAWN_MULTI', -1, 'ENEMY_BANDIT', 'f_bandit'), ('SPAWN_MULTI', -1, 'ENEMY_WITCH', 'f_witch'),
    ('COUNT', 0, '3', 'f_three'),
    ('NEW_GOAL', 0, 'GOAL', None),
    ('ACT', 0, 'ENEMY_BANDIT', 'f_bandit'),
    ('GOAL_COUNT', 0, '3', 'f_three'),
    (LOOT, 0, 'do ekwipunku trafia', 'f_loot_head'), (LOOT, 0, 'złoto', 'f_gold'), (LOOT, 0, '15', 'f_fifteen'),
    (LOOT, 0, 'mikstura zdrowia', 'f_potion'),
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
