-- T367 re-derivation #4 -- READ-ONLY. Does the key NAME A TASK, or is it merely PRESENT?
SELECT count(*) FILTER (WHERE idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') AS looks_like_uuid,
       count(*) FILTER (WHERE idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') AS not_uuid,
       count(*) AS total
FROM m_portfolio_command_source;

SELECT 'uuid-shaped, id <= 352' AS bucket, count(*) FROM m_portfolio_command_source
  WHERE id <= 352 AND idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
SELECT 'uuid-shaped, id > 352' AS bucket, count(*) FROM m_portfolio_command_source
  WHERE id > 352 AND idempotency_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- the non-UUID keys: do they in fact name a task?
SELECT id, idempotency_key FROM m_portfolio_command_source
WHERE idempotency_key !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
ORDER BY id;
