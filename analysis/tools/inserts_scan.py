"""Wstawki sceniczne w kwestiach postaci, np. „(miga)” albo „*wzdycha*” (uwaga z QA E14).

Szuka w bazie wydania tekstów w nawiasach i gwiazdkach i dzieli je na:
- wstawka: opis zachowania postaci (krótki, od małej litery, bez liczb i luk);
- inne: reszta (liczby, luki, nazwy przedmiotów, wtrącenia w zdaniu).

Pełna lista z tekstami trafia do analysis/work/out/<wydanie>_inserts.jsonl (nieśledzone),
raport z kluczami i liczbami do analysis/E14_INSERTS.md.

    .venv/Scripts/python -I analysis/tools/inserts_scan.py [--release m3]
"""
import argparse
import collections
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from lektor.build import INSERT as SPAN, insert_kind as kind  # noqa: E402
from lektor.normalize import clean_markup  # noqa: E402


def scan(db):
    con = sqlite3.connect(db)
    rows = con.execute('select key, grp, category, voice, text_raw from lines where tts order by grp, key').fetchall()
    found = []
    for key, grp, cat, voice, raw in rows:
        text = clean_markup(raw or '')
        for m in SPAN.finditer(text):
            inner = m.group(1) or m.group(2)
            found.append({'key': key, 'group': grp, 'category': cat, 'voice': voice,
                          'mark': '()' if m.group(1) else '**', 'kind': kind(inner, text, m.start()),
                          'insert': m.group(0), 'text': text})
    return found


def report(found, release, path):
    ins = [f for f in found if f['kind'] == 'wstawka']
    chars = [f for f in ins if f['voice'] != 'narrator']
    by_voice = collections.Counter(f['voice'] for f in chars)
    by_group = collections.Counter(f['group'] for f in chars)
    by_kind = collections.Counter((f['kind'], f['voice'] != 'narrator') for f in found)
    lines = ['# Wstawki sceniczne w kwestiach (%s)' % release.upper(), '',
             'Wynik `analysis/tools/inserts_scan.py --release %s`. Teksty są tylko w `analysis/work/out/%s_inserts.jsonl`.' % (release, release),
             'Wstawka to krótki opis zachowania w nawiasie albo gwiazdkach, od małej litery, bez liczb i luk.',
             'Skan czyta tekst z gry. Od D95 `build` wycina z kwestii postaci wstawki na początku zdania, a krótkie '
             'wtrącenie w środku zdania zostaje jako mowa postaci.', '',
             '| Rodzaj | Kwestie postaci | Kwestie narratora |', '|---|---:|---:|']
    for k in ('wstawka', 'inne'):
        lines.append('| %s | %d | %d |' % (k, by_kind[k, True], by_kind[k, False]))
    lines += ['', 'Wstawki w kwestiach postaci: %d w %d kwestiach, %d różnych tekstów.' % (
        len(chars), len({f['key'] for f in chars}), len({f['insert'].lower() for f in chars})), '',
        '## Według głosu', '', '| Głos | Wstawki |', '|---|---:|']
    lines += ['| %s | %d |' % kv for kv in by_voice.most_common()]
    lines += ['', '## Według grupy', '', '| Grupa | Wstawki |', '|---|---:|']
    lines += ['| %s | %d |' % kv for kv in sorted(by_group.items())]
    lines += ['', '## Klucze', '', ', '.join('`%s`' % k for k in sorted({f['key'] for f in chars})), '']
    open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', default='m3')
    a = ap.parse_args()
    found = scan(os.path.join(ROOT, 'analysis', 'work', 'lektor', a.release + '.sqlite'))
    out = os.path.join(ROOT, 'analysis', 'work', 'out', a.release + '_inserts.jsonl')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        for x in found:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    rep = os.path.join(ROOT, 'analysis', 'E14_INSERTS.md')
    report(found, a.release, rep)
    c = collections.Counter((x['kind'], x['voice'] != 'narrator') for x in found)
    print('wstawki postaci %d, narratora %d; inne %d; -> %s, %s' % (
        c['wstawka', True], c['wstawka', False], c['inne', True] + c['inne', False], out, rep))


if __name__ == '__main__':
    main()
