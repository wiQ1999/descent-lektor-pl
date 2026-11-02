# E4 · Companion i integracja (Windows)

Raport bez treści gry: klucze, liczby i czasy. Dzienniki companiona (`%LOCALAPPDATA%\LektorPL\logs\companion-*.jsonl`) i wyniki replayu (`analysis/work/companion/`) zawierają tylko klucze, liczby i czasy.

## Podsumowanie

| Kryterium (PLAN, D13) | Wynik | Stan |
|---|---|---|
| Replay logu E1: audio dla ≥ 98% okien | 332 z 337 okien z treścią do przeczytania (98,5%), bez 6 okien samego łupu (D50); wszystkich okien 332 z 343 (96,8%) | tak |
| Start < 0,5 s według logu | p50 0,120 s, p95 0,149 s, max 0,201 s (312 startów) | tak |
| Przerwanie < 0,3 s według logu | p50 0,114 s, p95 0,126 s, max 0,131 s (294 przerwania) | tak |
| Testy jednostkowe | 111 testów, w tym 23 companiona | tak |

## Co powstało

**Plugin 0.2.0** (`src/plugin`):
- `Sender`: wysyła każdą linię dziennika do companiona przez TCP na 127.0.0.1:47810, jako JSON lines.
  - Gniazdo jest nieblokujące i obsługiwane w `LateUpdate`, bez dodatkowych wątków (D40).
  - Połączenie jest ponawiane co 2 s. Bez połączenia zdarzenia przepadają.
- Nowe zdarzenia:
  - `objective`: cel misji z `UIGame._lastObjectiveKey`, jego argumenty i tekst etykiety (D31);
  - `open`/`close` z `kind: activation`: aktywacja wroga z `GameController._curEnemyActivation`, z kluczem i argumentami komunikatu oraz modelem wroga (D30).
- Przy wyjściu plugin odpina subskrypcje i zamyka połączenie. Port można zmienić w `Companion.Port` w konfiguracji BepInEx (0 wyłącza wysyłkę).

**Companion** (`src/lektor/companion`, zależności: numpy, soundfile, sounddevice):

| Moduł | Rola |
|---|---|
| `library` | klucz → fragmenty audio z pauzami |
| `director` | zasady odtwarzania: przerywanie, kolejka, wybory, przełączniki, pomiar opóźnień |
| `player` | jeden strumień sounddevice (D47), przerwanie z wyciszeniem w 10 ms; wariant bez dźwięku do replayu |
| `app` | serwer TCP, replay dzienników (bezpośrednio albo przez TCP), dziennik i podsumowanie |
| `config` | `%LOCALAPPDATA%\LektorPL\companion.toml`: port, ścieżki, głośność, urządzenie, przełączniki (D21) |

Jak `library` składa wypowiedź:
- **luki `{n}` (D16):** klucz z argumentu bez `<sprite=N>`, a u bossa alias w nawiasie;
- **znacznik `<EntityName>`:** nazwa wroga dopasowana po tekście;
- **wartość będąca kwestią:** odtwarzane jest audio tej kwestii;
- **lista wszystkich argumentów:** wartości oddzielone pauzą 0,15 s;
- **zapas:** wyszukiwanie po znormalizowanym tekście;
- **wariant aktywacji bez nazwy:** zamiana jak w grze;
- **wzmocnienie kategorii z manifestu (D04):** `walka_teren` +2 dB.

Zasady `director` (D03, D20, D45, doprecyzowane w D48):
- okno przerywa poprzednie;
- odpowiedź z wyboru gra do końca, a następne okno na nią czeka;
- cel i aktywacja czekają na 0,35 s ciszy po zdarzeniach okien;
- zamknięta aktywacja wypada z kolejki, a nowszy cel zastępuje starszy;
- cel odczytany już w oknie nie gra drugi raz.

**Skrypty:**
- `src/plugin/install/lektor-companion.ps1`: start companiona przed grą (D46);
- `lektor-hook.ps1 -Install -LoaderOnly`: sam BepInEx, do testu wyjścia;
- instrukcja: [docs/E4_EXIT_TEST.md](../docs/E4_EXIT_TEST.md) (D40).

Fallback na żywo zostaje na E6, po pomiarze na M5 (D44). Treść bez nagrania jest pomijana i logowana.

## Pokrycie: replay dzienników E1

Replay obejmuje oba dzienniki sesji E1, w sumie 15 min gry:
- 199 okien wiadomości;
- 144 okna fabularne;
- 36 wybranych opcji.

Okna z przerywnikami (D14) nie wystąpiły.

