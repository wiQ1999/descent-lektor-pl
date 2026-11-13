# E16: paczka testowa Q1–Q2 (t1)

Wydanie `t1` (D101) to baza `m3` z opcjami testu. Zakres to 13 grup `scope.TEST_GROUPS['t1']`: prolog i Q1, Welcome Home, Q2, opisy misji na mapie, miasto, wydarzenia miejskie, podróże aktu 1, wydarzenia 2A i 2B, wrogowie, sprzęt, komunikaty systemowe. Raport podaje klucze i liczby, bez tekstów gry. Liczby bazy są w [E16_DATA.md](E16_DATA.md), a audio w [E16_AUDIO.md](E16_AUDIO.md).

## Zakres

| | liczba |
|---|---:|
| kwestie do syntezy w zakresie | 2347 |
| okna narratora z wypowiedzią postaci | 133 |
| wersje bohatera z luki (`KLUCZ#bohater`) | 108 (z 28 kwestii `hero_variant` `ARG:N`) |
| nowe głosy `nv_*` (projekt OmniVoice, [CASTING.md](../docs/CASTING.md)) | 20, w 48 kwestiach |
| kwestie zdolności broni i talizmanów (przełącznik `zdolnosci`) | 847 |
| fragmenty audio zakresu | 3274: 2563 nowe, 711 przejęte z `m3` |

Narrator czyta teksty i wartości luk w jednym tempie 1,4 (`SPEED_MAX`). Narracja scen fabularnych zostaje w tempie naturalnym. Poza zakresem testu baza i audio są takie jak w `m3`.

## Generowanie i ocena

Nowe nagrania powstały tylko w OmniVoice (GTX 1650 Ti, fp32): 3478 podejść, 12,7 h GPU. Z `m3` paczka przejęła 7477 fragmentów bez generowania. Każde nowe podejście zostało sprawdzone Whisperem.

| krok | fragmenty do ponownego podejścia |
|---|---:|
| `e14_run.sh`, runda 1 | 191 |
| runda 2 | 64 |
| runda 3 | 42 |
| `extra_retakes.py`, runda 4 (nowe z zakresu) | 28 |
| runda 5 | 28 |
| runda 6 | 24 |
| po rundzie 6 | 21 |

Po siedmiu podejściach 21 nowych fragmentów zakresu nie ma podejścia zaakceptowanego przez automat. Paczka gra najlepsze z nich. Przeważają krótkie nazwy i podpowiedzi wrogów albo zdolności, na których Whisper często myli nazwy własne. Fragment `47e1115bcc5d35da` to wartość luki z samym znakiem zerowej szerokości, więc cisza jest poprawna.

Do tego dochodzi 15 fragmentów przejętych z `m3`, które automat odrzucił już w `m3`. Zostają bez zmian, jak w poprzedniej sesji. Lista do odsłuchu (36 fragmentów: id, źródło, głos, znaki, uwagi, klucze):

