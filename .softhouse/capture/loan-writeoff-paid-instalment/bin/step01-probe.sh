#!/usr/bin/env bash
# step01-probe.sh — OH-WOPAID-AU
#
# READ-ONLY probe. It records WHY a new loan must be created rather than reusing
# an existing one, and verifies the pinned business date.
#
# Objective: an ACTIVE loan whose schedule carries at least one instalment that
# is FULLY PAID (complete: true) AND at least one with outstanding principal,
# so a write-off exercises the `isNotFullyPaidOff()` SKIP in
#   writeoff.go:36 WriteOffOutstanding / Fineract handleWriteOff.
#
# Every call is a GET (or a read-only SQL SELECT). No write, no SQL insert.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-writeoff-paid-instalment

# ---- business date (read-only SQL) --------------------------------------
{
    echo "# OH-WOPAID-AU business date (read-only)"
    docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
        "select type, date from m_business_date order by type;"
} > "$OHS_OUT/probe-businessdate.txt"
cat "$OHS_OUT/probe-businessdate.txt"

# ---- loan inventory ------------------------------------------------------
ohs_get probe-loans "/loans?limit=100"

# loan id -> product / accounting / status (read-only SQL)
docker exec gerege-oracle-db psql -U root -d fineract_gerege -A -F'|' -c \
    "select l.id, l.account_no, coalesce(l.external_id,''), l.product_id, l.loan_status_id, p.name, p.accounting_type, l.principal_amount from m_loan l join m_product_loan p on p.id=l.product_id order by l.id;" \
    > "$OHS_OUT/probe-loans-db.txt"
cat "$OHS_OUT/probe-loans-db.txt"

# ---- per-loan schedule scan (READ-ONLY) ----------------------------------
IDS=$(python3 -c 'import json;d=json.load(open("'"$OHS_OUT"'/probe-loans-raw.json"));print(" ".join(str(l["id"]) for l in d.get("pageItems",[])))')
for id in $IDS; do
    ohs_get "probe-loan-$id-detail" "/loans/$id?associations=all"
done

# ---- reduce to a citeable JSON summary -----------------------------------
python3 - "$OHS_OUT" <<'PY' > "$OHS_OUT/probe-summary.json"
import json, os, sys
out = sys.argv[1]

def load(name):
    with open(os.path.join(out, name)) as f:
        return json.load(f)

loans = load('probe-loans-raw.json').get('pageItems', [])
db = {}
with open(os.path.join(out, 'probe-loans-db.txt')) as f:
    for line in f:
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        if len(parts) < 8 or not parts[0].isdigit():
            continue
        db[int(parts[0])] = {'accountNo': parts[1], 'externalId': parts[2],
                             'productId': int(parts[3]), 'loanStatusId': int(parts[4]),
                             'productName': parts[5], 'accountingType': int(parts[6]),
                             'principal': parts[7]}

summary = {'businessDate': None, 'loans': [], 'candidates': []}
with open(os.path.join(out, 'probe-businessdate.txt')) as f:
    for line in f:
        if line.startswith('BUSINESS_DATE|'):
            summary['businessDate'] = line.strip().split('|')[1]

for l in loans:
    lid = l['id']
    d = load('probe-loan-%d-detail-raw.json' % lid)
    periods = d.get('repaymentSchedule', {}).get('periods', []) or []
    paid, unpaid_with_principal = [], []
    for p in periods:
        if p.get('period') is None:
            continue
        po = p.get('principalOutstanding') or 0
        per = {
            'period': p.get('period'),
            'dueDate': p.get('dueDate'),
            'complete': p.get('complete'),
            'principalDue': p.get('principalDue'),
            'principalOutstanding': p.get('principalOutstanding'),
            'interestDue': p.get('interestDue'),
            'interestOutstanding': p.get('interestOutstanding'),
            'feeChargesDue': p.get('feeChargesDue'),
            'feeChargesOutstanding': p.get('feeChargesOutstanding'),
            'penaltyChargesDue': p.get('penaltyChargesDue'),
            'penaltyChargesOutstanding': p.get('penaltyChargesOutstanding'),
        }
        if p.get('complete') is True:
            paid.append(per)
        if not p.get('complete') and po and po > 0:
            unpaid_with_principal.append(per)
    meta = db.get(lid, {})
    row = {
        'id': lid,
        'accountNo': l.get('accountNo'),
        'externalId': l.get('externalId'),
        'productId': meta.get('productId'),
        'productName': meta.get('productName'),
        'accountingType': meta.get('accountingType'),
        'loanStatusId': meta.get('loanStatusId'),
        'status': d.get('status', {}).get('code'),
        'paidInstalments': paid,
        'nUnpaidWithPrincipal': len(unpaid_with_principal),
    }
    summary['loans'].append(row)
    if paid and unpaid_with_principal:
        summary['candidates'].append({'id': lid, 'productId': meta.get('productId'),
                                      'accountingType': meta.get('accountingType'),
                                      'paidInstalments': paid})

json.dump(summary, open(os.path.join(out, 'probe-summary.json'), 'w'), indent=2)
print(json.dumps(summary, indent=2))
PY

echo "probe done."
