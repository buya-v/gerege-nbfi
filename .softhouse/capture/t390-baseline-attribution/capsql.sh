#!/usr/bin/env bash
# T390 capsql.sh -- run one committed READ-ONLY .sql against the standing reference oracle's
# PostgreSQL and commit both the statement's sha256 and the output.
#
#   bash .softhouse/capture/t390-baseline-attribution/capsql.sh <name>
#
# reads  sql/<name>.sql   writes  out/<name>.txt  and  out/<name>.sql.sha256
#
# PostgreSQL only (CLAUDE.md). No other engine path exists here.
set -uo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DBC="${T390_DB_CONTAINER:-fineract-db-1}"
DBUSER="${T390_DB_USER:-root}"
DBNAME="${T390_DB_NAME:-fineract_gerege}"

n="${1:?usage: capsql.sh <name>}"
f="$DIR/sql/$n.sql"
[ -f "$f" ] || { echo "no such statement file: $f" >&2; exit 2; }

shasum -a 256 "$f" > "$DIR/out/$n.sql.sha256"
{
  echo "-- T390 $n -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "-- container=$DBC db=$DBNAME"
  echo "-- statement sha256: $(awk '{print $1}' "$DIR/out/$n.sql.sha256")"
  echo "--"
} > "$DIR/out/$n.txt"
# ON_ERROR_STOP=1 -- without it psql exits 0 on a failed statement and a broken query looks
# like a successful capture. Driven: the first run of q1 named a non-existent column, printed
# ERROR, and still reported rc=0.
docker exec -i "$DBC" psql -v ON_ERROR_STOP=1 -U "$DBUSER" -d "$DBNAME" -f - < "$f" >> "$DIR/out/$n.txt" 2>&1
rc=$?
echo "-- psql rc=$rc" >> "$DIR/out/$n.txt"
exit "$rc"
