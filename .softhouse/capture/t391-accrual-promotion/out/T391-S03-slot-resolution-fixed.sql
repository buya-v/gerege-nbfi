-- T391 -- q1 sections 1 and 3, re-issued with the column names q2 section 1 MEASURED
-- rather than guessed. q1's own transcript is kept with its two `ERROR:` lines in it:
-- a rig that silently replaces the transcript that failed has hidden a failure.
--
-- Read-only. capsql-readonly.sh refuses this file if it ever stops being SELECT-only.
\echo '=== 1. product 63: every slot mapping, decoded on AccrualAccountsForLoan ==='
SELECT m.id AS mapping_id,
       m.product_id,
       m.product_type,
       m.financial_account_type AS slot_code,
       CASE m.financial_account_type
           WHEN 1  THEN 'FUND_SOURCE'
           WHEN 2  THEN 'LOAN_PORTFOLIO'
           WHEN 3  THEN 'INTEREST_ON_LOANS'
           WHEN 4  THEN 'INCOME_FROM_FEES'
           WHEN 5  THEN 'INCOME_FROM_PENALTIES'
           WHEN 6  THEN 'LOSSES_WRITTEN_OFF'
           WHEN 7  THEN 'INTEREST_RECEIVABLE'
           WHEN 8  THEN 'FEES_RECEIVABLE'
           WHEN 9  THEN 'PENALTIES_RECEIVABLE'
           WHEN 10 THEN 'TRANSFERS_SUSPENSE'
           WHEN 11 THEN 'OVERPAYMENT'
           WHEN 12 THEN 'INCOME_FROM_RECOVERY'
           WHEN 13 THEN 'GOODWILL_CREDIT'
           ELSE 'slot ' || m.financial_account_type || ' has no AccrualAccountsForLoan name'
       END AS slot_name,
       m.gl_account_id,
       a.gl_code,
       a.name AS gl_name,
       a.classification_enum,
       a.manual_journal_entries_allowed,
       a.disabled,
       a.account_usage,
       m.payment_type,
       m.charge_id,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id = m.gl_account_id) AS je_rows_on_account
FROM acc_product_mapping m
JOIN acc_gl_account a ON a.id = m.gl_account_id
WHERE m.product_id = 63 AND m.product_type = 1
ORDER BY m.financial_account_type;

\echo '=== 2. ALL SIX accrual transactions L29..L34, each leg decoded to its slot ==='
SELECT j.id AS je_id,
       j.transaction_id,
       j.entry_date,
       j.type_enum AS dr2_cr1,
       j.account_id AS gl_id,
       a.gl_code,
       j.amount,
       j.currency_code,
       j.manual_entry,
       j.reversed,
       j.office_id,
       j.entity_type_enum,
       j.entity_id,
       j.loan_transaction_id,
       t.transaction_type_enum AS loan_txn_type,
       l.product_id,
       p.accounting_type,
       m.financial_account_type AS slot_code,
       CASE m.financial_account_type
           WHEN 3 THEN 'INTEREST_ON_LOANS'
           WHEN 4 THEN 'INCOME_FROM_FEES'
           WHEN 5 THEN 'INCOME_FROM_PENALTIES'
           WHEN 7 THEN 'INTEREST_RECEIVABLE'
           WHEN 8 THEN 'FEES_RECEIVABLE'
           WHEN 9 THEN 'PENALTIES_RECEIVABLE'
           ELSE 'OTHER SLOT -- read section 1'
       END AS slot_name
FROM acc_gl_journal_entry j
JOIN acc_gl_account a ON a.id = j.account_id
JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
JOIN m_loan l ON l.id = t.loan_id
JOIN m_product_loan p ON p.id = l.product_id
JOIN acc_product_mapping m ON m.product_id = l.product_id AND m.product_type = 1
                          AND m.gl_account_id = j.account_id
WHERE j.transaction_id IN ('L29', 'L30', 'L31', 'L32', 'L33', 'L34')
ORDER BY j.transaction_id, j.id;

\echo '=== 3. double entry on ALL SIX, in INTEGER MINOR UNITS ==='
SELECT j.transaction_id,
       count(*) AS legs,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::bigint ELSE 0 END) AS debit_minor,
       sum(CASE WHEN j.type_enum = 1 THEN (j.amount * 100)::bigint ELSE 0 END) AS credit_minor,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::bigint ELSE -(j.amount * 100)::bigint END) AS difference_minor
FROM acc_gl_journal_entry j
WHERE j.transaction_id IN ('L29', 'L30', 'L31', 'L32', 'L33', 'L34')
GROUP BY j.transaction_id ORDER BY j.transaction_id;

\echo '=== 4. the chart rows the vectors will carry as request.accounts ==='
SELECT id, gl_code, name, classification_enum, account_usage,
       manual_journal_entries_allowed, disabled
FROM acc_gl_account WHERE id IN (37, 38, 39, 41, 42, 43) ORDER BY id;

\echo '=== 5. scheduled-job state, with the column names this schema actually has ==='
SELECT id, name, cron_expression, is_active, previous_run_start_time, next_run_time
FROM job WHERE id IN (11, 16, 22, 33, 34) ORDER BY id;

\echo '=== 6. did any API call produce L32/L33/L34? command-source rows since T388 ==='
SELECT id, action_name, entity_name, resource_id, status, idempotency_key, made_on_date
FROM m_portfolio_command_source WHERE id > 375 ORDER BY id;
