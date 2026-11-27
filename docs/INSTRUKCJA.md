# Lektor PL do Descent: Legends of the Dark

Polski lektor do gry *Descent: Legends of the Dark* ze Steama. Czyta okna fabularne, dialogi, komunikaty misji i cele głosami z polskiego dubbingu. Nagrania są gotowe w folderze lektora, więc w trakcie gry lektor nie potrzebuje internetu.

## Co warto wiedzieć

- **Zakres:** ta wersja ma nagrania całego aktu 1: prologu, wszystkich scenariuszy głównych i pobocznych ze wstępami i zakończeniami, wydarzeń kampanii, podróży, tekstów miasta i list łupu. Wypowiedzi postaci w oknach narratora czytają głosy tych postaci, a każda postać bez imienia ma własny głos. Akt 2 przyjdzie w kolejnej wersji; do tego czasu lektor czyta w nim tylko wspólne komunikaty. Gra działa wtedy normalnie.
- **Jak działa:** gra uruchamia lektora sama. Mały dodatek w grze rozpoznaje okna i przekazuje je lektorowi, a lektor odtwarza nagrania przez głośnik komputera. Po wyjściu z gry lektor też się zamyka.
- **Co zmienia na komputerze:** wszystko leży w folderze `Descent-Lektor-PL` w folderze użytkownika. Instalacja nie potrzebuje hasła administratora i niczego nie instaluje w systemie.
<!-- win -->
- **Windows:** folder lektora to np. `C:\Users\Jan\Descent-Lektor-PL`, a w folderze gry pojawiają się 3 małe pliki.
<!-- /win -->
<!-- mac -->
- **Mac:** folder lektora leży w katalogu domowym, gra dostaje nowy podpis, a w Steam pojawia się opcja uruchamiania.
<!-- /mac -->
- **Muzyka:** lektor nie przycisza muzyki gry. Ustaw jej głośność w opcjach gry.

## Zawartość folderu

| Plik | Do czego |
|---|---|
| `Zainstaluj` | instaluje lektora w grze; ponowne uruchomienie naprawia instalację |
| `Odinstaluj` | usuwa lektora z gry |
| `Test dźwięku` | odtwarza jedną kwestię narratora i sprawdza plik ustawień |
| `ustawienia.toml` | ustawienia: głośność, tempo, głośnik, kategorie, skróty |
| `INSTRUKCJA.md` | ta instrukcja |
| `wersja.txt` | wersja paczki |
| `LICENSE.md`, `UZNANIE_AUTORSTWA.md`, `licencje/` | warunki korzystania, autorzy modeli głosu i programów w paczce |
| `logs/`, `zgloszenia/` | dzienniki i zgłoszenia błędów z gry, do wysłania autorowi |
| `plugin/`, `loader/`, `python/`, `lektor/`, `dane/`, `skrypty/`, `stan/` | pliki lektora, nie ruszaj ich |

<!-- win -->
Pliki do dwukliku mają na Windows końcówkę `.cmd`.

## Windows

### Wymagania

- Windows 10 albo 11 (64-bit).
- Gra kupiona i zainstalowana w Steam.
- Ok. 3 GB wolnego miejsca na dysku C: przy pierwszej instalacji (lektor zajmuje ok. 1,6 GB). Aktualizacja pobiera tylko zmienione części.

### Instalacja

1. Zamknij grę.
2. Otwórz PowerShell: naciśnij klawisz Windows, wpisz `PowerShell` i naciśnij Enter.
3. Wklej tę komendę (prawy przycisk myszy w oknie PowerShell wkleja) i naciśnij Enter:

   ```powershell
   irm https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download/instaluj-win.ps1 | iex
   ```

   - Instalator sam znajduje grę w bibliotekach Steam. Gdy jej nie znajdzie, poprosi o folder gry: w Steam kliknij grę prawym przyciskiem, wybierz *Zarządzaj → Przeglądaj pliki lokalne* i skopiuj ścieżkę z paska adresu.
   - Gdy w grze jest lektor ze starej paczki w innym folderze, instalator jeszcze przed pobieraniem zapyta, czy go odinstalować. Odpowiedz `T`. Ustawienia ze starego folderu nie przechodzą do nowego; stary folder usuń po instalacji.
   - Lektor trafia do folderu `Descent-Lektor-PL` w folderze użytkownika (np. `C:\Users\Jan\Descent-Lektor-PL`). Tam są `ustawienia.toml`, `Test dźwięku`, `Odinstaluj` i pozostałe pliki.
   - Na końcu powinien pojawić się napis „Zainstalowano” i lista 3 plików dodanych do folderu gry.
