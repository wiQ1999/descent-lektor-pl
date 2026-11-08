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

**Zmiana 2026-11-07:** ograniczenie do użytku prywatnego zastąpione przez D76 (publiczne wydania).

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

**Zmiana 2026-11-01:** zastąpione przez D41 (projekt głosu dla każdej postaci, bez zbiorów mowy).

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

**Zmiana 2026-11-01:** po porównaniu modeli zastąpione przez D35 (neutralna referencja, adnotacja tylko kategorii i tempa).

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

### D33 · 2026-11-01 · Model TTS: OmniVoice, 32 kroki (a)
**Decyzja:**
- M1 generujemy OmniVoice (`k2-fsa/OmniVoice`): fp16, 32 kroki, domyślne CFG 2,0. *Zmiana 2026-11-01: fp32 z przyspieszeniami (D42).*
- Akceptujesz licencje wag do prywatnego użytku: model CC-BY-NC, tokenizer audio Boson Higgs Audio 2 Community License. Wag ani wygenerowanego audio nie rozpowszechniamy.
- Referencje dla OmniVoice tniemy na granicach słów (do 10 s), a transkrypcja pochodzi z tego samego wycinka.

**Uzasadnienie:**
- Najlepsze oceny w obu rundach odsłuchu (`analysis/BAKEOFF.md`), CER bliski zera i najwyższe podobieństwo głosu.
- 16 kroków skraca czas o połowę, ale brzmi gorzej i ma więcej błędów.
- Koszt: na GTX 1650 Ti ok. 30 h na jedno podejście M1.

**Zmiana 2026-11-07:** zakaz rozpowszechniania wygenerowanego audio zastąpiony przez D76 (publiczne wydania). Wag nadal nie rozpowszechniamy.

### D34 · 2026-11-01 · Tempo czytania (b)
**Decyzja:**
- Narracja w scenach fabularnych (kategoria `narracja_fabularna`, np. intro i outro misji): tempo naturalne, przejęte z referencji, pauza między zdaniami 0,35 s.
- Dialogi bohaterów oraz narrator i system w trakcie rozgrywki: tempo bazowe 1,2, rosnące z długością kwestii do 1,4. Wstępnie: 1,2 do 80 znaków, potem liniowo do 1,4 przy 300 znakach. Progi korygujemy po odsłuchu E3.
- Pauza między zdaniami poza scenami fabularnymi: 0,25 s.
- Gdy automat wykryje uciętą końcówkę, ponowne podejście dostaje niższe tempo.

**Uzasadnienie:** Szybsze tempo brzmiało lepiej, zwłaszcza w długich tekstach. Najszybsze tempo psuło krótkie kwestie, a krótki okrzyk przy 1,2 urwał się na końcu. Mocny akcent i naturalne tempo pasują do narratora w scenach między rozgrywkami.

### D35 · 2026-11-01 · Ekspresja: neutralna referencja (c, zmienia D28)
**Decyzja:**
- Jedna neutralna referencja na głos i domyślne CFG 2,0. Emocję model bierze z tekstu.
- Adnotacja kwestii w E2 obejmuje tylko kategorię i tempo (D34). Referencji emocjonalnych w M1 nie używamy.

**Uzasadnienie:** Referencje emocjonalne nie poprawiły ocen w żadnym modelu, a niższe CFG obniżyło ocenę emocji. Mniej pracy w E2.

### D36 · 2026-11-01 · Głos systemowy na M1: narrator (e)
**Decyzja:** Głos systemowy to narrator z neutralną referencją i tempem według D34. Docelowy osobny głos wybieramy w E7 (D22).

**Uzasadnienie:** Komunikaty systemowe czytane narratorem dostały w odsłuchu 4/4/4 i 4/4/5.

### D37 · 2026-11-01 · Nazwy własne: jak zapisane, z wyjątkami (u)
**Decyzja:**
- Angielskie nazwy zostają w tekście tak, jak są zapisane.
- Zapis fonetyczny w słowniku dostają tylko nazwy, które w E3 wyjdą źle (ASR i lista odsłuchu).
- Nie wklejamy nazw generowanych po angielsku.

**Uzasadnienie:** OmniVoice czytał nazwy w zwykłym tekście dobrze. Wklejanie po angielsku wypadło źle we wszystkich modelach, a zapis fonetyczny dał błąd wymowy.

### D38 · 2026-11-01 · Podejścia i odsłuch w E3
**Decyzja:**
- Kwestie bohaterów: 3 podejścia. Pozostałe: 1 podejście i ponowne, gdy automat odrzuci wynik.
- Automat (ASR: CER i ucięta końcówka, podobieństwo głosu, długość) wybiera najlepsze podejście.
- Przed E5 odsłuchujesz kwestie odrzucone po ponownym podejściu i losowe 5% reszty (ok. 10 min).

**Uzasadnienie:** Kwestie bohaterów to 7% znaków M1, a automat nie wykrywa zmiany głosu w trakcie kwestii (F01 w rundzie 2). M1 to ok. 35–38 h pracy GPU.

### D39 · 2026-11-01 · Koszt całej gry: decyzja po E3
**Decyzja:** M1 generujemy OmniVoice. O modelu dla całej gry decydujemy po E3, przed E7, na podstawie czasu zmierzonego po przyspieszeniach i uwag z odsłuchu. Opcje to OmniVoice dla całej gry albo hybryda (np. szybszy model dla komunikatów, reguł i UI).

**Uzasadnienie:** Cała gra (D02, ok. 1,43 mln znaków) to na tej karcie ok. 610 h pracy GPU na jedno podejście, czyli ok. 25 dób. Przyspieszenia z E3 mogą to istotnie zmienić.

### D40 · 2026-11-01 · Crash przy wyjściu: diagnoza w E4 (z)
**Decyzja:**
- W E4 plugin dostaje odpinanie subskrypcji przy wyjściu z gry.
- Przed sesją E5 robisz dwa krótkie testy wyjścia (start, menu, wyjście): z samym BepInEx i z pluginem.

**Uzasadnienie:** Bez moda gra zamyka się czysto, więc przyczyną jest loader albo plugin. Crash występuje tylko przy wyjściu, a zapisy gry są kompletne, więc nie blokuje E2 i E3.

### D41 · 2026-11-01 · Głosy postaci NPC: projekt głosu
**Decyzja:**
- Każda postać w grze dostaje własny głos. Postacie bez głosu z dubbingu (D06) dostają głos zaprojektowany w OmniVoice, bez klonowania nagrań osób.
- Projekt zaczyna się od portretu postaci z plików gry (`d3/storymessagecharacters`, tekstura `*_Dialogue`) i opisu charakteru. Z nich wynika opis głosu (płeć, wiek, wysokość), własne zdanie referencji w stylu postaci (nie tekst gry) i tempo referencji.
- Do QA trafiają 4 kandydaci na postać, wybrani z większej puli tak, żeby różnili się barwą. Odpadają kandydaci z błędami ASR i z wysokością głosu spoza płci postaci.
- Wybrany kandydat zostaje stałą referencją postaci. Wybory zapisujemy w [CASTING.md](CASTING.md).
- W M1 projektujemy Adelynn i Ronana („Welcome Home”). Pozostałe postacie projektujemy po rozegraniu M1 z lektorem.
- Kwestie NPC mają tempo dialogów z D34, jak bohaterowie.
- Obsada M1 (runda 2): Adelynn: starsza kobieta, niski głos; Ronan: starszy mężczyzna, bardzo niski głos (szczegóły w CASTING.md).

**Uzasadnienie:**
- Projekt głosu nie wymaga pobierania danych ani zgody mówców, a każdą postać da się dopasować do wyglądu.
- Pierwsza runda bez portretu i z neutralnym tekstem dała głosy niepasujące do postaci.

### D42 · 2026-11-01 · OmniVoice w fp32 z przyspieszeniami (E3)
**Decyzja:**
- OmniVoice liczymy w fp32 zamiast fp16 (zmiana D33). Kroki i CFG bez zmian.
- Tokenizer audio po zakodowaniu referencji przenosimy na CPU, żeby model w fp32 mieścił się w 4 GB VRAM.
- Gałąź bez warunku (CFG) liczymy osobno, bez dopełniania do długości gałęzi z warunkiem (`lektor.synth`).
- Zmiana typu zmienia identyfikator modelu w kluczu cache: `omnivoice-08be0b4-fp32-s32-cfg2.0`.

**Uzasadnienie:**
- GTX 1650 Ti nie ma rdzeni tensorowych: mnożenie macierzy w fp16 osiąga 0,38 TFLOPS, w fp32 2,1 TFLOPS.
- Sam fp32 z tokenizerem na GPU spadał do pamięci systemowej (173 s na zdanie); po przeniesieniu tokenizera: 23 s; bez dopełniania: 17 s (tokeny identyczne w 100%).
- Próbka 11 fragmentów M1 (8 głosów, 19–230 znaków, te same ziarna): CER średnio 0,007 w obu ustawieniach, podobieństwo barwy 0,931 wobec 0,933, tempo identyczne. Czas 0,142 s na znak wobec 1,075 s (7,6× szybciej), szczyt VRAM 2,5 GB.
- Koszt wywołania: ok. 7,8 s stałe + 0,085 s na znak. M1 z podejściami bohaterów to ok. 5 h zamiast ok. 39 h.
- Odsłuch próbki w obu wersjach (2026-11-01): bez istotnej różnicy. Szybszy wariant obowiązuje też w kolejnych generowaniach.

### D43 · 2026-11-02 · Odsłuch E3: M1 bez poprawek, końcówki pod kontrolą w kolejnych generowaniach
**Decyzja:**
- Audio M1 przyjmujemy bez poprawek. Uwagi z odsłuchu zostają na kolejne generowania.
- W każdym kolejnym generowaniu pilnujemy uciętych końcówek wypowiedzi i je poprawiamy. Automat sprawdza też krótkie ostatnie słowo i urwanie mowy przy końcu pliku. Fragment z uciętą końcówką generujemy ponownie wolniej.
- Kandydaci do słownika wymowy (D37) przy następnym generowaniu:
  - imię Kehli czytane jako „Keli”;
  - wyraz z „rz” wymówiony z przeciągniętym „r”.
- Głos Ne’Krul (`nekrul`) w tempie dialogów brzmi za wolno. Tempo sprawdzamy przy następnym generowaniu jego kwestii.

**Uzasadnienie:**
- Ocena ogólna bardzo dobra: 54 z 61 fragmentów na liście bez uwag.
- Uwagi do 7 fragmentów:
  - 2 ucięte końcówki, obie w losowej próbce i niewykryte przez automat (zgubione końcowe „i” i urwane zakończenie);
  - 2 błędy wymowy;
  - 1 za wolne tempo;
  - 1 za słaba intonacja wykrzyknika;
  - 1 błąd w tekście gry, który głos przeczytał poprawnie.
