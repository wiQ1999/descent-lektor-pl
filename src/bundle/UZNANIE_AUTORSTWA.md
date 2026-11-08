# Uznanie autorstwa i licencje składników

Kod lektora (plugin, loader, companion, skrypty) jest objęty licencją z pliku `LICENSE.md`. Paczka zawiera też nagrania i programy innych autorów. Obowiązują ich własne licencje i regulaminy.

## Nagrania lektora

- **OmniVoice** (k2-fsa; Han Zhu, Lingxuan Ye, Wei Kang, Zengwei Yao, Liyong Guo, Fangjun Kuang, Zhifeng Han, Weiji Zhuang, Long Lin, Daniel Povey), model `k2-fsa/OmniVoice`. Czyta narratora, bohaterów i złoczyńców z polskim dubbingiem.
  - Kod: licencja Apache 2.0. Wagi modelu: licencja CC BY-NC, czyli użycie niekomercyjne z uznaniem autorstwa.
  - Praca: „OmniVoice: Towards Omnilingual Zero-Shot Text-to-Speech with Diffusion Language Models”, arXiv:2604.00688, 2026.
- **Higgs Audio v2** (Boson AI): tokenizer audio, którego używa OmniVoice. Licencja Boson Higgs Audio 2 Community License. Built with Higgs Audio.
- **ElevenLabs**, model `eleven_v4`, głosy zaprojektowane w ElevenLabs Voice Design. Czyta postacie bez polskiego dubbingu. Nagrania powstały w płatnym planie, na warunkach regulaminu ElevenLabs.
- Głosy OmniVoice są sklonowane z polskiego dubbingu gry, a teksty pochodzą z polskiej lokalizacji gry. Należą do Fantasy Flight Games i innych uprawnionych (`LICENSE.md`, pkt 6).

## Programy w paczce

- **Unity Doorstop 4.6.0** (NeighTools), folder `loader/`. Licencja GNU LGPL 2.1, tekst w `licencje/doorstop-LICENSE.txt`. Kod źródłowy: https://github.com/NeighTools/UnityDoorstop/releases/tag/v4.6.0
- **Python 3.12** z python-build-standalone (Astral), folder `python/`. Licencja PSF i licencje bibliotek leżą w plikach `LICENSE` w folderze Pythona.
- **Pakiety Pythona** companiona (m.in. NumPy, sounddevice, soundfile z libsndfile). Licencje leżą przy pakietach, w folderach `*.dist-info` w `site-packages`.
