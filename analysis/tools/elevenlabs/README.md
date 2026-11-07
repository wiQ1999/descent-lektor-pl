# ElevenLabs: serwer MCP i pomiar zużycia

Lokalny serwer `elevenlabs-mcp` 0.12.2 działa tylko w tym repozytorium (D73). Każde płatne wywołanie narzędzia zapisuje koszt w kredytach. Kredyty to licznik `character_count` konta, nie tokeny Claude.

## Pliki

| Plik | Git | Rola |
|---|---|---|
| `.mcp.json` | tak | serwer `elevenlabs` w zakresie projektu |
| `.claude/settings.json` | tak | hooki zużycia, narzędzia bezpłatne bez pytania o zgodę |
| `.claude/commands/zuzycie.md` | tak | komenda `/zuzycie` |
| `analysis/tools/elevenlabs/` | tak | `launch_mcp.py`, `usage_hook.py`, `usage_report.py`, `common.py` |
| `tests/elevenlabs/` | tak | testy bez sieci |
| `.env.elevenlabs.local` | nie | klucz API |
| `analysis/work/elevenlabs/audio/` | nie | audio z serwera |
| `analysis/work/elevenlabs/usage/` | nie | `elevenlabs.jsonl`, `pending/`, `errors.log` |

## Instalacja

1. Zainstaluj `uv`, jeśli go nie ma.
2. Skopiuj `.env.elevenlabs.local.example` do `.env.elevenlabs.local` i wpisz klucz. Klucz musi mieć prawo odczytu konta i historii, inaczej pomiar działa tylko z licznika albo wcale.
3. Uruchom `claude` w katalogu repozytorium i zatwierdź serwer `elevenlabs` z `.mcp.json`.
4. Otwórz nową sesję. `claude mcp list` pokazuje wtedy `elevenlabs` jako połączony.

## Użycie

Narzędzia to `mcp__elevenlabs__<nazwa>`. Odczyty działają bez pytania, a płatne narzędzia pytają o zgodę. Blokad `deny` nie ma (D73).

Raport: `/zuzycie` w sesji albo bezpośrednio:

```bash
uv run --no-project --python 3.13 analysis/tools/elevenlabs/usage_report.py [--period current|all] [--by day|voice|model|tool|session] [--csv PLIK] [--offline]
```

Testy:

```bash
.venv/Scripts/python -I -m pytest tests/elevenlabs
```

## Jak liczymy koszt

- Hook `pre` zapamiętuje licznik konta, a hook `post` dopasowuje wpis z historii konta po tekście, czasie i głosie.
- `method: history`: różnica liczników z wpisu historii, źródło główne.
- `method: subscription_delta`: różnica licznika konta przed i po wywołaniu. To zapas dla narzędzi spoza historii TTS.
- Licznik konta dogania wywołanie z opóźnieniem do około minuty, więc zerowa różnica nie znaczy zerowego kosztu. Taki rekord bez wpisu w historii ma flagę `unmeasured`.
- `text_to_voice` nie ma wpisu w historii, więc zwykle kończy się flagą `unmeasured`. Jego koszt widać w raporcie w wierszu „konto minus log”. W teście wyniósł 1 kredyt na znak tekstu podglądu.
- `create_voice_from_preview` nie kosztuje kredytów (zajmuje miejsce na głos), więc hook je pomija.
- Modele v3 i v4 mają w historii pusty `text` i `voice_id`. Tekst i głos leżą w polu `dialogue`.
- Log trzyma SHA-1 i długość tekstu. Tekstu nie zapisuje.

| Flaga | Znaczenie |
|---|---|
| `mismatch` | licznik drgnął, ale podaje co innego niż historia, `credits` pochodzi z historii |
| `unmeasured` | brak wpisu w historii i licznik nie drgnął albo nie odpowiada, np. opóźnienie licznika, awaria sieci, brak klucza |
| `tool_error` | narzędzie zwróciło błąd, koszt z różnicy licznika |

Hook zawsze kończy się kodem 0, a zapytania mają limit 5 s. Błędy trafiają do `errors.log`.

## Ocena próbek

`score_samples.py` ocenia próbki tym samym automatem co E3: ASR, końcówka, tempo, barwa wobec referencji i F0. Uruchamiamy go w `.venv`:

```bash
.venv/Scripts/python -I analysis/tools/elevenlabs/score_samples.py [plik ...]
```

## Odinstalowanie

1. Usuń `.mcp.json` albo wpis `elevenlabs` w tym pliku.
2. Usuń `hooks` i wpisy `mcp__elevenlabs__` z `.claude/settings.json`.
3. Usuń `.claude/commands/zuzycie.md` i `analysis/tools/elevenlabs/`.
4. Usuń `.env.elevenlabs.local`, a klucz unieważnij w panelu ElevenLabs.
5. Opcjonalnie usuń `analysis/work/elevenlabs/`.
6. Jeśli zatwierdzenie serwera ma zniknąć, usuń `elevenlabs` z `.claude/settings.local.json` albo uruchom `claude mcp reset-project-choices`.
