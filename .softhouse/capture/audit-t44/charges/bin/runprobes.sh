#!/bin/sh
# T44 audit leg (charges) — issue the four discrimination probes against the LIVE oracle.
# Additive only: /loans?command=calculateLoanSchedule persists nothing (T40 verified m_loan=0
# and this audit re-verifies it after the run). PostgreSQL only.
set -u

AUD=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/audit-t44/charges
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
O=$AUD/out/probes
mkdir -p "$O"

for f in "$AUD"/req/calc-AP-*.json; do
  n=$(basename "$f" .json); n=${n#calc-}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$O/$n-raw.json" -w '%{http_code}')
  echo "HTTP $code  $n  ->  $(shasum -a 256 "$O/$n-raw.json" | awk '{print $1}')"
done
