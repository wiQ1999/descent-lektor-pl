# Build macOS – weryfikacja

Źródło: depot Steam 1611072 (manifest 4011719406701483666), pobrany przez DepotDownloader 3.4.0 do `analysis/work/mac_depot/`: 401 plików, 3 015 764 158 B.
Porównanie z kopią buildu Windows z `analysis/work/game/`.
Skrypt: `analysis/tools/mac_compare.py`, wynik w `analysis/work/out/mac_compare.json` (bez tekstów gry).

```
.venv/Scripts/python -I analysis/tools/mac_compare.py --ilspy <ścieżka do ilspycmd.exe>
```

## Wynik w skrócie

Build macOS to ta sama gra co na Windows, tylko zbudowana dla innej platformy. Backend to Mono, kod klas potrzebnych lektorowi jest identyczny, a teksty i polskie audio są takie same.
Problemem nie jest więc hook, tylko **wczytanie własnego kodu**. Aplikacja ma Hardened Runtime bez `allow-dyld-environment-variables`, więc Doorstop przez `DYLD_INSERT_LIBRARIES` nie zadziała bez przepodpisania pakietu.

## 1. Backend, architektura, wersja

| | macOS | Windows |
|---|---|---|
| Backend skryptów | Mono (`Data/Managed/Assembly-CSharp.dll`, `libmonobdwgc-2.0.dylib`); brak `GameAssembly.dylib` i `global-metadata.dat`, więc to nie IL2CPP | Mono x86 |
| Architektura | uniwersalny Mach-O: x86_64 (minOS 10.13) + arm64 (minOS 11.0) | x86 (32-bit) |
| Unity (nagłówki UnityFS) | 2022.3.62f2 | 2022.3.62f2 |
| Wersja gry (`manifest.dat`, `CFBundleShortVersionString`) | 2.0.10 | 2.0.10 |
| Bundle ID | `com.fantasyflightgames.d3` | – |

- Natywny arm64 obejmuje wszystkie istotne Mach-O: plik główny (mały launcher ładujący `@executable_path/../Frameworks/UnityPlayer.dylib`), `UnityPlayer.dylib`, biblioteki Mono (`libmonobdwgc-2.0`, `libmono-native`, `libMonoPosixHelper`) i wtyczki `PlugIns/AkSoundEngine.bundle` oraz `lib_burst_generated.bundle`. Na Macach z Apple Silicon gra działa więc natywnie, bez Rosetty.
- W buildzie nie ma Steamworks (`steam_api`), a konta obsługuje AWS Cognito. Gra najpewniej startuje bez klienta Steam; do sprawdzenia na Macu z Apple Silicon.

## 2. Podpis i entitlements (rcodesign 0.29.0)

- Podpis Developer ID, team `7G6J35757P`. CodeDirectory ma flagę `CodeSignatureFlags(RUNTIME)` (Hardened Runtime) i runtime_version 13.1.0 w pliku głównym; biblioteki są podpisane z runtime 10.9–14.2.
- Entitlements (identyczne w `.app` i w pliku głównym):
  - `com.apple.security.cs.disable-library-validation` = true;
  - `com.apple.security.cs.disable-executable-page-protection` = true.
- **Brak** `com.apple.security.cs.allow-dyld-environment-variables`, `allow-jit`, `allow-unsigned-executable-memory` i `get-task-allow`.
- `_CodeSignature/CodeResources` pieczętuje cały katalog `Resources/Data/` (730 wpisów), w tym `Managed/Assembly-CSharp.dll`, `ScriptingAssemblies.json` i `RuntimeInitializeOnLoads.json`.

### Wniosek: Doorstop przez `DYLD_INSERT_LIBRARIES`

**Bez przepodpisania nie zadziała.** Przy Hardened Runtime dyld ignoruje zmienne `DYLD_*`, jeśli plik nie ma `allow-dyld-environment-variables`. Tak działają skrypty startowe BepInEx/Doorstop na macOS.

