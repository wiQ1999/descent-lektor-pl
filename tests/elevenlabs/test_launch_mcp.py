import subprocess

import common
import launch_mcp as L
from conftest import KEY


def stub_run(monkeypatch):
    calls = []

    def run(command, env, cwd):
        calls.append((command, env, cwd))
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(L.subprocess, 'run', run)
    monkeypatch.setattr(L.shutil, 'which', lambda name: '/bin/' + name)
    return calls


def test_server_gets_key_and_paths_from_repo(box, monkeypatch, capsys):
    calls = stub_run(monkeypatch)
    assert L.main() == 7
    [(command, env, cwd)] = calls
    assert command == ['/bin/uvx', '--python', L.PYTHON, 'elevenlabs-mcp==' + L.VERSION]
    assert KEY not in ' '.join(command)
    assert env[common.KEY_NAME] == KEY
    assert env['ELEVENLABS_MCP_OUTPUT_MODE'] == 'files'
    assert env['ELEVENLABS_MCP_BASE_PATH'] == str(common.AUDIO)
    assert cwd == box and common.AUDIO.is_dir()
    assert capsys.readouterr().out == ''


def test_missing_key_stops_with_message_on_stderr(box, monkeypatch, capsys):
    calls = stub_run(monkeypatch)
    (box / common.KEY_FILE).unlink()
    assert L.main() == 1
    captured = capsys.readouterr()
    assert not calls and captured.out == ''
    assert common.KEY_FILE in captured.err


def test_empty_key_counts_as_missing(box, monkeypatch, capsys):
    stub_run(monkeypatch)
    (box / common.KEY_FILE).write_text(common.KEY_NAME + '=\n', encoding='utf-8')
    assert L.main() == 1


def test_key_file_with_bom_and_quotes(box):
    (box / common.KEY_FILE).write_bytes(('﻿%s="%s"\r\n' % (common.KEY_NAME, KEY)).encode('utf-8'))
    assert common.api_key() == KEY


def test_missing_uvx(box, monkeypatch, capsys):
    monkeypatch.setattr(L.shutil, 'which', lambda name: None)
    assert L.main() == 1
    assert 'uvx' in capsys.readouterr().err
