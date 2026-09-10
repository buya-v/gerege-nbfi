#!/usr/bin/env bash
# STEP 3 — create the two NEW charges the loan needs so that BOTH the fee and the
# penalty terms of the four-term summary sum are non-zero AND DIFFER (100.00 vs
# 57.00). Equal values let a term-swap defect survive; these do not.
# F-2026-09-09-fee-penalty-blind.
source "$(dirname "$0")/common.sh"

create_charge() {
  local name="$1" extra="$2"
  local existing id
  existing=$(api_get "/charges" | python3 -c "import json,sys; d=json.load(sys.stdin); print([c['id'] for c in d if c.get('name')=='$name'])")
  if [ "$existing" != "[]" ]; then
    id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "{\"name\":\"$name\",\"id\":$id,\"reused\":true}"
    return
  fi
  echo "$extra" > "$REQ/charge-$name.json"
  api_post "/charges" "$REQ/charge-$name.json" > "$OUT/charge-$name-raw.json"
  cat "$OUT/charge-$name-raw.json" >&2
  id=$(python3 -c "import json;print(json.load(open('$OUT/charge-$name-raw.json')).get('resourceId',''))")
  echo "{\"name\":\"$name\",\"id\":$id,\"reused\":false}"
}

FEE=$(create_charge "OHLGR-Fee-Flat-100" '{"name":"OHLGR-Fee-Flat-100","chargeAppliesTo":1,"chargeTimeType":1,"chargeCalculationType":1,"currencyCode":"MNT","amount":100.00,"penalty":false,"active":true,"chargePaymentMode":0,"locale":"en","dateFormat":"dd MMMM yyyy"}')

PEN=$(create_charge "OHLGR-Penalty-Flat-57" '{"name":"OHLGR-Penalty-Flat-57","chargeAppliesTo":1,"chargeTimeType":2,"chargeCalculationType":1,"currencyCode":"MNT","amount":57.00,"penalty":true,"active":true,"chargePaymentMode":0,"dueDate":"01 September 2026","locale":"en","dateFormat":"dd MMMM yyyy"}')

echo "$FEE"
echo "$PEN"
python3 - "$STATE" "$FEE" "$PEN" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))
for a in sys.argv[2:]:
    o=json.loads(a)
    if o['name'].startswith('OHLGR-Fee'): s['feeCharge']=o['id']
    else: s['penaltyCharge']=o['id']
json.dump(s,open(sys.argv[1],'w'),indent=2)
PY
