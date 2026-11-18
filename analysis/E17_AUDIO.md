# E17: audio wersji produkcyjnej (m4)

Wygenerowano przez `python -I -m lektor audio-report`. Model `omnivoice-08be0b4-fp32-s32-cfg2.0`, GTX 1650 Ti. Raport zawiera tylko liczby i klucze techniczne.

## Czas generowania

Podejść: **18709** (1522652 znaków, 2017.6 min audio). Czas GPU: **76.9 h**, czyli **0.182 s na znak** i RTF 2.29 (mediana RTF podejść 2.49). Szczyt VRAM: 3.10 GB.

| znaki fragmentu | podejścia | średnio s | s na znak |
|---|---|---|---|
| 0–29 | 4076 | 9.3 | 0.528 |
| 30–79 | 6553 | 11.8 | 0.224 |
| 80–159 | 5867 | 17.9 | 0.159 |
| 160– | 2213 | 25.6 | 0.128 |

Z T1 przejęte 7300 fragmentów bez generowania.

Na znak nowego tekstu (z podejściami bohaterów i ponownymi): 0.252 s. Cała gra (D02, ok. 1.43 mln znaków) w tych samych proporcjach: ok. **100 h** GPU (D39; przed przyspieszeniami ok. 610 h na jedno podejście).

## Automat (D38)

Fragmentów: **11839**. Z ponownym podejściem: 530. Bez zaakceptowanego podejścia po ponownym: **110** (koncowka 63, cer 55, tempo 10, barwa 6, zgubiony_fragment 5, cisza 1).

Wybrane podejścia sprawdzone Whisperem (z przejętymi): **9789** z 11839. Pozostałe 2050 mają tylko szybką ocenę bez ASR (cisza, tempo, końcówka, barwa, pauzy; D96), więc ich CER w tabeli wynosi 0.

