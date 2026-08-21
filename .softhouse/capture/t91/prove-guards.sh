#!/bin/sh
# T91 — SHIP NO GUARD YOU HAVE NOT DRIVEN RED (P-22).
#
# Every guard T91 adds is driven to FAIL here first, then shown passing.  A proof that only shows
# the "after" cannot tell a fix from a no-op.
#
# It is destructive, so it works ONLY inside a `git archive` export under /tmp that it creates
# itself.  It never touches the worktree and never touches the oracle.
#
# T115 (closing T107's F-6, filed as FU-4).  THIS SCRIPT WAS ITSELF A VACUOUS PASS — the exact
# defect class it exists to prove absent, one layer out.  T107 ran it from a non-git export: the
# `git archive` failed, the export was EMPTY, all three G-1 legs died with "No such file or
# directory", the G-1 GREEN leg printed `exit=0` next to that failure, and the script still exited
# 0 with a full-looking transcript.  Three causes, all fixed here:
#   1. `git archive | tar` was never checked.  Now asserted non-empty; an empty export ABORTS.
#   2. `echo "exit=$?"` followed a `| tail -1` pipeline in the G-1 GREEN leg, so `$?` was tail's
#      status and that leg COULD NOT report a failure.  The pipeline is gone.
#   3. Every leg printed `(expect 3)` beside the observed value instead of COMPARING, and the
#      script exited 0 unconditionally.  Legs now compare and the script exits non-zero on any
#      mismatch.
# Plus two skip-branches that returned success: G-4's `exit 0` when there are no transcripts to
# poison, and the `command -v ugrep` else-branch, which printed an interactive measurement nobody
# can re-run.  A skipped guard is NOT a passing guard.
#
# Usage:  sh prove-guards.sh            (run from anywhere inside the repo)
# Exit:   0 = every leg behaved as expected; 1 = a leg did not; 2 = the harness could not establish
#         itself (which is an ERROR, never a pass).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
S=/tmp/t91-guards.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S/export"

BAD=0
expect() {  # expect <label> <observed> <wanted>
  if [ "$2" = "$3" ]; then
    echo "   exit=$2   EXPECTED $3   OK      [$1]"
  else
    echo "   exit=$2   EXPECTED $3   *** NOT AS EXPECTED ***   [$1]"
    BAD=$((BAD+1))
  fi
}

(cd "$ROOT" && git archive HEAD) > "$S/export.tar" 2>"$S/archive.err" || {
  echo "ABORT: git archive failed — there is nothing to prove anything against." >&2
  cat "$S/archive.err" >&2; exit 2; }
[ -s "$S/export.tar" ] || { echo "ABORT: git archive produced an EMPTY tar." >&2; exit 2; }
tar -x -C "$S/export" -f "$S/export.tar" || { echo "ABORT: could not unpack the export." >&2; exit 2; }
E=$S/export
for f in .softhouse/capture/charges/bin/preconditions.sh \
         .softhouse/capture/charges/bin/run-preconditions.sh \
         .softhouse/capture/pathb/t36/preconditions.sh \
         .softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json; do
  [ -f "$E/$f" ] || { echo "ABORT: the export is missing $f — an empty or partial export would make" >&2
                      echo "       every leg below 'fail' for the wrong reason and prove nothing." >&2; exit 2; }
done
echo "export: $(cd "$ROOT" && git rev-parse HEAD), $(find "$E" -type f | wc -l | tr -d ' ') files (asserted non-empty)"

echo "=================================================================== G-1"
echo "GUARD: the call-through refuses when the hardened rig is absent, and says so BEFORE it"
echo "       could have asserted anything.  The message 'PRECONDITIONS NOT RUN' must be TRUE AT"
echo "       THE MOMENT IT PRINTS."
echo
echo "-- GREEN first (rig present): expect exit 0 and 'ALL PRECONDITIONS HOLD'"
# NO PIPELINE HERE.  `echo "exit=$?"` after `| tail -1` reports TAIL's status, so this leg used to
# be structurally incapable of reporting a failure (T107 F-6.2).  Redirect, then read $?, then show.
CANARY_REQ=$E/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
  sh "$E/.softhouse/capture/charges/bin/preconditions.sh" gerege > "$S/g1green.txt" 2>&1
