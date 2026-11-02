# E5 · Sesja M1 z lektorem (Windows)

Plugin 0.2.0 wysyła okna gry do companiona, a companion czyta je pregenerowanym audio M1 (978 fragmentów, OmniVoice). Ta sesja sprawdza D13 w prawdziwej grze:
- audio w co najmniej 98% okien (bez okien samego łupu, D50);
- start poniżej 0,5 s;
- przerwanie poniżej 0,3 s.

Liczą się też Twoje wrażenia.

## 0. Najpierw testy wyjścia

Zrób dwa krótkie testy z [E4_EXIT_TEST.md](E4_EXIT_TEST.md) (D40). Jeśli po teście B plugin został zainstalowany, pomiń krok 1.

## 1. Instalacja (gra zamknięta)

```powershell
powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-hook.ps1 -Install
```

Po instalacji `lektor-hook.ps1` bez parametrów powinien pokazać „Plugin: 0.2.0…”.

## 2. Companion przed grą

W osobnym oknie PowerShella, w katalogu repozytorium:

```powershell
powershell -ExecutionPolicy Bypass -File src\plugin\install\lektor-companion.ps1
```

- Okno zostaw otwarte przez całą sesję. W konsoli widać klucze kolejnych okien, bez tekstów.
- Przy pierwszym starcie companion tworzy `%LOCALAPPDATA%\LektorPL\companion.toml`:
  - `volume`: głośność lektora od 0.0 do 1.0;
  - `device`: urządzenie wyjściowe, puste oznacza domyślne. Listę urządzeń pokazuje `.venv\Scripts\python -m sounddevice`;
  - `[toggles]`: 9 kategorii; `false` wycisza kategorię (D21).
- Po zmianie pliku zatrzymaj companion (Ctrl+C) i uruchom go ponownie. Plugin połączy się sam w ciągu 2 s.
- Głośność możesz też zmienić w mikserze głośności Windows (pozycja `python`).

## 3. Rozgrywka

Uruchom grę ze Steama. Zagraj w nowej kampanii (najlepiej w nowym slocie zapisu): prolog, Q1 i scena „Welcome Home” w mieście.

Żeby sprawdzić zasady odtwarzania:
- **Tempo:** zwykle słuchaj do końca. Kilka razy kliknij dalej w trakcie czytania (przerwanie).
- **Wybory:** wybieraj też opcje z cytatem bohatera. Po wyborze odpowiedź bohatera powinna zabrzmieć do końca, a następne okno zaczekać (D48).
- **Wstecz:** co najmniej raz cofnij się przyciskiem „wstecz”.
- **Cel misji:** po zmianie celu lektor czyta go po bieżącej kwestii.
- **Aktywacja wroga:** lektor czyta ją po bieżącej kwestii (D45). Gdy zamkniesz okno aktywacji wcześniej, odczyt przepada.
- **Łup:** listy łupu nie są czytane (D49–D51). Tak ma być.

Zapisz dla mnie (bez przepisywania treści, wystarczy np. „okno po walce z bossem”):
- okna, które powinny być czytane, a były ciche;
- zły głos, przekręcone słowa, ucięte końcówki (D43);
- audio za późno, nakładanie się albo ucinanie w złym momencie;
- głośność lektora względem gry i kategorie do wyciszenia;
- przycięcia, zawieszenia, crash.

W trakcie Twojej sesji nie uruchamiam obliczeń na GPU.

## 4. Koniec

1. Zapisz grę, wyjdź do menu i zamknij grę. Daj znać, czy przy wyjściu był crash.
2. W oknie companiona naciśnij Ctrl+C. Companion dopisze podsumowanie do swojego dziennika.
3. Plugin zostaw zainstalowany do zamknięcia E5, bo po poprawkach może być druga sesja. Odinstalowanie działa jak w [E1_PLAYTEST.md](E1_PLAYTEST.md) (`-Uninstall`).

Napisz „zrobione” i podeślij notatki. Dzienniki odczytam sam z `%LOCALAPPDATA%\LektorPL\logs`: `hook-*.jsonl` z pluginu i `companion-*.jsonl`.

## 5. Co dalej robię ja

W raporcie `analysis/E5_TEST.md` (bez treści gry):
- pokrycie okien;
- opóźnienia: plugin, TCP i companion;
- braki według kluczy;
- przerwane i oczekujące odczyty.

Potem poprawki, przyrostowa regeneracja audio i ewentualnie druga sesja.
