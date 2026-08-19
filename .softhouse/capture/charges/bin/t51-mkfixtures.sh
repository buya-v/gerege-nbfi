#!/bin/sh
# T51 -- build the request fixtures for the two TO_BE_CAPTURED items that each need one
# additive product.  Contacts no oracle; writes files only.
#
# ITEM 1 -- is T48-N1's aliasing behaviourally reachable?
#   LoanApplicationTerms.toLoanConfigurationDetails() [LoanApplicationTerms.java:1747-1756]
#   passes `isInterestChargedFromDateSameAsDisbursalDateEnabled` (a GLOBAL configuration
#   value, LoanScheduleAssembler.java:370-371) into the 16th constructor slot, which
#   LoanConfigurationDetails.java:67-76 names `interestRecognitionOnDisbursementDate` and
#   :92 assigns to the field its :201-203 getter returns.  The product/request field of the
#   same name never reaches that slot.  Needs a product with the flag TRUE plus a matched
#   comparator with it FALSE.
#
# ITEM 2 -- chargeCalculationType 5 (PERCENT_OF_DISBURSEMENT_AMOUNT).  Needs a
#   multi-disbursement (tranche) product.
#
# METHOD: product payloads are derived from the COMMITTED payloads by TEXT substitution on
# named lines only (T36's method), so every numeric literal stays byte-identical and no
# money value is ever round-tripped through a parser.  Calc requests are authored as text.
set -eu
D=$(cd "$(dirname "$0")" && pwd)
CH=$(cd "$D/.." && pwd)
W=$(cd "$CH/../../.." && pwd)
P=$W/.softhouse/capture/pathb/req
R=$CH/req
mkdir -p "$R"

echo "== T51 fixtures =="

# --------------------------------------------------------------- ITEM 1 products
# Base: product-3 (PROGRESSIVE, MNT, daysInYearType 1 = ACTUAL, daysInMonthType 1 = ACTUAL,
# interestCalculationPeriodType 0 = DAILY).  The ACT/ACT + DAILY combination is what makes
# ProgressiveEMICalculator's cross-year partial-period arm reachable at all
# [ProgressiveEMICalculator.java:1505-1507, :1526-1531]; a SAME_AS_REPAYMENT_PERIOD product
# returns earlier at :1516-1524 and never reaches it.
# The daysInYearCustomStrategy line is REPLACED (not deleted) by the flag, so the line count
# and every other byte are untouched.
sed -e 's/"name": "PathB DIYCS FULL_LEAP_YEAR",/"name": "T51 IROD true",/' \
    -e 's/"shortName": "PB3",/"shortName": "T5A",/' \
    -e 's/"daysInYearCustomStrategy": "FULL_LEAP_YEAR"/"interestRecognitionOnDisbursementDate": true/' \
    "$P/product-3-diycs-fullleapyear.json" > "$R/prod-T51-P1-irod-true.json"

sed -e 's/"name": "PathB DIYCS FULL_LEAP_YEAR",/"name": "T51 IROD false",/' \
    -e 's/"shortName": "PB3",/"shortName": "T5B",/' \
    -e 's/"daysInYearCustomStrategy": "FULL_LEAP_YEAR"/"interestRecognitionOnDisbursementDate": false/' \
    "$P/product-3-diycs-fullleapyear.json" > "$R/prod-T51-P2-irod-false.json"

# --------------------------------------------------------------- ITEM 2 product
# Base: product-1-baseline (the product every T40/T46/T48 charge capture used), changed ONLY
# in the multi-disbursement fields, so it is a matched comparator for product 1 by
# construction.
sed -e 's/"name": "PathB Progressive MNT",/"name": "T51 tranche multidisburse",/' \
    -e 's/"shortName": "PBM1",/"shortName": "T5C",/' \
    -e 's/"multiDisburseLoan": false,/"multiDisburseLoan": true,\n "maxTrancheCount": 3,\n "outstandingLoanBalance": 5000000,/' \
    "$P/product-1-baseline.json" > "$R/prod-T51-P3-tranche.json"