Co pomaga, a co nie:
- `disable-library-validation` = true pozwala załadować bibliotekę podpisaną ad-hoc lub przez innego dewelopera, ale dopiero gdy coś ją ładuje (`dlopen`, dodatkowe `LC_LOAD_DYLIB`). Samo nie daje punktu wejścia.
- Żeby Doorstop działał, trzeba zmienić podpis pliku głównego. Są dwie drogi: przepodpisać ad-hoc (`codesign -f -s -`) bez flagi runtime albo z dodanym `allow-dyld-environment-variables`. Każda zmiana pakietu psuje pieczęć Developer ID i znika po aktualizacji lub weryfikacji plików w Steam.
- Na macOS 13+ modyfikacja pakietu innego dewelopera wymaga zgody „Zarządzanie aplikacjami” (App Management) dla programu, który ją wykonuje.

## 3. Kod (dekompilacja ILSpy 11.2)

- `Assembly-CSharp.dll` różni się hashem (mac `829d7c71…`, win `9cbb619b…`), ale po dekompilacji różni się tylko 5 z 1573 plików `.cs`. Wszystkie różnice wynikają z platformy:
  - `CoreApplication`: nazwa platformy;
  - `CoreApplicationDelegate`: `open` zamiast `explorer` przy otwieraniu folderu;
  - `AssetBundleLoader`: `StandaloneOSX` zamiast `StandaloneWindows`;
  - `AudioController.GetSoundbankPath`: `Application.persistentDataPath` zamiast `dataPath`;
  - `SaveLoadController`: zapisy w `Application.persistentDataPath`.
- `MessageController` (40 członków), `StoryMessageController` (13) i `MasterMessageCache` (31) są **identyczne plik w plik**.
  - Jest delegat `MessageController.MessageDisplayBegin`, wywoływany przed pokazaniem komunikatu z `IMessageRequest`.
  - Jest delegat `MessageDisplayEnd`, wywoływany po zamknięciu okna; to jest zdarzenie zamknięcia.
  - Jest `StoryMessageController.DisplayMessage(IMessageRequest, StoryMessageSettings, bool)`.
  - `StoryMessageController` nie ma zdarzeń. Ma publiczne `IsShowingMessage` (zależne od prywatnego `_curProcessingMessage`) i `SubmitMessageFinish(...)`.
- Oba kontrolery są dostępne przez `PersistentGameObject.Instance` (`SingletonBehaviour<T>`): `Messages` i `StoryMessages`.

## 4. Dane

- `manifest.dat`: wersja 2.0.10 po obu stronach, po 200 bundli. Różnią się tylko nazwy bundli audio (`audio/mac/*` zamiast `audio/windows/*`); bundle tekstów mają te same nazwy.
- Teksty `loc/pl` + `qloc`: 17 156 kluczy po obu stronach, 0 kluczy tylko w jednym buildzie, **0 różnic treści**.
- Polskie audio (`audio/mac/polish` vs `audio/windows/polish`):
  - pakiety `.pck` różnią się o 12 B (nagłówek lub wyrównanie);
  - wszystkie 356 mediów ma identyczne md5;
  - `VOICES.md`, referencje głosów i zakres milestone 1 (`M1_SCOPE.md`) obowiązują bez zmian.

## 5. Rekomendacja

### Hook: ten sam kod co na Windows, ale bez detourów

Lektor nie potrzebuje Harmony. Wystarczy własny `MonoBehaviour`, który:
- subskrybuje `PersistentGameObject.Instance.Messages.MessageDisplayBegin` i `MessageDisplayEnd` (komunikaty questu: klucz, argumenty, zamknięcie okna);
- w `Update` sprawdza `StoryMessages.IsShowingMessage` i przez refleksję czyta `_curProcessingMessage` (okna fabularne). Opóźnienie wynosi najwyżej jedną klatkę, a zamknięcie okna to przejście `IsShowingMessage` z true na false.

Bez Harmony i MonoMod znika niepewność co do natywnych detourów na arm64. Na Windows możemy zostać przy patchu Harmony na `DisplayMessage` albo użyć tego samego odpytywania, żeby kod był wspólny.

### Wczytanie kodu na macOS (natywny arm64), w kolejności preferencji

