"""Plik konfiguracyjny companiona: %LOCALAPPDATA%/LektorPL/companion.toml (tworzony z wartościami domyślnymi)."""
import os
import tomllib

from .. import paths

TOGGLES = ('narracja', 'dialogi', 'komunikaty_questu', 'walka_teren', 'ui', 'okna_wyboru', 'nagrody',
           'aktywacje', 'cele', 'podroze', 'miasto', 'opis_misji')    # D21, aktywacje (D30), cele (D31), D66, D55

DEFAULT = '''# Companion lektora PL. Zmiany działają po ponownym uruchomieniu companiona.

# Port na localhost; ten sam co Companion.Port w BepInEx/config/pl.lektor.descent.cfg.
port = 47810

# Baza kwestii (E2) i katalog audio z manifest.json (E3).
db = "{db}"
audio = "{audio}"

# Głośność 0.0–1.0 i urządzenie wyjściowe (puste: domyślne systemowe; nazwa albo numer z `python -m sounddevice`).
volume = 1.0
device = ""

# Przełączniki kategorii (D21): false wycisza kategorię.
[toggles]
{toggles}
'''


def path():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~/.local/share')
    return os.path.join(base, 'LektorPL', 'companion.toml')


def default_text():
    slash = lambda p: p.replace(os.sep, '/')
    return DEFAULT.format(db=slash(paths.DB), audio=slash(paths.AUDIO), toggles='\n'.join('%s = true' % t for t in TOGGLES))


def load(file=None):
    """Konfiguracja jako słownik; brakujący plik tworzy z wartościami domyślnymi."""
    file = file or path()
    if not os.path.exists(file):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w', encoding='utf-8') as fh:
            fh.write(default_text())
    with open(file, 'rb') as fh:
        cfg = tomllib.loads(fh.read().decode('utf-8-sig'))     # Notatnik może dopisać BOM
    defaults = tomllib.loads(default_text())
    out = {**defaults, **cfg}
    out['toggles'] = {**defaults['toggles'], **cfg.get('toggles', {})}
    for k in ('db', 'audio'):           # ścieżki względne liczymy od pliku ustawień (paczka D60)
        out[k] = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(file)), out[k]))
    out['file'] = file
    return out
