#!/bin/sh
# T55 -- LEAP-BOUNDARY captures for the ACTUAL/ACTUAL cross-year partial-period arm.
#
# WHY THIS EXISTS.  Finding T48-N4: the partial-period arm
# [ProgressiveEMICalculator.java:1526-1530 / :1393-1397] computes
#     f = SUM_over_years  days(segment_y) / Year.of(y).length()
# and the plain ACT/ACT branch [:1533-1535 -> rateFactorByRepaymentPeriod :1950-1963] computes
#     f = actualDaysInPeriod / daysInYear.
# When every year in play is 365 days these are ALGEBRAICALLY EQUAL, so a cross-year vector
# inside a run of non-leap years grades the arm NOT AT ALL.  This pass captures shapes where a
# 366-day year is in play, so the two readings separate -- and captures the non-leap control so
# that the trap is OBSERVED rather than merely derived.
#
# SEAM: PATH B, the production wiring.  Chosen because it is the only seam that both (a) runs the
# arithmetic the server runs and (b) HONOURS daysInYearCustomStrategy.  Path A (the embeddable
# seam) provably DROPS that setting: LoanApplicationTerms's private Builder constructor
# [VERIFIED: LoanApplicationTerms.java:304-351] never copies builder.daysInYearCustomStrategy
# [VERIFIED: declared :380, set by the setter :567-570] into the field [VERIFIED: :291], so
# toLoanConfigurationDetails() [VERIFIED: :1746-1756] passes null regardless -- observed by T48 as
# 0 of 87 cells.  On Path B, LoanScheduleAssembler.java:753 and
# LoanScheduleGeneratorServiceImpl.java:44 do `mc = MoneyHelper.getMathContext()` and pass THAT
# SAME OBJECT to generate(mc, ...), so the ambient (19, HALF_UP) IS the threaded context.
#
# ADDITIVE ONLY.  Creates NO product, NO charge, NO client, NO loan.  Reuses the products T22/T36
# already left on `gerege`, asserted out of PostgreSQL before AND after:
#     id 7  ACT/ACT, DAILY, daysInYearCustomStrategy UNSET
#     id 3  ACT/ACT, DAILY, daysInYearCustomStrategy FULL_LEAP_YEAR
#     id 4  ACT/ACT, DAILY, daysInYearCustomStrategy FEB_29_PERIOD_ONLY
# Only POST /loans?command=calculateLoanSchedule is used; it persists nothing.  Nothing is
# started, stopped, restarted, re-tenanted, dropped or written.  PostgreSQL is the only engine.
set -eu

W="$(cd "$(dirname "$0")/../../../.." && pwd)"
LB=$W/.softhouse/capture/leapboundary
ORACLE_SRC=${T55_ORACLE_SRC:-/Users/buv/fineract}
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

O=$LB/out
R=$LB/req
mkdir -p "$O" "$R"

echo "== T55 leap-boundary Path B capture, tenant gerege =="

# ---------------------------------------------------------------- 0. the pin
PIN_COMMIT=${T55_PIN_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}
got=$(git -C "$ORACLE_SRC" rev-parse HEAD)
[ "$got" = "$PIN_COMMIT" ] || { echo "BREACH: pinned checkout is at $got, expected $PIN_COMMIT" >&2; exit 1; }
pc=$(git -C "$ORACLE_SRC" status --porcelain | wc -l | tr -d ' ')
[ "$pc" = "0" ] || { echo "BREACH: pinned checkout is dirty ($pc entries)" >&2; exit 1; }
echo "  ok  pinned reference-oracle checkout $got, clean"

# ------------------------------------------- 1. T36's 21-assertion preconditions gate
sh "$W/.softhouse/capture/charges/bin/run-preconditions.sh" "$O/preconditions.txt" > /dev/null || {
  echo "ABORT: preconditions breached -- nothing captured." >&2; exit 1; }
echo "  ok  preconditions: ALL PASS (see out/preconditions.txt)"

# ------------------------------------------- 2. assert the three products
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select id,name,days_in_year_enum,days_in_month_enum,interest_calculated_in_period_enum,coalesce(days_in_year_custom_strategy,'UNSET'),interest_recognition_on_disbursement_date from m_product_loan where id in (3,4,7) order by id;" \
  > "$O/products-asserted.txt"
