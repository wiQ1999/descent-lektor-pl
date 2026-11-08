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
- Instalację w grze opisuje `docs/INSTRUKCJA.md`.
- Każda paczka ma `LICENSE.md`, `UZNANIE_AUTORSTWA.md` (szablon w `src/bundle/`) i licencję Doorstop w `licencje/`.

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

## 8. Opcjonalnie

- ElevenLabs: `analysis/tools/elevenlabs/README.md` i skill `.claude/skills/elevenlabs/SKILL.md`.
- Arkusz porównawczy głosów (E11): `analysis/tools/voice_compare.py pick` losuje kwestie z bazy M2 (stałe ziarno), a `score` i `sheet` oceniają próbki i budują strony w `analysis/work/compare/e11/` z szablonu `voice_compare.html`.
  - Próbki ElevenLabs powstają przez MCP według skilla: `text_to_voice` z opisami z `analysis/tools/voice_designs_e11.json` i tekstem `<głos>#design` z `lines.json`, do `analysis/work/elevenlabs/audio/e11/<głos>/<wariant>/0/`.
  - Podglądy losują głos, więc nowe próbki brzmią inaczej niż w naszej ocenie.
  - Runda 2 (D79): wybrany podgląd zapisuje `create_voice_from_preview`, a `text_to_speech` czyta tekst `<głos>#design` modelami z `R2_MODELS` do `analysis/work/elevenlabs/audio/e11r2/<głos>/<model>/`. Głosy i warianty są w `R2_VOICES` w `voice_compare.py`.
- Build macOS do analizy (DepotDownloader, logujesz się sam): `analysis/MAC_REPORT.md`.
- Testy w grze i replay dzienników: `docs/E1_PLAYTEST.md`, `docs/E5_PLAYTEST.md`, `docs/E7_MAC_SESSION.md`.

## Czego nie da się odtworzyć 1:1

- **Podejścia audio:** model losuje, więc nowe podejścia brzmią trochę inaczej. Automat wybiera je jednak według tych samych zasad.
- **Oceny z odsłuchu i dzienniki z gry:** to wyniki sesji użytkownika, z treścią gry, więc nie trafiają do repozytorium. Wnioski z nich są w raportach i w `docs/DECISIONS.md`.
- **Zapisy gry:** ich kopie leżą tylko w `analysis/work/saves`.