echo "-- product payload drift (changed lines vs the committed base) --"
printf '  P1 vs product-3 : '
diff "$P/product-3-diycs-fullleapyear.json" "$R/prod-T51-P1-irod-true.json" | grep -c '^[<>]' || true
printf '  P2 vs product-3 : '
diff "$P/product-3-diycs-fullleapyear.json" "$R/prod-T51-P2-irod-false.json" | grep -c '^[<>]' || true
printf '  P3 vs product-1 : '
diff "$P/product-1-baseline.json" "$R/prod-T51-P3-tranche.json" | grep -c '^[<>]' || true
echo "-- P1 vs P2: the ONLY difference must be name, shortName and the flag --"
diff "$R/prod-T51-P1-irod-true.json" "$R/prod-T51-P2-irod-false.json" || true

# --------------------------------------------------------------- ITEM 1 calc requests
# Written as TEMPLATEs carrying "productId": 0; the capture script substitutes the id the
# oracle assigns and REFUSES to post a payload that still contains the placeholder.
mkcalc() {                       # mkcalc <name> <body-file-content-on-stdin>
  cat > "$R/calc-T51-$1-TEMPLATE.json"
  echo "  wrote calc-T51-$1-TEMPLATE.json"
}

# AA1 -- byte-verbatim from the committed calc-T48B-AA1-p7.json shape (2024-11-01, 6 monthly
# periods, 1,200,000 at 21.6%).  Period 2 runs 01 Dec 2024 -> 01 Jan 2025 and is the crossing
# period.  T48 captured this shape on product 7 (irod = f) and observed
# totalInterestCharged 76160.63; T48's Path A2 twin with the flag actually bound observed
# 76158.97.  So this shape is known to SEPARATE when the flag reaches the slot.
mkcalc IROD-AA1 <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 November 2024",
 "submittedOnDate": "01 November 2024",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# DEC15 -- disbursed 15 Dec 2024 (LEAP year, 366 days).  Period 1 crosses with a NON-ZERO
# first segment: 16 days in 2024 under the 31-Dec boundary, 17 under the 1-Jan boundary.
mkcalc IROD-DEC15 <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "15 December 2024",
 "submittedOnDate": "15 December 2024",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# DEC31 -- disbursed 31 Dec 2024.  The first segment is ZERO days under the 31-Dec boundary
# and ONE day (31 Dec -> 1 Jan, over 366) under the 1-Jan boundary.  This is the sharpest
# separator the boundary rule admits.
mkcalc IROD-DEC31 <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "31 December 2024",
 "submittedOnDate": "31 December 2024",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# R13 -- repaymentEvery 13 months, 2 periods from 15 Dec 2023.  Each period spans THREE year
# segments, so calculatePeriodFractions' while loop [:1554-1568] calls
# getFractionPeriodDueDateForEndOfYear TWICE per period.  If the boundary moves, it moves
# four times in one schedule.
mkcalc IROD-R13 <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 26,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 2,
 "repaymentEvery": 13,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "15 December 2023",
 "submittedOnDate": "15 December 2023",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# NOCROSS -- CONTROL.  No period crosses a year boundary, so partialPeriodCalculationNeeded
# [:1505-1507] is false everywhere and calculatePeriodFractions is never entered.  The two
# products MUST agree here whatever the answer to item 1 is; a difference would mean the two
# products differ in something other than the flag and would invalidate the whole item.
mkcalc IROD-NOCROSS <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 February 2025",
 "submittedOnDate": "01 February 2025",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# D365 -- the AA1 shape with daysInYearType forced to 365 in the request.  The first conjunct
# of partialPeriodCalculationNeeded is then false, so the arm cannot fire.  Diffing D365
# against AA1 on the SAME product proves the arm is reachable on this shape and that the
# corpus can SEE it -- without which "the two products agree" would prove nothing.
mkcalc IROD-D365 <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "daysInYearType": 365,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 November 2024",
 "submittedOnDate": "01 November 2024",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# REQTRUE / REQFALSE -- the REQUEST-level override.  LoanScheduleAssembler.java:537-541 lets
# the calculateLoanSchedule payload override the product's interestRecognitionOnDisbursement
# Date, and LoanScheduleValidator.java:78 lists it as a supported parameter.  These two legs
# ask whether the override reaches the slot when the product setting does not.
mkcalc IROD-AA1-REQTRUE <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "interestRecognitionOnDisbursementDate": true,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 November 2024",
 "submittedOnDate": "01 November 2024",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

