#!/usr/bin/env bash
# t379-anticalibration-drive.sh -- T379 finding R2, driven.
#
#   bash .softhouse/reviews/t379-review-t371/instruments/t379-anticalibration-drive.sh [REF]
#
# THE FINDING. T371's ANTI-calibration is itself fail-open, which is the defect it was written
# to repair, one layer in:
#
#   n=$(git grep -c -F "$CALIB_NEG_STR" -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
#   if [ "${n:-0}" -gt 0 ]; then ... exit 3 ; fi
#
# `2>/dev/null` discards the engine's complaint and the pipe into awk discards its exit status.
# A `git grep` that ERRORS therefore yields n=0, which is INDISTINGUISHABLE from "the sentinel is
# correctly absent" -- and the instrument prints
#     SWEEP CALIBRATE-: PASS -- known negative matched 0 times across the tracked corpus
# for a search that ran over NOTHING, then declares calibration=yes and proceeds to print zeros.
#
# The POSITIVE arm has the identical construction but fails SAFE: a never-run positive yields
# n=0 -> "CALIBRATION MISSED" -> exit 3. Only the anti-calibration arm is fail-OPEN.
#
# HOW THIS DRIVE MAKES THAT SEARCH FAIL without touching anything else: it replaces only the
# anti-calibration's PATHSPEC with `:(bogusmagic)x`, which git rejects with rc 128. Nothing else
# in the instrument is altered; the sha256 of the untouched original is printed for comparison.
#
# BOUND, stated so the finding is not overread: in the realistic world where git grep is broken
# enough to error on `-- .softhouse/`, all sixteen selectors error too and the run exits 4,
# loudly inadmissible. R2 bites only where those two identical invocations diverge.
#
# It writes only under a mktemp dir. No network, no database.
set -uo pipefail
REF="${1:-softhouse/T371-t367-conditions}"
ROOT=$(git rev-parse --show-toplevel) || exit 2
cd "$ROOT" || exit 2
SUT='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
W=$(mktemp -d "${TMPDIR:-/tmp}/t379-ac-XXXXXX") || exit 2
trap 'rm -rf "$W"' EXIT

echo "=================================================================="
echo "T379 R2 DRIVE -- the anti-calibration passes on a search that never ran"
echo "repo: $(git rev-parse --short HEAD)   ref under test: $REF ($(git rev-parse --short "$REF"))"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=================================================================="

git show "$REF:$SUT" > "$W/AFTER.sh" || { echo "cannot extract $REF:$SUT"; exit 2; }
printf 'AFTER sha256 (unmodified): %s\n' "$(shasum -a 256 "$W/AFTER.sh" | awk '{print $1}')"

echo
echo "---------- step 0: the engine's own status for the pathspec this drive substitutes"
git grep -c -F "zzq-t379-nothing" -- ":(bogusmagic)x" >/dev/null 2>&1
printf '    git grep -c -F <absent> -- ":(bogusmagic)x"   rc = %s   (>=2 == DID NOT RUN)\n' "$?"
git grep -c -F "zzq-t379-nothing" -- .softhouse/ >/dev/null 2>&1
printf '    git grep -c -F <absent> -- .softhouse/          rc = %s   (1 == a MEASURED zero)\n' "$?"

# Substitute ONLY the anti-calibration's pathspec. Selectors are commented out so the drive reads
# the calibration's behaviour and not 16 selectors of noise (and finishes in seconds, not 96 s).
sed 's|n=\$(git grep -c -F "\$CALIB_NEG_STR" -- .softhouse/ 2>/dev/null|n=$(git grep -c -F "$CALIB_NEG_STR" -- ":(bogusmagic)x" 2>/dev/null|' \
  "$W/AFTER.sh" | sed 's/^sel "S/#sel "S/' > "$W/ac-broken.sh"
sed 's/^sel "S/#sel "S/' "$W/AFTER.sh" > "$W/ac-control.sh"

printf '\n    anti-calibration line as driven:\n      %s\n' \
  "$(grep -n 'CALIB_NEG_STR" --' "$W/ac-broken.sh")"

echo
echo "---------- CONTROL: unmodified instrument, selectors suppressed"
out=$(bash "$W/ac-control.sh" 2>&1); rc=$?
printf '%s\n' "$out" | grep -E 'CALIBRATE|SWEEP-RESULT|SWEEP ABORT' | sed 's/^/    /'
printf '    EXIT=%s\n' "$rc"

echo
echo "---------- R2: the ANTI-CALIBRATION's search cannot run (git grep rc=128)"
out=$(bash "$W/ac-broken.sh" 2>&1); rc=$?
printf '%s\n' "$out" | grep -E 'CALIBRATE|SWEEP-RESULT|SWEEP ABORT' | sed 's/^/    /'
printf '    EXIT=%s\n' "$rc"

echo
echo "    ^^ EXPECTED IF THE GUARD WERE FAIL-CLOSED: an abort, exit 3, nothing else printed."
echo "       OBSERVED: 'SWEEP CALIBRATE-: PASS -- known negative matched 0 times across the"
echo "       tracked corpus', calibration=yes, exit 0. A NEGATIVE THE INSTRUMENT NEVER MEASURED,"
echo "       inside the anti-calibration added to prevent exactly that. This is T379 finding R2."
echo
echo "REMEDY (FU-T379-3): capture rc for BOTH calibration searches before the pipe into awk and"
echo "exit 3 on rc >= 2. That is a control-flow change to a shipped guard and needs its own red"
echo "drive, which is why T379 files it rather than proposing it as a MICRO-FIX."
echo "=================================================================="
