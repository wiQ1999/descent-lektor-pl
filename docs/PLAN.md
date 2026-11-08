# Plan etapów: lektor PL do Descent: Legends of the Dark

## Kontekst

Analizy są zamknięte (raporty w `analysis/`, commit 765145f), a rejestr decyzji jest w `docs/DECISIONS.md` (D01–D28 po rundach QA, D29–D40 po E0 i E1, D41 w E2).

Odsłuch próbek Chatterboxa dał jakość „dostateczną”:
- angielskie nazwy są spolszczane;
- odczyt jest monotonny;
- fp32 brzmi lepiej od fp16.

Dlatego przed generowaniem audio jest nowy etap E0: porównanie modeli i reżyserii. Test hooka (E1) zostaje jako pierwsze duże ryzyko i może iść równolegle z E0.

**Status:** plan zaakceptowany 2026-10-31. Żaden etap nie startuje bez potwierdzenia użytkownika. Decyzje są w [DECISIONS.md](DECISIONS.md).

## Kolejność i zależności

```
E0 porównanie TTS ─┐
                   ├─> E2 pipeline danych ─> E3 audio M1 ─┐
E1 test hooka ─────┘                                      ├─> E5 test Windows ─> E6 instalacja Win + Mac ─> E7 kolejne misje
E1 ──────────────────> E4 companion (z replayem logu E1) ─┘                                    E8 opcjonalnie
```

- Proponowany start to E1. Gdy Ty grasz, E0 może liczyć na GPU.
- Po każdym etapie robię commit, a decyzje trafiają do `DECISIONS.md`.
- W `analysis/` nie ma treści gry; audio, logi i próbki leżą w `analysis/work/` (ignorowane).
- E10 (wydanie w GitHub Releases) poszło po E13, przed E12 (D82).
- E11 (arkusz porównawczy głosów) idzie teraz. Jego wynik ustala model dla dalszego audio. E12 (katalog treści gry) idzie po nim.
- E14 (reszta gry) idzie po E10. E12 zostaje na później.

## E0 · Porządki i porównanie modeli TTS

**Status:** zakończony 2026-11-01 ([analysis/BAKEOFF.md](../analysis/BAKEOFF.md)). Wybrany OmniVoice, 32 kroki (D33). Tempo, ekspresja, głos systemowy, nazwy i podejścia: D34–D38. Model dla całej gry: po E3 (D39).

**Cel:** wybrać model, ustawienia i sposób reżyserii przed generowaniem M1 oraz rozstrzygnąć otwarte kwestie a, b, c, e i u.

**Zakres:**
1. Porządki:
   - `analysis/REPORT.md`: cytaty zastępuję kluczami i opisem, poprawiam szacunki tempa (D24);
   - osobny Python projektu przez uv (D12) i przebudowa `.venv`; potem kontrola przez `tts_bench.py --asr-only`.
2. Zestaw testowy, ok. 12 fragmentów z M1:
   - dialogi z emocjami (Syrus, Brynn, Galaden, Vaerix) i okrzyk;
   - 2 narracje;
   - komunikat z liczbami i ikonami oraz komunikat z angielskimi nazwami (np. „Frostgate”);
   - głos systemowy (UI, walka);
   - wybrana opcja z cytatem (D20);
   - kwestia `{n}` sklejana z fragmentów (D16), do oceny szwów.
3. Wspólna dla wszystkich modeli normalizacja-prototyp: tagi, ikony na słowa, cyfry na słowa z odmianą.
4. Prototyp reżyserii (D28):
   - słownik emocji;
   - katalog fragmentów dubbingu dla każdej postaci z etykietą emocji, z którego biorę referencje emocjonalne;
   - adnotacja zestawu.
5. Kandydaci, każdy w osobnym środowisku `analysis/work/envs/<model>`, wagi w `hf_cache`:
   - Chatterbox v2 dostrojony: fp32, referencje emocjonalne, 3 podejścia na fragment i wybór przez ASR;
   - Chatterbox v3: kod z GitHuba, wagi `t3_mtl23ls_v3` i `s3gen_v3`;
   - XTTS-v2 (coqui-tts);
   - OmniVoice: najpierw sprawdzam polski i licencję wag; jeśli coś nie pasuje, odpada z notatką.
6. Warianty:
   - tempo: pauzy 0,35 i 0,5 s, time-stretch 0,9;
   - ekspresja;
   - nazwy: po polsku, fragment po angielsku wklejony albo zapis fonetyczny.
7. Pomiary: RTF i VRAM na GTX 1650 Ti, WER i CER (Whisper), podobieństwo głosu.
8. Wynik:
   - próbki z jawnymi nazwami: `analysis/work/bakeoff/<model>/…` + `INDEX.md` (D27);
   - arkusz ocen do wypełnienia;
   - raport `analysis/BAKEOFF.md` bez treści gry.

