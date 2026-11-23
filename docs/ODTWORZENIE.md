# Odtworzenie projektu od zera

Repozytorium nie zawiera treści gry, modeli ani wygenerowanego audio (D75, D76). Gotowe paczki z audio są w wydaniach GitHub Releases (E10, D82). Ta instrukcja pozwala zbudować wszystko samodzielnie w `analysis/work/`, z kopii aplikacji na Twoim komputerze. Komendy uruchamiamy z katalogu głównego repozytorium w Git Bash, chyba że blok mówi inaczej.

## Wymagania

- Windows 11, karta NVIDIA z CUDA 12.4 (wystarczy GTX 1650 Ti 4 GB) i ok. 40 GB wolnego miejsca.
- Aplikacja *Descent: Legends of the Dark* zainstalowana ze Steam.
- Git, Git Bash, [uv](https://docs.astral.sh/uv/), .NET SDK 10 (plugin) i curl (paczki).
- Opcjonalnie: klucz ElevenLabs (E9) i DepotDownloader (analiza buildu macOS).

## 1. Kopia gry

Oryginał w folderze Steam zostaje tylko do odczytu. Pracujemy na kopii (PowerShell):

```powershell
robocopy "E:\SteamLibrary\steamapps\common\Legends of the Dark" "analysis\work\game" /E
```

Ścieżkę biblioteki Steam dopasuj do swojego komputera.

Projekt powstał na wersji gry ze Steam o numerze build `23973225`, z manifestem bundli `fddf8aedeb14` (`meta.manifest` w bazie). Z tej wersji baza kwestii, portrety i referencje głosów z dubbingu wychodzą bajt w bajt takie same (sprawdzone 2026-11-07). Aktualizacja gry może zmienić teksty, a wtedy baza też się zmieni. Głosy projektowane i audio za każdym razem wychodzą nieco inaczej, bo model losuje.

## 2. Środowisko `.venv`

Bazowy Python leży w projekcie (D52). Wersje pakietów są w `analysis/envs/venv.txt`.

```bash
uv python install 3.12.13 --install-dir analysis/work/python
```

```bash
uv venv --python analysis/work/python/cpython-3.12.13-windows-x86_64-none/python.exe .venv
```

```bash
uv pip install --python .venv/Scripts/python.exe --index https://download.pytorch.org/whl/cu124 --index-strategy unsafe-best-match --no-deps -r analysis/envs/venv.txt
```

```bash
uv pip install --python .venv/Scripts/python.exe --no-deps -e .
```

```bash
.venv/Scripts/python -I -m pytest -q
```

Testy działają bez kopii gry. Testy zależne od gry włącza zmienna `LEKTOR_GAME_TESTS=1`.

## 3. Środowisko OmniVoice

OmniVoice (D33) ma własne środowisko z wersjami z `analysis/envs/omnivoice.txt`:

```bash
uv python install 3.12.13 --install-dir "$LOCALAPPDATA/LektorPL/python"
```

```bash
bash analysis/envs/create_envs.sh omnivoice
```

```bash
uv pip install --python "$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" --no-deps -e .
```

Wagi modeli (OmniVoice, Whisper, VoiceEncoder) pobierają się same przy pierwszym użyciu do `analysis/work/hf_cache`.

## 4. vgmstream

Nagrania dubbingu są w formacie Wwise. Konwertuje je vgmstream r2168 ([wydanie](https://github.com/vgmstream/vgmstream/releases/tag/r2168), Windows). Archiwum rozpakuj do `analysis/work/bin/vgmstream-r2168/`.

SHA-256 pliku `vgmstream-cli.exe`: `10fb0691538d3133f0115a071f89775fc99f32210b7e5991cfc3c2869247e4b2`.

## 5. Nagrania i referencje głosów

```bash
.venv/Scripts/python -I analysis/tools/extract_voices.py
```

```bash
.venv/Scripts/python -I analysis/tools/analyze_voices.py
```

```bash
.venv/Scripts/python -I -m lektor refs
```

Głosy projektowane (D41) powstają w środowisku OmniVoice:

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/npc_voices.py scan r1
```

- Rundy i postacie są w `ROUNDS` w `analysis/tools/npc_voices.py`. Opisy, ziarna i wybrani kandydaci są w `docs/CASTING.md`.
- Wybranego kandydata zapisuje `npc_voices.py adopt <runda> <głos> <kandydat>`.
- Ziarna dają bardzo podobny głos, ale na innej karcie albo sterowniku może się on nieco różnić. Wynik warto odsłuchać.

## 6. Baza kwestii i audio

```bash
.venv/Scripts/python -I -m lektor build --release m2
```

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I -m lektor generate --release m2
```

Postacie bez dubbingu (D80, E13) czyta ElevenLabs. Ich fragmenty generuje płatna komenda w `.venv` z kluczem z `.env.elevenlabs.local` (`analysis/tools/elevenlabs/README.md`). Najpierw M1, bo M2 przejmuje z niego fragmenty o tym samym id:

```bash
.venv/Scripts/python -I -m lektor eleven --release m1 --dry-run
```

```bash
.venv/Scripts/python -I -m lektor eleven --release m2 --max-credits 5000
```

- `--dry-run` podaje liczbę znaków i szacunek kredytów bez połączenia z siecią. Koszt każdego wywołania trafia do logu zużycia ElevenLabs.
- Automat ocenia barwę wobec nagrań v4 z rundy 2 E11 (`analysis/work/elevenlabs/audio/e11r2/`, sekcja 8). Bez nich barwa tych głosów zostaje bez oceny.

```bash
.venv/Scripts/python -I -m lektor evaluate --release m2
```

```bash
.venv/Scripts/python -I -m lektor select --release m2
```

- Po `select` powtarzamy `generate --retake` (i `eleven --retake`), `evaluate` i `select` do trzech razy.
- Na końcu `finalize --release m2` tworzy pliki końcowe i stronę odsłuchu. `--listen-engine elevenlabs` ogranicza odsłuch do głosów ElevenLabs.
- Całe M2 to ok. 16 h GPU na GTX 1650 Ti. Każdy krok jest wznawialny.
- M1 buduje się tak samo, z `--release m1`.

Cała gra M3 (E14, D95). Najpierw klony E14 trafiają do bazy referencji (kopia poprzedniej bazy to `refs.before_e14.json`), potem budujemy bazę:

```bash
.venv/Scripts/python -I analysis/tools/voice_compare_e14.py adopt
```

```bash
.venv/Scripts/python -I -m lektor build --release m3
```

Całe generowanie prowadzi jeden skrypt, uruchamiany w aplikacji Claude, bo tylko w niej działa środowisko OmniVoice:
- ElevenLabs i OmniVoice idą naraz, w kolejności gry;
- potem ocena i do 3 rund ponownych podejść;
- na końcu `finalize` i `audio-report`.

Skrypt jest wznawialny, a dzienniki zapisuje w `analysis/work/audio/m3/logs/`.

```bash
bash analysis/tools/e14_run.sh
```

```bash
.venv/Scripts/python -I -m lektor progress --release m3
```

- `--all` pokazuje wszystkie paczki. Ten sam raport skrypt co 10 min zapisuje do `analysis/work/audio/m3/progress.md`.
- Stan dialogów wszystkich wydań (D104) pokazuje dashboard: misje osobno, reszta w kategoriach, wersja i procent wykonania. Skrypt odświeża plik `analysis/work/dashboard/index.html` razem z `progress.md`, a `--serve` (albo dwuklik `analysis/tools/dashboard.cmd`) liczy stan przy każdym odświeżeniu strony `http://127.0.0.1:47811/`:

```bash
.venv/Scripts/python -I -m lektor dashboard [--serve [PORT]] [--out PLIK]
```

- `MAX_CREDITS` (domyślnie 58000) ogranicza kredyty ElevenLabs całego wydania.

Wydanie częściowe (D96): akt 1 i części wspólne, z oceną dopasowaną do terminu.

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I -m lektor generate --release m3 --acts 3
```

```bash
.venv/Scripts/python -I -m lektor evaluate --release m3 --acts 1 3 --no-asr
```

```bash
.venv/Scripts/python -I -m lektor evaluate --release m3 --acts 1 3 --fp32 --until 11:05
```

- `--acts` ogranicza krok do części gry: 1 akt 1, 2 akt 2, 3 części wspólne.
- `--no-asr` to szybka ocena bez Whispera na CPU (cisza, tempo, końcówka z energii, barwa, pauzy) do `evals_quick.jsonl`. `select` bierze ją dla fragmentów bez pełnej oceny.
- `--fp32` liczy Whispera w fp32 (ok. 2,3 s na podejście wobec ok. 7,6 s w fp16), a `--until HH:MM` kończy ocenę o tej godzinie.
- W m3 Whisper ocenia najpierw ponowne podejścia, potem pierwsze podejścia w kolejności gry, na końcu pozostałe podejścia bohaterów. `--later <grupy>` przesuwa grupy na koniec (misje już rozegrane w zapisie gry).
- `select` łączy obie oceny podejścia. Przy tych samych uwagach wygrywa podejście sprawdzone Whisperem.
- Potem `select`, `finalize` i `audio-report` jak wyżej. Pokrycie kwestii z wybranych części gry sprawdza:

```bash
.venv/Scripts/python -I analysis/tools/release_coverage.py --release m3 --acts 1 3
```

Paczka testowa Q1–Q2 (E16, D101): wydanie `t1` na bazie `m3`, tylko OmniVoice, zakres z `scope.TEST_GROUPS`.
- Podział okien narratora na głosy postaci czyta `src/lektor/data/speakers_t1.json` (klucze i głosy, bez tekstów gry). Przegląd z tekstem i propozycją automatu zapisuje `analysis/tools/speakers_review.py` do `analysis/work/out/t1/speakers_review.txt`.
- Nowe głosy `nv_*` projektuje `analysis/tools/new_voices_t1.py` (kopia poprzedniej bazy referencji to `refs.before_t1.json`):

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/new_voices_t1.py design
```

```bash
.venv/Scripts/python -I analysis/tools/new_voices_t1.py choose
```

```bash
.venv/Scripts/python -I analysis/tools/new_voices_t1.py adopt
```

```bash
.venv/Scripts/python -I -m lektor build --release t1
```

```bash
REL=t1 ELEVEN=0 bash analysis/tools/e14_run.sh
```

- `generate` i `evaluate` bez `--groups` biorą zakres testu, a `generate` przejmuje z `audio/m3` fragmenty o tym samym id.
- Po trzech rundach skryptu odrzucone nowe fragmenty zakresu dostają do trzech dodatkowych rund (`extra_retakes.py` pisze `retake.json`, potem `generate --retake`, `evaluate`, `select`), a na końcu `finalize` i `audio-report`:

```bash
.venv/Scripts/python -I analysis/tools/extra_retakes.py --release t1
```

- Sprawdzenie: pokrycie zakresu i replay dzienników pluginu na bazie `t1` (konfiguracja z `companion.config.default_text()` po `paths.use('t1')`):

```bash
.venv/Scripts/python -I analysis/tools/release_coverage.py --release t1
```

```bash
.venv/Scripts/python -I -m lektor companion --config <plik.toml> --replay <hook.jsonl> --speed 0 --no-audio
```

```bash
.venv/Scripts/python -I -m lektor bundle --platform win --release t1
```

Wersja produkcyjna (E17, D107): wydanie `m4` na bazie `m3`, reguły t1 w całej grze, przejęcie nagrań z t1 i m3.
- Przegląd mówców w oknach narratora spoza t1 zapisuje `speakers_digest.py` do `analysis/work/out/prod/speakers_digest.txt`. Poprawki ręczne leżą w `analysis/work/out/prod/corrections.txt`, a opisy nowych postaci w `new_voices.txt` tamże.
- `speakers_freeze.py` składa z nich `src/lektor/data/speakers_prod.json` (propozycja automatu, poprawki i wybory t1) i sprawdza liczby głosów:

```bash
.venv/Scripts/python -I analysis/tools/speakers_digest.py
```

```bash
.venv/Scripts/python -I analysis/tools/speakers_freeze.py
```

```bash
.venv/Scripts/python -I -m lektor build --release m4
```

- Nowe głosy `nv_*` projektuje OmniVoice z profili postaci (`omni` w `analysis/tools/voice_designs_prod.json`): trzy ziarna na profil, wybór automatem, referencje do `refs.json`. Potem przebudowa bazy `m4`:

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/new_voices_prod.py design
```

```bash
.venv/Scripts/python -I analysis/tools/new_voices_prod.py choose
```

```bash
.venv/Scripts/python -I analysis/tools/new_voices_prod.py adopt
```
- Generowanie jak w E14 (`REL=m4 bash analysis/tools/e14_run.sh`). `generate` przejmuje wybory z t1 i m3 oraz nieocenione podejścia OmniVoice z m3 (`synth.adopt`). Dodatkowe rundy: `extra_retakes.py --release m4`.
- Paczka z aktem 1 (D108): `REL=m4 ELEVEN=1 ACTS="1 3" ASR_FP32=1 bash analysis/tools/e14_run.sh`, potem `extra_retakes.py --release m4` z `generate --retake --acts 1 3`, `evaluate --acts 1 3 --fp32`, `select`, `finalize` i `bundle --platform win|mac --release m4`.
- Zestawienie głosów do odsłuchu (opis, portret z gry, dwie próbki z gotowego audio), wynik w `analysis/work/compare/m4_cast/`. Strona czyta portrety i nagrania z plików obok, więc otwieramy ją w przeglądarce bezpośrednio albo przez `python -m http.server` (konfiguracja `cast-sheet` w `.claude/launch.json`):

```bash
.venv/Scripts/python -I analysis/tools/cast_sheet.py --release m4 [--acts 1 2 3]
```

- Domyślnie zestawienie obejmuje całą grę. Fragmenty spoza paczki (akt 2) mają próbki z podejść o bieżącym id, przycięte i wyrównane jak w `finalize`.
- Próbki E20 (D114): tempo narracji scen i Vaerixa w dwóch wariantach (nowe generowanie OmniVoice i WSOLA) oraz efekty z `lektor.effects` (duch, głos w głowie). Wynik w `analysis/work/compare/e20_probki/index.html`:

```bash
.venv/Scripts/python -I analysis/tools/e20_samples.py pick
```

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/e20_samples.py gen
```

```bash
.venv/Scripts/python -I analysis/tools/e20_samples.py check
```

```bash
.venv/Scripts/python -I analysis/tools/e20_samples.py page
```

- Kandydaci głosów E20 (D114): profile w `analysis/tools/voice_designs_e20.json` (nowe głosy, poprawki jakości, klony Ne'Krul i Levirax, odszumiona referencja Gilliama). Każdy kandydat czyta też kwestię z gry. Strona `analysis/work/compare/e20_recast/index.html`, wybór przejmuje `adopt` (litera A–C, `-` bez zmian):

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/recast_e20.py design
```

```bash
.venv/Scripts/python -I analysis/tools/recast_e20.py choose
```

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/recast_e20.py lines
```

```bash
.venv/Scripts/python -I analysis/tools/recast_e20.py page
```

```bash
.venv/Scripts/python -I analysis/tools/recast_e20.py adopt nv_x=B gilliam=A nv_y=-
```

- Runda 2 E20: te same kroki z `--round 2`, profile w `analysis/tools/voice_designs_e20_r2.json` (czyste projekty bez obróbki referencji, `keep` z rundy 1, klon z opisem w `clone_instructs`), wyniki w `analysis/work/compare/e20_recast/r2/`. Grupy wrogów o tej samej nazwie (`_groups`: jeden głos dla członków) mają własną stronę `r2/grupy.html`, a wybór numeru opcji przejmuje `group-adopt`:

```bash
.venv/Scripts/python -I analysis/tools/recast_e20.py group-plan --round 2
```

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/recast_e20.py group-lines --round 2
```

```bash
.venv/Scripts/python -I analysis/tools/recast_e20.py group-page --round 2
```

```bash
.venv/Scripts/python -I analysis/tools/recast_e20.py group-adopt --round 2 bandyta=3 hybryda=1
```

- Runda 3 E20: kroki `design`, `choose`, `lines`, `page`, `adopt` z `--round 3`, profile w `analysis/tools/voice_designs_e20_r3.json`, wyniki w `analysis/work/compare/e20_recast/r3/`. Rodzaj `like` daje kobiecy głos dla grupy wrogów o głosie `src`: klon referencji `src` po zmianie płci (`regender`: wysokość metodą PSOLA do mediany `f0`, potem formanty o `formant` półtonów, bez nowych pakietów) i nowe projekty kobiece, a na stronę idą klon i projekt najbliżej barwy `src`. Sam opis kobiecy przy klonie OmniVoice nie zmienia płci (F0 zostaje męskie). Pole `cps` w profilu zwalnia projekt (domyślnie 12,5 znaku na sekundę). `choose` omija kandydatów zbyt podobnych do odrzuconych we wszystkich wcześniejszych rundach.
- Runda 4 E20: te same kroki z `--round 4`, profile w `analysis/tools/voice_designs_e20_r4.json`, wyniki w `analysis/work/compare/e20_recast/r4/`. Profil może podać własne ziarna (`seeds`) i liczbę kandydatur na stronie (`picks`, domyślnie 3).
- Runda 5 E20: `--round 5`, profile w `analysis/tools/voice_designs_e20_r5.json`, wyniki w `analysis/work/compare/e20_recast/r5/`. Rodzaj `like` z pustym `instructs` daje same klony `src` po zmianie płci, po jednej kandydaturze na wariant `regender` (wariant może mieć `instruct`, `cps` profilu zwalnia klon). `post_regender` daje zwykły klon `src` ze zmianą płci na gotowym nagraniu (także w kwestii z gry w `lines`), `f0_min` podnosi dolny próg wysokości, a `voiced_min` (domyślnie 0,35) odrzuca szept.
- Runda 6 E20: `--round 6`, profil w `analysis/tools/voice_designs_e20_r6.json`, wyniki w `analysis/work/compare/e20_recast/r6/`. Wariant zmiany płci z `method: grain` przesuwa formanty ściśniętymi ziarnami PSOLA (bez `librosa.pitch_shift`). `per_variant` ustala liczbę ziaren na wariant `post_regender` na stronie.
- Runda 7 E20: `--round 7`, profil w `analysis/tools/voice_designs_e20_r7.json`, wyniki w `analysis/work/compare/e20_recast/r7/`. `method: resample` przyspiesza nagranie o 2^(formant/12) i wraca do czasu przez PSOLA ze znacznikami po korelacji. `own_line_seed` czyta kwestię z gry na ziarnie kandydata, a kandydaci kolejnych wariantów nie powtarzają ziaren. `keep_rejected_timbre` wyłącza filtr barwy odrzuconych kandydatów, gdy odrzucenie dotyczyło obróbki, a nie barwy.

- Zmiany obsady po odsłuchu (D109): kandydaci OmniVoice (dwa opisy, dwa ziarna, wariant z obróbką) i podglądy ElevenLabs na jednej stronie `analysis/work/compare/m4_recast/index.html`. Wybór z odsłuchu przejmuje `adopt` (litera A–C, `-` bez zmian), nowe profile ElevenLabs wpisujemy do `direction.ELEVEN_RECAST`, potem `build --release m4`:

```bash
"$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe" -I analysis/tools/recast_m4.py design
```

```bash
.venv/Scripts/python -I analysis/tools/recast_m4.py choose
```

```bash
.venv/Scripts/python -I analysis/tools/recast_m4.py page
```

```bash
.venv/Scripts/python -I analysis/tools/recast_m4.py adopt nv_x=A nv_y=-
```

## 7. Plugin i paczka

```bash
dotnet build src/plugin/Loader -c Release
```

```bash
powershell -ExecutionPolicy Bypass -File src/plugin/install/monomod-fix.ps1
```

```bash
.venv/Scripts/python -I -m lektor bundle --platform win --release m2
```

- Paczka trafia do `analysis/work/dist/`. Doorstop, Python i koła mają sumy w `src/bundle/pins.toml` i `src/bundle/requirements-<platform>.txt`.
- Audio w paczce jest w FLAC (D96). Kopie FLAC plików końcowych leżą w `analysis/work/audio/<wydanie>/flac/`.
- Części wspólne obu systemów (plugin, pakiet `lektor`, baza, audio, licencje, ustawienia) powstają w `analysis/work/dist/wspolne/` (D112). Paczki `win` i `mac` mają je jako twarde dowiązania, tylko `ustawienia.toml` jest kopią. Audio dowiązuje kopie FLAC, więc leży na dysku raz. Plików w `dist/win` i `dist/mac` nie zmieniamy w miejscu, bo zmiana trafi do obu paczek.
- Instalację w grze opisuje `docs/INSTRUKCJA.md`. Bloki `<!-- win -->` i `<!-- mac -->` dotyczą jednego systemu: paczka dostaje instrukcję tylko swojego systemu (`bundle.guide_text`).
- Nowy plugin i companion bez budowania paczki: `src/plugin/install/nakladka-test.ps1 -Paczka "<paczka>"` podmienia je w rozpakowanej paczce (oryginały w `stan\nakladka-kopia`, powrót: `-Przywroc`). Opis i lista kontrolna: `docs/NAKLADKA_TEST.md`.
- Każda paczka ma `LICENSE.md`, `UZNANIE_AUTORSTWA.md` (szablon w `src/bundle/`) i licencję Doorstop w `licencje/`.

### Instalacja jedną komendą: części paczki (E19, D111)

```bash
.venv/Scripts/python -I -m lektor bundle --platform win|mac --parts [--from DIR] [--out DIR] [--fresh]
```

- Dzieli gotową paczkę (`analysis/work/dist/<platform>/Descent-Lektor-PL`) na części we wspólnym katalogu `analysis/work/dist/online/`: `python-*.zip` i `program-*.zip` osobno dla systemów, warstwy `audio-*.zip` wspólne. Obok leżą manifesty `lektor-win.json` i `lektor-mac.json`, indeks `lektor-mac.txt` (dla bash) i skrypty `instaluj-win.ps1`, `instalator-win.ps1`, `instaluj-mac.sh`.
- Katalog jest kumulatywny: kolejna budowa dokłada warstwę audio tylko z nowymi i zmienionymi plikami, a części, których nie używa żaden manifest, usuwa. `--fresh` zaczyna audio od nowa; wtedy budujemy oba systemy.
- Instalator Maca sprawdzamy w Git Bash jak skrypty paczki: atrapy `codesign`, `pbcopy`, `pgrep`, `xattr` i `PLISTBUDDY`, sztuczny `HOME` z `Library/Application Support/Steam` (appmanifest i `userdata/*/config/localconfig.vdf`) i `LEKTOR_ZRODLO` wskazujące katalog z częściami. Ścieżki w `PATH` w postaci `/c/...` (`cygpath -u`). Na Macu: skopiować `dist/online` i uruchomić `LEKTOR_ZRODLO=<folder> bash <folder>/instaluj-mac.sh`.
- Próba lokalna Windows bez wydania: serwer `.venv/Scripts/python -I -m http.server 47899 --bind 127.0.0.1 --directory analysis/work/dist/online`, potem w PowerShell (folder gry i lektora tymczasowe):

```powershell
$env:LEKTOR_ZRODLO = 'http://127.0.0.1:47899'; $env:LEKTOR_FOLDER = '<folder testowy>'; $env:LEKTOR_GRA = '<atrapa gry z plikiem Legends of the Dark.exe>'
irm http://127.0.0.1:47899/instaluj-win.ps1 | iex
```

### Wydanie w GitHub Releases (E10, D82)

GitHub CLI działa bez instalacji. Pobierz `gh_2.103.3_windows_amd64.zip` z https://github.com/cli/cli/releases/tag/v2.103.3, sprawdź SHA-256 (`98d0cfa794721665d7973dd728c78aff7bd836d58f10f6d7a03568eccb0a22e0`) i rozpakuj do `analysis/work/bin/gh-2.103.3/gh/`. Token leży w `analysis/work/bin/gh-config` (ignorowane w Git). Logowanie (na pytanie o uwierzytelnienie Git odpowiedz `n`):

```bash
export GH_CONFIG_DIR="$PWD/analysis/work/bin/gh-config" GH="$PWD/analysis/work/bin/gh-2.103.3/gh/bin/gh.exe"
"$GH" auth login --hostname github.com --git-protocol https --web
```

Wypchnięcie z pomocnikiem poświadczeń `gh` tylko dla tej komendy:

```bash
git -c credential.helper= -c "credential.helper=!'$GH' auth git-credential" push origin main --tags
```

Wydanie z paczkami z `analysis/work/dist/` (opis z zakresem i sumami SHA-256 w pliku w `analysis/work/out/`):

```bash
"$GH" release create v0.2.0 --repo wiQ1999/descent-lektor-pl --prerelease --title "..." --notes-file analysis/work/out/e10_release_notes.md analysis/work/dist/Descent-Lektor-PL-win.zip analysis/work/dist/Descent-Lektor-PL-mac.zip
```

Od E19 (D111) wydanie jest zwykłe i oznaczone jako najnowsze (`releases/latest/download` pomija prerelease) i oprócz zipów ma wszystkie pliki z `analysis/work/dist/online/` (części, manifesty, indeks i skrypty instalacji):

```bash
"$GH" release create vX.Y.Z --repo wiQ1999/descent-lektor-pl --latest --title "..." --notes-file analysis/work/out/<opis>.md analysis/work/dist/Descent-Lektor-PL-win.zip analysis/work/dist/Descent-Lektor-PL-mac.zip analysis/work/dist/online/*
```

Przed wydaniem z instalatorem:
- `bundle --platform win` i `--platform mac`, potem `bundle --platform win --parts` i `bundle --platform mac --parts`. Pierwsze wydanie z `--fresh` dla obu systemów (jedna warstwa audio); w `dist/online/` leżą wtedy tylko pliki z bieżących manifestów.
- W opisie wydania: komenda z `INSTRUKCJA.md` i zdanie dla graczy starej paczki (Windows: instalator zapyta o odinstalowanie, odpowiedź `T`; Mac: nową opcję uruchamiania wkleić w Steam ze schowka).
- Po wydaniu: komenda z `INSTRUKCJA.md` bez `LEKTOR_ZRODLO` na komputerze z lektorem z komendy (aktualizacja z GitHub) i, jeśli się da, na drugim komputerze (świeża instalacja i ewentualne ostrzeżenie antywirusa).

## 8. Opcjonalnie

- ElevenLabs: `analysis/tools/elevenlabs/README.md` i skill `.claude/skills/elevenlabs/SKILL.md`.
- Arkusz porównawczy głosów (E11): `analysis/tools/voice_compare.py pick` losuje kwestie z bazy M2 (stałe ziarno), a `score` i `sheet` oceniają próbki i budują strony w `analysis/work/compare/e11/` z szablonu `voice_compare.html`.
  - Próbki ElevenLabs powstają przez MCP według skilla: `text_to_voice` z opisami z `analysis/tools/voice_designs_e11.json` i tekstem `<głos>#design` z `lines.json`, do `analysis/work/elevenlabs/audio/e11/<głos>/<wariant>/0/`.
  - Podglądy losują głos, więc nowe próbki brzmią inaczej niż w naszej ocenie.
  - Runda 2 (D79): wybrany podgląd zapisuje `create_voice_from_preview`, a `text_to_speech` czyta tekst `<głos>#design` modelami z `R2_MODELS` do `analysis/work/elevenlabs/audio/e11r2/<głos>/<model>/`. Głosy i warianty są w `R2_VOICES` w `voice_compare.py`.
- Szacunek postaci bez dubbingu w całej grze (E14): `.venv/Scripts/python -I analysis/tools/no_dub_scope.py` czyta wszystkie grafy z kopii gry i bazę `m2.sqlite`. Kwestie z tekstem zapisuje w `analysis/work/out/no_dub_lines.jsonl`, a liczby według mówcy, aktu i źródła w `no_dub_summary.json` i na konsoli (raport `analysis/E14_NO_DUB_SCOPE.md`).
- Arkusz obsady E14 (D83): `analysis/tools/voice_compare_e14.py` z poleceniami `portrait`, `context`, `pick`, `refs`, `choose`, `status`, `score` i `sheet` w `.venv` oraz `design` i `clone` w środowisku OmniVoice (kolejność w nagłówku skryptu). Opisy głosów są w `analysis/tools/voice_designs_e14.json`, wyniki w `analysis/work/compare/e14/`. Runda 2 (D84): `refs2` i `score` w `.venv`, `clone2` w środowisku OmniVoice, potem `sheet2` (strona `runda2.html`). Runda 3 (D87): podglądy z opisów `el3` (a, b, c) przez MCP do `…/<głos>/design3<a|b|c>/`, potem `score` i `sheet3` (strona `runda3.html`). Runda 4 (D88) tak samo z opisami `el4` (a–e) Delphyndry i `sheet4` (strona `runda4.html`). Runda 5 (D89): opisy `el5`, `score`, `fx5` (efekt smoka, lokalnie), znowu `score`, potem `sheet5` (strona `runda5.html`). Runda 6 (D90): opisy `el6`, `score` i `sheet6` (strona `runda6.html`). Runda 7 (D91): `refs7` w `.venv`, `clone7` w środowisku OmniVoice, `score`, w razie błędów `retake7` (OmniVoice), `score` i `pick7`, potem `sheet7` (strona `runda7.html`). Runda 8 (D92): podglądy z opisu `el8` przez MCP do `…/delphyndra/design8a/`, `refs8` w `.venv`, `clone8` w środowisku OmniVoice, `score`, w razie błędów `retake8`, `score` i `pick8`, potem `sheet8` (strona `runda8.html`). Runda 9 (D93): `refs9` w `.venv`, `clone9` w środowisku OmniVoice, `score`, w razie błędów `retake9`, `score` i `pick9`, potem `eq9` (barwa jak B, korektor na nagraniach), `score` i `sheet9` (strona `runda9.html`). Na koniec `adopt` kopiuje wybrane klony do bazy referencji (D95).
- Wstawki sceniczne (D86): `.venv/Scripts/python -I analysis/tools/inserts_scan.py [--release m3]` zapisuje listę z tekstami w `analysis/work/out/m3_inserts.jsonl` i raport `analysis/E14_INSERTS.md`.
  - Próbki ElevenLabs powstają przez MCP według skilla: `text_to_voice` z opisem `el` i tekstem `<głos>#design` z `lines.json` do `analysis/work/elevenlabs/audio/e14/<głos>/design/` (katalog trzeba utworzyć wcześniej), potem `create_voice_from_preview` z podglądu wskazanego przez `status` i `text_to_speech` eleven_v4 drugiego fragmentu do `…/<głos>/v4/`.
- Build macOS do analizy (DepotDownloader, logujesz się sam): `analysis/MAC_REPORT.md`.
- Testy w grze i replay dzienników: `docs/E1_PLAYTEST.md`, `docs/E5_PLAYTEST.md`, `docs/E7_MAC_SESSION.md`.

## Czego nie da się odtworzyć 1:1

- **Podejścia audio:** model losuje, więc nowe podejścia brzmią trochę inaczej. Automat wybiera je jednak według tych samych zasad.
- **Oceny z odsłuchu i dzienniki z gry:** to wyniki sesji użytkownika, z treścią gry, więc nie trafiają do repozytorium. Wnioski z nich są w raportach i w `docs/DECISIONS.md`.
- **Zapisy gry:** ich kopie leżą tylko w `analysis/work/saves`.
