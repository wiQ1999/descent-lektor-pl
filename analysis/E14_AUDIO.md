# E14: audio całej gry (M3)

Wygenerowano przez `python -I -m lektor audio-report`. Model `omnivoice-08be0b4-fp32-s32-cfg2.0`, GTX 1650 Ti. Raport zawiera tylko liczby i klucze techniczne.

## Czas generowania

Podejść: **12004** (926694 znaków, 1249.5 min audio). Czas GPU: **47.8 h**, czyli **0.186 s na znak** i RTF 2.29 (mediana RTF podejść 2.49). Szczyt VRAM: 3.10 GB.

| znaki fragmentu | podejścia | średnio s | s na znak |
|---|---|---|---|
| 0–29 | 2604 | 9.3 | 0.524 |
| 30–79 | 4635 | 11.7 | 0.216 |
| 80–159 | 3653 | 17.6 | 0.159 |
| 160– | 1112 | 26.1 | 0.130 |

Z M2 przejęte 3915 fragmentów bez generowania.

Na znak nowego tekstu (z podejściami bohaterów i ponownymi): 0.141 s. Cała gra (D02, ok. 1.43 mln znaków) w tych samych proporcjach: ok. **56 h** GPU (D39; przed przyspieszeniami ok. 610 h na jedno podejście).

## Automat (D38)

Fragmentów: **9779**. Z ponownym podejściem: 230. Bez zaakceptowanego podejścia po ponownym: **79** (koncowka 46, cer 35, barwa 7, zgubiony_fragment 4, tempo 2, cisza 2).

Wybrane podejścia sprawdzone Whisperem (z przejętymi): **5401** z 9779. Pozostałe 4378 mają tylko szybką ocenę bez ASR (cisza, tempo, końcówka, barwa, pauzy; D96), więc ich CER w tabeli wynosi 0.

| głos | fragmenty | podejścia ocenione | CER wybranych (mediana) | barwa (mediana) | odrzucone |
|---|---|---|---|---|---|
| adelynn | 56 | 5 | 0.000 | 0.942 | 3 |
| astarra | 27 | 0 | 0.000 | 0.942 | 0 |
| balthain | 13 | 0 | 0.000 | 0.954 | 0 |
| bruli | 45 | 5 | 0.000 | 0.941 | 1 |
| brynn | 448 | 86 | 0.000 | 0.917 | 3 |
| chance | 300 | 57 | 0.000 | 0.883 | 1 |
| ducard | 9 | 0 | 0.000 | 0.860 | 0 |
| flint | 10 | 0 | 0.000 | 0.941 | 0 |
| galaden | 313 | 60 | 0.000 | 0.924 | 0 |
| galgoraz | 10 | 0 | 0.000 | 0.956 | 0 |
| greysdon | 27 | 1 | 0.000 | 0.879 | 0 |
| herbie | 13 | 0 | 0.000 | 0.946 | 0 |
| kathryn | 13 | 3 | 0.000 | 0.927 | 0 |
| kehli | 346 | 42 | 0.000 | 0.896 | 0 |
| laurel | 33 | 8 | 0.000 | 0.914 | 0 |
| levirax | 6 | 6 | 0.003 | 0.939 | 0 |
| ltrand | 18 | 1 | 0.000 | 0.929 | 0 |
| magrit | 30 | 0 | 0.000 | 0.933 | 1 |
| mok | 7 | 0 | 0.000 | 0.971 | 0 |
| narrator | 7322 | 1179 | 0.000 | 0.928 | 66 |
| nekrul | 2 | 2 | 0.021 | 0.877 | 2 |
| outlaw | 12 | 0 | 0.000 | 0.964 | 0 |
| ronan | 9 | 0 | 0.000 | 0.936 | 0 |
| syrus | 373 | 51 | 0.000 | 0.925 | 0 |
| vaerix | 312 | 44 | 0.000 | 0.907 | 2 |
| xenith | 1 | 0 | 0.014 | 0.928 | 0 |
| zachareth | 24 | 0 | 0.000 | 0.907 | 0 |

## Pokrycie M3

Klucze do syntezy z zaakceptowanym audio wszystkich fragmentów: **6591 / 12608 (52.3%)**. Wartości luk z zaakceptowanym audio: 33412 / 34394.