g1=$?
tail -1 "$S/g1green.txt"
expect "G-1 GREEN rig present" "$g1" 0
echo
echo "-- RED (rig deleted): expect exit 2, no assertion made"
rm -f "$E/.softhouse/capture/pathb/t36/preconditions.sh"
CANARY_REQ=$E/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
  sh "$E/.softhouse/capture/charges/bin/preconditions.sh" gerege
expect "G-1 RED rig deleted" "$?" 2
echo
echo "-- RED through the T40 wrapper too (bin/run-preconditions.sh must propagate it)"
sh "$E/.softhouse/capture/charges/bin/run-preconditions.sh" "$S/rp.txt" > "$S/g1wrap.txt" 2>&1
g1w=$?
tail -1 "$S/g1wrap.txt"
expect "G-1 RED through the wrapper" "$g1w" 2
echo
echo "-- RED with the rig EMPTY rather than deleted (MF-2; the [ ! -f ] branch must NOT be what fires)"
: > "$E/.softhouse/capture/pathb/t36/preconditions.sh"
CANARY_REQ=$E/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json \
  sh "$E/.softhouse/capture/charges/bin/preconditions.sh" gerege
expect "G-1b RED rig empty (MF-2)" "$?" 2
echo "   NOTE: MF-2 closes the EMPTY-rig limb only.  A rig SUBSTITUTED with different bytes, and a"
echo "   shim reached through a symlink, both still admit — see t115-drive-mf2.sh, which measures"
echo "   them.  Only FU-1 (an identity check on the rig) closes those."
echo

echo "=================================================================== G-2"
echo "GUARD: verdict.sh treats an EMPTY transcript set as an ERROR, not a pass."
echo "       'a check that passes vacuously on zero files' is the defect class this run keeps"
echo "       finding, so it must not be reintroduced by the thing that checks for it."
echo
mkdir -p "$S/empty"
sh "$HERE/verdict.sh" "$S/empty" >/dev/null 2>"$S/g2.err"
expect "G-2 verdict.sh over an empty set" "$?" 3
cat "$S/g2.err"
echo

echo "=================================================================== G-3"
echo "GUARD: shell-invariance.sh treats ZERO compared pairs as an ERROR."
echo
mkdir -p "$S/inv/x-sh" "$S/inv/x-bash"
sh "$HERE/shell-invariance.sh" "$S/inv" x >/dev/null 2>"$S/g3.err"
expect "G-3 shell-invariance.sh over zero pairs" "$?" 3
cat "$S/g3.err"
echo

echo "=================================================================== G-4"
echo "GUARD: verdict.sh's greps are 'LC_ALL=C grep -a'."
echo "       A transcript with one stray non-UTF-8 byte must not be able to make the scanner say"
echo "       the HALF_UP certification is ABSENT when it is present."
echo
mkdir -p "$S/poison"
# A SKIPPED GUARD IS NOT A PASSING GUARD (T115).  This used to `exit 0` when there was nothing to
# poison, so a tree with no committed transcripts produced a clean-looking, fully-successful run of
# a guard that never executed.  It is now an ABORT.
cp "$ROOT/.softhouse/capture/t91/out/prefix-copy-sh"/A*.txt "$S/poison/" 2>/dev/null || \
  { echo "ABORT: no committed pre-fix transcripts to poison — G-4 cannot run, and a guard that" >&2
    echo "       did not run must not report success." >&2; exit 2; }
