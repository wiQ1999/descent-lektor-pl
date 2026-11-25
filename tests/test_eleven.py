"""E13 (D80): silnik ElevenLabs w lektor bez połączeń z siecią (atrapy odpowiedzi API)."""
import io
import json
import os
import sqlite3
import urllib.error

import pytest

from lektor import direction as D
from lektor import eleven, evaluate, paths, synth

TEXT = 'Rycerz otwiera ciężkie drzwi do piwnicy i schodzi po schodach.'


def fragments_db(path, rows):
    con = sqlite3.connect(path)
    con.execute('CREATE TABLE fragments (id TEXT PRIMARY KEY, voice TEXT, speed REAL, text TEXT, chars INTEGER, kind TEXT)')
    con.executemany('INSERT INTO fragments VALUES (?, ?, ?, ?, ?, ?)',
                    [(f, v, 1.2, TEXT, len(TEXT), 'line') for f, v in rows])
    con.commit()
    con.row_factory = sqlite3.Row
    return con


class Response(io.BytesIO):
    def __init__(self, body, headers):
        super().__init__(body)
        self.headers = headers


def test_engine_mapping():
    assert D.engine('adelynn') == 'elevenlabs' and D.engine('narrator') == 'omnivoice' and D.engine('brynn') == 'omnivoice'
    assert D.take_engine(1) == 'omnivoice' and D.take_engine(D.ELEVEN_TAKE0 + 1) == 'elevenlabs'
    # E13: 11, E14: 17 nowych (D95), D116: głos zastępczy Levirax w akcie 1
    assert len(D.ELEVEN_VOICES) == 29 and len(D.ELEVEN_VOICES_E14) == 17


def test_part_voice_only_in_prefixed_groups_of_release():
    """D116: Levirax w akcie 1 m4 czyta głos zastępczy ElevenLabs ze stylem i efektem; akt 2 i inne wydania bez zmian."""
    assert D.part_voice('levirax', 'a1_q10', 'm4') == 'levirax_e'
    assert D.part_voice('levirax', 'a2_q7', 'm4') == 'levirax' and D.part_voice('levirax', 'a1_q10', 'm3') == 'levirax'
    assert D.part_voice('narrator', 'a1_q10', 'm4') == 'narrator'
    assert D.engine('levirax_e') == 'elevenlabs' and D.engine('levirax') == 'omnivoice'
    assert D.FX['levirax_e'] == 'dragon_e' and D.ELEVEN_STYLE['levirax_e']['speed'] == 0.75


def test_jobs_split_between_engines(tmp_path):
    con = fragments_db(tmp_path / 'f.sqlite', [('a1', 'adelynn'), ('n1', 'narrator'), ('r1', 'ronan')])
    assert [(j[0], j[1], j[4]) for j in eleven.jobs(con)] == [('a1', 101, 1.0), ('r1', 101, 1.0)]
    assert [j[0] for j in synth.jobs(con)] == ['n1']
    assert list(eleven.jobs(con, retake={'r1': (102, 0.9), 'n1': (2, 1.1)})) == [('r1', 102, TEXT, 'ronan', 0.9)]
    assert list(eleven.jobs(con, voices=['adelynn']))[0][0] == 'a1'


