# E17: przygotowanie wersji produkcyjnej (m4)

Stan na 2026-11-14 po zakończeniu testów t1 (D101–D106). Raport podaje klucze, nazwy i liczby, bez tekstów gry. Liczności bazy są w `analysis/E17_DATA.md` (`report --release m4`).

## Co obejmuje m4

- Zakres i reguły bazy całej gry `m3` (`paths.BASE`).
- Reguły z testów t1 obowiązują w całej grze (`scope.T1_RULES`):
  - głosy postaci w oknach narratora (D101, D102), także w kwestiach postaci z wtrąceniem narratora (D105);
  - jedno tempo narratora `SPEED_MAX` poza narracją scen, także w lukach, łupie i nazwach wyzwań (`direction.ONE_TEMPO`);
  - okno ataku: zdolności i obrona wroga (`abilities.records`).
- Reguły bazy z t1, które już działały w całej grze: ikony i glify (D103), podglądy z kodu gry (D103), przeczenie, nazwy unikalnych wrogów (D105), nazwy wyzwań (D106).
- Opcje wyboru z półpauzą czyta narrator, jak w t1 (QA 2026-11-14).
- Mówcy bez imienia mają własne głosy (`nv_*`, QA 2026-11-14) z modelu lokalnego OmniVoice: 19 z t1 i 80 nowych z profili postaci.

## Przegląd mówców w oknach narratora

- Okna z wypowiedzią poza zakresem t1: 915 (`analysis/tools/speakers_digest.py`). Każde przejrzane ręcznie z kontekstem okna.
- Propozycja automatu była błędna albo pusta w 519 oknach. Typowe przyczyny:
  - imię adresata przed wypowiedzią („przed”) zamiast mówcy;
  - brak imion postaci spoza listy `speakers.NAMES` (np. Meza, Xenith, Laurel, Greysdon);
  - wypowiedź gracza („mówisz”) i bohatera z luki `{N}`.
- Wynik: `src/lektor/data/speakers_prod.json`, 1041 okien (915 nowych i 122 z t1, część wspólna). Plik buduje `analysis/tools/speakers_freeze.py` z propozycji automatu i poprawek (`analysis/work/out/prod/corrections.txt`). Skrypt sprawdza liczbę głosów wobec wypowiedzi i znane głosy.
- Zasady przyjęte w przeglądzie:
  - list albo napis w cudzysłowie bez autora przed cytatem czyta narrator (21 okien, m.in. podpisane listy `SQ2_WAIQAR_1`, `A2Q08_LECTERN_DESTROYED`);
  - wypowiedź gracza bez imienia czyta narrator;
  - bohater wskazany luką mówi głosem bohatera z argumentu okna (`arg:N`);
  - typ wroga (np. siostra krwi) ma jeden głos dla wszystkich egzemplarzy;
  - wtrącenie w środku wypowiedzi bez czasownika mówienia („– pierścień, amulet i szyfr –”) czyta mówca (`{"pieces": …}`, np. `A2Q11_SYRUS_PUZZLING`).
- Głos z Ynfernaelu z t1 (`nv_ynfernael`) to Baelziffar, demon z Q9. W m4 oba mają głos `nv_baelziffar`.

## Nowe głosy mówców bez imienia

- 99 głosów `nv_*`: 80 nowych z przeglądu i 19 z t1. Profile: `analysis/tools/voice_designs_prod.json` (`brief` po polsku z kontekstu wszystkich kwestii postaci, `omni` z projektem OmniVoice, `el` jako zapas dla ElevenLabs).
- Tekst do nagrania: 448 fragmentów, 35 175 znaków.
  - Głosy z najwyżej 100 znakami: 32.
  - Głosy z najwyżej 300 znakami: 66.
  - Głosy z ponad 1000 znakami: 11. Najwięcej mają `nv_fof_kapitan`, `nv_q13_smok`, `nv_sq1_wyslannik` i `nv_ocella`.
