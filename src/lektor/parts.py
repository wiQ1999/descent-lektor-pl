"""Paczka w częściach dla instalacji i aktualizacji jedną komendą (E19, D111).

  python -I -m lektor bundle --platform win|mac --parts [--from DIR] [--out DIR] [--fresh]

Dzieli gotowy folder paczki (bundle.build) na części i zapisuje manifest lektor-<platform>.json:
  python   Python z bibliotekami (zmienia się rzadko);
  program  plugin, loader, skrypty, pakiet lektor, baza, manifest audio, instrukcja, ustawienia domyślne;
  audio    warstwy z dane/final: każda budowa dokłada warstwę tylko z nowymi i zmienionymi plikami.

Nazwa części to rodzaj i początek sumy SHA-256 zipa, a zip jest deterministyczny (stała data, kolejność),
więc niezmieniona część ma tę samą nazwę i instalator jej nie pobiera. Windows i Mac mają wspólny katalog
analysis/work/dist/online/: warstwy audio obu systemów to te same zipy, więc wydanie ma jedną ich kopię. Katalog wyjściowy jest kumulatywny:
leżą w nim wszystkie części, do których odwołuje się manifest, i z nich budowa czyta poprzednie warstwy audio.
Warstwa, której wszystkie pliki przykryły późniejsze albo zniknęły z paczki, wypada z manifestu.
--fresh zaczyna audio od jednej warstwy (np. przed dużym wydaniem, gdy warstw jest dużo).

Instalator (Windows: starter instaluj-win.ps1 i instalator-win.ps1; Mac: instaluj-mac.sh) pobiera części, których
nie ma w stanie instalacji (stan/pakiet.json albo stan/pakiet.txt), rozpakowuje je w kolejności manifestu i usuwa
pliki poprzednich części, których nowy manifest nie wymienia. Mac dostaje obok JSON indeks tekstowy lektor-mac.txt,
bo bash 3.2 z macOS nie ma parsera JSON.
"""
import hashlib
import json
import os
import shutil
import zipfile

from . import bundle as B

FORMAT = 1
AUDIO_DIR = 'dane/final/'
DEFAULTS = 'skrypty/ustawienia.domyslne.toml'     # ustawienia.toml instalator tworzy albo scala z tym plikiem
# Windows: starter do `irm ... | iex` (tylko ASCII, bez BOM) i właściwy instalator (UTF-8 z BOM dla PowerShell 5.1);
# Mac: jeden skrypt do `curl ... | bash` (UTF-8, końce linii LF)
INSTALLER = {'win': ('instaluj-win.ps1', 'instalator-win.ps1'), 'mac': ('instaluj-mac.sh',)}
SKIP = set(B.LOCAL) | {'zgloszenia'}
STORED = set(B.STORED) | {'.zip'}
DATE = (2020, 1, 1, 0, 0, 0)
ONLINE = os.path.join(B.DIST, 'online')    # wspólny dla Windows i Maca: warstwy audio są te same
CHUNK = 1 << 30                 # warstwa audio w zipach do 1 GiB (limit pliku w GitHub Releases to 2 GiB)


def manifest_name(platform):
    return 'lektor-%s.json' % platform


def index_name(platform):
    return 'lektor-%s.txt' % platform


def index_text(manifest):
    """Indeks dla bash: wiersze rozdzielone tabulatorem, pliki z numerem części (od 1)."""
    lines = ['format\t%d' % manifest['format'], 'platform\t%s' % manifest['platform'], 'id\t%s' % manifest['id'],
             'version\t%s' % manifest['version']]
    for i, p in enumerate(manifest['parts'], 1):
        lines.append('part\t%d\t%s\t%s\t%s\t%d' % (i, p['kind'], p['name'], p['sha256'], p['size']))
    for i, p in enumerate(manifest['parts'], 1):
        lines += ['file\t%d\t%s' % (i, f) for f in p['files']]
    return '\n'.join(lines) + '\n'


def kind_of(rel):
    if rel.startswith('python/'):
        return 'python'
    if rel.startswith(AUDIO_DIR):
        return 'audio'
    return 'program'


def collect(src):
    """{rodzaj: [(ścieżka w paczce, ścieżka na dysku)]} z folderu paczki, bez stanu, dzienników i zgłoszeń."""
    out = {'python': [], 'program': [], 'audio': []}
    for rel in B.files_of(src):
        if rel.split('/', 1)[0] in SKIP or '__pycache__/' in rel:     # pyc z uruchomienia paczki
            continue
        full = os.path.join(src, *rel.split('/'))
        if rel == 'ustawienia.toml':
            rel = DEFAULTS
        out[kind_of(rel)].append((rel, full))
    return out


def write_part(entries, out, kind):
    """Deterministyczny zip w out/; zwraca wpis manifestu. Ta sama zawartość daje tę samą nazwę."""
    tmp = os.path.join(out, kind + '.zip.part')
    with zipfile.ZipFile(tmp, 'w') as z:
        for rel, full in sorted(entries):
            info = zipfile.ZipInfo(rel, DATE)
            info.create_system = 3          # prawa uniksowe: skrypty Maca wykonywalne po rozpakowaniu
            mode = 0o755 if os.path.splitext(rel)[1] in B.EXEC else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_STORED if os.path.splitext(rel)[1] in STORED else zipfile.ZIP_DEFLATED
            with open(full, 'rb') as src, z.open(info, 'w') as fh:
                shutil.copyfileobj(src, fh, 1 << 20)
    digest = B.sha256(tmp)
    name = '%s-%s.zip' % (kind, digest[:12])
    path = os.path.join(out, name)
    if os.path.exists(path):
        os.remove(tmp)
    else:
        os.replace(tmp, path)
    return {'name': name, 'kind': kind, 'sha256': digest, 'size': os.path.getsize(path),
            'files': sorted(rel for rel, _ in entries)}


