#!/bin/sh
# T55 -- determinism.  Re-post every committed request VERBATIM and byte-compare the response
# against the committed capture.  A capture that is not reproducible is not an observation of a
# deterministic oracle, and a vector store built on it would drift silently.
#
# Re-posts the SAME committed request files -- it does not re-author them, so a change in the
# authoring code cannot hide here.  Additive: calculateLoanSchedule persists nothing.
set -eu

W="$(cd "$(dirname "$0")/../../../.." && pwd)"
LB=$W/.softhouse/capture/leapboundary
B=https://localhost:8443/fineract-provider/api/v1
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
T='Fineract-Platform-TenantId: gerege'
CT='Content-Type: application/json'
O=$LB/out
D=$LB/out/rerun
mkdir -p "$D"

echo "== T55 determinism re-run =="
n=0; diffs=0
for f in "$LB"/req/calc-LB-*.json; do
  nm=$(basename "$f" .json); nm=${nm#calc-}
  code=$(curl -sk -X POST "$B/loans?command=calculateLoanSchedule" -H "$A" -H "$T" -H "$CT" \
           -d @"$f" -o "$D/$nm-raw.json" -w '%{http_code}')
  [ "$code" = "200" ] || { echo "BREACH: $nm re-run returned HTTP $code" >&2; exit 1; }
  n=$((n+1))
  if cmp -s "$O/$nm-raw.json" "$D/$nm-raw.json"; then
    :
  else
    echo "  DIFFERS: $nm" >&2
    diffs=$((diffs+1))
  fi
done

echo "  $n re-posted, $diffs byte-differences"
[ "$diffs" = "0" ] || { echo "BREACH: $diffs of $n responses are not byte-identical on re-post" >&2; exit 1; }

LOANS=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(*) from m_loan;")
[ "$LOANS" = "0" ] || { echo "BREACH: m_loan is $LOANS after the re-run, expected 0" >&2; exit 1; }
echo "  ok  m_loan still 0"
echo "== PASS -- all $n responses byte-identical on re-post =="
