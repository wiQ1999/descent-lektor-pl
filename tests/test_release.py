"""Wydania na kopii gry: M1 buduje się bez zmian (D63). Id fragmentów pomijamy, bo zależą od referencji głosów, a te
zmienia dobór z E7. Uruchamiane z LEKTOR_GAME_TESTS=1."""
import os
import sqlite3

import pytest

from lektor import build, game, paths, scope

pytestmark = pytest.mark.skipif(not os.environ.get('LEKTOR_GAME_TESTS'), reason='potrzebna kopia gry i baza M1')


def rows(path, query):
    con = sqlite3.connect(path)
    try:
        return set(con.execute(query))
    finally:
        con.close()


def test_loot_covers_item_kinds():
    g = game.Game()
    terms = g.terms()
    assert len(scope.loot_keys(g, terms)) > 200
    assert len(build.loot_texts(g, terms)) > 300


def test_m1_build_is_unchanged(tmp_path):
    path = str(tmp_path / 'm1.sqlite')
    build.build(path, 'm1')
    current = os.path.join(paths.OUT, 'm1.sqlite')
    for query in ('SELECT key, grp, category, toggle, voice, text_norm FROM lines', 'SELECT voice, speed, text FROM fragments',
                  'SELECT key, idx, kind, arg FROM segments', 'SELECT key, arg, value FROM slot_values'):
        assert rows(path, query) == rows(current, query), query