cat "$O/products-asserted.txt"
grep -q '^7|.*|1|1|0|UNSET|f$'              "$O/products-asserted.txt" || { echo "BREACH: product 7 is not ACT/ACT DAILY strategy-UNSET" >&2; exit 1; }
grep -q '^3|.*|1|1|0|FULL_LEAP_YEAR|f$'     "$O/products-asserted.txt" || { echo "BREACH: product 3 is not ACT/ACT DAILY FULL_LEAP_YEAR" >&2; exit 1; }
grep -q '^4|.*|1|1|0|FEB_29_PERIOD_ONLY|f$' "$O/products-asserted.txt" || { echo "BREACH: product 4 is not ACT/ACT DAILY FEB_29_PERIOD_ONLY" >&2; exit 1; }
echo "  ok  products 7 / 3 / 4 = UNSET / FULL_LEAP_YEAR / FEB_29_PERIOD_ONLY on ACT/ACT DAILY,"
echo "      interest_calculated_in_period_enum = 0 (DAILY) on all three -- required, because a"
echo "      SAME_AS_REPAYMENT_PERIOD product returns at :1516-1524 BEFORE the partial-period branch."

# The pair must differ ONLY in the day-count setting.  Assert the three products agree on every
# other schedule-feeding column, so 'differing only in the day-count setting' is not taken on trust.
docker exec fineract-db-1 psql -U root -d fineract_gerege -At \
  -c "select count(distinct (currency_code,currency_digits,coalesce(currency_multiplesof,-1),days_in_month_enum,days_in_year_enum,interest_method_enum,interest_calculated_in_period_enum,amortization_method_enum,interest_period_frequency_enum,loan_schedule_type,loan_schedule_processing_type,interest_recognition_on_disbursement_date,coalesce(installment_amount_in_multiples_of,-1),allow_partial_period_interest_calcualtion,is_equal_amortization,coalesce(enable_down_payment,false),coalesce(allow_multiple_disbursals,false),coalesce(fixed_length,-1),coalesce(allow_full_term_for_tranche,false),coalesce(principal_threshold_for_last_installment,-1),coalesce(interest_recalculation_enabled,false),repayment_start_date_type_enum)) from m_product_loan where id in (3,4,7);" \
  > "$O/products-matched.txt"
mp=$(cat "$O/products-matched.txt")
[ "$mp" = "1" ] || { echo "BREACH: products 3/4/7 differ on a schedule-feeding column other than the day-count strategy (distinct tuples: $mp)" >&2; exit 1; }
echo "  ok  products 3/4/7 agree on all 22 other schedule-feeding columns (distinct tuples = 1)"

LOANS_BEFORE=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_loan;")
PROD_BEFORE=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_product_loan;")
CLI_BEFORE=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_client;")
echo "  before: m_loan=$LOANS_BEFORE m_product_loan=$PROD_BEFORE m_client=$CLI_BEFORE"
[ "$LOANS_BEFORE" = "0" ] || { echo "BREACH: m_loan is $LOANS_BEFORE, expected 0" >&2; exit 1; }

