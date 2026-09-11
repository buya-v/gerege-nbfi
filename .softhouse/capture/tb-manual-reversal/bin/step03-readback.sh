#!/bin/bash
# OH-TBCAP-Y step 3 -- read back BOTH transaction ids via REST and SQL.
# SQL is read-only; oracle db is gerege-oracle-db, never fineract-db-1 / default.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
source "$DIR/bin/rest.sh"

ORIG="a2b795dca42b"
REV="a2b7964aa51b"
OUT="$DIR/step03-readback"
mkdir -p "$OUT"
PSQL="docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -At -c"

rest_get "$OUT/rest-orig.json" "/journalentries?transactionId=$ORIG"
rest_get "$OUT/rest-rev.json"  "/journalentries?transactionId=$REV"
echo "REST orig $(cat "$OUT/rest-orig.json.status"), rev $(cat "$OUT/rest-rev.json.status")"

$PSQL "SELECT id, office_id, account_id, transaction_id, entry_date, type_enum, amount, manual_entry, reversed, reversal_id FROM acc_gl_journal_entry WHERE transaction_id IN ('$ORIG','$REV') ORDER BY id" > "$OUT/sql-rows.txt" 2> "$OUT/sql-rows.txt.err"
$PSQL "SELECT count(*), max(id) FROM acc_gl_journal_entry" > "$OUT/sql-control-count-maxid.txt"

echo "--- SQL rows (both txn ids) ---"
cat "$OUT/sql-rows.txt"
echo "--- control count|maxid ---"
cat "$OUT/sql-control-count-maxid.txt"