| głos | fragmenty | podejścia ocenione | CER wybranych (mediana) | barwa (mediana) | odrzucone |
|---|---|---|---|---|---|
| adelynn | 84 | 33 | 0.000 | 0.940 | 4 |
| astarra | 27 | 0 | 0.000 | 0.942 | 0 |
| balthain | 13 | 0 | 0.000 | 0.954 | 0 |
| bruli | 53 | 8 | 0.000 | 0.942 | 1 |
| brynn | 613 | 437 | 0.000 | 0.916 | 6 |
| chance | 434 | 385 | 0.000 | 0.887 | 4 |
| drys | 12 | 15 | 0.000 | 0.882 | 1 |
| ducard | 9 | 11 | 0.008 | 0.887 | 1 |
| flint | 10 | 0 | 0.000 | 0.941 | 0 |
| galaden | 432 | 320 | 0.000 | 0.927 | 3 |
| galgoraz | 10 | 0 | 0.000 | 0.956 | 0 |
| greysdon | 61 | 34 | 0.000 | 0.879 | 0 |
| herbie | 13 | 0 | 0.000 | 0.946 | 0 |
| kathryn | 47 | 40 | 0.000 | 0.914 | 2 |
| kehli | 508 | 348 | 0.000 | 0.899 | 3 |
| laurel | 91 | 160 | 0.000 | 0.925 | 2 |
| levirax | 6 | 0 | 0.003 | 0.939 | 0 |
| ltrand | 18 | 18 | 0.000 | 0.917 | 0 |
| magrit | 30 | 0 | 0.000 | 0.933 | 1 |
| meza | 15 | 15 | 0.000 | 0.941 | 0 |
| mok | 7 | 0 | 0.000 | 0.971 | 0 |
| narrator | 7806 | 3475 | 0.000 | 0.924 | 59 |
| nekrul | 13 | 48 | 0.000 | 0.877 | 8 |
| nv_baelziffar | 14 | 30 | 0.000 | 0.927 | 0 |
| nv_bandyta | 4 | 0 | 0.000 | 0.859 | 0 |
| nv_dalavel | 1 | 1 | 0.000 | 0.958 | 0 |
| nv_eurth | 2 | 0 | 0.000 | 0.911 | 0 |
| nv_fae | 6 | 0 | 0.000 | 0.775 | 0 |
| nv_fanatyk | 4 | 0 | 0.000 | 0.868 | 0 |
| nv_fof_kapitan | 18 | 46 | 0.005 | 0.948 | 1 |
| nv_fof_mieszkanka | 1 | 1 | 0.000 | 0.811 | 0 |
| nv_gap | 2 | 0 | 0.000 | 0.917 | 0 |
| nv_glos | 2 | 0 | 0.000 | – | 0 |
| nv_gnom | 1 | 1 | 0.000 | 0.958 | 0 |
| nv_gont | 6 | 6 | 0.000 | 0.923 | 0 |
| nv_kowalka | 4 | 0 | 0.000 | 0.935 | 0 |
| nv_lisb_naukowiec | 3 | 3 | 0.000 | 0.958 | 0 |
| nv_lisb_wartownik_a | 1 | 2 | 0.010 | 0.952 | 0 |
| nv_lisb_wartownik_b | 2 | 2 | 0.000 | 0.926 | 0 |
| nv_lisb_zwiadowca | 2 | 4 | 0.000 | 0.914 | 0 |
| nv_nekromanta | 1 | 0 | 0.000 | 0.924 | 0 |
| nv_ocella | 25 | 42 | 0.000 | 0.923 | 1 |
| nv_orban | 4 | 0 | 0.000 | 0.926 | 0 |
| nv_ork | 1 | 0 | 0.000 | 0.933 | 0 |
| nv_preesha | 4 | 4 | 0.000 | 0.952 | 0 |
| nv_protektor | 12 | 0 | 0.000 | 0.927 | 0 |
| nv_q10_jezdzczyni | 3 | 3 | 0.000 | 0.902 | 0 |
| nv_q10_jezdziec | 4 | 4 | 0.000 | 0.905 | 0 |
| nv_q10_straznik | 1 | 7 | 0.121 | 0.910 | 1 |
| nv_q11_bandyta_nekromanta | 1 | 3 | 0.000 | 0.948 | 0 |
| nv_q11_kobieta_a | 4 | 4 | 0.000 | 0.917 | 0 |
| nv_q11_kobieta_b | 1 | 1 | 0.025 | 0.958 | 0 |
| nv_q11_kobieta_kufel | 3 | 3 | 0.000 | 0.928 | 0 |
| nv_q11_mlody_ork | 1 | 2 | 0.000 | 0.920 | 0 |
| nv_q11_ork_ojciec | 1 | 1 | 0.000 | 0.941 | 0 |
| nv_q11_pacjentka | 5 | 7 | 0.000 | 0.940 | 0 |
| nv_q11_rodzic | 1 | 2 | 0.006 | 0.961 | 0 |
| nv_q11_tlum | 1 | 1 | 0.000 | – | 0 |
| nv_q11_uchodzca | 1 | 1 | 0.000 | 0.950 | 0 |
| nv_q11_uzdrowiciel | 1 | 2 | 0.000 | 0.973 | 0 |
| nv_q11_zbir | 2 | 2 | 0.000 | 0.937 | 0 |
| nv_q12_banitka | 1 | 1 | 0.000 | 0.935 | 0 |
| nv_q12_duch | 3 | 7 | 0.133 | 0.893 | 0 |
| nv_q13_hybryda | 1 | 3 | 0.071 | 0.900 | 0 |
| nv_q13_smok | 27 | 27 | 0.000 | 0.956 | 0 |
| nv_q14_kucharz | 4 | 8 | 0.004 | 0.919 | 0 |
| nv_q14_stronnik | 2 | 4 | 0.037 | 0.929 | 0 |
| nv_q14_wiezien_hybryda | 2 | 2 | 0.017 | 0.873 | 0 |
| nv_q14_wskrzeszeniec | 3 | 6 | 0.000 | 0.880 | 0 |
| nv_q14_zolnierka | 5 | 11 | 0.016 | 0.917 | 1 |
| nv_q3_bandyta_skrzynia | 1 | 2 | 0.000 | 0.935 | 0 |
| nv_q3_herszt | 2 | 2 | 0.000 | 0.935 | 0 |
| nv_q9_blizniaki | 1 | 1 | 0.000 | 0.862 | 0 |
| nv_siostra_krwi | 4 | 5 | 0.010 | 0.881 | 0 |
| nv_sq1_wiedzma | 11 | 11 | 0.000 | 0.949 | 0 |
| nv_sq1_wyslannik | 25 | 32 | 0.000 | 0.933 | 1 |
| nv_straznik | 8 | 9 | 0.000 | 0.928 | 0 |
| nv_uchodzca | 1 | 0 | 0.000 | 0.905 | 0 |
| nv_warrick | 15 | 17 | 0.000 | 0.945 | 0 |
| nv_widmo | 14 | 0 | 0.000 | 0.903 | 0 |
| nv_wiesniak | 4 | 4 | 0.000 | 0.943 | 0 |
| nv_wiezien | 2 | 2 | 0.011 | 0.913 | 0 |
| nv_xain | 2 | 0 | 0.005 | 0.951 | 0 |
| nv_zarzadczyni | 5 | 7 | 0.011 | 0.935 | 0 |
| nv_zerai | 1 | 1 | 0.029 | 0.912 | 0 |
| outlaw | 49 | 40 | 0.000 | 0.950 | 0 |
| reneyr | 2 | 0 | 0.000 | 0.856 | 0 |
| ronan | 46 | 46 | 0.000 | 0.938 | 2 |
| syrus | 597 | 602 | 0.000 | 0.929 | 2 |
| vaerix | 476 | 459 | 0.000 | 0.907 | 6 |
| waiqar | 10 | 11 | 0.007 | 0.951 | 0 |
| xenith | 27 | 26 | 0.000 | 0.902 | 0 |
| zachareth | 26 | 0 | 0.000 | 0.906 | 0 |

## Pokrycie M4

Klucze do syntezy z zaakceptowanym audio wszystkich fragmentów: **7857 / 13925 (56.4%)**. Wartości luk z zaakceptowanym audio: 54521 / 58032.
