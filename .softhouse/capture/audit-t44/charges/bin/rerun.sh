#!/bin/sh
# T44 audit leg (charges) — INDEPENDENT re-issue of a sample of T40's committed requests
# against the LIVE reference oracle (Fineract), tenant `gerege`.
#
# Reads the committed request files BYTE-VERBATIM (-d @file); writes only under the audit
# write surface. Additive only: /loans?command=calculateLoanSchedule persists nothing.
# PostgreSQL is the only engine. No float touches money anywhere in this script.
set -u

AUD=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/audit-t44/charges
SH=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'

O=$AUD/out/rerun
mkdir -p "$O"

post() {
  _req=$1; _out=$2
  _code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
            -H "$A" -H "$T" -H "$CT" -d @"$_req" -o "$_out" -w '%{http_code}')
  echo "HTTP $_code  $(basename "$_req")  ->  $(shasum -a 256 "$_out" | awk '{print $1}')"
}

echo "== T44 audit re-run against the live oracle =="
date -u +'%Y-%m-%dT%H:%M:%SZ'
echo

echo "-- CTRL-B-01 (committed Path B control request, byte-verbatim) --"
post "$SH/capture/pathb/req/calc-B-01-baseline.json" "$O/CTRL-B-01-raw.json"
echo

echo "-- sampled T40 charge requests, byte-verbatim --"
for n in FC-01-flat-disbursement FC-04-pctinterest-instalment FC-05-pctamountinterest-instalment \
         FC-11-fee-on-disbursement-date FC-15-combined-fee-and-penalty FC-17-fee-after-final-duedate \
         FC-19-pctinterest-sdd-inside-p6 FC-20-pctinterest-sdd-on-disb FC-21-pctamtint-sdd-inside-p6 \
         FC-22-penalty-instalment-plus-sdd-on-p3-duedate; do
  post "$SH/capture/charges/req/calc-$n.json" "$O/$n-raw.json"
done
echo

echo "-- XR-01 refusal (expected NON-200) --"
post "$SH/capture/charges/req/calc-XR-01-fee-before-disbursement.json" "$O/XR-01-raw.json"
echo

echo "== committed digests, for comparison =="
shasum -a 256 "$SH/capture/charges/out/control/B-01-baseline-raw.json"
for n in FC-01-flat-disbursement FC-04-pctinterest-instalment FC-05-pctamountinterest-instalment \
         FC-11-fee-on-disbursement-date FC-15-combined-fee-and-penalty FC-17-fee-after-final-duedate \
         FC-19-pctinterest-sdd-inside-p6 FC-20-pctinterest-sdd-on-disb FC-21-pctamtint-sdd-inside-p6 \
         FC-22-penalty-instalment-plus-sdd-on-p3-duedate; do
  shasum -a 256 "$SH/capture/charges/out/fc/$n-raw.json"
done
