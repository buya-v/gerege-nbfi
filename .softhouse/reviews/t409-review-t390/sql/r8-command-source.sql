\pset pager off
-- Is there ANY command-source row that could account for the eighteen legs?
SELECT count(*) AS rows, max(id) AS max_id, min(id) AS min_id FROM m_portfolio_command_source;
-- the tail, with every column that could name an author or a key
SELECT id, action_name, entity_name, resource_id, loan_id, made_on_date, maker_id,
       status, idempotency_key
  FROM m_portfolio_command_source
 WHERE id > 350 ORDER BY id;
-- any command-source row created at or after the scheduler's window?
SELECT count(*) AS cs_rows_at_or_after_scheduler_window
  FROM m_portfolio_command_source
 WHERE made_on_date >= TIMESTAMPTZ '2026-08-28 16:00:00+00';
