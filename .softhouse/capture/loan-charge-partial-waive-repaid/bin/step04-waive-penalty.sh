#!/usr/bin/env bash
# step04-waive-penalty.sh — OH-CHGCAP-BD
#
# Waive the PENALTY.  POST /loans/{id}/charges/{chargeId}?command=waive with an
# empty JSON body (the endpoint derives the waive amount from the charge; the
# probe against a throwaway loan returned {"changes":{"amount":91.34}} for a
# partly-paid fee, and 200 for {}).
#
# For a charge whose due date is before the business date the oracle dates the
# waive transaction on the charge's due date (Fineract
# LoanChargeWritePlatformServiceImpl.waiveLoanCharge): here 2026-02-15.
#
# Observes charge.go Waive: amountWaived 0 -> 67.89, amountOutstanding 67.89 -> 0,
# paid false, waived true.  Also observes lifecycle.go DetermineTransition on the
# waive transaction date (loan still Active, outstanding remains -> NoTransition).
#
# Write: POST /loans/{id}/charges/{chargeId}?command=waive.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-charge-partial-waive-repaid

LID=$(cat "$OHS_OUT/.loan-id")
PCID=$(python3 - "$OHS_OUT/loan-$LID-after-partial-detail-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for c in d['charges']:
    if c['penalty']:
        print(c['id']); break
PY
)
[ -z "$PCID" ] && { echo "PENALTY CHARGE NOT FOUND"; exit 3; }
echo "penalty loanChargeId=$PCID"
printf '%s\n' "$PCID" > "$OHS_OUT/.penalty-charge-id"

REQ="$OHS_REQ/loan-$LID-waive-charge-$PCID.json"
printf '{}' > "$REQ"

ohs_post "loan-$LID-waive-charge-$PCID" "/loans/$LID/charges/$PCID?command=waive" "$REQ"

bash "$(dirname "$0")/capture-state.sh" "$LID" "after-waive"

echo "--- after the penalty waiver ---"
python3 - "$OHS_OUT" "$LID" <<'PY'
import json, sys
out, lid = sys.argv[1], sys.argv[2]
d = json.load(open(f'{out}/loan-{lid}-after-waive-detail-raw.json'))
s = d['summary']
print('status', d['status']['code'], 'totalOutstanding', s['totalOutstanding'])
print('buckets out: prin', s['principalOutstanding'], 'int', s['interestOutstanding'],
      'fee', s['feeChargesOutstanding'], 'pen', s['penaltyChargesOutstanding'])
for c in (d.get('charges') or []):
    print('  charge', c['id'], c['name'], 'penalty', c['penalty'], 'amt', c['amount'],
          'paid', c['amountPaid'], 'waived', c['amountWaived'], 'out', c['amountOutstanding'],
          'paidFlag', c['paid'], 'waivedFlag', c['waived'])
PY
echo "step04 done."
