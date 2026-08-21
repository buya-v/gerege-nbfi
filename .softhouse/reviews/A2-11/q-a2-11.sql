-- A2-11 independent re-derivation, run against the LIVE PostgreSQL of the reference
-- oracle (Fineract). Read-only. Nothing here writes.
\pset border 2

\echo '--- (1) acc_gl_account: distinct accounts and classifications, LIVE ---'
SELECT classification_enum,
       CASE classification_enum WHEN 1 THEN 'ASSET' WHEN 2 THEN 'LIABILITY'
            WHEN 3 THEN 'EQUITY' WHEN 4 THEN 'INCOME' WHEN 5 THEN 'EXPENSE' END AS classification,
       count(*) AS n, string_agg(gl_code, ',' ORDER BY gl_code) AS codes
FROM acc_gl_account GROUP BY classification_enum ORDER BY classification_enum;

\echo '--- (1b) total row count ---'
SELECT count(*) AS acc_gl_account_rows FROM acc_gl_account;

\echo '--- (2) product 22: which financial_account_type slots, and are all NINE mandatory present? ---'
SELECT product_id, count(*) AS rows,
       string_agg(DISTINCT financial_account_type::text, ',' ORDER BY financial_account_type::text) AS slots
FROM acc_product_mapping WHERE product_id = 22 AND product_type = 1 GROUP BY product_id;

\echo '--- (2b) the nine notNull() cash slots {1,2,3,4,5,6,10,11,12} vs product 22 ---'
SELECT m.needed AS mandatory_slot,
       EXISTS (SELECT 1 FROM acc_product_mapping p
               WHERE p.product_id=22 AND p.product_type=1
                 AND p.financial_account_type=m.needed AND p.payment_type IS NULL) AS mapped_default
FROM (VALUES (1),(2),(3),(4),(5),(6),(10),(11),(12)) AS m(needed) ORDER BY m.needed;

\echo '--- (3) G-10: EVERY mapping row pointing at GL account 2 (the retyped ASSET->INCOME account) ---'
SELECT p.product_id, p.product_type, p.financial_account_type, p.payment_type,
       p.gl_account_id, g.gl_code, g.name, g.classification_enum
FROM acc_product_mapping p JOIN acc_gl_account g ON g.id = p.gl_account_id
WHERE p.gl_account_id = 2 ORDER BY p.product_id, p.financial_account_type, p.payment_type;

\echo '--- (3b) counts: distinct PRODUCTS vs mapping ROWS holding gl 2 ---'
SELECT count(DISTINCT product_id) AS distinct_products, count(*) AS mapping_rows
FROM acc_product_mapping WHERE gl_account_id = 2;

\echo '--- (3c) ALL slots whose mapped account classification violates the create-time type rule ---'
\echo '---     FUND_SOURCE(1)/TRANSFERS_SUSPENSE(10) expect ASSET or LIABILITY (ASSET_LIABILITY_TYPES) ---'
SELECT p.product_id, p.financial_account_type, p.payment_type, p.gl_account_id,
       g.gl_code, g.classification_enum
FROM acc_product_mapping p JOIN acc_gl_account g ON g.id = p.gl_account_id
WHERE p.product_type = 1 AND p.financial_account_type IN (1,10)
  AND g.classification_enum NOT IN (1,2)
ORDER BY p.product_id, p.financial_account_type;

\echo '--- (4) journal entries for LOAN 5 (product 46) - the double-entry claim ---'
SELECT j.id, j.loan_transaction_id, j.type_enum,
       CASE j.type_enum WHEN 1 THEN 'CREDIT' WHEN 2 THEN 'DEBIT' END AS side,
       j.account_id, g.gl_code, g.name, g.classification_enum, j.amount, j.currency_code
FROM acc_gl_journal_entry j JOIN acc_gl_account g ON g.id = j.account_id
WHERE j.loan_transaction_id IN (SELECT id FROM m_loan_transaction WHERE loan_id = 5)
ORDER BY j.id;

\echo '--- (4b) debit/credit totals for loan 5, as exact numeric ---'
SELECT CASE j.type_enum WHEN 1 THEN 'CREDIT' WHEN 2 THEN 'DEBIT' END AS side,
       sum(j.amount) AS total, count(*) AS n
FROM acc_gl_journal_entry j
WHERE j.loan_transaction_id IN (SELECT id FROM m_loan_transaction WHERE loan_id = 5)
GROUP BY j.type_enum ORDER BY j.type_enum;

\echo '--- (4c) the same totals in INTEGER MINOR UNITS (MNT minor unit 2), and the sub-minor residue ---'
SELECT CASE j.type_enum WHEN 1 THEN 'CREDIT' WHEN 2 THEN 'DEBIT' END AS side,
       sum((j.amount * 100)::numeric)          AS total_minor_units_exact,
       sum(j.amount * 100) = trunc(sum(j.amount * 100)) AS is_whole_minor_units
FROM acc_gl_journal_entry j
WHERE j.loan_transaction_id IN (SELECT id FROM m_loan_transaction WHERE loan_id = 5)
GROUP BY j.type_enum ORDER BY j.type_enum;

\echo '--- (5) product 46 mapping rows, LIVE (does it hold CHARGE_OFF_EXPENSE 16 / GOODWILL_CREDIT 13?) ---'
SELECT product_id, financial_account_type, payment_type, gl_account_id
FROM acc_product_mapping WHERE product_id = 46 ORDER BY financial_account_type;

\echo '--- (6) money column types: no float anywhere in the three slice tables ---'
SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name IN ('acc_gl_journal_entry','acc_product_mapping','acc_gl_account')
  AND data_type IN ('numeric','double precision','real','money')
ORDER BY table_name, column_name;
