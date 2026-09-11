#!/usr/bin/env bash
# STEP 5 (OH-PROVEDGE-BA): read the new provisioning entry back exactly as OH-3
# read ENT-03/ENT-04: entry metadata (GET /provisioningentries/{id}) and the
# per-loan-product rows (GET /provisioningentries/entries?entryId={id}).
set -uo pipefail

BASE='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
TEN='Fineract-Platform-TenantId: gerege'
OUT_DIR=".softhouse/capture/provisioning-upper-edge/out"

RID=$(cat "$OUT_DIR/ENT-02-resource-id.txt")

curl -sk "$BASE/provisioningentries/$RID" -H "$AUTH" -H "$TEN" \
  > "$OUT_DIR/ENT-03-entry-metadata-raw.json"
curl -sk "$BASE/provisioningentries/entries?entryId=$RID&limit=100&offset=0" -H "$AUTH" -H "$TEN" \
  > "$OUT_DIR/ENT-04-entry-loan-products-raw.json"
curl -sk "$BASE/provisioningentries?limit=100&offset=0" -H "$AUTH" -H "$TEN" \
  > "$OUT_DIR/ENT-05-entries-list-raw.json"

echo "=== ENT-03 entry metadata (id=$RID) ==="
cat "$OUT_DIR/ENT-03-entry-metadata-raw.json"; echo
echo "=== ENT-04 loan-product rows ==="
python3 - "$OUT_DIR/ENT-04-entry-loan-products-raw.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for r in sorted(d['pageItems'], key=lambda x: x['overdueInDays']):
    print("overdueInDays=%-4d %-11s reserved=%s" % (
        r['overdueInDays'], r['categoryName'], r['amountreserved']))
print("totalFilteredRecords =", d['totalFilteredRecords'])
PY
echo "readback entry done"
