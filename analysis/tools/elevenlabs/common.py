"""Wspólne elementy narzędzi ElevenLabs: ścieżki, klucz API, klient HTTP, liczby po polsku.

Tylko biblioteka standardowa, bo skrypty startują przez `uv run --no-project`.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = 'https://api.elevenlabs.io'
TIMEOUT_S = 5
KEY_FILE = '.env.elevenlabs.local'
KEY_NAME = 'ELEVENLABS_API_KEY'
SUBSCRIPTION = '/v1/user/subscription'

ROOT = Path(__file__).resolve().parents[3]
AUDIO = ROOT / 'analysis' / 'work' / 'elevenlabs' / 'audio'
USAGE = ROOT / 'analysis' / 'work' / 'elevenlabs' / 'usage'
LOG = USAGE / 'elevenlabs.jsonl'
PENDING = USAGE / 'pending'
ERRORS = USAGE / 'errors.log'


def read_env(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            name, value = line.split('=', 1)
            values[name.strip()] = value.strip().strip('"\'')
    return values


def api_key():
    try:
        return read_env(ROOT / KEY_FILE).get(KEY_NAME) or None
    except OSError:
        return None


def get_json(path, key):
    request = urllib.request.Request(API + path, headers={
        'xi-api-key': key, 'Accept': 'application/json', 'User-Agent': 'lektor-pl-usage/1'})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return json.load(response)


def now_iso():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def unix_to_iso(value):
    if value is None:
        return None
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def log_error(message):
    key = api_key()
    if key:
        message = message.replace(key, '***')
    USAGE.mkdir(parents=True, exist_ok=True)
    with open(ERRORS, 'a', encoding='utf-8') as f:
        f.write('%s %s\n' % (now_iso(), message))


def read_log():
    if not LOG.exists():
        return []
    records = []
    for line in LOG.read_text(encoding='utf-8').splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            log_error('Pominięto uszkodzony wiersz logu zużycia')
    return records


def pl_int(value):
    return '{:,}'.format(value).replace(',', ' ')


def pl_pct(value):
    return ('%.2f' % value).replace('.', ',') + '%'
