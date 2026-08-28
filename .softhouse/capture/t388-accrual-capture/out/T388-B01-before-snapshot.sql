-- T388 BEFORE SNAPSHOT. Read-only. Every statement is a SELECT.
-- Taken BEFORE T388 wrote anything to the standing reference oracle (Fineract),
-- so that ORACLE-STATE-MOVED-BY-T388.md is a DIFF and not an assertion.
\echo '=== 1. engine ==='
SELECT version();
\echo '=== 2. append-table floors (the two tables oracle-state-baseline.sh watches) ==='
SELECT 'acc_gl_journal_entry' AS tbl, count(*) AS rows, max(id) AS max_id FROM acc_gl_journal_entry
UNION ALL
SELECT 'm_portfolio_command_source', count(*), max(id) FROM m_portfolio_command_source
UNION ALL
SELECT 'acc_gl_account', count(*), max(id) FROM acc_gl_account
UNION ALL
SELECT 'm_product_loan', count(*), max(id) FROM m_product_loan
UNION ALL
SELECT 'm_client', count(*), max(id) FROM m_client
UNION ALL
SELECT 'm_loan', count(*), max(id) FROM m_loan
UNION ALL
SELECT 'm_loan_transaction', count(*), max(id) FROM m_loan_transaction
UNION ALL
SELECT 'acc_product_mapping', count(*), max(id) FROM acc_product_mapping
UNION ALL
SELECT 'acc_gl_closure', count(*), max(id) FROM acc_gl_closure
ORDER BY 1;
\echo '=== 3. PER-GL-ACCOUNT journal entry counts -- EVERY account, LEFT JOIN so zero is printed ==='
SELECT a.id AS gl_id, a.gl_code, a.name, a.classification_enum, a.account_usage,
       a.manual_entries_allowed, a.disabled,
       count(j.id) AS je_rows
FROM acc_gl_account a
LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
GROUP BY a.id, a.gl_code, a.name, a.classification_enum, a.account_usage, a.manual_entries_allowed, a.disabled
ORDER BY a.id;
\echo '=== 4. every loan product, its accounting_type, and its loan count ==='
SELECT p.id, p.name, p.short_name, p.currency_code, p.accounting_type,
       count(l.id) AS loans
FROM m_product_loan p
LEFT JOIN m_loan l ON l.product_id = p.id
GROUP BY p.id, p.name, p.short_name, p.currency_code, p.accounting_type
ORDER BY p.id;
\echo '=== 5. ACCRUAL_PERIODIC (accounting_type = 3) products only ==='
SELECT id, name, short_name, currency_code, accounting_type FROM m_product_loan WHERE accounting_type = 3 ORDER BY id;
\echo '=== 6. clients ==='
SELECT id, account_no, display_name, firstname, middlename, lastname, external_id, status_enum, office_id, activation_date
FROM m_client ORDER BY id;
\echo '=== 7. accrual + COB scheduled jobs ==='
SELECT id, name, is_active, cron_expression, previous_run_start_time, next_run_time, currently_running
FROM job WHERE id IN (11,16,22,33,34) ORDER BY id;
\echo '=== 8. business date ==='
SELECT * FROM m_business_date ORDER BY id;
\echo '=== 9. tenant currency config: MNT ==='
SELECT * FROM m_organisation_currency ORDER BY id;
\echo '=== 10. offices ==='
SELECT id, name, opening_date, hierarchy FROM m_office ORDER BY id;
\echo '=== 11. journal entries grouped by entry type/source, to show none is an accrual today ==='
SELECT j.entry_type_enum, j.type_enum, j.manual_entry, count(*) AS rows
FROM acc_gl_journal_entry j GROUP BY 1,2,3 ORDER BY 1,2,3;
\echo '=== 12. loan transactions by type -- transaction_type_enum 10 is ACCRUAL ==='
SELECT transaction_type_enum, count(*) AS rows FROM m_loan_transaction GROUP BY 1 ORDER BY 1;
\echo '=== 13. is any journal entry linked to a loan ACCRUAL transaction today? ==='
SELECT count(*) AS accrual_linked_journal_entries
FROM acc_gl_journal_entry j
JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
WHERE t.transaction_type_enum = 10;
\echo '=== 14. funds and payment types (needed for product/loan creation) ==='
SELECT 'fund' AS kind, id, name FROM m_fund UNION ALL SELECT 'paymenttype', id, value FROM m_payment_type ORDER BY 1,2;
