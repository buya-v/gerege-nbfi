#!/bin/sh
# T40 — author the charge-definition request payloads as TEXT.
#
# Every payload is written verbatim here; no JSON library, no float, no round-trip.
# Money amounts (15000, 2500, 7500, 9000, 1200) are exact integers in MNT major units
# as Fineract's `amount` column expects.  The values on the PERCENT_OF_* charges are
# RATES, not money (Fineract stores them in the same `amount` column) — they are written
# as exact decimal text and parsed by Fineract into BigDecimal, exactly as the committed
# corpus already does for `interestRatePerPeriod: 21.6`.
#
# chargeAppliesTo 1 = LOAN            [ChargeAppliesTo.java]
# chargeTimeType  1 = DISBURSEMENT, 2 = SPECIFIED_DUE_DATE, 8 = INSTALMENT_FEE
#                                     [ChargeTimeType.java:26,27,34]
# chargeCalculationType 1 = FLAT, 2 = PERCENT_OF_AMOUNT,
#                       3 = PERCENT_OF_AMOUNT_AND_INTEREST, 4 = PERCENT_OF_INTEREST
#                                     [ChargeCalculationType.java:26-29]
# chargePaymentMode 0 = REGULAR
set -eu
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513/.softhouse/capture/charges/req

cat > "$R/charge-01-flat-disbursement.json" <<'EOF'
{
 "name": "T40 flat fee at disbursement",
 "chargeAppliesTo": 1,
 "chargeTimeType": 1,
 "chargeCalculationType": 1,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 15000,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-02-flat-instalment.json" <<'EOF'
{
 "name": "T40 flat fee per instalment",
 "chargeAppliesTo": 1,
 "chargeTimeType": 8,
 "chargeCalculationType": 1,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 2500,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-03-pctamount-disbursement.json" <<'EOF'
{
 "name": "T40 percent of amount at disbursement",
 "chargeAppliesTo": 1,
 "chargeTimeType": 1,
 "chargeCalculationType": 2,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 1.2345,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-04-pctinterest-instalment.json" <<'EOF'
{
 "name": "T40 percent of interest per instalment",
 "chargeAppliesTo": 1,
 "chargeTimeType": 8,
 "chargeCalculationType": 4,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 3.75,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-05-pctamountinterest-instalment.json" <<'EOF'
{
 "name": "T40 percent of amount plus interest per instalment",
 "chargeAppliesTo": 1,
 "chargeTimeType": 8,
 "chargeCalculationType": 3,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 1.2345,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-06-penalty-specifieddue.json" <<'EOF'
{
 "name": "T40 PENALTY flat on specified due date",
 "chargeAppliesTo": 1,
 "chargeTimeType": 2,
 "chargeCalculationType": 1,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 7500,
 "penalty": true,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-07-fee-specifieddue.json" <<'EOF'
{
 "name": "T40 flat fee on specified due date",
 "chargeAppliesTo": 1,
 "chargeTimeType": 2,
 "chargeCalculationType": 1,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 9000,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-08-penalty-instalment.json" <<'EOF'
{
 "name": "T40 PENALTY flat per instalment",
 "chargeAppliesTo": 1,
 "chargeTimeType": 8,
 "chargeCalculationType": 1,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 1200,
 "penalty": true,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-09-pctamount-instalment.json" <<'EOF'
{
 "name": "T40 percent of amount per instalment",
 "chargeAppliesTo": 1,
 "chargeTimeType": 8,
 "chargeCalculationType": 2,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 0.5,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

cat > "$R/charge-10-pctamount-specifieddue.json" <<'EOF'
{
 "name": "T40 percent of amount on specified due date",
 "chargeAppliesTo": 1,
 "chargeTimeType": 2,
 "chargeCalculationType": 2,
 "chargePaymentMode": 0,
 "currencyCode": "MNT",
 "amount": 1.2345,
 "penalty": false,
 "active": true,
 "locale": "en",
 "monthDayFormat": "dd MMM"
}
EOF

ls -1 "$R"/charge-*.json
