"""Paczka w częściach dla instalatora sieciowego (wariant B, Windows).

  python -I -m lektor bundle --platform win --parts [--from DIR] [--out DIR] [--fresh]

Dzieli gotowy folder paczki (bundle.build) na części i zapisuje manifest lektor-<platform>.json:
  python   Python z bibliotekami (zmienia się rzadko);
  program  plugin, loader, skrypty, pakiet lektor, baza, manifest audio, instrukcja, ustawienia domyślne;
  audio    warstwy z dane/final: każda budowa dokłada warstwę tylko z nowymi i zmienionymi plikami.

Nazwa części to rodzaj i początek sumy SHA-256 zipa, a zip jest deterministyczny (stała data, kolejność),
więc niezmieniona część ma tę samą nazwę i instalator jej nie pobiera. Katalog wyjściowy jest kumulatywny:
leżą w nim wszystkie części, do których odwołuje się manifest, i z nich budowa czyta poprzednie warstwy audio.
Warstwa, której wszystkie pliki przykryły późniejsze albo zniknęły z paczki, wypada z manifestu.
--fresh zaczyna audio od jednej warstwy (np. przed dużym wydaniem, gdy warstw jest dużo).

Instalator (starter instaluj-win.ps1 i instalator-win.ps1, obok manifestu) pobiera części, których nie ma w stan/pakiet.json instalacji,
rozpakowuje je w kolejności manifestu i usuwa pliki poprzednich części, których nowy manifest nie wymienia.
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
# starter do `irm ... | iex` (tylko ASCII, bez BOM) i właściwy instalator (UTF-8 z BOM dla PowerShell 5.1)
INSTALLER = {'win': ('instaluj-win.ps1', 'instalator-win.ps1')}
SKIP = set(B.UNSIGNED) | {'zgloszenia'}
STORED = set(B.STORED) | {'.flac', '.zip'}
DATE = (2020, 1, 1, 0, 0, 0)
CHUNK = 1 << 30                 # warstwa audio w zipach do 1 GiB (limit pliku w GitHub Releases to 2 GiB)


def manifest_name(platform):
    return 'lektor-%s.json' % platform


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
            info.create_system = 0
            info.external_attr = 0
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
    """Starter i instalator z końcami linii CRLF; starter musi być w ASCII, instalator dostaje BOM."""
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


def prune(out, manifest, platform):
    """Usuwa z katalogu wyjściowego części, do których manifest już się nie odwołuje."""
    used = {p['name'] for p in manifest['parts']} | {manifest_name(platform), *INSTALLER[platform]}
    for name in os.listdir(out):
        if name.endswith('.zip') and name not in used:
            os.remove(os.path.join(out, name))


def build(platform='win', src=None, out=None, fresh=False):
    if platform not in INSTALLER:
        raise SystemExit('Instalator w częściach jest na razie tylko dla Windows.')
    src = src or os.path.join(B.DIST, platform, B.NAME)
    out = out or os.path.join(B.DIST, platform + '-online')
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
    copy_installer(platform, out)
    prune(out, manifest, platform)
    return out
