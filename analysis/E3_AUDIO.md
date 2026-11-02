# E3: audio M1

Wygenerowano przez `python -I -m lektor audio-report`. Model `omnivoice-08be0b4-fp32-s32-cfg2.0`, GTX 1650 Ti. Raport zawiera tylko liczby i klucze techniczne.

## Czas generowania

Podejść: **1205** (93049 znaków, 126.0 min audio). Czas GPU: **5.0 h**, czyli **0.193 s na znak** i RTF 2.38 (mediana RTF podejść 2.56). Szczyt VRAM: 3.10 GB.

| znaki fragmentu | podejścia | średnio s | s na znak |
|---|---|---|---|
| 0–29 | 314 | 9.8 | 0.610 |
| 30–79 | 400 | 12.1 | 0.228 |
| 80–159 | 370 | 18.4 | 0.160 |
| 160– | 121 | 26.7 | 0.134 |

Na znak tekstu M1 (z podejściami bohaterów i ponownymi): 0.235 s. Cała gra (D02, ok. 1.43 mln znaków) w tych samych proporcjach: ok. **93 h** GPU (D39; przed przyspieszeniami ok. 610 h na jedno podejście).

## Automat (D38)

Fragmentów: **978**. Z ponownym podejściem: 39. Bez zaakceptowanego podejścia po ponownym: **13** (cer 9, koncowka 7, zgubiony_fragment 1, tempo 1).

| głos | fragmenty | podejścia ocenione | CER wybranych (mediana) | barwa (mediana) | odrzucone |
|---|---|---|---|---|---|
| adelynn | 12 | 13 | 0.006 | 0.933 | 1 |
| brynn | 27 | 82 | 0.000 | 0.917 | 0 |
| chance | 1 | 3 | 0.000 | 0.944 | 0 |
| galaden | 19 | 57 | 0.000 | 0.924 | 0 |
| kehli | 2 | 6 | 0.011 | 0.920 | 0 |
| narrator | 869 | 908 | 0.000 | 0.927 | 10 |
| nekrul | 1 | 2 | 0.043 | 0.883 | 1 |
| ronan | 4 | 4 | 0.003 | 0.928 | 0 |
| syrus | 28 | 84 | 0.000 | 0.930 | 0 |
| vaerix | 15 | 46 | 0.000 | 0.896 | 1 |

## Odsłuch

Ocenionych fragmentów: 61 (ok 54, wymowa 2, inne 2, tresc 2, tempo 1). Fragmenty z uwagami liczą się niżej jako niezaakceptowane; decyzje i uwagi na kolejne generowania: D43.

## Pokrycie M1

Klucze do syntezy z zaakceptowanym audio wszystkich fragmentów: **627 / 635 (98.7%)**. Wartości luk z zaakceptowanym audio: 1908 / 1908.
