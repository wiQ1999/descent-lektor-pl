"""Wzorzec statystyk misji (E20): sztuczny zapis i katalog, bez danych gry."""
import json

import pytest

from lektor import quest_summary as qs

CATALOG = {
    'items': {'MAT_A': 'CraftingMaterialModel', 'REC_A': 'RecipeModel', 'POT_A': 'ConsumableModel',
              'ARM_A': 'ArmorModel'},
    'weapons': {'SWORD_A': 2, 'BOW_A': 11, 'STAFF_A': 7, 'SWORD_B': 2, 'RUNE_A': 12},
    'feats': {'F_GAL_1': ['HERO_GALADEN', 3], 'F_GAL_2': ['HERO_GALADEN', 4], 'F_BRY_1': ['HERO_BRYNN', 2]},
}


def player(hero, index, health=0, parts=(), virtues=(12, 12)):
    return {'HeroId': hero, 'Index': index, 'HealthState': health,
            'VirtueOneValue': virtues[0], 'VirtueTwoValue': virtues[1],
            'EquippedWeapons': [{'Id': p, 'PartAId': p} for p in parts]}   # ekwipunek nie wpływa na przypisanie klas


def save(**summary):
    q = {'QuestTotalTime': 600.0, 'CurrentRound': 4, 'ObtainedGold': 30,
         'CoreWeaponClassUsage': [0] * 12, 'UniqueWeaponClassUsage': [0] * 4, 'ActionsPerformed': [0, 5, 9],
         'ObtainedTreasureIDs': [], 'ObtainedTreasureQty': [], 'CompletedFeatsInQuest': [],
         'StartingFeatPoints': [0.0] * 4}
    q.update(summary)
    return {'AllPlayers': [player('HERO_GALADEN', 0, 0, ['SWORD_A', 'BOW_A']), player('HERO_SYRUS', -1, 0, ['STAFF_A']),
                           player('HERO_BRYNN', 1, 1, ['SWORD_B', 'STAFF_A'], (16, 10))],
            'GameSceneData': {'GameState': {'QuestId': 'Q_TEST', 'GameDifficulty': 2, 'QuestSummary': q,
                                            'FeatProgresses': [{'RealFeatId': 'F_GAL_2', 'Count': 2}]}}}


def usage(**by_class):
    u = [0] * 12
    for name, n in by_class.items():
        u[qs.WEAPON_CLASSES.index(name)] = n
    return u


def test_tiles_and_actions():
    r = qs.compute(save(), CATALOG)
    assert (r['quest'], r['rounds'], r['gold'], r['seconds']) == ('Q_TEST', 4, 30, 600.0)
    assert (r['interactions'], r['combat'], r['difficulty']) == (5, 9, 'Heroic')


def test_active_players_by_index():
    r = qs.compute(save(), CATALOG)
    assert [h['hero'] for h in r['heroes']] == ['HERO_GALADEN', 'HERO_BRYNN']
    assert [h['health'] for h in r['heroes']] == ['Normal', 'MinorInjury']


def test_weapons_sorted_and_owned_by_class():
    # Klasa wskazuje bohatera (WeaponPartsModel.GetHero), nie ekwipunek: miecz to zawsze Brynn, łuk Galaden.
    r = qs.compute(save(CoreWeaponClassUsage=usage(Sword=3, Bow=5, Staff=2), UniqueWeaponClassUsage=[0, 1, 0, 0]),
                   CATALOG)
    assert [(w['class'], w['attacks']) for w in r['weapons']] == [('Bow', 5), ('Sword', 3), ('Staff', 2)]
    assert [w['heroes'] for w in r['weapons']] == [['HERO_GALADEN'], ['HERO_BRYNN'], []]   # Syrus poza drużyną
    assert r['attacks'] == 11
    galaden, brynn = r['heroes']
    assert (galaden['attacks'], galaden['favorite']) == (5, 'Bow')
    # Brynn: miecz (3) + runa (1, indeks gracza 1); ulubiona to miecz
    assert (brynn['attacks'], brynn['favorite'], brynn['rune']) == (4, 'Sword', 1)


def test_rune_wins_tie_as_favorite():
    r = qs.compute(save(CoreWeaponClassUsage=usage(Sword=2), UniqueWeaponClassUsage=[0, 2, 0, 0]), CATALOG)
    assert r['heroes'][1]['favorite'] == 'Rune'


def test_virtues_current_values():
    r = qs.compute(save(), CATALOG)
    assert [h['virtues'] for h in r['heroes']] == [[12, 12], [16, 10]]


def test_loot_by_kind_with_quantities():
    r = qs.compute(save(ObtainedTreasureIDs=['MAT_A', 'REC_A', 'POT_A', 'ARM_A', 'UNKNOWN'],
                        ObtainedTreasureQty=[20, 1, 2, 1, 1]), CATALOG)
    assert r['loot'] == {'items': 2, 'materials': 20, 'recipes': 1, 'consumables': 2}


def test_feat_progress_like_game_bar():
    r = qs.compute(save(CompletedFeatsInQuest=['F_GAL_1'], StartingFeatPoints=[2.25, 1.0, 0.0, 0.0]), CATALOG)
    anna, bob = r['heroes']
    assert anna['feats'] == 1
    assert anna['feat_start'] == pytest.approx(0.25)
    assert anna['feat_gained'] == pytest.approx(1 + 2 / 4 - 0.25)
    assert (bob['feats'], bob['feat_gained']) == (0, 0)


def test_float32_start_points_round_like_decimal():
    r = qs.compute(save(StartingFeatPoints=[4.099999904632568, 0.0, 0.0, 0.0]), CATALOG)
    assert r['heroes'][0]['feat_start'] == pytest.approx(0.1)


def test_diff_and_log_lines(tmp_path):
    expected = qs.compute(save(CoreWeaponClassUsage=usage(Bow=1)), CATALOG)
    log = tmp_path / 'hook.jsonl'
    good = {'ev': 'quest_summary', **expected}
    bad = {**good, 'rounds': 5}
    log.write_text('\n'.join([json.dumps({'ev': 'open', 'kind': 'message'}), json.dumps(good), json.dumps(bad)]),
                   encoding='utf-8')
    lines = qs.summary_lines(log)
    assert len(lines) == 2
    assert qs.diff(expected, lines[0]) == []
    assert qs.diff(expected, lines[1]) == [('rounds', 4, 5)]
