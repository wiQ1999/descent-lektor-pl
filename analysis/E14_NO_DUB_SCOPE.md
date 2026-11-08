# E14 · Postacie bez dubbingu w całej grze: zakres i koszt ElevenLabs

Pytanie: ile kwestii postaci bez polskiego dubbingu zostało poza M2 i ile kredytów ElevenLabs zużyje ich synteza. Raport podaje identyfikatory mówców i liczby. Kwestie z tekstem leżą w `analysis/work/out/no_dub_lines.jsonl`, a podsumowanie w `no_dub_summary.json` (nieśledzone).

## Metoda

- `analysis/tools/no_dub_scope.py` czyta wszystkie 2288 grafów gry bez scen deweloperskich (`Enemy Tool`, `Obstacle Course`).
- Kwestia postaci to klucz okna fabularnego z mówcą (jak `scope.voice_for`). Klucz z bohaterem, `VARIABLE_HERO`, Ne’Krulem albo Xenith czyta OmniVoice, więc tu nie wchodzi. Klucz z kilkoma mówcami bez dubbingu liczy się u pierwszego.
- Tekst przechodzi tę samą normalizację co fragmenty M2 (`normalize`, `pronounce`). Znaki liczą się po deduplikacji tekstu w obrębie postaci.
- Klucze z bazy M2 odpadają (148 kluczy).
- Kontrola na M2: metoda daje 11 516 znaków wobec 11 069 we fragmentach ElevenLabs M2, czyli ok. 4% więcej (dzielenie długich kwestii i deduplikacja fragmentów). Szacunek jest więc raczej górny.
- Koszt: 0,44 kredytu na znak `eleven_v4` (E9, E11, E13), ponowne podejścia +7% (E13), tempo 13,95 znaku na sekundę (E13).

## Wynik

1262 fragmenty, 129 128 znaków, 39 mówców. To ok. 2,5 h audio.

| Grupa | Mówcy | Fragmenty | Znaki | Akt 1 | Akt 2 | Kredyty | Z ponownymi | Audio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| głosy ElevenLabs z E13 | 11 | 280 | 25 145 | 8 665 | 16 480 | 11 064 | 11 838 | 30 min |
| nowe postacie | 19 | 724 | 76 434 | 7 990 | 68 444 | 33 631 | 35 985 | 91 min |
| złoczyńcy z okrzykami dubbingu | 9 | 258 | 27 549 | 6 202 | 21 347 | 12 122 | 12 970 | 33 min |
| **razem** | **39** | **1 262** | **129 128** | **22 857** | **106 271** | **56 816** | **60 793** | **154 min** |

- Złoczyńcy z okrzykami mają w grze tylko klipy z planszy (`Voice_Villains_Act1/Act2`, 3–7 s mowy na postać, `VOICES.md`). Tak samo było u Ne’Krula i Xenith, których sklonowaliśmy w OmniVoice (D19).
- Akt 1 poza M2 (22,9 tys. znaków): scenariusze Q2, Q4, Q5, Q9, Q10, Q11 i Q14, zakończenie SQ1, wydarzenia (2A–13A, Pre9A) i sceny fabularne. Q3, Q8, Q12, Q13 i SQ2 nie mają kwestii postaci bez dubbingu poza M2.
- Akt 2 (106,3 tys.): sceny scenariuszy `dle04` Q1–Q11 ze wstępami, zakończeniami i podróżami, wydarzenia `SE` i sceny `SS`.
- Tylko 1 kwestia ma lukę `{n}`.

### Mówcy

