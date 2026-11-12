# Partia ze znajomymi (E14, wydanie v0.3.0): przyczyny problemów

Analiza z 2026-11-11. Źródła:
- 5 zrzutów od użytkownika (nazwy plików z opisem problemu nie dotarły, mamy tylko numery 1–5);
- dzienniki paczki Windows z krótkiej sesji 14:40–14:45: `hook-20261111-143955.jsonl`, `companion-20261111-144005.jsonl`, kopie w `analysis/work/out/session_20261111/`;
- baza `m3.sqlite`, eksport tekstów `pl_terms.json`, grafy z kopii gry, dekompilacja.

- dzienniki partii z Maca (dostarczone 2026-11-12), kopie w `analysis/work/out/session_20261111/mac/`: krótki start Q1 14:59 (8 okien) i partia 17:35–21:09 (`hook-20261111-173501.jsonl`, `companion-20261111-173502.jsonl`).

Zdjęcia 2–4 pochodzą z partii na Macu. Jej wyniki opisuje sekcja „Partia na Macu”.

## Partia na Macu

Mapa aktu 1, wydarzenia i podróże, potem scenariusz Q6 (ok. 2 h 40 min) i powrót na mapę. Plugin i companion działały całą sesję bez błędów, wyjście z gry bez crasha.

| Miara | Wynik |
|---|---|
| Okna z dziennika pluginu | 420 (205 zwykłych, 166 fabularnych, 49 aktywacji) i 19 opisów misji; wszystkie zamknięte, żadne nie przeszło obok companiona |
| Pozycje companiona | 474: 459 zagrane, 15 bez dźwięku |
| Pokrycie | 97,3% okien z nagraniem, 98,4% okien z tekstem do czytania |
| Okna przerwane przez gracza przed końcem nagrania | 120, w tym 24 przed jedną czwartą |
| Opóźnienie startu | mediana 0,28 s, maks. 0,31 s (wyjście audio Maca 0,45 s) |

Braki i błędy w partii:

| Klucz | Razy | Co słychać | Przyczyna |
|---|---|---|---|
| `Q_FOF_HAUNTING1_PREVIEW`, `Q_FOF_TOWNSFOLK1_PREVIEW`, `Q_FOF_TOWNSFOLK2_PREVIEW` | 6 (po 2) | cisza | podglądy obiektów poza bazą (zrzut 2) |
| `ARGUMENT_1` (`TERRAIN_WELL_COIN_LOST_4`) | 1 | cisza | luka `ListOfKeys` (zrzut 3) |
| `UI_ENEMYDEFENSIVE_REMINDER` | 6 | sam nagłówek | brak `ENEMY_DEFEND_*` w bazie (zrzut 5); w partii zdolności bandyty, wilka i siostry krwi |
| `DEFAULT_SPAWN_ENEMY_MULTI` z `ENEMY_BANDIT_CRAZED_1_SING` | 1 | stara nazwa wroga | tabela `dle04EnemyLocalization` (zrzut 4) |
| `DEFAULT_GET_TREASURE_MULTI`, `DEFAULT_GET_TREASURE_SINGLE` z „Usuń: …” po bandycie | 2 | „Usuń: Bandyta” zamiast pełnej nazwy | Ten sam błąd nazwy: companion dopasowuje słowa łupu do nagranych nazw, pierwszego słowa nowej nazwy nie zna, więc je pomija, a resztę czyta nagraniem `ENEMY_BANDIT_1_SING` (sprawdzone na bazie paczki). |
| `TANGERINE_EVENT_5B_THE_PRICE_OF_KNOWLEDGE_31` (2), `TANGERINE_Q6_TRAVEL_EVENT_15C` (1) | 3 | cisza | zamierzona: wielokropek i wskazówka „X WYBIERA…” (D85); w dzienniku jako `brak_audio` |
| okno ataku z aktywacją zdolności | nie wiadomo | cisza | plugin nie podpina okna (zrzut 1), więc dziennik go nie liczy |

Sprawdzone bez uwag:
- tekst każdego okna bez luk zgadza się z bazą `m3` (0 różnic);
- wartości luk z gry zgadzają się z tekstami bazy poza nazwą bandyty;
- głosy w oknach fabularnych pasują do mówiącej postaci, kwestie bohatera zmiennego grały w głosie Syrusa (`#syrus`);
- okna otwarte w trakcie odpowiedzi bohatera po wyborze: w partii żadne nie przepadło (wszystkie 459 okien z nagraniem zagrało), dwie odpowiedzi ucichły, bo następna kwestia je powtarzała (D72);
- `TERRAIN_BARRICADE_PREVIEW` companion znalazł po tekście (ten sam tekst co `TERRAIN_BARRICADE`), zagrał w całości.

## Zrzuty

