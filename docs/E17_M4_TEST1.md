# E17: test paczki m4 w grze na Windows (D108)

Pierwszy test wersji produkcyjnej. Paczka ma akt 1 i części wspólne z regułami t1 w całej grze. Test sprawdza misje, których t1 nie obejmował. W nich padają nowe głosy w oknach narratora: mówcy bez imienia (`nv_*`), postacie ElevenLabs i złoczyńcy.

## Paczka

- `analysis/work/dist/Descent-Lektor-PL-win.zip`, commit 1597498, plugin 0.4.5, 11 839 fragmentów audio.
- `wersja.txt` w paczce powinien pokazać zakres „akt 1 i części wspólne” i commit 1597498.

## Przygotowanie

1. Rozpakuj paczkę w miejsce folderu `Descent-Lektor-PL` z testów t1.
2. Uruchom **Zainstaluj** z nowego folderu. Plugin jest ten sam co w ostatniej paczce t1, ale instalacja ustawi ścieżki do nowego folderu.
3. Uruchom grę i wczytaj **slot 4**: Q1, Q2, wydarzenie miejskie i 2A ukończone, dostępne Q3 i Q5. Slot 7 ma ten sam stan i może posłużyć za zapas.
4. Kopia wszystkich zapisów sprzed testu leży w `analysis/work/saves/snap-20261118/`.
5. Zrzuty zapisuj w `analysis/work/playtest/m4/` (`m1 - opis.png`, …), a dzienniki zostaw w `logs/` paczki.

## Co rozegrać i czego słuchać

Okna czytaj do końca, a po kwestii klikaj spokojnie.

### 1. Q3

30 okien narratora ma podział na głosy.

| kto mówi | głos | czego słuchać |
|---|---|---|
| Ocella | `nv_ocella` (OmniVoice, profil postaci) | 21 fragmentów, starsza kobieta; czy głos pasuje i czy brzmi tak samo w każdym oknie |
| Książę Banitów | `outlaw` (ElevenLabs) | wypowiedzi w oknach narratora tym samym głosem co w dialogach |
| herszt i bandyta przy skrzyni | `nv_q3_herszt`, `nv_q3_bandyta_skrzynia` | krótkie okrzyki, inny głos niż narrator |
| bohaterowie | dubbing | okrzyki w oknach narratora czyta bohater, a nie narrator |

### 2. Q5

40 okien narratora ma podział na głosy.

| kto mówi | głos | czego słuchać |
|---|---|---|
| Greysdon | `greysdon` (klon z okrzyków) | 51 fragmentów: zrozumiałość i końcówki |
| Astarra | `astarra` (ElevenLabs) | wypowiedzi w oknach narratora |
| bohaterowie | dubbing | Syrus ma tu najwięcej kwestii (82) |

### 3. Zawsze

- Narrator czyta wszystko w jednym tempie, także cele, łup i nazwy wyzwań.
- Okno ataku: opis zdolności broni i obrony wroga.
- Cel misji, który przeczytało już okno komunikatu, nie gra drugi raz.
- Wyzwanie ukończone: od razu „Wyzwanie ukończone!”, bohater i nazwa.

## Jeśli zostanie czas

Slot 8 to kampania znajomego z dostępnymi Q7 i Q8. Q7 ma 40 okien z podziałem (Meza, Xenith, mówcy z Lisbeth `nv_lisb_*`), a Q8 19 okien (Bruli, Ne’Krul). Po teście slot 8 można przywrócić z kopii.

## Odsłuch głosów

Zestawienie wszystkich 85 głosów aktu 1 z opisem, portretem i dwiema próbkami: `analysis/work/compare/m4_cast/index.html` (`analysis/tools/cast_sheet.py`). Zaznacz głosy do zmiany i wklej listę do czatu.

## Po sesji

Napisz, że skończyłeś. Przeanalizuję dzienniki `hook-*.jsonl` i `companion-*.jsonl` z `logs/` paczki oraz zrzuty.
