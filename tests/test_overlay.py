"""Sterowanie lektorem z gry (próba nakładki): tempo, wyciszenie, powtórka, stan dla pluginu, ustawienia i zgłoszenia."""
import json
import os
import socket
import tomllib

import numpy as np
import pytest

from lektor.companion import app as A
from lektor.companion import config as C
from lektor.companion import control as K
from test_companion import SR, close, entity, lib, msg, run   # noqa: F401 (fikstury)


def tone(sec, f=220.0):
    t = np.arange(int(sec * SR)) / SR
    return (0.3 * np.sin(2 * np.pi * f * t)).astype(np.float32)


@pytest.mark.parametrize('rate', [0.8, 1.3, 1.6])
def test_stretch_changes_length_not_pitch(rate):
    y = tone(2.0)
    out = K.stretch(y, rate, SR)
    assert abs(len(out) - len(y) / rate) <= 1
    body = out[SR // 10:-SR // 10]
    spec = np.abs(np.fft.rfft(body))
    peak = np.argmax(spec) * SR / len(body)
    assert abs(peak - 220.0) < 5.0
    assert np.max(np.abs(out)) < 0.4


def test_stretch_identity_and_short_audio():
    y = tone(0.02)
    assert K.stretch(y, 1.0, SR) is y and K.stretch(y, 1.4, SR) is y


def test_clamp_tempo_steps_and_limits():
    assert K.clamp_tempo(1.04) == 1.0 and K.clamp_tempo(1.26) == 1.3
    assert K.clamp_tempo(0.1) == K.TEMPO_MIN and K.clamp_tempo(3) == K.TEMPO_MAX


def test_set_setting_keeps_comments_and_adds_missing(tmp_path):
    f = tmp_path / 'ustawienia.toml'
    f.write_text('# opis\nvolume = 1.0   # głośność\n\n[toggles]\nnarracja = true    # opisy\n\n[plugin]\nautostart = true\n',
                 encoding='utf-8')
    K.set_setting(str(f), 'volume', 0.7)
    K.set_setting(str(f), 'tempo', 1.3)
    K.set_setting(str(f), 'narracja', False, 'toggles')
    K.set_setting(str(f), 'dialogi', False, 'toggles')
    text = f.read_text(encoding='utf-8')
    assert 'volume = 0.7   # głośność' in text and 'narracja = false    # opisy' in text
    cfg = tomllib.loads(text)
    assert cfg['tempo'] == 1.3 and cfg['toggles'] == {'narracja': False, 'dialogi': False}
    assert cfg['plugin'] == {'autostart': True}


def test_config_has_tempo_and_keys(tmp_path):
    cfg = C.load(str(tmp_path / 'c.toml'))
    assert cfg['tempo'] == 1.0 and cfg['skroty']['zglos'] == 'Ctrl+B'
    assert cfg['podsumowanie'] == {'statystyki': True}


def test_tempo_shortens_next_line_and_notice(run):
    d = run.d
    assert d.control('szybciej') == ('tempo', None) and d.tempo == 1.1
    d.control('tempo', 1.5)
    run(msg(1, 'HELLO'))
    assert abs(d.seconds[d.current.token] - 1.0 / 1.5) < 0.01
    assert d.state()['notice']['text'] == 'Tempo lektora 1,5×'
    d.control('tempo', 9)
    assert d.tempo == K.TEMPO_MAX


def test_mute_stops_and_keeps_history(run):
    run(msg(1, 'HELLO'))
    d = run.d
    d.control('wycisz')
    assert d.current is None and d.muted
    run(close(1), 0.1)
    run(msg(2, 'SPAWN', args=[entity('ENEMY_BANDIT')]), 0.1)
    assert d.current is None
    hist = d.state()['history']
    assert [h['key'] for h in hist] == ['SPAWN', 'HELLO'] and hist[0]['muted'] and not hist[1]['muted']


def test_repeat_last_survives_close_but_not_new_window(run):
    run(msg(1, 'HELLO'))
    d = run(close(1), 0.1)
    assert d.current is None
    d.control('powtorz')
    assert d.current.src == 'repeat' and d.current.key == 'HELLO'
    run(close(1), 0.1)
    assert d.current is not None
    run(msg(2, 'SPAWN', args=[entity('ENEMY_BANDIT')]), 0.1)
    assert d.current.key == 'SPAWN'
    assert [h['key'] for h in d.state()['history']] == ['SPAWN', 'HELLO']     # powtórka nie dubluje historii


def test_repeat_from_history_and_cut(run):
    run(msg(1, 'HELLO'))
    first = run.d.current.token
    d = run(msg(2, 'SPAWN', args=[entity('ENEMY_BANDIT')]), 0.1)
    d.control('powtorz', first)
    assert d.current.key == 'HELLO'
    d.control('utnij')
    assert d.current is None and d.state()['notice']['text'] == 'Ucięto kwestię'


def test_state_shows_speaker_progress_and_missing(run):
    run(msg(1, 'HELLO'))
    run(None, 0.4)
    st = run.d.state()
    assert st['now']['speaker'] == 'Narrator' and st['now']['text'] == 'Witaj w gospodzie.'
    assert 0.3 <= st['now']['elapsed'] <= 0.5 and st['now']['seconds'] == 1.0
    run(msg(2, 'NO_SUCH_KEY'), 0.1)
    assert run.d.state()['missing'] == 1


def test_remote_saves_settings_and_writes_report(run, tmp_path):
    f = tmp_path / 'ustawienia.toml'
    f.write_text('volume = 1.0\n\n[toggles]\nnarracja = true\n', encoding='utf-8')
    log = A.Log(str(tmp_path / 'logs' / 'c.jsonl'))
    d = run.d
    d.toggles['narracja'] = True
    r = A.Remote({'file': str(f), 'skroty': K.KEYS}, d, A.Link(), log, str(tmp_path / 'logs'))
    assert r.handle({'ev': 'control', 'cmd': 'szybciej'}, 1.0)
    assert r.handle({'ev': 'control', 'cmd': 'przelacznik', 'value': {'name': 'narracja', 'on': False}}, 1.0)
    assert r.handle({'ev': 'control', 'cmd': 'statystyki', 'value': False}, 1.0)
    cfg = tomllib.loads(f.read_text(encoding='utf-8'))
    assert cfg['tempo'] == 1.1 and cfg['toggles']['narracja'] is False
    assert cfg['podsumowanie'] == {'statystyki': False} and d.state()['stats'] is False
    d.toggles['narracja'] = True
    assert not r.handle(msg(1, 'HELLO'), run.clock())
    d.handle(msg(1, 'HELLO'))
    r.handle({'ev': 'report', 'category': 'wymowa', 'token': d.current.token, 'shot': 'x/ekran.png'}, run.clock())
    rep = tmp_path / 'zgloszenia'
    [name] = os.listdir(rep)
    data = json.loads((rep / name / 'zgloszenie.json').read_text(encoding='utf-8'))
    assert data['kategoria'] == 'wymowa' and data['kwestia']['resolved'] == 'HELLO'
    assert data['kwestia']['fragments'][0]['file'] == 'final/f_hello.wav' and data['zrzut'] == 'ekran.png'
    assert [e['key'] for e in data['zdarzenia_pluginu']] == ['HELLO']
    out = r.message(run.clock())
    assert out['ev'] == 'state' and out['reports'] == 1 and out['keys']['menu'] == 'Ctrl+L'
    log.close()


def test_link_sends_state_line_to_plugin():
    srv = A.server(0)
    try:
        link = A.Link()
        client = socket.create_connection(srv.getsockname())
        conn, _ = srv.accept()
        link.set(True, conn)
        assert link.send({'ev': 'state', 'tempo': 1.2})
        client.settimeout(2)
        assert json.loads(client.makefile('rb').readline()) == {'ev': 'state', 'tempo': 1.2}
        link.set(False)
        assert not link.send({'ev': 'state'})
        client.close()
        conn.close()
    finally:
        srv.close()
