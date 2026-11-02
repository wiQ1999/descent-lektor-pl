"""Serwer companiona i replay dziennika E1.

  serve   nasłuch na 127.0.0.1:<port>; plugin łączy się sam i ponawia połączenie (D46)
  replay  zdarzenia z dzienników pluginu z zachowaniem odstępów (speed, max_gap), bezpośrednio albo przez TCP

Dziennik companiona (%LOCALAPPDATA%/LektorPL/logs/companion-*.jsonl) ma tylko klucze, liczby i czasy.
"""
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


def listen(port, inbox, log, once=False):
    """Wątek serwera: jedno połączenie naraz (plugin); nowe połączenie zastępuje stare."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(('127.0.0.1', port))
    srv.listen(1)

    def loop():
        while True:
            conn, _ = srv.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            log({'ev': 'client', 'state': 'connected'})
            _reader(conn, inbox, (lambda: inbox.put((time.perf_counter(), END))) if once else None)
            log({'ev': 'client', 'state': 'disconnected'})
            if once:
                return
    threading.Thread(target=loop, daemon=True).start()
    return srv.getsockname()[1]


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


def run(cfg, replay=None, audio=True, speed=1.0, max_gap=None, tcp=False, drain=30.0, quiet=False):
    lib = Library(cfg['db'], cfg['audio'])
    lib.warm()
    player = Player(lib.sample_rate, cfg.get('device')) if audio else NullPlayer(lib.sample_rate)
    log = Log(os.path.join(log_dir(), 'companion-%s.jsonl' % time.strftime('%Y%m%d-%H%M%S')))
    director = Director(lib, player, cfg['toggles'], cfg.get('volume', 1.0), log)
    log({'ev': 'start', 'mode': 'replay' if replay else 'serve', 'model': lib.model, 'audio': audio,
         'output_latency': player.output_latency, 'speed': speed, 'max_gap': max_gap, 'tcp': tcp,
         'toggles': cfg['toggles'], 'replay': [os.path.basename(f) for f in replay or []]})
    inbox = queue.Queue()
    plugin_lag = []
    if not replay:
        listen(cfg['port'], inbox, log)
        say(quiet, 'Companion nasłuchuje na 127.0.0.1:%d. Dziennik: %s. Ctrl+C kończy.' % (cfg['port'], log.path))
    else:
        if tcp:
            port = listen(0, inbox, log, once=True)
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
            if ended is not None and (director.idle or time.perf_counter() - ended > drain):
                break
    except KeyboardInterrupt:
        pass
    time.sleep(0.2)
    director.tick()
    player.close()
    out = director.summary()
    lag = sorted(plugin_lag)
    out['plugin_lag'] = {'n': len(lag), 'p95': round(lag[int(0.95 * len(lag))], 3), 'max': round(lag[-1], 3)} if lag else None
    out['output_latency'] = player.output_latency
    out['log'] = log.path
    log({'ev': 'summary', **out})
    log.close()
    return out


def say(quiet, msg):
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def main(args):
    cfg = C.load(args.config)
    if args.replay:
        out = run(cfg, args.replay, audio=not args.no_audio, speed=args.speed, max_gap=args.max_gap, tcp=args.tcp)
        print(json.dumps({k: v for k, v in out.items() if k != 'missing'}, ensure_ascii=False, indent=1))
        for m in out['missing']:
            print('brak: %-10s %-45s %s ×%d' % (m['src'], m['key'], ','.join(m['missing']), m['n']))
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as fh:
                json.dump(out, fh, ensure_ascii=False, indent=1)
    else:
        run(cfg, audio=not args.no_audio)
