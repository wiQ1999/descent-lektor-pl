# Zakres milestone 1: prolog i Q1 (akt 1)

Źródło: `analysis/work/out/lines.jsonl` i kopie bundli. Skrypt: [`tools/m1_scope.py`](tools/m1_scope.py). Wynik bez tekstów trafia do `work/out/m1_scope.json`.
W tym pliku są tylko klucze i liczby. Liczba znaków to tekst PL po usunięciu znaczników; każdy placeholder `{n}` liczy się jako 6 znaków.

## Co wchodzi w zakres

Każdy klucz trafia do pierwszej pasującej grupy, w tej kolejności:

| Grupa | Źródło |
|---|---|
| `cutscene_01` | napisy `CutsceneModel` `CUTSCENE_01` (14 napisów z `displayAt` od 0,5 do 64,5 s, zdarzenie Wwise `Cutscene_1_Introduction`) |
| `story_q1` | sceny fabularne `d3/act1`: `TANGERINE Q1 Intro`, `Q1 Outro Win`, `Q1 Outro Lose` |
| `scene_q1` | wszystkie 73 grafy ze sceny `d3/quests/box1/story/q1`, łącznie z kopiami grafów `Default*` osadzonymi w scenie |
| `enemies_q1` | wrogowie, których scena tworzy wprost przez `SpawnEnemy` (odwołanie PPtr do `EnemyModel`): `ENEMY_BERSERKER_1` (Berserker) i `ENEMY_INTRO_BOSS` (Ne’Krul). Do tego modele i grafy z ich bundli `d3/enemies/berserker` i `d3/enemies/bloodsister` |
| `system` | grafy globalne `d3/gamereq` (koniec rundy, atak bohatera, aktywacje wrogów, łup, rany). Działają w każdym queście, więc nagrywa się je raz |

Poza zakresem (do decyzji):
- `TANGERINE Welcome Home Post Q1 Story Scene`: 49 rekordów, scena w mieście po Q1;
- poboczny quest SQ1;
- wrogowie losowani przez `SpawnRandomEnemies`. Kryteria w Q1: motyw `Uthuk, Mercenary, Humanoid`, poziom 1, bez golemów. Ich zbioru nie da się ustalić bez symulacji losowania, więc nie są policzeni. Mogą dodać po kilkadziesiąt kluczy aktywacji na każdy typ wroga.

Grupa `enemies_q1` jest celowo szersza niż potrzeba. Obejmuje wszystkie grafy obu bundli wrogów, czyli także warianty Ne’Krul z Q8, Q9 i Q12.

## Podsumowanie

| Grupa | Klucze | Znaki | Klucze z `{n}` | Warianty zależne od bohatera |
|---|---:|---:|---:|---:|
| `cutscene_01` | 14 | 655 | 0 | 0 |
| `story_q1` | 89 | 6 786 | 0 | 0 |
| `scene_q1` | 422 | 51 999 | 47 | 28 |
| `enemies_q1` | 31 | 4 237 | 21 | 0 |
| `system` | 90 | 6 835 | 14 | 0 |
| **Razem** | **646** | **70 512** | **82** | **28** |

Szacowana długość audio przy tempie polskiego lektora z przerywników (9,5–11,5 znaku/s, patrz [VOICES.md](VOICES.md)): 70 512 znaków to ok. 1 h 40 min – 2 h 05 min. Czas generowania podaje [BENCH.md](BENCH.md).

Warianty zależne od bohatera to klucze za `ConditionNode`, które sprawdzają bohatera zapisanego w zmiennej blackboardu (`Hero Choices DT`). Gracz usłyszy tylko jeden wariant, ale nagrać trzeba wszystkie.

### Rozkład na głosy

| Głos | Klucze | Znaki | Co obejmuje |
|---|---:|---:|---|
| narrator | 323 | 47 445 | komunikaty questu (290 kluczy, 44 694 znaki, z czego fragmenty kursywą: 26 518 znaków w 240 kluczach), narracja scen (10), zdarzenia (7), napisy `CUTSCENE_01` (14) |
| bohaterowie | 67 | 5 137 | Syrus 22 klucze / 2 132 znaki, Brynn 16 / 1 349, Galaden 16 / 896, Vaerix 13 / 760 |
| inny | 1 | 74 | Ne’Krul (`BLOOD_SISTER`) |
| systemowy | 255 | 17 856 | opcje wyboru (80), UI i podpowiedzi (100), aktywacje i komunikaty walki (36), nagrody (19), cele (8), nazwy questu i wrogów (12) |

Uwagi:
- W Q1 mówią tylko Syrus, Brynn, Galaden i Vaerix (drużyna prologu). Kehli i Fuks pojawiają się później.
- Opcje wyboru przypisałem do głosu systemowego. Część z nich to cytowane wypowiedzi drużyny w cudzysłowie, więc można je też czytać głosem wybranego bohatera.
- **`CUTSCENE_01` ma już polski dubbing w grze** (`1_Introduction_VoiceOver`, 70 s w `Polish.pck`, patrz [VOICES.md](VOICES.md)). TTS jest tu potrzebny tylko wtedy, gdy przerywnik ma brzmieć tym samym lektorem co reszta. Bez tego M1 to 632 klucze i 69 857 znaków.
- 30 kluczy ma ponad 300 znaków; najdłuższy ma 711. Takie kwestie trzeba dzielić na zdania przed generowaniem (patrz [BENCH.md](BENCH.md)).

## Lista kluczy

Kolejność: grupa, potem graf, potem `seq` (kolejność DFS w grafie). Kolumna „Wariant” oznacza klucz za warunkiem na bohatera.

