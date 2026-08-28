\pset pager off
-- Same sweep over the 33 base tables whose audit column is the older `created_date`
-- (timestamp WITHOUT time zone). Session TimeZone is Etc/UTC (r7), so the literal is comparable.
SELECT string_agg(
         format('SELECT %L::text AS tbl, count(*)::bigint AS n FROM public.%I WHERE created_date >= TIMESTAMP ''2026-08-28 16:00:00''',
                table_name, table_name),
         E'\nUNION ALL ' ORDER BY table_name)
       || E'\nORDER BY n DESC, tbl'
  FROM information_schema.columns
 WHERE table_schema='public' AND column_name='created_date'
   AND table_name IN (SELECT table_name FROM information_schema.tables
                       WHERE table_schema='public' AND table_type='BASE TABLE')
\gexec
