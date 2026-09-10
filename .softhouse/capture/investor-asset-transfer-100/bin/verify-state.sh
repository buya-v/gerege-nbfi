#!/usr/bin/env bash
# OH-INV-Y step 1 — verify the inherited state. Read-only REST reads.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "$HERE/lib.sh"

curl -sk -o "$OUT/health-check.json" -w '%{http_code}' \
    'https://localhost:8443/fineract-provider/actuator/health' > "$OUT/health-check.status"
printf 'GET  %-52s -> %s\n' '/actuator/health' "$(cat "$OUT/health-check.status")"

cap_get businessdate              "/businessdate"
cap_get transfer-17-loan-12       "/external-asset-owners/transfers/17?loanId=12"
cap_get transfers-loan-12         "/external-asset-owners/transfers?loanId=12"
cap_get transfer-17-je            "/external-asset-owners/transfers/17/journal-entries?loanId=12"
cap_get financialactivityaccounts "/financialactivityaccounts"
cap_get glaccount-6               "/glaccounts/6"
cap_get glaccounts-raw            "/glaccounts"
cap_get loan-12-raw               "/loans/12"
cap_get loanproduct-3-raw         "/loanproducts/3"
cap_get cob-steps-raw             "/jobs/LOAN_CLOSE_OF_BUSINESS/steps"

echo "--- inherited-state summary ---"
python3 - "$OUT" <<'PY'
import json, sys, os
d = sys.argv[1]
def load(n):
    try:
        return json.load(open(os.path.join(d, n)))
    except Exception as e:
        return {"_err": str(e)}
t = load("transfer-17-loan-12.json")
print("transfer17:", {k: t.get(k) for k in ("transferId","status","purchasePriceRatio","settlementDate","loan","transferExternalId")})
print("JE17:", open(os.path.join(d,"transfer-17-je.json")).read()[:200])
fa = load("financialactivityaccounts.json")
print("finActivities:", [(x.get("id"), x.get("financialActivity",{}).get("id"), x.get("glAccount",{}).get("id"), x.get("glAccount",{}).get("name")) for x in fa] if isinstance(fa,list) else fa)
gl6 = load("glaccount-6.json")
print("gl6:", {k: gl6.get(k) for k in ("id","name","glCode","type","usage")})
l = load("loan-12-raw.json")
print("loan12:", {k: l.get(k) for k in ("id","productId","status","principal","totalOutstanding","totalOverpaid","totalInterestChargesDue")})
PY
