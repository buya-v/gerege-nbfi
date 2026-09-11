#!/usr/bin/env bash
# step01-probe.sh — OH-CHGCAP-BD
#
# READ-ONLY probe. Records (a) the pinned business date, (b) the existing charge
# definitions (GET /charges) that this capture reuses, and (c) the loan
# inventory, so the OWNER can justify reusing charge 5 (fee) and charge 4
# (penalty) rather than creating one.
#
# Every call is a GET (or a read-only SQL SELECT). No write, no SQL insert.
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
# shellcheck disable=SC1091
. .softhouse/capture/ohsweep/lib.sh
ohs_ctx loan-charge-partial-waive-repaid

# ---- business date (read-only SQL) --------------------------------------
{
    echo "# OH-CHGCAP-BD business date (read-only, tenant gerege)"
    docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -A -F'|' -c \
        "select type, date from m_business_date order by type;"
} > "$OHS_OUT/probe-businessdate.txt"
cat "$OHS_OUT/probe-businessdate.txt"

# ---- charge definitions + loan inventory (GET only) ----------------------
ohs_get probe-charges "/charges"
ohs_get probe-loans   "/loans?limit=100"

# ---- charge definitions, reduced to the fields the OWNER cites -----------
python3 - "$OHS_OUT" <<'PY' > "$OHS_OUT/probe-charges-summary.json"
import json, os, sys
out = sys.argv[1]
charges = json.load(open(os.path.join(out, 'probe-charges-raw.json')))
rows = []
for c in charges:
    rows.append({
        'id': c.get('id'),
        'name': c.get('name'),
        'penalty': c.get('penalty'),
        'chargeTimeType': (c.get('chargeTimeType') or {}).get('code'),
        'chargeCalculationType': (c.get('chargeCalculationType') or {}).get('code'),
        'amount': c.get('amount'),
        'currency': (c.get('currency') or {}).get('code'),
        'active': c.get('active'),
    })
json.dump({'count': len(rows), 'charges': rows}, open(os.path.join(out, 'probe-charges-summary.json'), 'w'), indent=2)
print(json.dumps({'count': len(rows), 'charges': rows}, indent=2))
PY

echo "probe done."
