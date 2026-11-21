"""Statystyki misji z pliku zapisu gry (E20, D114): wzorzec liczb dla panelu podsumowania w pluginie.

Liczy to samo co `src/plugin/Core/QuestStats.cs`, ale z `.sav` (JSON) i katalogu identyfikatorów z bundli gry.
Katalog zawiera tylko identyfikatory, klasy modeli i liczby (bez tekstów gry):
  items:   {id przedmiotu: klasa modelu}            (CraftingMaterialModel, RecipeModel, ConsumableModel, ...)
  weapons: {id części broni: numer WeaponClasses}
  feats:   {id wyzwania: [id bohatera, Goal]}
"""
import json
from decimal import Decimal

WEAPON_CLASSES = ('Hammer', 'Crossbow', 'Sword', 'Warhammer', 'Warbell', 'Spear', 'Wand', 'Staff', 'Gauntlet',
                  'ThrowingKnives', 'DualBlades', 'Bow', 'Rune')
RUNE = 12
HEALTH = ('Normal', 'MinorInjury', 'MajorInjury', 'Defeated')
DIFFICULTY = ('Journey', 'Standard', 'Heroic', 'Warfare')
ACTION_INTERACT, ACTION_COMBAT = 1, 2
CATALOG_MODELS = ('ArmorModel', 'ConsumableModel', 'TrinketModel', 'CraftingMaterialModel', 'WeaponPartsModel',
                  'RecipeModel', 'LootModel')


def load_save(path):
    with open(path, encoding='utf-8-sig') as fh:
        return json.load(fh)


def active_players(save):
    """Jak SerializedGame.SetActivePlayers: gracze z Index >= 0, posortowani po Index."""
    players = save.get('AllPlayers') or (save.get('GameSceneData') or {}).get('GameState', {}).get('AllPlayers') or []
    return sorted((p for p in players if p.get('Index', -1) >= 0), key=lambda p: p['Index'])


def _at(seq, i, default=0):
    return seq[i] if seq and i < len(seq) else default


def _frac(value):
    """(decimal)float % 1.0m jak w UIQuestSummary.SyncTo: float32 rzutowany na decimal ma 7 cyfr znaczących."""
    return float(Decimal(f'{value:.7g}') % 1)


def compute(save, catalog):
    """Słownik o tym samym kształcie co wiersz `quest_summary` z dziennika pluginu."""
    state = save['GameSceneData']['GameState']
    q = state['QuestSummary']
    weapons_cat, items_cat, feats_cat = catalog.get('weapons', {}), catalog.get('items', {}), catalog.get('feats', {})
    actions = q.get('ActionsPerformed') or []

    heroes = []
    for i, p in enumerate(active_players(save)):
        classes = []
        for w in p.get('EquippedWeapons') or []:
            c = weapons_cat.get(w.get('PartAId'))
            if c is not None and c != RUNE and c not in classes:
                classes.append(c)
        heroes.append({'hero': p['HeroId'], 'health': HEALTH[p.get('HealthState', 0)], 'classes': classes,
                       'rune': _at(q.get('UniqueWeaponClassUsage'), i)})

    usage = q.get('CoreWeaponClassUsage') or []
    weapons = [{'class': c, 'attacks': n, 'heroes': [h for h in range(len(heroes)) if c in heroes[h]['classes']]}
               for c, n in enumerate(usage) if n > 0]
    weapons.sort(key=lambda w: (-w['attacks'], w['class']))
    attacks = sum(usage) + sum(h['rune'] for h in heroes)

    for idx, h in enumerate(heroes):
        best, h['favorite'], h['attacks'], shared = h['rune'], ('Rune' if h['rune'] > 0 else None), h['rune'], []
        for w in weapons:
            if idx not in w['heroes']:
                continue
            h['attacks'] += w['attacks']
            if w['attacks'] > best:
                best, h['favorite'] = w['attacks'], WEAPON_CLASSES[w['class']]
            shared += [o for o in w['heroes'] if o != idx and o not in shared]
        h['shared'] = shared

    for idx, h in enumerate(heroes):
        points = done = 0
        for fid in q.get('CompletedFeatsInQuest') or []:
            if (feats_cat.get(fid) or [None])[0] == h['hero']:
                done += 1
                points += 1
        for fp in state.get('FeatProgresses') or []:
            hero, goal = feats_cat.get(fp.get('RealFeatId')) or (None, 0)
            if hero != h['hero']:
                continue
            if goal > 0:
                points += fp.get('Count', 0) / goal
            break
        h['feats'] = done
        h['feat_start'] = _frac(_at(q.get('StartingFeatPoints'), idx, 0.0))
        h['feat_gained'] = points - h['feat_start']

    loot = {'items': 0, 'materials': 0, 'recipes': 0, 'consumables': 0}
    kinds = {'CraftingMaterialModel': 'materials', 'RecipeModel': 'recipes', 'ConsumableModel': 'consumables'}
    for i, item in enumerate(q.get('ObtainedTreasureIDs') or []):
        loot[kinds.get(items_cat.get(item), 'items')] += _at(q.get('ObtainedTreasureQty'), i, 1)

    return {
        'quest': state.get('QuestId') or None,
        'seconds': round(q.get('QuestTotalTime', 0.0), 3),
        'rounds': q.get('CurrentRound', 0),
        'gold': q.get('ObtainedGold', 0),
        'attacks': attacks,
        'interactions': _at(actions, ACTION_INTERACT),
        'combat': _at(actions, ACTION_COMBAT),
        'difficulty': DIFFICULTY[state.get('GameDifficulty', 1)],
        'loot': loot,
        'weapons': [{'class': WEAPON_CLASSES[w['class']], 'attacks': w['attacks'],
                     'heroes': [heroes[h]['hero'] for h in w['heroes']]} for w in weapons],
        'heroes': [{'hero': h['hero'], 'health': h['health'], 'attacks': h['attacks'], 'rune': h['rune'],
                    'favorite': h['favorite'], 'shared': [heroes[o]['hero'] for o in h['shared']],
                    'feats': h['feats'], 'feat_start': round(h['feat_start'], 3),
                    'feat_gained': round(h['feat_gained'], 3)} for h in heroes],
    }


