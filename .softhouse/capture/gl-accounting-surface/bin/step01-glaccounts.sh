#!/usr/bin/env bash
# STEP 1 — inventory the chart of accounts, then create ONLY what the accrual
# product's mapping set needs. ADDITIVE: existing accounts 1..4 are untouched.
#
# Type ids: 1=ASSET 2=LIABILITY 3=EQUITY 4=INCOME 5=EXPENSE
# Usage ids: 1=DETAIL 2=HEADER
source "$(dirname "$0")/common.sh"

api_get "/glaccounts?limit=1000" > "$OUT/glaccounts-before-raw.json"

create_gl() {
  local name="$1" glcode="$2" type_id="$3" desc="$4"
  local existing id
  existing=$(api_get "/glaccounts?limit=1000" | python3 -c "import json,sys; d=json.load(sys.stdin); print([g['id'] for g in d if g.get('glCode')=='$glcode'])")
  if [ "$existing" != "[]" ]; then
    id=$(echo "$existing" | python3 -c "import json,sys;print(json.load(sys.stdin)[0])")
    echo "{\"name\":\"$name\",\"glCode\":\"$glcode\",\"id\":$id,\"reused\":true}"
    return
  fi
  cat > "$REQ/gl-$glcode.json" <<EOF
{"name":"$name","glCode":"$glcode","manualEntriesAllowed":true,"type":$type_id,"usage":1,"description":"$desc"}
EOF
  api_post "/glaccounts" "$REQ/gl-$glcode.json" > "$OUT/gl-$glcode-raw.json"
  id=$(python3 -c "import json;print(json.load(open('$OUT/gl-$glcode-raw.json')).get('resourceId',''))")
  echo "{\"name\":\"$name\",\"glCode\":\"$glcode\",\"id\":$id,\"reused\":false}"
}

A1=$(create_gl "OHLGR-Loan-Portfolio"        "OHLGR-10010" 1 "OH-GLR loan portfolio (asset)")
A2=$(create_gl "OHLGR-Transfers-Suspense"    "OHLGR-10011" 1 "OH-GLR transfers in suspense (asset)")
A3=$(create_gl "OHLGR-Interest-Receivable"   "OHLGR-10012" 1 "OH-GLR interest receivable (asset)")
A4=$(create_gl "OHLGR-Fees-Receivable"       "OHLGR-10013" 1 "OH-GLR fees receivable (asset)")
A5=$(create_gl "OHLGR-Penalties-Receivable"  "OHLGR-10014" 1 "OH-GLR penalties receivable (asset)")
L1=$(create_gl "OHLGR-Fund-Source"           "OHLGR-20010" 2 "OH-GLR fund source (liability)")
L2=$(create_gl "OHLGR-Overpayment-Liability" "OHLGR-20011" 2 "OH-GLR overpayment liability")
I1=$(create_gl "OHLGR-Interest-On-Loans"     "OHLGR-40010" 4 "OH-GLR interest on loans (income)")
I2=$(create_gl "OHLGR-Income-From-Fees"      "OHLGR-40011" 4 "OH-GLR income from fees")
I3=$(create_gl "OHLGR-Income-From-Penalties" "OHLGR-40012" 4 "OH-GLR income from penalties")
I4=$(create_gl "OHLGR-Income-From-Recovery"  "OHLGR-40013" 4 "OH-GLR income from recovery")
E1=$(create_gl "OHLGR-Losses-Written-Off"    "OHLGR-50010" 5 "OH-GLR losses written off (expense)")

python3 - "$STATE" "$A1" "$A2" "$A3" "$A4" "$A5" "$L1" "$L2" "$I1" "$I2" "$I3" "$I4" "$E1" <<'PY'
import json,sys
s=json.load(open(sys.argv[1])); gl={}
for a in sys.argv[2:]:
    o=json.loads(a); gl[o['glCode']]=o
s['gl']=gl
json.dump(s,open(sys.argv[1],'w'),indent=2)
PY
cat "$STATE"
