# E5 · Sesja M1 z lektorem (Windows)

Sesja z 2026-11-02 trwała ok. 30 min:
- prolog i Q1, mapa aktu, scena „Welcome Home”, wyjście do menu i do pulpitu;
- plugin 0.2.1 na etapie 4 z poprawką MonoMod (D54);
- companion z pregenerowanym audio M1 (E3).

Dane pochodzą z prywatnych dzienników w `%LOCALAPPDATA%\LektorPL\logs`: `hook-20261102-222237.jsonl` z pluginu i `companion-20261102-222155.jsonl` z companiona. Raport nie zawiera treści gry.

## Wynik względem D13

| Kryterium | Cel | Wynik |
|---|---|---|
| audio w oknach (bez okien samego łupu, D50) | ≥ 98% | **96,98%** (225 z 232) |
| start odczytu | < 0,5 s | p50 0,117 s · p95 0,128 s · max 0,171 s (n = 227) |
| przerwanie | < 0,3 s | p50 0,114 s · p95 0,126 s · max 0,127 s (n = 132) |

- Start i przerwanie liczymy od odebrania zdarzenia przez companion do zmiany dźwięku na wyjściu. Wliczony jest bufor wyjścia audio 0,107 s.
- Dojście zdarzenia z pluginu do companiona: p95 3 ms, max 32 ms. Przygotowanie audio: p50 1,6 ms, p95 13 ms, max 50 ms.
- Odczyt czekający na koniec bieżącego (cel, aktywacja, D45): p95 0,142 s od zwolnienia.
- Pokrycie nie osiąga 98% przez klucze pominięte w M1 zgodnie z D49. Zobacz [Braki](#braki).
  - Okna łupu wielokrotnego (`DEFAULT_GET_TREASURE_MULTI`) też pokazują sam łup. Liczone tak jak `DEFAULT_GET_TREASURE_SINGLE` w D50, dają pokrycie 99,6% (225 z 226).

## Okna i odczyty

| Źródło | Liczba | Pełne | Częściowe | Bez audio | Bez klucza w bazie | Inne |
|---|---|---|---|---|---|---|
| okna wiadomości | 128 | 116 | 2 | 3 | 7 | – |
| okna fabularne | 107 | 107 | – | – | – | – |
| odpowiedź bohatera po wyborze (D48) | 17 | 17 | – | – | – | – |
| cel misji (D31) | 14 | 1 | 8 | – | – | 5 pominiętych: ten sam tekst był w oknie |
| aktywacja wroga (D30) | 8 | 7 | – | – | – | 1 puste okno bez klucza i tekstu |

- Do końca zabrzmiało 122 odczytów, a 132 przerwało kliknięcie dalej albo nowe okno. 124 okna zamknięto przed końcem audio.
- Odczyty według głosu:

  | Głos | Odczyty |
  |---|---|
  | narrator | 179 |
  | brynn | 21 |
  | syrus | 19 |
  | galaden | 15 |
  | adelynn | 12 |
  | vaerix | 11 |
  | ronan | 6 |
  | kehli | 2 |
  | chance | 1 |

- Klucze bazy M1, które pojawiły się w sesji:

  | Grupa | Klucze | Uwagi |
  |---|---|---|
  | „Welcome Home” | 47 z 49 | |
  | fabuła Q1 | 55 z 89 | |
  | sceny Q1 | 115 z 365 | gałęzie i węzły zależą od wyborów i losowania |
  | wrogowie | 6 z 106 | |
  | system | 4 z 26 | |
  | przerywnik | 0 z 14 | nie pojawił się w dzienniku |

## Braki

| Klucz | Okna | Brak | Przyczyna |
|---|---|---|---|
| `DEFAULT_GET_TREASURE_MULTI` | 6 | klucz | łup wielokrotny; klucz pominięty w M1 (D49) |
| `DEFAULT_GET_TREASURE_SINGLE` | 3 | luki `LocalizationKey`, `RawText` | sam łup, wyłączony z kryterium (D50) |
| `TRAVEL_28` | 1 | klucz | zdarzenie podróży poza bazą M1 (D49) |
| `TACTIC_PHASE_DESCRIPTION` | 2 | luka `VariableString` | wartość znana dopiero w grze; jak w E4 |
| `Q1_OBJECTIVE_5` | 5 | luka `VariableInt` | licznik postępu celu bez nagrania |
| `Q1_OBJECTIVE_6` | 3 | luka `VariableInt` | licznik postępu celu bez nagrania |

Cele misji plugin zgłasza dopiero od E4 (D32). Dlatego replay E1 ich nie zawierał, a wartości liczników celu nie trafiły do inwentarza wartości E2. Razem z odczytem aktualizacji celu poprawimy to w E7 (D55).

## Wydajność i stabilność

- Plugin pracował najwyżej 3,2 ms na klatkę.
  - Najdłuższe klatki (0,92 s i 0,35 s) wypadły w pierwszych 2 minutach, przy ładowaniu menu i Q1, a 0,22 s przy ładowaniu mapy.
  - Poza tym klatki trwały poniżej 0,1 s.
- Plugin połączył się z companionem 41 s po starcie companiona i rozłączył przy wyjściu z gry, bez zerwań w trakcie sesji.
- Wyjście do pulpitu było bez crasha: w `Crashes` nie przybył folder. To drugie potwierdzenie poprawki D54, po teście D.

## Uwagi z gry (D55)

Uwagi użytkownika. M1 zostaje bez zmian, a uwagi trafiają do kolejnych scenariuszy (E7):
1. Aktualizacje celu z licznikiem powtarzały się (dane: `Q1_OBJECTIVE_5` ×5, `Q1_OBJECTIVE_6` ×3).
2. Brak odczytu łupu i zdobytych przedmiotów (zgodnie z D49–D51 w M1). Od E7 czyta je narrator.
3. Kehli ma zmienną modulację głosu w dialogach. Do ujednolicenia.
4. Głosy Ronana i Baronessy Adelynn nie do końca pasują. Robimy ponowny dobór (D41).
5. Opis misji przy wyborze na mapie powinien czytać narrator. Plugin nie widzi tego okna. W dzienniku ze sceny mapy (`Act1Map`) jest 51 okien fabularnych i 11 okien wiadomości, ale nie ma żadnego zdarzenia z opisem misji. Klasę tego okna znajdziemy w dekompilacji przed E7.

## Wnioski

- Opóźnienia spełniają D13 z dużym zapasem: start p95 0,13 s, przerwanie p95 0,13 s.
- Pokrycie 96,98% wynika wyłącznie z kluczy, które M1 świadomie pomija (D49): łup wielokrotny i jedno zdarzenie podróży. Od E7 nagrywamy wszystkie kwestie i łup (D49, D51).
- Plugin z poprawką MonoMod jest stabilny: 30 min gry bez spadków płynności i bez crasha przy wyjściu.
