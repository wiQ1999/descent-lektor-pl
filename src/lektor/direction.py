"""Reżyseria kwestii: tempo i pauzy (D34), przełącznik kategorii (D21, D30, D31), klucz cache fragmentu."""
import hashlib

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
ELEVEN_TAKE0 = 100      # podejścia ElevenLabs mają numery od 101; podejścia OmniVoice tych głosów zostają jako zapas


def engine(voice):
    return 'elevenlabs' if voice in ELEVEN_VOICES else 'omnivoice'


def take_engine(take):
    return 'elevenlabs' if take > ELEVEN_TAKE0 else 'omnivoice'


SCENE_CATEGORIES = {'narracja_fabularna'}   # narracja w scenach fabularnych: tempo naturalne
SCENE_PAUSE = 0.35
PAUSE = 0.25
SPEED_MIN, SPEED_MAX = 1.2, 1.4
SPEED_FROM, SPEED_TO = 80, 300          # znaki: do 80 tempo bazowe, od 300 maksymalne (wstępnie, D34)

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
GROUP_TOGGLES = {'travel_act1': 'podroze', 'town': 'miasto', 'map': 'opis_misji'}     # D66, D55 pkt 5


def tempo(category, chars):
    """(speed, pauza między zdaniami). speed None = tempo przejęte z referencji (naturalne)."""
    if category in SCENE_CATEGORIES:
        return None, SCENE_PAUSE
    x = min(max((chars - SPEED_FROM) / (SPEED_TO - SPEED_FROM), 0.0), 1.0)
    return round(SPEED_MIN + x * (SPEED_MAX - SPEED_MIN), 2), PAUSE


def toggle(category, key, group=None):
    """Przełącznik companiona (D21). Aktywacje wrogów (D30) i cele (D31) mają własne, a podróże, miasto i opisy
    celów na mapie obejmują całą grupę."""
    if group in GROUP_TOGGLES:
        return GROUP_TOGGLES[group]
    if key.startswith('ENEMY_ACTIVATION_') or '_TACTIC_' in key:
        return 'aktywacje'
    return TOGGLES.get(category, 'ui')


def fragment_id(voice, text, speed):
    """Klucz cache: model + głos + tempo + znormalizowany tekst. Referencja głosu wchodzi przez nazwę głosu."""
    s = '%s|%s|%s|%s' % (MODEL_ID, voice, 'nat' if speed is None else '%.2f' % speed, text)
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]
