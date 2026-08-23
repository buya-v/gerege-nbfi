#!/usr/bin/env bash
# T290 -- the reviewer's own instruments for the T271 review, in the order a reader should meet
# them. Every transcript in `out/` is produced by this script.
#
# NOTHING CALLS THIS. `.softhouse/conformance.sh` is contended by T273/T285 and T290 may not touch
# it; the guard this directory contains is a SPECIFICATION for T269 plus a red drive that proves
# it is not decorative. Saying that here, in the file, rather than only in a handoff, is the
# minimum (P-89: prose does not fire on the next fire).
#
# EXIT: 0 every leg behaved as this review predicts; 1 a leg did not; 2 a leg errored.
# Never conflated (P-80).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
OUT="$HERE/out"
mkdir -p "$OUT"

WORST=0
note() {
  local name="$1" rc="$2" want="$3"
  echo ">>> $name exit $rc (expected $want)"
  if [ "$rc" -ne "$want" ]; then
    echo "!!! $name did NOT behave as this review predicts"
    if [ 1 -gt "$WORST" ]; then WORST=1; fi
  fi
}

echo "================================================================================"
echo "T290 -- INDEPENDENT REVIEW of T271 (B-1, t219-g8-residual)"
echo "HEAD         : $(git -C "$ROOT" rev-parse HEAD)"
echo "vector store : $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
echo "================================================================================"

RULE="$ROOT/.softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py"
EVIDENCE="$ROOT/.softhouse/capture/t219-g8-residual/out/classify-t219.json"
ACK271="$ROOT/.softhouse/capture/t271-b1-t219/acknowledged-t219.json"

echo ""
echo "### 0. REPRODUCE BOTH DIRECTIONS MYSELF, before reading any of T271's conclusions."
echo "    RED: the rule as it stands on main. GREEN: the same evidence under T271's register."
RC=0; python3 "$RULE" "$EVIDENCE" > "$OUT/red-reproduced.txt" 2>&1 || RC=$?
tail -8 "$OUT/red-reproduced.txt"; note "R-VPA on main's register (RED)" "$RC" 1
RC=0; python3 "$RULE" --acknowledgements "$ACK271" "$EVIDENCE" > "$OUT/green-reproduced.txt" 2>&1 || RC=$?
tail -8 "$OUT/green-reproduced.txt"; note "R-VPA under T271's register (GREEN)" "$RC" 0
echo "    counted with this review's OWN instrument, not with the rule's summary line."
echo "    A shell count here was six fail-open findings; see the header of the counter."
RC=0
python3 "$HERE/count_disagreement_blocks_t290.py" \
  "$OUT/red-reproduced.txt" "$OUT/green-reproduced.txt" || RC=$?
note count_disagreement_blocks_t290.py "$RC" 0

echo ""
echo "### 1. RE-DERIVE THE MONEY MYSELF, from the raw capture, in integer minor units."
echo "    Reads the raw gz and prediction.json ONLY; an open() interposer makes reading"
echo "    classify-t219.json or any T271 instrument a hard error."
RC=0; python3 "$HERE/rederive_t290.py" > "$OUT/rederive-t290.txt" 2>&1 || RC=$?
tail -32 "$OUT/rederive-t290.txt"; note rederive_t290.py "$RC" 0

echo ""
echo "### 1b. Verify the three T271 claims a reviewer must not take on trust: that its INDEP"
echo "    instrument really is independent (audit hook + adversarial swap), that the"
echo "    conformance.sh anchors are what T271 says, and that its reported exit 1 is a true"
echo "    no-match, calibrated on a known positive and on a deliberately broken search."
# The word that used to be on the line above was the name of the search program. T259's lint
# scans printed strings too and flagged it as a bare invocation (P-75). Reworded rather than
# silenced with the lint's `ok` escape hatch, which would switch the detector off for the file.
RC=0; python3 "$HERE/verify_t271_claims_t290.py" > "$OUT/verify-t271-claims.txt" 2>&1 || RC=$?
cat "$OUT/verify-t271-claims.txt"; note verify_t271_claims_t290.py "$RC" 0

echo ""
echo "### 2. ATTACK THE ACKNOWLEDGEMENT -- five attacks, four of which fail to break it."
RC=0; python3 "$HERE/attack_acknowledgement_t290.py" > "$OUT/attack-acknowledgement.txt" 2>&1 || RC=$?
cat "$OUT/attack-acknowledgement.txt"; note attack_acknowledgement_t290.py "$RC" 0

echo ""
echo "### 2b. BREAK T271's battery leg G1 on purpose and show the red. A claim about a guard is"
echo "    worth what its red drive is worth; G1 is what T271's whole 'green by acknowledgement,"
echo "    not by lowering' argument rests on."
RC=0; bash "$HERE/break_battery_g1_t290.sh" > "$OUT/battery-g1-broken.txt" 2>&1 || RC=$?
tail -14 "$OUT/battery-g1-broken.txt"; note break_battery_g1_t290.sh "$RC" 0

