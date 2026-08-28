\pset pager off
-- FINAL STATE READING. Compared against r2/r8 taken at the start of this review, this is the
-- evidence that NOTHING THIS REVIEW DID MOVED THE SHARED ORACLE.
SELECT 'acc_gl_journal_entry rows/maxid' AS k, count(*)||'/'||coalesce(max(id)::text,'null') AS v FROM acc_gl_journal_entry
UNION ALL SELECT 'acc_gl_journal_entry distinct transaction_id', count(DISTINCT transaction_id)::text FROM acc_gl_journal_entry
UNION ALL SELECT 'acc_gl_closure rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_closure
UNION ALL SELECT 'm_portfolio_command_source rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM m_portfolio_command_source
UNION ALL SELECT 'm_loan rows', count(*)::text FROM m_loan
UNION ALL SELECT 'm_office rows', count(*)::text FROM m_office
UNION ALL SELECT 'm_loan_transaction rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM m_loan_transaction
UNION ALL SELECT 'acc_gl_account rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM acc_gl_account
UNION ALL SELECT 'THE PROMOTED PAIR gl 18 legs', count(*)::text FROM acc_gl_journal_entry WHERE account_id=18
UNION ALL SELECT 'THE PROMOTED PAIR gl 22 legs', count(*)::text FROM acc_gl_journal_entry WHERE account_id=22
UNION ALL SELECT 'max created_on_utc on the ledger', max(created_on_utc)::text FROM acc_gl_journal_entry
UNION ALL SELECT 'max last_modified_on_utc on the ledger', max(last_modified_on_utc)::text FROM acc_gl_journal_entry
UNION ALL SELECT 'job_run_history rows/maxid', count(*)||'/'||coalesce(max(id)::text,'null') FROM job_run_history;
