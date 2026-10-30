"""Płeć mówców z tekstów PL: formy 1. osoby czasu przeszłego/trybu przypuszczającego (-łem/-łam, -łbym/-łabym),
przymiotniki po „jestem” oraz tytuł w nazwie postaci (Baronessa, Mistrzyni…). Wynik: liczby, bez tekstów.

Wejście: work/out/{pl_terms.json,lines.jsonl}; nazwy postaci z bundla d3/storymessagecharacters.
Wyjście: work/out/speaker_gender.json i tabela Markdown na stdout.

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/speaker_gender.py
"""
import json
import os
import re
import sys
from collections import defaultdict

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLES = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')
OUT = os.path.join(ROOT, 'work', 'out')
TAG = re.compile(r'<[^>]+>')
MASC = re.compile(r'\b\w+(?:łem|łbym)\b|\bjestem\s+\w+(?:y|i)\b', re.I)
FEM = re.compile(r'\b\w+(?:łam|łabym)\b|\bjestem\s+\w+a\b', re.I)
# fałszywe trafienia: rzeczowniki/czasowniki zakończone na -łam/-łem, które nie są formą 1. os.
FALSE = {'przełam', 'złam', 'połam', 'wyłam', 'hełm', 'hełmem', 'wyłom', 'jestem sama', 'jestem tutaj', 'jestem tu'}
F_TITLES = ('baronessa', 'hrabina', 'mistrzyni', 'strażniczka', 'poruczniczka', 'dzwonniczka', 'władczyni', 'królowa', 'księżniczka')
M_TITLES = ('baron ', 'hrabia', 'mistrz ', 'sir ', 'książę', 'szaman', 'król ')


def character_names(terms):
    m = json.load(open(os.path.join(BUNDLES, 'manifest.dat'), encoding='utf-8'))
    fn = next(b['filename'] for b in m['bundleInfos'] if b['name'] == 'd3/storymessagecharacters')
    names = {}
    for o in UnityPy.load(os.path.join(BUNDLES, fn)).objects:
        if o.type.name == 'MonoBehaviour':
            t = o.read_typetree()
            if t.get('_id'):
                names[t['_id'].replace('STORY_CHARACTER_', '')] = (terms.get(t.get('KeyName')) or {}).get('text') or ''
    return names


def main():
    terms = json.load(open(os.path.join(OUT, 'pl_terms.json'), encoding='utf-8'))
    names = character_names(terms)
    keys_of = defaultdict(set)
    for l in open(os.path.join(OUT, 'lines.jsonl'), encoding='utf-8'):
        r = json.loads(l)
        if len(r['speakers']) == 1:
            keys_of[r['speakers'][0].replace('STORY_CHARACTER_', '')].add(r['key'])
    res = {}
    for sp, keys in sorted(keys_of.items(), key=lambda kv: -len(kv[1])):
        m = f = 0
        for k in keys:
            txt = TAG.sub('', (terms.get(k) or {}).get('text') or '')
            m += sum(1 for x in MASC.findall(txt) if x.lower() not in FALSE)
            f += sum(1 for x in FEM.findall(txt) if x.lower() not in FALSE)
        name = names.get(sp, '')
        low = name.lower() + ' '
        title = 'F' if low.startswith(F_TITLES) else 'M' if low.startswith(M_TITLES) else ''
        if m + f >= 3:
            verdict = 'M' if m >= 3 * f else 'F' if f >= 3 * m else '?'
        else:
            verdict = title or '?'
        if title and verdict not in ('?', title):
            verdict = '?'
        res[sp] = {'name': name, 'keys': len(keys), 'masc_forms': m, 'fem_forms': f, 'title': title, 'text_verdict': verdict}
    json.dump(res, open(os.path.join(OUT, 'speaker_gender.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print('| Mówca | Nazwa PL | Kwestie | -łem/-łbym | -łam/-łabym | Tytuł | Z tekstu |')
    print('|---|---|---:|---:|---:|---|---|')
    for sp, v in res.items():
        print('| `%s` | %s | %d | %d | %d | %s | %s |' % (sp, v['name'], v['keys'], v['masc_forms'], v['fem_forms'],
                                                         v['title'] or '–', v['text_verdict']))


if __name__ == '__main__':
    main()