- Najpierw planowaliśmy ElevenLabs. Profilu głosu ElevenLabs nie da się jednak odtworzyć z opisu ani z ziarna, a 99 głosów nie mieści się w 30 miejscach planu Creator. Głosy nagrywa więc model lokalny (decyzja użytkownika 2026-11-14).
- Projekt OmniVoice (`analysis/tools/new_voices_prod.py`): profil to płeć, wiek, wysokość i szept oraz własne zdanie w stylu postaci. Każdy profil ma trzy ziarna. Automat wybiera ziarno z najmniejszym CER i wysokością w zakresie płci, a z dobrych to, które leży najdalej od narratora, obsady i głosów wybranych wcześniej.
- Wynik projektu (2026-11-15):
  - Dwa profile w pierwszym projekcie dały złą mowę na wszystkich ziarnach: `nv_q9_blizniaki` (CER 6,35) i `nv_ta2_kupiec` (CER 0,85). Po zmianie zdania i wysokości oba przeszły z CER 0.
  - Cztery głosy były za blisko innych: `nv_crayleth` 0,956, `nv_q14_zolnierka` 0,944 (do Adelynn), `nv_gravia` 0,940 i `nv_sq1_wiedzma` 0,937. Dostały siedem ziaren. Podobieństwo spadło do 0,943, 0,809, 0,930 i 0,930.
  - Najbliższe pary po wyborze: `nv_kowalka`~`nv_crayleth` 0,943, `nv_gont`~`nv_crayleth` 0,934, `nv_nekromanta`~`nv_a2q8_zamiatacz` 0,933. W t1 za bliskie uznaliśmy 0,949.
  - Głosy, referencje i liczby fragmentów: `docs/CASTING.md` (E17).

## Szacunek generowania

Stan po przejęciu nagrań z t1 i m3 (`synth.inherit`, `synth.adopt`):

- Przejęte wybory z t1 i m3: 7289 fragmentów. Wybór OmniVoice z t1 dla głosu, który w m4 ma ElevenLabs (obsada E13 i E14), nie przechodzi.
- Przejęte podejścia OmniVoice z m3 bez oceny: 2058. Ocena i wybór policzą je jak własne.
- OmniVoice, razem z głosami `nv_*`: 15 758 podejść, 1,28 mln znaków (bohaterowie po 3 podejścia), ok. 65–75 h GPU. Generowanie trwa od 2026-11-15 (`progress --release m4`).
  - Większość to akt 2, którego m3 nie wygenerowało (akt 2: 190 z 1028 tys. znaków).
  - Drugą część stanowi narrator w jednym tempie.
- ElevenLabs:

| Część | Podejścia | Znaki | Kredyty (szacunek) |
|---|---:|---:|---:|
| głosy obsady (28) | 1168 | 109 738 | ok. 48 300 |
| w tym nowe wypowiedzi z okien narratora | | ok. 22 000 | ok. 9 700 |

- Limit to 60 tys. kredytów, jak limit klucza API (`MAX_CREDITS`). Ok. 48 tys. przed ponownymi podejściami mieści się w nim z zapasem ok. 12 tys. na ponowne podejścia (w E14 ok. 10%).

## Kontrola tekstów całej gry

Skan fragmentów m4 (glify PUA, znaczniki `TERM_`, luki `{}`, nawiasy, wersaliki, cyfry):

- Glify i znaczniki: brak.
- Poprawione w normalizacji: kafel z literą przed numerem (`Q8_DROP_ACID`, „B13”) i nawias bez pary po urwanym znaczniku gry (`BOOKSHELF_CHOICE_BAUBLES_FALSE_07`).
- Zostają, jak w m3:
  - liczebniki rzymskie „Aktu II” (`A2Q00_SELECT_HEROES`) i „IV” (`TRAVEL_EVENT_A2_16_3`);
  - licznik `({0/3})` w `Q9_OBJECTIVE_1_UPDATED` (tak zapisany w grze);
  - kwestia deweloperska `Q3_DEBUG_SKIP_TO_HIDEOUT`;
  - wersaliki dla emfazy w mowie postaci. OmniVoice i ElevenLabs czytają je zwykłą pisownią (D85).
- Okna narratora z wypowiedzią, które zostają w całości narratorowi: 47 opcji wyboru (QA), 3 komunikaty misji z wypowiedzią gracza (`Q3_OCELLA_NO`, `SECRET_DOOR_TIME`, `A2Q03_SHADOW_OTHER`) i efekt kuszy Kehli (`WEAPON_ABILITY_C_CROSSBOW_4_EFFECT`, jak w t1).
