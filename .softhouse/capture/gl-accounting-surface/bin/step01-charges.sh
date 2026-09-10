#!/usr/bin/env bash
# STEP 1 — create the two NEW charges the loan needs so that BOTH the fee and the
# penalty terms of the four-term summary sum are non-zero AND DIFFER. Equal values
# would let a term-swap defect survive; these do not.
#
# The amounts are written as INTEGER tokens (100, 57). `POST /charges` binds
# `private double amount` (T186 2.4), so the only text that survives that double
# byte-for-byte is text that is already the shortest round-trip repr of its
# binary64 value. `100` and `57` do; `100.00` and `57.00` do not (they re-emit as
# `100.0` / `57.0`). This is the P-25 defect the bar refused OH-GL-R for.
source "$(dirname "$0")/common.sh"

create_charge() {
  local name="$1" body="$2"
  local existing id
  existing=$(api_get "/charges" | python3 -c "import json,sys; d=json.load(sys.stdin); print([c['id'] for c in d if c.get('name')=='$name'])")
  if [ "$existing" != "[]" ]; then
    id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "{\"name\":\"$name\",\"id\":$id,\"reused\":true}"
    return
  fi
  printf '%s' "$body" > "$REQ/charge-$name.json"
  api_post "/charges" "$REQ/charge-$name.json" > "$OUT/charge-$name-raw.json"
  cat "$OUT/charge-$name-raw.json" >&2; echo >&2
  id=$(python3 -c "import json;print(json.load(open('$OUT/charge-$name-raw.json')).get('resourceId',''))")
  echo "{\"name\":\"$name\",\"id\":$id,\"reused\":false}"
}

FEE=$(create_charge "OHLGT-Fee-SDD-100" '{"name":"OHLGT-Fee-SDD-100","chargeAppliesTo":1,"chargeTimeType":2,"chargeCalculationType":1,"currencyCode":"MNT","amount":100,"penalty":false,"active":true,"chargePaymentMode":0,"locale":"en","dateFormat":"dd MMMM yyyy"}')

PEN=$(create_charge "OHLGT-Penalty-SDD-57" '{"name":"OHLGT-Penalty-SDD-57","chargeAppliesTo":1,"chargeTimeType":2,"chargeCalculationType":1,"currencyCode":"MNT","amount":57,"penalty":true,"active":true,"chargePaymentMode":0,"locale":"en","dateFormat":"dd MMMM yyyy"}')

echo "$FEE"
echo "$PEN"
python3 - "$STATE" "$FEE" "$PEN" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))
for a in sys.argv[2:]:
    o=json.loads(a)
    if o['name'].startswith('OHLGT-Fee'): s['feeCharge']=o['id']
    else: s['penaltyCharge']=o['id']
json.dump(s,open(sys.argv[1],'w'),indent=2)
PY