mkcalc IROD-AA1-REQFALSE <<'EOF'
{
 "clientId": 2,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 6,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 6,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 0,
 "interestRecognitionOnDisbursementDate": false,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 November 2024",
 "submittedOnDate": "01 November 2024",
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# --------------------------------------------------------------- ITEM 2 calc requests
# All on the tranche product (productId placeholder 0) or on product 1 (the matched
# single-disbursement comparator, id fixed at 1 because it is a committed fixture).
# chargeId placeholders are 0 too and are filled the same way.

mkcalc TR-00-ctrl <<'EOF'
{
 "clientId": 1,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 January 2026", "principal": 500000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 400000 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

mkcalc TR-01-c5-tranche <<'EOF'
{
 "clientId": 1,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 January 2026", "principal": 500000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 400000 } ],
 "charges": [
  { "chargeId": 0, "amount": 1.2345 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# The comparator that decides the question.  chargeCalculationType 2 = PERCENT_OF_AMOUNT is
# a percentage of the LOAN principal; 5 = PERCENT_OF_DISBURSEMENT_AMOUNT should be a
# percentage of EACH DISBURSEMENT.  On uneven tranches the two readings cannot coincide --
# unless type 5 is implemented as type 2, which is exactly what T48 could not rule out.
mkcalc TR-02-c2-comparator <<'EOF'
{
 "clientId": 1,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 January 2026", "principal": 500000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 400000 } ],
 "charges": [
  { "chargeId": 3, "amount": 1.2345 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# FLAT at chargeTimeType 12.  validValuesForTrancheDisbursement() is exactly {FLAT (1),
# PERCENT_OF_DISBURSEMENT_AMOUNT (5)} [ChargeCalculationType.java:82-84], so this is the
# other admissible tranche charge and separates "per tranche" from "once".
mkcalc TR-03-c1flat-tranche <<'EOF'
{
 "clientId": 1,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 January 2026", "principal": 500000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 400000 } ],
 "charges": [
  { "chargeId": 0, "amount": 7000 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# ONE tranche only, on the SAME tranche product: isolates "the product is multi-disburse"
# from "the request actually has several tranches".
mkcalc TR-04-c5-onetranche <<'EOF'
{
 "clientId": 1,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 January 2026", "principal": 1200000 } ],
 "charges": [
  { "chargeId": 0, "amount": 1.2345 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# The tranche product with NO disbursementData at all -- the fallback path.
mkcalc TR-05-c5-nodisbdata <<'EOF'
{
 "clientId": 1,
 "productId": 0,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": 12,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": 12,
 "repaymentEvery": 1,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "charges": [
  { "chargeId": 0, "amount": 1.2345 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

# The SAME three-tranche shape on product 1 (single-disbursement).  Product 1 differs from
# the tranche product ONLY in the multi-disbursement fields, by construction above.
mkcalc TR-06-c5-on-singledisb-product <<'EOF'
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
 "interestRatePerPeriod": 21.6,
 "interestRateFrequencyType": 3,
 "amortizationType": 1,
 "interestType": 0,
 "interestCalculationPeriodType": 1,
 "transactionProcessingStrategyCode": "advanced-payment-allocation-strategy",
 "expectedDisbursementDate": "01 January 2026",
 "submittedOnDate": "01 January 2026",
 "maxOutstandingLoanBalance": 5000000,
 "disbursementData": [
  { "expectedDisbursementDate": "01 January 2026", "principal": 500000 },
  { "expectedDisbursementDate": "01 March 2026", "principal": 300000 },
  { "expectedDisbursementDate": "01 June 2026", "principal": 400000 } ],
 "charges": [
  { "chargeId": 0, "amount": 1.2345 } ],
 "locale": "en",
 "dateFormat": "dd MMMM yyyy"
}
EOF

echo
echo "fixtures written to $R"
ls "$R" | grep '^calc-T51-' | sed 's/^/  /'
ls "$R" | grep '^prod-T51-' | sed 's/^/  /'