**Do wykorzystania** (bez pisania od nowa):
- z `analysis/tools/tts_bench.py`: `synth`, `offload_conditioning`, `load_conds`, `asr_check`, `speaker_similarity`, `split_sentences`, `spoken`;
- z `analysis/tools/style_samples.py`: `wsola`, `trim`, `pick`;
- `analysis/tools/extract_voices.py` + `work/voices/index.json` jako katalog nagrań dubbingu.

**Kryteria ukończenia:**
- każdy dostępny kandydat wygenerował cały zestaw;
- arkusz ocen jest wypełniony;
- QA rozstrzyga a, b, c, e i u;
- `BAKEOFF.md` i commit.

**Zależności:** brak.

**Co wymaga Ciebie:**
- ustawienie profilu NVIDIA dla nowego interpretera; ścieżkę podam po instalacji;
- odsłuch i oceny;
- runda QA.

## E1 · Test hooka na Windows (tylko logowanie)

**Status:** zakończony 2026-10-31 ([analysis/E1_HOOK.md](../analysis/E1_HOOK.md)). Okna pokryte w 100%. Kwestie x i y rozstrzygnięte (D31, D30), crash przy wyjściu (z) diagnozujemy w E4 (D40).

**Cel:**
- potwierdzić, że plugin widzi wszystkie okna;
- zebrać log realnie wyświetlanych kluczy, argumentów i wrogów;
- zrobić pierwszy pomiar pokrycia.

**Zakres:**
1. `src/plugin/Core`: rdzeń C# bez Harmony i bez zależności od BepInEx (D11):
   - subskrypcja `MessageController.MessageDisplayBegin` i `MessageDisplayEnd`;
   - polling `StoryMessageController.IsShowingMessage` i odczyt `_curProcessingMessage` przez refleksję, przez `PersistentGameObject.Instance`;
   - na zdarzenie zapisuje: typ okna, otwarcie i zamknięcie, klucz, argumenty (`MessageArgument.ResolveArgument`), wyrenderowany tekst, mówców z rozwiązanym `VARIABLE_HERO` (`StoryMessageCharacterSettings`), wybraną opcję (D20) i czas;
   - zapis do JSONL.
2. `src/plugin/BepInEx`: cienki adapter (`BaseUnityPlugin`) uruchamiający rdzeń.
   - Build przez dotnet SDK 8/10, który jest już zainstalowany.
   - Referencje do `Assembly-CSharp.dll` i UnityEngine biorę z kopii w `analysis/work/game`; DLL nie trafiają do repo.
3. Skrypty PowerShell do instalacji i odinstalowania:
   - BepInEx 5 x86 z oficjalnych wydań GitHub, z kontrolą SHA-256;
   - lista plików folderu gry przed i po, żeby potwierdzić, że odinstalowanie przywraca stan.
4. Instrukcja gry: prolog, Q1 i „Welcome Home”, w tym co kliknąć (np. różne opcje wyboru).
5. `analysis/tools/hook_coverage.py`: porównanie logu z `m1_scope.json` i `.qlog` (wykorzystuję `qlog_watch.py`). Raport `analysis/E1_HOOK.md` (bez tekstów):
   - pokrycie okien;
   - nieznane klucze i wrogowie;
   - wartości `{n}`;
   - zamknięcia okien;
   - opóźnienie odpytywania.

**Kryteria ukończenia:**
- co najmniej 98% okien zalogowanych z kluczem, tekstem i mówcą (cel 100%);
- zamknięcia są rejestrowane;
- brak crashy i spadków płynności;
- odinstalowanie przywraca folder gry.

**Zależności:** brak.

**Co wymaga Ciebie:**
- start (instalacja BepInEx w folderze gry według D11);
- przejście prologu, Q1 i „Welcome Home”;
- wskazanie logu.

## E2 · Pipeline danych w `src/`

**Cel:** gotowa baza kwestii M1 do generowania.

**Status:** zakończony 2026-11-01 ([analysis/E2_DATA.md](../analysis/E2_DATA.md)). Baza M1: 649 kluczy, 965 fragmentów, szacunek E3 ok. 39 h GPU. Raport liczności zaakceptowany. Głosy NPC ze sceny „Welcome Home” zaprojektowane od portretów (D41, [CASTING.md](CASTING.md)).

**Zakres:** pakiet `src/lektor/` (pyproject w katalogu głównym, testy pytest w `tests/`):
- **ekstrakcja z kopii gry:** wykorzystuję logikę `extract_lines.py`, `m1_scope.py` i `speaker_gender.py`. Wynik to SQLite z kluczem, tekstem, kategorią, mówcą i głosem, kontekstem (graf, `seq`), argumentami i wariantami.
- **normalizacja:**
  - tagi;
  - glify PUA według mapy ikon;
  - liczby na słowa z odmianą według wzorców z gry;
  - nazwy jak zapisane, słownik zapisów fonetycznych tylko dla wyjątków z E3 (D37).