- Imiona, które ASR zapisuje inaczej („Fuks”, „Vaerix”), brzmią dobrze.

### D44 · 2026-11-02 · Treść bez nagrania w E4: pominięcie i log
**Decyzja:**
- Companion pomija wartość luki albo kwestię bez nagrania i czyta resztę kwestii, a log zbiera braki. Dotyczy to np. łupu (`RawText`) i kluczy znanych dopiero w grze.
- Syntezę na żywo dodajemy po pomiarze na MacBooku M5 (E6).

**Uzasadnienie:** Na GTX 1650 Ti OmniVoice ma RTF ok. 2,4. Pięć sekund łupu to ok. 12 s czekania, czyli ponad limit 2–3 s z D03.

### D45 · 2026-11-02 · Kolejność: okno przerywa, cel i aktywacja czekają
**Decyzja:**
- Nowe okno przerywa audio poprzedniego okna (D03).
- Cel misji (D31) i aktywacja wroga (D30) czekają w kolejce, aż skończy się bieżąca kwestia.

**Uzasadnienie:** Cel i aktywacja zwykle pojawiają się razem z oknem questu i nie powinny go ucinać.

### D46 · 2026-11-02 · Start companiona: skrypt przed grą
**Decyzja:**
- W E4 i E5 companion uruchamiasz skryptem przed grą.
- Plugin sam łączy się z companionem i ponawia połączenie.
- Autostart przez plugin rozważamy w E6.

**Uzasadnienie:** Prostsze i bez uruchamiania zewnętrznego programu z gry, co nie miesza się z diagnozą crasha przy wyjściu (D40).

### D47 · 2026-11-02 · Odtwarzanie: sounddevice
**Decyzja:** Companion odtwarza audio przez pakiet `sounddevice` (PortAudio), zainstalowany tylko w środowisku projektu.
**Uzasadnienie:** Ta sama ścieżka na Windows i macOS. Pozwala zatrzymać dźwięk w kilkadziesiąt ms (D13: przerwanie poniżej 0,3 s).

### D48 · 2026-11-02 · Szczegóły odtwarzania w companionie (doprecyzowanie D03, D20, D45)
**Decyzja:**
- Odpowiedź bohatera po wyborze opcji (D20) gra do końca. Okno otwarte w jej trakcie czeka i gra od początku po niej.
- Kolejka (cel, aktywacja) rusza po 0,35 s bez zdarzeń okien. Zamknięcie okna i otwarcie następnego przychodzą razem, więc cel nie wcina się między okna.
- Cel lub aktywacja przerwane przez nowe okno wracają raz na początek kolejki.
- Zamknięta aktywacja wypada z kolejki. Nowszy cel zastępuje starszy.
- Cel odczytany w ciągu 30 s jako wartość luki w oknie (okno questu z kluczem celu w `{n}`) nie gra drugi raz.
- Okno z wyłączoną kategorią (D21) nie gra, ale zatrzymuje audio poprzedniego okna, bo tamto zniknęło z ekranu.
- Pokrycie liczymy dla okien z lektorem, bez przerywników z dubbingiem gry (D14). Okna złożone tylko z treści znanej dopiero w grze (łup) liczymy osobno (D44).

**Uzasadnienie:** Bez tego odpowiedź z wyboru byłaby od razu ucinana przez następne okno, a cel czytany dwa razy albo w pół okna. Te reguły nie zmieniają zakresu ani obsady, tylko doprecyzowują kolejność.

### D49 · 2026-11-02 · Braki bazy M1: pominięte; w kolejnych misjach nagrania wszystkich kwestii
**Decyzja:**
- W M1 companion pomija i loguje (D44) klucze, których nie ma w bazie E2:
  - `TRAVEL_57` i `DEFAULT_GET_TREASURE_MULTI` z sesji E1;
  - do 87 kluczy zakresu M1, które gra wstawia w węzłach łupu i testów.
- Od kolejnych scenariuszy (E7) baza obejmuje nagrania wszystkich kwestii. Inwentarz E2 czyta też parametry węzłów łupu i testów, a nie tylko przypisania w grafach (`SetStringKey`).

**Uzasadnienie:** M1 jest poziomem testowym. Inwentarz poprawiamy raz, przed kolejnymi misjami (E4_COMPANION.md).

### D50 · 2026-11-02 · Kryterium pokrycia E4 bez okien samego łupu
**Decyzja:** Do kryterium „audio dla ≥ 98% okien” nie wliczamy okien, których cała treść to lista łupu składana przez grę. Wynik E4: 332 z 337 okien (98,5%).
**Uzasadnienie:** Zgodnie z D44 companion w E4 nie czyta treści znanej dopiero w grze.

### D51 · 2026-11-02 · Łup składany z fragmentów
**Decyzja:**
- Listę łupu (`RawText`: nagłówek, potem nazwy przedmiotów albo kart z liczbami) companion czyta z pregenerowanych fragmentów: nagłówków i nazw z puli łupu misji.
- Listę rozpoznaje po tekście.
- Wprowadzamy to razem z pełnym inwentarzem (D49), w E7. Synteza na żywo zostaje zapasem po pomiarze na M5 (D44).

**Uzasadnienie:** Działa bez GPU przy stole i na Macu, a pula nazw w misji jest skończona.

### D52 · 2026-11-02 · Bazowy Python `.venv` w folderze projektu
**Decyzja:** Bazowy CPython 3.12.13 dla `.venv` (z uv, D12) leży w `analysis/work/python/` (ignorowane w Git). `home` w `.venv/pyvenv.cfg` wskazuje tę kopię. Skrypt `lektor-companion.ps1` sprawdza ją przed startem.
**Uzasadnienie:**
- Aplikacja Claude jest pakietem MSIX, więc Python zainstalowany z niej do `%LOCALAPPDATA%\LektorPL\python` trafił do prywatnego folderu pakietu.
- Poza aplikacją `.venv` go nie widział: w teście B wystąpił błąd „No Python at …”.
- Folder projektu na D: nie jest wirtualizowany.

### D53 · 2026-11-02 · Crash przy wyjściu: test C z etapami pluginu przed E5
**Decyzja:** Przed sesją E5 robimy test C ([E4_EXIT_TEST.md](E4_EXIT_TEST.md)): plugin 0.2.1 z `Diagnostics.Stage` od 0 do 3, do pierwszego crasha. Poprawka trafi do pluginu na sesję E5.
**Uzasadnienie:**
- Test A (sam BepInEx) przeszedł bez crasha, a test B (plugin 0.2.0) skończył się crashem w `mono_domain_free`.
- Przy stole na Macu okno crasha przy każdym wyjściu byłoby uciążliwe, a przyczyna może dotyczyć też Maca.

### D54 · 2026-11-02 · Crash przy wyjściu: poprawka MonoMod (test D)
**Decyzja:**
- Test D: `BepInEx\core\MonoMod.Utils.dll` zamieniamy na kopię bez zapisu flagi `corlib_internal`.
  - Kopię tworzy `monomod-fix.ps1`, a podmienia `lektor-hook.ps1 -MonoModFix`.
  - Plugin od razu na etapie 4, z companionem.
- Jeśli crash zniknie, `-Install` nakłada poprawkę domyślnie i sprawdza sumy SHA-256 (oryginału i kopii).
- Jeśli nie zniknie, akceptujemy crash przy wyjściu i przechodzimy do sesji E5.

**Uzasadnienie:**
- Test C: crash wystąpił już na etapie 0, gdy plugin jest wczytany, ale nic nie robi. Kod pluginu nie ma więc wpływu.
- MonoMod.Utils 22.1.29.1 z BepInEx 5.4.23.5 liczy położenie flagi w strukturze `MonoAssembly` bez pola `ignores_checks_assembly_names`, które ma Mono z Unity 2022.3.
  - Na x86 bajt trafia w ten wskaźnik (+0x4F zamiast +0x53).
  - Przy wyjściu `mono_domain_free` zwalnia uszkodzoną listę. To MonoMod #329, naprawione w MonoMod 25.
- HarmonyX robi ten zapis przy każdym patchu (proxy `ILGenerator`), a BepInEx patchuje `Assembly.LoadFile` także bez pluginów.
  - Nie wiemy na pewno, dlaczego test A przeszedł.
  - Zły wskaźnik ma stałą wartość 0x01000000, więc skutek jego zwolnienia zależy od tego, co leży pod tym adresem.
- Kopia różni się od oryginału jedną instrukcją: `stind.i1` zamieniam na dwa `pop`.
  - Flaga i tak nie trafiała w swoje pole, więc Harmony działa jak dotąd.
  - Porównanie wszystkich metod potwierdza, że zmieniła się tylko ta jedna.
- `HarmonyBackend = dynamicmethod` nic by nie zmienił. `mscorlib` gry ma `DynamicMethod.il_info`, więc MonoMod już domyślnie używa tego generatora.
- Ten sam wzór pomija pole także na x64, więc sprawdzimy to na Macu w E6.

**Wynik (2026-11-02):** test D bez crasha: plugin na etapie 4, połączenie z companionem, w `Crashes` brak nowego folderu. Od teraz `-Install` nakłada poprawkę domyślnie. Wyjście po 30-minutowej sesji E5 też było bez crasha.

### D55 · 2026-11-02 · Uwagi z sesji E5: M1 bez poprawek, zmiany w kolejnych scenariuszach
**Decyzja:** Audio i plugin M1 zostają bez zmian. Uwagi z sesji uwzględniamy w kolejnych generowanych scenariuszach (E7):
1. **Aktualizacje celu z licznikiem** (klucze do bramy X/4, mieszkańcy X/2; `Q1_OBJECTIVE_5`, `Q1_OBJECTIVE_6`) powtarzały się przy każdej zmianie licznika.
   - Licznik nie miał nagrania (luka `VariableInt` w celu), więc brzmiał sam tekst.
   - Sposób odczytu (za każdym razem, tylko licznik, tylko pierwszy raz) ustalimy w QA przed E7.
2. **Łup i zdobyte przedmioty** czyta narrator. To wykonanie D49 i D51 (nagrania wszystkich kwestii, łup z fragmentów).
3. **Kehli:** modulacja głosu zmienia się między kwestiami dialogów. Barwę i wysokość ujednolicamy przez referencję i wybór podejść.
4. **Ronan i Baronessa Adelynn:** głosy nie do końca pasują. Przed scenariuszem, w którym mówią, robimy ponowny dobór według D41.
5. **Opis misji przy wyborze na mapie** czyta narrator. To nowe źródło tekstu w pluginie: plugin go teraz nie widzi, a w dzienniku ze sceny mapy nie ma takich zdarzeń. Do tego nagrania opisów misji.

