# E7: audio M2

Wygenerowano przez `python -I -m lektor audio-report`. Model `omnivoice-08be0b4-fp32-s32-cfg2.0`, GTX 1650 Ti. Raport zawiera tylko liczby i klucze techniczne.

## Czas generowania

Podejść: **4333** (286848 znaków, 394.7 min audio). Czas GPU: **15.9 h**, czyli **0.200 s na znak** i RTF 2.42 (mediana RTF podejść 2.60). Szczyt VRAM: 3.10 GB.

| znaki fragmentu | podejścia | średnio s | s na znak |
|---|---|---|---|
| 0–29 | 1296 | 9.4 | 0.555 |
| 30–79 | 1655 | 11.6 | 0.216 |
| 80–159 | 1102 | 17.2 | 0.157 |
| 160– | 280 | 25.9 | 0.130 |

Z M1 przejęte 965 fragmentów bez generowania.

Na znak nowego tekstu (z podejściami bohaterów i ponownymi): 0.276 s. Cała gra (D02, ok. 1.43 mln znaków) w tych samych proporcjach: ok. **110 h** GPU (D39; przed przyspieszeniami ok. 610 h na jedno podejście).

## Automat (D38)

Fragmentów: **3919**. Z ponownym podejściem: 173. Bez zaakceptowanego podejścia po ponownym: **42** (koncowka 28, cer 22, barwa 1, cisza 1, zgubiony_fragment 1, tempo 1).

| głos | fragmenty | podejścia ocenione | CER wybranych (mediana) | barwa (mediana) | odrzucone |
|---|---|---|---|---|---|
| adelynn | 39 | 32 | 0.000 | 0.927 | 1 |
| astarra | 16 | 27 | 0.000 | 0.892 | 1 |
| bruli | 10 | 13 | 0.000 | 0.913 | 0 |
| brynn | 119 | 291 | 0.000 | 0.907 | 2 |
| chance | 69 | 212 | 0.000 | 0.885 | 1 |
| flint | 5 | 5 | 0.000 | 0.938 | 0 |
| galaden | 76 | 174 | 0.000 | 0.928 | 0 |
| galgoraz | 10 | 10 | 0.000 | 0.938 | 0 |
| herbie | 13 | 13 | 0.000 | 0.914 | 0 |
| kathryn | 9 | 10 | 0.000 | 0.907 | 0 |
| kehli | 120 | 364 | 0.000 | 0.901 | 0 |
| ltrand | 10 | 20 | 0.009 | 0.919 | 2 |
| mok | 7 | 7 | 0.017 | 0.936 | 0 |
| narrator | 3145 | 2498 | 0.000 | 0.926 | 33 |
| nekrul | 1 | 0 | 0.043 | 0.883 | 1 |
| outlaw | 12 | 12 | 0.000 | 0.929 | 0 |
| ronan | 9 | 27 | 0.000 | 0.909 | 0 |
| syrus | 127 | 297 | 0.000 | 0.931 | 0 |
| vaerix | 121 | 320 | 0.000 | 0.906 | 1 |
| xenith | 1 | 1 | 0.014 | 0.928 | 0 |

## Pokrycie M2

Klucze do syntezy z zaakceptowanym audio wszystkich fragmentów: **2295 / 2335 (98.3%)**. Wartości luk z zaakceptowanym audio: 14564 / 15236.

## Przegląd końcówek (D71)

Dopisane ręcznie po `audio-report`.

Pierwsza ocena oznaczyła 67 fragmentów, w tym 50 przez końcówkę. Część alarmów była fałszywa: Whisper pisze „Keli” jako „Kelly”, „Ne’Krul” razem, a kafle planszy cyframi („6A”). Po poprawce reguł w `evaluate.words` i `tail_cut` zostały 42 fragmenty, w tym 28 z końcówką.

Te 28 przesłuchał drugi raz Whisper, z ciszą wokół pliku i na samym ogonie nagrania:

| wynik | fragmenty | wniosek |
|---|---:|---|
| ostatnie słowo słyszalne | 9 | końcówka cała |
| inny zapis słowa o podobnej długości | 14 | nazwy i krótkie wartości, bez śladu cięcia |
| ostatnie słowo przed luką, ASR go nie zapisuje | 2 | w nagraniu jest osobny odcinek mowy 0,3–0,4 s, słowo jest wypowiedziane |
| końcowe „a” lub „i” przed luką | 2 | nie do sprawdzenia automatem |
| sam spójnik „i” jako fragment | 1 | nagranie ma 0,4–0,5 s mowy |

Wszystkie 5 ostatnich to kawałki szablonów z kart wrogów, po których gra czyta wartość luki. Kwestii fabularnych to nie dotyczy.

Fragment z pustym tekstem (`​`, znak zerowej szerokości) daje ciszę i nie przeszkadza.

Replay dzienników E1, E5 i E5B przez M2: 578 okien, pokrycie 0,9983, pokrycie czytelnych okien 1,0. Jeden brak: nazwa w łupie `DEFAULT_GET_TREASURE_MULTI`.

Brak usunięty w D72: lista łupu zna już nazwy wrogów, bez nowego audio.

Strona odsłuchu: `analysis/work/audio/m2/listen/index.html` (30 fragmentów, D72).
