#!/usr/bin/env bash
# drive-capture-wrapper.sh -- RED AND GREEN ARMS FOR capture-under-witness.sh
#
# NOTHING HERE WRITES TO THE REFERENCE ORACLE. The GREEN arm runs a real read-only capture
# (a SELECT through the committed capsql rig) inside a witnessed window. The RED arms are
# manufactured from COPIES in a scratch directory under /tmp.
set -uo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
C="$DIR/instruments/capture-under-witness.sh"
W="$DIR/instruments/oracle-window-witness.sh"
SCRATCH="${TMPDIR:-/tmp}/t417-wrap-$$"
mkdir -p "$SCRATCH/witness"
trap 'rm -rf "$SCRATCH"' EXIT

pass=0; fail=0
arm() { local name="$1" want="$2"; shift 2
  echo "=============================================================================="
  echo "ARM: $name    (expected rc $want)"
  echo "------------------------------------------------------------------------------"
  "$@"; local got=$?
  echo "------------------------------------------------------------------------------"
  if [ "$got" = "$want" ]; then echo "ARM RESULT: PASS  (rc=$got)"; pass=$((pass+1))
  else echo "ARM RESULT: FAIL  (rc=$got, wanted $want)"; fail=$((fail+1)); fi
  echo
}

# GREEN 1 -- a REAL read-only capture inside a witnessed window. The capture command is the
# committed capsql rig running s3-ledger-now.sql, which is a SELECT.
arm "GREEN-1 a real read-only capture inside a witnessed window -> quiescent, provenance written" 0 \
  env ORACLE_WITNESS_DIR="$SCRATCH/witness" bash "$C" WRAP-GREEN -- \
    bash "$DIR/capsql.sh" s3-ledger-now

# GREEN 2 -- the provenance block exists, is non-empty, and names a rollup and a verdict.
check_prov() {
  local f="$SCRATCH/witness/WRAP-GREEN.provenance.tsv"
  [ -s "$f" ] || { echo "no provenance file at $f"; return 1; }
  local v r
  v=$(awk -F'\t' '$1=="witness_verdict"{print $2}' "$f")
  r=$(awk -F'\t' '$1=="rollup_open"{print $2}' "$f")
  echo "  witness_verdict = $v"
  echo "  rollup_open     = $r"
  echo "  runs_in_window  = $(awk -F'\t' '$1=="runs_in_window"{print $2}' "$f")"
  echo "  graded_tables   = $(awk -F'\t' '$1=="graded_tables"{print $2}' "$f")"
  case "$v" in QUIESCENT*) ;; *) echo "verdict is not QUIESCENT"; return 1;; esac
  [ -n "$r" ] || { echo "rollup is empty"; return 1; }
  return 0
}
arm "GREEN-2 the provenance block carries a rollup, a run count and a verdict" 0 check_prov

# RED 1 -- the capture command FAILS inside a clean window. A still oracle is not a successful
# capture, and the wrapper must not report OK.
arm "RED-1 clean window but the capture command fails -> refused, not OK" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/witness" bash "$C" WRAP-CMDFAIL -- \
    bash -c 'echo "pretend capture"; exit 7'

# RED 2 -- no `--` separator. A wrapper that silently treats its own flags as the command is
# how a capture ends up unwitnessed.
arm "RED-2 malformed invocation (no --) -> refuses rather than guessing" 1 \
  bash "$C" WRAP-BAD bash -c true

# RED 3 -- no command after --.
arm "RED-3 no command after -- -> refuses" 1 \
  bash "$C" WRAP-EMPTY --

# RED 4 -- wrong interpreter.
arm "RED-4 invoked as sh -> exit 3, not exit 2" 3 \
  sh "$C" WRAP-SH -- true

# RED 5 -- CONTAMINATED WINDOW. The witness's open file is doctored between open and close by
# a "capture command" that edits its OWN COPY of the open witness -- standing in for an oracle
# that moved. Nothing is written to the database.
arm "RED-5 the oracle moved while the capture was open -> REFUSED, capture not promotable" 1 \
  env ORACLE_WITNESS_DIR="$SCRATCH/witness" bash "$C" WRAP-CONTAM -- \
    bash -c "sed -i.bak 's/^tbl\tm_office\t[0-9]*\t.*/tbl\tm_office\t1\tMOVEDUNDERTHECAPTURE000000000000/' \"$SCRATCH/witness/WRAP-CONTAM.open.tsv\"; echo 'the oracle moved under this capture'"

echo "=============================================================================="
echo "DRIVE SUMMARY: $pass passed, $fail failed"
echo "NOTHING WAS WRITTEN TO THE REFERENCE ORACLE BY THIS DRIVE."
[ "$fail" -eq 0 ]
