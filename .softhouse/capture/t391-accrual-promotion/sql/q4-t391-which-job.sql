-- T391 -- WHICH scheduled job produced L32/L33/L34? Read-only.
--
-- The entries were created 2026-08-28 16:01:00.100 .. .117 UTC. Three accrual jobs are
-- ACTIVE and two of them started at 16:01:00 -- job 22 at .002 and job 11 at .049 --
-- while job 16 did not start until 16:02:00. So the window belongs to 11 or 22, and
-- the discriminator is whether loan 8 posts income as a transaction: job 22 is
-- ADD_ACCRUAL_TRANSACTIONS_FOR_LOANS_WITH_INCOME_POSTED_AS_TRANSACTIONS and selects
-- only loans with that flag set.
--
-- WHAT THIS QUERY CANNOT DO, said before it runs: `job` and `job_run_history` record
-- WHEN a job ran, not WHICH ROWS it wrote. There is no foreign key from a journal entry
-- to a job. So this establishes the window and eliminates a candidate; it does not
-- prove authorship, and T391 does not claim it does.
\echo '=== 1. loan 8: the flags that decide which accrual job selects it ==='
SELECT id, product_id, loan_type_enum, loan_status_id,
       is_npa, interest_recalculation_enabled,
       expected_disbursedon_date, disbursedon_date, expected_maturedon_date
FROM m_loan WHERE id = 8;

\echo '=== 2. every column of m_loan whose name mentions income or accrual ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'm_loan' AND (column_name LIKE '%income%' OR column_name LIKE '%accrual%')
ORDER BY ordinal_position;

\echo '=== 3. every column of m_product_loan whose name mentions income or accrual ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'm_product_loan' AND (column_name LIKE '%income%' OR column_name LIKE '%accrual%')
ORDER BY ordinal_position;

\echo '=== 4. job run history around the window, if this schema keeps one ==='
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'job%' ORDER BY table_name;

\echo '=== 5. the three active accrual jobs, verbatim ==='
SELECT id, name, display_name, cron_expression, is_active,
       previous_run_start_time, next_run_time, task_priority
FROM job ORDER BY id;
