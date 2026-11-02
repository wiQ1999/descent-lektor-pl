# Lektor PL – Descent: Legends of the Dark

Prywatny polski lektor TTS do gry *Descent: Legends of the Dark* (Unity 2022.3.62f2, Mono, Wwise, Steam).

Docelowo:
- plugin w grze wysyła zdarzenia okien (klucz, argumenty, tekst, mówca) do lokalnego procesu companion;
- companion odtwarza pregenerowane audio sklonowanymi głosami z polskiego dubbingu.

Gramy na MacBooku Air M5 (arm64). Development robimy na Windows 11 z GTX 1650 Ti.

## Zasady pracy

- Plan etapów ustalamy w [docs/PLAN.md](docs/PLAN.md). Żaden etap nie startuje bez akceptacji użytkownika.
- Decyzje zapisujemy w [docs/DECISIONS.md](docs/DECISIONS.md) (data, decyzja, uzasadnienie).
- Obsadę głosów zapisujemy w [docs/CASTING.md](docs/CASTING.md). Głos NPC projektujemy od portretu postaci z plików gry (D41), a kandydaci do QA mają się wyraźnie różnić.
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
docs/        PLAN.md (etapy), DECISIONS.md (decyzje i otwarte kwestie), CASTING.md (obsada głosów)
analysis/    raporty z analiz + tools/ (skrypty Python/UnityPy)
  work/      kopie gry, depot macOS, dekompilacja, audio, próbki: nieśledzone
