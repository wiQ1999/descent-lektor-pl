"""Reżyseria kwestii: tempo i pauzy (D34), przełącznik kategorii (D21, D30, D31), klucz cache fragmentu."""
import hashlib

from . import paths

# Ustawienia syntezy (D33, D42). Zmiana któregokolwiek pola zmienia klucze cache wszystkich fragmentów.
MODEL = {'name': 'omnivoice', 'rev': '08be0b4', 'dtype': 'fp32', 'num_step': 32, 'guidance_scale': 2.0}
MODEL_ID = 'omnivoice-08be0b4-fp32-s32-cfg2.0'

# Postacie bez dubbingu czyta ElevenLabs (D80, E13): głosy z rundy 2 E11 (docs/CASTING.md), ustawienia domyślne.
# Klucze fragmentów zostają z OmniVoice (fragment_id), zmienia się tylko silnik, który je czyta.
ELEVEN_MODEL = 'eleven_v4'
ELEVEN_VOICES = {'adelynn': 'dH4FrDMHSw1B31tzWOPw', 'ronan': '7ScqSXmT0oXvHenzw9hJ', 'astarra': 'B9Xmu9MUTLL4L5SIDsAD',
                 'kathryn': 'JZzQvOujFtUu9vpAsm2q', 'ltrand': 'OLeMFzYjewG73PEGvePC', 'bruli': 'UDpt5qLmStrzpqQQZI9G',
                 'herbie': 'BFwE7UC8qCq4bda0mhyE', 'mok': 'SQ2Rf1tdmOCUqClP6qJ4', 'outlaw': '6yCDeMiG8Fnpn0gPqxz3',
                 'flint': 'gfzrH3j2kaDI5cNZuaPW', 'galgoraz': 'Quk21RWppOlJmKTYBeGr'}
# E14 (D84, D87, D88): nowe postacie bez dubbingu z arkusza obsady; Delphyndra jest klonem OmniVoice (D94).
ELEVEN_VOICES_E14 = {'magrit': '4z2ttMe9kFzyBLgroafB', 'alys': 'PzYUKC9HYBoJ4OGyP1QE', 'greigory': '1iufCs0OK7CV8njHiko7',
                     'button': 'RMWgUKFzzgxce9riuhEC', 'laurel': 'YpSjl2k2ogKW014dXeX3', 'arden': 'jl1qd5mvirQo588r4kkX',
                     'veta': '0rtBIPGtLS4yt8kPC7Cs', 'trevalyn': 'PnphcFpQiiZTzbeOcbxp', 'balthain': '9CdwdaxrlepOclY1rmY5',
                     'ducard': 'm5FL5XfqLXQEY9dOd5GJ', 'pryor': '6gJmPw2772iK66WdPEKX', 'grace': '7nGRsoaWpcG4aZ7JLbJW',
                     'drys': 'UrUMN6EMRqqvJz3oDHD1', 'waiqar': 'IQY1bvB4YbPVoS6Go9q3', 'morant': '3CNDe9njN2kEBkgjZlEi',
                     'nara': 'peH5NmVUWPLR3C6OwCIg', 'meza': '6QqpmxamtHSBJVCpfj8E'}
ELEVEN_VOICES.update(ELEVEN_VOICES_E14)
# D109: nowe profile po odsłuchu m4. Znacznik wchodzi do klucza fragmentu (build.voice_tag), więc kwestie tych
# głosów dostają nowe id i ElevenLabs czyta je od nowa; podgląd projektu leży w elevenlabs/audio/m4_recast/<głos>.
ELEVEN_RECAST = {'laurel': ('mNYK3E8hLlawETLY1i23', 'D109'), 'ltrand': ('mlfNLSkD2rRJuAjOiqyV', 'D109'),
                 'ducard': ('HHaHDYNatBEDVYdzrvGp', 'D109')}
# E20 (D114): wybrane, ale włączane przy kolejnym generowaniu (akt 2): głos -> (voice_id, znacznik, efekt finalize).
# Włączenie: wpis do ELEVEN_RECAST i FX. Do tego czasu kwestie zostają przy obecnym głosie (6 fragmentów aktu 1).
RECAST_LATER = {'levirax': ('FcGRaGTdqjgS5L4Rbh1J', 'D114', 'dragon_e')}     # głos L z rundy 2 ElevenLabs, wybór E z rundy 3
ELEVEN_VOICES.update({v: vid for v, (vid, _) in ELEVEN_RECAST.items()})
# E20 (D114): sposób czytania głosu w ElevenLabs: ustawienia głosu, tempo i znaczniki audio eleven_v4 przed kwestią
# (lead) i po pierwszym zdaniu (breath). Znaczniki idą tylko do API; ocena porównuje mowę z tekstem fragmentu.
ELEVEN_STYLE = {'levirax': {'stability': 0.3, 'style': 0.3, 'speed': 0.75,
                            'lead': '[long, deep inhale] [slowly, booming]', 'breath': '[deep inhale]'}}
