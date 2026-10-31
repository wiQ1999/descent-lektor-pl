# Decyzje

Rejestr decyzji projektu. Każda pozycja ma datę, decyzję i uzasadnienie. Pytania jeszcze nierozstrzygnięte są w sekcji „Otwarte kwestie” na końcu.
Plan etapów: [PLAN.md](PLAN.md).

## Podjęte

### D01 · 2026-10-31 · Sposób użycia
**Decyzja:** Gramy w 4 osoby przy stole, na MacBooku Air M5 32 GB znajomego, z monitorem ultrawide. Gra pochodzi ze Steam. Development i testy robimy na Windows 11.
**Uzasadnienie:** Tak wygląda docelowa sesja. Na Windows jest kopia gry, GPU do generowania i środowisko analiz.

### D02 · 2026-10-31 · Zakres lektora
**Decyzja:** Lektor PL czyta wszystko: dialogi, narrację, zdarzenia, eksplorację, komunikaty gry i walki.
**Uzasadnienie:** Przy stole nikt nie powinien musieć czytać ekranu na głos.

### D03 · 2026-10-31 · Wyzwalanie i przerywanie
**Decyzja:**
- Docelowo lektor startuje automatycznie. Na start dopuszczamy prostsze warianty.
- Kliknięcie „Kontynuuj” w trakcie czytania przerywa bieżącą kwestię i zaczyna nową.
- Akceptowalne opóźnienie od wyświetlenia okna do startu audio to do 2–3 s.

**Uzasadnienie:** Gracze często klikają dalej, zanim lektor skończy. Kilka sekund opóźnienia nie psuje rozgrywki.

### D04 · 2026-10-31 · Reżyseria
**Decyzja:** Emocje i tempo zależą od kategorii kwestii: spokojna narracja, szybsze i głośniejsze okrzyki w walce. Bez efektów dźwiękowych i bez muzyki.
**Uzasadnienie:** Styl ma się zgadzać z treścią. Efekty i muzykę gra ma własne.

### D05 · 2026-10-31 · Silnik i tryb generowania
**Decyzja:**
- Silnik TTS ma być lokalny i darmowy; chmura to tylko plan B.
- Najpierw generujemy na GTX 1650 Ti.
- Kolejne misje dokładamy przyrostowo, nie wszystkie naraz.

**Uzasadnienie:** Brak kosztów i pełna kontrola nad danymi. Benchmark pokazał, że GTX 1650 Ti wystarcza do generowania wsadowego (`analysis/BENCH.md`).

### D06 · 2026-10-31 · Głosy
**Decyzja:**
- Narratora i bohaterów klonujemy z polskiego dubbingu gry, wyłącznie do użytku prywatnego.
- Pozostali mówcy dostają gotowe głosy.
- Na start potrzebujemy minimum: narratora, bohaterów, głosu „inny” i głosu systemowego.

**Uzasadnienie:**
- Odsłuch próbek z benchmarku: głosy postaci brzmią bardzo dobrze.
- Klonujemy tylko głosy z dubbingu tej gry, na potrzeby prywatnej rozgrywki.
- Głosów innych osób nie klonujemy bez ich zgody.

### D07 · 2026-10-31 · Mac
**Decyzja:** Na Macu akceptujemy BepInEx albo inny loader, o ile działa. Bez maszyny wirtualnej.
**Uzasadnienie:** Gra działa natywnie na arm64 (`analysis/MAC_REPORT.md`), a VM byłaby zbyt ciężka dla MacBooka Air przy stole.

### D08 · 2026-10-31 · Implementacja
**Decyzja:** Kod piszemy sami, stos technologiczny jest dowolny.
**Uzasadnienie:** Prywatny projekt bez zewnętrznych ograniczeń.

### D09 · 2026-10-31 · Wzorce w `.gitignore`
**Decyzja:** Wzorce `build/`, `dist/` i `models/` są zakotwiczone do katalogu głównego (`/build/`, `/dist/`, `/models/`). Wagi modeli nadal wyklucza ignorowanie rozszerzeń (`*.safetensors`, `*.pt` itd.) i katalogu `hf_cache/`.
**Uzasadnienie:** Wcześniejsze wzorce ukrywały też katalogi z kodem, np. `src/<pakiet>/models/`, co sprawdziłem przez `git check-ignore`.

