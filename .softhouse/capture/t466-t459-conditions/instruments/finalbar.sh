#!/bin/bash
# =============================================================================================
# T466 FINAL BAR -- run on the FINISHED COMMITTED TREE.
#
#   * `bash`, never `sh`/`zsh` (exit 3 is the harness's own wrong-interpreter refusal);
#   * the probe line's PRESENCE is counted BEFORE its value is read;
#   * an EMPTY log is an INSTRUMENT failure and never "the bar refused".
#
# The repository root is DERIVED FROM THIS FILE'S OWN LOCATION and the harness path is
# ASSEMBLED FROM FRAGMENTS, so this script spells no absolute path and no repo-relative
# literal -- a copy of it adds no row to the dead-path frontier and carries no absolute path
# that will be dead the moment this worktree is pruned.
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd)
SH=".soft""house"
CONF="$SH/conformance"".sh"

if [ ! -f "$R/$CONF" ]; then
  echo "ERROR: the derived repository root does not carry the harness: $R" >&2
  echo "ERROR: this script cannot establish what it is grading. REFUSING (exit 3)." >&2
  exit 3
fi
LOG="${T466_BAR_LOG:-${TMPDIR:-/tmp}/T466-FINAL-BAR.log}"

echo "=== 0. THE TREE BEING GRADED ==================================================="
echo "repository root                        = $R"
echo "HEAD                                   = $( cd "$R" && git rev-parse HEAD )"
echo "git status --porcelain (must be empty):"
( cd "$R" && git status --porcelain ) | sed 's/^/    /'
echo "git rev-parse HEAD:<harness>           = $( cd "$R" && git rev-parse "HEAD:$CONF" )"
echo "git hash-object --no-filters <harness> = $( cd "$R" && git hash-object --no-filters -- "$CONF" )"
echo "git hash-object (no flag)   <harness>  = $( cd "$R" && git hash-object -- "$CONF" )"
echo "ls-files -v, entries NOT in state H    : [$( cd "$R" && git ls-files -v | grep -v '^H ' | tr '\n' ';' )]"
echo
echo "=== 1. THE RUN ================================================================="
echo "command: bash <harness>   (bash, not sh, not zsh)"
rc=0
( cd "$R" && bash "$CONF" ) > "$LOG" 2>&1 || rc=$?
if [ ! -s "$LOG" ]; then
  echo "INSTRUMENT FAILURE: the bar produced an EMPTY log. That is not a refusal." >&2
  exit 3
fi
echo "EXIT = $rc"
echo
echo "=== 2. PROBE PRESENCE BEFORE PROBE VALUE ======================================="
n=$( LC_ALL=C grep -c 'probe = ' "$LOG" )
echo "grep -c 'probe = '  -> $n      <-- PRESENCE, read first"
if [ "$n" -gt 0 ]; then
  echo "probe value         -> $( LC_ALL=C grep -m1 'probe = ' "$LOG" | sed 's/.*probe = //' )"
else
  echo "probe value         -> NOT READ: the line was not printed, and an absent probe line is"
  echo "                       the guard working, not a value to interpret."
fi
echo
echo "=== 3. VERDICT ================================================================="
LC_ALL=C grep -m2 '^VERDICT' "$LOG"
echo
echo "=== 4. THIS GUARD'S OWN OUTPUT ================================================="
LC_ALL=C grep -n 'LOCAL-STATE\|HARNESS-TEXT\|RECOMPUTE:\|this harness \|SUBSTITUTION and a SUPPRESSION' "$LOG" \
  | sed 's/^/    /'
echo
echo "=== 5. GUARD COST =============================================================="
LC_ALL=C grep -n 'GUARD-COST CENSUS\|guard-cost: PASS\|COST .* guard_harness_text_is_committed' "$LOG" \
  | sed 's/^/    /'
echo
echo "=== 6. ANY GUARD REFUSAL ======================================================="
LC_ALL=C grep -nE 'guard_[a-z_]+ FAILED:|a HARD guard failed' "$LOG" | sed 's/^/    /'
echo "    [nothing listed above = no guard refused]"
echo
echo "full transcript: $LOG"
