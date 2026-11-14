# E16: test paczki t1 w grze, Q1 i Q2 (2026-11-13/14)

Sesja Windows 22:17–22:47 z paczką testową `t1` (plugin 0.4.2). Zrzuty l6–l10 i dzienniki leżą w `analysis/work/playtest/t1/` (poza Git). Zrzuty l1–l5 pochodzą z partii 2026-11-11 i opisuje je [E14_PARTY.md](E14_PARTY.md). Raport podaje klucze i liczby, bez tekstów gry.

## Zrzuty i przyczyny

| zrzut | okno (klucz) | co słychać | przyczyna |
|---|---|---|---|
| l6 | okno ataku, opis obrony wroga (`ENEMY_DEFEND_ZEALOT`) | cisza | Okno ataku pokazuje obronę wroga w polu `UIHeroAttackDialog.TextDefensive` (`SerializedEnemy.GetDefenseKey()`). Plugin czyta z tego okna tylko kafelki zdolności (`PoolAbilityTrigger`), więc nie wysyła zdarzenia. Audio jest gotowe: 62 klucze `ENEMY_DEFEND_*` mają fragmenty jako wartości luki `UI_ENEMYDEFENSIVE_REMINDER` (D98). |
| l7, l10 | `Q1_OBJECTIVE_5_UPDATE`, `Q1_OBJECTIVE_6_UPDATE` | treść celu z licznikiem, a zaraz potem sam licznik („jeden z czterech”) | Okno komunikatu czyta cały cel z licznikiem. 0,1–0,3 s później plugin zgłasza zmianę celu (`objective`, ten sam klucz celu), a companion czyta licznik drugi raz (D64). Tłumienie `w_oknie` działa tylko wtedy, gdy cel był wartością luki w oknie (`OBJECTIVE_UPDATED` z `Q1_OBJECTIVE_3`). Okna `*_UPDATE` mają tekst celu wpisany na stałe, więc companion go nie rozpoznaje. |
| (ten sam błąd) | `OBJECTIVE_UPDATED` z wartością `Q1_OBJECTIVE_5_0` | cel czytany dwa razy w całości | Wartość luki to wariant `Q1_OBJECTIVE_5_0`, a zdarzenie celu ma klucz `Q1_OBJECTIVE_5`. Klucze się różnią, więc tłumienie nie działa. |
| l8 | `Q1_ROUND_TABLE_LETTER` | cały list czyta narrator | List stoi w cudzysłowie „…”. `speakers.split` rozpoznaje mowę tylko po półpauzie, a cudzysłów traktuje celowo jak narrację, bo zwykle oznacza tytuł albo napis. Autorkę (Adelynn) wskazuje zdanie przed cytatem. |
| l9 | `Q1_BRYNN_SHOUT` | całość czyta narrator | Wypowiedź otwiera akapit bez półpauzy, a półpauza pojawia się dopiero przed „mówi zmartwiona Brynn”. Reguła bierze półpauzę w środku zdania narracji za wtrącenie. |

W dzienniku sesji nie ma żadnego zdarzenia `ability`. Nie da się z niego ustalić, czy w tej sesji pojawił się kafelek aktywowanej zdolności broni albo talizmanu (D100).

## Mowa w oknach narratora: przegląd

Przegląd objął 1968 okien narratora w zakresie `t1`, z czego 133 mają podział na głosy. Wśród pozostałych 51 ma półpauzę, cudzysłów albo wykrzyknik z imieniem. Po przejrzeniu każdego z nich mowę postaci zawierają:

| wzorzec | okna w zakresie t1 | reszta gry | przykłady (klucze) |
|---|---:|---:|---|
| mowa bez otwierającej półpauzy, potem „– mówi X” | 1 | 1 | `Q1_BRYNN_SHOUT` |
| list albo wypowiedź w cudzysłowie z pełnymi zdaniami | 2 | 33 | `Q1_ROUND_TABLE_LETTER`, `TRAVEL_GALADEN_RESP_DEDICATION` |
| opcja wyboru zaczynająca się półpauzą (mowa bohatera wydarzenia) | 2 | – | `TRAVEL_KEHLI_OP_INNOVATION`, `TRAVEL_KEHLI_OP_RELIABILITY` |
| nadpisanie `narrator` z mową bohatera broni | 1 | – | `WEAPON_ABILITY_C_CROSSBOW_4_EFFECT` |

