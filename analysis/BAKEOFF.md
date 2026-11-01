# E0 · Porównanie modeli TTS

Data: 2026-10-31 – 2026-11-01. GTX 1650 Ti 4 GB, Windows 11.
Próbki, transkrypcje i wyniki z tekstami są prywatne: `analysis/work/bakeoff/` (`index.html` i `r2.html` do odsłuchu i ocen, `INDEX.md`, `eval.json`, `oceny_tts.csv`, `oceny_r2.csv`).

| Skrypt | Rola |
|---|---|
| `analysis/tools/normalize_pl.py` | normalizacja-prototyp wspólna dla wszystkich modeli: tagi, ikony na słowa, liczby na słowa z odmianą |
| `analysis/tools/bakeoff_set.py` | zestaw testowy, słownik emocji, referencje emocjonalne z dubbingu, transkrypcja referencji (Whisper) |
| `analysis/tools/bakeoff_gen.py` | generowanie w środowisku danego modelu, pomiar czasu i VRAM |
| `analysis/tools/bakeoff_eval.py` | ASR (CER/WER), podobieństwo głosu, wybór najlepszego podejścia, głośność -20 LUFS, strona odsłuchu |
| `analysis/envs/create_envs.sh` + `<model>.txt` | środowiska kandydatów z przypiętymi wersjami |

## Kandydaci

| Model | Kod i wagi | Środowisko | Ustawienia | Licencja wag |
|---|---|---|---|---|
| Chatterbox v2 (dostrojony) | `chatterbox-tts` 0.1.7 | `.venv` (Python 3.13, torch 2.6.0+cu124) | fp32, cfg 0,3, exaggeration ze słownika emocji, własna pętla T3 (repetition_penalty 2,0, min_p 0,05), offload kondycjonowania | MIT |
| Chatterbox v3 | `resemble-ai/chatterbox` master `5de7a54` (2026-07-21), wagi T3 v3 | `%LOCALAPPDATA%\LektorPL\envs\chatterbox3` (Python 3.12, torch 2.6.0+cu124) | oficjalne `generate()`, te same cfg i exaggeration, offload kondycjonowania | MIT |
| XTTS-v2 | `coqui-tts` 0.28.0 | `...\envs\xtts` (torch 2.6.0+cu124) | domyślne | CPML, niekomercyjna (D29) |
| OmniVoice | `k2-fsa/OmniVoice` master `08be0b4` (2026-08-24) | `...\envs\omnivoice` (torch 2.8.0+cu128) | fp16, 32 kroki | niekomercyjna; kod Apache-2.0 |

Środowiska poza `.venv` powstają przez `bash analysis/envs/create_envs.sh` z Pythona projektu (uv, D12). Wagi leżą w `analysis/work/hf_cache`.

## Zestaw

- **Fragmenty:** 12 z M1, opisane w `set.json` kluczem i własnym opisem:
  - dialogi czterech bohaterów z różnymi emocjami i okrzyk;
  - dwie narracje, w tym długi komunikat z imieniem bohatera;
  - reguła z liczbami i ikoną;
  - aktywacja wroga i cel misji z licznikiem (głos systemowy);
  - opcja wyboru z cytatem bohaterki (D20);
  - komunikat z nazwami wrogów sklejany z fragmentów (D16).
- **Referencje:** 31 nagrań z polskiego dubbingu: 4 bohaterów × 7 emocji i narrator × 3. Głos systemowy to narrator w stylu neutralnym (kwestia e).
- **Zadania:** 29 na model, razem 67 próbek:

| Wariant | Zadania | Podejścia | Co sprawdza |
|---|---|---|---|
| A | 12 | 3 | referencja neutralna |
| B | 7 | 3 | referencja emocjonalna (D28) |
| T2 / T3 | 2 / 2 | 1 | zdania osobno z pauzą 0,5 s / pauza 0,4 s i tempo 0,9 (kwestia b) |
| N1 / N2 | 2 / 2 | 1 | nazwa zapisana fonetycznie / po angielsku jako osobny fragment (kwestia u) |
| Q | 1 | 1 | cytat głosem bohaterki + opis narratora (D20) |
| S | 1 | 1 | sklejanie fragmentów (D16) |