| Zrzut | Okno (klucz) | Co zrobił lektor | Przyczyna |
|---|---|---|---|
| 1 | wynik ataku: obrażenia i aktywacja zdolności przedmiotu (`UIHeroAttackDialog`, `UIAbilityTrigger`) | nic, plugin nie wysłał zdarzenia | Plugin nie podpina okna ataku. E1 zaliczył wynik ataku do interfejsu (`E1_HOOK.md`). |
| 2 | `Q_FOF_HAUNTING1_PREVIEW` | cisza (klucza nie ma w bazie) | Podgląd obiektu na planszy: pole `GameInteractable.PreviewKey`, wyświetlane przez `DisplayQuickMessage`. `scope` zbiera tylko klucze z węzłów grafów, więc podglądy z komponentów sceny nie trafiają do bazy. |
| 3 | `ARGUMENT_1` z wartością `TERRAIN_WELL_COIN_LOST_4` | cisza (wartości luki nie ma w bazie) | Luka typu `ListOfKeys`: gra losuje klucz z listy w zmiennej blackboardu („Keys for Coin Toss”). `game.message_args` nie czyta nazwy listy z `Data.Keys`, a `scope.slot_keys` pomija ten typ. |
| 4 | `DEFAULT_SPAWN_ENEMY_MULTI` z wartością `ENEMY_BANDIT_CRAZED_1_SING` | czyta inną nazwę wroga niż na kartach | Klucz jest w dwóch tabelach CSV: `EnemyLocalization` i nowszej `dle04EnemyLocalization`. Gra pokazuje nazwę z nowszej, a `game.terms` zostawia pierwszą znalezioną. Nagranie powstało ze starej nazwy. |
| 5 | `UI_ENEMYDEFENSIVE_REMINDER` | częściowe: sam nagłówek, 1,8 s | Luka `VariableString` `_currDefenseKey` nie ma znanych wartości. Hook podaje klucz zdolności (`ENEMY_DEFEND_*`), ale żadnego z 62 takich kluczy nie ma w bazie. Okno ma też zły przełącznik: `nagrody` zamiast `walka_teren`. |

## Brakujące fragmenty

W sesji testowej companion przyjął 92 okna. Pięć z nich nie zagrało albo zagrało tylko część:

| Okno | Wynik w dzienniku | Przyczyna |
|---|---|---|
| `TERRAIN_WELL_BRYNN_CHALLENGE_TEST`, `TERRAIN_WELL_BRYNN_CHALLENGE_PASS` | `pełne`, ale bez `play` | Oba okna otworzyły się w trakcie odpowiedzi bohatera po wyborze (3,5 s) i czekały na jej koniec (D48). Gracz zamknął je wcześniej, a companion wyrzucił czekające okno bez wpisu w dzienniku. |
| `TANGERINE_Q6_TRAVEL_EVENT_15C` | `brak_audio` | Kwestia to sam wielokropek. Cisza jest poprawna, ale wynik w dzienniku wygląda jak błąd. |
| `UI_ENEMYDEFENSIVE_REMINDER` | `częściowe` | jak zrzut 5 |
| `Q_FOF_OBJECTIVE_1` | `w_oknie` | poprawnie: cel był już odczytany w oknie (D64) |

W sesji testowej okna czekające na odpowiedź bohatera przepadły przy szybkim klikaniu. W partii na Macu ten przypadek nie wystąpił, a brakujące fragmenty to podglądy, lista kluczy i opisy zdolności wrogów (sekcja „Partia na Macu”).

Inne źródła ciszy w akcie 1:
- podglądy obiektów (zrzut 2): 232 klucze `*_PREVIEW` bez nagrania w całej grze, ok. 26 tys. znaków, w tym 7 w Q6. Część może być nieużywana; pewna lista wyjdzie ze skanu komponentów;
- listy kluczy (zrzut 3): 3 kwestie (`ARGUMENT_1`, `TERRAIN_WELL_GALADEN_TEST_FAIL`, `SUCKER_PUNCH`), m.in. 6 wariantów `TERRAIN_WELL_COIN_LOST_*` i 6 `TERRAIN_WELL_GALADEN_TEST_FLAVOR_*`;
- zdolności obronne wrogów (zrzut 5): 62 klucze `ENEMY_DEFEND_*`, ok. 13 tys. znaków;
- 43 kwestie ElevenLabs bez głosu (Q10, Q11, 9A, 10A, D96), poza Q6;
- 80 kwestii bez tekstu do czytania (63 to sam wielokropek, 17 to wskazówka „X WYBIERA…”, pomijana według D85). Cisza jest zamierzona.

## Pominięte i dlaczego

