# Lektor PL do Descent: Legends of the Dark

Polski lektor do gry *Descent: Legends of the Dark* ze Steama. Czyta okna fabularne, dialogi, komunikaty misji i cele głosami z polskiego dubbingu. Nagrania są gotowe w folderze, więc lektor nie potrzebuje internetu.

## Co warto wiedzieć

- **Zakres:** ta wersja ma nagrania prologu, pierwszej misji i sceny „Welcome Home” w mieście. W dalszych misjach lektor milczy, a gra działa normalnie. Listy łupu nie są jeszcze czytane.
- **Jak działa:** gra uruchamia lektora sama. Mały dodatek w grze rozpoznaje okna i przekazuje je lektorowi, a lektor odtwarza nagrania przez głośnik komputera. Po wyjściu z gry lektor też się zamyka.
- **Co zmienia na komputerze:** wszystko leży w folderze `Descent-Lektor-PL`. Instalacja nie potrzebuje hasła administratora i niczego nie instaluje w systemie.
  - Windows: w folderze gry pojawiają się 3 małe pliki.
  - Mac: gra dostaje nowy podpis, a w Steam pojawia się opcja uruchamiania.
- **Muzyka:** lektor nie przycisza muzyki gry. Ustaw jej głośność w opcjach gry.
- **Prywatność:** paczka zawiera nagrania z gry. Nie udostępniaj jej publicznie.

## Zawartość folderu

| Plik | Do czego |
|---|---|
| `Zainstaluj` | instaluje lektora w grze; ponowne uruchomienie naprawia instalację |
| `Odinstaluj` | usuwa lektora z gry |
| `Wyłącz lektora`, `Włącz lektora` | wyłącza albo włącza lektora bez odinstalowania |
| `Ustawienia` | otwiera plik ustawień (głośność, głośnik, kategorie) |
| `Test dźwięku` | odtwarza jedną kwestię narratora |
| `INSTRUKCJA.md` | ta instrukcja |
| `wersja.txt` | wersja paczki |
| `logs/` | dzienniki do zgłaszania problemów |
| `plugin/`, `loader/`, `python/`, `lektor/`, `dane/`, `skrypty/` | pliki lektora, nie ruszaj ich |

Na Windows pliki do dwukliku mają końcówkę `.cmd`, a na Macu `.command`.

## Windows

### Wymagania

- Windows 10 albo 11 (64-bit).
- Gra kupiona i zainstalowana w Steam.
- Ok. 0,5 GB wolnego miejsca.

### Instalacja

1. Rozpakuj paczkę w stałe miejsce, np. `C:\Gry\Descent-Lektor-PL`. Nie rozpakowuj jej do folderu gry. Folderu nie usuwaj, bo gra wczytuje lektora właśnie z niego.
2. Zamknij grę.
3. Kliknij dwukrotnie `Zainstaluj.cmd`.
   - Jeśli Windows pokaże „System Windows ochronił ten komputer”, kliknij „Więcej informacji”, a potem „Uruchom mimo to”.
   - Skrypt sam znajduje grę w bibliotekach Steam. Gdy jej nie znajdzie, poprosi o folder gry: w Steam kliknij grę prawym przyciskiem, wybierz *Zarządzaj → Przeglądaj pliki lokalne* i skopiuj ścieżkę z paska adresu.
   - Na końcu powinien pojawić się napis „Zainstalowano” i lista 3 dodanych plików.
4. Kliknij dwukrotnie `Test dźwięku.cmd`. Powinna zabrzmieć jedna kwestia narratora.

### Granie

Uruchom grę zwykłym przyciskiem *Graj* w Steam. Lektor startuje razem z grą i czyta od pierwszego okna. Po wyjściu z gry zamyka się sam.

### Ustawienia

1. Kliknij dwukrotnie `Ustawienia.cmd`. Plik `ustawienia.toml` otworzy się w Notatniku.
2. Zmień wartości:
   - `volume`: głośność lektora od `0.0` do `1.0`;
   - `device`: głośnik albo słuchawki. Puste `""` oznacza urządzenie domyślne systemu. Możesz wpisać fragment nazwy urządzenia, np. `"Headphones"`;
   - sekcja `[toggles]`: `false` wycisza daną kategorię, np. `ui = false` wyłącza komunikaty interfejsu.
3. Zapisz plik (Ctrl+S). Zmiany działają od następnego uruchomienia gry.
4. Uruchom `Test dźwięku.cmd`. Test sprawdza też, czy w pliku nie ma błędu.

Głośność lektora zmienisz też w mikserze głośności Windows, gdzie lektor widnieje jako `python`.

### Wyłączanie i włączanie

Przy zamkniętej grze kliknij dwukrotnie `Wyłącz lektora.cmd`. Gra startuje wtedy bez lektora. `Włącz lektora.cmd` włącza go z powrotem.

### Odinstalowanie

1. Zamknij grę.
2. Kliknij dwukrotnie `Odinstaluj.cmd`. Skrypt usuwa 3 pliki lektora z folderu gry i sprawdza, czy folder wygląda jak przed instalacją.
3. Teraz możesz usunąć folder `Descent-Lektor-PL`.

### Przeniesienie folderu i aktualizacje gry

