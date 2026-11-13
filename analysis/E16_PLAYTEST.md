# E16: test paczki t1 w grze, Q1 (2026-11-13)

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
