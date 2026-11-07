import io
import json
import time
import urllib.error

import pytest

import common
import usage_hook as H
from conftest import KEY

TEXT = 'Zdanie testowe  z ogonkami: zażółć gęślą jaźń.'
RESET = 1796083200


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    monkeypatch.setattr(H, 'HISTORY_RETRY_S', 0)


def sub(count=1000):
    return {'tier': 'creator', 'character_count': count, 'character_limit': 100000,
            'next_character_count_reset_unix': RESET}


def item(request='r1', voice='v1', cost=46, text=TEXT, date=None):
    return {'history_item_id': 'h-' + request, 'request_id': request, 'date_unix': date or int(time.time()),
            'character_count_change_from': 1000, 'character_count_change_to': 1000 + cost, 'voice_id': voice,
            'voice_name': 'Adam', 'model_id': 'eleven_multilingual_v2', 'text': text, 'source': 'TTS'}


def event(name='PostToolUse', tool='text_to_speech', **extra):
    data = {'session_id': 's1', 'tool_use_id': 'toolu_1', 'hook_event_name': name,
            'tool_name': 'mcp__elevenlabs__' + tool, 'tool_input': {'text': TEXT, 'voice_id': 'v1'}}
    data.update(extra)
    return data


def api(monkeypatch, subs=(), history=()):
    """Atrapa API: kolejne odpowiedzi konta, stała lista historii. Wyjątek w `subs` udaje awarię."""
    subs = list(subs)

    def get(path, key):
        assert key == KEY
        if path == common.SUBSCRIPTION:
            answer = subs.pop(0)
        else:
            answer = {'history': list(history)}
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(common, 'get_json', get)


def run(monkeypatch, capsys, mode, data):
    raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
    monkeypatch.setattr('sys.stdin', io.TextIOWrapper(io.BytesIO(raw), encoding='cp1250'))
    monkeypatch.setattr('sys.argv', ['usage_hook.py', mode])
    assert H.main() == 0
    return capsys.readouterr().out


def records():
    return common.read_log()


def errors():
    return common.ERRORS.read_text(encoding='utf-8') if common.ERRORS.exists() else ''


def cycle(monkeypatch, capsys, subs, history, data=None):
    api(monkeypatch, subs, history)
    data = data or event()
    run(monkeypatch, capsys, 'pre', dict(data, hook_event_name='PreToolUse'))
    return run(monkeypatch, capsys, 'post', data)


def test_history_match_gives_cost_and_percentages(box, monkeypatch, capsys):
    response = [{'type': 'text', 'text': 'Success. File saved as: %s. Voice used: Adam' % (box / 'audio' / 'tts_1.mp3')}]
    out = cycle(monkeypatch, capsys, [sub(1000), sub(1046)], [item()], event(tool_response=response))
    [r] = records()
    assert (r['credits'], r['method'], r['flag']) == (46, 'history', None)
    assert (r['credits_history'], r['credits_delta']) == (46, 46)
    assert r['pct_call'] == 0.046 and r['pct_period'] == 1.046 and r['used_period'] == 1046
    assert r['period_reset'] == common.unix_to_iso(RESET)
    assert r['audio_file'] == 'audio/tts_1.mp3'
    context = json.loads(out)['hookSpecificOutput']
    assert context['hookEventName'] == 'PostToolUse'
    assert context['additionalContext'].startswith('ElevenLabs: 46 kr. (0,05% limitu); w okresie 1,05% (1 046 / 100 000), reset')
    assert not list(common.PENDING.glob('*.json'))


def test_history_ignores_other_text_voice_and_old_items(box, monkeypatch, capsys):
    old = int(time.time()) - 3600
    cycle(monkeypatch, capsys, [sub(1000), sub(1046)],
          [item('a', text='Inne zdanie'), item('b', voice='v2'), item('c', date=old)])
    [r] = records()
    assert (r['credits'], r['method'], r['request_id']) == (46, 'subscription_delta', None)


def test_whitespace_does_not_break_match():
    found = H.match_history([item(text=' '.join(TEXT.split()))], {'text': TEXT}, time.time(), time.time(), set())
    assert found['request_id'] == 'r1'


def test_voice_name_match_ignores_case():
    assert H.match_history([item()], {'text': TEXT, 'voice_name': 'ADAM'}, time.time(), time.time(), set())
    assert not H.match_history([item()], {'text': TEXT, 'voice_name': 'Bella'}, time.time(), time.time(), set())


