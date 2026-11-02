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

**Co wymaga Ciebie i znajomego:**
- testy W1 i W2 na Windows;
- dostęp do Maca i zgoda znajomego;
- zgoda „Zarządzanie aplikacjami” dla Terminala;
- sesja przy stole.

## E7 · Kolejne misje przyrostowo

- przed startem: decyzja o modelu dla całej gry według czasu z E3 (D39);
- SQ1 i kolejne misje;
- nagrania wszystkich kwestii: inwentarz czyta też parametry węzłów łupu i testów (D49);
- łup składany z fragmentów: nagłówki i nazwy z puli łupu misji (D51);
- głosy pozostałych postaci projektowane od portretu (D41) po rozegraniu M1 z lektorem; docelowy głos systemowy;
- wersje `VARIABLE_HERO` w głosach bohaterów (D17);
- złoczyńcy (D19);
- uwagi z sesji E5 (D55):
  - odczyt aktualizacji celu z licznikiem (QA) i nagrania liczników;
  - łup i zdobyte przedmioty czytane przez narratora;
  - ujednolicona modulacja Kehli;
  - ponowny dobór głosów Ronana i Adelynn;
  - opis misji przy wyborze na mapie: hook w pluginie i nagrania;
- procedura po aktualizacji gry: porównanie manifestu, diff kluczy, regeneracja zmienionych.

Każda misja przechodzi cykl E2 → E3 → test.

## E8 · Opcjonalnie

- OCR jako zapas;
- pomiar generowania na żywo przez MLX lub MPS na M5 (przeniesione z E6, D57);
- przyciszanie muzyki przez Wwise (D23);
- UI ustawień.

## Weryfikacja

Każdy etap kończy się sprawdzeniem jego kryteriów ukończenia, wpisem decyzji do `DECISIONS.md` i commitem. Pliki z `analysis/work/` nie trafiają do repozytorium.
