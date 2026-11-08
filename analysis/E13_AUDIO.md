# E13 · Postacie bez dubbingu w ElevenLabs

Pytanie etapu: jak przegenerować fragmenty 11 postaci bez dubbingu głosami z D80, żeby trafiły do paczki tak jak audio OmniVoice. Sposób ustala D81. Raport podaje klucze i liczby. Nagrania, oceny automatu i strona odsłuchu leżą w `analysis/work/audio/m1/` i `analysis/work/audio/m2/`.

## Metoda

- Komenda `python -I -m lektor eleven` (D81) woła API ElevenLabs bez MCP:
  - model `eleven_v4`, głosy z `direction.ELEVEN_VOICES`, ustawienia domyślne jak w ocenie E11;
  - wynik w PCM 24 kHz;
  - jedno podejście na fragment, ponowne (do 3) tylko przy uwagach automatu.
- Kolejność: pilot (po jednym fragmencie na postać), M1 (prolog i Q1), potem M2. M2 przejęło z M1 11 fragmentów o tym samym id.
- Automat E3 ocenia nagrania tak jak OmniVoice: CER z Whisper, ucięta końcówka (tekst i ogon nagrania), zgubiony fragment, barwa, tempo, pauzy. Barwę mierzy wobec nagrania v4 danej postaci z rundy 2 E11, a tempo wobec tempa v4 przy speed 1,0 (14,7 znaku na sekundę).
- `finalize` przycina ciszę i wyrównuje nagrania do -20 LUFS, jak przy OmniVoice. Manifest podaje model każdego fragmentu.

## Koszt

| Wydanie | Fragmenty ElevenLabs | Wywołania | w tym ponowne | Znaki | Kredyty |
|---|---:|---:|---:|---:|---:|
| M1 | 16 | 19 | 3 | 1 614 | 711 |
| M2 (bez 11 przejętych z M1) | 129 | 144 | 15 | 10 675 | 4 700 |
| **razem** | **145** | **163** | **18** | **12 289** | **5 411** |

- Koszt każdego wywołania pochodzi z historii konta (163 z 163 rekordów), średnio 0,44 kredytu na znak. Zgadza się to ze stawką z E9 i E11.
- Pilot: 11 wywołań, 303 kredyty. Ponowne podejścia: 371 kredytów, czyli 7% kosztu pierwszych podejść.
- Zatwierdzony szacunek E13 to ok. 4,9 tys. kredytów dla M2, z limitem +20% (ok. 5,9 tys.). M1 doszło w QA na starcie etapu, a całość zmieściła się w limicie.
- Wywołanie API trwa w medianie 1,4 s. Z odczytem kosztu z historii fragment zajmuje ok. 4 s, więc 120 fragmentów M2 trwało ok. 8 minut. Ocena automatem (Whisper na GPU) trwała dłużej, ok. 25 minut.
- Postacie bez dubbingu w całej grze to wg E11 ok. 24,6 tys. kredytów. Z ponownymi podejściami (+7%) wychodzi ok. 26 tys.

## Automat

| Postać (M2) | Fragmenty | Znaki | Podejścia | Kredyty* | CER ElevenLabs | CER OmniVoice | Barwa (mediana) | Tempo wobec v4 z E11 | Uwagi po ponownych |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| adelynn | 39 | 3 166 | 48 | 1 496 | 1,3% | 1,4% | 0,935 | 0,99 | 3 |
| astarra | 16 | 1 219 | 16 | 536 | 0,3% | 0,7% | 0,936 | 0,99 | 0 |
| herbie | 13 | 1 168 | 14 | 536 | 0,3% | 0,5% | 0,946 | 1,02 | 0 |
| outlaw | 12 | 1 045 | 15 | 640 | 0,4% | 0,5% | 0,964 | 1,02 | 0 |
| mok | 7 | 910 | 7 | 399 | 0,5% | 1,6% | 0,971 | 0,86 | 0 |
| galgoraz | 10 | 850 | 10 | 374 | 0,0% | 0,3% | 0,956 | 0,83 | 0 |
| bruli | 10 | 724 | 10 | 319 | 0,4% | 0,4% | 0,954 | 0,93 | 0 |
| ltrand | 10 | 541 | 11 | 258 | 1,8% | 3,0% | 0,919 | 0,93 | 0 |
| ronan | 9 | 535 | 9 | 237 | 0,4% | 0,7% | 0,936 | 0,87 | 0 |
| kathryn | 9 | 522 | 9 | 229 | 0,8% | 0,8% | 0,927 | 0,90 | 0 |
| flint | 5 | 389 | 6 | 186 | 0,2% | 0,2% | 0,948 | 0,95 | 0 |
| **razem** | **140** | **11 069** | **155** | **5 210** | **0,72%** | **1,01%** | | **0,94** | **3** |

