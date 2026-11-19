import json
import os
import zipfile

import pytest

from lektor import parts as P


def make_bundle(root, audio, program=b'plugin v1'):
    files = {'wersja.txt': 'plugin: 0.5.0\nzbudowano: 2026-11-19 22:44, commit abc\n',
             'ustawienia.toml': 'volume = 1.0\n', 'plugin/LektorPL.Loader.dll': program,
             'python/python.exe': b'MZ python', 'stan/instalacja.txt': 'game=x', 'logs/companion.jsonl': '{}',
             'zgloszenia/1.png': b'png', 'dane/m4.sqlite': b'db'}
    files.update({'dane/final/%s.flac' % k: v for k, v in audio.items()})
    for rel, data in files.items():
        path = os.path.join(root, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(data.encode() if isinstance(data, str) else data)
    return str(root)


def manifest(out):
    with open(os.path.join(out, 'lektor-win.json'), encoding='utf-8') as fh:
        return json.load(fh)


def effective(out, m):
    """Pliki po instalacji: części w kolejności manifestu, tylko pliki z ich list."""
    state = {}
    for p in m['parts']:
        with zipfile.ZipFile(os.path.join(out, p['name'])) as z:
            for rel in p['files']:
                state[rel] = z.read(rel)
    return state


@pytest.fixture
def dirs(tmp_path):
    return tmp_path / 'src', str(tmp_path / 'out')


def test_parts_split_kinds_and_skip_user_files(dirs):
    src, out = dirs
    P.build('win', make_bundle(src, {'a': b'A1', 'b': b'B1'}), out)
    m = manifest(out)
    assert [p['kind'] for p in m['parts']] == ['python', 'program', 'audio']
    files = effective(out, m)
    assert files[P.DEFAULTS] == b'volume = 1.0\n'
    assert 'ustawienia.toml' not in files
    assert not any(f.split('/')[0] in ('stan', 'logs', 'zgloszenia') for f in files)
    assert m['version'] == 'plugin 0.5.0, zbudowano 2026-11-19 22:44'
    with open(os.path.join(out, 'instalator-win.ps1'), 'rb') as fh:
        data = fh.read()
    assert data.startswith(b'\xef\xbb\xbf') and b'\r\n' in data and b'\n' not in data.replace(b'\r\n', b'')
    with open(os.path.join(out, 'instaluj-win.ps1'), 'rb') as fh:
        data = fh.read()
    assert data.decode('ascii') and b'\n' not in data.replace(b'\r\n', b'')     # starter dla irm | iex


def test_unchanged_build_keeps_names(dirs):
    src, out = dirs
    bundle = make_bundle(src, {'a': b'A1'})
    first = manifest(P.build('win', bundle, out))
    os.utime(os.path.join(bundle, 'dane', 'final', 'a.flac'), (1, 1))     # data pliku nie zmienia części
    second = manifest(P.build('win', bundle, out))
    assert first['id'] == second['id']
    assert [p['name'] for p in first['parts']] == [p['name'] for p in second['parts']]


def test_audio_update_adds_layer_with_changes_only(dirs):
    src, out = dirs
    bundle = make_bundle(src, {'a': b'A1', 'b': b'B1', 'c': b'C1'})
    first = manifest(P.build('win', bundle, out))
    make_bundle(src, {'a': b'A2', 'd': b'D1'})                          # a zmienione, d nowe
    os.remove(os.path.join(bundle, 'dane', 'final', 'c.flac'))          # c usunięte
    second = manifest(P.build('win', bundle, out))
    audio = [p for p in second['parts'] if p['kind'] == 'audio']
    assert audio[0]['name'] == first['parts'][2]['name']               # stara warstwa bez ponownego pobierania
    assert audio[0]['files'] == ['dane/final/b.flac']
    assert audio[1]['files'] == ['dane/final/a.flac', 'dane/final/d.flac']
    files = effective(out, second)
    assert {k: v for k, v in files.items() if k.startswith('dane/final/')} == {
        'dane/final/a.flac': b'A2', 'dane/final/b.flac': b'B1', 'dane/final/d.flac': b'D1'}


def test_fully_covered_layer_drops_out_and_is_pruned(dirs):
    src, out = dirs
    bundle = make_bundle(src, {'a': b'A1'})
    old = manifest(P.build('win', bundle, out))['parts'][2]['name']
    make_bundle(src, {'a': b'A2'})
    m = manifest(P.build('win', bundle, out))
    assert [p['name'] for p in m['parts'] if p['kind'] == 'audio'] != [old]
    assert not os.path.exists(os.path.join(out, old))


def test_fresh_starts_single_layer(dirs):
    src, out = dirs
    bundle = make_bundle(src, {'a': b'A1', 'b': b'B1'})
    P.build('win', bundle, out)
    make_bundle(src, {'a': b'A2'})
    m = manifest(P.build('win', bundle, out, fresh=True))
    audio = [p for p in m['parts'] if p['kind'] == 'audio']
    assert len(audio) == 1 and audio[0]['files'] == ['dane/final/a.flac', 'dane/final/b.flac']


def test_large_layer_is_chunked(dirs, monkeypatch):
    src, out = dirs
    monkeypatch.setattr(P, 'CHUNK', 4)
    m = manifest(P.build('win', make_bundle(src, {'a': b'AAA', 'b': b'BBB', 'c': b'CCC'}), out))
    audio = [p for p in m['parts'] if p['kind'] == 'audio']
    assert [p['files'] for p in audio] == [['dane/final/a.flac', 'dane/final/b.flac'], ['dane/final/c.flac']]


def test_mac_is_not_supported_yet(dirs):
    src, out = dirs
    with pytest.raises(SystemExit):
        P.build('mac', make_bundle(src, {}), out)
