import json

import common
import usage_report as R

OLD_RESET = 1793491200
NEW_RESET = 1796083200


def rec(credits, reset=NEW_RESET, ts='2026-11-06T10:00:00+01:00', flag=None, voice='Adam', tool='text_to_speech'):
    return {'ts': ts, 'session_id': 'sesja-abcdefgh', 'tool': tool, 'voice_name': voice, 'model_id': 'm1',
            'credits': credits, 'flag': flag, 'period_reset': common.unix_to_iso(reset)}


def write_log(records):
    common.USAGE.mkdir(parents=True, exist_ok=True)
    common.LOG.write_text(''.join(json.dumps(r) + '\n' for r in records), encoding='utf-8')


def account(used=1000, reset=NEW_RESET):
    return {'tier': 'creator', 'character_count': used, 'character_limit': 100000,
            'next_character_count_reset_unix': reset}


def test_period_change_separates_records():
    records = [rec(500, OLD_RESET, ts='2026-10-20T10:00:00+01:00'), rec(200), rec(100)]
    text = R.report(records, account(), 'current', 'day')
    assert 'łącznie: wywołania 3, kredyty 800' in text
    assert 'wywołania 2, kredyty 300' in text
    assert 'projekt w okresie: 300 / 100 000 (0,30%)' in text


def test_all_period_shows_every_record_in_groups():
    records = [rec(500, OLD_RESET, voice='Bella'), rec(200)]
    text = R.report(records, account(), 'all', 'voice')
    assert 'Bella' in text and 'Adam' in text and 'cały log' in text


def test_outside_usage_and_remaining():
    text = R.report([rec(300)], account(1000), 'current', 'tool')
    assert 'konto w okresie: 1 000 / 100 000 (1,00%), pozostało 99 000' in text
    assert 'konto minus log: 700' in text
    assert 'UWAGA' not in text


def test_negative_reconciliation_warns():
    text = R.report([rec(1500)], account(1000), 'current', 'day')
    assert 'konto minus log: -500' in text
    assert 'UWAGA' in text


def test_unmeasured_cost_is_named_in_reconciliation():
    assert 'rekordów bez pomiaru: 1' in R.report([rec(None, flag='unmeasured')], account(173), 'current', 'day')
    assert 'bez pomiaru' not in R.report([rec(100)], account(173), 'current', 'day')


def test_flags_are_counted():
    records = [rec(1, flag='mismatch'), rec(None, flag='unmeasured'), rec(0, flag='tool_error'), rec(0, flag='tool_error')]
    assert 'Flagi: mismatch 1, unmeasured 1, estimated 0, tool_error 2' in R.report(records, account(), 'current', 'day')


def test_offline_takes_period_from_newest_record():
    records = [rec(500, OLD_RESET, ts='2026-10-20T10:00:00+01:00'), rec(200)]
    text = R.report(records, None, 'current', 'day')
    assert 'wywołania 1, kredyty 200' in text
    assert 'tryb offline' in text


def test_empty_log():
    assert 'wywołania 0, kredyty 0' in R.report([], None, 'current', 'day')


def test_cli_offline_and_csv(box, capsys):
    write_log([rec(200, voice='Adam'), rec(100, voice='Adam')])
    path = box / 'raport.csv'
    assert R.main(['--offline', '--by', 'voice', '--csv', str(path)]) == 0
    assert 'kredyty 300' in capsys.readouterr().out
    assert path.read_text(encoding='utf-8-sig').splitlines() == ['głos;wywołania;kredyty', 'Adam;2;300']


def test_cli_survives_account_failure(box, capsys):
    write_log([rec(200)])
    assert R.main([]) == 0
    assert 'pominięta' in capsys.readouterr().out


def test_mark_then_summary_counts_only_this_prompt(box, monkeypatch, capsys):
    write_log([rec(500, ts='2026-11-06T10:00:00+01:00')])
    monkeypatch.setattr(R, 'subscription', lambda: account(1000))
    monkeypatch.setattr(common, 'now_iso', lambda: '2026-11-07T12:00:00+01:00')
    assert R.main(['--mark']) == 0
    write_log([rec(500, ts='2026-11-06T10:00:00+01:00'), rec(120, ts='2026-11-07T12:05:00+01:00'),
               rec(80, ts='2026-11-07T12:06:00+01:00', flag='estimated', tool='text_to_voice')])
    monkeypatch.setattr(R, 'subscription', lambda: account(1210))
    capsys.readouterr()
    assert R.main(['--summary']) == 0
    out = capsys.readouterr().out
    assert '- ten prompt: 200 kr. z logu (wywołania: 2, w tym 1 z szacunkiem stawki); licznik konta: +210 kr.' in out
    assert '- projekt: 700 kr. w bieżącym okresie, 700 kr. łącznie (okres: 0,70% limitu 100 000)' in out
    assert '- konto: 1 210 / 100 000 (1,21%), pozostało 98 790' in out


def test_summary_without_mark_or_account():
    text = R.summary([rec(300)], None, None)
    assert 'brak znacznika' in text and 'konto: brak danych' in text


def test_summary_skips_counter_after_period_reset():
    mark = {'ts': '2026-10-20T10:00:00+01:00', 'character_count': 90000, 'period_reset': common.unix_to_iso(OLD_RESET)}
    text = R.summary([rec(300)], account(500), mark)
    assert 'licznik konta' not in text and 'ten prompt: 300 kr.' in text


def test_record_without_reset_joins_its_period():
    undated = dict(rec(70, ts='2026-11-07T21:37:00+01:00'), period_reset=None)
    old = dict(rec(5, reset=OLD_RESET, ts='2026-10-01T10:00:00+02:00'), period_reset=None)
    reset = common.unix_to_iso(NEW_RESET)
    assert [r['credits'] for r in R.in_period([rec(100), undated, old], reset)] == [100, 70]