### D10 · 2026-10-31 · Odtwarzanie przez companiona (n)
**Decyzja:**
- Plugin w grze tylko wysyła zdarzenia przez localhost: typ okna, otwarcie i zamknięcie, klucz, argumenty, wyrenderowany tekst, mówców, rozwiązany slot `VARIABLE_HERO` i czas.
- Zewnętrzny proces companion (Python) odtwarza audio, przerywa je, obsługuje cache, sklejanie i fallback oraz loguje pokrycie.

**Uzasadnienie:**
- Unity Audio jest wyłączone w obu buildach, a wstrzykiwanie do Wwise byłoby bardzo złożone.
- Mały plugin jest wspólny dla Windows i Maca.

### D11 · 2026-10-31 · Loader na Windows (o)
**Decyzja:** Na Windows używamy BepInEx 5 x86. Dodaje on `winhttp.dll`, `doorstop_config.ini` i `BepInEx/` obok exe gry; istniejących plików gry nie zmieniamy. Rdzeń pluginu działa bez Harmony i bez zależności od BepInEx (delegaty + polling, `MAC_REPORT.md`). BepInEx jest tylko cienkim adapterem.
**Uzasadnienie:**
- Aktualizacja i weryfikacja plików w Steam nie usuwają tych plików, a odinstalowanie to usunięcie trzech pozycji.
- `RuntimeInitializeOnLoads.json` odpada, bo Steam go nadpisuje.

### D12 · 2026-10-31 · Osobny Python dla projektu (q)
**Decyzja:**
- Projekt dostaje własny interpreter, instalowany przez uv (jest już w systemie). Na nim przebudowujemy `.venv`.
- Dla tego interpretera ustawiasz w panelu NVIDIA „CUDA – Sysmem Fallback Policy: Prefer No Sysmem Fallback”.
- Wsad generowania i tak pilnuje RTF i VRAM.

**Uzasadnienie:**
- `.venv\Scripts\python.exe` to tylko launcher. CUDA działa w bazowym `Python313\python.exe` (sprawdzone przez `Win32_Process`), więc profil dla `.venv` nie działa, a profil dla bazowego Pythona objąłby inne projekty.
- Bez fallbacku przekroczenie VRAM kończy się błędem OOM zamiast cichego spowolnienia (RTF ok. 13).

### D13 · 2026-10-31 · Kryteria zaliczenia testu (r)
**Decyzja:**
- Co najmniej 98% okien M1 ma audio.
- Pregenerowana kwestia startuje poniżej 0,5 s od wyświetlenia okna.
- Przerwanie po „Kontynuuj” zajmuje poniżej 0,3 s.
- Fallback na żywo nie wlicza się do opóźnienia.

**Uzasadnienie:** Rzadkie braki są akceptowalne. Opóźnienie ma być niezauważalne, z zapasem względem limitu 2–3 s z D03.

### D14 · 2026-10-31 · Przerywniki z dubbingiem bez TTS (j)
**Decyzja:** Napisy wszystkich 20 przerywników (115 kluczy, w tym CUTSCENE_01) nie dostają TTS. Companion je ignoruje, ale loguje do raportu pokrycia jako „oryginalne audio”.
**Uzasadnienie:** 17 polskich nagrań gry pokrywa wszystkie przerywniki, więc lektor zagłuszałby dubbing.

### D15 · 2026-10-31 · Zakres milestone 1 (k)
**Decyzja:**
- M1 = prolog + Q1 + scena „Welcome Home” po Q1.
- Losowych wrogów ustalamy z logu sesji testowej E1.
- SQ1 robimy później.

**Uzasadnienie:** Pierwsza sesja przy stole nie powinna się urywać zaraz po Q1, a pełna lista wrogów wynika dopiero z gry.

### D16 · 2026-10-31 · Kwestie z `{n}`: sklejanie fragmentów (h)
**Decyzja:**
- Tekst wokół luk i wartości luk (nazwy wrogów, bohaterów, liczby, wstawiane teksty innych kluczy) generujemy jako osobne fragmenty.
- Companion skleja je w chwili odtwarzania.

**Uzasadnienie:**
- Zawsze działa natychmiast i bez eksplozji wariantów.
- Wybrane świadomie mimo słyszalnych szwów na łączeniach.

