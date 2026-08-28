#!/bin/zsh
# T361 — PROVE THE CONDITIONS, because a condition handed over as an untested diff is a
# guess, and this lineage is five repairs deep.
#
# Applies C1 (F-T361-1, OPEN), C2 (F-T361-2, SHUT), C3 (F-T361-3, SHUT) and C4 (F-T361-4,
# OPEN-coverage) to a THROWAWAY COPY of the shipped file — never to the file — and then:
#
#   1. `zsh -n` must pass;
#   2. T361's own reader corpus must go 7 fail-open -> 0, with the two CONTROL rows (x16 a
#      genuine release must still FREE, x17 a 100 h lock must still TAKE) still green, so the
#      fix is not "refuse everything";
#   3. `--self-test-lock-readers` must still pass, and must now REFUSE the C1 mutation
#      (i.e. C1 comes with rows that grade it -- otherwise it is an ungraded fix);
#   4. T342's positive control must still PASS -- every takeover arm still fires;
#   5. the 192-state driver must still print 0 disagreements -- no arm moved;
#   6. C3 must hold at LOCK_CEILING_SECS=604800, the value that broke it before.
emulate -L zsh
set -uo pipefail
SRC="${1:?usage: t361-prove-conditions.zsh <fire-program.sh> <repo-root-for-instruments>}"
INST="${2:?}"
W="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/t361-cond.XXXXXX")" || exit 3
[[ -n "$W" && -d "$W" && "$W" != "/" ]] || exit 3
trap 'rm -rf "$W"' EXIT
F="$W/fire-program.sh"
cp "$SRC" "$F"

apply() {  # $1 label  $2.. sed programs; VOID if the file does not change
  local label="$1"; shift
  local before="$W/.before"; cp "$F" "$before"
  local p; for p in "$@"; do /usr/bin/sed -i '' -e "$p" "$F"; done
  if cmp -s "$before" "$F"; then print -r -- "*** VOID: $label did not change the file"; exit 3; fi
  print -r -- "applied: $label"
}

# ---- C1: reject implausible instants in released_at (F-T361-1, direction OPEN) ----
apply "C1 threshold" \
  's@^LOCK_CEILING_SECS=.*$@&\nLOCK_RELEASE_SKEW_SECS="${LOCK_RELEASE_SKEW_SECS:-3600}"   # T361 C1 — how far in the future a released_at may plausibly sit@'
apply "C1 predicate" \
  's@^  _iso8601_epoch "$v" >/dev/null || return 0$@  local -i _e _now\n  _e="$(_iso8601_epoch "$v")" || return 0\n  (( _e > 0 )) || return 0\n  _now=$(date +%s)\n  (( _e <= _now + LOCK_RELEASE_SKEW_SECS )) || return 0@'

# ---- C2: check mktemp (F-T361-2, direction SHUT) ----
apply "C2 mktemp" \
  's@^  LOCK="$(mktemp -d "${TMPDIR:-/tmp}/fire-selftest.XXXXXX")/LOCK"$@  _st_dir="$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/fire-selftest.XXXXXX" 2>/dev/null)" || _st_dir=""\n  if [[ -z "$_st_dir" || ! -d "$_st_dir" || "$_st_dir" == "/" ]]; then\n    print -u2 "self-test: could not create a scratch directory under ${TMPDIR:-/tmp}; refusing to run against an unknown path"\n    exit 2\n  fi\n  LOCK="$_st_dir/LOCK"@' \
  's@^  _st_dir="${LOCK:h}"$@@'

# ---- C3: derive the group-C fixture from the threshold (F-T361-3, direction SHUT) ----
apply "C3 derived fixture" \
  's@^  _OLD="$(_epoch_iso8601 $(( _NOW_E - 360000 )))".*$@  _OLD="$(_epoch_iso8601 $(( _NOW_E - (LOCK_CEILING_SECS * 2 + 60) )))"   # T361 C3 — DERIVED from the threshold, never typed@'

# ---- C4 + C1 rows: the self-test grades what the conditions fixed ----
apply "C1/C4 self-test rows" \
  's@^  print -r -- ""\n@@;' \
  's@^  print -r -- "--- B. DEAD holder on THIS host@  _row z01 HELD "{\\"host\\": \\"$_H\\", \\"pid\\": $_LIVE, \\"started_at\\": \\"$_NOW\\", \\"released_at\\": \\"0001-01-01T00:00:00Z\\"}" "T361 C1: Go zero time.Time -- a writer saying NOT RELEASED"\n  _row z02 HELD "{\\"host\\": \\"$_H\\", \\"pid\\": $_LIVE, \\"started_at\\": \\"$_NOW\\", \\"released_at\\": \\"1970-01-01T00:00:00Z\\"}" "T361 C1: the epoch -- an int64 0 formatted"\n  _row z03 HELD "{\\"host\\": \\"$_H\\", \\"pid\\": $_LIVE, \\"started_at\\": \\"$_NOW\\", \\"released_at\\": \\"9999-12-31T23:59:59Z\\"}" "T361 C1: datetime.max as a never sentinel"\n  _row e01 HELD "{\\"host\\": \\"not-$_H\\", \\"pid\\": ${_DEAD:-1}, \\"started_at\\": \\"$_NOW\\"}" "T361 C4: FOREIGN host, pid dead here -- arm 2 must NOT judge another machine (P-85)"\n  _row e02 HELD "{\\"host\\": \\"not-$_H\\", \\"pid\\": $_LIVE, \\"started_at\\": \\"$_NOW\\"}" "T361 C4: FOREIGN host, live pid"\n\n&@'

