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

## Ustalenia z analiz (fakty, na których opierają się decyzje)

- Unity Audio jest wyłączone w obu buildach (`globalgamemanagers` → `AudioManager.m_DisableAudio = true`), a dźwięk gra obsługuje przez Wwise. Odtwarzanie przez `AudioSource` w grze nie zadziała bez obejść.
- RTF na GTX 1650 Ti wynosi ok. 2,2 (`analysis/BENCH.md`). Generowanie na żywo nie zmieści się w 2–3 s, więc kwestie trzeba pregenerować albo brać z cache.
- Build macOS ma identyczne teksty, audio i klasy hooka jak Windows. Doorstop przez `DYLD_INSERT_LIBRARIES` wymaga przepodpisania pakietu (`analysis/MAC_REPORT.md`).
- Milestone 1 nie potrzebuje głosów NPC (mówi tylko Ne’Krul), ale potrzebuje głosu systemowego od razu: 255 kluczy (`analysis/M1_SCOPE.md`).

## Otwarte kwestie

W nawiasie podana jest wstępna rekomendacja. Rozstrzygnięte kwestie przenosimy wyżej jako decyzje D…

### Głos i styl

| # | Kwestia | Wstępna rekomendacja | Odsłuch |
|---|---|---|---|
| a | Wariant TTS | fp16, cfg_weight 0,3 | tak |
| b | Tempo: synteza jest ok. 30% szybsza od lektora | u narratora dłuższe pauzy między zdaniami (0,35–0,5 s) i test time-stretch 0,9 na ok. 10 próbkach; bohaterowie bez zmian | tak |
| c | Exaggeration według kategorii | narracja 0,4, dialog 0,5, okrzyki i walka 0,7, systemowy 0,3; korekta po odsłuchu | tak |
| d | Narrator i Galaden brzmią prawie tak samo | zostawić, prawdopodobnie to ten sam aktor; ewentualna korekta po teście przy stole | – |
| e | Głos systemowy | na M1 tymczasowo narrator w neutralnym stylu; równolegle szukamy gotowego głosu z licencją pozwalającą na klonowanie | tak |
| f | Opcje wyboru z cytowanymi wypowiedziami | głos systemowy | – |
| g | Przełączniki kategorii w companionie (np. wyłączanie podpowiedzi samouczka albo reguł) | tak, domyślnie wszystko włączone | – |
| u | Wymowa nazw własnych | słownik wymowy (zapis fonetyczny) uzupełniany po odsłuchu i kontroli ASR | – |

### Treść i zakres

| # | Kwestia | Wstępna rekomendacja |
|---|---|---|
| h | Kwestie z `{n}` | pregenerować wartości, które da się wyliczyć (bohaterowie, wrogowie Q1, liczby 0–20); do tego cache i generowanie na żywo jako fallback |
| i | Sloty `VARIABLE_HERO*` | 6 wariantów audio na kwestię |
| j | CUTSCENE_01 i pozostałe przerywniki z oryginalnym dubbingiem (115 kluczy napisów, 17 nagrań) | bez TTS |
| k | Poszerzenie M1 | dodać scenę „Welcome Home” po Q1; losowych wrogów ustalić z logu sesji testowej; SQ1 później |
| l | Złoczyńcy | Ne’Krul już w M1, pozostali później; przy słabym klonie gotowy głos o podobnym charakterze |
| m | Źródło gotowych głosów NPC | decyzja przed skalowaniem; nie klonujemy głosów osób bez ich zgody |
| v | Krótkie cytaty z gry w `analysis/REPORT.md` | do decyzji: zostawić albo zastąpić kluczami i opisem |
| w | Szacunki czasu w `analysis/REPORT.md` zakładają tempo 15 znaków/s | do decyzji: poprawić według `VOICES.md` i `BENCH.md` |

### Technika

| # | Kwestia | Wstępna rekomendacja |
|---|---|---|
| n | Odtwarzanie: zewnętrzny companion czy w grze | companion; Unity Audio jest wyłączone |
| o | Loader na Windows | BepInEx 5 x86, bez zmian w plikach gry; nie `RuntimeInitializeOnLoads.json`, bo Steam go nadpisze |
| p | Wyciszanie muzyki gry pod lektorem | później; w M1 bez |
| q | NVIDIA „CUDA – Sysmem Fallback Policy” | „Prefer No Sysmem Fallback” tylko dla `python.exe` z `.venv`, nie globalnie |
| r | Kryteria zaliczenia testu | co najmniej 98% okien M1 ma audio; start pregenerowanej kwestii poniżej 0,5 s od wyświetlenia okna |
| s | Mac: Doorstop wymaga przepodpisania pakietu | do decyzji: przepodpisana kopia `.app` poza folderem Steam albo zmiana oryginału |
| t | Mac: uruchamianie companiona (Python i zależności na cudzym Macu) | do decyzji: przenośna paczka w jednym folderze bez instalacji systemowej albo instalacja Pythona |
