#!/bin/bash
# T125 — GREEN half of the proof (P-22: a gate must be shown to pass as well as to refuse).
#
# Nothing is simulated and nothing is bypassed here.  Both sidecars are run UNMODIFIED, with
# their full preconditions, against the real `gerege` tenant at the ratified
# MathContext(19, HALF_UP), and each writes into its own scratch evidence directory via
# ATTEST_OUT so that no committed capture set is touched.  The run must:
#   * exit 0;
#   * write an attestation.json;
#   * print the GATE line proving the mode behaviourally;
#   * and reproduce every previously-committed response body BYTE FOR BYTE.
#
# Usage: bash drive-canary-green.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
T36="$HERE/../t36"
CHBIN="$HERE/../../charges/bin"
rc_all=0

run() {  # run <label> <script> <outdir> [extra args...]
  local label=$1 script=$2 outdir=$3; shift 3
  echo
  echo "=================================================================="
  echo "GREEN: $label"
  echo "=================================================================="
  mkdir -p "$outdir"
  ATTEST_OUT="$outdir" ATTEST_TASK=T125 ATTEST_BRANCH=softhouse/T125-attest-canary-gates \
    python3 "$script" gerege "$@" > "$outdir/stdout.txt" 2> "$outdir/stderr.txt"
  local rc=$?
  cat "$outdir/stdout.txt"
  [ -s "$outdir/stderr.txt" ] && { echo "--- stderr ---"; cat "$outdir/stderr.txt"; }
  echo "EXIT CODE: $rc"
  [ "$rc" -ne 0 ] && rc_all=1
  [ -f "$outdir/attestation.json" ] || { echo "FAIL: no attestation.json written"; rc_all=1; }
  return 0
}

run "pathb/t36/attest.py gerege pathb" "$T36/attest.py" "$HERE/green-t36-gerege" pathb
run "charges/bin/attest-t40.py gerege" "$CHBIN/attest-t40.py" "$HERE/green-t40-gerege"

echo
echo "=================================================================="
echo "BYTE-IDENTITY: did any previously-passing capture change its bytes?"
echo "=================================================================="
python3 "$HERE/compare-bytes.py" "$HERE/green-t36-gerege" "$HERE/green-t40-gerege" || rc_all=1

echo
echo "T125 GREEN overall: $rc_all (0 = every gate passed on the ratified tenant)"
exit $rc_all
