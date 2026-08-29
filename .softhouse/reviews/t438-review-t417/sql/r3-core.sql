\pset footer off
\echo '== j1: job cardinals =='
SELECT count(*) AS job_rows, count(*) FILTER (WHERE is_active) AS active, count(*) FILTER (WHERE NOT is_active) AS inactive FROM job;
\echo '== j2: distinct jobs that ran in the last 24h =='
SELECT count(DISTINCT job_id) AS distinct_jobs_24h FROM job_run_history WHERE start_time >= (now() AT TIME ZONE 'UTC') - interval '24 hours';
\echo '== j3: job 36 cadence =='
SELECT id, name, is_active, cron_expression, currently_running FROM job WHERE id=36;
SELECT count(*) AS job36_alltime FROM job_run_history WHERE job_id=36;
SELECT count(*) AS job36_24h FROM job_run_history WHERE job_id=36 AND start_time >= (now() AT TIME ZONE 'UTC') - interval '24 hours';
\echo '== j3b: job 36 gap analysis in last 60 min =='
SELECT count(*) AS runs_last_60min, min(start_time), max(start_time) FROM job_run_history WHERE job_id=36 AND start_time >= (now() AT TIME ZONE 'UTC') - interval '60 minutes';
\echo '== j4: jobs currently running RIGHT NOW =='
SELECT count(*) FILTER (WHERE currently_running) AS in_flight FROM job;
\echo '== L1: ledger cardinals =='
SELECT count(*) AS rows, max(id) AS maxid, count(DISTINCT transaction_id) AS distinct_txn FROM acc_gl_journal_entry;
\echo '== L2: distinct last_modified_by / created_by over ALL ledger rows =='
SELECT last_modified_by, count(*) FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
SELECT created_by, count(*) FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
\echo '== L3: max created / modified =='
SELECT max(created_on_utc) AS max_created, max(last_modified_on_utc) AS max_modified FROM acc_gl_journal_entry;
\echo '== L4: the T409-vs-T417 contradiction: min(entry_date) WHERE NOT is_running_balance_calculated =='
SELECT min(entry_date) AS min_entry_date, count(*) AS not_calculated FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated;
SELECT count(*) AS rows_ge_min FROM acc_gl_journal_entry
 WHERE entry_date >= (SELECT min(entry_date) FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated);
\echo '== L4b: the not-calculated rows in full =='
SELECT id, entry_date, transaction_id, is_running_balance_calculated FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated ORDER BY entry_date, id;
\echo '== L5: entry_date distribution =='
SELECT entry_date, count(*) FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
\echo '== L6: appusers =='
SELECT id, username FROM m_appuser ORDER BY id;
