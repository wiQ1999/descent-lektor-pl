"""Raport liczności bazy M1 (analysis/E2_DATA.md). Tylko liczby i klucze techniczne, bez tekstów gry."""
import glob
import json
import os
from collections import Counter

from . import db, paths
from . import direction as D
from . import segment as S
from .build import SPRITE

# OmniVoice fp16, 32 kroki na GTX 1650 Ti (E0, BAKEOFF.md): wywołanie kosztuje ok. 60 s stałego czasu
# i ok. 10 s na sekundę audio; tempo 1,2 daje ok. 12,1 znaku/s audio.
CALL_S, PER_AUDIO_S = 60.0, 10.0
CPS = 10.1              # znaki na sekundę audio przy tempie 1,0
HERO_TAKES = 3          # D38
HEROES = ('brynn', 'syrus', 'galaden', 'vaerix', 'kehli', 'chance')


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def grouped(con, col, where='1'):
    return con.execute('SELECT %s, COUNT(*), SUM(tts), SUM(COALESCE(chars, 0)) FROM lines WHERE %s '
                       'GROUP BY 1 ORDER BY 3 DESC, 1' % (col, where)).fetchall()


def audio_seconds(chars, speed):
    return chars / CPS / (speed or 1.0)


def e1_coverage(con):
    """Wartości luk z dzienników E1 (%LOCALAPPDATA%/LektorPL/logs) względem inwentarza w bazie."""
    logs = sorted(glob.glob(os.path.join(os.environ.get('LOCALAPPDATA', ''), 'LektorPL', 'logs', '*.jsonl')))
    if not logs:
        return []
    have = {(k, a, v) for k, a, v in con.execute('SELECT key, arg, value FROM slot_values')}
    slots = {(k, a) for k, a in con.execute("SELECT key, arg FROM segments WHERE kind = 'slot'")}
    lines = {k for (k,) in con.execute('SELECT key FROM lines')}
    seen, ok, miss = set(), Counter(), Counter()
    for p in logs:
        for raw in open(p, encoding='utf-8'):
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if e.get('key') not in lines:
                continue
            for i, a in enumerate(e.get('args') or []):
                if not isinstance(a, dict):
                    continue
                t, v = a.get('type'), a.get('as_key')
                if t == 'VariableInt':
                    v = a.get('value', v)
                elif t == 'EntityName' and v:
                    v = SPRITE.sub('', v).split(' (')[0]  # alias bossa to osobna wartość
                arg = i if (e['key'], i) in slots else -1  # {n}: jedna luka na wszystkie argumenty
                if (e['key'], i, str(v)) in seen or (e['key'], arg) not in slots:
                    continue  # argument bez luki w tekście (gra przekazuje go mimo to)
                seen.add((e['key'], i, str(v)))
                if (e['key'], arg, str(v)) in have:
                    ok[t] += 1
                else:
                    miss[t, e['key']] += 1
    s = ['### Pokrycie wartości z sesji E1', '',
         'Unikalne pary (kwestia, wartość) z dzienników E1 dla kwestii z bazy: %d w inwentarzu, %d poza nim.' % (
             sum(ok.values()), sum(miss.values())), '']
    s += ['- `%s` (%s): %d' % (k, t, n) for (t, k), n in sorted(miss.items(), key=str)]
    return s + ['', 'Wartości spoza inwentarza companion obsłuży syntezą na żywo albo pominie (E4).', '']


