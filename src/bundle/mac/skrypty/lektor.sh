#!/bin/bash
# Lektor PL dla Descent: Legends of the Dark (macOS, Apple Silicon). Uruchamiany z plików .command w folderze paczki.
#
#   install    zdejmuje kwarantannę z folderu, rozpakowuje Pythona, znajduje grę w Steam, nadaje jej podpis ad-hoc
#              z uprawnieniem do DYLD_* (D25, D58) i kopiuje do schowka opcję uruchamiania dla Steama.
#              Ponowne uruchomienie naprawia instalację, np. po aktualizacji gry, która przywraca jej podpis.
#   uninstall  usuwa stan instalacji i podaje 2 kroki w Steam (opcja uruchamiania, weryfikacja plików gry).
#   disable    gra startuje bez lektora (plik "wylaczony" czyta start.sh); enable włącza go z powrotem.
#   test       odtwarza jedną kwestię narratora z ustawieniami z ustawienia.toml (Test dźwięku).
#   status     stan instalacji i najnowsze dzienniki.
#
# Skrypt działa w bash 3.2 z macOS. Stan instalacji leży w folderze paczki (stan/), dzienniki w logs/.

BUNDLE="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$BUNDLE/stan"
STATE_FILE="$STATE/instalacja.txt"
PY="$BUNDLE/python/bin/python3"
SITE="$BUNDLE/python/lib/python3.12/site-packages"
DOORSTOP="$BUNDLE/loader/libdoorstop.dylib"
SETTINGS="$BUNDLE/ustawienia.toml"
STEAM="$HOME/Library/Application Support/Steam"
APP_ID=1611070
ENT=com.apple.security.cs.allow-dyld-environment-variables
PLISTBUDDY="${PLISTBUDDY:-/usr/libexec/PlistBuddy}"   # test na Windows podstawia własny
APP_MANAGEMENT='x-apple.systempreferences:com.apple.preference.security?Privacy_AppBundles'