# ------------------------------------------- 3. author the requests as TEXT
# clientId 2 = "Path B Leap Fixture", activation 2023-01-01 [m_client, read-only SELECT].
# Client 1 activates 2026-01-01 and the oracle rejects an earlier submittedOnDate with HTTP 403
# error.msg.loan.submittal.cannot.be.before.client.activation.date -- observed by T48.
# NO money value here has a decimal point: principal is the integer 1200000.  interestRatePerPeriod
# is a RATE, not money; it is written as the exact decimal text 21.6 and Fineract parses request
# numbers to BigDecimal, so no binary double is constructed on the way in.
mkreq() {
  _name=$1; _prod=$2; _disb=$3; _n=$4; _every=$5; _termfreq=$6
  cat > "$R/calc-$_name.json" <<EOF
{
 "clientId": 2,
 "productId": $_prod,
 "loanType": "individual",
 "principal": 1200000,
 "loanTermFrequency": $_termfreq,
 "loanTermFrequencyType": 2,
 "numberOfRepayments": $_n,
 "repaymentEvery": $_every,
 "repaymentFrequencyType": 2,
 "interestRatePerPeriod": 21.6,
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

# ---- the shapes.  Every one is chosen from the source-derived rule, not by search. ----------
#
# THE DIRECTION SET (same shape, three different year pairs -- the pair-of-pairs that makes
# T48-N4 an OBSERVATION):
#   LB-LEAPIN   period 2 crosses 2023-12-31: years 365 then 366.  ANCHOR -- identical shape to
#               T48's T48B-PUREB, so its numbers must reproduce a committed observation.
#   LB-LEAPOUT  period 2 crosses 2024-12-31: years 366 then 365.  NEW -- no captured PAIR in the
#               program exercises this direction (T48's AA1 was product 7 only, no twin).
#   LB-NONLEAP  period 2 crosses 2025-12-31: years 365 then 365.  CONTROL -- arm and plain branch
#               are algebraically equal, so this pair MUST come out at 0 cells.
#
# THE 15-DECEMBER SET: a 16-day first segment instead of 30, so the two readings separate by more.
# LB-DEC31: FIRST SEGMENT IS ZERO DAYS at the 31-Dec boundary, from-date year is leap.
# LB-F29CROSS: the crossing period CONTAINS 29 Feb 2024, so FEB_29_PERIOD_ONLY's third conjunct
#              [:1507] is TRUE and product 4 takes the arm too -- a predicted 0.
# LB-MULTI3:  ONE period spanning TWO 31-Dec boundaries -> calculatePeriodFractions loops THREE
#             times.  2024-06-01 -> 2026-06-01 contains NO 29 Feb (29 Feb 2024 precedes the
#             from-date), so product 4 is suppressed and the pair must separate.
# LB-MULTI3F: the same three-segment geometry but CONTAINING 29 Feb 2024 -> a predicted 0.
# LB-HALFYR:  semi-annual; period 1 crosses AND contains 29 Feb, period 2 does not cross but
#             starts inside the leap year, so effect (a) alone acts on period 2.
set -- \
  "LB-LEAPIN 01 November 2023 2 1 2" \
  "LB-LEAPOUT 01 November 2024 2 1 2" \
  "LB-NONLEAP 01 November 2025 2 1 2" \
  "LB-DEC15IN 15 December 2023 1 1 1" \
  "LB-DEC15OUT 15 December 2024 1 1 1" \
  "LB-DEC15NL 15 December 2025 1 1 1" \
  "LB-DEC31 31 December 2024 1 1 1" \
  "LB-F29CROSS 01 December 2023 1 4 4" \
  "LB-MULTI3 01 June 2024 1 24 24" \
  "LB-MULTI3F 01 June 2023 1 24 24" \
  "LB-HALFYR 01 November 2023 2 6 12"
for spec in "$@"; do
  # shellcheck disable=SC2086
  set -- $spec
  nm=$1; disb="$2 $3 $4"; n=$5; ev=$6; tf=$7
  for p in 7 3 4; do
    mkreq "$nm-p$p" "$p" "$disb" "$n" "$ev" "$tf"
  done
done

echo
echo "-- capturing --"
: > "$O/HTTP-CODES.txt"
for f in "$R"/calc-LB-*.json; do
  n=$(basename "$f" .json); n=${n#calc-}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$O/$n-raw.json" -w '%{http_code}')
  printf '  %-18s HTTP %s\n' "$n" "$code"
  printf '%s %s\n' "$n" "$code" >> "$O/HTTP-CODES.txt"
  [ "$code" = "200" ] || { echo "BREACH: $n returned HTTP $code, not 200" >&2; sed -n '1,20p' "$O/$n-raw.json" >&2; exit 1; }
done

bad=$(awk '$2!="200"' "$O/HTTP-CODES.txt" | wc -l | tr -d ' ')
[ "$bad" = "0" ] || { echo "BREACH: $bad captures are not HTTP 200" >&2; exit 1; }
for f in "$O"/LB-*-raw.json; do
  [ -s "$f" ] || { echo "BREACH: $f is empty" >&2; exit 1; }
done

# ------------------------------------------- 4. re-assert the environment is UNCHANGED
LOANS_AFTER=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_loan;")
PROD_AFTER=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_product_loan;")
CLI_AFTER=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_client;")
[ "$LOANS_AFTER" = "$LOANS_BEFORE" ] || { echo "BREACH: m_loan $LOANS_BEFORE -> $LOANS_AFTER" >&2; exit 1; }
[ "$PROD_AFTER"  = "$PROD_BEFORE"  ] || { echo "BREACH: m_product_loan $PROD_BEFORE -> $PROD_AFTER" >&2; exit 1; }
[ "$CLI_AFTER"   = "$CLI_BEFORE"   ] || { echo "BREACH: m_client $CLI_BEFORE -> $CLI_AFTER" >&2; exit 1; }
echo "  ok  ADDITIVE-ONLY held: m_loan=$LOANS_AFTER m_product_loan=$PROD_AFTER m_client=$CLI_AFTER (unchanged)"

# the containers must not have restarted mid-run -- several captures' comparability rests on it
docker inspect fineract-fineract-1 --format '{{.State.StartedAt}} {{.RestartCount}}' > "$O/container-state.txt"
docker inspect fineract-db-1       --format '{{.State.StartedAt}} {{.RestartCount}}' >> "$O/container-state.txt"
rc=$(awk '{s+=$2} END{print s+0}' "$O/container-state.txt")
[ "$rc" = "0" ] || { echo "BREACH: container RestartCount total is $rc, expected 0" >&2; exit 1; }
echo "  ok  container RestartCount total 0"

echo
shasum -a 256 "$O"/LB-*-raw.json > "$O/DIGESTS.txt"
echo "== PASS -- capture admissible.  $(ls "$O"/LB-*-raw.json | wc -l | tr -d ' ') raw responses in out/ =="
