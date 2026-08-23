-- T287 ARM 2 BLAST-RADIUS MEASUREMENT, part 2.
--
-- q1-ledger-state.sql section 3 failed with
--     ERROR: column je.is_manual_entry does not exist
--     HINT: Perhaps you meant to reference the column "je.manual_entry".
-- That failure is committed verbatim as out/M-01-ledger-state.txt -- it is an observation
-- about the adopted Fineract schema (the column is `manual_entry`), not something to hide.
-- This file re-asks section 3 with the real column name and adds the questions the first
-- pass raised.
--
-- PostgreSQL. Read-only: every statement is a SELECT.
\pset pager off
\echo '=== 3. journal entries PER OFFICE: count, earliest and latest entry_date ==='
SELECT je.office_id,
       o.name AS office_name,
       count(*)             AS entries,
       min(je.entry_date)   AS earliest_entry_date,
       max(je.entry_date)   AS latest_entry_date,
       count(*) FILTER (WHERE je.manual_entry) AS manual_entries
FROM acc_gl_journal_entry je
JOIN m_office o ON o.id = je.office_id
GROUP BY je.office_id, o.name
ORDER BY je.office_id;

\echo ''
\echo '=== 3c. every distinct entry_date with a count, so the shape is visible not summarised ==='
SELECT entry_date, count(*) AS entries, count(*) FILTER (WHERE manual_entry) AS manual
FROM acc_gl_journal_entry
GROUP BY entry_date
ORDER BY entry_date;

\echo ''
\echo '=== 4b. is the business-date feature enabled at all? (m_business_date was EMPTY) ==='
SELECT name, enabled, value, date_value
FROM c_configuration
WHERE name LIKE '%business%date%' OR name LIKE '%cob%'
ORDER BY name;

\echo ''
\echo '=== 4c. what the DATABASE thinks now is, and the tenant timezone ==='
SELECT current_date AS db_current_date, now() AS db_now, current_setting('TimeZone') AS db_tz;

\echo ''
\echo '=== 6. loan products and their accounting type ==='
-- accounting_type: 1=NONE, 2=CASH_BASED, 3=ACCRUAL_PERIODIC, 4=ACCRUAL_UPFRONT.
-- Decisive for blast radius: a closure only refuses an automatic entry if the product
-- actually POSTS one. accounting_type=1 posts nothing, so checkForBranchClosures never runs.
SELECT id, name, short_name, currency_code, accounting_type
FROM m_product_loan
ORDER BY id;

\echo ''
\echo '=== 7. loans that exist, their office, and their date span ==='
SELECT l.id, c.office_id, l.loan_type_enum, l.product_id, l.submittedon_date, l.disbursedon_date, l.loan_status_id
FROM m_loan l
LEFT JOIN m_client c ON c.id = l.client_id
ORDER BY l.id;

\echo ''
\echo '=== 8. savings accounts (deposit activation is a user gate -- checking presence only) ==='
SELECT count(*) AS savings_accounts FROM m_savings_account;
