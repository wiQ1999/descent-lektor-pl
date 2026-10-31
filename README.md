# Lektor PL dla Descent: Legends of the Dark

Prywatny projekt polskiego lektora TTS do gry *Descent: Legends of the Dark* (Unity, Steam).
Docelowo: baza kwestii z plików gry + pregenerowane audio, odtwarzane w chwili wyświetlenia okna
(hook pod Mono albo OCR jako indeks do bazy). Szczegóły i uzasadnienie w [analysis/REPORT.md](analysis/REPORT.md).

## Układ folderów

```
docs/              PLAN.md (etapy), DECISIONS.md (decyzje i otwarte kwestie)
analysis/          analizy plików gry
  REPORT.md        lokalizacja tekstów, struktura kwestii, mówcy, statystyki, rekomendacja
  MAC_REPORT.md    build macOS (backend, podpis, różnice względem Windows)
  VOICES.md        próbki głosu z polskiego dubbingu, referencje do klonowania, płeć mówców
  M1_SCOPE.md      zakres milestone 1 (prolog + Q1)
  BENCH.md         benchmark generowania TTS
  E1_HOOK.md       test hooka w grze (pokrycie okien, luki, wydajność)
  tools/           skrypty analityczne (Python, UnityPy)
  work/            kopie plików gry, cache, wyniki pośrednie, audio — NIE jest śledzony w Git
src/
  plugin/          plugin do gry: rdzeń C# + adapter BepInEx + skrypt instalacji (docs/E1_PLAYTEST.md)
```

## Zasady

- Pliki gry i `%USERPROFILE%\AppData\LocalLow\...` są tylko do odczytu; analiza działa na kopiach w `analysis/work/`.
- Wyniki zawierające treść gry (teksty, audio, dekompilacja) są prywatne i nie trafiają do repozytorium.
- Repozytorium nie ma zdalnego `origin`.

## Uruchamianie narzędzi

Środowisko `.venv` leży w katalogu głównym (Python 3.13, Windows):

```bash
.venv/Scripts/python -I analysis/tools/extract_lines.py
.venv/Scripts/python -I analysis/tools/analyze.py
```