4. W folderze lektora kliknij dwukrotnie `Test dźwięku.cmd`. Powinna zabrzmieć jedna kwestia narratora.

Bez komendy: pobierz z wydania plik `Descent-Lektor-PL-win.zip`, rozpakuj go w stałe miejsce (nie do folderu gry) i kliknij dwukrotnie `Zainstaluj.cmd`. Jeśli Windows pokaże „System Windows ochronił ten komputer”, kliknij „Więcej informacji”, a potem „Uruchom mimo to”. Takiej instalacji komenda nie aktualizuje.

### Aktualizacja

Przy zamkniętej grze uruchom w PowerShell tę samą komendę co przy instalacji. Instalator pobiera tylko części, które zmieniły się od zainstalowanej wersji, i usuwa pliki, których nowa wersja już nie ma. Zostają Twoje ustawienia (nowe opcje dostają wartości domyślne), zgłoszenia i dzienniki. Gdy wersja jest aktualna, instalator to pisze i niczego nie pobiera.

### Granie

Uruchom grę zwykłym przyciskiem *Graj* w Steam. Lektor startuje razem z grą i czyta od pierwszego okna. Po wyjściu z gry zamyka się sam.

### Odinstalowanie

1. Zamknij grę.
2. Kliknij dwukrotnie `Odinstaluj.cmd`. Skrypt usuwa 3 pliki lektora z folderu gry i sprawdza, czy folder wygląda jak przed instalacją.
3. Teraz możesz usunąć folder `Descent-Lektor-PL`.

### Aktualizacje gry

Aktualizacja gry w Steam nie usuwa lektora. Gdy po niej lektor milczy, uruchom komendę instalacji jeszcze raz albo `Zainstaluj.cmd` w folderze lektora. Folderu lektora nie przenoś: komenda instaluje i aktualizuje go zawsze w tym samym miejscu.

<!-- /win -->
<!-- mac -->
Pliki do dwukliku mają na Macu końcówkę `.command`.

## Mac (Apple Silicon)

### Wymagania

- Mac z procesorem Apple (M1 lub nowszym) i aktualnym macOS.
- Gra kupiona i zainstalowana w Steam.
- Ok. 4 GB wolnego miejsca przy pierwszej instalacji (lektor zajmuje ok. 1,6 GB). Aktualizacja pobiera tylko zmienione części.

### Instalacja

1. Zamknij grę.
2. Otwórz Terminal: Cmd+Spacja, wpisz `Terminal` i naciśnij Enter.
3. Wklej tę komendę (Cmd+V) i naciśnij Enter:

   ```bash
   curl -fsSL https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download/instaluj-mac.sh | bash
   ```

   - Lektor trafia do folderu `Descent-Lektor-PL` w katalogu domowym. Tam są `ustawienia.toml`, `Test dźwięku`, `Odinstaluj` i pozostałe pliki (w Finderze: *Idź → Katalog domowy*).
   - Instalator nadaje grze nowy podpis, bo bez niego macOS nie pozwala wczytać dodatku. Jeśli macOS zapyta, czy Terminal może zarządzać aplikacjami, zgódź się. Gdy zgoda wymaga ustawień, włącz Terminal w *Ustawienia systemowe → Prywatność i ochrona → Zarządzanie aplikacjami*, zamknij Terminal (Cmd+Q) i uruchom komendę jeszcze raz.
   - Na końcu instalator kopiuje do schowka opcję uruchamiania dla Steama i pisze, czy trzeba ją wkleić.