| fragment | źródło | głos | znaki | uwagi | klucze |
|---|---|---|---:|---|---|
| `8b1a67ba171072ba` | m3 | adelynn | 24 | koncowka | `TANGERINE_WELCOME_HOME_POST_Q1_STORY_SCENE_REVISION_28A` |
| `2a2c8ac80c2ed5bb` | m3 | bruli | 40 | barwa | `TANGERINE_Q2_OUTRO_WIN_09V`, `TANGERINE_Q2_SOFT_LOSS_09V` |
| `048a4fd1586c25f1` | nowy | narrator | 35 | cer, zgubiony_fragment | `ENEMY_TACTIC_DOOMCALLER_DONE` |
| `175c899594d97a88` | nowy | narrator | 23 | koncowka | `WEAPON_ABILITY_B_BOW_5+_DESC`, `WEAPON_ABILITY_B_BOW_5_DESC` |
| `36894871b11556f9` | nowy | narrator | 12 | cer, koncowka | `ENEMY_TACTIC_DOOMCALLER_TELEPORTATION` |
| `3b1f0ba86cf6a046` | nowy | narrator | 10 | koncowka | `TRINKET7_ID`, `TRINKET7_ID_UPGRADED` |
| `47e1115bcc5d35da` | nowy | narrator | 1 | cisza | `SHADE_TACTIC_DEEP_BREATH_ACTIVATION`, `TACTIC_PHASE_DESCRIPTION` i 1 innych |
| `5193fe878b1fbdc2` | m3 | narrator | 42 | cer | `TRAVEL_CHANCE_RESP_INDEPENDENCE`, `TRAVEL_CHANCE_RESP_INDEPENDENCE#brynn` i 5 innych |
| `577d816bfce03d69` | nowy | narrator | 22 | koncowka | `BERSERKER_TACTIC_RAMPAGE_HINT` |
| `61441af620600f31` | nowy | narrator | 14 | koncowka | `WEAPON_ABILITY_COMPROMISE`, `WEAPON_ABILITY_COMPROMISE+` |
| `65398aaa2e62be61` | m3 | narrator | 28 | koncowka | `E_C1_1_CHOICE_VAERIX` |
| `7a4d5ff4f4494ced` | m3 | narrator | 61 | cer, koncowka | `TRAVEL_24` |
| `8709369d312f3e0d` | nowy | narrator | 3 | cer | `BANDIT_TACTIC_MULTI_SHOT_ACTIVATION`, `BANDIT_TACTIC_MULTI_SHOT_HINT` i 215 innych |
| `8d95b1325ad3860f` | nowy | narrator | 17 | koncowka | `TERRAIN_WELL_KEHLI_BREW` |
| `8e9306bca84d8d42` | nowy | narrator | 31 | koncowka | `ZEALOT_TACTIC_BLOODBOND_HINT` |
| `9071de045fa0f635` | m3 | narrator | 34 | koncowka | `Q1_THE_NIGHT_PASSES` |
| `9281fa63aa564342` | m3 | narrator | 126 | cer | `Q1_TEACH_INTERACT` |
| `acecf50b8a75dc5f` | m3 | narrator | 137 | cer, koncowka, zgubiony_fragment | `Q1_VAERIX_DRAMATIC_CHOICE_2` |
| `c0640577b0e6f365` | nowy | narrator | 29 | koncowka | `ENEMY_ACTIVATION_DRAGON_DIVE` |
| `c4c2627d90d6c182` | nowy | narrator | 15 | koncowka | `TRAVEL_SYRUS_RESP_AMBITION` |
| `cda1537b0a57eb4b` | nowy | narrator | 73 | koncowka | `ENEMY_TACTIC_DOOMCALLER_TELEPORTATION` |
| `d052cd69e6bb9fd1` | m3 | narrator | 112 | cer | `Q1_TEACH_INTERACT` |
| `d5e19bc9102720d2` | m3 | narrator | 123 | cer | `Q1_TEACH_GARGOYLES` |
| `dc14a239d9f8d120` | nowy | narrator | 34 | cer | `ZEALOT_TACTIC_BLOODBOND_HINT` |
| `dc23638bbc9056aa` | nowy | narrator | 25 | koncowka | `FAE_TACTIC_BUBBLE_TROUBLE_ACTIVATION` |
| `e0e37a9c911d8a59` | nowy | narrator | 18 | koncowka | `BANDIT_TACTIC_MULTI_SHOT_ACTIVATION`, `BANDIT_TACTIC_MULTI_SHOT_HINT` i 215 innych |
| `e3e0e17d96eb5d6e` | m3 | narrator | 101 | koncowka | `STORY_QUEST_14_DESC` |
| `e4d5d88ad6b03b62` | m3 | narrator | 86 | cer | `Q1_TEACH_UNDERLAYS` |
| `ebccb95ace0b3e14` | nowy | narrator | 15 | koncowka | `WIGHT_TACTIC_SUDDEN_RAGE_ACTIVATION` |
| `f699662b59c4f62b` | m3 | narrator | 93 | koncowka | `STORY_QUEST_5_DESC` |
| `fbd3533b6c397a20` | nowy | narrator | 7 | cer | `WEAPON_WAND` |
| `4d5ab9e8a23ab49b` | nowy | nekrul | 17 | tempo | `Q1_BOSS_SPAWN` |
| `6c5c7f50e5aaf04f` | m3 | nekrul | 74 | tempo | `TANGERINE_Q1_OUTRO_LOSE_1_1` |
| `318e61d4fb484dfa` | nowy | nv_fae | 26 | koncowka | `FAE_TACTIC_BUBBLE_TROUBLE_HINT` |
| `94469b91f9d839b2` | nowy | nv_fae | 24 | koncowka | `FAE_TACTIC_BUBBLE_TROUBLE_ACTIVATION` |
| `c51242dcdc3fb361` | m3 | vaerix | 50 | cer | `TANGERINE_WELCOME_HOME_POST_Q1_STORY_SCENE_REVISION_09` |

## Testy

- `pytest`: 302 przeszło, 2 pominięte.
- Plugin 0.4.2 (`dotnet build src/plugin/Loader -c Release`): 0 ostrzeżeń.
- Pokrycie (`release_coverage.py --release t1`): 2347 z 2347 kwestii zakresu z pełnym audio.
- Replay dzienników partii z 2026-11-11 (`--speed 0 --no-audio`), `m3` wobec `t1`:

| dziennik | wydanie | okna | pełne | częściowe | brak audio | start p50 / p95 (s) |
|---|---|---:|---:|---:|---:|---|
| Windows, 14:39 | m3 | 82 | 78 | 3 | 0 | 0,54 / 1,09 |
| Windows, 14:39 | t1 | 82 | 81 | 0 | 0 | 0,47 / 0,96 |
| Mac, 17:35 | m3 | 371 | 349 | 12 | 7 | 1,74 / 3,83 |
| Mac, 17:35 | t1 | 371 | 361 | 1 | 6 | 1,39 / 3,25 |

W `t1` braki w dzienniku z Maca to wyłącznie zapowiedzi misji Q6 (`Q_FOF_HAUNTING1_PREVIEW`, `Q_FOF_TOWNSFOLK1_PREVIEW`, `Q_FOF_TOWNSFOLK2_PREVIEW`, `Q_FOF_KATHRYN_PREVIEW`). Q6 leży poza zakresem testu. Okno częściowe także pochodzi spoza zakresu. Replay Pythonem i ustawieniami z gotowej paczki daje te same liczby.

## Paczka

`analysis/work/dist/Descent-Lektor-PL-win.zip` (1,82 GB, folder `analysis/work/dist/win/Descent-Lektor-PL`). Zawiera plugin 0.4.2, bazę `dane/t1.sqlite`, 10338 fragmentów FLAC i przełącznik `zdolnosci = true` w `ustawienia.toml`. W `wersja.txt` zakres jest opisany jako „test Q1–Q2 (E16, D101)”. Paczki nie wydano na GitHub.

Odinstalowanie paczki z wydania 0.3.0 i instalacja testowej idą jak zwykle według `INSTRUKCJA.md`. Okno ataku czyta nazwę i opis zdolności z kafelków po potwierdzeniu trafień. Na partię zostaje sprawdzenie w grze:
- podział na głosy;
- wersje bohatera;
- jedno tempo narratora;
- okno ataku.
