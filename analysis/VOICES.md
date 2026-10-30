# Głosy: polski dubbing jako referencje do klonowania

Źródło: kopia `Polish.pck` (Wwise AKPK, `StreamingAssets/Audio/GeneratedSoundBanks/Windows/`), ta sama zawartość co `Polish.bytes` w bundlu `audio/windows/polish`.
Audio i transkrypcje są tylko w `analysis/work/voices/` (prywatne, poza repozytorium). W tym pliku są wyłącznie liczby i nazwy plików.

Skrypty:
- [`tools/extract_voices.py`](tools/extract_voices.py): `.wem` z banków (DIDX/DATA), nazwy z `SoundbanksInfo.xml`, konwersja do WAV przez `vgmstream-cli` r2168;
- [`tools/analyze_voices.py`](tools/analyze_voices.py): czas czystej mowy, F0 (pYIN), tło w pauzach, charakter kwestii, wybór referencji;
- [`tools/voice_similarity.py`](tools/voice_similarity.py): podobieństwo głosów (embedding `VoiceEncoder` z Chatterbox);
- [`tools/speaker_gender.py`](tools/speaker_gender.py): płeć mówców z polskich form czasowników.

## 1. Co jest w polskiej paczce

`SoundbanksInfo.xml` podaje dla każdego pliku PL nazwę źródłową (`ShortName`) i bank. Do mapowania nie był potrzebny wwiser. Wszystkie pliki PL leżą w pamięci banków (`Streaming="false"`).

| Bank | Pliki PL | Zawartość |
|---|---:|---|
| `Voice_Cutscenes_Act1` / `Music_Cutscenes_Act1` | 7 | lektor przerywników aktu 1 (te same media w obu bankach) |
| `Voice_Cutscenes_Act2` / `Music_Cutscenes_Act2` | 10 | lektor przerywników aktu 2 (DLE04), warianty zależne od wyborów |
| `Voice_Heroes_Act1` / `Act2` | 240 unikalnych | 6 bohaterów × 40 krótkich kwestii (`<Bohater>_<Typ>_<n>.wav`) |
| `Voice_Villains_Act1` / `Act2` | 99 | 9 złoczyńców × 11 kwestii (`<Złoczyńca>_<Typ>_<n>.wav`) |
| **Razem** | **356** | **28:52 audio, 44,1 kHz**, mono (7 przerywników aktu 1 i 3 klipy w stereo) |

**Przerywniki są w pełni zdubbingowane po polsku.** Każdy z 20 modeli `CutsceneModel` (`CUTSCENE_01–07`, `CUTSCENE_A201–A207` z wariantami) wskazuje przez `SoundEventName` zdarzenie Wwise. Jego `MediaRefs` prowadzą do jednego z 17 polskich plików. **Dlatego 115 kluczy `napisy_cutscenek` z [REPORT.md](REPORT.md) nie potrzebuje TTS.** Muzyka przerywników to osobne pliki SFX `FFG_Descent_v1.0_Cutscene0N`, strumieniowane z `Media/`.

Nagrania bohaterów i złoczyńców to krótkie okrzyki z planszy: wybór questu lub bohatera, łup, rany, pokonanie wroga, wygrana, porażka. Okien fabularnych i komunikatów questu nikt w grze nie czyta i to jest zakres lektora.

## 2. Mówcy w nagraniach

Jak liczone są kolumny:
- **Czysta mowa:** suma segmentów powyżej progu energii (30 dB pod szczytem i powyżej -50 dBFS), pauzy poniżej 250 ms łączę z segmentem.
- **Tło:** mediana poziomu w pauzach wewnątrz nagrania.
- **Charakter:** liczony **względem mediany danego mówcy** (z-score F0 i głośności). Pokazuje, które klipy odstają od zwykłego tonu mówcy, a nie bezwzględną głośność.
- **Spójność:** mediana podobieństwa cosinusowego embeddingów między plikami tego samego mówcy.

