#!/bin/sh
# T51 pass 3 -- ITEM 3: `fixedLength`.
#
# Pass 2 sent fixedLength on an interest-bearing request and the oracle answered HTTP 403
# "Fixed Length configuration is only allowed for zero interest products"
# [VERIFIED: LoanProductDataValidator.java:2784-2787, reached from
# LoanApplicationValidator.fixedLengthValidations :819-834].  That validator derives
# `thereIsInterest` from the REQUEST's interestRatePerPeriod [:829-830], not from the
# product -- so no new product is needed; the request carries interestRatePerPeriod 0.
# The second guard is fixedLength >= ((numberOfRepayments - 1) * repayEvery) + 1 [:2790-2796].
#
# ADDITIVE ONLY.  Creates nothing at all: calculateLoanSchedule legs only.
set -eu
. "$(dirname "$0")/lib.sh"
O=$CH/out/t51
R=$CH/req
mkdir -p "$O"

echo "== T51 capture pass 3 (fixedLength), tenant gerege =="
sh "$CH/bin/run-preconditions.sh" "$O/preconditions-pass3.txt" > /dev/null || {
  echo "ABORT: preconditions breached." >&2; exit 1; }
grep -q '^ALL PRECONDITIONS HOLD' "$O/preconditions-pass3.txt" || {
  echo "ABORT: no PASS line." >&2; exit 1; }
echo "preconditions: ALL PASS (PASS line present)"

docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-before-pass3.txt"
echo "BEFORE  m_charge|m_loan|m_product_loan = $(cat "$O/state-before-pass3.txt")"

mkzero() {   # <stem> <fixedLength-line-or-empty>
  cat > "$R/calc-T51-$1.json" <<EOF
{
 "clientId": 1,
 "productId": 1,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 0,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
$2 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF
  echo "  wrote calc-T51-$1.json"
}

echo
echo "-- pass-3 fixtures (zero-interest requests) --"
mkzero FL0-CTRL     ""
mkzero FL0-11       ' "fixedLength": 11,'
mkzero FL0-12       ' "fixedLength": 12,'
mkzero FL0-18       ' "fixedLength": 18,'
mkzero FL0-365      ' "fixedLength": 365,'
# The interest-bearing rejection, re-issued so this pass owns the 403 as its own observation.
mkzero FL-INTEREST-REJECT ' "fixedLength": 18,'
sed -i '' 's/"interestRatePerPeriod": 0,/"interestRatePerPeriod": 21.6,/' "$R/calc-T51-FL-INTEREST-REJECT.json"

echo
echo "-- capturing pass 3 --"
for n in FL0-CTRL FL0-11 FL0-12 FL0-18 FL0-365 FL-INTEREST-REJECT; do
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$R/calc-T51-$n.json" -o "$O/T51-$n-raw.json" -w '%{http_code}')
  echo "  T51-$n  HTTP $code"
  echo "T51-$n $code" >> "$O/HTTP-CODES.txt"
done

echo
docker exec fineract-db-1 psql -U root -d fineract_gerege -tAc \
  "select (select count(*) from m_charge), (select count(*) from m_loan), (select count(*) from m_product_loan)" \
  | tr -d '\r' > "$O/state-after-pass3.txt"
echo "AFTER   m_charge|m_loan|m_product_loan = $(cat "$O/state-after-pass3.txt")"
[ "$(cat "$O/state-before-pass3.txt")" = "$(cat "$O/state-after-pass3.txt")" ] \
  || { echo "BREACH: pass 3 changed server state; it must create nothing" >&2; exit 1; }
echo "  pass 3 created nothing: before == after"
