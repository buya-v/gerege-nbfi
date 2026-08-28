#!/bin/zsh
# ============================================================================
# T385 · INDEPENDENT RE-DRIVE of T383's derived-fixture gate (F-T380-2), and of
# its STATED COST: `LOCK_CEILING_SECS <= 3600` now refuses the fire.
#
# The question this driver has to answer is not "does it refuse?" but
# "is it a BOUND or a BAN?" -- so every refusing case is paired with an
# accepting one on the other side of it, and the TOP of the accepted range
# (which T383 left [UNVERIFIED]) is measured here for the first time.
#
# Nothing is mutated: the environment IS the input. `--probe` only, throwaway
# repo, no lock taken, nothing dispatched. FIRE_SNAPSHOT_OF & friends unset.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ="${1:?usage: t385-threshold-drive.zsh <wrapper-under-test>}"
SUBJ="${SUBJ:A}"
WORK="/tmp/t385/th-${SUBJ:t:r}"
rm -rf "$WORK"; mkdir -p "$WORK"
cp /tmp/t385/lib-worktree-prune.zsh "$WORK/"
cp "$SUBJ" "$WORK/fire-program.sh"; chmod +x "$WORK/fire-program.sh"

print -r -- "T385 threshold drive"
print -r -- "wrapper under test : $SUBJ"
print -r -- "sha256             : $(shasum -a 256 "$SUBJ" | awk '{print $1}')"
print -r -- "default in file    : $(LC_ALL=C grep -m1 '^LOCK_CEILING_SECS=' "$SUBJ")"
print -r -- "                     $(LC_ALL=C grep -m1 '^LOCK_RELEASE_SKEW_SECS=' "$SUBJ")"
print -r -- ""

typeset -i CHECKS=0 WRONG=0

# _case <id> <want-rc> <must-ERE|-> <mustnot-ERE|-> <note> <ENV=VAL ...>
_case() {
  local id="$1" want="$2" must="$3" mustnot="$4" note="$5"; shift 5
  CHECKS+=1
  local -a envs; envs=( "$@" )
  local OUT RC
  OUT="$(env GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs-th "${envs[@]}" \
         /bin/zsh "$WORK/fire-program.sh" --probe 2>&1)"
  RC=$?
  local verdict=ok
  (( RC == want )) || verdict="WRONG(rc=$RC want=$want)"
  [[ "$must"    == "-" ]] || print -r -- "$OUT" | LC_ALL=C grep -qE "$must"    || verdict="WRONG(missing /$must/)"
  [[ "$mustnot" == "-" ]] || ! print -r -- "$OUT" | LC_ALL=C grep -qE "$mustnot" || verdict="WRONG(FORBIDDEN /$mustnot/)"
  [[ "$verdict" == ok ]] || WRONG+=1
  printf '%-5s %-38s rc=%-3d %s   [%s]\n' "$id" "$verdict" "$RC" "$note" "${envs[*]}"
  print -r -- "$OUT" | LC_ALL=C grep -E 'CONFIGURATION ERROR|FATAL|tally VERIFIED|probe only|refusing|not a valid' \
    | cut -c1-260 | sed 's/^/        | /'
}

mkdir -p /tmp/t385/logs-th

print -r -- "--- the accepted side: defaults and legitimate non-defaults MUST START ---"
_case t00 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'DEFAULTS (86400 / 3600) -- what the launchd plist actually runs' NOOP=1
_case t03 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'ceiling 604800 = 7 days, legitimate'      LOCK_CEILING_SECS=604800
_case t04 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'ceiling 3601 = one second above the bound' LOCK_CEILING_SECS=3601
_case t07 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'skew 0, legitimate (believe no future instant)' LOCK_RELEASE_SKEW_SECS=0
_case t09 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'ceiling 86401, just above the shipped default' LOCK_CEILING_SECS=86401
_case t10 0 'tally VERIFIED' 'CONFIGURATION ERROR' 'skew 86400 = 24 h, generous but plausible'  LOCK_RELEASE_SKEW_SECS=86400

print -r -- ""
print -r -- "--- the refused side, each paired with the accepting case above ---"
_case t01 78 'CONFIGURATION ERROR' 'this is the READERS' 'ceiling = int64 max (T380 k12)'     LOCK_CEILING_SECS=9223372036854775807
_case t02 78 'inside-ceiling age=-1800' 'this is the READERS' 'ceiling 1800: g01 was VACUOUS before' LOCK_CEILING_SECS=1800
_case t05 78 'inside-ceiling age=0'  'this is the READERS' 'ceiling 3600: the exact boundary'  LOCK_CEILING_SECS=3600
_case t06 78 'CONFIGURATION ERROR' 'this is the READERS' 'skew = int64 max'                    LOCK_RELEASE_SKEW_SECS=9223372036854775807
# NOTE (T385): the OLD _knob_int refusal ALSO opens with "FATAL: CONFIGURATION ERROR", so the
# forbidden string here has to be the NEW gate's own wording, not that shared prefix.
_case t08 78 'not a non-negative decimal integer' 'derived fixtures do not land' 'ceiling = abc: the OLD _knob_int gate, not displaced' LOCK_CEILING_SECS=abc

print -r -- ""
print -r -- "--- NEW: the TOP of the accepted range, which T383 left [UNVERIFIED] ---"
# The binding constraint is `_NOW_E - (CEILING*2 + 60) >= 0`, so the largest accepted
# ceiling is floor((now - 60) / 2). Derived by running the same arithmetic, not typed.
typeset -i NOW MAXC
NOW=$(date -u +%s)
MAXC=$(( (NOW - 60) / 2 ))
print -r -- "  now(epoch)=$NOW  =>  derived maximum ceiling = $MAXC s  ~ $(( MAXC / 31557600 )) years"
_case t11 0  'tally VERIFIED'      'CONFIGURATION ERROR' 'ceiling just BELOW the derived maximum'  LOCK_CEILING_SECS=$(( MAXC - 3600 ))
_case t12 78 'CONFIGURATION ERROR' 'this is the READERS' 'ceiling just ABOVE the derived maximum'  LOCK_CEILING_SECS=$(( MAXC + 3600 ))
_case t13 78 'CONFIGURATION ERROR' 'this is the READERS' 'ceiling = int64max/2 (CEILING*2+60 wraps)' LOCK_CEILING_SECS=4611686018427387903

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG"
if (( WRONG == 0 )); then print -r -- "RESULT: PASS"; else print -r -- "RESULT: FAIL"; fi
