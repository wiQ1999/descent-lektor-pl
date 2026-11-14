"""Styl klonu w generowaniu (D94), kolejność gry i postęp E14 (D95). Bez modelu, GPU i sieci."""
import json
import sqlite3

from lektor import build, paths, progress, synth
from lektor import direction as D


def fragments_db(rows):
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE fragments (id TEXT PRIMARY KEY, voice TEXT, speed REAL, text TEXT, chars INTEGER, kind TEXT)')
    con.executemany('INSERT INTO fragments VALUES (?, ?, ?, ?, ?, ?)', [(*r, len(r[3]), 'text') for r in rows])
    return con


def test_styled_speed():
    assert synth.styled_speed(1.2, {'style': {'speed': 0.85}}) == 1.02
    assert synth.styled_speed(None, {'style': {'speed': 0.85}}) == 0.85
    assert synth.styled_speed(1.2, {'sha': 'x'}) == 1.2 and synth.styled_speed(None, None) is None


def test_jobs_apply_style_to_fresh_takes_and_follow_order():
    con = fragments_db([('a', 'levirax', 1.2, 'Pierwsze zdanie.'), ('b', 'narrator', None, 'Drugie zdanie.'),
                        ('c', 'levirax', 1.2, 'Trzecie zdanie.')])
    refs = {'levirax': {'style': {'speed': 0.85, 'instruct': 'female'}}}
    order = {'c': (1, 0), 'b': (1, 1), 'a': (2, 0)}
    got = list(synth.jobs(con, refs=refs, order=order))
    assert [(j[0], j[4]) for j in got] == [('c', 1.02), ('b', None), ('a', 1.02)]
    # Ponowne podejście ma tempo z zapisanego podejścia, z już uwzględnionym stylem.
    assert list(synth.jobs(con, retake={'a': (2, 0.97)}, refs=refs)) == [('a', 2, 'Pierwsze zdanie.', 'levirax', 0.97)]


def test_voice_tag_includes_style_only_when_present():
    refs = {'narrator': {'sha': 'abcdef1234'}, 'levirax': {'sha': '0123456789', 'style': {'speed': 0.85}}}
    assert build.voice_tag('narrator', refs) == 'narrator@abcdef12'
    assert build.voice_tag('levirax', refs) == 'levirax@01234567~{"speed": 0.85}'
    assert build.voice_tag('magrit', refs) == 'magrit'


def test_load_state_merges_logs_and_skips_broken_line(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'AUDIO', str(tmp_path))
    (tmp_path / 'takes.jsonl').write_text(json.dumps({'fragment': 'a', 'take': 1}) + '\n{"fragment": "b", "ta',
                                          encoding='utf-8')
    (tmp_path / 'takes_eleven.jsonl').write_text(json.dumps({'fragment': 'c', 'take': 101, 'credits': 40}) + '\n',
                                                 encoding='utf-8')
    state = synth.load_state()
    assert set(state) == {('a', 1), ('c', 101)} and progress.spent_credits(state) == 40


def test_game_order_acts_then_common_parts():
    groups = ['system', 'a2_q1', 'events', 'a1_q2', 'travel_act2', 'a1_sq1', 'city', 'a1_q10', 'gear']
    assert sorted(groups, key=progress.rank) == ['a1_q2', 'a1_q10', 'a1_sq1', 'city', 'a2_q1', 'travel_act2',
                                                 'events', 'gear', 'system']
    assert [progress.act(g) for g in ('town', 'town_act2', 'enemies')] == [1, 2, 3]


def test_needed_takes_by_engine():
    assert progress.needed('brynn') == [1, 2, 3]
    assert progress.needed('narrator') == [1]
    assert progress.needed(next(iter(D.ELEVEN_VOICES))) == [D.ELEVEN_TAKE0 + 1]


def test_m4_inherits_own_engine_and_adopts_unchosen_takes(tmp_path, monkeypatch):
    """D107: m4 przejmuje wybory t1 i m3 tylko w silniku głosu (nv_* w t1 z OmniVoice odpada), a podejścia
    OmniVoice z m3 bez wyboru trafiają do takes.jsonl m4 do oceny."""
    monkeypatch.setattr(paths, 'WORK', str(tmp_path))

    def release(name, choice=None, takes=()):
        d = tmp_path / 'audio' / name
        (d / 'takes').mkdir(parents=True)
        (d / 'choice.json').write_text(json.dumps(choice or {}), encoding='utf-8')
        (d / 'takes.jsonl').write_text(''.join(json.dumps(t) + '\n' for t in takes), encoding='utf-8')
        for f, c in (choice or {}).items():
            (d / 'takes' / ('%s_t%d.wav' % (f, c['take']))).write_bytes(b'x')
        for t in takes:
            (d / 'takes' / ('%s_t%d.wav' % (t['fragment'], t['take']))).write_bytes(b'x')

    release('t1', {'n': {'take': 1, 'voice': 'narrator'}, 'v': {'take': 1, 'voice': 'nv_bandyta'}})
    release('m3', {'n': {'take': 2, 'voice': 'narrator'}, 'x': {'take': 1, 'voice': 'syrus'}},
            [{'fragment': 'u', 'take': 1, 'voice': 'syrus'}, {'fragment': 'x', 'take': 1, 'voice': 'syrus'}])
    paths.use('m4')
    try:
        (tmp_path / 'audio' / 'm4').mkdir(parents=True)
        monkeypatch.setattr(paths, 'AUDIO', str(tmp_path / 'audio' / 'm4'))
        con = fragments_db([('n', 'narrator', 1.4, 'a'), ('v', 'nv_bandyta', None, 'b'), ('x', 'syrus', None, 'c'),
                            ('u', 'syrus', None, 'd')])
        done = synth.inherit(con)
        assert done == {'n': {'take': 1, 'voice': 'narrator'}, 'x': {'take': 1, 'voice': 'syrus'}}
        assert D.engine('nv_bandyta') == 'elevenlabs'
        assert synth.adopt(con, done) == 1 and ('u', 1) in synth.load_state()
        assert synth.adopt(con, done) == 0
    finally:
        paths.use('m1')
