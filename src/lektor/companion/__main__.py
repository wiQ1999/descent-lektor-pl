"""python -I -m lektor.companion: companion bez cli.py (paczka D60 nie ma modułów E2 i E3).

Uruchomiony przez plugin nie ma konsoli, więc błąd startu (np. literówka w ustawienia.toml)
zapisujemy do <logs>/companion-blad.log.
"""
import argparse
import os
import sys
import time
import traceback

from .app import add_args, main

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
ap = argparse.ArgumentParser(prog='lektor.companion', description='companion lektora PL')
add_args(ap)
args = ap.parse_args()
try:
    main(args)
except Exception:
    if args.logs:
        os.makedirs(args.logs, exist_ok=True)
        with open(os.path.join(args.logs, 'companion-blad.log'), 'a', encoding='utf-8') as fh:
            fh.write('%s\n%s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), traceback.format_exc()))
    raise
