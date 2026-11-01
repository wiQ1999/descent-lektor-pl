# E2: baza kwestii M1

Wygenerowano przez `python -I -m lektor report` z `analysis/work/lektor/m1.sqlite` (zbudowana 2026-11-01T16:48:12, pakiet 0.1.0, model `omnivoice-08be0b4-fp16-s32-cfg2.0`, manifest gry `fddf8aedeb14`). Raport zawiera tylko liczby i klucze techniczne.

## Kwestie

Kluczy: **649**, z tego do syntezy **635** (pozostałe to napisy przerywników z dubbingiem, D14).
Wrogowie w zakresie: `ENEMY_BERSERKER_1`, `ENEMY_FAE_1`, `ENEMY_INTRO_BOSS`, `ENEMY_WARY_BANDIT_1`, `ENEMY_WOLF_1`, `ENEMY_ZEALOT_1`. Grafy Q1: 93. Klucze przerywnika: 14.

### Grupa zakresu

| grupa zakresu | klucze | do syntezy | znaki |
|---|---|---|---|
| scene_q1 | 365 | 365 | 49526 |
| enemies | 106 | 106 | 14740 |
| story_q1 | 89 | 89 | 6660 |
| welcome_home | 49 | 49 | 4406 |
| system | 26 | 26 | 1549 |
| cutscene_01 | 14 | 0 | 0 |

### Kategoria

| kategoria | klucze | do syntezy | znaki |
|---|---|---|---|
| komunikat_questu | 293 | 293 | 46902 |
| walka_teren | 115 | 115 | 15822 |
| dialog | 109 | 109 | 8431 |
| opcja_wyboru | 69 | 69 | 1646 |
| system_nagroda | 22 | 22 | 1517 |
| narracja_fabularna | 18 | 18 | 2190 |
| cel_misji | 8 | 8 | 237 |
| zdarzenie | 1 | 1 | 136 |
| napisy_cutscenek | 14 | 0 | 0 |

### Głos

| głos | klucze | do syntezy | znaki |
|---|---|---|---|
| narrator | 540 | 526 | 68450 |
| brynn | 27 | 27 | 2176 |
| syrus | 26 | 26 | 2257 |
| galaden | 20 | 20 | 1102 |
| vaerix | 16 | 16 | 961 |
| adelynn | 12 | 12 | 1185 |
| ronan | 4 | 4 | 354 |
| kehli | 2 | 2 | 209 |
| chance | 1 | 1 | 113 |
| nekrul | 1 | 1 | 74 |

### Przełącznik companiona

| przełącznik companiona | klucze | do syntezy | znaki |
|---|---|---|---|
| komunikaty_questu | 293 | 293 | 46902 |
| dialogi | 109 | 109 | 8431 |
| aktywacje | 93 | 93 | 12989 |
| okna_wyboru | 69 | 69 | 1646 |
| walka_teren | 24 | 24 | 3294 |
| nagrody | 20 | 20 | 1056 |
| narracja | 19 | 19 | 2326 |
| cele | 8 | 8 | 237 |
| ui | 14 | 0 | 0 |

## Segmenty i fragmenty

| rodzaj segmentu | liczba |
|---|---|
| text | 893 |
| slot | 223 |
| quote | 6 |
| desc | 5 |

Unikalnych fragmentów do syntezy: **980** (text 863, value 106, quote 6, desc 5), znaków: 76494.

Najdłuższy fragment: 259 znaków.

## Luki {n} (D16)

| typ luki | luki | kwestie | wartości | w tym audio innej kwestii | unikalne fragmenty |
|---|---|---|---|---|---|
| EntityName | 111 | 81 | 1332 | 0 | 12 |
| VariableString | 62 | 41 | 313 | 0 | 21 |
| VariableInt | 28 | 28 | 588 | 0 | 63 |
| LocalizationKey | 9 | 8 | 27 | 10 | 17 |
| EnemyNameWithArticle | 6 | 4 | 72 | 0 | 12 |
| ? | 4 | 4 | 0 | 0 | 0 |
| ListOfKeys | 2 | 2 | 0 | 0 | 0 |
| RawText | 1 | 1 | 0 | 0 | 0 |

