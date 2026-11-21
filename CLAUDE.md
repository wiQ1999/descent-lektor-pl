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
- Repozytorium jest publiczne: `wiQ1999/descent-lektor-pl` (D82). `.gitignore` blokuje treść gry, modele i audio w każdym miejscu, bez Git LFS. Gotowe paczki idą do GitHub Releases (D76, E10).
  - Wypchnięcie i wydania robimy przenośnym `gh` z `analysis/work/bin/` (`GH_CONFIG_DIR=analysis/work/bin/gh-config`, pomocnik poświadczeń tylko w `git -c`, bez globalnej konfiguracji Git). Komendy są w `docs/ODTWORZENIE.md` §7.
  - Do GitHub (`gh auth login`) i Steam (DepotDownloader) loguje się użytkownik.
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
  lektor/    pakiet Python: baza kwestii M1 (build), referencje (refs), raporty (report), audio E3 (synth, evaluate, finalize), ElevenLabs E13 (eleven),
             companion/ (E4: library, director, player, app), bundle (E6: folder paczki)
  plugin/    Core (C#, net472, bez Harmony i BepInEx), Loader (Doorstop 4.6, D58), BepInEx (adapter, zapas deweloperski),
             install/ (lektor-hook.ps1, lektor-companion.ps1, monomod-fix.ps1)
  bundle/    szablony paczki Descent-Lektor-PL (E6): ustawienia.toml, pins.toml, UZNANIE_AUTORSTWA.md (E10), win/ (.cmd + skrypty/lektor.ps1), mac/
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
Cała gra M3 (E14): `--release m3`, baza `m3.sqlite`, audio `audio/m3/`, raporty `analysis/E14_DATA.md` i `analysis/E14_AUDIO.md`. Grupa kwestii to misja albo wydarzenie (`scope.m3_group`), a M3 przejmuje fragmenty z M2 (`paths.PREVIOUS`).
W m3 komunikat gry po pustym wierszu w kwestii postaci czyta narrator, a tekst WIELKIMI literami czytamy zwykłą pisownią (`build.line_parts`, D85). Wstawki w nawiasach czekają na E15 (D86).

Paczka testowa Q1–Q2 (E16, D101): `--release t1`, baza `t1.sqlite`, audio `audio/t1/`, reguły i zakres bazy z `m3` (`paths.BASE`), tylko OmniVoice (`paths.LOCAL_ONLY`), generowanie i ocena w grupach `scope.TEST_GROUPS['t1']`.
- Wypowiedzi postaci w oknach narratora czyta postać: półpauza, mowa przed „– mówi X” i list w „…” z autorem przed cytatem (D102) (`speakers.py`, nadpisania w `src/lektor/data/speakers_t1.json`, przegląd `analysis/tools/speakers_review.py`). `arg:N` to bohater z luki {N}: wersje `KLUCZ#bohater`, companion wybiera je po argumencie (`hero_variant` `ARG:N`). Głosy `nv_*` projektuje `analysis/tools/new_voices_t1.py design|choose|adopt`.
- Narrator ma w zakresie testu jedno tempo `SPEED_MAX` (`direction.ONE_TEMPO`), także w wartościach luk i łupu.
- Okno ataku: kwestie zdolności (`abilities.py`), zdarzenia pluginu `open/close` `kind: ability` i `kind: defense` (obrona wroga, D102), przełącznik `zdolnosci`.
- Cel misji, którego tekst przeczytało okno komunikatu, nie gra drugi raz (`director.plain`, D102).
- Ikony (D103): każda ikona glosariusza ma słowo w `normalize.ICONS` (plus to „potencjał”), glify bez linku mapuje `GLYPH_TERMS`, a ikona ulepszenia daje „ulepszony/-a/-e” przed nazwą (`normalize.upgraded`). Klucze i luki wybierane w kodzie gry dodaje `scope` (`CODE_PREVIEWS`, `GiveTreasure._outputFirstKey`).
- D105–D106: w chwili ukończenia wyzwania plugin zgłasza `feat_done`, a companion mówi nagłówek, bohatera i nazwę (`library.feat_done`, nazwy w `@FEATS`); okno wyzwania (`kind: feat`, `library.feat`) czyta nagłówek i nagrodę jak łup. Kwestia postaci z wtrąceniem „– mówi X” dzieli się jak okno narratora (`build.NARRATED`). Ikona po przeczeniu stoi w dopełniaczu. Wrogowie bez `_SING` (`scope.unique_enemy_names`) mają nazwę w `EntityName` i w łupie.
- Przebieg: `REL=t1 ELEVEN=0 bash analysis/tools/e14_run.sh`, potem dodatkowe rundy `analysis/tools/extra_retakes.py` i `bundle --platform win --release t1`.

Wersja produkcyjna (E17, D107): `--release m4`, baza `m4.sqlite`, audio `audio/m4/`, zakres `m3` (`paths.BASE`), reguły t1 w całej grze (`scope.T1_RULES`, `ONE_TEMPO`).
- Mówcy w oknach narratora: `src/lektor/data/speakers_prod.json` z `analysis/tools/speakers_freeze.py` (propozycja automatu + `analysis/work/out/prod/corrections.txt` + wybory t1). Przegląd: `speakers_digest.py`.
- Mówcy bez imienia (`nv_*`, 99) mają własne głosy OmniVoice: 19 z t1 i 80 z profili postaci (`omni` w `analysis/tools/voice_designs_prod.json`), projekt i wybór automatem `analysis/tools/new_voices_prod.py design|choose|adopt`.
- `generate` przejmuje wybory z t1 i m3 (tylko silnik głosu w m4) i nieocenione podejścia OmniVoice z m3 (`paths.ADOPT`, `synth.adopt`).
- Pierwsza paczka m4 obejmuje akt 1 i części wspólne (D108, `ACTS="1 3" ASR_FP32=1`). Test w grze: `docs/E17_M4_TEST1.md`. Zestawienie głosów do odsłuchu: `analysis/tools/cast_sheet.py` (`analysis/work/compare/m4_cast/index.html`).
- Zmiany obsady po odsłuchu (D109): `analysis/tools/recast_m4.py design|choose|page|adopt` (kandydaci OmniVoice i podglądy ElevenLabs w `analysis/work/compare/m4_recast/`). Nowe profile ElevenLabs wpisujemy do `direction.ELEVEN_RECAST` (znacznik w kluczu fragmentu). „Warrick” model czyta „Łorik” (`normalize.PHONETIC`).

- `build --release m2 --only event_e5b map` buduje tylko wybrane grupy spoza M1.
- Fazę B E14 prowadzi `bash analysis/tools/e14_run.sh` (D95). Skrypt jest wznawialny i działa w aplikacji Claude:
  - ElevenLabs i OmniVoice idą naraz, w kolejności gry;
  - potem ocena, ponowne podejścia i `finalize`;
  - dzienniki zapisuje w `audio/m3/logs/`.
- Postęp: `progress --release m3 [--all]`, a co 10 min także plik `audio/m3/progress.md`.
- Dashboard stanu dialogów wszystkich wydań (D104): `dashboard [--serve [PORT]]` pisze `analysis/work/dashboard/index.html` (misje osobno, reszta w kategoriach, wersja i procent); `--serve` albo `analysis/tools/dashboard.cmd` liczy stan przy każdym odświeżeniu `http://127.0.0.1:47811/`. `e14_run.sh` odświeża plik razem z `progress.md`.
- ElevenLabs zapisuje stan w `takes_eleven.jsonl`.
- Wydanie częściowe (D96): `generate` i `evaluate` przyjmują `--acts 1 3` (akt 1 i części wspólne).
  - `evaluate --no-asr` robi szybką ocenę bez Whispera do `evals_quick.jsonl`.
  - `evaluate --fp32 --until HH:MM` liczy Whispera w fp32 do podanej godziny.
  - Pokrycie kwestii sprawdza `analysis/tools/release_coverage.py`.
- Paczka ma audio w FLAC (D96).
- Styl klonu w `refs.json` (`style.speed`, `style.instruct`) wchodzi do klucza fragmentu i do `synth`.
- Postacie bez dubbingu (D80, E13) czyta ElevenLabs `eleven_v4`: `eleven --release m1|m2 [--dry-run] [--retake] [--max-credits N]` w `.venv` (płatne, wznawialne). Głosy i `voice_id` są w `direction.ELEVEN_VOICES`. Podejścia mają numery od 101 obok podejść OmniVoice, `select` bierze dla głosu tylko jego silnik. M1 generujemy przed M2, bo M2 przejmuje z M1 fragmenty o tym samym id.
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

- Instalacja jedną komendą (E19, D111): `bundle --platform win|mac --parts` dzieli paczkę na części z manifestem we wspólnym `analysis/work/dist/online/` (warstwy audio wspólne dla obu systemów). Aktualizacja pobiera tylko zmienione części. Próba lokalna i test Maca z atrapami: `docs/ODTWORZENIE.md`.
  - Windows: starter `src/bundle/online/instaluj-win.ps1` (tylko ASCII, `irm | iex`) uruchamia `instalator-win.ps1`; folder `%USERPROFILE%\Descent-Lektor-PL`, stan w `stan\pakiet.json`.
  - Mac: `instaluj-mac.sh` (`curl | bash`, bash 3.2, indeks `lektor-mac.txt`, pytania z `/dev/tty`); folder `~/Descent-Lektor-PL`, stan w `stan/pakiet.txt`.
- Budowa potrzebuje `uv` (koła dla wybranego systemu, `--python-platform`) i `curl` (pobrania; Python z uv na Windows nie widzi magazynu certyfikatów). Na komputerze z grą żadne z nich nie jest potrzebne.

- Części wspólne paczek powstają raz w `analysis/work/dist/wspolne/`, a `dist/win` i `dist/mac` mają je jako twarde dowiązania (D112). Instrukcję paczka dostaje tylko dla swojego systemu (bloki `<!-- win -->`/`<!-- mac -->` w `docs/INSTRUKCJA.md`).
- Paczka ma pliki do dwukliku (`Zainstaluj`, `Odinstaluj`, `Test dźwięku`). Ustawienia gracz zmienia w `ustawienia.toml` (D112). Uruchamia je użytkownik według `docs/INSTRUKCJA.md` (kopia w paczce) oraz `docs/E6_W1_TEST.md`, `docs/E6_W2_TEST.md` i `docs/E7_MAC_SESSION.md`.
- Skrypty Maca (`src/bundle/mac/skrypty/lektor.sh`, `start.sh`, bash 3.2) sprawdzamy `bash -n` i w Git Bash z atrapami `codesign`, `arch`, `pbcopy`, `pgrep` i `defaults` na początku `PATH`. Ścieżkę PlistBuddy nadpisuje zmienna `PLISTBUDDY`.
- Instalator Windows (`skrypty/lektor.ps1`) zapisuje stan w `stan/` paczki, a dzienniki loadera, pluginu i companiona trafiają do `logs/` paczki.
- Plugin uruchamia companion (`python -I -m lektor.companion --config ustawienia.toml --logs logs --parent-pid <gra>`), a companion kończy się po zamknięciu gry (D59).
- Pliki `.ps1` mają BOM: PowerShell 5.1 czyta plik bez BOM jako ANSI, a `ł` (bajt 0x82 w cp1250) staje się wtedy apostrofem.

Companion (E4). Konfiguracja w `%LOCALAPPDATA%\LektorPL\companion.toml` (tworzona przy pierwszym starcie). W grze użytkownik uruchamia go skryptem `src/plugin/install/lektor-companion.ps1`:

```bash
.venv/Scripts/python -I -m lektor companion                      # serwer TCP 127.0.0.1:47810 dla pluginu
.venv/Scripts/python -I -m lektor companion --replay <hook.jsonl ...> [--tcp] [--speed 0] [--no-audio] [--config plik.toml] [--out wynik.json]
```

- Nakładka w grze (E18, D110): skróty, przycisk „PL” z menu (kopia podmenu drużyny, `src/plugin/Core/PlMenu.cs`, `Overlay.cs`) i zgłoszenia w `zgloszenia/`. Plugin wysyła `control` i `report`, companion odsyła `state` (`companion/control.py`: tempo WSOLA, zapis `ustawienia.toml`, zgłoszenie). Lista kontrolna w grze: `docs/NAKLADKA_TEST.md`.
- Statystyki misji (E20, D114): panele po bokach okna podsumowania misji (`src/plugin/Core/SummaryPanel.cs`, dane `QuestStats.cs`, tylko standardowy zapis gry). Włącznik `[podsumowanie] statystyki` i checkbox w menu lektora (`control` `statystyki`, w stanie `stats`); podgląd w misji Ctrl+P przy `[podsumowanie] podglad = true` (`docs/E20_PODGLAD.md`). Wzorzec liczb z `.sav`: `analysis/tools/quest_summary_preview.py`.
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
- Arkusz obsady E14 (nowe postacie i złoczyńcy): `analysis/tools/voice_compare_e14.py` (kroki w nagłówku skryptu, `design` i `clone` w środowisku OmniVoice), opisy w `voice_designs_e14.json`, wyniki w `analysis/work/compare/e14/`. Katalog wyjściowy MCP ElevenLabs tworzymy przed wywołaniem.
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
| [analysis/E13_AUDIO.md](analysis/E13_AUDIO.md) | postacie bez dubbingu w ElevenLabs (E13): koszt, wyniki automatu, ponowne podejścia, porównanie z OmniVoice |
| [analysis/E14_DATA.md](analysis/E14_DATA.md) | baza kwestii całej gry M3 (E14): liczności według grupy, kategorii i głosu, luki `{n}`, szacunek generowania |
| [analysis/E14_AUDIO.md](analysis/E14_AUDIO.md) | audio M3 (E14, wydanie częściowe D96): czas generowania, wyniki automatu, udział oceny Whisperem |
| [analysis/E14_NO_DUB_SCOPE.md](analysis/E14_NO_DUB_SCOPE.md) | postacie bez dubbingu w całej grze (E14): kwestie poza M2 według mówcy i aktu, koszt ElevenLabs, miejsca na głosy |
| [analysis/E14_INSERTS.md](analysis/E14_INSERTS.md) | wstawki sceniczne w nawiasach (D86, do E15): liczby według głosu i grupy, klucze |
| [analysis/E14_PARTY.md](analysis/E14_PARTY.md) | partia ze znajomymi (v0.3.0): przyczyny ciszy i braków według zrzutów i dzienników, wnioski do poprawki |
| [analysis/E16_DATA.md](analysis/E16_DATA.md) | baza paczki testowej t1 (E16): liczności według grupy, kategorii i głosu |
| [analysis/E16_AUDIO.md](analysis/E16_AUDIO.md) | audio t1 (E16): czas generowania, wyniki automatu według głosu, w tym nowych `nv_*` |
| [analysis/E16_TEST.md](analysis/E16_TEST.md) | paczka testowa Q1–Q2 (E16): podział na głosy, jedno tempo, okno ataku, pokrycie, replay, lista odsłuchu |
| [analysis/E16_PLAYTEST.md](analysis/E16_PLAYTEST.md) | testy t1 w grze (Q1–Q2, 2026-11-13/14): zrzuty, przyczyny, przegląd mowy w oknach narratora, poprawki D102, D103, D105 i D106 (okno i zapowiedź wyzwania, przeczenie, wtrącenia) |
| [analysis/E17_PREP.md](analysis/E17_PREP.md) | przygotowanie wersji produkcyjnej m4: przegląd mówców w oknach, nowe głosy mówców bez imienia, szacunek GPU i kredytów, kontrola tekstów |
| [analysis/E17_DATA.md](analysis/E17_DATA.md) | baza kwestii m4: liczności według grupy, kategorii i głosu, szacunek generowania |
| [analysis/E20_SUMMARY.md](analysis/E20_SUMMARY.md) | statystyki misji w oknie podsumowania (E20): sekcje i dane gry, czego gra nie zapisuje, testy w grze, ustawienia |
