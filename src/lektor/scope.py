"""Zakres wydań. M1 (D15): prolog, Q1 i scena „Welcome Home”, wrogowie Q1 i z losowania (E1), grafy systemowe.
M2 (D62, D66): M1 oraz scenariusze i wydarzenia dostępne w kampanii, podróże aktu 1, miasto i opisy celów na mapie.

Klucz trafia do pierwszej grupy wydania. Kwestie to tylko teksty okien (komunikat, opcja wyboru, cel misji);
klucze z warunków i akcji grafów odpadają, a klucze wstawiane w luki {n} trafiają do inwentarza wartości.
Od M2 inwentarz czyta też argumenty węzłów łupu, testów i celów (D49).
"""
import re
from collections import defaultdict

from . import game as G

Q1_BUNDLE = 'd3/quests/box1/story/q1'
STORY_PREFIX = 'TANGERINE Q1 '
WELCOME_PREFIX = 'TANGERINE Welcome Home'
CUTSCENE_ID = 'CUTSCENE_01'
# Wrogowie z losowania widziani w sesji E1 (D15, D30): klucze nazw z argumentów EntityName.
RANDOM_ENEMY_NAMES = ('ENEMY_BANDIT_1_SING', 'ENEMY_ZEALOT_1_SING', 'ENEMY_FAE_SING', 'ENEMY_WOLF_1_SING')
# Nazwy wrogów w argumentach EntityName widziane w E1, których nie ma w modelach wrogów z zakresu (boss).
E1_ENTITY_NAMES = RANDOM_ENEMY_NAMES + ('ENEMY_BERSERKER_SING', 'ENEMY_BLOOD_SISTER_1_SING')
# Argumenty dodawane przez kod gry, nie przez graf (E1): klucz → argumenty.
CODE_ARGS = {'DEFAULT_SPAWN_ENEMY_MULTI': [{'type': 'EntityName', 'ref': None}]}
GROUPS = ('cutscene_01', 'story_q1', 'welcome_home', 'scene_q1', 'enemies', 'system')
# Scenariusz: bundel sceny i przedrostek grafów wstępu, zakończeń i podróży w d3/act1.
QUESTS = {'q6': ('d3/quests/box1/story/q6', 'TANGERINE Q6 '), 'q7': ('d3/quests/box1/story/q7', 'TANGERINE Q7 '),
          'q8': ('d3/quests/box1/story/q8', 'TANGERINE Q8 ')}
# Sceny i wydarzenia z d3/act1 (grafy Arrival DT w d3/narrativeevents tylko je wywołują).
SCENES = {'pre_q678': 'TANGERINE Story Scene Triage Pre Q678', 'event_e5b': 'TANGERINE EVENT 5B ',
          'event_ec3': 'TANGERINE Event Now Lets Find Out', 'event_ec1': 'TANGERINE Event The Orcs of Forthyn'}
RELEASE_GROUPS = {'m1': (), 'm2': (*QUESTS, *SCENES, 'travel_act1', 'town', 'map')}
DESTINATIONS = (('d3/coreset/data', 'QuestModel', '_keyName', '_descKey'),
                ('d3/narrativeevents', 'NarrativeEventModel', '_keyName', '_keyDesc'))
LOOT_TEMPLATES = ('GAIN_PHYSICAL_TREASURE', 'GAIN_DIGITAL_TREASURE', 'NO_ITEM_BACKUP', 'NO_RECIPE_BACKUP', 'CONSUMABLE_BACKUP',
                  'CONSUMABLE_BACKUP_MULTIPLE', 'REMOVE_ENTITY', 'UI_GOLD', 'UI_RECIPE')
LOOT_BUNDLES = ('d3/items', 'd3/heroes')
LOOT_MODELS = {'ArmorModel', 'ConsumableModel', 'TrinketModel', 'CraftingMaterialModel', 'WeaponPartsModel', 'LootModel',
               'SkillModel', 'FeatModel'}
OBJECTIVE_PREFIXES = ('Q1_OBJECTIVE_', 'Q8_OBJECTIVE_', 'Q_FOF_OBJECTIVE_', 'Q_LISB_OBJECTIVE_')
# EnemyThemeTraits (flagi) do kryteriów losowania wrogów (EnemyFilter).
THEMES = {'Undead': 4, 'Dragonkind': 8, 'Uthuk': 0x10, 'UndeadFaction': 0x80000, 'UthukFaction': 0x100000,
          'DragonFaction': 0x200000, 'BaronialFaction': 0x400000}

HEROES = {'BRYNN': 'brynn', 'SYRUS': 'syrus', 'GALADEN': 'galaden', 'VAERIX': 'vaerix', 'KEHLI': 'kehli',
          'CHANCE': 'chance'}
