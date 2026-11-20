# E20: podgląd panelu podsumowania misji (Windows)

Szybki test wyglądu panelu statystyk (D113) w trakcie misji, bez jej kończenia. Plugin 0.6.0 z gałęzi `feature/quest-summary`.

Podgląd pokazuje panel nad planszą, z ramką w miejscu okna podsumowania gry. Okna gry nie otwiera i niczego w grze nie zmienia.

## 1. Podmiana pluginu w paczce

Zamknij grę. W PowerShellu, w folderze worktree `D:\Projects\Descent Legendy Mroku - lektor\.claude\feature\quest-summary`:

```powershell
powershell -ExecutionPolicy Bypass -File src/plugin/install/nakladka-test.ps1 -Paczka "$env:USERPROFILE\Descent-Lektor-PL"
```

Skrypt kopiuje oryginały do `stan\nakladka-kopia` w paczce.

## 2. Włączenie podglądu

W `ustawienia.toml` paczki, w sekcji `[plugin]`, dopisz wiersz:

```toml
podsumowanie_podglad = true
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
powershell -ExecutionPolicy Bypass -File src/plugin/install/nakladka-test.ps1 -Paczka "$env:USERPROFILE\Descent-Lektor-PL" -Przywroc
```

Wiersz `podsumowanie_podglad` usuń z `ustawienia.toml` albo ustaw na `false`.
