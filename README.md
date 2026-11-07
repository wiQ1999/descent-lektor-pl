# Lektor PL dla Descent: Legends of the Dark

Nieoficjalny, niekomercyjny polski lektor TTS do aplikacji gry planszowej *Descent: Legends of the Dark* (pol. *Descent: Legendy Mroku*, Fantasy Flight Games).

- Plugin w grze wysyła zdarzenia okien (klucz, argumenty, tekst, mówca) do lokalnego procesu companion.
- Companion odtwarza pregenerowane audio głosami zbliżonymi do polskiego dubbingu.

Projekt działa na Windows i na Macu z Apple Silicon. Szczegóły i uzasadnienie są w [analysis/REPORT.md](analysis/REPORT.md), a etapy w [docs/PLAN.md](docs/PLAN.md).

## Licencja i wydania

- Warunki korzystania: [LICENSE.md](LICENSE.md).
- Repozytorium nie zawiera treści gry (tekstów, grafik, nagrań, kodu), modeli ani wygenerowanego audio. Narzędzia odtwarzają je lokalnie z kopii aplikacji użytkownika.
- Gotowe paczki dla Windows i Maca (audio, plugin, companion, instalator i instrukcja) będą w wydaniach GitHub Releases. Gracz pobiera jeden plik dla swojego systemu.

## Odtworzenie od zera

Pełna instrukcja: [docs/ODTWORZENIE.md](docs/ODTWORZENIE.md). Obejmuje kopię gry, środowiska Python, modele, bazę kwestii, audio, plugin i paczkę.

## Układ folderów

```
LICENSE.md, README.md, CLAUDE.md (zasady pracy z Claude Code)
docs/              PLAN.md, DECISIONS.md, CASTING.md, ODTWORZENIE.md, INSTRUKCJA.md, instrukcje testów w grze
analysis/          raporty z analiz (REPORT.md, VOICES.md, E*_*.md)
  envs/            wersje pakietów środowisk (.venv, OmniVoice) i skrypt create_envs.sh
  tools/           skrypty analityczne (Python, UnityPy), elevenlabs/ (serwer MCP i pomiar zużycia)
  work/            kopia gry, baza kwestii, audio, modele, paczki: NIE jest śledzony w Git
src/
  lektor/          pakiet Python: baza kwestii, referencje, generowanie i ocena audio, companion, paczka
  plugin/          plugin do gry (C#): Core, Loader (Doorstop), BepInEx (zapas), skrypty instalacji
  bundle/          szablony paczki Descent-Lektor-PL (Windows, macOS) i przypięte pobrania
tests/             pytest (własne zdania testowe, bez tekstów gry)
```

## Zasady

- Pliki gry i `LocalLow` są tylko do odczytu. Analiza działa na kopiach w `analysis/work/`.
- Wyniki z treścią gry (teksty, audio, dekompilacja, próbki TTS) zostają w `analysis/work/` i nie trafiają do repozytorium.
- Raporty podają klucze, nazwy i liczby, bez pełnych tekstów kwestii.
