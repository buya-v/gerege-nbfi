-- A2-26: the ledger's row-level ground truth AFTER the A2-3xx captures.
--
-- sql/q3-final-state.sql is the A2-7-era dump and is now stale: it predates the retype
-- being visible in a REST read-back, predates every manual journal entry, predates every
-- multi-leg entry, and predates the first reversal. This query is a SUPERSET of q3's
-- journal-entry projection, not a replacement of q3 -- q3 stays exactly as it was, and
-- out/A2-150-db-final-state.txt stays exactly as it was, because both are evidence of a
-- state this oracle has now left.
--
-- Read-only. Every statement is a SELECT.
\pset border 2

\echo '--- acc_gl_account: classification TODAY (gl 2 is the G-10 retype) ---'
SELECT id, parent_id, gl_code, name, classification_enum, account_usage,
       manual_journal_entries_allowed, disabled
FROM acc_gl_account ORDER BY id;

\echo '--- acc_gl_journal_entry: EVERY row, with the columns a ledger vector would grade ---'
\echo '--- NOTE office_running_balance / organization_running_balance: Fineract STORES a ---'
\echo '--- balance ON the entry. Gerege non-negotiable: balances are DERIVED, never written. ---'
SELECT j.id, j.transaction_id, j.entry_date, j.transaction_date, j.type_enum,
       j.account_id, g.gl_code, g.name AS gl_name, g.classification_enum AS gl_class_today,
       j.amount, j.currency_code, j.manual_entry, j.reversed, j.reversal_id,
       j.entity_type_enum, j.entity_id, j.loan_transaction_id,
       j.is_running_balance_calculated, j.office_running_balance, j.organization_running_balance
FROM acc_gl_journal_entry j JOIN acc_gl_account g ON g.id = j.account_id
ORDER BY j.id;

\echo '--- per-transaction double-entry check, in INTEGER MINOR UNITS (no float anywhere) ---'
\echo '--- amount is numeric(19,6); MNT minor unit is 2, so minor = round(amount*100) exactly ---'
SELECT j.transaction_id,
       count(*) AS legs,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::numeric(19,0) ELSE 0 END) AS debit_minor,
       sum(CASE WHEN j.type_enum = 1 THEN (j.amount * 100)::numeric(19,0) ELSE 0 END) AS credit_minor,
       sum(CASE WHEN j.type_enum = 2 THEN (j.amount * 100)::numeric(19,0)
                ELSE -(j.amount * 100)::numeric(19,0) END) AS debit_minus_credit_minor,
       bool_and(j.amount * 100 = (j.amount * 100)::numeric(19,0)) AS every_leg_is_a_whole_minor_unit
FROM acc_gl_journal_entry j
GROUP BY j.transaction_id
ORDER BY min(j.id);

\echo '--- leg-count distribution: the corpus had ONLY two-leg entries before A2-26 ---'
SELECT legs, count(*) AS transactions FROM (
  SELECT transaction_id, count(*) AS legs FROM acc_gl_journal_entry GROUP BY transaction_id
) t GROUP BY legs ORDER BY legs;

\echo '--- the reversal pair: original rows and the rows that reverse them ---'
SELECT o.id AS original_id, o.transaction_id AS original_txn, o.type_enum AS original_type,
       o.amount AS original_amount, o.reversed AS original_reversed,
       r.id AS reversal_id, r.transaction_id AS reversal_txn, r.type_enum AS reversal_type,
       r.amount AS reversal_amount
FROM acc_gl_journal_entry o LEFT JOIN acc_gl_journal_entry r ON r.id = o.reversal_id
WHERE o.reversed IS TRUE OR o.reversal_id IS NOT NULL
ORDER BY o.id;

\echo '--- acc_product_mapping: which products still point at the retyped gl 2 ---'
SELECT m.product_id, m.financial_account_type, m.payment_type, m.gl_account_id,
       g.gl_code, g.name, g.classification_enum AS gl_class_today
FROM acc_product_mapping m JOIN acc_gl_account g ON g.id = m.gl_account_id
WHERE m.gl_account_id = 2 ORDER BY m.product_id, m.financial_account_type, m.payment_type;

\echo '--- money column types on the ledger tables: none may be a float ---'
SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name IN ('acc_gl_journal_entry')
  AND data_type IN ('numeric','double precision','real','money')
ORDER BY column_name;

\echo '--- the command store, which is what makes Idempotency-Key work ---'
SELECT id, action_name, entity_name, idempotency_key, status
FROM m_portfolio_command_source
WHERE idempotency_key LIKE 'a2-26-idem-probe-%'
ORDER BY id;
