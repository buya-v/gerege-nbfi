#!/bin/sh
# T22 INDEPENDENT AUDIT — run the item-8 probes on the fresh `gerege` tenant
# (Asia/Ulaanbaatar, rounding-mode 4 = HALF_UP, PostgreSQL 18.3).
set -u
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb
R=$W/t22-audit/req
O=$W/t22-audit/out-probe
mkdir -p "$O"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

for f in p05-diycs-sarp-full p06-diycs-sarp-feb29 p07-daily-actact \
         p08-daily-360-30 p09-sarp-360-30; do
  curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" \
       -d @"$R/$f.json" -o "$O/$f-create.json"
  echo "$f -> $(cat "$O/$f-create.json")"
done

for t in p05 p06 p07 p08 p09; do
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
       -H "$A" -H "$T" -H "$CT" -d @"$R/calc-$t.json" -o "$O/$t-raw.json"
  echo "$t -> $(wc -c < "$O/$t-raw.json") bytes"
done
