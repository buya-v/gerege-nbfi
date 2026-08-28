#!/bin/zsh
# T361 — the REGRESSION surface T353's handoff does not enumerate.
#
# T353's own `epoch-parity.zsh` asks "does `_iso8601_epoch` AGREE with `date -j` on 19
# well-formed instants". That is the wrong question for a REPLACEMENT: the risk is the
# inputs where the two DISAGREE, on the one host where the old code worked (this Mac).
# BSD `date -j -f` is famously LENIENT — it normalises out-of-range fields and ignores
# trailing garbage — so the two cannot agree everywhere and the interesting question is
# WHICH WAY each disagreement falls.
#
# Direction, for the two call sites:
#   * `lock_started_age`: NEW refuses where OLD accepted -> `sage` empty -> arms 3 and 5
#     cannot fire -> **SHUT** (liveness). NEW accepts where OLD refused, or returns a
#     LARGER age -> arm 3 fires earlier -> **OPEN** (P-85 safety).
#   * `lock_released_at`: this call site is NEW in T353 (T342 had no shape check at all),
#     so every refusal there is a strict tightening -> **OPEN direction closed**.
emulate -L zsh
set -uo pipefail

SRC="${1:?usage: diff-vs-date-j.zsh <path to fire-program.sh>}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/t361-dj.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
sed -n '/^_iso8601_epoch() {/,/^}/p' "$SRC" > "$WORK/iso.zsh"
grep -q '^_iso8601_epoch() {' "$WORK/iso.zsh" || { print -u2 "ABORT: extraction failed"; exit 3; }
source "$WORK/iso.zsh"

# The OLD expression, copied byte-for-byte out of T342's shipped file, not retyped.
OLDSRC="${2:?usage: diff-vs-date-j.zsh <new> <T342 fire-program.sh>}"
grep -n 'date -j -f' "$OLDSRC" >/dev/null || { print -u2 "ABORT: no 'date -j -f' in $OLDSRC"; exit 3; }
print -r -- "old expression, as extracted from $OLDSRC:"
grep -n 'date -j -f' "$OLDSRC"
old_epoch() { TZ=UTC /bin/date -j -f "%Y-%m-%dT%H:%M:%SZ" "$1" +%s 2>/dev/null; }

print -r -- ""
printf '%-46s %-16s %-16s %s\n' INPUT 'OLD(date -j)' 'NEW(_iso8601)' 'DIRECTION at lock_started_age'
printf '%-46s %-16s %-16s %s\n' '---' '---' '---' '---'

typeset -i nsame=0 nopen=0 nshut=0 nboth=0
cmp_one() {
  local in="$1" o n odisp ndisp dir
  o="$(old_epoch "$in")" || o=""
  n="$(_iso8601_epoch "$in")" || n=""
  odisp="${o:-REFUSE}"; ndisp="${n:-REFUSE}"
  if [[ "$o" == "$n" ]]; then dir="same"; nsame+=1
  elif [[ -n "$o" && -z "$n" ]]; then dir="SHUT  (was readable, now unreadable -> arms 3/5 die)"; nshut+=1
  elif [[ -z "$o" && -n "$n" ]]; then dir="OPEN  (was unreadable, now an age -> arm 3 can fire)"; nopen+=1
  else dir="VALUE MOVED $(( n - o ))s $( (( n > o )) && print '-> older -> OPEN' || print '-> younger -> SHUT')"; nboth+=1
  fi
  printf '%-46s %-16s %-16s %s\n' "${in:0:44}" "$odisp" "$ndisp" "$dir"
}

for x in \
  '2026-08-28T14:00:05Z' '1970-01-01T00:00:00Z' '2000-02-29T00:00:00Z' \
  '2026-08-28T14:00:05Z trailing junk' '2026-08-28T14:00:05ZZZZ' '2026-08-28T14:00:05Z ' \
  '2026-13-01T00:00:00Z' '2026-00-01T00:00:00Z' '2026-02-30T00:00:00Z' '2026-02-31T00:00:00Z' \
  '2026-08-00T00:00:00Z' '2026-08-32T00:00:00Z' '2026-04-31T00:00:00Z' \
  '2026-08-28T24:00:00Z' '2026-08-28T25:00:00Z' '2026-08-28T14:60:00Z' '2026-08-28T14:00:60Z' \
  '2026-08-28T14:00:61Z' '2026-08-28T99:99:99Z' \
  '1900-02-29T00:00:00Z' '2100-02-29T00:00:00Z' '2026-02-29T00:00:00Z' \
  '2026-08-28T14:00:05z' '2026-08-28T14:00:05+00:00' '2026-08-28T14:00:05' \
  '2026-08-28 14:00:05Z' '2026-08-28T14:00:05.5Z' \
  '0000-01-01T00:00:00Z' '0001-01-01T00:00:00Z' '9999-12-31T23:59:59Z' '12026-01-01T00:00:00Z' \
  ' 2026-08-28T14:00:05Z' 'None' 'pending' '' '0' '-'
do cmp_one "$x"; done

print -r -- ""
print -r -- "SAME=$nsame  NEW-ONLY-ACCEPTS(OPEN)=$nopen  NEW-ONLY-REFUSES(SHUT)=$nshut  VALUE-MOVED=$nboth"
print -r -- ""
print -r -- "READ THIS AS: every disagreement must be SHUT, or accounted for. A single OPEN row"
print -r -- "means T353 made a LIVE lock more takeable on the one host T342 already worked on."
