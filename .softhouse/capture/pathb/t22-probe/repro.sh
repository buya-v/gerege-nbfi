#!/bin/sh
# T22 audit probe — independent re-execution of REPRODUCE.md against the running
# reference oracle (Fineract server + PostgreSQL). Creates NEW products (the
# tenant already holds Path B products 1-4), reuses the existing fixture clients
# 1 and 2, and captures the four schedules again.
#
# Usage: sh repro.sh <tag>   (tag is appended to output filenames)
set -u
TAG="${1:-repro}"
P="$(cd "$(dirname "$0")" && pwd)"

B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: default'
CT='Content-Type: application/json'

echo "== creating products =="
for f in product-1-baseline product-2-multiplesof100 \
         product-3-diycs-fullleapyear product-4-diycs-feb29only; do
  curl -sk -X POST "$B/loanproducts" -H "$A" -H "$T" -H "$CT" \
       -d @"$P/req/$f-repro.json" -o "$P/out/$f-$TAG-create.json"
  echo "$f -> $(cat "$P/out/$f-$TAG-create.json")"
done