src/         kod docelowy (plugin, pipeline, companion)
  lektor/    pakiet Python: baza kwestii M1 (build), referencje (refs), raporty (report), audio E3 (synth, evaluate, finalize),
             companion/ (E4: library, director, player, app)
  plugin/    Core (C#, net472, bez Harmony i BepInEx), BepInEx (adapter), install/ (lektor-hook.ps1, lektor-companion.ps1, monomod-fix.ps1)
tests/       pytest dla src/lektor (zdania testowe własne, bez tekstów gry)
```

## Komendy

Środowisko: `.venv` w katalogu głównym (Python 3.12, torch 2.6.0+cu124, chatterbox-tts 0.1.7, pakiet `lektor` zainstalowany w trybie edytowalnym). Bazowy Python `.venv` leży w `analysis/work/python` (D52).

- Aplikacja Claude działa jako pakiet MSIX. To, co nasze narzędzia zapisują w `%LOCALAPPDATA%`, trafia do `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local` i jest niewidoczne poza aplikacją.
  - Wszystko, czego użytkownik albo gra używa poza aplikacją, trzymamy na D: (w repozytorium).
  - Pliki tworzone przez grę albo użytkownika (dzienniki pluginu, `companion.toml`) widzimy normalnie.
  - Środowiska modeli E0 (`%LOCALAPPDATA%\LektorPL\envs`) działają tylko w aplikacji.

```bash
.venv/Scripts/python -I analysis/tools/<skrypt>.py
.venv/Scripts/python -I analysis/tools/tts_bench.py --asr-only
```

Pipeline danych (E2). Baza i referencje lądują w `analysis/work/lektor/` (prywatne):

```bash
.venv/Scripts/python -I -m lektor build      # baza kwestii M1 z kopii gry (m1.sqlite)
.venv/Scripts/python -I -m lektor refs       # referencje głosów do 10 s z transkrypcją (Whisper, GPU)
.venv/Scripts/python -I -m lektor report     # raport liczności analysis/E2_DATA.md
.venv/Scripts/python -I -m pytest -q
```

Modele z porównania E0 mają własne środowiska w `%LOCALAPPDATA%\LektorPL\envs\<model>` (tworzy je `analysis/envs/create_envs.sh`). Wybrany model to OmniVoice (D33):

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/bakeoff_gen.py omnivoice [--only F01_A] [--force]
.venv/Scripts/python -I analysis/tools/bakeoff_eval.py [--page r2 --models omnivoice --variants A P1]
```

Audio M1 (E3). Generowanie w środowisku OmniVoice (pakiet `lektor` zainstalowany tam w trybie edytowalnym), ocena w `.venv`. Wyniki w `analysis/work/audio/m1/` (prywatne); każdy krok jest wznawialny:

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I -m lektor generate [--limit N] [--voices narrator] [--retake]
.venv/Scripts/python -I -m lektor evaluate     # ASR, barwa, tempo -> evals.jsonl
.venv/Scripts/python -I -m lektor select       # choice.json, retake.json
.venv/Scripts/python -I -m lektor finalize     # final/*.wav, manifest.json, listen/index.html
.venv/Scripts/python -I -m lektor audio-report # analysis/E3_AUDIO.md
```

Plugin (referencje do DLL z kopii gry w `analysis/work/game`, wynik w `build/plugin/`):

```bash
dotnet build src/plugin/BepInEx -c Release
.venv/Scripts/python -I analysis/tools/hook_coverage.py [dziennik.jsonl ...]
powershell -ExecutionPolicy Bypass -File src/plugin/install/monomod-fix.ps1   # MonoMod.Utils.dll bez zapisu corlib_internal (D54)
```

Instalację i odinstalowanie w folderze gry (`lektor-hook.ps1 -Install [-LoaderOnly] [-Stage N] [-MonoModFix]|-Uninstall|-Status|-Stage N|-MonoModFix`) uruchamia użytkownik według `docs/E1_PLAYTEST.md` i `docs/E4_EXIT_TEST.md`. Dzienniki pluginu i companiona: `%LOCALAPPDATA%\LektorPL\logs`.

Companion (E4). Konfiguracja w `%LOCALAPPDATA%\LektorPL\companion.toml` (tworzona przy pierwszym starcie). W grze użytkownik uruchamia go skryptem `src/plugin/install/lektor-companion.ps1`:

```bash
.venv/Scripts/python -I -m lektor companion                      # serwer TCP 127.0.0.1:47810 dla pluginu
.venv/Scripts/python -I -m lektor companion --replay <hook.jsonl ...> [--tcp] [--speed 0] [--no-audio] [--config plik.toml] [--out wynik.json]
```

- Replay z `--speed 0 --no-audio` sprawdza samo pokrycie. Opóźnienia mierzymy w czasie rzeczywistym (`--tcp`, wyjście audio wyciszone w configu `volume = 0.0`).

- Python uruchamiamy z `-I`.
- `analysis/tools/normalize_pl.py` to nakładka na `lektor.normalize`; skrypty E0 wymagają pakietu `lektor` w `.venv`.
- Wypisywanie tekstów gry (np. `normalize_pl.py --m1`) zostawiamy na pliki w `analysis/work/`, nie na konsolę.
- Plugin nie woła getterów gry z leniwą inicjalizacją (np. `I2.Loc.LocalizationManager.CurrentLanguage`). Czyta pola przez refleksję, bo wcześniejsze wywołanie psuje start gry (E1_HOOK.md).
- OmniVoice potrzebuje referencji ciętych na granicach słów i transkrypcji z tego samego wycinka. Ucięta referencja sprawia, że model dopowiada jej końcówkę (BAKEOFF.md).
- OmniVoice na GTX 1650 Ti liczymy w fp32 (karta bez rdzeni tensorowych: fp16 jest ok. 5,5× wolniejsze), z tokenizerem audio przeniesionym na CPU po zakodowaniu referencji i gałęzią CFG bez dopełniania (`lektor.synth`).
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
| [analysis/E2_DATA.md](analysis/E2_DATA.md) | baza kwestii M1 (E2): liczności, luki `{n}` i ich wartości, pokrycie wartości z E1, szacunek E3 |
| [analysis/E3_AUDIO.md](analysis/E3_AUDIO.md) | audio M1 (E3): czas generowania na znak, wyniki automatu, odsłuch, pokrycie kluczy, koszt całej gry |
| [analysis/E4_COMPANION.md](analysis/E4_COMPANION.md) | companion i plugin 0.2.0 (E4): budowa, zasady odtwarzania, pokrycie i opóźnienia z replayu E1, braki bazy M1 |