- **dzielenie:** długie kwestie na zdania; szablony `{n}` na fragmenty i inwentarz wartości: wrogowie z E1, bohaterowie, liczby (D16).
- **reguły z decyzji:**
  - okna wyboru: podział na cytat i opis (D20);
  - `VARIABLE_HERO` głosem narratora (D17);
  - przerywniki wykluczone (D14).
- **kategoria i tempo** każdej kwestii według D34: narracja w scenach fabularnych w tempie naturalnym, reszta 1,2–1,4 według długości (D35 zastępuje adnotację emocji z D28).
- **referencje:** jedna neutralna na głos, cięta na granicach słów, z transkrypcją z tego samego wycinka (D33). NPC bez dubbingu: projekt głosu od portretu postaci (D41).
- **klucz cache:** hash znormalizowanego tekstu + głos + styl + wersja modelu.
- **zakres:** policzenie zakresu „Welcome Home” (D15).

**Kryteria ukończenia:**
- baza M1 kompletna: `M1_SCOPE`, „Welcome Home” i wrogowie z E1;
- testy normalizacji, podziału i fragmentów przechodzą;
- raport liczności.

**Zależności:** E0 (model, tempo, nazwy) i E1 (wrogowie, wartości `{n}`, format zdarzeń).

**Co wymaga Ciebie:** przegląd raportu liczności.

## E3 · Generowanie audio M1

**Cel:** komplet audio M1 po automatycznym QA.

**Zakres:**
- wsad z wznawianiem, ze stanem zapisywanym dla każdej kwestii;
- strażnik RTF i VRAM (D12);
- przyspieszenia OmniVoice bez zmiany brzmienia (krótsze referencje, gałąź bez warunku CFG bez dopełniania), sprawdzone na próbce przed wsadem;
- podejścia według D38: bohaterowie 3, reszta 1 i ponowne dla odrzuconych; wybór najlepszego według CER, uciętej końcówki, podobieństwa głosu i długości;
- wykrywanie zgubionych fragmentów;
- normalizacja głośności według kategorii (D04);
- manifest i pliki w `analysis/work/audio/` (ignorowane);
- lista do odsłuchu: kwestie odrzucone po ponownym podejściu + losowe 5% (D38).

**Kryteria ukończenia:**
- co najmniej 98% kluczy M1 z zaakceptowanym audio;
- lista odsłuchu przejrzana, poprawki wygenerowane;
- zmierzony czas generowania na znak, potrzebny do decyzji o całej grze (D39).

**Zależności:** E0 i E2.

**Co wymaga Ciebie:** odsłuch listy (ok. 10 min) i decyzje o poprawkach. GPU zajmie ok. 35–38 h (OmniVoice, D33), mniej po przyspieszeniach.

**Status:** zakończony 2026-11-02 ([analysis/E3_AUDIO.md](../analysis/E3_AUDIO.md)). Przyspieszenia: fp32, tokenizer na CPU, CFG bez dopełniania (D42), 7,6× szybciej. Wsad 5,0 h GPU (0,19 s na znak), 978 fragmentów, 98,4% kluczy przyjętych automatycznie. Odsłuch 61 fragmentów: ocena bardzo dobra, M1 bez poprawek; ucięte końcówki, wymowa i tempo Ne’Krul na kolejne generowania (D43). Cała gra ok. 93 h GPU (D39).

## E4 · Companion i integracja

**Cel:** lektor działający na Windows.

**Zakres:**
- plugin wysyła zdarzenia przez localhost (TCP, JSON lines);
- companion w `src/lektor/companion`:
  - wyszukiwanie po kluczu i hashu tekstu;
  - sklejanie `{n}` (D16);
  - kolejka i przerywanie (D03);
  - przełączniki kategorii (D21);
  - opcjonalny fallback na żywo;
  - log pokrycia i opóźnień;
  - plik konfiguracyjny;
- tryb replay logu JSONL z E1, do testów bez gry;
- obserwacja celu misji i aktywacji wroga (D30–D32);
- odpinanie subskrypcji przy wyjściu z gry i instrukcja dwóch krótkich testów wyjścia przed E5: sam BepInEx i plugin (D40).

**Kryteria ukończenia:** replay logu E1 daje audio dla co najmniej 98% okien, start poniżej 0,5 s i przerwanie poniżej 0,3 s według logu (D13); testy jednostkowe przechodzą.

**Zależności:** E1 i E2. Do pełnego testu potrzebne jest E3, ale pracę można zacząć wcześniej.

**Status:** zakończony 2026-11-02 ([analysis/E4_COMPANION.md](../analysis/E4_COMPANION.md)).
- Plugin 0.2.0 wysyła zdarzenia przez TCP oraz obserwuje cel misji i aktywację wroga.
- Companion odtwarza audio M1 przez sounddevice.
- Replay E1: audio w 98,5% okien z treścią (D50). Start 0,15 s, przerwanie 0,13 s (p95).
- Zasady odtwarzania: D48. Braki bazy M1 pominięte (D49). Łup od E7 składany z fragmentów (D51).