Każdy model dostaje ten sam tekst po normalizacji, te same referencje, podział i ziarna losowania.

## Wydajność

RTF to czas generowania podzielony przez długość audio, bez ładowania modelu.

| Model | RTF łącznie | RTF min–maks | Znaki/s generowania | Znaki/s audio | Szczyt VRAM (allocated) | Ładowanie |
|---|---|---|---|---|---|---|
| Chatterbox v2 | 2,80 | 2,0–4,1 | 4,6 | 12,8 | 2,9 GB | 45 s |
| Chatterbox v3 | 2,31 | 1,9–3,6 | 5,5 | 12,8 | 2,9 GB | 53 s |
| XTTS-v2 | **0,98** | 0,7–1,2 | **12,0** | 11,8 | **1,9 GB** | 46 s |
| OmniVoice | 17,4 | 12,6–52 | 0,6 | **10,6** | 2,2 GB | 102–113 s |

- **Liczone bez F05_A.** Jego trzy podejścia powstały w przebiegu smoke. U Chatterboxa ten proces liczył od zera kondycjonowanie 31 referencji, stąd 10,9 GB allocated (część w pamięci współdzielonej) i RTF 3–4. W pełnym przebiegu kondycjonowanie wczytywało się z cache.
- **OmniVoice** mieści się w VRAM, więc jego wolne tempo nie wynika z przepełnienia pamięci. Czas jednego wywołania to ok. 60 s stałego kosztu i ok. 10 s na sekundę audio (dopasowanie dla kwestii z jednego fragmentu). Krótkie kwestie mają przez to RTF 20–50. Pełny zestaw generował się 4,6 h, a pozostałe modele 11–30 min. Liczby po poprawce referencji narratora (niżej).
- **Tempo mowy:** lektor z dubbingu czyta 9–10 znaków/s z pauzami (`VOICES.md`). Najbliżej jest OmniVoice, a Chatterbox jest ok. 30% szybszy, tak jak w `BENCH.md`. Warianty T2 i T3 (pauzy, tempo 0,9) są w liczbach wszystkich modeli.

Szacowany czas jednego przebiegu na tym GPU (znaki z `BENCH.md`, bez ponownych podejść):

| Zakres | Chatterbox v2 | Chatterbox v3 | XTTS-v2 | OmniVoice |
|---|---|---|---|---|
| milestone 1 (70,5 tys. znaków) | 4 h 17 min | 3 h 33 min | 1 h 38 min | ok. 32 h |
| A (567 tys.) | 34 h | 28,5 h | 13 h | ok. 11 dób |
| C (1,43 mln) | 87 h | 72 h | 33 h | ok. 27 dób |

Przy 3 podejściach na kwestię (wybór przez ASR) czasy rosną trzykrotnie. OmniVoice na tej karcie nadaje się tylko do pojedynczych kwestii. Całe M1 wymagałoby innego sprzętu albo generowania wsadowego (`generate` przyjmuje listę tekstów), czego nie testowałem.

## Dokładność i podobieństwo głosu

ASR: Whisper large-v3-turbo, tekst po normalizacji `tts_bench.norm_words`. Podobieństwo: VoiceEncoder Chatterboxa, cosinus do neutralnej referencji danego głosu. Najlepsze podejście to najniższy CER, a przy remisie wyższe podobieństwo.

| Model | CER mediana, wszystkie | CER mediana, najlepsze | Zadania z CER > 10% (najlepsze) | Podobieństwo, mediana |
|---|---|---|---|---|
| Chatterbox v2 | 1,5% | 1,1% | 0 | 0,934 |
| Chatterbox v3 | 1,1% | 0,9% | 1 | 0,938 |
| XTTS-v2 | 0,6% | **0,0%** | 2 | 0,923 |
| OmniVoice (po poprawce) | **0,0%** | **0,0%** | **0** | **0,950** |

Mediana CER (najlepsze podejście) i podobieństwo według wariantu:

| Wariant | Chatterbox v2 | Chatterbox v3 | XTTS-v2 | OmniVoice |
|---|---|---|---|---|
| A | 0,4% / 0,936 | 0,0% / 0,936 | 0,0% / 0,923 | 0,0% / 0,954 |
| B | 0,8% / 0,914 | 1,0% / 0,894 | 0,0% / 0,909 | 0,0% / 0,935 |
| T2 | 0,9% / 0,954 | 0,4% / 0,958 | 0,4% / 0,923 | 0,4% / 0,964 |
| T3 | 4,5% / 0,956 | 0,4% / 0,963 | 0,3% / 0,926 | 0,8% / 0,968 |
| N1 | 3,1% / 0,941 | 3,1% / 0,936 | 12,8% / 0,926 | 3,1% / 0,936 |
| N2 | 7,2% / 0,939 | 13,3% / 0,946 | 1,6% / 0,931 | 0,0% / 0,957 |
| Q | 2,9% / 0,817 | 2,9% / 0,846 | 47,1% / 0,883 | 2,9% / 0,817 |
| S | 4,3% / 0,941 | 7,4% / 0,951 | 2,1% / 0,944 | 1,1% / 0,944 |

Obserwacje:
- **Wszystkie modele czytają polski poprawnie.** Błędy skupiają się w kilku wariantach, a zwykłe dialogi i komunikaty mają CER bliski zera.
- **Nazwy (kwestia u):**
  - nazwa po angielsku jako osobny fragment (N2) psuje Chatterboxa: v3 w jednym zadaniu dopowiada kilka słów (CER 27%);
  - XTTS radzi sobie z N2, ale gubi słowa przy zapisie fonetycznym (N1, CER 22% w jednym zadaniu);
  - OmniVoice czyta N2 bez błędów.
- **Bardzo krótki cytat (Q, D20):** XTTS przy cytacie z trzech słów dodaje słowa, które nie padają w tekście (CER 47%). To znana słabość XTTS przy krótkich wejściach.
- **Referencja emocjonalna (B)** obniża podobieństwo do neutralnej referencji o 0,01–0,04. Tego się spodziewaliśmy, bo zmienia barwę. Czy oddaje emocję, rozstrzyga odsłuch.
- **Flaga „ucięta końcówka”** pojawia się u wszystkich modeli w tych samych zadaniach (Q i komunikaty z nazwą wroga na końcu). To raczej zapis nazwy przez Whispera niż ucięcie. Do sprawdzenia uchem.

### OmniVoice: dopowiadanie transkrypcji referencji

W pierwszym przebiegu OmniVoice dopowiadał na początku próbek narratora i systemu 1–12 słów z końca transkrypcji referencji, bez wyjątku we wszystkich takich zadaniach. Stąd CER 6–38%. Próbki bohaterów nie miały tego błędu.

- **Przyczyna:** referencje narratora to ciągłe 15-sekundowe wycinki przerywników z muzyką pod spodem, ucięte w środku mowy. Referencje bohaterów są sklejone z kilku kwestii, z ciszą na końcu. OmniVoice jako jedyny korzysta z transkrypcji referencji i przy ucięciu w środku słowa źle dopasowuje ją do audio.
- **Poprawka** (`bakeoff_set.py --short-prompts`):
  - tylko dla OmniVoice biorę wycinki 7,6–9,6 s według znaczników czasu słów z Whispera, od pełnego zdania do zdania albo pauzy;
  - transkrypcja zawiera dokładnie słowa z wycinka;
  - model zaleca referencje 3–10 s.
- **Zakres powtórki:** 33 próbki narratora i systemu. Pierwszy przebieg jest w `work/bakeoff/omnivoice_v1/`. Pozostałe modele nie używają transkrypcji, więc ich wyniki zostają.

Po poprawce:
- **Zgodność:** we wszystkich 15 zadaniach narratora i systemu CER najlepszego podejścia wynosi 0–1,1%, a wcześniej 6–38%. Żadna próbka nie zaczyna się od słów z referencji.
- **Szybkość:** RTF spadł z 16–59 do 13–52, bo prompt jest krótszy.
- **Wniosek na E2/E3:** referencje dla modeli z transkrypcją tniemy na granicach słów, a transkrypcję bierzemy z tego samego wycinka.