def report(path=paths.DB):
    con = db.connect(path)
    meta = {r['k']: json.loads(r['v']) for r in con.execute('SELECT * FROM meta')}
    n_lines, n_tts = con.execute('SELECT COUNT(*), SUM(tts) FROM lines').fetchone()
    frags = con.execute('SELECT voice, speed, chars, kind FROM fragments').fetchall()
    refs = {r['voice'] for r in con.execute('SELECT voice FROM refs')}
    s = ['# E2: baza kwestii M1', '',
         'Wygenerowano przez `python -I -m lektor report` z `%s` (zbudowana %s, pakiet %s, model `%s`, '
         'manifest gry `%s`). Raport zawiera tylko liczby i klucze techniczne.' % (
             paths.rel(path), meta['built_at'], meta['version'], meta['model_id'], meta['manifest'][:12]), '',
         '## Kwestie', '',
         'Kluczy: **%d**, z tego do syntezy **%d** (pozostałe to napisy przerywników z dubbingiem, D14).' % (n_lines, n_tts),
         'Wrogowie w zakresie: %s. Grafy Q1: %d. Klucze przerywnika: %d.' % (
             ', '.join('`%s`' % e for e in meta['scope']['enemies']), meta['scope']['q1_graphs'],
             meta['scope']['cutscene_keys']), '']
    for title, col in (('Grupa zakresu', 'grp'), ('Kategoria', 'category'), ('Głos', 'voice'),
                       ('Przełącznik companiona', 'toggle')):
        s += ['### ' + title, '', table((title.lower(), 'klucze', 'do syntezy', 'znaki'), grouped(con, col)), '']

    s += ['## Segmenty i fragmenty', '']
    seg = con.execute('SELECT kind, COUNT(*) FROM segments GROUP BY 1 ORDER BY 2 DESC').fetchall()
    s += [table(('rodzaj segmentu', 'liczba'), seg), '']
    by_kind = Counter(f['kind'] for f in frags)
    s += ['Unikalnych fragmentów do syntezy: **%d** (%s), znaków: %d.' % (
        len(frags), ', '.join('%s %d' % kv for kv in by_kind.most_common()), sum(f['chars'] for f in frags)), '']
    longest = max((f['chars'] for f in frags), default=0)
    s += ['Najdłuższy fragment: %d znaków.' % longest, '']

    s += ['## Luki {n} (D16)', '']
    slots = con.execute("SELECT arg_type, COUNT(*), COUNT(DISTINCT key) FROM segments WHERE kind = 'slot' "
                        'GROUP BY 1 ORDER BY 2 DESC').fetchall()
    vals = {r[0]: r[1:] for r in con.execute(
        'SELECT s.arg_type, COUNT(*), SUM(v.fragment IS NULL), COUNT(DISTINCT v.fragment) FROM slot_values v '
        "JOIN segments s ON s.key = v.key AND s.arg = v.arg AND s.kind = 'slot' GROUP BY 1")}
    s += [table(('typ luki', 'luki', 'kwestie', 'wartości', 'w tym audio innej kwestii', 'unikalne fragmenty'),
                [(t or '?', n, k, *vals.get(t, (0, 0, 0))) for t, n, k in slots]), '',
          'Wartość „audio innej kwestii” to klucz z bazy (np. cel misji), którego nagranie companion odtwarza w luce. '
          'Liczby: %d–%d. Wartości luk mają jedno tempo %.1f.' % (S.NUMBER_VALUES[0], S.NUMBER_VALUES[-1], D.SPEED_MIN), '']
    fb = con.execute("SELECT key, note FROM lines WHERE note LIKE 'luka%' ORDER BY key").fetchall()
    s += ['Kwestie z luką bez znanych wartości (companion użyje syntezy na żywo albo pominie lukę): %d.' % len(fb), '']
    s += ['- `%s`: %s' % (r['key'], r['note']) for r in fb] + ([''] if fb else [])

    s += e1_coverage(con)
    s += ['## Do przejrzenia', '']
    multi = con.execute('SELECT key, speakers FROM lines WHERE json_array_length(speakers) > 1 ORDER BY key').fetchall()
    s += ['Kwestie z kilkoma mówcami w grafach (głos z pierwszego rozpoznanego): %d.' % len(multi), '']
    s += ['- `%s`: %s' % (r['key'], ', '.join(json.loads(r['speakers']))) for r in multi] + ([''] if multi else [])
    other = con.execute("SELECT key, speakers FROM lines WHERE voice = 'inny' ORDER BY key").fetchall()
    s += ['Dialogi bez przypisanego głosu (`inny`): %d.' % len(other), '']
    s += ['- `%s`: %s' % (r['key'], ', '.join(json.loads(r['speakers']))) for r in other] + ([''] if other else [])
    noq = con.execute("SELECT key FROM lines WHERE note = 'cytat bez rozpoznanego bohatera' ORDER BY key").fetchall()
    s += ['Opcje wyboru z cytatem bez rozpoznanego bohatera (cytat głosem narratora): %d.' % len(noq), '']
    s += ['- `%s`' % r['key'] for r in noq] + ([''] if noq else [])
    voices = sorted({f['voice'] for f in frags})
    missing = [v for v in voices if v not in refs]
    s += ['Głosy fragmentów bez referencji w bazie: %s.' % (', '.join('`%s`' % v for v in missing) or 'brak'), '']

    s += ['## Szacunek generowania (E3)', '']
    rows, total = [], 0.0
    for v in voices:
        fv = [f for f in frags if f['voice'] == v]
        audio = sum(audio_seconds(f['chars'], f['speed']) for f in fv)
        takes = HERO_TAKES if v in HEROES else 1
        gpu = (len(fv) * CALL_S + audio * PER_AUDIO_S) * takes
        total += gpu
        rows.append((v, len(fv), sum(f['chars'] for f in fv), '%.1f' % (audio / 60), takes, '%.1f' % (gpu / 3600)))
    by_kind_gpu = Counter()
    for f in frags:
        by_kind_gpu[f['kind']] += CALL_S + audio_seconds(f['chars'], f['speed']) * PER_AUDIO_S
    s += [table(('głos', 'fragmenty', 'znaki', 'audio min', 'podejścia', 'GPU h'), rows), '',
          'Razem ok. **%.1f h** GPU bez retake, przy obecnym wywołaniu po jednym fragmencie (%.0f s na wywołanie '
          '+ %.0f s na sekundę audio, %.1f znaku/s przy tempie 1,0). Jedno podejście według rodzaju fragmentu: %s.' % (
              total / 3600, CALL_S, PER_AUDIO_S, CPS,
              ', '.join('%s %.1f h' % (k, v / 3600) for k, v in by_kind_gpu.most_common())), '']
    out = paths.ROOT + '/analysis/E2_DATA.md'
    open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(s))
    return out