4. Przy pierwszej instalacji, albo gdy instalator o to prosi: w Steam kliknij grę prawym przyciskiem i wybierz *Właściwości → Ogólne*. W polu *Opcje uruchamiania* zastąp tekst skopiowanym (Cmd+V).
   - Gdy wcześniej był lektor ze starej paczki w innym folderze, instalator to napisze. Po wklejeniu nowej opcji stary folder możesz usunąć.
5. W folderze lektora kliknij dwukrotnie `Test dźwięku.command`. Powinna zabrzmieć jedna kwestia narratora.

Bez komendy: pobierz z wydania plik `Descent-Lektor-PL-mac.zip`, rozpakuj go, przenieś folder `Descent-Lektor-PL` do katalogu domowego (nie do Dokumentów, Pobranych ani na Biurko) i kliknij dwukrotnie `Zainstaluj.command`. Jeśli macOS zablokuje plik, otwórz *Ustawienia systemowe → Prywatność i ochrona* i kliknij „Otwórz mimo to”. Opcję uruchamiania wklej jak w kroku 4. Takiej instalacji komenda nie aktualizuje.

### Aktualizacja

Przy zamkniętej grze uruchom w Terminalu tę samą komendę co przy instalacji. Instalator pobiera tylko zmienione części, a ustawienia, zgłoszenia i dzienniki zostają. Opcji uruchamiania w Steam nie trzeba zmieniać, bo folder lektora się nie zmienia.

### Granie

Uruchom grę zwykłym przyciskiem *Graj* w Steam. Lektor startuje razem z grą i zamyka się sam po wyjściu z niej.

### Odinstalowanie

1. Zamknij grę.
2. Kliknij dwukrotnie `Odinstaluj.command`.
3. W Steam usuń tekst z pola *Opcje uruchamiania* (*Właściwości → Ogólne*).
4. W Steam wybierz *Właściwości → Zainstalowane pliki → Zweryfikuj spójność plików gry*. Steam przywróci oryginalny plik gry z jego podpisem.
5. Usuń folder `Descent-Lektor-PL`.

### Aktualizacje gry

Aktualizacja w Steam przywraca oryginalny podpis gry. Gra wtedy uruchomi się bez lektora i pokaże komunikat. Uruchom ponownie komendę instalacji albo `Zainstaluj.command` w folderze lektora. Opcja uruchamiania w Steam zostaje bez zmian.

<!-- /mac -->

## Lektor w trakcie gry

Na dolnym pasku, obok zębatki i drużyny, jest przycisk **PL**. Otwiera menu lektora:
- bieżąca kwestia oraz przyciski Powtórz, Utnij i Wycisz;
- tempo (0,8–1,6×) i głośność lektora;
- „Co czyta lektor”: kategorie do włączenia i wyłączenia, a na końcu listy „Statystyki na koniec misji”: panele po bokach okna podsumowania misji (ataki, wyzwania i postawy bohaterów, balans gry, przebieg misji i łup);
- 3 ostatnie kwestie: „Graj” odtwarza kwestię jeszcze raz, „Zgłoś” zgłasza błąd w tej kwestii;
- „Zgłoś błąd” i lista skrótów.

Zmiany tempa, głośności, statystyk i kategorii zapisują się od razu w `ustawienia.toml`. Wyciszenie działa do końca sesji.

| Skrót | Działanie |
|---|---|
| Ctrl + + / Ctrl + - | szybciej / wolniej (od następnej kwestii) |
| Ctrl + M | wycisza albo włącza lektora |
| Ctrl + R | powtarza ostatnią kwestię |
| Ctrl + S | ucina bieżącą kwestię |
| Ctrl + B | zgłoszenie błędu: zrzut ekranu, potem cyfra 1–6 z rodzajem błędu (0 anuluje) |
| Ctrl + L | otwiera albo zamyka menu lektora |

