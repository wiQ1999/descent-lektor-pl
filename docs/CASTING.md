# Obsada głosów

Rejestr wybranych głosów postaci. Zasady: D06 (klony z dubbingu), D19 (złoczyńcy), D36 (głos systemowy), D41 (projekt głosu dla postaci bez dubbingu).

Referencje leżą prywatnie w `analysis/work/lektor/refs/` (`refs.json`: plik, transkrypcja, długość, SHA-1). Skrót SHA wchodzi do klucza cache fragmentów, więc zmiana referencji wymusza ponowne wygenerowanie audio tego głosu.

## Głosy z dubbingu

Wycinki do 10 s z neutralnych referencji dubbingu, cięte na granicach słów (D33, `python -m lektor refs`).

| Głos | Mówca w grze | Źródło | Referencja | SHA | Decyzja |
|---|---|---|---|---|---|
| `narrator` | narrator, głos systemowy, `VARIABLE_HERO` | dubbing | 9,3 s | `edb64551` | D06, D17, D36 |
| `brynn` | `BRYNN` | dubbing | 8,9 s | `d717a241` | D06 |
| `syrus` | `SYRUS` | dubbing | 9,5 s | `b19b1b16` | D06 |
| `galaden` | `GALADEN` | dubbing | 7,6 s | `0ea7eacb` | D06, D18 |
| `vaerix` | `VAERIX` | dubbing | 9,3 s | `b1bec8e9` | D06 |
| `kehli` | `KEHLI` | dubbing | 7,5 s | `3bc86e98` | D06; po E5 do ujednolicenia modulacji (D55) |
| `chance` | `CHANCE` (Fuks) | dubbing | 9,4 s | `ec82e7c0` | D06 |
| `nekrul` | `BLOOD_SISTER` (Ne’Krul) | dubbing | 5,7 s | `c477e56c` | D19 |

## Głosy projektowane (D41)

Narzędzie: `analysis/tools/npc_voices.py` (portret, pula kandydatów, wybór 4 najbardziej różnych barw, klony kwestii do odsłuchu). Tekst referencji jest własny, nie z gry.

| Głos | Mówca w grze | Portret i charakter | Opis głosu (instruct) | Ziarno | Tekst i tempo referencji | Stan |
|---|---|---|---|---|---|---|
| `adelynn` | `BARONESS_ADELYNN` | starsza kobieta, szlachcianka, bardzo poukładana; mówi zbyt pewnie siebie, szlacheckim tonem | `female, elderly, low pitch` | 11 | wyniosłe zdanie o rodzie, 9,5 zn./s; 9,2 s, SHA `a5b7bc13` | wybrana 2026-11-01 (kandydat 1 z 4, ok. 180 Hz); po E5 do ponownego doboru (D55) |
| `ronan` | `RONAN` | dojrzały, umięśniony, rosły chłop jak wiking; głos waleczny, w szalonym tonie | `male, elderly, very low pitch` | 37 | bojowy okrzyk, 11,5 zn./s; 7,0 s, SHA `b57b0f1e` | wybrany 2026-11-01 (kandydat 3 z 4, ok. 95 Hz, najbliżej wysokości narratora); po E5 do ponownego doboru (D55) |

Kwestie NPC mają tempo dialogów z D34, jak bohaterowie; charakter daje referencja.

Historia:
- Runda 1 (2026-11-01, bez portretu, neutralny tekst referencji): żaden kandydat nie pasował do postaci.
- Runda 2 (2026-11-01, portret, zdanie w stylu postaci): 12 kandydatów na postać (4 opisy × 3 ziarna), wszyscy bez błędów ASR; do odsłuchu 4 najbardziej różne barwy.