echo ""
echo "### 3. THE GUARD CONDITION T269 MUST WIRE, and the red drive that separates it from the"
echo "    one T271 specified. R2/R3 are the finding: T271-SPEC GREEN, T290-GUARD REFUSED."
RC=0; python3 "$HERE/red/drive-red-t290.py" > "$OUT/red-drive-t290.txt" 2>&1 || RC=$?
cat "$OUT/red-drive-t290.txt"; note drive-red-t290.py "$RC" 0

echo ""
echo "### 3b. IS THE FINDING STILL CURRENT? main moved under this review and T286 rewrites the"
echo "    rule. Measured against BOTH rules on three trees rather than read off either"
echo "    docstring -- a reviewer shipping a stale finding is P-80 applied to a finding."
RC=0; python3 "$HERE/probe_t286_rule_t290.py" > "$OUT/t286-currency.txt" 2>&1 || RC=$?
cat "$OUT/t286-currency.txt"; note probe_t286_rule_t290.py "$RC" 0

echo ""
echo "### 4. The guard on the clean tree, so no green here is explicable by the guard being inert."
RC=0; python3 "$HERE/guard_rvpa_floor_t290.py" > "$OUT/guard-green.txt" 2>&1 || RC=$?
tail -12 "$OUT/guard-green.txt"; note guard_rvpa_floor_t290.py "$RC" 0

echo ""
echo "### 5. F-T290-2's disposition repair moves no measured number."
RC=0; python3 "$HERE/prove_repair_inert.py" > "$OUT/disposition-repair-is-inert.txt" 2>&1 || RC=$?
cat "$OUT/disposition-repair-is-inert.txt"; note prove_repair_inert.py "$RC" 0

echo ""
echo "### 6. ADJUDICATING what T271 declined to rule on: calibration[] does not reproduce."
echo "    EXPECTED EXIT 1 -- it is a REAL measured negative about pre-existing committed"
echo "    evidence, not a T290 failure. A 0 here would mean the contradiction went away."
RC=0; python3 "$HERE/diagnose_calibration_t290.py" > "$OUT/calibration-diagnosis.txt" 2>&1 || RC=$?
cat "$OUT/calibration-diagnosis.txt"; note diagnose_calibration_t290.py "$RC" 1

echo ""
echo "### 7. Fail-open lint, pointed at T290's OWN instruments first (P-81: writing the rule"
echo "    does not immunise you against it; only the guard does)."
RC=0
python3 "$ROOT/.softhouse/capture/t256-verdict-predicate/lint_failopen_t259.py" "$HERE" \
  > "$OUT/lint-t290-own.txt" 2>&1 || RC=$?
tail -8 "$OUT/lint-t290-own.txt"; note lint_failopen_t259.py "$RC" 0

echo ""
echo "### 8. The committed evidence this review touched is byte-unchanged."
# DELIBERATELY PIPELINE-FREE: piping into grep discards the producer's exit status unless
# pipefail happens to be set. Redirect, then test the file.
#
# THIS LINE WAS A FINDING AGAINST ITSELF, and it is recorded rather than quietly repaired. The
# first draft said the sentence above inside a double-quoted `echo`, with the words cmd-pipe-grep
# wrapped in BACKTICKS. In double quotes bash EXECUTES a backtick span (P-74 -- an unescaped
# backtick in a quoted string executes, and has already silently deleted a word and amended a
# commit in this program), and T259's lint flagged the same line for a second reason (P-75 --
# a bare `grep` may resolve to bundled ugrep). One line, two of this program's recorded defects,
# inside the leg whose whole subject is fail-open shell. `lint_failopen_t259.py` over this
# directory now: findings 0, exit 0.
RC=0
git -C "$ROOT" status --porcelain -- \
  .softhouse/capture/t219-g8-residual \
  .softhouse/capture/t229-g8-site3 \
  .softhouse/capture/t256-verdict-predicate \
  .softhouse/capture/t271-b1-t219 \
  .softhouse/conformance.sh > "$OUT/evidence-unmoved.txt" 2>&1 || RC=$?
if [ -s "$OUT/evidence-unmoved.txt" ]; then
  echo "!!! evidence MOVED:"; cat "$OUT/evidence-unmoved.txt"; WORST=1
else
  echo "    (empty porcelain = nothing this review ran left a file moved)"
fi
note "git status over the evidence" "$RC" 0

echo ""
echo "================================================================================"
echo "T290 RUN: worst exit $WORST"
echo "vector store at end: $(git -C "$ROOT" rev-parse HEAD:.softhouse/vectors)"
echo "================================================================================"
exit "$WORST"
