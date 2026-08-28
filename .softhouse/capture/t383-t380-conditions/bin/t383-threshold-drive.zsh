#!/bin/zsh
# =====================================================================================
# T383 — drives F-T380-2: an ACCEPTED-but-absurd threshold breaks the self-test's DERIVED
# FIXTURES, and the wiring then blames the READERS for a THRESHOLD fault.
#
# T380 measured the headline case (`out/07-k12-int64-max-ceiling.txt`):
# `LOCK_CEILING_SECS=9223372036854775807` is accepted by `_knob_int` (it fits int64), the
# derived `_NOW_E - (CEILING*2 + 60)` goes pre-epoch, `_epoch_iso8601` refuses it, `_OLD` is
# EMPTY, c01/c02 go FAIL-SHUT, and the log says *"The thresholds validated at startup, so
# this is the READERS."*  That sentence is false in this case.
#
# UNLIKE the multiplicity drive, NOTHING IS MUTATED here: the environment IS the input, so
# every case drives the UNMODIFIED subject with a hostile (or a legitimate) threshold. That
# is the F-T368-3 discipline T377 established and T380 endorsed.
#
# THE GRADE IS TWO-SIDED. A validator that refuses everything above the default is a ban, not
# a bound: f03/f04/f07 are LEGITIMATE settings that must still START the fire, and f05 pins
# the exact boundary next to f04.
#
# SUBJ selects which file is graded — the post-fix wrapper (default) or the pre-fix one, so
# the RED/GREEN difference is visible in the same table. Expectations below are POST-FIX.
#
# NO MONEY IS COMPUTED ON THIS PATH. Every number here is an exit status or a count of seconds.
# =====================================================================================
emulate -L zsh
set -u

SUBJ="${SUBJ:-/tmp/t383-subject/.softhouse/bin/fire-program.sh}"
SUBJ_BIN="${SUBJ:h}"
SUBJ_REPO="${SUBJ_REPO:-${SUBJ:h:h:h}}"
WORK="${WORK:-/tmp/t383-thresh}"
/bin/rm -rf "$WORK"; /bin/mkdir -p "$WORK"

unset FIRE_SNAPSHOT_OF FIRE_REPO_SCRIPT

typeset -i CHECKS=0 WRONG=0

run() {   # <id> <want_rc> <want_regex|-> <forbid_regex|-> <VAR=value>...
  local id="$1" want_rc="$2" want_re="$3" forbid_re="$4"; shift 4
  local out kv; local -i rc
  local -a envs
  envs=("$@")
  out="$(env "${envs[@]}" FIRE_NO_SNAPSHOT=1 FIRE_SCRIPT_DIR="$SUBJ_BIN" \
             GEREGE_NBFI_REPO="$SUBJ_REPO" LOG_DIR="$WORK/logs" \
             /bin/zsh "$SUBJ" --probe 2>&1)"; rc=$?
  print -r -- "$out" > "$WORK/$id.out"

  local verdict="ok"
  (( rc == want_rc )) || verdict="*** WRONG rc=$rc want=$want_rc"
  if [[ "$verdict" == ok && "$want_re" != "-" ]]; then
    print -r -- "$out" | LC_ALL=C grep -qE "$want_re" || verdict="*** WRONG missing /$want_re/"
  fi
  if [[ "$verdict" == ok && "$forbid_re" != "-" ]]; then
    print -r -- "$out" | LC_ALL=C grep -qE "$forbid_re" && verdict="*** WRONG forbidden /$forbid_re/ present"
  fi
  [[ "$verdict" == ok ]] || (( WRONG+=1 ))
  (( CHECKS+=1 ))
  print -r -- "$id  $verdict  rc=$rc   [${envs[*]:-default env}]"
}

print -r -- "=== T383 threshold/fixture drive — subject $SUBJ"
print -r -- "=== sha256: $(/usr/bin/shasum -a 256 "$SUBJ" | cut -c1-64)"
print -r -- "=== expectations are POST-FIX; nothing is mutated, the ENVIRONMENT is the input"
print -r -- ""

# ---- f00 CONTROL, default thresholds: the fire must START. ---------------------------------
run f00 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'CONFIGURATION ERROR' \
  FIRE_T383=1

# ---- f01 THE T380 CASE: int64 max ceiling. Accepted by _knob_int, breaks the group-C fixture.
#      Pre-fix: rc 2 and *"this is the READERS"*. Post-fix: rc 78, THRESHOLD, readers unblamed.
run f01 78 'CONFIGURATION ERROR — the self-test.s DERIVED fixtures' 'this is the READERS' \
  LOCK_CEILING_SECS=9223372036854775807

# ---- f02 A SUB-HOUR CEILING. Pre-fix the fire STARTS and g01 reads `ok` — VACUOUSLY, because
#      `_NEAR_AGE` is negative, `_NEAR` is in the FUTURE, the age reads negative and arm 6
#      answers HELD-default. The row wants HELD, so it passes while grading nothing (P-22).
#      Post-fix: rc 78 naming the inside-ceiling fixture. ------------------------------------
run f02 78 'inside-ceiling age=-1800' 'this is the READERS' \
  LOCK_CEILING_SECS=1800

# ---- f03 A LEGITIMATE 7-DAY CEILING (T380's k10). Must STILL START — a bound, not a ban. ---
run f03 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'CONFIGURATION ERROR' \
  LOCK_CEILING_SECS=604800

# ---- f04 THE BOUNDARY, ACCEPTED SIDE: ceiling 3601 leaves `_NEAR_AGE` = 1, strictly inside. -
run f04 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'CONFIGURATION ERROR' \
  LOCK_CEILING_SECS=3601

# ---- f05 THE BOUNDARY, REFUSED SIDE: ceiling 3600 leaves `_NEAR_AGE` = 0 — an "inside the
#      ceiling" fixture that is NOW, which grades nothing. f04/f05 straddle it exactly, so the
#      bound is a comparison against the fixture and not a typed cardinal. --------------------
run f05 78 'inside-ceiling age=0' 'this is the READERS' \
  LOCK_CEILING_SECS=3600

# ---- f06 int64 max SKEW: `SKEW*2 + 60` wraps negative, so z06's "past the skew bound" fixture
#      lands in the PAST and the row grades the opposite of its claim. -----------------------
run f06 78 'CONFIGURATION ERROR — the self-test.s DERIVED fixtures' 'this is the READERS' \
  LOCK_RELEASE_SKEW_SECS=9223372036854775807

# ---- f07 SKEW ZERO is LEGITIMATE (T368/T380 k09: "believe no future instant at all") and must
#      still start. The new gate must not have quietly turned the skew minimum into 1. --------
run f07 0 'tally VERIFIED by the wiring — 45 executed \+ 0 skipped = 45 declared' 'CONFIGURATION ERROR' \
  LOCK_RELEASE_SKEW_SECS=0

# ---- f08 A MALFORMED ceiling still refuses at `_knob_int`, BEFORE the fixture gate, with the
#      original message. The new gate must not have displaced the old one. --------------------
run f08 78 'is not a non-negative decimal integer of seconds' 'DERIVED fixtures' \
  LOCK_CEILING_SECS=abc

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG"
if (( WRONG == 0 )); then print -r -- "RESULT: PASS"; exit 0; fi
print -r -- "RESULT: FAIL"; exit 1