| Mówca | Pliki | Łącznie | Czysta mowa | Charakter (spok./podn./krzyk) | F0 mediana | Tło w pauzach | Podkład | Spójność głosu | Referencja |
|---|---:|---:|---:|---|---:|---:|---|---:|---|
| narrator | 17 | 12:40 | 10:29 | 14 / 3 / 0 | 111 Hz | -75 dB | brak | 0,97 | `refs/narrator.wav` (15,1 s, 1 fragment) |
| Brynn | 40 | 1:30 | 1:15 | 34 / 5 / 1 | 274 Hz | -97 dB | brak | 0,72 | `refs/brynn.wav` (11,7 s, 4 klipy) |
| Syrus | 40 | 1:50 | 1:29 | 33 / 5 / 2 | 116 Hz | -63 dB | brak | 0,76 | `refs/syrus.wav` (14,9 s, 5 klipy) |
| Kehli | 40 | 1:51 | 1:34 | 32 / 8 / 0 | 262 Hz | -73 dB | brak | 0,71 | `refs/kehli.wav` (14,8 s, 4 klipy) |
| Vaerix | 40 | 1:52 | 1:35 | 34 / 5 / 1 | 119 Hz | -73 dB | brak | 0,74 | `refs/vaerix.wav` (14,8 s, 6 klipy) |
| Galaden | 40 | 2:11 | 1:55 | 36 / 4 / 0 | 181 Hz | -60 dB | brak | 0,79 | `refs/galaden.wav` (13,0 s, 3 klipy) |
| Fuks (Chance) | 40 | 1:45 | 1:25 | 33 / 7 / 0 | 222 Hz | -67 dB | brak | 0,70 | `refs/chance.wav` (12,8 s, 4 klipy) |
| Ne’Krul | 11 | 53 s | 47 s | 11 / 0 / 0 | 217 Hz | -62 dB | brak | 0,82 | `refs/nekrul.wav` (11,1 s, 2 klipy) |
| Levirax | 11 | 41 s | 35 s | 10 / 1 / 0 | 243 Hz | -78 dB | brak | 0,72 | `refs/levirax.wav` (5,2 s, 1 klip) |
| Greysdon | 11 | 37 s | 31 s | 7 / 3 / 1 | 299 Hz | -47 dB | brak | 0,76 | `refs/greysdon.wav` (2,8 s, 1 klip) |
| Vraskhar | 11 | 36 s | 29 s | 9 / 2 / 0 | 284 Hz | -68 dB | brak | 0,79 | `refs/vraskhar.wav` (6,6 s, 2 klipy) |
| Navoth | 11 | 33 s | 28 s | 9 / 2 / 0 | 348 Hz | -56 dB | brak | 0,77 | `refs/navoth.wav` (6,4 s, 2 klipy) |
| Reneyr | 11 | 33 s | 27 s | 9 / 2 / 0 | 140 Hz | -59 dB | brak | 0,80 | `refs/reneyr.wav` (6,4 s, 2 klipy) |
| Zachareth | 11 | 30 s | 25 s | 11 / 0 / 0 | 258 Hz | -64 dB | brak | 0,77 | `refs/zachareth.wav` (7,1 s, 2 klipy) |
| Xenith | 11 | 27 s | 22 s | 8 / 2 / 1 | 129 Hz | -63 dB | brak | 0,69 | `refs/xenith.wav` (7,2 s, 2 klipy) |
| Gilliam | 11 | 21 s | 17 s | 9 / 1 / 1 | 198 Hz | -67 dB | brak | 0,75 | `refs/gilliam.wav` (5,3 s, 2 klipy) |

Typy kwestii według nazw plików:

| Mówcy | Mowa (`QuestSelect`, `HeroSelect`, `GainTreasure`, `QuestWon`, `QuestLost`, `FeatComplete`, `Spawn`) | Okrzyki bojowe (`DefeatEnemy`, `Attack`, `Defend`) | Ból (`MinorWound`, `MajorWound`, `Defeat`) |
|---|---|---|---|
| bohaterowie (każdy) | 23 klipy, 47–72 s mowy | 9 klipów, 13–20 s | 8 klipów, 13–23 s |
| złoczyńcy (każdy) | 2 klipy, 4–11 s mowy | 7 klipów, 9–28 s | 2 klipy, 3–8 s |

Wnioski:
- **Podkładu muzycznego nie ma w żadnym nagraniu.**
  - Przerywniki aktu 1 mają w pauzach cyfrową ciszę (ok. -100 dBFS).
  - W przerywnikach aktu 2 i części klipów postaci tło wynosi od -47 do -78 dB, ale płaskość widma w pauzach to 0,02–0,14 przy niskim poziomie. To szum lub pogłos nagrania, a nie podkład.
  - Najwyższe tło ma Greysdon (-47 dB). Warto odsłuchać, czy jego głos nie jest przetworzony efektem.
