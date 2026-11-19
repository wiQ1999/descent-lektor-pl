# Próba nakładki lektora w grze

Branch `feature/in-game-overlay`, plugin `0.5.0-nakladka`. Próba poza planem etapów: bez nowej paczki i bez pakowania zgłoszeń.

## Co jest w próbie

- **Skróty** (z Ctrl; przy Ctrl gra nie rusza kamerą):

  | Skrót | Działanie |
  |---|---|
  | Ctrl+= / Ctrl+− (też na klawiaturze numerycznej) | tempo lektora ±0,1 (0,8–1,6×, od następnej kwestii) |
  | Ctrl+M | wycisza albo włącza lektora |
  | Ctrl+R | powtarza ostatnią kwestię |
  | Ctrl+S | ucina bieżącą kwestię |
  | Ctrl+B | zgłoszenie błędu: zrzut ekranu, potem cyfra 1–6 (0 albo Backspace anuluje) |
  | Ctrl+L | menu lektora |

  Skróty można zmienić w `ustawienia.toml`, w sekcji `[skroty]`.
- **Komunikat** u góry ekranu po każdej akcji, np. „Tempo lektora 1,2×”.
- **Przycisk „PL”** na dolnym pasku, obok zębatki i drużyny. Otwiera menu lektora, które zawiera:
  - bieżącą kwestię z paskiem postępu;
  - przyciski Powtórz, Utnij i Wycisz;
  - tempo i głośność;
  - 10 ostatnich kwestii: ▶ odtwarza kwestię jeszcze raz, „Zgłoś” zgłasza błąd w tej kwestii;
  - 13 kategorii „Co czyta lektor”;
  - stan: zgłoszenia, okna bez nagrania, wersje.

  Zmiany tempa, głośności i kategorii zapisują się od razu w `ustawienia.toml`.
- **Zgłoszenia** trafiają do folderu `zgloszenia\<data-godzina>\` w paczce. Każde ma:
  - `ekran.png`;
  - `zgloszenie.json`: kategorię, kwestię z kluczami, głosem i fragmentami nagrań oraz ostatnie 60 s zdarzeń pluginu i companiona.

## Przygotowanie (Windows)

1. Zamknij grę.
2. W PowerShell w folderze tego worktree wgraj próbę do rozpakowanej paczki v0.4.0 (podaj jej ścieżkę):

   ```powershell
   powershell -ExecutionPolicy Bypass -File src/plugin/install/nakladka-test.ps1 -Paczka "<ścieżka>\Descent-Lektor-PL"
   ```

   Skrypt zapisuje oryginały w `stan\nakladka-kopia`. Powrót do nich: ten sam skrypt z `-Przywroc`.

## Co sprawdzić w grze

1. Na planszy misji na dolnym pasku jest przycisk „PL”. Jego wygląd i położenie pasują do zębatki i drużyny. Przycisk znika razem z paskiem.
2. Klik w „PL” otwiera menu, a drugi klik je zamyka. Otwarcie zębatki albo drużyny zwija menu lektora.
3. Klik w menu nie klika w planszę: nic się nie zaznacza i figurki się nie ruszają.
4. Tempo: Ctrl+= dwa razy. Następna kwestia jest szybsza i ma ten sam głos. Sprawdź też 1,6×.
5. Wyciszenie, powtórka, ucięcie: skrótem i z menu. Powtórka z historii (▶) gra wybraną kwestię.
6. Zgłoszenie: Ctrl+B w trakcie kwestii, potem cyfra. Drugie zgłoszenie: „Zgłoś” przy kwestii w historii. Sprawdź oba foldery w `zgloszenia\`. Zrzut nie powinien pokazywać menu.
7. Kategoria wyłączona w menu przestaje grać. Po ponownym uruchomieniu gry ustawienia zostają.
8. W mieście i na mapie świata: czy przycisk „PL” jest widoczny i nie zasłania innych elementów.

Po teście potrzebuję:
- zrzutów ekranu z przyciskiem i z menu;
- dzienników z `logs\` (`hook-*.jsonl` z wpisem `overlay_button`, `companion-*.jsonl`);
- folderu `zgloszenia\`.

## Próbki tempa

`analysis/work/compare/nakladka_tempo/`: narrator, Kehli i Syrus w tempie 1,0 / 1,2 / 1,4 / 1,6 (`<głos>_<tempo>.wav`).