**Uzasadnienie:** Prośba użytkownika po sesji E5: nie poprawiać teraz, uwzględnić przy kolejnych scenariuszach.

### D56 · 2026-11-02 · E5 zamknięte
**Decyzja:** E5 uznajemy za zamknięte. Okna łupu wielokrotnego (`DEFAULT_GET_TREASURE_MULTI`) liczymy w kryterium tak jak łup pojedynczy w D50. Pokrycie wynosi wtedy 99,6%. Plugin zostaje zainstalowany w grze na Windows.
**Uzasadnienie:**
- Opóźnienia spełniają D13 z zapasem.
- Wszystkie braki to klucze, które M1 świadomie pomija (D49). Od E7 i tak je nagrywamy (D49, D51).

### D57 · 2026-11-02 · Zakres E6: instalacja na Windows i Macu z instrukcją
**Decyzja:**
- E6 przygotowuje instalację na Macu i na Windows. Ręczne uruchamianie skryptów zastępuje folder `Descent-Lektor-PL` z plikami do dwukliku.
- Instrukcja `docs/INSTRUKCJA.md` dla użytkownika (kopia w paczce) opisuje instalację, ustawienia, uruchamianie, wyłączanie i odinstalowanie.
- Pomiar syntezy na żywo na M5 (MLX/MPS) przenosimy do E8.

**Uzasadnienie:**
- Prośba użytkownika.
- Nazwa folderu ma mówić, do jakiej gry jest dodatek.
- Lektor używa pregenerowanego audio, a pomiar wymagałby na Macu znajomego dużych bibliotek.

### D58 · 2026-11-02 · Loader: Doorstop i własny punkt wejścia (zmienia D11 i D25 w części loadera)
**Decyzja:**
- Na obu systemach Doorstop 4.6 wczytuje nasz `LektorPL.Loader.dll` z folderu paczki, bez BepInEx, Harmony i MonoMod.
- Loader czeka, aż gra wczyta `UnityEngine.CoreModule`, a przy pierwszej scenie uruchamia Core.
- BepInEx z poprawką D54 zostaje w repozytorium jako zapas deweloperski.

**Uzasadnienie:**
- Doorstop od 4.5 działa natywnie na arm64.
- BepInEx 5 (MonoMod 22) na Macu ruszyłby tylko pod Rosettą, która znika po macOS 27.
- Na Windows znika poprawiony plik MonoMod. W folderze gry zostają 3 pliki Doorstop.
- Rdzeń od początku nie zależy od loadera (D11).

**Wynik testu W1 (2026-11-04, Windows):**
- Loader wykrył `UnityEngine.CoreModule` przez `AssemblyLoad`, a rdzeń wystartował na pierwszej scenie (`Splash`), ok. 11 s po starcie Doorstop.
- Gra startowała i działała normalnie. Wyjście było bez crasha, bez BepInEx i bez poprawki D54.

### D59 · 2026-11-02 · Companion uruchamia plugin (zmienia D46)
**Decyzja:**
- Gdy port companiona jest wolny, plugin uruchamia go w tle z Pythona w paczce.
- Companion kończy się po zamknięciu gry (sprawdza proces gry i rozłączenie).
- Pliki „Wyłącz lektora” i „Włącz lektora” wyłączają cały dodatek bez odinstalowania. „Odinstaluj” usuwa pliki z folderu gry.

**Uzasadnienie:**
- Gra startuje zwykłym przyciskiem w Steam.
- Powód D46, czyli diagnoza crasha przy wyjściu, odpadł (D54).
- Użytkownik chce łatwego wyłączenia i odinstalowania.

**Wynik testu W1 (2026-11-04, Windows):**
- Plugin uruchomił companion (0,44 s na wątku gry, w czasie ekranu startowego), a połączenie było po 0,56 s.
- Lektor czytał od pierwszego okna: 17 okien, pokrycie 100%, start p95 0,17 s, przerwanie p95 0,13 s.
- Companion skończył się 1,1 s po wyjściu z gry (powód `gra_zamknieta`).

**Wynik testu W2 (2026-11-04, Windows, paczka z zipa na Pulpicie, według `INSTRUKCJA.md`):**
- Każdy krok zadziałał, a instrukcja była jasna.
- W obu sesjach z lektorem plugin uruchomił companion, a ten zamknął się ok. 1 s po wyjściu z gry. Wszystkie okna miały audio, start p95 0,13 s.
- Sesja po „Wyłącz lektora” nie zostawiła dziennika loadera: Doorstop nie wczytał dodatku.
- Po „Odinstaluj” folder gry był jak przed instalacją.

### D60 · 2026-11-02 · Python w folderze paczki, paczka kompletna (zmienia D26)
**Decyzja:**
- Companion działa na Pythonie 3.12 z python-build-standalone, czyli tych samych buildach, które instaluje uv. Python leży w folderze paczki razem z `numpy`, `sounddevice` i `soundfile`.
- Biblioteki instaluję przy budowie paczki, a pobrania mają przypięte sumy SHA-256.
- Instalacja nie potrzebuje internetu, hasła administratora, Homebrew ani Command Line Tools.
- Na Macu nie instaluję samego uv, bo paczka ma gotowe środowisko.

**Uzasadnienie:**
- Użytkownik wybrał opcję „wszystko w folderze” i paczkę kompletną.
- Na Macu znajomego nic nie zostaje poza folderem: odinstalowanie to usunięcie folderu.
- uv byłby tylko pośrednikiem, który pobiera ten sam Python.

### D61 · 2026-11-04 · Sesja na Macu później, E7 startuje wcześniej
**Decyzja:**
- Sesja E6 na Macu odbędzie się później. Do tego czasu E6 zostaje otwarte tylko w tym kroku: paczka Mac jest gotowa i sprawdzona na atrapach.
- E7 zaczynamy bez czekania na sesję na Macu.

**Uzasadnienie:** Użytkownik nie ma teraz dostępu do Maca.

### D62 · 2026-11-04 · Kampania znajomego w slocie 5, z niej zakres E7
**Decyzja:**
- Zapisy znajomego z Maca (jeden slot, 23,3 h, wersja gry 2.0.10) skopiowałem do nowego slotu `SavedGames\5` w folderze gry. Sloty 1–4 zostały bez zmian. Kopia robocza leży w `analysis/work/saves/mac-friend`.
- Zakres E7 wyznacza ta kampania. Stan odczytuje `analysis/tools/campaign_state.py` (identyfikatory na konsolę, tytuły PL w `analysis/work/out/campaign_state.md`).
  - Rozegrane: Q1, Q3, Q4 (`STORY_QUEST_4_S`), Q2, Q5, SQ1 oraz wydarzenia E3B, E4B, E4A i miejskie `CITY_EVENT_0`, `CITY_EVENT_4`, `CITY_EVENT_1`.
  - Dostępne na mapie: scenariusze Q6, Q7, Q8 i wydarzenia E5B, EC3, EC1.

**Uzasadnienie:**
- Zapis to JSON. Gra wybiera najnowszy plik po nazwie i nie sprawdza wersji ani platformy przy wczytaniu (`SaveLoadController`).
  - Pole `AssetBundleVersion` różni się między Makiem (3) i Windows (2), ale gra go nie porównuje.
  - Nowy slot niczego nie nadpisuje. Wycofanie to usunięcie folderu `5`.
- Synchronizacja z chmurą Asmodee działa tylko po zalogowaniu i rozpoznaje sloty po `SlotGUID`, więc slot znajomego nie koliduje z Twoimi.
- Użytkownik chce nagrywać to, co grupa może teraz wybrać, a nie kolejny scenariusz po Q1.

### D63 · 2026-11-04 · Zakres i kolejność E7
**Decyzja:** E7 obejmuje wszystko, co jest dostępne na mapie (D62), z uwagami z E5 (D55). Kolejność:
1. Przygotowanie:
   - postacie poboczne z Q6–Q8 i wydarzeń oraz ich głosy (D41, QA z próbkami);
   - ponowny dobór Ronana i Adelynn oraz ujednolicenie Kehli (D55);
   - pozostałe czynności przygotowawcze.
2. Test: pierwsze wydarzenie poboczne w całym cyklu (baza, audio, plugin, gra).
3. Jeden duży blok autonomiczny: pozostałe scenariusze i wydarzenia oraz zaktualizowane paczki instalacyjne na Windows i Maca.

**Uzasadnienie:** Wybór użytkownika w QA. Test na jednym wydarzeniu sprawdza cały cykl na małym zakresie, zanim ruszy duży blok.

### D64 · 2026-11-04 · Odczyt celu z licznikiem i guzików ogólnych
**Decyzja:**
- Cel z licznikiem (D55 pkt 1): pierwszy raz lektor czyta cały tekst celu, a przy kolejnych zmianach sam licznik (np. „dwa z czterech”). Potrzebne są nagrania liczebników.
- Okna z wyborem: lektor czyta wybrany guzik (D20), ale pomija guziki ogólne typu „Kontynuuj”. Przykładem jest pytanie o koniec rundy mroku (ruch wrogów). Treść okna czyta jak zawsze.

**Uzasadnienie:** Wybór użytkownika w QA i uwaga z gry. Powtarzany cały cel i odczyt „Kontynuuj” nic nie wnoszą.

### D65 · 2026-11-04 · Model w E7: OmniVoice (część D39)
**Decyzja:** Scenariusze E7 generujemy OmniVoice, jak M1. O modelu dla całej gry (D39) decydujemy przy większym zakresie.

**Uzasadnienie:**
- Nowy tekst Q6–Q8 to ok. 89 tys. znaków, tyle co M1 (ok. 6–7 h GPU przy 0,235 s na znak z E3).
- Głosy i jakość zostają takie jak w M1.

### D66 · 2026-11-04 · E7: podróże i miasto w zakresie, test na E5B, odbiór na Macu
**Decyzja:**
- Zakres E7 (D63) obejmuje też wydarzenia podróży aktu 1 (ok. 32 tys. znaków, narrator) i teksty budynków w mieście (ok. 9 tys. znaków). Razem E7 to ok. 140 tys. znaków, czyli ok. 9–10 h GPU.
- Test cyklu: wydarzenie E5B „Cena wiedzy” (Astarra i Syrus). Grasz je sam na Windows ze slotu 5.
- Odbiór dużego bloku to gra ze znajomymi na Macu. Paczka Windows też musi być kompletna, ale bez osobnego testu odbioru.

**Uzasadnienie:**
- Podróże i miasto wypadają przy każdym wyjściu na Q6–Q8. Bez nich lektor milczałby w części gry.
- E5B jest najkrótsze i sprawdza jednocześnie nowy głos NPC i głos bohatera z dubbingu.
- Wybór użytkownika w QA.

