#!/bin/bash
# A2-15's RED/GREEN drives.
#
# P-22: "Ship no guard you have not personally driven RED. State the input that
# makes it fail, and commit the transcript." This program has now had THREE
# instances of an unwired guard, so a ledger invariant, a ledger money cell, a
# ledger structural cell, the exemption default-deny and the new census pins are
# each perturbed HERE, through `bash .softhouse/conformance.sh` -- the route that
# actually executes (P-45) -- and each perturbation is REVERTED and the revert is
# verified by digest.
#
# P-62: the exit code is recorded but is never the evidence. `exit 2` is
# overloaded across at least five conditions in this harness, so every case also
# asserts the DIAGNOSTIC LINE it must print.
#
# assert_mutated: a mutation proof over an unmutated file proves nothing and
# looks identical to one that works. Every case checks its own perturbation
# applied before it runs anything.
#
# Run from the repository root:  bash .softhouse/capture/tierA-a2/red-green-a2-15.sh
set -u

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT" || exit 2
VEC="$ROOT/.softhouse/vectors/ledger"
CONF="$ROOT/.softhouse/conformance.sh"
TMP="$(mktemp -d -t a2-15-redgreen)"
pass=0
fail=0

digest_store() { LC_ALL=C shasum -a 256 "$VEC"/*.json | LC_ALL=C shasum -a 256 | cut -d' ' -f1; }
BASE_DIGEST="$(digest_store)"

say() { printf '%s\n' "$*"; }

# expect_red <label> <required-substring> -- runs conformance and demands a
# NON-ZERO exit AND the substring.
expect_red() {
  local label="$1" needle="$2" out rc
  out="$(bash "$CONF" 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ] && printf '%s' "$out" | LC_ALL=C grep -qaF -- "$needle"; then
    say "RED  OK    exit $rc   $label"
    say "           matched: $needle"
    printf '%s' "$out" | LC_ALL=C grep -aF -- "$needle" | head -3 | sed 's/^/           | /'
    pass=$((pass+1))
  else
    say "RED  FAIL  exit $rc   $label"
    say "           the output had to contain: $needle"
    printf '%s' "$out" | tail -25 | sed 's/^/           | /'
    fail=$((fail+1))
  fi
  say ""
}

expect_green() {
  local label="$1" out rc
  out="$(bash "$CONF" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ] && printf '%s' "$out" | LC_ALL=C grep -qa '^VERDICT: PASS'; then
    say "GREEN OK   exit $rc   $label"
    pass=$((pass+1))
  else
    say "GREEN FAIL exit $rc   $label"
    printf '%s' "$out" | tail -20 | sed 's/^/           | /'
    fail=$((fail+1))
  fi
  say ""
}

# perturb <file> <sed-expr> <needle-that-must-now-be-present>
perturb() {
  local f="$1" expr="$2" needle="$3"
  cp "$f" "$TMP/$(basename "$f").orig"
  LC_ALL=C sed -i '' "$expr" "$f"
  if ! LC_ALL=C grep -qaF -- "$needle" "$f"; then
    say "SETUP FAIL the perturbation did not apply to $f, so the case would be VACUOUS"
    fail=$((fail+1))
    return 1
  fi
  return 0
}

restore() {
  local f="$1"
  cp "$TMP/$(basename "$f").orig" "$f"
}

say "======================================================================="
say "A2-15 RED/GREEN DRIVES — every new assertion driven RED through"
say "bash .softhouse/conformance.sh, the route that actually executes (P-45)."
say "ledger vector-set digest before: $BASE_DIGEST"
say "======================================================================="
say ""

expect_green "control: the pristine committed store (anti-no-op — if this ever fails, every RED below is meaningless)"

# ---------------------------------------------------------------------------
# CASE 1 — MONEY, ONE MINOR UNIT. DEC-2 §5.2 requirement 7 (ii).
# ---------------------------------------------------------------------------
F="$VEC/LDG-02-repayment-split-4leg-minor-units.json"
if perturb "$F" 's/"amount_minor": "27045058"/"amount_minor": "27045059"/' '"amount_minor": "27045059"'; then
  expect_red "CASE 1 — ONE MINOR UNIT on a promoted leg (27045058 -> 27045059) must be a MONEY kill with a non-zero margin" \
    "legs[0].amount_minor: MONEY want 27045059, got 27045058 (margin -1 minor units)"
  restore "$F"
fi

# ---------------------------------------------------------------------------
# CASE 2 — STRUCTURAL cell. DEC-2 §5.2 requirement 7 (i).
# ---------------------------------------------------------------------------
if perturb "$F" 's/"gl_account_code": "10201"/"gl_account_code": "10202"/' '"gl_account_code": "10202"'; then
  expect_red "CASE 2 — a resolved gl_account_code (10201 -> 10202) must be a STRUCTURAL kill, reported as a cell difference and not as money" \
    'legs[0].gl_account_code: want "10202", got "10201"'
  restore "$F"
fi

# ---------------------------------------------------------------------------
# CASE 3 — I-1 DOUBLE ENTRY, and A MEASUREMENT THAT CORRECTED THIS CASE.
#
# The first version of this case perturbed one credit leg by a minor unit and
# demanded `INVARIANT double_entry_balances VIOLATED`. IT DID NOT FIRE, and the
# reason is worth more than the case was: THE CORRECT IMPLEMENTATION REFUSES AN
# UNBALANCED ENTRY RATHER THAN POSTING ONE. `GoPoster.PostEntry` calls
# `ledger.DoubleEntryBalances` and returns the oracle's own 403
# (error.msg.glJournalEntry.invalid.mismatch.debits.credits), so no entry ever
# reaches the invariant. That is the RIGHT behaviour -- it is exactly what
# LDG-REFUSE-01 grades -- and it means the VIOLATED branch of I-1 is unreachable
# by perturbing a vector while the correct port is selected.
#
# So the case is SPLIT, and both halves are asserted rather than the awkward one
# being dropped:
#   3a, through conformance.sh: the perturbation must make the run RED, and the
#       report must say the implementation REFUSED a request the oracle ACCEPTED.
#   3b, in CASE 8 below: `ledger-wrong-truncating` produces legs that do not
#       balance, and THAT reaches `INVARIANT double_entry_balances VIOLATED`.
# Recording this rather than quietly rewriting the case is the point: a red drive
# that is edited until it passes has measured the edit, not the guard.
# ---------------------------------------------------------------------------
F1="$VEC/LDG-01-manual-je-3leg-minor-units.json"
# BOTH occurrences of the leg's major text are moved -- request AND expect --
# because this schema refuses a vector whose two transcriptions of the same
# oracle characters disagree.
if perturb "$F1" 's/"amount_major_text": "125000.620000"/"amount_major_text": "125000.610000"/g' '"amount_major_text": "125000.610000"'; then
  expect_red "CASE 3a — one credit leg moved by ONE MINOR UNIT must make the run RED, with the port REFUSING an entry the oracle accepted" \
    "the implementation REFUSED a request the oracle ACCEPTED (HTTP 403 error.msg.glJournalEntry.invalid.mismatch.debits.credits)"
  restore "$F1"
fi

# ---------------------------------------------------------------------------
# CASE 4 — I-2 SPLITS SUM TO WHOLE, INDEPENDENTLY OF I-1.
# The requested transaction amount is moved by one minor unit. Every leg still
# balances against every other leg, so I-1 STAYS GREEN; only I-2 goes red. This
# is the case that proves I-2 is not a restatement of I-1 on this corpus.
# ---------------------------------------------------------------------------
if perturb "$F" 's/"transaction_amount_major_text": "300000"/"transaction_amount_major_text": "300001"/' '"transaction_amount_major_text": "300001"'; then
  expect_red "CASE 4 — I-2 ALONE: the requested total moved by one minor unit must make splits_sum_to_whole VIOLATED while double_entry_balances still HOLDS" \
    "INVARIANT splits_sum_to_whole VIOLATED"
  restore "$F"
fi

# ---------------------------------------------------------------------------
# CASE 5 — THE EXEMPTION DEFAULT-DENY. The ledger schema admits no exemption;
# declaring one must be INADMISSIBLE, not silently accepted.
# ---------------------------------------------------------------------------
if perturb "$F1" 's/"invariant_exemptions": \[\]/"invariant_exemptions": [{"invariant": "double_entry_balances", "reason": "RED-DRIVE PROBE, reverted immediately"}]/' \
    'RED-DRIVE PROBE'; then
  expect_red "CASE 5 — a declared invariant_exemptions entry must be INADMISSIBLE in the ledger schema (no grounding classifier exists for it)" \
    "THIS SCHEMA ADMITS NONE"
  restore "$F1"
fi

# ---------------------------------------------------------------------------
# CASE 6 — THE CENSUS PIN, INFLATION ARM. A seventh ledger vector must move
# EXEMPTION_PIN_LEDGER_PARITY and be refused by the gate.
# ---------------------------------------------------------------------------
cp "$VEC/LDG-04-header-account-accepted.json" "$TMP/extra.json"
LC_ALL=C sed 's/LDG-04-header-account-accepted/LDG-99-PIN-INFLATION-PROBE/' "$TMP/extra.json" \
  > "$VEC/LDG-99-PIN-INFLATION-PROBE.json"
if LC_ALL=C grep -qaF 'LDG-99-PIN-INFLATION-PROBE' "$VEC/LDG-99-PIN-INFLATION-PROBE.json"; then
  expect_red "CASE 6 — INFLATION: a seventh ledger vector must fail the pinned ledger parity count" \
    "exemption census MISMATCH: LEDGER parity vectors        = 5, but this file pins 4"
else
  say "SETUP FAIL could not plant the inflation probe"
  fail=$((fail+1))
fi
rm -f "$VEC/LDG-99-PIN-INFLATION-PROBE.json"

# ---------------------------------------------------------------------------
# CASE 7 — THE CENSUS PIN, DEFLATION ARM. This is the half nobody notices: with
# every ledger vector removed the loanschedule half is still green, the report
# prints its empty-store banner, and the verdict WOULD be PASS. The pin is what
# refuses it.
# ---------------------------------------------------------------------------
mkdir -p "$TMP/ledger-aside"
mv "$VEC"/*.json "$TMP/ledger-aside/"
if [ -z "$(ls -A "$VEC" 2>/dev/null)" ]; then
  expect_red "CASE 7 — DEFLATION: with EVERY ledger vector deleted the run must REFUSE, not pass over a corpus that vanished" \
    "the exemption census gate could not find the LEDGER-parity-PASS figure"
else
  say "SETUP FAIL could not empty the ledger vector directory"
  fail=$((fail+1))
fi
mv "$TMP/ledger-aside"/*.json "$VEC/"

# ---------------------------------------------------------------------------
# CASE 8 — THE NAMED WRONG IMPLEMENTATIONS. DEC-2 precondition P-10: a
# graded_against row is a DECLARATIVE record and executes nothing, so each named
# implementation is RUN here and shown going red. This is the bottom-left cell of
# §5.2 requirement 7's matrix, and it is the cell P-10 was added because nothing
# was executing.
# ---------------------------------------------------------------------------
BIN="$TMP/conf"
( cd "$ROOT/nexus" && \
  GOROOT=/Users/buv/gerege-nbfi/.softhouse/toolchain/go \
  GOPATH=/Users/buv/gerege-nbfi/.softhouse/toolchain/gopath \
  GOCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gocache \
  GOMODCACHE=/Users/buv/gerege-nbfi/.softhouse/toolchain/gomodcache \
  /Users/buv/gerege-nbfi/.softhouse/toolchain/go/bin/go build -o "$BIN" \
    ./internal/apps/loanschedule/conformance/cmd/conformance ) || { say "could not build"; exit 2; }

wrong_case() { # wrong_case <impl> <needle>
  local impl="$1" needle="$2" out rc
  out="$("$BIN" -oracle-probe=up -ledger-impl="$impl" 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ] && printf '%s' "$out" | LC_ALL=C grep -qaF -- "$needle"; then
    say "RED  OK    exit $rc   CASE 8/$impl"
    printf '%s' "$out" | LC_ALL=C grep -aF -- "$needle" | head -2 | sed 's/^/           | /'
    pass=$((pass+1))
  else
    say "RED  FAIL  exit $rc   CASE 8/$impl — the output had to contain: $needle"
    printf '%s' "$out" | LC_ALL=C grep -a 'ledger parity' | sed 's/^/           | /'
    fail=$((fail+1))
  fi
  say ""
}

# The needle names LDG-01's first leg, because the ledger report is ordered by
# case_id and LDG-01 is first. 10000025 -> 10000000 is the 25 minor units a
# truncating port loses -- the exact discrimination a whole-tugrik corpus could
# not make.
wrong_case ledger-wrong-truncating \
  "legs[0].amount_minor: MONEY want 10000025, got 10000000 (margin -25 minor units)"
# CASE 3b. The same implementation, a different assertion: its truncated legs do
# not balance, so this is where I-1's VIOLATED branch is actually reached.
wrong_case ledger-wrong-truncating \
  "INVARIANT double_entry_balances VIOLATED: ledger: double entry does not balance: debits 30000000, credits 29999900 (minor units)"
wrong_case ledger-wrong-header-refusing \
  "the implementation REFUSED a request the oracle ACCEPTED"
wrong_case ledger-wrong-manual-permission-ignored \
  "expected an ORACLE REFUSAL and the implementation returned a posted entry instead"
wrong_case ledger-wrong-netting-totals \
  "total_debits_minor: MONEY want 12500062, got 0"
wrong_case ledger-wrong-code-ignored \
  'legs[0].gl_account_code: want "10300", got ""'
wrong_case ledger-wrong-split-drift \
  "INVARIANT splits_sum_to_whole VIOLATED"

# ---------------------------------------------------------------------------
# THE REVERT IS VERIFIED, not assumed. A red drive that leaves the store
# perturbed is a red drive that has quietly promoted a wrong vector.
# ---------------------------------------------------------------------------
END_DIGEST="$(digest_store)"
say "======================================================================="
say "ledger vector-set digest after:  $END_DIGEST"
if [ "$BASE_DIGEST" = "$END_DIGEST" ]; then
  say "REVERT OK  — the ledger vector set is byte-identical to where it started."
  pass=$((pass+1))
else
  say "REVERT FAIL — THE STORE WAS LEFT PERTURBED. Do not commit."
  fail=$((fail+1))
fi

expect_green "control: the pristine committed store, AFTER every drive"

say "======================================================================="
say "A2-15 RED/GREEN: $pass passed, $fail failed"
say "======================================================================="
rm -rf "$TMP"
[ "$fail" -eq 0 ] || exit 1
exit 0
