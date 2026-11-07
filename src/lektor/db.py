"""Baza kwestii (SQLite, nieśledzona: analysis/work/lektor/m1.sqlite).

lines        kwestia (klucz okna): grupa, kategoria, przełącznik, głos, tempo, tekst surowy i znormalizowany
segments     kolejne części kwestii: tekst (fragment do syntezy), luka {n} albo cytat/opis opcji (D20)
slot_values  wartości luk: dla kwestii i numeru luki fragment każdej możliwej wartości (D16)
fragments    unikalne fragmenty do wygenerowania w E3 (id = klucz cache)
refs         referencje głosów (wycinek do 10 s z transkrypcją, D33)
meta         wersje: pakiet, model, manifest gry, data budowy
"""
import json
import os
import sqlite3

SCHEMA = '''
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE lines (
  key TEXT PRIMARY KEY, grp TEXT, category TEXT, toggle TEXT, voice TEXT, speakers TEXT, hero_variant TEXT,
  role TEXT, node_type TEXT, owner TEXT, seq INTEGER, tts INTEGER, text_raw TEXT, text_norm TEXT, args TEXT,
  chars INTEGER, speed REAL, pause REAL, note TEXT);
CREATE TABLE segments (
  key TEXT, idx INTEGER, kind TEXT, arg INTEGER, arg_type TEXT, voice TEXT, text TEXT, fragment TEXT,
  pause_after REAL, PRIMARY KEY (key, idx));
CREATE TABLE slot_values (key TEXT, arg INTEGER, value TEXT, fragment TEXT, PRIMARY KEY (key, arg, value));
CREATE TABLE fragments (id TEXT PRIMARY KEY, voice TEXT, speed REAL, text TEXT, chars INTEGER, kind TEXT);
CREATE TABLE refs (voice TEXT PRIMARY KEY, wav TEXT, text TEXT, seconds REAL, source TEXT, sha TEXT);
'''


def write(path, meta, lines, segments, slot_values, fragments, refs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    con.executemany('INSERT INTO meta VALUES (?, ?)', [(k, json.dumps(v, ensure_ascii=False)) for k, v in meta.items()])
    con.executemany('INSERT INTO lines VALUES (%s)' % ','.join('?' * 19), [(
        r['key'], r['group'], r['category'], r['toggle'], r['voice'], json.dumps(r['speakers']),
        json.dumps(r['hero_variant']), r['role'], r['node_type'], r['owner'], r['seq'], r['tts'], r['text_raw'],
        r.get('text_norm'), json.dumps(r['args'], ensure_ascii=False), r.get('chars'), r.get('speed'), r.get('pause'),
        r.get('note')) for r in lines])
    con.executemany('INSERT INTO segments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [(
        s['key'], s['idx'], s['kind'], s.get('arg'), s.get('arg_type'), s['voice'], s.get('text'), s.get('fragment'),
        s.get('pause_after')) for s in segments])
    con.executemany('INSERT INTO slot_values VALUES (?, ?, ?, ?)', slot_values)
    con.executemany('INSERT INTO fragments VALUES (?, ?, ?, ?, ?, ?)', [(
        f['id'], f['voice'], f['speed'], f['text'], len(f['text']), f['kind']) for f in fragments.values()])
    con.executemany('INSERT INTO refs VALUES (?, ?, ?, ?, ?, ?)', [(
        v, r['wav'], r['text'], r['seconds'], r['source'], r['sha']) for v, r in refs.items()])
    con.commit()
    con.close()
    os.replace(tmp, path)


def connect(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con