CHARACTER_VOICES = {**HEROES, 'BLOOD_SISTER': 'nekrul', 'BARONESS_ADELYNN': 'adelynn', 'RONAN': 'ronan',
                    'ASTARRA': 'astarra', 'KATHRYN': 'kathryn', 'LTRAND': 'ltrand', 'MASTERBRULI': 'bruli',
                    'DRAGON_HYBRID': 'xenith', 'HERBIE': 'herbie', 'ELDERMOK': 'mok', 'OUTLAWPRINCE': 'outlaw'}
HERO_NAME_KEYS = ['HERO_%s_NAME' % h for h in HEROES]
UPPER = re.compile(r'^[A-Z][A-Z0-9_]{3,}$')


def voice_for(category, speakers):
    """Głos kwestii: mówca dialogu albo narrator (VARIABLE_HERO: D17, komunikaty systemowe: D36)."""
    if category == 'dialog':
        ids = [s.replace('STORY_CHARACTER_', '') for s in speakers]
        for i in ids:
            if i.startswith('VARIABLE_HERO'):
                return 'narrator'
            if i in CHARACTER_VOICES:
                return CHARACTER_VOICES[i]
        return 'inny' if ids else 'narrator'
    return 'narrator'


def var_id(name):
    """Nazwa zmiennej blackboardu bez prefiksu globalnego („@Global_BB/x”, „Quest_BB/x” → „x”)."""
    return (name or '').lstrip('@').rsplit('/', 1)[-1].strip().lower()


def is_name_var(name):
    """Zmienna z imieniem gracza albo bohatera (E1: playerName, Hero Name, Hero On Watch Name → HERO_*_NAME)."""
    v = var_id(name)
    return 'name' in v and not any(w in v for w in ('enemy', 'terrain', 'item', 'dest'))


def string_assignments(v, out, names):
    """Zmienne tekstowe w grafie: klucze ustawiane przez SetStringKey i SetVariable<string> → out[zmienna],
    zmienne z imieniem gracza (GetPlayerStringField Name) → names."""
    if isinstance(v, dict):
        t = v.get('$type', '')
        if t == 'FFG.Core.Tasks.SetStringKey':
            out[var_id((v.get('_valueA') or {}).get('_name'))].add(v.get('_pendingKey'))
        elif t.startswith('NodeCanvas.Tasks.Actions.SetVariable`1[[System.String'):
            b = v.get('valueB') or {}
            if isinstance(b.get('_value'), str):
                out[var_id((v.get('valueA') or {}).get('_name'))].add(b['_value'])
        elif t == 'FFG.D3.Tasks.GetPlayerStringField' and v.get('_field') == 'Name':
            names.add(var_id((v.get('_resultString') or {}).get('_name')))
        for x in v.values():
            string_assignments(x, out, names)
    elif isinstance(v, list):
        for x in v:
            string_assignments(x, out, names)


def merged_args(main, rs):
    """Argumenty głównego węzła; „refs” zbiera odwołania z tej samej pozycji we wszystkich węzłach z kluczem
    (OBJECTIVE_UPDATED dostaje w różnych węzłach różne klucze celów)."""
    return [dict(a, refs=sorted({r['args'][i]['ref'] for r in rs
                                 if i < len(r['args']) and r['args'][i]['type'] == a['type'] and r['args'][i]['ref']}))
            for i, a in enumerate(main.get('args') or [])]


def all_args(rs):
    """Argumenty ze wszystkich węzłów z kluczem (D49). Węzeł łupu bywa bez typu i bez klucza na pierwszej pozycji,
    a cel misji ma argumenty w zadaniu SetObjective, więc typ i odwołania zbieramy z każdego węzła."""
    lists = [r['args'] or r.get('objective_args') or [] for r in rs]
    out = []
    for i in range(max(map(len, lists), default=0)):
        at = [a[i] for a in lists if i < len(a)]
        refs = sorted({a['ref'] for a in at if a['ref']})
        out.append({'type': next((a['type'] for a in at if a['type']), None), 'ref': refs[0] if refs else None, 'refs': refs})
    return out


def theme_mask(names):
    return sum(THEMES.get(n.strip(), 0) for n in (names or '').split(','))


def random_pool(graphs, enemies):
    """Wrogowie, których mogą wylosować węzły SpawnRandomEnemies z grafów (kryteria motywu, EnemyFilter)."""
    out = set()
    for gr in graphs:
        for n in gr['graph'].get('nodes', []):
            crit = n.get('_criteria')
            if not isinstance(crit, dict):
                continue
            any_of, none_of = theme_mask(crit.get('ThemeAny')), theme_mask(crit.get('ThemeExclude'))
            out |= {e for e, v in enemies.items() if v['random'] and (not any_of or v['theme'] & any_of)
                    and not v['theme'] & none_of}
    return out


