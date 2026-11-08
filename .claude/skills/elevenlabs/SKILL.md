---
name: elevenlabs
description: Korzystanie z MCP ElevenLabs w repozytorium lektora PL. Szacunek kosztu i zgoda przed płatnym wywołaniem, parametry narzędzi, miejsce na audio, ocena próbek i obowiązkowe podsumowanie zużycia kredytów na końcu odpowiedzi. Używaj przy każdym zadaniu, które woła narzędzia mcp__elevenlabs__* (TTS, projekt głosu, klon, modele, konto).
---

# MCP ElevenLabs w tym repozytorium

Serwer `elevenlabs-mcp` 0.12.2 działa tylko w zakresie projektu (`.mcp.json`, D73). Hooki z `.claude/settings.json` zapisują koszt każdego płatnego wywołania w `analysis/work/elevenlabs/usage/elevenlabs.jsonl`. Szczegóły instalacji: `analysis/tools/elevenlabs/README.md`.

Kredyty to licznik znaków konta ElevenLabs (`character_count`), nie tokeny Claude.

## 1. Początek prompta

Przed pierwszym wywołaniem MCP w danym prompcie zapisz znacznik licznika konta:

```bash
uv run --no-project --python 3.13 analysis/tools/elevenlabs/usage_report.py --mark
```

Znacznik robisz raz na prompt. Od niego liczy się zużycie w podsumowaniu z punktu 7.

## 2. Darmowe i płatne narzędzia

| Rodzaj | Narzędzia |
|---|---|
| bezpłatne | `check_subscription`, `list_models`, `search_voices`, `get_voice`, `search_voice_library`, inne `list_*` i `get_*`, `create_voice_from_preview` (zajmuje miejsce na głos) |
| płatne | `text_to_speech`, `text_to_voice`, `voice_clone`, `speech_to_speech`, `speech_to_text`, `isolate_audio`, `text_to_sound_effects`, muzyka |
| nie używamy | agenci, rozmowy i połączenia telefoniczne (`create_agent`, `make_outbound_call` itd.) |

Fragmenty wydania (postacie bez dubbingu, D80) generuje komenda `python -I -m lektor eleven` bez MCP (E13, D81). Jest płatna jak `text_to_speech`, więc obowiązują te same zasady: zgoda, `--mark` i `--summary`. Szacunek bez sieci daje `--dry-run`, a limit wsadu `--max-credits`. Koszt sama zapisuje w logu zużycia (`tool: lektor_eleven`).

## 3. Zgoda i szacunek kosztu

- Przed płatnym wywołaniem policz koszt: znaki tekstu × stawka modelu. Stawki z pomiarów są niżej.
- Zgoda: użytkownik musi wprost zlecić płatne wywołania w prompcie albo zatwierdzić szacunek w QA (`AskUserQuestion`). Jeśli zakres nie jest jasny, najpierw QA z kosztem.
- Gdy koszt przekracza zatwierdzony szacunek o więcej niż 20%, zatrzymaj się i zapytaj.
- Testy automatyczne nigdy nie łączą się z siecią.
- Ten sam tekst czytany kilkoma modelami podawaj z jawnym `model_id`: hook dopasowuje wpis historii po tekście, głosie i modelu.

Stawki zmierzone na koncie (kredyty na znak). Brak wpisu znaczy, że stawki nie zmierzyliśmy, więc w szacunku przyjmij 1,0:

| Model albo narzędzie | Stawka | Źródło |
|---|---:|---|
| `eleven_v4` | 0,44 | E9, D74; E11, D79 |
| `eleven_multilingual_v2` | 0,44 | E11, D79 |
| `eleven_v3` | 0,44 | E11, D79 |
| `eleven_flash_v2_5` | 0,22 | E11, D79 |
| `text_to_voice` (3 podglądy) | 1,0 | E9, E11 (D78): przyrost licznika równy liczbie znaków tekstu |

Nowo zmierzone stawki dopisz do tej tabeli i do raportu etapu.

Cennik API (2026-11) podaje 0,08 USD za 1000 znaków dla v4, v3 i Multilingual v2 oraz 0,04 USD dla v4 Turbo, v3 Conversational i Flash v2.5. Na subskrypcji ElevenLabs podaje 1 kredyt na znak przed zniżkami. Rzeczywistą stawkę mierzy dopiero hook.

## 3a. Modele z polskim

| Model | Przeznaczenie | Uwagi |
|---|---|---|
| `eleven_v4` | najbardziej ekspresyjny: postacie, dialogi, audiobooki | tagi audio, do 10 000 znaków |
| `eleven_v4_turbo` | czas rzeczywisty (ok. 100 ms) | tagi audio |
| `eleven_v3` | ekspresyjny dialog i narracja | tagi audio, do 5000 znaków, bez `similarity_boost`, `use_speaker_boost` i `speed` |
| `eleven_v3_conversational` | v3 w czasie rzeczywistym (ok. 165 ms) | tagi audio |
| `eleven_multilingual_v2` | lektor, audiobook, długie teksty | najstabilniejszy na długich tekstach, do 10 000 znaków |
| `eleven_flash_v2_5` | szybka i tania konwersja masowa | normalizacja tekstu wyłączona, do 40 000 znaków |
| `eleven_turbo_v2_5` | przestarzały, zastąpiony przez Flash v2.5 | nie używamy w nowych pracach |

`eleven_storytel_v2` jest na liście modeli, ale dokumentacja go nie opisuje.

## 4. Parametry wywołań