Pozostałe trafienia są poprawne:
- półpauza jako wtrącenie w narracji: `Q1_LECTERN_INTERACT`, `TEST_TRAP_FAIL_0`;
- cudzysłów przy tytule, przycisku albo napisie: `TUTORIAL_FEATS`, `TRAVEL_56`;
- okna już podzielone przez wersje bohatera z luki: `Q1_CHOOSE_HERO_ON_WATCH`, kwestie `TANGERINE_*` z `VARIABLE_HERO2`.

Opcje wyboru (`opcja_wyboru`) są wyłączone z podziału w `build.split_voices`.

## Propozycje poprawek

1. Cel misji: companion pomija zdarzenie `objective`, gdy w ciągu `DUP_S` przeczytał okno, którego tekst zawiera tekst tego celu (bez licznika). Reguła obejmuje okna `*_UPDATE`, warianty `_0` i każdą przyszłą odmianę. Bez nowego audio.
2. Mowa bez półpauzy: akapit bez otwierającej półpauzy, w którym pierwsza półpauza stoi przed czasownikiem mówienia (mówi, woła, szepcze…) z imieniem albo luką, dzieli się na mowę i wtrącenie.
3. Cytaty: wypowiedź albo list w „…” z co najmniej jednym pełnym zdaniem dostaje głos autora wskazanego w narracji tuż przed cytatem. Bez autora zostaje narracją (napisy, tabliczki). Cytat może trwać przez kilka akapitów.
4. Opcje wyboru zaczynające się półpauzą w wydarzeniach postaci (`VirtueTravelEvent <bohater>`): czyta je ten bohater.
5. Okno ataku: plugin przy otwarciu okna wysyła klucz obrony wroga (`GetDefenseKey()`), a companion czyta gotowy fragment `ENEMY_DEFEND_*`. Bez nowego audio.

Punkty 2–4 zmieniają kilka okien w zakresie `t1` i wymagają generowania nowych fragmentów (OmniVoice, kilka minut). Punkty 1 i 5 zmieniają companion i plugin.

## Wykonanie (D102)

Wybrane w QA poprawki: 1, 2, 3 i 5. Punkt 4 (opcje wyboru) i głos `nv_*` dla cytatów bez autora zostają bez zmian.

- **Cel misji** (`director.plain`, `_read_in_window`, `_drop_read_goals`). Replay sesji: 13 z 14 zmian celu ma wynik `w_oknie`. Gra tylko pierwszy cel misji, który nie miał okna.
- **Mowa bez półpauzy i cytaty z autorem** (`speakers.ATTRIBUTION`, `speakers.speech_quote`, rodzaj kawałka `q`). Cytat w akapicie zaczętym półpauzą należy do wypowiedzi mówiącego, np. Kehli cytuje kogoś w `TRAVEL_KEHLI_CHOICE`. W zakresie `t1` zmieniły się dokładnie 2 okna: `Q1_BRYNN_SHOUT` (brynn) i `Q1_ROUND_TABLE_LETTER` (adelynn). W reszcie gry nowa reguła obejmie 26 okien z cytatem.
- **Obrona wroga w oknie ataku.** Plugin 0.4.3 ma nowe zdarzenie `open/close` `kind: defense` z kluczem `GetDefenseKey()`. Companion gra nagranie wartości luki `UI_ENEMYDEFENSIVE_REMINDER` (`Library.defense`) z przełącznikiem `zdolnosci`. Nowe zdarzenie trzeba jeszcze sprawdzić w grze.
- **Audio.** 8 nowych fragmentów OmniVoice (brynn 1, adelynn 5, narrator 2), wszystkie zaakceptowane przez automat, z 1 ponownym podejściem. Pokrycie zakresu: 2347 z 2347 kwestii.
- **Testy.** `pytest`: 308 przechodzi, 2 pominięte. Plugin buduje się bez ostrzeżeń.

## Druga sesja: Q1 i Q2 z paczką D102 (2026-11-13/14)

Sesja Windows 23:40–00:18 z paczką `t1` (plugin 0.4.3, commit b303ccc). Zrzuty l11–l12 i dzienniki leżą w `analysis/work/playtest/t1/` (`logs-20261113b/`). Gracz przeszedł Q1, Q2 i część drogi do Q5.

