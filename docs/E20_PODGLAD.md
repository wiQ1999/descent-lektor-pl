# E20: podgląd panelu podsumowania misji (Windows)

Szybki test wyglądu panelu statystyk (D114) w trakcie misji, bez jej kończenia. Plugin 1.1.0 z gałęzi `feature/quest-summary`.

Podgląd pokazuje panel nad planszą, z ramką w miejscu okna podsumowania gry. Okna gry nie otwiera i niczego w grze nie zmienia.

## 1. Podmiana pluginu w paczce

Zamknij grę. W PowerShellu (z dowolnego folderu, pełna ścieżka do skryptu z worktree):

```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Descent Legendy Mroku - lektor\.claude\feature\quest-summary\src\plugin\install\nakladka-test.ps1" -Paczka "$env:USERPROFILE\Descent-Lektor-PL"
```

Skrypt kopiuje oryginały do `stan\nakladka-kopia` w paczce i na końcu wypisuje `rdzeń 1.1.0.0`. Skrypt z głównego folderu repozytorium wgrywa stary rdzeń bez panelu.

Po starcie gry pierwszy wiersz najnowszego `logs\hook-*.jsonl` ma `"plugin":"1.1.0"`.

## 2. Włączenie podglądu

W `ustawienia.toml` paczki, w sekcji `[podsumowanie]`, dopisz wiersz:

```toml
podglad = true
```

## 3. W grze

1. Wczytaj zapis z trwającej misji, najlepiej po kilku atakach i z łupem (np. Q6 albo Q2).
2. Naciśnij **Ctrl+P**. Panel pojawia się nad planszą, a w środku stoi ramka okna gry.
3. Zrób zrzut ekranu (`Win+Shift+S` albo `PrtSc`).
4. Naciśnij **Ctrl+P** jeszcze raz, żeby zamknąć podgląd.
5. Jeśli możesz, przełącz grę w tryb okienkowy o proporcjach 16:10 (np. 1680×1050) i powtórz kroki 2–4.

## 4. Co odesłać

- zrzuty ekranu z podglądu;
- najnowszy dziennik pluginu z folderu `logs` paczki (wiersze `quest_summary_preview` i `summary_panel`);
- uwagi do wyglądu: czytelność, rozmiary, kolory, co się nie mieści.

## 5. Powrót

```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Descent Legendy Mroku - lektor\.claude\feature\quest-summary\src\plugin\install\nakladka-test.ps1" -Paczka "$env:USERPROFILE\Descent-Lektor-PL" -Przywroc
```

Wiersz `podglad` usuń z sekcji `[podsumowanie]` w `ustawienia.toml` albo ustaw na `false`.
