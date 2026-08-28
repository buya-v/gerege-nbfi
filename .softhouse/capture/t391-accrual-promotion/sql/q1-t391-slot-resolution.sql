-- T391 -- THE MEASUREMENT THIS PROMOTION RESTS ON: the (product, slot) -> GL account
-- resolution for product 63, and the eighteen legs of L29/L30/L31 decoded THROUGH IT.
--
-- Read-only. Every statement is a SELECT; capsql-readonly.sh refuses this file if it
-- ever stops being one.
--
-- WHY THE SLOT AND NOT THE ACCOUNT. T242 (A2-34 F-4) corrected a sentence the harness
-- printed on every run as measured fact -- 'gl 18, 22 and 16 carry ZERO journal entries'
-- -- when gl 16 had sixteen. The error was structural: ONE GL ACCOUNT BACKS SEVERAL
-- SLOTS. gl 16 is PENALTIES_RECEIVABLE (slot 9) on product 28 AND FUND_SOURCE (slot 1)
-- on ten cash products, and every one of its rows arrives through the latter. A vector
-- that graded the ACCOUNT would reproduce that error exactly. Section 4 below is the
-- check that makes the slot decode on product 63 UNAMBIGUOUS rather than merely
-- plausible: the mapping must be a bijection and none of accounts 35-47 may appear on
-- any other product.
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
       a.manual_entries_allowed,
       a.disabled,
       a.account_usage,
       m.payment_type,
       m.charge_id,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id = m.gl_account_id) AS je_rows_on_account
FROM acc_product_mapping m
JOIN acc_gl_account a ON a.id = m.gl_account_id
WHERE m.product_id = 63 AND m.product_type = 1
ORDER BY m.financial_account_type;

\echo '=== 2. product 63 itself: accounting_type, currency, scale ==='
SELECT id, name, short_name, accounting_type, currency_code, currency_digits,
       currency_multiplesof, principal_amount, nominal_interest_rate_per_period,
       interest_period_frequency_enum, interest_method_enum,
       number_of_repayments, repay_every, repayment_period_frequency_enum
FROM m_product_loan WHERE id = 63;

\echo '=== 3. the EIGHTEEN legs of L29/L30/L31, each decoded to its slot ==='
SELECT j.id AS je_id,
       j.transaction_id,
       j.entry_date,
       j.type_enum AS dr2_cr1,
       j.account_id AS gl_id,
       a.gl_code,
       j.amount,
       j.currency_code,
       j.manual_entry,
       j.is_reversed,
       j.loan_transaction_id,
       t.transaction_type_enum AS loan_txn_type,
       l.id AS loan_id,
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
WHERE j.transaction_id IN ('L29', 'L30', 'L31')
ORDER BY j.transaction_id, j.id;

\echo '=== 4. IS THE DECODE UNAMBIGUOUS? bijection on 63, and no account shared ==='
\echo '-- 4a. mapping count vs distinct accounts vs distinct slots on product 63 --'
SELECT count(*) AS mappings,
       count(DISTINCT gl_account_id) AS distinct_accounts,
       count(DISTINCT financial_account_type) AS distinct_slots
FROM acc_product_mapping WHERE product_id = 63 AND product_type = 1;

\echo '-- 4b. does any OTHER product map any of accounts 35-47? (expect ZERO rows) --'
SELECT m.product_id, m.product_type, m.financial_account_type AS slot_code, m.gl_account_id
FROM acc_product_mapping m
WHERE m.gl_account_id BETWEEN 35 AND 47 AND NOT (m.product_id = 63 AND m.product_type = 1)
ORDER BY m.product_id, m.financial_account_type;

\echo '-- 4c. the CONTRAST that makes 4b load-bearing: gl 16, the T242 trap, live --'
SELECT m.product_id, p.accounting_type, m.financial_account_type AS slot_code,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id = 16) AS je_rows_on_gl16
FROM acc_product_mapping m
JOIN m_product_loan p ON p.id = m.product_id
WHERE m.gl_account_id = 16 AND m.product_type = 1
ORDER BY m.product_id;

\echo '=== 5. double entry per transaction, in INTEGER MINOR UNITS (numeric, no float) ==='
SELECT j.transaction_id,
       count(*) AS legs,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::bigint ELSE 0 END) AS debit_minor,
       sum(CASE WHEN j.type_enum = 1 THEN (j.amount * 100)::bigint ELSE 0 END) AS credit_minor,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::bigint ELSE -(j.amount * 100)::bigint END) AS difference_minor
FROM acc_gl_journal_entry j
WHERE j.transaction_id IN ('L29', 'L30', 'L31')
GROUP BY j.transaction_id ORDER BY j.transaction_id;

\echo '=== 6. SUB-MINOR-UNIT RESIDUE CHECK: any amount with a non-zero 3rd decimal? ==='
SELECT j.id, j.transaction_id, j.amount
FROM acc_gl_journal_entry j
WHERE j.transaction_id IN ('L29', 'L30', 'L31')
  AND (j.amount * 100) <> trunc(j.amount * 100)
ORDER BY j.id;

\echo '=== 7. product 63 slots that are still UNPOSTED -- 6, 10, 11, 12, 13 ==='
SELECT m.financial_account_type AS slot_code,
       m.gl_account_id,
       a.gl_code,
       a.name AS gl_name,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id = m.gl_account_id) AS je_rows
FROM acc_product_mapping m
JOIN acc_gl_account a ON a.id = m.gl_account_id
WHERE m.product_id = 63 AND m.product_type = 1
  AND m.financial_account_type IN (1, 2, 6, 10, 11, 12, 13)
ORDER BY m.financial_account_type;

\echo '=== 8. product 28 slots 7/8/9, the ones the registry still records as unposted ==='
SELECT m.financial_account_type AS slot_code,
       m.gl_account_id,
       a.gl_code,
       (SELECT count(*) FROM acc_gl_journal_entry j WHERE j.account_id = m.gl_account_id) AS je_rows_on_account,
       (SELECT count(*) FROM acc_gl_journal_entry j
          JOIN m_loan_transaction t2 ON t2.id = j.loan_transaction_id
          JOIN m_loan l2 ON l2.id = t2.loan_id
         WHERE j.account_id = m.gl_account_id AND l2.product_id = 28) AS je_rows_through_product_28
FROM acc_product_mapping m
JOIN acc_gl_account a ON a.id = m.gl_account_id
WHERE m.product_id = 28 AND m.product_type = 1 AND m.financial_account_type IN (7, 8, 9)
ORDER BY m.financial_account_type;

\echo '=== 9. every ACCRUAL_PERIODIC product in this tenant (accounting_type = 3) ==='
SELECT id, name, accounting_type,
       (SELECT count(*) FROM m_loan l WHERE l.product_id = p.id) AS loans
FROM m_product_loan p WHERE accounting_type = 3 ORDER BY id;

\echo '=== 10. THE CORPUS SENTENCE: receivable-slot entries in the TENANT, by product ==='
SELECT l.product_id,
       m.financial_account_type AS slot_code,
       count(*) AS entries
FROM acc_gl_journal_entry j
JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
JOIN m_loan l ON l.id = t.loan_id
JOIN acc_product_mapping m ON m.product_id = l.product_id AND m.product_type = 1
                          AND m.gl_account_id = j.account_id
JOIN m_product_loan p ON p.id = l.product_id
WHERE p.accounting_type = 3 AND m.financial_account_type IN (7, 8, 9)
GROUP BY l.product_id, m.financial_account_type
ORDER BY l.product_id, m.financial_account_type;
