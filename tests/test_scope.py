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
