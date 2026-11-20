"""Wzorzec liczb panelu podsumowania misji (E20, D113) z plików zapisu gry.

  quest_summary_preview.py catalog                      # katalog id z bundli -> analysis/work/out/quest_summary_catalog.json
  quest_summary_preview.py show ZAPIS.sav [...]         # statystyki misji z zapisu (JSON na konsolę: same liczby i id)
  quest_summary_preview.py compare ZAPIS.sav DZIENNIK.jsonl   # wzorzec wobec ostatniego wiersza quest_summary pluginu

Zapis porównujemy z ostatnim zapisem w misji (autozapis na końcu rundy); po powrocie na mapę gra liczy czas od nowa.
Katalog trafia do analysis/work (nieśledzone); ścieżkę kopii gry można zmienić zmienną LEKTOR_WORK.
"""
import argparse
import json
import os
import sys

from lektor import paths, quest_summary as qs

CATALOG = os.path.join(paths.WORK, 'out', 'quest_summary_catalog.json')


def load_catalog(path):
    if not os.path.exists(path):
        sys.exit(f'Brak katalogu {path}: uruchom najpierw "catalog".')
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--catalog', default=CATALOG)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('catalog')
    p = sub.add_parser('show')
    p.add_argument('saves', nargs='+')
    p = sub.add_parser('compare')
    p.add_argument('save')
    p.add_argument('log')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    if a.cmd == 'catalog':
        from lektor.game import Game
        cat = qs.build_catalog(Game())
        os.makedirs(os.path.dirname(a.catalog), exist_ok=True)
        with open(a.catalog, 'w', encoding='utf-8') as fh:
            json.dump(cat, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print(f'{a.catalog}: {len(cat["items"])} przedmiotów, {len(cat["weapons"])} części broni, {len(cat["feats"])} wyzwań')
        return

    cat = load_catalog(a.catalog)
    if a.cmd == 'show':
        for path in a.saves:
            print(json.dumps({'save': os.path.basename(path), **qs.compute(qs.load_save(path), cat)}, ensure_ascii=False))
        return

    expected = qs.compute(qs.load_save(a.save), cat)
    lines = qs.summary_lines(a.log)
    if not lines:
        sys.exit(f'Brak wiersza quest_summary w {a.log}.')
    actual = lines[-1]
    problems = [d for d in qs.diff(expected, actual) if d[0] != 'quest' or d[1] is not None]
    for field, exp, got in problems:
        print(f'{field}: zapis={exp!r} plugin={got!r}')
    print('zgodne' if not problems else f'{len(problems)} różnic')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
