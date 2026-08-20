#!/bin/bash
# ---------------------------------------------------------------------------------------------
# T82 — CONSTRUCT AN INPUT THAT SHOULD MAKE EACH REWRITTEN GUARD FAIL, AND SHOW IT FAILING.
#
# The bar for T82 is explicit: "a guard you cannot make go red is still dead." Every guard this task
# rewrote is exercised here against an input built to break it, and the transcript is committed
# alongside (`TRANSCRIPT.txt`).
#
# EVERY CASE IS LABELLED WITH WHAT IT PROVES, because T87 rejected the first version of this rig for
# a case that could not discriminate while printing that it had:
#
#   GUARD        the corrected code REFUSES an input that the PRE-FIX code ACCEPTS. Each is paired
#                with a COUNTERPROOF run against the FORK POINT'S REAL EXTRACTED BYTES — never a
#                reconstruction, and never the moving ref `main` — because "the new code refuses X"
#                only demonstrates a cure alongside "the old code did not".
#   CONTROL      the honest input must stay GREEN. A guard that fires on everything is as useless as
#                one that fires on nothing.
#   REGRESSION   both codebases agree and must go on agreeing. Proves the rewrite broke nothing;
#                proves NOTHING about the defect, and says so.
#
# The mutations are applied to COPIES under `scratch/`. Nothing here writes to
# `.softhouse/capture/src/run-pass3i.sh`, to `.softhouse/capture/out/`, or to any vector.
#
# NO ORACLE, NO DOCKER, NO DATABASE, NO CONTAINER. Committed artefacts and `git show` only.
#
#   usage: bash prove-guards-go-red.sh
# ---------------------------------------------------------------------------------------------
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
SRC="$ROOT/.softhouse/capture/src/run-pass3i.sh"
CAP="$ROOT/.softhouse/capture/out/capture-prod3i-raw.json"
CF="$ROOT/.softhouse/capture/t74-multiplesof/build-counterfactuals.py"
S="$HERE/scratch"
DRIVER="$HERE/run-precondition-block.sh"
PROMOTE="$HERE/prove-promote-guards.py"

rm -rf "$S"
mkdir -p "$S"

# --- the PRE-FIX bytes, for every counterproof -------------------------------------------------
# T87's method, adopted: a counterproof against a RECONSTRUCTION of the old code proves less than one
# against the old code. These are extracted from git, not rebuilt from a string literal.
#
# THE BASELINE IS PINNED TO THE FORK POINT, NOT TO `main`. An earlier version of this rig used the
# moving ref `main:`, which is a TIME BOMB: the moment this branch merges, `main` contains the FIX,
# every COUNTERPROOF row starts asserting that the fixed code accepts a mutation it is designed to
# refuse, and all seven flip to failing — against the rig itself. A proof harness that goes red on
# merge is exactly the evidence-integrity defect this task was rejected for once already. The fork
# point is immutable and keeps meaning "the code as it stood before this branch" forever.
BASE="$(git -C "$ROOT" merge-base main HEAD)"
git -C "$ROOT" show "$BASE:.softhouse/capture/src/run-pass3i.sh"      > "$S/run-pass3i-BASE.sh"
git -C "$ROOT" show "$BASE:.softhouse/handoff/T74-promote-vectors.py" > "$S/promote-BASE.py"
git -C "$ROOT" show "$BASE:.softhouse/capture/t74-multiplesof/build-counterfactuals.py" \
                                                                     > "$S/build-counterfactuals-BASE.py"

pass=0
fail=0

# expect <want-exit> <label> -- <command...>
expect() {
  want="$1"; label="$2"; shift 3
  echo
  echo "=============================================================================="
  echo "$label"
  echo "  expecting exit $want"
  echo "------------------------------------------------------------------------------"
  "$@" > "$S/last.out" 2>&1
  got=$?
  sed -e 's/^/  | /' "$S/last.out"
  echo "------------------------------------------------------------------------------"
  if [ "$got" = "$want" ]; then
    echo "  RESULT: exit $got — AS EXPECTED"
    pass=$((pass + 1))
  else
    echo "  RESULT: exit $got — *** NOT WHAT WAS EXPECTED ($want) ***"
    fail=$((fail + 1))
  fi
}

