# E16: trzeci test paczki t1 (D103)

Test sprawdza poprawki D103 i fragmenty zakresu t1, których dwie poprzednie sesje nie objęły albo które zostały szybko przeklikane.

## Stan zapisów (2026-11-14)

Gra wczytuje ze slotu najnowszy plik. Kopia zapisów leży w `analysis/work/saves/snap-20261114/`.

| slot | najnowszy zapis | stan | do testu t1 |
|---|---|---|---|
| 1 | 2026-11-13 22:47 | Q1 ukończone, w toku Q3 | nie: Q3 jest poza zakresem t1 |
| 2 | 2026-10-31 22:00 | początek Q1 | Q1 przeszło już dwa testy |
| 3 | 2026-11-06 22:28 | Q1 ukończone, w toku Q2 (runda 1) | zapasowy: Q2 bez podróży przed misją |
| **4** | 2026-11-02 22:52 | **Q1 ukończone, miasto, dostępne Q2 i Q3** | **tak** |
| 5 | 2026-11-11 14:45 | kampania znajomego (23,5 h), w toku Q6 | nie: Q6 poza zakresem |
| 6 | 2026-11-06 22:30 | początek Q1 | Q1 przeszło już dwa testy |
| 7 | 2026-11-14 00:18 | Q1, Q2, miasto i E2A ukończone, w toku Q5 | nie: Q5 poza zakresem |
| 8 | 2026-11-11 21:09 | kampania znajomego po partii (26,9 h), dostępne Q7 i Q8 (dodany 2026-11-14) | nie: poza zakresem |

Slot 4 daje wszystko, czego brakuje: wydarzenie miejskie, podróż przed Q2, całe Q2 i potem wydarzenie 2A na mapie. Q2 w slocie 7 jest już ukończone, a slot 3 zaczyna Q2 od razu na planszy.

## Przygotowanie

1. Rozpakuj nową paczkę `Descent-Lektor-PL-win.zip` (commit 9888a75, 10593 fragmentów) w miejsce folderu na pulpicie. Plugin się nie zmienił, więc nie trzeba instalować go ponownie. `wersja.txt` powinien pokazać commit 9888a75.
2. Uruchom grę i wczytaj **slot 4**.
3. Zrzuty zapisuj jak dotąd w `analysis/work/playtest/t1/` (`l13 - opis.png`, …), a po grze zostaw dzienniki w `logs/` paczki.

## Co wykonać i czego słuchać

Okna czytaj do końca. Po zakończeniu kwestii klikaj spokojnie, zwłaszcza w wydarzeniach: w sesji 2 wydarzenie 2A przeszło w kilka sekund.

### 1. Miasto (slot 4 zaczyna w mieście)

- Wejdź do miasta i rozegraj wydarzenie miejskie, jeśli się pojawi.
- Słuchaj, czy wypowiedzi postaci w oknach narratora czyta postać, a nie narrator (9 takich okien w grupie miasta).
- Na liście łupu po wyborach powinna paść nazwa każdego przedmiotu.

### 2. Podróż przed Q2

- Wybierz Q2 na mapie. Podróż kończy się wyborem, po którym Kehli mówi o znalezisku, a narrator podaje nazwę przedmiotu z łupu (`TANGERINE_Q2_TRAVEL_STORY_10RL` albo `10EX`; D103).
- Obie odpowiedzi prowadzą do tej kwestii. W sesji 2 nazwa przedmiotu przepadała.

### 3. Q2

| sytuacja | czego słuchać | poprawka |
|---|---|---|
| kliknięcie żetonu odkrycia albo elementu bez opisu („Brak dodatkowych informacji”) | lektor czyta tekst | D103 (l12) |
| atak na fae | opis obrony: „za każdy **potencjał** zamieniony na **sukces**…” | D103 (l11) |
| atak na golema, fanatyka albo bandytę | opis obrony raz na okno | D102 |
| kafelek zdolności broni po trafieniu | nazwa i opis zdolności | D101 |
| zmiana celu w oknie „Zaktualizowano zadanie” | cel czytany tylko raz | D102 |
| okrzyki krasnoluda, Kehli i ogłoszenie golemów w oknach narratora | wypowiedzi czyta postać (11 okien z podziałem w Q2) | D101–D102 |
| łup z regału albo skrzyni | nazwy przedmiotów i liczby | D96 |

### 4. Po Q2: wydarzenie 2A na mapie

- Po Q2 mapa oferuje Q3, wydarzenie 2A i Q5. Rozegraj **2A**, czytając okna do końca.
- Wybór między innowacją a niezawodnością kończy się kwestią z podziałem na głosy (`…_09_10AInnovation` albo `…_10AReliability`).
- Q3 i Q5 leżą poza zakresem t1: tam lektor zamilknie albo przeczyta tylko część okien.

## Czego ta sesja nie sprawdzi

**Ikona ulepszenia** („ulepszony Róg Odwagi”) wymaga ulepszonego przedmiotu. Żaden zapis takiego nie ma, a w slocie 5 są tylko receptury ulepszeń. Sprawdzimy ją, gdy drużyna ulepszy przedmiot w kuźni.

## Po sesji

Napisz, że skończyłeś. Przeanalizuję dzienniki `hook-*.jsonl` i `companion-*.jsonl` z `logs/` paczki oraz nowe zrzuty.

## Wynik i następny test (D105)

Sesja na slocie 4 odbyła się 2026-11-14. Wyniki i przyczyny błędów l13–l15 są w `analysis/E16_PLAYTEST.md`.

Nowa paczka ma plugin 0.4.4, więc przed grą uruchom **Zainstaluj** z nowej paczki. Bez tego okno wyzwania zostanie ciche. W kolejnej sesji sprawdź:

| sytuacja | czego słuchać | poprawka |
|---|---|---|
| ukończone wyzwanie bohatera | „Wyzwanie ukończone!” i lista nagród (karty z imieniem bohatera) | D105 (l14) |
| aktywacja fanatyka | „jeśli cel nie wyrzucił wzmocnienia” | D105 (l13) |
| wydarzenie miejskie, wybór dla Brynn | wtrącenie „– mamrocze Kehli…” i polecenie po nim czyta narrator | D105 (l15) |
| łup po pokonaniu golema w Q2 | nazwa golema w poleceniu „Usuń: …” | D105 |
| atak na fae | „potencjał” w opisie obrony | D103 (nie wystąpił w sesji 3) |
| kafelek zdolności broni | nazwa i opis zdolności | D101 (nie wystąpił w sesji 3) |

### Po czwartej sesji (D106)

Paczka z pluginem 0.4.5: przed grą znowu uruchom **Zainstaluj**. Gdy bohater ukończy wyzwanie, lektor od razu powie „Wyzwanie ukończone!”, imię bohatera i nazwę wyzwania. Nagrodę przeczyta po wejściu do menu wyzwań.
