# Lektor PL – Descent: Legends of the Dark

Nieoficjalny, niekomercyjny polski lektor TTS do gry *Descent: Legends of the Dark* (Unity 2022.3.62f2, Mono, Wwise, Steam). Licencja: [LICENSE.md](LICENSE.md) (D75).

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
- Treści gry (teksty, grafiki, nagrania, dekompilacja), modeli ani wygenerowanego audio nie commitujemy (D75, D76). Raporty podają klucze, nazwy i liczby, bez pełnych tekstów.
- Repozytorium trafi publicznie na GitHub. `.gitignore` blokuje treść gry, modele i audio w każdym miejscu, bez Git LFS. Gotowe paczki idą do GitHub Releases (D76, etap E10). Zdalne repozytorium i publikację wydań robi użytkownik. Logowanie do Steam (DepotDownloader) też.
- Dokumentacja nie powtarza zastrzeżeń prawnych: opisuje je `LICENSE.md` (D76).
- Każde nowe narzędzie albo krok przygotowania dopisujemy do [docs/ODTWORZENIE.md](docs/ODTWORZENIE.md), a nowe pakiety `.venv` do `analysis/envs/venv.txt`.
- Wagi modeli i cache Hugging Face trzymamy w `analysis/work/hf_cache` (ignorowane w Git).

## Układ repozytorium

```
CLAUDE.md, README.md, LICENSE.md
docs/        PLAN.md (etapy), DECISIONS.md (decyzje i otwarte kwestie), CASTING.md (obsada głosów), ODTWORZENIE.md (od zera)
analysis/    raporty z analiz + tools/ (skrypty Python/UnityPy, elevenlabs/: serwer MCP i pomiar zużycia)
  envs/      wersje pakietów: venv.txt (.venv), omnivoice.txt i inne środowiska E0, create_envs.sh
  work/      kopie gry, depot macOS, dekompilacja, audio, próbki: nieśledzone
src/         kod docelowy (plugin, pipeline, companion)
  lektor/    pakiet Python: baza kwestii M1 (build), referencje (refs), raporty (report), audio E3 (synth, evaluate, finalize),
             companion/ (E4: library, director, player, app), bundle (E6: folder paczki)
  plugin/    Core (C#, net472, bez Harmony i BepInEx), Loader (Doorstop 4.6, D58), BepInEx (adapter, zapas deweloperski),
             install/ (lektor-hook.ps1, lektor-companion.ps1, monomod-fix.ps1)
  bundle/    szablony paczki Descent-Lektor-PL (E6): ustawienia.toml, pins.toml, win/ (.cmd + skrypty/lektor.ps1), mac/
tests/       pytest dla src/lektor (zdania testowe własne, bez tekstów gry)
```

## Komendy

Środowisko: `.venv` w katalogu głównym (Python 3.12, torch 2.6.0+cu124, chatterbox-tts 0.1.7, pakiet `lektor` zainstalowany w trybie edytowalnym). Bazowy Python `.venv` leży w `analysis/work/python` (D52). Wersje pakietów: `analysis/envs/venv.txt`, instalacja w `docs/ODTWORZENIE.md`.

- Aplikacja Claude działa jako pakiet MSIX. To, co nasze narzędzia zapisują w `%LOCALAPPDATA%`, trafia do `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local` i jest niewidoczne poza aplikacją.
  - Wszystko, czego użytkownik albo gra używa poza aplikacją, trzymamy na D: (w repozytorium).
  - Pliki tworzone przez grę albo użytkownika (dzienniki pluginu, `companion.toml`) widzimy normalnie.
  - Środowiska modeli E0 (`%LOCALAPPDATA%\LektorPL\envs`) działają tylko w aplikacji.

```bash
.venv/Scripts/python -I analysis/tools/<skrypt>.py
.venv/Scripts/python -I analysis/tools/tts_bench.py --asr-only
```

Pipeline danych (E2). Baza i referencje lądują w `analysis/work/lektor/` (nieśledzone):

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

