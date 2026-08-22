#!/usr/bin/env bash
# T254 reviewer instrument: run the BAR in a candidate worktree and capture
# stdout, stderr and the exit code separately.
#
# The harness is invoked EXACTLY as `bash .softhouse/conformance.sh` (exit 3 is
# a wrong-interpreter refusal, so the interpreter is named explicitly).
#
# P-80: the exit code is captured and REPORTED, never swallowed. `set -e` is
# deliberately NOT set around the harness call, because a non-zero harness exit
# is the measurement, not an error of this script.
set -uo pipefail

TREE="${1:?candidate worktree}"
LABEL="${2:?label}"
OUT="${3:?outdir}"

cd "$TREE" || { echo "FATAL: cannot cd $TREE" >&2; exit 90; }

{
  echo "======================================================================"
  echo "BAR RUN: $LABEL"
  echo "tree:   $TREE"
  echo "date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "residue /tmp/t234_matrix2.txt: $([ -e /tmp/t234_matrix2.txt ] && echo PRESENT || echo ABSENT)"
  echo "residue /tmp/t234_matrix.txt:  $([ -e /tmp/t234_matrix.txt ] && echo PRESENT || echo ABSENT)"
  echo "======================================================================"
} > "$OUT/$LABEL.meta.txt"

bash .softhouse/conformance.sh > "$OUT/$LABEL.stdout.txt" 2> "$OUT/$LABEL.stderr.txt"
rc=$?

echo "BAR_EXIT=$rc" >> "$OUT/$LABEL.meta.txt"
echo "BAR_EXIT=$rc"
cat "$OUT/$LABEL.meta.txt"
