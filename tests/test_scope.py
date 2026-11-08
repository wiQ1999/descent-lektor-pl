"""Głosy kwestii (D17, D36) i inwentarz wartości luk (D16)."""
import pytest

from lektor import scope

VALUES = {
    'entity': ['ENEMY_BANDIT_1_SING', 'HERO_BRYNN_NAME'],
    'vars': {'injury': ['INJURY_1', 'INJURY_3'], 'hero on watch name': ['HERO_SYRUS_NAME']},
    'name_vars': ['playername'],
    'objectives': ['Q1_OBJECTIVE_1', 'Q1_OBJECTIVE_2'],
}


@pytest.mark.parametrize('category, speakers, voice', [
    ('dialog', ['STORY_CHARACTER_SYRUS'], 'syrus'),
    ('dialog', ['STORY_CHARACTER_BARONESS_ADELYNN'], 'adelynn'),
    ('dialog', ['STORY_CHARACTER_VARIABLE_HERO_1'], 'narrator'),
    ('dialog', ['STORY_CHARACTER_UNKNOWN'], 'inny'),
    ('dialog', [], 'narrator'),
    ('komunikat_questu', ['STORY_CHARACTER_SYRUS'], 'narrator'),
    ('walka_teren', [], 'narrator'),
])
def test_voice_for(category, speakers, voice):
    assert scope.voice_for(category, speakers) == voice


@pytest.mark.parametrize('speakers, voice', [
    (['STORY_CHARACTER_ALYS'], 'alys'),
    (['STORY_CHARACTER_SHADOW_RENEYR'], 'reneyr'),
    (['STORY_CHARACTER_ALYS', 'STORY_CHARACTER_BRYNN'], 'brynn'),     # głos z M1/M2 wygrywa jak dotąd
    (['STORY_CHARACTER_ALYS', 'STORY_CHARACTER_VARIABLE_HERO2'], 'narrator'),
])
def test_voice_for_m3_characters(speakers, voice):
    assert scope.voice_for('dialog', speakers) == voice


@pytest.mark.parametrize('bundle, owner, group', [
    ('d3/quests/box1/story/q12', 'DT Boss', 'a1_q12'),
    ('d3/quests/box1/side/s2', 'DT', 'a1_sq2'),
    ('d3/quests/dle04/story/q3', 'DT Meet Shadow', 'a2_q3'),
    ('d3/act1', 'TANGERINE Q10 Outro Win', 'a1_q10'),
    ('d3/act1', 'TANGERINE Q2_Q5 Transition', 'a1_q5'),
    ('d3/act1', 'TANGERINE Post Q10', 'a1_q10'),
    ('d3/act1', 'TANGERINE SQ1 Intro', 'a1_sq1'),
    ('d3/act1', 'TANGERINE EVENT 4A Something', 'a1_event_4a'),
    ('d3/act1', 'TANGERINE Story Scene Pre Finale (Imported)', 'a1_scene_pre_finale'),
    ('d3/act2', 'A2 Q00 Intro', 'a2_q0'),
    ('d3/act2', 'A2 SE05 New', 'a2_se05'),
    ('d3/act2', 'A2 SS03 (Imported)', 'a2_ss03'),
    ('d3/act2', 'Act_2_WorldMap_DT', 'town_act2'),
    ('d3/travelevents', 'Act 2 Road', 'travel_act2'),
    ('d3/cityevents', 'A2S01 The Citadel', 'city_act2'),
    ('d3/weapons/bow', 'Bow', 'gear'),
    ('d3/quests/enemy tool', 'Tool', None),
])
def test_m3_group(bundle, owner, group):
    assert scope.m3_group(bundle, owner) == group


def test_m3_rank_follows_campaign():
    groups = ['a2_q1', 'a1_q10', 'city', 'a1_q2', 'a1_event_pre9a', 'a1_event_10a', 'a1_sq1', 'a2_se05']
    assert sorted(groups, key=scope.m3_rank) == ['a1_q2', 'a1_q10', 'a1_sq1', 'a1_event_pre9a', 'a1_event_10a', 'city',
                                                 'a2_q1', 'a2_se05']


@pytest.mark.parametrize('name, vid', [
    ('Quest_BB/Hero On Watch Name', 'hero on watch name'),
    ('@Global_Timing_BB/trinketWSBonus', 'trinketwsbonus'),
    ('_playerName', '_playername'),
    (None, ''),
])
def test_var_id(name, vid):
    assert scope.var_id(name) == vid


@pytest.mark.parametrize('name, is_name', [
    ('playerName', True), ('Hero Name', True), ('_targetName', True),
    ('Terrain Name', False), ('DestName', False), ('EnemyGUID', False), ('Item1 String', False),
])
def test_is_name_var(name, is_name):
    assert scope.is_name_var(name) is is_name


