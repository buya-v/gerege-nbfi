-- T391 -- the driver's four points about the overnight scheduler run, re-measured
-- here rather than accepted. Read-only.
--
-- The driver (from T390's measurement) states: app user 2 `system` on the eighteen
-- scheduler legs where T388's carry 1 `mifos`; no command-source row for any of them;
-- loan 8 now 6/6 periods accrued. Each is checked below. T391's own observations were
-- ALL taken AFTER the scheduler run -- 2026-08-29, against the live database and the live
-- contract boundary -- so none of them is a pre-scheduler snapshot; this query is the
-- evidence for saying so rather than asserting it.
\echo '=== 1. WHO wrote each cohort of journal entries ==='
SELECT CASE WHEN j.id <= 75 THEN 'id <= 75  (predates T388)'
            WHEN j.id <= 95 THEN 'id 76-95  (T388, by API)'
            ELSE 'id 96-113 (the scheduler)' END AS cohort,
       j.created_by,
       u.username,
       count(*) AS legs,
       min(j.created_on_utc) AS first_write,
       max(j.created_on_utc) AS last_write
FROM acc_gl_journal_entry j
LEFT JOIN m_appuser u ON u.id = j.created_by
GROUP BY 1, 2, 3 ORDER BY 1, 2;

\echo '=== 2. is there ANY command-source row for the scheduler legs? ==='
SELECT count(*) AS command_source_rows_above_379 FROM m_portfolio_command_source WHERE id > 379;

\echo '=== 3. loan 8: every schedule period and whether it has accrued ==='
SELECT r.installment, r.fromdate, r.duedate,
       r.principal_amount, r.interest_amount, r.fee_charges_amount, r.penalty_charges_amount,
       r.interest_accrued_derived, r.fee_accrued_derived, r.penalty_accrued_derived
FROM m_loan_repayment_schedule r
WHERE r.loan_id = 8 ORDER BY r.installment;

\echo '=== 4. the six accrual loan transactions on loan 8, with author ==='
SELECT t.id, t.transaction_type_enum, t.transaction_date, t.amount,
       t.created_by, u.username, t.created_on_utc, t.is_reversed
FROM m_loan_transaction t
LEFT JOIN m_appuser u ON u.id = t.created_by
WHERE t.loan_id = 8 ORDER BY t.id;

\echo '=== 5. how many jobs are ACTIVE, and how many tables could one touch unseen ==='
SELECT count(*) FILTER (WHERE is_active) AS active_jobs, count(*) AS total_jobs FROM job;
SELECT count(*) AS tables_in_this_database
FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
