# E1 · Test hooka na Windows (tylko logowanie)

Data: 2026-10-31. Plugin `LektorPL` 0.1.1, BepInEx 5.4.23.5 win_x86 (D11), gra 2.0.10, Unity 2022.3.62f2.
Dziennik i szczegóły (z tekstami) leżą poza repozytorium: `%LOCALAPPDATA%\LektorPL\logs\hook-*.jsonl`, `analysis/work/out/e1_coverage.json`.
Raport powstał przez `analysis/tools/hook_coverage.py` i dodatkowe porównania tekstu z ekranem.

## Wynik

| Kryterium (PLAN E1) | Wynik | Status |
|---|---|---|
| ≥ 98% okien z kluczem, tekstem i mówcą | 285/285 okien (100%) | spełnione |
| Zamknięcia okien | 285/285, w tym 12 cofnięć i 32 wybory z kluczem opcji | spełnione |
| Brak crashy i spadków płynności | crash przy starcie w 0.1.0 (naprawiony); crash przy wyjściu do pulpitu, tylko z loaderem (otwarte) | częściowo |
| Odinstalowanie przywraca folder gry | identyczny poza zapisami gry | spełnione |

Okna `MessageController` i `StoryMessageController` są pokryte w całości. Dwa rodzaje treści z zakresu M1 gra pokazuje jednak poza tymi oknami (sekcja „Luki”).

## Sesje

| Sesja | Plugin | Czas | Przebieg | Wynik |
|---|---|---|---|---|
| 3 próby | 0.1.0 | ok. 7 s | ekran ładowania assetów | crash w Wwise (niżej) |
| krótka | 0.1.1 | 4,6 min | początek Q1 | 58 okien, 0 błędów |
| główna | 0.1.1 | 10,4 min | nowa kampania: prolog i Q1 (7,4 min), mapa aktu z „Welcome Home” (2,5 min) | 285 okien, 0 błędów |

Dalej liczby z sesji głównej.

### Crash przy starcie (0.1.0)

Stos: `PersistentGameObject.InitializeWwise` → `AkSoundEngine.SetCurrentLanguage` → wyjątek natywny w `AkSoundEngine`.

Przyczyna: plugin przy podpięciu delegatów (scena `Start`, przed załadowaniem bundli) wołał `FFGLocalization.GetCurrentLanguage()`. Getter `I2.Loc.LocalizationManager.CurrentLanguage` wywołuje `InitializeIfNeeded()`, który bez źródeł językowych zostawia język `null` i zatrzaskuje `s_isInitialized`. Gra przekazywała potem `null` do Wwise.

Poprawka (0.1.1): plugin czyta pole `mCurrentLanguage` przez refleksję. Zasada na dalsze etapy: **plugin nie woła getterów gry z leniwą inicjalizacją**; czyta pola albo czeka, aż gra sama je zainicjalizuje.

Ostrzeżenie `[LocalizationManager] System language is not supported: Polish` w `Player.log` pochodzi z Asmodee SDK i nie ma związku z crashem.

## Pokrycie okien

| Miara | Wartość |
|---|---|
| Okna | 285: 108 fabularnych, 177 zwykłych |
| Typy | `MessageRequest` 246, `MultipleChoiceMessageRequest` 32, `ChallengeMessageRequest` 7; źródło zawsze `DialogueTree` |
| Zwykłe okna przez delegaty | 177/177; polling nie znalazł okna pominiętego przez delegaty |
| `.qlog` (3 pliki) | 83/85 kluczy; brakujące `UI_LOG_HEROATTACK` i `UI_LOG_ENEMYATTACK` to wpisy dziennika ataku, nie okna |
| Tekst pluginu = tekst na ekranie | zwykłe 128/128 porównywalnych, fabularne 108/108 |
| Opóźnienie pokazania tekstu okna fabularnego | mediana 16 ms, p95 19 ms, maks. 23 ms |
| Cofnięcia | 8 zwykłych, 4 fabularne |
| Wybory | 29 zwykłych, 3 fabularne; za każdym razem klucz wybranej opcji |
| Mówcy (okna fabularne) | 91 okien z jednym mówcą, 17 narracji bez mówcy; 8 postaci (6 bohaterów, 2 NPC) |

Uwagi do porównania tekstu:
- 45 zwykłych okien nie ma próbki z ekranu. Sniffer TMP skanuje co 1 s i nie powtarza tekstu, który już widział.
- 4 pozorne różnice to próbki sąsiedniego okna z tego samego skanu.
- Render bez losowania (`performRNG: false`) dał w tej sesji zawsze ten sam tekst co gra.

### Klucze

- **Unikalne klucze okien:** 223.
- **W zakresie M1:** 171, czyli 27% z 632 kluczy okien M1. Jedno przejście widzi jedną gałąź; reszta to inne wybory, warunki i warianty. Najwięcej brakuje w kategoriach `komunikat_questu` (186), `ui_system` (100) i `opcja_wyboru` (80).
- **Poza M1:** 52 klucze:
  - 48 ze sceny „Welcome Home”; jej zakres policzymy w E2 (D15);
  - 1 zdarzenie podróży na mapie;
  - 3 z Q1: dwie podpowiedzi taktyk wrogów i komunikat o kilku skarbach.

### Argumenty `{n}`