## Odsłuch

Arkusz: `analysis/work/bakeoff/index.html`. Dla każdego zadania i modelu jest karta z najlepszym podejściem (głośność wyrównana do -20 LUFS) i oceny 1–5: naturalność, wymowa, emocja. Oceny zapisują się w przeglądarce, a eksport daje plik CSV.

### Runda 1: cztery modele (2026-11-01)

Ocenione wszystkie 116 kart (29 zadań × 4 modele). Średnie 1–5 (naturalność / wymowa / emocja):

| Model | Wszystkie | A, bohaterowie | A, narrator i system | B | T2/T3 | N1 | N2 | Q | S |
|---|---|---|---|---|---|---|---|---|---|
| Chatterbox v2 | 2,3 / 2,5 / 2,5 | 2,8 / 2,4 / 2,8 | 2,9 / 3,1 / 2,7 | 2,1 / 1,9 / 1,9 | 2,0 / 2,0 / 2,5 | 3,5 / 4,5 / 3,5 | 1,0 / 1,0 / 2,5 | 1 / 3 / 2 | 1 / 3 / 3 |
| Chatterbox v3 | 2,5 / 2,7 / 2,9 | 3,2 / 2,4 / 3,0 | 3,0 / 3,0 / 3,1 | 2,3 / 2,4 / 2,3 | 2,0 / 2,5 / 3,0 | 2,5 / 4,0 / 3,5 | 1,0 / 1,0 / 2,0 | 3 / 4 / 4 | 1 / 4 / 3 |
| XTTS-v2 | 2,1 / 3,1 / 3,2 | 2,6 / 4,0 / 3,8 | 2,4 / 3,0 / 3,9 | 2,3 / 3,1 / 3,3 | 1,5 / 2,8 / 3,5 | 2,0 / 3,5 / 1,5 | 1,0 / 2,5 / 1,5 | 1 / 1 / 1 | 1 / 4 / 4 |
| OmniVoice | **3,0 / 3,8 / 3,9** | 2,6 / 4,0 / 4,2 | **3,7 / 4,1 / 4,1** | **2,6 / 4,0 / 4,0** | **3,8 / 4,0 / 4,0** | 2,0 / 2,5 / 4,0 | 1,5 / 2,5 / 2,0 | **4 / 4 / 4** | **4 / 4 / 4** |

Uwagi z arkusza:
- **OmniVoice** jest najbardziej niezawodny. Najczęstsza uwaga to „za wolno” (14 kart). Przy krótkich komunikatach w trakcie rozgrywki akcent jest za mocny. Mocny akcent i naturalne tempo pasują do narratora w scenach między rozgrywkami. U bohaterów naturalność (2,6) wyraźnie odstaje od wymowy i emocji, właśnie przez tempo.
- **Chatterbox v2** w 8 kartach ma dziwne dźwięki na końcu próbki, a referencja emocjonalna daje obcy akcent. Wymowa bohaterów w obu wersjach Chatterboxa jest słaba (2,4).
- **XTTS-v2** ma dobrą wymowę, ale najniższą naturalność. Cytat Q jest zepsuty (1 / 1 / 1), a przy N1 emocja jest przesadzona.
- **Nazwy (u):** wklejenie nazwy po angielsku (N2) źle wypada u wszystkich modeli („źle czyta”, F02 N2: 1 / 1 / 1). Zapis fonetyczny (N1) najlepiej wypada u Chatterboxa v2, a u OmniVoice w jednym zadaniu daje błąd wymowy.
- **Referencja emocjonalna (B)** nie poprawia wyniku w żadnym modelu. U OmniVoice narrator z referencją napiętą jest „gorszy od wersji naturalnej”.
- **Pauzy:** 0,4–0,5 s między zdaniami to za dużo (T3 u OmniVoice: „za duże pauzy”).
- **Cytat (Q, D20):** OmniVoice 4 / 4 / 4. Przy opcji czytanej w całości narratorem (F11 A) słowa bohaterki powinny brzmieć mocniej niż komentarz narratora, co potwierdza podział z D20.

