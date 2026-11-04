"""Folder paczki Descent-Lektor-PL dla Windows i Maca (E6, D57–D60).

  python -I -m lektor bundle --platform win|mac [--dev] [--out DIR]

Pełna paczka (analysis/work/dist/<platform>/Descent-Lektor-PL + zip obok) ma wszystko, czego potrzeba w grze:
plugin, Doorstop, Python 3.12 z bibliotekami companiona, część pakietu lektor, bazę i audio M1, instrukcję
i pliki do dwukliku. Pobrania (Doorstop, Python, koła) mają przypięte sumy SHA-256 (pins.toml,
requirements-<platform>.txt). Koła instaluje uv, tylko przy budowie: na komputerze z grą uv nie jest potrzebny.

--dev buduje analysis/work/dev-bundle: plugin z builda, Doorstop, skrypty i ustawienia ze ścieżkami do bazy
i audio w repozytorium oraz z Pythonem z .venv (test W1). Ponowna budowa podmienia pliki, ale zostawia stan
instalacji (stan/), dzienniki (logs/) i zmienione ustawienia.

Paczka zawiera audio M1, więc jest prywatna i powstaje w analysis/work/ (ignorowane w Git).
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tarfile
import time
import tomllib
import urllib.parse
import urllib.request
import zipfile

from . import paths

NAME = 'Descent-Lektor-PL'
SCOPES = {'m1': 'M1 (prolog i Q1)', 'm2': 'M2 (prolog, Q1, Q6–Q8, wydarzenia E5B, EC3, EC1, podróże aktu 1)'}
SRC = os.path.join(paths.ROOT, 'src', 'bundle')
PLUGIN_BIN = os.path.join(paths.ROOT, 'build', 'plugin', 'LektorPL.Loader', 'bin', 'Release')
PLUGIN_FILES = ('LektorPL.Loader.dll', 'LektorPL.Core.dll')
CACHE = os.path.join(paths.WORK, 'bin')
DEV = os.path.join(paths.WORK, 'dev-bundle')
DIST = os.path.join(paths.WORK, 'dist')
GUIDE = os.path.join(paths.ROOT, 'docs', 'INSTRUKCJA.md')
LEKTOR = ('__init__.py', 'normalize.py', 'paths.py', 'companion/__init__.py', 'companion/__main__.py',
          'companion/app.py', 'companion/config.py', 'companion/director.py', 'companion/library.py',
          'companion/player.py')     # companion bez modułów E2 i E3
UV_PLATFORM = {'win': 'x86_64-pc-windows-msvc', 'mac': 'aarch64-apple-darwin'}
# site-packages względem folderu paczki: Windows od razu, Mac po rozpakowaniu Pythona przez Zainstaluj.command
SITE = {'win': ('python', 'Lib', 'site-packages'), 'mac': ('python', 'lib', 'python3.12', 'site-packages')}
# Części Pythona zbędne companionowi: Tcl/Tk, IDLE, pip, nagłówki i biblioteki do kompilacji (ok. 30 MB)
TRIM_WIN = ('tcl', 'include', 'libs', 'Scripts', 'Lib/idlelib', 'Lib/tkinter', 'Lib/turtledemo', 'Lib/ensurepip',
            'Lib/test', 'Lib/site-packages/pip', 'DLLs/_tkinter.pyd', 'DLLs/tcl86t.dll', 'DLLs/tk86t.dll')
CRLF = ('.cmd', '.ps1')        # skrypty Windows
BOM = ('.ps1',)                # PowerShell 5.1 bez BOM czyta plik jako ANSI
EXEC = ('.command', '.sh')     # prawa wykonywania na Macu
STORED = ('.wav', '.gz')       # bez kompresji w zipie (i tak nie zyskują)
UNSIGNED = ('logs', 'stan')    # bez sum w skrypty/pliki.sha256


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
    path = os.path.join(CACHE, pin['dir'], urllib.parse.unquote(pin['url'].rsplit('/', 1)[1]))
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        curl = shutil.which('curl')     # magazyn certyfikatów systemu; Python z uv go na Windows nie widzi
        if curl:
            subprocess.run([curl, '-sSfL', '-o', path + '.part', pin['url']], check=True)
        else:
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
            raise SystemExit('Brak %s. Zbuduj plugin: dotnet build src/plugin/Loader -c Release' % src)
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


def copy_python(platform, dest):
    """Python 3.12 z bibliotekami companiona; zwraca katalog, do którego trafiły biblioteki."""
    archive = fetch(pins()['python'][platform])
    if platform == 'win':
        with tarfile.open(archive) as t:
            t.extractall(dest, filter='data')       # katalog python/ z python.exe
        site = os.path.join(dest, *SITE['win'])
        for rel in TRIM_WIN:
            path = os.path.join(dest, 'python', *rel.split('/'))
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        for name in os.listdir(site):
            if name.startswith('pip-') and name.endswith('.dist-info'):
                shutil.rmtree(os.path.join(site, name))
    else:
        os.makedirs(os.path.join(dest, 'python'), exist_ok=True)
        shutil.copy2(archive, os.path.join(dest, 'python', 'python.tar.gz'))
        site = os.path.join(dest, 'python', 'site-packages')    # Zainstaluj.command przenosi je do SITE['mac']
    os.makedirs(site, exist_ok=True)
    uv = shutil.which('uv')
    if not uv:
        raise SystemExit('Budowa paczki potrzebuje uv (instaluje koła dla wybranego systemu).')
    subprocess.run([uv, 'pip', 'install', '-q', '--target', site, '--python-platform', UV_PLATFORM[platform],
                    '--python-version', '3.12', '--require-hashes', '--only-binary', ':all:', '--no-deps',
                    '-r', os.path.join(SRC, 'requirements-%s.txt' % platform)], check=True)
    shutil.rmtree(os.path.join(site, 'bin'), ignore_errors=True)   # f2py i podobne: zbędne
    # Folder paczki na sys.path, żeby `-m lektor.companion` znalazł lektor/ (działa też z -I).
    with open(os.path.join(site, 'lektor-pl.pth'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('/'.join(['..'] * len(SITE[platform])) + '\n')
    return site


def copy_lektor(dest):
    src = os.path.join(paths.ROOT, 'src', 'lektor')
    for rel in LEKTOR:
        dst = os.path.join(dest, 'lektor', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(src, rel), dst)


def copy_data(dest):
    """Baza wydania i audio z manifestu (tylko pliki, które manifest wskazuje)."""
    out = os.path.join(dest, 'dane')
    os.makedirs(out, exist_ok=True)
    shutil.copy2(paths.DB, os.path.join(out, paths.RELEASE + '.sqlite'))
    with open(os.path.join(paths.AUDIO, 'manifest.json'), encoding='utf-8') as fh:
        manifest = json.load(fh)
    for m in manifest['fragments'].values():
        dst = os.path.join(out, m['file'])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(paths.AUDIO, m['file']), dst)
    shutil.copy2(os.path.join(paths.AUDIO, 'manifest.json'), out)
    return len(manifest['fragments'])


def settings_text(dev):
    with open(os.path.join(SRC, 'ustawienia.toml'), encoding='utf-8') as fh:
        text = fh.read()
    slash = lambda p: p.replace(os.sep, '/')
    if dev:
        python = os.path.join(paths.ROOT, '.venv', 'Scripts', 'python.exe')
        values = {'@DB@': slash(paths.DB), '@AUDIO@': slash(paths.AUDIO),
                  '@PYTHON@': "python = '%s'    # tryb deweloperski: Python z .venv" % slash(python)}
    else:
        values = {'@DB@': 'dane/%s.sqlite' % paths.RELEASE, '@AUDIO@': 'dane', '@PYTHON@': ''}
    for k, v in values.items():
        text = text.replace(k, v)
    return text.rstrip('\n') + '\n'


def version_text(platform, fragments):
    git = lambda *a: subprocess.run(['git', '-C', paths.ROOT, *a], capture_output=True, text=True).stdout.strip()
    commit = git('rev-parse', '--short', 'HEAD') + (' (zmiany niezatwierdzone)' if git('status', '--porcelain', '--untracked-files=no') else '')
    core = subprocess.run(['git', '-C', paths.ROOT, 'show', 'HEAD:src/plugin/Core/Bootstrap.cs'], capture_output=True, text=True).stdout
    plugin = next((ln.split('"')[1] for ln in core.splitlines() if 'const string Version' in ln), '?')
    return ('Lektor PL dla Descent: Legends of the Dark\n'
            'system: %s\nplugin: %s\nzakres: %s, %d fragmentów audio\nzbudowano: %s, commit %s\n'
            % ({'win': 'Windows', 'mac': 'macOS (Apple Silicon)'}[platform], plugin, SCOPES[paths.RELEASE], fragments,
               time.strftime('%Y-%m-%d %H:%M'), commit))


def files_of(dest):
    out = []
    for base, dirs, files in os.walk(dest):
        dirs.sort()
        for name in sorted(files):
            out.append(os.path.relpath(os.path.join(base, name), dest).replace(os.sep, '/'))
    return out


def write_sums(dest):
    lines = ['%s  %s' % (sha256(os.path.join(dest, f)), f) for f in files_of(dest)
             if f.split('/', 1)[0] not in UNSIGNED and f != 'skrypty/pliki.sha256']
    with open(os.path.join(dest, 'skrypty', 'pliki.sha256'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    return len(lines)


def write_zip(dest, path):
    """Zip z folderem paczki; pliki .command i .sh z prawem wykonywania (Mac), nazwy w UTF-8."""
    with zipfile.ZipFile(path + '.part', 'w') as z:
        for rel in files_of(dest):
            full = os.path.join(dest, rel)
            info = zipfile.ZipInfo('%s/%s' % (NAME, rel), time.localtime(os.path.getmtime(full))[:6])
            info.create_system = 3
            mode = 0o755 if os.path.splitext(rel)[1] in EXEC else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_STORED if os.path.splitext(rel)[1] in STORED else zipfile.ZIP_DEFLATED
            with open(full, 'rb') as src, z.open(info, 'w') as fh:
                shutil.copyfileobj(src, fh, 1 << 20)
        for folder in ('logs/',):
            info = zipfile.ZipInfo('%s/%s' % (NAME, folder))
            info.create_system = 3
            info.external_attr = (stat.S_IFDIR | 0o755) << 16 | 0x10
            z.writestr(info, b'')
    os.replace(path + '.part', path)
    return path


def build(platform='win', dev=False, out=None):
    dest = out or (DEV if dev else os.path.join(DIST, platform, NAME))
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
    if dev:
        return dest
    copy_python(platform, dest)
    copy_lektor(dest)
    fragments = copy_data(dest)
    shutil.copy2(GUIDE, os.path.join(dest, 'INSTRUKCJA.md'))
    with open(os.path.join(dest, 'wersja.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(version_text(platform, fragments))
    write_sums(dest)
    if out is None:
        write_zip(dest, os.path.join(DIST, '%s-%s.zip' % (NAME, platform)))
    return dest
