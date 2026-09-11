#!/usr/bin/env bash
# step05-writeoff.sh — OH-WOPAID-AU
#
# Write loan 13 off at the pinned business date 2026-09-03.  The last transaction
# is the 2026-02-01 repayment, so the write-off is strictly later (not
# future-dated).  Endpoint copied from the loan-11 capture: the command lives on
# the transactions sub-resource (POST /loans/{id}?command=writeoff is refused 400).
#
# Body has no numeric token at all, so it is byte-stable.
#
# Write: POST /loans/{id}/transactions?command=writeoff.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-writeoff-paid-instalment

LID=$(python3 -c "import json;print(json.load(open('$OHS_OUT/loan-13-before-detail-raw.json'))['id'])")
REQ="$OHS_REQ/loan-$LID-writeoff.json"
cat > "$REQ" <<'EOF'
{"transactionDate":"03 September 2026","locale":"en","dateFormat":"dd MMMM yyyy"}
EOF

ohs_post "loan-$LID-writeoff" "/loans/$LID/transactions?command=writeoff" "$REQ"

# after the write-off
bash "$(dirname "$0")/capture-state.sh" "$LID" "after"

echo "--- the write-off transaction and the after arithmetic ---"
python3 - "$OHS_OUT" "$LID" <<'PY'
import json, sys
out, lid = sys.argv[1], sys.argv[2]
prev = json.load(open(f'{out}/loan-{lid}-after-repay-detail-raw.json'))
aft  = json.load(open(f'{out}/loan-{lid}-after-detail-raw.json'))
txns = json.load(open(f'{out}/loan-{lid}-after-transactions-raw.json'))['content']
wo = [t for t in txns if t['type']['code'] == 'loanTransactionType.writeOff']
print('write-off txn:', [(t['id'], t['amount'], t.get('principalPortion'),
      t.get('interestPortion'), t.get('feeChargesPortion'),
      t.get('penaltyChargesPortion')) for t in wo])
s = aft['summary']
print('after buckets: prin', s['principalOutstanding'], 'int', s['interestOutstanding'],
      'fee', s['feeChargesOutstanding'], 'pen', s['penaltyChargesOutstanding'],
      'total', s['totalOutstanding'])
print('after writtenoff: prin', s['principalWrittenOff'], 'int', s['interestWrittenOff'],
      'fee', s['feeChargesWrittenOff'], 'pen', s['penaltyChargesWrittenOff'],
      'total', s['totalWrittenOff'])
print('status', aft['status']['code'])
# arithmetic: write-off amount == sum over UNPAID instalments only
paid = [p for p in prev['repaymentSchedule']['periods'] if p.get('complete')]
unpaid = [p for p in prev['repaymentSchedule']['periods'] if p.get('period') and not p.get('complete')]
def tot(p): return p['principalOutstanding'] + p['interestOutstanding'] + p['feeChargesOutstanding'] + p['penaltyChargesOutstanding']
paid_sum, unpaid_sum = sum(map(tot, paid)), sum(map(tot, unpaid))
print(f'paid instalments sum   = {paid_sum:.2f}  ({len(paid)} instalment(s))')
print(f'UNPAID instalments sum = {unpaid_sum:.2f}  ({len(unpaid)} instalments)')
print(f'all-instalments sum    = {paid_sum+unpaid_sum:.2f}  (a port that forgets the skip would write this off)')
PY