### Runda 2: tempo i akcent OmniVoice

Tylko OmniVoice, 10 fragmentów: dialogi bohaterów (F01–F05) oraz narrator i system w trakcie rozgrywki (F07–F10, F12). Narracja scen między rozgrywkami (F06, F11) zostaje w wariancie A. Każdy wariant to jedno podejście z ziarnem pierwszego podejścia A, pauza między zdaniami 0,25 s (A: 0,35 s). Strona odsłuchu: `analysis/work/bakeoff/r2.html` (A obok P1–P4).

| Wariant | Ustawienia | CER | Podobieństwo | Tempo, zn./s | Rozrzut F0, półtony | RTF łącznie | M1, jedno podejście |
|---|---|---|---|---|---|---|---|
| A | tempo z referencji, CFG 2,0, 32 kroki | 0,0% | 0,954 | 10,3 | 4,17 | 17,5 | ok. 33 h |
| P1 | tempo 1,2 | 0,4% | 0,940 | 12,1 | 3,97 | 18,7 | ok. 30 h |
| P2 | tempo 1,2, CFG 1,4 | 0,5% | 0,942 | 12,2 | 3,87 | 18,8 | ok. 30 h |
| P3 | tempo 1,35, CFG 1,4 | 0,5% | 0,925 | 13,7 | 3,58 | 20,1 | ok. 29 h |
| P4 | jak P2, 16 kroków | 0,0% | 0,938 | 12,3 | 3,85 | **9,5** | **ok. 15 h** |

Mediany po fragmentach. A to najlepsze z 3 podejść, P1–P4 po jednym, więc CER A jest lekko uprzywilejowany. Tempo dla porównania: Chatterbox 12,9–13,4, XTTS 12,4 zn./s.

- **Tempo:** `speed` 1,2 przyspiesza mowę o ok. 18%, do poziomu pozostałych modeli. Podobieństwo spada o ok. 0,015, a przy 1,35 o ok. 0,03.
- **Akcent:** niższe CFG prawie nie zmienia rozrzutu wysokości głosu (P2 wobec P1: 3,87 wobec 3,97, a w połowie fragmentów rozrzut rośnie). Wyraźniej spłaszcza mowę szybsze tempo (P3: 3,58). Rozrzut F0 to tylko przybliżenie akcentowania, bo akcent to też głośność i długość sylab. Rozstrzyga odsłuch.
- **16 kroków (P4):** te same pomiary co P2 przy połowie czasu. Jeśli w odsłuchu nie odstaje od P2, M1 skraca się z ok. 30 h do ok. 15 h na tej karcie.
- **Koszt wywołania:** model co krok przelicza cały ciąg (styl, tekst, referencja, cel) dwa razy, z warunkiem i bez (CFG). Gałąź bez warunku jest dopełniana do długości gałęzi z warunkiem. Dalsze rezerwy na E3: krótsze referencje bohaterów (obecnie 9–15 s) i liczenie gałęzi bez warunku bez dopełnienia.

Odsłuch rundy 2 (50 kart, średnie naturalność / wymowa / emocja):

| Wariant | Średnia | Krótkie (37–58 zn.: F05, F09, F10) | Średnie (81–104 zn.: F01, F02, F04, F12) | Długie (128–335 zn.: F03, F07, F08) |
|---|---|---|---|---|
| A | 3,0 / 3,8 / 3,5 | 3,3 / 3,7 / 3,3 | 2,8 / 3,8 / 3,2 | 3,0 / 4,0 / 4,0 |
| P1 | **3,5 / 3,7 / 3,8** | 3,3 / 3,7 / 4,0 | 3,2 / 3,5 / 3,2 | **4,0 / 4,0 / 4,3** |
| P2 | 3,5 / 3,7 / 3,5 | 3,3 / 3,7 / 3,7 | 3,2 / 3,8 / 3,2 | 4,0 / 3,7 / 3,7 |
| P3 | 3,3 / 3,5 / 3,4 | 3,0 / 3,7 / 3,3 | 3,0 / 3,0 / 3,2 | 4,0 / 4,0 / 3,7 |
| P4 | 3,2 / 3,5 / 3,3 | 3,3 / 3,0 / 3,7 | 2,5 / 3,5 / 2,8 | 4,0 / 4,0 / 3,7 |