| Typ | Wystąpienia | Uwagi |
|---|---|---|
| `LocalizationKey` | 19 | klucz w `as_key` |
| `EntityName` | 17 | `<sprite=N>` + klucz wroga; boss ma alias w nawiasie (`… (Q1_BOSS_NAME)`); raz `as_key` zwrócił sam znacznik `<EntityName>` przy poprawnej wartości |
| `VariableString` | 15 | |
| `RawText` | 10 | gotowy tekst z listą kart z losowania łupu; nie ma klucza, potrzebuje syntezy na żywo albo składania z fragmentów |
| `VariableInt` | 9 | wartości 0–5 |

Wrogowie z losowania w Q1: bandyta, fanatyk, istota fae, berserker i boss (wiedźma krwi). `m1_scope.json` znał tylko berserkera i bossa, więc inwentarz wrogów z E1 (D16) uzupełnia zakres M1 o aktywacje i taktyki pozostałych.

`VARIABLE_HERO` nie wystąpił ani razu w Q1 i „Welcome Home”. Rozwiązanie mówcy przez `GetNameKey()` jest więc nieprzetestowane w grze. Do sprawdzenia w pierwszej misji, w której wystąpi.

## Luki: treść M1 poza oknami wiadomości

| Treść | Gdzie w grze | Klucze M1 | Jak obserwować |
|---|---|---|---|
| Aktualny cel misji | etykieta HUD `UIGame.LabelCurrentObjective`; okno pojawia się tylko przy części aktualizacji (`Q1_OBJECTIVE_5_UPDATE`, `_6_UPDATE`) | 8 (`cel_misji`); w sesji 10 zmian celu | polling `UIGame._lastObjectiveKey` i `_LastObjectiveArguments` |
| Aktywacja wroga | `UIEnemyActivationDialog.TextActivation`, ustawiane w `UIGame.ShowEnemyActivation` z `EnemyActivationRequest.Message` | 9 (`ENEMY_ACTIVATION_*`) + aktywacje wrogów z losowania | polling bieżącej aktywacji w `GameController` (klucz i argumenty `Message`) |

Pozostałe teksty widoczne tylko w UI to opcje wyboru jako przyciski (pokryte przez `choices`), wynik ataku, wybór broni i cnoty, karta i podsumowanie questu oraz opisy obrony wroga. Należą do interfejsu, a nie do narracji.

## Wydajność

- **Płynność:** ok. 120 klatek/s (7117–7202 klatek na minutę).
- **Najdłuższa klatka w rozgrywce:** 31–46 ms, z wyjątkiem minut z ładowaniem sceny (964 ms przy wejściu do Q1, 230 ms przy wejściu na mapę).
- **Koszt pluginu:**
  - 314–388 ms na minutę, czyli ok. 0,6% czasu;
  - najdłuższa pojedyncza klatka pracy: 8,2 ms;
  - szacunek: prawie cały koszt to sniffer TMP (`FindObjectsOfType<TMP_Text>` co 1 s, ok. 6 ms na skan). Bez sniffera zostaje kilka µs na klatkę;
  - sniffer jest narzędziem diagnostycznym E1; w E4 domyślnie wyłączony.

## Crash przy wyjściu do pulpitu (otwarte)

- **Częstość:** 2 z 2 wyjść z grą z loaderem.
- **Moment:** po zamknięciu Input System.
- **Stos:** `mono_jit_cleanup` → `mono_domain_free`.
- **Stan pluginu:** zdążył zapisać `stop` (`OnApplicationQuit`).
- **Zapisy gry:** kompletne.

Test bez moda (2026-11-01): wyjście z menu do pulpitu przebiegło bez crasha. W `Crashes` nie przybył nowy folder, a `Player.log` kończy się normalnym zamknięciem. Crash wywołuje więc loader (BepInEx 5 z Doorstopem) albo nasz plugin. Plugin nie ma własnych wątków ani timerów; przy wyjściu zostają tylko subskrypcje zdarzeń gry i `SceneManager.activeSceneChanged`.

Do rozdzielenia przyczyn trzeba sesji z BepInEx bez pluginu, a potem z pluginem, który przy wyjściu odpina subskrypcje.

## Odinstalowanie

`lektor-hook.ps1 -Uninstall` usuwa wyłącznie pliki z listy instalacji. Po obu sesjach lista plików folderu gry jest identyczna ze stanem sprzed instalacji. Jedyny wyjątek to nowe zapisy w `Legends of the Dark_Data\SavedGames\3`: 5 × `.sav`, 3 × `.qlog`, 1 × `.backup`.

## Wnioski dla kolejnych etapów

- **E2:**
  - wrogowie z losowania (bandyta, fanatyk, fae) i ich aktywacje dochodzą do zakresu M1;
  - scena „Welcome Home” ma co najmniej 48 kluczy okien;
  - argumenty `RawText` (łup) wymagają osobnej ścieżki.
- **E4:**
  - format zdarzeń JSONL i wykrywanie pokazania okna fabularnego (zmiana tekstu, maks. 23 ms) można przenieść bez zmian;
  - do dodania obserwacja celu misji (D31) i aktywacji wroga (D30);
  - `EntityName` mapujemy po wartości, gdy `as_key` zwraca znacznik.
- **Otwarte:**
  - crash przy wyjściu z loaderem (bez moda go nie ma);
  - `VARIABLE_HERO` bez testu w grze.
