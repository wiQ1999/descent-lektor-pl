# Descent: Legends of the Dark — analiza plików pod lektora TTS (PL)

Data analizy: 2026-10-30 · wersja treści: `manifest.dat` → `version 2.0.10`.
Pliki gry i `LocalLow` czytałem wyłącznie do skopiowania. Analiza działała na kopiach w `analysis/work/` (5,5 GB, poza repozytorium Git). Skrypty leżą w `analysis/tools/`, a wyniki pośrednie z pełnymi tekstami w `analysis/work/out/`. Te wyniki są prywatne i nie należy ich publikować.

---

## 1. Lokalizacja plików

| Miejsce | Zawartość | Znaczenie dla lektora |
|---|---|---|
| `E:\SteamLibrary\steamapps\common\Legends of the Dark\` | `Legends of the Dark.exe`, `UnityPlayer.dll`, `MonoBleedingEdge\`, `UnityCrashHandler32.exe`, `*_BurstDebugInformation_DoNotShip` | build **32-bitowy (x86)** |
| `…\Legends of the Dark_Data\` | `Managed\` (140 DLL), `resources.assets`, `sharedassets0/1`, `level0/1`, `globalgamemanagers*` | brak tekstów fabuły; `resources.assets` ma tylko teksty SDK konta Asmodee (SSO/CommunityHub), bez PL |
| `…\_Data\StreamingAssets\bundles\` | **200 AssetBundli (2,7 GB)** + `manifest.dat` (JSON: nazwa logiczna → plik-hash, lista assetów, zależności) | **tu są wszystkie teksty i grafy dialogów** |
| `…\_Data\StreamingAssets\Audio\GeneratedSoundBanks\Windows\` | Wwise: `Default.pck` (SFX/muzyka), `Polish.pck`, `SoundbanksInfo.xml` | `Polish.pck` gra rozpakowuje z bundla `audio/windows/polish` dla wybranego języka (plik jest bajtowo identyczny z `Polish.bytes`) |
| `…\_Data\SavedGames\<slot>\*.sav`, `*.qlog` | zapisy gry **w folderze gry**, nie w AppData (5 ostatnich par na slot) | `.qlog` to log **kluczy** komunikatów questu zapisywany razem z `.sav`; nie działa na żywo (zob. pkt 9) |
| `%USERPROFILE%\AppData\LocalLow\Fantasy Flight Games\Descent - Legends of the Dark\` | `Player.log`, `Unity\<guid>\Analytics\` | brak treści; log pokazuje wersję silnika i wybór języka |
| `%USERPROFILE%\AppData\LocalLow\Unity\Fantasy Flight Games_Descent - Legends of the Dark\` | cache Unity `Caching` (2,6 GB, 303 wpisy `<plik>\<hash>\__data`) | patrz niżej |

**Cache w LocalLow:** gra zapisała go przy pierwszym uruchomieniu (20:54). 200 wpisów to przekompresowane kopie bundli ze StreamingAssets. Pozostałe 103 wpisy to inne buildy tych samych 103 bundli, z innymi hashami plików (sceny questów, wrogowie, bronie, UI, mapy, czcionki). **Wśród nich nie ma bundli tekstowych** (`loc/*`, `qloc/*`, `d3/act1`, `d3/act2`, zdarzenia). Sprawdziłem też sceny questów z cache (Q1, A2Q01): zestawy kluczy komunikatów są identyczne z wersją w StreamingAssets. Gra nie pobiera więc żadnych dodatkowych tekstów w trakcie działania. Biblioteki AWS (Cognito/S3/AppSync) obsługują konto Asmodee i chmurę.

## 2. Wersja Unity i backend skryptów

- **Unity 2022.3.62f2.** Potwierdzają to `Player.log` („Initialize engine version: 2022.3.62f2 (7670c08855a9)”) i nagłówki bundli (`UnityFS 5.x.x 2022.3.62f2`).
- **Backend: Mono.** Są `Managed\Assembly-CSharp.dll` (2,6 MB), `Assembly-CSharp-firstpass.dll` i `MonoBleedingEdge\`. Nie ma `GameAssembly.dll`, `il2cpp_data\` ani `global-metadata.dat`.
- Kluczowe biblioteki są wkompilowane w `Assembly-CSharp`:
  - **I2 Localization** (`I2.Loc.LanguageSourceAsset`),
  - **NodeCanvas DialogueTrees** (ParadoxNotion, serializacja grafów JSON w wersji 2.97),
  - własne węzły FFG (`FFG.Core.DTNodes.*`, `FFG.D3.DTNodes.*`),
  - TextMeshPro, Wwise 2023.1.17.
- Pakietu **Unity Localization (StringTable) nie ma**. `UnityEngine.LocalizationModule.dll` to tylko moduł silnika.
- Wniosek: przy Mono kod łatwo podejrzeć (ILSpy/dnSpy). W razie potrzeby da się też podpiąć hook przez Harmony/BepInEx w wersji x86.

## 3. Gdzie są teksty polskie

System lokalizacji to **I2 Localization**, z arkuszem źródłowym Google „I2Loc D3 Main”. Teksty są w UTF-8 i zawierają ą/ę/ś/ż/ź/ó/ł.

| Bundle (nazwa z `manifest.dat`) | Plik | Format | Zawartość PL |
|---|---|---|---|
| `loc/pl` | `32cdc444…` | 9 × **TextAsset CSV** `Key,Type,Desc,Polish` | `StoryAct1Localization` (3314 wierszy), `StoryAct2Localization` (2830), `MainLocalization` (2351), `dle04MainLocalization` (1251), `GlossaryLocalization` (1199), `dle04EnemyLocalization` (261), `EnemyLocalization` (257), `dle04GlossaryLocalization` (189), `AsmoConnectLocalization` (85) |
| `qloc/act1/*`, `qloc/act2/*` | 27 bundli | **MonoBehaviour `I2.Loc.LanguageSourceAsset`** („Q1 Localization”…) | teksty per quest: `mSource.mTerms[].Languages[]` w 13 językach, **PL ma indeks 5** (`Code: "pl"`), razem 5488 wpisów |
| `localization` | `a5920e06…` | 9 pustych `LanguageSourceAsset` + `AvailableLanguages` | kontenery, które w runtime wypełniają się z CSV z `loc/<język>` |
| `language/polish` | `d2c1d63e…` | `PolishSettings.asset` + logo PL | ustawienia języka, bez tekstów |

**Razem: 17 156 unikalnych kluczy, z czego 17 030 ma tekst PL.** Ze 126 pustych wpisów 119 ma tekst EN, czyli gra pokaże fallback. 11 710 kluczy pochodzi z CSV, a 5444 z qloc.

**Kto odwołuje się do kluczy.** Teksty są płaskie (klucz → tekst). Strukturę kwestii, czyli mówcę, kolejność i warunki, opisują osobno grafy NodeCanvas `DialogueTree`. Ich JSON siedzi w polu `_serializedGraph` (asset) albo `boundGraphSerialization` (komponent `DialogueTreeController` na scenie). Po deduplikacji jest **2288 unikalnych grafów**:

| Źródło grafów | Bundle | Grafy |
|---|---|---:|
| Sceny questów (rozgrywka na planszy) | `d3/quests/box1/*`, `d3/quests/dle04/*` (sceny `.unity`) | 1651 |
| Sceny fabularne między questami | `d3/act1` (98 DT „TANGERINE … (Imported)”), `d3/act2` (71) | 170 |
| Zdarzenia podróży / narracyjne / miejskie | `d3/travelevents`, `d3/narrativeevents`, `d3/cityevents` | 119 / 20 / 17 |
| Wrogowie, przedmioty, teren, logika gry | `d3/enemies/*`, `d3/weapons/*`, `d3/items`, `d3/coreset/*`, `d3/gamereq` | 80 / 30 / 15 / 19 |
| Mapa świata | `d3/worldmap/act1`, `act2` | 36 |

Klucze spoza grafów odczytują modele ScriptableObject:
- `CutsceneModel`: napisy z czasem `displayAt`;
- `QuestModel`: nazwy, opisy i wpisy dziennika kampanii;
- `NarrativeEventModel` i `CityEventModel`;
- `GameFactsModel`: ciekawostki na ekranie ładowania;
- `StoryCharacterModel`: postać → klucz imienia i portret, bundle `d3/storymessagecharacters`.

## 4. Struktura kwestii

**Węzeł okna fabularnego** (`FFG.D3.DTNodes.StoryMessageNode`), przykład skrócony:

```json
{ "_message": { "_key": "TANGERINE_Q9_OUTRO_WIN_05K", "_settings": {"FocusTargetParam": {}} },
  "_settings": { "Character_1": {"_characterId": "STORY_CHARACTER_GALADEN"},
                 "Character_2": {"IsSpeaking": true, "_characterId": "STORY_CHARACTER_KEHLI"},
                 "Character_3": {}, "Character_4": {}, "BackgroundType": "Forest" },
  "_name": "05K", "$type": "FFG.D3.DTNodes.StoryMessageNode", "$id": "45" }
```

| Element | Pole | Uwagi |
|---|---|---|
| Klucz tekstu | `_message._key` | termin I2, który rozwiązuje się w CSV albo qloc |
| Mówca | `_settings.Character_1..4` z `IsSpeaking: true` | do 4 portretów na scenie; mówiący jest oznaczony flagą. Brak flagi oznacza narrację. 55 kluczy ma ≥ 2 mówców |
| Imię mówcy | `StoryCharacterModel._id` → `KeyName` → tekst PL | np. `STORY_CHARACTER_CHANCE` → `HERO_CHANCE_NAME` → „Fuks” |
| Typ okna / scena | `$type` węzła + `BackgroundType` | tła: Village, Manor, Forest, Road, House, Dungeon, Battlefield, Forest_Night, Mountain, Archaut_Council, Camp… |
| Kolejność | `connections[]` (`_sourceNode` → `_targetNode`), start = pierwszy węzeł; `_name` = numer kwestii („01”, „02”…) | ekstraktor zapisuje też numer `seq` z przejścia DFS |
| Wybory | `_message.Choices[]._key` w `MultipleChoiceStoryMessageNode`, `MultipleChoiceMessageNode`, `BinaryChoiceMessageNode`, `VirtueChoiceNode`/`StoryVirtueChoiceNode` | 806 kluczy opcji |
| Placeholdery | `{0}`, `{1}`… w tekście + `_message._arguments[].ArgType` | `RawText` 1414, `VariableString` 1084, `VariableInt` 825, `EntityName` 780, `EnemyNameWithArticle` 27, `ListOfKeys` 17 |
| Warunki / gałęzie | `ConditionNode`, `MultipleConditionNode`: `CheckHeroIsInPlay`, `CheckHeroVirtue`, `CheckProductOwned`, `CheckBoolean/Int/String` | — |

**Rich text** w tekstach fabularnych i komunikatach:
- `<i>…</i>` ×4027: warstwa fabularna komunikatów;
- `<style=Term><link=TERM_X>…</link></style>` ×2172: odnośniki do glosariusza;
- `<b>` ×81;
- `\n`;
- 509 glifów z obszaru Private Use (np. U+F5E5 = ikona obrażeń), które TTS musi pominąć albo zamienić na słowo.

Placeholderów `{n}` jest 1466 wystąpień w ok. 890 kluczach. Rozkład kluczy: komunikaty questowe 513, walka 298, zdarzenia 61, narracja 12, dialogi 5. Za placeholderami stoją imiona wrogów i bohaterów, liczby i nazwy przedmiotów.

**Warianty zależne od bohatera** to osobne klucze, a nie parametry. Przykładowo `…_05K` (Kehli) stoi za `CheckHeroIsInPlay(HERO_KEHLI)`. Za jawnym warunkiem na bohatera stoją 224 klucze. Sufiksy w `_name` (K, S, G, V, C, B…) zwykle odpowiadają bohaterowi albo gałęzi. Dochodzą do tego sloty `STORY_CHARACTER_VARIABLE_HERO1–4` (261 kwestii), które dopiero w runtime wskazują konkretnego bohatera z drużyny.

**Płeć:** w tekstach nie ma mechanizmu wariantów płci (brak parametrów I2, praktycznie brak form „(a)”). Formy rodzajowe są wpisane na sztywno, bo adresat jest znany: w dialogach „-łeś” pojawia się 93 razy, a „-łaś” 79 razy. Komunikaty zwracają się do gracza w 2. osobie, w liczbie pojedynczej albo mnogiej.

**Kolejność w scenariuszu:**
- kampania `d3/coreset/data` (`Campaign 1.asset`, `QuestModel`);
- Akt 1: Q1–Q14 + S1–S2;
- Akt 2 (DLE04): A2Q01–A2Q11;
- sceny fabularne `TANGERINE Qn Intro/Outro/Travel Story`, `A2 SSnn`, `Event nX …` wokół questów i na mapie świata.

**Przykładowe rekordy** (z wyjścia ekstraktora; zamiast tekstu opis, bo repozytorium nie zawiera treści gry):

| Typ | Rekord | Tekst PL (opis) |
|---|---|---|
| dialog | `d3/act1` · „TANGERINE Q9 Outro Win” · `StoryMessageNode` `04` · mówca `GALADEN` · tło Forest | krótka kwestia po walce, jedno zdanie |
| wariant | to samo, `05K` · warunek `HERO:HERO_KEHLI` · mówca `KEHLI` | okrzyk radości, dwa krótkie zdania |
| narracja | „TANGERINE Q10 Intro” `01` · brak mówcy · tło House | opis sali tronowej, kilka zdań |
| komunikat questu | scena Q10 · „DT Fire End of Round” · `MessageNode` · arg `VariableInt` | zdanie fabularne kursywą `<i>…</i>`, nowa linia, potem reguła z liczbą `{0}` |
| napis cutscenki | `CutsceneModel` `CUTSCENE_01` · `displayAt: 0.5` · bank `Voice_Cutscenes_Act1` | nazwa własna, dwa słowa |

## 5. Mówcy

51 identyfikatorów mówców. 46 z nich ma imię w modelu postaci, 4 to dynamiczne sloty bohatera, a 1 (`DRYS`) nie ma modelu. Kolumna „Kwestie” liczy unikalne klucze, w których postać mówi (`IsSpeaking`). Klucz z dwoma mówcami liczy się u obu.

| # | ID mówcy (`_characterId`) | Nazwa PL (EN) | Kwestie | Znaki PL |
|---:|---|---|---:|---:|
| 1 | `BRYNN` | Brynn | 666 | 51 619 |
| 2 | `SYRUS` | Syrus | 555 | 47 581 |
| 3 | `KEHLI` | Kehli | 537 | 43 436 |
| 4 | `VAERIX` | Vaerix | 520 | 39 133 |
| 5 | `GALADEN` | Galaden | 509 | 38 409 |
| 6 | `CHANCE` | Fuks (Chance) | 427 | 31 831 |
| 7 | `VARIABLE_HERO2` | *dynamiczny slot bohatera* | 201 | 7 699 |
| 8 | `BARONESSMAGRIT` | Baronessa Magrit (Baroness Magrit) | 142 | 15 695 |
| 9 | `ALYS` | Alys Raine | 97 | 10 748 |
| 10 | `BARONZACHARETH` | Baron Zachareth | 74 | 7 561 |
| 11 | `MASTERBRULI` | Mistrz Bruli (Master Bruli) | 72 | 5 857 |
| 12 | `RENEYR` | Hrabia Reneyr (Count Reneyr) | 69 | 7 619 |
| 13 | `LAUREL` | Laurel | 67 | 5 440 |
| 14 | `GREIGORY` | Baron Greigory | 65 | 6 919 |
| 15 | `RONAN` | Ronan | 63 | 5 189 |
| 16 | `BUTTON` | Guzik (Button) | 62 | 5 715 |
| 17 | `BARONESS_ADELYNN` | Baronessa Adelynn (Baroness Adelynn) | 60 | 5 165 |
| 18 | `VARIABLE_HERO1` | *dynamiczny slot bohatera* | 58 | 2 984 |
| 19 | `MASTERGALGORAZ` | Mistrz Galgoraz (Master Galgoraz) | 56 | 4 948 |
| 20 | `ASTARRA` | Astarra | 51 | 4 326 |
| 21 | `SIRBALTHAIN` | Sir Balthain | 43 | 4 708 |
| 22 | `COUNTESSDUCARD` | Hrabina Ducard (Countess Ducard) | 38 | 3 905 |
| 23 | `VETA` | Mistrzyni Runów Veta (Runemaster Veta) | 38 | 4 405 |
| 24 | `ARDEN` | Arden Gladhand | 38 | 4 717 |
| 25 | `TREVALYN` | Baron Trevalyn | 37 | 4 162 |
| 26 | `ELDERMOK` | Szaman Mok (Elder Mok) | 30 | 3 289 |
| 27 | `MASTERFLINT` | Mistrz Flint (Master Flint) | 27 | 2 559 |
| 28 | `GREYSDON` | Greysdon | 27 | 2 786 |
| 29 | `LTRAND` | Poruczniczka Rand (Lt. Rand) | 25 | 1 775 |
| 30 | `NAVOTH` | Dzwonniczka Navoth (Bellringer Navoth) | 25 | 2 771 |
| 31 | `KATHRYN` | Kathryn | 24 | 1 797 |
| 32 | `LEVIRAX` | Levirax | 23 | 2 583 |
| 33 | `WAIQAR` | Waiqar | 23 | 2 696 |
| 34 | `MORANT` | Morant Bratobójca (Morant the Kin-Killer) | 22 | 2 663 |
| 35 | `HERBIE` | Herbie | 18 | 1 694 |
| 36 | `OUTLAWPRINCE` | Książę Banita (The Outlaw Prince) | 17 | 1 253 |
| 37 | `DELPHYNDRA` | Smocza Władzcyni Delphyndra (Dragonlord Delphyndra) | 16 | 1 675 |
| 38 | `NARA` | Nara Kieł (Nara the Fang) | 15 | 1 563 |
| 39 | `GILLIAM` | Baron Gilliam | 15 | 1 967 |
| 40 | `BLOOD_SISTER` | Ne’Krul (Ne'Krul) | 11 | 706 |
| 41 | `CHANCE_SHADOW` | Cień (Shadow) | 11 | 311 |
| 42 | `GRACE` | Baronessa Grace (Baroness Grace) | 11 | 1 237 |
| 43 | `VRASKHAR` | Vraskhar | 10 | 821 |
| 44 | `PRYOR` | Baronessa Pryor (Baroness Pryor) | 10 | 1 879 |
| 45 | `GILLIAM_EVIL` | Baron Gilliam | 10 | 1 355 |
| 46 | `SHADOW_RENEYR` | Cień (Shadow) | 7 | 162 |
| 47 | `MEZA` | Strażniczka Meza (Sentinel Meza) | 4 | 448 |
| 48 | `DRYS` | *brak modelu postaci* | 3 | 260 |
| 49 | `VARIABLE_HERO3` | *dynamiczny slot bohatera* | 1 | 31 |
| 50 | `VARIABLE_HERO4` | *dynamiczny slot bohatera* | 1 | 27 |
| 51 | `DRAGON_HYBRID` | Xenith | 1 | 147 |

Narrator (okna fabularne bez mówcy) ma osobno 1015 kwestii i 115,6 tys. znaków. Komunikaty questowe i zdarzenia nie mają pola mówcy.

## 6. Statystyki

Znaki liczyłem po usunięciu tagów i glifów, z `{n}` liczonym jako 6 znaków. Klucz z wieloma użyciami liczy się raz, w najważniejszej kategorii. Pominąłem sceny deweloperskie (`Enemy Tool`, `Obstacle Course`).

| Kategoria | Klucze | Znaki PL | z tego `<i>` (fabularne) |
|---|---:|---:|---:|
| Dialog (okno fabularne z mówcą) | 4 777 | 393 531 | — |
| Narracja fabularna (okno bez mówcy) | 1 015 | 115 631 | — |
| Zdarzenia (podróż / narracyjne / miejskie / mapa) | 182 | 57 966 | 49 511 |
| Komunikaty questów (plansza) | 3 546 | 742 186 | 569 834 |
| Walka / teren / przedmioty | 531 | 92 962 | 58 361 |
| Opcje wyborów | 806 | 20 002 | — |
| Cele misji | 160 | 6 614 | — |
| Napisy cutscenek (*mają już nagrania*) | 115 | 6 856 | — |
| Opisy questów, dziennik, zdarzenia, ciekawostki (modele) | 566 | 85 918 | — |
| Nazwy wrogów, opisy atutów, imiona postaci (modele/CSV) | 457 | 22 349 | — |
| Szablony nagród (`GiveTreasure`, system) | 19 | 1 262 | — |
| UI / system | 2 263 | 115 973 | — |
| Glosariusz / zasady | 1 368 | 138 381 | — |
| Nieużywane (stare rewizje `TANGERINE_*`, nieodwołane klucze questów) | 1 351 | 100 420 | — |
| **Razem** | **17 156** | **1 900 051** | — |

**Szacunek długości audio** (poprawiony według [VOICES.md](VOICES.md) i [BENCH.md](BENCH.md); pierwsza wersja zakładała 15 znaków/s):
- polski lektor z przerywników czyta 9–10 znaków/s razem z pauzami;
- synteza Chatterboxa czyta 12,5–13,4 znaku/s.

| Zakres lektora | Klucze | Znaki | Audio przy tempie lektora (9 / 10 zn./s) | Audio z syntezy (13,4–12,5 zn./s) |
|---|---:|---:|---|---|
| A. Okna fabularne: dialog + narracja + zdarzenia | 5 974 | 567 128 | 17,5 / 15,8 h | 11,8–12,6 h |
| B. A + warstwa fabularna komunikatów (`<i>`) z questów i walki | — | 1 195 323 | 36,9 / 33,2 h | 24,8–26,6 h |
| C. A + pełne komunikaty (z regułami) + wybory + cele | 11 036 | 1 430 154 | 44,1 / 39,7 h | 29,6–31,8 h |
| D. C + opisy questów, dziennik, ciekawostki | 11 602 | 1 516 072 | 46,8 / 42,1 h | 31,4–33,7 h |

Czas generowania ≈ długość audio z syntezy × RTF silnika. Przy zmierzonym RTF Chatterboxa 2,1–2,5 na GTX 1650 Ti zakres A to ok. 25–30 h pracy GPU, a C ok. 64–75 h (BENCH.md). Spowolnienie syntezy do tempa lektora (np. time-stretch) wydłuża audio, ale nie czas generowania.

## 7. Czy da się odróżnić kategorie

Tak, prawie deterministycznie, bez heurystyk na treści:

| Kategoria | Rozpoznanie |
|---|---|
| **Dialog** | `StoryMessageNode` / `MultipleChoiceStoryMessageNode` / `StoryVirtueChoiceNode` z co najmniej jedną postacią `IsSpeaking: true` |
| **Narracja fabularna** | ten sam typ węzła bez `IsSpeaking` (portrety mogą być widoczne) |
| **Zdarzenie** | graf z `d3/travelevents`, `d3/narrativeevents`, `d3/cityevents`, `d3/worldmap/*` albo nazwa grafu „Travel Event…”, „Event nX…”, „City Event…”; węzły `MessageNode` / `BinaryChoiceMessageNode` |
| **Komunikat questu** | `MessageNode`, `ChallengeMessageNode` (test cechy), `MultipleChoiceMessageNode` w grafach scen questów; w środku `<i>…</i>` to warstwa fabularna, a tekst bez kursywy to reguły |
| **Walka / system** | grafy z `d3/enemies/*`, `d3/weapons/*`, `d3/coreset/*`, `d3/gamereq`; węzły `DisplayEnemyActivation`, `Spawn*`, `GiveTreasure`; prefiksy kluczy `ENEMY_`, `*_TACTIC_*`, `TERRAIN_`, `UI_`, `DEFAULT_`; źródło CSV `Main`/`Glossary`/`Enemy` |

Ograniczenia:
- niektóre klucze występują w kilku kontekstach (stosuję priorytet: dialog > narracja > zdarzenie > quest > walka);
- jeden `MessageNode` potrafi łączyć narrację i reguły, więc rozdzielam go po `<i>`;
- sloty `VARIABLE_HERO*` wskazują mówcę dopiero w trakcie gry.

## 8. Rekomendacja: hybryda (baza + pregenerowane audio), OCR tylko pomocniczo

**Rekomenduję hybrydę.** Uzasadnienie:

1. **Pełny, czysty tekst z metadanymi.** 100% tekstów PL jest dostępnych lokalnie, razem z kluczem, mówcą, tłem, kolejnością i wariantami. Pozwala to przypisać głos do postaci (51 mówców plus narrator), oczyścić tagi i glify oraz wygenerować audio offline w najlepszej jakości i z ręczną kontrolą. Zakres A to ok. 12–13 h audio z syntezy (16–17,5 h w tempie lektora).
2. **Wyzwalanie na żywo** (szczegóły w pkt 9):
   - **`.qlog` się do tego nie nadaje.** Gra zapisuje go tylko przy zapisie stanu, czyli z opóźnieniem do całej rundy, i pomija okna fabularne.
   - **Hook Mono** (BepInEx x86) daje klucz, argumenty i mówcę w chwili wyświetlenia, dla 100% okien:
     - komunikaty questu: subskrypcja istniejącego, nieużywanego przez grę delegata `MessageController.MessageDisplayBegin`;
     - okna fabularne: patch Harmony na `StoryMessageController.DisplayMessage`.

     To najdokładniejsza opcja. Wymaga dodania BepInEx do folderu gry, ale samych plików gry nie zmienia.
   - **OCR jako indeks:** zrzut okna → OCR → dopasowanie rozmyte do bazy 17 tys. kwestii → odtworzenie pliku. Błędy OCR nie psują wtedy wymowy, bo czytany jest tekst z bazy. To wariant bez ingerencji w folder gry.
3. **OCR jako jedyne źródło jest słabe:**
   - brak informacji o mówcy (zostaje tylko portret);
   - błędy na stylizowanych fontach i polskich znakach;
   - TTS musi działać na żywo, więc rośnie opóźnienie albo spada jakość głosu;
   - trudno oddzielić kursywę fabularną od reguł;
   - nie da się przygotować wariantów ani zrobić korekty wymowy nazw własnych.
4. **Elementy dynamiczne.** Około 890 kluczy z `{n}` (głównie komunikaty bojowe i questowe) można:
   - pregenerować w wariantach (6 bohaterów, ok. 112 nazw wrogów z `EnemyModel`, liczby), albo
   - składać z fragmentów, albo
   - generować na żywo tylko ten podzbiór.

   Dla `VARIABLE_HERO*` (261 kwestii) najlepiej pregenerować 6 wariantów głosu.
5. **Istniejące nagrania.** Bank `Polish.pck` ma 356 plików audio (wg `DIDX`):
   - przerywniki filmowe (`Voice_Cutscenes_Act1/2`, napisy 115 kluczy);
   - okrzyki bohaterów i złoczyńców (`Voice_Heroes_*`, `Voice_Villains_*`).

   **Żaden z nich nie jest identyczny z wersją EN**, podczas gdy paczki HU, KO i ZH to kopie EN 1:1. Paczka PL to więc najpewniej osobne nagranie (do potwierdzenia odsłuchem). Tych elementów nie trzeba udźwiękawiać, za to okna fabularne i komunikaty nie mają żadnego głosu.
6. **Aktualizacje gry.** Klucze są stabilne. Po każdej aktualizacji wystarczy ponownie uruchomić skrypty z `analysis/tools/` i dograć audio dla zmienionych lub nowych kluczy (różnica tekstów PL per klucz).

## 9. Weryfikacja `.qlog`

Sprawdziłem to na dwa sposoby:
- dekompilacja kopii `Assembly-CSharp.dll` (ILSpy, `analysis/work/decompiled/`) i analiza klas `MasterMessageCache`, `MessageController`, `StoryMessageController`, `SaveLoadController`, `QuestLogEntry`;
- odczyt istniejących plików z `SavedGames\1`.

**Co trafia do logu:**
- tylko okna obsługiwane przez `FFG.Core.MessageController`: `MessageNode`, `MultipleChoiceMessageNode`, `BinaryChoiceMessageNode`, `ChallengeMessageNode`, `VirtueChoiceNode`, `EnemySelectMessageNode`, wybór gracza, interakcje;
- i tylko w scenie questu (`Scene.Game`, warunek w `FinishPendingMessage`);
- do tego podsumowania ataków (`UI_LOG_HEROATTACK`, `UI_LOG_ENEMYATTACK` z kluczem aktywacji po `@`) i zmiany faz.

**Czego w logu nie ma:**
- okien fabularnych `StoryMessageNode` (`StoryMessageController` w ogóle nie używa `MessageCache`), także tych w scenach questów;
- zdarzeń z mapy świata i miasta (inne sceny; zapis na mapie zamyka strumień logu bez zapisu);
- cutscenek;
- samego okna aktywacji wroga (zostaje tylko podsumowanie).

**Kiedy:**
- Wpis trafia do pamięci dopiero **po zamknięciu** okna (`FinishPendingMessage`), a nie w chwili wyświetlenia.
- Na dysk lądują wszystkie zbuforowane wpisy naraz, i tylko przy zapisie w scenie questu:
  - autozapis po przygotowaniu („Default After Setup”),
  - autozapis **na końcu każdej rundy** („Default End of Round”),
  - ręczny zapis albo „zapisz i wyjdź”,
  - jeden graf questu DLE04 („DT Defense”).
- Każdy zapis tworzy nowy plik `yyyy-MM-dd_HH-mm-ss.qlog` z **pełną historią questu**. Gra trzyma 5 najnowszych.

**Format** (`QuestLogEntry.GetCompressedMessage`), UTF-8 bez BOM, końce linii CRLF:

```text
<SlotGUID>|<DateTime.Ticks>|<QuestId>          ← nagłówek, np. …|STORY_QUEST_1
<runda>|<klucz>|<typ>[|arg1|arg2…]              ← wpisy od NAJNOWSZEGO do najstarszego
```

- typ: 0 Standard, 1 Phase (klucz = numer fazy), 2 Attack, 3 Instruction, 4 Story;
- argumenty to klucze lokalizacji (np. `HERO_BRYNN_NAME`) albo wartości;
- `@` oddziela argumenty aktywacji;
- `{BR}` oznacza nową linię.

Istniejący plik z Q1 ma 12 wpisów. Po odwróceniu kolejność zgadza się z przebiegiem questu: wybór wartownika → Brynn na warcie → narracja o upływie nocy → powitanie samouczka → rozstawienie → cel misji → faza 1.

**Wniosek:** `.qlog` **nie nadaje się do wyzwalania lektora na żywo**: opóźnienie sięga całej rundy, a okna fabularne są pominięte. Przydaje się natomiast do:
- ustalenia kontekstu po wczytaniu gry (quest, runda, które komunikaty już padły);
- testów pokrycia bazy audio;
- ewentualnej funkcji „przeczytaj podsumowanie ostatniej rundy”.

Przy okazji: komunikaty questu zawierają też cytowane wypowiedzi postaci w kursywie (np. „…” – mówi Brynn) bez pola mówcy. Dla nich naturalny jest głos narratora.

Do sprawdzenia tego w praktyce służy `analysis/tools/qlog_watch.py`. Skrypt w trybie tylko do odczytu obserwuje `SavedGames` i po każdym zapisie wypisuje nowe wpisy z kategorią i tekstem PL:

```bash
.venv/Scripts/python -I analysis/tools/qlog_watch.py
```

## Narzędzia (w `analysis/tools/`)

Uruchamiane z katalogu głównego repozytorium przez `.venv/Scripts/python -I analysis/tools/<skrypt>.py`. Skrypty ze stałymi ścieżkami liczą je względem `analysis/` i operują na kopiach w `analysis/work/` niezależnie od bieżącego katalogu; pozostałe (`manifest_summary.py`, `peek_*.py`, `dump_mb.py`, `index_bundles.py`) dostają ścieżki w argumentach.

| Skrypt | Działanie |
|---|---|
| `manifest_summary.py` | grupy bundli i bundle tekstowe z `manifest.dat` |
| `index_bundles.py`, `scan_classes.py` | indeks bundli (StreamingAssets + cache) oraz klasy MonoBehaviour i grafy w nich |
| `survey_graphs.py` | typy węzłów i zadań NodeCanvas |
| `extract_lines.py` | słownik PL (`pl_terms.json`) + rekordy kwestii (`lines.jsonl`: graf, węzeł, klucz, rola, mówcy, tło, warunki, `seq`) |
| `analyze.py` | statystyki (`stats.json`) i kategorie kluczy (`key_categories.json`) |
| `pck_compare.py` | porównanie paczek głosowych Wwise PL / EN / inne |
| `qlog_watch.py` | podgląd `.qlog` w trakcie gry (tylko odczyt) |