Wnioski z odsłuchu:
- **Kroki:** 32 kroki brzmią lepiej i mają mniej błędów niż 16 (P4 wobec P2, m.in. błąd wymowy w F10). Oszczędność czasu z P4 odpada.
- **Tempo:** szybsze od naturalnego brzmi lepiej. Najszybsze (1,35) pasuje do długich tekstów, a do krótkich lepiej tylko trochę szybsze od naturalnego. Przy 1,35 krótka kwestia F02 dostała 1 / 1 / 2.
- **Akcent:** niższe CFG (P2) nie poprawia oceny, a obniża emocję (3,5 wobec 3,8 w P1). Zostaje domyślne CFG 2,0.
- **Ucięta końcówka:** w krótkim okrzyku (F05, 37 zn.) przy tempie 1,2 koniec się urywa. OmniVoice z góry ustala długość wyniku według tempa, więc przy krótkich kwestiach zapas jest mały. To kolejny powód, żeby krótkie kwestie przyspieszać mniej.
- **Dwa głosy:** w F01 (Syrus, dwie angielskie nazwy) wszystkie warianty P brzmią „jak 2 osobne głosy”, a wybrany A nie. Podobieństwo pierwszej i drugiej połowy próbki tego nie wykrywa (F01 P: 0,86–0,90 wobec 0,83 w A). Na E3: kilka podejść dla kwestii bohaterów i lista odsłuchu. Do sprawdzenia też referencja Syrusa, która jest sklejona z kilku nagrań i ma 14,9 s.

## Wnioski

Decyzje po odsłuchu i QA (`docs/DECISIONS.md`):
- **Model (D33):** OmniVoice, fp16, 32 kroki, CFG 2,0. Referencje cięte na granicach słów.
- **Tempo (D34):** narracja w scenach fabularnych w tempie naturalnym. Dialogi oraz narrator i system w trakcie rozgrywki: 1,2, rosnące z długością kwestii do 1,4, pauza 0,25 s.
- **Ekspresja (D35):** jedna neutralna referencja na głos. Referencje emocjonalne i adnotacja emocji wypadają z M1.
- **Głos systemowy (D36):** narrator.
- **Nazwy (D37):** jak zapisane, zapis fonetyczny tylko dla wyjątków.
- **E3 (D38, D39):** bohaterowie 3 podejścia, reszta 1 i ponowne dla odrzuconych. Model dla całej gry wybieramy po E3.

Zestawienie modeli z pomiarów automatycznych (przed odsłuchem):

| Model | Za | Przeciw |
|---|---|---|
| Chatterbox v2 | znany z `BENCH.md`, poprawny tekst | najwolniejszy z praktycznych (M1 ok. 4,3 h na podejście), tempo 30% szybsze od lektora |
| Chatterbox v3 | szybszy od v2 (RTF 2,3), podobieństwo i CER podobne | wklejona angielska nazwa (N2) potrafi wywołać dopowiedzenie |
| XTTS-v2 | najszybszy (RTF ok. 1, M1 ok. 1,6 h), najmniej VRAM, najniższy CER zwykłych kwestii | najniższe podobieństwo głosu, błędy przy bardzo krótkich wejściach (cytat D20) i zapisie fonetycznym |
| OmniVoice | najlepszy CER i podobieństwo, tempo najbliższe lektorowi, poprawne angielskie nazwy | na tej karcie ok. 32 h na M1 (RTF ok. 17), wymaga starannie przyciętych referencji z transkrypcją |

- **Nazwy (u):** żaden wariant nie jest bezpieczny we wszystkich modelach. Wybór zależy od modelu.
- **Tempo (b):** Chatterbox potrzebuje T2 albo T3. Oba nie pogarszają CER w v3. OmniVoice i XTTS są bliżej lektora już bez zmian.
