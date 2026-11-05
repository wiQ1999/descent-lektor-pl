import hashlib
import io
import os
import tomllib
import zipfile

import pytest

from lektor import bundle as B
from lektor.companion import config as C


@pytest.fixture
def fake(tmp_path, monkeypatch):
    """Plugin z builda i Doorstop z cache zastąpione małymi plikami w katalogu tymczasowym."""
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    for name in B.PLUGIN_FILES:
        (bin_dir / name).write_bytes(b'MZ' + name.encode())
    monkeypatch.setattr(B, 'PLUGIN_BIN', str(bin_dir))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('x86/winhttp.dll', b'doorstop x86')
        z.writestr('x86/.doorstop_version', b'4.6.0')
        z.writestr('x64/winhttp.dll', b'doorstop x64')
    data = buf.getvalue()
    (tmp_path / 'doorstop.zip').write_bytes(data)
    pin = {'url': 'https://example.invalid/doorstop.zip', 'sha256': hashlib.sha256(data).hexdigest(),
           'dir': 'doorstop', 'files': ['x86/winhttp.dll', 'x86/.doorstop_version']}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('universal/libdoorstop.dylib', b'doorstop universal')
        z.writestr('universal/.doorstop_version', b'4.6.0')
    mac_data = buf.getvalue()
    mac = {'url': 'https://example.invalid/doorstop-mac.zip', 'sha256': hashlib.sha256(mac_data).hexdigest(),
           'dir': 'doorstop', 'files': ['universal/libdoorstop.dylib', 'universal/.doorstop_version']}
    monkeypatch.setattr(B, 'pins', lambda: {'doorstop': {'win': pin, 'mac': mac}})
    monkeypatch.setattr(B, 'CACHE', str(tmp_path))
    (tmp_path / 'doorstop').mkdir()
    (tmp_path / 'doorstop' / 'doorstop.zip').write_bytes(data)
    (tmp_path / 'doorstop' / 'doorstop-mac.zip').write_bytes(mac_data)
    return tmp_path


def test_pins_have_sha256_for_every_download():
    pins = B.pins()
    assert set(pins) == {'doorstop', 'python'} and all(set(g) == {'win', 'mac'} for g in pins.values())
    for group in pins.values():
        for pin in group.values():
            assert len(pin['sha256']) == 64 and pin['url'].startswith('https://')
    assert all(pin['files'] for pin in pins['doorstop'].values())


def test_wheel_requirements_are_hashed_and_match_venv():
    from importlib.metadata import version
    for platform in ('win', 'mac'):
        text = open(os.path.join(B.SRC, 'requirements-%s.txt' % platform), encoding='utf-8').read()
        pinned = dict(line.split(' ')[0].split('==') for line in text.splitlines() if '==' in line)
        assert '--hash=sha256:' in text and set(pinned) >= {'numpy', 'sounddevice', 'soundfile'}
        assert all(pinned[p] == version(p) for p in ('numpy', 'sounddevice', 'soundfile'))


def test_bundle_lektor_subset_has_whole_companion():
    companion = {'companion/' + f for f in os.listdir(os.path.join(B.paths.ROOT, 'src', 'lektor', 'companion')) if f.endswith('.py')}
    assert companion <= set(B.LEKTOR)


def test_zip_keeps_exec_bits_and_utf8_names(tmp_path):
    dest = tmp_path / 'Descent-Lektor-PL'
    (dest / 'skrypty').mkdir(parents=True)
    (dest / 'Zainstaluj.command').write_text('#!/bin/bash\n', encoding='utf-8')
    (dest / 'Wyłącz lektora.command').write_text('#!/bin/bash\n', encoding='utf-8')
    (dest / 'skrypty' / 'start.sh').write_text('#!/bin/bash\n', encoding='utf-8')
    (dest / 'ustawienia.toml').write_text('volume = 1.0\n', encoding='utf-8')
    path = B.write_zip(str(dest), str(tmp_path / 'p.zip'))
    with zipfile.ZipFile(path) as z:
        modes = {i.filename: (i.external_attr >> 16) & 0o777 for i in z.infolist()}
        assert modes['Descent-Lektor-PL/Zainstaluj.command'] == 0o755 and modes['Descent-Lektor-PL/skrypty/start.sh'] == 0o755
        assert modes['Descent-Lektor-PL/ustawienia.toml'] == 0o644 and 'Descent-Lektor-PL/logs/' in modes
        assert z.getinfo('Descent-Lektor-PL/Wyłącz lektora.command').flag_bits & 0x800


def test_settings_template_is_valid_toml_with_relative_paths(tmp_path):
    text = B.settings_text(dev=False)
    cfg = tomllib.loads(text)
    assert cfg['db'] == 'dane/m1.sqlite' and cfg['plugin'] == {'autostart': True}
    assert set(cfg['toggles']) == set(C.TOGGLES) and '@' not in text
    f = tmp_path / 'paczka' / 'ustawienia.toml'
    f.parent.mkdir()
    f.write_text(text, encoding='utf-8')
    assert C.load(str(f))['audio'] == str(tmp_path / 'paczka' / 'dane')


def test_dev_settings_point_to_repository_and_venv():
    cfg = tomllib.loads(B.settings_text(dev=True))
    assert os.path.normpath(cfg['db']) == os.path.normpath(B.paths.DB)
    assert cfg['plugin']['python'].endswith('.venv/Scripts/python.exe')


