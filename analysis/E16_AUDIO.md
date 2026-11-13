# E16: audio paczki testowej Q1–Q2 (t1)

Wygenerowano przez `python -I -m lektor audio-report`. Model `omnivoice-08be0b4-fp32-s32-cfg2.0`, GTX 1650 Ti. Raport zawiera tylko liczby i klucze techniczne.

## Czas generowania

Podejść: **3558** (234871 znaków, 304.3 min audio). Czas GPU: **13.0 h**, czyli **0.199 s na znak** i RTF 2.56 (mediana RTF podejść 2.96). Szczyt VRAM: 3.10 GB.

| znaki fragmentu | podejścia | średnio s | s na znak |
|---|---|---|---|
| 0–29 | 1505 | 9.1 | 0.562 |
| 30–79 | 890 | 11.4 | 0.216 |
| 80–159 | 813 | 17.2 | 0.150 |
| 160– | 350 | 25.2 | 0.125 |

Z M3 przejęte 7477 fragmentów bez generowania.

Na znak nowego tekstu (z podejściami bohaterów i ponownymi): 0.047 s. Cała gra (D02, ok. 1.43 mln znaków) w tych samych proporcjach: ok. **19 h** GPU (D39; przed przyspieszeniami ok. 610 h na jedno podejście).

## Automat (D38)

Fragmentów: **10338**. Z ponownym podejściem: 363. Bez zaakceptowanego podejścia po ponownym: **85** (koncowka 48, cer 38, barwa 6, zgubiony_fragment 5, tempo 3, cisza 2).

Wybrane podejścia sprawdzone Whisperem (z przejętymi): **6461** z 10338. Pozostałe 3877 mają tylko szybką ocenę bez ASR (cisza, tempo, końcówka, barwa, pauzy; D96), więc ich CER w tabeli wynosi 0.

| głos | fragmenty | podejścia ocenione | CER wybranych (mediana) | barwa (mediana) | odrzucone |
|---|---|---|---|---|---|
| adelynn | 56 | 0 | 0.000 | 0.942 | 3 |
| astarra | 27 | 0 | 0.000 | 0.942 | 0 |
| balthain | 13 | 0 | 0.000 | 0.954 | 0 |
| bruli | 53 | 9 | 0.000 | 0.937 | 1 |
| brynn | 473 | 76 | 0.000 | 0.915 | 3 |
| chance | 312 | 36 | 0.000 | 0.885 | 1 |
| ducard | 9 | 0 | 0.000 | 0.860 | 0 |
| flint | 10 | 0 | 0.000 | 0.941 | 0 |
| galaden | 333 | 60 | 0.000 | 0.924 | 0 |
| galgoraz | 10 | 0 | 0.000 | 0.956 | 0 |
| greysdon | 27 | 0 | 0.000 | 0.879 | 0 |
| herbie | 13 | 0 | 0.000 | 0.946 | 0 |
| kathryn | 13 | 0 | 0.000 | 0.927 | 0 |
| kehli | 401 | 165 | 0.000 | 0.898 | 0 |
| laurel | 33 | 0 | 0.000 | 0.914 | 0 |
| levirax | 6 | 0 | 0.003 | 0.939 | 0 |
| ltrand | 18 | 0 | 0.000 | 0.929 | 0 |
| magrit | 30 | 0 | 0.000 | 0.933 | 1 |
| mok | 7 | 0 | 0.000 | 0.971 | 0 |
| narrator | 7625 | 2938 | 0.000 | 0.928 | 69 |
| nekrul | 5 | 15 | 0.000 | 0.870 | 3 |
| nv_bandyta | 4 | 5 | 0.000 | 0.859 | 0 |
| nv_eurth | 2 | 2 | 0.000 | 0.911 | 0 |
| nv_fae | 6 | 27 | 0.000 | 0.795 | 2 |
| nv_fanatyk | 4 | 5 | 0.000 | 0.868 | 0 |
| nv_gap | 2 | 3 | 0.000 | 0.917 | 0 |
| nv_glos | 2 | 2 | 0.000 | – | 0 |
| nv_gnom | 1 | 1 | 0.000 | 0.905 | 0 |
| nv_gont | 6 | 6 | 0.000 | 0.936 | 0 |
| nv_kowalka | 4 | 5 | 0.000 | 0.935 | 0 |
| nv_nekromanta | 1 | 2 | 0.000 | 0.924 | 0 |
| nv_orban | 4 | 5 | 0.000 | 0.926 | 0 |
| nv_ork | 1 | 2 | 0.000 | 0.933 | 0 |
| nv_protektor | 12 | 12 | 0.000 | 0.927 | 0 |
| nv_straznik | 8 | 8 | 0.000 | 0.948 | 0 |
| nv_uchodzca | 1 | 1 | 0.000 | 0.905 | 0 |
| nv_widmo | 14 | 15 | 0.000 | 0.903 | 0 |
| nv_wiesniak | 4 | 4 | 0.003 | 0.933 | 0 |
| nv_wiezien | 2 | 2 | 0.022 | 0.927 | 0 |
| nv_xain | 2 | 2 | 0.005 | 0.951 | 0 |
| nv_ynfernael | 1 | 1 | 0.000 | 0.867 | 0 |
| outlaw | 12 | 0 | 0.000 | 0.964 | 0 |
| reneyr | 2 | 2 | 0.000 | 0.856 | 0 |
| ronan | 9 | 0 | 0.000 | 0.936 | 0 |
| syrus | 402 | 87 | 0.000 | 0.926 | 0 |
| vaerix | 331 | 58 | 0.000 | 0.907 | 2 |
| xenith | 1 | 0 | 0.014 | 0.928 | 0 |
| zachareth | 26 | 2 | 0.000 | 0.906 | 0 |

## Pokrycie T1

Klucze do syntezy z zaakceptowanym audio wszystkich fragmentów: **7485 / 13724 (54.5%)**. Wartości luk z zaakceptowanym audio: 22253 / 34433.