def test_logged_request_is_not_matched_twice(box, monkeypatch, capsys):
    cycle(monkeypatch, capsys, [sub(1000), sub(1046)], [item('r1')])
    cycle(monkeypatch, capsys, [sub(1046), sub(1092)], [item('r2'), item('r1')], event(tool_use_id='toolu_2'))
    assert [r['request_id'] for r in records()] == ['r1', 'r2']
    cycle(monkeypatch, capsys, [sub(1092), sub(1138)], [item('r1')], event(tool_use_id='toolu_3'))
    assert records()[-1]['method'] == 'subscription_delta'


def test_mismatch_keeps_both_values(box, monkeypatch, capsys):
    cycle(monkeypatch, capsys, [sub(1000), sub(1100)], [item(cost=46)])
    [r] = records()
    assert (r['credits'], r['credits_history'], r['credits_delta'], r['flag']) == (46, 46, 100, 'mismatch')


def test_counter_lag_is_not_a_mismatch_and_period_uses_history(box, monkeypatch, capsys):
    cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [item(cost=46)])
    [r] = records()
    assert (r['credits'], r['credits_delta'], r['flag']) == (46, 0, None)
    assert r['used_period'] == 1046 and r['pct_period'] == 1.046


def test_counter_lag_without_history_is_not_zero_cost(box, monkeypatch, capsys):
    out = cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [])
    [r] = records()
    assert (r['credits'], r['credits_delta'], r['flag']) == (None, 0, 'unmeasured')
    assert 'nie zmierzono' in json.loads(out)['hookSpecificOutput']['additionalContext']


def test_dialogue_item_matches_by_text_and_voice(box, monkeypatch, capsys):
    entry = item()
    entry.update(text=None, voice_id=None, voice_name=None,
                 dialogue=[{'text': ' '.join(TEXT.split()), 'voice_id': 'v1', 'voice_name': 'Bella'}])
    cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [entry])
    [r] = records()
    assert (r['credits'], r['method'], r['voice_id'], r['voice_name']) == (46, 'history', 'v1', 'Bella')


def test_dialogue_item_with_other_voice_is_skipped():
    entry = item()
    entry.update(text=None, voice_id=None, dialogue=[{'text': TEXT, 'voice_id': 'v2'}])
    assert not H.match_history([entry], {'text': TEXT, 'voice_id': 'v1'}, time.time(), time.time(), set())


def test_history_is_asked_again_when_item_is_late(box, monkeypatch, capsys):
    pages = [[], [], [item()]]
    answers = [sub(1000), sub(1046)]

    def get(path, key):
        return answers.pop(0) if path == common.SUBSCRIPTION else {'history': pages.pop(0)}

    monkeypatch.setattr(common, 'get_json', get)
    run(monkeypatch, capsys, 'pre', event('PreToolUse'))
    run(monkeypatch, capsys, 'post', event())
    assert records()[0]['method'] == 'history' and not pages


def test_network_failure_writes_unmeasured_record_and_error(box, monkeypatch, capsys):
    down = urllib.error.URLError('brak sieci')
    api(monkeypatch, [down, down], [])
    monkeypatch.setattr(H, 'HISTORY_PATH', common.SUBSCRIPTION)
    run(monkeypatch, capsys, 'pre', event('PreToolUse'))
    api(monkeypatch, [down, down], [])
    out = run(monkeypatch, capsys, 'post', event())
    [r] = records()
    assert (r['credits'], r['method'], r['flag']) == (None, None, 'unmeasured')
    assert 'URLError' in errors()
    assert 'nie zmierzono' in json.loads(out)['hookSpecificOutput']['additionalContext']


def test_free_tool_leaves_no_trace(box, monkeypatch, capsys):
    for tool in ('check_subscription', 'list_models', 'get_voice', 'search_voices', 'play_audio'):
        for mode in ('pre', 'post'):
            assert run(monkeypatch, capsys, mode, event(tool=tool)) == ''
    assert not common.LOG.exists() and errors() == ''


def test_missing_key_keeps_record_without_network(box, monkeypatch, capsys):
    (box / common.KEY_FILE).unlink()
    run(monkeypatch, capsys, 'pre', event('PreToolUse'))
    run(monkeypatch, capsys, 'post', event())
    assert records()[0]['flag'] == 'unmeasured'
    assert 'Brak klucza' in errors()


def test_failed_tool_uses_counter_only(box, monkeypatch, capsys):
    failure = event('PostToolUseFailure', error='Błąd: ' + TEXT)
    out = cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [item()], failure)
    [r] = records()
    assert (r['credits'], r['method'], r['flag']) == (0, 'subscription_delta', 'tool_error')
    assert json.loads(out)['hookSpecificOutput']['hookEventName'] == 'PostToolUseFailure'