- Po przeniesieniu folderu w inne miejsce uruchom ponownie `Zainstaluj.cmd`.
- Aktualizacja gry w Steam nie usuwa lektora. Gdy po aktualizacji lektor milczy, uruchom `Zainstaluj.cmd` jeszcze raz.

## Mac (Apple Silicon)

### Wymagania

- Mac z procesorem Apple (M1 lub nowszym) i aktualnym macOS.
- Gra kupiona i zainstalowana w Steam.
- Ok. 0,5 GB wolnego miejsca.

### Instalacja

1. Skopiuj plik `Descent-Lektor-PL-mac.zip` na Maca, np. pendrive'em. Rozpakuj go na dysku Maca dwuklikiem w Finderze.
2. Przenieś folder `Descent-Lektor-PL` do katalogu domowego (w Finderze: *Idź → Katalog domowy*).
   - Nie zostawiaj go w Dokumentach, Pobranych ani na Biurku. macOS chroni te foldery i gra nie mogłaby wczytać lektora.
3. Zamknij grę.
4. Kliknij dwukrotnie `Zainstaluj.command`. Otworzy się okno Terminala.
   - Jeśli macOS zablokuje plik („nie można sprawdzić dewelopera”), otwórz *Ustawienia systemowe → Prywatność i ochrona*, na dole kliknij „Otwórz mimo to”, a potem ponownie kliknij plik dwukrotnie.
   - Skrypt nadaje grze nowy podpis, bo bez niego macOS nie pozwala wczytać dodatku. Jeśli macOS zapyta, czy Terminal może zarządzać aplikacjami, zgódź się. Gdy zgoda wymaga ustawień, włącz Terminal w *Ustawienia systemowe → Prywatność i ochrona → Zarządzanie aplikacjami* i uruchom `Zainstaluj.command` jeszcze raz.
   - Na końcu skrypt kopiuje do schowka opcję uruchamiania dla Steama.
5. W Steam kliknij grę prawym przyciskiem i wybierz *Właściwości → Ogólne*. W polu *Opcje uruchamiania* wklej skopiowany tekst (Cmd+V).
6. Kliknij dwukrotnie `Test dźwięku.command`. Powinna zabrzmieć jedna kwestia narratora.

### Granie

Uruchom grę zwykłym przyciskiem *Graj* w Steam. Lektor startuje razem z grą i zamyka się sam po wyjściu z niej.

### Ustawienia

1. Kliknij dwukrotnie `Ustawienia.command`. Plik `ustawienia.toml` otworzy się w TextEdit.
2. Wartości są takie same jak na Windows (zobacz [Ustawienia](#ustawienia)).
   - Tekst wpisuj w zwykłych cudzysłowach `"`. Jeśli TextEdit zamienia je na „ozdobne”, wyłącz *Edycja → Zastępowanie → Inteligentne cudzysłowy*.
3. Zapisz plik (Cmd+S) i uruchom `Test dźwięku.command`.

### Wyłączanie i włączanie

`Wyłącz lektora.command` sprawia, że gra startuje bez lektora. Opcja uruchamiania w Steam może zostać. `Włącz lektora.command` włącza go z powrotem.

### Odinstalowanie

1. Zamknij grę.
2. Kliknij dwukrotnie `Odinstaluj.command`.
3. W Steam usuń tekst z pola *Opcje uruchamiania* (*Właściwości → Ogólne*).
4. W Steam wybierz *Właściwości → Zainstalowane pliki → Zweryfikuj spójność plików gry*. Steam przywróci oryginalny plik gry z jego podpisem.
5. Usuń folder `Descent-Lektor-PL`.

### Aktualizacje gry

Aktualizacja w Steam przywraca oryginalny podpis gry. Gra wtedy uruchomi się bez lektora i pokaże komunikat. Uruchom ponownie `Zainstaluj.command`. Opcja uruchamiania w Steam zostaje bez zmian.

## Gdy coś nie działa

| Objaw | Co zrobić |
|---|---|
| Lektor nic nie mówi | Uruchom `Test dźwięku`. Gdy test milczy, sprawdź `volume` i `device` w Ustawieniach oraz głośność systemu. Gdy test działa, a w grze cisza, uruchom `Zainstaluj` jeszcze raz. |
| Lektor gra na złym głośniku | Wpisz fragment nazwy właściwego urządzenia w `device` w Ustawieniach. |
| Pierwsze okno jest czytane z opóźnieniem | Lektor startuje razem z grą. Pierwsze okno może zabrzmieć z opóźnieniem do kilku sekund. |
| Lektor czyta coś, czego nie chcesz | Wyłącz kategorię w sekcji `[toggles]` Ustawień. |
| Gra nie startuje albo działa dziwnie | Uruchom `Wyłącz lektora` i sprawdź, czy problem znika. Napisz do autora paczki. |
| Test dźwięku pokazuje błąd | W `ustawienia.toml` jest literówka. Popraw ją albo przywróć wartości z tej instrukcji. |

Zgłaszając problem, wyślij plik `wersja.txt` i folder `logs`. Dzienniki zawierają klucze okien, czasy, fragmenty tekstów z gry i ścieżki folderów lektora.
