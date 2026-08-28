\pset pager off
-- Which acc_gl_journal_entry rows were NOT touched at 16:01 last night?
SELECT id, transaction_id, entry_date, created_on_utc, last_modified_on_utc,
       is_running_balance_calculated
  FROM acc_gl_journal_entry
 WHERE last_modified_on_utc IS NULL
    OR last_modified_on_utc < TIMESTAMPTZ '2026-08-28 16:00:00+00'
 ORDER BY id;
-- FALSIFIABLE PREDICTION. JournalEntryRunningBalanceUpdateServiceImpl.updateRunningBalance()
-- takes entityDate = MIN(entry_date) WHERE is_running_balance_calculated=false, then UPDATEs
-- every row with entry_date >= entityDate [426a23544, :72-76, :157, :163, :265].
SELECT (SELECT min(entry_date) FROM acc_gl_journal_entry WHERE is_running_balance_calculated=false)
         AS next_entity_date,
       (SELECT count(*) FROM acc_gl_journal_entry
         WHERE entry_date >= (SELECT min(entry_date) FROM acc_gl_journal_entry
                               WHERE is_running_balance_calculated=false))
         AS rows_the_next_00_01_run_will_UPDATE,
       (SELECT count(*) FROM acc_gl_journal_entry) AS rows_total;
