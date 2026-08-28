-- T390 Q2: the tail of the command-source audit table.
-- If L32-L34 had come through the command bus there would be a row above 379.
SELECT id, idempotency_key, status, action_name, entity_name, made_on_date
FROM m_portfolio_command_source
WHERE id > 375
ORDER BY id;
