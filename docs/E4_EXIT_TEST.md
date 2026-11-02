# E4 · Testy wyjścia z gry (przed E5, D40, D53, D54)

W E1 gra z loaderem 2 z 2 razy kończyła się crashem przy wyjściu do pulpitu (`mono_jit_cleanup`). Bez moda zamyka się czysto. Testy A i B pokażą, czy crash wywołuje sam BepInEx, czy nasz plugin. Plugin 0.2.0 przy wyjściu odpina subskrypcje i zamyka połączenie z companionem.

Wyniki:
- A: bez crasha;
- B: crash;
- C: crash już na etapie 0;
- D (poprawka MonoMod, D54): bez crasha.

`-Install` nakłada teraz poprawkę domyślnie.

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

## Test C: etapy pluginu 0.2.1 (po crashu w teście B)

Test A (sam BepInEx) przeszedł bez crasha, a test B (plugin 0.2.0) skończył się crashem w `mono_domain_free`. Plugin 0.2.1 ma ustawienie `Stage`, które włącza kolejne części pluginu:

| Etap | Co działa |
|---|---|
| 0 | BepInEx wczytuje plugin, plugin nic nie robi |
| 1 | ukryty obiekt gry z pustym Runnerem |
| 2 | + dziennik `hook-*.jsonl` |
| 3 | + Tracker: subskrypcje okien i odczyt pól gry, bez wysyłki do companiona |
| 4 | całość (domyślnie, jak w teście B) |

Companion nie jest potrzebny.

1. Zainstaluj plugin 0.2.1 z etapem 0 (gra zamknięta):

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Uninstall
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install -Stage 0
   ```

2. Uruchom grę ze Steama, poczekaj ok. 30 s w menu i wyjdź do pulpitu. Zanotuj, czy był crash.
3. Bez crasha ustaw kolejny etap (gra zamknięta) i powtórz krok 2:

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Stage 1
   ```

   Potem tak samo `-Stage 2` i `-Stage 3`. Przerwij na pierwszym etapie z crashem.
4. Na koniec przywróć całość: `-Stage 4`. `lektor-hook.ps1` bez parametrów pokaże wersję 0.2.1 i etap.

Jak odczytam wynik:

| Pierwszy crash | Wniosek |
|---|---|
| etap 0 | crash wywołuje samo wczytanie pluginu przez BepInEx; nasz kod nie ma wpływu |
| etap 1 | ukryty obiekt (`HideAndDontSave`, `DontDestroyOnLoad`); Runner przeniosę na obiekt pluginu |
| etap 2 | plik dziennika |
| etap 3 | Tracker (subskrypcje, odczyt pól); zawężam dalej w Trackerze |
| brak do etapu 3 | wysyłka do companiona; ale 0.1.0 bez wysyłki też miał crash, więc powtórzymy etap 3 |

Wynik: crash już na etapie 0. Crash wywołuje samo wczytanie pluginu przez BepInEx.

## Test D: poprawka MonoMod, plugin na etapie 4 (D54)

Przyczyną jest błąd w `MonoMod.Utils.dll` z BepInEx 5.4.23.5 (MonoMod #329):
- w 32-bitowej grze ta biblioteka zapisuje bajt w złe pole struktury Mono;
- przy wyjściu Mono zwalnia uszkodzony w ten sposób wskaźnik.

Przygotowałem kopię biblioteki, która pomija ten zapis; poza tym jest identyczna z oryginałem. Leży w `analysis/work/bin/BepInEx-5.4.23.5/monomod-fix/` (tworzy ją `monomod-fix.ps1`). Skrypt sprawdza sumę SHA-256 kopii i oryginału przed podmianą. Odinstalowanie usuwa ją razem z całym BepInEx.

1. Podmień bibliotekę i włącz cały plugin (gra zamknięta):

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -MonoModFix -Stage 4
   ```

   Oczekiwane: „MonoMod.Utils.dll: podmieniono na kopię z poprawką D54…” i „Etap diagnostyczny pluginu: 4”.
2. W osobnym oknie uruchom companion (jak w teście B, krok 3).
3. Uruchom grę ze Steama, poczekaj ok. 30 s w menu i wyjdź do pulpitu. Zanotuj, czy pojawiło się okno crasha i czy w `Crashes` przybył folder.
4. Zamknij companion (Ctrl+C). Plugin zostaw na sesję E5.

`lektor-hook.ps1` bez parametrów pokaże „MonoMod.Utils.dll: z poprawką D54” i „Etap diagnostyczny: 4”.

| Wynik | Dalej |
|---|---|
| brak crasha | `-Install` nakłada poprawkę domyślnie, potem sesja E5; wyjście po sesji będzie drugim sprawdzeniem |
| crash | akceptujemy crash przy wyjściu i przechodzimy do sesji E5 |

Wynik 2026-11-02: bez crasha. Plugin pracował na etapie 4 z companionem; w `Crashes` nie przybył folder.

## Co mi podać

- Test A: crash tak/nie.
- Test B: crash tak/nie.
- Test C: etapy bez crasha i pierwszy etap z crashem.
- Test D: crash tak/nie.
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
