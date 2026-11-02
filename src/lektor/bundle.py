"""Folder paczki Descent-Lektor-PL dla Windows i Maca (E6, D57–D60).

  python -I -m lektor bundle --platform win|mac [--dev] [--out DIR]

--dev buduje analysis/work/dev-bundle: plugin z builda, Doorstop, skrypty i ustawienia ze ścieżkami do bazy
i audio w repozytorium oraz z Pythonem z .venv (test W1). Ponowna budowa podmienia pliki, ale zostawia stan
instalacji (stan/), dzienniki (logs/) i zmienione ustawienia.

Paczka zawiera audio M1, więc jest prywatna i powstaje w analysis/work/ (ignorowane w Git).
"""
import hashlib
import os
import shutil
import tomllib
import urllib.request
import zipfile

from . import paths

NAME = 'Descent-Lektor-PL'
SRC = os.path.join(paths.ROOT, 'src', 'bundle')
PLUGIN_BIN = os.path.join(paths.ROOT, 'build', 'plugin', 'LektorPL.Loader', 'bin', 'Release')
PLUGIN_FILES = ('LektorPL.Loader.dll', 'LektorPL.Core.dll')
CACHE = os.path.join(paths.WORK, 'bin')
DEV = os.path.join(paths.WORK, 'dev-bundle')
CRLF = ('.cmd', '.ps1')        # skrypty Windows
BOM = ('.ps1',)                # PowerShell 5.1 bez BOM czyta plik jako ANSI


def pins():
    with open(os.path.join(SRC, 'pins.toml'), 'rb') as fh:
        return tomllib.load(fh)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def fetch(pin):
    """Plik z cache analysis/work/bin/<dir>/ (pobrany, gdy go brak) o sumie z pins.toml."""
    path = os.path.join(CACHE, pin['dir'], pin['url'].rsplit('/', 1)[1])
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with urllib.request.urlopen(pin['url']) as r, open(path + '.part', 'wb') as fh:
            shutil.copyfileobj(r, fh)
        os.replace(path + '.part', path)
    got = sha256(path)
    if got != pin['sha256']:
        raise SystemExit('Zła suma SHA-256 %s: %s' % (path, got))
    return path


def copy_loader(platform, dest):
    pin = pins()['doorstop'][platform]
    out = os.path.join(dest, 'loader')
    os.makedirs(out, exist_ok=True)
    with zipfile.ZipFile(fetch(pin)) as z:
        for name in pin['files']:
            with z.open(name) as src, open(os.path.join(out, name.rsplit('/', 1)[1]), 'wb') as fh:
                shutil.copyfileobj(src, fh)


def copy_plugin(dest):
    out = os.path.join(dest, 'plugin')
    os.makedirs(out, exist_ok=True)
    for name in PLUGIN_FILES:
        src = os.path.join(PLUGIN_BIN, name)
        if not os.path.exists(src):
            raise SystemExit('Brak %s. Zbuduj plugin: dotnet build src/plugin/Loader -c Release' % paths.rel(src))
        shutil.copy2(src, out)


def copy_scripts(platform, dest):
    """Szablony z src/bundle/<platform>/ z końcami linii wymaganymi przez system."""
    root = os.path.join(SRC, platform)
    for base, _, files in os.walk(root):
        for name in files:
            src = os.path.join(base, name)
            dst = os.path.join(dest, os.path.relpath(src, root))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, 'rb') as fh:
                data = fh.read().replace(b'\r\n', b'\n')
            if data.startswith(b'\xef\xbb\xbf'):
                data = data[3:]
            ext = os.path.splitext(name)[1].lower()
            if ext in CRLF:
                data = data.replace(b'\n', b'\r\n')
            if ext in BOM:
                data = b'\xef\xbb\xbf' + data
            with open(dst, 'wb') as fh:
                fh.write(data)


def settings_text(dev):
    with open(os.path.join(SRC, 'ustawienia.toml'), encoding='utf-8') as fh:
        text = fh.read()
    slash = lambda p: p.replace(os.sep, '/')
    if dev:
        python = os.path.join(paths.ROOT, '.venv', 'Scripts', 'python.exe')
        values = {'@DB@': slash(paths.DB), '@AUDIO@': slash(paths.AUDIO),
                  '@PYTHON@': "python = '%s'    # tryb deweloperski: Python z .venv" % slash(python)}
    else:
        values = {'@DB@': 'dane/m1.sqlite', '@AUDIO@': 'dane', '@PYTHON@': ''}
    for k, v in values.items():
        text = text.replace(k, v)
    return text.rstrip('\n') + '\n'


def build(platform='win', dev=False, out=None):
    dest = out or (DEV if dev else os.path.join(paths.WORK, 'dist', platform, NAME))
    if not dev and os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.join(dest, 'logs'), exist_ok=True)
    copy_plugin(dest)
    copy_loader(platform, dest)
    copy_scripts(platform, dest)
    settings = os.path.join(dest, 'ustawienia.toml')
    if not (dev and os.path.exists(settings)):
        with open(settings, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(settings_text(dev))
    return dest
