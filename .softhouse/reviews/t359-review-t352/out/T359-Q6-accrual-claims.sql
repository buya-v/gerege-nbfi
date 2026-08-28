-- T359 verification of T352 §3.4: the three claims it made about ledger.accrual.entry.
-- (a) "three accrual jobs are ACTIVE and ran 2026-08-27"; (b) "COB jobs 33/34 inactive
-- with null previous_run_start_time"; (c) "product 28 is ACCRUAL_PERIODIC, all thirteen
-- financial_account_type slots 1..13 mapped, including 7->gl 18, 8->gl 22, 9->gl 16, and
-- it has ZERO loans".
\pset footer off
\echo '--- (a)+(b) every job whose name mentions accrual or COB ---'
SELECT id, name, is_active, previous_run_start_time, next_run_time
FROM job
WHERE name ILIKE '%accrual%' OR name ILIKE '%COB%' OR name ILIKE '%business day%'
ORDER BY id;

\echo '--- (c1) accounting_type of every loan product, and which is ACCRUAL_PERIODIC (3) ---'
SELECT id, name, accounting_type FROM m_product_loan ORDER BY id;

\echo '--- (c2) product 28 GL mappings: slot -> account ---'
SELECT financial_account_type, gl_account_id, product_type, payment_type, charge_id
FROM acc_product_mapping WHERE product_id = 28 AND product_type = 1
ORDER BY financial_account_type;

\echo '--- (c3) loan counts per product, LEFT JOIN so a zero shows ---'
SELECT p.id AS product_id, p.accounting_type, count(l.id) AS loans
FROM m_product_loan p LEFT JOIN m_loan l ON l.product_id = p.id
GROUP BY p.id, p.accounting_type ORDER BY p.id;
