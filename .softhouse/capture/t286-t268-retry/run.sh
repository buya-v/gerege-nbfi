#!/usr/bin/env bash
# T292 -- reproduce every number in the handoff, in order, from a clean checkout.
#
# NOTHING HERE SWALLOWS AN EXIT STATUS. Each stage's code is captured into a variable and
# CLASSIFIED; an unexpected code is a REFUSAL of this script, never a silent pass. `set -euo
# pipefail` is on and no stage is wrapped in `|| true`.
#
# P-75: `grep` in this environment is the bundled ugrep with hidden --exclude-dir behaviour, and
# `rg` is not installed at all. Every search below uses /usr/bin/grep explicitly.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/out"
mkdir -p "$OUT"

say() { printf '%s\n' "$*"; }

say "T292 -- R-VPA fail-closed by construction. Reproducing all stages."
say "  rule    : $HERE/check_verdict_predicate_agreement_t292.py"
say "  blob    : $(git hash-object "$HERE/check_verdict_predicate_agreement_t292.py")"
say "  python  : $(python3 -c 'import sys;print(sys.version.split()[0])')"
say ""

# ------------------------------------------------------------------ 1. the census that decided
# the design. Measured BEFORE the coverage predicate was written, not after it (P-72: calibrate,
# and publish the calibration).
say "== 1. real-corpus census =="
CENSUS_RC=0
python3 "$HERE/probe/census_real_corpus.py" \
  "$HERE/../t229-g8-site3/out/classify-t229.json" \
  "$HERE/../t219-g8-residual/out/classify-t219.json" \
  | tee "$OUT/census-real-corpus.txt" || CENSUS_RC=$?
case "$CENSUS_RC" in
  0) say "   census OK" ;;
  *) say "   CENSUS FAILED rc=$CENSUS_RC -- the design rationale is UNMEASURED"; exit 1 ;;
esac
say ""

# ------------------------------------------------------------------ 2. the adversary
say "== 2. adversary: PROP-A container invariance, PROP-B no vacuous green,"
say "      PROP-C lost-refusal ledger vs the pinned PRE blob, PROP-D error/verdict separation =="
ADV_RC=0
python3 "$HERE/probe/adversary_t292.py" --seeds "${SEEDS:-12}" \
  | tee "$OUT/adversary-t292.txt" || ADV_RC=$?
case "$ADV_RC" in
  0) say "   ADVERSARY PASS" ;;
  1) say "   ADVERSARY FAIL -- a property was violated, a leg was SKIPPED, or a refusal was LOST"
     exit 1 ;;
  *) say "   ADVERSARY ERROR rc=$ADV_RC -- this run measured nothing"; exit 2 ;;
esac
say ""

# ------------------------------------------------------------------ 3. mutant kill
say "== 3. mutant kill: break the rule on purpose, watch the adversary go RED =="
MUT_RC=0
python3 "$HERE/probe/mutants_t292.py" --seeds "${MUT_SEEDS:-2}" \
  | tee "$OUT/mutants-t292.txt" || MUT_RC=$?
case "$MUT_RC" in
  0) say "   ALL MUTANTS KILLED" ;;
  1) say "   A MUTANT SURVIVED -- the adversary cannot see a planted defect, so its green is"
     say "   worth nothing (P-45's harder sibling: a guard nobody has watched fail)"
     exit 1 ;;
  *) say "   MUTANT RUNNER ERROR rc=$MUT_RC"; exit 2 ;;
esac
say ""

# ------------------------------------------------------------------ 3b. calibrate the headline
# number. A counter only ever observed reading zero is indistinguishable from one that cannot
# count -- P-45 pointed at a statistic instead of a guard.
say "== 3b. calibrate LOST REFUSALS: plant the lineage's defect and watch the counter FIRE =="
CAL_RC=0
python3 "$HERE/probe/prove_adversary_sees_a_lost_refusal.py" \
  | tee "$OUT/lost-refusal-calibration.txt" || CAL_RC=$?
case "$CAL_RC" in
  0) say "   COUNTER FIRES -- 'LOST REFUSALS: 0' on the shipped rule is a measurement" ;;
  1) say "   COUNTER DID NOT FIRE on a planted lost refusal. Every 'LOST REFUSALS: 0' in this"
     say "   directory is decoration until this passes."
     exit 1 ;;
  *) say "   CALIBRATION ERROR rc=$CAL_RC"; exit 2 ;;
esac
say ""

