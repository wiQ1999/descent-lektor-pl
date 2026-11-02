"""Companion lektora (E4): odbiera zdarzenia pluginu przez TCP na localhost i odtwarza pregenerowane audio.

  library   kwestia (klucz, argumenty) -> lista fragmentów audio z pauzami (sklejanie luk {n}, D16)
  director  zasady odtwarzania: przerywanie (D03), kolejka celu i aktywacji (D45), okna wyboru (D20), przełączniki (D21)
  player    odtwarzanie przez sounddevice (D47) albo bez dźwięku (replay)
  app       serwer TCP, replay dziennika E1, dziennik companiona i podsumowanie pokrycia

Zależności: numpy, soundfile, sounddevice (bez torch), żeby companion dało się uruchomić także na Macu (E6).
"""
