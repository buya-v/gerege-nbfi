-- T294 -- THE WRITE-CHECK CENSUS. Fired IDENTICALLY before and after the single POST, so a
-- reviewer can see the reference oracle's ledger did not move rather than take a worker's
-- word for it. Same shape as T287's M-04/M-05 pair.
--
-- READ-ONLY. Every statement is a SELECT.
SELECT count(*) AS journal_entries, max(id) AS max_journal_entry_id
  FROM acc_gl_journal_entry;

SELECT count(*) AS closures, max(id) AS max_closure_id
  FROM acc_gl_closure;

SELECT count(*) AS commands, max(id) AS max_command_id
  FROM m_portfolio_command_source;

SELECT count(*) AS journal_entry_transaction_ids
  FROM (SELECT DISTINCT transaction_id FROM acc_gl_journal_entry) t;