say() { printf '%s\n' "$*"; }
ok() { printf '\033[32m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*"; }
finish() {
    say ''
    say 'Możesz zamknąć to okno.'
    exit "${1:-0}"
}
fail() {
    printf '\n\033[31mBłąd: %s\033[0m\n' "$*"
    finish 1
}

game_running() { pgrep -f 'Legends of the Dark.app/Contents/MacOS/' >/dev/null 2>&1; }

assert_closed() {
    if game_running; then fail 'Gra jest uruchomiona. Zamknij ją i uruchom ten plik ponownie.'; fi
}

assert_installed() {
    [ -f "$STATE_FILE" ] || fail 'Lektor nie jest zainstalowany. Najpierw uruchom Zainstaluj.command.'
}

state_value() { sed -n "s/^$1=//p" "$STATE_FILE" 2>/dev/null | head -1; }

check_location() {
    case "$BUNDLE/" in
        "$HOME/Desktop/"* | "$HOME/Documents/"* | "$HOME/Downloads/"* | "$HOME/Library/Mobile Documents/"*)
            fail "Folder leży w miejscu chronionym przez macOS: $BUNDLE
Gra nie mogłaby z niego wczytać lektora. Przenieś folder Descent-Lektor-PL do katalogu domowego ($HOME) i uruchom Zainstaluj.command ponownie." ;;
        /Volumes/*)
            fail "Folder leży na dysku zewnętrznym albo pendrivie: $BUNDLE
Skopiuj go do katalogu domowego ($HOME) i uruchom Zainstaluj.command ponownie." ;;
    esac
}

unpack_python() {
    if [ ! -x "$PY" ]; then
        say 'Rozpakowuję Pythona...'
        tar -xzf "$BUNDLE/python/python.tar.gz" -C "$BUNDLE" || fail 'Nie udało się rozpakować Pythona (python/python.tar.gz).'
    fi
    if [ -d "$BUNDLE/python/site-packages" ]; then
        mkdir -p "$SITE"
        cp -R "$BUNDLE/python/site-packages/." "$SITE/" || fail 'Nie udało się skopiować bibliotek Pythona.'
        rm -rf "$BUNDLE/python/site-packages"
    fi
    "$PY" -I -c 'import lektor.companion.app, numpy, sounddevice, soundfile' ||
        fail 'Python z paczki nie działa. Wyślij autorowi paczki zrzut tego okna.'
}

# Biblioteki Steam: główna i dodatkowe z libraryfolders.vdf; w każdej appmanifest gry wskazuje folder.
find_game() {
    local vdf="$STEAM/steamapps/libraryfolders.vdf" lib acf dir app
    {
        printf '%s\n' "$STEAM"
        [ -f "$vdf" ] && sed -n 's/^[[:space:]]*"path"[[:space:]]*"\(.*\)"[[:space:]]*$/\1/p' "$vdf"
    } | while IFS= read -r lib; do
        acf="$lib/steamapps/appmanifest_$APP_ID.acf"
        [ -f "$acf" ] || continue
        dir="$(sed -n 's/^[[:space:]]*"installdir"[[:space:]]*"\(.*\)"[[:space:]]*$/\1/p' "$acf" | head -1)"
        for app in "$lib/steamapps/common/$dir"/*.app; do
            if [ -d "$app" ]; then printf '%s\n' "$app"; break 2; fi
        done
    done
}

ask_game() {
    warn 'Nie znalazłem gry w bibliotekach Steam.' >&2
    say 'W Steam kliknij grę prawym przyciskiem i wybierz Zarządzaj > Przeglądaj pliki lokalne.' >&2
    say 'Przeciągnij plik Legends of the Dark z otwartego okna Findera tutaj i naciśnij Enter.' >&2
    local app
    read -r -p 'Gra: ' app
    # Terminal wkleja ścieżkę z ukośnikami przed spacjami i spacją na końcu.
    app="$(printf '%s' "$app" | sed -e 's/[[:space:]]*$//' -e 's/\\\(.\)/\1/g')"
    app="${app%/}"
    [ -d "$app/Contents/MacOS" ] || return 1
    printf '%s\n' "$app"
}

has_entitlement() { codesign -d --entitlements - --xml "$1" 2>/dev/null | grep -q "$ENT"; }

# Podpis ad-hoc z dotychczasowymi uprawnieniami i dodatkowym allow-dyld-environment-variables (D25).
resign() {
    local app="$1" tmp
    tmp="$(mktemp -d)"
    codesign -d --entitlements - --xml "$app" > "$tmp/ent.plist" 2>/dev/null
    if [ ! -s "$tmp/ent.plist" ]; then
        rm -f "$tmp/ent.plist"
        "$PLISTBUDDY" -c 'Clear dict' "$tmp/ent.plist" >/dev/null
    fi
    "$PLISTBUDDY" -c "Add :$ENT bool true" "$tmp/ent.plist" 2>/dev/null ||
        "$PLISTBUDDY" -c "Set :$ENT true" "$tmp/ent.plist"
    if ! codesign -f -s - --options runtime --entitlements "$tmp/ent.plist" "$app" 2>"$tmp/err" &&
        ! { grep -qi 'detritus' "$tmp/err" && xattr -cr "$app" 2>/dev/null &&
            codesign -f -s - --options runtime --entitlements "$tmp/ent.plist" "$app" 2>"$tmp/err"; }; then
        if grep -qi 'not permitted' "$tmp/err"; then
            open "$APP_MANAGEMENT"
            rm -rf "$tmp"
            fail 'macOS nie pozwolił zmienić podpisu gry.
W otwartym oknie Ustawień systemowych (Prywatność i ochrona > Zarządzanie aplikacjami) włącz Terminal.
Potem zamknij Terminal (Cmd+Q) i uruchom Zainstaluj.command ponownie.'
        fi
        cat "$tmp/err"
        rm -rf "$tmp"
        fail 'Nie udało się zmienić podpisu gry.'
    fi
    rm -rf "$tmp"
    has_entitlement "$app" || fail 'Podpis gry nie ma potrzebnego uprawnienia mimo zmiany.'
}

do_install() {
    check_location
    xattr -dr com.apple.quarantine "$BUNDLE" 2>/dev/null
    chmod +x "$BUNDLE"/*.command "$BUNDLE"/skrypty/*.sh 2>/dev/null
    assert_closed
    unpack_python

    local app
    app="$(find_game)"
    [ -n "$app" ] || app="$(ask_game)" || fail 'To nie jest pakiet gry (.app).'
    say "Gra: $app"

    codesign -v "$DOORSTOP" 2>/dev/null || codesign -f -s - "$DOORSTOP" || fail 'Nie udało się podpisać loadera (libdoorstop.dylib).'
    if has_entitlement "$app"; then
        say 'Podpis gry ma już potrzebne uprawnienie.'
    else
        say 'Zmieniam podpis gry, żeby mogła wczytać lektora...'
        resign "$app"
        ok 'Podpis gry zmieniony.'
    fi

    mkdir -p "$STATE" "$BUNDLE/logs"
    {
        printf '# Lektor PL: instalacja z %s. Nie usuwaj, dopóki lektor jest zainstalowany.\n' "$(date '+%Y-%m-%d %H:%M:%S')"
        printf 'game=%s\n' "$app"
    } > "$STATE_FILE"
    rm -f "$BUNDLE/wylaczony"

    local launch="\"$BUNDLE/skrypty/start.sh\" %command%"
    printf '%s' "$launch" | pbcopy
    say ''
    ok 'Zainstalowano.'
    say ''
    say 'Opcja uruchamiania jest w schowku:'
    say "  $launch"
    say ''
    say 'Jeśli to pierwsza instalacja, wklej ją w Steam:'
    say '  prawy przycisk na grze > Właściwości > Ogólne > Opcje uruchamiania, potem Cmd+V.'
    say 'Po aktualizacji gry opcja zostaje, wystarczy ponownie uruchomić Zainstaluj.command.'
    say 'Nie przenoś ani nie usuwaj tego folderu bez odinstalowania.'
    finish 0
}

do_uninstall() {
    assert_closed
    assert_installed
    rm -rf "$STATE"
    rm -f "$BUNDLE/wylaczony"
    ok 'Odinstalowano lektora z paczki. Zostały 2 kroki w Steam:'
    say '  1. Prawy przycisk na grze > Właściwości > Ogólne > Opcje uruchamiania: usuń cały tekst.'
    say '  2. Właściwości > Zainstalowane pliki > Zweryfikuj spójność plików gry.'
    say '     Steam przywróci oryginalny plik gry z jego podpisem.'
    say 'Potem możesz usunąć folder Descent-Lektor-PL.'
    finish 0
}

do_disable() {
    assert_installed
    touch "$BUNDLE/wylaczony"
    ok 'Lektor wyłączony: gra startuje bez niego. Włączysz go plikiem Włącz lektora.command.'
    finish 0
}

do_enable() {
    assert_installed
    rm -f "$BUNDLE/wylaczony"
    ok 'Lektor włączony. Uruchom grę ze Steama.'
    finish 0
}

do_test() {
    [ -x "$PY" ] || fail 'Python z paczki nie jest rozpakowany. Najpierw uruchom Zainstaluj.command.'
    say 'Odtwarzam jedną kwestię narratora...'
    "$PY" -I -m lektor.companion --test --config "$SETTINGS" --logs "$BUNDLE/logs" ||
        fail 'Test dźwięku nie powiódł się. Sprawdź ustawienia.toml (literówka?).'
    ok 'Jeśli nic nie było słychać: sprawdź głośność (volume) i urządzenie (device) w Ustawieniach.'
    finish 0
}

do_status() {
    if [ ! -f "$STATE_FILE" ]; then say 'Lektor nie jest zainstalowany.'; finish 0; fi
    local app
    app="$(state_value game)"
    say "Gra: $app"
    if has_entitlement "$app"; then say 'Podpis gry: pozwala wczytać lektora'; else warn 'Podpis gry: oryginalny (po aktualizacji?), uruchom Zainstaluj.command'; fi
    if [ -f "$BUNDLE/wylaczony" ]; then say 'Lektor: wyłączony'; else say 'Lektor: włączony'; fi
    local f
    for f in loader hook companion start; do
        f="$(ls -t "$BUNDLE/logs/$f"-*.* "$BUNDLE/logs/$f".* 2>/dev/null | head -1)"
        [ -n "$f" ] && say "  $(basename "$f")"
    done
    finish 0
}

case "${1:-status}" in
    install) do_install ;;
    uninstall) do_uninstall ;;
    disable) do_disable ;;
    enable) do_enable ;;
    test) do_test ;;
    status) do_status ;;
    *) fail "Nieznane polecenie: $1" ;;
esac
