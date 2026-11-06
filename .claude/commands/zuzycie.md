---
description: Raport zużycia kredytów ElevenLabs (suma, proporcja do limitu, uzgodnienie z kontem)
argument-hint: "[--period current|all] [--by day|voice|model|tool|session] [--csv PLIK] [--offline]"
---

Uruchom przez Bash, z katalogu głównego repozytorium:

```bash
uv run --no-project --python 3.13 analysis/tools/elevenlabs/usage_report.py $ARGUMENTS
```

Przedstaw wynik w kilku zdaniach: zużycie projektu, proporcja do limitu, pozostałe kredyty, data resetu i zużycie spoza projektu. Wymień rekordy z flagami, jeśli są. Nie wywołuj narzędzi MCP.
