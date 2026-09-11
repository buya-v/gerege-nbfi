#!/usr/bin/env bash
# STEP 1 (OH-PROVEDGE-BA): READ-ONLY recon of the oracle tenant `gerege` before
# any write. Captures the pinned business date, the criteria-1 band definitions
# (the seam under test), the current provisioning entries, and the active loans
# on product 2 with their schedules. Nothing here writes to the tenant.
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
OUT_DIR=".softhouse/capture/provisioning-upper-edge/out"
DB='gerege-oracle-db'

mkdir -p "$OUT_DIR"

get() { curl -sk -u mifos:password -H "$TEN" "$BASE$1"; }

get /businessdate > "$OUT_DIR/recon-businessdate-raw.json"
get /provisioningcriteria/1 > "$OUT_DIR/recon-criteria-1-raw.json"
get '/provisioningentries?limit=100&offset=0' > "$OUT_DIR/recon-entries-list-raw.json"

# active loans on the mapped product, from the oracle's own read-back
get '/loans?limit=1000' > "$OUT_DIR/recon-loans-list-raw.json"

python3 - "$OUT_DIR" <<'PY'
import json, os, sys
out = sys.argv[1]
bd = json.load(open(os.path.join(out, 'recon-businessdate-raw.json')))
crit = json.load(open(os.path.join(out, 'recon-criteria-1-raw.json')))
loans = json.load(open(os.path.join(out, 'recon-loans-list-raw.json')))

def iso(a):
    if a is None: return None
    return "%04d-%02d-%02d" % tuple(a)

print("businessDate =", iso(next(x for x in bd if x['type'] == 'BUSINESS_DATE')['date']))
for d in crit['definitions']:
    print("band %-11s [%d,%d] %s%%" % (d['categoryName'], d['minAge'], d['maxAge'], d['provisioningPercentage']))
items = loans.get('pageItems', loans if isinstance(loans, list) else [])
act = [l for l in items if l.get('loanProductId') == 2 and l.get('status', {}).get('active')]
print("active product-2 loans:", len(act))
for l in sorted(act, key=lambda x: x['id']):
    print("  id=%d ext=%s outstanding=%s" % (l['id'], l.get('externalId'), l.get('totalOutstanding')))
PY

echo "--- read-only SQL corroboration: schedules of active product-2 loans ---"
docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -A -F'|' -c \
"select l.id, l.external_id, s.installment, s.duedate, s.completed_derived
   from m_loan l
   join m_loan_repayment_schedule s on s.loan_id = l.id
  where l.product_id = 2 and l.loan_status_id = 300 and s.installment = 1
  order by l.id;"

echo "recon done"
