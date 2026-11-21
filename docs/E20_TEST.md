# E20: test okna podsumowania misji (Windows)

Test sprawdza panel statystyk (D114) w prawdziwym oknie podsumowania misji gry. Plugin 1.1.0 z gałęzi `feature/quest-summary`.

## Stan zapisów (2026-11-21)

Slot 2: Q1 w toku, runda 1, 6 ataków i 3 interakcje, 25 materiałów i 1 przepis. Kopia przed testem leży w `analysis/work/saves/slot2-20261121/` (10 plików, najnowszy `2026-11-21_10-32-05.sav`).

## 1. Nakładka

Zamknij grę i wgraj świeży build (kopia oryginałów z poprzedniej próby zostaje):

```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Descent Legendy Mroku - lektor\.claude\feature\quest-summary\src\plugin\install\nakladka-test.ps1" -Paczka "$env:USERPROFILE\Descent-Lektor-PL"
```

Wiersz `podsumowanie_podglad` w `ustawienia.toml` może zostać. Panel w oknie podsumowania pokazuje się bez niego.

## 2. W grze

1. Wczytaj slot 2 i dokończ Q1.
2. Gdy pojawi się okno podsumowania misji, zrób zrzut ekranu, zanim klikniesz „Dalej”. Jeśli łup się przewija, zrób też zrzut po przewinięciu.
3. Kliknij „Dalej”. Panel powinien zniknąć razem z oknem.
4. Jeśli możesz, przed kliknięciem „Dalej” przełącz grę w okno 16:10 (np. 1680×1050) i zrób drugi zrzut. Okno gry powinno się wtedy zmniejszyć, a panele zmieścić po bokach.

## 3. Co odesłać

- zrzuty okna podsumowania;
- uwagi: czytelność, co zasłania okno gry albo „Dalej”, czy liczby zgadzają się z oknem gry.

Dziennik pluginu i zapisy czytam sam z plików (`logs\hook-*.jsonl` w paczce, wiersze `quest_summary` i `summary_panel`).

## 4. Przywrócenie zapisu ręcznie

Zamknij grę. Gra wczytuje ze slotu najnowszy plik, więc trzeba usunąć zapisy z testu i oddać kopię:

```powershell
$slot = "E:\SteamLibrary\steamapps\common\Legends of the Dark\Legends of the Dark_Data\SavedGames\2"
Remove-Item "$slot\*" -Confirm:$false
Copy-Item "D:\Projects\Descent Legendy Mroku - lektor\analysis\work\saves\slot2-20261121\*" $slot
Get-ChildItem $slot | Select-Object Name, Length, LastWriteTime
```

Bez PowerShella:

1. Otwórz w Eksploratorze `E:\SteamLibrary\steamapps\common\Legends of the Dark\Legends of the Dark_Data\SavedGames\2` i usuń wszystkie pliki.
2. Skopiuj tam wszystkie pliki z `D:\Projects\Descent Legendy Mroku - lektor\analysis\work\saves\slot2-20261121`.
3. W slocie ma być 10 plików, najnowszy `2026-11-21_10-32-05.sav`.

Jeśli gra po starcie zapyta o konflikt zapisów w chmurze, wybierz wersję lokalną.

## 5. Powrót paczki

```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Descent Legendy Mroku - lektor\.claude\feature\quest-summary\src\plugin\install\nakladka-test.ps1" -Paczka "$env:USERPROFILE\Descent-Lektor-PL" -Przywroc
```
