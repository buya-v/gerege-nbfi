#!/bin/zsh
# T361 — an INDEPENDENT adversarial corpus for the lock READERS.
#
# This is not T353's `--self-test-lock-readers` and does not reuse its rows. It sources the
# SHIPPED file's reader functions (extracted by `sed`, P-46) against a scratch $LOCK and asks
# `lock_decide` for a verdict, exactly as the self-test does — but the bodies are chosen by a
# reviewer who did not write the fix, and the corpus is aimed at the SENTINEL-INSTANT class
# that T353's tightening ("any syntactically valid instant is a release") does not cover.
#
# want=HELD  -> anything else is FAIL-OPEN: a lock held by a LIVE process on THIS host reads
#               as takeable. P-85, *"two orchestrators held the lock at once, and the cause
#               was an unpushed in-flight state"* [.softhouse/patterns.md:2822].
# want=<verdict> -> anything else is FAIL-SHUT: liveness, the fire waits.
emulate -L zsh
set -uo pipefail

SRC="${1:?usage: t361-reader-corpus.zsh <path to fire-program.sh>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t361-rc.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

{
  sed -n '/^lock_decide() {/,/^}/p'         "$SRC"
  sed -n '/^_lock_json_fields() {/,/^}$/p'  "$SRC"
  sed -n '/^_lock_json_field() {/,/^}$/p'   "$SRC"
  sed -n '/^_iso8601_epoch() {/,/^}/p'      "$SRC"
  sed -n '/^_epoch_iso8601() {/,/^}/p'      "$SRC"
  sed -n '/^lock_pid_state() {/,/^}/p'      "$SRC"
  sed -n '/^lock_released_at() {/,/^}/p'    "$SRC"
  sed -n '/^lock_started_age() {/,/^}/p'    "$SRC"
} > "$WORK/readers.zsh"
# Mandatory on EVERY vintage. `_lock_json_fields` and `_iso8601_epoch` exist only from T353,
# so they are required only when the source actually defines them — the point of running this
# corpus against T342 and `main` as well is to establish whether T353 REGRESSED anything.
for f in lock_decide _lock_json_field lock_pid_state lock_released_at lock_started_age; do
  grep -q "^${f}() {" "$WORK/readers.zsh" || { print -u2 "ABORT: extraction of $f failed"; exit 3; }
done
for f in _lock_json_fields _iso8601_epoch _epoch_iso8601; do
  if grep -q "^${f}() {" "$SRC"; then
    grep -q "^${f}() {" "$WORK/readers.zsh" || { print -u2 "ABORT: $f is in $SRC but extraction dropped it"; exit 3; }
  fi
done
# Thresholds are EXTRACTED FROM THE SOURCE, not typed here, so this corpus keeps working
# across vintages that add one. (Typing them is how the first run of T361's own
# condition-proof reported a false FAIL-SHUT: the patched file had gained
# `LOCK_RELEASE_SKEW_SECS` and the harness had not, so `set -u` killed the comparison inside
# `lock_released_at`. A harness that hard-codes its subject's configuration is P-80's shape.)
eval "$(grep -E '^LOCK_[A-Z_]+=' "$SRC")"
: ${LOCK_MAX_AGE_SECS:=21600} ${LOCK_CEILING_SECS:=86400}
LOCK="$WORK/LOCK"
source "$WORK/readers.zsh"
whence -w lock_released_at | grep -q function || { print -u2 "ABORT: readers not callable"; exit 3; }

H="$(hostname -s)"
NOW_E=$(date +%s)
NOW="$(/usr/bin/python3 -c 'import sys,datetime;print(datetime.datetime.fromtimestamp(int(sys.argv[1]),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' $NOW_E)"
OLD="$(/usr/bin/python3 -c 'import sys,datetime;print(datetime.datetime.fromtimestamp(int(sys.argv[1]),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' $(( NOW_E - 360000 )))"
LIVE=$$

print -r -- "T361 independent reader corpus"
print -r -- "source=$SRC  sha256=$(shasum -a 256 "$SRC" | awk '{print $1}')"
print -r -- "host=$H live_pid=$LIVE now=$NOW old=$OLD"
print -r -- ""

