-- T352. What would an accrual vector need? Measured, not assumed.
-- The coverage report's `ledger.accrual.entry` row claims (a) product 28 is the only
-- ACCRUAL_PERIODIC product, (b) it has no loan, (c) no receivable slot has ever been
-- posted through. Re-derive all three against the live reference oracle.
\pset footer off

-- (a) every product's accounting_type. 1=NONE 2=CASH 3=ACCRUAL_PERIODIC 4=ACCRUAL_UPFRONT
SELECT id, name, accounting_type, currency_code
  FROM m_product_loan
 ORDER BY accounting_type DESC, id;

-- (b) which products actually carry loans
SELECT p.id AS product_id, p.accounting_type, count(l.id) AS loans
  FROM m_product_loan p
  LEFT JOIN m_loan l ON l.product_id = p.id
 GROUP BY p.id, p.accounting_type
 ORDER BY p.accounting_type DESC, p.id;

-- (c) has ANY journal entry ever arrived through a receivable slot? The accrual
-- receivable slots on product 28, per acc_product_mapping.
SELECT m.product_id, m.financial_account_type, m.product_type, m.payment_type,
       m.charge_id, m.gl_account_id
  FROM acc_product_mapping m
 WHERE m.product_id = 28
 ORDER BY m.financial_account_type;

-- (d) every journal entry in the tenant, grouped by account, so "the slot is unposted /
-- the account is not empty" can be re-checked rather than remembered.
SELECT account_id, count(*) AS entries, min(entry_date) AS first_entry, max(entry_date) AS last_entry
  FROM acc_gl_journal_entry
 GROUP BY account_id
 ORDER BY account_id;

-- (e) is there an accrual job at all, and has it ever run?
SELECT id, name, is_active, previous_run_start_time
  FROM job
 WHERE name ILIKE '%accrual%' OR name ILIKE '%COB%'
 ORDER BY id;
