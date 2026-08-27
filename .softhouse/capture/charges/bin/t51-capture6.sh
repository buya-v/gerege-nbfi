#!/bin/sh
# T51 pass 6 -- the SAME-PRODUCT control for pass 5.
#
# Pass 5 showed products 20 and 21 (both allow_full_term_for_tranche = t, differing only in
# interest_recognition_on_disbursement_date) give byte-identical schedules.  That proves
# nothing unless the full-term-tranche arm was actually ENTERED.  addDisbursement's guard is
# `scheduleModel.loanProductRelatedDetail().isAllowFullTermForTranche()` [:141], and
# allowFullTermForTranche is request-overridable [LoanScheduleValidator.java:79,
# LoanScheduleAssembler.java:543-546], so turning it OFF in the request on the SAME product
# is a confound-free control: only that one guard changes.
#
# ADDITIVE ONLY.  Creates nothing.
set -eu
. "$(dirname "$0")/lib.sh"
O=$CH/out/t51
R=$CH/req
mkdir -p "$O"

echo "== T51 capture pass 6 (same-product allowFullTermForTranche control) =="
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass6.txt" > /dev/null || {
  echo "ABORT: preconditions breached." >&2; exit 1; }
grep -q '^ALL PRECONDITIONS HOLD' "$O/preconditions-pass6.txt" || {
  echo "ABORT: no PASS line." >&2; exit 1; }
echo "preconditions: ALL PASS (PASS line present)"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-before-pass6.txt"
echo "BEFORE  m_charge|m_loan|m_product_loan = $(cat "$O/state-before-pass6.txt")"

for n in 4 5; do
  sed 's/"maxOutstandingLoanBalance": 5000000,/"maxOutstandingLoanBalance": 5000000,\
 "allowFullTermForTranche": false,/' \
    "$R/calc-T51-FTTP-P$n.json" > "$R/calc-T51-FTTPOFF-P$n.json"
  grep -q '"allowFullTermForTranche": false,' "$R/calc-T51-FTTPOFF-P$n.json" \
    || { echo "ABORT: the control payload does not carry the override" >&2; exit 1; }
  echo "  wrote calc-T51-FTTPOFF-P$n.json"
done

for n in FTTPOFF-P4 FTTPOFF-P5; do
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$R/calc-T51-$n.json" -o "$O/T51-$n-raw.json" -w '%{http_code}')
  echo "  T51-$n  HTTP $code"
  echo "T51-$n $code" >> "$O/HTTP-CODES.txt"
done

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-after-pass6.txt"
echo "AFTER   m_charge|m_loan|m_product_loan = $(cat "$O/state-after-pass6.txt")"
[ "$(cat "$O/state-before-pass6.txt")" = "$(cat "$O/state-after-pass6.txt")" ] \
  || { echo "BREACH: pass 6 changed server state" >&2; exit 1; }
echo "  pass 6 created nothing: before == after"
echo
shasum -a 256 "$O"/T51-FTTP-P4-raw.json "$O"/T51-FTTP-P5-raw.json \
              "$O"/T51-FTTPOFF-P4-raw.json "$O"/T51-FTTPOFF-P5-raw.json
