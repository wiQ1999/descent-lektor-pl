# E9: test ElevenLabs na żywo

Test z 2026-11-07 (D74). Sprawdza serwer MCP, pomiar zużycia i własny wariant głosu na jednej kwestii. Ocena brzmienia czeka na odsłuch.

## Warunki

- Konto: plan Creator, limit 127 047 kredytów, reset 2026-11-15.
- Kwestia: losowa kwestia bohatera `TANGERINE_Q8_INTRO_REVISED_05G` (Kehli, 173 znaki, ziarno 585854).
- Model: `eleven_v4`. Język podajemy jako `pl`, ale serwer nie przekazuje go do API.
- Głos gotowy: `Bella`, premade z etykietą polską.
- Głos własny: `Lektor PL - Kehli test`. Opis powstał z portretu Kehli: młoda krasnoludka majsterkowiczka, psotny uśmiech.
- Z trzech podglądów wybrałem ten o F0 najbliższym dubbingowi i naturalnym tempie.

## Wyniki automatu

Barwa to podobieństwo do referencji z dubbingu Kehli. F0 referencji w tym samym pomiarze: 220 Hz. Tempo to stosunek do bazy automatu E3.

| Nagranie | CER | Ucięta końcówka | Barwa | Tempo | Najdłuższa pauza | F0 |
|---|---:|---|---:|---:|---:|---:|
| OmniVoice, wybrany głos Kehli | 0,006 | nie | 0,906 | 1,35 | 0,74 s | 186 Hz |
| ElevenLabs, Bella | 0,006 | nie | 0,743 | 1,42 | 0,52 s | 239 Hz |
| ElevenLabs, głos własny | 0,006 | nie | 0,707 | 1,34 | 0,58 s | 280 Hz |
| podgląd głosu B | 0,006 | nie | 0,713 | 1,37 | 0,86 s | 289 Hz |
| podgląd głosu C | 0,006 | nie | 0,721 | 1,57 | 0,51 s | 285 Hz |

- Wszystkie nagrania czytają tekst tak samo dokładnie.
- OmniVoice ma znacznie wyższe podobieństwo barwy, bo klonuje dubbing. ElevenLabs testowaliśmy bez klonowania.
- Głos własny jest wyraźnie wyższy od dubbingu Kehli, a Bella jest najbliżej pod względem F0.

## Koszt

| Wywołanie | Kredyty | Pomiar |
|---|---:|---|
| `text_to_speech`, Bella | 76 | historia |
| `text_to_voice`, 3 podglądy | 173 | licznik konta, odczyt po czasie |
| `create_voice_from_preview` | 0 | licznik konta |
| `text_to_speech`, głos własny | 76 | historia |
| **razem** | **325** | 0,26% limitu |

- `eleven_v4` kosztował 0,44 kredytu na znak, a podglądy głosu 1 kredyt na znak.
- Całe M2 to 283 309 znaków, czyli ok. 124 500 kredytów na jedno podejście bez powtórek. To 98% miesięcznego limitu planu Creator.
- Stawka pochodzi z dwóch wywołań tej samej kwestii.

## Co test zmienił w pomiarze

- Modele v3 i v4 mają w historii pusty `text` i `voice_id`. Tekst i głos są w polu `dialogue`, więc pierwsze wywołanie nie znalazło dopasowania.
- Licznik konta dogania wywołanie po około minucie. Pierwsza wersja hooka pokazała przez to fałszywe 0 kredytów.
- Po poprawce drugi TTS dał od razu 76 kredytów z historii, zgodnie z licznikiem konta.
- `text_to_voice` nie ma wpisu w historii. Hook zapisze go z flagą `unmeasured`, a koszt pojawi się w raporcie w wierszu „konto minus log”.
- Trzy rekordy z testu poprawiłem ręcznie, bo powstały przed poprawką: pierwszy TTS, `text_to_voice` i `create_voice_from_preview` (ten ostatni usunięty, narzędzie jest bezpłatne).

## Odsłuch

Próbki są w `analysis/work/elevenlabs/odsluch/` (poza repozytorium, 6 plików z referencją dubbingu).
