#!/usr/bin/env bash
# step02-create.sh — OH-WOPAID-AU
#
# Create ONE accounting-bearing loan whose schedule can carry a FULLY PAID
# instalment: product 3 (OHLGR-Accrual-Loan, accountingRule ACCRUAL PERIODIC),
# principal 100000, 12 monthly periods at 12%/yr, disbursed 2026-01-01 exactly
# like loan 11 (OHGLR-L02) so the period-1 due is principal 7884.88 + interest
# 1000.00 (the same schedule the loan-11 write-off used). Two specified-due-date
# charges (fee 100 due 15 Feb 2026, penalty 57 due 15 Mar 2026) keep all four
# outstanding buckets exercised, exactly as committed vector LN-L11 expects.
#
# Every numeric JSON token is an integer or a JSON string. No float is ever
# serialised, so every body survives a binary-double round trip byte-for-byte.
#
# Writes: POST /clients, POST /loans, /loans/{id}?command=approve, ?command=disburse.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-writeoff-paid-instalment

DATE="01 January 2026"
CLIENT_EXT="OHWOPAID-C01"
LOAN_EXT="OHWOPAID-L01"

# ---- client ---------------------------------------------------------------
cat > "$OHS_REQ/client-$CLIENT_EXT-create.json" <<EOF
{"officeId":1,"firstname":"OHWOPAID","lastname":"Borrower","externalId":"$CLIENT_EXT","legalFormId":1,"active":true,"activationDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post "client-$CLIENT_EXT-create" "/clients" "$OHS_REQ/client-$CLIENT_EXT-create.json"
CID=$(ohs_id "$OHS_OUT/client-$CLIENT_EXT-create-raw.json")
[ -z "$CID" ] && { echo "CLIENT CREATE FAILED"; cat "$OHS_OUT/client-$CLIENT_EXT-create-raw.json"; exit 3; }
echo "clientId=$CID"
printf '%s\n' "$CID" > "$OHS_OUT/.client-id"
printf '%s\n' "$CLIENT_EXT" > "$OHS_OUT/.client-ext"

# ---- loan submit ----------------------------------------------------------
# chargeId 5 = OHLGR-Fee-SDD-100 (fee 100), chargeId 4 = OHLGR-Penalty-Flat-57.
cat > "$OHS_REQ/loan-$LOAN_EXT-submit.json" <<EOF
{
  "clientId": $CID,
  "productId": 3,
  "externalId": "$LOAN_EXT",
  "principal": "100000",
  "loanTermFrequency": 12,
  "loanTermFrequencyType": 2,
  "numberOfRepayments": 12,
  "repaymentEvery": 1,
  "repaymentFrequencyType": 2,
  "interestRatePerPeriod": 12,
  "interestRateFrequencyType": 3,
  "amortizationType": 1,
  "interestType": 0,
  "interestCalculationPeriodType": 1,
  "transactionProcessingStrategyCode": "mifos-standard-strategy",
  "loanType": "individual",
  "submittedOnDate": "$DATE",
  "expectedDisbursementDate": "$DATE",
  "charges": [
    {"chargeId": 5, "amount": 100, "dueDate": "15 February 2026"},
    {"chargeId": 4, "amount": 57, "dueDate": "15 March 2026"}
  ],
  "locale": "en",
  "dateFormat": "dd MMMM yyyy"
}
EOF
ohs_post "loan-$LOAN_EXT-submit" "/loans" "$OHS_REQ/loan-$LOAN_EXT-submit.json"
LID=$(ohs_id "$OHS_OUT/loan-$LOAN_EXT-submit-raw.json")
[ -z "$LID" ] && { echo "LOAN SUBMIT FAILED"; cat "$OHS_OUT/loan-$LOAN_EXT-submit-raw.json"; exit 3; }
echo "loanId=$LID"
printf '%s\n' "$LID" > "$OHS_OUT/.loan-id"
printf '%s\n' "$LOAN_EXT" > "$OHS_OUT/.loan-ext"

# ---- approve + disburse ---------------------------------------------------
cat > "$OHS_REQ/loan-$LOAN_EXT-approve.json" <<EOF
{"approvedOnDate":"$DATE","expectedDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post "loan-$LOAN_EXT-approve" "/loans/$LID?command=approve" "$OHS_REQ/loan-$LOAN_EXT-approve.json"

cat > "$OHS_REQ/loan-$LOAN_EXT-disburse.json" <<EOF
{"actualDisbursementDate":"$DATE","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF
ohs_post "loan-$LOAN_EXT-disburse" "/loans/$LID?command=disburse" "$OHS_REQ/loan-$LOAN_EXT-disburse.json"

# ---- capture the freshly-created state (READ-ONLY) ------------------------
ohs_get "loan-$LID-created-detail"      "/loans/$LID?associations=all"
ohs_get "loan-$LID-created-transactions" "/loans/$LID/transactions"

echo "--- created loan summary ---"
python3 - "$OHS_OUT/loan-$LID-created-detail-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d.get('summary', {})
print('status', d.get('status', {}).get('code'))
for k in ['principalDisbursed', 'totalExpectedRepayment', 'principalOutstanding',
          'interestOutstanding', 'feeChargesOutstanding', 'penaltyChargesOutstanding',
          'totalOutstanding']:
    print(f'  {k}={s.get(k)}')
rs = d.get('repaymentSchedule', {})
for p in (rs.get('periods') or [])[:3]:
    print('  period', p.get('period'), 'due', p.get('dueDate'), 'complete', p.get('complete'),
          'prinDue', p.get('principalDue'), 'intDue', p.get('interestDue'),
          'feeDue', p.get('feeChargesDue'), 'penDue', p.get('penaltyChargesDue'))
PY
echo "step02 done. loanId=$LID"
