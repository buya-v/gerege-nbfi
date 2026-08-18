#!/bin/sh
# T22 audit probe — re-capture the four Path B schedules from the running oracle.
# Usage: sh capture.sh <tag>
set -u
TAG="${1:-repro}"
P="$(cd "$(dirname "$0")" && pwd)"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: default'
CT='Content-Type: application/json'

for f in calc-B-01-baseline calc-B-02-multiplesof100 \
         calc-B-03-diycs-fullleapyear calc-B-04-diycs-feb29only; do
  curl -sk -X POST "$B/loans?command=calculateLoanSchedule" \
       -H "$A" -H "$T" -H "$CT" -d @"$P/req/$f-repro.json" \
       -o "$P/out/$f-$TAG-raw.json"
  echo "$f -> $(wc -c < "$P/out/$f-$TAG-raw.json") bytes"
done
