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

## Wynik do przekazania

- Czy kroki 3–6 przebiegły jak opisano, a jeśli nie: zrzut okna PowerShell.
- Czas pobierania i rozpakowania w kroku 3 (orientacyjnie).
- Czy jakiś komunikat był niejasny.

## Po teście

- Stary folder `analysis/work/dist/win/Descent-Lektor-PL` nie jest już zainstalowany w grze; zostaje jako paczka do zipa.
- Powrót do starej instalacji: `Odinstaluj.cmd` w `C:\Users\<Ty>\Descent-Lektor-PL`, potem `Zainstaluj.cmd` w starym folderze.
