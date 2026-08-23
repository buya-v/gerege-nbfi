-- T305 M-3 -- THE RESIDUE CLASS, MEASURED ON THE TENANT THAT ALREADY CARRIES IT.  READ-ONLY.
--
-- The brief names the expected class from T287: "left acc_gl_closure_id_seq is_called=t and
-- a PUBLIC audit row". This query measures BOTH layers of that class on whichever database
-- it is pointed at, so the same instrument answers "what does gerege already carry" and
-- "what would a fresh tenant carry after the same treatment".
--
-- WHY SEQUENCES ARE READ OFF THE RELATION AND NOT OFF pg_sequences: pg_sequences does NOT
-- expose is_called. T294 §4 records that its first draft labelled `last_value IS NOT NULL`
-- as is_called and that this was a mislabel of exactly the A2-34 F-4 kind. Reading the
-- sequence relation directly is the correction, carried forward here rather than re-made.
-- A bare SELECT from a sequence relation does NOT advance it.

\echo '== A. the ledger sequences -- is_called t is the permanent half of the T287 residue.'
SELECT 'acc_gl_journal_entry_id_seq' AS seq, last_value, is_called FROM acc_gl_journal_entry_id_seq
UNION ALL
SELECT 'acc_gl_closure_id_seq',              last_value, is_called FROM acc_gl_closure_id_seq
UNION ALL
SELECT 'm_portfolio_command_source_id_seq',  last_value, is_called FROM m_portfolio_command_source_id_seq;

\echo '== B. the audit rows this program own probes have left, ACCOUNTING entities only.'
SELECT id, action_name, entity_name, resource_id, status, office_id, api_get_url, made_on_date_utc
  FROM m_portfolio_command_source
 WHERE entity_name IN ('JOURNALENTRY','GLCLOSURE','GLACCOUNT','FINANCIALACTIVITYACCOUNT')
 ORDER BY id;

\echo '== C. the audit table as a whole -- how much of it is ours.'
SELECT count(*) AS all_audit_rows,
       max(id)  AS max_audit_id,
       count(*) FILTER (WHERE entity_name IN ('JOURNALENTRY','GLCLOSURE','GLACCOUNT','FINANCIALACTIVITYACCOUNT')) AS accounting_audit_rows
  FROM m_portfolio_command_source;

\echo '== D. the ledger itself, for the before/after comparison this task does NOT need to make.'
SELECT count(*) AS journal_entries, max(id) AS max_journal_entry_id,
       count(DISTINCT transaction_id) AS distinct_transaction_ids
  FROM acc_gl_journal_entry;