| Wynik | Okna | Uwagi |
|---|---|---|
| pełne audio | 329 | 144 fabularne + 185 wiadomości |
| audio bez jednej luki | 3 | `TACTIC_PHASE_DESCRIPTION` ×2, `…_DARK_PRAYER` ×1: wartość znana dopiero w grze (bonus z błyskotki) |
| okno samego łupu | 6 | `DEFAULT_GET_TREASURE_SINGLE`: cała treść to `{0}` i `{1}` (D44) |
| brak klucza w bazie | 5 | `DEFAULT_GET_TREASURE_MULTI` ×4, `TRAVEL_57` ×1 |
| odpowiedzi z wyboru | 36 z 36 | wszystkie z audio |

Pokrycie wynosi 332 z 343 okien, czyli 96,8%. Bez okien samego łupu jest to 332 z 337, czyli 98,5%.

### Przyczyny braków

- **Okna łupu** (`DEFAULT_GET_TREASURE_SINGLE` i `_MULTI`) mają dwie luki:
  - `{0}`: klucz zwykłej kwestii ustawiany w węźle łupu (np. `CHEST_ITEM_FIND_3`, `TREE_CHOICE_MOSS_SELECT`, `XP_GAIN_1_KEHLI_CHANCE`);
  - `{1}`: lista łupu, którą gra składa sama (`RawText`).

  Klucze z `{0}` są w zakresie M1 z analizy (`M1_SCOPE.md`), ale budowanie bazy E2 ich nie znalazło. Inwentarz wartości luk czyta przypisania w grafach (`SetStringKey`), a nie parametry węzłów łupu.
- Takich kluczy zakresu M1 bez kwestii i bez wartości w bazie jest najwyżej 87, razem 9,1 tys. znaków (ok. 25 min GPU). Należą do nich też wyniki testów przy studni i kotle oraz opisy rogu odwagi. Część to opisy przedmiotów, które nie trafiają do okien.
- `DEFAULT_GET_TREASURE_MULTI` i `TRAVEL_57` (zdarzenie podróży na mapie) E1 oznaczyło jako spoza M1. E2 ich nie dodało.

## Opóźnienia (D13)

Pomiar obejmuje replay w czasie rzeczywistym przez TCP, z odstępami jak w sesji E1. Wyjście audio jest prawdziwe (sounddevice, MME, domyślne urządzenie) i wyciszone w konfiguracji. Czas startu liczymy od odbioru zdarzenia do szacowanego wyjścia pierwszej próbki z przetwornika (`outputBufferDacTime`), a przerwanie od odbioru zdarzenia do wyciszenia.

| Pomiar | n | p50 | p95 | max |
|---|---|---|---|---|
| start okna (od zdarzenia) | 312 | 0,120 s | 0,149 s | 0,201 s |
| przerwanie (nowe okno albo zamknięcie) | 294 | 0,114 s | 0,126 s | 0,131 s |
| start z kolejki (cel, aktywacja, okno po odpowiedzi z wyboru), od chwili zwolnienia | 19 | 0,124 s | 0,144 s | 0,144 s |

- Większość czasu to bufor wyjścia MME: 0,107 s według `sounddevice`, plus blok 512 próbek (21 ms).
- Przygotowanie wypowiedzi (wyszukanie i sklejenie fragmentów, odczyt WAV) trwa p50 1,4 ms, p95 28 ms.
- Jeśli w E5 zabraknie zapasu, WASAPI powinno skrócić bufor wyjścia.

W sesji E1 okna były przeklikiwane bez lektora, więc 287 z 332 okien zamknięto przed końcem ich audio. W replayu to głównie test przerwań. Rzeczywisty odsetek przerwanych odczytów pokaże E5.

Opóźnienie pluginu (od `MessageDisplayBegin` do wysłania okna, `t - begin_t`): p95 0,002 s, max 0,032 s.

Pierwsze okno po starcie czekało 0,25 s na import biblioteki audio i pierwszy odczyt z dysku. Companion robi teraz tę rozgrzewkę przy starcie.

## Decyzje i co dalej

- **Braki bazy M1:** pominięte. Od kolejnych scenariuszy nagrywamy wszystkie kwestie, a inwentarz czyta też parametry węzłów łupu i testów (D49).
- **Kryterium pokrycia:** liczone bez okien samego łupu (D50).
- **Lista łupu:** od E7 składana z pregenerowanych fragmentów (D51).
- **E5:**
  - najpierw dwa testy wyjścia według [docs/E4_EXIT_TEST.md](../docs/E4_EXIT_TEST.md) (D40);
  - potem sesja M1 z lektorem według [docs/E5_PLAYTEST.md](../docs/E5_PLAYTEST.md).
