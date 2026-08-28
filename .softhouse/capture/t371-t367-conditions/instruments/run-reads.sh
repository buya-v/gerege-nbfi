#!/usr/bin/env bash
# run-reads.sh -- T371's READ-ONLY derivation against the live reference oracle (Fineract).
#
#   bash .softhouse/capture/t371-t367-conditions/instruments/run-reads.sh
#
# EVERY STATEMENT IT ISSUES IS A `SELECT`. It opens with a read of the append-only max ids and
# closes with the same read, so the transcript itself attests that T371 did not move the oracle.
# It fires NO PROBE. `PROBES.tsv` therefore needs no row for T371 -- and that is not a promise,
# it is checkable from the OPENING/CLOSING pair at the top and bottom of every output file.
#
# WHY THIS MATTERS MORE THAN IT USED TO: T367 established that a 4xx BURNS the idempotency key,
# because `saveInitial` precedes handler dispatch. A REFUSED probe is as irreversible as an
# accepted one. There is no "safe" write to this tenant, not even a rejected one.
set -uo pipefail
[ -n "${BASH_VERSION:-}" ] || { echo "run with bash, not sh"; exit 3; }
ROOT=$(git rev-parse --show-toplevel) || exit 2
DIR="$ROOT/.softhouse/capture/t371-t367-conditions"
DB=${T371_DB_CONTAINER:-fineract-db-1}
TENANTDB=${T371_TENANT_DB:-fineract_gerege}

q() { # q <sql-file> <out-file>
  local rc
  docker exec -i "$DB" psql -U root -d "$TENANTDB" -f - < "$1" > "$2" 2>&1; rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "READ FAILED (rc=$rc) on $1 -- the tenant database is unreachable or the query errored." >&2
    echo "  This is NOT a statement about the oracle's state. See $2." >&2
    return 2
  fi
  # a psql that connected but errored still exits 0 under some invocations; catch it explicitly
  if grep -q '^psql:.*ERROR' "$2"; then
    echo "READ ERRORED inside psql on $1 -- see $2. No negative from this run is interpretable." >&2
    return 2
  fi
  echo "ok  $1 -> $2"
}

rc=0
{ echo "T371 OPENING READ  $(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$DIR/out/Q1-OPENING.txt"
q "$DIR/sql/q1-opening-read.sql" "$DIR/out/Q1-OPENING.tmp" || rc=2
cat "$DIR/out/Q1-OPENING.tmp" >> "$DIR/out/Q1-OPENING.txt" 2>/dev/null; rm -f "$DIR/out/Q1-OPENING.tmp"

q "$DIR/sql/q2-status-split.sql"          "$DIR/out/Q2-STATUS-SPLIT.txt"  || rc=2
q "$DIR/sql/q3-key-naming.sql"            "$DIR/out/Q3-KEY-NAMING.txt"    || rc=2
q "$DIR/sql/q4-instrument-blindspots.sql" "$DIR/out/Q4-BLINDSPOTS.txt"    || rc=2

{ echo "T371 CLOSING READ  $(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$DIR/out/Q5-CLOSING.txt"
q "$DIR/sql/q1-opening-read.sql" "$DIR/out/Q5-CLOSING.tmp" || rc=2
cat "$DIR/out/Q5-CLOSING.tmp" >> "$DIR/out/Q5-CLOSING.txt" 2>/dev/null; rm -f "$DIR/out/Q5-CLOSING.tmp"

echo
echo "OPENING vs CLOSING -- if these differ, something moved the oracle DURING this read:"
if diff <(grep -E 'je_|cs_|closure_' "$DIR/out/Q1-OPENING.txt") \
        <(grep -E 'je_|cs_|closure_' "$DIR/out/Q5-CLOSING.txt") > /dev/null 2>&1; then
  echo "  IDENTICAL. T371 fired no probe."
else
  echo "  *** DIFFERENT. Do not treat this run as read-only evidence."
  rc=1
fi
exit "$rc"
