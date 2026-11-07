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