python3 - "$S/poison/A2a-mutated-canary-gerege.txt" <<'PY'
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
i = b.find(b'PASS  effective rounding mode canary')
j = b.find(b'\n', i)
open(p, 'wb').write(b[:j] + b'\xff\xfe' + b[j:])
print('   poisoned the certification line itself with an invalid multibyte sequence')
PY
echo
echo "-- what /usr/bin/grep (BSD) does with and without -a:"
LC_ALL=C /usr/bin/grep -qF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
echo "   BSD  -qF  rc=$?"
LC_ALL=C /usr/bin/grep -aqF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
echo "   BSD -aqF  rc=$?"
echo "   MEASURED: on this machine BSD grep matched EITHER WAY, and T107b independently reproduced"
echo "   that (18 of 18 combinations).  T80 reported that BSD grep in a UTF-8 locale matches"
echo "   nothing here; that does NOT reproduce and is not repeated as fact."
echo "   *** THE LC_ALL=C grep -a HARDENING STANDS EITHER WAY.  Its stated REASON is under"
echo "   adjudication by T108; fail-closed is right whichever way T108 rules. ***"
echo
if command -v ugrep >/dev/null 2>&1; then
  LC_ALL=C ugrep -qF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
  echo "   ugrep  -qF  rc=$?   (1 = 'absent' — WRONG, the sentence is there)"
  LC_ALL=C ugrep -aqF 'PASS  effective rounding mode canary' "$S/poison/A2a-mutated-canary-gerege.txt"
  echo "   ugrep -aqF  rc=$?   (0 = present — correct)"
else
  echo "   ugrep is NOT on PATH here, so the ugrep limb WAS NOT MEASURED BY THIS RUN."
  echo "   [UNVERIFIED] T91 reported interactively that ugrep 7.5.0 -I returns 1 ('absent') on this"
  echo "   exact poisoned file and that -a fixes it.  T107b could not reproduce it — there is no"
  echo "   ugrep on this host at all — and downgraded the claim from [VERIFIED].  It rests on"
  echo "   unrecorded interactive runs and ZERO committed evidence.  T108 settles which tool T80"
  echo "   actually observed.  This branch states the absence of a measurement; it does not stand"
  echo "   in for one."
fi
echo
echo "-- verdict.sh (with -a) on the poisoned set: must still name A2a as an admission"
sh "$HERE/verdict.sh" "$S/poison" > "$S/g4.txt" 2>&1
LC_ALL=C /usr/bin/grep -a '^A2a' "$S/g4.txt"
if LC_ALL=C /usr/bin/grep -aq "^A2a.*ADMITS" "$S/g4.txt"; then
  echo "   A2a named as an admission on the poisoned set   OK      [G-4]"
else
  echo "   A2a NOT named as an admission   *** NOT AS EXPECTED ***   [G-4]"; BAD=$((BAD+1))
fi
echo

echo "=================================================================== G-5  (T115)"
echo "GUARD: verdict.sh refuses when it cannot RECORD a failure."
echo "       The scoring loop runs in a pipeline subshell, so its only channel is a file.  When"
echo "       that file lived in the transcript directory and the directory was read-only, every"
echo "       append failed silently and the scorer printed 'ALL 13 ATTACKS MET THEIR DECLARED"
echo "       EXPECTATION', exit 0, WHILE ITS OWN TABLE SHOWED SIX ADMITS ROWS."
echo
echo "-- GREEN: the real pre-fix transcripts must still score SIX admissions, exit 1"
rm -rf "$S/g5"; cp -R "$ROOT/.softhouse/capture/t91/out/prefix-livetwin-sh" "$S/g5"
sh "$HERE/verdict.sh" "$S/g5" > "$S/g5.txt" 2>&1
expect "G-5 GREEN discriminates" "$?" 1
echo "   admissions named: $(LC_ALL=C /usr/bin/grep -ac 'ADMITS' "$S/g5.txt")   (expect 12 = 6 rows + 6 recorded)"
echo
echo "-- RED: the same transcripts in a READ-ONLY directory"
rm -rf "$S/g5ro"; cp -R "$ROOT/.softhouse/capture/t91/out/prefix-livetwin-sh" "$S/g5ro"
chmod a-w "$S/g5ro"
sh "$HERE/verdict.sh" "$S/g5ro" > "$S/g5ro.txt" 2>&1
g5=$?
chmod u+w "$S/g5ro"
expect "G-5 RED read-only transcript dir still reports the 6 admissions" "$g5" 1
if LC_ALL=C /usr/bin/grep -aq 'ALL 13 ATTACKS MET' "$S/g5ro.txt"; then
  echo "   *** VACUOUS PASS: scored a clean sweep it could not have recorded a failure for"; BAD=$((BAD+1))