### D67 · 2026-11-04 · E7: obsada, runda 1
**Decyzja:**
- Astarra dostaje głos kandydata `adelynn_d3_s5` (projekt: starsza kobieta, średnia wysokość).
- Adelynn zostaje przy obecnym głosie, więc jej kwestie z M1 nie powstają od nowa.
- Kehli dostaje referencję `kehli_srodek`. Jej kwestie z M1 powstaną od nowa.
- Ronan: żaden kandydat nie przeszedł. Ma być niski i urywany, z chrypą jak u wikinga, więc powstają nowe warianty (runda 1b).
- W każdym zestawieniu kandydatów strona odsłuchu pokazuje też głosy już wybrane.

**Uzasadnienie:** Wybór z odsłuchu. Liczby (F0, rozrzut) były tylko podpowiedzią. Sekcja z wybranymi głosami pozwala sprawdzić, czy rodzaj głosu się nie powtarza.

### D68 · 2026-11-05 · E7: obsada, rundy 1b, 2 i 3
**Decyzja:**
- Ronan: `ronan_d1_s29`, bez dodatkowej chrypy. Referencja ma urywane frazy. Ronan dostaje 3 podejścia na fragment, bo taka referencja czasem daje powtórzenie.
- Kathryn: `kathryn_d3_s29`. Poruczniczka Rand: `ltrand_d3_s29`. Mistrz Bruli: `bruli_d2_s29`.
- Herbie: `herbie_d4_s5`. Szaman Mok: `mok_d3_s5`. Książę Banita: `outlaw_d2_s17`.
- Xenith: klon z dubbingu (jak D19).
- Automat dostaje regułę pauzy (ponad 1,2 s w środku kwestii), a fragment z wadą ma do 3 ponownych podejść zamiast jednego.

**Uzasadnienie:** Wybór z odsłuchu. W pierwszej kwestii Ronana użytkownik usłyszał za długą pauzę i powtórzenie, a ASR dał tam CER 0,064, poniżej progu 0,08. Kolejne podejścia wyszły z CER 0. W teście E5B jedno ponowne podejście zostawiło ucięte końcówki u Astarry.

### D69 · 2026-11-05 · E7: odblokowania po Q6–Q8
**Decyzja:**
- Do M2 dochodzą wydarzenia otwierane przez Q6–Q8 (E6A, E7A, E8A) i wydarzenia warunkowe z mapy (E8B, EC2, EC4, SQ1A, E5A).
- Scena przed Q9 wchodzi jako zabezpieczenie. Z danych gry nie wynika, czy odpala się sama po Q6–Q8.
- Q9 i SQ2 nie wchodzą. Oba to pełne scenariusze wybierane na mapie, SQ2 ma ok. 47 000 znaków.
- Nowe postacie: Mistrz Flint (`flint_d2_s17`), Mistrz Galgoraz (`galgoraz_d1_s53_drzenie`, z osobnej rundy: głos bardzo starej osoby, z drżeniem w referencji).

**Uzasadnienie:** Lektor nie powinien milknąć zaraz po ukończeniu scenariuszy ani w wydarzeniach, które mogą wypaść przy stole. Scenariuszy, które trzeba dopiero wybrać na mapie, generujemy dopiero wtedy, gdy będą dostępne. Pierwszy szacunek SQ2 był błędny, więc decyzję podjęto po sprostowaniu.

### D70 · 2026-11-05 · E7: wyniki testu E5B
**Wynik testu w grze:** opis misji czytany poprawnie, głosy brzmią dobrze, „Kontynuuj” bez odczytu, gra działa płynnie. Trzy poprawki przed blokiem B.

**Decyzja:**
- Opis misji milknie po zamknięciu panelu celu. Plugin 0.4.1 sprawdza widoczność panelu, bo `CurrentNode` zostaje ustawiony po zamknięciu.
- Cytat w opcji wyboru w M2 czyta bohater, który mówi w oknie (rozszerza D20). Mówca NPC to rozmówca, więc jego cytat zostaje przy narratorze. Opcje bez cudzysłowu też zostają przy narratorze, bo wśród nich są opisy testów i odpowiedzi skierowane do mówcy.
- Fragmenty M2 mają imię zapisane fonetycznie: „Keli” zamiast „Kehli”. Okno gry i `text_norm` zostają bez zmian, a companion porównuje tekst luki po tej samej zamianie. M1 się nie zmienia.
- Kampania znajomego wróciła do slotu 5 po teście (8 z 8 plików identycznych). Stan po teście leży w `analysis/work/saves/slot5-po-e5b`.

**Uzasadnienie:** To uwagi użytkownika z testu. Zmiana imienia dotyczy 108 fragmentów (ok. 12 700 znaków), które powstaną w bloku B razem z resztą. Poprawkę panelu sprawdzimy dopiero w grze, przy sesji na Macu.

### D71 · 2026-11-06 · E7: wyniki generowania M2
**Decyzja:** Oddajemy audio M2 z 42 oznaczonymi fragmentami z 3919. Nie generujemy ich ponownie, bo po 4 podejściach (bohaterowie po 6) wynik się nie zmienia, a przegląd nie pokazał uciętej kwestii fabularnej.

**Uzasadnienie:** Większość alarmów to zapis Whispera (nazwy, kafle). Ocena zna już te formy (`ASR_NAMES`, `TILE_LETTERS`, końcówka słowa w `tail_cut`). Niepewne zostały dwa końcowe spójniki w kawałkach kart wrogów, przed wartością luki. Szczegóły w `analysis/E7_AUDIO.md`. Końcówki sprawdzimy też uchem przy sesji na Macu.

### D72 · 2026-11-06 · E7: uwagi z gry na paczce M2
**Wynik testu:** uciszanie opisu misji i cytaty w głosie bohatera działają. Wymowę „Keli” użytkownik sprawdzi później. Sesję na Macu zagrano na paczce z pierwszą misją: wszystko działało zgodnie z założeniami, dziennika nie ma.

**Decyzja:**
- Sposób budowania paczek Windows i Mac zostaje bez zmian. Działanie paczki na Macu uznajemy za potwierdzone, E6 jest zamknięte. `analysis/E6_INSTALL.md` nie powstaje, bo nie ma dziennika.
- Zamknięcie okna w trakcie czytania wycisza głos przez 0,35 s zamiast go urywać. Nowy dźwięk skraca wyciszanie do 10 ms, więc opóźnienie startu się nie zmienia (D13).
- Odpowiedź z wyboru nie gra, gdy następna kwestia zaczyna się jej tekstem albo go zawiera. Czyta ją okno, w głosie mówcy i w całości. Okno otwiera się w tej samej chwili co zamknięcie opcji, więc ucięcia odpowiedzi nie słychać. W dziennikach zasada zadziałała 6 razy (zdarzenie `repeat`).
- Lista łupu zna nazwy wrogów z zakresu. Gra kończy nią polecenie usunięcia wroga z planszy (`REMOVE_ENTITY`). To był jedyny brak w replayu. Nowego audio nie trzeba.
- Strona odsłuchu ma najwyżej 30 fragmentów: po jednym z głosu, reszta losowo, bez odrzuconych przez automat. Odsłuch M2 odkładamy do czasu, aż zapadnie decyzja o sposobie generowania.
- Ponowna budowa paczki nie usuwa `stan/` i `logs/`, bo gra bywa zainstalowana z tego folderu. Zip ich nie zawiera.

**Uzasadnienie:** To uwagi użytkownika z gry. Rezygnacja z odpowiedzi zamiast z kwestii nie gubi tekstu, bo kwestia bywa dłuższa niż opcja. Replay ostatniej sesji pokazuje jeszcze 56 braków, ale to Q2 i samouczek, czyli teksty spoza zakresu M2.

### D73 · 2026-11-06 · E9: serwer MCP ElevenLabs i pomiar zużycia
**Decyzja:**
- Kolejny etap to test jakości głosów w ElevenLabs. OmniVoice zostaje modelem paczek, dopóki test nie wskaże innej drogi.
- Serwer `elevenlabs-mcp` 0.12.2 działa lokalnie i tylko w zakresie projektu (`.mcp.json`). Konfiguracji globalnej nie zmieniamy.
- Klucz leży w nieśledzonym `.env.elevenlabs.local`.
- Skrypty leżą w `analysis/tools/elevenlabs/`, a audio i logi w `analysis/work/elevenlabs/`. Repozytorium nie ma folderów `tools/` ani `runtime/` z planu użytkownika.
- Hooki zapisują koszt każdego płatnego wywołania: z historii konta, a w zapasie z różnicy licznika. Log trzyma SHA-1 i długość tekstu, bez samego tekstu.
- Dodatkowy hook `PostToolUseFailure` zapisuje wywołania z błędem, bo `PostToolUse` działa tylko po sukcesie.
- Stan między hookami to osobny plik na wywołanie (`usage/pending/`), a nie wspólny `pending.json`. Równoległe wywołania nie nadpisują sobie stanu.
- Bez reguł `deny`: kwestie prawne i licencyjne użytkownik rozstrzygnie w kolejnych etapach.
- Test na żywo obejmuje TTS na losowej kwestii bohatera, pomiar zużycia i własny wariant głosu. Zastępuje to neutralne zdanie z planu użytkownika.

**Uzasadnienie:** To decyzje użytkownika z QA. Układ ścieżek trzyma się zasady, że wyniki prywatne leżą w `analysis/work/`. Testy automatyczne nie łączą się z siecią, a każde płatne wywołanie wymaga zgody.

### D74 · 2026-11-07 · E9: wynik testu na żywo
**Wynik:** serwer, pomiar i własny głos działają. Cały test kosztował 325 kredytów. `eleven_v4` kosztuje 0,44 kredytu na znak, więc jedno podejście całego M2 to ok. 124 500 kredytów, czyli 98% miesięcznego limitu planu Creator. Szczegóły: `analysis/E9_ELEVENLABS.md`.

**Decyzja:**
- Hook bierze tekst i głos także z pola `dialogue`, bo modele v3 i v4 nie wypełniają `text` i `voice_id`.
- Hook pyta o historię do trzech razy, bo wpis może się spóźnić.
- Zerowa różnica licznika nie oznacza zerowego kosztu, bo licznik konta spóźnia się o około minutę. Bez wpisu w historii rekord dostaje flagę `unmeasured`.
- Procent okresu liczymy z wpisu historii, jeśli jest świeższy od licznika.
- `create_voice_from_preview` jest bezpłatne, więc hook je pomija.
- Głos `Lektor PL - Kehli test` zostaje na koncie do decyzji po odsłuchu.

