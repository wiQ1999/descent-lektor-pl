#!/bin/bash
# Lektor PL: opcja uruchamiania w Steam  "<folder paczki>/skrypty/start.sh" %command%
#
# Uruchamia grę z Doorstop 4.6 i loaderem lektora (D58). Grę bez lektora uruchamia, gdy:
#   - w folderze paczki jest plik "wylaczony" (Wyłącz lektora.command);
#   - podpis gry nie pozwala wczytać dodatku, np. po aktualizacji w Steam; wtedy pokazuje komunikat.
#
# /bin/bash i arch to pliki systemowe, więc macOS usuwa z ich środowiska zmienne DYLD_*. Dlatego
# DYLD_INSERT_LIBRARIES przekazujemy grze przez `arch -e`, a biblioteki Steama (overlay) bierzemy
# z STEAM_DYLD_INSERT_LIBRARIES, tak jak run.sh z Doorstop.

BUNDLE="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$BUNDLE/logs/start.log"
ENT=com.apple.security.cs.allow-dyld-environment-variables

note() {
    mkdir -p "$BUNDLE/logs" 2>/dev/null
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG" 2>/dev/null
}

# Steam podaje plik wykonywalny z wnętrza .app albo sam pakiet .app.
exe="$1"
shift
case "$exe" in
    *.app/Contents/MacOS/*) ;;
    *)
        app="${exe%/}"
        [ "$app" = "${app%.app}" ] && app="$app.app"
        exe="$app/Contents/MacOS/$(defaults read "$app/Contents/Info" CFBundleExecutable)"
        ;;
esac
app="${exe%%.app/Contents/MacOS/*}.app"
export ARCHPREFERENCE="arm64,x86_64"

if [ -f "$BUNDLE/wylaczony" ]; then
    note "lektor wyłączony, gra bez lektora"
    exec arch "$exe" "$@"
fi

if ! codesign -d --entitlements - --xml "$app" 2>/dev/null | grep -q "$ENT"; then
    note "podpis gry bez $ENT (aktualizacja gry?), gra bez lektora"
    osascript -e 'display dialog "Gra uruchomi się bez lektora, bo po aktualizacji ma nowy podpis.\n\nPo wyjściu z gry uruchom Zainstaluj.command w folderze Descent-Lektor-PL." with title "Lektor PL" buttons {"OK"} default button 1' >/dev/null 2>&1 &
    exec arch "$exe" "$@"
fi

inherited="${DYLD_INSERT_LIBRARIES:-${STEAM_DYLD_INSERT_LIBRARIES:-}}"
inject="$BUNDLE/loader/libdoorstop.dylib${inherited:+:$inherited}"
export DOORSTOP_ENABLED=1
export DOORSTOP_TARGET_ASSEMBLY="$BUNDLE/plugin/LektorPL.Loader.dll"
note "gra z lektorem: $exe"
exec arch -e DYLD_INSERT_LIBRARIES="$inject" "$exe" "$@"
