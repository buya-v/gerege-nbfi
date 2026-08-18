#!/bin/sh
# T22 audit: re-execute the four committed Path B calc requests VERBATIM against
# the existing `default` tenant (products 1-4 already exist there).
set -u
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-acea9b5e2faae26c3/.softhouse/capture/pathb
O=$W/t22-audit/out-rerun-default
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: default'
CT='Content-Type: application/json'
for n in 01 02 03 04; do
  case $n in 01) f=calc-B-01-baseline;;           02) f=calc-B-02-multiplesof100;;
             03) f=calc-B-03-diycs-fullleapyear;; 04) f=calc-B-04-diycs-feb29only;; esac
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
    -H "$A" -H "$T" -H "$CT" -d @"$W/req/$f.json" -o "$O/B-$n-raw.json"
  echo "B-$n -> $(wc -c < "$O/B-$n-raw.json") bytes"
done
