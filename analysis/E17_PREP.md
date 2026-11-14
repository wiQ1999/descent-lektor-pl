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
- Mówcy bez imienia mają własne głosy ElevenLabs (`nv_*`, QA 2026-11-14). Dotyczy to także 19 głosów testowych t1, które w t1 były projektami OmniVoice.

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

## Nowe głosy ElevenLabs

- 99 głosów `nv_*`: 80 nowych z przeglądu i 19 z t1. Opisy do projektu głosu: `analysis/tools/voice_designs_prod.json` (`brief` po polsku z kontekstu wszystkich kwestii postaci, `el` dla `text_to_voice`).
- Tekst do nagrania: 448 fragmentów, 35 175 znaków.
  - Głosy z najwyżej 100 znakami: 32.
  - Głosy z najwyżej 300 znakami: 66.
  - Głosy z ponad 1000 znakami: 11. Najwięcej mają `nv_fof_kapitan`, `nv_q13_smok`, `nv_sq1_wyslannik` i `nv_ocella`.
- Do czasu projektu `eleven` pomija głosy bez `voice_id` i podaje ich liczbę znaków (`direction.ELEVEN_VOICES_PROD`).

## Szacunek generowania

Stan po przejęciu nagrań z t1 i m3 (`synth.inherit`, `synth.adopt`):

- Przejęte wybory z t1 i m3: 7289 fragmentów. Wybór OmniVoice z t1 dla głosu, który w m4 ma ElevenLabs, nie przechodzi.
- Przejęte podejścia OmniVoice z m3 bez oceny: 2058. Ocena i wybór policzą je jak własne.
- OmniVoice: zostało ok. 1,27 mln znaków podejść (bohaterowie po 3 podejścia), ok. 62 h GPU (`progress --release m4`).
  - Większość to akt 2, którego m3 nie wygenerowało (akt 2: 190 z 1028 tys. znaków).
  - Drugą część stanowi narrator w jednym tempie.
- ElevenLabs:

| Część | Podejścia | Znaki | Kredyty (szacunek) |
|---|---:|---:|---:|
| głosy obsady (28) | 1168 | 109 738 | ok. 48 300 |
| w tym nowe wypowiedzi z okien narratora | | ok. 22 000 | ok. 9 700 |
| nowe głosy `nv_*` (99) | 448 | 35 175 | ok. 15 500 |
| razem przed ponownymi podejściami | 1616 | 144 913 | ok. 63 800 |

- Do tego projekt 99 głosów (podglądy `text_to_voice`) i ponowne podejścia (w E14 ok. 10%).
- Plan Creator ma 30 miejsc na głosy (`E14_NO_DUB_SCOPE.md`). Obsada ElevenLabs zajmuje co najmniej 28 (`direction.ELEVEN_VOICES`), więc 99 nowych głosów się nie zmieści.

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
