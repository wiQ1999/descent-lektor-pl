"""Ścieżki projektu. Kopie gry i wszystkie wyniki z treścią gry leżą w analysis/work/ (ignorowane w Git)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.environ.get('LEKTOR_WORK') or os.path.join(ROOT, 'analysis', 'work')
BUNDLES = os.path.join(WORK, 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')
VOICES = os.path.join(WORK, 'voices')          # nagrania dubbingu (analysis/tools/extract_voices.py)
OUT = os.path.join(WORK, 'lektor')
REFS = os.path.join(OUT, 'refs')
HF_HOME = os.path.join(WORK, 'hf_cache')
RELEASES = ('m1', 'm2')                         # m2: M1 i scenariusze E7 w jednej bazie (D63)
RELEASE = DB = AUDIO = None


def use(release):
    """Wydanie, na którym pracują komendy: baza kwestii oraz katalog podejść, plików końcowych i manifestu."""
    global RELEASE, DB, AUDIO
    RELEASE = release
    DB = os.path.join(OUT, release + '.sqlite')
    AUDIO = os.path.join(WORK, 'audio', release)


use('m1')


def rel(path):
    """Ścieżka względem katalogu głównego repozytorium (do zapisu w bazie)."""
    return os.path.relpath(path, ROOT).replace(os.sep, '/')
