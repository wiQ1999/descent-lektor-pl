"""Raport zużycia kredytów ElevenLabs: suma z logu, proporcja do limitu, uzgodnienie z kontem.

`--mark` zapisuje licznik konta na początku prompta, a `--summary` podaje zużycie od tego znacznika
i sumę projektu wobec limitu (podsumowanie na końcu odpowiedzi, skill `elevenlabs`).
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime

import common

FLAGS = ('mismatch', 'unmeasured', 'estimated', 'tool_error')
MARK = 'prompt_mark.json'
GROUPS = {
    'day': ('dzień', lambda r: (r.get('ts') or '')[:10]),
    'voice': ('głos', lambda r: r.get('voice_name') or r.get('voice_id') or 'brak'),
    'model': ('model', lambda r: r.get('model_id') or 'brak'),
    'tool': ('narzędzie', lambda r: r.get('tool') or 'brak'),
    'session': ('sesja', lambda r: (r.get('session_id') or 'brak')[:8]),
}


def credits_sum(records):
    return sum(r.get('credits') or 0 for r in records)


def current_reset(records, sub):
    if sub and sub.get('next_character_count_reset_unix') is not None:
        return common.unix_to_iso(sub['next_character_count_reset_unix'])
    dated = [r for r in records if r.get('period_reset')]
    return max(dated, key=lambda r: r['ts'])['period_reset'] if dated else None


def in_period(records, reset):
    return [r for r in records if reset is not None and r.get('period_reset') == reset]


def grouped(records, by):
    label = GROUPS[by][1]
    rows = defaultdict(lambda: [0, 0])
    for record in records:
        row = rows[label(record)]
        row[0] += 1
        row[1] += record.get('credits') or 0
    return [(name, calls, used) for name, (calls, used) in sorted(rows.items())]


def table(header, rows):
    width = max([len(header)] + [len(str(r[0])) for r in rows])
    lines = ['  %-*s %10s %10s' % (width, header, 'wywołania', 'kredyty')]
    lines += ['  %-*s %10s %10s' % (width, name, common.pl_int(calls), common.pl_int(used)) for name, calls, used in rows]
    return lines


def sum_lines(records, period, reset):
    lines = ['Suma z logu',
             '  łącznie: wywołania %s, kredyty %s' % (common.pl_int(len(records)), common.pl_int(credits_sum(records)))]
    until = ' (reset %s)' % reset[:10] if reset else ''
    lines.append('  bieżący okres%s: wywołania %s, kredyty %s' % (
        until, common.pl_int(len(period)), common.pl_int(credits_sum(period))))
    return lines


def account_lines(period, sub):
    limit = sub.get('character_limit')
    used = sub.get('character_count')
    if not limit or used is None:
        return ['Proporcja do subskrypcji', '  konto nie podało limitu albo zużycia']
    project = credits_sum(period)
    reset = common.unix_to_iso(sub.get('next_character_count_reset_unix'))
    outside = used - project
    lines = [
        'Proporcja do subskrypcji (%s)' % sub.get('tier', 'plan nieznany'),
        '  projekt w okresie: %s / %s (%s)' % (common.pl_int(project), common.pl_int(limit), common.pl_pct(project / limit * 100)),
        '  konto w okresie: %s / %s (%s), pozostało %s, reset %s' % (
            common.pl_int(used), common.pl_int(limit), common.pl_pct(used / limit * 100),
            common.pl_int(limit - used), (reset or 'nieznany')[:10]),
        '',
        'Uzgodnienie',
        '  konto minus log: %s (zużycie spoza projektu, np. panel WWW)' % common.pl_int(outside),
    ]
    unmeasured = sum(r.get('flag') == 'unmeasured' for r in period)
    if unmeasured:
        lines.append('  ta wartość obejmuje też koszt rekordów bez pomiaru: %d' % unmeasured)
    if outside < 0:
        lines.append('  UWAGA: log pokazuje więcej niż konto. Sprawdź rekordy z flagami i okres rozliczeniowy.')
    return lines


def flag_line(records):
    counts = ['%s %d' % (flag, sum(r.get('flag') == flag for r in records)) for flag in FLAGS]
    return 'Flagi: ' + ', '.join(counts)


def report(records, sub, period_name, by):
    reset = current_reset(records, sub)
    period = in_period(records, reset)
    shown = period if period_name == 'current' else records
    scope = 'bieżący okres' if period_name == 'current' else 'cały log'
    lines = ['ElevenLabs: zużycie projektu', ''] + sum_lines(records, period, reset)
    lines += ['', 'Podział (%s)' % scope] + table(GROUPS[by][0], grouped(shown, by)) + ['']
    lines += account_lines(period, sub) if sub else ['Proporcja do subskrypcji', '  pominięta: tryb offline albo brak odpowiedzi konta']
    return '\n'.join(lines + ['', flag_line(shown)])


def mark_path():
    return common.USAGE / MARK


def write_mark(sub):
    sub = sub or {}
    mark = {'ts': common.now_iso(), 'character_count': sub.get('character_count'),
            'period_reset': common.unix_to_iso(sub.get('next_character_count_reset_unix'))}
    common.USAGE.mkdir(parents=True, exist_ok=True)
    mark_path().write_text(json.dumps(mark), encoding='utf-8')
    return mark


def read_mark():
    try:
        return json.loads(mark_path().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def since(records, ts):
    start = datetime.fromisoformat(ts)
    return [r for r in records if r.get('ts') and datetime.fromisoformat(r['ts']) >= start]


def prompt_line(records, mark, sub):
    if not mark:
        return '- ten prompt: brak znacznika początku (`--mark`), pokazuję tylko sumy'
    own = since(records, mark['ts'])
    estimated = sum(r.get('flag') == 'estimated' for r in own)
    unmeasured = sum(r.get('flag') == 'unmeasured' for r in own)
    text = '- ten prompt: %s kr. z logu (wywołania: %s' % (common.pl_int(credits_sum(own)), common.pl_int(len(own)))
    if estimated:
        text += ', w tym %d z szacunkiem stawki' % estimated
    if unmeasured:
        text += ', %d bez pomiaru' % unmeasured
    text += ')'
    reset = common.unix_to_iso((sub or {}).get('next_character_count_reset_unix'))
    if sub and mark.get('character_count') is not None and reset == mark.get('period_reset'):
        text += '; licznik konta: +%s kr. od początku prompta' % common.pl_int(sub['character_count'] - mark['character_count'])
    return text


def summary(records, sub, mark):
    """Krótki blok Markdown na koniec odpowiedzi: ten prompt, projekt i konto wobec limitu."""
    reset = current_reset(records, sub)
    period = in_period(records, reset)
    lines = ['**ElevenLabs: zużycie kredytów**', prompt_line(records, mark, sub)]
    limit = (sub or {}).get('character_limit')
    project = '- projekt: %s kr. w bieżącym okresie, %s kr. łącznie' % (
        common.pl_int(credits_sum(period)), common.pl_int(credits_sum(records)))
    if limit:
        project += ' (okres: %s limitu %s)' % (common.pl_pct(credits_sum(period) / limit * 100), common.pl_int(limit))
    lines.append(project)
    if limit and sub.get('character_count') is not None:
        used = sub['character_count']
        lines.append('- konto: %s / %s (%s), pozostało %s, reset %s' % (
            common.pl_int(used), common.pl_int(limit), common.pl_pct(used / limit * 100), common.pl_int(limit - used),
            (common.unix_to_iso(sub.get('next_character_count_reset_unix')) or 'nieznany')[:10]))
    else:
        lines.append('- konto: brak danych (tryb offline albo brak odpowiedzi)')
    return '\n'.join(lines)


def write_csv(path, rows, by):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([GROUPS[by][0], 'wywołania', 'kredyty'])
        writer.writerows(rows)


def subscription():
    key = common.api_key()
    if not key:
        print('Brak klucza API: raport bez danych konta.', file=sys.stderr)
        return None
    try:
        return common.get_json(common.SUBSCRIPTION, key)
    except Exception as exc:
        print('Konto nie odpowiedziało (%s): raport bez danych konta.' % type(exc).__name__, file=sys.stderr)
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description='Raport zużycia kredytów ElevenLabs.')
    parser.add_argument('--period', choices=['current', 'all'], default='current')
    parser.add_argument('--by', choices=sorted(GROUPS), default='day')
    parser.add_argument('--csv', metavar='PLIK')
    parser.add_argument('--offline', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--mark', action='store_true', help='zapisz licznik konta na początku prompta')
    mode.add_argument('--summary', action='store_true', help='zużycie od znacznika i suma projektu wobec limitu')
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    records = common.read_log()
    sub = None if args.offline else subscription()
    if args.mark:
        mark = write_mark(sub)
        print('Znacznik prompta: %s, licznik konta %s' % (mark['ts'], mark['character_count']))
        return 0
    if args.summary:
        print(summary(records, sub, read_mark()))
        return 0
    print(report(records, sub, args.period, args.by))
    if args.csv:
        shown = in_period(records, current_reset(records, sub)) if args.period == 'current' else records
        write_csv(args.csv, grouped(shown, args.by), args.by)
    return 0


if __name__ == '__main__':
    sys.exit(main())
