\echo '== s3a: ledger counters NOW -- compare against T409 out/r18 (109/113, 38, 379/379, m_loan 8) =='
SELECT 'acc_gl_journal_entry rows/maxid' AS k, count(*)||'/'||coalesce(max(id)::text,'null') AS v FROM acc_gl_journal_entry
UNION ALL SELECT 'distinct transaction_id', count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry
UNION ALL SELECT 'acc_gl_closure rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure
UNION ALL SELECT 'm_portfolio_command_source rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source
UNION ALL SELECT 'm_loan rows', count(*)::text FROM m_loan
UNION ALL SELECT 'm_office rows', count(*)::text FROM m_office
UNION ALL SELECT 'max created_on_utc', max(created_on_utc)::text FROM acc_gl_journal_entry
UNION ALL SELECT 'max last_modified_on_utc', max(last_modified_on_utc)::text FROM acc_gl_journal_entry;

\echo '== s3b: T409 mutation proof, re-derived =='
SELECT count(*) FILTER (WHERE created_on_utc < timestamptz '2026-08-28 16:00:00+00'
                          AND last_modified_on_utc >= timestamptz '2026-08-28 16:00:00+00') AS created_before_modified_after,
       count(*) FILTER (WHERE last_modified_on_utc > created_on_utc) AS modified_after_create,
       min(created_on_utc) FILTER (WHERE last_modified_on_utc > created_on_utc) AS oldest_mutated_created,
       min(last_modified_on_utc) FILTER (WHERE last_modified_on_utc > created_on_utc) AS mutation_first,
       max(last_modified_on_utc) FILTER (WHERE last_modified_on_utc > created_on_utc) AS mutation_last,
       string_agg(DISTINCT last_modified_by::text, ',') AS modifier_ids,
       string_agg(DISTINCT created_by::text, ',') AS creator_ids
FROM acc_gl_journal_entry;

\echo '== s3c: T409 prediction state -- next job-9 sweep size =='
SELECT min(entry_date) AS min_uncalculated_entry_date,
       count(*) FILTER (WHERE NOT is_running_balance_calculated) AS uncalculated_rows
FROM acc_gl_journal_entry;
SELECT count(*) AS rows_at_or_after_min_uncalculated
FROM acc_gl_journal_entry
WHERE entry_date >= (SELECT min(entry_date) FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated);

\echo '== s3d: distinct users on the ledger table -- the trap, measured =='
SELECT 'distinct created_by' AS k, string_agg(DISTINCT created_by::text, ',') AS v FROM acc_gl_journal_entry
UNION ALL SELECT 'distinct last_modified_by', string_agg(DISTINCT last_modified_by::text, ',') FROM acc_gl_journal_entry;

\echo '== s3e: m_appuser =='
SELECT id, username, firstname, lastname, is_deleted FROM m_appuser ORDER BY id;
