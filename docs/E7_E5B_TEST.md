# E7 · Test cyklu na wydarzeniu E5B (Windows, slot 5)

Test sprawdza cały cykl E7 na jednym wydarzeniu, zanim ruszy duże generowanie (D63, D66):
- nowe głosy (Astarra) i odczyt wydarzenia z kampanii;
- nazwę i opis misji czytane po wybraniu jej na mapie (plugin 0.4.0);
- łup czytany z fragmentów (D51);
- guzik „Kontynuuj” bez odczytu (D64).

Używasz paczki deweloperskiej `analysis\work\dev-bundle`. Baza i audio są w repozytorium, a Python w `.venv`. W tej paczce nagrane są tylko M1, E5B i opisy misji, więc inne misje na mapie mogą być czytane częściowo.

Slot 5 to kopia kampanii znajomego. Rozegranie E5B zmieni tylko slot 5 na tym komputerze. Oryginał leży w `analysis\work\saves\mac-friend`.

## 1. Instalacja (gra zamknięta)

1. W `analysis\work\dev-bundle` kliknij dwukrotnie `Odinstaluj.cmd`, jeśli lektor jest zainstalowany.
2. Kliknij dwukrotnie `Zainstaluj.cmd`.
3. Kliknij dwukrotnie `Test dźwięku.cmd`. Powinna zabrzmieć jedna kwestia narratora.

## 2. Gra

1. Uruchom grę zwykłym przyciskiem w Steam.
2. Wczytaj slot 5. Gra powinna otworzyć mapę miasta.
3. Na mapie kliknij po kolei kilka celów, ale jeszcze żadnego nie wybieraj. Po każdym kliknięciu narrator powinien przeczytać nazwę i opis celu. Zamknięcie panelu powinno uciszyć odczyt.
4. Wybierz wydarzenie **„Cena wiedzy”** i rusz w drogę.
5. Rozegraj wydarzenie do końca. Astarra i Syrus powinni mówić swoimi głosami.
6. Jeśli pojawi się wydarzenie w podróży albo okno z łupem, zwróć uwagę, czy lista przedmiotów jest czytana w całości.
7. Wróć do miasta i wyjdź do pulpitu z menu gry.

## 3. Wynik

Napisz mi:
- czy opis misji czytał się po kliknięciu celu i cichł po zamknięciu panelu;
- jak brzmią Astarra i Syrus w wydarzeniu i czy któraś kwestia ma uciętą końcówkę;
- czy po wyborze opcji słychać odpowiedź bohatera, a po guziku „Kontynuuj” nic nie jest czytane;
- czy gra działała płynnie i czy przy wyjściu pojawił się raport crasha.

Dzienniki odczytam sam z `analysis\work\dev-bundle\logs`:
- `hook-*.jsonl`: zdarzenia `details`, okna i wybory;
- `companion-*.jsonl`: odczyty, braki i opóźnienia.

## Gdy coś nie działa

- **Lektor milczy:** gra działa normalnie. Napisz mi, a ja przejrzę dzienniki.
- **Gra nie startuje albo się wysypuje:** kliknij dwukrotnie `Wyłącz lektora.cmd` albo `Odinstaluj.cmd`.