- **Narrator przerywników to jeden lektor.** Spójność wynosi 0,97 na 17 plikach, głos męski, F0 ok. 110 Hz. Ponad 10 minut czystej, spokojnej mowy to najlepszy materiał do klonowania.
- **Embedding narratora jest bardzo bliski Galadena (0,96).** Każdy przerywnik ma Galadena jako drugi najbliższy głos (0,93–0,96). Prawdopodobnie to ten sam aktor, co trzeba potwierdzić odsłuchem. Jeśli tak, narrator i Galaden w TTS będą brzmieć podobnie.
- **Tempo lektora:** 10,0–12,3 znaku tekstu napisów na sekundę czystej mowy (mediana ok. 11,5); z pauzami 9–10 znaków/s. W REPORT.md zakładałem 15 znaków/s, więc czasy audio scenariuszy z punktu 6 trzeba wydłużyć o ok. 30%.
- **Złoczyńcy mają za mało mowy.** Każdy ma tylko 2 klipy `Spawn` (4–11 s), reszta to okrzyki i stęknięcia. U Zacharetha pYIN prawie nie wykrywa dźwięcznych ramek. Referencje złoczyńców mają 3–7 s (Ne’Krul 11 s), więc nadają się najwyżej do prób. Chatterbox działa najlepiej od ok. 10 s.
- **Podobieństwa bohater ↔ złoczyńca sugerują aktorów w kilku rolach:** Vaerix ↔ Xenith 0,94, Fuks ↔ Greysdon 0,94, Kehli ↔ Navoth 0,92, Brynn ↔ Vraskhar 0,92. Dla krótkich, krzyczanych klipów embedding jest jednak mało wiarygodny.
- Przesterowania nie ma: żadna próbka nie osiąga |x| ≥ 0,99.
- F0 nie nadaje się do ustalania płci złoczyńców: okrzyki zawyżają je do 200–350 Hz także u mężczyzn. U Galadena (181 Hz) mediana jest prawdopodobnie zawyżona przez błędy oktawowe pYIN.

## 3. Referencje do klonowania (Chatterbox Multilingual, zero-shot)

Chatterbox używa pierwszych 10 s referencji w S3Gen i pierwszych 6 s w T3. Embedding mówcy liczy z całości. Dlatego najlepszy materiał musi być na początku pliku.

| Głos | Plik (`work/voices/refs/`) | Długość | Źródło |
|---|---|---:|---|
| narrator | `narrator.wav` | 15,1 s | `3_Wings Of War_VoiceOver.wav` (CUTSCENE_03), 0,8–15,8 s: ciągła mowa, cisza w pauzach, najniższe tło |
| Syrus | `syrus.wav` | 14,9 s | `GainTreasure_2`, `HeroSelect_1`, `QuestWon_3`, `QuestLost_3`, `GainTreasure_3` |
| Brynn | `brynn.wav` | 11,7 s | `GainTreasure_2`, `GainTreasure_5`, `HeroSelect_1`, `QuestWon_4` |
| Kehli | `kehli.wav` | 14,8 s | `QuestLost_3`, `QuestWon_3`, `QuestLost_2`, `QuestWon_2` |
| Vaerix | `vaerix.wav` | 14,8 s | `QuestSelect_3`, `QuestSelect_6`, `FeatComplete_2`, `QuestWon_3`, `QuestSelect_4`, `GainTreasure_4` |
| Galaden | `galaden.wav` | 13,0 s | `QuestWon_1`, `QuestSelect_2`, `QuestLost_2` |
| Fuks (Chance) | `chance.wav` | 12,8 s | `QuestSelect_5`, `QuestLost_2`, `FeatComplete_1`, `FeatComplete_2` |
| złoczyńcy | `<imię>.wav` | 2,8–11,1 s | klipy `Spawn`/`Defend`, za krótkie (patrz wyżej) |

Jak powstały referencje bohaterów:
- klipy sklejone z pauzą 0,3 s i znormalizowane do szczytu -1 dBFS;
- wybierane od najspokojniejszych klipów mowy (najniższy z-score);
- tylko klipy bez przesterowania i z udziałem dźwięcznych ramek powyżej 35%.

To heurystyka. **Przed produkcją trzeba odsłuchać wszystkie referencje.** Klipy bohaterów to krótkie, ekspresyjne kwestie, a nie neutralna narracja. Wybór referencji dla narratora jest pewniejszy.

## 4. Płeć mówców (uzupełnienie listy z REPORT.md)

Źródła ustaleń:
- formy 1. osoby: `-łem/-łbym` (męskie) i `-łam/-łabym` (żeńskie);
- formy 3. osoby po imieniu (`… zrobiła`);
- zaimki w tekstach EN (dla niejasnych przypadków);
- tytuły (Baronessa, Mistrzyni, Poruczniczka…);
- F0 nagrań bohaterów (mediana z klipów mowy);
- przynależność do bundli wrogów (`d3/enemies/dragon`, `vampire`…).