def build_catalog(game):
    """Katalog identyfikatorów z bundli gry (lektor.game.Game)."""
    items, weapons, feats = {}, {}, {}
    for bundle in sorted(game.files):
        if not (bundle in ('d3/items', 'd3/loot', 'd3/recipes') or bundle.startswith(('d3/weapons/', 'd3/heroes/'))):
            continue
        hero, bundle_feats = None, []
        for _, t, cls in game.behaviours(bundle):
            if cls in CATALOG_MODELS and t.get('_id'):
                items[t['_id']] = cls
            if cls == 'WeaponPartsModel' and t.get('_id'):
                weapons[t['_id']] = t.get('Class')
            elif cls == 'HeroModel':
                hero = t.get('_id')
            elif cls == 'FeatModel' and t.get('_id'):
                bundle_feats.append((t['_id'], t.get('Goal', 0)))
        for fid, goal in bundle_feats:              # wyzwania bohatera leżą w jego bundlu (HeroSource w tym pliku)
            feats[fid] = [hero, goal]
    return {'items': items, 'weapons': weapons, 'feats': feats}


def summary_lines(path):
    """Wiersze `quest_summary` z dziennika pluginu (JSON lines)."""
    out = []
    with open(path, encoding='utf-8') as fh:
        for raw in fh:
            raw = raw.strip()
            if '"quest_summary"' not in raw:
                continue
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            if line.get('ev') == 'quest_summary':
                out.append(line)
    return out


def diff(expected, actual, tol=0.01):
    """Różnice między wzorcem a wierszem pluginu: [(pole, wzorzec, plugin)]."""
    out = []

    def walk(path, a, b):
        if isinstance(a, dict):
            for k in a:
                walk(f'{path}.{k}' if path else k, a[k], (b or {}).get(k) if isinstance(b, dict) else None)
        elif isinstance(a, list):
            if not isinstance(b, list) or len(a) != len(b):
                out.append((path, a, b))
                return
            for i, (x, y) in enumerate(zip(a, b)):
                walk(f'{path}[{i}]', x, y)
        elif isinstance(a, float) or isinstance(b, float):
            if b is None or abs(float(a) - float(b)) > tol:
                out.append((path, a, b))
        elif a != b:
            out.append((path, a, b))

    walk('', expected, actual)
    return out
