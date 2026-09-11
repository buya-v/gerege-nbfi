#!/bin/bash
# OH-TBCAP-Y step 5 -- read m_trial_balance read-only (every column + count),
# and run the SQL equivalent of JournalEntryRepository.findTrialBalanceLinesForDate
# for the entry date used, as the value the tasklet would have written had :80 not thrown.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
OUT="$DIR/step05-trial-balance"
mkdir -p "$OUT"
PSQL="docker exec gerege-oracle-db psql -U postgres -d fineract_gerege"

# full table, all columns
$PSQL -c "SELECT * FROM m_trial_balance ORDER BY office_id, account_id, entry_date, created_date" > "$OUT/mtb-all-rows.txt" 2>&1
$PSQL -At -c "SELECT count(*) FROM m_trial_balance" > "$OUT/mtb-count.txt" 2>&1
$PSQL -c "\d m_trial_balance" > "$OUT/mtb-columns.txt" 2>&1

# control: journal entry count / max id vs REST
$PSQL -At -c "SELECT count(*), max(id) FROM acc_gl_journal_entry" > "$OUT/je-count-maxid.txt" 2>&1

# SQL transcription of the JPQL in JournalEntryRepository.findTrialBalanceLinesForDate (52-66)
$PSQL -c "
SELECT je.office_id,
       je.account_id,
       SUM(CASE WHEN je.type_enum = 1 THEN -1 * je.amount ELSE je.amount END) AS amount,
       je.entry_date,
       je.created_on_utc,
       SUM(je.amount) AS closing_balance
FROM acc_gl_journal_entry je
WHERE je.entry_date = DATE '2026-06-15'
GROUP BY je.office_id, je.account_id, je.entry_date, je.created_on_utc
ORDER BY je.office_id, je.account_id, je.created_on_utc" > "$OUT/equiv-query-2026-06-15.txt" 2>&1

echo "=== m_trial_balance count ==="; cat "$OUT/mtb-count.txt"
echo "=== m_trial_balance all rows ==="; cat "$OUT/mtb-all-rows.txt"
echo "=== equiv query for 2026-06-15 ==="; cat "$OUT/equiv-query-2026-06-15.txt"
echo "=== je count|maxid ==="; cat "$OUT/je-count-maxid.txt"