echo "T82 guard proofs"
echo "run-pass3i.sh          sha256 $(shasum -a 256 "$SRC" | cut -d' ' -f1)"
echo "build-counterfactuals  sha256 $(shasum -a 256 "$CF" | cut -d' ' -f1)"
echo "promote-vectors        sha256 $(shasum -a 256 "$ROOT/.softhouse/handoff/T74-promote-vectors.py" | cut -d' ' -f1)"
echo "capture under test     sha256 $(shasum -a 256 "$CAP" | cut -d' ' -f1)"
echo "fork-point (BASE)      $BASE"
echo "BASE run-pass3i.sh     sha256 $(shasum -a 256 "$S/run-pass3i-BASE.sh" | cut -d' ' -f1)"
echo "BASE promote-vectors   sha256 $(shasum -a 256 "$S/promote-BASE.py" | cut -d' ' -f1)"

# ==============================================================================================
# CONTROL — the committed artefact, unmutated, must still be GREEN.
# ==============================================================================================
expect 0 "CONTROL — committed pass-3i capture through the corrected precondition block" -- \
  bash "$DRIVER" "$CAP" "$S/att-control.json"

# ==============================================================================================
# E-1 / GUARD 17a — an id in EXPECTED_IDS that CASE_PRECISION does not register.
#
# The edit the guard exists to catch and the one the old form could not: somebody adds a case to the
# harness and to EXPECTED_IDS and forgets the precision table. Both halves are mutated, script AND
# capture, because that is what the real edit looks like — the harness emits the case, so the id list
# matches and check 8 passes.
# ==============================================================================================
python3 "$HERE/mutate.py" add-unregistered-case "$SRC" "$CAP" \
  "$S/17a-run.sh" "$S/17a-capture.json" > "$S/17a-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17a-mutation.txt"
expect 1 "E-1 GUARD 17a — unregistered id must FAIL THE RUN (the claim that was unreachable)" -- \
  env T82_SCRIPT="$S/17a-run.sh" bash "$DRIVER" "$S/17a-capture.json" "$S/att-17a.json"

# --- COUNTERPROOF, against the FORK POINT'S REAL BYTES ------------------------------------------------
# The same mutation applied to the fork point's run-pass3i.sh. Not a reconstruction of the old
# table — the old table itself.
python3 "$HERE/mutate.py" add-unregistered-case "$S/run-pass3i-BASE.sh" "$CAP" \
  "$S/17a-main-run.sh" "$S/17a-main-capture.json" > "$S/17a-main-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17a-main-mutation.txt"
expect 0 "E-1 COUNTERPROOF — the SAME unregistered id through the FORK POINT'S REAL pre-T82 bytes" -- \
  env T82_SCRIPT="$S/17a-main-run.sh" bash "$DRIVER" "$S/17a-main-capture.json" "$S/att-17a-main.json"

# ==============================================================================================
# E-1 / GUARD 17b — a CASE_PRECISION entry this run does not capture.
# ==============================================================================================
python3 "$HERE/mutate.py" add-stale-entry "$SRC" "$CAP" \
  "$S/17b-run.sh" "$S/17b-capture.json" > "$S/17b-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17b-mutation.txt"
expect 1 "E-1 GUARD 17b — stale CASE_PRECISION entry must FAIL THE RUN" -- \
  env T82_SCRIPT="$S/17b-run.sh" bash "$DRIVER" "$CAP" "$S/att-17b.json"

