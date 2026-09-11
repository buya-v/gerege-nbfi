#!/bin/bash
# OH-TBCAP-Y step 0b -- READ-ONLY controls. Proves the SQL read is the live oracle,
# and pins the columns the trial-balance query actually reads.
set -u
DIR=$(cd "$(dirname "$0")/.." && pwd)
RAW="$DIR/raw"
PSQL="docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -At -c"
q() { $PSQL "$2" > "$1" 2> "$1.err"; }

# Control: SQL max id MUST equal max id in GET /journalentries (140). See tools README.
q "$RAW/00-control-sql-vs-rest.txt" \
  "SELECT (SELECT max(id) FROM acc_gl_journal_entry) AS sql_max_id, (SELECT count(*) FROM acc_gl_journal_entry) AS sql_count;"

# JournalEntry.transactionDate maps to entry_date; JournalEntry.createdDate maps to created_on_utc.
q "$RAW/00-je-transaction-date-column.txt" \
  "SELECT count(*) AS rows, count(transaction_date) AS non_null_transaction_date FROM acc_gl_journal_entry;"
q "$RAW/00-je-created-on-utc-nullcount.txt" \
  "SELECT count(*) AS rows, count(created_on_utc) AS non_null_created_on_utc, count(created_date) AS non_null_created_date FROM acc_gl_journal_entry;"

# findMaxCreatedDate equivalent: MAX(transactionDate) on m_trial_balance -> NULL on empty.
q "$RAW/00-mtb-max-created-date.txt" "SELECT max(created_date) FROM m_trial_balance;"

# reversed / reversal_id state before any write.
q "$RAW/00-je-reversed-counts.txt" \
  "SELECT reversed, count(*), count(reversal_id) FROM acc_gl_journal_entry GROUP BY reversed ORDER BY reversed;"

echo "step00b done"