Wartość „audio innej kwestii” to klucz z bazy (np. cel misji), którego nagranie companion odtwarza w luce. Liczby: 0–20. Wartości luk mają jedno tempo 1.2.

Kwestie z luką bez znanych wartości (companion użyje syntezy na żywo albo pominie lukę): 13.

- `APPLY_AFFLICTION_DAMAGE`: luka bez znanych wartości (None): fallback
- `ARGUMENT_1`: luka bez znanych wartości (ListOfKeys): fallback
- `DEFAULT_GET_TREASURE_SINGLE`: luka bez znanych wartości (RawText): fallback
- `GO_TO_DESTINATION`: luka bez znanych wartości (VariableString): fallback
- `Q1_OBJECTIVE_5`: luka bez znanych wartości (None): fallback
- `Q1_OBJECTIVE_6`: luka bez znanych wartości (None): fallback
- `TACTIC_PHASE_DESCRIPTION`: luka bez znanych wartości (VariableString): fallback
- `TACTIC_PHASE_DESCRIPTION_DARK_PRAYER`: luka bez znanych wartości (VariableString): fallback
- `TERRAIN_WELL_GALADEN_TEST_FAIL`: luka bez znanych wartości (ListOfKeys): fallback
- `TRINKET_HORN_OF_COURAGE_ABILITY_PLUR`: luka bez znanych wartości (VariableString): fallback
- `TRINKET_HORN_OF_COURAGE_ABILITY_SING`: luka bez znanych wartości (VariableString): fallback
- `UI_ENEMYDEFENSIVE_REMINDER`: luka bez znanych wartości (VariableString): fallback
- `WOLF_TACTIC_READY_BITE_GO_ACTIVATION`: luka bez znanych wartości (VariableString): fallback

### Pokrycie wartości z sesji E1

Unikalne pary (kwestia, wartość) z dzienników E1 dla kwestii z bazy: 46 w inwentarzu, 11 poza nim.

- `DEFAULT_GET_TREASURE_SINGLE` (LocalizationKey): 3
- `DEFAULT_GET_TREASURE_SINGLE` (RawText): 6
- `TACTIC_PHASE_DESCRIPTION` (VariableString): 1
- `TACTIC_PHASE_DESCRIPTION_DARK_PRAYER` (VariableString): 1

Wartości spoza inwentarza companion obsłuży syntezą na żywo albo pominie (E4).

## Do przejrzenia

Kwestie z kilkoma mówcami w grafach (głos z pierwszego rozpoznanego): 0.

Dialogi bez przypisanego głosu (`inny`): 0.

Opcje wyboru z cytatem bez rozpoznanego bohatera (cytat głosem narratora): 0.

Głosy fragmentów bez referencji w bazie: brak.

## Szacunek generowania (E3)

| głos | fragmenty | znaki | audio min | podejścia | GPU h |
|---|---|---|---|---|---|
| adelynn | 12 | 1185 | 1.6 | 1 | 0.5 |
| brynn | 27 | 2049 | 2.7 | 3 | 2.7 |
| chance | 1 | 113 | 0.2 | 3 | 0.1 |
| galaden | 19 | 1094 | 1.5 | 3 | 1.7 |
| kehli | 2 | 209 | 0.3 | 3 | 0.2 |
| narrator | 871 | 68182 | 87.7 | 1 | 29.1 |
| nekrul | 1 | 74 | 0.1 | 1 | 0.0 |
| ronan | 4 | 354 | 0.5 | 1 | 0.1 |
| syrus | 28 | 2308 | 3.1 | 3 | 2.9 |
| vaerix | 15 | 926 | 1.2 | 3 | 1.4 |

Razem ok. **38.8 h** GPU bez retake, przy obecnym wywołaniu po jednym fragmencie (60 s na wywołanie + 10 s na sekundę audio, 10.1 znaku/s przy tempie 1,0). Jedno podejście według rodzaju fragmentu: text 30.2 h, value 2.3 h, quote 0.1 h, desc 0.1 h.
