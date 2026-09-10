#!/usr/bin/env bash
# STEP 5 — capture the GL surface for the NEW loan. ADDITIVE: GETs only.
source "$(dirname "$0")/common.sh"

LOAN="${1:-$(state_get loan)}"
echo "loan=$LOAN"

api_get "/loans/$LOAN"                        > "$OUT/loan-$LOAN-raw.json"
api_get "/loans/$LOAN/transactions"           > "$OUT/loan-$LOAN-transactions-raw.json"
api_get "/journalentries?loanId=$LOAN"        > "$OUT/journalentries-loan-$LOAN-raw.json"
api_get "/journalentries"                     > "$OUT/journalentries-all-raw.json"
api_get "/glaccounts"                         > "$OUT/glaccounts-after-raw.json"

# journal entries by each loan transaction id
python3 - "$OUT/loan-$LOAN-transactions-raw.json" <<'PY' > "$OUT/txn-ids.txt"
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    ids=[t['id'] for t in (d if isinstance(d,list) else d.get('pageItems',[]))]
except Exception:
    ids=[]
print('\n'.join(str(i) for i in ids))
PY
while read -r tid; do
  [ -z "$tid" ] && continue
  api_get "/journalentries?transactionId=$tid" > "$OUT/journalentries-txn-$tid-raw.json"
done < "$OUT/txn-ids.txt"

echo "--- loan summary ---"
python3 - "$OUT/loan-$LOAN-raw.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
s=d.get('summary',{})
for k in ['principal','principalOutstanding','principalOverdue','interestCharged','interestOutstanding','interestOverdue','feeChargesCharged','feeChargesOutstanding','feeChargesOverdue','penaltyChargesCharged','penaltyChargesOutstanding','penaltyChargesOverdue','totalOutstanding','totalOverdue','totalExpectedRepayment','totalRepayment']:
    if k in s: print(f"  {k}={s[k]}")
PY
echo "--- transactions ---"
cat "$OUT/loan-$LOAN-transactions-raw.json"
echo
echo "--- journalentries for loan ---"
cat "$OUT/journalentries-loan-$LOAN-raw.json"
echo
