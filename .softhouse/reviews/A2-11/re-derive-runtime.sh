#!/bin/bash
# A2-11 (b) — INDEPENDENT live re-derivation of A2-7's runtime-vs-creation finding.
#
# A2-7's instrument was loan 5 on product 46. Loan 5 is now CLOSED (written off by
# A2-7's own A2-232), and a charge-off on it now fails the *status* pre-check
# ("Loan Account is not Active", 403) before ever reaching the mapping lookup — so
# loan 5 can no longer test the claim. I build a FRESH loan on the SAME product 46,
# whose nine mapping rows I verified in the live DB (slots 1,2,3,4,5,6,10,11,12 —
# no 13 GOODWILL_CREDIT, no 16 CHARGE_OFF_EXPENSE).
#
# This is ADDITIVE: it creates one loan. It does not modify or delete any evidence.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/obs"
mkdir -p "$OUT"
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

post() { # post NAME PATH JSONBODY
  local name="$1" path="$2" body="$3" code
  code=$(printf '%s' "$body" | curl -sk --max-time 60 -o "$OUT/$name.json" -w '%{http_code}' \
         -X POST -H "$A" -H "$T" -H "$CT" --data-binary @- "$B$path")
  local rc=$?
  if [ $rc -ne 0 ]; then echo "TRANSPORT FAILURE rc=$rc on $path" >&2; rm -f "$OUT/$name.json"; exit 1; fi
  printf '%s' "$code" > "$OUT/$name.status"
  echo "POST $path -> $code"
  echo "     $(cat "$OUT/$name.json")"
}

echo "=== create a fresh loan on product 46 (byte-identical shape to A2-7's a2-7-loan-220.json) ==="
post a2-11-loan-create /loans '{"clientId":1,"productId":46,"principal":1200000,"loanTermFrequency":6,"loanTermFrequencyType":2,"numberOfRepayments":6,"repaymentEvery":1,"repaymentFrequencyType":2,"interestRatePerPeriod":0,"interestType":0,"amortizationType":1,"interestCalculationPeriodType":1,"transactionProcessingStrategyCode":"mifos-standard-strategy","expectedDisbursementDate":"01 February 2026","submittedOnDate":"01 February 2026","loanType":"individual","locale":"en","dateFormat":"dd MMMM yyyy"}'

LOAN=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["loanId"])' "$OUT/a2-11-loan-create.json")
echo "LOAN=$LOAN"

post a2-11-loan-approve "/loans/$LOAN?command=approve" '{"approvedOnDate":"01 February 2026","locale":"en","dateFormat":"dd MMMM yyyy"}'
post a2-11-loan-disburse "/loans/$LOAN?command=disburse" '{"actualDisbursementDate":"01 February 2026","transactionAmount":1200000,"locale":"en","dateFormat":"dd MMMM yyyy"}'

echo
echo "=== PROBE 1 — charge-off on a product with all nine notNull() slots mapped ==="
post a2-11-chargeoff "/loans/$LOAN/transactions?command=charge-off" '{"transactionDate":"01 March 2026","locale":"en","dateFormat":"dd MMMM yyyy"}'

echo
echo "=== PROBE 2 — goodwillCredit on the same loan ==="
post a2-11-goodwillcredit "/loans/$LOAN/transactions?command=goodwillCredit" '{"transactionDate":"01 March 2026","transactionAmount":100000,"locale":"en","dateFormat":"dd MMMM yyyy"}'

echo
echo "=== CONTROL — a repayment on the same loan must SUCCEED (so the 404s are about the mapping, not the loan) ==="
post a2-11-repayment "/loans/$LOAN/transactions?command=repayment" '{"transactionDate":"01 March 2026","transactionAmount":200000,"locale":"en","dateFormat":"dd MMMM yyyy"}'

echo
echo "=== state after the two refusals ==="
curl -sk --max-time 40 -o "$OUT/a2-11-loan-state.json" -H "$A" -H "$T" "$B/loans/$LOAN"
python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print("  status:",d["status"]["value"]," principal:",d["principal"])' "$OUT/a2-11-loan-state.json"
echo "$LOAN" > "$OUT/a2-11-loan-id.txt"
