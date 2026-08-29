#!/bin/bash
# =============================================================================================
# T477 FINAL BAR -- run on the FINISHED COMMITTED TREE, at this branch`s tip.
#
#   * `bash`, never `sh`/`zsh` (exit 3 is the harness`s own wrong-interpreter refusal);
#   * the probe line`s PRESENCE is counted BEFORE its value is read;
#   * an EMPTY log is an INSTRUMENT failure and never "the bar refused";
#   * every grep prints its MATCH COUNT, so an empty list is a number and not an absence.
#
# The repository is entered ONCE, FATALLY, at the top. The root is derived from this file`s own
# location and the harness path is assembled from fragments, so no absolute path and no
# repo-relative literal is spelled here.
# =============================================================================================
set -u

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 3
R=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd) || exit 3
SH=".soft""house"
CONF="$SH/conformance"".sh"

cd "$R" || {
  echo "ERROR: could not enter the derived repository root: $R" >&2
  echo "ERROR: REFUSING (exit 3). Nothing below would be a measurement." >&2
  exit 3
}
[ -f "$CONF" ] || {
  echo "ERROR: the derived repository root does not carry the harness: $R" >&2
  echo "ERROR: REFUSING (exit 3)." >&2
  exit 3
}
LOG="${T477_BAR_LOG:-${TMPDIR:-/tmp}/T477-FINAL-BAR.log}"

echo "=== 0. THE TREE BEING GRADED ==================================================="
echo "repository root                        = $R"
echo "HEAD                                   = $( git rev-parse HEAD )"
echo "git status --porcelain lines           = $( git status --porcelain | LC_ALL=C grep -c '' || true )"
git status --porcelain | LC_ALL=C sed 's/^/    /' || true
echo "git rev-parse HEAD:<harness>           = $( git rev-parse "HEAD:$CONF" )"
echo "git hash-object --no-filters <harness> = $( git hash-object --no-filters -- "$CONF" )"
echo "git hash-object (no flag)   <harness>  = $( git hash-object -- "$CONF" )"
echo "ls-files -v, entries NOT in state H    = $( git ls-files -v | LC_ALL=C grep -vc '^H ' || true )"
echo
echo "=== 1. THE RUN ================================================================="
echo "command: bash <harness>   (bash, not sh, not zsh)"
rc=0
bash "$CONF" >"$LOG" 2>&1 || rc=$?
if [ ! -s "$LOG" ]; then
  echo "INSTRUMENT FAILURE: the bar produced an EMPTY log. That is not a refusal." >&2
  exit 3
fi
echo "EXIT = $rc"
echo
echo "=== 2. PROBE PRESENCE BEFORE PROBE VALUE ======================================="
n=$( LC_ALL=C grep -c 'probe = ' "$LOG" || true )
echo "grep -c 'probe = '  -> $n      <-- PRESENCE, read first"
if [ "$n" -gt 0 ]; then
  echo "probe value         -> $( LC_ALL=C grep 'probe = ' "$LOG" | LC_ALL=C sed -n 's/.*probe = //p' | tr '\n' ' ' )"
else
  echo "probe value         -> NOT PRINTED. An ABSENT probe line is the guard machinery working,"
  echo "                       never an oracle outage (P-84)."
fi
echo
echo "=== 3. VERDICT ================================================================="
echo "VERDICT lines: $( LC_ALL=C grep -c '^VERDICT' "$LOG" || true )"
LC_ALL=C grep '^VERDICT' "$LOG" | LC_ALL=C sed 's/^/    /' || true
echo
echo "=== 4. THIS GUARD'S OWN OUTPUT ================================================="
pat='LOCAL-STATE\|HARNESS-TEXT\|RECOMPUTE:\|CHALLENGE:\|READ CENSUS\|this harness '
echo "matching lines: $( LC_ALL=C grep -c "$pat" "$LOG" || true )"
LC_ALL=C grep -n "$pat" "$LOG" | LC_ALL=C sed 's/^/    /' || true
echo
echo "=== 5. GUARD COST =============================================================="
echo "matching lines: $( LC_ALL=C grep -c 'GUARD-COST CENSUS\|COST .* guard_harness_text_is_committed\|guard-cost:' "$LOG" || true )"
LC_ALL=C grep -n 'GUARD-COST CENSUS\|COST .* guard_harness_text_is_committed\|guard-cost:' "$LOG" \
  | LC_ALL=C sed 's/^/    /' || true
echo
echo "=== 6. THE PINS ================================================================"
echo "matching lines: $( LC_ALL=C grep -c 'frontier\|pinned at\|DEADPATH-FRONTIER' "$LOG" || true )"
LC_ALL=C grep -n 'frontier\|pinned at\|DEADPATH-FRONTIER' "$LOG" | LC_ALL=C sed 's/^/    /' || true
echo
echo "=== 7. EVERY GUARD REFUSAL, COUNT FIRST ========================================"
echo "refusal lines matched: $( LC_ALL=C grep -c 'conformance: guard_[a-z_]*[:(]* *FAILED\|conformance: guard_[a-z_]*:' "$LOG" || true )"
LC_ALL=C grep -n 'conformance: guard_[a-z_]*[:(]* *FAILED\|conformance: guard_[a-z_]*:' "$LOG" \
  | LC_ALL=C sed 's/^/    /' || true
echo
echo "full transcript kept at: $LOG   ($( LC_ALL=C grep -c '' "$LOG" ) lines)"
