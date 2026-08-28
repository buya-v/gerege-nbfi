-- T388: the journal entries the periodic accrual run produced, and THE SLOT EACH ONE
-- ARRIVED THROUGH.
--
-- WHY THE SLOT DECODE IS THE POINT. The bar's own correction record (T242, A2-34 F-4)
-- is about exactly this confusion: ONE GL ACCOUNT BACKS SEVERAL SLOTS, so an entry that
-- merely LANDS ON a receivable account is not the same as one that ARRIVED THROUGH a
-- receivable slot. The join below goes
--
--     acc_gl_journal_entry -> m_loan_transaction (transaction_type_enum = 10 ACCRUAL)
--                          -> m_loan -> m_product_loan (accounting_type = 3)
--     acc_gl_journal_entry.account_id -> acc_product_mapping.gl_account_id
--                          (for THIS product, product_type = 1 LOAN)
--
-- so `financial_account_type` is the acc_product_mapping slot code the account is
-- reachable through on THIS product, and because T388 gave the product THIRTEEN
-- DISTINCT accounts the mapping is a bijection and the decode is unambiguous. That is a
-- property of this capture's design, not of Fineract, and it is why the accounts were
-- created clean.
--
-- Slot codes decode on AccrualAccountsForLoan (accounting_type = 3):
--   7 INTEREST_RECEIVABLE   8 FEES_RECEIVABLE   9 PENALTIES_RECEIVABLE
-- [VERIFIED against the ported enum, nexus/internal/apps/ledger/slots.go, and against
--  Fineract AccountingConstants.java:95-122 at 426a23544].
--
-- Read-only.
\echo '=== 1. every journal entry T388 produced, with its slot decode ==='
SELECT j.id             AS je_id,
       j.transaction_id,
       j.entry_date,
       j.type_enum      AS dr1_cr2,
       j.account_id     AS gl_id,
       a.gl_code,
       a.name           AS gl_name,
       j.amount,
       j.currency_code,
       j.manual_entry,
       j.loan_transaction_id,
       t.transaction_type_enum AS loan_txn_type,
       l.id             AS loan_id,
       l.product_id,
       p.accounting_type,
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
           ELSE 'slot ' || m.financial_account_type || ' does not decode on AccrualAccountsForLoan'
       END AS slot_name
FROM acc_gl_journal_entry j
JOIN acc_gl_account a       ON a.id = j.account_id
LEFT JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
LEFT JOIN m_loan l          ON l.id = t.loan_id
LEFT JOIN m_product_loan p  ON p.id = l.product_id
LEFT JOIN acc_product_mapping m ON m.product_id = l.product_id
                               AND m.product_type = 1
                               AND m.gl_account_id = j.account_id
WHERE j.id > 75
ORDER BY j.id;

\echo '=== 2. ONLY the entries that arrived through a RECEIVABLE slot (7, 8, 9) ==='
SELECT j.id AS je_id, j.transaction_id, j.entry_date, j.type_enum AS dr1_cr2,
       j.account_id AS gl_id, a.gl_code, j.amount,
       m.financial_account_type AS slot_code,
       CASE m.financial_account_type
           WHEN 7 THEN 'INTEREST_RECEIVABLE'
           WHEN 8 THEN 'FEES_RECEIVABLE'
           WHEN 9 THEN 'PENALTIES_RECEIVABLE'
       END AS slot_name
FROM acc_gl_journal_entry j
JOIN acc_gl_account a ON a.id = j.account_id
JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
JOIN m_loan l ON l.id = t.loan_id
JOIN acc_product_mapping m ON m.product_id = l.product_id AND m.product_type = 1
                          AND m.gl_account_id = j.account_id
WHERE t.transaction_type_enum = 10
  AND m.financial_account_type IN (7, 8, 9)
ORDER BY j.id;

\echo '=== 3. the ACCRUAL loan transactions on loan 8 ==='
SELECT id, loan_id, transaction_type_enum, transaction_date, amount,
       principal_portion_derived, interest_portion_derived,
       fee_charges_portion_derived, penalty_charges_portion_derived, is_reversed
FROM m_loan_transaction WHERE loan_id = 8 ORDER BY id;

\echo '=== 4. double entry check: debits = credits per transaction_id, in MINOR UNITS ==='
SELECT j.transaction_id,
       count(*) AS legs,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::bigint ELSE 0 END) AS debit_minor,
       sum(CASE WHEN j.type_enum = 1 THEN (j.amount * 100)::bigint ELSE 0 END) AS credit_minor,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::bigint ELSE -(j.amount * 100)::bigint END) AS difference_minor
FROM acc_gl_journal_entry j
WHERE j.id > 75
GROUP BY j.transaction_id ORDER BY j.transaction_id;

\echo '=== 5. per-GL-account counts AFTER T388 -- every account, so the diff is derivable ==='
SELECT a.id AS gl_id, a.gl_code, a.name, count(j.id) AS je_rows
FROM acc_gl_account a
LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
GROUP BY a.id, a.gl_code, a.name ORDER BY a.id;

\echo '=== 6. append-table state AFTER T388 ==='
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

\echo '=== 7. the command-source rows T388 wrote, by idempotency key ==='
SELECT id, action_name, entity_name, resource_id, status, idempotency_key
FROM m_portfolio_command_source WHERE idempotency_key LIKE 'T388-%' ORDER BY id;