Audio M1 (E3). Generowanie w środowisku OmniVoice (pakiet `lektor` zainstalowany tam w trybie edytowalnym), ocena w `.venv`. Wyniki w `analysis/work/audio/m1/` (nieśledzone); każdy krok jest wznawialny:

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I -m lektor generate [--limit N] [--voices narrator] [--retake]
.venv/Scripts/python -I -m lektor evaluate     # ASR, barwa, tempo -> evals.jsonl
.venv/Scripts/python -I -m lektor select       # choice.json, retake.json
.venv/Scripts/python -I -m lektor finalize     # final/*.wav, manifest.json, listen/index.html
.venv/Scripts/python -I -m lektor audio-report # analysis/E3_AUDIO.md
```

Wydanie M2 (E7): te same komendy z `--release m2` (domyślnie `m1`). Baza to `analysis/work/lektor/m2.sqlite`, audio `analysis/work/audio/m2/`, raporty `analysis/E7_DATA.md` i `analysis/E7_AUDIO.md`.

- `build --release m2 --only event_e5b map` buduje tylko wybrane grupy spoza M1.
- `generate --release m2` przejmuje z `audio/m1` fragmenty o tym samym id i liczy resztę.
- Po `select` powtarzamy `generate --retake`, `evaluate`, `select` do trzech razy, potem `finalize`.
- W M2 cytat w opcji czyta bohater okna, a fragmenty mają imię zapisane fonetycznie (`normalize.pronounce`, D70). M1 buduje się bez zmian.

Głosy NPC (D41): `analysis/tools/npc_voices.py` z poleceniami `portrait, scan, mix, select, rasp, tremor, clone, refresh, stats, adopt`. `refresh rN` odświeża stronę odsłuchu bez modelu.

Plugin (referencje do DLL z kopii gry w `analysis/work/game`, wynik w `build/plugin/`):

```bash
dotnet build src/plugin/Loader -c Release    # LektorPL.Loader.dll + LektorPL.Core.dll (paczka E6)
dotnet build src/plugin/BepInEx -c Release   # adapter BepInEx (zapas deweloperski)
.venv/Scripts/python -I analysis/tools/hook_coverage.py [dziennik.jsonl ...]
powershell -ExecutionPolicy Bypass -File src/plugin/install/monomod-fix.ps1   # MonoMod.Utils.dll bez zapisu corlib_internal (D54)
```

Instalację i odinstalowanie w folderze gry (`lektor-hook.ps1 -Install [-LoaderOnly] [-Stage N]|-Uninstall|-Status|-Stage N|-MonoModFix`) uruchamia użytkownik według `docs/E1_PLAYTEST.md`, `docs/E4_EXIT_TEST.md` i `docs/E5_PLAYTEST.md`. Dzienniki pluginu i companiona: `%LOCALAPPDATA%\LektorPL\logs`.

- `-Install` zawsze podmienia `BepInEx\core\MonoMod.Utils.dll` na kopię z `monomod-fix.ps1` (D54). Z oryginałem BepInEx 5.4.23.5 gra (x86) wysypuje się przy wyjściu: MonoMod #329 psuje strukturę `MonoAssembly`.

Paczka (E6, D57–D60). Doorstop i Python są przypięte sumami w `src/bundle/pins.toml`, koła w `src/bundle/requirements-<platform>.txt` (z `requirements.in` przez `uv pip compile --generate-hashes`). Cache w `analysis/work/bin/`:

```bash
.venv/Scripts/python -I -m lektor bundle --dev                 # analysis/work/dev-bundle: plugin z builda, Python z .venv (test W1)
.venv/Scripts/python -I -m lektor bundle --platform win|mac    # analysis/work/dist/<platform>/Descent-Lektor-PL + zip
```

- Budowa potrzebuje `uv` (koła dla wybranego systemu, `--python-platform`) i `curl` (pobrania; Python z uv na Windows nie widzi magazynu certyfikatów). Na komputerze z grą żadne z nich nie jest potrzebne.

- Paczka ma pliki do dwukliku (`Zainstaluj`, `Odinstaluj`, `Wyłącz/Włącz lektora`, `Ustawienia`, `Test dźwięku`). Uruchamia je użytkownik według `docs/INSTRUKCJA.md` (kopia w paczce) oraz `docs/E6_W1_TEST.md`, `docs/E6_W2_TEST.md` i `docs/E7_MAC_SESSION.md`.
- Skrypty Maca (`src/bundle/mac/skrypty/lektor.sh`, `start.sh`, bash 3.2) sprawdzamy `bash -n` i w Git Bash z atrapami `codesign`, `arch`, `pbcopy`, `pgrep` i `defaults` na początku `PATH`. Ścieżkę PlistBuddy nadpisuje zmienna `PLISTBUDDY`.
- Instalator Windows (`skrypty/lektor.ps1`) zapisuje stan w `stan/` paczki, a dzienniki loadera, pluginu i companiona trafiają do `logs/` paczki.
- Plugin uruchamia companion (`python -I -m lektor.companion --config ustawienia.toml --logs logs --parent-pid <gra>`), a companion kończy się po zamknięciu gry (D59).
- Pliki `.ps1` mają BOM: PowerShell 5.1 czyta plik bez BOM jako ANSI, a `ł` (bajt 0x82 w cp1250) staje się wtedy apostrofem.

Companion (E4). Konfiguracja w `%LOCALAPPDATA%\LektorPL\companion.toml` (tworzona przy pierwszym starcie). W grze użytkownik uruchamia go skryptem `src/plugin/install/lektor-companion.ps1`:

```bash
.venv/Scripts/python -I -m lektor companion                      # serwer TCP 127.0.0.1:47810 dla pluginu
.venv/Scripts/python -I -m lektor companion --replay <hook.jsonl ...> [--tcp] [--speed 0] [--no-audio] [--config plik.toml] [--out wynik.json]
```

- Replay z `--speed 0 --no-audio` sprawdza samo pokrycie. Opóźnienia mierzymy w czasie rzeczywistym (`--tcp`, wyjście audio wyciszone w configu `volume = 0.0`).

ElevenLabs (E9, D73). Serwer MCP tylko w zakresie projektu (`.mcp.json`), klucz w nieśledzonym `.env.elevenlabs.local`, audio i logi w `analysis/work/elevenlabs/`. Instrukcja: `analysis/tools/elevenlabs/README.md`.

```bash
uv run --no-project --python 3.13 analysis/tools/elevenlabs/usage_report.py [--period current|all] [--by day|voice|model|tool|session] [--csv PLIK] [--offline]
.venv/Scripts/python -I analysis/tools/elevenlabs/score_samples.py [plik ...]   # ocena próbek automatem E3
.venv/Scripts/python -I -m pytest tests/elevenlabs
```

- W sesji ten sam raport daje `/zuzycie`.
- Każde zadanie z MCP ElevenLabs prowadzimy według skilla `elevenlabs` (`.claude/skills/elevenlabs/SKILL.md`, D77). Na początku prompta `usage_report.py --mark`, a na końcu odpowiedzi blok z `usage_report.py --summary`.
- Arkusz porównawczy głosów (E11): `.venv/Scripts/python -I analysis/tools/voice_compare.py pick|status|score|sheet`, opisy wariantów w `analysis/tools/voice_designs_e11.json`, szablon stron `voice_compare.html`, wyniki w `analysis/work/compare/e11/`.
- Płatne narzędzia wywołujemy tylko za zgodą użytkownika. Testy automatyczne nie łączą się z siecią.
- Hooki z `.claude/settings.json` zapisują koszt każdego płatnego wywołania. Log nie zawiera tekstów.

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
| [analysis/E5_TEST.md](analysis/E5_TEST.md) | sesja M1 z lektorem (E5): D13 w grze, okna i odczyty, braki, wydajność, uwagi z gry (D55) |
| [analysis/E7_DATA.md](analysis/E7_DATA.md) | baza kwestii M2 (E7): liczności, luki `{n}`, pokrycie wartości, szacunek generowania |
| [analysis/E7_AUDIO.md](analysis/E7_AUDIO.md) | audio M2 (E7): czas na znak, wyniki automatu, pokrycie kluczy |
| [analysis/E9_ELEVENLABS.md](analysis/E9_ELEVENLABS.md) | test ElevenLabs (E9): wyniki automatu, koszt na znak, co test zmienił w pomiarze |
| [analysis/E11_VOICES.md](analysis/E11_VOICES.md) | arkusz głosów (E11): dubbing wobec OmniVoice, warianty ElevenLabs, cztery modele TTS, oceny, stawki, koszt na grupę głosów |