else
  echo "   no false 'ALL 13' verdict   OK      [G-5]"
fi
echo

echo "=================================================================== G-6  (T115)"
echo "GUARD: run-attacks.sh refuses when its canary MUTATION did not take."
echo "       sed is not grep: a substitution whose pattern does not match is a COPY, so a"
echo "       reformatted canonical request would silently turn both 'mutated canary' attacks into"
echo "       firing the PINNED TIE at the rig — a full-looking transcript of an attack that never"
echo "       happened."
echo
# Reformat the canonical request INSIDE THE EXPORT (1162502.5 -> 1162502.50, the same number
# written differently) so the committed sed pattern no longer matches, then run the EXPORT's copy
# of run-attacks.sh, which resolves its own ROOT to the export.  The assertion fires before any
# attack is dispatched, so THE ORACLE IS NEVER CONTACTED BY THIS LEG.
CANONX=$E/.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json
LC_ALL=C sed 's/"principal": 1162502.5,/"principal": 1162502.50,/' "$CANONX" > "$S/canon-reformatted.json"
cmp -s "$S/canon-reformatted.json" "$CANONX" && {
  echo "ABORT: could not reformat the canonical request, so G-6 has no red input." >&2; exit 2; }
cp "$S/canon-reformatted.json" "$CANONX"
RECIPE=.softhouse/capture/charges/bin/preconditions.sh LABEL=g6-mutation-check SH=sh \
  sh "$E/.softhouse/capture/t91/run-attacks.sh" > "$S/g6.txt" 2>&1
expect "G-6 RED reformatted canary -> harness error, not an 'attack'" "$?" 2
LC_ALL=C /usr/bin/grep -a 'HARNESS ERROR' "$S/g6.txt" | head -2 | sed 's/^/   /'
echo

echo "=================================================================== G-7  (T115)"
echo "GUARD: shell-invariance.sh compares the UNION of both sides, not just the sh side."
echo "       It used to iterate over the sh directory only, so a transcript present on the bash"
echo "       side and absent on the sh side was never compared, and it still reported agreement."
echo
rm -rf "$S/inv7"; mkdir -p "$S/inv7/y-sh" "$S/inv7/y-bash"
printf 'EXIT=0\n' > "$S/inv7/y-sh/A1.txt"
printf 'EXIT=0\n' > "$S/inv7/y-bash/A1.txt"
sh "$HERE/shell-invariance.sh" "$S/inv7" y > "$S/g7green.txt" 2>&1
expect "G-7 GREEN matched pair" "$?" 0
printf 'TOTALLY DIFFERENT\nEXIT=9\n' > "$S/inv7/y-bash/A2.txt"
sh "$HERE/shell-invariance.sh" "$S/inv7" y > "$S/g7red.txt" 2>&1
expect "G-7 RED bash-only transcript" "$?" 1
LC_ALL=C /usr/bin/grep -a 'MISSING' "$S/g7red.txt" | head -1 | sed 's/^/   /'
echo

echo "=================================================================== VERDICT"
echo "MF-1 and MF-2 are driven red and green by their own committed scripts, not here:"
echo "   sh .softhouse/capture/t91/t115-drive-mf1.sh"
echo "   sh .softhouse/capture/t91/t115-drive-mf2.sh      (also measures N9/N10, which stay OPEN)"
echo "   sh .softhouse/capture/t91/t115-drive-mf3-mf4.sh  (MF-3's breach count, MF-4's census)"
echo
if [ "$BAD" -eq 0 ]; then
  echo "done — every leg behaved as expected."
  exit 0
fi
echo "done — $BAD leg(s) did NOT behave as expected.  This script now EXITS NON-ZERO for that,"
echo "which it did not do before T115."
exit 1
