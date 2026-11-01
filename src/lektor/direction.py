"""Reżyseria kwestii: tempo i pauzy (D34), przełącznik kategorii (D21, D30, D31), klucz cache fragmentu."""
import hashlib

# Ustawienia syntezy (D33). Zmiana któregokolwiek pola zmienia klucze cache wszystkich fragmentów.
MODEL = {'name': 'omnivoice', 'rev': '08be0b4', 'dtype': 'fp16', 'num_step': 32, 'guidance_scale': 2.0}
MODEL_ID = 'omnivoice-08be0b4-fp16-s32-cfg2.0'

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


def tempo(category, chars):
    """(speed, pauza między zdaniami). speed None = tempo przejęte z referencji (naturalne)."""
    if category in SCENE_CATEGORIES:
        return None, SCENE_PAUSE
    x = min(max((chars - SPEED_FROM) / (SPEED_TO - SPEED_FROM), 0.0), 1.0)
    return round(SPEED_MIN + x * (SPEED_MAX - SPEED_MIN), 2), PAUSE


def toggle(category, key):
    """Przełącznik companiona (D21). Aktywacje wrogów (D30) i cele (D31) mają własne."""
    if key.startswith('ENEMY_ACTIVATION_') or '_TACTIC_' in key:
        return 'aktywacje'
    return TOGGLES.get(category, 'ui')


def fragment_id(voice, text, speed):
    """Klucz cache: model + głos + tempo + znormalizowany tekst. Referencja głosu wchodzi przez nazwę głosu."""
    s = '%s|%s|%s|%s' % (MODEL_ID, voice, 'nat' if speed is None else '%.2f' % speed, text)
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]
