-- T391 -- job_run_history around the 2026-08-28 16:01 window. Read-only.
\echo '=== 1. job_run_history columns ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'job_run_history' ORDER BY ordinal_position;

\echo '=== 2. every run recorded on 2026-08-28 for the accrual jobs ==='
SELECT * FROM job_run_history
WHERE job_id IN (11, 16, 22) AND start_time > TIMESTAMP '2026-08-28 00:00:00'
ORDER BY job_id, start_time;

\echo '=== 3. m_loan columns whose name mentions posted or transaction ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'm_loan' AND (column_name LIKE '%posted%' OR column_name LIKE '%transaction%')
ORDER BY ordinal_position;
