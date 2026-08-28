#!/usr/bin/env bash
# T409 capsql.sh -- run one committed READ-ONLY .sql against the reference oracle PostgreSQL.
# reads sql/<name>.sql ; writes out/<name>.txt and out/<name>.sql.sha256
# PostgreSQL only (CLAUDE.md). ON_ERROR_STOP=1 so a failed statement yields a non-zero rc.
set -uo pipefail
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DBC="${T409_DB_CONTAINER:-fineract-db-1}"
DBUSER="${T409_DB_USER:-root}"
DBNAME="${T409_DB_NAME:-fineract_gerege}"
n="${1:?usage: capsql.sh <name>}"
f="$DIR/sql/$n.sql"
[ -f "$f" ] || { echo "no such statement file: $f" >&2; exit 2; }
shasum -a 256 "$f" > "$DIR/out/$n.sql.sha256"
{
  echo "-- T409 $n -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "-- container=$DBC db=$DBNAME"
  echo "-- statement sha256: $(awk "{print \$1}" "$DIR/out/$n.sql.sha256")"
  echo "--"
} > "$DIR/out/$n.txt"
docker exec -i "$DBC" psql -v ON_ERROR_STOP=1 -U "$DBUSER" -d "$DBNAME" -f - < "$f" >> "$DIR/out/$n.txt" 2>&1
rc=$?
echo "-- psql rc=$rc" >> "$DIR/out/$n.txt"
exit "$rc"
