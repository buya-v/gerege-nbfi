-- T391 -- HAS THE ORACLE MOVED SINCE T388? Read-only.
--
-- WHY THIS QUERY EXISTS AND WHY IT RUNS BEFORE ANYTHING IS PROMOTED. T388's capture
-- was taken 2026-08-28T11:40Z. Job 16 ('Add Periodic Accrual Transactions') is ACTIVE
-- with cron '0 2 0 1/1 * ? *', so it has had at least one scheduled opportunity to fire
-- since. Section 10 of q1 returned SIX entries per receivable slot where T388 recorded
-- THREE, which is the signature of exactly that. A promotion that transcribed T388's
-- numbers without re-measuring would be promoting a snapshot, not the oracle.
\echo '=== 1. the schema columns this rig needs, so no query guesses a name ==='
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('acc_gl_account', 'acc_gl_journal_entry', 'acc_product_mapping')
ORDER BY table_name, ordinal_position;

\echo '=== 2. EVERY journal transaction on loan 8, with leg count and dates ==='
SELECT j.transaction_id,
       count(*) AS legs,
       min(j.entry_date) AS entry_date,
       min(j.created_on_utc) AS created_on_utc,
       min(j.loan_transaction_id) AS min_loan_txn,
       max(j.loan_transaction_id) AS max_loan_txn,
       min(j.id) AS min_je, max(j.id) AS max_je
FROM acc_gl_journal_entry j
JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
WHERE t.loan_id = 8
GROUP BY j.transaction_id
ORDER BY min(j.id);

\echo '=== 3. every loan transaction on loan 8 ==='
SELECT id, loan_id, transaction_type_enum, transaction_date, amount,
       principal_portion_derived, interest_portion_derived,
       fee_charges_portion_derived, penalty_charges_portion_derived,
       is_reversed, created_on_utc
FROM m_loan_transaction WHERE loan_id = 8 ORDER BY id;

\echo '=== 4. append-table state TODAY ==='
SELECT 'acc_gl_journal_entry' AS tbl, count(*) AS rows, max(id) AS max_id FROM acc_gl_journal_entry
UNION ALL SELECT 'm_portfolio_command_source', count(*), max(id) FROM m_portfolio_command_source
UNION ALL SELECT 'acc_gl_account', count(*), max(id) FROM acc_gl_account
UNION ALL SELECT 'm_product_loan', count(*), max(id) FROM m_product_loan
UNION ALL SELECT 'm_client', count(*), max(id) FROM m_client
UNION ALL SELECT 'm_loan', count(*), max(id) FROM m_loan
UNION ALL SELECT 'm_loan_transaction', count(*), max(id) FROM m_loan_transaction
UNION ALL SELECT 'acc_product_mapping', count(*), max(id) FROM acc_product_mapping
UNION ALL SELECT 'acc_gl_closure', count(*), max(id) FROM acc_gl_closure
ORDER BY 1;

\echo '=== 5. the forbidden set -- twelve promoted accounts, counted TODAY ==='
SELECT a.id AS gl_id, a.gl_code, count(j.id) AS je_rows
FROM acc_gl_account a
LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
WHERE a.id IN (1, 2, 4, 6, 8, 10, 15, 16, 17, 18, 21, 22)
GROUP BY a.id, a.gl_code ORDER BY a.id;

\echo '=== 6. the scheduled jobs that could have moved loan 8 ==='
SELECT id, name, cron_expression, is_active, previous_run_start_time, next_run_time,
       previous_run_status
FROM job WHERE id IN (11, 16, 22, 33, 34) ORDER BY id;

\echo '=== 7. rows created AFTER T388 finished (2026-08-28T12:00:00Z) ==='
SELECT j.id, j.transaction_id, j.account_id, j.type_enum AS dr2_cr1, j.amount,
       j.entry_date, j.created_on_utc, j.loan_transaction_id
FROM acc_gl_journal_entry j
WHERE j.created_on_utc > TIMESTAMP '2026-08-28 12:00:00'
ORDER BY j.id;
