#!/bin/sh
# T421 capsql-readonly.sh NAME SQLFILE  -- a COPY of T391's, not a `.` of it.
#
# T421's mutation budget for the reference oracle is ZERO. This scans the query
# bytes ACTUALLY ABOUT TO BE EXECUTED for statement keywords that could move
# state, and exits 2 BEFORE psql is invoked. It is driven RED by
# bin/40-red-drive-readonly-guard.sh, because a guard nobody has watched fail
# enforces nothing (P-45).
#
# WHAT IT DELIBERATELY DOES NOT DO: it is not a SQL parser and does not claim to
# make arbitrary input safe. It is a guard on THIS rig's own queries, whose
# author is this task.
#
# Records, on a COMPLETED execution only:
#   out/NAME.txt   psql output verbatim (stdout and stderr as seen)
#   out/NAME.sql   the exact bytes executed -- a snapshot, not a pointer
#   out/NAME.psql  container / database / psql exit status / captured-at-utc
set -e
NAME="$1"
SQLFILE="$2"
if [ -z "$NAME" ] || [ -z "$SQLFILE" ]; then
  echo "usage: capsql-readonly.sh NAME SQLFILE" >&2
  exit 64
fi
if [ ! -f "$SQLFILE" ]; then
  echo "no such SQL file: $SQLFILE" >&2
  exit 64
fi

DIR=$(dirname "$0")
OUT="$DIR/out"
mkdir -p "$OUT"
CONTAINER=fineract-db-1
DB=fineract_gerege
DBUSER=root

# --- WRITE-STATEMENT REFUSAL ------------------------------------------------
# Executable text only: -- comments and /* */ blocks are stripped first, so a
# write hidden on a line after a comment marker cannot slip past on the strength
# of the marker.
EXEC=$(sed 's|--.*$||' "$SQLFILE" | tr '\n' ' ' | sed 's:/\*[^*]*\*/: :g')
for KW in INSERT UPDATE DELETE DROP TRUNCATE ALTER CREATE GRANT REVOKE MERGE \
          COPY VACUUM REINDEX CLUSTER REFRESH CALL DO SET COMMIT ROLLBACK; do
  if printf '%s' "$EXEC" | tr 'a-z' 'A-Z' | grep -qw "$KW"; then
    echo "REFUSED: executable SQL contains the write/state keyword '$KW'." >&2
    echo "         T421 is read-only against the reference oracle." >&2
    echo "         NOTHING WAS EXECUTED." >&2
    exit 2
  fi
done
# ---------------------------------------------------------------------------

TMP=$(mktemp)
cp "$SQLFILE" "$TMP"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
set +e
docker exec -i "$CONTAINER" psql -U "$DBUSER" -d "$DB" -f - < "$TMP" > "$OUT/$NAME.txt" 2>&1
RC=$?
set -e
if [ ! -s "$OUT/$NAME.txt" ] && [ "$RC" -ne 0 ]; then
  echo "TRANSPORT FAILURE (rc=$RC): NO OBSERVATION WAS MADE; nothing written." >&2
  rm -f "$TMP" "$OUT/$NAME.txt"
  exit 1
fi
mv "$TMP" "$OUT/$NAME.sql"
{
  echo "record-kind: sql"
  echo "case-id: $NAME"
  echo "container: $CONTAINER"
  echo "database: $DB"
  echo "db-user: $DBUSER"
  echo "psql-exit-status: $RC"
  echo "query-sha256: $(shasum -a 256 "$OUT/$NAME.sql" | cut -d' ' -f1)"
  echo "captured-at-utc: $TS"
} > "$OUT/$NAME.psql"
echo "captured $NAME (psql exit $RC) at $TS"
