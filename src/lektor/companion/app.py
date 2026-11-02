"""Serwer companiona i replay dziennika E1.

  serve   nasłuch na 127.0.0.1:<port>; plugin łączy się sam i ponawia połączenie (D46).
          Uruchomiony przez plugin (D59) kończy się razem z grą: --parent-pid, --exit-after-disconnect,
          --exit-if-no-client. Zajęty port oznacza, że companion już działa, więc drugi kończy się od razu.
  replay  zdarzenia z dzienników pluginu z zachowaniem odstępów (speed, max_gap), bezpośrednio albo przez TCP
  test    jedna kwestia narratora (Test dźwięku w paczce)

Dziennik companiona (--logs, domyślnie %LOCALAPPDATA%/LektorPL/logs/companion-*.jsonl) ma tylko klucze, liczby i czasy.
"""
import errno
import json
import os
import queue
import socket
import sys
import threading
import time

from . import config as C
from .director import Director
from .library import Library
from .player import NullPlayer, Player

END = object()


def log_dir():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~/.local/share')
    return os.path.join(base, 'LektorPL', 'logs')


class Log:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self._fh = open(path, 'a', encoding='utf-8')
        self._lock = threading.Lock()

    def __call__(self, rec):
        rec = {'t': round(time.perf_counter(), 3), **rec}
        with self._lock:
            self._fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            self._fh.flush()

    def close(self):
        self._fh.close()


def _reader(conn, inbox, on_eof=None):
    with conn, conn.makefile('rb') as fh:
        for raw in fh:
            inbox.put((time.perf_counter(), raw))
    if on_eof:
        on_eof()


class Link:
    """Stan połączenia z pluginem: czy jest, czy kiedykolwiek było i od kiedy trwa (zamykanie z grą, D59)."""

    def __init__(self, clock=time.perf_counter):
        self.connected, self.ever = False, False
        self._clock = clock
        self.since = clock()

    def set(self, connected):
        self.connected = connected
        self.ever = self.ever or connected
        self.since = self._clock()