def test_synthesize_request_and_retry():
    calls = []

    def opener(req, timeout):
        calls.append(req)
        if len(calls) == 1:
            raise urllib.error.HTTPError(req.full_url, 429, 'busy', {}, io.BytesIO(b'{}'))
        return Response(b'\x00\x01' * 10, {'Request-Id': 'r1', 'History-Item-Id': 'h1'})

    pcm, headers = eleven.synthesize('KEY', 'voice123', TEXT, 7, opener=opener, sleep=lambda s: None)
    assert pcm == b'\x00\x01' * 10 and headers == {'request-id': 'r1', 'history-item-id': 'h1'}
    req = calls[-1]
    assert req.full_url == 'https://api.elevenlabs.io/v1/text-to-speech/voice123?output_format=pcm_24000'
    assert 'KEY' not in req.full_url and req.get_header('Xi-api-key') == 'KEY'
    body = json.loads(req.data)
    assert body == {'text': TEXT, 'model_id': 'eleven_v4', 'seed': 7, 'voice_settings': {
        'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.0, 'use_speaker_boost': True, 'speed': 1.0}}


def test_synthesize_error_hides_key():
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, 'no', {}, io.BytesIO(b'{"detail": "invalid"}'))

    with pytest.raises(eleven.ElevenError) as err:
        eleven.synthesize('SECRETKEY', 'v', TEXT, 1, opener=opener, sleep=lambda s: None)
    assert '401' in str(err.value) and 'SECRETKEY' not in str(err.value)


def test_cost_from_history_header_or_rate():
    def opener(req, timeout):
        assert req.full_url.endswith('/v1/history/h1')
        return Response(json.dumps({'character_count_change_from': 100, 'character_count_change_to': 128}).encode(), {})

    assert eleven.history_credits('K', 'h1', opener=opener, sleep=lambda s: None) == 28
    assert eleven.history_credits('K', None) is None
    assert eleven.measure(TEXT, {}, 28) == (28, 'history', None)
    assert eleven.measure(TEXT, {'character-cost': '27'}, None) == (27, 'header', None)
    assert eleven.measure(TEXT, {}, None) == (round(len(TEXT) * eleven.RATE), 'rate', 'estimated')


def test_usage_record_has_no_text():
    sub = {'character_limit': 1000, 'tier': 'creator', 'next_character_count_reset_unix': 1794700800}
    r = eleven.usage_record(TEXT, 'adelynn', {'request-id': 'r1'}, 28, 'history', None, 28, sub,
                            os.path.join(paths.AUDIO, 'takes', 'x.wav'))
    assert TEXT not in json.dumps(r, ensure_ascii=False)
    assert r['text_len'] == len(TEXT) and len(r['text_sha1']) == 40 and r['voice_id'] == D.ELEVEN_VOICES['adelynn']
    assert r['tool'] == 'lektor_eleven' and r['pct_call'] == 2.8 and r['period_reset'].endswith('Z')
    assert r['audio_file'].startswith('analysis/work/audio/')


def test_write_wav_and_key(tmp_path, monkeypatch):
    assert eleven.write_wav(str(tmp_path / 'a.wav'), b'\x00\x00' * 24000) == 1.0
    monkeypatch.setattr(paths, 'ROOT', str(tmp_path))
    assert eleven.api_key() is None
    (tmp_path / eleven.KEY_FILE).write_text('# x\nELEVENLABS_API_KEY="abc"\n', encoding='utf-8')
    assert eleven.api_key() == 'abc'


def test_expected_tempo_per_engine():
    assert evaluate.expected_cps(1.2) == pytest.approx(evaluate.REF_CPS * 1.2)
    assert evaluate.expected_cps(1.0, 'elevenlabs') == evaluate.ELEVEN_CPS


def ev(fid, take, voice, asr=TEXT, sim=0.9):
    return {'fragment': fid, 'take': take, 'voice': voice, 'speed': 1.0 if take > 100 else 1.2, 'chars': len(TEXT),
            'asr': asr, 'speech_s': 4.0, 'sim': sim, 'cps': 14.0, 'cps_ratio': 1.0, 'end_rms': 0.0, 'end_gap': 0.3,
            'pause': 0.2}


def test_select_prefers_engine_of_voice(tmp_path, monkeypatch):
    fragments_db(tmp_path / 'm2.sqlite', [('a1', 'adelynn'), ('a2', 'adelynn'), ('a3', 'adelynn'), ('a4', 'adelynn'),
                                          ('n1', 'narrator')]).close()
    monkeypatch.setattr(paths, 'DB', str(tmp_path / 'm2.sqlite'))
    monkeypatch.setattr(paths, 'AUDIO', str(tmp_path))
    cut = 'Rycerz otwiera ciężkie drzwi do piwnicy'
    rows = [ev('a1', 1, 'adelynn'), ev('a1', 101, 'adelynn', sim=0.85),    # EL wygrywa z OmniVoice o wyższej barwie
            ev('a2', 1, 'adelynn'),                                       # bez EL: zostaje OmniVoice, bez ponownego
            ev('a3', 1, 'adelynn'), ev('a3', 101, 'adelynn', asr=cut),    # EL ucięty: ponowne podejście EL wolniej
            ev('n1', 1, 'narrator', asr=cut), ev('n1', 101, 'narrator')]  # narrator: podejście EL się nie liczy
    with open(tmp_path / 'evals.jsonl', 'w', encoding='utf-8') as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    inherited = {'a1': {'take': 2, 'voice': 'adelynn', 'speed': 1.2, 'problems': []},     # OmniVoice z M1: EL ma pierwszeństwo
                 'a4': {'take': 101, 'voice': 'adelynn', 'speed': 1.0, 'problems': []}}   # EL z M1: przejęty
    (tmp_path / 'inherited.json').write_text(json.dumps(inherited), encoding='utf-8')
    choice, retake = evaluate.select()
    assert choice['a1']['take'] == 101 and choice['a2']['take'] == 1 and choice['a4']['take'] == 101
    assert choice['a3']['take'] == 101 and 'koncowka' in choice['a3']['problems']
    assert retake == {'a3': [102, 0.9], 'n1': [2, 1.1]}
    assert choice['n1']['take'] == 1 and choice['n1']['takes'] == 1


def test_select_rejected_takes_get_retake(tmp_path, monkeypatch):
    """E21 (D115): podejście odrzucone w odsłuchu (rejected.json) przegrywa i dostaje ponowne podejście."""
    fragments_db(tmp_path / 'm4.sqlite', [('w1', 'narrator'), ('w2', 'narrator')]).close()
    monkeypatch.setattr(paths, 'DB', str(tmp_path / 'm4.sqlite'))
    monkeypatch.setattr(paths, 'AUDIO', str(tmp_path))
    rows = [ev('w1', 1, 'narrator', sim=0.95), ev('w2', 1, 'narrator'), ev('w2', 2, 'narrator', sim=0.89)]
    with open(tmp_path / 'evals.jsonl', 'w', encoding='utf-8') as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    (tmp_path / 'rejected.json').write_text(json.dumps({'w1': [1], 'w2': [1]}), encoding='utf-8')
    choice, retake = evaluate.select()
    assert choice['w1']['problems'] == ['odsluch'] and retake['w1'] == [2, 1.2]
    assert choice['w2']['take'] == 2 and not choice['w2']['problems'] and 'w2' not in retake


def test_levirax_style_tags_and_settings(tmp_path, monkeypatch):
    # E21 (D115): Levirax czyta głos ze znacznikami wdechu, wolniej i z własnymi ustawieniami
    t = eleven.tagged('levirax', 'Dość. Idźcie stąd… teraz. Już.')
    assert t == '[long, deep inhale] [slowly, booming] Dość. [deep inhale] Idźcie stąd… teraz. Już.'
    assert eleven.tagged('ronan', TEXT) == TEXT
    vid, tag, fx = D.RECAST_LATER['levirax']
    assert 'levirax' not in D.ELEVEN_VOICES and 'levirax' not in D.FX and tag == 'D115' and fx == 'dragon_e'
    monkeypatch.setitem(D.ELEVEN_VOICES, 'levirax', vid)     # po włączeniu przy kolejnym generowaniu
    con = fragments_db(tmp_path / 'f.sqlite', [('l1', 'levirax')])
    assert [j[4] for j in eleven.jobs(con)] == [0.75]
    assert eleven.voice_settings('levirax') == {'stability': 0.3, 'style': 0.3} and eleven.voice_settings('ronan') == {}
    calls = []

    def opener(req, timeout):
        calls.append(json.loads(req.data))
        return Response(b'\x00\x01', {})

    eleven.synthesize('K', 'v', TEXT, 1, 0.65, opener=opener, settings=eleven.voice_settings('levirax'))
    vs = calls[0]['voice_settings']
    assert vs['speed'] == 0.7 and vs['stability'] == 0.3 and vs['style'] == 0.3 and vs['similarity_boost'] == 0.75
