"""Zakres M1 (D15): prolog, Q1 i scena „Welcome Home”, wrogowie Q1 i z losowania (E1), grafy systemowe.

Klucz trafia do pierwszej grupy z GROUPS. Kwestie to tylko teksty okien (komunikat, opcja wyboru, cel misji);
klucze z warunków i akcji grafów odpadają, a klucze wstawiane w luki {n} trafiają do inwentarza wartości.
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

HEROES = {'BRYNN': 'brynn', 'SYRUS': 'syrus', 'GALADEN': 'galaden', 'VAERIX': 'vaerix', 'KEHLI': 'kehli',
          'CHANCE': 'chance'}
CHARACTER_VOICES = {**HEROES, 'BLOOD_SISTER': 'nekrul', 'BARONESS_ADELYNN': 'adelynn', 'RONAN': 'ronan'}
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


def collect(game, terms):
    """Zakres M1: (rekordy kwestii, inwentarz kluczy wartości dla luk, informacje o źródłach)."""
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

    records = []
    for key, group in group_of.items():
        term = terms.get(key) or {}
        if not term.get('text'):
            continue
        rs = refs.get(key, [])
        if group == 'cutscene_01' and not rs:
            cat = 'napisy_cutscenek'
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
            'args': merged_args(main, rs) or CODE_ARGS.get(key, []),
            'tts': 0 if cat == 'napisy_cutscenek' else 1,  # przerywniki mają dubbing (D14)
        })
    order = {g: i for i, g in enumerate(GROUPS)}
    records.sort(key=lambda r: (order[r['group']], r['owner'] or '', r['seq'] if r['seq'] is not None else 1e9, r['key']))

    # Inwentarz wartości luk (D16). E1: EntityName to forma pojedyncza nazwy wroga, u bossa z aliasem
    # w nawiasie („ENEMY_…_SING (Q1_BOSS_NAME)”); zmienne tekstowe dostają klucze, najczęściej HERO_*_NAME.
    entity = sorted({k for e in chosen for k in enemies[e]['keys'] if re.match(r'^ENEMY_.*_SING$', k)} |
                    {k for k in E1_ENTITY_NAMES if k in terms})
    entity += sorted(s for s in q1_strings if re.match(r'^Q\d+_BOSS_NAME$', s) and s in terms)
    values = {
        'entity': entity + HERO_NAME_KEYS,
        'vars': {v: sorted(k for k in ks if k in terms) for v, ks in var_keys.items()},
        'name_vars': sorted(name_vars),
        'objectives': sorted({k for k, rs in refs.items() if any(r['role'] == 'objective' for r in rs)} |
                             {k for k in terms if k.startswith('Q1_OBJECTIVE_')}),
    }
    info = {'enemies': chosen, 'q1_graphs': len(q1), 'cutscene_keys': len(cutscene)}
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
