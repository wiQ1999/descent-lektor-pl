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
| `delphyndra` | `DELPHYNDRA` | – (OmniVoice) | przyjęta w rundzie 9 (próbka A): klon OmniVoice `delph_b_jasniej` z `refs9.json`, monolog Leviraxa 3 półtony niżej, instrukcja „female”, tempo 0,85 (D94); głos ElevenLabs z rundy 1 usunięty (D95) |
| `nara` | `NARA` | `peH5NmVUWPLR3C6OwCIg` | przyjęta w rundzie 3 (opis `el3` c: stara orczyca), głos z rundy 1 usunięty |
| `meza` | `MEZA` | `6QqpmxamtHSBJVCpfj8E` | przyjęta w rundzie 3 (opis `el3` a: lodowaty szept), głos z rundy 1 usunięty |

Postać z wybranym nowym wariantem dostaje nowy głos na koncie, a głos z rundy 1 usuwamy (zgoda z QA, D84). Runda 3 (D87): trzy opisy `el3` na postać. Runda 4 (D88): pięć opisów `el4` dla Delphyndry.

## E14: złoczyńcy z okrzykami dubbingu w OmniVoice (D83, D84)

Klony OmniVoice z okrzyków albo monologów z gry, jak Ne’Krul i Xenith (D19). Referencje do 10 s w `analysis/work/compare/e14/omni/refs.json`. Od 2026-11-09 są w bazie referencji (`voice_compare_e14.py adopt`, D95), razem z Delphyndrą.

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

## E16: mówcy jednorazowi w oknach narratora (D101, paczka testowa `t1`)

Wypowiedzi postaci w oknach narratora czyta postać wskazana w tekście albo w kontekście (`src/lektor/data/speakers_t1.json`). Mówcy bez imienia i bez obsady dostali głosy testowe: losowe projekty OmniVoice bez portretu i bez QA, wybrane automatem (`analysis/tools/new_voices_t1.py`). Ziarno: najmniejszy CER, wysokość w zakresie płci, a z dobrych to, które leży najdalej od narratora i głosów wybranych wcześniej. Każdy głos ma własne zdanie w stylu postaci (nie tekst gry). Najbliższe pary barwy: `nv_wiezien`~`nv_fanatyk` i `nv_ynfernael`~`nv_nekromanta` (0,919). Widmo w pierwszej wersji było za blisko kowalki (0,949), więc dostało szept.

