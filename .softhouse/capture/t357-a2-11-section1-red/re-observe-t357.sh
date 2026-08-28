#!/bin/bash
# T357 — INDEPENDENT re-observation of the reads that A2-11's check-shape.py replays,
# taken from the LIVE reference oracle (Fineract) on fire 20260828-140005.
#
# WHY THIS EXISTS. check-shape.py section 1 is RED with three named failures
# (paymentChannelToFundSourceMappings / feeToIncomeAccountMappings /
# penaltyToIncomeAccountMappings "present and null" -> observed '<absent>').
# Adjudicating those three requires answering "is the FAIL a defect in the OBSERVED
# EVIDENCE (stale or corrupt obs bytes) or a defect in the CHECKER (a false
# expectation)?" That question cannot be answered by replaying the same obs bytes,
# so this rig goes back to the oracle and observes afresh. Nothing is synthesised;
# every byte under out/ is what the oracle returned.
#
# WRITES ONLY under this rig's own out/. It does NOT touch
# .softhouse/reviews/A2-11/obs/, because those bytes are A2-11's committed evidence
# and overwriting them would destroy the artefact under adjudication.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/out"
mkdir -p "$OUT"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'

get() { # get NAME PATH
  local name="$1" path="$2" code rc
  code=$(curl -sk --max-time 60 -o "$OUT/$name.json" -w '%{http_code}' -H "$A" -H "$T" "$B$path")
  rc=$?
  if [ $rc -ne 0 ]; then echo "TRANSPORT FAILURE rc=$rc on $path" >&2; rm -f "$OUT/$name.json"; return 1; fi
  printf '%s' "$code" > "$OUT/$name.status"
  echo "GET $path -> $code  bytes=$(wc -c < "$OUT/$name.json" | tr -d ' ')  sha256=$(shasum -a 256 < "$OUT/$name.json" | cut -d' ' -f1)"
}

echo "=== provenance ==="
echo "captured_by      T357 (fire 20260828-140005)"
echo "captured_at      $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "oracle_base      $B"
echo "tenant           gerege"
echo "oracle_health    $(curl -sk --max-time 20 https://localhost:8443/fineract-provider/actuator/health)"
echo

echo "=== the three loan-product reads check-shape.py replays ==="
get t357-get-loanproduct-46 /loanproducts/46
get t357-get-loanproduct-22 /loanproducts/22
get t357-get-loanproduct-28 /loanproducts/28
echo
echo "=== the GL read check-shape.py replays ==="
get t357-get-glaccount-2 /glaccounts/2
echo
echo "=== the product list check-shape.py replays ==="
get t357-get-loanproducts-list /loanproducts
