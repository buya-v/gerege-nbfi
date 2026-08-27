#!/usr/bin/env bash
# T299 -- DRIVE .softhouse/guards/check-capture-namespace.sh RED AND GREEN.
#
# P-45, the rule this drive exists for: "a test-only guard is not a guard ... verify the path
# that ACTUALLY EXECUTES calls it, not merely that a test does." Its corollary, recorded five
# times in this program: a guard nobody has watched FAIL enforces nothing. So every arm below
# is watched failing, and the vacuity arms are watched refusing.
#
# ENGINE (P-33/P-53): bash, git 2.50.x, POSIX awk/sed; versions printed below. No `git grep -E`
# is used, so P-53's backslash-class trap cannot apply here.
#
# CALIBRATION (P-72): arm G1 must pass on an untouched clone before any red arm is believed.
# If the guard is already red at HEAD, no red arm below can be attributed to its planted defect.
#
# EVERYTHING HAPPENS IN A THROWAWAY CLONE. A live fire is running against the real checkout.
#
# P-84 IS TESTED AS WRITTEN, NOT CITED: "exit 2 with NO probe line printed is a failed HARD
# guard or a build failure, not an oracle outage -- test for the line's PRESENCE before its
# value." Every arm reports whether `NAMESPACE-CENSUS:` was printed, BEFORE reporting anything
# it said, so an exit-2 refusal is legible as an instrument failure and never as a count of 0.
set -u

ROOT="$(git rev-parse --show-toplevel)" || exit 2
[ -n "$ROOT" ] || exit 2
cd "$ROOT" || exit 2
GUARD=".softhouse/guards/check-capture-namespace.sh"
[ -f "$GUARD" ] || { echo "ABORT(2): guard absent at $GUARD"; exit 2; }

echo "T299 NAMESPACE-GUARD RED/GREEN DRIVE"
echo "engine    : $(bash --version | head -1) | $(git --version)"
echo "HEAD      : $(git rev-parse HEAD)"
echo "guard     : $GUARD"
echo

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t299-guard.XXXXXXXX")" || exit 2
trap 'rm -rf "$SCRATCH"' EXIT
CLONE="$SCRATCH/clone"
git clone -q --no-hardlinks "$ROOT" "$CLONE" || { echo "ABORT(2): clone failed"; exit 2; }
# The guard reads TRACKED paths, so the worktree's staged-but-uncommitted state must be carried
# into the clone deliberately rather than assumed present.
git diff --cached --binary > "$SCRATCH/staged.patch"
if [ -s "$SCRATCH/staged.patch" ]; then
  ( cd "$CLONE" && git apply --index "$SCRATCH/staged.patch" ) \
    || { echo "ABORT(2): could not carry the staged state into the clone"; exit 2; }
  echo "carried   : staged-but-uncommitted state applied to the clone"
fi
echo

FAILED=0

arm() {
  # $1 label   $2 expected exit   $3 expected probe-line presence (1/0)
  label="$1"; want_rc="$2"; want_probe="$3"
  ( cd "$CLONE" && bash "$GUARD" ) >"$SCRATCH/$label.txt" 2>&1
  rc=$?
  probe="$(LC_ALL=C grep -ac '^NAMESPACE-CENSUS: ' "$SCRATCH/$label.txt" || true)"
  [ -n "$probe" ] || probe=0
  # PRESENCE BEFORE VALUE (P-84).
  echo "  probe line printed : $probe time(s)   [expected $want_probe]"
  echo "  exit               : $rc              [expected $want_rc]"
  if [ "$probe" -gt 0 ]; then
    echo "  census             : $(LC_ALL=C sed -n 's/^NAMESPACE-CENSUS: //p' "$SCRATCH/$label.txt")"
  else
    echo "  census             : NOT PRINTED -- read this as the guard refusing, never as zero"
    echo "  refusal reason     :"
    LC_ALL=C sed -n '1,8p' "$SCRATCH/$label.txt" | sed 's/^/      /'
  fi
  if [ "$rc" -eq "$want_rc" ] && [ "$probe" -eq "$want_probe" ]; then
    echo "  ARM RESULT         : PASS"
  else
    echo "  ARM RESULT         : **FAIL**"
    FAILED=$((FAILED + 1))
  fi
  echo
}