### D17 · 2026-10-31 · Sloty `VARIABLE_HERO` (i)
**Decyzja:** Na razie kwestie slotów `VARIABLE_HERO1–4` czytamy głosem narratora. Później dodamy wersje w głosie każdego bohatera, a plugin wybierze tę właściwą.
**Uzasadnienie:**
- W M1 takich kwestii nie ma (w całej grze jest ich 261).
- Gra podstawia bohatera N-tego gracza (`ActivePlayers[N]`), więc pełna obsługa wymaga wariantu na bohatera.

### D18 · 2026-10-31 · Narrator i Galaden (d)
**Decyzja:** Zostawiamy bez zmian.
**Uzasadnienie:**
- Referencja Galadena pochodzi z oryginalnych nagrań gry (`Galaden_QuestWon_1`, `Galaden_QuestSelect_2`, `Galaden_QuestLost_2`), a narratora z przerywnika `3_Wings Of War`.
- Podobieństwo 0,96 wynika z samego dubbingu, a nie z naszego wyboru.

### D19 · 2026-10-31 · Złoczyńcy (l)
**Decyzja:**
- Ne’Krula klonujemy już w M1.
- Pozostałych złoczyńców robimy przy ich misjach. Przy słabym klonie z krótkiej referencji (2,8–11,1 s) dostają gotowy głos o podobnym charakterze.

**Uzasadnienie:** W M1 mówi tylko Ne’Krul.

### D20 · 2026-10-31 · Okna wyboru (f)
**Decyzja:**
- Po otwarciu okna wyboru czytamy jego treść według kategorii, na start głosem systemowym. Samych opcji nie czytamy.
- Po kliknięciu czytamy wybraną odpowiedź:
  - część cytowaną (po myślniku lub w cudzysłowie) głosem bohatera, np. „Jestem wojowniczką” głosem Brynn;
  - opis (np. „deklaruje Brynn”) i opcje bez cytatu głosem narratora.

**Uzasadnienie:** Gracze widzą opcje na ekranie. Wybrana odpowiedź brzmi jak w słuchowisku, a przed wyborem nie ma długiego wyliczania.

### D21 · 2026-10-31 · Przełączniki kategorii (g)
**Decyzja:** Companion ma przełączniki kategorii: narracja, dialogi, komunikaty questu, walka i teren, UI i samouczek, okna wyboru, nagrody. Domyślnie wszystkie są włączone.
**Uzasadnienie:** Zgodnie z D02 lektor czyta wszystko, ale przy stole może się okazać, że część komunikatów męczy.

### D22 · 2026-10-31 · Gotowe głosy NPC (m)
**Decyzja:**
- Referencje bierzemy wyłącznie z nagrań z wyraźną zgodą lub licencją na syntezę (np. polskie zbiory mowy CC0/CC-BY, w których mówcy zgodzili się na takie użycie).
- Do tego mieszamy embeddingi kilku mówców w nowe, nieidentyfikowalne głosy.
- Konkretne głosy wybieramy odsłuchem przed E7. Dotyczy też docelowego głosu systemowego.

**Uzasadnienie:** Nie klonujemy głosów osób bez ich zgody. Mieszanie daje wiele różnych NPC z małej liczby źródeł.

### D23 · 2026-10-31 · Muzyka pod lektorem (p)
**Decyzja:**
- W M1 nie wyciszamy muzyki; ustawiacie jej głośność w opcjach gry.
- Później dodamy przyciszanie przez Wwise: plugin zmienia głośność szyny muzyki.

**Uzasadnienie:** Rozwiązanie w Wwise działa tak samo na Windows i Macu, ale nie jest potrzebne do pierwszego testu.

### D24 · 2026-10-31 · Porządki w `analysis/REPORT.md` (v, w)
**Decyzja:**
- Cytaty z gry zastępujemy kluczami i opisem.
- Szacunki długości audio poprawiamy według tempa z `VOICES.md` i `BENCH.md`: lektor 9–10 znaków/s z pauzami, synteza 12,5–13,4.

**Uzasadnienie:** Repozytorium ma być wolne od treści gry, a stare liczby zakładały 15 znaków/s.

