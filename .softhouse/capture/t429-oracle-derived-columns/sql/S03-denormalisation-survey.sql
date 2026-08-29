\echo === S03.1 how many base tables are in this tenant schema at all ===
SELECT count(*) AS base_tables FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

\echo === S03.2 EVERY column in the tenant schema whose name ends _derived ===
SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_schema = 'public' AND column_name LIKE '%%\_derived'
ORDER BY table_name, ordinal_position;

\echo === S03.3 EVERY column whose name contains running_balance, anywhere ===
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public' AND column_name LIKE '%%running_balance%%'
ORDER BY table_name, ordinal_position;

\echo === S03.4 EVERY column whose name contains balance / total_ / cumulative / outstanding / summary ===
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public'
  AND (column_name LIKE '%%balance%%' OR column_name LIKE 'total\_%%'
       OR column_name LIKE '%%cumulative%%' OR column_name LIKE '%%outstanding%%')
ORDER BY table_name, ordinal_position;

\echo === S03.5 the audit-metadata quartet: which tables carry created_on_utc / last_modified_on_utc ===
SELECT count(DISTINCT table_name) AS tables_with_created_on_utc
FROM information_schema.columns
WHERE table_schema = 'public' AND column_name = 'created_on_utc';