| Głos | Kto mówi | Opis OmniVoice | Ziarno | Referencja | Kwestie |
|---|---|---|---:|---|---:|
| `nv_bandyta` | bandyta, okrzyki w walce | `male, young adult, high pitch` | 23 | 8,4 s, SHA `cfadd386` | 3 |
| `nv_wiesniak` | uwolniony wieśniak (Q1) | `male, elderly, moderate pitch` | 23 | 8,9 s, SHA `f523a4bb` | 4 |
| `nv_straznik` | ranny strażnik w piwnicy (Q1) | `male, middle-aged, low pitch` | 37 | 9,1 s, SHA `3538bd60` | 3 |
| `nv_wiezien` | uwolniony więzień (Q1) | `male, young adult, moderate pitch` | 23 | 7,6 s, SHA `4654b2b1` | 1 |
| `nv_orban` | rozczochrany mężczyzna z łopatą (boss) | `male, middle-aged, high pitch` | 23 | 8,2 s, SHA `7c0660e6` | 2 |
| `nv_fanatyk` | fanatyk, okrzyki w walce | `male, young adult, low pitch` | 37 | 7,8 s, SHA `62856326` | 3 |
| `nv_eurth` | Pani Kości (boss) | `female, middle-aged, low pitch` | 37 | 8,6 s, SHA `746f2df2` | 1 |
| `nv_ynfernael` | głos z Ynfernaelu | `male, elderly, very low pitch, whisper` | 11 | 8,0 s, SHA `9d547553` | 1 |
| `nv_fae` | fae, okrzyki w walce | `female, child, very high pitch` | 37 | 8,0 s, SHA `2f41934e` | 5 |
| `nv_xain` | porucznik smoczego miotu (boss) | `male, young adult, very low pitch` | 37 | 7,8 s, SHA `98bb0495` | 1 |
| `nv_widmo` | widmo, okrzyki w walce | `female, elderly, low pitch, whisper` | 23 | 8,1 s, SHA `5d8a6d81` | 10 |
| `nv_nekromanta` | cień nekromanty | `male, elderly, low pitch, whisper` | 23 | 7,9 s, SHA `ab66ab02` | 1 |
| `nv_gnom` | gnom na drodze (podróż) | `male, teenager, very high pitch` | 37 | 9,1 s, SHA `8db3e8bf` | 1 |
| `nv_gap` | gap przy procesji (podróż) | `female, middle-aged, moderate pitch` | 37 | 9,1 s, SHA `2a811e46` | 1 |
| `nv_ork` | ork z karawany (podróż) | `male, middle-aged, very low pitch` | 37 | 8,1 s, SHA `87fe47ed` | 1 |
| `nv_uchodzca` | uchodźcy (podróż) | `female, young adult, high pitch` | 37 | 8,4 s, SHA `ca508237` | 1 |
| `nv_glos` | odległy głos z lasu (podróż) | `male, elderly, high pitch` | 11 | 8,5 s, SHA `4539ea56` | 1 |
| `nv_protektor` | Protektor Cytadeli (podróż Brynn) | `male, middle-aged, moderate pitch` | 23 | 8,4 s, SHA `9ad50cfb` | 4 |
| `nv_gont` | mistrzyni Gont, orczyca (podróż Syrusa) | `female, young adult, low pitch` | 37 | 8,1 s, SHA `92e2bac3` | 3 |
| `nv_kowalka` | kowalka, smocza hybryda (podróż Vaerix) | `female, middle-aged, very low pitch` | 23 | 7,9 s, SHA `f1da6143` | 1 |

Bohater wskazany luką (`{0}`) mówi głosem bohatera z argumentu okna (`arg:N`). Nowe nagrania postaci czytanych dotąd przez ElevenLabs powstają w paczce testowej w OmniVoice z referencji zapasowych (D80).

## E17: mówcy bez imienia w wersji produkcyjnej (D107, wydanie `m4`)

Każda postać bez imienia ma własny głos, a typ wroga jeden głos. Mówców pogrupowaliśmy według misji i kontekstu w ręcznym przeglądzie wszystkich okien narratora (`src/lektor/data/speakers_prod.json`). `nv_ynfernael` z t1 to Baelziffar (`nv_baelziffar`, nowy projekt).

- Głosy nagrywa model lokalny OmniVoice (decyzja użytkownika 2026-11-14). Profilu ElevenLabs nie da się odtworzyć, a 99 głosów nie mieści się na koncie.
- 19 głosów z t1 (tabela wyżej) zostaje przy swoich referencjach.
- 80 nowych głosów ma profil postaci z kontekstu wszystkich jej kwestii (`omni` w `analysis/tools/voice_designs_prod.json`): płeć, wiek, wysokość, szept i własne zdanie w stylu postaci (nie tekst gry).
- Projekt i wybór: `analysis/tools/new_voices_prod.py`, trzy ziarna na profil, wybór automatem bez odsłuchu (QA 2026-11-14).

Wybrane głosy (automat: najmniejszy CER, wysokość w zakresie płci, a z dobrych najdalej od narratora, obsady i głosów wybranych wcześniej). `nv_q9_blizniaki` i `nv_ta2_kupiec` dostały nowe zdanie po nieudanym pierwszym projekcie (CER 6,35 i 0,85). Cztery głosy za bliskie innym dostały siedem ziaren zamiast trzech. Najbliższe pary barwy po wyborze: `nv_kowalka`~`nv_crayleth` 0,943, `nv_gont`~`nv_crayleth` 0,934, `nv_nekromanta`~`nv_a2q8_zamiatacz` 0,933.

