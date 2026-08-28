-- T371 q3 -- F1: does an idempotency_key NAME A TASK, or is it a server-minted UUID?
-- Fineract mints one when the caller sends no header:
--   IdempotencyKeyResolver.resolve -> ...orElseGet(idempotencyKeyGenerator::create)
--   IdempotencyKeyGenerator.create() -> UUID.randomUUID().toString()
-- So the classifier is the UUID.toString() SHAPE, 8-4-4-4-12 lowercase hex.
-- Reported two ways so the classifier is falsifiable:
--   (a) uuid_shaped vs not
--   (b) among the not-uuid-shaped, how many actually carry a task token
SELECT is_nullable, data_type
FROM information_schema.columns
WHERE table_name = 'm_portfolio_command_source' AND column_name = 'idempotency_key';

SELECT count(*)                                                              AS total_rows,
       count(*) FILTER (WHERE idempotency_key IS NULL)                       AS null_keys,
       count(*) FILTER (WHERE btrim(idempotency_key) = '')                   AS blank_keys,
       count(DISTINCT idempotency_key)                                       AS distinct_keys,
       count(*) FILTER (WHERE idempotency_key ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') AS uuid_shaped,
       count(*) FILTER (WHERE idempotency_key !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') AS not_uuid_shaped,
       count(*) FILTER (WHERE idempotency_key !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
                          AND id > 352)                                      AS not_uuid_above_floor,
       count(*) FILTER (WHERE idempotency_key ~* '(^|[^a-z0-9])(t[0-9]{2,3}|a2-[0-9]+|arm[0-9]+)([^a-z0-9]|$)') AS carries_task_token
FROM m_portfolio_command_source;

-- every non-UUID key, listed, so the 20 is auditable rather than asserted
SELECT id, status, idempotency_key
FROM m_portfolio_command_source
WHERE idempotency_key !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
ORDER BY id;
