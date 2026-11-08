# Obsada głosów

Rejestr wybranych głosów postaci. Zasady: D06 (klony z dubbingu), D19 (złoczyńcy), D36 (głos systemowy), D41 (projekt głosu dla postaci bez dubbingu), D80 (postacie bez dubbingu w ElevenLabs).

Referencje leżą w `analysis/work/lektor/refs/` (`refs.json`: plik, transkrypcja, długość, SHA-1). Skrót SHA wchodzi do klucza cache fragmentów, więc zmiana referencji wymusza ponowne wygenerowanie audio tego głosu.

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

## Głosy ElevenLabs dla postaci bez dubbingu (D80)

Od E11 postacie bez dubbingu czyta ElevenLabs `eleven_v4` z ustawieniami domyślnymi (stability 0,5, similarity 0,75, style 0, speed 1,0). Głosy powstały z opisów w `analysis/tools/voice_designs_e11.json` (`text_to_voice`, D78) i są zapisane na koncie jako `Lektor PL - <głos> <wariant>`. Głosy OmniVoice z tabeli niżej zostają jako zapas.

| Głos | Wariant | voice_id | Ocena: podgląd (runda 1) / v4 (runda 2) | Uwagi |
|---|---|---|---|---|
| `adelynn` | b | `dH4FrDMHSw1B31tzWOPw` | 4 / 3 | remis z OmniVoice w rundzie 1; zamyka ponowny dobór z D55 |
| `ronan` | b | `7ScqSXmT0oXvHenzw9hJ` | 5 / 4 | |
| `astarra` | b | `B9Xmu9MUTLL4L5SIDsAD` | 5 / 5 | remis z c |
| `kathryn` | a | `JZzQvOujFtUu9vpAsm2q` | 5 / 5 | remis z c |
| `ltrand` | a | `OLeMFzYjewG73PEGvePC` | 4 / 3 | |
| `bruli` | a | `UDpt5qLmStrzpqQQZI9G` | 5 / 5 | remis z b i c |
| `herbie` | c | `BFwE7UC8qCq4bda0mhyE` | 5 / 4 | |
| `mok` | a | `SQ2Rf1tdmOCUqClP6qJ4` | 4 / 4 | remis z b |
| `outlaw` | b | `6yCDeMiG8Fnpn0gPqxz3` | 5 / 5 | |
| `flint` | a | `gfzrH3j2kaDI5cNZuaPW` | 5 / 5 | remis z c |
| `galgoraz` | a | `Quk21RWppOlJmKTYBeGr` | 5 / 5 | remis z c |

## E14: nowe postacie bez dubbingu w ElevenLabs (D84)

Głosy z opisów w `analysis/tools/voice_designs_e14.json` (`text_to_voice`, jeden opis z portretu i kontekstu kwestii), zapisane jako `Lektor PL - <postać> E14`. W ślepym porównaniu z OmniVoice wygrał ElevenLabs, więc OmniVoice dla tych postaci odpada. Ustawienia jak wyżej.

| Głos | Mówca w grze | voice_id | Stan |
|---|---|---|---|
| `magrit` | `BARONESSMAGRIT` | `4z2ttMe9kFzyBLgroafB` | przyjęty w rundzie 1 |
| `alys` | `ALYS` | `PzYUKC9HYBoJ4OGyP1QE` | przyjęty w rundzie 1 |
| `greigory` | `GREIGORY` | `1iufCs0OK7CV8njHiko7` | przyjęty w rundzie 1 |
| `button` | `BUTTON` | `RMWgUKFzzgxce9riuhEC` | przyjęty w rundzie 1 |
| `laurel` | `LAUREL` | `YpSjl2k2ogKW014dXeX3` | przyjęty w rundzie 1 |
| `arden` | `ARDEN` | `jl1qd5mvirQo588r4kkX` | przyjęty w rundzie 1 |
| `veta` | `VETA` | `0rtBIPGtLS4yt8kPC7Cs` | przyjęty w rundzie 1 |
| `trevalyn` | `TREVALYN` | `PnphcFpQiiZTzbeOcbxp` | przyjęty w rundzie 1 |
| `balthain` | `SIRBALTHAIN` | `9CdwdaxrlepOclY1rmY5` | przyjęty w rundzie 1 |
| `ducard` | `COUNTESSDUCARD` | `m5FL5XfqLXQEY9dOd5GJ` | przyjęty w rundzie 1 |
| `pryor` | `PRYOR` | `6gJmPw2772iK66WdPEKX` | przyjęty w rundzie 1 |
| `grace` | `GRACE` | `7nGRsoaWpcG4aZ7JLbJW` | przyjęty w rundzie 1; opis z wiekiem 18–20, bo `text_to_voice` odrzuca wiek poniżej 18 |
| `drys` | `DRYS` | `UrUMN6EMRqqvJz3oDHD1` | przyjęty w rundzie 1 |
| `waiqar` | `WAIQAR` | `IQY1bvB4YbPVoS6Go9q3` | przyjęty w rundzie 2 (opis `el2`: doświadczony wojownik), głos z rundy 1 usunięty |
| `morant` | `MORANT` | `3CNDe9njN2kEBkgjZlEi` | przyjęty w rundzie 2 (opis `el2`), głos z rundy 1 usunięty |
| `delphyndra` | `DELPHYNDRA` | `1sr70RNkbV4TmYCh7tKG` (runda 1) | runda 6: wielka, krwiożercza smoczyca, wyraźnie kobieca, bez efektu (D90) |
| `nara` | `NARA` | `peH5NmVUWPLR3C6OwCIg` | przyjęta w rundzie 3 (opis `el3` c: stara orczyca), głos z rundy 1 usunięty |
| `meza` | `MEZA` | `6QqpmxamtHSBJVCpfj8E` | przyjęta w rundzie 3 (opis `el3` a: lodowaty szept), głos z rundy 1 usunięty |

