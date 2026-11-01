# Lektor PL – Descent: Legends of the Dark

Prywatny polski lektor TTS do gry *Descent: Legends of the Dark* (Unity 2022.3.62f2, Mono, Wwise, Steam).

Docelowo:
- plugin w grze wysyła zdarzenia okien (klucz, argumenty, tekst, mówca) do lokalnego procesu companion;
- companion odtwarza pregenerowane audio sklonowanymi głosami z polskiego dubbingu.

Gramy na MacBooku Air M5 (arm64). Development robimy na Windows 11 z GTX 1650 Ti.

## Zasady pracy

- Plan etapów ustalamy w [docs/PLAN.md](docs/PLAN.md). Żaden etap nie startuje bez akceptacji użytkownika.
- Decyzje zapisujemy w [docs/DECISIONS.md](docs/DECISIONS.md) (data, decyzja, uzasadnienie).
- Kwestie do decyzji rozstrzygamy przez QA w `AskUserQuestion`:
  - 3–4 pytania na rundę;
  - rekomendacja jako pierwsza opcja, z krótkim uzasadnieniem;
  - gdy decyzja wymaga odsłuchu, najpierw przygotowujemy próbki i podajemy ścieżki do nich.
- Bez QA nie zmieniamy zakresu ani obsady głosów, nie ruszamy plików w folderze gry i niczego nie instalujemy w systemie.
- Po każdym etapie robimy commit.
- Gdy krok wymaga gry, przygotowujemy instrukcję dla użytkownika i czekamy na wynik.
- Pliki gry (`E:\SteamLibrary\steamapps\common\Legends of the Dark`) i `LocalLow` są tylko do odczytu; pracujemy na kopiach w `analysis/work/`.
- Treść gry (teksty, audio, dekompilacja, próbki TTS) jest prywatna. Nie commitujemy jej ani nie publikujemy; w raportach nie ma pełnych tekstów.
- Repozytorium jest lokalne: gałąź `main`, bez zdalnego `origin`. Logowanie do Steam (DepotDownloader) użytkownik robi sam.
- Wagi modeli i cache Hugging Face trzymamy w `analysis/work/hf_cache` (ignorowane w Git).

## Układ repozytorium

```
CLAUDE.md, README.md
docs/        PLAN.md (etapy), DECISIONS.md (decyzje i otwarte kwestie)
analysis/    raporty z analiz + tools/ (skrypty Python/UnityPy)
  work/      kopie gry, depot macOS, dekompilacja, audio, próbki: nieśledzone
src/         kod docelowy (plugin, pipeline, companion)
  plugin/    Core (C#, net472, bez Harmony i BepInEx), BepInEx (adapter), install/lektor-hook.ps1
```

## Komendy

Środowisko: `.venv` w katalogu głównym (Python 3.13, torch 2.6.0+cu124, chatterbox-tts 0.1.7).

```bash
.venv/Scripts/python -I analysis/tools/<skrypt>.py
.venv/Scripts/python -I analysis/tools/tts_bench.py --asr-only
```

Modele z porównania E0 mają własne środowiska w `%LOCALAPPDATA%\LektorPL\envs\<model>` (tworzy je `analysis/envs/create_envs.sh`). Wybrany model to OmniVoice (D33):

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/bakeoff_gen.py omnivoice [--only F01_A] [--force]
.venv/Scripts/python -I analysis/tools/bakeoff_eval.py [--page r2 --models omnivoice --variants A P1]
```

Plugin (referencje do DLL z kopii gry w `analysis/work/game`, wynik w `build/plugin/`):

```bash
dotnet build src/plugin/BepInEx -c Release
.venv/Scripts/python -I analysis/tools/hook_coverage.py [dziennik.jsonl ...]
```

Instalację i odinstalowanie w folderze gry (`lektor-hook.ps1 -Install|-Uninstall|-Status`) uruchamia użytkownik według `docs/E1_PLAYTEST.md`. Dzienniki pluginu: `%LOCALAPPDATA%\LektorPL\logs`.

- Python uruchamiamy z `-I`.
- Plugin nie woła getterów gry z leniwą inicjalizacją (np. `I2.Loc.LocalizationManager.CurrentLanguage`). Czyta pola przez refleksję, bo wcześniejsze wywołanie psuje start gry (E1_HOOK.md).
- OmniVoice potrzebuje referencji ciętych na granicach słów i transkrypcji z tego samego wycinka. Ucięta referencja sprawia, że model dopowiada jej końcówkę (BAKEOFF.md).
- Na GPU 4 GB po kondycjonowaniu Chatterboxa zdejmujemy z GPU tokenizer S3, CAMPPlus i VoiceEncoder (`offload_conditioning` w `tts_bench.py`). Bez tego model wychodzi poza VRAM i RTF rośnie do ok. 13.

## Raporty

| Raport | Zawartość |
|---|---|
| [analysis/REPORT.md](analysis/REPORT.md) | gdzie są teksty, struktura kwestii, mówcy, statystyki, warianty hooka |
| [analysis/MAC_REPORT.md](analysis/MAC_REPORT.md) | build macOS, podpis, sposób wczytania pluginu, hook bez Harmony |
| [analysis/VOICES.md](analysis/VOICES.md) | polski dubbing, referencje głosów, płeć mówców, tempo lektora |
| [analysis/M1_SCOPE.md](analysis/M1_SCOPE.md) | zakres milestone 1 (prolog + Q1) |
| [analysis/BENCH.md](analysis/BENCH.md) | Chatterbox na GTX 1650 Ti: VRAM, RTF, błędy, ekstrapolacja |
| [analysis/E1_HOOK.md](analysis/E1_HOOK.md) | test hooka w grze: pokrycie okien, argumenty, luki, wydajność, crashe |
| [analysis/BAKEOFF.md](analysis/BAKEOFF.md) | porównanie modeli TTS (E0): wydajność, CER, podobieństwo, odsłuch, tempo i akcent OmniVoice |