- `output_directory`: ścieżka absolutna w `analysis/work/elevenlabs/audio/<zadanie>/`. Audio nie trafia do Git (D76).
  - Katalog musi istnieć przed wywołaniem (`mkdir -p`). Serwer 0.12.2 najpierw generuje i pobiera kredyty, a dopiero potem sprawdza katalog. W E14 przepadło tak 6 podglądów (ok. 890 kr.). Katalog załóż przed wywołaniem: `text_to_speech` odrzuca nieistniejący katalog („not writeable”, bez kosztu).
- `text`: tekst do syntezy po normalizacji z bazy wydania (`fragments.text` albo `lines.text_norm` w `analysis/work/lektor/m2.sqlite`). Jest w nim zapis fonetyczny (D70), liczby słowami i ikony słowami. Surowego tekstu okna nie wysyłaj.
- `model_id`: podawaj zawsze. Modele i obsługę polskiego sprawdzisz bezpłatnie w `list_models`.
- `language`: `pl`. Serwer 0.12.2 nie przekazuje go do API, model rozpoznaje język z tekstu.
- `output_format`: do odsłuchu `mp3_44100_192` (plan Creator), domyślny `mp3_44100_128` też wystarczy. PCM 44,1 kHz wymaga planu Pro.
- Teksty gry wysyłamy tylko w wywołaniach narzędzi. Na konsolę i do raportów w repozytorium ich nie wypisujemy.

## 5. Głosy

- Plan Creator ma 30 miejsc na głosy własne. Zajęte miejsca sprawdzisz w `search_voices`. Nazwy zapisujemy jako `Lektor PL - <postać> <wariant>`.
- `text_to_voice` z polem `text` (100–1000 znaków) daje 3 podglądy, które czytają ten tekst. Podgląd może od razu być próbką do porównania. `create_voice_from_preview` zapisuje tylko wybrany głos.
- Nazwa pliku podglądu zawiera `generated_voice_id` (`voice_design_<id>_<czas>.mp3`). Dokumentacja nie podaje, jak długo identyfikator jest ważny, więc wybrane podglądy zapisuj na koncie niedługo po ocenie.
- Filtr bezpieczeństwa ElevenLabs potrafi odrzucić opis (błąd 403 `blocked_generation`, bez kosztu). W E11 odrzucił „frightened girl… has died”. Przeredaguj opis: dorosła postać („young woman”), bez łączenia dziecka ze śmiercią, i zapisz nową wersję w pliku opisów.
- Serwer 0.12.2 przekazuje do projektu głosu tylko opis i tekst (endpoint `create_previews`, model `eleven_multilingual_ttv_v2`). Model `eleven_ttv_v3`, `seed`, `guidance_scale`, `loudness`, `quality` i referencja audio są dostępne tylko w bezpośrednim API.
- Opis głosu piszemy według wzoru ElevenLabs: „Native Polish. <płeć>, <wiek>. <jakość>.”, potem „Persona: … Emotion: …” i 1–2 zdania o barwie, tempie i sposobie mówienia. Słowo „accent” zostawiamy dla dialektu, a do intonacji używamy słów „intonation” i „emphasis”.
- Parametry `text_to_speech` (`stability`, `similarity_boost`, `style`, `speed`) zmieniają sposób czytania, nie barwę głosu. Barwę wybiera opis albo klon.
- Opis głosu postaci bez dubbingu budujemy z portretu i charakteru z `docs/CASTING.md` (D41). Warianty mają się wyraźnie różnić.
- Opis z wiekiem poniżej 18 lat `text_to_voice` odrzuca (403 `blocked_generation`). Młode postacie opisujemy jako 18–20 lat.
- `voice_clone` (klon natychmiastowy) bierze tylko referencje z `analysis/work/lektor/refs/` i tylko po zgodzie użytkownika w QA. Regulamin ElevenLabs wymaga praw do klonowanego głosu.
- Głosy testowe usuwamy albo zostawiamy według decyzji użytkownika. Stan zapisujemy w `docs/DECISIONS.md`.

## 6. Ocena próbek

Próbki oceniamy tym samym automatem co E3 (CER, ucięta końcówka, tempo, barwa wobec referencji, F0):

```bash
.venv/Scripts/python -I analysis/tools/elevenlabs/score_samples.py [plik ...]
```

Strony odsłuchu i arkusze ocen leżą w `analysis/work/`. Raport w repozytorium podaje same liczby, bez tekstów gry.

## 7. Koniec odpowiedzi: podsumowanie zużycia (obowiązkowe)

W każdej odpowiedzi, w której padło wywołanie MCP ElevenLabs, wiadomość kończy się blokiem zużycia. Licznik konta spóźnia się o około minutę, więc uruchom raport po co najmniej 60 s od ostatniego płatnego wywołania:

```bash
uv run --no-project --python 3.13 analysis/tools/elevenlabs/usage_report.py --summary
```

Wklej wynik bez zmian jako ostatnią część wiadomości zamykającej. Blok podaje:
- zużycie tego prompta z logu, z liczbą szacunków i rekordów bez pomiaru, oraz przyrost licznika konta od znacznika;
- sumę projektu w bieżącym okresie i łącznie, wobec limitu subskrypcji;
- stan konta: zużycie, pozostałe kredyty i datę resetu.

Gdy zużycie z logu różni się od przyrostu licznika, wyjaśnij różnicę jednym zdaniem: opóźnienie licznika, szacunek stawki albo zużycie spoza projektu.
