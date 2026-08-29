\echo === S05.1 the MODIFIED cohort only: the exact window of last_modified_on_utc ===
SELECT count(*) AS n, min(last_modified_on_utc) AS lo, max(last_modified_on_utc) AS hi,
       count(DISTINCT last_modified_by) AS distinct_modifiers
FROM acc_gl_journal_entry WHERE last_modified_on_utc > created_on_utc;

\echo === S05.2 job 9 last run window, for the bracketing argument ===
SELECT h.id, h.job_id, h.start_time, h.end_time, h.status, h.trigger_type
FROM job_run_history h WHERE h.job_id = 9 ORDER BY h.id DESC LIMIT 1;

\echo === S05.3 every job whose last run window CONTAINS the modified window ===
SELECT h.job_id, j.display_name, h.start_time, h.end_time
FROM job_run_history h JOIN job j ON j.id = h.job_id
WHERE h.start_time <= timestamp '2026-08-28 16:01:00.033938'
  AND h.end_time   >= timestamp '2026-08-28 16:01:00.037287'
ORDER BY h.start_time;

\echo === S05.4 the LEGACY audit pair: did created_date / lastmodified_date move too? ===
SELECT count(*) AS total,
       count(created_date) AS created_date_notnull,
       count(lastmodified_date) AS lastmodified_date_notnull,
       count(*) FILTER (WHERE lastmodified_date > created_date) AS legacy_moved
FROM acc_gl_journal_entry;

\echo === S05.5 command source: is there ANY command row for the running-balance update? ===
SELECT count(*) AS total_command_rows FROM m_portfolio_command_source;
SELECT action_name, entity_name, count(*) AS n FROM m_portfolio_command_source
GROUP BY 1,2 ORDER BY 3 DESC LIMIT 20;

\echo === S05.6 the trial-balance table job 30 writes, and the annual summary job 40 writes ===
SELECT count(*) AS m_trial_balance_rows FROM m_trial_balance;
SELECT count(*) AS annual_summary_rows FROM acc_gl_journal_entry_annual_summary;

\echo === S05.7 acc_gl_journal_entry_annual_summary columns ===
SELECT ordinal_position, column_name, data_type FROM information_schema.columns
WHERE table_schema='public' AND table_name='acc_gl_journal_entry_annual_summary' ORDER BY 1;

\echo === S05.8 m_trial_balance columns ===
SELECT ordinal_position, column_name, data_type FROM information_schema.columns
WHERE table_schema='public' AND table_name='m_trial_balance' ORDER BY 1;

\echo === S05.9 the money and structure columns of every posted row, unchanged since capture? ===
SELECT id, transaction_id, account_id, type_enum, amount, currency_code, office_id,
       reversed, reversal_id, manual_entry, entity_type_enum, entity_id, entry_date
FROM acc_gl_journal_entry WHERE transaction_id IN ('L29','L30','L32') ORDER BY id;
