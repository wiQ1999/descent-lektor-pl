# Benchmark TTS: Chatterbox Multilingual na GTX 1650 Ti

Skrypt: `analysis/tools/tts_bench.py`. Wyniki są w `analysis/work/bench/results.json`, próbki WAV w `analysis/work/bench/<wariant>/`; nie ma ich w repozytorium.

```
.venv/Scripts/python -I analysis/tools/tts_bench.py
```

## Wynik w skrócie

- Na karcie 4 GB model działa z RTF ok. **2,1–2,5**, czyli minuta audio generuje się ok. 2,5 minuty. Warunek: po kondycjonowaniu trzeba zdjąć z GPU moduły potrzebne tylko do kondycjonowania. Bez tego fp32 wychodzi poza VRAM, a RTF rośnie do 12–15.
- W 80 próbkach (20 kwestii × 4 warianty) nie było OOM, ucięć na limicie tokenów, wymuszonych EOS ani powtórzeń. Średni WER według Whispera to 0,06–0,075, a CER ok. 0,02. Najgorsze wyniki dają krótkie dialogi z nazwami własnymi i jest to głównie kwestia zapisu nazw przez ASR.
- Warianty fp32/fp16 i cfg_weight 0,3/0,5 mają zbliżoną szybkość i dokładność. fp16 oszczędza ok. 1 GB VRAM.
- Szacowany czas generowania na tym GPU (jeden przebieg, bez poprawek):

  | Zakres | Czas |
  |---|---|
  | milestone 1 | ok. 3 h 10 min – 3 h 40 min |
  | zakres A | 25–30 h |
  | zakres C | 64–75 h |

## Konfiguracja

| | |
|---|---|
| GPU | NVIDIA GeForce GTX 1650 Ti, 4095 MiB, Windows 11 (sterownik z fallbackiem do pamięci współdzielonej) |
| Środowisko | Python 3.13, torch 2.6.0+cu124, chatterbox-tts 0.1.7 (`ChatterboxMultilingualTTS`, `language_id='pl'`) |
| Parametry | exaggeration 0,5, temperature 0,8, repetition_penalty 2,0, min_p 0,05, top_p 1,0, max_new_tokens 1000 (stała w bibliotece), seed 1234 + nr kwestii |
| Głosy | referencje z `analysis/work/voices/refs/` (`VOICES.md`): narrator 15,1 s, Syrus, Brynn; kondycjonowanie liczone raz i zapisane (`conds/<głos>.pt`) |
| Warianty | fp32 / fp16 (T3 w half precision; S3Gen i VoiceEncoder w fp32) × cfg_weight 0,5 / 0,3 |
| Ocena | Whisper large-v3-turbo (fp16, PL): WER, CER, powtórzone słowa, brak końcówki; podobieństwo głosu do referencji (VoiceEncoder) |

### Kwestie

20 kwestii z zakresu milestone 1 (`M1_SCOPE.md`), razem 3567 znaków. Placeholdery `{n}` zastąpiono przykładowymi imionami.

| Kategoria | Liczba | Głos | Długość |
|---|---|---|---|
| dialog | 8 (4 Syrus, 4 Brynn) | bohater | 30–220 znaków |
| narracja fabularna | 6 | narrator | 60–420 znaków |
| komunikat questu | 4 | narrator | 100–260 znaków |
| długi komunikat questu | 2 | narrator | ponad 400 znaków; dzielony na zdania (fragmenty do 260 znaków), sklejany z przerwą 0,25 s |

## Pamięć GPU

| Stan | VRAM |
|---|---|
| Po załadowaniu modelu (16,8 s) | 3074 MiB allocated (nvidia-smi 3155 MiB) |
| Po zdjęciu tokenizera S3, CAMPPlus i VoiceEncodera na CPU | 2557 MiB |
| Szczyt fp32, z offloadem | 3067–3107 MiB allocated |
| Szczyt fp16, z offloadem | 2016–2089 MiB allocated |
| Szczyt fp32, **domyślne zachowanie biblioteki** | 4050–4118 MiB allocated, czyli więcej niż fizyczny VRAM |

- Bez offloadu sterownik Windows przenosi część pamięci do RAM zamiast zgłosić OOM. Pierwsze dwie kwestie miały RTF 15,0 i 12,1, więc ten przebieg przerwałem.
- `offload_conditioning()` w skrypcie zdejmuje te moduły z GPU. Podmienia też `S3Gen.device`, bo biblioteka odczytuje urządzenie z tokenizera.
- Nawet z offloadem pamięć zarezerwowana przez alokator PyTorch dochodzi do 4144–4676 MiB, a nvidia-smi pokazuje 3,9 GB. Część cache alokatora może więc lądować w pamięci współdzielonej.
  - Przy długich przebiegach warto co jakiś czas wołać `torch.cuda.empty_cache()` i pilnować RTF.
  - Można też w panelu NVIDIA ustawić „CUDA – Sysmem Fallback Policy: Prefer No Sysmem Fallback”. Wtedy wyjście poza VRAM kończy się OOM zamiast cichym spowolnieniem. To ustawienie systemowe, decyzja należy do Ciebie.