### D25 · 2026-10-31 · Mac: oryginał + BepInEx (s)
**Decyzja:**
- Na Macu BepInEx (z Doorstop) instalujemy w oryginalnym pakiecie w folderze Steam.
- Plik wykonywalny przepodpisujemy lokalnie (ad-hoc, wbudowane `codesign`) z uprawnieniem do zmiennych `DYLD_*`.
- Gra startuje ze Steam z opcją uruchamiania `"…/run_bepinex.sh" %command%`.
- Skrypt instalacji i cofania uruchamiamy ponownie po każdej aktualizacji gry.
- Terminal potrzebuje zgody „Zarządzanie aplikacjami”.
- Wymagana jest zgoda właściciela Maca.

**Uzasadnienie:** Zwykły start ze Steam bez dodatkowej kopii 3 GB. Koszt: ponowne uruchomienie skryptu po aktualizacjach.

### D26 · 2026-10-31 · Mac: companion na Pythonie z Homebrew (t)
**Decyzja:**
- Na Macu znajomego instalujemy Homebrew i Pythona (`brew install python`), a companion działa we własnym środowisku w folderze projektu.
- Instrukcja instalacji i odinstalowania jest częścią E6.

**Uzasadnienie:** Standardowe narzędzia, łatwe aktualizacje zależności. Koszt: Homebrew, Command Line Tools i Python zostają w systemie znajomego.

### D27 · 2026-10-31 · Porównanie modeli TTS przed generowaniem
**Decyzja:**
- Przed generowaniem M1 robimy porównanie (bake-off) na tych samych fragmentach tekstu. Kandydaci:
  - Chatterbox v2 dostrojony (fp32, referencje emocjonalne, parametry do kwestii, kilka podejść i wybór przez ASR);
  - Chatterbox v3 (nowsze wagi `t3_mtl23ls_v3`, `s3gen_v3`);
  - XTTS-v2;
  - OmniVoice, po sprawdzeniu polskiego i licencji wag.
- Ocena jest jawna: pliki podpisane nazwą modelu, odsłuch obok siebie.

**Uzasadnienie:**
- Odsłuch próbek z benchmarku: jakość „dostateczna”.
- Problemy:
  - wspólne dla wariantów: angielskie nazwy (np. „Frostgate”) są spolszczane, a odczyt jest jednolity, bez zmian tempa i barwy w dialogach;
  - fp32 brzmi wstępnie lepiej od fp16.

### D28 · 2026-10-31 · Reżyseria: adnotacja kwestii + referencje emocjonalne
**Decyzja:**
- Każda kwestia dostaje adnotację emocji i tempa (np. spokojnie, napięcie, okrzyk, szept) na podstawie treści i kontekstu.
- Emocja wybiera fragment polskiego dubbingu jako referencję oraz parametry syntezy.
- Zatwierdzasz słownik emocji i odsłuchujesz próbki.

**Uzasadnienie:** Same parametry kategorii nie dają zmian tempa i barwy w obrębie dialogu.

### D29 · 2026-10-31 · XTTS-v2: akceptacja licencji CPML
**Decyzja:** Akceptujesz Coqui Public Model License dla wag XTTS-v2, więc XTTS bierze udział w porównaniu (D27).

**Uzasadnienie:** Projekt jest prywatny i niekomercyjny, a CPML dopuszcza taki użytek.

### D30 · 2026-10-31 · Aktywacje wrogów czytane głosem systemowym (y)
**Decyzja:**
- Lektor czyta tekst aktywacji wroga z `UIEnemyActivationDialog` (`ENEMY_ACTIVATION_*` i taktyki) głosem systemowym.
- Aktywacje mają osobny przełącznik kategorii (D21).
- Do zakresu M1 dochodzą aktywacje wrogów z losowania widzianych w E1: bandyty, fanatyka i fae.

**Uzasadnienie:** To instrukcja ruchu wroga, którą przy stole i tak ktoś czyta. Przełącznik pozwala wyłączyć ją, gdy się powtarza.

### D31 · 2026-10-31 · Cel misji czytany przy zmianie (x)
**Decyzja:**
- Lektor czyta nowy cel misji, gdy gra podmienia go w HUD.
- Czyta też zmiany samego licznika (np. 1/4 → 2/4).
- Głos systemowy, osobny przełącznik kategorii (D21).
- Źródło: `UIGame._lastObjectiveKey` i `_LastObjectiveArguments`.