| # | Klucz | Grupa | Kategoria | Głos | Mówca | Wariant | Znaki | {n} |
|---:|---|---|---|---|---|---|---:|---:|
| 1 | `CUTSCENE_01_INTRO_01` | cutscene_01 | napisy_cutscenek | narrator | – | – | 13 |  |
| 2 | `CUTSCENE_01_INTRO_02` | cutscene_01 | napisy_cutscenek | narrator | – | – | 40 |  |
| 3 | `CUTSCENE_01_INTRO_03` | cutscene_01 | napisy_cutscenek | narrator | – | – | 14 |  |
| 4 | `CUTSCENE_01_INTRO_04` | cutscene_01 | napisy_cutscenek | narrator | – | – | 50 |  |
| 5 | `CUTSCENE_01_INTRO_05` | cutscene_01 | napisy_cutscenek | narrator | – | – | 30 |  |
| 6 | `CUTSCENE_01_INTRO_06` | cutscene_01 | napisy_cutscenek | narrator | – | – | 55 |  |
| 7 | `CUTSCENE_01_INTRO_07` | cutscene_01 | napisy_cutscenek | narrator | – | – | 70 |  |
| 8 | `CUTSCENE_01_INTRO_08` | cutscene_01 | napisy_cutscenek | narrator | – | – | 71 |  |
| 9 | `CUTSCENE_01_INTRO_09` | cutscene_01 | napisy_cutscenek | narrator | – | – | 87 |  |
| 10 | `CUTSCENE_01_INTRO_10` | cutscene_01 | napisy_cutscenek | narrator | – | – | 55 |  |
| 11 | `CUTSCENE_01_INTRO_11` | cutscene_01 | napisy_cutscenek | narrator | – | – | 40 |  |
| 12 | `CUTSCENE_01_INTRO_12` | cutscene_01 | napisy_cutscenek | narrator | – | – | 35 |  |
| 13 | `CUTSCENE_01_INTRO_13` | cutscene_01 | napisy_cutscenek | narrator | – | – | 34 |  |
| 14 | `CUTSCENE_01_INTRO_14` | cutscene_01 | napisy_cutscenek | narrator | – | – | 61 |  |
| 15 | `TANGERINE_Q1_INTRO_REVISED_00` | story_q1 | narracja_fabularna | narrator | – | – | 129 |  |
| 16 | `TANGERINE_Q1_INTRO_REVISED_01` | story_q1 | narracja_fabularna | narrator | – | – | 136 |  |
| 17 | `TANGERINE_Q1_INTRO_REVISED_02` | story_q1 | dialog | bohaterowie | SYRUS | – | 98 |  |
| 18 | `TANGERINE_Q1_INTRO_REVISED_03` | story_q1 | dialog | bohaterowie | GALADEN | – | 42 |  |
| 19 | `TANGERINE_Q1_INTRO_REVISED_04` | story_q1 | dialog | bohaterowie | SYRUS | – | 54 |  |
| 20 | `TANGERINE_Q1_INTRO_REVISED_04A` | story_q1 | dialog | bohaterowie | BRYNN | – | 38 |  |
| 21 | `TANGERINE_Q1_INTRO_REVISED_04B` | story_q1 | dialog | bohaterowie | SYRUS | – | 154 |  |
| 22 | `TANGERINE_Q1_INTRO_REVISED_04C` | story_q1 | dialog | bohaterowie | SYRUS | – | 126 |  |
| 23 | `TANGERINE_Q1_INTRO_REVISED_05` | story_q1 | dialog | bohaterowie | SYRUS | – | 52 |  |
| 24 | `TANGERINE_Q1_INTRO_REVISED_06` | story_q1 | dialog | bohaterowie | VAERIX | – | 17 |  |
| 25 | `TANGERINE_Q1_INTRO_REVISED_07` | story_q1 | dialog | bohaterowie | BRYNN | – | 16 |  |
| 26 | `TANGERINE_Q1_INTRO_REVISED_08` | story_q1 | narracja_fabularna | narrator | – | – | 13 |  |
| 27 | `TANGERINE_Q1_INTRO_REVISED_09A` | story_q1 | dialog | bohaterowie | SYRUS | – | 37 |  |
| 28 | `TANGERINE_Q1_INTRO_REVISED_10A` | story_q1 | dialog | bohaterowie | SYRUS | – | 85 |  |
| 29 | `TANGERINE_Q1_INTRO_REVISED_10A_11M` | story_q1 | opcja_wyboru | systemowy | SYRUS | – | 32 |  |
| 30 | `TANGERINE_Q1_INTRO_REVISED_10A_11P` | story_q1 | opcja_wyboru | systemowy | SYRUS | – | 58 |  |
| 31 | `TANGERINE_Q1_INTRO_REVISED_11M` | story_q1 | dialog | bohaterowie | SYRUS | – | 190 |  |
| 32 | `TANGERINE_Q1_INTRO_REVISED_12B` | story_q1 | dialog | bohaterowie | BRYNN | – | 217 |  |
| 33 | `TANGERINE_Q1_INTRO_REVISED_13A` | story_q1 | dialog | bohaterowie | GALADEN | – | 29 |  |
| 34 | `TANGERINE_Q1_INTRO_REVISED_14AA` | story_q1 | dialog | bohaterowie | SYRUS | – | 52 |  |
| 35 | `TANGERINE_Q1_INTRO_REVISED_14A` | story_q1 | dialog | bohaterowie | SYRUS | – | 57 |  |
| 36 | `TANGERINE_Q1_INTRO_REVISED_14A_15S` | story_q1 | opcja_wyboru | systemowy | SYRUS | – | 20 |  |
| 37 | `TANGERINE_Q1_INTRO_REVISED_14A_15V` | story_q1 | opcja_wyboru | systemowy | SYRUS | – | 25 |  |
| 38 | `TANGERINE_Q1_INTRO_REVISED_15S` | story_q1 | dialog | bohaterowie | SYRUS | – | 99 |  |
| 39 | `TANGERINE_Q1_INTRO_REVISED_16A` | story_q1 | dialog | bohaterowie | GALADEN | – | 4 |  |
| 40 | `TANGERINE_Q1_INTRO_REVISED_17A` | story_q1 | dialog | bohaterowie | SYRUS | – | 103 |  |
| 41 | `TANGERINE_Q1_INTRO_REVISED_18A` | story_q1 | dialog | bohaterowie | GALADEN | – | 249 |  |
| 42 | `TANGERINE_Q1_INTRO_REVISED_19A` | story_q1 | dialog | bohaterowie | GALADEN | – | 80 |  |
| 43 | `TANGERINE_Q1_INTRO_REVISED_20A` | story_q1 | dialog | bohaterowie | VAERIX | – | 25 |  |
| 44 | `TANGERINE_Q1_INTRO_REVISED_21A` | story_q1 | dialog | bohaterowie | SYRUS | – | 51 |  |
| 45 | `TANGERINE_Q1_INTRO_REVISED_21A_22A` | story_q1 | opcja_wyboru | systemowy | SYRUS | – | 9 |  |
| 46 | `TANGERINE_Q1_INTRO_REVISED_21A_22B` | story_q1 | opcja_wyboru | systemowy | SYRUS | – | 16 |  |
| 47 | `TANGERINE_Q1_INTRO_REVISED_22A` | story_q1 | dialog | bohaterowie | VAERIX | – | 81 |  |
| 48 | `TANGERINE_Q1_INTRO_REVISED_23A` | story_q1 | narracja_fabularna | narrator | – | – | 103 |  |
| 49 | `TANGERINE_Q1_INTRO_REVISED_24A` | story_q1 | dialog | bohaterowie | VAERIX | – | 180 |  |
| 50 | `TANGERINE_Q1_INTRO_REVISED_25B` | story_q1 | dialog | bohaterowie | BRYNN | – | 54 |  |
| 51 | `TANGERINE_Q1_INTRO_REVISED_25C` | story_q1 | dialog | bohaterowie | VAERIX | – | 148 |  |
| 52 | `TANGERINE_Q1_INTRO_REVISED_25A` | story_q1 | dialog | bohaterowie | BRYNN | – | 43 |  |
| 53 | `TANGERINE_Q1_INTRO_REVISED_26A` | story_q1 | dialog | bohaterowie | GALADEN | – | 48 |  |
| 54 | `TANGERINE_Q1_INTRO_REVISED_27A` | story_q1 | dialog | bohaterowie | BRYNN | – | 109 |  |
| 55 | `TANGERINE_Q1_INTRO_REVISED_18` | story_q1 | narracja_fabularna | narrator | – | – | 183 |  |
| 56 | `QUEST_INTRO_SELECT_HEROES` | story_q1 | zdarzenie | narrator | – | – | 119 |  |
| 57 | `TANGERINE_Q1_INTRO_REVISED_15V` | story_q1 | dialog | bohaterowie | SYRUS | – | 133 |  |
| 58 | `TANGERINE_Q1_INTRO_REVISED_16B` | story_q1 | dialog | bohaterowie | GALADEN | – | 33 |  |
| 59 | `TANGERINE_Q1_INTRO_REVISED_11P` | story_q1 | dialog | bohaterowie | SYRUS | – | 228 |  |
| 60 | `TANGERINE_Q1_INTRO_REVISED_12A` | story_q1 | dialog | bohaterowie | BRYNN | – | 335 |  |
| 61 | `TANGERINE_Q1_INTRO_REVISED_28A` | story_q1 | dialog | bohaterowie | VAERIX | – | 57 |  |
| 62 | `TANGERINE_Q1_INTRO_REVISED_16` | story_q1 | narracja_fabularna | narrator | – | – | 141 |  |
| 63 | `TANGERINE_Q1_INTRO_REVISED_16_17B` | story_q1 | opcja_wyboru | systemowy | – | – | 39 |  |
| 64 | `TANGERINE_Q1_INTRO_REVISED_16_17G` | story_q1 | opcja_wyboru | systemowy | – | – | 33 |  |
| 65 | `TANGERINE_Q1_INTRO_REVISED_16_17S` | story_q1 | opcja_wyboru | systemowy | – | – | 33 |  |
| 66 | `TANGERINE_Q1_INTRO_REVISED_16_17V` | story_q1 | opcja_wyboru | systemowy | – | – | 44 |  |
| 67 | `TANGERINE_Q1_INTRO_REVISED_17B` | story_q1 | dialog | bohaterowie | BRYNN | – | 106 |  |
| 68 | `TANGERINE_Q1_INTRO_REVISED_17G` | story_q1 | dialog | bohaterowie | GALADEN | – | 86 |  |
| 69 | `TANGERINE_Q1_INTRO_REVISED_17S` | story_q1 | dialog | bohaterowie | SYRUS | – | 76 |  |
| 70 | `TANGERINE_Q1_INTRO_REVISED_17V` | story_q1 | dialog | bohaterowie | VAERIX | – | 54 |  |
| 71 | `TANGERINE_Q1_OUTRO_LOSE_01` | story_q1 | narracja_fabularna | narrator | – | – | 65 |  |
| 72 | `TANGERINE_Q1_OUTRO_LOSE_1_1` | story_q1 | dialog | inny | BLOOD_SISTER | – | 74 |  |
| 73 | `TANGERINE_Q1_OUTRO_LOSE_1_2` | story_q1 | narracja_fabularna | narrator | – | – | 168 |  |
| 74 | `TANGERINE_Q1_OUTRO_LOSE_02` | story_q1 | dialog | bohaterowie | BRYNN | – | 21 |  |
| 75 | `TANGERINE_Q1_OUTRO_LOSE_03` | story_q1 | dialog | bohaterowie | VAERIX | – | 23 |  |
| 76 | `TANGERINE_Q1_OUTRO_LOSE_04` | story_q1 | dialog | bohaterowie | GALADEN | – | 14 |  |
| 77 | `TANGERINE_Q1_OUTRO_LOSE_05` | story_q1 | dialog | bohaterowie | SYRUS | – | 99 |  |
| 78 | `TANGERINE_Q1_OUTRO_LOSE_06` | story_q1 | dialog | bohaterowie | BRYNN | – | 69 |  |
| 79 | `TANGERINE_Q1_OUTRO_LOSE_07` | story_q1 | dialog | bohaterowie | VAERIX | – | 45 |  |
| 80 | `TANGERINE_Q1_OUTRO_LOSE_08` | story_q1 | dialog | bohaterowie | GALADEN | – | 119 |  |
| 81 | `TANGERINE_Q1_OUTRO_LOSE_09` | story_q1 | dialog | bohaterowie | SYRUS | – | 82 |  |
| 82 | `TANGERINE_Q1_OUTRO_LOSE_10` | story_q1 | dialog | bohaterowie | GALADEN | – | 21 |  |
| 83 | `TANGERINE_Q1_OUTRO_LOSE_11` | story_q1 | dialog | bohaterowie | VAERIX | – | 39 |  |
| 84 | `TANGERINE_Q1_OUTRO_LOSE_12` | story_q1 | dialog | bohaterowie | BRYNN | – | 19 |  |
| 85 | `TANGERINE_Q1_OUTRO_LOSE_13` | story_q1 | dialog | bohaterowie | BRYNN | – | 104 |  |
| 86 | `TANGERINE_Q1_OUTRO_LOSE_14` | story_q1 | dialog | bohaterowie | SYRUS | – | 37 |  |
| 87 | `TANGERINE_Q1_OUTRO_LOSE_15` | story_q1 | dialog | bohaterowie | GALADEN | – | 10 |  |
| 88 | `TANGERINE_Q1_OUTRO_WIN_01` | story_q1 | narracja_fabularna | narrator | – | – | 120 |  |
| 89 | `TANGERINE_Q1_OUTRO_WIN_02A` | story_q1 | narracja_fabularna | narrator | – | – | 89 |  |
| 90 | `TANGERINE_Q1_OUTRO_WIN_02` | story_q1 | dialog | bohaterowie | BRYNN | – | 21 |  |
| 91 | `TANGERINE_Q1_OUTRO_WIN_03` | story_q1 | dialog | bohaterowie | VAERIX | – | 23 |  |
| 92 | `TANGERINE_Q1_OUTRO_WIN_04` | story_q1 | dialog | bohaterowie | GALADEN | – | 14 |  |
| 93 | `TANGERINE_Q1_OUTRO_WIN_05` | story_q1 | dialog | bohaterowie | SYRUS | – | 93 |  |
| 94 | `TANGERINE_Q1_OUTRO_WIN_06` | story_q1 | dialog | bohaterowie | BRYNN | – | 74 |  |
| 95 | `TANGERINE_Q1_OUTRO_WIN_07` | story_q1 | dialog | bohaterowie | VAERIX | – | 29 |  |
| 96 | `TANGERINE_Q1_OUTRO_WIN_08` | story_q1 | dialog | bohaterowie | GALADEN | – | 128 |  |
| 97 | `TANGERINE_Q1_OUTRO_WIN_09` | story_q1 | dialog | bohaterowie | SYRUS | – | 189 |  |
| 98 | `TANGERINE_Q1_OUTRO_WIN_10` | story_q1 | dialog | bohaterowie | GALADEN | – | 9 |  |
| 99 | `TANGERINE_Q1_OUTRO_WIN_11` | story_q1 | dialog | bohaterowie | VAERIX | – | 39 |  |
| 100 | `TANGERINE_Q1_OUTRO_WIN_12` | story_q1 | dialog | bohaterowie | BRYNN | – | 19 |  |
| 101 | `TANGERINE_Q1_OUTRO_WIN_13` | story_q1 | dialog | bohaterowie | BRYNN | – | 104 |  |
| 102 | `TANGERINE_Q1_OUTRO_WIN_14` | story_q1 | dialog | bohaterowie | SYRUS | – | 37 |  |
| 103 | `TANGERINE_Q1_OUTRO_WIN_15` | story_q1 | dialog | bohaterowie | GALADEN | – | 10 |  |
| 104 | `Q1_LECTERN_INTERACT` | scene_q1 | komunikat_questu | narrator | – | – | 263 |  |
| 105 | `DEFAULT_GET_TREASURE_SINGLE` | scene_q1 | system_nagroda | systemowy | – | – | 13 | 2 |
| 106 | `UI_FAIL` | scene_q1 | opcja_wyboru | systemowy | – | – | 8 |  |
| 107 | `UI_PASS` | scene_q1 | opcja_wyboru | systemowy | – | – | 5 |  |
| 108 | `TERRAIN_BOOKSHELF_EMPTY` | scene_q1 | ui_system | systemowy | – | – | 67 |  |
| 109 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_2` | scene_q1 | komunikat_questu | narrator | – | – | 186 |  |
| 110 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_03` | scene_q1 | komunikat_questu | narrator | – | – | 127 |  |
| 111 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_04` | scene_q1 | komunikat_questu | narrator | – | – | 114 |  |
| 112 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05` | scene_q1 | komunikat_questu | narrator | – | – | 179 |  |
| 113 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05_OPT1` | scene_q1 | opcja_wyboru | systemowy | – | – | 14 |  |
| 114 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05_OPT2` | scene_q1 | opcja_wyboru | systemowy | – | – | 13 |  |
| 115 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05_OPT3` | scene_q1 | opcja_wyboru | systemowy | – | – | 17 |  |
| 116 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05_Y` | scene_q1 | komunikat_questu | narrator | – | – | 160 |  |
| 117 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05_R` | scene_q1 | komunikat_questu | narrator | – | – | 140 |  |
| 118 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_05_B` | scene_q1 | komunikat_questu | narrator | – | – | 136 |  |
| 119 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_06` | scene_q1 | komunikat_questu | narrator | – | – | 152 |  |
| 120 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_07` | scene_q1 | komunikat_questu | narrator | – | – | 92 |  |
| 121 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_08` | scene_q1 | komunikat_questu | narrator | – | – | 120 |  |
| 122 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_09` | scene_q1 | komunikat_questu | narrator | – | – | 164 |  |
| 123 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_16` | scene_q1 | komunikat_questu | narrator | – | – | 206 |  |
| 124 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_16_P` | scene_q1 | komunikat_questu | narrator | – | – | 38 |  |
| 125 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_16_F` | scene_q1 | komunikat_questu | narrator | – | – | 94 |  |
| 126 | `BOOKSHELF_CHOICE_BAUBLES_FALSE` | scene_q1 | komunikat_questu | narrator | – | – | 82 |  |
| 127 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_10` | scene_q1 | komunikat_questu | narrator | – | – | 89 |  |
| 128 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_11` | scene_q1 | komunikat_questu | narrator | – | – | 107 |  |
| 129 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15` | scene_q1 | komunikat_questu | narrator | – | – | 277 |  |
| 130 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15_OPT1` | scene_q1 | opcja_wyboru | systemowy | – | – | 14 |  |
| 131 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15_OPT2` | scene_q1 | opcja_wyboru | systemowy | – | – | 15 |  |
| 132 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15_OPT3` | scene_q1 | opcja_wyboru | systemowy | – | – | 29 |  |
| 133 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15_Y` | scene_q1 | komunikat_questu | narrator | – | – | 227 |  |
| 134 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15_R` | scene_q1 | komunikat_questu | narrator | – | – | 144 |  |
| 135 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_15_B` | scene_q1 | komunikat_questu | narrator | – | – | 139 |  |
| 136 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_12` | scene_q1 | komunikat_questu | narrator | – | – | 127 |  |
| 137 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_13` | scene_q1 | komunikat_questu | narrator | – | – | 120 |  |
| 138 | `BOOKSHELF_CHOICE_BAUBLES_FALSE_14` | scene_q1 | komunikat_questu | narrator | – | – | 118 |  |
| 139 | `BOOKSHELF_CHOICE_BOOK_FALSE_2` | scene_q1 | komunikat_questu | narrator | – | – | 94 |  |
| 140 | `BOOKSHELF_CHOICE_BOOK_FALSE_03` | scene_q1 | komunikat_questu | narrator | – | – | 185 |  |
| 141 | `BOOKSHELF_CHOICE_BOOK_FALSE_04` | scene_q1 | komunikat_questu | narrator | – | – | 166 |  |
| 142 | `BOOKSHELF_CHOICE_BOOK_FALSE_05` | scene_q1 | komunikat_questu | narrator | – | – | 234 |  |
| 143 | `HERO_AVENGER_NAME` | scene_q1 | opcja_wyboru | systemowy | – | – | 5 |  |
| 144 | `BOOKSHELF_CHOICE_BOOK_FALSE_07_BRYNN` | scene_q1 | komunikat_questu | narrator | – | – | 333 |  |
| 145 | `BOOKSHELF_CHOICE_BOOK_FALSE_07_KEHLI` | scene_q1 | komunikat_questu | narrator | – | – | 336 |  |
| 146 | `BOOKSHELF_CHOICE_BOOK_FALSE_07_CHANCE` | scene_q1 | komunikat_questu | narrator | – | – | 287 |  |
| 147 | `BOOKSHELF_CHOICE_BOOK_FALSE_07_GALADEN` | scene_q1 | komunikat_questu | narrator | – | – | 214 |  |
| 148 | `BOOKSHELF_CHOICE_BOOK_FALSE_07_VAERIX` | scene_q1 | komunikat_questu | narrator | – | – | 252 |  |
| 149 | `BOOKSHELF_CHOICE_BOOK_FALSE_07_SYRUS` | scene_q1 | komunikat_questu | narrator | – | – | 343 |  |
| 150 | `BOOKSHELF_CHOICE_BOOK_FALSE_07` | scene_q1 | komunikat_questu | narrator | – | – | 318 |  |
| 151 | `BOOKSHELF_CHOICE_BOOK_FALSE_08` | scene_q1 | komunikat_questu | narrator | – | – | 228 |  |
| 152 | `BOOKSHELF_CHOICE_BOOK_FALSE_09` | scene_q1 | komunikat_questu | narrator | – | – | 96 |  |
| 153 | `BOOKSHELF_CHOICE_BOOK_FALSE_06` | scene_q1 | komunikat_questu | narrator | – | – | 234 |  |
| 154 | `BOOKSHELF_CHOICE_BOOK_FALSE` | scene_q1 | komunikat_questu | narrator | – | – | 147 |  |
| 155 | `BOOKSHELF_CHOICE_BOOK_FALSE_10` | scene_q1 | komunikat_questu | narrator | – | – | 173 |  |
| 156 | `BOOKSHELF_CHOICE_BOOK_FALSE_11` | scene_q1 | komunikat_questu | narrator | – | – | 202 |  |
| 157 | `BOOKSHELF_CHOICE_BOOK_FALSE_13` | scene_q1 | komunikat_questu | narrator | – | – | 158 |  |
| 158 | `BOOKSHELF_CHOICE_BOOK_FALSE_14` | scene_q1 | komunikat_questu | narrator | – | – | 150 |  |
| 159 | `BOOKSHELF_CHOICE_BOOK_FALSE_16` | scene_q1 | komunikat_questu | narrator | – | – | 150 |  |
| 160 | `BOOKSHELF_CHOICE_BOOK_FALSE_12` | scene_q1 | komunikat_questu | narrator | – | – | 99 |  |
| 161 | `BOOKSHELF_CHOICE_BOOK_FALSE_12_P` | scene_q1 | komunikat_questu | narrator | – | – | 353 |  |
| 162 | `BOOKSHELF_CHOICE_BOOK_FALSE_12_F` | scene_q1 | komunikat_questu | narrator | – | – | 337 |  |
| 163 | `HERO_PRODIGY_NAME` | scene_q1 | opcja_wyboru | systemowy | – | – | 5 |  |
| 164 | `BOOKSHELF_CHOICE_BOOK_FALSE_15_SYRUS` | scene_q1 | komunikat_questu | narrator | – | – | 280 |  |
| 165 | `BOOKSHELF_CHOICE_BOOK_FALSE_15` | scene_q1 | komunikat_questu | narrator | – | – | 141 | 1 |
| 166 | `BOOKSHELF_CHOICE_BOOK_FALSE_15_P` | scene_q1 | komunikat_questu | narrator | – | – | 190 |  |
| 167 | `BOOKSHELF_CHOICE_BOOK_FALSE_15_F` | scene_q1 | komunikat_questu | narrator | – | – | 261 |  |
| 168 | `HERO_SYRUS_NAME` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 5 |  |
| 169 | `Q1_SYRUS_AMBITION_2` | scene_q1 | opcja_wyboru | systemowy | – | – | 25 |  |
| 170 | `Q1_SYRUS_DRAMATIC_CHOICE_2` | scene_q1 | komunikat_questu | narrator | – | – | 383 |  |
| 171 | `Q1_SYRUS_OPTIMISM_2` | scene_q1 | opcja_wyboru | systemowy | – | – | 46 |  |
| 172 | `OBJECTIVE_UPDATED` | scene_q1 | komunikat_questu | narrator | – | – | 30 | 1 |
| 173 | `TERRAIN_BOOKSHELF_ALREADY_SEARCHED` | scene_q1 | komunikat_questu | narrator | – | – | 92 |  |
| 174 | `BOOKSHELF_CHOICE` | scene_q1 | komunikat_questu | narrator | – | – | 78 |  |
| 175 | `BOOKSHELF_CHOICE_BAUBLES` | scene_q1 | opcja_wyboru | systemowy | – | – | 19 |  |
| 176 | `BOOKSHELF_CHOICE_BOOK` | scene_q1 | opcja_wyboru | systemowy | – | – | 17 |  |
| 177 | `BOOKSHELF_CHOICE_BOTTLES` | scene_q1 | opcja_wyboru | systemowy | – | – | 16 |  |
| 178 | `Q1_OBJECTIVE_5` | scene_q1 | cel_misji | systemowy | – | – | 37 | 1 |
| 179 | `Q1_OBJECTIVE_5_UPDATE` | scene_q1 | komunikat_questu | narrator | – | – | 61 | 1 |
| 180 | `Q1_BOOKSHELF_KEY_GET` | scene_q1 | komunikat_questu | narrator | – | – | 58 |  |
| 181 | `Q1_FOUND_ALL_KEYS` | scene_q1 | komunikat_questu | narrator | – | – | 51 |  |
| 182 | `Q1_OBJECTIVE_5_5` | scene_q1 | cel_misji | systemowy | – | – | 16 |  |
| 183 | `Q1_SYRUS_FIRST` | scene_q1 | komunikat_questu | narrator | – | – | 76 |  |
| 184 | `BOOKSHELF_CHOICE_BOTTLES_FALSE` | scene_q1 | komunikat_questu | narrator | – | – | 114 |  |
| 185 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_03` | scene_q1 | komunikat_questu | narrator | – | – | 105 |  |
| 186 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_04` | scene_q1 | komunikat_questu | narrator | – | – | 93 |  |
| 187 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_05` | scene_q1 | komunikat_questu | narrator | – | – | 93 |  |
| 188 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_06` | scene_q1 | komunikat_questu | narrator | – | – | 151 |  |
| 189 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_07` | scene_q1 | komunikat_questu | narrator | – | – | 191 |  |
| 190 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_08` | scene_q1 | komunikat_questu | narrator | – | – | 156 |  |
| 191 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_09` | scene_q1 | komunikat_questu | narrator | – | – | 109 |  |
| 192 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_2` | scene_q1 | komunikat_questu | narrator | – | – | 116 |  |
| 193 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_10` | scene_q1 | komunikat_questu | narrator | – | – | 86 |  |
| 194 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_11` | scene_q1 | komunikat_questu | narrator | – | – | 95 |  |
| 195 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_12` | scene_q1 | komunikat_questu | narrator | – | – | 121 |  |
| 196 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_13` | scene_q1 | komunikat_questu | narrator | – | – | 171 |  |
| 197 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_15` | scene_q1 | komunikat_questu | narrator | – | – | 131 |  |
| 198 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_14` | scene_q1 | komunikat_questu | narrator | – | – | 101 |  |
| 199 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_14_P` | scene_q1 | komunikat_questu | narrator | – | – | 131 |  |
| 200 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_14_F` | scene_q1 | komunikat_questu | narrator | – | – | 118 |  |
| 201 | `BOOKSHELF_CHOICE_BOTTLES_FALSE_16` | scene_q1 | komunikat_questu | narrator | – | – | 129 |  |
| 202 | `HERO_GALADEN_NAME` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 7 |  |
| 203 | `Q1_CHEST_KEY` | scene_q1 | komunikat_questu | narrator | – | – | 40 |  |
| 204 | `Q1_GALADEN_CONNECT_2` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 35 |  |
| 205 | `Q1_GALADEN_DEDICATE_2` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 23 |  |
| 206 | `Q1_GALADEN_DRAMATIC_CHOICE_2` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 425 |  |
| 207 | `Q1_ONLY_GALADEN` | scene_q1 | komunikat_questu | narrator | – | – | 56 |  |
| 208 | `REMOVE_CHEST_CANCEL` | scene_q1 | komunikat_questu | narrator | – | – | 130 | 2 |
| 209 | `CHEST_ITEM_FIND` | scene_q1 | ui_system | systemowy | – | – | 43 |  |
| 210 | `CHEST_ITEM_FIND_2` | scene_q1 | ui_system | systemowy | – | – | 87 |  |
| 211 | `CHEST_ITEM_FIND_3` | scene_q1 | ui_system | systemowy | – | – | 136 |  |
| 212 | `CHEST_ITEM_FIND_4` | scene_q1 | ui_system | systemowy | – | – | 117 |  |
| 213 | `CHEST_ITEM_FIND_5` | scene_q1 | ui_system | systemowy | – | – | 111 |  |
| 214 | `TEST_AGILITY` | scene_q1 | komunikat_questu | narrator | – | – | 30 | 1 |
| 215 | `TEST_LOCK_0` | scene_q1 | komunikat_questu | narrator | – | – | 133 |  |
| 216 | `TEST_LOCK_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 77 |  |
| 217 | `TEST_LOCK_1` | scene_q1 | komunikat_questu | narrator | – | – | 132 |  |
| 218 | `TEST_INSIGHT` | scene_q1 | komunikat_questu | narrator | – | – | 30 | 1 |
| 219 | `TEST_LOCK_2` | scene_q1 | komunikat_questu | narrator | – | – | 138 |  |
| 220 | `TEST_LOCK_3` | scene_q1 | komunikat_questu | narrator | – | – | 133 |  |
| 221 | `TEST_MIGHT` | scene_q1 | komunikat_questu | narrator | – | – | 25 | 1 |
| 222 | `TEST_WILL` | scene_q1 | komunikat_questu | narrator | – | – | 25 | 1 |
| 223 | `AGILITY` | scene_q1 | opcja_wyboru | systemowy | – | – | 8 |  |
| 224 | `TEST_HOLDER_OPEN` | scene_q1 | komunikat_questu | narrator | – | – | 27 | 2 |
| 225 | `TEST_TRAP_0` | scene_q1 | ui_system | systemowy | – | – | 177 |  |
| 226 | `TEST_TRAP_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 96 |  |
| 227 | `TEST_TRAP_FAIL_0` | scene_q1 | komunikat_questu | narrator | – | – | 202 |  |
| 228 | `INSIGHT` | scene_q1 | opcja_wyboru | systemowy | – | – | 9 |  |
| 229 | `TEST_TRAP_1` | scene_q1 | ui_system | systemowy | – | – | 183 |  |
| 230 | `TEST_TRAP_FAIL_1` | scene_q1 | komunikat_questu | narrator | – | – | 172 |  |
| 231 | `MIGHT` | scene_q1 | opcja_wyboru | systemowy | – | – | 4 |  |
| 232 | `TEST_TRAP_2` | scene_q1 | ui_system | systemowy | – | – | 148 |  |
| 233 | `TEST_TRAP_FAIL_2` | scene_q1 | komunikat_questu | narrator | – | – | 39 | 1 |
| 234 | `TEST_TRAP_3` | scene_q1 | ui_system | systemowy | – | – | 159 |  |
| 235 | `WILLPOWER` | scene_q1 | ui_system | systemowy | – | – | 4 |  |
| 236 | `TEST_TRAP_FAIL_3` | scene_q1 | komunikat_questu | narrator | – | – | 253 |  |
| 237 | `HERO_CHANCE_NAME` | scene_q1 | opcja_wyboru | systemowy | – | – | 4 |  |
| 238 | `TREE_CHOICE_CLIMB_SELECT_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 134 |  |
| 239 | `TREE_CHOICE_CLIMB_SELECT` | scene_q1 | komunikat_questu | narrator | – | – | 101 |  |
| 240 | `TREE_CHOICE_CLIMB_SELECT_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 115 |  |
| 241 | `TERRAIN_FIRE_TIMER_5` | scene_q1 | komunikat_questu | narrator | – | – | 170 |  |
| 242 | `TERRAIN_FIRE_TIMER_AFFLICT` | scene_q1 | komunikat_questu | narrator | – | – | 120 | 1 |
| 243 | `TERRAIN_FIRE_TIMER_4` | scene_q1 | komunikat_questu | narrator | – | – | 132 |  |
| 244 | `TERRAIN_FIRE_TIMER_3` | scene_q1 | komunikat_questu | narrator | – | – | 122 |  |
| 245 | `TERRAIN_FIRE_TIMER_2` | scene_q1 | komunikat_questu | narrator | – | – | 132 |  |
| 246 | `TERRAIN_FIRE_TIMER_1` | scene_q1 | komunikat_questu | narrator | – | – | 243 |  |
| 247 | `TERRAIN_FIRE_TIMER_0` | scene_q1 | komunikat_questu | narrator | – | – | 143 |  |
| 248 | `TERRAIN_WELL_PREVIEW_DESTROYED` | scene_q1 | komunikat_questu | narrator | – | – | 58 |  |
| 249 | `TERRAIN_WELL_PREVIEW_BAD_WATER` | scene_q1 | komunikat_questu | narrator | – | – | 38 |  |
| 250 | `TERRAIN_WELL_PREVIEW_LUCKY` | scene_q1 | komunikat_questu | narrator | – | – | 63 |  |
| 251 | `TERRAIN_WELL_PREVIEW` | scene_q1 | komunikat_questu | narrator | – | – | 100 |  |
| 252 | `STORY_QUEST_1` | scene_q1 | model:QuestModel | systemowy | – | – | 11 |  |
| 253 | `Q1_CHOOSE_BRYNN` | scene_q1 | opcja_wyboru | systemowy | – | – | 29 |  |
| 254 | `Q1_CHOOSE_GALADEN` | scene_q1 | opcja_wyboru | systemowy | – | – | 32 |  |
| 255 | `Q1_CHOOSE_HERO_ON_WATCH` | scene_q1 | komunikat_questu | narrator | – | – | 164 | 1 |
| 256 | `Q1_CHOOSE_SYRUS` | scene_q1 | opcja_wyboru | systemowy | – | – | 17 |  |
| 257 | `Q1_CHOOSE_VAERIX` | scene_q1 | opcja_wyboru | systemowy | – | – | 38 |  |
| 258 | `Q1_BRYNN_IS_ON_WATCH` | scene_q1 | komunikat_questu | narrator | – | – | 123 |  |
| 259 | `Q1_THE_NIGHT_PASSES` | scene_q1 | komunikat_questu | narrator | – | – | 337 | 1 |
| 260 | `Q1_TEACH_WELCOME` | scene_q1 | komunikat_questu | narrator | – | – | 562 |  |
| 261 | `Q1_PLACE_16B` | scene_q1 | komunikat_questu | narrator | – | – | 96 | 1 |
| 262 | `Q1_TEACH_UNDERLAYS` | scene_q1 | komunikat_questu | narrator | – | – | 398 |  |
| 263 | `Q1_PLACE_EXPLORE_0` | scene_q1 | komunikat_questu | narrator | – | – | 128 |  |
| 264 | `Q1_PLACE_EXPLORE_1` | scene_q1 | komunikat_questu | narrator | – | – | 178 |  |
| 265 | `Q1_EXPLORE_TOKEN` | scene_q1 | komunikat_questu | narrator | – | – | 259 |  |
| 266 | `Q1_PLACE_HERO` | scene_q1 | komunikat_questu | narrator | – | – | 180 | 1 |
| 267 | `Q1_OBJECTIVE_1` | scene_q1 | cel_misji | systemowy | – | – | 34 |  |
| 268 | `Q1_GALADEN_IS_ON_WATCH` | scene_q1 | komunikat_questu | narrator | – | – | 104 |  |
| 269 | `Q1_SYRUS_IS_ON_WATCH` | scene_q1 | komunikat_questu | narrator | – | – | 156 |  |
| 270 | `Q1_VAERIX_IS_ON_WATCH` | scene_q1 | komunikat_questu | narrator | – | – | 111 |  |
| 271 | `ENEMY_ACTIVATION_DRAGON_DIVE` | scene_q1 | walka_teren | systemowy | – | – | 225 | 2 |
| 272 | `ENEMY_CONFUSION_ACTIVATION_OFFMAP` | scene_q1 | komunikat_questu | narrator | – | – | 124 | 3 |
| 273 | `ENEMY_CONFUSION_ACTIVATION_OFFMAP_2` | scene_q1 | komunikat_questu | narrator | – | – | 85 | 2 |
| 274 | `ENEMY_CONFUSION_ACTIVATION_01` | scene_q1 | walka_teren | systemowy | – | – | 164 |  |
| 275 | `ENEMY_CONFUSION_ACTIVATION_02` | scene_q1 | walka_teren | systemowy | – | – | 161 | 1 |
| 276 | `ENEMY_CONFUSION_ACTIVATION_03` | scene_q1 | walka_teren | systemowy | – | – | 151 | 1 |
| 277 | `ENEMY_CONFUSION_ACTIVATION_04` | scene_q1 | walka_teren | systemowy | – | – | 136 | 2 |
| 278 | `TERRAIN_BURNING_INSPECT` | scene_q1 | komunikat_questu | narrator | – | – | 365 |  |
| 279 | `TERRAIN_FIRE_CHANNEL` | scene_q1 | opcja_wyboru | systemowy | – | – | 31 |  |
| 280 | `TERRAIN_FIRE_DOUSE` | scene_q1 | opcja_wyboru | systemowy | – | – | 11 |  |
| 281 | `TERRAIN_FIRE_DOUSE_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 157 | 1 |
| 282 | `TERRAIN_FIRE_DOUSE_TEST_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 62 |  |
| 283 | `TERRAIN_FIRE_DOUSE_TEST_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 122 |  |
| 284 | `TERRAIN_FIRE_SYRUS_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 177 |  |
| 285 | `TERRAIN_FIRE_SYRUS_TEST_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 226 |  |
| 286 | `TERRAIN_FIRE_SYRUS_TEST_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 148 |  |
| 287 | `TERRAIN_FIRE_SYRUS_TEST_SUPER` | scene_q1 | komunikat_questu | narrator | – | – | 288 |  |
| 288 | `TERRAIN_FIRE_CHANNEL_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 252 |  |
| 289 | `TERRAIN_FIRE_CHANNEL_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 295 |  |
| 290 | `TERRAIN_FIRE_CHANNEL_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 124 |  |
| 291 | `HERO_BRYNN_NAME` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 5 |  |
| 292 | `HERO_VAERIX_NAME` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 6 |  |
| 293 | `Q1_BRYNN_DOOR` | scene_q1 | komunikat_questu | narrator | – | – | 128 | 1 |
| 294 | `Q1_DOOR_IS_LOCKED` | scene_q1 | quest_niepowiazany | narrator | – | – | 42 |  |
| 295 | `Q1_DOOR_POP_TO_5A` | scene_q1 | komunikat_questu | narrator | – | – | 74 |  |
| 296 | `Q1_DOOR_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 53 |  |
| 297 | `Q1_PLACE_5A` | scene_q1 | komunikat_questu | narrator | – | – | 54 |  |
| 298 | `Q1_TEACH_GARGOYLES` | scene_q1 | komunikat_questu | narrator | – | – | 507 |  |
| 299 | `Q1_VAERIX_TABLE` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 117 |  |
| 300 | `DEFAULT_SPAWN_ENEMY_MULTI` | scene_q1 | walka_teren | systemowy | – | – | 32 |  |
| 301 | `Q1_GALADEN_CHEST` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 145 |  |
| 302 | `Q1_PLACE_16A_TERRAIN` | scene_q1 | komunikat_questu | narrator | – | – | 26 |  |
| 303 | `Q1_PLACE_GATE` | scene_q1 | komunikat_questu | narrator | – | – | 55 |  |
| 304 | `Q1_OBJECTIVE_5_0` | scene_q1 | quest_niepowiazany | narrator | – | – | 32 |  |
| 305 | `Q1_BRYNN_DOOR_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 170 |  |
| 306 | `Q1_GALADEN_DOOR` | scene_q1 | komunikat_questu | narrator | – | – | 229 | 1 |
| 307 | `Q1_GALADEN_DOOR_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 79 |  |
| 308 | `Q1_SYRUS_DOOR` | scene_q1 | komunikat_questu | narrator | – | – | 267 | 1 |
| 309 | `Q1_SYRUS_DOOR_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 89 |  |
| 310 | `Q1_VAERIX_DOOR` | scene_q1 | komunikat_questu | narrator | – | – | 171 | 1 |
| 311 | `Q1_VAERIX_DOOR_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 120 |  |
| 312 | `Q1_DOOR_SWING_OPEN` | scene_q1 | komunikat_questu | narrator | – | – | 69 |  |
| 313 | `Q1_PLACE_6B` | scene_q1 | komunikat_questu | narrator | – | – | 38 |  |
| 314 | `Q1_SYRUS_BOOKSHELF` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 203 |  |
| 315 | `Q1_PLACE_SOLIDER_1` | scene_q1 | komunikat_questu | narrator | – | – | 102 |  |
| 316 | `Q1_BRYNN_SHOUT` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 117 |  |
| 317 | `Q1_PORTAL_FIREBALL` | scene_q1 | komunikat_questu | narrator | – | – | 211 |  |
| 318 | `Q1_SPAWN_MORE` | scene_q1 | komunikat_questu | narrator | – | – | 56 |  |
| 319 | `Q1_PORTAL_EARTHQUAKE` | scene_q1 | komunikat_questu | narrator | – | – | 121 |  |
| 320 | `Q1_PORTAL_BOOST` | scene_q1 | komunikat_questu | narrator | – | – | 177 |  |
| 321 | `Q1_ENEMY_DEFEAT` | scene_q1 | komunikat_questu | narrator | – | – | 51 | 1 |
| 322 | `Q1_SIGHT_KNOWN` | scene_q1 | komunikat_questu | narrator | – | – | 76 |  |
| 323 | `Q1_PLACE_9B_LATE` | scene_q1 | komunikat_questu | narrator | – | – | 18 |  |
| 324 | `Q1_PLACE_TREE` | scene_q1 | komunikat_questu | narrator | – | – | 16 |  |
| 325 | `DEFAULT_SPAWN_ENEMY` | scene_q1 | walka_teren | systemowy | – | – | 20 | 1 |
| 326 | `Q1_RED_LIGHT_SOURCE` | scene_q1 | komunikat_questu | narrator | – | – | 97 |  |
| 327 | `Q1_PLACE_18B` | scene_q1 | komunikat_questu | narrator | – | – | 19 |  |
| 328 | `Q1_PLACE_18B_TERRAIN` | scene_q1 | komunikat_questu | narrator | – | – | 61 |  |
| 329 | `Q1_PORTAL_PLACE` | scene_q1 | komunikat_questu | narrator | – | – | 95 |  |
| 330 | `Q1_BOSS_SPAWN` | scene_q1 | walka_teren | systemowy | – | – | 361 | 1 |
| 331 | `Q1_NEKRUL_SPAWN_EXTRA` | scene_q1 | komunikat_questu | narrator | – | – | 180 |  |
| 332 | `Q1_OBJECTIVE_8` | scene_q1 | cel_misji | systemowy | – | – | 19 |  |
| 333 | `OBJECTIVE_FINAL` | scene_q1 | komunikat_questu | narrator | – | – | 24 | 1 |
| 334 | `Q1_PLACE_4B_LATE` | scene_q1 | komunikat_questu | narrator | – | – | 18 |  |
| 335 | `Q1_GALADEN_SIGHT_TOKEN_3B` | scene_q1 | komunikat_questu | narrator | – | – | 236 |  |
| 336 | `Q1_PLACE_4B` | scene_q1 | komunikat_questu | narrator | – | – | 44 |  |
| 337 | `Q1_TEACH_INTERACT` | scene_q1 | komunikat_questu | narrator | – | – | 422 |  |
| 338 | `Q1_PLACE_EXPLORE` | scene_q1 | komunikat_questu | narrator | – | – | 58 |  |
| 339 | `Q1_ATTACK_AN_ENEMY` | scene_q1 | komunikat_questu | narrator | – | – | 253 |  |
| 340 | `Q1_SIGHT_TOKEN_3B` | scene_q1 | komunikat_questu | narrator | – | – | 224 |  |
| 341 | `Q1_PLACE_9B` | scene_q1 | komunikat_questu | narrator | – | – | 44 |  |
| 342 | `Q1_SPAWN_FIRST_BESERKER` | scene_q1 | walka_teren | systemowy | – | – | 60 | 1 |
| 343 | `Q1_GATE_KEYS_FOUND_FLAVOR` | scene_q1 | komunikat_questu | narrator | – | – | 64 |  |
| 344 | `Q1_GATE_KEYS_NOT_FOUND_FLAVOR` | scene_q1 | komunikat_questu | narrator | – | – | 89 | 1 |
| 345 | `Q1_GATE_POP` | scene_q1 | komunikat_questu | narrator | – | – | 143 |  |
| 346 | `Q1_PLACE_17A` | scene_q1 | komunikat_questu | narrator | – | – | 39 |  |
| 347 | `Q1_OBJECTIVE_6` | scene_q1 | cel_misji | systemowy | – | – | 38 | 1 |
| 348 | `Q1_OBJECTIVE_6_UPDATE` | scene_q1 | komunikat_questu | narrator | – | – | 62 | 1 |
| 349 | `Q1_PLACE_17A_TERRAIN` | scene_q1 | komunikat_questu | narrator | – | – | 70 |  |
| 350 | `Q1_PLACE_INTERACTS` | scene_q1 | komunikat_questu | narrator | – | – | 77 |  |
| 351 | `Q1_SPAWN_ENEMY` | scene_q1 | walka_teren | systemowy | – | – | 21 | 1 |
| 352 | `Q1_SAVE_VILLAGERS` | scene_q1 | komunikat_questu | narrator | – | – | 125 |  |
| 353 | `Q1_GATE_NO_POP` | scene_q1 | komunikat_questu | narrator | – | – | 79 |  |
| 354 | `HERO_KEHLI_NAME` | scene_q1 | opcja_wyboru | systemowy | – | – | 5 |  |
| 355 | `TERRAIN_WELL_CHANCE` | scene_q1 | komunikat_questu | narrator | – | – | 75 |  |
| 356 | `TERRAIN_WELL_CHANCE_DIVE` | scene_q1 | opcja_wyboru | systemowy | – | – | 9 |  |
| 357 | `TERRAIN_WELL_COIN` | scene_q1 | opcja_wyboru | systemowy | – | – | 13 |  |
| 358 | `TERRAIN_WELL_DRINK` | scene_q1 | opcja_wyboru | systemowy | – | – | 10 |  |
| 359 | `TERRAIN_WELL_CHANCE_DIVE_CHALLENGE` | scene_q1 | komunikat_questu | narrator | – | – | 91 |  |
| 360 | `TERRAIN_WELL_CHANCE_DIVE_CHALLENGE_FAIL` | scene_q1 | ui_system | systemowy | – | – | 230 |  |
| 361 | `TERRAIN_WELL_CHANCE_DIVE_CHALLENGE_PASS` | scene_q1 | ui_system | systemowy | – | – | 163 |  |
| 362 | `TERRAIN_WELL_BRYNN` | scene_q1 | komunikat_questu | narrator | – | – | 46 |  |
| 363 | `TERRAIN_WELL_BRYNN_CHALLENGE` | scene_q1 | opcja_wyboru | systemowy | – | – | 42 |  |
| 364 | `TERRAIN_WELL_BRYNN_CHALLENGE_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 139 |  |
| 365 | `TERRAIN_WELL_BRYNN_CHALLENGE_FAIL_HEROES` | scene_q1 | komunikat_questu | narrator | – | – | 254 |  |
| 366 | `TERRAIN_WELL_BRYNN_CHALLENGE_FAIL_ENEMIES` | scene_q1 | komunikat_questu | narrator | – | – | 208 |  |
| 367 | `TERRAIN_WELL_BRYNN_CHALLENGE_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 363 |  |
| 368 | `TERRAIN_WELL_GALADEN` | scene_q1 | komunikat_questu | narrator | – | – | 35 |  |
| 369 | `TERRAIN_WELL_GALADEN_REFLECTION` | scene_q1 | opcja_wyboru | systemowy | – | – | 23 |  |
| 370 | `TERRAIN_WELL_GALADEN_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 120 |  |
| 371 | `TERRAIN_WELL_GALADEN_TEST_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 154 | 1 |
| 372 | `TERRAIN_WELL_GALADEN_TEST_PASS+` | scene_q1 | komunikat_questu | narrator | – | – | 233 |  |
| 373 | `TERRAIN_WELL_SYRUS` | scene_q1 | komunikat_questu | narrator | – | – | 37 |  |
| 374 | `TERRAIN_WELL_SYRUS_MAGIC` | scene_q1 | opcja_wyboru | systemowy | – | – | 19 |  |
| 375 | `TERRAIN_WELL_SYRUS_TETST` | scene_q1 | komunikat_questu | narrator | – | – | 96 |  |
| 376 | `TERRAIN_WELL_SYRUS_TEST_FAIL` | scene_q1 | ui_system | systemowy | – | – | 107 |  |
| 377 | `TERRAIN_WELL_SYRUS_TEST_PASS` | scene_q1 | ui_system | systemowy | – | – | 180 |  |
| 378 | `TERRAIN_WELL_SYRUS_TEST_PASS+` | scene_q1 | ui_system | systemowy | – | – | 143 |  |
| 379 | `TERRAIN_WELL_KEHLI` | scene_q1 | komunikat_questu | narrator | – | – | 44 |  |
| 380 | `TERRAIN_WELL_KEHLI_BREW` | scene_q1 | opcja_wyboru | systemowy | – | – | 17 |  |
| 381 | `TERRAIN_WELL_KEHLI_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 150 |  |
| 382 | `TERRAIN_WELL_KEHLI_TEST_FAIL` | scene_q1 | ui_system | systemowy | – | – | 145 |  |
| 383 | `TERRAIN_WELL_KEHLI_TEST_PASS` | scene_q1 | ui_system | systemowy | – | – | 90 |  |
| 384 | `TERRAIN_WELL_VAERIX` | scene_q1 | komunikat_questu | narrator | – | – | 35 |  |
| 385 | `TERRAIN_WELL_VAERIX_HEALING` | scene_q1 | opcja_wyboru | systemowy | – | – | 31 |  |
| 386 | `TERRAIN_WELL_VAERIX_HEALING_EFFECT` | scene_q1 | komunikat_questu | narrator | – | – | 208 |  |
| 387 | `TERRAIN_WELL_LUCKY_CHARM_COIN` | scene_q1 | komunikat_questu | narrator | – | – | 164 |  |
| 388 | `ARGUMENT_1` | scene_q1 | komunikat_questu | narrator | – | – | 6 | 1 |
| 389 | `TERRAIN_WELL_DRINK_RESULT_LUCKY` | scene_q1 | komunikat_questu | narrator | – | – | 104 |  |
| 390 | `TERRAIN_WELL_DRINK_RESULT_LUCKY_POST` | scene_q1 | komunikat_questu | narrator | – | – | 44 |  |
| 391 | `TERRAIN_WELL_DRINK_RESULT` | scene_q1 | komunikat_questu | narrator | – | – | 72 |  |
| 392 | `Q1_PERSON_1_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 112 |  |
| 393 | `Q1_PERSON_1_TEST_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 19 |  |
| 394 | `Q1_PERSON_1_TEST_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 289 |  |
| 395 | `Q1_SOLDIER_1_BRYNN` | scene_q1 | komunikat_questu | narrator | – | – | 258 |  |
| 396 | `Q1_SOLDIER_1_BRYNN_2` | scene_q1 | komunikat_questu | narrator | – | – | 571 | 1 |
| 397 | `Q1_WHAT_IS_A_CONSUMABLE` | scene_q1 | komunikat_questu | narrator | – | – | 351 |  |
| 398 | `Q1_BRYNN_DRAMATIC_CHOICE_2` | scene_q1 | komunikat_questu | narrator | – | – | 340 |  |
| 399 | `Q1_BRYNN_VALOR_2` | scene_q1 | opcja_wyboru | systemowy | – | – | 42 |  |
| 400 | `Q1_BYRNN_NOBLE_2` | scene_q1 | opcja_wyboru | systemowy | – | – | 45 |  |
| 401 | `Q1_SAVE_VILLAGERS_BRYNN` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 252 |  |
| 402 | `Q1_SAVE_VILLAGERS_DEPART` | scene_q1 | komunikat_questu | narrator | – | – | 120 |  |
| 403 | `Q1_FLASH_LIGHT` | scene_q1 | komunikat_questu | narrator | – | – | 287 |  |
| 404 | `Q1_BRYNN_DRAMATIC_CHOICE` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 239 |  |
| 405 | `Q1_BRYNN_NOBLE` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 9 |  |
| 406 | `Q1_BRYNN_VALOR` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 6 |  |
| 407 | `Q1_GALADEN_CONNECT` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 28 |  |
| 408 | `Q1_GALADEN_DEDICATE` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 35 |  |
| 409 | `Q1_GALADEN_DRAMATIC_CHOICE` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 214 |  |
| 410 | `Q1_NOT_BRYNN` | scene_q1 | komunikat_questu | narrator | – | – | 52 |  |
| 411 | `Q1_VAERIX_DRAMATIC_CHOICE` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 169 |  |
| 412 | `Q1_VAERIX_REBEL` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 61 |  |
| 413 | `Q1_VAERIX_VISION` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 49 |  |
| 414 | `Q1_SOLDIER_1` | scene_q1 | komunikat_questu | narrator | – | – | 629 | 1 |
| 415 | `Q1_SYRUS_AMBITION` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 21 |  |
| 416 | `Q1_SYRUS_DRAMATIC_CHOICE` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 162 |  |
| 417 | `Q1_SYRUS_OPTIMISIM` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 33 |  |
| 418 | `Q1_PLACE_15B` | scene_q1 | komunikat_questu | narrator | – | – | 18 |  |
| 419 | `Q1_JUMP_TEACH` | scene_q1 | komunikat_questu | narrator | – | – | 305 |  |
| 420 | `Q1_PLACE_SIGHT_TO_NEKRUL` | scene_q1 | komunikat_questu | narrator | – | – | 70 |  |
| 421 | `Q1_OBJECTIVE_7` | scene_q1 | cel_misji | systemowy | – | – | 44 |  |
| 422 | `Q1_SAVE_VILLAGERS_GALADEN` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 353 |  |
| 423 | `Q1_SAVE_VILLAGERS_VAERIX` | scene_q1 | komunikat_questu | narrator | – | – | 251 |  |
| 424 | `Q1_PERSON_2_TEST` | scene_q1 | komunikat_questu | narrator | – | – | 122 |  |
| 425 | `Q1_PERSON_2_TEST_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 349 |  |
| 426 | `TERRAIN_LARGE_TABLE_PREVIEW_0_ITEMS` | scene_q1 | komunikat_questu | narrator | – | – | 67 |  |
| 427 | `TERRAIN_LARGE_TABLE_ITEM_1` | scene_q1 | ui_system | systemowy | – | – | 13 |  |
| 428 | `TERRAIN_LARGE_TABLE_ITEM_3` | scene_q1 | ui_system | systemowy | – | – | 28 |  |
| 429 | `TERRAIN_LARGE_TABLE_PREVIEW_2_ITEMS` | scene_q1 | komunikat_questu | narrator | – | – | 83 | 2 |
| 430 | `TERRAIN_LARGE_TABLE_OPTION_1` | scene_q1 | opcja_wyboru | systemowy | – | – | 20 |  |
| 431 | `TERRAIN_LARGE_TABLE_OPTION_3` | scene_q1 | opcja_wyboru | systemowy | – | – | 36 |  |
| 432 | `TERRAIN_LARGE_TABLE_PREVIEW_1_ITEM` | scene_q1 | komunikat_questu | narrator | – | – | 73 | 1 |
| 433 | `TERRAIN_LARGE_TABLE_ITEM_4` | scene_q1 | ui_system | systemowy | – | – | 15 |  |
| 434 | `TERRAIN_LARGE_TABLE_RESULT_1` | scene_q1 | komunikat_questu | narrator | – | – | 280 |  |
| 435 | `TERRAIN_LARGE_TABLE_ITEM_2` | scene_q1 | ui_system | systemowy | – | – | 19 |  |
| 436 | `TERRAIN_LARGE_TABLE_RESULT_3` | scene_q1 | komunikat_questu | narrator | – | – | 288 |  |
| 437 | `TERRAIN_LARGE_TABLE_OPTION_4` | scene_q1 | opcja_wyboru | systemowy | – | – | 18 |  |
| 438 | `TERRAIN_LARGE_TABLE_RESULT_4` | scene_q1 | komunikat_questu | narrator | – | – | 143 |  |
| 439 | `TERRAIN_LARGE_TABLE_OPTION_2` | scene_q1 | opcja_wyboru | systemowy | – | – | 16 |  |
| 440 | `TERRAIN_LARGE_TABLE_RESULT_2` | scene_q1 | komunikat_questu | narrator | – | – | 195 |  |
| 441 | `Q1_NEKRUL_DEFEAT` | scene_q1 | komunikat_questu | narrator | – | – | 296 |  |
| 442 | `Q1_PLACE_REMAINING_HEROES` | scene_q1 | komunikat_questu | narrator | – | – | 109 |  |
| 443 | `Q1_OBJECTIVE_4` | scene_q1 | cel_misji | systemowy | – | – | 18 |  |
| 444 | `Q1_END_ROUND_REMINDER` | scene_q1 | komunikat_questu | narrator | – | – | 436 | 1 |
| 445 | `TREE_CHOICE_FRUIT_SELECT` | scene_q1 | komunikat_questu | narrator | – | – | 154 |  |
| 446 | `TERRAIN_CAULDRON_POTION_TEST_A` | scene_q1 | komunikat_questu | narrator | – | – | 199 |  |
| 447 | `TERRAIN_CAULDRON_POTION_F` | scene_q1 | komunikat_questu | narrator | – | – | 71 |  |
| 448 | `TERRAIN_CAULDRON_POTION_P` | scene_q1 | ui_system | systemowy | – | – | 179 |  |
| 449 | `TERRAIN_CAULDRON_KEHLI` | scene_q1 | komunikat_questu | narrator | – | – | 183 |  |
| 450 | `TERRAIN_CAULDRON_KEHLI_01` | scene_q1 | opcja_wyboru | systemowy | – | – | 4 |  |
| 451 | `TERRAIN_CAULDRON_KEHLI_02` | scene_q1 | opcja_wyboru | systemowy | – | – | 8 |  |
| 452 | `TERRAIN_CAULDRON_KEHLI_03` | scene_q1 | opcja_wyboru | systemowy | – | – | 8 |  |
| 453 | `TERRAIN_CAULDRON_KEHLI_HEAL` | scene_q1 | komunikat_questu | narrator | – | – | 104 | 1 |
| 454 | `TERRAIN_CAULDRON_KEHLI_ENEMIES_NONE` | scene_q1 | komunikat_questu | narrator | – | – | 241 |  |
| 455 | `TERRAIN_CAULDRON_KEHLI_ENEMIES` | scene_q1 | komunikat_questu | narrator | – | – | 154 | 1 |
| 456 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_00` | scene_q1 | komunikat_questu | narrator | – | – | 153 | 1 |
| 457 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_08` | scene_q1 | ui_system | systemowy | – | – | 48 |  |
| 458 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_05` | scene_q1 | ui_system | systemowy | – | – | 35 |  |
| 459 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_02` | scene_q1 | ui_system | systemowy | – | – | 69 |  |
| 460 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_07` | scene_q1 | ui_system | systemowy | – | – | 45 |  |
| 461 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_09` | scene_q1 | ui_system | systemowy | – | – | 100 |  |
| 462 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_04` | scene_q1 | ui_system | systemowy | – | – | 76 |  |
| 463 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_01` | scene_q1 | ui_system | systemowy | – | – | 48 |  |
| 464 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_06` | scene_q1 | ui_system | systemowy | – | – | 123 |  |
| 465 | `TERRAIN_CAULDRON_KEHLI_WILDCARD_03` | scene_q1 | ui_system | systemowy | – | – | 72 |  |
| 466 | `TERRAIN_CAULDRON_POTION_TEST_B` | scene_q1 | komunikat_questu | narrator | – | – | 178 |  |
| 467 | `TERRAIN_CAULDRON_POTION_AUTO` | scene_q1 | ui_system | systemowy | – | – | 105 |  |
| 468 | `TERRAIN_CAULDRON_POTION_LOOT` | scene_q1 | ui_system | systemowy | – | – | 176 |  |
| 469 | `Q1_NO_MORE_TABLE` | scene_q1 | komunikat_questu | narrator | – | – | 70 |  |
| 470 | `Q1_ROUND_TABLE_LETTER` | scene_q1 | komunikat_questu | narrator | – | – | 711 |  |
| 471 | `Q1_WHAT_IS_A_RECIPE` | scene_q1 | komunikat_questu | narrator | – | – | 321 |  |
| 472 | `Q1_TABLE_KEY` | scene_q1 | komunikat_questu | narrator | – | – | 41 |  |
| 473 | `Q1_VAERIX_DRAMATIC_CHOICE_2` | scene_q1 | komunikat_questu | narrator | – | bohater z BB | 400 |  |
| 474 | `Q1_VAERIX_REBEL_2` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 48 |  |
| 475 | `Q1_VAERIX_VISION_2` | scene_q1 | opcja_wyboru | systemowy | – | bohater z BB | 60 |  |
| 476 | `Q1_ONLY_VAERIX` | scene_q1 | komunikat_questu | narrator | – | – | 52 |  |
| 477 | `TREE_CHOICE_MOSS_SELECT` | scene_q1 | ui_system | systemowy | – | – | 52 |  |
| 478 | `TERRAIN_SMALL_TABLE_0` | scene_q1 | komunikat_questu | narrator | – | – | 48 |  |
| 479 | `TERRAIN_SMALL_TABLE_1` | scene_q1 | komunikat_questu | narrator | – | – | 79 |  |
| 480 | `TERRAIN_SMALL_TABLE_2` | scene_q1 | komunikat_questu | narrator | – | – | 67 |  |
| 481 | `TERRAIN_SMALL_TABLE_3` | scene_q1 | komunikat_questu | narrator | – | – | 101 |  |
| 482 | `TERRAIN_SMALL_TABLE_PREVIEW_0` | scene_q1 | komunikat_questu | narrator | – | – | 16 |  |
| 483 | `TERRAIN_SMALL_TABLE_PREVIEW_1` | scene_q1 | komunikat_questu | narrator | – | – | 63 |  |
| 484 | `TERRAIN_SMALL_TABLE_PREVIEW_2` | scene_q1 | komunikat_questu | narrator | – | – | 57 |  |
| 485 | `TERRAIN_SMALL_TABLE_PREVIEW_3` | scene_q1 | komunikat_questu | narrator | – | – | 57 |  |
| 486 | `TERRAIN_BARRICADE` | scene_q1 | komunikat_questu | narrator | – | – | 210 |  |
| 487 | `TERRAIN_BARRICADE_OPTION_1` | scene_q1 | opcja_wyboru | systemowy | – | – | 21 |  |
| 488 | `TERRAIN_BARRICADE_OPTION_2` | scene_q1 | opcja_wyboru | systemowy | – | – | 18 |  |
| 489 | `TERRAIN_BARRICADE_OPTION_SYRUS` | scene_q1 | opcja_wyboru | systemowy | – | – | 27 |  |
| 490 | `TERRAIN_BARRICADE_MIGHT_CHALLENGE` | scene_q1 | komunikat_questu | narrator | – | – | 133 |  |
| 491 | `TERRAIN_BARRICADE_CHALLENGE_FAIL` | scene_q1 | komunikat_questu | narrator | – | – | 97 |  |
| 492 | `TERRAIN_BARRICADE_CHALLENGE_PASS` | scene_q1 | komunikat_questu | narrator | – | – | 63 |  |
| 493 | `TERRAIN_BARRICADE_INSIGHT_CHALLENGE` | scene_q1 | komunikat_questu | narrator | – | – | 61 |  |
| 494 | `TERRAIN_BARRICADE_PASS_SYRUS` | scene_q1 | komunikat_questu | narrator | – | – | 200 |  |
| 495 | `Q1_ROUND_TABLE_OVER` | scene_q1 | komunikat_questu | narrator | – | – | 43 |  |
| 496 | `Q1_ROUND_TABLE_PREVIEW` | scene_q1 | komunikat_questu | narrator | – | – | 50 |  |
| 497 | `Q1_PLACE_ARCHWAY_11B` | scene_q1 | komunikat_questu | narrator | – | – | 195 |  |
| 498 | `Q1_OBJECTIVE_3` | scene_q1 | cel_misji | systemowy | – | – | 22 |  |
| 499 | `Q1_TAP_TEACH` | scene_q1 | komunikat_questu | narrator | – | – | 281 |  |
| 500 | `TERRAIN_CAULRON_DONE` | scene_q1 | komunikat_questu | narrator | – | – | 55 |  |
| 501 | `TERRAIN_TREE_DONE` | scene_q1 | komunikat_questu | narrator | – | – | 107 |  |
| 502 | `TREE_CHOICE` | scene_q1 | komunikat_questu | narrator | – | – | 144 |  |
| 503 | `TREE_CHOICE_CLIMB` | scene_q1 | opcja_wyboru | systemowy | – | – | 16 |  |
| 504 | `TREE_CHOICE_FRUIT` | scene_q1 | opcja_wyboru | systemowy | – | – | 12 |  |
| 505 | `TREE_CHOICE_MOSS` | scene_q1 | opcja_wyboru | systemowy | – | – | 34 |  |
| 506 | `TUTORIAL_CRAFTING` | scene_q1 | komunikat_questu | narrator | – | – | 275 |  |
| 507 | `TUTORIAL_CRAFTING_2` | scene_q1 | komunikat_questu | narrator | – | – | 537 |  |
| 508 | `TUTORIAL_ARMORY` | scene_q1 | komunikat_questu | narrator | – | – | 271 |  |
| 509 | `TUTORIAL_STORE` | scene_q1 | komunikat_questu | narrator | – | – | 185 |  |
| 510 | `UI_UNDERLAY_WATER` | scene_q1 | komunikat_questu | narrator | – | – | 95 |  |
| 511 | `TERRAIN_WELL_WATER_SPOILED` | scene_q1 | komunikat_questu | narrator | – | – | 74 |  |
| 512 | `TERRAIN_WELL_DESTROYED` | scene_q1 | komunikat_questu | narrator | – | – | 84 |  |
| 513 | `STORY_QUEST_3` | scene_q1 | model:QuestModel | systemowy | – | – | 13 |  |
| 514 | `STORY_QUEST_5` | scene_q1 | model:QuestModel | systemowy | – | – | 13 |  |
| 515 | `TUTORIAL_TRAVEL` | scene_q1 | zdarzenie | narrator | – | – | 201 |  |
| 516 | `STORY_QUEST_10` | scene_q1 | model:QuestModel | systemowy | – | – | 9 |  |
| 517 | `SIDE_QUEST_2` | scene_q1 | model:QuestModel | systemowy | – | – | 15 |  |
| 518 | `STORY_QUEST_2` | scene_q1 | model:QuestModel | systemowy | – | – | 16 |  |
| 519 | `STORY_QUEST_9` | scene_q1 | model:QuestModel | systemowy | – | – | 17 |  |
| 520 | `TUTORIAL_CITY_1` | scene_q1 | zdarzenie | narrator | – | – | 151 |  |
| 521 | `TUTORIAL_CITY_2` | scene_q1 | zdarzenie | narrator | – | – | 149 |  |
| 522 | `XP_GAIN_1` | scene_q1 | zdarzenie | narrator | – | – | 132 |  |
| 523 | `XP_GAIN_1_KEHLI_CHANCE` | scene_q1 | ui_system | systemowy | – | – | 75 |  |
| 524 | `TUTORIAL_EVENT` | scene_q1 | zdarzenie | narrator | – | – | 90 |  |
| 525 | `NEW_QUEST` | scene_q1 | zdarzenie | narrator | – | – | 33 |  |
| 526 | `ENEMY_BERSERKER_PLUR` | enemies_q1 | model:EnemyModel | systemowy | – | – | 11 |  |
| 527 | `ENEMY_BERSERKER_SING` | enemies_q1 | model:EnemyModel | systemowy | – | – | 9 |  |
| 528 | `ENEMY_DEFEND_BERSERKER` | enemies_q1 | model:EnemyModel | systemowy | – | – | 87 |  |
| 529 | `ENEMY_DEFEND_BLOOD_SISTER` | enemies_q1 | model:EnemyModel | systemowy | – | – | 152 |  |
| 530 | `Q1_BOSS_NAME` | enemies_q1 | model:EnemyModel | systemowy | – | – | 7 |  |
| 531 | `ENEMY_ACTIVATION_BERSERKER_BASIC` | enemies_q1 | walka_teren | systemowy | – | – | 120 | 1 |
| 532 | `ENEMY_ACTIVATION_FLAYED_BASIC` | enemies_q1 | walka_teren | systemowy | – | – | 245 | 2 |
| 533 | `ENEMY_ACTIVATION_BERSERKER_TACTIC_RAMPAGE` | enemies_q1 | walka_teren | systemowy | – | – | 53 | 2 |
| 534 | `BERSERKER_TACTIC_ENRAGE_ACTIVATION` | enemies_q1 | walka_teren | systemowy | – | – | 204 | 1 |
| 535 | `BERSERKER_TACTIC_THROW_ACTIVATION` | enemies_q1 | walka_teren | systemowy | – | – | 172 | 2 |
| 536 | `BERSERKER_TACTIC_INDOMITABLE_NO_DEATH` | enemies_q1 | walka_teren | systemowy | – | – | 203 | 1 |
| 537 | `ENEMY_DEFEAT_BERSERKER_FLAYED` | enemies_q1 | walka_teren | systemowy | – | – | 154 | 1 |
| 538 | `ENEMY_DEFEAT_BERSERKER_FLAYED_FAIL` | enemies_q1 | walka_teren | systemowy | – | – | 69 | 1 |
| 539 | `BERSERKER_TACTIC_RAMPAGE_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 79 | 2 |
| 540 | `BERSERKER_TACTIC_ENRAGE_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 147 | 1 |
| 541 | `BERSERKER_TACTIC_THROW_HINT` | enemies_q1 | komunikat_questu | narrator | – | – | 70 | 1 |
| 542 | `BERSERKER_TACTIC_INDOMITABLE_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 115 | 1 |
| 543 | `BLOOD_SISTER_TACTIC_DEATH_CALL` | enemies_q1 | walka_teren | systemowy | – | – | 261 | 1 |
| 544 | `ENEMY_ACTIVATION_BLOOD_SISTER_BASIC_1` | enemies_q1 | walka_teren | systemowy | – | – | 90 |  |
| 545 | `ENEMY_ACTIVATION_BLOOD_SISTER_UNDEAD` | enemies_q1 | walka_teren | systemowy | – | – | 172 |  |
| 546 | `ENEMY_ACTIVATION_MISTRESS_OF_BONES` | enemies_q1 | walka_teren | systemowy | – | – | 137 |  |
| 547 | `ENEMY_ACTIVATION_BLOOD_SISTER_BLOOD_CALL` | enemies_q1 | walka_teren | systemowy | – | – | 100 | 1 |
| 548 | `ENEMY_ACTIVATION_BLOOD_SISTER_LIFE_LOCK` | enemies_q1 | walka_teren | systemowy | – | – | 136 | 1 |
| 549 | `BLOOD_SISTER_TACTIC_RED_MIST_ACTIVATION` | enemies_q1 | walka_teren | systemowy | – | – | 206 | 1 |
| 550 | `ENEMY_DEFEAT_BOSS_EURTH_ESCAPE` | enemies_q1 | walka_teren | systemowy | – | – | 357 |  |
| 551 | `ENEMY_DEFEAT_BOSS_EURTH_FINAL` | enemies_q1 | walka_teren | systemowy | – | – | 227 |  |
| 552 | `BLOOD_SISTER_TACTIC_LIFE_LOCK_REACTION` | enemies_q1 | walka_teren | systemowy | – | – | 82 | 2 |
| 553 | `BLOOD_SISTER_TACTIC_BLOOD_CALL_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 87 | 2 |
| 554 | `BLOOD_SISTER_TACTIC_LIFE_LOCK_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 128 | 1 |
| 555 | `BLOOD_SISTER_TACTIC_RED_MIST_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 176 | 1 |
| 556 | `BLOOD_SISTER_TACTIC_DEATH_CALL_HINT` | enemies_q1 | walka_teren | systemowy | – | – | 181 | 1 |
| 557 | `FAE_TACTIC_BE_BACK_SPAWN` | system | system_nagroda | systemowy | – | – | 255 | 2 |
| 558 | `BREW_BASKET_GIVE` | system | ui_system | systemowy | – | – | 27 |  |
| 559 | `TACTIC_PHASE` | system | ui_system | systemowy | – | – | 11 |  |
| 560 | `TACTIC_PHASE_DESCRIPTION_DARK_PRAYER` | system | system_nagroda | systemowy | – | – | 148 | 1 |
| 561 | `APPLY_AFFLICTION_DAMAGE` | system | system_nagroda | systemowy | – | – | 64 | 1 |
| 562 | `UI_CONTINUE` | system | opcja_wyboru | systemowy | – | – | 9 |  |
| 563 | `UI_CONTINUE_TO_HERO_PHASE` | system | system_nagroda | systemowy | – | – | 21 |  |
| 564 | `UI_INTERRUPT` | system | opcja_wyboru | systemowy | – | – | 10 |  |
| 565 | `TACTIC_PHASE_DESCRIPTION` | system | system_nagroda | systemowy | – | – | 75 | 1 |
| 566 | `ENEMY_LOOT_DROP` | system | ui_system | systemowy | – | – | 40 |  |
| 567 | `ITEM_UNDYING_SKULL_BERSERKER_2` | system | ui_system | systemowy | – | – | 212 |  |
| 568 | `ITEM_UNDYING_SKULL_BANDIT_2` | system | ui_system | systemowy | – | – | 133 |  |
| 569 | `ITEM_UNDYING_SKULL_ZEALOT_2` | system | ui_system | systemowy | – | – | 215 |  |
| 570 | `ITEM_UNDYING_SKULL_GOLEM_2` | system | ui_system | systemowy | – | – | 91 |  |
| 571 | `ITEM_UNDYING_SKULL_WOLF_2` | system | ui_system | systemowy | – | – | 119 |  |
| 572 | `ITEM_UNDYING_SKULL_SHADE_2` | system | ui_system | systemowy | – | – | 131 |  |
| 573 | `ITEM_UNDYING_SKULL_FAE_2` | system | ui_system | systemowy | – | – | 121 |  |
| 574 | `ITEM_UNDYING_SKULL_WIGHT_2` | system | ui_system | systemowy | – | – | 114 |  |
| 575 | `ITEM_UNDYING_SKULL_CENTURION_2` | system | ui_system | systemowy | – | – | 132 |  |
| 576 | `ITEM_UNDYING_SKULL_BLOODWITCH_2` | system | ui_system | systemowy | – | – | 91 |  |
| 577 | `ITEM_UNDYING_SKULL_HARBINGER_2` | system | ui_system | systemowy | – | – | 137 |  |
| 578 | `ITEM_UNDYING_SKULL_DOOMCALLER_2` | system | ui_system | systemowy | – | – | 146 |  |
| 579 | `ITEM_UNDYING_SKULL_DRAGON_2` | system | ui_system | systemowy | – | – | 93 |  |
| 580 | `ITEM_UNDYING_SKULL_VIPER_2` | system | ui_system | systemowy | – | – | 160 |  |
| 581 | `ITEM_UNDYING_SKULL_MERCENARY_2` | system | ui_system | systemowy | – | – | 165 |  |
| 582 | `ITEM_UNDYING_SKULL_REANIMATE_2` | system | ui_system | systemowy | – | – | 133 |  |
| 583 | `ITEM_UNDYING_SKULL_SALAMANDER_2` | system | ui_system | systemowy | – | – | 116 |  |
| 584 | `ITEM_UNDYING_SKULL_VAMPIRE_2` | system | ui_system | systemowy | – | – | 148 |  |
| 585 | `ITEM_UNDYING_SKULL_BERSERKER_1` | system | ui_system | systemowy | – | – | 134 |  |
| 586 | `ITEM_UNDYING_SKULL_BANDIT_1` | system | ui_system | systemowy | – | – | 163 |  |
| 587 | `ITEM_UNDYING_SKULL_ZEALOT_1` | system | ui_system | systemowy | – | – | 122 |  |
| 588 | `ITEM_UNDYING_SKULL_GOLEM_1` | system | ui_system | systemowy | – | – | 141 |  |
| 589 | `ITEM_UNDYING_SKULL_WOLF_1` | system | ui_system | systemowy | – | – | 164 |  |
| 590 | `ITEM_UNDYING_SKULL_SHADE_1` | system | ui_system | systemowy | – | – | 88 |  |
| 591 | `ITEM_UNDYING_SKULL_FAE_1` | system | ui_system | systemowy | – | – | 115 |  |
| 592 | `ITEM_UNDYING_SKULL_WIGHT_1` | system | ui_system | systemowy | – | – | 135 |  |
| 593 | `ITEM_UNDYING_SKULL_CENTURION_1` | system | ui_system | systemowy | – | – | 141 |  |
| 594 | `ITEM_UNDYING_SKULL_BLOODWITCH_1` | system | ui_system | systemowy | – | – | 88 |  |
| 595 | `ITEM_UNDYING_SKULL_HARBINGER_1` | system | ui_system | systemowy | – | – | 76 |  |
| 596 | `ITEM_UNDYING_SKULL_DOOMCALLER_1` | system | ui_system | systemowy | – | – | 125 |  |
| 597 | `ITEM_UNDYING_SKULL_DRAGON_1` | system | ui_system | systemowy | – | – | 121 |  |
| 598 | `ITEM_UNDYING_SKULL_VIPER_1` | system | ui_system | systemowy | – | – | 152 |  |
| 599 | `ITEM_UNDYING_SKULL_MERCENARY_1` | system | ui_system | systemowy | – | – | 132 |  |
| 600 | `ITEM_UNDYING_SKULL_REANIMATE_1` | system | ui_system | systemowy | – | – | 135 |  |
| 601 | `ITEM_UNDYING_SKULL_SALAMANDER_1` | system | ui_system | systemowy | – | – | 75 |  |
| 602 | `ITEM_UNDYING_SKULL_VAMPIRE_1` | system | ui_system | systemowy | – | – | 120 |  |
| 603 | `ITEM_DEAD_MAN_COMPASS_SMALL` | system | ui_system | systemowy | – | – | 36 |  |
| 604 | `ITEM_DEAD_MAN_COMPASS_BIG` | system | ui_system | systemowy | – | – | 80 |  |
| 605 | `REMOVE_ENEMY` | system | komunikat_questu | narrator | – | – | 13 | 1 |
| 606 | `UI_ENEMYDEFENSIVE_REMINDER` | system | system_nagroda | systemowy | – | – | 28 | 1 |
| 607 | `UI_ENEMY_DEFEAT_INTERRUPTED` | system | system_nagroda | systemowy | – | – | 37 |  |
| 608 | `PERFORM_DIFFERENT_ACTION` | system | komunikat_questu | narrator | – | – | 32 |  |
| 609 | `SPECTER_TACTIC_RUNELOCK_INTERUPT` | system | walka_teren | systemowy | – | – | 193 | 2 |
| 610 | `UI_DEFEAT_HERO` | system | system_nagroda | systemowy | – | – | 28 | 1 |
| 611 | `UI_WOUND_HERO` | system | opcja_wyboru | systemowy | – | – | 14 |  |
| 612 | `REMEMBRANCE_HILT_REVIVE` | system | system_nagroda | systemowy | – | – | 168 | 1 |
| 613 | `HERO_DEFATED_FLIP` | system | system_nagroda | systemowy | – | – | 42 | 1 |
| 614 | `TRINKET_HORN_OF_COURAGE_ABILITY_1` | system | ui_system | systemowy | – | – | 31 |  |
| 615 | `TRINKET_HORN_OF_COURAGE_ABILITY_2` | system | ui_system | systemowy | – | – | 59 |  |
| 616 | `TRINKET_HORN_OF_COURAGE_ABILITY_3` | system | ui_system | systemowy | – | – | 42 |  |
| 617 | `TRINKET_HORN_OF_COURAGE_ABILITY_4` | system | ui_system | systemowy | – | – | 36 |  |
| 618 | `TRINKET_HORN_OF_COURAGE_ABILITY_5` | system | ui_system | systemowy | – | – | 23 |  |
| 619 | `TRINKET_HORN_OF_COURAGE_ABILITY_6` | system | ui_system | systemowy | – | – | 26 |  |
| 620 | `TRINKET_HORN_OF_COURAGE_ABILITY_7` | system | ui_system | systemowy | – | – | 17 |  |
| 621 | `TRINKET_HORN_OF_COURAGE_ABILITY_AND` | system | ui_system | systemowy | – | – | 1 |  |
| 622 | `TRINKET4_ID` | system | ui_system | systemowy | – | – | 10 |  |
| 623 | `TRINKET_HORN_OF_COURAGE_ABILITY_PLUR` | system | system_nagroda | systemowy | – | – | 30 | 4 |
| 624 | `TRINKET_HORN_OF_COURAGE_ABILITY_SING` | system | system_nagroda | systemowy | – | – | 18 | 2 |
| 625 | `INJURY_1` | system | ui_system | systemowy | – | – | 10 |  |
| 626 | `HERO_DEFEATED_MESSAGE` | system | system_nagroda | systemowy | – | – | 41 | 2 |
| 627 | `INJURY_2` | system | ui_system | systemowy | – | – | 12 |  |
| 628 | `INJURY_3` | system | ui_system | systemowy | – | – | 8 |  |
| 629 | `INJURY_4` | system | ui_system | systemowy | – | – | 10 |  |
| 630 | `INJURY_5` | system | ui_system | systemowy | – | – | 8 |  |
| 631 | `INJURY_6` | system | ui_system | systemowy | – | – | 10 |  |
| 632 | `INJURY_7` | system | ui_system | systemowy | – | – | 17 |  |
| 633 | `INJURY_8` | system | ui_system | systemowy | – | – | 13 |  |
| 634 | `INJURY_9` | system | ui_system | systemowy | – | – | 17 |  |
| 635 | `INJURY_10` | system | ui_system | systemowy | – | – | 12 |  |
| 636 | `NO_CHOSEN_TACTIC` | system | system_nagroda | systemowy | – | – | 77 |  |
| 637 | `GO_TO_DESTINATION` | system | system_nagroda | systemowy | – | – | 18 | 1 |
| 638 | `UI_NO` | system | opcja_wyboru | systemowy | – | – | 3 |  |
| 639 | `UI_YES` | system | opcja_wyboru | systemowy | – | – | 3 |  |
| 640 | `END_TRAVEL` | system | system_nagroda | systemowy | – | – | 44 |  |
| 641 | `CARD_HERO_SHEET` | system | ui_system | systemowy | – | – | 14 |  |
| 642 | `CARD_WEAPON` | system | ui_system | systemowy | – | – | 11 |  |
| 643 | `CARD_SKILL_1A` | system | ui_system | systemowy | – | – | 18 |  |
| 644 | `CARD_SKILL_1B` | system | ui_system | systemowy | – | – | 18 |  |
| 645 | `ENEMY_BANDIT_SCORCHED_EARTH_TIMER_END` | system | system_nagroda | systemowy | – | – | 48 |  |
| 646 | `ENEMY_BANDIT_SCORCHED_EARTH_TIMER_CONT` | system | system_nagroda | systemowy | – | – | 115 |  |
