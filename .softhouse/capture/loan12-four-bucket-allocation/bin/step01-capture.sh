#!/usr/bin/env bash
# STEP 1 — capture the four-bucket repayment allocation on loan 12 (OHLGT-L03).
#
# The single write is a repayment of 97978.65 MNT (9797865 minor) dated
# 2026-09-02, the oracle business date. It is sized to consume the loan's ENTIRE
# penalty (57.00), fee (100.00) and interest (6618.53) buckets and 91203.12 of
# the 100000.00 principal, leaving principal 8796.88 outstanding. Under the
# product's mifos-standard-strategy the processor walks instalments and, within
# each, pays penalty -> fee -> interest -> principal; because the amount fully
# consumes every penalty, fee and interest cell, the transaction's four portions
# equal the greedy allocation of the loan-level four-bucket pool. Every numeric
# token in the request body is a JSON string, so the body is byte-stable.
source "$(dirname "$0")/common.sh"

LOAN=12

# --- BEFORE: the four-bucket pool the allocation starts from -----------------
api_get "/loans/$LOAN?associations=repaymentSchedule,transactions" > "$OUT/loan-$LOAN-before-raw.json"

# --- THE ONE WRITE: the repayment -------------------------------------------
REQBODY="$REQ/repay-OHALLOCG-97978.65.json"
HTTP=$(curl -sk -m 30 -o "$OUT/repay-OHALLOCG-97978.65-raw.json" -w '%{http_code}' \
  -X POST "$BASE/loans/$LOAN/transactions?command=repayment" \
  -H "$AUTH" -H "$TEN" -H "$CT" --data-binary @"$REQBODY")
printf '%s\n' "$HTTP" > "$OUT/repay-OHALLOCG-97978.65-http-status.txt"
echo "POST /loans/$LOAN/transactions?command=repayment -> HTTP $HTTP"
cat "$OUT/repay-OHALLOCG-97978.65-raw.json"; echo

# If the oracle refused, the refusal IS the result: stop here and keep the body.
case "$HTTP" in
  2??) ;;
  *) echo "REFUSED: oracle returned HTTP $HTTP — capture recorded, no further writes"; exit 0 ;;
esac

# --- AFTER: the loan, its transactions and its journal entries --------------
api_get "/loans/$LOAN?associations=repaymentSchedule,transactions" > "$OUT/loan-$LOAN-after-raw.json"
api_get "/loans/$LOAN/transactions" > "$OUT/loan-$LOAN-transactions-after-raw.json"
api_get "/journalentries?loanId=$LOAN" > "$OUT/journalentries-loan-$LOAN-after-raw.json"

echo "--- loan $LOAN summary AFTER ---"
python3 "$CAP/bin/summary.py" "$OUT/loan-$LOAN-after-raw.json"
