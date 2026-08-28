#!/bin/sh
# capsql.sh NAME SQLFILE
#
# T275. One observation = one SQL result set, recorded verbatim, INCLUDING THE QUERY BYTES
# THAT WERE ACTUALLY EXECUTED.
#
# WHY THIS EXISTS
# ---------------
# Every DB snapshot in this corpus before T275 was taken by hand:
#
#     docker exec -i fineract-db-1 psql -U root -d fineract_gerege -f - < sql/qN.sql > out/A2-nnn.txt
#
# (CAPTURE-PLAN.md §6). That has the exact shape of defect D-1 in
# DEFECTS-FOUND-BY-REVIEW.md: the artefact under out/ carries NO record of which query
# produced it, so a later edit to sql/qN.sql silently invalidates the recipe and nothing
# goes red. D-1 is the same defect on the HTTP side -- `body-file:` pointed at a req/ file
# that mkreq2.py had since overwritten -- and it cost this directory 10 provably-false
# recipes. cap8.sh closed it for HTTP by committing the wire bytes as out/NAME.req; this
# closes it for SQL by committing the executed bytes as out/NAME.sql.
#
# WHAT IS WRITTEN, on a COMPLETED execution only:
#   out/NAME.txt         the psql output, verbatim, stdout and stderr interleaved as seen
#   out/NAME.sql         the exact query bytes fed to psql -- a snapshot, not a pointer
#   out/NAME.sql.sha256  its digest, so MANIFEST.sha256 covers it and drift is detectable
#   out/NAME.psql        the record: container, tenant database, psql exit status, timestamp
#
# FAILURE DISCIPLINE, carried over from cap8.sh's D-2 fix:
#   * The query is snapshotted to a temp dir BEFORE execution and moved into place only
#     AFTER psql returns, so nothing under out/ can ever carry a fresh timestamp on stale
#     bytes.
#   * `docker exec` failing (container gone, database gone, bad credentials) means NO
#     OBSERVATION WAS MADE. Nothing is written under out/, any pre-existing artefact from
#     an earlier fire is NAMED and LEFT INTACT rather than overwritten, and the script
#     exits non-zero so a `|| exit 1` caller stops.
#   * A SQL ERROR is NOT a transport failure. psql exits non-zero on a bad query, and that
#     refusal is an observation exactly as an HTTP 4xx is: it is recorded as data in
#     out/NAME.psql (`psql-exit-status:`) and the output is kept. The two cases are
#     distinguished by whether `docker exec` itself could run at all.
#
# PostgreSQL is the only database in this program (CLAUDE.md). This script names psql
# explicitly and has no other engine path.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)

NAME=${1-}; SQLFILE=${2-}
[ -n "$NAME" ] && [ -n "$SQLFILE" ] || { echo "usage: capsql.sh NAME SQLFILE" >&2; exit 2; }
[ -f "$DIR/$SQLFILE" ] || { echo "REFUSING: $SQLFILE does not exist -- nothing to execute and nothing to record." >&2; exit 2; }

DBC=fineract-db-1
DBUSER=root
DBNAME=fineract_gerege

TXT="$DIR/out/$NAME.txt"
SQL="$DIR/out/$NAME.sql"
SQLSHA="$DIR/out/$NAME.sql.sha256"
REC="$DIR/out/$NAME.psql"

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/capsql.XXXXXX")
# EXIT HUP INT TERM QUIT -- QUIT included for the same reason cap10.sh added it (T216/T236):
# bash does not run the EXIT trap for an untrapped SIGQUIT, so Ctrl-\ mid-capture would
# otherwise leak this scratch dir.
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM QUIT
TMPSQL="$TMPD/query.sql"
TMPOUT="$TMPD/out.txt"

cp "$DIR/$SQLFILE" "$TMPSQL"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# `docker exec` propagates psql's exit status, so rc alone cannot tell a dead container
# from a bad query. `probe` establishes that the container and database are reachable
# FIRST; only then is a non-zero rc attributable to the query itself.
probe=0
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -Atc 'SELECT 1' >/dev/null 2>&1 || probe=$?
if [ "$probe" -ne 0 ]; then
  echo "TRANSPORT FAILURE: container '$DBC' / database '$DBNAME' not reachable (probe rc=$probe) for $NAME -- NO OBSERVATION WAS MADE." >&2
  echo "  NOTHING was written under out/ for $NAME by this fire." >&2
  for f in "$TXT" "$SQL" "$SQLSHA" "$REC"; do
    if [ -e "$f" ]; then
      echo "  PRE-EXISTING from an EARLIER fire, left intact, NOT this fire's output: out/${f##*/}" >&2
    fi
  done
  if [ -e "$REC" ]; then
    echo "  that earlier artefact's own captured-at-utc: $(sed -n 's/^captured-at-utc: //p' "$REC")" >&2
  fi
  exit 1
fi

rc=0
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DBNAME" -f - < "$TMPSQL" > "$TMPOUT" 2>&1 || rc=$?

# The execution completed (the engine answered). Commit the observation.
if command -v shasum >/dev/null 2>&1; then
  SHA=$(shasum -a 256 "$TMPSQL" | awk '{print $1}')
else
  SHA=$(sha256sum "$TMPSQL" | awk '{print $1}')
fi
BYTES=$(wc -c < "$TMPSQL" | tr -d ' ')
mv "$TMPOUT" "$TXT"
mv "$TMPSQL" "$SQL"
printf '%s  %s\n' "$SHA" "$NAME.sql" > "$SQLSHA"
{
  echo "docker exec -i $DBC psql -U $DBUSER -d $DBNAME -f -"
  echo "tenant-database: $DBNAME"
  echo "query-file: $SQLFILE"
  echo "query-bytes-artefact: $NAME.sql"
  echo "query-sha256: $SHA"
  echo "query-bytes: $BYTES"
  echo "psql-exit-status: $rc"
  echo "captured-at-utc: $TS"
} > "$REC"
printf '%-44s psql exit %s\n' "$NAME" "$rc"
