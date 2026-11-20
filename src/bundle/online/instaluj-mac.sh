#!/bin/bash
# Lektor PL dla Descent: Legends of the Dark (macOS, Apple Silicon): instalacja i aktualizacja jedną komendą.
#
#   W Terminalu:  curl -fsSL https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download/instaluj-mac.sh | bash
#
# Pobiera indeks lektor-mac.txt z tego samego miejsca co skrypt i części paczki, których brakuje w instalacji
# (stan/pakiet.txt), sprawdza ich sumy SHA-256 i rozpakowuje je do stałego folderu ~/Descent-Lektor-PL.
# Potem wywołuje skrypty/lektor.sh install (Python, podpis gry, opcja uruchamiania w schowku). Aktualizacja
# podmienia tylko zmienione części, usuwa pliki, których nowa wersja już nie ma, i zachowuje ustawienia (scalone
# z nowymi domyślnymi), zgłoszenia i dzienniki.
#
# Pliki pobrane przez curl nie dostają kwarantanny, więc Gatekeeper nie blokuje plików .command.
# Pytania czytamy z /dev/tty: przy `curl ... | bash` standardowe wejście to treść skryptu.
# Działa w bash 3.2 z macOS (bez tablic asocjacyjnych i bez jq).
#
# Zmienne środowiskowe (tylko do testów):
#   LEKTOR_ZRODLO  adres albo folder z indeksem i częściami (domyślnie najnowsze wydanie na GitHub)
#   LEKTOR_FOLDER  folder lektora (domyślnie ~/Descent-Lektor-PL)

