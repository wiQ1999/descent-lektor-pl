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
| `kehli` | `KEHLI` | dubbing, klipy `QuestSelect_3`, `DefeatEnemy_3`, `QuestLost_4` | 9,4 s | `64fd3c8f` | D06, D55, D67; M1 miało referencję `3bc86e98` |
| `chance` | `CHANCE` (Fuks) | dubbing | 9,4 s | `ec82e7c0` | D06 |
| `nekrul` | `BLOOD_SISTER` (Ne’Krul) | dubbing | 5,7 s | `c477e56c` | D19 |
| `xenith` | `DRAGON_HYBRID` (Xenith) | dubbing, klipy `Xenith_Spawn_2`, `Xenith_Spawn_1` | 7,8 s | `297ce273` | D19, D68 |

## Głosy projektowane (D41)

Narzędzie: `analysis/tools/npc_voices.py` (portret, pula kandydatów, wybór 4 najbardziej różnych barw, klony kwestii do odsłuchu). Tekst referencji jest własny, nie z gry.

| Głos | Mówca w grze | Portret i charakter | Opis głosu (instruct) | Ziarno | Tekst i tempo referencji | Stan |
|---|---|---|---|---|---|---|
| `adelynn` | `BARONESS_ADELYNN` | starsza kobieta, szlachcianka, bardzo poukładana; mówi zbyt pewnie siebie, szlacheckim tonem | `female, elderly, low pitch` | 11 | wyniosłe zdanie o rodzie, 9,5 zn./s; 9,2 s, SHA `a5b7bc13` | wybrana 2026-11-01 (kandydat 1 z 4, ok. 180 Hz); po E5 do ponownego doboru (D55) |
| `ronan` | `RONAN` | potężny wojownik jak wiking, jasna broda, pandka na ramieniu; głos niski, urywany | `male, elderly, very low pitch` | 29 | urywane frazy, 7,5 zn./s; 9,5 s, SHA `c7fccc1c` | wybrany w QA E7 (D68), 3 podejścia na fragment; M1 miało inny głos |
| `astarra` | `ASTARRA` | dojrzała czarodziejka z kosturem, surowe spojrzenie; mówi stanowczo i chłodno | `female, elderly, moderate pitch` | 5 | wyniosłe zdanie w stylu Adelynn, 10,5 zn./s; 9,4 s, SHA `ec7dbea1` | wybrany w QA E7 (D67), kandydat `adelynn_d3_s5` |
| `kathryn` | `KATHRYN` | duch młodej kobiety w podartej sukni; smutny, zawodzący | `female, young adult, low pitch` | 29 | zdanie w stylu postaci; 8,5 s, SHA `105babf2` | wybrany w QA E7 (D68) |
| `ltrand` | `LTRAND` | młoda oficerka w zbroi; rzeczowa, głos dowódcy | `female, young adult, moderate pitch` | 29 | zdanie w stylu postaci; 7,8 s, SHA `eb5ebaf4` | wybrany w QA E7 (D68) |
| `bruli` | `MASTERBRULI` | starszy krępy krasnolud; zrzędliwy, skrupulatny mistrz | `male, middle-aged, low pitch` | 29 | zdanie w stylu postaci; 7,9 s, SHA `1680b8ba` | wybrany w QA E7 (D68) |
| `herbie` | `HERBIE` | chudy wieśniak z kilofem; gadatliwy cwaniaczek | `male, middle-aged, low pitch` | 5 | zdanie w stylu postaci; 6,3 s, SHA `4c2eac83` | wybrany w QA E7 (D68) |
| `mok` | `ELDERMOK` | stary orkowy szaman z kosturem; niski, chrapliwy, powolny | `male, middle-aged, very low pitch` | 5 | zdanie w stylu postaci; 8,6 s, SHA `cd51f9fa` | wybrany w QA E7 (D68) |
| `outlaw` | `OUTLAWPRINCE` | potężny mężczyzna w ciężkiej zbroi; arogancki przywódca | `male, middle-aged, very low pitch` | 17 | zdanie w stylu postaci; 6,1 s, SHA `c3baa7be` | wybrany w QA E7 (D68) |
| `flint` | `MASTERFLINT` | krzepki krasnolud kowal, gęsta ruda broda; serdeczny, wesoły | `male, middle-aged, moderate pitch` | 17 | zdanie w stylu postaci; 8,7 s, SHA `0e586296` | wybrany w QA E7 (D69) |

Kwestie NPC mają tempo dialogów z D34, jak bohaterowie; charakter daje referencja.

Historia:
- Runda 1 (2026-11-01, bez portretu, neutralny tekst referencji): żaden kandydat nie pasował do postaci.
- Runda 2 (2026-11-01, portret, zdanie w stylu postaci): 12 kandydatów na postać (4 opisy × 3 ziarna), wszyscy bez błędów ASR; do odsłuchu 4 najbardziej różne barwy.
- Runda E7/1 (2026-11-04, Astarra, Adelynn, Ronan, Kehli): Astarra dostała głos z puli Adelynn, Adelynn została przy obecnym, Kehli ma referencję `kehli_srodek`, a Ronan idzie do rundy 1b: niski, urywany, z chrypą (D67).
- Runda E7/1b (2026-11-04, Ronan): urywany tekst referencji, 18 kandydatów, warianty z chrypą w referencji i po wygenerowaniu. Wygrał kandydat bez dodatkowej chrypy (D68).
- Rundy E7/2 i E7/3 (2026-11-05): Kathryn, Rand, Bruli, Xenith, Herbie, Mok, Banita. Strony odsłuchu pokazywały też głosy już wybrane (D68).
