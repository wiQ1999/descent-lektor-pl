"""python -I -m lektor.companion: companion bez cli.py (paczka D60 nie ma modułów E2 i E3)."""
import argparse
import sys

from .app import add_args, main

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
ap = argparse.ArgumentParser(prog='lektor.companion', description='companion lektora PL')
add_args(ap)
main(ap.parse_args())