main() {
    SRC="${LEKTOR_ZRODLO:-https://github.com/wiQ1999/descent-lektor-pl/releases/latest/download}"
    F="${LEKTOR_FOLDER:-$HOME/Descent-Lektor-PL}"
    F="${F%/}"
    STATE="$F/stan"
    DL="$STATE/pobrane"
    INSTALLED="$STATE/pakiet.txt"
    STEAM="$HOME/Library/Application Support/Steam"
    TTY=/dev/tty
    ( : < "$TTY" ) 2>/dev/null || TTY=/dev/null       # bez terminala (np. test) pytań nie będzie

    say ''
    printf '\033[36m%s\033[0m\n' 'Lektor PL: instalacja i aktualizacja'
    if pgrep -f 'Legends of the Dark.app/Contents/MacOS/' >/dev/null 2>&1; then
        fail 'Gra jest uruchomiona. Zamknij ją i uruchom instalację ponownie.'
    fi
    mkdir -p "$DL" || fail "Nie mogę utworzyć folderu $F."

    fetch lektor-mac.txt "$DL/index.txt" || fail 'Nie udało się pobrać listy części (lektor-mac.txt).'
    [ "$(field format "$DL/index.txt")" = 1 ] && [ "$(field platform "$DL/index.txt")" = mac ] ||
        fail 'Ten instalator nie obsługuje pobranej listy części. Uruchom najnowszą komendę z instrukcji.'
    local id version old_id upgrade=0
    id="$(field id "$DL/index.txt")"
    version="$(field version "$DL/index.txt")"
    if [ -f "$INSTALLED" ]; then
        upgrade=1
        old_id="$(field id "$INSTALLED")"
    fi

    # Opcja uruchamiania w Steam wskazuje folder lektora (skrypty/start.sh). Inny folder to stara paczka.
    local launch other paste=1
    launch="$(grep -h 'skrypty/start.sh' "$STEAM"/userdata/*/config/localconfig.vdf 2>/dev/null | head -1)"
    other="$(printf '%s' "$launch" | sed -n 's/.*"\(\/.*\)\/skrypty\/start\.sh.*/\1/p' | sed 's/\\$//')"
    if [ "$other" = "$F" ]; then
        paste=0
    elif [ -n "$other" ]; then
        warn "Steam uruchamia teraz lektora ze starego folderu: $other"
        say 'Po instalacji podmienisz opcję uruchamiania w Steam na nową (instalator skopiuje ją do schowka).'
    fi

    if [ "$upgrade" = 1 ] && [ "$old_id" = "$id" ]; then
        ok "Lektor jest aktualny: $version"
        say "Folder: $F"
        run_lektor
        rm -rf "$DL"
        summary "$paste"
        return 0
    fi

    # Części do pobrania: te, których suma nie występuje w zainstalowanej wersji.
    grep '^part	' "$DL/index.txt" > "$DL/parts.txt"
    : > "$DL/todo.txt"
    local n kind name sha size
    while IFS='	' read -r _ n kind name sha size; do
        if [ "$upgrade" = 1 ] && grep -q "	$sha	" "$INSTALLED"; then continue; fi
        printf '%s\t%s\t%s\t%s\t%s\n' "$n" "$kind" "$name" "$sha" "$size" >> "$DL/todo.txt"
    done < "$DL/parts.txt"
    local count total bytes
    count="$(wc -l < "$DL/todo.txt" | tr -d ' ')"
    total="$(wc -l < "$DL/parts.txt" | tr -d ' ')"
    bytes="$(awk -F'\t' '{s += $5} END {printf "%.0f", s}' "$DL/todo.txt")"
    if [ "$upgrade" = 1 ]; then say "Aktualizacja: $(field version "$INSTALLED")  ->  $version"; else say "Nowa instalacja: $version"; fi
    say "Folder: $F"
    say "Do pobrania: $count z $total części, $(human "$bytes")"
    local free_kb
    free_kb="$(df -k "$F" | awk 'NR == 2 {print $4}')"
    if [ -n "$free_kb" ] && [ "$free_kb" -lt $(( bytes / 1024 * 2 + 300000 )) ]; then
        fail "Za mało miejsca na dysku: potrzeba ok. $(human $(( bytes * 2 + 300000000 ))), wolne $(human $(( free_kb * 1024 )))."
    fi

    # Pliki nowej wersji (posortowane, do porównań przez comm).
    grep '^file	' "$DL/index.txt" | cut -f3- | LC_ALL=C sort -u > "$DL/files.txt"

    local i=0 zip
    while IFS='	' read -r n kind name sha size; do
        i=$((i + 1))
        say "[$i/$count] $name ($(human "$size"))"
        zip="$DL/$name"
        [ -f "$zip" ] && [ "$(file_size "$zip")" = "$size" ] || fetch "$name" "$zip" ||
            fail "Nie udało się pobrać $name. Uruchom komendę ponownie: pobieranie wznowi się od miejsca przerwania."
        if [ "$(sha_of "$zip")" != "$sha" ]; then
            rm -f "$zip"
            fail "Pobrany plik $name ma złą sumę SHA-256. Uruchom komendę ponownie."
        fi
        [ "$kind" = python ] && rm -rf "$F/python"      # nowy Python: lektor.sh rozpakuje go od nowa
        extract "$zip" "$F" || fail "Nie udało się rozpakować $name."
        if [ "$kind" = audio ]; then                     # pliki warstwy przykryte albo usunięte w nowszej wersji
            zip_list "$zip" | LC_ALL=C sort > "$DL/entries.txt"
            LC_ALL=C comm -23 "$DL/entries.txt" "$DL/files.txt" | while IFS= read -r f; do rm -f "$F/$f"; done
        fi
        rm -f "$zip"
    done < "$DL/todo.txt"

    if [ "$upgrade" = 1 ]; then
        grep '^file	' "$INSTALLED" | cut -f3- | LC_ALL=C sort -u > "$DL/old.txt"
        local removed
        removed="$(LC_ALL=C comm -23 "$DL/old.txt" "$DL/files.txt" | grep -v '^python/' | while IFS= read -r f; do
            [ -f "$F/$f" ] && rm -f "$F/$f" && echo x; done | wc -l | tr -d ' ')"
        [ "$removed" != 0 ] && say "Usunięto pliki poprzedniej wersji: $removed"
    fi

    if [ -f "$F/ustawienia.toml" ]; then
        cp "$F/ustawienia.toml" "$STATE/ustawienia.przed-aktualizacja.toml"
        merge_settings "$F/ustawienia.toml" "$F/skrypty/ustawienia.domyslne.toml" > "$DL/ustawienia.toml" &&
            mv "$DL/ustawienia.toml" "$F/ustawienia.toml"
        say 'Ustawienia zachowane (nowe opcje dostały wartości domyślne).'
    else
        cp "$F/skrypty/ustawienia.domyslne.toml" "$F/ustawienia.toml"
    fi

    run_lektor
    cp "$DL/index.txt" "$INSTALLED"
    rm -rf "$DL"
    say ''
    if [ "$upgrade" = 1 ]; then ok "Zaktualizowano do: $version"; else ok "Zainstalowano: $version"; fi
    summary "$paste"
}