1. **Kopia pakietu poza folderem Steam.** Kopiujemy `.app` do własnego katalogu i przepodpisujemy ad-hoc z `allow-dyld-environment-variables` (albo bez flagi runtime). Potem uruchamiamy ją z Doorstop przez `DYLD_INSERT_LIBRARIES`, przez skrypt albo opcję uruchamiania Steam.
   - Plusy: oryginał w Steam zostaje nietknięty. Zapisy i ustawienia leżą w `persistentDataPath`, więc są wspólne z oryginałem.
   - Minusy: po każdej aktualizacji gry trzeba odświeżyć kopię (ok. 3 GB). Trzeba też sprawdzić na Macu z Apple Silicon, czy Doorstop ma build arm64 zgodny z Mono Unity 2022.3.
2. **Wpis loadera bez natywnego kodu.** Dopisujemy własny DLL do `Data/ScriptingAssemblies.json` i metodę do `Data/RuntimeInitializeOnLoads.json`. Unity sam go wczyta i wywoła; gra już używa tego mechanizmu dla 23 metod z 7 assembly.
   - Plusy: nie potrzeba Doorstop, `DYLD_*` ani przepodpisywania pliku wykonywalnego. Ten sam mechanizm działa na Windows.
   - Minusy: zmieniamy zapieczętowane zasoby (dwa JSON + nowy DLL). To hipoteza do sprawdzenia na Macu z Apple Silicon: czy macOS uruchomi pakiet z naruszoną pieczęcią zasobów bez kwarantanny i czy Steam nie nadpisze plików przy aktualizacji. Najbezpieczniej robić to na kopii z wariantu 1.
3. **Hook pod Rosettą (slice x86_64).** Odradzam.
   - Rosetta nie omija Hardened Runtime, więc problem z `DYLD_INSERT_LIBRARIES` jest ten sam.
   - Daje tylko zgodność z x86-owymi buildami BepInEx/MonoMod, a my nie potrzebujemy detourów.
   - Apple zapowiedziało, że macOS 27 to ostatnia wersja z pełną Rosettą 2; później zostanie tylko ograniczony podzbiór dla starszych gier. To rozwiązanie z terminem ważności.
4. **OCR (zapas).** Osobny proces z uprawnieniem do nagrywania ekranu wycina okno dialogowe, rozpoznaje tekst i dopasowuje go rozmyto do znanych 17 156 tekstów.
   - Plusy: OCR musi tylko wskazać klucz, a nie odczytać tekst bezbłędnie. Pakiet zostaje nietknięty i aktualizacje go nie psują.
   - Minusy: brak mówcy i wariantów `{n}` wprost (trzeba je odtwarzać z dopasowania), opóźnienie, wrażliwość na rozdzielczość i skalowanie UI. Trzeba sprawdzić jakość OCR dla polskich znaków.

### Ryzyka

- **Aktualizacje Steam:** wariant 2 na oryginale zostanie nadpisany; wariant 1 wymaga ponownej kopii i podpisu. Mapowanie hooka nie zależy od offsetów, więc przetrwa aktualizacje, dopóki nie zmienią się nazwy klas i pól.
- **Gatekeeper / App Management:** przepodpisany pakiet traci notaryzację. Uruchamiany lokalnie bez atrybutu kwarantanny powinien działać, ale wymaga to testu na Macu z Apple Silicon z aktualnym macOS.
- **Pole prywatne `_curProcessingMessage`:** refleksja może przestać działać po zmianie nazwy w aktualizacji. Trzeba mieć na to obsługę błędów i log.
- **Doorstop arm64:** dostępność i stabilność buildu arm64 dla Unity 2022.3 Mono trzeba sprawdzić przed decyzją.
- **Rosetta:** wariant 3 przestanie działać po macOS 27.

### Do sprawdzenia na Macu z Apple Silicon (kolejność)

1. Czy gra startuje z kopii pakietu poza folderem Steam, bez klienta Steam.
2. Czy kopia po ad-hoc re-sign z `allow-dyld-environment-variables` ładuje Doorstop arm64.
3. Czy kopia z dopisanym wpisem w `RuntimeInitializeOnLoads.json` wywołuje własną metodę (bez Doorstop).
4. Czy test `MessageDisplayBegin` + odpytywanie `IsShowingMessage` loguje klucze w Q1.
