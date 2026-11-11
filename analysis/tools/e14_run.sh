#!/usr/bin/env bash
# Faza B E14 (D95): całe audio M3 w kolejności gry, bez przerw na odsłuch. Uruchamiać z katalogu głównego
# w aplikacji Claude (środowisko OmniVoice działa tylko w niej), komputer nie może zasnąć:
#
#   bash analysis/tools/e14_run.sh                  # każdy krok jest wznawialny: po przerwie ta sama komenda
#   .venv/Scripts/python -I -m lektor progress --release m3 [--all]    # postęp (też analysis/work/audio/m3/progress.md)
#
# Kroki: ElevenLabs (B1, sieć, płatne, limit MAX_CREDITS na całe wydanie) równolegle z OmniVoice (B2, GPU);
# potem evaluate i select, do ROUNDS rund ponownych podejść obu silników, ocena końcowa, finalize i audio-report.
# Strażnik generate (D12) przerywa wsad przy spadaniu do pamięci systemowej: skrypt wznawia go po minucie,
# dopóki przybywa podejść. Dzienniki: analysis/work/audio/m3/logs/.
#
# Wydanie częściowe (D96): ACTS="1 3" ogranicza generowanie i ocenę do aktu 1 i części wspólnych, ELEVEN=0 pomija
# ElevenLabs, ASR_FP32=1 liczy Whispera w fp32, ROUNDS ustala liczbę rund ponownych podejść.
set -u
cd "$(dirname "$0")/../.."
REL=m3
PY=.venv/Scripts/python
OMNI="$LOCALAPPDATA/LektorPL/envs/omnivoice/Scripts/python.exe"
AUDIO=analysis/work/audio/$REL
LOGS=$AUDIO/logs
MAX_CREDITS=${MAX_CREDITS:-58000}       # zatwierdzone w QA B1 (D95): ok. 44 tys. + ponowne podejścia
ROUNDS=${ROUNDS:-3}
SNAPSHOT_S=${SNAPSHOT_S:-600}
ACTS=${ACTS:-}
ELEVEN=${ELEVEN:-1}
ASR_FP32=${ASR_FP32:-0}
ACT_ARGS=()
[ -n "$ACTS" ] && ACT_ARGS=(--acts $ACTS)
EVAL_ARGS=("${ACT_ARGS[@]}")
[ "$ASR_FP32" = 1 ] && EVAL_ARGS+=(--fp32)
mkdir -p "$LOGS"

log() { echo "$(date '+%F %T') $*" | tee -a "$LOGS/run.log"; }
mark() { "$PY" -I -m lektor progress --release $REL --mark "$1"; log "== $1"; snapshot; }
snapshot() {
    "$PY" -I -m lektor progress --release $REL > "$AUDIO/progress.tmp" 2>> "$LOGS/run.log" &&
        mv -f "$AUDIO/progress.tmp" "$AUDIO/progress.md"
}
lines() { [ -f "$1" ] && wc -l < "$1" || echo 0; }
budget() {
    "$PY" -I -c "from lektor import paths, progress; paths.use('$REL'); print(max(0, $MAX_CREDITS - round(progress.spent_credits())))"
}
retakes() { "$PY" -I -c "import json; print(len(json.load(open('$AUDIO/retake.json', encoding='utf-8'))))"; }

omni() {    # generate z wznawianiem po strażniku; trzy przerwy z rzędu bez nowych podejść kończą krok błędem
    local stuck=0 before code
    while [ $stuck -lt 3 ]; do
        before=$(lines "$AUDIO/takes.jsonl")
        "$OMNI" -I -m lektor generate --release $REL "$@" "${ACT_ARGS[@]}" >> "$LOGS/generate.log" 2>&1 && return 0
        code=$?
        log "generate $*: kod $code, wznowienie za 60 s"
        if [ "$(lines "$AUDIO/takes.jsonl")" -gt "$before" ]; then stuck=0; else stuck=$((stuck + 1)); fi
        sleep 60
    done
    log "generate $*: trzy przerwy bez nowych podejść"
    return 1
}

eleven() {  # budżet liczony od nowa przed każdym wsadem: suma kredytów podejść M3 nie przekroczy MAX_CREDITS
    local n b code
    for n in 1 2 3 4 5; do
        b=$(budget)
        "$PY" -I -m lektor eleven --release $REL "$@" --max-credits "$b" >> "$LOGS/eleven.log" 2>&1 && return 0
        code=$?
        log "eleven $*: kod $code (budżet $b kr.), ponowienie za 120 s"
        sleep 120
    done
    return 1
}

step() {    # krok w .venv; błąd kończy skrypt (wznowienie tą samą komendą)
    "$PY" -I -m lektor "$1" --release $REL "${@:2}" >> "$LOGS/$1.log" 2>&1 || { mark "przerwane: $1"; exit 1; }
}

both() {    # ElevenLabs w tle, OmniVoice na pierwszym planie; GPU zwalnia się dopiero po obu
    local el=
    if [ "$ELEVEN" = 1 ]; then eleven "$@" & el=$!; fi
    omni "$@"
    local om=$?
    [ -z "$el" ] || wait $el || log "eleven $*: niedokończone (szczegóły w logs/eleven.log)"
    [ $om -eq 0 ] || { mark "przerwane: generate $*"; exit 1; }
}

( while sleep "$SNAPSHOT_S"; do snapshot; done ) &
SNAP=$!
trap 'kill $SNAP 2>/dev/null' EXIT

log "start: części ${ACTS:-wszystkie}, ElevenLabs $ELEVEN (budżet $(budget) z $MAX_CREDITS kr.), Whisper fp32 $ASR_FP32, rundy $ROUNDS"
mark "pierwsze podejścia: ElevenLabs i OmniVoice"
both
for r in $(seq 1 "$ROUNDS"); do
    mark "ocena przed rundą $r ponownych podejść"
    step evaluate "${EVAL_ARGS[@]}"
    step select
    n=$(retakes)
    log "do ponownego podejścia: $n fragmentów"
    [ "$n" -eq 0 ] && break
    mark "ponowne podejścia, runda $r z $ROUNDS: $n fragmentów"
    both --retake
done
mark "ocena końcowa"
step evaluate "${EVAL_ARGS[@]}"
step select
mark "finalize"
"$PY" -I -m lektor finalize --release $REL >> "$LOGS/finalize.log" 2>&1 || { mark "przerwane: finalize"; exit 1; }
step audio-report
mark "gotowe"
