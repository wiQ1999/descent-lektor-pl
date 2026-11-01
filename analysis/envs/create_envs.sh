#!/usr/bin/env bash
# Środowiska kandydatów porównania TTS (E0), poza repozytorium: %LOCALAPPDATA%\LektorPL\envs\<nazwa>.
# Pakiety są hardlinkami z cache uv (ten sam dysk C:), więc kolejne środowiska zajmują mało miejsca.
# Gdy istnieje <nazwa>.txt, instaluje dokładnie te wersje; inaczej rozwiązuje zależności i zapisuje <nazwa>.txt.
#
# Uruchomienie (Git Bash): bash analysis/envs/create_envs.sh [chatterbox3] [xtts] [omnivoice]
set -euo pipefail
PY="$LOCALAPPDATA/LektorPL/python/cpython-3.12.13-windows-x86_64-none/python.exe"
ENVS="$LOCALAPPDATA/LektorPL/envs"
HERE="$(cd "$(dirname "$0")" && pwd)"
CB_SHA=5de7a54aa4e5e2baadb0182dde554908b48b85c2   # resemble-ai/chatterbox master, 2026-07-21 (T3 v3)
OV_SHA=08be0b4ccbac3e13e374e86fbfead4b4cac343e2   # k2-fsa/OmniVoice master, 2026-08-24

build() {  # nazwa, indeks PyTorch, pakiety...
    local name=$1 index=$2; shift 2
    local py="$ENVS/$name/Scripts/python.exe"
    [ -x "$py" ] || uv venv --python "$PY" "$ENVS/$name"
    local opts=(--python "$py" --link-mode hardlink --index "$index" --index-strategy unsafe-best-match)
    if [ -f "$HERE/$name.txt" ]; then
        uv pip install "${opts[@]}" --no-deps -r "$HERE/$name.txt"
    else
        uv pip install "${opts[@]}" "$@"
        uv pip freeze --python "$py" > "$HERE/$name.txt"
    fi
}

[ $# -gt 0 ] || set -- chatterbox3 xtts omnivoice
for n in "$@"; do
    case $n in
      chatterbox3) build chatterbox3 https://download.pytorch.org/whl/cu124 \
                     "chatterbox-tts @ git+https://github.com/resemble-ai/chatterbox@$CB_SHA" ;;
      xtts)        build xtts https://download.pytorch.org/whl/cu124 \
                     coqui-tts==0.28.0 torch==2.6.0 torchaudio==2.6.0 ;;
      omnivoice)   build omnivoice https://download.pytorch.org/whl/cu128 \
                     "omnivoice @ git+https://github.com/k2-fsa/OmniVoice@$OV_SHA" torch==2.8.0 torchaudio==2.8.0 ;;
      *) echo "nieznane środowisko: $n" >&2; exit 2 ;;
    esac
done
