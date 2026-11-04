# E6 · Sesja na Macu

Sesja sprawdza paczkę na MacBooku Air M5. Sprawdzamy:
- instalację według instrukcji;
- pełną sesję M1 z lektorem;
- wyjście z gry;
- wyłączenie i odinstalowanie.

Instalacja trwa ok. 15 minut, potem gracie M1 przy stole.

Skryptów Maca nie dało się tu uruchomić na prawdziwym macOS. Sprawdziłem je na atrapach poleceń systemowych. Pierwsze uruchomienie może więc trafić na błąd, którego atrapy nie pokazały. Wtedy zrób zrzut ekranu okna Terminala (Cmd+Shift+4, spacja, klik w okno) i przerwij. Poprawię paczkę.

## 1. Przygotowanie na Windows

1. Skopiuj `analysis\work\dist\Descent-Lektor-PL-mac.zip` (328 MB) na pendrive. Wystarczy system plików FAT32 albo exFAT.
2. Zip zawiera audio z gry. Nie wysyłaj go dalej i po sesji usuń go z pendrive'a.

## 2. Przed instalacją na Macu

1. W Steam poczekaj na koniec aktualizacji gry. Potem uruchom ją raz bez lektora i wyjdź.
   - Aktualizacja po instalacji przywraca oryginalny podpis gry. Gra wystartuje wtedy bez lektora i pokaże komunikat.
2. Ustaw w macOS wyjście dźwięku, którego użyjecie przy stole.

## 3. Instalacja według instrukcji

Rozpakuj zip i otwórz `INSTRUKCJA.md` z folderu paczki. W Finderze podgląd otwiera spacja. Przejdź sekcję **Mac → Instalacja** (kroki 1–6) i zanotuj:
- czy macOS zablokował `Zainstaluj.command` i co trzeba było kliknąć;
- czy skrypt sam znalazł grę;
- czy macOS pytał o *Zarządzanie aplikacjami* i czy trzeba było uruchomić skrypt drugi raz;
- czy *Test dźwięku* zabrzmiał.

## 4. Sesja M1

1. Uruchom grę przyciskiem *Graj* w Steam.
2. Zagrajcie prolog i pierwszy scenariusz (M1), jak w E5. Zapisuj uwagi tak jak w E5:
   - okna bez lektora;
   - zły głos;
   - opóźnienia;
   - przycięcia.
3. Wyjdź z gry do pulpitu z menu gry.
4. Otwórz *Monitor aktywności* i wpisz `python` w polu wyszukiwania. Proces powinien zniknąć do 15 s po wyjściu z gry.

## 5. Wyłączanie

1. Kliknij dwukrotnie `Wyłącz lektora.command`.
2. Uruchom grę. Lektor powinien milczeć, wystarczy menu główne. Wyjdź z gry.
3. Kliknij dwukrotnie `Włącz lektora.command`.

## 6. Dzienniki

Skopiuj na pendrive:
1. Z folderu `~/Descent-Lektor-PL`: folder `logs` i plik `wersja.txt`.
2. Folder z dziennikami Unity: `~/Library/Logs/Fantasy Flight Games/Descent - Legends of the Dark`. W Finderze wybierz *Idź → Idź do folderu* i wklej tę ścieżkę.
3. Jeśli gra się wysypała, dodaj najnowsze pliki z nazwą gry z `~/Library/Logs/DiagnosticReports`.

Na Windows wrzuć je do `analysis\work\e6-mac\`.
- Folder `analysis\work` jest wykluczony z Git.
- Dzienniki zawierają fragmenty tekstów z gry.

## 7. Odinstalowanie

1. Przejdź sekcję **Mac → Odinstalowanie**, kroki 1–4. Folder paczki możesz zostawić.
2. Uruchom grę ze Steama. Powinna działać normalnie, bez lektora.
3. Opcjonalnie sprawdź podpis gry w Terminalu na Macu:

   ```bash
   codesign -dv ~/Library/Application\ Support/Steam/steamapps/common/Legends\ of\ the\ Dark/*.app 2>&1 | grep -E 'Authority|Signature'
   ```

   - Po weryfikacji plików w Steam pokaże `Authority=Developer ID Application`.
   - Przy zainstalowanym lektorze pokazuje `Signature=adhoc`.
   - Gra może leżeć w innej bibliotece Steama. Wtedy podmień początek ścieżki.

Żeby dalej grać z lektorem, uruchom ponownie `Zainstaluj.command` i wklej opcję uruchamiania w Steam.

## 8. Wynik

Napisz mi:
- czy każdy krok zadziałał:
  - blokada pliku;
  - wykrycie gry;
  - *Zarządzanie aplikacjami*;
  - Test dźwięku;
  - lektor w grze;
  - wyjście z gry i zamknięcie Pythona;
  - wyłączenie;
  - odinstalowanie;
- uwagi z sesji M1;
- które miejsca instrukcji były niejasne albo czego w niej brakowało;
- czy dzienniki są już w `analysis\work\e6-mac\`.