reset_clone() {
  ( cd "$CLONE" && git reset -q --hard HEAD && git clean -qfd ) || exit 2
  if [ -s "$SCRATCH/staged.patch" ]; then
    ( cd "$CLONE" && git apply --index "$SCRATCH/staged.patch" ) || exit 2
  fi
}

echo "=== G1 -- CALIBRATION: the guard is GREEN on an untouched clone ==="
arm G1 0 1
if [ "$FAILED" -ne 0 ]; then
  echo "CALIBRATION FAILED: the guard is not green at HEAD, so no red arm below can be"
  echo "attributed to the defect it plants. ABORT(1)."
  exit 1
fi

echo "=== R1 -- a THIRD directory under an id that already owns one, with no OWNER record ==="
reset_clone
mkdir -p "$CLONE/.softhouse/capture/t256-planted-by-t299"
echo "planted by T299's red drive" > "$CLONE/.softhouse/capture/t256-planted-by-t299/note.txt"
( cd "$CLONE" && git add -A .softhouse/capture/t256-planted-by-t299 ) || exit 2
arm R1 1 1

echo "=== R2 -- a FRESH collision on an id that has never collided (T290) ==="
reset_clone
mkdir -p "$CLONE/.softhouse/capture/t290-second-rig"
echo "planted by T299's red drive" > "$CLONE/.softhouse/capture/t290-second-rig/note.txt"
( cd "$CLONE" && git add -A .softhouse/capture/t290-second-rig ) || exit 2
arm R2 1 1

echo "=== R3 -- the existing OWNER record REMOVED (the fix reverted) ==="
reset_clone
( cd "$CLONE" && git rm -q -f .softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md ) || exit 2
arm R3 1 1

echo "=== R4 -- an OWNER record that is PRESENT but names no task id (a control that measures"
echo "===       nothing must not be accepted as one) ==="
reset_clone
: > "$CLONE/.softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md"
echo "this file explains nothing and names nobody" \
  > "$CLONE/.softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md"
( cd "$CLONE" && git add -A .softhouse/capture/t256-verdict-predicate ) || exit 2
arm R4 1 1

echo "=== V1 -- VACUITY: the CALIBRATION cannot lapse into a pass. Both known-positive"
echo "===       directories removed -> the guard must REFUSE (exit 2), not report zero ==="
reset_clone
( cd "$CLONE" && git rm -rqf .softhouse/capture/t256-verdict-predicate \
                             .softhouse/capture/t256-toolchain-population ) || exit 2
arm V1 2 0

echo "=== V2 -- VACUITY: the SELECTOR matching nothing must REFUSE, not report zero ==="
echo "===       (this is the BSD-sed defect this guard shipped with for one run, reproduced"
echo "===        deliberately by breaking the same line) ==="
reset_clone
( cd "$CLONE" && python3 - "$GUARD" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = "s#^\\.softhouse/(capture|reviews)/([^/]+)/.*#\\1/\\2#p"
assert old in s, "the selector line moved; this vacuity arm must be re-pointed, not skipped"
open(p, "w").write(s.replace(old, "s#^XXNOSUCHPREFIXXX/([^/]+)/.*#\\1#p"))
PY
) || { echo "  V2 SETUP FAILED -- the selector line could not be found to break."; FAILED=$((FAILED+1)); }
arm V2 2 0

reset_clone
echo "============================================================================"
if [ "$FAILED" -eq 0 ]; then
  echo "ALL ARMS PASSED: 1 green (calibration), 4 red, 2 vacuity refusals."
  echo "(The clone is discarded on exit. The real checkout was never modified.)"
  exit 0
fi
echo "$FAILED ARM(S) FAILED."
exit 1