def test_slot_keys_entity():
    assert scope.slot_keys('EntityName', {'ref': 'EnemyGUID'}, 'X', VALUES) == VALUES['entity']
    assert scope.slot_keys('EnemyNameWithArticle', {}, 'X', VALUES) == VALUES['entity']


def test_slot_keys_variables():
    assert scope.slot_keys('VariableString', {'ref': 'WorkingInjury'}, 'X', VALUES) == []
    assert scope.slot_keys('VariableString', {'ref': 'Quest_BB/Injury'}, 'X', VALUES) == ['INJURY_1', 'INJURY_3']
    keys = scope.slot_keys('VariableString', {'ref': 'Quest_BB/Hero On Watch Name'}, 'X', VALUES)
    assert keys[:6] == scope.HERO_NAME_KEYS and keys.count('HERO_SYRUS_NAME') == 1


def test_slot_keys_localization_key():
    arg = {'type': 'LocalizationKey', 'ref': 'Q1_OBJECTIVE_4', 'refs': ['Q1_OBJECTIVE_1', 'Q1_OBJECTIVE_4']}
    assert scope.slot_keys('LocalizationKey', arg, 'OBJECTIVE_UPDATED', VALUES) == ['Q1_OBJECTIVE_1', 'Q1_OBJECTIVE_4']
    assert scope.slot_keys('LocalizationKey', {'ref': 'currentObjective'}, 'OBJECTIVE_UPDATED', VALUES) == \
        VALUES['objectives']
    assert scope.slot_keys('LocalizationKey', {'ref': None}, 'DEFAULT_GET_TREASURE_SINGLE', VALUES) == []


def test_slot_keys_runtime_only():
    for t in ('RawText', 'ListOfKeys', None):
        assert scope.slot_keys(t, {'ref': 'x'}, 'X', VALUES) == []


def test_merged_args_collects_refs_from_all_nodes():
    main = {'args': [{'type': 'LocalizationKey', 'ref': 'A'}]}
    rs = [main, {'args': [{'type': 'LocalizationKey', 'ref': 'B'}]}, {'args': [{'type': 'VariableInt', 'ref': 'n'}]},
          {'args': []}]
    assert scope.merged_args(main, rs) == [{'type': 'LocalizationKey', 'ref': 'A', 'refs': ['A', 'B']}]


def test_all_args_reads_loot_and_objective_nodes():
    rs = [{'args': [{'type': None, 'ref': None}, {'type': 'RawText', 'ref': None}]},
          {'args': [{'type': 'LocalizationKey', 'ref': 'CHEST_1'}, {'type': 'RawText', 'ref': None}]},
          {'args': [], 'objective_args': [{'type': 'LocalizationKey', 'ref': 'CHEST_2'}]}]
    assert scope.all_args(rs) == [{'type': 'LocalizationKey', 'ref': 'CHEST_1', 'refs': ['CHEST_1', 'CHEST_2']},
                                  {'type': 'RawText', 'ref': None, 'refs': []}]


def test_random_pool_uses_theme_criteria():
    enemies = {'A': {'theme': 0x100000, 'random': True}, 'B': {'theme': 0x200008, 'random': True},
               'C': {'theme': 0x100000, 'random': False}, 'D': {'theme': 0x200000, 'random': True}}
    graphs = [{'graph': {'nodes': [{'_criteria': {'ThemeAny': 'UthukFaction'}}, {'_message': {}},
                                   {'_criteria': {'ThemeAny': 'DragonFaction', 'ThemeExclude': 'Dragonkind'}}]}}]
    assert scope.random_pool(graphs, enemies) == {'A', 'D'}


def test_string_assignments():
    graph = {'nodes': [
        {'$type': 'FFG.Core.Tasks.SetStringKey', '_valueA': {'_name': 'Quest_BB/Injury'}, '_pendingKey': 'INJURY_2'},
        {'$type': 'NodeCanvas.Tasks.Actions.SetVariable`1[[System.String, mscorlib]]',
         'valueA': {'_name': 'Dest'}, 'valueB': {'_value': 'PLACE_1'}},
        {'$type': 'FFG.D3.Tasks.GetPlayerStringField', '_field': 'Name', '_resultString': {'_name': 'Who'}},
    ]}
    out, names = {}, set()
    from collections import defaultdict
    out = defaultdict(set)
    scope.string_assignments(graph, out, names)
    assert dict(out) == {'injury': {'INJURY_2'}, 'dest': {'PLACE_1'}}
    assert names == {'who'}
