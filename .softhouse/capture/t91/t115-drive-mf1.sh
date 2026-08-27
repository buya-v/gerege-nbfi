#!/bin/sh
# T115 — drive MF-1 RED and GREEN.  P-22: ship no guard you have not personally driven red.
#
# MF-1 closes T107's F-1: verdict.sh guarded zero FILES but not zero CONTENT.  `st=$(tail -1 …)`
# was never validated, and the ten BREACH rows test `[ "$st" != 0 ]`, which ANY garbage string
# satisfies — so a set of content-free transcripts scored `ALL 13 ATTACKS MET THEIR DECLARED
# EXPECTATION`, exit 0.
#
# This script builds the red input FROM THE COMMITTED TRANSCRIPTS (not from a fixture I wrote to
# suit the answer) and runs BOTH the pre-MF-1 verdict.sh and the current one over it, so the
# transcript distinguishes a fix from a no-op.  The pre-MF-1 bytes come from an IMMUTABLE SHA,
# not from a moving ref (P-24): a baseline that can follow `main` will follow it exactly when you
# stop watching.
#
# Usage:  sh t115-drive-mf1.sh
# Exit:   0 = MF-1 behaved as specified in every leg; 1 = a leg did not.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)

# The pre-MF-1 verdict.sh: T91's tip, pinned as a literal sha.  If this sha ever fails to resolve
# the run must ABORT, not silently skip — that would be the very defect class this proves.
PRE_SHA=ccf3c14171dea52bd044d81d5ca67aba8054b74c   # T91's tip, the bytes T107 reviewed

S=/tmp/t115-mf1.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S"

( cd "$ROOT" && git show "$PRE_SHA:.softhouse/capture/t91/verdict.sh" ) > "$S/verdict-PRE.sh" 2>"$S/err" || {
  echo "ABORT: cannot resolve the pinned pre-MF-1 verdict.sh at $PRE_SHA" >&2; cat "$S/err" >&2; exit 2; }
[ -s "$S/verdict-PRE.sh" ] || { echo "ABORT: the pinned pre-MF-1 verdict.sh is EMPTY — nothing would be proved" >&2; exit 2; }
if LC_ALL=C grep -aq 'no EXIT= line' "$S/verdict-PRE.sh"; then
  echo "ABORT: the 'pre' baseline already CONTAINS MF-1 — this proof would compare the fix to itself" >&2; exit 2
fi
echo "baseline: $PRE_SHA:verdict.sh  sha256=$(shasum -a 256 < "$S/verdict-PRE.sh" | cut -c1-16)  (MF-1 absent, asserted)"
echo "current : $HERE/verdict.sh     sha256=$(shasum -a 256 < "$HERE/verdict.sh" | cut -c1-16)"
echo

# ---------------------------------------------------------------- inputs
# real: the committed post-fix and pre-fix transcript sets, untouched.
cp -R "$HERE/out/postfix-livetwin-sh" "$S/real-post"
cp -R "$HERE/out/prefix-livetwin-sh"  "$S/real-pre"
# red: the same post-fix set with the TEN `BREACH` transcripts replaced by one content-free line.
# Ten, because those are exactly the rows scored `[ "$st" != 0 ]`, which any garbage satisfies.
cp -R "$HERE/out/postfix-livetwin-sh" "$S/trunc"
TRUNCATED='A2a-mutated-canary-gerege A2b-mutated-canary-default
A2c-crafted-canary-and-expectation-gerege A3a-swapped-canary-gerege A3b-missing-canary
A3c-no-canary A4a-expect-override-default A4b-expect-override-gerege
A5-helpful-correct-override A6-canary-is-a-directory'
nt=0
for n in $TRUNCATED; do
  [ -f "$S/trunc/$n.txt" ] || { echo "ABORT: no committed transcript $n.txt to truncate" >&2; exit 2; }
  echo 'truncated, nothing was ever run' > "$S/trunc/$n.txt"
  nt=$((nt+1))
done
[ "$nt" -eq 10 ] || { echo "ABORT: truncated $nt transcripts, expected 10" >&2; exit 2; }
echo "red input: $nt of 13 committed transcripts replaced by the single line 'truncated, nothing was ever run'"
echo "           (no attack body, no PASS/FAIL line, no EXIT= line)"
echo