# ==============================================================================================
# E-1 / GUARD 17c — a case that runs at a precision the table does not name for it.
# ==============================================================================================
python3 "$HERE/mutate.py" wrong-precision "$SRC" "$CAP" \
  "$S/17c-run.sh" "$S/17c-capture.json" > "$S/17c-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17c-mutation.txt"
expect 1 "E-1 GUARD 17c — a case at a precision its table entry forbids must FAIL THE RUN" -- \
  bash "$DRIVER" "$S/17c-capture.json" "$S/att-17c.json"

# ==============================================================================================
# E-2 / GUARD 18 — the LIVE half of the misfiling check, BOTH directions.
#
# The two dead halves intersected `probe_ids` with its own complement and are gone. The half kept
# compares two INDEPENDENTLY derived sets: ids that promise precision 12 by NAME, and ids OBSERVED
# running below 19.
#
# (a) register a non-`-p12` case at 12 and run it at 12 — an unnamed probe;
# (b) register a `-p12` case at 19 and run it at 19 — a name that promises a precision it does not
#     run. Direction (b) was added after T87 exercised it and T82's rig had not.
# In both, guard 17 is SATISFIED, so guard 18 is the one that has to catch it.
# ==============================================================================================
python3 "$HERE/mutate.py" unnamed-probe "$SRC" "$CAP" \
  "$S/18a-run.sh" "$S/18a-capture.json" > "$S/18a-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/18a-mutation.txt"
expect 1 "E-2 GUARD 18(a) — a probe that is not named \`-p12\` must FAIL THE RUN" -- \
  env T82_SCRIPT="$S/18a-run.sh" bash "$DRIVER" "$S/18a-capture.json" "$S/att-18a.json"

python3 "$HERE/mutate.py" named-probe-at-19 "$SRC" "$CAP" \
  "$S/18b-run.sh" "$S/18b-capture.json" > "$S/18b-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/18b-mutation.txt"
expect 1 "E-2 GUARD 18(b) — a \`-p12\` id that does NOT run below 19 must FAIL THE RUN" -- \
  env T82_SCRIPT="$S/18b-run.sh" bash "$DRIVER" "$S/18b-capture.json" "$S/att-18b.json"

# ==============================================================================================
# E-3 — build-counterfactuals.py's rounding-mode predicate.
#
# The old predicate was the Python chained comparison `ia[mode] != ib[mode] != 'HALF_UP'`, which
# Python evaluates as `(ia != ib) and (ib != 'HALF_UP')`. When BOTH arms ran at the same non-ratified
# mode the first conjunct is FALSE, so the guard PASSED — and that is precisely the case the
# varying-inputs check above it cannot catch, because a value common to both arms does not vary.
# ==============================================================================================
expect 0 "E-3 CONTROL — the committed capture, both arms HALF_UP, must still PASS" -- \
  python3 "$CF" "$CAP" "$S/cf-legit.json"

python3 "$HERE/mutate.py" both-arms-half-down "$SRC" "$CAP" \
  "$S/e3-run.sh" "$S/e3-both-half-down.json" > "$S/e3-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/e3-mutation.txt"
expect 1 "E-3 GUARD — BOTH arms at the non-ratified HALF_DOWN must now FAIL" -- \
  python3 "$CF" "$S/e3-both-half-down.json" "$S/cf-both.json"

expect 0 "E-3 COUNTERPROOF — the SAME both-arms capture through the FORK POINT'S chained comparison" -- \
  python3 "$S/build-counterfactuals-BASE.py" "$S/e3-both-half-down.json" "$S/cf-both-main.json"

python3 "$HERE/mutate.py" one-arm-half-down "$SRC" "$CAP" \
  "$S/e3b-run.sh" "$S/e3-one-half-down.json" > "$S/e3b-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/e3b-mutation.txt"
expect 1 "E-3 GUARD — ONE arm at HALF_DOWN must keep FAILING (no regression)" -- \
  python3 "$CF" "$S/e3-one-half-down.json" "$S/cf-one.json"

