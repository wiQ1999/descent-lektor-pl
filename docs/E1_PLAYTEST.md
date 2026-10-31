# E1 · Sesja testowa hooka (Windows)

Plugin w tej wersji niczego nie czyta na głos: okna fabularne będą ciche, tak jak w grze bez moda (dubbing mają tylko przerywniki). Zapisuje tylko okna wiadomości do dziennika, żeby sprawdzić pokrycie (cel ≥ 98% okien, D13). Loader to BepInEx 5.4.23.5 x86 (D11), pobrany z oficjalnego wydania na GitHubie i sprawdzony sumą SHA-256.

## 1. Instalacja (gra zamknięta)

W PowerShellu, w katalogu repozytorium:

```powershell
powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install
```

Skrypt:
- odmówi pracy, gdy gra jest uruchomiona albo w folderze gry są już pliki loadera;
- zapisze listę plików gry przed i po instalacji w `analysis/work/install/`;
- wypisze różnice. Oczekiwane: około 25 dodanych plików (`winhttp.dll`, `doorstop_config.ini`, `.doorstop_version`, `BepInEx\…`), 0 usuniętych i 0 zmienionych.

Plugin trzeba przebudować tylko po zmianach w kodzie: `dotnet build src\plugin\BepInEx -c Release`.

## 2. Sprawdzenie startu

1. Uruchom grę normalnie ze Steama.
2. Gdy pojawi się menu, w drugim oknie PowerShella:

   ```powershell
   powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1
   ```

   Powinien pokazać „Najnowszy dziennik pluginu: …\LektorPL\logs\hook-….jsonl”.
3. Jeśli dziennika nie ma, zamknij grę i podeślij mi plik `E:\SteamLibrary\steamapps\common\Legends of the Dark\BepInEx\LogOutput.log`.

## 3. Rozgrywka

Zagraj w nowej kampanii (najlepiej w nowym slocie zapisu): prolog, Q1 do końca, potem scena „Welcome Home” w mieście.

Żeby log pokrył różne przypadki:
- **Okna fabularne:** przeczytaj każde i przejdź dalej. Co najmniej raz cofnij się przyciskiem „wstecz”.
- **Wybory:** wybieraj różne opcje (w tym te z cytatem bohatera w cudzysłowie). Jeśli kiedyś powtórzysz scenę, wybierz inaczej.
- **Q1:**
  - graj normalnie: ruch, przeszukiwanie i interakcje z żetonami, walka, kilka końców rundy;
  - otwórz raz dziennik questu i kartę bohatera;
  - nie pomijaj samouczków.
- **Na koniec:** zapisz grę i wyjdź do menu (gra dopisuje wtedy `.qlog`, z którym porównuję dziennik), potem zamknij grę.
  - Crash przy samym wyjściu do pulpitu (okno raportu Unity po zamknięciu) już znam. Zapisy i dziennik są wtedy zapisane, wystarczy, że dasz znać, czy wystąpił.

Zapisz dla mnie:
- skład drużyny;
- czy wystąpiły przycięcia, zawieszenia albo crash (przybliżona chwila i co się działo);
- okna, które wydały Ci się nietypowe (bez przepisywania treści, wystarczy np. „okno po walce z bossem”).

W trakcie Twojej sesji nie uruchamiam obliczeń na GPU, żeby nie zafałszować pomiaru płynności.

## 4. Odinstalowanie (gra zamknięta)

```powershell
powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Uninstall
```

Skrypt:
- kopiuje `LogOutput.log` do `analysis/work/install/logs/`;
- usuwa wyłącznie pliki dodane przy instalacji;
- porównuje folder gry ze stanem sprzed instalacji. Oczekiwane: brak różnic poza `Legends of the Dark_Data\SavedGames\…` (Twoje zapisy).

Wklej mi wynik albo napisz „zrobione”: listy plików zostają w `analysis/work/install/`, a dziennik pluginu w `%LOCALAPPDATA%\LektorPL\logs\` (po odinstalowaniu nadal tam jest).

## 5. Co dalej robię ja

```powershell
.venv\Scripts\python -I analysis\tools\hook_coverage.py
```

Wynik bez treści gry trafi do `analysis/E1_HOOK.md`:
- pokrycie okien względem `.qlog` i zakresu M1;
- zamknięcia i wybory;
- opóźnienie pokazania okien fabularnych;
- argumenty `{n}` i wrogowie z losowania;
- rozwiązanie `VARIABLE_HERO`;
- wydajność i błędy.
