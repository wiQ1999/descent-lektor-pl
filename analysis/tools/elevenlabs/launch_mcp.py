"""Uruchamia lokalny serwer MCP ElevenLabs z kluczem z pliku nieśledzonego.

Na stdout pisze tylko sam serwer, bo to kanał protokołu MCP. Diagnostyka idzie na stderr.
"""
import os
import shutil
import subprocess
import sys

import common

VERSION = '0.12.2'
PYTHON = '3.13'


def server_env(key):
    return dict(os.environ, **{
        common.KEY_NAME: key,
        'ELEVENLABS_MCP_OUTPUT_MODE': 'files',
        'ELEVENLABS_MCP_BASE_PATH': str(common.AUDIO),
    })


def main():
    key = common.api_key()
    if not key:
        print('ElevenLabs MCP: brak %s w pliku %s (wzór: %s.example).'
              % (common.KEY_NAME, common.KEY_FILE, common.KEY_FILE), file=sys.stderr)
        return 1
    uvx = shutil.which('uvx')
    if not uvx:
        print('ElevenLabs MCP: nie znaleziono uvx. Zainstaluj uv i uruchom sesję ponownie.', file=sys.stderr)
        return 1
    common.AUDIO.mkdir(parents=True, exist_ok=True)
    command = [uvx, '--python', PYTHON, 'elevenlabs-mcp==' + VERSION]
    return subprocess.run(command, env=server_env(key), cwd=common.ROOT).returncode


if __name__ == '__main__':
    sys.exit(main())
