"""Zdolności broni i talizmanów z okna ataku (E16, D101).

Po potwierdzeniu trafień okno ataku (UIHeroAttackDialog) pokazuje kafelki UIAbilityTrigger: nazwę zdolności
w szablonie WEAPON_ABILITY_TRIGGER i jej opis. Klucze leżą w modelach zdolności broni (WeaponAbilityModel: KeyName,
KeyDesc) i talizmanów (KeyName, AbilityKey) w bundlach d3/weapons/* i d3/items. Companion czyta nazwę i opis
(przełącznik 'zdolnosci'); plugin podaje klucze kafelka (zdarzenie open/close, kind 'ability').
"""
import re

WEAPON_FIELDS = {'KeyName', 'KeyDesc', 'Chance', 'EffectTiming', 'ShowPostAttackMessage'}
TRINKET_FIELDS = {'KeyName', 'AbilityKey', 'AbilityType'}
BUNDLES = re.compile(r'^d3/(weapons/|items$)')
GROUP, CATEGORY, TOGGLE = 'gear', 'walka_teren', 'zdolnosci'


def keys(game):
    """[(klucz nazwy, klucz opisu)] wszystkich zdolności broni i talizmanów, bez powtórzeń."""
    out = []
    for name in sorted(game.files):
        if not BUNDLES.match(name):
            continue
        for _, t, _ in game.behaviours(name):
            if WEAPON_FIELDS <= t.keys():
                out.append((t['KeyName'], t['KeyDesc']))
            elif TRINKET_FIELDS <= t.keys():
                out.append((t['KeyName'], t['AbilityKey']))
    return list(dict.fromkeys(out))


def records(game, terms, existing):
    """Kwestie nazw i opisów zdolności, których jeszcze nie ma w bazie (klucze bez tekstu pomijamy)."""
    out, seen = [], set(existing)
    for pair in keys(game):
        for key in pair:
            if not key or key in seen or not (terms.get(key) or {}).get('text'):
                continue
            seen.add(key)
            out.append({'key': key, 'group': GROUP, 'category': CATEGORY, 'toggle': TOGGLE,
                        'text_raw': terms[key]['text'], 'speakers': [], 'voice': 'narrator', 'hero_variant': [],
                        'role': 'ability', 'node_type': None, 'owner': None, 'seq': None, 'args': [], 'tts': 1})
    return out