| Głos | Kto mówi | Opis OmniVoice | Ziarno | Referencja | Fragmenty |
|---|---|---|---:|---|---:|
| `nv_a2q11_medyk` | uratowany medyk Cytadeli | `male, young adult, moderate pitch` | 23 | 6,36 s, SHA `654af252` | 1 |
| `nv_a2q11_protektor` | uratowany Protektor Cytadeli | `male, middle-aged, moderate pitch` | 23 | 7,16 s, SHA `80cd3497` | 1 |
| `nv_a2q11_wojowniczka` | ranna wojowniczka Cytadeli | `female, middle-aged, low pitch` | 11 | 6,52 s, SHA `98c51557` | 1 |
| `nv_a2q11_zolnierz` | ranny żołnierz z manierką | `male, young adult, high pitch` | 11 | 6,68 s, SHA `4dd136a6` | 1 |
| `nv_a2q2_straznik` | strażnik więzienia (most zwodzony) | `male, middle-aged, moderate pitch` | 37 | 4,23 s, SHA `5b8a38b5` | 1 |
| `nv_a2q3_bandyta` | banita z zasadzki | `male, young adult, moderate pitch` | 11 | 3,32 s, SHA `4385d679` | 1 |
| `nv_a2q3_strazniczka` | strażniczka w karczmie | `female, middle-aged, low pitch` | 11 | 7,24 s, SHA `5b797414` | 1 |
| `nv_a2q3_straznik` | strażnik pod urokiem (nieobecny wzrok) | `male, middle-aged, low pitch` | 37 | 5,16 s, SHA `9fbb184e` | 1 |
| `nv_a2q3_zolnierz` | żołnierz w karczmie | `male, middle-aged, low pitch` | 37 | 7,61 s, SHA `7d09f2e6` | 1 |
| `nv_a2q5_hybryda` | hybryda zwiadowca | `male, young adult, low pitch` | 37 | 3,74 s, SHA `8d91ea40` | 2 |
| `nv_a2q5_lowczyni` | łowczyni (hybryda) ścigająca Narę | `female, young adult, low pitch` | 37 | 5,82 s, SHA `d82d73f7` | 1 |
| `nv_a2q7_wygnaniec` | mężczyzna przy płonącej studni (wygnaniec w Jaskini Snów) | `male, young adult, low pitch` | 23 | 6,73 s, SHA `d14b35e0` | 1 |
| `nv_a2q8_bibliotekarka` | bibliotekarka opactwa, widzi przyszłość | `female, elderly, moderate pitch` | 37 | 7,71 s, SHA `59179837` | 10 |
| `nv_a2q8_kronikarz` | kronikarz opactwa, stary kotoczłek, dawny wędrowiec | `male, elderly, high pitch` | 11 | 8,53 s, SHA `6af22bf9` | 11 |
| `nv_a2q8_ogrodniczka` | gnomka ogrodniczka w opactwie, rozmawia z duchami | `female, middle-aged, very high pitch` | 11 | 7,08 s, SHA `50b8928a` | 18 |
| `nv_a2q8_zamiatacz` | młodzieniec w opactwie, porzucił czarnoksięstwo | `male, young adult, moderate pitch, whisper` | 23 | 7,72 s, SHA `d4397af7` | 10 |
| `nv_baelziffar` | Baelziffar, demon Ynfernaelu, głos w głowie Galadena | `male, elderly, very low pitch, whisper` | 11 | 9,08 s, SHA `1bdbb154` | 14 |
| `nv_crayleth` | Crayleth, Pierwsza Włóczniczka Levirax | `female, middle-aged, very low pitch` | 101 | 7,67 s, SHA `303e32bd` | 5 |
| `nv_czerwona_gwiazda` | Czerwona Gwiazda, najmłodsza z poległych, uzdrowicielka we śnie | `female, young adult, high pitch` | 37 | 7,48 s, SHA `e1b41445` | 1 |
| `nv_dalavel` | Dalavel, starsza elfka, mentorka Galadena (wizja) | `female, elderly, moderate pitch` | 11 | 7,51 s, SHA `e7d16fdb` | 3 |
| `nv_denavel` | Denavel, poległy kuzyn Galadena we śnie (elf, mówi na migi) | `male, young adult, moderate pitch, whisper` | 11 | 7,72 s, SHA `f388a369` | 2 |
| `nv_edgar` | Edgar Przecieracz Szlaków, posłaniec Carthridge | `male, middle-aged, low pitch` | 37 | 7,48 s, SHA `b8279ecc` | 9 |
| `nv_fof_kapitan` | kapitan straży Fallowhearth, mężczyzna, kusznik | `male, middle-aged, low pitch` | 23 | 8,41 s, SHA `0321dd00` | 18 |
| `nv_fof_mieszkanka` | kobieta z Fallowhearth | `female, middle-aged, moderate pitch` | 23 | 8,2 s, SHA `59ea416d` | 1 |
| `nv_fulminar` | Fulminar, potężny smok, władca Navoth | `male, elderly, very low pitch` | 11 | 7,68 s, SHA `41ef5a0a` | 8 |
| `nv_gorzae` | Gorzae, nadzorczyni sądowa | `female, middle-aged, moderate pitch` | 23 | 8,52 s, SHA `dd42c551` | 4 |
| `nv_gravia` | Gravia Kein, Opiekunka Cytadeli, umierająca od trucizny | `female, elderly, low pitch` | 67 | 8,09 s, SHA `bc7a7084` | 14 |
| `nv_honora` | Honora, dowódczyni lojalistów, artystka | `female, middle-aged, moderate pitch` | 23 | 8,44 s, SHA `692eb144` | 3 |
| `nv_lisb_naukowiec` | człowiek w szatach, naukowiec/agent | `male, middle-aged, high pitch` | 23 | 8,04 s, SHA `0df29c99` | 3 |
| `nv_lisb_wartownik_a` | wartownik hybryda (pierwszy) | `male, young adult, moderate pitch` | 11 | 7,71 s, SHA `20cbeba2` | 1 |
| `nv_lisb_wartownik_b` | wartownik hybryda (drugi) | `male, middle-aged, very low pitch` | 23 | 7,24 s, SHA `5f0ba5e9` | 2 |
| `nv_lisb_zwiadowca` | zwiadowca smoczych hybryd | `male, young adult, low pitch` | 11 | 7,85 s, SHA `09671894` | 2 |
| `nv_nicodemus` | Nicodemus, młody żołnierz buntowników | `male, teenager, moderate pitch` | 11 | 7,64 s, SHA `db12f2a6` | 2 |
| `nv_ocella` | ciotka Ocella, stara zielarka w kniei | `female, elderly, high pitch` | 23 | 9,31 s, SHA `ec6cc6b2` | 25 |
| `nv_patralis` | Patralis, karczmarka | `female, middle-aged, moderate pitch` | 23 | 7,88 s, SHA `327c5fe4` | 10 |
| `nv_preesha` | Preesha, kobieta-hyrrinx z bimbrem | `female, middle-aged, low pitch` | 11 | 7,7 s, SHA `c96d3623` | 4 |
| `nv_q10_jezdzczyni` | jeźdźczyni alerionów ze złamaną ręką | `female, young adult, high pitch` | 11 | 8,23 s, SHA `d2a0a294` | 3 |
| `nv_q10_jezdziec` | jeździec alerionów (mężczyzna) | `male, young adult, moderate pitch` | 37 | 7,91 s, SHA `5840b71c` | 4 |
| `nv_q10_straznik` | strażnik przy bramie Highmont | `male, young adult, high pitch` | 37 | 6,43 s, SHA `c3d24e2a` | 1 |
| `nv_q11_bandyta_nekromanta` | bandyta z kosturem, ożywia zmarłych | `male, middle-aged, low pitch, whisper` | 11 | 7,0 s, SHA `27788e15` | 1 |
| `nv_q11_kobieta_a` | podejrzliwa uchodźczyni | `female, middle-aged, low pitch` | 37 | 8,36 s, SHA `b5e86193` | 4 |
| `nv_q11_kobieta_b` | uchodźczyni z Highmont | `female, young adult, moderate pitch` | 23 | 7,0 s, SHA `58bb629a` | 1 |
| `nv_q11_kobieta_kufel` | kobieta w tawernie Azylu z kuflem | `female, middle-aged, low pitch` | 23 | 8,12 s, SHA `bd0acf8f` | 3 |
| `nv_q11_mlody_ork` | młody ork stolarz | `male, teenager, low pitch` | 23 | 8,2 s, SHA `41f37cac` | 1 |
| `nv_q11_ork_ojciec` | ork z synem | `male, middle-aged, very low pitch` | 37 | 6,18 s, SHA `54d240fe` | 1 |
| `nv_q11_pacjentka` | pacjentka z chorą nogą, haftuje | `female, elderly, moderate pitch` | 37 | 7,64 s, SHA `aa13f172` | 5 |
| `nv_q11_rodzic` | rodzic dzieci przy studni | `male, young adult, low pitch` | 37 | 7,53 s, SHA `b4773d22` | 1 |
| `nv_q11_tlum` | ktoś z tłumu uchodźców | `male, middle-aged, high pitch` | 11 | 5,25 s, SHA `70697be9` | 1 |
| `nv_q11_uchodzca` | uchodźca opuszczający Azyl | `male, elderly, moderate pitch` | 11 | 7,0 s, SHA `98b24987` | 1 |
| `nv_q11_uzdrowiciel` | uzdrowiciel w Azylu | `male, middle-aged, moderate pitch` | 11 | 8,1 s, SHA `188a7b65` | 1 |
| `nv_q11_zbir` | zbir Księcia Banity przy drzwiach | `male, middle-aged, very low pitch` | 11 | 7,48 s, SHA `93afae20` | 2 |
| `nv_q12_banitka` | dawna znajoma Fuksa z bandy | `female, young adult, low pitch` | 23 | 7,48 s, SHA `7d35654a` | 1 |
| `nv_q12_duch` | upiór uwięzionej zdrajczyni Forthynu (szkielet) | `female, elderly, low pitch, whisper` | 11 | 7,01 s, SHA `a9e71a3b` | 3 |
| `nv_q13_hybryda` | smocza hybryda, posłaniec Xenitha | `male, middle-aged, low pitch` | 11 | 6,14 s, SHA `ebe99ec7` | 1 |
| `nv_q13_smok` | duch martwego smoka (szkielet w klasztorze) | `male, elderly, very low pitch` | 23 | 8,18 s, SHA `7056dd92` | 27 |
| `nv_q14_kucharz` | kucharz zamkowy, więzień | `male, middle-aged, high pitch` | 37 | 7,29 s, SHA `ae8ebaee` | 4 |
| `nv_q14_stronnik` | stronnik barona Zacharetha | `male, young adult, moderate pitch` | 37 | 6,43 s, SHA `946a798f` | 2 |
| `nv_q14_wiezien_hybryda` | uwięziona hybryda (mężczyzna), „zdrajca” Levirax | `male, middle-aged, low pitch` | 37 | 6,89 s, SHA `280320b3` | 2 |
| `nv_q14_wskrzeszeniec` | wskrzeszeniec z legionu Waiqara | `male, elderly, high pitch, whisper` | 11 | 6,12 s, SHA `a3393aed` | 3 |
| `nv_q14_zolnierka` | uwięziona żołnierka Forthynu | `female, young adult, low pitch` | 101 | 7,09 s, SHA `8a04e14b` | 5 |
| `nv_q3_bandyta_skrzynia` | bandyta przy skrzyni, zna Fuksa | `male, young adult, high pitch` | 23 | 6,67 s, SHA `2a5a7fc0` | 1 |
| `nv_q3_herszt` | bandyta przy studni, najgroźniejszy z bandy | `male, middle-aged, low pitch` | 23 | 6,85 s, SHA `d46bc649` | 2 |
| `nv_q9_blizniaki` | elfie bliźnięta z wizji | `male, teenager, moderate pitch` | 37 | 8,44 s, SHA `44eb9e4f` | 2 |
| `nv_saphar` | Saphar, uczona z Cytadeli | `female, young adult, high pitch` | 11 | 8,24 s, SHA `f07b2b27` | 10 |
| `nv_siostra_krwi` | siostra krwi / wiedźma krwi, sługa Ne'Krul | `female, young adult, high pitch` | 23 | 7,32 s, SHA `c7149646` | 6 |
| `nv_sq1_wiedzma` | przemieniona wiedźma-potwór z resztką świadomości | `female, middle-aged, very low pitch` | 11 | 7,17 s, SHA `2602754f` | 11 |
| `nv_sq1_wyslannik` | blady mężczyzna, nekromanta-wysłannik | `male, middle-aged, moderate pitch, whisper` | 11 | 6,04 s, SHA `40b65840` | 25 |
| `nv_ta2_04_kobieta` | młoda kobieta prosząca Fuksa o pomoc | `female, young adult, high pitch, whisper` | 11 | 7,64 s, SHA `a9216373` | 2 |
| `nv_ta2_czeladnik` | posłaniec Gildii Kamieniarzy (krasnolud) | `male, teenager, low pitch` | 11 | 6,92 s, SHA `f64cd205` | 4 |
| `nv_ta2_gospodarz` | nieufny gospodarz z kuszą | `male, middle-aged, very low pitch` | 11 | 7,56 s, SHA `11bc334e` | 1 |
| `nv_ta2_karciarz` | wieśniak wygrywający w karty | `male, elderly, moderate pitch` | 37 | 7,65 s, SHA `39518c70` | 1 |
| `nv_ta2_kupiec` | kupiec porzucony przez ochroniarzy | `male, middle-aged, moderate pitch` | 51 | 8,44 s, SHA `59bfa80e` | 1 |
| `nv_ta2_mag` | arogancki uczony mag z zepsutym wozem | `male, middle-aged, high pitch` | 23 | 8,04 s, SHA `49f39b7c` | 5 |
| `nv_ta2_orczyca` | zawadiacka orczyca karciarka | `female, young adult, low pitch` | 23 | 6,93 s, SHA `a25d6f9a` | 1 |
| `nv_ta2_pielgrzym` | krasnolud z grupy pielgrzymów | `male, elderly, low pitch` | 37 | 7,96 s, SHA `9e1640d6` | 1 |
| `nv_ta2_sierzant` | ranny sierżant eskorty uchodźców | `male, middle-aged, low pitch` | 37 | 7,07 s, SHA `b6bb1fa5` | 2 |
| `nv_ta2_sluzacy` | służący w przydrożnej gospodzie | `male, young adult, high pitch` | 23 | 6,42 s, SHA `dd19feb5` | 1 |
| `nv_warrick` | Warrick, stary ork-rolnik | `male, elderly, very low pitch` | 11 | 8,88 s, SHA `e78b95f3` | 15 |
| `nv_zarzadczyni` | zarządczyni zamku Highmont | `female, middle-aged, moderate pitch` | 37 | 8,44 s, SHA `7dae77c3` | 5 |
| `nv_zerai` | porucznik Zerai, smocza hybryda w zbroi oficera (kobieta) | `female, middle-aged, low pitch` | 37 | 7,48 s, SHA `3a8e73e5` | 1 |