**Uzasadnienie:** Cele są krótkie, a przy stole wszyscy od razu wiedzą, co dalej.

### D32 · 2026-10-31 · Nowe źródła tekstu w pluginie: E4, test w E5
**Decyzja:** Obserwację źródeł spoza okien wiadomości (aktywacja wroga, ewentualnie cel misji) dodajemy w E4 i sprawdzamy w sesji E5. Nie robimy dodatkowej sesji E1.

**Uzasadnienie:** Miejsca odczytu są znane z dekompilacji (`GameController` i `UIGame`), a osobna sesja tylko po to opóźniłaby E2.

## Ustalenia z analiz (fakty, na których opierają się decyzje)

- Unity Audio jest wyłączone w obu buildach (`globalgamemanagers` → `AudioManager.m_DisableAudio = true`). Dźwięk gra obsługuje przez Wwise.
- RTF na GTX 1650 Ti wynosi ok. 2,2 (`analysis/BENCH.md`), więc generowanie na żywo nie zmieści się w 2–3 s.
- Build macOS ma identyczne teksty, audio i klasy hooka jak Windows (`analysis/MAC_REPORT.md`).
- Milestone 1 nie potrzebuje głosów NPC (mówi tylko Ne’Krul), ale głos systemowy jest potrzebny od razu: 255 kluczy (`analysis/M1_SCOPE.md`).
- Argumenty `{n}` mają typy `RawText`, `VariableString`, `EntityName`, `VariableInt`, `ListOfKeys` (`MessageArgument`). Wartości to nazwy wrogów i bohaterów, liczby i teksty innych kluczy.
- Słoty `VARIABLE_HERO1–4` to bohaterowie kolejnych aktywnych graczy (`StoryCharacterModel.GetVariableCharacterIndex`, `ActivePlayers[N]`).
- Próbki stylu (`analysis/tools/style_samples.py`, `analysis/work/qa_samples/`) pokazały, czego wymaga normalizacja:
  - cyfry trzeba zamieniać na słowa z odmianą („na 1 karcie” → „na jednej karcie”);
  - ikony (glify PUA) na słowa;
  - każdy fragment trzeba kontrolować przez ASR, bo przy dzieleniu na zdania jedno zdanie potrafi zniknąć.
- Jest .NET SDK 8 i 10, a uv 0.11.11 jest już zainstalowany.
- E1 (`analysis/E1_HOOK.md`):
  - hook bez Harmony widzi 100% okien `MessageController` i `StoryMessageController`; tekst pluginu zgadza się z ekranem;
  - plugin nie może wołać getterów gry z leniwą inicjalizacją. Wywołanie `I2.Loc.LocalizationManager.CurrentLanguage` przed załadowaniem bundli powodowało crash Wwise przy starcie;
  - cel misji (HUD) i tekst aktywacji wroga (`UIEnemyActivationDialog`) gra pokazuje poza oknami wiadomości.

## Otwarte kwestie

Kwestie a–u rozstrzygamy w porównaniu modeli (D27), z po teście gry bez moda (x: D31, y: D30). W nawiasie podana jest wstępna rekomendacja.

| # | Kwestia | Stan |
|---|---|---|
| a | Model i wariant TTS (precyzja, cfg_weight) | po porównaniu; wstępnie fp32 brzmi lepiej od fp16 |
| b | Tempo: synteza jest ok. 30% szybsza od lektora | po porównaniu; próbki pauz i time-stretch w `analysis/work/qa_samples/tempo/` |
| c | Ekspresja według kategorii i emocji | po porównaniu, w ramach D28; próbki w `analysis/work/qa_samples/exag/` |
| e | Głos systemowy na start | po porównaniu (narrator w neutralnym stylu); docelowo gotowy głos według D22 |
| u | Nazwy własne i angielska wymowa (np. „Frostgate”) | po porównaniu: czy wydzielać nazwy z treści (fragment po angielsku, słownik albo zapis fonetyczny) |
| z | Crash przy wyjściu do pulpitu z loaderem (`mono_jit_cleanup`) | test gry bez moda (wyjście z menu do pulpitu) |