## E5 · Test na Windows

**Cel:** spełnić D13 w prawdziwej grze.

**Zakres:**
- instrukcja, Twoja sesja M1 z lektorem;
- raport pokrycia i opóźnień `analysis/E5_TEST.md`;
- poprawki i regeneracja przyrostowa.

**Kryteria ukończenia:** D13 spełnione.

**Zależności:** E3 i E4.

**Co wymaga Ciebie:** sesja gry i uwagi.

**Status:** rozpoczęty 2026-11-02. Najpierw testy wyjścia ([E4_EXIT_TEST.md](E4_EXIT_TEST.md), D40, D53, D54), potem sesja według [E5_PLAYTEST.md](E5_PLAYTEST.md).
- Test A (sam BepInEx, 0 pluginów): wyjście bez crasha.
- Test B: start companiona przerwał brak bazowego Pythona poza aplikacją Claude (naprawione w D52).
  - W powtórce plugin 0.2.0 połączył się z companionem i zapisał `stop`.
  - Przy wyjściu był crash w `mono_domain_free`, jak w E1.
  - A i B wskazywały na plugin, więc zawęziliśmy to testem C (plugin 0.2.1 z etapami).
- Test C: crash już na etapie 0, gdy plugin nic nie robi. Przyczyną jest błąd MonoMod #329 w BepInEx, nie kod pluginu (D54).
- Test D: `MonoMod.Utils.dll` z poprawką, plugin na etapie 4 z companionem (D54): bez crasha. `-Install` nakłada poprawkę domyślnie.
- Sesja M1 2026-11-02, ok. 30 min ([analysis/E5_TEST.md](../analysis/E5_TEST.md)):
  - start p95 0,128 s, przerwanie p95 0,126 s;
  - pokrycie 96,98%: braki to klucze pominięte w M1 (D49). Gdy łup wielokrotny liczymy jak w D50, wychodzi 99,6%;
  - wyjście bez crasha;
  - uwagi z gry trafiają do E7 (D55).
- **Zamknięty 2026-11-02** (D56).

## E6 · Instalacja na Windows i Macu

**Cel:** lektor instalowany dwuklikiem z jednego folderu na Windows i Macu, gra uruchamiana zwykłym przyciskiem w Steam, instrukcja dla użytkownika (D57).

**Zakres:**
- własny loader na Doorstop 4.6 na obu systemach, bez BepInEx, Harmony i MonoMod (D58);
- companion uruchamiany przez plugin i zamykany po wyjściu z gry; osobne pliki do wyłączania i odinstalowania (D59);
- paczka `Descent-Lektor-PL` dla każdego systemu:
  - Python 3.12 (python-build-standalone) z bibliotekami;
  - audio i baza M1;
  - pliki Zainstaluj, Odinstaluj, Wyłącz lektora, Włącz lektora, Ustawienia, Test dźwięku;
  - paczka jest kompletna i nie potrzebuje internetu przy instalacji (D60);
- Mac: przepodpisanie ad-hoc pliku gry z uprawnieniem do `DYLD_*` i opcja uruchamiania w Steam (D25);
- instrukcja `docs/INSTRUKCJA.md`, kopia w paczce;
- testy: W1 (loader na Windows), W2 (instalacja z paczki na Windows) i sesja M1 na Macu przy stole;
- raport `analysis/E6_INSTALL.md`.

**Kolejność prac** (plan zaakceptowany 2026-11-02):
1. Loader (`src/plugin/Loader`), autostart companiona (`Core/Launcher.cs`) i nowe opcje companiona: `--logs`, `--parent-pid`, zamknięcie po rozłączeniu, pojedyncza instancja, `--test`.
2. Test W1 na Windows: Doorstop z loaderem zamiast BepInEx, companion uruchamiany przez plugin.
3. Paczka Windows (`python -m lektor bundle --platform win`), skrypty i instrukcja; skrypty sprawdzone na udawanym folderze gry.
4. Test W2: instalacja z paczki według instrukcji, wyłączenie i odinstalowanie.
5. Paczka na Maca. Skrypty bash sprawdzam tu tylko składniowo.
6. Sesja na Macu przy stole. Folder `logs/` wraca do analizy.
7. Raport i commit.

**Ryzyka:**
- punkt wejścia przed startem Unity (czekanie na `UnityEngine.CoreModule` i `sceneLoaded`);
- zgoda „Zarządzanie aplikacjami” i podpis gry, który znika po aktualizacji;
- Doorstop arm64 z Mono Unity 2022.3;
- chronione foldery (TCC) i Gatekeeper.

**Kryteria ukończenia:**
- Windows: instalacja, wyłączenie i odinstalowanie z paczki według instrukcji, bez poleceń w terminalu. Po odinstalowaniu folder gry jest jak przed instalacją.
- Mac: pełna sesja M1 bez interwencji, D13 według dzienników, wyjście bez crasha, odinstalowanie sprawdzone.
- `INSTRUKCJA.md` przeszła oba systemy.