**Uzasadnienie:** Pierwsze wywołanie pokazało fałszywe 0 kredytów, a tego testy bez sieci nie mogły wykryć, bo opierały się na opisie API. Po poprawce drugi TTS dał koszt zgodny z licznikiem konta.

### D75 · 2026-11-07 · Licencja i publikacja repozytorium
**Decyzja:**
- Kod, dokumentacja i raporty mają krótką licencję niekomercyjną po polsku i angielsku (`LICENSE.md`, rozstrzyga wersja polska).
- Korzystać mogą tylko osoby, które legalnie nabyły grę planszową *Descent: Legends of the Dark* (pol. *Descent: Legendy Mroku*, Fantasy Flight Games). Gra wymaga darmowej aplikacji, więc warunek dotyczy gry planszowej.
- Repozytorium może trafić publicznie na GitHub. Zdalne repozytorium dodaje użytkownik (zmienione w D82).
- W Git nie ma treści gry (tekstów, grafik, nagrań, dekompilacji), modeli ani wygenerowanego audio. `.gitignore` blokuje je w każdym miejscu repozytorium, także grafiki, bazy, dzienniki i archiwa.
- Narzędzia odtwarzają te dane lokalnie z kopii aplikacji użytkownika (`docs/ODTWORZENIE.md`).
- Wersje pakietów `.venv` są zapisane w `analysis/envs/venv.txt`. Instalacja na sucho w czystym środowisku przechodzi.
- Historia Git zostaje bez zmian. Stara wersja `analysis/REPORT.md` ma dwa krótkie cytaty z gry (kilkanaście słów), co mieści się w prawie cytatu. Adres e-mail z commitów będzie publiczny.
- `AGENTS.md` i `.codex/hooks.json` usunięte: dublowały `CLAUDE.md` i hooki z `.claude/settings.json`.

**Uzasadnienie:** Licencja może obejmować tylko utwory autora repozytorium. Prawa do tekstów, grafik i dubbingu ma wydawca i aktorzy, a warunek posiadania gry nie pozwala ich publikować. Publiczne repozytorium z treścią gry grozi zgłoszeniem DMCA i usunięciem. Skan wszystkich plików i całej historii ciągami 6 słów z tekstów gry (PL i EN) nie znalazł treści gry poza tymi dwoma cytatami.

**Zmiana 2026-11-07:** uzasadnienie o publikacji zastąpione przez D76. Zasada „Git bez treści gry, modeli i audio” zostaje.

### D76 · 2026-11-07 · Wydania na GitHub Releases
**Decyzja:**
- Wygenerowanego audio nie śledzimy w Git. Nie używamy Git LFS.
- Repozytorium ma narzędzia, które odtwarzają całe środowisko i pozwalają generować oraz klonować głosy na własne potrzeby (`docs/ODTWORZENIE.md`).
- Gotowe paczki Windows i Mac publikujemy w GitHub Releases publicznego repozytorium użytkownika. Paczka ma komplet plików jak dotąd: audio, bazę kwestii, plugin, loader, companion z Pythonem, skrypty i instrukcję.
- Wydania mogą zawierać głosy oparte na dubbingu i teksty gry. To dodatek do Descent objęty licencją tylko dla posiadaczy gry planszowej.
- Repozytorium nie ma komendy pobierania plików z wydania.
- Wydanie przygotujemy w etapie E10.
- Z `LICENSE.md` (pkt 6) znika zdanie o prywatnym użytku nagrań. Dokumentacja nie powtarza zastrzeżeń z licencji.
- Zostają reguły techniczne: Git bez treści gry, modeli i audio, raporty z kluczami i liczbami, długie teksty gry w plikach `analysis/work/`.
- D76 zastępuje prywatny użytek klonów z D06, zakaz rozpowszechniania audio z D33 i uzasadnienie D75. Stare wpisy mają adnotacje.

**Uzasadnienie:** To decyzje użytkownika z QA. Audio to najdłuższa część pracy (M2 ok. 16 h GPU) i nie odtwarza się bajt w bajt, więc gracze dostają je gotowe. Pliki wydań leżą poza historią Git (do 2 GiB na plik), więc repozytorium zostaje małe bez LFS.

### D77 · 2026-11-07 · E11: arkusz porównawczy głosów i skill ElevenLabs
**Decyzja:**
- Następny etap to arkusz porównawczy głosów (E11). Katalog treści gry przechodzi na później (E12). Sposób przechowywania i zarządzania danymi z gry dobieram sam, w projekcie i poza Git.
- Głosy z dubbingu porównujemy bez ElevenLabs: referencja z gry wobec OmniVoice. Klonów dubbingu w ElevenLabs nie robimy.
- Postacie bez dubbingu: OmniVoice wobec 3 wariantów ElevenLabs. Modele i sposób robienia wariantów ustalimy w QA po opisie modeli.
- Kwestie losuje `analysis/tools/voice_compare.py pick` (ziarno 20261107): jeden fragment, co najmniej 7 słów, do 220 znaków, gotowe audio M2 bez uwag automatu.
- Ne’Krul ma w M2 jedną kwestię, a automat zgłosił w niej uciętą końcówkę i tempo. Arkusz pokazuje ją z tą uwagą.
- Skill `elevenlabs` (`.claude/skills/elevenlabs/SKILL.md`, tylko to repozytorium) opisuje korzystanie z MCP.
- Każda odpowiedź z wywołaniem MCP kończy się blokiem zużycia: ten prompt, projekt i konto wobec limitu (`usage_report.py --mark` na początku i `--summary` na końcu).
- Hook szacuje koszt `text_to_voice` stawką 1 kredytu na znak tekstu podglądu (flaga `estimated`), bo to narzędzie nie ma wpisu w historii.

**Uzasadnienie:** To decyzje użytkownika z QA. Serwer MCP 0.12.2 przekazuje do projektu głosu tylko opis i tekst (endpoint `create_previews`, model `eleven_multilingual_ttv_v2`). Parametry `seed` i `guidance_scale` oraz model `eleven_ttv_v3` wymagałyby własnego wywołania API.

**Zmiana 2026-11-07:** sposób liczenia kosztu `text_to_voice` zastąpiony przez D78.

### D78 · 2026-11-07 · E11: warianty ElevenLabs, druga runda modeli TTS i ocena na ślepo
**Decyzja:**
- Warianty postaci bez dubbingu: 3 wyraźnie różne opisy na postać z portretu i `docs/CASTING.md`, przez MCP `text_to_voice`. Opisy są w `analysis/tools/voice_designs_e11.json`, bez osobnej akceptacji przed generowaniem. Wariant a jest najbliżej obecnej obsady, b i c zmieniają wiek, barwę i temperament.
- Każdy opis daje 3 podglądy z obiema kwestiami. Do arkusza trafia najlepszy według automatu E3: bez uciętej końcówki i dziur, potem najniższy CER.
- Koszt zatwierdzony: ok. 5,8 tys. kredytów (+20%). Głosów nie zapisujemy na koncie.
- Druga runda po ocenach: zwycięski wariant każdej z 11 postaci zapisujemy na koncie (11 z 29 wolnych miejsc) i czytamy te same kwestie modelami `eleven_v4`, `eleven_multilingual_v2`, `eleven_flash_v2_5` i `eleven_v3` (ok. 6,6 tys. kredytów przy stawce 1,0 dla modeli niezmierzonych).
- Ocena na ślepo w skali 1–5 z notatką. Próbki A–D w losowej kolejności, odsłona etykiet i wyników automatu po ocenie, eksport do `e11_oceny.json`. Przy dubbingu oceniamy podobieństwo OmniVoice do oryginału i jakość.
- Kwestie OmniVoice sklejamy w jedno nagranie (pauza 0,5 s), a wszystkie próbki arkusza wyrównujemy do -20 LUFS, żeby porównywać ten sam tekst przy tej samej głośności.
- Hook liczy `text_to_voice` zawsze stawką 1 kredytu na znak tekstu podglądu (`method: rate`), a różnicę licznika tylko zapisuje.

**Uzasadnienie:** Wybór użytkownika z QA. Przyrost licznika konta po pierwszych czterech podglądach wyniósł 733 kredyty, dokładnie 3 × 206 + 115 znaków. Licznik konta jest wspólny i spóźniony, więc przy wywołaniach z rzędu jego różnica łapała koszt sąsiednich wywołań: dwa rekordy dostały po 733 kredyty. Te rekordy poprawiliśmy w logu na stawkę.

### D79 · 2026-11-07 · E11: runda 2, cztery modele TTS jednym głosem
**Decyzja:**
- Runda 2 porównuje modele TTS, nie głosy. Bierzemy jeden wariant na postać. Przy remisie ocen bierzemy wariant bliższy portretowi i `docs/CASTING.md`: Astarra b, Kathryn a, Bruli a, Mok a, Flint a, Galgoraz a. Adelynn (remis z OmniVoice) dostaje wariant b. Wybór obsady przy remisach zostaje otwarty.
- 11 głosów zapisanych na koncie jako `Lektor PL - <postać> <wariant>`, razem 12 z 30 miejsc (z testem Kehli). Głosy zostają do decyzji o obsadzie.
- Te same kwestie czytają `eleven_v4`, `eleven_multilingual_v2`, `eleven_flash_v2_5` i `eleven_v3`, z domyślnymi ustawieniami (stability 0,5, similarity 0,75, style 0, speed 1,0) i bez tagów audio.
- Strony c1 i c2: 4 modele na ślepo i wzorzec z podglądu rundy 1 bez oceny.
- Hook dopasowuje wpis historii także po modelu i pomija wpisy już przypisane (`history_item_id`).

**Uzasadnienie:** Użytkownik chciał przejść do generowania bez rozstrzygania remisów, bo runda 2 dotyczy modeli. Zmierzone stawki (historia konta, 1921 znaków na model): v4, Multilingual v2 i v3 po 0,44 kredytu na znak, Flash v2.5 0,22. Cała runda kosztowała 2956 kredytów zamiast szacowanych 6,6 tys. Pierwsze cztery rekordy dostały ten sam wpis historii, bo tekst był ten sam, a hooki działały równolegle. Poprawiliśmy je w logu według historii konta.

### D80 · 2026-11-07 · Wynik E11: OmniVoice dla dubbingu, ElevenLabs v4 dla postaci bez dubbingu
**Decyzja:**
- Narrator (z głosem systemowym), bohaterowie z dubbingiem i złoczyńcy z dubbingiem zostają w OmniVoice.
- Postacie bez dubbingu czyta ElevenLabs `eleven_v4` z ustawieniami domyślnymi.
- Obsada postaci bez dubbingu to głosy z rundy 2, razem z wariantami przy remisach: Adelynn b, Ronan b, Astarra b, Kathryn a, Porucznik Rand a, Bruli a, Herbie c, Mok a, Banita b, Flint a, Galgoraz a (`docs/CASTING.md`). To zamyka ponowny dobór głosu Adelynn z D55.
- Głosy OmniVoice tych postaci zostają jako zapas. Głosy ElevenLabs zostają na koncie (12 z 30 miejsc).
- Przegenerowanie fragmentów tych postaci w pipeline to osobny etap (E13 w `docs/PLAN.md`), po akceptacji planu.

