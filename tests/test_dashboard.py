"""Dashboard stanu dialogów: podział na elementy, pokrycie wydań, wybór wersji, strona. Bez modelu, GPU i sieci."""
import json
import os
import sqlite3

import pytest

from lektor import dashboard, db, paths


def make_release(work, release, lines, final=(), takes=(), inherited=(), values=()):
    """lines: {klucz: (grupa, [fragmenty])}; values: [(wartość, fragment)]."""
    os.makedirs(os.path.join(work, 'lektor'), exist_ok=True)
    audio = os.path.join(work, 'audio', release)
    os.makedirs(audio, exist_ok=True)
    con = sqlite3.connect(os.path.join(work, 'lektor', release + '.sqlite'))
    con.executescript(db.SCHEMA)
    con.execute("INSERT INTO meta VALUES ('built_at', '\"2026-01-02T03:04:05\"')")
    for key, (group, frags) in lines.items():
        con.execute('INSERT INTO lines (key, grp, tts, text_raw) VALUES (?, ?, 1, ?)', (key, group, 'Tytuł próbny'))
        con.executemany('INSERT INTO segments (key, idx, kind, fragment) VALUES (?, ?, ?, ?)',
                        [(key, i, 'text', f) for i, f in enumerate(frags)])
    con.executemany('INSERT INTO slot_values VALUES (?, 0, ?, ?)', [('K%d' % i, v, f) for i, (v, f) in enumerate(values)])
    con.commit()
    con.close()
    json.dump({'fragments': {f: {} for f in final}}, open(os.path.join(audio, 'manifest.json'), 'w'))
    json.dump({f: {} for f in inherited}, open(os.path.join(audio, 'inherited.json'), 'w'))
    with open(os.path.join(audio, 'takes.jsonl'), 'w') as fh:
        fh.writelines(json.dumps({'fragment': f, 'take': 1}) + '\n' for f in takes)
        fh.write('{"fragment": "urw')       # urwany wiersz po przerwaniu procesu


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'WORK', str(tmp_path))
    monkeypatch.setattr(paths, 'OUT', str(tmp_path / 'lektor'))
    return str(tmp_path)


def test_element_keeps_missions_apart_and_groups_the_rest():
    assert dashboard.element('story_q1')[:3] == dashboard.element('scene_q1')[:3] == ('a1_main', 'a1_q1', 'Q1')
    assert dashboard.element('q6')[:3] == ('a1_main', 'a1_q6', 'Q6')
    assert dashboard.element('a1_q12')[:3] == ('a1_main', 'a1_q12', 'Q12')
    assert dashboard.element('a1_sq2')[:3] == ('a1_side', 'a1_sq2', 'SQ2')
    assert dashboard.element('a2_q0')[:3] == ('a2_main', 'a2_q0', 'Q0 (wstęp)')
    assert dashboard.element('a2_ss03')[0] == 'a2_side'
    assert [dashboard.element(g)[2] for g in ('event_ec1', 'a1_event_2a', 'a2_se04', 'gear', 'system', 'nowa')] == [
        'Wydarzenia aktu 1', 'Wydarzenia aktu 1', 'Wydarzenia aktu 2', 'Przedmioty i zdolności', 'System i łup', 'Inne']


def test_titles_and_labels():
    assert dashboard.title_groups('E2A_MEETING_NAME') == ('event_e2a', 'a1_event_2a')
    assert dashboard.title_groups('EC1_ORCS_NAME') == ('event_ec1', 'a1_event_1')
    assert dashboard.title_groups('A2SE01_X_NAME') == ('a2_se01',)
    assert dashboard.group_label('a1_event_2a', {'a1_event_2a': 'Tytuł'}) == '2A: Tytuł'
    assert dashboard.group_label('event_e5b', {}) == '5B' and dashboard.group_label('a2_se04', {}) == 'SE04'


def test_pct_never_rounds_to_done_or_to_nothing():
    assert [dashboard.pct(*x) for x in ((0, 10), (10, 10), (999, 1000), (1, 1000), (1, 2), (0, 0))] == [
        '0%', '100%', '99%', '<1%', '50%', '0%']


def test_collect_measures_releases_against_the_widest_database(work):
    make_release(work, 'm1', {'A': ('scene_q1', ['a1']), 'B': ('scene_q1', ['b1'])}, final=['a1', 'b1'])
    make_release(work, 'm3', {'A': ('scene_q1', ['a1']), 'B': ('scene_q1', ['b1']), 'C': ('story_q1', ['c1', 'c2']),
                              'D': ('a2_q1', ['d1']), 'E': ('a2_q1', ['e1']), 'G': ('gear', ['g1'])},
                 final=['a1', 'b1', 'c1'], takes=['c2', 'd1'], inherited=['g1'], values=[('V', 'v1'), ('V', 'v2')])
    data = dashboard.collect()
    assert data['reference'] == 'm3' and data['total'] == 7 and data['any'] == 2
    rows = {r['label']: r for s in data['sections'] if not s['title'].startswith('Akt 2') for r in s['rows']}
    assert rows['Q1']['total'] == 3 and rows['Q1']['rel'] == {'m1': [2, 0], 'm3': [2, 1]}
    assert [g['id'] for g in rows['Q1']['groups']] == ['scene_q1', 'story_q1']
    assert dashboard.best(rows['Q1']) == ('m3', 2, 1)
    q1 = next(r for s in data['sections'] if s['title'].startswith('Akt 2') for r in s['rows'])
    assert q1['rel']['m3'] == [0, 1] and dashboard.best(q1) == ('m3', 0, 1) and q1['groups'] == []
    assert rows['Przedmioty i zdolności']['rel']['m3'] == [0, 1]       # przejęte, jeszcze bez pliku końcowego
    assert rows['System i łup']['total'] == 1 and dashboard.best(rows['System i łup']) is None


def test_best_prefers_the_release_that_made_the_audio():
    assert dashboard.best({'rel': {'m2': [5, 0], 'm3': [5, 0], 't1': [5, 0]}}) == ('m2', 5, 0)
    assert dashboard.best({'rel': {'m2': [5, 0], 'm3': [6, 0]}}) == ('m3', 6, 0)
    assert dashboard.best({'rel': {'m2': [0, 0], 'm3': [0, 0]}}) is None


def test_write_page_and_signature(work, tmp_path):
    assert 'Brak baz kwestii' in dashboard.render(dashboard.collect())
    make_release(work, 'm1', {'A': ('scene_q1', ['a1']), 'T': ('a1_sq1', ['t1'])}, final=['a1'])
    before = dashboard.signature()
    page = open(dashboard.write(str(tmp_path / 'out' / 'index.html')), encoding='utf-8').read()
    assert 'Akt 1: misje główne' in page and 'Akt 1: misje poboczne' in page and '>M1<' in page
    assert '<span class="tag off">brak</span>' in page and '50%' in page
    with open(os.path.join(work, 'audio', 'm1', 'takes.jsonl'), 'a') as fh:
        fh.write('\n' + json.dumps({'fragment': 't1', 'take': 1}) + '\n')
    assert dashboard.signature() != before
    assert dashboard.collect()['releases'][0]['made'] == 1