## Szybkość

RTF to czas generowania podzielony przez długość audio. Czas generowania obejmuje T3, S3Gen i znak wodny, bez ładowania modelu i kondycjonowania.

| Wariant | RTF łącznie | RTF mediana / max | Znaki na s generowania | Audio | Udział T3 / S3Gen / znak wodny |
|---|---|---|---|---|---|
| fp32, cfg 0,5 | 2,47 | 2,46 / 2,99 | 5,3 | 272 s | 81% / 18% / 0% |
| fp32, cfg 0,3 | 2,08 | 2,17 / 2,37 | 6,0 | 285 s | 78% / 21% / 0% |
| fp16, cfg 0,5 | 2,16 | 2,16 / 2,46 | 6,2 | 267 s | 78% / 20% / 0% |
| fp16, cfg 0,3 | 2,23 | 2,20 / 2,55 | 5,7 | 280 s | 79% / 19% / 0% |

- Wąskim gardłem jest T3, autoregresyjny model języka generujący tokeny mowy (ok. 80% czasu). fp16 go nie przyspiesza, najpewniej dlatego, że przy batchu 2 (CFG) i małej karcie liczy się narzut na token, a nie przepustowość obliczeń.
- Różnice między wariantami (2,1–2,5) mieszczą się w rozrzucie losowania. Każdy wariant generuje trochę inną długość audio przy tym samym seedzie.
- RTF jest podobny we wszystkich kategoriach (dialog 2,2–2,4, narracja 2,1–2,2, komunikaty 2,0–2,6). Dzielenie długich komunikatów na zdania nie pogarsza szybkości.

## Błędy

| Wariant | OOM | Brak EOS | Wymuszone EOS | Ostrz. powtórzeń | WER śr. / mediana | CER śr. | Kwestie WER > 0,15 | Powtórzone słowa | Brak końcówki |
|---|---|---|---|---|---|---|---|---|---|
| fp32, cfg 0,5 | 0 | 0 | 0 | 0 | 0,067 / 0,049 | 0,020 | 2 | 0 | 1 |
| fp32, cfg 0,3 | 0 | 0 | 0 | 0 | 0,063 / 0,056 | 0,018 | 2 | 0 | 2 |
| fp16, cfg 0,5 | 0 | 0 | 0 | 0 | 0,075 / 0,052 | 0,021 | 3 | 0 | 1 |
| fp16, cfg 0,3 | 0 | 0 | 0 | 0 | 0,061 / 0,042 | 0,017 | 2 | 0 | 1 |

Kolumny:
- „Brak EOS”: fragment ucięty na 1000 tokenach.
- „Wymuszone EOS” i „Ostrz. powtórzeń”: ostrzeżenia `AlignmentStreamAnalyzer`.
- „Powtórzone słowa”: powtórzenia w transkrypcji, których nie ma w tekście.
- „Brak końcówki”: żadne z dwóch ostatnich słów tekstu nie występuje w ostatnich 6 słowach transkrypcji.

WER według kategorii:

| Wariant | dialog | narracja | komunikat | długi komunikat |
|---|---|---|---|---|
| fp32, cfg 0,5 | 0,126 | 0,018 | 0,038 | 0,041 |
| fp32, cfg 0,3 | 0,112 | 0,018 | 0,038 | 0,056 |
| fp16, cfg 0,5 | 0,143 | 0,027 | 0,022 | 0,051 |
| fp16, cfg 0,3 | 0,112 | 0,018 | 0,028 | 0,056 |

Jak czytać te liczby:
- Najgorsze dwie kwestie to krótkie dialogi Brynn (38 i 54 znaki, ok. 3 s audio). Mają WER 0,40 i 0,22 **identycznie we wszystkich 4 wariantach**. Porównanie transkrypcji z tekstem pokazało, że różnice to zapis nazw własnych przez Whispera: podwojone spółgłoski, inna pisownia imion i miejsc. Przy 6–9 słowach każda taka różnica podnosi WER o 0,1–0,2. Te same nazwy dają też „brak końcówki”, czyli fałszywy alarm.
- Błędy, które mogą pochodzić z syntezy, są pojedyncze. W jednym wariancie w transkrypcji krótkiego dialogu brakuje pierwszego słowa. W innym jedna krótka kwestia Syrusa ma WER 0,2 (nie sprawdzałem jej ręcznie). Narracja i komunikaty mają WER 0,02–0,06.
- Wniosek: przy produkcji wystarczy automatyczny filtr WER lub CER z wyjątkami dla nazw własnych (słownik nazw z gry) i ponowne generowanie z innym seedem dla odrzuconych kwestii. W tej próbce odpadłyby pojedyncze kwestie.

