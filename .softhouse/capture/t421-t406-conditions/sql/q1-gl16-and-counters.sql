-- T421 / F-T406-5 re-verification, plus the counters that say whether the
-- reference oracle moved between T406's review and this task. READ-ONLY.
\echo '=== 1. EVERY product that maps gl_account_id 16, with the product accounting rule ==='
SELECT m.product_id,
       p.accounting_type,
       CASE p.accounting_type WHEN 2 THEN 'CASH' WHEN 3 THEN 'ACCRUAL_PERIODIC'
            WHEN 4 THEN 'ACCRUAL_UPFRONT' WHEN 1 THEN 'NONE' ELSE '?' END AS rule_name,
       m.financial_account_type AS slot
FROM acc_product_mapping m
JOIN m_product_loan p ON p.id = m.product_id
WHERE m.gl_account_id = 16
ORDER BY p.accounting_type, m.product_id;

\echo '=== 2. THE COUNT that the vector prose asserts: CASH products (accounting_type 2) mapping gl 16 ==='
SELECT count(*) AS cash_products_mapping_gl16
FROM acc_product_mapping m JOIN m_product_loan p ON p.id = m.product_id
WHERE m.gl_account_id = 16 AND p.accounting_type = 2;

\echo '=== 3. and the NON-cash ones, which the eleven-item list wrongly folded into that count ==='
SELECT m.product_id, p.accounting_type, m.financial_account_type AS slot
FROM acc_product_mapping m JOIN m_product_loan p ON p.id = m.product_id
WHERE m.gl_account_id = 16 AND p.accounting_type <> 2
ORDER BY m.product_id;

\echo '=== 4. ORACLE COUNTERS -- did anything move since T406 reviewed? ==='
SELECT (SELECT count(*) FROM m_portfolio_command_source)  AS command_source_rows,
       (SELECT max(id)   FROM m_portfolio_command_source) AS command_source_max_id,
       (SELECT count(*)  FROM acc_gl_journal_entry)       AS journal_entry_rows,
       (SELECT max(id)   FROM acc_gl_journal_entry)       AS journal_entry_max_id,
       (SELECT count(*)  FROM m_loan_transaction)         AS loan_txn_rows,
       (SELECT max(id)   FROM m_loan_transaction)         AS loan_txn_max_id;

\echo '=== 5. THE PROMOTED ACCOUNTS -- leg counts, which must NOT have moved ==='
SELECT gl.id AS gl_account_id, gl.gl_code, count(je.id) AS journal_entries
FROM acc_gl_account gl
LEFT JOIN acc_gl_journal_entry je ON je.account_id = gl.id
WHERE gl.id IN (16,18,22,37,38,39,40,41,42,43,44,45,46,47)
GROUP BY gl.id, gl.gl_code
ORDER BY gl.id;

\echo '=== 6. product 63 mapping -- the bijection the vectors transcribe ==='
SELECT financial_account_type AS slot, gl_account_id, product_type, payment_type, charge_id
FROM acc_product_mapping WHERE product_id = 63 ORDER BY financial_account_type;

\echo '=== 7. the three graded transactions, amounts AS STORED (text, never a float) ==='
SELECT je.transaction_id, je.id, je.account_id, je.type_enum,
       je.amount::text AS amount_text, je.is_running_balance_calculated
FROM acc_gl_journal_entry je
WHERE je.transaction_id IN ('L29','L30','L32')
ORDER BY je.transaction_id, je.id;