def test_settings_with_bom_from_notepad_load(tmp_path):
    f = tmp_path / 'ustawienia.toml'
    f.write_bytes(b'\xef\xbb\xbf' + B.settings_text(dev=False).encode('utf-8'))
    assert C.load(str(f))['port'] == 47810


def test_win_bundle_layout_and_line_endings(fake, monkeypatch):
    monkeypatch.setattr(B, 'copy_python', lambda platform, dest: None)     # Python i audio sprawdza budowa paczki
    monkeypatch.setattr(B, 'copy_data', lambda dest: 0)
    dest = B.build('win', out=str(fake / 'out'))
    files = sorted(B.files_of(dest))
    assert files == sorted(['INSTRUKCJA.md', 'Odinstaluj.cmd', 'Test dźwięku.cmd', 'Ustawienia.cmd', 'Wyłącz lektora.cmd',
                            'Włącz lektora.cmd', 'Zainstaluj.cmd', 'loader/.doorstop_version', 'loader/winhttp.dll',
                            'plugin/LektorPL.Core.dll', 'plugin/LektorPL.Loader.dll', 'skrypty/lektor.ps1',
                            'skrypty/pliki.sha256', 'ustawienia.toml', 'wersja.txt'] + ['lektor/' + f for f in B.LEKTOR])
    sums = open(os.path.join(dest, 'skrypty', 'pliki.sha256'), encoding='utf-8').read().splitlines()
    assert len(sums) == len(files) - 1 and all(len(line.split('  ')[0]) == 64 for line in sums)
    assert open(os.path.join(dest, 'loader', 'winhttp.dll'), 'rb').read() == b'doorstop x86'
    cmd = open(os.path.join(dest, 'Zainstaluj.cmd'), 'rb').read()
    assert b'\r\n' in cmd and b'\n' not in cmd.replace(b'\r\n', b'')
    ps1 = open(os.path.join(dest, 'skrypty', 'lektor.ps1'), 'rb').read()
    assert ps1.startswith(b'\xef\xbb\xbf') and not ps1.startswith(b'\xef\xbb\xbf\xef\xbb\xbf')
    assert b'\n' not in ps1.replace(b'\r\n', b'')
    assert b'\r' not in open(os.path.join(dest, 'ustawienia.toml'), 'rb').read()


def test_mac_bundle_layout_and_unix_scripts(fake, monkeypatch):
    monkeypatch.setattr(B, 'copy_python', lambda platform, dest: None)
    monkeypatch.setattr(B, 'copy_data', lambda dest: 0)
    dest = B.build('mac', out=str(fake / 'out'))
    commands = ['Odinstaluj', 'Test dźwięku', 'Ustawienia', 'Wyłącz lektora', 'Włącz lektora', 'Zainstaluj']
    assert sorted(B.files_of(dest)) == sorted(
        ['INSTRUKCJA.md', 'loader/.doorstop_version', 'loader/libdoorstop.dylib', 'plugin/LektorPL.Core.dll',
         'plugin/LektorPL.Loader.dll', 'skrypty/lektor.sh', 'skrypty/pliki.sha256', 'skrypty/start.sh',
         'ustawienia.toml', 'wersja.txt'] + [c + '.command' for c in commands] + ['lektor/' + f for f in B.LEKTOR])
    for rel in [c + '.command' for c in commands] + ['skrypty/lektor.sh', 'skrypty/start.sh']:
        data = open(os.path.join(dest, rel), 'rb').read()
        assert data.startswith(b'#!/bin/bash\n') and b'\r' not in data, rel
    assert 'macOS' in open(os.path.join(dest, 'wersja.txt'), encoding='utf-8').read()


def test_dev_rebuild_keeps_state_logs_and_settings(fake):
    dest = str(fake / 'dev')
    B.build('win', dev=True, out=dest)
    os.makedirs(os.path.join(dest, 'stan'))
    for name, text in (('stan/instalacja.txt', 'game=x'), ('logs/hook-1.jsonl', '{}'), ('ustawienia.toml', 'volume = 0.5\n' + B.settings_text(True))):
        with open(os.path.join(dest, name), 'w', encoding='utf-8') as fh:
            fh.write(text)
    B.build('win', dev=True, out=dest)
    assert open(os.path.join(dest, 'ustawienia.toml'), encoding='utf-8').read().startswith('volume = 0.5\n')
    assert os.path.exists(os.path.join(dest, 'logs', 'hook-1.jsonl')) and os.path.exists(os.path.join(dest, 'stan', 'instalacja.txt'))


def test_bad_download_sum_stops_build(fake, monkeypatch):
    bad = dict(B.pins()['doorstop']['win'], sha256='0' * 64)
    monkeypatch.setattr(B, 'pins', lambda: {'doorstop': {'win': bad}})
    with pytest.raises(SystemExit, match='SHA-256'):
        B.build('win', dev=True, out=str(fake / 'out'))


def test_dev_settings_follow_release(tmp_path):
    from lektor import bundle, paths
    old = paths.RELEASE
    path = tmp_path / 'ustawienia.toml'
    try:
        paths.use('m1')
        path.write_text('db = "%s"' % paths.DB.replace('\\', '/'), encoding='utf-8')
        assert bundle.keep_settings(str(path), True)
        assert not bundle.keep_settings(str(path), False)
        paths.use('m2')
        assert not bundle.keep_settings(str(path), True)
    finally:
        paths.use(old)