# ------------------------------------------------------------------ 4. the measured negatives
say "== 4. negative result: what gating headerAffirmations would cost =="
NEG_RC=0
python3 "$HERE/probe/negative_result_header_affirmations.py" \
  | tee "$OUT/negative-result-header-affirmations.txt" || NEG_RC=$?
case "$NEG_RC" in
  0) say "   NEGATIVE RESULT DEMONSTRATED" ;;
  *) say "   NEGATIVE RESULT NOT DEMONSTRATED rc=$NEG_RC -- re-read the table"; exit 1 ;;
esac
say ""

say "== 5. F-T290-1b, driven against THIS rule (expected: STILL OPEN) =="
F290_RC=0
python3 "$HERE/probe/drive_f_t290_1b.py" \
  | tee "$OUT/f-t290-1b-driven.txt" || F290_RC=$?
case "$F290_RC" in
  0) say "   every arm behaved as claimed, INCLUDING the arm that shows the hole is open" ;;
  *) say "   F-T290-1b probe rc=$F290_RC -- an arm did NOT behave as claimed"; exit 1 ;;
esac
say ""

# ------------------------------------------------------------------ 6. fail-open lint, on OUR OWN
# instruments first -- P-81: the fail-open guard caught three workers' own instruments in one fire,
# including two written to enforce the very rule they broke.
say "== 6. T259 fail-open lint, pointed at T292's own instruments =="
LINT_RC=0
python3 "$HERE/../t256-verdict-predicate/lint_failopen_t259.py" "$HERE" \
  | tee "$OUT/lint-failopen-t292.txt" || LINT_RC=$?
case "$LINT_RC" in
  0) say "   LINT CLEAN" ;;
  1) say "   LINT FINDINGS -- repair them before quoting any number above"; exit 1 ;;
  *) say "   LINT ERROR rc=$LINT_RC"; exit 2 ;;
esac
say ""

# ------------------------------------------------------------------ 7. scope guard, read not asserted
#
# THE BASELINE IS THE MERGE BASE, NOT `main`. The first draft of this stage diffed against `main`
# and reported `conformance.sh CHANGED (1 lines) -- scope violation` on a branch that has never
# touched the file. `main` MOVED WHILE THIS BRANCH RAN -- T293, T294, T295 and T300 all landed
# edits to conformance.sh -- so diffing a long-lived branch against a moving tip measures OTHER
# PEOPLE'S WORK AND ATTRIBUTES IT TO YOU. That is the same species as everything else in this
# directory: a guard that fires confidently while measuring the wrong thing. The question "did I
# touch this file" has exactly one correct baseline: the commit I forked from.
say "== 7. scope: conformance.sh must be untouched BY THIS BRANCH =="
BASE="$(git -C "$HERE/../../.." merge-base HEAD main)"
say "   merge-base (this branch's fork point): $BASE"
GG=0
git -C "$HERE/../../.." diff --name-only "$BASE" HEAD -- .softhouse/conformance.sh \
  > "$OUT/scope-conformance.txt" || GG=$?
case "$GG" in
  0) : ;;
  *) say "   git diff rc=$GG -- the question is UNANSWERED"; exit 2 ;;
esac
# Recorded, not gating: how far main has moved on this file since the fork, so a reader is not
# surprised by a merge conflict and does not mistake it for a scope violation.
git -C "$HERE/../../.." log --oneline "$BASE..main" -- .softhouse/conformance.sh \
  > "$OUT/scope-conformance-main-moved.txt" || true   # lint-failopen: ok -- CENSUS ONLY, not gating; the gating read is the merge-base diff above, whose status IS classified
# NOT `grep -c`: it exits 1 on zero matches, and the only way to use it here would be to swallow
# that status, which is the defect this whole directory is about. `wc -l` cannot lie about a
# count it did not take.
HITS="$(/usr/bin/wc -l < "$OUT/scope-conformance.txt" | /usr/bin/tr -d ' ')"
MAIN_MOVED="$(/usr/bin/wc -l < "$OUT/scope-conformance-main-moved.txt" | /usr/bin/tr -d ' ')"
case "$HITS" in
  0) say "   conformance.sh: 0 changed paths vs the fork point. SCOPE GUARD HELD."
     say "   (census, not gating: main has $MAIN_MOVED commits touching conformance.sh since the"
     say "    fork -- other tasks' work, not this branch's)" ;;
  *) say "   conformance.sh CHANGED BY THIS BRANCH ($HITS paths) -- scope violation"; exit 1 ;;
esac
say ""
say "ALL STAGES PASSED."