**Uzasadnienie:** Wybór użytkownika z QA po arkuszu E11 (`analysis/E11_VOICES.md`). Dubbing w OmniVoice dostał 4,56 za jakość i 4,22 za podobieństwo, bez kredytów. Postacie bez dubbingu: ElevenLabs 4,73, OmniVoice 1,91. W rundzie 2 v4 miał najwyższą średnią (4,36) i był najlepszy lub ex aequo u 10 z 11 postaci, przy tej samej stawce co Multilingual v2 (0,44 kredytu na znak). Między najlepszymi modelami użytkownik nie słyszał znaczących różnic. Postacie bez dubbingu w M2 to ok. 4,9 tys. kredytów.

### D81 · 2026-11-07 · E13: postacie bez dubbingu w ElevenLabs przez własną komendę
**Decyzja:**
- Fragmenty generuje komenda `python -I -m lektor eleven` w `.venv` z kluczem z `.env.elevenlabs.local`, bez MCP. Obejmuje M2 i M1 (prolog i Q1, Adelynn i Ronan).
- Jedno podejście na fragment. Ponowne (do 3) tylko przy uwagach automatu, a przy końcówce wolniej (speed 0,9, jak w D34).
- Najpierw pilot po jednym fragmencie na postać, potem reszta bez zatrzymania.
- Silnik i `voice_id` głosu są w `direction.ELEVEN_VOICES`. Klucze fragmentów zostają z OmniVoice. Podejścia ElevenLabs mają numery od 101 i leżą obok podejść OmniVoice, które zostają jako zapas.
- `select` bierze dla głosu tylko podejścia jego silnika, a medianę barwy liczy osobno dla silnika. M2 przejmuje z M1 podejścia ElevenLabs fragmentów o tym samym id, więc M1 generujemy pierwsze.
- Wynik w PCM 24 kHz, w próbkowaniu manifestu. Manifest podaje model każdego fragmentu.
- Automat ocenia barwę wobec nagrania v4 z rundy 2 E11, a tempo wobec tempa v4 przy speed 1,0 (14,7 znaku na sekundę, mediana z E11).
- Koszt każdego wywołania trafia do logu zużycia jako `lektor_eleven`, z wpisu historii konta wskazanego nagłówkiem `history-item-id`.
- Limit etapu to zatwierdzony szacunek +20% (ok. 5,9 tys. kredytów), pilnowany opcją `--max-credits`.

**Uzasadnienie:** Wybór użytkownika z QA. Komenda jest wznawialna, liczy koszt jak hook MCP i przyda się przy całej grze. Pilot (11 fragmentów, 303 kredyty) przeszedł automat bez uwag. Wynik: 156 fragmentów w manifestach (M1 16, M2 140), 163 wywołania, 5411 kredytów (0,44 na znak, w tym 7% na ponowne podejścia). Automat zostawił 4 uwagi u Adelynn, wszystkie to fałszywe alarmy Whispera. Szczegóły: `analysis/E13_AUDIO.md`.

### D82 · 2026-11-08 · E10: publiczne repozytorium i wydanie v0.2.0
**Decyzja:**
- E10 idzie teraz, po E13 i przed E12. Wydanie obejmuje M2 z głosami postaci bez dubbingu z E13.
- Repozytorium `wiQ1999/descent-lektor-pl` jest publiczne. Zdalne repozytorium, wypchnięcie i wydanie robi Claude przenośnym GitHub CLI z `analysis/work/bin/` z konfiguracją w `analysis/work/bin/gh-config`, bez zmian w globalnej konfiguracji Git. Loguje się użytkownik (`gh auth login`), Claude nie widzi tokenu. Zmienia D75 (zdalne repozytorium dodaje użytkownik) i zakres E10 (publikację robi użytkownik).
- Tag `v0.2.0`, wydanie oznaczone jako pre-release: Q9 i SQ2 nie mają jeszcze audio (D69), a sesja przy stole na Macu jest otwarta (D61, E7).
- Historia Git zostaje bez zmian: z dwoma krótkimi cytatami w starej wersji `analysis/REPORT.md` (D75) i adresem e-mail konta GitHub użytkownika w commitach.
- Każda paczka ma `LICENSE.md`, `UZNANIE_AUTORSTWA.md` (OmniVoice, Higgs Audio v2, ElevenLabs, dubbing i teksty gry, Doorstop, Python i pakiety) i tekst licencji Doorstop w `licencje/`. Folder `loader/` zostaje bez zmian, bo instalator kopiuje go do gry.
- Opis wydania podaje zakres scenariuszy, rozmiary i sumy SHA-256 paczek. `INSTRUKCJA.md` ma zakres M2 i miejsce na dysku po rozpakowaniu.

**Uzasadnienie:** Prośba użytkownika po lokalnym teście paczki M2 i wybory z QA. Wagi OmniVoice (CC BY-NC) i tokenizer Higgs Audio v2 (Boson Higgs Audio 2 Community License) wymagają uznania autorstwa, a CC BY-NC także użytku niekomercyjnego. Wydanie jest niekomercyjne, a uznanie autorstwa jest w każdej paczce. Audio ElevenLabs powstało w płatnym planie. Doorstop (LGPL 2.1) wymaga tekstu licencji i dostępu do źródeł, stąd plik w `licencje/` i link do wydania źródłowego. Skan historii (66 commitów, ciągi 5 słów ze wszystkich tekstów gry PL i EN) znalazł tylko dwa cytaty z D75 i żadnych kluczy API ani tokenów.

### D83 · 2026-11-08 · E14: reszta gry, kolejność i obsada
**Decyzja:**
- Następny etap to reszta gry (E14). Najpierw kwestie postaci bez dubbingu w ElevenLabs, potem pozostałe kwestie narratora i postaci z dubbingiem lokalnie w OmniVoice.
- Generowanie idzie paczkami: w ElevenLabs paczka na postać, w OmniVoice paczka na misję. Postęp pokazuje, ile zrobiono i ile czasu zostało.
- Złoczyńcy z samymi okrzykami dubbingu (Zachareth, Reneyr, Greysdon, Navoth, Levirax, Gilliam, Vraskhar) dostają klon OmniVoice z okrzyków, jak Ne’Krul i Xenith. ElevenLabs tylko wtedy, gdy klon wypadnie słabo w ocenie użytkownika.
- Obsada 18 nowych postaci z udziałem użytkownika: jeden opis z portretu i kontekstu kwestii, jeden projekt głosu ElevenLabs, 2 losowe fragmenty. Arkusz pokazuje portret, opis i fragmenty, dotychczasowe głosy oraz głosy OmniVoice nowych postaci i złoczyńców, żeby dla każdej postaci wybrać silnik.
- Plan E14 zaakceptowany 2026-11-08.
- Testowy głos Kehli zostaje usunięty z konta ElevenLabs.

**Uzasadnienie:** Wybory użytkownika z QA po szacunku `analysis/E14_NO_DUB_SCOPE.md`: 129,1 tys. znaków postaci bez dubbingu poza M2, w tym 27,5 tys. złoczyńców z okrzykami. Wariant z OmniVoice dla złoczyńców kosztuje ok. 57 tys. kredytów z obsadą i mieści się w 30 miejscach na głosy. Wszystko w ElevenLabs to ok. 74 tys. i 37 miejsc.

### D84 · 2026-11-08 · E14: obsada po rundzie 1 arkusza
**Decyzja:**
- Postacie bez dubbingu gry czyta tylko ElevenLabs. Głosów OmniVoice dla nich nie robimy.
- Przyjęte głosy ElevenLabs (13): Magrit, Alys, Greigory, Button, Laurel, Arden, Veta, Trevalyn, Balthain, Ducard, Pryor, Grace i Drys.
- Nowy wariant do ponownej oceny (5): Waiqar (doświadczony wojownik), Morant (inny wariant), Delphyndra (smoczy, nie ludzki), Nara (kobieta ork), Meza (mniej ludzki, hybryda).
- Przyjęci złoczyńcy w OmniVoice (5): Zachareth, Reneyr, Greysdon, Navoth i Vraskhar. Nowy wariant: Levirax (przeciągane końcówki jak u gada) i Gilliam (bardziej przerażony).
- Testowy głos „Lektor PL - Kehli test” usunięty z konta 2026-11-08. Gdy w rundzie 2 wybierzemy nowy wariant, głos tej postaci z rundy 1 usuwamy z konta i zapisujemy nowy.
- Głosy i voice_id: `docs/CASTING.md`.

**Uzasadnienie:** Oceny użytkownika z arkusza `e14_oceny.json`: w ślepym porównaniu ElevenLabs wygrał u każdej postaci i słychać, który to model, bo ma lepszą jakość. Uwagi przy 5 postaciach i 2 złoczyńcach wymagają innego wariantu. Konto ma 30 z 30 miejsc, więc nowe głosy zastępują stare.

### D85 · 2026-11-08 · M3: komunikaty gry czyta narrator
**Decyzja:**
- W m3 komunikat gry doklejony po pustym wierszu do kwestii postaci (zasoby, złoto, przychylność, legendy, żetony, rozdziały) czyta narrator jako osobny segment. Postać czyta tylko swoją wypowiedź.
- Tekst WIELKIMI literami w m3 czytamy zwykłą pisownią zamiast go wycinać. Liczby rzymskie zamieniamy na słowa („akt drugi”). Pomijamy tylko wskazówki „X WYBIERA…”.
- M1 i M2 budują się bez zmian.

**Uzasadnienie:** Uwaga użytkownika przy Zacharecie: kwestia „Do waszych zasobów dodano…” brzmi jak dla narratora. Komunikaty systemowe czyta narrator od D36. Przegląd bazy pokazał, że normalizacja wycinała komunikaty wielkimi literami tylko w części i postać czytała resztki, np. „W AKCIE jeden Z”. Wybór z QA: komunikaty czyta narrator. Wynik: 87 kwestii z komunikatem narratora (69 różnych komunikatów, 5 w zakresie M2), 39 kwestii z odzyskanym tekstem wielkimi literami, fragmentów +183 i −91 (ok. 15 tys. znaków, głównie narrator).