| Mówca | Grupa | Fragmenty | Znaki | Akt 1 | Akt 2 | Kredyty |
|---|---|---:|---:|---:|---:|---:|
| `BARONESSMAGRIT` | nowa | 140 | 15 210 | 2 967 | 12 243 | 6 692 |
| `ALYS` | nowa | 95 | 10 515 | 0 | 10 515 | 4 627 |
| `BARONZACHARETH` | złoczyńca | 74 | 7 585 | 2 940 | 4 645 | 3 337 |
| `RENEYR` | złoczyńca | 68 | 7 521 | 0 | 7 521 | 3 309 |
| `GREIGORY` | nowa | 64 | 6 609 | 0 | 6 609 | 2 908 |
| `BUTTON` | nowa | 60 | 5 596 | 0 | 5 596 | 2 462 |
| `LAUREL` | nowa | 62 | 4 919 | 2 179 | 2 740 | 2 164 |
| `ARDEN` | nowa | 38 | 4 678 | 0 | 4 678 | 2 058 |
| `RONAN` | E13 | 53 | 4 626 | 2 137 | 2 489 | 2 035 |
| `MASTERBRULI` | E13 | 54 | 4 523 | 2 467 | 2 056 | 1 990 |
| `VETA` | nowa | 38 | 4 405 | 0 | 4 405 | 1 938 |
| `TREVALYN` | nowa | 37 | 4 147 | 0 | 4 147 | 1 825 |
| `MASTERGALGORAZ` | E13 | 46 | 4 098 | 0 | 4 098 | 1 803 |
| `SIRBALTHAIN` | nowa | 38 | 4 002 | 1 195 | 2 807 | 1 761 |
| `COUNTESSDUCARD` | nowa | 38 | 3 909 | 594 | 3 315 | 1 720 |
| `ASTARRA` | E13 | 33 | 3 012 | 929 | 2 083 | 1 325 |
| `GREYSDON` | złoczyńca | 27 | 2 786 | 2 786 | 0 | 1 226 |
| `NAVOTH` | złoczyńca | 25 | 2 771 | 0 | 2 771 | 1 219 |
| `WAIQAR` | nowa | 23 | 2 666 | 1 055 | 1 611 | 1 173 |
| `MORANT` | nowa | 22 | 2 596 | 0 | 2 596 | 1 142 |
| `LEVIRAX` | złoczyńca | 23 | 2 583 | 476 | 2 107 | 1 137 |
| `ELDERMOK` | E13 | 23 | 2 310 | 0 | 2 310 | 1 016 |
| `GILLIAM` | złoczyńca | 15 | 1 966 | 0 | 1 966 | 865 |
| `PRYOR` | nowa | 10 | 1 840 | 0 | 1 840 | 810 |
| `MASTERFLINT` | E13 | 19 | 1 832 | 501 | 1 331 | 806 |
| `BARONESS_ADELYNN` | E13 | 17 | 1 710 | 1 710 | 0 | 752 |
| `DELPHYNDRA` | nowa | 16 | 1 675 | 0 | 1 675 | 737 |
| `NARA` | nowa | 15 | 1 562 | 0 | 1 562 | 687 |
| `GILLIAM_EVIL` | złoczyńca | 10 | 1 355 | 0 | 1 355 | 596 |
| `GRACE` | nowa | 11 | 1 237 | 0 | 1 237 | 544 |
| `LTRAND` | E13 | 14 | 1 199 | 581 | 618 | 528 |
| `KATHRYN` | E13 | 12 | 1 120 | 151 | 969 | 493 |
| `VRASKHAR` | złoczyńca | 10 | 821 | 0 | 821 | 361 |
| `HERBIE` | E13 | 5 | 526 | 0 | 526 | 231 |
| `MEZA` | nowa | 4 | 448 | 0 | 448 | 197 |
| `DRYS` | nowa (bez modelu postaci) | 3 | 244 | 0 | 244 | 107 |
| `OUTLAWPRINCE` | E13 | 4 | 189 | 189 | 0 | 83 |
| `CHANCE_SHADOW` | nowa (cień Fuksa) | 10 | 176 | 0 | 176 | 77 |
| `SHADOW_RENEYR` | złoczyńca (cień Reneyra) | 6 | 161 | 0 | 161 | 71 |

## Koszt z projektowaniem głosów

Projekt głosu jak w E11 (3 różne opisy, `text_to_voice`, 3 podglądy na opis) kosztował ok. 525 kredytów na postać (E11: 5763 kredyty na 11 postaci). Warianty mówców `GILLIAM_EVIL`, `SHADOW_RENEYR` i `CHANCE_SHADOW` mogą korzystać z głosu postaci bazowej, więc nowych głosów jest 18 (nowe postacie) i 7 (złoczyńcy).

| Wariant | Znaki | Synteza z ponownymi | Projekt głosów | Razem | Głosy na koncie |
|---|---:|---:|---:|---:|---:|
| A: ElevenLabs bez złoczyńców (złoczyńcy w OmniVoice jak Ne’Krul) | 101 579 | ok. 47,8 tys. | 18 × 525 ≈ 9,5 tys. | **ok. 57 tys.** | 12 + 18 = 30 z 30 |
| B: wszystko w ElevenLabs | 129 128 | ok. 60,8 tys. | 25 × 525 ≈ 13,1 tys. | **ok. 74 tys.** | 12 + 25 = 37 z 30 |
| tylko akt 1, wariant A | 16 655 | ok. 7,8 tys. | 5 × 525 ≈ 2,6 tys. | ok. 10,5 tys. | 12 + 5 |

- Konto (2026-11-08): plan Creator, 127 047 kredytów na okres, zużyte 39 926, zostało 87 121 do resetu 2026-11-15. Oba warianty mieszczą się w jednym okresie.
- Plan Creator ma 30 miejsc na głosy, zajętych 12 (11 postaci i test Kehli). Wariant A zajmuje wszystkie. Wariant B wymaga zwolnienia 7 miejsc albo wyższego planu.
- To szacunek samych postaci bez dubbingu. Narrator, bohaterowie i złoczyńcy z dubbingiem w całej grze to OmniVoice na GPU (ok. 110 h dla całej gry wg E7, bez kredytów).
