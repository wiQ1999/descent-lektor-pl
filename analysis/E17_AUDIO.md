# E17: audio wersji produkcyjnej (m4)

Wygenerowano przez `python -I -m lektor audio-report`. Model `omnivoice-08be0b4-fp32-s32-cfg2.0`, GTX 1650 Ti. Raport zawiera tylko liczby i klucze techniczne.

## Czas generowania

Podejść: **23288** (1865458 znaków, 2470.0 min audio). Czas GPU: **94.8 h**, czyli **0.183 s na znak** i RTF 2.30 (mediana RTF podejść 2.50). Szczyt VRAM: 3.11 GB.

| znaki fragmentu | podejścia | średnio s | s na znak |
|---|---|---|---|
| 0–29 | 5177 | 9.4 | 0.538 |
| 30–79 | 8259 | 11.8 | 0.223 |
| 80–159 | 7221 | 17.8 | 0.158 |
| 160– | 2631 | 25.4 | 0.127 |

Z T1 przejęte 6429 fragmentów bez generowania.

Na znak nowego tekstu (z podejściami bohaterów i ponownymi): 0.295 s. Cała gra (D02, ok. 1.43 mln znaków) w tych samych proporcjach: ok. **117 h** GPU (D39; przed przyspieszeniami ok. 610 h na jedno podejście).

## Automat (D38)

Fragmentów: **19428**. Z ponownym podejściem: 780. Bez zaakceptowanego podejścia po ponownym: **152** (koncowka 84, cer 72, tempo 12, barwa 11, zgubiony_fragment 3, cisza 2).

Wybrane podejścia sprawdzone Whisperem (z przejętymi): **17772** z 19428. Pozostałe 1656 mają tylko szybką ocenę bez ASR (cisza, tempo, końcówka, barwa, pauzy; D96), więc ich CER w tabeli wynosi 0.

