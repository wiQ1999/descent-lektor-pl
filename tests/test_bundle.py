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
    monkeypatch.setattr(B, 'pins', lambda: {'doorstop': {'win': pin}})
    monkeypatch.setattr(B, 'CACHE', str(tmp_path))
    (tmp_path / 'doorstop').mkdir()
    (tmp_path / 'doorstop' / 'doorstop.zip').write_bytes(data)
    return tmp_path


def test_pins_have_sha256_for_every_download():
    for group in B.pins().values():
        for pin in group.values():
            assert len(pin['sha256']) == 64 and pin['url'].startswith('https://') and pin['files']


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


def test_win_bundle_layout_and_line_endings(fake):
    dest = B.build('win', out=str(fake / 'out'))
    files = sorted(os.path.relpath(os.path.join(b, f), dest).replace(os.sep, '/') for b, _, fs in os.walk(dest) for f in fs)
    assert files == sorted(['Odinstaluj.cmd', 'Test dźwięku.cmd', 'Ustawienia.cmd', 'Wyłącz lektora.cmd', 'Włącz lektora.cmd',
                            'Zainstaluj.cmd', 'loader/.doorstop_version', 'loader/winhttp.dll',
                            'plugin/LektorPL.Core.dll', 'plugin/LektorPL.Loader.dll', 'skrypty/lektor.ps1', 'ustawienia.toml'])
    assert open(os.path.join(dest, 'loader', 'winhttp.dll'), 'rb').read() == b'doorstop x86'
    cmd = open(os.path.join(dest, 'Zainstaluj.cmd'), 'rb').read()
    assert b'\r\n' in cmd and b'\n' not in cmd.replace(b'\r\n', b'')
    ps1 = open(os.path.join(dest, 'skrypty', 'lektor.ps1'), 'rb').read()
    assert ps1.startswith(b'\xef\xbb\xbf') and not ps1.startswith(b'\xef\xbb\xbf\xef\xbb\xbf')
    assert b'\n' not in ps1.replace(b'\r\n', b'')
    assert b'\r' not in open(os.path.join(dest, 'ustawienia.toml'), 'rb').read()


def test_dev_rebuild_keeps_state_logs_and_settings(fake):
    dest = str(fake / 'dev')
    B.build('win', dev=True, out=dest)
    os.makedirs(os.path.join(dest, 'stan'))
    for name, text in (('stan/instalacja.txt', 'game=x'), ('logs/hook-1.jsonl', '{}'), ('ustawienia.toml', 'volume = 0.5\n')):
        with open(os.path.join(dest, name), 'w', encoding='utf-8') as fh:
            fh.write(text)
    B.build('win', dev=True, out=dest)
    assert open(os.path.join(dest, 'ustawienia.toml'), encoding='utf-8').read() == 'volume = 0.5\n'
    assert os.path.exists(os.path.join(dest, 'logs', 'hook-1.jsonl')) and os.path.exists(os.path.join(dest, 'stan', 'instalacja.txt'))


def test_bad_download_sum_stops_build(fake, monkeypatch):
    bad = dict(B.pins()['doorstop']['win'], sha256='0' * 64)
    monkeypatch.setattr(B, 'pins', lambda: {'doorstop': {'win': bad}})
    with pytest.raises(SystemExit, match='SHA-256'):
        B.build('win', out=str(fake / 'out'))