| Co lektor pomija | Ile | Dlaczego | Miejsce w kodzie |
|---|---|---|---|
| Podglądy obiektów na planszy (`*_PREVIEW` z `GameInteractable.PreviewKey`) | do 232 kluczy w grze (ok. 26 tys. znaków), 7 w Q6 | Klucz siedzi w komponencie sceny, a nie w węźle grafu. Zakres zbiera tylko węzły grafów. | `scope.collect` |
| Wartości losowane z listy kluczy (`ListOfKeys`) | 3 kwestie z luką, m.in. 12 wariantów przy studni | Odczyt argumentów nie zna tego typu i nie zapisuje nazwy listy. | `game.message_args`, `scope.slot_keys` |
| Opis zdolności obronnej wroga (`ENEMY_DEFEND_*`) | 62 klucze (ok. 13 tys. znaków) | Luka `_currDefenseKey` dostaje wartość w kodzie gry, a nie w grafie, więc baza nie zna jej wartości. | `scope.collect` (wartości luk) |
| Aktywacja zdolności przedmiotu w oknie ataku | wszystkie przedmioty ze zdolnością | Plugin nie podpina okna ataku (E1 zaliczył je do interfejsu). | plugin `Core` |
| Okno otwarte w trakcie odpowiedzi bohatera po wyborze i zamknięte przed jej końcem | w sesji testowej 2 z 92 okien, w partii 0 | Okno czeka na koniec odpowiedzi (D48), a po zamknięciu wypada z kolejki bez wpisu w dzienniku. | `director._window`, `director._close` |
| Kwestie ElevenLabs bez głosu | 43 w akcie 1 | Wyczerpany limit klucza API (D96). | `eleven` |
| Kwestie bez tekstu do czytania | 80 (63 wielokropki, 17 wskazówek „X WYBIERA…”) | Zamierzone: wielokropek nie ma treści, wskazówki pomijamy według D85. | `build` |

Czytane źle:

| Co | Ile | Dlaczego | Miejsce w kodzie |
|---|---|---|---|
| Nazwa wroga `ENEMY_BANDIT_CRAZED_1_SING` | 1 klucz, wartość w 414 lukach `EntityName` i w listach łupu („Usuń: …”) | Nowsza tabela `dle04EnemyLocalization` nadpisuje w grze `EnemyLocalization`, a `game.terms` bierze pierwszą. W grze takich kluczy jest 23 (głównie słownik), w bazie m3 tylko ten. | `game.terms`, słownik łupu companiona |
| Przełącznik okien `UI_ENEMYDEFENSIVE_REMINDER` i `TACTIC_PHASE_DESCRIPTION` | 2 kwestie | Kategoria zastępcza `system_nagroda` daje przełącznik `nagrody`. | `game.fallback_category` |

## Wnioski do poprawki

Bez zmiany zakresu (diagnostyka):
1. `director`: wpis `porzucone` w dzienniku, gdy okno czekające na odpowiedź bohatera zamknie się przed startem.
2. `director`: wynik `pusta` zamiast `brak_audio` dla kwestii bez tekstu do czytania.

Dane (nowe kwestie, wymagają QA i generowania):
- `game.terms`: tekst z tabeli `dle04*` nadpisuje tekst z tabeli bazowej, jak w grze. Nowe nagranie dla `ENEMY_BANDIT_CRAZED_1_SING` (1 fragment).
3. `game.message_args` i `scope.slot_keys`: typ `ListOfKeys`. Odwołanie to nazwa listy z `Data.Keys`, a wartości to domyślna zawartość listy w blackboardzie grafu.
4. `scope`: skan komponentów `GameInteractable` w bundlach scen (`PreviewKey`, gdy nie ma `DTControllerPreview` ani `DefaultPreview`). Kategoria `komunikat_questu`, głos narratora.
5. `scope`: klucze `ENEMY_DEFEND_*` z modeli wrogów jako wartości luki `_currDefenseKey`. Kategoria okna `walka_teren` (to samo `TACTIC_PHASE_DESCRIPTION`, które dziś też ma przełącznik `nagrody`).
6. Przebudowa `m3`, generowanie nowych fragmentów w OmniVoice: szacunek ok. 3 h GPU dla całej gry (66 s na 1000 znaków z fazy B), mniej dla samego aktu 1.

Zachowanie (do decyzji w QA):
7. Okno otwarte w trakcie odpowiedzi bohatera (D48): dziś czeka i przepada po zamknięciu. Do wyboru: wyciszyć odpowiedź, gdy okno ma własny tekst, albo zostawić czekanie.
   Przykład z sesji testowej: przy studni Brynn wybiera wyzwanie, jej odpowiedź trwa 3,5 s. W tym czasie otwierają się okno testu woli i okno wyniku testu. Gracz zamyka oba przed końcem odpowiedzi, więc żadne nie zostaje przeczytane.
8. Okno ataku (zrzut 1): lektor czyta tylko aktywację zdolności, nazwę i opis z kluczy przedmiotu, bez liczb (D97). Nowe źródło w pluginie.

Kolejność i zakres dalszych prac (generowanie od początku albo od konkretnej misji) użytkownik ustali później (D97).

Uwaga do narzędzia: `hook_coverage.py` zawsze zapisuje szczegóły do `analysis/work/out/e1_coverage.json` i nadpisuje wynik E1. Plik E1 odtworzony z pięciu dzienników z 2026-10-31 (343 okna), szczegóły partii leżą w `session_20261111/mac/coverage_details.json`. Warto dodać opcję `--out`.