# ==============================================================================================
# D-1 — the promotion script's derived request fields.
# ==============================================================================================
expect 1 "D-1 GUARD — a capture whose daysInMonth/daysInYear are not 30/360 must be REFUSED" -- \
  python3 "$PROMOTE" "$ROOT" day-count

expect 0 "D-1 COUNTERPROOF — the FORK POINT accepts it and writes the hard-coded FIXED_30_360" -- \
  python3 "$PROMOTE" "$ROOT" day-count "$S/promote-BASE.py"

expect 1 "D-1 GUARD — a capture with a NON-ZERO downPaymentPercentage must be REFUSED" -- \
  python3 "$PROMOTE" "$ROOT" down-payment

expect 0 "D-1 COUNTERPROOF — the FORK POINT accepts it and writes the hard-coded {0, 1}" -- \
  python3 "$PROMOTE" "$ROOT" down-payment "$S/promote-BASE.py"

expect 1 "D-1 GUARD — a capture with downPaymentEnabled true must be REFUSED" -- \
  python3 "$PROMOTE" "$ROOT" down-payment-enabled

# ==============================================================================================
# D-2 — absence distinguished from a legitimate zero.
# ==============================================================================================
expect 1 "D-2 GUARD — a capture with NO repayment-every key at all must be REFUSED" -- \
  python3 "$PROMOTE" "$ROOT" repayment-every-absent

expect 0 "D-2 COUNTERPROOF — the FORK POINT accepts it and writes a NULL repayment interval" -- \
  python3 "$PROMOTE" "$ROOT" repayment-every-absent "$S/promote-BASE.py"

expect 1 "D-2 GUARD — a capture whose two repayment-every keys DISAGREE must be REFUSED" -- \
  python3 "$PROMOTE" "$ROOT" repayment-every-conflict

# --- THE headline D-2 guard: the case the `or 0` defect actually produced -----------------------
# Added after T87's F-2: the rig shipped without ever exercising the one guard that cures `or 0`.
expect 1 "D-2 GUARD — a PAYABLE row with an ABSENT periodNumber must be REFUSED (the \`or 0\` defect)" -- \
  python3 "$PROMOTE" "$ROOT" period-number-absent-payable

expect 0 "D-2 COUNTERPROOF — the FORK POINT accepts it, writes installment_number 0 and promotes six vectors" -- \
  python3 "$PROMOTE" "$ROOT" period-number-absent-payable "$S/promote-BASE.py"

expect 1 "D-2 GUARD — a NON-PAYABLE row that CARRIES a periodNumber must be REFUSED" -- \
  python3 "$PROMOTE" "$ROOT" period-number-on-nonpayable

expect 0 "D-2 COUNTERPROOF — the FORK POINT accepts that too" -- \
  python3 "$PROMOTE" "$ROOT" period-number-on-nonpayable "$S/promote-BASE.py"

expect 1 "D-2 GUARD — a non-integer periodNumber must be REFUSED, not coerced" -- \
  python3 "$PROMOTE" "$ROOT" period-number-bad

# --- REGRESSION control, honestly labelled -----------------------------------------------------
# NOT a guard proof. The PRE-FIX code decided the VALUE with `or 0` (:255) and the WITHDRAWAL
# with a separate `is None` test (:260-261), so a recorded 0 already survived un-withdrawn there. This case is green on BOTH
# codebases; the mode asserts that they emit the SAME cells rather than claiming they differ.
expect 0 "D-2 REGRESSION — a legitimate periodNumber 0 stays green, and the FORK POINT emits the SAME cells" -- \
  python3 "$PROMOTE" "$ROOT" period-number-zero

echo
echo "=============================================================================="
echo "T82 guard proofs: $pass as expected, $fail not as expected"
echo "=============================================================================="
[ "$fail" -eq 0 ] || exit 1
