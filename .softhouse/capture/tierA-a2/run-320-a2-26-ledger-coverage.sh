#!/bin/sh
# A2-26 / group C -- CLOSE THE LEDGER COVERAGE GAP THE CENSUS MEASURED.
#
# WHAT THE CENSUS FOUND (census-a2-26.py, committed alongside):
#   * 9 journal-entry observations exist, over 7 DISTINCT transactions.
#   * EVERY ONE of them has EXACTLY TWO legs. The corpus contains no journal entry with
#     three or more legs anywhere, so "splits sum to the whole" -- one of the property
#     invariants /softhouse-uat asserts -- is graded by NOTHING.
#   * Every A2 loan product carries interestRatePerPeriod 0 and no charge, so
#     INTEREST_ON_LOANS (gl 8), INCOME_FROM_FEES (gl 9) and INCOME_FROM_PENALTIES (gl 10)
#     have NEVER received a journal entry, on any product, in the whole corpus. Coverage
#     is what a corpus can DISTINGUISH; on those three slots it can distinguish nothing.
#
# THE INSTRUMENT. A new CASH product whose every mapped slot is an account the reference
# oracle still accepts today -- G-10 option (c), and PROVEN by A2-315 rather than
# inferred: gl 2 (retyped ASSET->INCOME) appears nowhere in it. It differs from
# req/a2-7-prod-210-cash-nine-mandatory.json only in carrying a non-zero interest rate,
# a goodwill slot, and a name. A loan on it carries two charges that already exist on
# this oracle -- charge 1 (flat MNT 15,000 at disbursement) and charge 6 (PENALTY, flat
# MNT 7,500 on a specified due date) -- so a single repayment must be split by the
# transaction processor across penalty, fee, interest and principal.
#
# This measures. No expected answer is written down anywhere in this script, and a
# refusal is recorded exactly as a success is: if the oracle declines any step, that
# refusal is the observation and the batch stops there rather than fabricating a
# continuation.
#
# LIMITATION, carried forward from run-220-a2-7-runtime-v8.sh and still true: cap8.sh
# sends no `Idempotency-Key`. Group E (run-340) probes what the oracle does with one.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
C="$DIR/cap8.sh"

sh "$C" A2-330-prod-coverage POST /loanproducts req/a2-26-prod-coverage.json || exit 1
cat "$DIR/out/A2-330-prod-coverage.json"; echo

python3 "$DIR/resolve8.py" "$DIR/req/a2-26-loan-coverage.json" \
        "$DIR/out/A2-330-prod-coverage.json" resourceId \
        "$DIR/req/a2-26-loan-coverage-resolved.json" || exit 1

sh "$C" A2-331-prod-coverage-readback GET "/loanproducts/$(python3 -c 'import json,sys,decimal;print(json.load(open(sys.argv[1]),parse_float=decimal.Decimal)["resourceId"])' "$DIR/out/A2-330-prod-coverage.json")" || exit 1

sh "$C" A2-332-loan-coverage POST /loans req/a2-26-loan-coverage-resolved.json || exit 1
cat "$DIR/out/A2-332-loan-coverage.json"; echo

LID=$(python3 -c 'import json,sys,decimal;print(json.load(open(sys.argv[1]),parse_float=decimal.Decimal).get("loanId",""))' \
      "$DIR/out/A2-332-loan-coverage.json")
echo "observed loanId = ${LID:-<none>}"
[ -n "$LID" ] || { echo "no loan was created -- the coverage leg cannot run" >&2; exit 1; }

sh "$C" A2-333-approve-coverage  POST "/loans/$LID?command=approve"  req/a2-26-approve.json  || exit 1
sh "$C" A2-334-disburse-coverage POST "/loans/$LID?command=disburse" req/a2-26-disburse.json || exit 1
sh "$C" A2-335-je-after-disburse-coverage GET "/journalentries?loanId=$LID&limit=80" || exit 1

# The loan's own schedule at this point -- the money the split below must be a split OF.
sh "$C" A2-336-loan-state-after-disburse GET "/loans/$LID?associations=all" || exit 1

# THE PROBE: one repayment large enough to reach penalty, fee, interest and principal.
sh "$C" A2-337-repayment-split POST "/loans/$LID/transactions?command=repayment" \
   req/a2-26-repayment-split.json || exit 1
cat "$DIR/out/A2-337-repayment-split.json"; echo

sh "$C" A2-338-je-after-repayment-coverage GET "/journalentries?loanId=$LID&limit=80" || exit 1
sh "$C" A2-339-loan-state-after-repayment GET "/loans/$LID?associations=all" || exit 1
