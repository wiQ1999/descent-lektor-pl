# E11 · Arkusz porównawczy głosów

Pytanie etapu: którego modelu użyć (lokalny OmniVoice czy ElevenLabs przez MCP) dla narratora, bohaterów z głosem z gry i pozostałych postaci (D77–D79). Raport podaje liczby. Kwestie, nagrania i strony ocen leżą w `analysis/work/compare/e11/`.

## Metoda

- Kwestie: po 2 losowe z bazy M2 na postać (`voice_compare.py pick`, ziarno 20261107), jeden fragment, co najmniej 7 słów, do 220 znaków. Ne’Krul i Xenith mają w M2 po jednej kwestii.
- Głosy z dubbingu (9): referencja z gry wobec OmniVoice, bez ElevenLabs (D77).
- Postacie bez dubbingu (11), runda 1: obecny głos OmniVoice wobec 3 wariantów ElevenLabs z różnych opisów (`text_to_voice`, 3 podglądy na opis, do arkusza najlepszy według automatu, D78).
- Runda 2: jeden głos ElevenLabs na postać, zapisany na koncie, te same kwestie czytane czterema modelami TTS z domyślnymi ustawieniami (D79).
- Ocena na ślepo w skali 1–5 (jedna osoba, użytkownik), nagrania wyrównane do -20 LUFS. Automat E3: CER z Whisper, ucięta końcówka, dziury, tempo, barwa (VoiceEncoder).

## Głosy z dubbingu: OmniVoice wobec oryginału

| Głos | Jakość | Podobieństwo | CER | Barwa wobec dubbingu | F0 OmniVoice / dubbing (Hz) |
|---|---:|---:|---:|---:|---|
| narrator | 4 | 4 | 0,6% | 0,960 | 115 / 118 |
| nekrul | 5 | 5 | 4,3% | 0,880 | 176 / 225 |
| xenith | 4 | 5 | 1,4% | 0,930 | 111 / 104 |
| brynn | 5 | 4 | 1,0% | 0,959 | 229 / 226 |
| syrus | 5 | 4 | 0,5% | 0,961 | 110 / 110 |
| galaden | 5 | 5 | 1,4% | 0,940 | 150 / 149 |
| vaerix | 4 | 4 | 0,0% | 0,959 | 111 / 97 |
| kehli | 5 | 4 | 0,0% | 0,920 | 197 / 220 |
| chance | 4 | 3 | 0,0% | 0,934 | 222 / 195 |
| **średnio** | **4,56** | **4,22** | 1,0% | 0,938 | |

Kwestia Ne’Krula ma uwagę automatu z E7 (końcówka, tempo), a mimo to dostała 5.

## Postacie bez dubbingu, runda 1: OmniVoice wobec wariantów ElevenLabs

| Postać | OmniVoice | Wariant a | Wariant b | Wariant c |
|---|---:|---:|---:|---:|
| adelynn | 4 | 2 | 4 | 2 |
| ronan | 1 | 4 | 5 | 2 |
| astarra | 2 | 4 | 5 | 5 |
| kathryn | 2 | 5 | 3 | 5 |
| ltrand | 2 | 4 | 3 | 3 |
| bruli | 1 | 5 | 5 | 5 |
| herbie | 1 | 4 | 4 | 5 |
| mok | 1 | 4 | 4 | 3 |
| outlaw | 1 | 4 | 5 | 4 |
| flint | 3 | 5 | 4 | 5 |
| galgoraz | 3 | 5 | 4 | 5 |
| **średnio** | **1,91** | **4,18** | **4,18** | **4,00** |

- Najlepszy wariant ElevenLabs średnio 4,73. ElevenLabs wygrał u 10 z 11 postaci, a u Adelynn zremisował z OmniVoice.
- Remisy między wariantami: Astarra (b, c), Kathryn (a, c), Bruli (a, b, c), Mok (a, b), Flint (a, c), Galgoraz (a, c).
- Automat: 99 podglądów, średni CER 0,3%, bez uciętych końcówek i dziur. OmniVoice tych postaci: średni CER 0,8%.

## Runda 2: cztery modele TTS jednym głosem

