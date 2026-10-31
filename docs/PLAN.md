# Plan etapów: lektor PL do Descent: Legends of the Dark

## Kontekst

Analizy są zamknięte (raporty w `analysis/`, commit 765145f), a rejestr decyzji jest w `docs/DECISIONS.md` (D01–D28 po rundach QA).

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
E1 test hooka ─────┘                                      ├─> E5 test Windows ─> E6 MacBook ─> E7 kolejne misje
E1 ──────────────────> E4 companion (z replayem logu E1) ─┘                                    E8 opcjonalnie
```

- Proponowany start to E1. Gdy Ty grasz, E0 może liczyć na GPU.
- Po każdym etapie robię commit, a decyzje trafiają do `DECISIONS.md`.
- W `analysis/` nie ma treści gry; audio, logi i próbki leżą w `analysis/work/` (ignorowane).

## E0 · Porządki i porównanie modeli TTS

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

**Zakres:** pakiet `src/lektor/` (pyproject w katalogu głównym, testy pytest w `tests/`):
- **ekstrakcja z kopii gry:** wykorzystuję logikę `extract_lines.py`, `m1_scope.py` i `speaker_gender.py`. Wynik to SQLite z kluczem, tekstem, kategorią, mówcą i głosem, kontekstem (graf, `seq`), argumentami i wariantami.
- **normalizacja:**
  - tagi;
  - glify PUA według mapy ikon;
  - liczby na słowa z odmianą według wzorców z gry;
  - słownik wymowy i nazw w formacie z decyzji u.
- **dzielenie:** długie kwestie na zdania; szablony `{n}` na fragmenty i inwentarz wartości: wrogowie z E1, bohaterowie, liczby (D16).
- **reguły z decyzji:**
  - okna wyboru: podział na cytat i opis (D20);
  - `VARIABLE_HERO` głosem narratora (D17);
  - przerywniki wykluczone (D14).
- **adnotacja emocji i tempa** dla M1 według słownika z E0 (D28). Przygotowuję ją ja, Ty przeglądasz próbkę.
- **klucz cache:** hash znormalizowanego tekstu + głos + styl + wersja modelu.
- **zakres:** policzenie zakresu „Welcome Home” (D15).

**Kryteria ukończenia:**
- baza M1 kompletna: `M1_SCOPE`, „Welcome Home” i wrogowie z E1;
- testy normalizacji, podziału i fragmentów przechodzą;
- raport liczności.

**Zależności:** E0 (model, nazwy, słownik emocji) i E1 (wrogowie, wartości `{n}`, format zdarzeń).

**Co wymaga Ciebie:** przegląd próbki adnotacji i listy nazw.

## E3 · Generowanie audio M1

**Cel:** komplet audio M1 po automatycznym QA.

**Zakres:**
- wsad z wznawianiem, ze stanem zapisywanym dla każdej kwestii;
- strażnik RTF i VRAM (D12);
- kilka podejść na kwestię i wybór najlepszego według CER i podobieństwa głosu;
- wykrywanie zgubionych fragmentów;
- normalizacja głośności według kategorii (D04);
- manifest i pliki w `analysis/work/audio/` (ignorowane);
- lista do odsłuchu: odrzucone kwestie + losowa próbka.

**Kryteria ukończenia:** co najmniej 98% kluczy M1 z zaakceptowanym audio; lista odsłuchu przejrzana, poprawki wygenerowane.

**Zależności:** E0 i E2.

**Co wymaga Ciebie:** odsłuch listy i decyzje o poprawkach. GPU zajmie ok. 3–4 h, zależnie od modelu z E0.

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
- tryb replay logu JSONL z E1, do testów bez gry.

**Kryteria ukończenia:** replay logu E1 daje audio dla co najmniej 98% okien, start poniżej 0,5 s i przerwanie poniżej 0,3 s według logu (D13); testy jednostkowe przechodzą.

**Zależności:** E1 i E2. Do pełnego testu potrzebne jest E3, ale pracę można zacząć wcześniej.

## E5 · Test na Windows

**Cel:** spełnić D13 w prawdziwej grze.

**Zakres:**
- instrukcja, Twoja sesja M1 z lektorem;
- raport pokrycia i opóźnień `analysis/E5_TEST.md`;
- poprawki i regeneracja przyrostowa.

**Kryteria ukończenia:** D13 spełnione.

**Zależności:** E3 i E4.

**Co wymaga Ciebie:** sesja gry i uwagi.

## E6 · MacBook Air M5

**Cel:** działanie przy stole.

**Zakres:**
- zgoda znajomego i lista kontrolna z `MAC_REPORT.md`;
- ryzyko arm64: paczka BepInEx 5 dla macOS standardowo działa pod Rosettą, a Doorstop 4.5+ ma natywny arm64.
  - Najpierw testuję Doorstop arm64 z BepInEx albo z naszym punktem wejścia.
  - Zapas: Rosetta, która działa do macOS 27.
- przepodpisanie ad-hoc oryginału, opcja uruchamiania w Steam i skrypt instalacji, cofania i ponownego nałożenia po aktualizacji (D25);
- Homebrew, Python i companion (D26);
- przeniesienie audio;
- pomiar generowania na żywo przez MLX lub MPS na M5;
- test przy stole.

**Kryteria ukończenia:**
- pełna sesja M1 bez interwencji;
- D13 spełnione na Macu;
- instrukcja odinstalowania sprawdzona.

**Zależności:** E5.

**Co wymaga Ciebie i znajomego:** dostęp do Maca, zgody (Zarządzanie aplikacjami, instalacja Homebrew), sesja przy stole.

## E7 · Kolejne misje przyrostowo

- SQ1 i kolejne misje;
- głosy NPC i docelowy głos systemowy (D22);
- wersje `VARIABLE_HERO` w głosach bohaterów (D17);
- złoczyńcy (D19);
- procedura po aktualizacji gry: porównanie manifestu, diff kluczy, regeneracja zmienionych.

Każda misja przechodzi cykl E2 → E3 → test.

## E8 · Opcjonalnie

- OCR jako zapas;
- przyciszanie muzyki przez Wwise (D23);
- UI ustawień.

## Weryfikacja

Każdy etap kończy się sprawdzeniem jego kryteriów ukończenia, wpisem decyzji do `DECISIONS.md` i commitem. Pliki z `analysis/work/` nie trafiają do repozytorium.