say() { printf '%s\n' "$*"; }
ok() { printf '\033[32m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*"; }
fail() {
    printf '\n\033[31mBłąd: %s\033[0m\n' "$*"
    exit 1
}

field() { awk -F'\t' -v k="$1" '$1 == k {sub(/^[^\t]*\t/, ""); print; exit}' "$2"; }
file_size() { wc -c < "$1" | tr -d ' '; }
human() { awk -v b="$1" 'BEGIN {if (b >= 1073741824) printf "%.1f GB", b / 1073741824; else printf "%.0f MB", (b < 1048576 ? 1 : b / 1048576)}'; }

sha_of() {
    if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1"; else sha256sum "$1"; fi | awk '{print $1}'
}

# Adres http(s) albo folder (testy). -C -: wznawia przerwane pobieranie dużej części.
fetch() {
    case "$SRC" in
        http://* | https://*)
            local bar=--silent
            case "$1" in *.zip) bar=--progress-bar ;; esac
            curl -fL --retry 3 --show-error "$bar" -C - -o "$2" "${SRC%/}/$1" ;;
        *) cp "$SRC/$1" "$2" ;;
    esac
}

# ditto z macOS zachowuje polskie nazwy plików i prawa wykonywania; unzip tylko poza macOS (testy).
extract() {
    if command -v ditto >/dev/null 2>&1; then ditto -x -k "$1" "$2"; else unzip -q -o "$1" -d "$2"; fi
}
zip_list() { unzip -Z1 "$1"; }

# Nowy plik domyślny z wartościami użytkownika dla kluczy, które ma w swoim pliku (baza i audio zawsze z nowej wersji).
merge_settings() {
    awk '
        function key_of(line,   k) {
            if (!match(line, /^[ \t]*[A-Za-z0-9_-]+[ \t]*=/)) return ""
            k = substr(line, RSTART, RLENGTH); gsub(/[ \t=]/, "", k); return sec "." k
        }
        FNR == 1 { sec = "" }
        /^[ \t]*\[/ { sec = $0; gsub(/^[ \t]*\[|\].*$/, "", sec); if (FNR == NR) next; print; next }
        FNR == NR { k = key_of($0); if (k != "" && k != ".db" && k != ".audio") mine[k] = $0; next }
        { k = key_of($0); if (k != "" && (k in mine)) print mine[k]; else print }
    ' "$1" "$2"
}

run_lektor() {
    /bin/bash "$F/skrypty/lektor.sh" install --quiet "$@" < "$TTY" ||
        fail 'Instalacja w grze nie powiodła się (komunikat powyżej).'
}

summary() {
    say "Folder lektora (ustawienia.toml, Test dźwięku, Odinstaluj): $F"
    if [ "$1" = 1 ]; then
        say ''
        say 'Opcja uruchamiania jest w schowku. Wklej ją w Steam:'
        say '  prawy przycisk na grze > Właściwości > Ogólne > Opcje uruchamiania (zastąp stary tekst), potem Cmd+V.'
    fi
    say 'Uruchom grę normalnie ze Steama: lektor wystartuje razem z nią.'
    say 'Aktualizacja: ta sama komenda. Folderu lektora nie przenoś.'
}

main "$@"
