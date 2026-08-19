#!/bin/sh
# T48 -- PATH B corroboration of the ACTUAL/ACTUAL cross-year partial-period arm and of
# FEB_29_PERIOD_ONLY's two effects, on the PRODUCTION WIRING.
#
# WHY THIS LEG EXISTS.  Path A drops daysInYearCustomStrategy entirely
# [LoanApplicationTerms.java:304-351 never copies :380 into :291], so the strategy can only
# be exercised in-process through the Path A2 EMICalculator seam -- a seam Fineract's own
# unit tests use, but NOT the one the server uses end to end.  Path B is the production
# wiring: LoanScheduleAssembler.java:753 / LoanScheduleGeneratorServiceImpl.java:44 do
# `mc = MoneyHelper.getMathContext()` and pass THAT SAME OBJECT to generate(mc, ...), so on
# Path B the ambient context IS the threaded context.  Corroborating the A2 numbers here is
# what makes the finding a statement about the oracle rather than about a test seam.
#
# ADDITIVE ONLY.  Creates NO product and NO charge.  It reuses the products T22/T36 already
# left on `gerege`, read straight out of PostgreSQL and asserted before use:
#     id 7  ACT/ACT, DAILY, daysInYearCustomStrategy UNSET
#     id 3  ACT/ACT, DAILY, daysInYearCustomStrategy FULL_LEAP_YEAR
#     id 4  ACT/ACT, DAILY, daysInYearCustomStrategy FEB_29_PERIOD_ONLY
# Only POST /loans?command=calculateLoanSchedule is used; it persists nothing.  Nothing is
# restarted, re-tenanted, dropped or written.  PostgreSQL is the only engine.
set -eu

W="$(cd "$(dirname "$0")/../../../.." && pwd)"
AA=$W/.softhouse/capture/actualactual
CH=$W/.softhouse/capture/charges
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

O=$AA/pathb/out
R=$AA/pathb/req
mkdir -p "$O" "$R"

echo "== T48 Path B ACT/ACT corroboration, tenant gerege =="

sh "$CH/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached -- nothing captured." >&2; exit 1; }
echo "preconditions: ALL PASS"

# --- assert the three products are exactly what this leg assumes -------------------------
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select id,name,days_in_year_enum,days_in_month_enum,interest_calculated_in_period_enum,coalesce(days_in_year_custom_strategy,'UNSET'),interest_recognition_on_disbursement_date from m_product_loan where id in (3,4,7) order by id;" \
  > "$O/products-asserted.txt"
cat "$O/products-asserted.txt"
grep -q '^7|.*|1|1|0|UNSET|f$'          "$O/products-asserted.txt" || { echo "ABORT: product 7 is not ACT/ACT DAILY strategy-UNSET" >&2; exit 1; }
grep -q '^3|.*|1|1|0|FULL_LEAP_YEAR|f$' "$O/products-asserted.txt" || { echo "ABORT: product 3 is not ACT/ACT DAILY FULL_LEAP_YEAR" >&2; exit 1; }
grep -q '^4|.*|1|1|0|FEB_29_PERIOD_ONLY|f$' "$O/products-asserted.txt" || { echo "ABORT: product 4 is not ACT/ACT DAILY FEB_29_PERIOD_ONLY" >&2; exit 1; }
echo "  ok  products 7 / 3 / 4 are UNSET / FULL_LEAP_YEAR / FEB_29_PERIOD_ONLY on ACT/ACT DAILY"

LOANS_BEFORE=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_loan;")
[ "$LOANS_BEFORE" = "0" ] || { echo "ABORT: m_loan is $LOANS_BEFORE, expected 0" >&2; exit 1; }

# --- author the requests as TEXT.  No float touches an amount. ---------------------------
# clientId 2 = "Path B Leap Fixture", activation date 2023-01-01 [m_client, read-only SELECT].
# Client 1 activates 2026-01-01 and the oracle rejects any earlier submittedOnDate with
# HTTP 403 error.msg.loan.submittal.cannot.be.before.client.activation.date -- observed, and
# the reason every request below uses client 2.  B-03/B-04 used client 2 for the same reason.
mkreq() {
  _name=$1; _prod=$2; _disb=$3; _n=$4; _every=$5; _termfreq=$6; _principal=$7; _rate=$8
  cat > "$R/calc-$_name.json" <<EOF
{
 "clientId": 2,
 "productId": $_prod,
 "loanType": "individual",
 "principal": $_principal,
 "loanTermFrequency": $_termfreq,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": $_n,
 "repaymentEvery": $_every,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": $_rate,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "$_disb",
 "submittedOnDate": "$_disb",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF
}

# EFFECT (b) IN PURE ISOLATION -- both periods start in non-leap 2023, so effect (a) (the
# 366 -> 365 substitution, which needs the FROM-DATE's year to be leap) is a provable no-op;
# period 2 crosses the year boundary and contains no 29 February, so only the third conjunct
# of partialPeriodCalculationNeeded [ProgressiveEMICalculator.java:1507] can move anything.
for p in 7 3 4; do
  mkreq "T48B-PUREB-p$p" "$p" "01 November 2023" 2 1 2 1200000 21.6
done
# the one-year shape: 12 monthly from 2023-12-01
for p in 7 3 4; do
  mkreq "T48B-YEAR-p$p" "$p" "01 December 2023" 12 1 12 1200000 21.6
done
# the quarterly shape whose second period crosses the boundary AND contains 29 Feb 2024
for p in 7 3 4; do
  mkreq "T48B-QTR-p$p" "$p" "01 September 2023" 4 3 12 10000000 12.0
done
# the arm with NO strategy at all, leap -> non-leap, six monthly from 2024-11-01
mkreq "T48B-AA1-p7" 7 "01 November 2024" 6 1 6 1200000 21.6
# the B-03 / B-04 shape re-issued at this pass's ids, so the new captures are anchored to
# two observations the program already holds
mkreq "T48B-B03SHAPE-p3" 3 "01 January 2024" 12 1 12 1200000 21.6
mkreq "T48B-B04SHAPE-p4" 4 "01 January 2024" 12 1 12 1200000 21.6
mkreq "T48B-B03SHAPE-p7" 7 "01 January 2024" 12 1 12 1200000 21.6

echo
echo "-- capturing --"
: > "$O/HTTP-CODES.txt"
for f in "$R"/calc-T48B-*.json; do
  n=$(basename "$f" .json); n=${n#calc-}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$O/$n-raw.json" -w '%{http_code}')
  echo "  $n  HTTP $code"
  echo "$n $code" >> "$O/HTTP-CODES.txt"
  [ "$code" = "200" ] || { echo "ABORT: $n returned HTTP $code" >&2; cat "$O/$n-raw.json" >&2; exit 1; }
done

LOANS_AFTER=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_loan;")
[ "$LOANS_AFTER" = "0" ] || { echo "BREACH: m_loan is $LOANS_AFTER after the run, expected 0" >&2; exit 1; }
PROD_AFTER=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_product_loan;")
[ "$PROD_AFTER" = "16" ] || { echo "BREACH: m_product_loan is $PROD_AFTER, expected 16 (this leg creates none)" >&2; exit 1; }
echo "  ok  no loan persisted, no product created"

echo
shasum -a 256 "$O"/T48B-*-raw.json
