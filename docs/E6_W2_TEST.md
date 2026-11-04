# E6 · Test W2: instalacja z paczki (Windows)

Test sprawdza paczkę tak, jak dostanie ją znajomy: sam zip i instrukcja, bez repozytorium i bez `.venv`. Sprawdzamy też, czy instrukcja jest jasna. Test trwa ok. 15 minut.

## 1. Usunięcie instalacji z W1 (gra zamknięta)

Kliknij dwukrotnie `analysis\work\dev-bundle\Odinstaluj.cmd`. Skrypt powinien pokazać brak różnic w folderze gry, poza zapisami gry.

## 2. Rozpakowanie paczki

1. Skopiuj `analysis\work\dist\Descent-Lektor-PL-win.zip` w miejsce poza repozytorium, np. do `C:\Gry\`.
2. Rozpakuj go w Eksploratorze: prawy przycisk, *Wyodrębnij wszystkie*. Powstanie folder `Descent-Lektor-PL`.

## 3. Według instrukcji

Otwórz `INSTRUKCJA.md` z rozpakowanego folderu i przejdź sekcję **Windows**, korzystając tylko z niej:
1. **Instalacja:** `Zainstaluj.cmd` i `Test dźwięku.cmd`.
2. **Ustawienia:** zmień `volume` na `0.6`, zapisz i uruchom Test dźwięku. Głos powinien być cichszy. Potem przywróć `1.0`.
3. **Granie:** uruchom grę ze Steama, wczytaj zapis, przejdź kilka okien i wyjdź do pulpitu.
4. **Wyłączanie:** `Wyłącz lektora.cmd`, uruchom grę (lektor powinien milczeć) i wyjdź. Potem `Włącz lektora.cmd`.
5. **Odinstalowanie:** `Odinstaluj.cmd`. Skrypt powinien pokazać brak różnic w folderze gry, poza zapisami gry.

Po teście możesz zainstalować lektora ponownie (`Zainstaluj.cmd`), żeby grać z nim dalej.

## 4. Wynik

Napisz mi:
- gdzie rozpakowano paczkę (ścieżka folderu), bo stamtąd odczytam dzienniki z `logs\`;
- czy każdy krok zadziałał (SmartScreen, wykrycie gry, Test dźwięku, lektor w grze, wyłączenie, odinstalowanie);
- które miejsca instrukcji były niejasne albo czego w niej brakowało.
