#!/bin/sh
# capsql.sh NAME DBNAME SQLFILE
#
# One observation = one SQL result set, recorded verbatim, INCLUDING THE QUERY BYTES THAT
# WERE ACTUALLY EXECUTED. ADAPTED for T305 from
# .softhouse/capture/t294-openingbalance-refusal/capsql.sh. THE ONE BEHAVIOURAL DIFFERENCE
# from that file: the tenant database is an ARGUMENT rather than a fixed env var, because
# T305's whole question spans THREE databases -- `fineract_gerege` (ours), `fineract_default`
# (the other registered tenant) and `fineract_tenants` (the shared registry) -- and a rig
# that could only see one of them could not answer it. The database actually used is
# recorded in out/NAME.psql, so no observation is ambiguous about which one it came from.
#
# WHAT IS WRITTEN, on a COMPLETED execution only:
#   out/NAME.txt         the psql output, verbatim, stdout and stderr interleaved as seen
#   out/NAME.sql         the exact query bytes fed to psql -- a snapshot, not a pointer
#   out/NAME.sql.sha256  its digest, so drift is detectable
#   out/NAME.psql        the record: container, database, psql exit status, timestamp
#
# A SQL ERROR IS NOT A TRANSPORT FAILURE -- it is an observation, recorded in
# `psql-exit-status:`. `probe` establishes reachability FIRST so a non-zero rc is
# attributable to the query and not to a dead container.
#
# READ-ONLY BY CONSTRUCTION, AND CHECKED: this script REFUSES any query file containing a
# write verb. That is a content fence in the P-92 sense -- it does not depend on the
# author's intent, on a comment, or on any state outside the file's own bytes.
#
# PostgreSQL is the only database in this program (CLAUDE.md). This script names psql
# explicitly and has no other engine path.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/env.sh"

NAME=${1-}; DB=${2-}; SQLFILE=${3-}
[ -n "$NAME" ] && [ -n "$DB" ] && [ -n "$SQLFILE" ] || { echo "usage: capsql.sh NAME DBNAME SQLFILE" >&2; exit 2; }
[ -f "$DIR/$SQLFILE" ] || { echo "REFUSING: $SQLFILE does not exist -- nothing to execute and nothing to record." >&2; exit 2; }

# ---- READ-ONLY CONTENT FENCE ----------------------------------------------------------
# Strip SQL line comments first, so a write verb NAMED IN PROSE (and every query file here
# quotes source and explains itself at length) cannot trip the fence, while a write verb in
# executable position cannot hide behind one.
STRIPPED=$(sed 's/--.*$//' "$DIR/$SQLFILE")
if printf '%s\n' "$STRIPPED" | grep -qiE '(^|[^a-z_])(insert|update|delete|drop|truncate|alter|create|grant|revoke|copy|vacuum|reindex|call|do|nextval|setval)([^a-z_]|$)'; then
  echo "REFUSING: $SQLFILE contains a WRITE verb in executable position. This rig is read-only." >&2
  printf '%s\n' "$STRIPPED" | grep -inE '(^|[^a-z_])(insert|update|delete|drop|truncate|alter|create|grant|revoke|copy|vacuum|reindex|call|do|nextval|setval)([^a-z_]|$)' >&2
  exit 2
fi

TXT="$DIR/out/$NAME.txt"
SQL="$DIR/out/$NAME.sql"
SQLSHA="$DIR/out/$NAME.sql.sha256"
REC="$DIR/out/$NAME.psql"

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/capsql305.XXXXXX")
trap 'rm -rf "$TMPD"' EXIT HUP INT TERM QUIT
TMPSQL="$TMPD/query.sql"
TMPOUT="$TMPD/out.txt"

cp "$DIR/$SQLFILE" "$TMPSQL"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

probe=0
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DB" -Atc 'SELECT 1' >/dev/null 2>&1 || probe=$?
if [ "$probe" -ne 0 ]; then
  echo "TRANSPORT FAILURE: container '$DBC' / database '$DB' not reachable (probe rc=$probe) for $NAME -- NO OBSERVATION WAS MADE." >&2
  for f in "$TXT" "$SQL" "$SQLSHA" "$REC"; do
    [ -e "$f" ] && echo "  PRE-EXISTING from an EARLIER fire, left intact, NOT this fire's output: out/${f##*/}" >&2
  done
  exit 1
fi

rc=0
# -v ON_ERROR_STOP=0 is deliberate: a failing statement is data here, and the remaining
# statements are still worth executing. The failure is recorded in psql-exit-status.
docker exec -i "$DBC" psql -U "$DBUSER" -d "$DB" -f - < "$TMPSQL" > "$TMPOUT" 2>&1 || rc=$?

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
  echo "docker exec -i $DBC psql -U $DBUSER -d $DB -f -"
  echo "database: $DB"
  echo "query-file: $SQLFILE"
  echo "query-bytes-artefact: $NAME.sql"
  echo "query-sha256: $SHA"
  echo "query-bytes: $BYTES"
  echo "psql-exit-status: $rc"
  echo "captured-at-utc: $TS"
} > "$REC"
printf '%-46s db=%-18s psql exit %s\n' "$NAME" "$DB" "$rc"
