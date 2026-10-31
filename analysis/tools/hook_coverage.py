"""Pokrycie okien przez plugin (E1): dziennik JSONL pluginu vs zakres M1 i .qlog gry.

Wejście:
  dziennik pluginu  %LOCALAPPDATA%/LektorPL/logs/hook-*.jsonl (domyślnie najnowszy)
  work/out/m1_scope.json, work/out/pl_terms.json
  pliki .qlog z SavedGames zmienione w czasie sesji (gra dopisuje okna przy zapisie w scenie questu)
Wyjście:
  stdout                 liczby bez treści gry (do analysis/E1_HOOK.md)
  work/out/e1_coverage.json  szczegóły z kluczami i wartościami argumentów (prywatne)

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/hook_coverage.py [dziennik.jsonl ...]
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qlog_watch import DEFAULT_SAVES, parse_qlog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'work', 'out')
LOGS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'LektorPL', 'logs')
TAG = re.compile(r'<[^>]+>')
NOT_WINDOWS = {'napisy_cutscenek'}  # napisy przerywników nie są oknami (D14)


def norm(text):
    return re.sub(r'\s+', ' ', TAG.sub('', text or '')).strip()


def read_events(paths):
    events = []
    for p in paths:
        with open(p, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    print('uszkodzona linia %s:%d' % (os.path.basename(p), n), file=sys.stderr)
                    continue
                e['_file'] = os.path.basename(p)
                events.append(e)
    return events


def session_qlogs(events, saves):
    """Pliki .qlog zmienione między pierwszym a ostatnim zdarzeniem (z zapasem 2 min)."""
    stamps = [datetime.datetime.strptime(e['utc'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
              for e in events if e.get('utc')]
    if not stamps:
        return []
    lo, hi = min(stamps).timestamp() - 120, max(stamps).timestamp() + 120
    return sorted(p for p in glob.glob(os.path.join(saves, '*', '*.qlog')) if lo <= os.path.getmtime(p) <= hi)


def pct(a, b):
    return '%.1f%%' % (100.0 * a / b) if b else '-'


def quantiles(xs):
    if not xs:
        return {}
    xs = sorted(xs)
    pick = lambda q: xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))]  # noqa: E731
    return {'n': len(xs), 'median': round(statistics.median(xs), 3), 'p95': round(pick(0.95), 3), 'max': round(xs[-1], 3)}


def analyze(events, scope, terms, qlogs):
    rows = {r['key']: r for r in scope['rows']}
    by_ev = collections.Counter((e['ev'], e.get('kind')) for e in events)
    opens = [e for e in events if e['ev'] == 'open']
    closes = {(e['_file'], e['id']): e for e in events if e['ev'] == 'close' and e.get('id', -1) >= 0}
    shown = {(e['_file'], e['id']): e for e in events if e['ev'] == 'shown'}

    windows = []
    for o in opens:
        k = (o['_file'], o['id'])
        s = shown.get(k)
        c = closes.get(k)
        text = (s or {}).get('text') if o['kind'] == 'story' else o.get('text')
        speakers = [ch for ch in (s or {}).get('characters', []) if ch.get('speaking')]
        complete = bool(o.get('key')) and bool(text) and c is not None and (o['kind'] != 'story' or s is not None)
        windows.append({'id': o['id'], 'file': o['_file'], 'kind': o['kind'], 'type': o.get('type'), 'via': o.get('via'),
                        'key': o.get('key'), 'has_text': bool(text), 'shown': s is not None, 'closed': c is not None,
                        'close_via': (c or {}).get('via'), 'speakers': [ch.get('name_key') for ch in speakers],
                        'complete': complete, 'in_m1': o.get('key') in rows,
                        'category': rows.get(o.get('key'), {}).get('category')})

    keys_seen = collections.Counter(w['key'] for w in windows)
    m1_windows = {k for k, r in rows.items() if r['category'] not in NOT_WINDOWS}

    # Argumenty {n}: typy i wartości (do inwentarza fragmentów, D16).
    args = collections.defaultdict(collections.Counter)
    for o in opens:
        for a in o.get('args') or []:
            args[a.get('type')][a.get('as_key')] += 1

    # Mówcy i rozwiązanie VARIABLE_HERO (D17).
    variable = collections.Counter()
    speakers = collections.Counter()
    for e in shown.values():
        for ch in e.get('characters', []):
            if ch.get('speaking'):
                speakers[ch.get('name_key')] += 1
            if ch.get('variable'):
                variable['%s -> %s' % (ch.get('model'), ch.get('name_key'))] += 1

    choices = collections.Counter()
    for c in closes.values():
        if c.get('choice_key'):
            choices[c['choice_key']] += 1

    # .qlog: okna, które gra uznała za wyświetlone (scena questu).
    q_keys = collections.Counter()
    for p in qlogs:
        _, entries = parse_qlog(p)
        for rnd, key, etype, _args in entries:
            if etype != 1 and key:
                q_keys[key] += 1
    q_missing = sorted(k for k in q_keys if k not in keys_seen)

    # TMP_Text spoza okien: teksty dopasowane do kluczy gry (dokładnie, po usunięciu tagów).
    by_text = collections.defaultdict(list)
    for k, v in terms.items():
        t = norm(v.get('text'))
        if len(t) >= 12:
            by_text[t].append(k)
    window_texts = {norm(e.get('text')) for e in events if e['ev'] in ('open', 'shown')}
    tmp_keys, tmp_unknown = collections.Counter(), 0
    for e in events:
        if e['ev'] != 'tmp':
            continue
        t = norm(e.get('text'))
        if t in window_texts:
            continue
        ks = by_text.get(t)
        if ks:
            for k in ks:
                tmp_keys[k] += 1
        else:
            tmp_unknown += 1
    tmp_m1 = sorted(k for k in tmp_keys if k in rows and k not in keys_seen)

    perf = [e for e in events if e['ev'] == 'perf']
    errors = collections.Counter(e.get('where') for e in events if e['ev'] == 'error')
    waits = [e['wait'] for e in shown.values() if 'wait' in e]

    summary = {
        'files': sorted({e['_file'] for e in events}),
        'events': {'%s/%s' % k: n for k, n in sorted(by_ev.items(), key=lambda x: str(x[0]))},
        'start': [{k: e.get(k) for k in ('plugin', 'game', 'unity', 'fields_ok')} for e in events if e['ev'] == 'start'],
        'windows': len(windows),
        'windows_complete': sum(w['complete'] for w in windows),
        'windows_by_kind': dict(collections.Counter(w['kind'] for w in windows)),
        'windows_by_type': dict(collections.Counter(w['type'] for w in windows)),
        'message_via_poll': sum(1 for w in windows if w['kind'] == 'message' and w['via'] == 'poll'),
        'message_close_via_poll': sum(1 for w in windows if w['kind'] == 'message' and w['close_via'] == 'poll'),
        'not_closed': sum(1 for w in windows if not w['closed']),
        'story_not_shown': sum(1 for w in windows if w['kind'] == 'story' and not w['shown']),
        'story_shown_reason': dict(collections.Counter(e.get('reason') for e in shown.values())),
        'story_wait_s': quantiles(waits),
        'unique_keys': len(keys_seen),
        'keys_in_m1': sum(1 for k in keys_seen if k in rows),
        'keys_outside_m1': sum(1 for k in keys_seen if k not in rows),
        'm1_window_keys_seen': '%d / %d' % (len(m1_windows & set(keys_seen)), len(m1_windows)),
        'qlog_files': len(qlogs),
        'qlog_keys': len(q_keys),
        'qlog_keys_logged': len(q_keys) - len(q_missing),
        'qlog_coverage': pct(len(q_keys) - len(q_missing), len(q_keys)),
        'arg_types': {t: sum(c.values()) for t, c in args.items()},
        'speaking_characters': len(speakers),
        'variable_slots': len(variable),
        'choices_logged': sum(choices.values()),
        'tmp_texts_matching_keys_outside_windows': len(tmp_keys),
        'tmp_m1_keys_not_in_windows': len(tmp_m1),
        'tmp_unmatched_texts': tmp_unknown,
        'perf_max_frame_ms': max((e['max_frame_ms'] for e in perf), default=None),
        'perf_work_ms_max': max((e['work_ms_max'] for e in perf), default=None),
        'perf_work_ms_per_min_max': max((e['work_ms_total'] / max(e['seconds'], 1) * 60 for e in perf), default=None),
        'errors': dict(errors),
    }
    details = {
        'summary': summary,
        'keys_outside_m1': sorted(k for k in keys_seen if k not in rows),
        'm1_window_keys_missing': sorted(m1_windows - set(keys_seen)),
        'qlog_keys_missing_in_hook': q_missing,
        'incomplete_windows': [w for w in windows if not w['complete']],
        'args': {t: dict(c.most_common()) for t, c in args.items()},
        'speakers': dict(speakers.most_common()),
        'variable_slots': dict(variable.most_common()),
        'choices': dict(choices.most_common()),
        'tmp_m1_keys_not_in_windows': tmp_m1,
        'tmp_keys_outside_windows': dict(tmp_keys.most_common()),
        'windows': windows,
    }
    return summary, details


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('logs', nargs='*', help='dzienniki JSONL (domyślnie najnowszy w %%LOCALAPPDATA%%/LektorPL/logs)')
    ap.add_argument('--saves', default=DEFAULT_SAVES)
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    paths = a.logs or sorted(glob.glob(os.path.join(LOGS, 'hook-*.jsonl')), key=os.path.getmtime)[-1:]
    if not paths:
        sys.exit('brak dziennika w %s' % LOGS)
    events = read_events(paths)
    scope = json.load(open(os.path.join(OUT, 'm1_scope.json'), encoding='utf-8'))
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    qlogs = session_qlogs(events, a.saves) if os.path.isdir(a.saves) else []
    summary, details = analyze(events, scope, terms, qlogs)
    json.dump(details, open(os.path.join(OUT, 'e1_coverage.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print('szczegóły: work/out/e1_coverage.json', file=sys.stderr)


if __name__ == '__main__':
    main()