### D86 · 2026-11-08 · Wstawki sceniczne w kwestiach: etap po E14
**Decyzja:**
- Wstawki w nawiasach z opisem zachowania postaci zbieramy teraz i poprawiamy w osobnym etapie E15, po nagraniu całej gry.
- E15 rozważy dwa warianty: postać pomija wstawkę albo wstawkę czyta narrator.
- Listę daje `analysis/tools/inserts_scan.py`, raport `analysis/E14_INSERTS.md`.

**Uzasadnienie:** Prośba użytkownika po odsłuchu arkusza E14. Skan m3: 264 wstawki w kwestiach postaci (prawie wszystkie to ta sama jednowyrazowa wstawka na początku kwestii) i 28 w kwestiach narratora. Do E15 postać czyta wstawkę razem z kwestią, więc E15 wymaga ponownego generowania tych kwestii.

### D87 · 2026-11-08 · E14: obsada po rundzie 2 arkusza
**Decyzja:**
- Przyjęte nowe głosy ElevenLabs: Waiqar i Morant (ocena 4). Zapisane jako „Lektor PL - <postać> E14 r2”, a ich głosy z rundy 1 usunięte z konta (zgoda z QA, D84).
- Przyjęte warianty złoczyńców (ocena 5): Levirax `levirax_v2a` (monolog jak w rundzie 1, tempo 0,85) i Gilliam `gilliam_v2b` (referencja z rundy 1 z drżeniem).
- Delphyndra, Nara i Meza (ocena 1): runda 3 z trzema wyraźnie różnymi opisami na postać (`el3` a, b, c w `voice_designs_e14.json`). Arkusz pokazuje z każdego opisu jeden podgląd: przy równym CER ten z F0 najbliżej 200 Hz.
- Głosy tych trzech postaci z rundy 1 zostają na koncie do wyboru w rundzie 3.

**Uzasadnienie:** Oceny użytkownika z arkusza `e14r2_oceny.json` i prośba o po 3 warianty dla głosów z niską oceną. Uwagi z rundy 2: Delphyndra brzmi jak mężczyzna (podgląd miał 98 Hz, bo arkusz wybierał tylko po CER), Nara nie brzmi jak kobieta ork, a Meza ma być chłodna i demoniczna. Koszt rundy 3: 9 projektów, ok. 2 tys. kredytów.

### D88 · 2026-11-08 · E14: obsada po rundzie 3 arkusza
**Decyzja:**
- Przyjęte głosy (ocena 5): Nara z opisu c (stara orczyca, zdarty głos) i Meza z opisu a (lodowaty szept z demonicznym podtonem). Zapisane jako „Lektor PL - <postać> E14 r3”, a głosy z rundy 1 usunięte z konta.
- Delphyndra: runda 4 z pięcioma bardzo różnymi opisami głosu potężnej smoczycy (`el4` a–e w `voice_designs_e14.json`). Na stronie jest dla porównania Levirax, żeby dwie smoczyce w grze brzmiały różnie.
- Głos Delphyndry z rundy 1 zostaje na koncie do wyboru w rundzie 4. Podglądy nie zajmują miejsc, więc liczba wariantów nie zależy od wolnych miejsc (29 z 30 zajętych).

**Uzasadnienie:** Oceny użytkownika z arkusza `e14r3_oceny.json`. Delphyndra nadal nie pasuje, a głos ma przypominać potężnego smoka płci żeńskiej. Koszt rundy 4: 5 projektów, ok. 1,2 tys. kredytów.

### D89 · 2026-11-08 · E14: Delphyndra, runda 5 z efektem smoka
**Decyzja:**
- Runda 5 dla Delphyndry: pięć opisów głosu głębokiego i chropawego (`el5` a–e). Arkusz bierze z każdego opisu podgląd z F0 najbliżej 140 Hz, nie niżej niż 120 Hz.
- Obok każdego wariantu jest ta sama próbka z efektem smoka zrobionym lokalnie (`dragon_fx` w `voice_compare_e14.py`):
  - ton niżej o 3 półtony razem z formantami;
  - bas oktawę niżej pod filtrem 300 Hz;
  - chrypa z nasycenia;
  - pogłos jaskini 1,6 s.
- Jeśli wygra wersja z efektem, dodanie efektu do pipeline’u dla kwestii Delphyndry będzie osobną decyzją przed generowaniem.

**Uzasadnienie:** Uwaga użytkownika po rundzie 4: głos ma być głęboki i chropawy, podobny do smoka z filmu „Hobbit”. Taki głos w filmie powstał z obróbki dźwięku. Projekt głosu ElevenLabs przy bardzo niskim tonie daje głos męski (98 Hz w rundzie 2), więc niski ton uzyskujemy też efektem, a nie tylko opisem. Koszt rundy 5: 5 projektów, ok. 1,2 tys. kredytów. Efekt nie kosztuje kredytów, a automat ma po nim CER ≤ 0,4%.

### D90 · 2026-11-08 · E14: Delphyndra, runda 6 bez efektu
**Decyzja:**
- Runda 6 dla Delphyndry: pięć opisów `el6`. Każdy zaczyna się od słów „huge, bloodthirsty female dragon” i kilka razy podkreśla kobiecy głos. Efekt smoka z D89 odpada.
- Arkusz bierze z każdego opisu podgląd z F0 najbliżej 190 Hz i nie niżej niż 160 Hz, bo część głosów z rundy 5 brzmiała jak męska.

**Uzasadnienie:** Uwaga użytkownika po rundzie 5: głosy nie przypominają smoka, a część z nich brzmi jak męska. Prośba, by zapytanie do MCP wprost mówiło o wielkiej, krwiożerczej smoczycy. Każdy opis daje zwykle jeden lub dwa podglądy około 120–150 Hz i jeden powyżej 200 Hz, więc próg 160 Hz odcina głosy podobne do męskich. Koszt rundy 6: 5 projektów, ok. 1,2 tys. kredytów.

### D91 · 2026-11-08 · E14: Delphyndra, runda 7 jako mieszanka Leviraxa i próbki C
**Decyzja:**
- Głos Delphyndry łączymy z dwóch źródeł: klonu Leviraxa z dubbingu i próbki C z rundy 6 (podgląd ElevenLabs z opisu `el6` a).
- Mieszanka to klon OmniVoice z referencji sklejonej z obu głosów. Oba wycinki są przycięte na granicach słów (Whisper ze znacznikami słów), mają wyrównaną głośność i transkrypcję z tych samych wycinków (`refs7` w `voice_compare_e14.py`).
- Arkusz ma cztery proporcje:
  - więcej Leviraxa: 7,5 s + 2,4 s;
  - po równo: 4,6 s + 4,6 s;
  - po równo w tempie 0,85 jak wybrany Levirax;
  - więcej próbki C: 3,5 s + 6,3 s.
- Nagrania z błędem automatu dostają ponowne podejścia z innymi ziarnami (`retake7`, `pick7`).
- Jeśli wygra mieszanka, Delphyndrę czyta OmniVoice, co jest wyjątkiem od D84. Zapiszemy to po wyborze.

**Uzasadnienie:** Uwaga użytkownika po rundzie 6: próbka C jest najciekawsza, ale to wciąż nie to. Prośba o połączenie jej z głosem Leviraxa. ElevenLabs nie łączy głosów przez MCP, a klon ElevenLabs z nagrań dubbingu wymaga osobnej zgody (prawa do głosu, skill `elevenlabs`). Lokalny klon OmniVoice z dubbingu stosujemy dla złoczyńców od D19 i nie kosztuje kredytów. Mieszanka z przewagą próbki C we wszystkich 7 podejściach pomija dwa krótkie okrzyki we fragmencie 2 (CER 20%). Pozostałe mają CER 0.

### D92 · 2026-11-08 · E14: Delphyndra, runda 8 z nowym profilem i trzema klonami Leviraxa
**Decyzja:**
- Profil Delphyndry (`brief` w `voice_designs_e14.json`) piszemy od nowa z portretu. To ciężka bestia, a nie ekscentryczna dama:
  - krzywe kły, z pyska kapie zielona, żrąca ślina;
  - mosiężny gogiel na oku i mechaniczny szpon;
  - głos zwierzęcy i mroczny: gardłowy, mokry od śliny, z warczeniem, sapaniem i sykiem; kobiecy, ale nieludzki.
- Poprzedni profil zostaje w `brief_r1`.
- Z nowego profilu powstaje jeden opis `el8` (`text_to_voice`, 243 kredyty). Arkusz pokazuje wszystkie trzy podglądy, bo każdy to inny głos, a automat żadnego nie odrzucił.
- Trzy klony Leviraxa w OmniVoice różnią się referencją, bo klon przejmuje z niej wysokość, chrypę i syk (`refs8` w `voice_compare_e14.py`):
  - olbrzymka: monolog 4 półtony niżej, tempo 0,85;
  - bestia: monolog 2 półtony niżej z warczeniem (warstwa oktawę niżej i chrypa `roughen`), tempo 0,9;
  - gadzina: ciche, syczące okrzyki z wariantu `levirax_v2b` z dodanym sykiem, tempo 0,8.
- Nagrania z błędem automatu dostają ponowne podejścia jak w rundzie 7 (`retake8`, `pick8`).
- Wybór klonu oznacza, że Delphyndrę czyta OmniVoice (wyjątek od D84). Zapiszemy to po wyborze.

**Uzasadnienie:** Uwaga użytkownika po rundzie 7: głos wciąż kompletnie nie pasuje do postaci. Prośba o profil od portretu, głos bardziej zwierzęcy i mroczny oraz trzy mocno różne klony Leviraxa. Stary profil opisywał ekscentryczną wynalazczynię i prowadził opisy ElevenLabs w stronę ludzkiego głosu. Portret pokazuje bestię. Obróbka referencji zamiast gotowego nagrania daje klon z naturalną intonacją. Efekt nałożony po generowaniu w rundzie 5 nie przekonał.

Wyniki automatu: wszystkie sześć wariantów ma CER 0 i nie ma uciętych końcówek. Gadzina potrzebowała ponownego podejścia we fragmencie 1: pierwsze miało CER 14%, wybrane ziarno 17. Mediana F0:
- podglądy ElevenLabs: 116, 119 i 269 Hz;
- klony: olbrzymka 90 Hz, bestia 107 Hz (jak Levirax), gadzina 230 Hz.

Najniższe głosy mogą brzmieć męsko, a o tym rozstrzyga odsłuch.