ELEVEN_TAKE0 = 100      # podejścia ElevenLabs mają numery od 101; podejścia OmniVoice tych głosów zostają jako zapas

# E20 (D114): efekt na audio głosu (lektor.effects), wypalany przez finalize w pliku końcowym; wybór z odsłuchu.
FX = {'kathryn': 'ghost_c2', 'nv_q13_smok': 'ghost_c2', 'nv_baelziffar': 'ghost_b2', 'nv_q12_duch': 'ghost_c2'}


def engine(voice):
    if paths.RELEASE in paths.LOCAL_ONLY:
        return 'omnivoice'
    return 'elevenlabs' if voice in ELEVEN_VOICES else 'omnivoice'


def take_engine(take):
    return 'elevenlabs' if take > ELEVEN_TAKE0 else 'omnivoice'


SCENE_CATEGORIES = {'narracja_fabularna'}   # narracja w scenach fabularnych: tempo naturalne
SCENE_PAUSE = 0.35
PAUSE = 0.25
SPEED_MIN, SPEED_MAX = 1.2, 1.4
SPEED_FROM, SPEED_TO = 80, 300          # znaki: do 80 tempo bazowe, od 300 maksymalne (wstępnie, D34)
ONE_TEMPO = ('t1', 'm4')   # E16 (D101): narrator w zakresie reguł t1 zawsze SPEED_MAX (poza narracją scen), także luki; m4: cała gra (D107)

TOGGLES = {
    'dialog': 'dialogi',
    'narracja_fabularna': 'narracja', 'zdarzenie': 'narracja', 'fabula_niepowiazana': 'narracja',
    'komunikat_questu': 'komunikaty_questu', 'quest_niepowiazany': 'komunikaty_questu',
    'walka_teren': 'walka_teren',
    'cel_misji': 'cele',
    'opcja_wyboru': 'okna_wyboru',
    'system_nagroda': 'nagrody',
    'ui_system': 'ui',
}
# Okna walki z grafów systemowych, które kategoria system_nagroda przypisałaby nagrodom (D98).
KEY_TOGGLES = {'UI_ENEMYDEFENSIVE_REMINDER': 'walka_teren', 'TACTIC_PHASE_DESCRIPTION': 'walka_teren'}
GROUP_TOGGLES = {'travel_act1': 'podroze', 'town': 'miasto', 'map': 'opis_misji',     # D66, D55 pkt 5
                 'travel_act2': 'podroze', 'town_act2': 'miasto', 'city': 'miasto', 'city_act2': 'miasto'}    # E14


def tempo(category, chars):
    """(speed, pauza między zdaniami). speed None = tempo przejęte z referencji (naturalne)."""
    if category in SCENE_CATEGORIES:
        return None, SCENE_PAUSE
    x = min(max((chars - SPEED_FROM) / (SPEED_TO - SPEED_FROM), 0.0), 1.0)
    return round(SPEED_MIN + x * (SPEED_MAX - SPEED_MIN), 2), PAUSE


def toggle(category, key, group=None):
    """Przełącznik companiona (D21). Aktywacje wrogów (D30) i cele (D31) mają własne, a podróże, miasto i opisy
    celów na mapie obejmują całą grupę."""
    if key in KEY_TOGGLES:
        return KEY_TOGGLES[key]
    if group in GROUP_TOGGLES:
        return GROUP_TOGGLES[group]
    if key.startswith('ENEMY_ACTIVATION_') or '_TACTIC_' in key:
        return 'aktywacje'
    return TOGGLES.get(category, 'ui')


def fragment_id(voice, text, speed):
    """Klucz cache: model + głos + tempo + znormalizowany tekst. Referencja głosu wchodzi przez nazwę głosu."""
    s = '%s|%s|%s|%s' % (MODEL_ID, voice, 'nat' if speed is None else '%.2f' % speed, text)
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]
