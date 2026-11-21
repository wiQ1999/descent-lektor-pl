# E20 · Statystyki misji w oknie podsumowania gry

Plugin 1.1.0 dokłada dwa panele po bokach okna podsumowania misji (`UIQuestSummary`). Dane bierze tylko ze standardowego zapisu gry. Decyzje i historia układu: D114.

## Co pokazuje panel

| Panel | Sekcja | Dane gry |
|---|---|---|
| lewy | Ataki | `CoreWeaponClassUsage` przypisane do stałego właściciela klasy (`WeaponPartsModel.GetHero`) + `UniqueWeaponClassUsage[indeks gracza]` (runa) |
| lewy | Wyzwania | `CompletedFeatsInQuest`, `FeatProgresses`, `StartingFeatPoints`: przyrost paska jak w oknie gry, z liczbą ukończonych |
| lewy | Postawy | `SerializedPlayer.VirtueOneValue/VirtueTwoValue`, nazwy z `HeroModel.VirtueOneKey/VirtueTwoKey`: bieżący stan, pasek od środka |
| prawy | Balans gry | `ActionsPerformed`: walka i interakcje całej drużyny |
| prawy | Przebieg misji | `CurrentRound`, `QuestTotalTime`, ataki, interakcje, `ObtainedGold` ÷ rundy |
| prawy | Łup | `ObtainedGold`, `ObtainedTreasureIDs/Qty` według typu modelu: przedmioty, materiały, przepisy, mikstury |

Sortowanie: ataki i wyzwania malejąco. Postawy w kolejności graczy.

Wiersz `quest_summary` w dzienniku pluginu ma te same liczby (bez tekstów gry). `analysis/tools/quest_summary_preview.py` liczy je z pliku `.sav`.

## Czego gra nie zapisuje

- Zabitych wrogów: ani łącznie, ani na bohatera.
- Interakcji i walki poszczególnych bohaterów w całej misji. `ActionsPerformed` liczy drużynę, a ikony akcji nad portretami (`SavedActionIcons`, z bohaterem) gra czyści co rundę. Dziennik misji (`.qlog`) nie notuje interakcji.
- Wyborów postaw w misji: `StoryVirtueChoiceNode` dodaje wagę do wartości postawy, bez historii.

## Testy w grze (2026-11-21, Windows, 1920×1080)

| Test | Wynik |
|---|---|
| Podgląd Ctrl+P w misji (Q7, kilka rund) | panele pokazują bieżące dane; po poprawkach wyglądu zaakceptowane |
| Koniec misji (STORY_QUEST_1, 4 bohaterów) | panel w oknie gry, liczby jak w oknie: 1663,6 s (27:43), 3 rundy, 14 ataków, 12 interakcji, łup 1 / 57 / 3 / 4 |
| Wcześniejszy koniec misji (STORY_QUEST_1) | 1391,0 s = 23:10 w oknie gry, złoto i stan bohaterów zgodne |
| Szerokość panelu | płótno 1920, bez skalowania okna (`scale` 1), panel 303 jednostki |

Zapis gry nie zawiera końcowego stanu misji (zapis z połowy misji nie ma ostatnich akcji, a zapis po misji ma podsumowanie wyzerowane), więc wzorcem dla końca misji jest okno gry. `quest_summary_preview.py compare` sprawdza liczby na zapisie z trwającej misji.

Do zrobienia przy najbliższej sesji na Macu: okno 16:10 (płótno ok. 1728), skala okna gry i czytelność paneli.

## Ustawienia

- `ustawienia.toml`, sekcja `[podsumowanie]`: `statystyki = true` (na start gry). W grze przełącza je checkbox „Statystyki na koniec misji” w menu lektora (na końcu listy „Co czyta lektor”). Companion zapisuje zmianę w pliku.
- `[podsumowanie] podglad = true`: skrót Ctrl+P w misji (tylko do testów, poza szablonem).
