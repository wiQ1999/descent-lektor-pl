"""Fragmenty postaci bez dubbingu w ElevenLabs (E13, D80). Uruchamiać w .venv:

  python -I -m lektor eleven --release m1|m2 [--limit N] [--voices ...] [--retake] [--dry-run] [--max-credits N]

Głosy i model: direction.ELEVEN_VOICES i ELEVEN_MODEL, ustawienia domyślne jak w ocenie E11. Wynik w PCM 24 kHz
(próbkowanie manifestu) trafia do takes/<id>_t101.wav, a ponowne podejścia do t102 i dalej, obok podejść OmniVoice.
Stan po każdym wywołaniu idzie do takes.jsonl, więc przerwany wsad wznawia się tą samą komendą. M2 przejmuje z M1
wybrane podejścia ElevenLabs fragmentów o tym samym id.

Klucz API leży w nieśledzonym .env.elevenlabs.local i nie trafia do logów ani na konsolę. Każde wywołanie trafia
do logu zużycia ElevenLabs (D73) z kosztem z historii konta; log ma tylko SHA-1 i długość tekstu.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
import wave
from datetime import datetime, timezone

from . import db, paths
from . import direction as D
from .synth import inherit, load_state, seed_for, take_path

API = 'https://api.elevenlabs.io'
KEY_FILE = '.env.elevenlabs.local'
KEY_NAME = 'ELEVENLABS_API_KEY'
OUTPUT_FORMAT = 'pcm_24000'
SAMPLE_RATE = 24000
SETTINGS = {'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.0, 'use_speaker_boost': True, 'speed': 1.0}
RATE = 0.44             # kredyty na znak eleven_v4 (E9, E11): szacunek przed wsadem i gdy historia konta milczy
TIMEOUT_S = 120
RETRY_CODES = (429, 500, 502, 503, 504)
RETRY_WAITS = (2, 4, 8)
HISTORY_WAITS = (0, 2, 5)
TOOL = 'lektor_eleven'
USAGE_LOG = os.path.join(paths.WORK, 'elevenlabs', 'usage', 'elevenlabs.jsonl')
REF_DIR = os.path.join(paths.WORK, 'elevenlabs', 'audio', 'e11r2')    # nagrania v4 z oceny E11: referencja barwy
REF_PREFIX = 'elevenlabs:'


class ElevenError(RuntimeError):
    pass


def api_key():
    try:
        lines = open(os.path.join(paths.ROOT, KEY_FILE), encoding='utf-8-sig').read().splitlines()
    except OSError:
        return None
    for line in lines:
        name, _, value = line.strip().partition('=')
        if name.strip() == KEY_NAME and value.strip():
            return value.strip().strip('"\'')
    return None


def _request(key, path, data=None):
    headers = {'xi-api-key': key, 'User-Agent': 'lektor-pl/1'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data).encode('utf-8')
    return urllib.request.Request(API + path, data=data, headers=headers, method='GET' if data is None else 'POST')


def get_json(key, path, opener=urllib.request.urlopen):
    with opener(_request(key, path), timeout=10) as r:
        return json.load(r)


def synthesize(key, voice_id, text, seed, speed=1.0, opener=urllib.request.urlopen, sleep=time.sleep):
    """(PCM 16 bit mono 24 kHz, nagłówki odpowiedzi małymi literami). Błędy 429 i 5xx ponawia."""
    body = {'text': text, 'model_id': D.ELEVEN_MODEL, 'voice_settings': {**SETTINGS, 'speed': speed}, 'seed': seed}
    path = '/v1/text-to-speech/%s?output_format=%s' % (voice_id, OUTPUT_FORMAT)
    for wait in (*RETRY_WAITS, None):
        try:
            with opener(_request(key, path, body), timeout=TIMEOUT_S) as r:
                return r.read(), {k.lower(): v for k, v in r.headers.items()}
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_CODES or wait is None:
                raise ElevenError('HTTP %d: %s' % (e.code, e.read()[:300].decode('utf-8', 'replace'))) from None
        sleep(wait)


def history_credits(key, item_id, opener=urllib.request.urlopen, sleep=time.sleep):
    """Koszt wywołania z historii konta (character_count_change_to - from); None, gdy historia go nie podaje."""
    if not item_id:
        return None
    for wait in HISTORY_WAITS:
        sleep(wait)
        try:
            item = get_json(key, '/v1/history/' + item_id, opener)
        except (urllib.error.URLError, OSError, ValueError):
            continue
        a, b = item.get('character_count_change_from'), item.get('character_count_change_to')
        if a is not None and b is not None:
            return b - a
    return None


def measure(text, headers, history):
    """(kredyty, metoda, flaga): historia konta, nagłówek odpowiedzi albo stawka."""
    if history is not None:
        return history, 'history', None
    for name in ('character-cost', 'x-character-count'):
        if str(headers.get(name, '')).isdigit():
            return int(headers[name]), 'header', None
    return round(len(text) * RATE), 'rate', 'estimated'


def write_wav(path, pcm):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return len(pcm) / 2 / SAMPLE_RATE


def usage_record(text, voice, headers, credits, method, flag, history, sub, audio):
    """Wiersz logu zużycia w formacie hooka MCP (usage_hook.build_record): bez tekstu, z SHA-1 i długością."""
    limit = sub.get('character_limit')
    reset = sub.get('next_character_count_reset_unix')
    return {
        'ts': datetime.now().astimezone().isoformat(timespec='seconds'), 'session_id': None, 'tool_use_id': None,
        'tool': TOOL, 'request_id': headers.get('request-id'), 'history_item_id': headers.get('history-item-id'),
        'voice_id': D.ELEVEN_VOICES[voice], 'voice_name': voice, 'model_id': D.ELEVEN_MODEL,
        'text_sha1': hashlib.sha1(text.encode('utf-8')).hexdigest(), 'text_len': len(text),
        'credits': credits, 'credits_history': history, 'credits_delta': None, 'method': method, 'flag': flag,
        'tier': sub.get('tier'), 'limit': limit,
        'period_reset': None if reset is None else datetime.fromtimestamp(reset, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'used_period': None, 'pct_call': round(credits / limit * 100, 3) if limit else None, 'pct_period': None,
        'audio_file': paths.rel(audio)}


def append_usage(record):
    os.makedirs(os.path.dirname(USAGE_LOG), exist_ok=True)
    with open(USAGE_LOG, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + '\n')


def refs():
    """Referencje barwy głosów ElevenLabs dla automatu: {'elevenlabs:<głos>': {'wav': ścieżka}}."""
    out = {}
    for voice in D.ELEVEN_VOICES:
        folder = os.path.join(REF_DIR, voice, D.ELEVEN_MODEL)
        files = sorted(f for f in os.listdir(folder) if f.endswith('.mp3')) if os.path.isdir(folder) else []
        if files:
            out[REF_PREFIX + voice] = {'wav': paths.rel(os.path.join(folder, files[0]))}
    return out


def jobs(con, voices=None, retake=None):
    """(fragment, podejście, tekst, głos, tempo ElevenLabs) do wygenerowania. retake: {fragment: (podejście, tempo)}."""
    rows = con.execute('SELECT id, voice, text FROM fragments ORDER BY voice, id').fetchall()
    for r in rows:
        if D.engine(r['voice']) != 'elevenlabs' or voices and r['voice'] not in voices:
            continue
        if retake is not None:
            if r['id'] in retake:
                take, speed = retake[r['id']]
                yield r['id'], take, r['text'], r['voice'], speed
            continue
        yield r['id'], D.ELEVEN_TAKE0 + 1, r['text'], r['voice'], SETTINGS['speed']


def inherited(con):
    """Podejścia ElevenLabs wybrane w poprzednim wydaniu dla fragmentów o tym samym id (pliki kopiuje synth.inherit)."""
    if paths.RELEASE not in paths.PREVIOUS:
        return {}
    return {f: c for f, c in inherit(con).items() if D.take_engine(c['take']) == 'elevenlabs'}


def generate(limit=None, voices=None, retake_file=None, dry_run=False, max_credits=None):
    con = db.connect(paths.DB)
    retake = None
    if retake_file:
        retake = {k: tuple(v) for k, v in json.load(open(retake_file, encoding='utf-8')).items()}
    state = load_state()
    done = inherited(con)
    todo = [j for j in jobs(con, voices, retake) if (j[0], j[1]) not in state and j[0] not in done]
    if limit:
        todo = todo[:limit]
    chars = sum(len(j[2]) for j in todo)
    print('do wygenerowania: %d podejść, %d znaków, ok. %d kredytów; przejęte z M1: %d' % (
        len(todo), chars, round(chars * RATE), len(done)), file=sys.stderr, flush=True)
    if not todo or dry_run:
        return todo
    key = api_key()
    if not key:
        sys.exit('Brak %s w %s' % (KEY_NAME, KEY_FILE))
    sub = get_json(key, '/v1/user/subscription')
    os.makedirs(os.path.join(paths.AUDIO, 'takes'), exist_ok=True)
    log = open(os.path.join(paths.AUDIO, 'takes.jsonl'), 'a', encoding='utf-8')
    spent = 0
    for n, (fid, take, text, voice, speed) in enumerate(todo, 1):
        if max_credits is not None and spent + len(text) * RATE > max_credits:
            sys.exit('Limit %d kredytów: zużyto %d, następne wywołanie by go przekroczyło. Wsad zatrzymany.' % (
                max_credits, spent))
        seed = seed_for(fid, take)
        t0 = time.perf_counter()
        pcm, headers = synthesize(key, D.ELEVEN_VOICES[voice], text, seed, speed)
        gen_s = time.perf_counter() - t0
        path = take_path(fid, take)
        sec = write_wav(path, pcm)
        history = history_credits(key, headers.get('history-item-id'))
        credits, method, flag = measure(text, headers, history)
        if method == 'rate':
            print('Koszt ze stawki: historia konta i nagłówki go nie podały (nagłówki: %s)' % ', '.join(sorted(headers)),
                  file=sys.stderr, flush=True)
        append_usage(usage_record(text, voice, headers, credits, method, flag, history, sub, path))
        spent += credits
        rec = {'fragment': fid, 'take': take, 'voice': voice, 'speed': speed, 'seed': seed, 'silent_retries': 0,
               'chars': len(text), 'seconds': round(sec, 2), 'gen_s': round(gen_s, 2), 'vram_gb': None,
               'model': D.ELEVEN_MODEL, 'voice_id': D.ELEVEN_VOICES[voice], 'credits': credits, 'credits_method': method}
        log.write(json.dumps(rec) + '\n')
        log.flush()
        print('%3d/%d %s t%d %-8s %5.1f s audio, %.1f s, %d kr. (%s), razem %d kr.' % (
            n, len(todo), fid, take, voice, sec, gen_s, credits, method, spent), file=sys.stderr, flush=True)
    return todo