| głos | fragmenty | podejścia ocenione | CER wybranych (mediana) | barwa (mediana) | odrzucone |
|---|---|---|---|---|---|
| adelynn | 84 | 33 | 0.000 | 0.940 | 4 |
| alys | 107 | 114 | 0.000 | 0.937 | 1 |
| arden | 42 | 45 | 0.000 | 0.951 | 1 |
| astarra | 55 | 28 | 0.000 | 0.932 | 0 |
| balthain | 39 | 31 | 0.000 | 0.950 | 1 |
| bruli | 77 | 33 | 0.000 | 0.948 | 1 |
| brynn | 1081 | 1877 | 0.000 | 0.919 | 10 |
| button | 62 | 67 | 0.000 | 0.935 | 1 |
| chance | 809 | 1535 | 0.000 | 0.903 | 6 |
| delphyndra | 16 | 19 | 0.000 | 0.954 | 0 |
| drys | 17 | 21 | 0.000 | 0.898 | 1 |
| ducard | 46 | 50 | 0.000 | 0.926 | 1 |
| flint | 24 | 14 | 0.000 | 0.942 | 0 |
| galaden | 824 | 1510 | 0.000 | 0.932 | 4 |
| galgoraz | 65 | 59 | 0.000 | 0.945 | 1 |
| gilliam | 29 | 40 | 0.020 | 0.933 | 1 |
| grace | 15 | 19 | 0.000 | 0.894 | 0 |
| greigory | 72 | 82 | 0.000 | 0.936 | 3 |
| greysdon | 62 | 35 | 0.000 | 0.880 | 0 |
| herbie | 18 | 5 | 0.000 | 0.946 | 0 |
| kathryn | 57 | 51 | 0.000 | 0.922 | 2 |
| kehli | 945 | 1670 | 0.000 | 0.901 | 3 |
| laurel | 120 | 191 | 0.000 | 0.924 | 2 |
| levirax | 25 | 26 | 0.000 | 0.934 | 0 |
| levirax_e | 6 | 6 | 0.016 | 0.889 | 0 |
| ltrand | 25 | 26 | 0.000 | 0.917 | 0 |
| magrit | 164 | 144 | 0.000 | 0.933 | 3 |
| meza | 21 | 21 | 0.000 | 0.941 | 0 |
| mok | 30 | 23 | 0.000 | 0.950 | 0 |
| morant | 48 | 50 | 0.000 | 0.926 | 0 |
| nara | 34 | 36 | 0.000 | 0.950 | 0 |
| narrator | 11457 | 8457 | 0.000 | 0.926 | 70 |
| navoth | 37 | 39 | 0.000 | 0.903 | 0 |
| nekrul | 23 | 93 | 0.000 | 0.890 | 9 |
| nv_a2q11_medyk | 1 | 1 | 0.000 | 0.893 | 0 |
| nv_a2q11_protektor | 1 | 1 | 0.000 | 0.875 | 0 |
| nv_a2q11_wojowniczka | 1 | 1 | 0.000 | 0.919 | 0 |
| nv_a2q11_zolnierz | 1 | 1 | 0.000 | 0.953 | 0 |
| nv_a2q2_straznik | 1 | 1 | 0.000 | – | 0 |
| nv_a2q3_bandyta | 1 | 1 | 0.000 | – | 0 |
| nv_a2q3_strazniczka | 1 | 1 | 0.019 | 0.963 | 0 |
| nv_a2q3_straznik | 1 | 1 | 0.000 | – | 0 |
| nv_a2q3_zolnierz | 1 | 1 | 0.000 | 0.945 | 0 |
| nv_a2q5_hybryda | 2 | 2 | 0.011 | 0.914 | 0 |
| nv_a2q5_lowczyni | 1 | 1 | 0.017 | 0.914 | 0 |
| nv_a2q7_wygnaniec | 1 | 1 | 0.000 | 0.927 | 0 |
| nv_a2q8_bibliotekarka | 10 | 10 | 0.000 | 0.919 | 0 |
| nv_a2q8_kronikarz | 11 | 11 | 0.000 | 0.865 | 0 |
| nv_a2q8_ogrodniczka | 18 | 22 | 0.000 | 0.928 | 0 |
| nv_a2q8_zamiatacz | 10 | 10 | 0.000 | 0.951 | 0 |
| nv_baelziffar | 14 | 33 | 0.000 | 0.927 | 0 |
| nv_bandyta | 4 | 5 | 0.000 | 0.906 | 0 |
| nv_crayleth | 5 | 5 | 0.013 | 0.955 | 0 |
| nv_czerwona_gwiazda | 1 | 1 | 0.000 | 0.962 | 0 |
| nv_dalavel | 3 | 3 | 0.000 | 0.958 | 0 |
| nv_denavel | 2 | 2 | 0.011 | 0.921 | 0 |
| nv_edgar | 9 | 10 | 0.000 | 0.915 | 0 |
| nv_eurth | 2 | 2 | 0.000 | 0.873 | 0 |
| nv_fae | 6 | 6 | 0.000 | 0.844 | 0 |
| nv_fanatyk | 4 | 4 | 0.000 | – | 0 |
| nv_fof_kapitan | 18 | 51 | 0.005 | 0.944 | 1 |
| nv_fof_mieszkanka | 1 | 1 | 0.000 | 0.811 | 0 |
| nv_fulminar | 8 | 8 | 0.000 | 0.948 | 0 |
| nv_gap | 2 | 0 | 0.000 | 0.917 | 0 |
| nv_glos | 2 | 0 | 0.000 | – | 0 |
| nv_gnom | 1 | 1 | 0.000 | 0.958 | 0 |
| nv_gont | 6 | 12 | 0.000 | 0.901 | 0 |
| nv_gorzae | 4 | 4 | 0.000 | 0.943 | 0 |
| nv_gravia | 14 | 17 | 0.010 | 0.918 | 0 |
| nv_honora | 3 | 3 | 0.012 | 0.927 | 0 |
| nv_kowalka | 4 | 4 | 0.000 | 0.939 | 0 |
| nv_lisb_naukowiec | 3 | 3 | 0.000 | 0.958 | 0 |
| nv_lisb_wartownik_a | 1 | 3 | 0.010 | 0.951 | 0 |
| nv_lisb_wartownik_b | 2 | 2 | 0.000 | 0.926 | 0 |
| nv_lisb_zwiadowca | 2 | 6 | 0.000 | 0.921 | 0 |
| nv_nekromanta | 1 | 0 | 0.000 | 0.924 | 0 |
| nv_nicodemus | 2 | 2 | 0.095 | 0.883 | 0 |
| nv_ocella | 25 | 44 | 0.000 | 0.923 | 1 |
| nv_orban | 4 | 4 | 0.000 | 0.923 | 0 |
| nv_ork | 1 | 0 | 0.000 | 0.933 | 0 |
| nv_patralis | 10 | 15 | 0.000 | 0.935 | 1 |
| nv_preesha | 4 | 4 | 0.000 | 0.952 | 0 |
| nv_protektor | 12 | 0 | 0.000 | 0.927 | 0 |
| nv_q10_jezdzczyni | 3 | 3 | 0.000 | 0.902 | 0 |
| nv_q10_jezdziec | 4 | 8 | 0.000 | 0.938 | 0 |
| nv_q10_straznik | 1 | 8 | 0.061 | 0.897 | 0 |
| nv_q11_bandyta_nekromanta | 1 | 5 | 0.000 | 0.949 | 0 |
| nv_q11_kobieta_a | 4 | 4 | 0.000 | 0.917 | 0 |
| nv_q11_kobieta_b | 1 | 1 | 0.025 | 0.958 | 0 |
| nv_q11_kobieta_kufel | 3 | 3 | 0.000 | 0.928 | 0 |
| nv_q11_mlody_ork | 1 | 2 | 0.000 | 0.920 | 0 |
| nv_q11_ork_ojciec | 1 | 1 | 0.000 | 0.941 | 0 |
| nv_q11_pacjentka | 5 | 13 | 0.000 | 0.918 | 0 |
| nv_q11_rodzic | 1 | 3 | 0.019 | 0.950 | 0 |
| nv_q11_tlum | 1 | 2 | 0.000 | – | 0 |
| nv_q11_uchodzca | 1 | 2 | 0.000 | 0.964 | 0 |
| nv_q11_uzdrowiciel | 1 | 2 | 0.000 | 0.973 | 0 |
| nv_q11_zbir | 2 | 4 | 0.000 | 0.939 | 0 |
| nv_q12_banitka | 1 | 1 | 0.000 | 0.935 | 0 |
| nv_q12_duch | 3 | 10 | 0.012 | 0.938 | 0 |
| nv_q13_hybryda | 1 | 3 | 0.071 | 0.900 | 0 |
| nv_q13_smok | 27 | 61 | 0.000 | 0.863 | 0 |
| nv_q14_kucharz | 4 | 12 | 0.014 | 0.915 | 0 |
| nv_q14_stronnik | 2 | 6 | 0.034 | 0.971 | 0 |
| nv_q14_wiezien_hybryda | 2 | 4 | 0.017 | 0.919 | 0 |
| nv_q14_wskrzeszeniec | 3 | 6 | 0.000 | 0.880 | 0 |
| nv_q14_zolnierka | 5 | 13 | 0.016 | 0.917 | 1 |
| nv_q3_bandyta_skrzynia | 1 | 7 | 0.075 | 0.953 | 0 |
| nv_q3_herszt | 2 | 4 | 0.000 | 0.942 | 0 |
| nv_q9_blizniaki | 2 | 3 | 0.000 | 0.929 | 0 |
| nv_saphar | 10 | 10 | 0.000 | 0.902 | 0 |
| nv_siostra_krwi | 6 | 11 | 0.010 | 0.933 | 0 |
| nv_sq1_wiedzma | 11 | 23 | 0.000 | 0.950 | 0 |
| nv_sq1_wyslannik | 25 | 65 | 0.000 | 0.939 | 0 |
| nv_straznik | 8 | 9 | 0.000 | 0.928 | 0 |
| nv_ta2_04_kobieta | 2 | 2 | 0.003 | 0.935 | 0 |
| nv_ta2_czeladnik | 4 | 4 | 0.011 | 0.946 | 0 |
| nv_ta2_gospodarz | 1 | 1 | 0.000 | 0.926 | 0 |
| nv_ta2_karciarz | 1 | 1 | 0.000 | 0.886 | 0 |
| nv_ta2_kupiec | 1 | 1 | 0.000 | 0.864 | 0 |
| nv_ta2_mag | 5 | 5 | 0.000 | 0.903 | 0 |
| nv_ta2_orczyca | 1 | 1 | 0.000 | – | 0 |
| nv_ta2_pielgrzym | 1 | 1 | 0.029 | 0.946 | 0 |
| nv_ta2_sierzant | 2 | 2 | 0.000 | 0.931 | 0 |
| nv_ta2_sluzacy | 1 | 1 | 0.000 | 0.911 | 0 |
| nv_uchodzca | 1 | 0 | 0.000 | 0.905 | 0 |
| nv_warrick | 15 | 17 | 0.000 | 0.945 | 0 |
| nv_widmo | 14 | 0 | 0.000 | 0.903 | 0 |
| nv_wiesniak | 4 | 4 | 0.000 | 0.943 | 0 |
| nv_wiezien | 2 | 3 | 0.000 | 0.912 | 0 |
| nv_xain | 2 | 2 | 0.005 | 0.949 | 0 |
| nv_zarzadczyni | 5 | 14 | 0.000 | 0.943 | 0 |
| nv_zerai | 1 | 1 | 0.029 | 0.912 | 0 |
| outlaw | 51 | 42 | 0.000 | 0.950 | 0 |
| pryor | 12 | 12 | 0.009 | 0.934 | 0 |
| reneyr | 91 | 93 | 0.000 | 0.931 | 0 |
| ronan | 74 | 77 | 0.000 | 0.938 | 3 |
| syrus | 1043 | 1958 | 0.000 | 0.928 | 4 |
| trevalyn | 40 | 45 | 0.005 | 0.945 | 0 |
| vaerix | 889 | 3224 | 0.000 | 0.898 | 15 |
| veta | 51 | 55 | 0.000 | 0.930 | 1 |
| vraskhar | 59 | 65 | 0.000 | 0.929 | 0 |
| waiqar | 23 | 25 | 0.000 | 0.953 | 0 |
| xenith | 27 | 26 | 0.000 | 0.902 | 0 |
| zachareth | 84 | 67 | 0.000 | 0.905 | 0 |

## Pokrycie M4

Klucze do syntezy z zaakceptowanym audio wszystkich fragmentów: **13733 / 13925 (98.6%)**. Wartości luk z zaakceptowanym audio: 55056 / 58032.