def crc_of(path):
    """(CRC32, rozmiar) pliku: tak samo jak w nagłówku zipa, bez czytania zipów do pamięci."""
    import zlib
    crc, size = 0, 0
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            crc = zlib.crc32(chunk, crc)
            size += len(chunk)
    return crc, size


def previous_layers(out, platform):
    path = os.path.join(out, manifest_name(platform))
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as fh:
        old = json.load(fh)
    return [p for p in old['parts'] if p['kind'] == 'audio']


def audio_layers(entries, out, platform, fresh=False):
    """Poprzednie warstwy, które coś jeszcze wnoszą, i nowa warstwa ze zmienionymi plikami (o ile są)."""
    layers = [] if fresh else previous_layers(out, platform)
    owner, state = {}, {}         # plik -> indeks warstwy, która go daje; plik -> (CRC32, rozmiar)
    for i, layer in enumerate(layers):
        with zipfile.ZipFile(os.path.join(out, layer['name'])) as z:
            for info in z.infolist():
                owner[info.filename] = i
                state[info.filename] = (info.CRC, info.file_size)
    changed = [(rel, full) for rel, full in entries if state.get(rel) != crc_of(full)]
    new = {rel for rel, _ in changed}
    served = {}                 # indeks warstwy -> pliki, które nadal z niej pochodzą
    for rel, _ in entries:
        if rel in owner and rel not in new:
            served.setdefault(owner[rel], []).append(rel)
    kept = []
    for i, layer in enumerate(layers):
        if i in served:         # w manifeście warstwa wymienia tylko pliki, które z niej zostają
            kept.append({**layer, 'files': sorted(served[i])})
    chunk, size = [], 0
    for rel, full in changed:
        chunk.append((rel, full))
        size += os.path.getsize(full)
        if size >= CHUNK:
            kept.append(write_part(chunk, out, 'audio'))
            chunk, size = [], 0
    if chunk:
        kept.append(write_part(chunk, out, 'audio'))
    return kept


def version_of(src):
    """Wersja z wersja.txt paczki: plugin i chwila budowy."""
    values = {}
    with open(os.path.join(src, 'wersja.txt'), encoding='utf-8') as fh:
        for line in fh:
            if ':' in line:
                k, v = line.split(':', 1)
                values[k.strip()] = v.strip()
    return 'plugin %s, zbudowano %s' % (values.get('plugin', '?'), values.get('zbudowano', '?').split(',')[0])


def copy_installer(platform, out):
    """Skrypty instalacji. Windows: CRLF, starter tylko w ASCII, instalator z BOM. Mac: LF bez BOM."""
    if platform == 'mac':
        for name in INSTALLER[platform]:
            with open(os.path.join(B.SRC, 'online', name), 'rb') as fh:
                data = fh.read().replace(b'\r\n', b'\n')
            replace_file(os.path.join(out, name), data[3:] if data.startswith(b'\xef\xbb\xbf') else data)
        return
    starter, installer = INSTALLER[platform]
    for name in (starter, installer):
        with open(os.path.join(B.SRC, 'online', name), 'rb') as fh:
            data = fh.read().replace(b'\r\n', b'\n')
        if data.startswith(b'\xef\xbb\xbf'):
            data = data[3:]
        if name == starter:
            data.decode('ascii')      # irm czyta plik z wydania jako ISO-8859-1
        else:
            data = b'\xef\xbb\xbf' + data
        replace_file(os.path.join(out, name), data.replace(b'\n', b'\r\n'))


def replace_file(path, data):
    """Nowy plik zamiast zapisu w miejscu: katalog części może mieć twarde dowiązania do plików innego katalogu."""
    with open(path + '.part', 'wb') as fh:
        fh.write(data)
    os.replace(path + '.part', path)


def prune(out):
    """Usuwa z katalogu wyjściowego części, do których nie odwołuje się żaden manifest (Windows ani Mac)."""
    used = set()
    for platform in INSTALLER:
        path = os.path.join(out, manifest_name(platform))
        if os.path.exists(path):
            with open(path, encoding='utf-8') as fh:
                used |= {p['name'] for p in json.load(fh)['parts']}
    for name in os.listdir(out):
        if name.endswith('.zip') and name not in used:
            os.remove(os.path.join(out, name))


def build(platform='win', src=None, out=None, fresh=False):
    if platform not in INSTALLER:
        raise SystemExit('Nieznany system: %s' % platform)
    src = src or os.path.join(B.DIST, platform, B.NAME)
    out = out or ONLINE
    if not os.path.exists(os.path.join(src, 'wersja.txt')):
        raise SystemExit('Brak paczki w %s. Najpierw: python -I -m lektor bundle --platform %s' % (src, platform))
    os.makedirs(out, exist_ok=True)
    entries = collect(src)
    parts = [write_part(entries['python'], out, 'python'), write_part(entries['program'], out, 'program')]
    parts += audio_layers(entries['audio'], out, platform, fresh)
    manifest = {'format': FORMAT, 'platform': platform, 'version': version_of(src),
                'id': hashlib.sha256(''.join(p['sha256'] for p in parts).encode()).hexdigest()[:12],
                'parts': parts}
    replace_file(os.path.join(out, manifest_name(platform)), json.dumps(manifest, ensure_ascii=False, indent=1).encode('utf-8'))
    if platform == 'mac':
        replace_file(os.path.join(out, index_name(platform)), index_text(manifest).encode('utf-8'))
    copy_installer(platform, out)
    prune(out)
    return out