**Zależności:** E5.

**Stan (2026-11-04):**
- Kroki 1–3 zrobione. Test W1 przeszedł: loader i autostart działają, wyjście bez crasha (D58, D59).
- Paczka Windows: 363 MB (zip 316 MB), Python 3.12.15 z bibliotekami, 978 nagrań M1. Skrypty sprawdzone na udawanym folderze gry, także z rozpakowanego zipa.
- Test W2 przeszedł: instalacja z zipa według instrukcji, ustawienia, gra, wyłączenie i odinstalowanie (D59).
- Paczka Mac: zip 328 MB. Skrypty przeszły `bash -n` i przebieg na udawanym macOS (atrapy `codesign`, `arch`, `pbcopy`): instalacja, wykrycie gry, przepodpisanie, start z lektorem i bez, aktualizacja gry, odmowa zgody, odinstalowanie.
- Następny krok: sesja na Macu, odłożona (D61). Przy stole przejdzie razem z odbiorem E7, według instrukcji [E7_MAC_SESSION.md](E7_MAC_SESSION.md).

**Co wymaga Ciebie i znajomego:**
- testy W1 i W2 na Windows;
- dostęp do Maca i zgoda znajomego;
- zgoda „Zarządzanie aplikacjami” dla Terminala;
- sesja przy stole.

## E7 · Scenariusze dostępne w kampanii (Q6–Q8, wydarzenia, podróże, miasto)

Plan zaakceptowany 2026-11-04. Zakres wyznacza kampania znajomego w slocie 5 (D62). Decyzje: D61–D66. Wynik to kumulatywne wydanie M2 (M1 i E7 w jednej bazie), companion i plugin 0.4.0 oraz paczki na Windows i Maca.

**Zakres (nowy tekst, ok. 141 tys. znaków, ok. 10–11 h GPU):**
- scenariusze Q6, Q7, Q8 ze scenami wstępu, zakończeń i podróży oraz scena „Triage Pre Q678”;
- wydarzenia E5B, EC3, EC1;
- podróże aktu 1 i teksty miasta;
- wrogowie Q6–Q8 z pul losowania, pule łupu, liczniki celów, warianty `VARIABLE_HERO` (D17), opisy celów na mapie.

**Faza A: przygotowanie (z QA):**
- A1: zakres wydania w `scope.py`, baza M2, przejmowanie gotowych fragmentów z M1, inwentarz z węzłów łupu i testów (D49);
- A2: obsada, trzy rundy QA z próbkami:
  1. Astarra, Adelynn, Ronan, Kehli;
  2. Kathryn, Poruczniczka Rand, Mistrz Bruli, Xenith;
  3. Herbie, Szaman Mok, Książę Banita.

  Na końcu QA o odblokowaniach po Q6–Q8;
- A3: companion: licznik i guziki ogólne (D64), warianty bohatera, łup (D51), opis misji, nowe przełączniki;
- A4: plugin 0.4.0, opis misji z `DestinationDetails` (D55 pkt 5);
- A5: test cyklu na E5B na Windows (slot 5), instrukcja `docs/E7_E5B_TEST.md`.

Zakres po QA (D69): dochodzą E6A, E7A, E8A, E8B, EC2, EC4, SQ1A, E5A i scena przed Q9. Q9 i SQ2 zostają na kolejny etap.

Test E5B zaliczony 2026-11-05, poprawki w D70. Pełna baza M2: 2349 kluczy, 3919 fragmentów, 283 tys. znaków.

Blok B skończony 2026-11-06 (D71): 15,9 h GPU, replay dzienników E1, E5 i E5B z pokryciem 0,9983, paczki Windows i Mac z pluginem 0.4.1.

Uwagi z gry w D72. Paczka na Macu potwierdzona na pierwszej misji, E6 zamknięte. Sesja przy stole z kampanią zostaje otwarta (`docs/E7_MAC_SESSION.md`).

**Faza B: blok autonomiczny (bez QA):** pełna baza M2, generowanie z kontrolą uciętych końcówek, raporty `analysis/E7_DATA.md` i `analysis/E7_AUDIO.md`, replay bez regresji M1, paczki Windows i Mac, instrukcja `docs/E7_MAC_SESSION.md`.

**Faza C: odbiór:** gra ze znajomymi na Macu (D66). Sesja zamyka też E6 na Macu (D61).

**Później (bez zmian):**
- złoczyńcy przy ich misjach (D19);
- docelowy głos systemowy;
- procedura po aktualizacji gry: porównanie manifestu, diff kluczy, regeneracja zmienionych;
- kolejne scenariusze: ten sam cykl dla tego, co odblokuje kampania.

## E8 · Opcjonalnie

- OCR jako zapas;
- pomiar generowania na żywo przez MLX lub MPS na M5 (przeniesione z E6, D57);
- przyciszanie muzyki przez Wwise (D23);
- UI ustawień.

