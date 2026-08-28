-- T388 AFTER SNAPSHOT. Every counter the t305/t327 STANDING-baseline files pin by string
-- equality, plus the ones T352/T359/T363 tracked, re-derived live so the blast-radius
-- list is a DIFF and not a memory.
-- Read-only.
\echo '=== the six counters t305/t327 STANDING-baseline.txt pins by literal ==='
SELECT 'acc_gl_journal_entry rows/max' AS pin,
       count(*)::text || '/' || coalesce(max(id)::text, 'null') AS live FROM acc_gl_journal_entry
UNION ALL
SELECT 'acc_gl_closure rows/max', count(*)::text || '/' || coalesce(max(id)::text, 'null') FROM acc_gl_closure
UNION ALL
SELECT 'distinct_transaction_id', count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry
UNION ALL
SELECT 'm_portfolio_command_source rows/max', count(*)::text || '/' || coalesce(max(id)::text, 'null') FROM m_portfolio_command_source
UNION ALL
SELECT 'm_loan', count(*)::text FROM m_loan
UNION ALL
SELECT 'm_office', count(*)::text FROM m_office;

\echo '=== m_portfolio_command_source status split (reference-oracle.md doctrine, T371 deleted the cardinal) ==='
SELECT status, count(*) FROM m_portfolio_command_source GROUP BY status ORDER BY status;

\echo '=== ACCRUAL_PERIODIC products -- capabilities-ledger.json says product 28 is THE ONLY ONE ==='
SELECT id, name, short_name, accounting_type FROM m_product_loan WHERE accounting_type = 3 ORDER BY id;

\echo '=== journal entries that arrived through a RECEIVABLE slot -- the count the bar prints as ZERO ==='
SELECT count(*) AS receivable_slot_journal_entries
FROM acc_gl_journal_entry j
JOIN m_loan_transaction t ON t.id = j.loan_transaction_id
JOIN m_loan l ON l.id = t.loan_id
JOIN m_product_loan p ON p.id = l.product_id AND p.accounting_type = 3
JOIN acc_product_mapping m ON m.product_id = l.product_id AND m.product_type = 1
                          AND m.gl_account_id = j.account_id
WHERE m.financial_account_type IN (7, 8, 9);

\echo '=== gl 18 and gl 22 -- the pair the ledger.accrual.entry argument rests on ==='
SELECT a.id AS gl_id, a.gl_code, count(j.id) AS je_rows
FROM acc_gl_account a LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
WHERE a.id IN (18, 22) GROUP BY a.id, a.gl_code ORDER BY a.id;

\echo '=== EVERY GL account a PROMOTED vector reads, live -- the P0 check ==='
SELECT a.id AS gl_id, a.gl_code, count(j.id) AS je_rows
FROM acc_gl_account a LEFT JOIN acc_gl_journal_entry j ON j.account_id = a.id
WHERE a.id IN (1, 2, 4, 6, 8, 10, 15, 16, 17, 18, 21, 22)
GROUP BY a.id, a.gl_code ORDER BY a.id;

\echo '=== distinct currency codes ==='
SELECT currency_code, count(*) FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