\* Kredyty liczone z podejściami fragmentów przejętych z M1.

- **Pierwsze podejście w M2:** automat zgłosił 7 ze 140 fragmentów:
  - 3 końcówki (dwie u Adelynn, jedna u Banity);
  - 2 barwę (Adelynn, Flint);
  - 2 CER (Herbie, Porucznik Rand).
- **Po ponownych podejściach:** ponowne podejścia poprawiły 4 z nich. Zostały 3 fragmenty Adelynn. W M1 zgłoszony był 1 z 16 fragmentów i został po 3 ponownych podejściach.
- **Uwagi automatu przy OmniVoice:** w tych samych fragmentach OmniVoice miał po wyborze 4 uwagi w M2 i 1 w M1. CER OmniVoice w M1: 1,65%, ElevenLabs: 1,21%.
- **Tempo:** ElevenLabs czyta tak samo szybko jak OmniVoice w tych fragmentach (mediana 13,95 wobec 13,9 znaku na sekundę mowy; 13,2 wobec 13,4 minuty audio). Wobec tempa z próbek E11 to 0,94, w zakresie 0,50–1,17.

## Fragmenty z uwagą automatu (przejrzane bez odsłuchu)

| Fragment | Wydanie | Uwaga | Przegląd |
|---|---|---|---|
| `0a7d96cbdebe0a2e` | M1 | końcówka | 5 z 5 słów, ostatnie słowo Whisper zapisuje we wszystkich 6 podejściach (też OmniVoice) inaczej o 2 litery, ogon nagrania naturalny (poziom 0,03–0,05, cisza 0,14–0,32 s) |
| `8b1a67ba171072ba` | M2 | końcówka | ten sam wzorzec: 5 z 5 słów, różnica 2 liter w ostatnim słowie w 8 podejściach obu silników, ogon naturalny |
| `5719fb38f76812e0` | M2 | końcówka | jedno słowo (12 liter), które Whisper dzieli na dwa albo zapisuje inaczej; mowa 0,86 s, ogon naturalny (poziom ok. 0,02, cisza 0,16–0,29 s) |
| `46a3229ce94a3cb1` | M2 | barwa | CER 0, wszystkie słowa, ogon naturalny; barwa 0,85 we wszystkich 4 podejściach wobec mediany Adelynn 0,945; kwestia czytana wolniej (tempo 0,65) |

Wszystkie cztery to najpewniej fałszywe alarmy automatu: zapis nazwy przez Whisper albo inna intonacja jednej kwestii. Fragmenty zostają w manifeście z uwagą, a strona odsłuchu ich nie zawiera (zasada krótkiego odsłuchu).

## Odsłuch

Strona `analysis/work/audio/m2/listen/index.html` ma 30 losowych fragmentów ElevenLabs bez uwag automatu, z każdej z 11 postaci (`finalize --listen-engine elevenlabs`).

Wynik (użytkownik, 2026-11-08): 30 z 30 fragmentów „dobrze”, bez uwag. Oceny są w `listen/odsluch_e3.csv`, razem ze starszymi ocenami z E3.

## Wynik

- Manifest M1: 16 z 978 fragmentów z `eleven_v4` (Adelynn 12, Ronan 4), reszta bez zmian.
- Manifest M2: 140 z 3919 fragmentów z `eleven_v4`, wszystkie fragmenty 11 postaci bez dubbingu. Pozostałe fragmenty mają te same podejścia co przed E13.
- Próbkowanie 24 kHz bez zmian, więc companion i paczka działają bez zmian w kodzie. Paczki win i mac zbudowane od nowa.
- Automat nie znalazł prawdziwie uciętych końcówek. Cztery zgłoszenia opisuje tabela wyżej.