| Postać (wariant) | v4 | Multilingual v2 | Flash v2.5 | v3 |
|---|---:|---:|---:|---:|
| adelynn (b) | 3 | 3 | 2 | 2 |
| ronan (b) | 4 | 4 | 4 | 4 |
| astarra (b) | 5 | 4 | 4 | 5 |
| kathryn (a) | 5 | 5 | 3 | 3 |
| ltrand (a) | 3 | 4 | 3 | 3 |
| bruli (a) | 5 | 5 | 3 | 3 |
| herbie (c) | 4 | 3 | 2 | 3 |
| mok (a) | 4 | 2 | 2 | 4 |
| outlaw (b) | 5 | 5 | 2 | 3 |
| flint (a) | 5 | 5 | 4 | 3 |
| galgoraz (a) | 5 | 5 | 4 | 5 |
| **średnio** | **4,36** | **4,09** | **3,00** | **3,45** |
| najlepszy lub ex aequo | 10 z 11 | 8 z 11 | 1 z 11 | 4 z 11 |

| Model | Kredyty na znak | CER | Barwa wobec podglądu z rundy 1 | Tempo wobec lektora |
|---|---:|---:|---:|---:|
| `eleven_v4` | 0,44 | 0,6% | 0,963 | 1,35 |
| `eleven_multilingual_v2` | 0,44 | 0,3% | 0,964 | 1,35 |
| `eleven_flash_v2_5` | 0,22 | 0,3% | 0,945 | 1,53 |
| `eleven_v3` | 0,44 | 0,3% | 0,924 | 1,43 |

- Stawki pochodzą z historii konta: 1921 znaków na model. Automat nie znalazł uciętych końcówek ani dziur w 44 nagraniach.
- Według użytkownika między najlepszymi modelami nie ma znaczących różnic. v4 i Multilingual v2 kosztują tyle samo.
- Flash jest o połowę tańszy, ale dostał najniższe oceny i czyta najszybciej.

## Koszt

Zużycie E11: runda 1 5763 kredytów z logu (licznik konta +5789, różnica 26 bez przypisanego wywołania), runda 2 2956 (log i licznik zgodne). Projekt głosu kosztuje 1 kredyt na znak tekstu podglądu.

Koszt syntezy całej grupy głosów (znaki po normalizacji; cała gra, D02: 1,43 mln znaków w proporcjach M2):

| Grupa | Znaki M2 | Udział | v4 / v2 / v3: M2 | Flash: M2 | v4 / v2 / v3: cała gra | Flash: cała gra |
|---|---:|---:|---:|---:|---:|---:|
| narrator | 235 802 | 83,2% | 103 753 | 51 876 | ok. 524 tys. | ok. 262 tys. |
| bohaterowie z dubbingiem | 36 217 | 12,8% | 15 935 | 7 968 | ok. 80 tys. | ok. 40 tys. |
| złoczyńcy z dubbingiem | 221 | 0,1% | 97 | 49 | ok. 0,5 tys. | ok. 0,2 tys. |
| postacie bez dubbingu | 11 069 | 3,9% | 4 870 | 2 435 | ok. 24,6 tys. | ok. 12,3 tys. |

- Limit konta Creator to 127 047 kredytów na okres. Narrator całej gry w v4 to ok. 4 okresy limitu, a postacie bez dubbingu w M2 to ok. 4% jednego okresu.
- OmniVoice nie zużywa kredytów: M2 to ok. 16 h GPU, cała gra ok. 110 h (E7_AUDIO.md).
- Gra ma więcej postaci, które nie mają jeszcze głosu, więc koszt postaci bez dubbingu dla całej gry to dolny szacunek.

## Wnioski

- Głosy z dubbingu: OmniVoice dostał 4,56 za jakość i 4,22 za podobieństwo, bez kredytów. ElevenLabs nie był tu porównywany (D77).
- Postacie bez dubbingu: ElevenLabs wyraźnie lepszy (4,73 wobec 1,91 dla OmniVoice).
- Model ElevenLabs: v4 ma najwyższą średnią i jest najlepszy lub ex aequo u 10 z 11 postaci, przy tej samej cenie co Multilingual v2. Flash obniża koszt o połowę kosztem ocen.
- Warianty przy remisach i Adelynn (3 w v4, najniżej w rundzie 2) rozstrzygnęło QA.

## Decyzja (D80)

Dubbing (narrator, bohaterowie, złoczyńcy) zostaje w OmniVoice. Postacie bez dubbingu czyta ElevenLabs `eleven_v4` głosami z rundy 2, razem z Adelynn w wariancie b (`docs/CASTING.md`). Przegenerowanie ich fragmentów to etap E13.
