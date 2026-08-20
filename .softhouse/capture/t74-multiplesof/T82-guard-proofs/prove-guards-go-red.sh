#!/bin/bash
# ---------------------------------------------------------------------------------------------
# T82 — CONSTRUCT AN INPUT THAT SHOULD MAKE EACH REWRITTEN GUARD FAIL, AND SHOW IT FAILING.
#
# The bar for T82 is explicit: "a guard you cannot make go red is still dead." Every guard this task
# rewrote is exercised here against an input built to break it, and the transcript is committed
# alongside (`TRANSCRIPT.txt`).
#
# The mutations are applied to COPIES under `scratch/`. Nothing here writes to
# `.softhouse/capture/src/run-pass3i.sh`, to `.softhouse/capture/out/`, or to any vector.
#
# NO ORACLE, NO DOCKER, NO DATABASE, NO CONTAINER. Committed artefacts only.
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

rm -rf "$S"
mkdir -p "$S"

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
echo "capture under test     sha256 $(shasum -a 256 "$CAP" | cut -d' ' -f1)"

# ==============================================================================================
# CONTROL — the committed artefact, unmutated, must still be GREEN.
# A proof that only shows red is half a proof: a guard that fires on everything is as useless as
# one that fires on nothing.
# ==============================================================================================
expect 0 "CONTROL — committed pass-3i capture through the corrected precondition block" -- \
  bash "$DRIVER" "$CAP" "$S/att-control.json"

# ==============================================================================================
# E-1 / GUARD 17a — an id in EXPECTED_IDS that CASE_PRECISION does not register.
#
# This is the edit the guard exists to catch and the one the old form could not: someone adds a case
# to the harness and to EXPECTED_IDS and forgets the precision table. Under the OLD form the table
# was built by looping over EXPECTED_IDS, so the new id was silently registered from its own suffix
# (19, because it does not end in `-p12`) and the run proceeded. Both halves are mutated here, script
# AND capture, because that is what the real edit looks like: the harness emits the case, so the id
# list matches and check 8 passes.
# ==============================================================================================
python3 "$HERE/mutate.py" add-unregistered-case "$SRC" "$CAP" \
  "$S/17a-run.sh" "$S/17a-capture.json" > "$S/17a-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17a-mutation.txt"
expect 1 "E-1 GUARD 17a — unregistered id must FAIL THE RUN (the claim that was unreachable)" -- \
  env T82_SCRIPT="$S/17a-run.sh" bash "$DRIVER" "$S/17a-capture.json" "$S/att-17a.json"

# --- and the SAME mutation against the OLD, pre-T82 form of the guard, to show the fix is real ---
python3 "$HERE/mutate.py" restore-old-table "$S/17a-run.sh" "$CAP" \
  "$S/17a-old-run.sh" "$S/17a-old-capture.json" > "$S/17a-old-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17a-old-mutation.txt"
expect 0 "E-1 COUNTERPROOF — the SAME unregistered id through the OLD self-constructed table" -- \
  env T82_SCRIPT="$S/17a-old-run.sh" bash "$DRIVER" "$S/17a-capture.json" "$S/att-17a-old.json"

# ==============================================================================================
# E-1 / GUARD 17b — a CASE_PRECISION entry this run does not capture.
#
# The other direction, and the reason the table is checked both ways: a stale entry is how a table
# stops describing the run it is validating. Script-only mutation.
# ==============================================================================================
python3 "$HERE/mutate.py" add-stale-entry "$SRC" "$CAP" \
  "$S/17b-run.sh" "$S/17b-capture.json" > "$S/17b-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17b-mutation.txt"
expect 1 "E-1 GUARD 17b — stale CASE_PRECISION entry must FAIL THE RUN" -- \
  env T82_SCRIPT="$S/17b-run.sh" bash "$DRIVER" "$CAP" "$S/att-17b.json"

# ==============================================================================================
# E-1 / GUARD 17c — a case that runs at a precision the table does not name for it.
#
# The per-case half, inside the `bad` loop. Capture-only mutation: T74-E-P4 is registered at 19 and
# is made to report 12.
# ==============================================================================================
python3 "$HERE/mutate.py" wrong-precision "$SRC" "$CAP" \
  "$S/17c-run.sh" "$S/17c-capture.json" > "$S/17c-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/17c-mutation.txt"