def sources(game, act1, group):
    """Grafy grupy spoza M1."""
    if group in QUESTS:
        bundle, prefix = QUESTS[group]
        return list(game.graphs(bundle)) + [gr for gr in act1 if gr['owner'].startswith(prefix)]
    if group in SCENES:
        return [gr for gr in act1 if gr['owner'].startswith(SCENES[group])]
    if group == 'travel_act1':
        return [gr for gr in game.graphs('d3/travelevents') if not gr['owner'].startswith('Act 2')]
    if group == 'town':
        return list(game.graphs('d3/worldmap/act1')) + [gr for gr in act1 if gr['owner'] == 'WorldMapDT']
    return []


def destination_keys(game, terms):
    """Nazwy i opisy celów aktu 1 z panelu mapy (D55 pkt 5)."""
    for bundle, cls, name, desc in DESTINATIONS:
        for _, t, c in game.behaviours(bundle):
            if c == cls and t.get('_act') == 0:
                yield from (k for k in (t.get(name), t.get(desc)) if k and (terms.get(k) or {}).get('text'))


def loot_keys(game, terms):
    """Klucze tekstów listy łupu (D51): szablony z GiveTreasure i nazwy tego, co gra może dać w akcie 1."""
    keys = set(LOOT_TEMPLATES) | set(HERO_NAME_KEYS)
    for bundle in LOOT_BUNDLES + tuple(b for b in game.files if b.startswith('d3/weapons/')):
        for _, t, cls in game.behaviours(bundle):
            if cls in LOOT_MODELS and t.get('_act') == 0:
                keys |= {k for k in (t.get('KeyName'), t.get('_id')) if k}
    return sorted(k for k in keys if (terms.get(k) or {}).get('text'))