## E9 · Test głosów w ElevenLabs

Sprawdzamy jakość generowania w chmurze wobec OmniVoice (D73).

**Przygotowanie (gotowe):** serwer MCP w zakresie projektu, pomiar zużycia, raport `/zuzycie`. Instrukcja w `analysis/tools/elevenlabs/README.md`.

**Test na żywo (zrobiony 2026-11-07, D74, `analysis/E9_ELEVENLABS.md`):**
1. Bezpłatnie: `check_subscription`, `list_models`.
2. TTS na losowej kwestii bohatera.
3. Pomiar zużycia: rekord w logu, koszt zgodny z historią konta, procent zgodny z `check_subscription`.
4. Własny wariant głosu: `text_to_voice`, potem `create_voice_from_preview`.
5. Próbki do odsłuchu razem z głosem z OmniVoice.

Dalszy zakres etapu ustalamy po odsłuchu próbek.

## E10 · Wydanie w GitHub Releases

Publiczne wydanie gotowych paczek (D76).

**Status:** ukończony 2026-11-08 (D82). Repozytorium `wiQ1999/descent-lektor-pl` jest publiczne, a wydanie `v0.2.0` (pre-release) ma paczki M2 dla Windows i Maca.

**Zakres:**
- paczki Windows i Mac z kompletem plików jak dotąd: audio WAV, baza kwestii, plugin, loader, companion z Pythonem, skrypty i instrukcja;
- `LICENSE.md` w każdej paczce (pkt 3 licencji wymaga go w każdej kopii);
- sprawdzenie licencji modeli przy rozpowszechnianiu audio i uznanie autorstwa: OmniVoice (wagi CC-BY-NC) i tokenizer Higgs Audio 2 (notka o autorstwie);
- tag wersji i opis wydania: zakres scenariuszy i sumy SHA-256 paczek;
- publikację robi Claude przenośnym `gh` po zalogowaniu użytkownika (D82; pierwotnie: użytkownik).

## E11 · Arkusz porównawczy głosów

Pytanie etapu: którego modelu użyć (lokalny OmniVoice czy ElevenLabs przez MCP) i w jakim zakresie: narrator, bohaterowie z głosem z gry, reszta postaci (D77).

**Status:** ukończony 2026-11-07. Wynik w `analysis/E11_VOICES.md`, decyzja D80: dubbing w OmniVoice, postacie bez dubbingu w ElevenLabs `eleven_v4`.

**Zakres ustalony:**
- głosy z dubbingu (narrator, 6 bohaterów, Ne’Krul, Xenith): referencja z gry i OmniVoice na tych samych kwestiach, bez ElevenLabs;
- postacie bez dubbingu z audio M2 (11): OmniVoice wobec 3 wyraźnie różnych wariantów ElevenLabs;
- po 2 losowe kwestie na postać: jeden fragment, co najmniej 7 słów, do 220 znaków. Narrator ma jedną z narracji fabularnej i jedną z komunikatów questu, a Ne’Krul i Xenith mają w M2 po jednej kwestii;
- każda postać osobno, strony arkusza po 3–6 postaci, oceny z eksportem, wyniki automatu E3 i koszt całej gry na model;
- wywołania MCP według skilla `elevenlabs`, z podsumowaniem zużycia w każdej odpowiedzi.

**Runda 2 (D78, D79):** jeden głos na postać bez dubbingu, zapisany na koncie i przeczytany modelami `eleven_v4`, `eleven_multilingual_v2`, `eleven_flash_v2_5` i `eleven_v3`. Po ocenach raport `analysis/E11_VOICES.md` i decyzja o modelu dla każdej grupy.

**Kryteria ukończenia:** oceny obu rund, zmierzone stawki modeli, koszt całej gry na model i grupę głosów, decyzja w `DECISIONS.md`.

## E13 · Postacie bez dubbingu w ElevenLabs

Pytanie etapu: jak przegenerować fragmenty postaci bez dubbingu głosami z D80, żeby trafiły do paczki M2 tak jak audio OmniVoice.

**Status:** ukończony 2026-11-08. Odsłuch: 30 z 30 fragmentów bez uwag. D81: własna komenda `lektor eleven`, M1 i M2, jedno podejście i ponowne przy uwagach, pilot przed resztą. Wynik w `analysis/E13_AUDIO.md`: 156 fragmentów z `eleven_v4`, 5411 kredytów, paczki win i mac przebudowane.

**Zakres:**
- silnik głosu przypisany w `direction.py`: 11 postaci bez dubbingu → ElevenLabs `eleven_v4` z `voice_id` z `docs/CASTING.md`, reszta bez zmian;
- generowanie 140 fragmentów M2 i 16 fragmentów M1 tych postaci (11 fragmentów wspólnych, ok. 5,1 tys. kredytów, limit ok. 5,9 tys.) z zapisem kosztu w logu zużycia;
- te same kroki co E3: `evaluate`, `select`, do 3 ponownych podejść, `finalize` (PCM 24 kHz do WAV, -20 LUFS, manifest);
- strona odsłuchu do ok. 30 fragmentów, raport `analysis/E13_AUDIO.md`, paczki przebudowane.