def test_tool_error_inside_response(box, monkeypatch, capsys):
    cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [], event(tool_response={'isError': True, 'content': []}))
    assert records()[0]['flag'] == 'tool_error'


def test_tool_without_history_uses_counter(box, monkeypatch, capsys):
    data = event(tool='text_to_voice', tool_input={'voice_description': 'Niski głos'})
    cycle(monkeypatch, capsys, [sub(1000), sub(1300)], [], data)
    [r] = records()
    assert (r['tool'], r['credits'], r['method'], r['text_len']) == ('text_to_voice', 300, 'subscription_delta', 10)


def test_voice_design_without_counter_move_uses_rate(box, monkeypatch, capsys):
    data = event(tool='text_to_voice', tool_input={'voice_description': 'Niski głos', 'text': TEXT})
    out = cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [], data)
    [r] = records()
    assert (r['credits'], r['method'], r['flag']) == (len(TEXT), 'rate', None)
    assert 'flaga' not in out


def test_voice_design_ignores_counter_moved_by_other_calls(box, monkeypatch, capsys):
    data = event(tool='text_to_voice', tool_input={'voice_description': 'Niski głos', 'text': TEXT})
    cycle(monkeypatch, capsys, [sub(1000), sub(1733)], [], data)
    [r] = records()
    assert (r['credits'], r['credits_delta'], r['method']) == (len(TEXT), 733, 'rate')


def test_voice_design_without_text_stays_unmeasured(box, monkeypatch, capsys):
    data = event(tool='text_to_voice', tool_input={'voice_description': 'Niski głos'})
    cycle(monkeypatch, capsys, [sub(1000), sub(1000)], [], data)
    [r] = records()
    assert (r['credits'], r['flag']) == (None, 'unmeasured')


def test_post_without_pre_still_records(box, monkeypatch, capsys):
    api(monkeypatch, [sub(1046)], [item()])
    run(monkeypatch, capsys, 'post', event())
    [r] = records()
    assert (r['credits'], r['credits_delta'], r['flag']) == (46, None, None)


def test_old_pending_entries_are_removed(box, monkeypatch, capsys):
    common.PENDING.mkdir(parents=True)
    old = common.PENDING / 'stary.json'
    old.write_text('{}', encoding='utf-8')
    monkeypatch.setattr(H, 'PENDING_MAX_AGE_S', -1)
    H.prune_pending()
    assert not old.exists()


def test_bad_input_never_blocks(box, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.TextIOWrapper(io.BytesIO(b'nie json'), encoding='utf-8'))
    monkeypatch.setattr('sys.argv', ['usage_hook.py', 'post'])
    assert H.main() == 0
    assert 'usage_hook' in errors()


def test_log_has_no_text_and_no_key(box, monkeypatch, capsys):
    cycle(monkeypatch, capsys, [sub(1000), sub(1046)], [item()])
    cycle(monkeypatch, capsys, [sub(1046), sub(1046)], [],
          event('PostToolUseFailure', tool_use_id='toolu_2', error='Błąd: ' + TEXT))
    down = urllib.error.HTTPError('https://api.elevenlabs.io', 401, 'zły ' + KEY, {}, None)
    api(monkeypatch, [down], [])
    monkeypatch.setattr(H, 'HISTORY_PATH', common.SUBSCRIPTION)
    run(monkeypatch, capsys, 'post', event(tool_use_id='toolu_3', tool_input={'text': TEXT}, hook_event_name='PostToolUseFailure'))
    saved = common.LOG.read_text(encoding='utf-8') + errors()
    for secret in (KEY, TEXT, ' '.join(TEXT.split()), 'zażółć'):
        assert secret not in saved
    assert records()[0]['text_len'] == len(TEXT)


@pytest.mark.parametrize('name,paid', [('text_to_speech', True), ('text_to_voice', True), ('voice_clone', True),
                                       ('create_voice_from_preview', False), ('list_agents', False),
                                       ('get_conversation', False), ('create_composition_plan', False)])
def test_paid_filter(name, paid):
    assert H.is_paid(name) is paid


def test_audio_path_from_windows_message_with_spaces(box):
    path = r'D:\Projects\Descent Legendy Mroku - lektor\analysis\work\elevenlabs\audio\tts_abc.mp3'
    message = 'Success. File saved as: %s. Voice used: Adam' % path
    assert H.AUDIO_PATH.search(message).group(0) == path
    assert H.audio_file('Success. Voice created: Adam with ID:abc') is None