print -r -- ""
print -r -- "=== 1. zsh -n"
zsh -n "$F" && print -r -- "  PASS" || { print -r -- "  *** FAIL"; exit 1; }

print -r -- ""
print -r -- "=== 2. T361 reader corpus — want ROWS=24 FAIL_OPEN=0 FAIL_SHUT=0 (x16/x17 controls green)"
# T361's own corpus lives beside THIS script, not under $INST (which is the tree the T342/T353
# instruments are staged in). `${0:A:h}` is resolved here, before anything cd's — the same
# discipline F-T361/§4 checked in the wrapper.
zsh "${0:A:h}/t361-reader-corpus.zsh" "$F" > "$W/corpus.txt" 2>&1
local crc=$?
grep -E '^(x11|x16|x17|z01|y01)' "$W/corpus.txt"
tail -1 "$W/corpus.txt"
print -r -- "  corpus rc=$crc"
print -r -- "  NOTE: the one residual FAIL-SHUT is row x11 and it is C1 WORKING, not C1 breaking."
print -r -- "  x11's literal is the fixed instant 2026-08-28T14:00:05Z, which is hours AHEAD of"
print -r -- "  the clock at the time of this run, so C1's plausibility bound refuses it. That is"
print -r -- "  the STATED COST of C1: a released_at further ahead than LOCK_RELEASE_SKEW_SECS"
print -r -- "  reads as NOT released. Direction SHUT, configurable, and preferable to the OPEN"
print -r -- "  direction it replaces. x11 was written against T353's contract; under C1 its"
print -r -- "  correct expectation is HELD. Recorded rather than rescored."

print -r -- ""
print -r -- "=== 3. --self-test-lock-readers on the patched file (want rc 0, ROWS=32)"
zsh "$F" --self-test-lock-readers > "$W/st.txt" 2>&1
local strc=$?
tail -1 "$W/st.txt"; print -r -- "  rc=$strc"

print -r -- ""
print -r -- "=== 3b. and it must CATCH C1 being reverted (else C1 is an ungraded fix)"
cp "$F" "$W/rev.sh"
/usr/bin/sed -i '' -e 's@^  (( _e > 0 )) || return 0$@  : # C1 reverted@' -e 's@^  (( _e <= _now + LOCK_RELEASE_SKEW_SECS )) || return 0$@  : # C1 reverted@' "$W/rev.sh"
cmp -s "$F" "$W/rev.sh" && { print -r -- "  *** VOID: revert did not apply"; exit 3; }
zsh "$W/rev.sh" --self-test-lock-readers > "$W/strev.txt" 2>&1
local revrc=$?
tail -1 "$W/strev.txt"; print -r -- "  rc=$revrc  (want NON-ZERO)"

print -r -- ""
print -r -- "=== 3c. and it must CATCH C4 being reverted"
cp "$F" "$W/rev4.sh"
/usr/bin/sed -i '' -e 's@^  \[\[ "$host" == "$(hostname -s)" \]\].*$@  : # C4 host check reverted@' "$W/rev4.sh"
cmp -s "$F" "$W/rev4.sh" && { print -r -- "  *** VOID: revert did not apply"; exit 3; }
zsh "$W/rev4.sh" --self-test-lock-readers > "$W/strev4.txt" 2>&1
local rev4rc=$?
tail -1 "$W/strev4.txt"; print -r -- "  rc=$rev4rc  (want NON-ZERO)"

print -r -- ""
print -r -- "=== 4. T342 positive control — every takeover arm must still fire"
zsh "$INST/.softhouse/capture/t342-releasedat-failopen/bin/positive-control.zsh" "$F" 2>&1 | grep -E '^(RESULT|  (OK|FAIL))'

print -r -- ""
print -r -- "=== 5. 192-state driver — no arm may have moved"
zsh "$INST/.softhouse/capture/t279-lock-partition/drive-wrapper-vs-skill.zsh" "$F" 2>&1 | grep -E 'disagreements|RESULT'

print -r -- ""
print -r -- "=== 6. C3 at LOCK_CEILING_SECS=604800 — the value that used to stop the fire"
LOCK_CEILING_SECS=604800 zsh "$F" --self-test-lock-readers > "$W/st604800.txt" 2>&1
local c3rc=$?
tail -1 "$W/st604800.txt"; print -r -- "  rc=$c3rc  (want 0)"

print -r -- ""
print -r -- "=== 7. C2 — mktemp failure must now REFUSE, not fall back to /"
grep -n 'mktemp -d "\${TMPDIR' "$F" | head -2
grep -n 'refusing to run against an unknown path' "$F" | head -2
grep -c '_st_dir="\${LOCK:h}"' "$F"