**Do decyzji na starcie:** wywołania przez MCP (140 wywołań narzędzia w sesji) czy własny skrypt w `lektor` z kluczem z `.env.elevenlabs.local` (wznawialny, z tym samym logiem zużycia).

**Kryteria ukończenia:** wszystkie fragmenty tych postaci w manifestach M1 i M2 z ElevenLabs, automat bez uciętych końcówek, odsłuch, koszt w raporcie, commit.

## E14 · Reszta gry: postacie bez dubbingu, potem narrator i głosy z dubbingu

Pytanie etapu: jak nagrać całą resztę gry poza M2. Najpierw kwestie postaci bez dubbingu w ElevenLabs, potem lokalnie w OmniVoice narrator, bohaterowie i złoczyńcy. Szacunek: `analysis/E14_NO_DUB_SCOPE.md`. Decyzje z QA: D83.

**Status:** plan zaakceptowany 2026-11-08, z głosami OmniVoice nowych postaci w arkuszu. Trwa faza A.

**Faza A: przygotowanie**
- A1: baza całej gry `m3`: zakres wszystkich scenariuszy, wydarzeń, podróży i miasta aktów 1 i 2, łup i wrogowie aktu 2. Fragmenty o tym samym id przejmujemy z M2. Raport liczności jak `E7_DATA.md`.
  - Zrobione 2026-11-08: 12 622 klucze, 17 876 fragmentów (1,50 mln znaków), 95 grup; 3919 fragmentów M2 bez zmian, nowych 13 957 (1,22 mln znaków). Raport `analysis/E14_DATA.md`.
- A2: konto ElevenLabs: usunięcie testowego głosu Kehli po potwierdzeniu nazwy i id (12 → 11 z 30 miejsc).
- A3: obsada z Twoim udziałem:
  - 18 nowych postaci: portret z plików gry (`npc_voices.py portrait`), jeden opis głosu z portretu i kontekstu kwestii, jeden projekt `text_to_voice` czytający pierwszy losowy fragment, zapis głosu na koncie i drugi losowy fragment w `eleven_v4`;
  - te same 18 postaci w OmniVoice: projekt z portretu jak w D41 (`npc_voices.py`), te same 2 fragmenty, do decyzji o silniku;
  - 7 złoczyńców z okrzykami: klon OmniVoice z okrzyków (jak Ne’Krul i Xenith, D19), te same 2 losowe fragmenty;
  - arkusz porównawczy: portret, opis i 2 fragmenty każdej postaci, a obok dotychczasowe głosy (11 postaci ElevenLabs z E13 oraz Ne’Krul i Xenith w OmniVoice) z 2 fragmentami;
  - Twoja ocena: akceptacja, poprawka opisu albo zmiana silnika (ElevenLabs albo OmniVoice dla każdej postaci). Wynik w `docs/CASTING.md`.
  - Koszt obsady: ok. 5–6 tys. kredytów.
  - Arkusz gotowy 2026-11-08 (`analysis/tools/voice_compare_e14.py`, opisy w `voice_designs_e14.json`): 18 głosów „Lektor PL - <postać> E14” zapisanych na koncie (30 z 30 miejsc), próbki ok. 4,5 tys. kredytów, w tym ok. 0,9 tys. straty na podglądach bez katalogu wyjściowego. Złoczyńcy Zachareth, Reneyr i Levirax mają referencję z monologu, pozostali z okrzyków.
  - Runda 1 oceniona 2026-11-08 (D84): tylko ElevenLabs dla postaci bez dubbingu, 13 głosów i 5 złoczyńców przyjętych. Głos testowy Kehli usunięty (29 z 30 miejsc).
  - Runda 2 gotowa 2026-11-08 (`runda2.html`, oceny w `e14r2_oceny.json`): po 3 nowe podglądy dla Waiqara, Moranta, Delphyndry, Nary i Mezy (ok. 1,2 tys. kredytów), na arkuszu najlepszy z nich obok głosu z rundy 1; Levirax i Gilliam po 2 nowe warianty klonu.
  - Runda 2 oceniona 2026-11-08 (D87): przyjęci Waiqar i Morant (nowe głosy, stare usunięte) oraz Levirax `v2a` i Gilliam `v2b`.
  - Runda 3 gotowa 2026-11-08 (`runda3.html`, oceny w `e14r3_oceny.json`): Delphyndra, Nara i Meza po 3 różne opisy (ok. 2 tys. kredytów).
  - Runda 3 oceniona 2026-11-08 (D88): przyjęte Nara i Meza (nowe głosy, stare usunięte).
  - Runda 4 gotowa 2026-11-08 (`runda4.html`, oceny w `e14r4_oceny.json`): Delphyndra, 5 bardzo różnych opisów (ok. 1,2 tys. kredytów). Żaden nie pasował.
  - Runda 5 gotowa 2026-11-08 (`runda5.html`, oceny w `e14r5_oceny.json`, D89): Delphyndra, 5 opisów głosu głębokiego i chropawego, każdy też z lokalnym efektem smoka (ok. 1,2 tys. kredytów). Głosy nie przypominały smoka, część brzmiała jak męska.
  - Runda 6 gotowa 2026-11-08 (`runda6.html`, oceny w `e14r6_oceny.json`, D90): Delphyndra, 5 opisów z „wielką, krwiożerczą smoczycą” wprost i wyraźnie kobiecym głosem, bez efektu (ok. 1,2 tys. kredytów). Najciekawsza próbka C, ale wciąż nie to.
  - Runda 7 gotowa 2026-11-08 (`runda7.html`, oceny w `e14r7_oceny.json`, D91): Delphyndra jako mieszanka Leviraxa i próbki C, 4 proporcje klonu OmniVoice (bez kredytów). Uwaga po ocenie: głos wciąż nie pasuje.
  - Runda 8 gotowa 2026-11-08 (`runda8.html`, oceny w `e14r8_oceny.json`, D92): nowy profil Delphyndry z portretu (bestia), jeden opis ElevenLabs (3 podglądy, 243 kredyty) i trzy różne klony Leviraxa w OmniVoice. Wybrana próbka B (olbrzymka) do poprawek.
  - Runda 9 gotowa 2026-11-08 (`runda9.html`, oceny w `e14r9_oceny.json`, D93): pięć poprawek klonu B: bez robotycznego brzmienia, z kobiecym charakterem albo barwą dopasowaną do B. Wybrana próbka A: Delphyndra w OmniVoice (D94). Obsada A3 zamknięta.