**Potwór** oznacza postać nieludzką, której głos zapewne będzie wymagał efektu: smok, nieumarły, cień. Wampiry i hybrydy smoków mówiące ludzkim głosem są oznaczone jako męskie albo żeńskie, z dopiskiem.

| # | ID | Nazwa PL | Kwestie | Znaki PL | Płeć | Typ głosu | Podstawa |
|---:|---|---|---:|---:|---|---|---|
| 1 | `BRYNN` | Brynn | 666 | 51 619 | K | żeński | tekst: 56× -łam; F0 nagrań ~260 Hz |
| 2 | `SYRUS` | Syrus | 555 | 47 581 | M | męski | tekst: 58× -łem; F0 ~115 Hz |
| 3 | `KEHLI` | Kehli | 537 | 43 436 | K | żeński | tekst: 62× -łam; F0 ~290 Hz |
| 4 | `VAERIX` | Vaerix | 520 | 39 133 | M | męski | F0 ~100 Hz; tekst: 2× -łem (hybryda smoka, głos ludzki) |
| 5 | `GALADEN` | Galaden | 509 | 38 409 | M | męski | tekst: 32× -łem |
| 6 | `CHANCE` | Fuks (Chance) | 427 | 31 831 | M | męski | tekst: 48× -łem; F0 ~175 Hz |
| 7 | `VARIABLE_HERO2` | *dynamiczny slot bohatera* | 201 | 7 699 | – | zależny od bohatera | slot dynamiczny |
| 8 | `BARONESSMAGRIT` | Baronessa Magrit (Baroness Magrit) | 142 | 15 695 | K | żeński | tytuł + 12× -łam |
| 9 | `ALYS` | Alys Raine | 97 | 10 748 | K | żeński | 3. os. -ła; EN „she” 20× |
| 10 | `BARONZACHARETH` | Baron Zachareth | 74 | 7 561 | M | męski | tytuł + 12× -łem |
| 11 | `MASTERBRULI` | Mistrz Bruli (Master Bruli) | 72 | 5 857 | M | męski | tytuł + 6× -łem |
| 12 | `RENEYR` | Hrabia Reneyr (Count Reneyr) | 69 | 7 619 | M | męski | tytuł + 32× -łem (wampir: opcjonalny efekt) |
| 13 | `LAUREL` | Laurel | 67 | 5 440 | K | żeński | 5× -łam, 3. os. -ła 6× |
| 14 | `GREIGORY` | Baron Greigory | 65 | 6 919 | M | męski | tytuł; 3. os. -ł; EN „he” 33× |
| 15 | `RONAN` | Ronan | 63 | 5 189 | M | męski | 3. os. -ł; EN „he” |
| 16 | `BUTTON` | Guzik (Button) | 62 | 5 715 | K | żeński | 8× -łam; EN „she” |
| 17 | `BARONESS_ADELYNN` | Baronessa Adelynn (Baroness Adelynn) | 60 | 5 165 | K | żeński | tytuł + 11× -łam |
| 18 | `VARIABLE_HERO1` | *dynamiczny slot bohatera* | 58 | 2 984 | – | zależny od bohatera | slot dynamiczny |
| 19 | `MASTERGALGORAZ` | Mistrz Galgoraz (Master Galgoraz) | 56 | 4 948 | M | męski | tytuł |
| 20 | `ASTARRA` | Astarra | 51 | 4 326 | K | żeński | 14× -łam |
| 21 | `SIRBALTHAIN` | Sir Balthain | 43 | 4 708 | M | męski | tytuł + 9× -łem |
| 22 | `COUNTESSDUCARD` | Hrabina Ducard (Countess Ducard) | 38 | 3 905 | K | żeński | tytuł + 8× -łam |
| 23 | `VETA` | Mistrzyni Runów Veta (Runemaster Veta) | 38 | 4 405 | K | żeński | tytuł (Mistrzyni) |
| 24 | `ARDEN` | Arden Gladhand | 38 | 4 717 | M | męski | 9× -łem |
| 25 | `TREVALYN` | Baron Trevalyn | 37 | 4 162 | M | męski | tytuł |
| 26 | `ELDERMOK` | Szaman Mok (Elder Mok) | 30 | 3 289 | M | męski | tytuł (Szaman) |
| 27 | `MASTERFLINT` | Mistrz Flint (Master Flint) | 27 | 2 559 | M | męski | tytuł |
| 28 | `GREYSDON` | Greysdon | 27 | 2 786 | M | męski | 5× -łem; „Profesor” (fanatyk-nekromanta) |
| 29 | `LTRAND` | Poruczniczka Rand (Lt. Rand) | 25 | 1 775 | K | żeński | tytuł (Poruczniczka) |
| 30 | `NAVOTH` | Dzwonniczka Navoth (Bellringer Navoth) | 25 | 2 771 | K | żeński | tytuł (Dzwonniczka) + 6× -łam |
| 31 | `KATHRYN` | Kathryn | 24 | 1 797 | K | żeński | 8× -łam |
| 32 | `LEVIRAX` | Levirax | 23 | 2 583 | K | potwór | Smocza Władczyni (smok); 3. os. -ła 23× |
| 33 | `WAIQAR` | Waiqar | 23 | 2 696 | M | potwór | nieumarły władca; 6× -łem |
| 34 | `MORANT` | Morant Bratobójca (Morant the Kin-Killer) | 22 | 2 663 | M | męski | 6× -łem |
| 35 | `HERBIE` | Herbie | 18 | 1 694 | M | męski | 8× -łem |
| 36 | `OUTLAWPRINCE` | Książę Banita (The Outlaw Prince) | 17 | 1 253 | M | męski | tytuł (Książę) |
| 37 | `DELPHYNDRA` | Smocza Władzcyni Delphyndra (Dragonlord Delphyndra) | 16 | 1 675 | K | potwór | Smocza Władczyni (smok); 4× -łam |
| 38 | `NARA` | Nara Kieł (Nara the Fang) | 15 | 1 563 | K | żeński | EN „she” 22× |
| 39 | `GILLIAM` | Baron Gilliam | 15 | 1 967 | M | męski | tytuł + 6× -łem |
| 40 | `BLOOD_SISTER` | Ne’Krul (Ne'Krul) | 11 | 706 | K | żeński | wiedźma krwi Uthuk; 3. os. -ła 33×; F0 nagrań ~215 Hz |
| 41 | `CHANCE_SHADOW` | Cień (Shadow) | 11 | 311 | M | potwór | cień Fuksa (istota nadprzyrodzona) |
| 42 | `GRACE` | Baronessa Grace (Baroness Grace) | 11 | 1 237 | K | żeński | tytuł |
| 43 | `VRASKHAR` | Vraskhar | 10 | 821 | K | żeński | „Gorzki Jad”, Żmijowy Legion; 3. os. -ła 10× |
| 44 | `PRYOR` | Baronessa Pryor (Baroness Pryor) | 10 | 1 879 | K | żeński | tytuł + 4× -łam |
| 45 | `GILLIAM_EVIL` | Baron Gilliam | 10 | 1 355 | M | potwór | Baron Gilliam jako wampir (bundle vampire) |
| 46 | `SHADOW_RENEYR` | Cień (Shadow) | 7 | 162 | M | potwór | cień Reneyra (istota nadprzyrodzona) |
| 47 | `MEZA` | Strażniczka Meza (Sentinel Meza) | 4 | 448 | K | żeński | tytuł (Strażniczka) |
| 48 | `DRYS` | *brak modelu postaci* | 3 | 260 | M | męski | Porucznik Drys (Herold); EN „he” |
| 49 | `VARIABLE_HERO3` | *dynamiczny slot bohatera* | 1 | 31 | – | zależny od bohatera | slot dynamiczny |
| 50 | `VARIABLE_HERO4` | *dynamiczny slot bohatera* | 1 | 27 | – | zależny od bohatera | slot dynamiczny |
| 51 | `DRAGON_HYBRID` | Xenith | 1 | 147 | M | męski | Kapitan Xenith (hybryda smoka); F0 nagrań ~130 Hz |

Podsumowanie dla głosu „inny” (dialogi spoza bohaterów; kwestie i znaki jak w REPORT.md):

| Typ głosu | Mówcy | Kwestie | Znaki PL |
|---|---:|---:|---:|
| męski | 18 | 677 | 68 298 |
| żeński | 17 | 690 | 68 396 |
| potwór | 6 | 90 | 8 782 |
| *(bohaterowie, w tym sloty dynamiczne)* | 10 | 3 475 | 262 750 |

Kwestie „inne” dzielą się prawie po równo na męskie i żeńskie. Do pokrycia wystarczą 2–3 głosy męskie, 2–3 żeńskie i 1–2 przetworzone głosy potworów. Sloty `VARIABLE_HERO1–4` trzeba w grze rozwiązać na konkretnego bohatera, więc każda taka kwestia wymaga 6 wariantów audio.