typeset -i N=0 OPEN=0 SHUT=0
row() {  # $1 id  $2 want (HELD | exact verdict)  $3 body  $4 note
  local id="$1" want="$2" body="$3" note="$4" rel sage pst v mark
  printf '%s' "$body" > "$LOCK"
  rel="$(lock_released_at)"; sage="$(lock_started_age)"; pst="$(lock_pid_state)"
  v="$(lock_decide 1 "$rel" "$sage" 60 "$pst")"
  N+=1; mark=ok
  if [[ "$want" == HELD ]]; then
    [[ "$v" == HELD-* ]] || { mark="*** FAIL-OPEN"; OPEN+=1; }
  else
    [[ "$v" == "$want" ]] || { mark="*** FAIL-SHUT"; SHUT+=1; }
  fi
  printf '%-5s %-14s want=%-14s got=%-16s %s\n' "$id" "$mark" "$want" "${v:-<none>}" "$note"
}

print -r -- "--- Z. ZERO-VALUE / SENTINEL INSTANTS in released_at, holder is a LIVE pid on THIS host."
print -r -- "    These are what a machine emits for an UNSET timestamp. want=HELD; anything else is OPEN."
row z01 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"0001-01-01T00:00:00Z\"}" "Go time.Time ZERO VALUE (encoding/json RFC3339) -- VERIFIED by running go"
row z02 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"0000-01-01T00:00:00Z\"}" "year zero"
row z03 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"1970-01-01T00:00:00Z\"}" "the UNIX epoch -- what an int64 0 formats to"
row z04 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"0001-01-01T00:00:01Z\"}" "one second past the Go zero"
row z05 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"9999-12-31T23:59:59Z\"}" "datetime.max / 'never' sentinel"
row z06 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"2999-01-01T00:00:00Z\"}" "far-future 'not yet' sentinel"

print -r -- ""
print -r -- "--- Y. released_at IN THE FUTURE while the holder is LIVE. want=HELD."
row y01 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"$(/usr/bin/python3 -c 'import sys,datetime;print(datetime.datetime.fromtimestamp(int(sys.argv[1]),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' $(( NOW_E + 31536000 )))\"}" "released_at one YEAR in the future"

print -r -- ""
print -r -- "--- X. THE OTHER READERS, bodies T353's self-test does not have."
row x01 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"$NOW\",\"host\":\"$H\"}" "duplicate host key -> whole body must be unreadable"
row x02 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"0001-01-01T00:00:00Z\"}" "started_at = Go zero -> negative epoch -> sage must read empty"
row x03 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"1969-12-31T23:59:59Z\"}" "started_at pre-epoch -> negative -> sage empty"
row x04 TAKE-ceiling "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"1970-01-01T00:00:01Z\"}" "started_at 1970 -> a REAL huge age -> ceiling MUST fire"
row x05 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$(/usr/bin/python3 -c 'import sys,datetime;print(datetime.datetime.fromtimestamp(int(sys.argv[1]),datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' $(( NOW_E + 3600 )))\"}" "started_at one hour in the FUTURE (clock skew) -> negative age -> HELD"
row x06 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"$NOW\\u0000\"}" "released_at with an escaped NUL -> control char -> unreadable"
row x07 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"$NOW\\n\"}" "released_at with an escaped newline"
row x08 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":[\"$NOW\"]}" "released_at is an ARRAY containing an instant"
row x09 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":{\"v\":\"$NOW\"}}" "released_at is an OBJECT"
row x10 HELD "{\"host\":\"$H\",\"pid\":\"$LIVE\",\"started_at\":\"$NOW\"}" "pid as a STRING -> pid_state absent"
row x11 FREE-released "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"\\u0032026-08-28T14:00:05Z\"}" "\\u0032 IS the digit 2: the shape check runs on the DECODED string. CORRECT, and want was set to FREE after measuring it"
row x12 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"２０２６-08-28T14:00:05Z\"}" "fullwidth digits in released_at"
row x13 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"2026-08-28T14:00:05Z\\u0020\"}" "trailing escaped SPACE"
row x14 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"2026-13-01T00:00:00Z\"}" "month 13 in released_at"
row x15 HELD "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"2026-02-29T00:00:00Z\"}" "impossible date in released_at"
row x16 FREE-released "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$NOW\",\"released_at\":\"$NOW\"}" "CONTROL: a genuine release MUST still fire arm 1"
row x17 TAKE-ceiling "{\"host\":\"$H\",\"pid\":$LIVE,\"started_at\":\"$OLD\"}" "CONTROL: 100 h old MUST still fire arm 3"

print -r -- ""
print -r -- "ROWS=$N FAIL_OPEN=$OPEN FAIL_SHUT=$SHUT"
(( OPEN == 0 && SHUT == 0 )) || exit 1
exit 0