Postać z wybranym nowym wariantem dostaje nowy głos na koncie, a głos z rundy 1 usuwamy (zgoda z QA, D84). Runda 3 (D87): trzy opisy `el3` na postać. Runda 4 (D88): pięć opisów `el4` dla Delphyndry.

## E14: złoczyńcy z okrzykami dubbingu w OmniVoice (D83, D84)

Klony OmniVoice z okrzyków albo monologów z gry, jak Ne’Krul i Xenith (D19). Referencje do 10 s w `analysis/work/compare/e14/omni/refs.json`; do bazy referencji trafią przed generowaniem.

| Głos | Mówca w grze | Źródło referencji | Długość | Stan |
|---|---|---|---|---|
| `zachareth` | `BARONZACHARETH` | monolog `DLE04_4_Betrayal_Zachareth_VoiceOver` | 8,1 s | przyjęty w rundzie 1 |
| `reneyr` | `RENEYR`, `SHADOW_RENEYR` | monolog `DLE04_4_Betrayal_Reneyr_VoiceOver` | 7,5 s | przyjęty w rundzie 1 |
| `greysdon` | `GREYSDON` | okrzyki `Greysdon_Spawn_2`, `Greysdon_Spawn_1` | 7,2 s | przyjęty w rundzie 1 |
| `navoth` | `NAVOTH` | okrzyki | 6,4 s | przyjęty w rundzie 1 |
| `vraskhar` | `VRASKHAR` | okrzyki | 6,6 s | przyjęty w rundzie 1 |
| `levirax` | `LEVIRAX` | monolog `Levirax_VoiceOver` | 8,5 s | przyjęty w rundzie 2: wariant `levirax_v2a`, tempo 0,85 (przeciągane końcówki) |
| `gilliam` | `GILLIAM`, `GILLIAM_EVIL` | okrzyki z drżeniem 0,6 | 5,3 s | przyjęty w rundzie 2: wariant `gilliam_v2b` (bardziej przerażony) |

Referencje wariantów z rundy 2 są w `analysis/work/compare/e14/omni/refs2.json`.

## Głosy projektowane w OmniVoice (D41, zapas od D80)

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
| `galgoraz` | `MASTERGALGORAZ` | stary smokowiec w ochrowej szacie, rogi, biała broda; bardzo stary mędrzec, głos starczy, drżący | `male, elderly, very low pitch` | 53 | wolne frazy, 7 zn./s, drżenie dodane do referencji; 13,07 s, SHA `f882e69f` | wybrany w QA E7 (D69), runda 4b |

Kwestie NPC mają tempo dialogów z D34, jak bohaterowie; charakter daje referencja.

Historia:
- Runda 1 (2026-11-01, bez portretu, neutralny tekst referencji): żaden kandydat nie pasował do postaci.
- Runda 2 (2026-11-01, portret, zdanie w stylu postaci): 12 kandydatów na postać (4 opisy × 3 ziarna), wszyscy bez błędów ASR; do odsłuchu 4 najbardziej różne barwy.
- Runda E7/1 (2026-11-04, Astarra, Adelynn, Ronan, Kehli): Astarra dostała głos z puli Adelynn, Adelynn została przy obecnym, Kehli ma referencję `kehli_srodek`, a Ronan idzie do rundy 1b: niski, urywany, z chrypą (D67).
- Runda E7/1b (2026-11-04, Ronan): urywany tekst referencji, 18 kandydatów, warianty z chrypą w referencji i po wygenerowaniu. Wygrał kandydat bez dodatkowej chrypy (D68).
- Rundy E7/2 i E7/3 (2026-11-05): Kathryn, Rand, Bruli, Xenith, Herbie, Mok, Banita. Strony odsłuchu pokazywały też głosy już wybrane (D68).
- Rundy E7/4 i 4b (2026-11-05): Flint z pierwszej próby. Galgoraz w drugiej: 30 kandydatów, 9 do odsłuchu, dobranych tak, by różnili się też od Bruliego, Herbiego, Flinta i Ronana (D69).