def server(port):
    """Gniazdo nasłuchu na localhost albo None, gdy port jest zajęty (companion już działa)."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        srv.bind(('127.0.0.1', port))
    except OSError as e:
        srv.close()
        if e.errno in (errno.EADDRINUSE, errno.EACCES) or getattr(e, 'winerror', None) in (10048, 10013):
            return None
        raise
    srv.listen(1)
    return srv


def listen(srv, inbox, log, once=False, link=None):
    """Wątek serwera: jedno połączenie naraz (plugin); nowe połączenie zastępuje stare."""
    def loop():
        while True:
            conn, _ = srv.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            log({'ev': 'client', 'state': 'connected'})
            if link:
                link.set(True)
            _reader(conn, inbox, (lambda: inbox.put((time.perf_counter(), END))) if once else None)
            log({'ev': 'client', 'state': 'disconnected'})
            if link:
                link.set(False)
            if once:
                return
    threading.Thread(target=loop, daemon=True).start()
    return srv.getsockname()[1]


def alive(pid):
    """Czy proces o tym PID jeszcze działa (proces gry, D59)."""
    if os.name == 'nt':
        import ctypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        k32.OpenProcess.restype = ctypes.c_void_p
        k32.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
        k32.CloseHandle.argtypes = (ctypes.c_void_p,)
        handle = k32.OpenProcess(0x00100000, False, pid)        # SYNCHRONIZE
        if not handle:
            return ctypes.get_last_error() == 5                  # brak dostępu: proces istnieje
        try:
            return k32.WaitForSingleObject(handle, 0) == 0x102   # WAIT_TIMEOUT: nadal działa
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def exit_reason(link, now, started, parent_alive=None, after_disconnect=None, no_client=None):
    """Powód zakończenia companiona uruchomionego przez plugin albo None."""
    if parent_alive is False:
        return 'gra_zamknieta'
    if after_disconnect is not None and link.ever and not link.connected and now - link.since > after_disconnect:
        return 'rozlaczenie'
    if no_client is not None and not link.ever and now - started > no_client:
        return 'brak_pluginu'
    return None


def feed(files, speed, max_gap, put):
    """Linie dzienników z odstępami z pola t (podzielonymi przez speed, przyciętymi do max_gap)."""
    for f in files:
        prev = None
        with open(f, encoding='utf-8') as fh:
            for raw in fh:
                t = json.loads(raw).get('t', 0.0)
                if prev is not None and speed > 0:
                    gap = max(0.0, t - prev) / speed
                    time.sleep(min(gap, max_gap) if max_gap else gap)
                prev = t
                put(raw.encode('utf-8'))


def run(cfg, replay=None, audio=True, speed=1.0, max_gap=None, tcp=False, drain=30.0, quiet=False,
        logs=None, parent_pid=None, exit_after_disconnect=None, exit_if_no_client=None):
    srv = None
    if not replay:
        srv = server(cfg['port'])
        if srv is None:
            say(quiet, 'Port %d jest zajęty: companion już działa.' % cfg['port'])
            return None
    lib = Library(cfg['db'], cfg['audio'])
    lib.warm()
    player = Player(lib.sample_rate, cfg.get('device')) if audio else NullPlayer(lib.sample_rate)
    log = Log(os.path.join(logs or log_dir(), 'companion-%s.jsonl' % time.strftime('%Y%m%d-%H%M%S')))
    director = Director(lib, player, cfg['toggles'], cfg.get('volume', 1.0), log)
    log({'ev': 'start', 'mode': 'replay' if replay else 'serve', 'model': lib.model, 'audio': audio,
         'output_latency': player.output_latency, 'speed': speed, 'max_gap': max_gap, 'tcp': tcp,
         'toggles': cfg['toggles'], 'replay': [os.path.basename(f) for f in replay or []],
         'parent_pid': parent_pid, 'exit_after_disconnect': exit_after_disconnect, 'exit_if_no_client': exit_if_no_client})
    inbox = queue.Queue()
    plugin_lag = []
    link = Link()
    started = next_check = time.perf_counter()
    reason = None
    if not replay:
        listen(srv, inbox, log, link=link)
        say(quiet, 'Companion nasłuchuje na 127.0.0.1:%d. Dziennik: %s. Ctrl+C kończy.' % (cfg['port'], log.path))
    else:
        if tcp:
            port = listen(server(0), inbox, log, once=True)
            client = socket.create_connection(('127.0.0.1', port))
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            put = client.sendall

            def worker():
                feed(replay, speed, max_gap, put)
                client.close()
        else:
            def worker():
                feed(replay, speed, max_gap, lambda raw: inbox.put((time.perf_counter(), raw)))
                inbox.put((time.perf_counter(), END))
        threading.Thread(target=worker, daemon=True).start()
    ended = None
    try:
        while True:
            try:
                recv, raw = inbox.get(timeout=0.005)
            except queue.Empty:
                recv, raw = None, None
            if raw is END:
                ended = time.perf_counter()
            elif raw is not None:
                try:
                    ev = json.loads(raw)
                except ValueError:
                    log({'ev': 'bad_line'})
                    continue
                if ev.get('ev') == 'open' and ev.get('begin_t') is not None:
                    plugin_lag.append(ev['t'] - ev['begin_t'])
                director.handle(ev, recv)
                if not quiet and not replay and ev.get('ev') in ('open', 'shown', 'objective'):
                    say(quiet, '%-10s %s' % (ev.get('kind') or ev.get('ev'), ev.get('key') or ''))
            director.tick()
            now = time.perf_counter()
            if ended is not None and (director.idle or now - ended > drain):
                reason = 'koniec_replayu'
                break
            if not replay and now >= next_check:
                next_check = now + 1.0
                reason = exit_reason(link, now, started, alive(parent_pid) if parent_pid else None,
                                     exit_after_disconnect, exit_if_no_client)
                if reason:
                    break
    except KeyboardInterrupt:
        reason = 'przerwane'
    time.sleep(0.2)
    director.tick()
    player.close()
    out = director.summary()
    lag = sorted(plugin_lag)
    out['plugin_lag'] = {'n': len(lag), 'p95': round(lag[int(0.95 * len(lag))], 3), 'max': round(lag[-1], 3)} if lag else None
    out['output_latency'] = player.output_latency
    out['reason'] = reason
    out['log'] = log.path
    log({'ev': 'summary', **out})
    log.close()
    return out


def say(quiet, msg):
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def sample_key(lib):
    """Pełna kwestia narracji do Testu dźwięku: pierwsza po kluczu, najchętniej średniej długości."""
    medium = lambda k: 40 <= len(lib.lines[k]['text_norm'] or '') <= 160
    keys = sorted((k for k, ln in lib.lines.items()
                   if ln['tts'] and ln['voice'] == 'narrator' and ln['toggle'] == 'narracja'),
                  key=lambda k: (not medium(k), k))
    for key in keys:
        if lib.resolve(key).complete:
            return key
    raise SystemExit('Brak kwestii narracji do testu dźwięku.')


def sound_test(cfg, timeout=2.0):
    """Jedna kwestia narratora przez wybrane urządzenie i głośność; zwraca klucz kwestii."""
    lib = Library(cfg['db'], cfg['audio'])
    key = sample_key(lib)
    y = lib.audio(lib.resolve(key), cfg.get('volume', 1.0))
    player = Player(lib.sample_rate, cfg.get('device'))
    player.play(y, 'test')
    deadline = time.perf_counter() + len(y) / lib.sample_rate + timeout
    try:
        while time.perf_counter() < deadline:
            if any(what == 'end' for _, what, _ in player.poll()):
                break
            time.sleep(0.05)
    finally:
        player.close()
    return key


def add_args(c):
    """Opcje companiona wspólne dla `python -m lektor companion` i `python -m lektor.companion` (paczka)."""
    c.add_argument('--config', help='plik konfiguracji (domyślnie %%LOCALAPPDATA%%/LektorPL/companion.toml)')
    c.add_argument('--replay', nargs='+', metavar='JSONL', help='dzienniki pluginu do odtworzenia zamiast serwera')
    c.add_argument('--speed', type=float, default=1.0, help='tempo replayu (0: bez odstępów)')
    c.add_argument('--max-gap', type=float, help='najdłuższy odstęp między zdarzeniami w replayu (s)')
    c.add_argument('--tcp', action='store_true', help='replay przez TCP na localhost (jak z pluginu)')
    c.add_argument('--no-audio', action='store_true', help='bez dźwięku (czas trwania z długości audio)')
    c.add_argument('--out', help='podsumowanie replayu jako JSON')
    c.add_argument('--logs', help='katalog dzienników (domyślnie %%LOCALAPPDATA%%/LektorPL/logs)')
    c.add_argument('--parent-pid', type=int, help='kończy companion, gdy zniknie proces o tym PID (gra)')
    c.add_argument('--exit-after-disconnect', type=float, metavar='S', help='kończy companion S sekund po rozłączeniu pluginu')
    c.add_argument('--exit-if-no-client', type=float, metavar='S', help='kończy companion, gdy plugin nie połączy się w S sekund')
    c.add_argument('--quiet', action='store_true', help='bez komunikatów na konsoli (start z pluginu)')
    c.add_argument('--test', action='store_true', help='odtwarza jedną kwestię narratora i kończy (Test dźwięku)')


def main(args):
    cfg = C.load(args.config)
    if args.test:
        print('Test dźwięku: %s' % sound_test(cfg))
        return
    if args.replay:
        out = run(cfg, args.replay, audio=not args.no_audio, speed=args.speed, max_gap=args.max_gap, tcp=args.tcp)
        print(json.dumps({k: v for k, v in out.items() if k != 'missing'}, ensure_ascii=False, indent=1))
        for m in out['missing']:
            print('brak: %-10s %-45s %s ×%d' % (m['src'], m['key'], ','.join(m['missing']), m['n']))
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as fh:
                json.dump(out, fh, ensure_ascii=False, indent=1)
    else:
        run(cfg, audio=not args.no_audio, quiet=args.quiet, logs=args.logs, parent_pid=args.parent_pid,
            exit_after_disconnect=args.exit_after_disconnect, exit_if_no_client=args.exit_if_no_client)
