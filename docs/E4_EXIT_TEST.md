# E4 · Dwa testy wyjścia z gry (przed E5, D40)

W E1 gra z loaderem 2 z 2 razy kończyła się crashem przy wyjściu do pulpitu (`mono_jit_cleanup`). Bez moda zamyka się czysto. Te dwa krótkie testy pokażą, czy crash wywołuje sam BepInEx, czy nasz plugin. Plugin 0.2.0 przy wyjściu odpina subskrypcje i zamyka połączenie z companionem.

Każdy test zajmuje ok. 3 minuty: start gry, menu, wyjście. Nie trzeba wczytywać zapisu.

Przed testami sprawdź, ile folderów jest w `%TEMP%\Fantasy Flight Games\Descent - Legends of the Dark\Crashes`. Każdy crash dodaje tam nowy folder.

## Test A: sam BepInEx (gra zamknięta)

1. Zainstaluj sam loader, bez pluginu:

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install -LoaderOnly
   ```

   Oczekiwane: ok. 25 dodanych plików, 0 usuniętych i 0 zmienionych. Na końcu: „Zainstalowano sam BepInEx, bez pluginu”.
2. Uruchom grę ze Steama i poczekaj na menu główne (ok. 30 s w menu).
3. Wyjdź do pulpitu przyciskiem wyjścia w menu gry.
4. Zanotuj, czy pojawiło się okno raportu crasha i czy w `Crashes` przybył folder.
5. Odinstaluj (gra zamknięta):

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Uninstall
   ```

   Skrypt kopiuje `LogOutput.log` do `analysis/work/install/logs/` i porównuje folder gry ze stanem sprzed instalacji.

## Test B: BepInEx z pluginem 0.2.0 i companionem

1. Jeśli od ostatniego builda zmieniał się kod pluginu: `dotnet build src\plugin\BepInEx -c Release`.
2. Zainstaluj loader z pluginem:

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install
   ```

3. W osobnym oknie PowerShella uruchom companion i zostaw okno otwarte:

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-companion.ps1
   ```

   Pokaże „Companion nasłuchuje na 127.0.0.1:47810”.
4. Uruchom grę ze Steama i poczekaj na menu (ok. 30 s).
   - Sprawdź stan: `lektor-hook.ps1` bez parametrów powinien pokazać „Plugin: 0.2.0…” i najnowszy dziennik `hook-….jsonl`.
   - W oknie companiona nie musi nic się pojawić, bo menu nie ma okien wiadomości. Połączenie widać w jego dzienniku (`client connected`).
5. Wyjdź do pulpitu z menu gry. Zanotuj okno raportu crasha i nowy folder w `Crashes`.
6. Zamknij companion (Ctrl+C).
7. Plugin możesz zostawić na sesję E5. Odinstalowanie działa tak samo jak w teście A.

## Co mi podać

- Test A: crash tak/nie.
- Test B: crash tak/nie.
- Czy companion pokazał połączenie albo błąd (wystarczy „było połączenie”).

Pliki odczytam sam:
- dzienniki pluginu i companiona z `%LOCALAPPDATA%\LektorPL\logs`;
- kopie `LogOutput.log` z `analysis/work/install/logs`;
- nowe foldery z `Crashes` (tylko odczyt).

Jak odczytam wynik:

| A | B | Wniosek |
|---|---|---|
| crash | crash | przyczyną jest loader (BepInEx 5 / Doorstop); plugin nie ma wpływu |
| brak | crash | przyczyną jest plugin mimo odpinania; szukam dalej w pluginie |
| brak | brak | odpinanie w 0.2.0 usunęło crash |
| crash | brak | wynik niespójny; powtarzamy oba testy |
