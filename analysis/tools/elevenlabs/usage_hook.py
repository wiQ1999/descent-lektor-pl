"""Hook Claude Code: zapisuje zużycie kredytów przy każdym płatnym wywołaniu MCP ElevenLabs.

Tryb `pre` zapamiętuje licznik konta, tryb `post` liczy koszt i dopisuje rekord do logu.
Hook nigdy nie blokuje pracy: kończy się kodem 0, a błędy trafiają do errors.log.
Log nie zawiera tekstów, tylko SHA-1 i długość.

Licznik konta dogania wywołanie z opóźnieniem do około minuty, więc zerowa różnica nie znaczy
zerowego kosztu. Modele v3 i v4 trzymają tekst i głos w polu `dialogue` wpisu historii.
Narzędzia bez wpisu w historii (np. `text_to_voice`) dostają szacunek ze stawki na znak z testu E9.
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import common

FREE_PREFIXES = ('list_', 'get_', 'search_')
FREE_TOOLS = {'check_subscription', 'play_audio', 'create_composition_plan', 'create_voice_from_preview'}
TEXT_FIELDS = ('text', 'prompt', 'voice_description')
HISTORY_PATH = '/v1/history?page_size=20'
HISTORY_SLACK_S = 5
HISTORY_ATTEMPTS = 3
HISTORY_RETRY_S = 2
PENDING_MAX_AGE_S = 3600
# Kredyty na znak tekstu dla narzędzi bez historii (E9: podglądy głosu kosztowały 1 kredyt na znak).
RATE_ESTIMATES = {'text_to_voice': 1.0}
AUDIO_EXT = r'\.(?:mp3|wav|pcm|ogg|opus|flac)'
AUDIO_PATH = re.compile(r'(?:[A-Za-z]:[\\/]|/)[^,;\n"]+?' + AUDIO_EXT)


def short_name(tool_name):
    return tool_name.rsplit('__', 1)[-1]


def is_paid(tool):
    return tool not in FREE_TOOLS and not tool.startswith(FREE_PREFIXES)


def call_key(event):
    if event.get('tool_use_id'):
        return re.sub(r'\W', '_', event['tool_use_id'])
    raw = json.dumps([event.get('session_id'), event.get('tool_name'), event.get('tool_input')], sort_keys=True)
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()


def fetch(path, key):
    if not key:
        return None
    try:
        return common.get_json(path, key)
    except Exception as exc:
        common.log_error('%s: %s: %s' % (path, type(exc).__name__, exc))
        return None


def prune_pending():
    limit = time.time() - PENDING_MAX_AGE_S
    for path in common.PENDING.glob('*.json'):
        if path.stat().st_mtime < limit:
            path.unlink(missing_ok=True)


def pre(event):
    common.PENDING.mkdir(parents=True, exist_ok=True)
    prune_pending()
    sub = fetch(common.SUBSCRIPTION, common.api_key()) or {}
    entry = {'tool': short_name(event['tool_name']), 'ts_pre': time.time(), 'character_count': sub.get('character_count')}
    (common.PENDING / (call_key(event) + '.json')).write_text(json.dumps(entry), encoding='utf-8')


def take_pending(event):
    path = common.PENDING / (call_key(event) + '.json')
    try:
        entry = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    path.unlink(missing_ok=True)
    return entry


def squeeze(text):
    return ' '.join((text or '').split())


def item_text(item):
    return item.get('text') or ' '.join(part.get('text') or '' for part in item.get('dialogue') or [])


def item_voices(item):
    return [item] + list(item.get('dialogue') or [])


def voice_matches(item, tool_input):
    if tool_input.get('voice_id'):
        return any(v.get('voice_id') == tool_input['voice_id'] for v in item_voices(item))
    if tool_input.get('voice_name'):
        wanted = tool_input['voice_name'].casefold()
        return any((v.get('voice_name') or '').casefold() == wanted for v in item_voices(item))
    return True


def match_history(items, tool_input, ts_pre, now, used_requests):
    text = squeeze(tool_input.get('text'))
    if not text:
        return None
    for item in items:
        fresh = ts_pre - HISTORY_SLACK_S <= item.get('date_unix', 0) <= now + HISTORY_SLACK_S
        if (fresh and squeeze(item_text(item)) == text and voice_matches(item, tool_input)
                and item.get('request_id') not in used_requests):
            return item
    return None


def find_history(tool_input, ts_pre, key):
    if not squeeze(tool_input.get('text')):
        return None
    used = {r.get('request_id') for r in common.read_log()} - {None}
    for attempt in range(HISTORY_ATTEMPTS):
        if attempt:
            time.sleep(HISTORY_RETRY_S)
        history = fetch(HISTORY_PATH, key)
        if history is None:
            return None
        item = match_history(history.get('history', []), tool_input, ts_pre, time.time(), used)
        if item:
            return item
    return None


def measure(item, before, after, failed):
    """Zwraca (kredyty, metoda, flaga, kredyty z historii, kredyty z licznika)."""
    history = None if item is None else item['character_count_change_to'] - item['character_count_change_from']
    delta = None if before is None or after is None else after - before
    moved = delta is not None and delta > 0
    if failed:
        return delta, 'subscription_delta' if delta is not None else None, 'tool_error', history, delta
    if history is not None:
        return history, 'history', 'mismatch' if moved and delta != history else None, history, delta
    if moved:
        return delta, 'subscription_delta', None, history, delta
    return None, None, 'unmeasured', history, delta


def response_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return '\n'.join(response_text(v) for v in value)
    return ''


def audio_file(response):
    found = AUDIO_PATH.search(response_text(response))
    if not found:
        return None
    path = Path(found.group(0))
    try:
        return path.resolve().relative_to(common.ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def failed_call(event):
    response = event.get('tool_response')
    return (event.get('hook_event_name') == 'PostToolUseFailure'
            or (isinstance(response, dict) and bool(response.get('isError'))))


def request_text(tool_input):
    return next((tool_input[f] for f in TEXT_FIELDS if isinstance(tool_input.get(f), str)), None)


def percent(part, whole):
    if part is None or not whole:
        return None
    return round(part / whole * 100, 3)


def build_record(event, pending, sub, item, failed):
    tool_input = event.get('tool_input') or {}
    sub = sub or {}
    item = item or {}
    credits, method, flag, history, delta = measure(
        item or None, pending.get('character_count'), sub.get('character_count'), failed)
    text = request_text(tool_input)
    tool = short_name(event.get('tool_name', ''))
    if flag == 'unmeasured' and tool in RATE_ESTIMATES and isinstance(tool_input.get('text'), str):
        credits, method, flag = round(len(tool_input['text']) * RATE_ESTIMATES[tool]), 'rate_estimate', 'estimated'
    limit = sub.get('character_limit')
    used = max(filter(None, (sub.get('character_count'), item.get('character_count_change_to'))), default=None)
    voice = next((v for v in item_voices(item) if v.get('voice_id')), {})
    return {
        'ts': common.now_iso(),
        'session_id': event.get('session_id'),
        'tool_use_id': event.get('tool_use_id'),
        'tool': tool,
        'request_id': item.get('request_id'),
        'history_item_id': item.get('history_item_id'),
        'voice_id': voice.get('voice_id') or tool_input.get('voice_id'),
        'voice_name': voice.get('voice_name') or tool_input.get('voice_name'),
        'model_id': item.get('model_id') or tool_input.get('model_id'),
        'text_sha1': None if text is None else hashlib.sha1(text.encode('utf-8')).hexdigest(),
        'text_len': None if text is None else len(text),
        'credits': credits,
        'credits_history': history,
        'credits_delta': delta,
        'method': method,
        'flag': flag,
        'tier': sub.get('tier'),
        'limit': limit,
        'period_reset': common.unix_to_iso(sub.get('next_character_count_reset_unix')),
        'used_period': used,
        'pct_call': percent(credits, limit),
        'pct_period': percent(used, limit),
        'audio_file': audio_file(event.get('tool_response')),
    }


def append_record(record):
    common.USAGE.mkdir(parents=True, exist_ok=True)
    with open(common.LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def summary(record):
    if record['credits'] is None:
        text = 'ElevenLabs: nie zmierzono zużycia'
    else:
        text = 'ElevenLabs: %s kr.' % common.pl_int(record['credits'])
        if record['pct_call'] is not None:
            text += ' (%s limitu)' % common.pl_pct(record['pct_call'])
    if record['pct_period'] is not None:
        text += '; w okresie %s (%s / %s)' % (
            common.pl_pct(record['pct_period']), common.pl_int(record['used_period']), common.pl_int(record['limit']))
    if record['period_reset']:
        text += ', reset %s' % record['period_reset'][:10]
    if record['flag']:
        text += '; flaga: %s' % record['flag']
    return text + '.'


def post(event):
    pending = take_pending(event)
    failed = failed_call(event)
    now = time.time()
    ts_pre = pending.get('ts_pre', now - (event.get('duration_ms') or 0) / 1000)
    key = common.api_key()
    if not key:
        common.log_error('Brak klucza API: rekord bez pomiaru')
    sub = fetch(common.SUBSCRIPTION, key)
    item = None if failed or not key else find_history(event.get('tool_input') or {}, ts_pre, key)
    record = build_record(event, pending, sub, item, failed)
    append_record(record)
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': event.get('hook_event_name', 'PostToolUse'), 'additionalContext': summary(record)}}))


def run(mode):
    event = json.loads(sys.stdin.buffer.read().decode('utf-8'))
    if is_paid(short_name(event.get('tool_name', ''))):
        {'pre': pre, 'post': post}[mode](event)


def main():
    try:
        run(sys.argv[1])
    except Exception as exc:
        try:
            common.log_error('usage_hook: %s: %s' % (type(exc).__name__, exc))
        except Exception:
            pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
