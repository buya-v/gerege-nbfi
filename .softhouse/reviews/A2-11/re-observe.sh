#!/bin/bash
# A2-11 — independent re-observation of A2-7's captures against the LIVE reference oracle
# (Fineract). Writes only under .softhouse/reviews/A2-11/obs/ so the A2 capture manifest
# is untouched. Nothing here is synthesised; every byte is what the oracle returned.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/obs"
mkdir -p "$OUT"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

get() { # get NAME PATH
  local name="$1" path="$2" code
  code=$(curl -sk --max-time 60 -o "$OUT/$name.json" -w '%{http_code}' -H "$A" -H "$T" "$B$path")
  local rc=$?
  if [ $rc -ne 0 ]; then echo "TRANSPORT FAILURE rc=$rc on $path" >&2; rm -f "$OUT/$name.json"; return 1; fi
  printf '%s' "$code" > "$OUT/$name.status"
  echo "GET $path -> $code  bytes=$(wc -c < "$OUT/$name.json" | tr -d ' ')  sha256=$(shasum -a 256 < "$OUT/$name.json" | cut -d' ' -f1)"
}

post() { # post NAME PATH BODYFILE
  local name="$1" path="$2" body="$3" code
  code=$(curl -sk --max-time 60 -o "$OUT/$name.json" -w '%{http_code}' -X POST -H "$A" -H "$T" -H "$CT" --data-binary @"$body" "$B$path")
  local rc=$?
  if [ $rc -ne 0 ]; then echo "TRANSPORT FAILURE rc=$rc on $path" >&2; rm -f "$OUT/$name.json"; return 1; fi
  printf '%s' "$code" > "$OUT/$name.status"
  echo "POST $path -> $code  bytes=$(wc -c < "$OUT/$name.json" | tr -d ' ')  sha256=$(shasum -a 256 < "$OUT/$name.json" | cut -d' ' -f1)"
}

echo "=== health ==="
curl -sk --max-time 20 https://localhost:8443/fineract-provider/actuator/health | tee "$OUT/a2-11-health.txt"; echo

echo
echo "=== (a) re-issue GET /loanproducts/{id} ==="
get a2-11-get-loanproduct-46 /loanproducts/46
get a2-11-get-loanproduct-22 /loanproducts/22
get a2-11-get-loanproduct-28 /loanproducts/28

echo
echo "=== GL chart read-back ==="
get a2-11-get-glaccounts /glaccounts
get a2-11-get-glaccount-2 /glaccounts/2

echo
echo "=== loan product list ==="
get a2-11-get-loanproducts-list /loanproducts

echo
echo "=== journal entries for loan 5 ==="
get a2-11-get-je-loan5 '/journalentries?loanId=5&limit=200'
