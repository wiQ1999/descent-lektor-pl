"""Plik konfiguracyjny companiona: %LOCALAPPDATA%/LektorPL/companion.toml (tworzony z wartościami domyślnymi)."""
import os
import tomllib

from .. import paths
from .control import KEYS

TOGGLES = ('narracja', 'dialogi', 'komunikaty_questu', 'walka_teren', 'ui', 'okna_wyboru', 'nagrody',
           'aktywacje', 'cele', 'podroze', 'miasto', 'opis_misji', 'zdolnosci')    # D21, D30, D31, D66, D55, E16 (D101)

DEFAULT = '''# Companion lektora PL. Zmiany działają po ponownym uruchomieniu companiona.

# Port na localhost; ten sam co Companion.Port w BepInEx/config/pl.lektor.descent.cfg.
port = 47810

# Baza kwestii (E2) i katalog audio z manifest.json (E3).
db = "{db}"
audio = "{audio}"

# Głośność 0.0–1.0 i urządzenie wyjściowe (puste: domyślne systemowe; nazwa albo numer z `python -m sounddevice`).
volume = 1.0
device = ""

# Tempo lektora 0.8–1.6 (zmieniane też w grze: skróty i menu lektora).
tempo = 1.0

# Przełączniki kategorii (D21): false wycisza kategorię.
[toggles]
{toggles}

# Skróty w grze: nazwy klawiszy Unity (KeyCode) z Ctrl, Alt albo Shift; kilka wariantów po przecinku.
[skroty]
{keys}

# Statystyki misji przy oknie podsumowania misji (E20, D114); zmieniane też w grze (menu lektora).
[podsumowanie]
statystyki = true
'''


def path():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~/.local/share')
    return os.path.join(base, 'LektorPL', 'companion.toml')


def default_text():
    slash = lambda p: p.replace(os.sep, '/')
    return DEFAULT.format(db=slash(paths.DB), audio=slash(paths.AUDIO), toggles='\n'.join('%s = true' % t for t in TOGGLES),
                          keys='\n'.join('%s = "%s"' % kv for kv in KEYS.items()))


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
    out['skroty'] = {**defaults['skroty'], **cfg.get('skroty', {})}
    out['podsumowanie'] = {**defaults['podsumowanie'], **cfg.get('podsumowanie', {})}
    for k in ('db', 'audio'):           # ścieżki względne liczymy od pliku ustawień (paczka D60)
        out[k] = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(file)), out[k]))
    out['file'] = file
    return out