- A4: komunikaty gry w kwestiach postaci czyta narrator, a tekst wielkimi literami nie znika (D85). Baza `m3` przebudowana: 126 kwestii zmienionych, 17 968 fragmentów.
- A5: wstawki sceniczne w kwestiach zebrane do E15 (D86, `analysis/E14_INSERTS.md`).

**Faza B: generowanie paczkami z postępem**
- B1: ElevenLabs: paczka na postać (11 głosów z E13 i 18 nowych, 101,6 tys. znaków, ok. 48 tys. kredytów z ponownymi). Po każdej paczce automat E3 i ponowne podejścia tej postaci. Limit `--max-credits`: zatwierdzony szacunek +20%.
- B2: OmniVoice: paczka na misję (scenariusz, wydarzenie, podróże, miasto, system), narrator, bohaterowie i złoczyńcy razem. Szacunek z bazy `m3`: ok. 105 h GPU bez ponownych podejść (narrator 830 tys. znaków, bohaterowie 255 tys. po 3 podejścia, D38).
- Komenda postępu: dla każdej paczki stan (gotowe, w toku, czeka), fragmenty i znaki zrobione i pozostałe, kredyty albo godziny GPU oraz przewidywany czas do końca z tempa dotychczasowych paczek.

**Faza C: odbiór**
- `select` i `finalize` dla `m3`, raporty `analysis/E14_DATA.md` i `analysis/E14_AUDIO.md`, odsłuch do ok. 30 fragmentów (osobno ElevenLabs i OmniVoice), paczki Windows i Mac, wydanie na GitHub po Twoim teście w grze.

**Kryteria ukończenia:** wszystkie kwestie aktów 1 i 2 w manifeście `m3`, automat bez uciętych końcówek, odsłuch, koszt w raporcie, commit.

## E15 · Wstawki sceniczne w kwestiach (po E14)

Pytanie etapu: jak czytać opisy zachowania postaci w nawiasach (D86). Skan `analysis/tools/inserts_scan.py` znalazł 264 wstawki w kwestiach postaci i 28 w kwestiach narratora (`analysis/E14_INSERTS.md`).
- Próbki obu wariantów: postać pomija wstawkę albo wstawkę czyta narrator przed kwestią. Wybór w QA po odsłuchu.
- Zmiana w `build` dla wybranego wariantu, przebudowa `m3`, ponowne generowanie zmienionych kwestii (ElevenLabs tylko u postaci bez dubbingu, reszta w OmniVoice).
- Plan etapu przedstawię przed startem.

## E12 · Katalog treści gry (później)

Uporządkowanie treści całej gry do nagrania: kategorie, mówcy, scenariusze, przedmioty i miejsce na poprawki, np. zapis fonetyczny. Sposób przechowywania dobieram sam (D77). Katalog leży w projekcie, w `analysis/work/`, poza Git (D76). Plan etapu przedstawię przed startem.

## Weryfikacja

Każdy etap kończy się sprawdzeniem jego kryteriów ukończenia, wpisem decyzji do `DECISIONS.md` i commitem. Pliki z `analysis/work/` nie trafiają do repozytorium.