def collect(game, terms, release='m1', only=None):
    """Zakres wydania: (rekordy kwestii, inwentarz kluczy wartości dla luk, informacje o źródłach).
    only: grupy spoza M1, gdy nie wszystkie (test cyklu na jednym wydarzeniu, D63)."""
    extra = [g for g in RELEASE_GROUPS[release] if not only or g in only]
    group_of, refs = {}, defaultdict(list)
    var_keys, name_vars = defaultdict(set), set()

    def take(gr, group):
        for ln in G.graph_lines(gr, terms):
            group_of.setdefault(ln['key'], group)
            refs[ln['key']].append(ln)
        string_assignments(gr['graph'], var_keys, name_vars)

    cutscene = [k for k in game.cutscene_keys(CUTSCENE_ID) if k in terms]
    for k in cutscene:
        group_of.setdefault(k, 'cutscene_01')
    act1 = list(game.graphs('d3/act1'))
    for gr in act1:
        if gr['owner'].startswith(STORY_PREFIX):
            take(gr, 'story_q1')
    for gr in act1:
        if gr['owner'].startswith(WELCOME_PREFIX):
            take(gr, 'welcome_home')

    q1 = list(game.graphs(Q1_BUNDLE))
    q1_refs = set().union(*(gr['refs'] for gr in q1)) if q1 else set()
    q1_strings = {s for gr in q1 for s in G.walk_strings(gr['graph']) if UPPER.match(s)}
    q1_strings |= {s for _, t, _ in game.behaviours(Q1_BUNDLE) for s in G.walk_strings(t) if UPPER.match(s)}
    for gr in q1:
        take(gr, 'scene_q1')

    enemies = game.enemy_models(terms)
    chosen = sorted(e for e, v in enemies.items()
                    if e in q1_strings or v['ref'] in q1_refs or set(v['keys']) & set(RANDOM_ENEMY_NAMES))
    for bundle in sorted({enemies[e]['bundle'] for e in chosen}):
        for gr in game.graphs(bundle):
            take(gr, 'enemies')
    for gr in game.graphs('d3/gamereq'):
        take(gr, 'system')

    extra_graphs = []
    for group in extra:
        graphs = sources(game, act1, group)
        extra_graphs += graphs
        for gr in graphs:
            take(gr, group)
    if 'map' in extra:
        for k in destination_keys(game, terms):
            group_of.setdefault(k, 'map')
    extra_strings = {s for gr in extra_graphs for s in G.walk_strings(gr['graph']) if UPPER.match(s)}
    if extra_graphs:
        extra_refs = set().union(*(gr['refs'] for gr in extra_graphs))
        added = {e for e, v in enemies.items() if e in extra_strings or v['ref'] in extra_refs} | random_pool(extra_graphs, enemies)
        for bundle in sorted({enemies[e]['bundle'] for e in added} - {enemies[e]['bundle'] for e in chosen}):
            for gr in game.graphs(bundle):
                take(gr, 'enemies')
        chosen = sorted(set(chosen) | added)

    records = []
    for key, group in group_of.items():
        term = terms.get(key) or {}
        if not term.get('text'):
            continue
        rs = refs.get(key, [])
        if group == 'cutscene_01' and not rs:
            cat = 'napisy_cutscenek'
        elif group == 'map':
            cat = 'opis_misji'
        elif rs:
            cat = min((G.category(r) for r in rs), key=G.CATEGORY_PRIORITY.index)
        else:
            cat = G.fallback_category(term)
        speakers = sorted({s for r in rs for s in r['speakers']})
        main = next((r for r in rs if r['role'] == 'message' and r['args']), rs[0] if rs else {})
        records.append({
            'key': key, 'group': group, 'category': cat, 'text_raw': term['text'],
            'speakers': [s.replace('STORY_CHARACTER_', '') for s in speakers],
            'voice': voice_for(cat, speakers),
            'hero_variant': sorted({c for r in rs for c in r['conds'] if c.startswith('HERO:')}),
            'role': main.get('role', 'model'), 'node_type': main.get('node_type'),
            'owner': main.get('owner'), 'seq': main.get('seq'),
            'args': (all_args(rs) if release != 'm1' else merged_args(main, rs)) or CODE_ARGS.get(key, []),
            'tts': 0 if cat == 'napisy_cutscenek' else 1,  # przerywniki mają dubbing (D14)
        })
    order = {g: i for i, g in enumerate(GROUPS + RELEASE_GROUPS[release])}
    records.sort(key=lambda r: (order[r['group']], r['owner'] or '', r['seq'] if r['seq'] is not None else 1e9, r['key']))

    # Inwentarz wartości luk (D16). E1: EntityName to forma pojedyncza nazwy wroga, u bossa z aliasem
    # w nawiasie („ENEMY_…_SING (Q1_BOSS_NAME)”); zmienne tekstowe dostają klucze, najczęściej HERO_*_NAME.
    entity = sorted({k for e in chosen for k in enemies[e]['keys'] if re.match(r'^ENEMY_.*_SING$', k)} |
                    {k for k in E1_ENTITY_NAMES if k in terms})
    entity += sorted(s for s in q1_strings | extra_strings if re.match(r'^Q\d+_BOSS_NAME$', s) and s in terms)
    values = {
        'entity': entity + HERO_NAME_KEYS,
        'vars': {v: sorted(k for k in ks if k in terms) for v, ks in var_keys.items()},
        'name_vars': sorted(name_vars),
        'objectives': sorted({k for k, rs in refs.items() if any(r['role'] == 'objective' for r in rs)} |
                             {k for k in terms if k.startswith(OBJECTIVE_PREFIXES if extra else 'Q1_OBJECTIVE_')}),
    }
    info = {'enemies': chosen, 'q1_graphs': len(q1), 'cutscene_keys': len(cutscene), 'groups': extra}
    if release != 'm1':     # VARIABLE_HERO (D17): wersja w głosie każdego bohatera, companion wybiera po mówcy
        records += [dict(r, key='%s#%s' % (r['key'], hero), voice=hero) for r in records
                    if r['category'] == 'dialog' and any(s.startswith('VARIABLE_HERO') for s in r['speakers'])
                    for hero in HEROES.values()]
    return records, values, info


def slot_keys(arg_type, arg, line_key, values):
    """Klucze, które mogą trafić w lukę; pusta lista, gdy wartość znana dopiero w grze."""
    if arg_type in ('EntityName', 'EnemyNameWithArticle'):
        return values['entity']
    if arg_type not in ('VariableString', 'LocalizationKey'):
        return []
    keys = []
    for ref in arg.get('refs') or [arg.get('ref')]:
        if not ref:
            continue
        if var_id(ref) in values['name_vars'] or is_name_var(ref):
            keys += HERO_NAME_KEYS
        if values['vars'].get(var_id(ref)):
            keys += values['vars'][var_id(ref)]
        elif arg_type == 'LocalizationKey' and UPPER.match(ref):
            keys.append(ref)  # klucz wpisany wprost w argument
    if not keys and line_key.startswith('OBJECTIVE_'):
        keys = values['objectives']  # OBJECTIVE_UPDATED / OBJECTIVE_FINAL: bieżący cel misji (E1)
    return list(dict.fromkeys(keys))
