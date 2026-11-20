# E19: test instalacji jedną komendą na Windows (bez wydania)

Instalator pobiera części z lokalnego serwera na tym komputerze, tak jak później z GitHub Releases. Części leżą w `analysis/work/dist/win-online/` (zbudowane 2026-11-20 z paczki m4 z 2026-11-19: to samo audio i plugin 0.5.0, nowe skrypty i instrukcja).

Lektor jest teraz zainstalowany w grze ze starej paczki (`analysis/work/dist/win/Descent-Lektor-PL`). Test sprawdza więc też przejście ze starej instalacji.

## Kroki

1. Zamknij grę.
2. Otwórz pierwsze okno PowerShell i uruchom serwer (okno zostaw otwarte do końca testu):

   ```powershell
   & 'D:\Projects\Descent Legendy Mroku - lektor\.venv\Scripts\python.exe' -I -m http.server 47899 --bind 127.0.0.1 --directory 'D:\Projects\Descent Legendy Mroku - lektor\analysis\work\dist\win-online'
   ```

3. Otwórz drugie okno PowerShell. Pierwsza linia kieruje instalator na lokalny serwer zamiast GitHub (działa tylko w tym oknie):

   ```powershell
   $env:LEKTOR_ZRODLO = 'http://127.0.0.1:47899'
   ```

   ```powershell
   irm http://127.0.0.1:47899/instaluj-win.ps1 | iex
   ```

   Oczekiwane:
   - „Gra: E:\SteamLibrary\steamapps\common\Legends of the Dark”;
   - jeszcze przed pobieraniem: „W grze jest lektor zainstalowany z innego folderu: …\dist\win\Descent-Lektor-PL” i pytanie. Odpowiedz `T`;
   - odinstalowanie starej wersji (3 usunięte pliki, brak różnic w folderze gry);
   - „Nowa instalacja”, 4 części, ok. 1,8 GB, pasek postępu przy każdej;
   - „Zmiany w folderze gry: dodane 3” i „Zainstalowano”;
   - folder `C:\Users\<Ty>\Descent-Lektor-PL`.
4. W folderze `C:\Users\<Ty>\Descent-Lektor-PL` kliknij dwukrotnie `Test dźwięku.cmd`: jedna kwestia narratora.
5. Uruchom grę ze Steama i sprawdź kilka okien oraz menu **PL**.
6. Zamknij grę i w drugim oknie uruchom komendę z kroku 3 jeszcze raz. Oczekiwane: „Lektor jest aktualny”, nic się nie pobiera.
7. Zamknij serwer (Ctrl+C w pierwszym oknie).

## Aktualizacja do wersji 2

Wersja 2 leży w `analysis/work/dist/win-online-v2/`. Różni się od wersji 1 tylko tym, co sprawdza aktualizację:
- 3 nagrania mają nowy znacznik w pliku FLAC (ta sama mowa, inne bajty, jak ponowny eksport): `000ab757eed838b0`, `000ff2bc5d5bb4ae`, `001422a83aa7a0a9`;
- 1 nowy plik `dane/final/e19-test-nowy.flac`, którego lektor nie używa;
- nowa opcja `test_e19 = true` w `ustawienia.toml` (companion jej nie używa) i nowy opis wersji w `wersja.txt`.

8. Przygotuj zmiany, które aktualizacja ma zachować:
   - w grze, w menu **PL**, zmień głośność albo tempo i wyłącz jedną kategorię „Co czyta lektor”;
   - zrób jedno zgłoszenie (Ctrl + B, potem cyfra);
   - zamknij grę i kliknij `Wyłącz lektora.cmd` w folderze lektora.
9. W pierwszym oknie uruchom serwer wersji 2:

   ```powershell
   & 'D:\Projects\Descent Legendy Mroku - lektor\.venv\Scripts\python.exe' -I -m http.server 47899 --bind 127.0.0.1 --directory 'D:\Projects\Descent Legendy Mroku - lektor\analysis\work\dist\win-online-v2'
   ```

10. W drugim oknie (z ustawionym `LEKTOR_ZRODLO`; w nowym oknie ustaw je jak w kroku 3) uruchom tę samą komendę:

    ```powershell
    irm http://127.0.0.1:47899/instaluj-win.ps1 | iex
    ```

    Oczekiwane:
    - bez pytania o odinstalowanie;
    - „Aktualizacja: plugin 0.5.0, zbudowano 2026-11-20 10:31 -> plugin 0.5.0, zbudowano 2026-11-20 10:49”;
    - „Do pobrania: 2 z 5 części, 7 MB” (program i mała warstwa audio);
    - „Ustawienia zachowane” i „Lektor w grze: wyłączony”;
    - „Zaktualizowano do: …”.
11. Sprawdź w folderze lektora:
    - `ustawienia.toml`: Twoje zmiany z kroku 8 i nowa linia `test_e19 = true`; kopia sprzed aktualizacji w `stan\ustawienia.przed-aktualizacja.toml`;
    - zgłoszenie z kroku 8 w `zgloszenia\`;
    - `wersja.txt` z opisem wersji 2.
12. Kliknij `Włącz lektora.cmd`, uruchom grę i sprawdź, czy lektor czyta, a menu **PL** pokazuje Twoje ustawienia.
13. Zamknij grę, uruchom komendę jeszcze raz („Lektor jest aktualny”) i zamknij serwer.

## Wynik 2026-11-20

Kroki 3–6 i 8–13 przebiegły jak w opisie. Pytania o starą paczkę nie było: jej pliki zostały wcześniej usunięte z gry ręcznie (`stan\przed-instalacja.csv` nowej instalacji nie ma plików lektora).

## Wynik do przekazania

- Czy kroki 3–6 i 8–13 przebiegły jak opisano, a jeśli nie: zrzut okna PowerShell.
- Czas pobierania i rozpakowania w kroku 3 (orientacyjnie).
- Czy jakiś komunikat był niejasny.

## Po teście

- Stary folder `analysis/work/dist/win/Descent-Lektor-PL` nie jest już zainstalowany w grze; zostaje jako paczka do zipa.
- Powrót do starej instalacji: `Odinstaluj.cmd` w `C:\Users\<Ty>\Descent-Lektor-PL`, potem `Zainstaluj.cmd` w starym folderze.
- Katalogi `win-online` i `win-online-v2` usunięto po teście; części obu systemów buduje teraz `bundle --parts` we wspólnym `analysis/work/dist/online/`.