fail=0
leg() { # leg <label> <script> <dir> <expected-exit> <expected-grep>
  _lab=$1; _scr=$2; _dir=$3; _wx=$4; _wg=$5
  rm -rf "$S/w"; cp -R "$_dir" "$S/w"
  sh "$_scr" "$S/w" > "$S/o" 2>&1; _x=$?
  echo "=== $_lab"
  sed 's/^/    /' "$S/o"
  echo "    EXIT=$_x   (expected $_wx)"
  if [ "$_x" != "$_wx" ]; then echo "    *** WRONG EXIT"; fail=$((fail+1)); fi
  if [ -n "$_wg" ] && ! LC_ALL=C grep -aq "$_wg" "$S/o"; then
    echo "    *** expected output to contain: $_wg"; fail=$((fail+1))
  fi
  echo
}

echo "############ RED — the content-free transcript set"
leg "PRE-MF-1  over the truncated set  (the DEFECT)" "$S/verdict-PRE.sh" "$S/trunc" 0 'ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION'
leg "POST-MF-1 over the truncated set  (the FIX)"    "$HERE/verdict.sh"   "$S/trunc" 1 'EXPECTATIONS NOT MET (10)'
rm -rf "$S/w"; cp -R "$S/trunc" "$S/w"
sh "$HERE/verdict.sh" "$S/w" > "$S/e" 2>&1
nerr=$(LC_ALL=C grep -ac 'ERROR (no EXIT= line' "$S/e")
echo "ERROR rows named by post-MF-1 on the truncated set: $nerr   (expected 20 = 10 table rows + 10 .score-fail lines)"
[ "$nerr" -eq 20 ] || { echo "    *** expected 20, got $nerr"; fail=$((fail+1)); }
echo

echo "############ GREEN — MF-1 must not blunt the scorer"
leg "POST-MF-1 over the REAL post-fix transcripts" "$HERE/verdict.sh" "$S/real-post" 0 'ALL 13 ATTACKS MET THEIR DECLARED EXPECTATION'
leg "POST-MF-1 over the REAL pre-fix  transcripts" "$HERE/verdict.sh" "$S/real-pre"  1 'EXPECTATIONS NOT MET (6)'
echo "the six pre-fix admissions post-MF-1, named:"
rm -rf "$S/w"; cp -R "$S/real-pre" "$S/w"
sh "$HERE/verdict.sh" "$S/w" 2>&1 | LC_ALL=C grep -a 'ADMITS' | sed 's/^/    /'
echo

echo "############ the residual T107b recorded, driven RED rather than recorded and left"
echo "MF-1 AS SPECIFIED validates the VALUE \$st, not the SHAPE of the last line, so a transcript"
echo "whose final line is a bare numeral would still be accepted as a status.  T107b measured it,"
echo "declined to block, and left the decision to the next worker.  T115 closes it (test (a) in"
echo "verdict.sh).  Both directions are driven here:"
rm -rf "$S/bare"; cp -R "$S/trunc" "$S/bare"
printf '5\n' > "$S/bare/A2a-mutated-canary-gerege.txt"
echo
echo "-- PRE-MF-1 (T107's value-only rule, as the spec was written): a bare '5' scores OK"
rm -rf "$S/w"; cp -R "$S/bare" "$S/w"
sh "$S/verdict-PRE.sh" "$S/w" 2>&1 | LC_ALL=C grep -a '^A2a' | sed 's/^/    /'
echo
echo "-- POST-MF-1 (T115, shape test added): a bare '5' is an ERROR"
rm -rf "$S/w"; cp -R "$S/bare" "$S/w"
sh "$HERE/verdict.sh" "$S/w" > "$S/o" 2>&1; bx=$?
LC_ALL=C grep -a '^A2a' "$S/o" | sed 's/^/    /'
echo "    EXIT=$bx  (expected 1)"
[ "$bx" -eq 1 ] || { echo "    *** the bare-numeral residual is NOT closed"; fail=$((fail+1)); }
if ! LC_ALL=C grep -aq '^A2a.*ERROR (no EXIT= line' "$S/o"; then
  echo "    *** expected A2a to be scored ERROR"; fail=$((fail+1)); fi
echo

if [ "$fail" -eq 0 ]; then
  echo "RESULT: MF-1 driven RED and GREEN, every leg as specified."
  exit 0
fi
echo "RESULT: $fail leg(s) did not behave as specified."
exit 1
