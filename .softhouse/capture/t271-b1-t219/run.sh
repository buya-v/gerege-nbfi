#!/usr/bin/env bash
# T271 / B-1 -- run everything this task produced, in the order a reader should meet it.
#
# NOTHING CALLS THIS YET. `.softhouse/conformance.sh` is held by a sibling task this fire and
# T271 may not touch it; T269 is the wiring task and T271 is one of its hard dependencies. Until
# then this, like R-VPA itself before it is wired, is a measurement nobody reads -- and saying so
# in the file rather than only in a handoff is the point (P-78).
#
# EXIT: 0 all green; 1 at least one leg refused; 2 a leg errored. Never conflated (P-80).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
RULE="$ROOT/.softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py"
EVIDENCE="$ROOT/.softhouse/capture/t219-g8-residual/out/classify-t219.json"

echo "================================================================================"
echo "T271 -- B-1: the verdict/predicate defect in t219-g8-residual"
echo "HEAD         : $(git -C "$ROOT" rev-parse HEAD)"
echo "vector store : $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
echo "================================================================================"

WORST=0
note() {
  local name="$1" rc="$2"
  echo ">>> $name exit $rc"
  if [ "$rc" -gt "$WORST" ]; then WORST="$rc"; fi
}

echo ""
echo "### 1. REPRODUCE THE RED FIRST -- the rule as it stands on main, before anything of mine"
RC=0
python3 "$RULE" "$EVIDENCE" || RC=$?
note "check_verdict_predicate_agreement.py (main register) EXPECTED 1" "$RC"
if [ "$RC" -ne 1 ]; then
  echo "!! the baseline did not refuse. The rest of this run measures nothing."
  exit 1
fi
WORST=0

echo ""
echo "### 2. Re-derive all seven P2 carriers from the RAW capture, integer minor units"
RC=0
python3 "$HERE/rederive_t219_carriers.py" || RC=$?
note rederive_t219_carriers.py "$RC"

echo ""
echo "### 2b. The SAME seven carriers, re-derived by a SECOND instrument written independently"
RC=0
python3 "$HERE/independent_recheck_t271.py" || RC=$?
note independent_recheck_t271.py "$RC"

echo ""
echo "### 2c. Reconcile the two BY RUNNING THEM, never by arithmetic (P-83)"
RC=0
python3 "$HERE/reconcile_probes_t271.py" || RC=$?
note reconcile_probes_t271.py "$RC"

echo ""
echo "### 3. Prove the two edits in t219-g8-residual are labelled corrections, not retro-edits"
RC=0
bash "$HERE/prove_comment_only.sh" || RC=$?
note prove_comment_only.sh "$RC"

echo ""
echo "### 4. GREEN -- the same evidence under T271's acknowledgement register"
RC=0
python3 "$RULE" --acknowledgements "$HERE/acknowledged-t219.json" "$EVIDENCE" || RC=$?
note "check_verdict_predicate_agreement.py (T271 register) EXPECTED 0" "$RC"

echo ""
echo "### 5. The RED/GREEN battery, including the negative controls and T268 forward-compat"
RC=0
python3 "$HERE/red/drive-red-t271.py" || RC=$?
note drive-red-t271.py "$RC"

echo ""
echo "### 6. The target-list runner T269 is meant to install -- both files in one invocation"
RC=0
python3 "$HERE/run_rvpa_over_targets.py" || RC=$?
note "run_rvpa_over_targets.py EXPECTED 0" "$RC"

echo ""
echo "### 7. Fail-open lint, pointed at T271's OWN instruments first (P-80)"
RC=0
python3 "$ROOT/.softhouse/capture/t256-verdict-predicate/lint_failopen_t259.py" "$HERE" || RC=$?
note lint_failopen_t259.py "$RC"

echo ""
echo "### 8. RE-MEASURE the target list's completeness -- is t219 still the only new carrier?"
echo "    T259's census figures are NOT restated here; they are re-taken (P-83)."
RC=0
# DELIBERATELY PIPELINE-FREE. `cmd | tail` discards the producer's exit status unless `pipefail`
# happens to be set, and an instrument whose status depends on a shell option set 60 lines away
# is one `set +o pipefail` from fail-open. Redirect, then read the file.
CENSUS_OUT="$HERE/out/census-rerun-at-t271.txt"
python3 "$ROOT/.softhouse/capture/t256-verdict-predicate/census_verdict_shape.py" \
  > "$CENSUS_OUT" 2>&1 || RC=$?
tail -30 "$CENSUS_OUT"
note "census_verdict_shape.py (read-only, re-measured)" "$RC"

echo ""
echo "### 9. AN OUT-OF-SCOPE DEFECT THIS TASK TRIPPED OVER: P-88, still live at this HEAD."
echo "    The conformance bar is GREEN if and only if /tmp/t234_matrix2.txt happens to exist."
echo "    Measured, not fixed -- t234's instrument and conformance.sh's pin are both outside"
echo "    T271's scope and both contended this fire. The probe RESTORES THE HOST STATE IT FOUND"
echo "    (/tmp is shared with concurrent workers), so it neither manufactures the green nor"
echo "    forces the red on anybody else. Measured live: the file REAPPEARED seconds after an"
echo "    earlier draft deleted it, so the bar's colour depends on inter-agent timing too."
RC=0
bash "$HERE/probe_tmp_dependency_t271.sh" || RC=$?
note "probe_tmp_dependency_t271.sh (diagnostic; 0 = contingency DEMONSTRATED)" "$RC"
# NOTE ON THE POLARITY, because it inverts what a reader expects. This probe exits 0 when the
# contingency IS demonstrated -- i.e. 0 means "the defect is real and reproduced", which is the
# honest reading of a diagnostic. It exits 1 when the classification does NOT move with the file,
# which would mean T271's explanation of the red bar is WRONG and must not be quoted. So a 1 here
# rightly poisons this run's worst-exit: it is a statement about T271's own claim, not about t234.

echo ""
echo "================================================================================"
echo "T271 RUN: worst exit $WORST"
echo "vector store at end: $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
echo "================================================================================"
exit "$WORST"