expect 1 "E-1 GUARD 17c — a case at a precision its table entry forbids must FAIL THE RUN" -- \
  bash "$DRIVER" "$S/17c-capture.json" "$S/att-17c.json"

# ==============================================================================================
# E-2 / GUARD 18 — the LIVE half of the misfiling check.
#
# The two dead halves intersected `probe_ids` with its own complement and are gone. The half kept
# compares two INDEPENDENTLY derived sets: ids that promise precision 12 by NAME, and ids OBSERVED
# running below 19. To make them disagree, register a non-`-p12` case at 12 (script) and make it run
# at 12 (capture) — so guard 17 is satisfied and guard 18 is the one that has to catch it. That is
# exactly the "somebody adds an unnamed probe" edit the sidecar classification exists to prevent.
# ==============================================================================================
python3 "$HERE/mutate.py" unnamed-probe "$SRC" "$CAP" \
  "$S/18-run.sh" "$S/18-capture.json" > "$S/18-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/18-mutation.txt"
expect 1 "E-2 GUARD 18 — a probe that is not named \`-p12\` must FAIL THE RUN" -- \
  env T82_SCRIPT="$S/18-run.sh" bash "$DRIVER" "$S/18-capture.json" "$S/att-18.json"

# ==============================================================================================
# E-3 — build-counterfactuals.py's rounding-mode predicate.
#
# The old predicate was the Python chained comparison
#     ia[mode] != ib[mode] != 'HALF_UP'
# which Python evaluates as (ia != ib) and (ib != 'HALF_UP'). When BOTH arms ran at the same
# non-ratified mode the first conjunct is FALSE, so the whole thing is false and the guard PASSES —
# and "both arms at the same non-ratified mode" is precisely the case the varying-inputs check above
# it cannot catch, because a shared value does not vary.
#
# Three runs: the legitimate capture (must still pass), both arms at HALF_DOWN (must now fail), and
# one arm at HALF_DOWN (the case the OLD predicate did catch, which must keep failing).
# ==============================================================================================
expect 0 "E-3 LEGITIMATE — the committed capture, both arms HALF_UP, must still PASS" -- \
  python3 "$CF" "$CAP" "$S/cf-legit.json"

python3 "$HERE/mutate.py" both-arms-half-down "$SRC" "$CAP" \
  "$S/e3-run.sh" "$S/e3-both-half-down.json" > "$S/e3-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/e3-mutation.txt"
expect 1 "E-3 GUARD — BOTH arms at the non-ratified HALF_DOWN must now FAIL" -- \
  python3 "$CF" "$S/e3-both-half-down.json" "$S/cf-both.json"

python3 "$HERE/mutate.py" one-arm-half-down "$SRC" "$CAP" \
  "$S/e3b-run.sh" "$S/e3-one-half-down.json" > "$S/e3b-mutation.txt" 2>&1
sed -e 's/^/  MUTATION: /' "$S/e3b-mutation.txt"
expect 1 "E-3 GUARD — ONE arm at HALF_DOWN must keep FAILING (no regression)" -- \
  python3 "$CF" "$S/e3-one-half-down.json" "$S/cf-one.json"

# ==============================================================================================
# D-1 / D-2 — the promotion script's derived fields and its absent-key handling.
# ==============================================================================================
expect 1 "D-1 GUARD — a capture whose daysInMonth/daysInYear are not 30/360 must be REFUSED" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" day-count

expect 1 "D-1 GUARD — a capture with a NON-ZERO downPaymentPercentage must be REFUSED" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" down-payment

expect 1 "D-1 GUARD — a capture with downPaymentEnabled true must be REFUSED" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" down-payment-enabled

expect 1 "D-2 GUARD — a capture with NO repayment-every key at all must be REFUSED" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" repayment-every-absent

expect 1 "D-2 GUARD — a capture whose two repayment-every keys DISAGREE must be REFUSED" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" repayment-every-conflict

expect 0 "D-2 CONTROL — a legitimate periodNumber of 0 must SURVIVE, not collapse into the fallback" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" period-number-zero

expect 1 "D-2 GUARD — a non-integer periodNumber must be REFUSED, not coerced" -- \
  python3 "$HERE/prove-promote-guards.py" "$ROOT" period-number-bad

echo
echo "=============================================================================="
echo "T82 guard proofs: $pass as expected, $fail not as expected"
echo "=============================================================================="
[ "$fail" -eq 0 ] || exit 1
