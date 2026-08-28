-- T388: the tenant's timezone and rounding mode, and PostgreSQL's idea of now, so the
-- business date the accrual run will use is OBSERVED rather than assumed.
-- Read-only. NOTE: the tenant registry lives in the fineract_tenants database, not here,
-- so what this file can see is the tenant DB's own clock plus the global config rows.
\echo '=== now, as the tenant database sees it ==='
SELECT now() AS db_now_tz, current_date AS db_current_date,
       (now() AT TIME ZONE 'Asia/Ulaanbaatar') AS ulaanbaatar_now;
\echo '=== global configuration rows that bear on business date and accrual ==='
SELECT id, name, enabled, value, date_value FROM c_configuration
WHERE name ILIKE '%business%' OR name ILIKE '%accrual%' OR name ILIKE '%charge%' OR name ILIKE '%cob%'
ORDER BY name;
