"""Podgląd plików .qlog (log komunikatów questu) podczas gry — tylko odczyt.

Gra dopisuje komunikaty do .qlog wyłącznie przy zapisie w scenie questu
(po przygotowaniu, na końcu rundy, przy ręcznym zapisie / wyjściu), a w pliku
są one w kolejności od najnowszego. Skrypt co sekundę szuka najnowszego .qlog,
odwraca kolejność i wypisuje wpisy, których nie było w poprzednim pliku.

Uruchomienie:
  .venv/Scripts/python -I analysis/tools/qlog_watch.py            # obserwuj na żywo
  .venv/Scripts/python -I analysis/tools/qlog_watch.py --once     # pokaż najnowszy plik i zakończ
"""
import argparse
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAVES = r'E:\SteamLibrary\steamapps\common\Legends of the Dark\Legends of the Dark_Data\SavedGames'
ENTRY_TYPES = {0: 'Standard', 1: 'Phase', 2: 'Attack', 3: 'Instruction', 4: 'Story'}
TAG = re.compile(r'<[^>]+>')


def parse_qlog(path):
    """Zwraca (nagłówek, wpisy chronologicznie). Wpis: (runda, klucz, typ, [argumenty])."""
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        lines = [l.rstrip('\r\n') for l in f]
    if not lines:
        return None, []
    header = lines[0].split('|')
    entries = []
    for l in lines[1:]:
        if not l:
            continue
        p = l.replace('{BR}', '\n').split('|')
        etype = int(p[2]) if len(p) > 2 and p[2].isdigit() else -1
        entries.append((p[0], p[1] if len(p) > 1 else '', etype, p[3:]))
    entries.reverse()
    return header, entries


def newest_qlog(saves):
    files = glob.glob(os.path.join(saves, '*', '*.qlog'))
    return max(files, key=os.path.getmtime) if files else None


def describe(entry, terms, cats, show_text):
    rnd, key, etype, args = entry
    t = ENTRY_TYPES.get(etype, str(etype))
    if etype == 1:
        return 'R%s  [faza %s]' % (rnd, key)
    line = 'R%s  %-11s %-45s %s' % (rnd, t, key, cats.get(key, '-'))
    if args:
        line += '  args=' + ','.join(args)
    if show_text:
        txt = (terms.get(key) or {}).get('text') or ''
        line += '\n      ' + re.sub(r'\s+', ' ', TAG.sub('', txt))[:140]
    return line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--saves', default=DEFAULT_SAVES)
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--no-text', action='store_true')
    a = ap.parse_args()
    out = os.path.join(ROOT, 'work', 'out')
    terms = json.load(open(os.path.join(out, 'pl_terms.json'), encoding='utf-8'))
    cats = json.load(open(os.path.join(out, 'key_categories.json'), encoding='utf-8'))
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    seen_path, seen_mtime, prev = None, None, []
    while True:
        p = newest_qlog(a.saves)
        if p and (p != seen_path or os.path.getmtime(p) != seen_mtime):
            try:
                header, entries = parse_qlog(p)
            except OSError:
                time.sleep(0.5)
                continue
            new = entries[len(prev):] if entries[:len(prev)] == prev else entries
            print('== %s  quest=%s  wpisów=%d  nowych=%d' % (
                os.path.basename(p), header[2] if header and len(header) > 2 else '?', len(entries), len(new)))
            for e in new:
                print(describe(e, terms, cats, not a.no_text))
            sys.stdout.flush()
            seen_path, seen_mtime, prev = p, os.path.getmtime(p), entries
        if a.once:
            break
        time.sleep(1.0)


if __name__ == '__main__':
    main()