| zrzut | okno (klucz) | co słychać | przyczyna |
|---|---|---|---|
| l11 | okno ataku, obrona wroga `ENEMY_DEFEND_FAE` | opis bez ikony plusa | Ikona plusa to `<link=TERM_ADVANTAGE>` z glifem. `normalize.ICONS` nie miał tej ikony, więc link bez tekstu znikał z nagrania. Tak samo znikała ikona akcji (`TERM_ACTIONS`) i glify ikon bez linku (np. obrażenia po luce). |
| l12 | podgląd żetonu odkrycia `DEFAULT_EXPLORE_PREVIEW` | cisza | Klucz wybiera kod gry (`GameInteractable`, obiekt z `DefaultPreview`), a nie graf ani pole `PreviewKey`. Zakres D98 pomijał takie obiekty, więc kwestii nie było w bazie (`brak_klucza`, 4 okna). |

Inne ustalenia z dzienników:

- **Obrona wroga (D102) działa:** 18 okien ataku, każde z odczytem `ENEMY_DEFEND_*` (fae, bandyta, berserker, fanatyk, siostra krwi, golem).
- **Kafelek zdolności broni działa:** 2 okna `ability` (zdolność części broni) z nazwą i opisem.
- **Cel misji (D102):** 24 zmiany celu pominięte jako przeczytane w oknie.
  - Licznik wyników pokazał `objective/pełne: -1`.
  - Cel z niepełną luką (`OBJECTIVE_01`, wynik `częściowe`) zdjęty z kolejki odejmował od wyniku `pełne`.
  - Poprawka w `director._drop_read_goals`.
- **Luka łupu w Q2:** `TANGERINE_Q2_TRAVEL_STORY_10RL` (i `10EX`) ma lukę `Output First Key`. Gra wpisuje do niej klucz pierwszego przedmiotu z węzła `GiveTreasure` (`_outputFirstKey`), więc baza nie znała jej wartości. Ten sam wzorzec mają 3 kwestie w całej grze.
- **Ikona ulepszenia:** nazwy ulepszonych przedmiotów (310 kluczy w grze) mają na końcu glif ulepszenia, który lektor pomijał. Nazwy pojawiają się w kafelku zdolności w oknie ataku i na liście łupu.
- **Poza zakresem testu:** 4 okna podróży przed Q5 (`TANGERINE_Q5_TRAVEL_STORY_*`) bez nagrań, zgodnie z zakresem D101.
- **Pokrycie i wydajność:** pokrycie okien 98,4% (99,2% okien do czytania), start dźwięku p50 0,12 s, p95 0,15 s.

## Wykonanie (D103)

Wybrane w QA: plus jako „potencjał”, nazwy łupu w luce nagrane, ikona ulepszenia jako przymiotnik przed nazwą z odmianą.

- **Ikony** (`normalize.ICONS`, `GLYPH_TERMS`): „potencjał” i „akcja”, glify bez linku, mianownik przed dwukropkiem, biernik pojedynczy po „zamieniony na”.
- **Ulepszenie** (`normalize.upgraded`, `name_gender`): rodzaj z pierwszego wyrazu nazwy, z wyjątkami w `HEAD_GENDER` (liczba mnoga, „rękojeść”). Sprawdzone na wszystkich 310 nazwach gry. Companion stosuje tę samą zamianę do tekstu okna łupu, więc znajduje nagranie wersji ulepszonej.
- **Podglądy z kodu** (`scope.CODE_PREVIEWS`): `DEFAULT_EXPLORE_PREVIEW` w grupie `system` jako komunikat questu.
- **Łup w luce** (`scope.string_assignments`, `loot`): zmienna z `GiveTreasure._outputFirstKey` dostaje klucze przedmiotów aktu (716 wartości). W Q2 luka stoi w komunikacie po pustym wierszu, który czyta narrator (D85), więc wartości mają głos narratora i w większości korzystają z nagrań listy łupu.
- **Audio.** 285 nowych fragmentów OmniVoice (narrator): 135 nazw ulepszonych przedmiotów, 22 opisy z ikonami, `DEFAULT_EXPLORE_PREVIEW`, wartości luk i listy łupu. Po czterech rundach ponownych podejść automat przyjął wszystkie 285; 16 potrzebowało więcej niż jednego podejścia. Pokrycie zakresu: 2348 z 2348 kwestii.
- **Replay sesji** (`--speed 0 --no-audio`): pokrycie okien do czytania 100%. `DEFAULT_EXPLORE_PREVIEW` i `TANGERINE_Q2_TRAVEL_STORY_10RL` grają w całości. Liczniki wyników celów nie schodzą poniżej zera. Braki zostały tylko w oknach poza zakresem testu (`OBJECTIVE_01` i podróż przed Q5).
- **Testy.** `pytest`: 322 przechodzą, 2 pominięte. Plugin bez zmian (0.4.3).