## Podobieństwo głosu

Średni kosinus embeddingu VoiceEncoder próbki do jej nagrania referencyjnego:

| Wariant | narrator | Syrus | Brynn | min |
|---|---|---|---|---|
| fp32, cfg 0,5 | 0,945 | 0,890 | 0,906 | 0,822 |
| fp32, cfg 0,3 | 0,943 | 0,907 | 0,913 | 0,867 |
| fp16, cfg 0,5 | 0,943 | 0,889 | 0,905 | 0,817 |
| fp16, cfg 0,3 | 0,943 | 0,907 | 0,915 | 0,867 |

- Punkt odniesienia z `VOICES.md`: oryginalne przerywniki narratora mają do centroidu narratora 0,98, a do najbliższego innego głosu (Galaden) 0,93–0,95.
- Klon narratora (0,94) leży więc między „ten sam lektor” a „podobny inny głos”. Barwa jest bliska, ale embedding odróżnia ją od oryginału.
- cfg 0,3 daje bohaterom trochę wyższe podobieństwo (+0,01–0,02) i mniej najsłabszych próbek.
- VoiceEncoder słabo rozróżnia męskie głosy (narrator ≈ Galaden 0,96). Te liczby nie zastąpią odsłuchu.

## Tempo mowy

- Synteza czyta 12,5–13,4 znaku na sekundę audio razem z pauzami (cfg 0,3: 12,5–12,7; cfg 0,5: 13,1–13,4).
- Oryginalny lektor czyta 9–10 znaków/s z pauzami i ok. 11,5 znaku/s czystej mowy (`VOICES.md`). **Synteza jest ok. 30% szybsza od lektora.**
- Według tempa syntezy milestone 1 to ok. 1 h 30 min audio. Według tempa lektora `M1_SCOPE.md` szacuje 1 h 40 min – 2 h 05 min.
- Chatterbox nie ma parametru tempa. Jeśli tempo ma być bliższe oryginałowi, są trzy opcje: niższe cfg_weight (trochę wolniej), dłuższe przerwy między zdaniami przy sklejaniu albo time-stretch w postprodukcji.

## Ekstrapolacja

Czas generowania liczony jako znaki podzielone przez znaki na sekundę generowania danego wariantu. Obejmuje jeden przebieg na GTX 1650 Ti, bez ponownych generacji i bez wariantów `{n}` dla każdego bohatera (w milestone 1 są 82 klucze z `{n}`).

| Zakres | Znaki | fp32, cfg 0,5 | fp32, cfg 0,3 | fp16, cfg 0,5 | fp16, cfg 0,3 | Audio (tempo syntezy) |
|---|---|---|---|---|---|---|
| milestone 1 | 70 512 | 3 h 41 min | 3 h 15 min | 3 h 10 min | 3 h 26 min | 1 h 30 min |
| milestone 1 bez CUTSCENE_01 | 69 857 | 3 h 39 min | 3 h 13 min | 3 h 08 min | 3 h 24 min | 1 h 29 min |
| A | 567 128 | 29 h 39 min | 26 h 07 min | 25 h 28 min | 27 h 34 min | 12 h 00 min |
| C | 1 430 154 | 74 h 45 min | 65 h 51 min | 64 h 14 min | 69 h 31 min | 30 h 16 min |

- Milestone 1 da się wygenerować w jeden wieczór.
- Zakres A to 1–1,5 doby pracy GPU, a C ok. 3 doby. Oba nadają się do przebiegu wsadowego z wznawianiem, zapisem po każdej kwestii i kontrolą RTF (wykrywanie spadku do pamięci współdzielonej).
- Do tego trzeba doliczyć ok. 10% na ponowne generacje i warianty `{n}`.

## Uwagi

- Wagi Chatterbox i Whispera (4,6 GB) leżą w `analysis/work/hf_cache`, które jest ignorowane w Git. Przy pierwszym utworzeniu tokenizera wielojęzycznego biblioteka pobiera też model segmentacji chińskiej `spacy_pkuseg` (91 MB) do `~/.pkuseg`, czyli poza repozytorium. Dla polskiego jest nieużywany.
- Każda próbka dostaje niesłyszalny znak wodny PerTh z biblioteki. Koszt czasu jest pomijalny; zostawiam go włączonego.
- Ograniczenia pomiaru:
  - jeden seed na kwestię i tylko 20 kwestii;
  - ASR nie mierzy prozodii, akcentu w nazwach ani emocji;
  - wybór wariantu wymaga odsłuchu próbek z `analysis/work/bench/`.
- Wstępna rekomendacja do potwierdzenia odsłuchem: **fp16, cfg_weight 0,3**. Ta sama jakość według ASR, o 1 GB mniej VRAM (zapas na karcie 4 GB), trochę wyższe podobieństwo bohaterów i wolniejsze, bliższe lektorowi tempo.
