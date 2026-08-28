-- T388 BEFORE SNAPSHOT, part 2. The two statements q1 could not run, with the
-- column names re-derived from information_schema rather than guessed.
-- Read-only.
\echo '=== A. acc_gl_account columns ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'acc_gl_account' ORDER BY ordinal_position;
\echo '=== B. acc_gl_journal_entry columns ==='
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'acc_gl_journal_entry' ORDER BY ordinal_position;
\echo '=== C. PER-GL-ACCOUNT journal entry counts -- EVERY account, LEFT JOIN so zero is printed ==='
SELECT a.id AS gl_id, a.gl_code, a.name, a.classification_enum, a.account_usage,
       a.manual_entries_allowed, a.disabled,
       count(j.id) AS je_rows
FROM acc_gl_account a
LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
GROUP BY a.id, a.gl_code, a.name, a.classification_enum, a.account_usage, a.manual_entries_allowed, a.disabled
ORDER BY a.id;
\echo '=== D. journal entries by type/manual flag ==='
SELECT type_enum, manual_entry, entity_type_enum, count(*) AS rows
FROM acc_gl_journal_entry GROUP BY 1,2,3 ORDER BY 1,2,3;
\echo '=== E. the two existing ACCRUAL loan transactions, and their journal entries (expect none) ==='
SELECT t.id, t.loan_id, l.product_id, t.transaction_type_enum, t.transaction_date, t.amount, t.is_reversed,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.loan_transaction_id = t.id) AS je_rows
FROM m_loan_transaction t JOIN m_loan l ON l.id = t.loan_id
WHERE t.transaction_type_enum = 10 ORDER BY t.id;
\echo '=== F. product 28 mapping, for the record ==='
SELECT m.id, m.product_id, m.product_type, m.financial_account_type, m.gl_account_id, m.payment_type, m.charge_id
FROM acc_product_mapping m WHERE m.product_id = 28 ORDER BY m.financial_account_type;
