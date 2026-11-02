# E6 · Test W1: własny loader i autostart companiona (Windows)

Test sprawdza nowy sposób uruchamiania lektora (D58, D59):
- Doorstop 4.6 i `LektorPL.Loader.dll` zamiast BepInEx;
- companion uruchamia plugin, bez ręcznego okna PowerShella;
- companion kończy się sam po zamknięciu gry.

Używasz paczki deweloperskiej `analysis\work\dev-bundle`. Ma ten sam układ i te same pliki do dwukliku co docelowa paczka, ale bazę i audio bierze z repozytorium, a Pythona z `.venv`. Test trwa ok. 5 minut.

Przed testem sprawdź, ile folderów jest w `%TEMP%\Fantasy Flight Games\Descent - Legends of the Dark\Crashes`.

## 1. Usunięcie BepInEx (gra zamknięta)

Zamknij okno companiona z E5, jeśli jest otwarte. W katalogu repozytorium uruchom:

```powershell
powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Uninstall
```

Na końcu skrypt powinien pokazać brak różnic względem stanu sprzed instalacji, poza zapisami gry.

## 2. Instalacja z paczki deweloperskiej

1. Otwórz w Eksploratorze folder `analysis\work\dev-bundle`.
2. Kliknij dwukrotnie `Zainstaluj.cmd`. Skrypt sam znajdzie grę w Steam i powinien pokazać 3 dodane pliki: `winhttp.dll`, `doorstop_config.ini` i `.doorstop_version`.
3. Kliknij dwukrotnie `Test dźwięku.cmd`. Powinna zabrzmieć jedna kwestia narratora.

## 3. Gra

1. Uruchom grę zwykłym przyciskiem w Steam. Nie uruchamiaj companiona ręcznie.
2. Zacznij prolog w nowym slocie albo wczytaj zapis i przejdź kilka okien fabularnych. Lektor powinien czytać jak w E5.
   - Pierwsze okno może zabrzmieć z opóźnieniem do kilku sekund, bo companion dopiero startuje.
3. Wyjdź do pulpitu z menu gry.
4. Odczekaj ok. 20 s. Companion powinien sam się zamknąć: w Menedżerze zadań nie powinno być procesu `python` (poza innymi programami w Pythonie, jeśli jakieś działają).

## 4. Wynik

Napisz mi:
- czy lektor czytał i od którego okna;
- czy gra startowała i działała tak jak z BepInEx;
- czy przy wyjściu pojawił się raport crasha albo nowy folder w `Crashes`;
- czy po ok. 20 s od wyjścia zniknął proces `python`.

Dzienniki odczytam sam z `analysis\work\dev-bundle\logs`:
- `loader-*.log`: wczytanie modułu Unity, pierwsza scena, start rdzenia;
- `hook-*.jsonl`: uruchomienie companiona (`launch`) i połączenie;
- `companion-*.jsonl`: odczyty i powód zakończenia.

## Gdy coś nie działa

- **Lektor milczy:** gra działa normalnie, a loader zapisuje błędy tylko do `logs\loader-*.log`. Napisz mi, a ja przejrzę dzienniki.
- **Gra nie startuje albo się wysypuje:** kliknij dwukrotnie `Wyłącz lektora.cmd` (gra wystartuje bez lektora) albo `Odinstaluj.cmd`.
- **Powrót do BepInEx:** najpierw `Odinstaluj.cmd`, potem `lektor-hook.ps1 -Install`.