Zgłoszenia trafiają do folderu `zgloszenia` w folderze lektora: każde ma zrzut ekranu i plik z opisem kwestii.

<!-- mac -->
Na Macu skróty używają klawisza Control, nie Command.
<!-- /mac -->

## Ustawienia

Ustawienia leżą w pliku `ustawienia.toml` w folderze lektora. Otwórz go w edytorze tekstu:
<!-- win -->
- Windows: prawy przycisk na pliku, *Otwórz za pomocą → Notatnik*. Zapisujesz Ctrl+S.
<!-- /win -->
<!-- mac -->
- Mac: prawy przycisk na pliku, *Otwórz za pomocą → TextEdit*. Zapisujesz Cmd+S. Tekst wpisuj w zwykłych cudzysłowach `"`. Jeśli TextEdit zamienia je na „ozdobne”, wyłącz *Edycja → Zastępowanie → Inteligentne cudzysłowy*.
<!-- /mac -->

Wartości:
- `volume`: głośność lektora od `0.0` do `1.0`;
- `tempo`: tempo lektora od `0.8` do `1.6`, `1.0` to tempo nagrań;
- `device`: głośnik albo słuchawki. Puste `""` oznacza urządzenie domyślne systemu. Możesz wpisać fragment nazwy urządzenia, np. `"Headphones"`;
- sekcja `[toggles]`: `false` wycisza daną kategorię, np. `ui = false` wyłącza komunikaty interfejsu, `opis_misji = false` wyłącza odczyt nazwy i opisu misji na mapie, a `zdolnosci = false` wyłącza w oknie ataku odczyt obrony wroga i zdolności broni oraz talizmanów;
- sekcja `[skroty]`: skróty klawiszowe w grze;
- sekcja `[podsumowanie]`: `statystyki = false` wyłącza panele ze statystykami przy oknie podsumowania misji.

Zmiany działają od następnego uruchomienia gry. Głośność, tempo, statystyki i kategorie zmienisz też w grze, w menu **PL**. Po zmianie uruchom `Test dźwięku`: sprawdza też, czy w pliku nie ma błędu.
<!-- win -->

Głośność lektora zmienisz też w mikserze głośności Windows, gdzie lektor widnieje jako `python`.
<!-- /win -->

## Gdy coś nie działa

| Objaw | Co zrobić |
|---|---|
| Lektor nic nie mówi | Uruchom `Test dźwięku`. Gdy test milczy, sprawdź `volume` i `device` w `ustawienia.toml` oraz głośność systemu. Gdy test działa, a w grze cisza, uruchom `Zainstaluj` jeszcze raz. |
| Komenda instalacji kończy się błędem pobierania | Sprawdź internet i uruchom komendę ponownie: pobieranie wznowi się od miejsca przerwania. |
| Lektor gra na złym głośniku | Wpisz fragment nazwy właściwego urządzenia w `device` w `ustawienia.toml`. |
| Pierwsze okno jest czytane z opóźnieniem | Lektor startuje razem z grą. Pierwsze okno może zabrzmieć z opóźnieniem do kilku sekund. |
| Lektor czyta coś, czego nie chcesz | Wyłącz kategorię w menu **PL** w grze albo w sekcji `[toggles]` w `ustawienia.toml`. |
| Lektor czyta za wolno albo za szybko | Zmień tempo w menu **PL** albo skrótem Ctrl + + / Ctrl + -. |
| Gra nie startuje albo działa dziwnie | Uruchom `Odinstaluj` i sprawdź, czy problem znika. Napisz do autora paczki. |
| Test dźwięku pokazuje błąd | W `ustawienia.toml` jest literówka. Popraw ją albo przywróć wartości z tej instrukcji. |

Błąd lektora najłatwiej zgłosić w chwili, gdy wystąpi: Ctrl + B albo „Zgłoś” w menu **PL**. Zgłaszając problem, wyślij plik `wersja.txt` oraz foldery `zgloszenia` i `logs`. Dzienniki zawierają klucze okien, czasy, fragmenty tekstów z gry i ścieżki folderów lektora.
