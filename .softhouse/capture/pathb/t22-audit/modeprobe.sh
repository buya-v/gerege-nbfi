#!/bin/sh
# T22 INDEPENDENT AUDIT — same product, same request, two tenants that differ ONLY
# in c_configuration `rounding-mode`:
#   default : Asia/Kolkata,     rounding-mode 6 = HALF_EVEN   (what Path B was captured at)
#   gerege  : Asia/Ulaanbaatar, rounding-mode 4 = HALF_UP     (the ratified Gerege setting)
set -u
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb
R=$W/t22-audit/req
O=$W/t22-audit/out-modeprobe
mkdir -p "$O"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
CT='Content-Type: application/json'

for t in gerege default; do
  curl -sk -X POST "$B/loanproducts" -H "$A" -H "Fineract-Platform-TenantId: $t" -H "$CT" \
       -d @"$R/pmode-mult1.json" -o "$O/product-$t-create.json"
  echo "$t product -> $(cat "$O/product-$t-create.json")"
done

for t in gerege default; do
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
       -H "$A" -H "Fineract-Platform-TenantId: $t" -H "$CT" \
       -d @"$R/calc-pmode-$t.json" -o "$O/pmode-$t-raw.json"
  echo "$t capture -> $(wc -c < "$O/pmode-$t-raw.json") bytes"
done
