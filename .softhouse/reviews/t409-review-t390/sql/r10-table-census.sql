\pset pager off
-- How many base tables does this tenant database actually have? (T390 wrote 280 in one place;
-- T391 corrected it to 281. Measured here, not inherited.)
SELECT count(*) AS base_tables FROM information_schema.tables
 WHERE table_schema='public' AND table_type='BASE TABLE';
-- how many carry an audit column this instrument could have used
SELECT column_name, count(*) AS tables_with_it
  FROM information_schema.columns c
 WHERE c.table_schema='public'
   AND c.column_name IN ('created_on_utc','created_date','last_modified_on_utc','lastmodified_date')
   AND c.table_name IN (SELECT table_name FROM information_schema.tables
                         WHERE table_schema='public' AND table_type='BASE TABLE')
 GROUP BY column_name ORDER BY column_name;
