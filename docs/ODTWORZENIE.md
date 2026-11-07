# Odtworzenie projektu od zera

Repozytorium nie zawiera treści gry, modeli ani wygenerowanego audio (D75, D76). Gotowe paczki z audio będą w wydaniach GitHub Releases (etap E10). Ta instrukcja pozwala zbudować wszystko samodzielnie w `analysis/work/`, z kopii aplikacji na Twoim komputerze. Komendy uruchamiamy z katalogu głównego repozytorium w Git Bash, chyba że blok mówi inaczej.

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

```bash
.venv/Scripts/python -I -m lektor evaluate --release m2
```

```bash
.venv/Scripts/python -I -m lektor select --release m2
```

- Po `select` powtarzamy `generate --retake`, `evaluate` i `select` do trzech razy.
- Na końcu `finalize --release m2` tworzy pliki końcowe i stronę odsłuchu.
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
- Gotowe paczki publikujemy w GitHub Releases (D76, etap E10).
- Instalację w grze opisuje `docs/INSTRUKCJA.md`.

## 8. Opcjonalnie

- ElevenLabs: `analysis/tools/elevenlabs/README.md`.
- Build macOS do analizy (DepotDownloader, logujesz się sam): `analysis/MAC_REPORT.md`.
- Testy w grze i replay dzienników: `docs/E1_PLAYTEST.md`, `docs/E5_PLAYTEST.md`, `docs/E7_MAC_SESSION.md`.

## Czego nie da się odtworzyć 1:1

- **Podejścia audio:** model losuje, więc nowe podejścia brzmią trochę inaczej. Automat wybiera je jednak według tych samych zasad.
- **Oceny z odsłuchu i dzienniki z gry:** to wyniki sesji użytkownika, z treścią gry, więc nie trafiają do repozytorium. Wnioski z nich są w raportach i w `docs/DECISIONS.md`.
- **Zapisy gry:** ich kopie leżą tylko w `analysis/work/saves`.
