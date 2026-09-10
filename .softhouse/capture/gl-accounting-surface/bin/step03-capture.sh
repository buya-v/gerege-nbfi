#!/usr/bin/env bash
# STEP 3 — capture the GL + summary surface for the NEW loan and for loan 10.
#
# ADDITIVE: GETs only. No request body on a GET, so nothing here can carry the
# P-25 defect; the responses are ORACLE OBSERVATIONS (T186 7 A4: never rewritten,
# never re-emitted through a float), so their non-preserved numeric cells are
# recorded as read and are not graded as request bodies.
source "$(dirname "$0")/common.sh"

LOAN="${1:-$(state_get loan3)}"
echo "loan3=$LOAN"

api_get "/loans/$LOAN"                         > "$OUT/loan-$LOAN-raw.json"
api_get "/loans/$LOAN/transactions"            > "$OUT/loan-$LOAN-transactions-raw.json"
api_get "/journalentries?loanId=$LOAN"         > "$OUT/journalentries-loan-$LOAN-raw.json"
api_get "/journalentries"                      > "$OUT/journalentries-all-raw.json"
api_get "/glaccounts"                          > "$OUT/glaccounts-after-raw.json"

# The fee-zero / penalty-non-zero observation comes from the EXISTING loan 10
# (OHGLR-L01): its loan-level fee was a disbursement charge settled at
# disbursement, its SDD penalty 57 stays outstanding. A GET does not modify it.
api_get "/loans/10"                            > "$OUT/loan-10-raw.json"

# journal entries by each of the new loan's transaction ids
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

echo "--- loan $LOAN summary (four-term) ---"
python3 - "$OUT/loan-$LOAN-raw.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
s=d.get('summary',{})
for k in ['principal','principalOutstanding','principalOverdue','interestCharged','interestOutstanding','interestOverdue','feeChargesCharged','feeChargesOutstanding','feeChargesOverdue','penaltyChargesCharged','penaltyChargesOutstanding','penaltyChargesOverdue','totalOutstanding','totalOverdue','totalExpectedRepayment','totalRepayment']:
    if k in s: print(f"  {k}={s[k]}")
PY
echo "--- loan 10 summary (fee 0, penalty non-zero) ---"
python3 - "$OUT/loan-10-raw.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
s=d.get('summary',{})
for k in ['principal','interestCharged','interestOutstanding','feeChargesOutstanding','penaltyChargesOutstanding','totalOutstanding']:
    if k in s: print(f"  {k}={s[k]}")
PY
echo "--- journalentries for loan $LOAN ---"
cat "$OUT/journalentries-loan-$LOAN-raw.json"
echo