### D93 · 2026-11-08 · E14: Delphyndra, runda 9 z poprawkami klonu B
**Decyzja:**
- W rundzie 8 wygrała próbka B, czyli olbrzymka: klon Leviraxa 4 półtony niżej. Runda 9 ją poprawia.
- Źródło robotycznego brzmienia: `librosa.effects.pitch_shift` to wokoder fazowy. Rozciąga czas i zostawia w referencji metaliczny pogłos, a klon go przejmuje.
- Ton obniżamy teraz samym przepróbkowaniem, jak wolniejsza taśma. Ton i formanty spadają razem, bez artefaktów, a referencja wydłuża się o 2^(n/12).
- Wydłużenie wyrównuje mnożnik `speed`, bo OmniVoice liczy długość nagrania z tempa referencji (`clone_kw`).
- PSOLA odrzuciliśmy po próbie: pYIN uznaje za dźwięczną tylko połowę ramek chropawego głosu Leviraxa, więc zmiana tonu działała tylko częściowo.
- Pięć wariantów, wszystkie z monologu Leviraxa w tempie 0,85:
  - bez artefaktów: ton i gardło jak w B;
  - to samo z instrukcją OmniVoice „female” obok klonu;
  - 3 półtony niżej zamiast 4, z instrukcją „female”;
  - jak bez artefaktów, z miękkim tchnieniem w referencji;
  - barwa jak B: te same nagrania co „bez artefaktów”, z korektorem liniowo-fazowym (najwyżej ±12 dB, wygładzenie 1/3 oktawy) z ich widma do widma nagrań B (`eq9`).
- Piąty wariant jest potrzebny, bo klon z przepróbkowanej referencji wychodzi ciemniejszy od B (środek widma ok. 1600 zamiast 2340 Hz), choć same referencje mają podobną jasność. Korektor na referencji tego nie zmienił, a na nagraniach przywraca rozkład pasm B.
- Dla porównania arkusz ma Leviraxa i B z rundy 8.
- Wyniki automatu: wszystkie warianty bez uciętych końcówek. CER wynosi 0, poza tchnieniem z 6% we fragmencie 2 (poniżej progu 10%). Długość nagrań jest jak w B, więc wyrównanie tempa działa. Mediana F0 81–91 Hz (B: 90 Hz).

**Uzasadnienie:** Uwaga użytkownika: B momentami brzmi robotycznie. Niska barwa pasuje, ale głos ma dostać trochę kobiecego charakteru przy tej samej barwie. Przepróbkowanie usuwa przyczynę, zamiast ją maskować. Instrukcja „female” to jedyny sposób w OmniVoice, żeby nadać kobiecy charakter bez zmiany referencji. Model przyjmuje ją razem z klonem, bo opis stylu i referencja to osobne części wejścia.

### D94 · 2026-11-08 · E14: Delphyndra w OmniVoice, obsada A3 zamknięta
**Decyzja:**
- Delphyndrę czyta klon OmniVoice `delph_b_jasniej`, czyli próbka A z rundy 9:
  - referencja to monolog Leviraxa przepróbkowany 3 półtony niżej, transkrypcja bez zmian (`refs9.json`);
  - instrukcja OmniVoice „female” obok klonu;
  - tempo 0,85 × wydłużenie referencji 1,189.
- To wyjątek od D84: jedyna postać bez dubbingu w OmniVoice.
- Pipeline fazy B dostaje dla głosu instrukcję i mnożnik tempa, które dziś ma tylko `voice_compare_e14.py` (`clone_kw`).
- Zakres: 16 fragmentów, 1675 znaków, tylko w misji `a2_q6`. Levirax mówi w `a1_q10`, `a2_q7` i `a2_q11`, więc podobne głosy nie spotkają się w jednej scenie.
- Paczka ElevenLabs fazy B1 bez Delphyndry: 1027 nowych fragmentów, 99,8 tys. znaków (11 głosów E13: 25,4 tys., 17 głosów E14: 74,4 tys.).

**Uzasadnienie:** Ostateczny wybór użytkownika po rundzie 9. Żaden z 6 rund opisów ElevenLabs nie dał głosu smoczycy, a klon Leviraxa z kobiecym charakterem tak.

### D95 · 2026-11-09 · E14: start fazy B
**Decyzja:**
- Głos ElevenLabs Delphyndry z rundy 1 (`1sr70RNkbV4TmYCh7tKG`) usunięty z konta: 28 z 30 miejsc.
- Wstawki sceniczne wycinamy z kwestii postaci już teraz (`build.drop_inserts`), przed generowaniem:
  - znika wstawka na początku zdania: 263 kwestie, wszystkie z jedną wstawką o mruganiu;
  - krótkie wtrącenie w środku zdania zostaje, bo to mowa postaci (1 kwestia);
  - w obu wariantach E15 postać wstawki nie czyta, więc E15 zmieni tylko kwestie narratora albo dołoży narratora przed kwestią (D86).
- B1 zatwierdzone w całości: 28 głosów, 1027 fragmentów, 99,7 tys. znaków, ok. 44 tys. kredytów, z ponownymi ok. 48 tys. Limit to 58 tys. kredytów na całe wydanie (`MAX_CREDITS` w `analysis/tools/e14_run.sh`), liczony od nowa przed każdym wsadem.
- B2 obejmuje całość w kolejności gry: akt 1, akt 2, potem części wspólne (wydarzenia, sprzęt, wrogowie, system). Fragment należy do pierwszej paczki, w której występuje (`lektor.progress`). Użytkownik nie sprawdza paczek po drodze.
- Postęp pokazuje `lektor progress --release m3`: części i paczki, znaki, godziny GPU, kredyty, czas do końca. Skrypt co 10 min zapisuje go do `analysis/work/audio/m3/progress.md`.
- Klony E14 w bazie referencji (`voice_compare_e14.py adopt`): 8 głosów.
  - Levirax ma styl z tempem 0,85.
  - Delphyndra ma instrukcję „female” i tempo 1,0108 (0,85 × wydłużenie referencji 1,189).
  - Styl wchodzi do klucza fragmentu (`build.voice_tag`). `synth` mnoży przez niego tempo pierwszych podejść i przekazuje instrukcję, a ponowne podejścia biorą tempo z zapisanego podejścia.
- ElevenLabs zapisuje stan w `takes_eleven.jsonl`, bo oba silniki działają naraz. `load_state` czyta oba dzienniki i pomija urwany wiersz.
- Baza `m3` po zmianach ma 17 956 fragmentów, z czego 3915 przejmujemy z M2. Do zrobienia zostaje:
  - OmniVoice: 13 014 fragmentów, 20 512 podejść, 1,62 mln znaków, ok. 107 h GPU bez ponownych podejść;
  - ElevenLabs: 1027 fragmentów.

**Uzasadnienie:** QA 2026-11-09 przyniosło cztery decyzje:
- usunięcie starego głosu;
- wycięcie wstawek teraz;
- zatwierdzenie całego B1;
- B2 w kolejności gry, akt po akcie, bez sprawdzania przez użytkownika, z postępem zwracanym przez skrypt.

Wycięcie teraz oszczędza ponowne generowanie 263 kwestii w E15.

## Ustalenia z analiz (fakty, na których opierają się decyzje)

- Unity Audio jest wyłączone w obu buildach (`globalgamemanagers` → `AudioManager.m_DisableAudio = true`). Dźwięk gra obsługuje przez Wwise.
- RTF na GTX 1650 Ti wynosi ok. 2,2 (`analysis/BENCH.md`), więc generowanie na żywo nie zmieści się w 2–3 s.
- Build macOS ma identyczne teksty, audio i klasy hooka jak Windows (`analysis/MAC_REPORT.md`).
- Prolog i Q1 nie potrzebują głosów NPC (mówi tylko Ne’Krul), ale głos systemowy jest potrzebny od razu: 255 kluczy (`analysis/M1_SCOPE.md`). Scena „Welcome Home” dołączona w D15 ma dwie postacie NPC: Adelynn (12 kwestii) i Ronan (4) (`analysis/E2_DATA.md`).
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
  - cel misji (HUD) i tekst aktywacji wroga (`UIEnemyActivationDialog`) gra pokazuje poza oknami wiadomości;
  - crash przy wyjściu do pulpitu (`mono_jit_cleanup`) występuje tylko z loaderem. Bez moda gra zamyka się czysto (test 2026-11-01).
- E0 (`analysis/BAKEOFF.md`):
  - OmniVoice z góry ustala długość wyniku: domyślnie według tempa referencji (z pauzami, stąd „za wolno”), a `speed` ją skraca;
  - koszt wywołania OmniVoice rośnie z długością całego ciągu (tekst, referencja, wynik), liczonego co krok dwa razy (CFG);
  - modele z transkrypcją referencji potrzebują wycinków ciętych na granicach słów.
- E2 (`analysis/E2_DATA.md`):
  - baza M1: 649 kluczy, 635 do syntezy, 965 unikalnych fragmentów; szacunek E3 ok. 38 h GPU bez retake;
  - wilk wystąpił w losowaniu sesji E1 (`DEFAULT_SPAWN_ENEMY`), więc według D15/D30 jego aktywacje i taktyki są w zakresie;
  - w argumentach `EntityName` gra podaje tylko formę pojedynczą nazwy wroga, u bossa z aliasem w nawiasie;
  - zmienne tekstowe (`VariableString`, część `LocalizationKey`) dostają klucze ustawiane w grafach (`SetStringKey`) albo imiona bohaterów; inwentarz wartości liczymy dla każdej zmiennej osobno;
  - `{n}` w `DEFAULT_SPAWN_ENEMY_MULTI` to lista wszystkich argumentów;
  - wartości luk mają jedno tempo 1,2 (krótki fragment według D34), więc te same nazwy i liczby nie mnożą się przez tempo kwestii;
  - 13 kwestii ma luki znane dopiero w grze (łup `RawText`, listy kluczy, teksty spoza grafów); companion obsłuży je syntezą na żywo albo pominie lukę (E4);
  - zwykły rzeczownik po luce liczbowej zostaje w formie z szablonu; odmieniają się liczebnik i ikony.

## Otwarte kwestie

Kwestie a–u są rozstrzygnięte po porównaniu modeli (D33–D38), x i y w D30 i D31.

| # | Kwestia | Stan |
|---|---|---|
| z | Crash przy wyjściu do pulpitu z loaderem (`mono_jit_cleanup`) | usunięty poprawką MonoMod (D54): test D i wyjście po sesji E5 bez crasha; na Macu sprawdzimy w E6 |
| – | Odczyt aktualizacji celu z licznikiem i nagrania liczników | ustalony w D64, wykonanie w E7 |
| – | Opis misji na mapie: nowe źródło w pluginie | E7 (D55) |
| – | Własny punkt wejścia Doorstop przed startem Unity | działa na Windows (test W1, D58); na Macu sprawdzimy w sesji E6, odłożonej (D61) |
| – | Model dla całej gry | E7 na OmniVoice (D65); cała gra przy większym zakresie (D39) |
| – | `VARIABLE_HERO` bez testu w grze | w sesji E5 |
| – | Wydanie paczek w GitHub Releases | E10 (D76) |
