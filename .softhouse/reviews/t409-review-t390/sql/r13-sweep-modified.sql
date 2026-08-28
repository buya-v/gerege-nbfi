\pset pager off
-- Exception class (c): an UPDATE below the floor is invisible to a max(id) floor. Sweep every
-- base table carrying last_modified_on_utc for a modification at or after the scheduler window.
SELECT string_agg(
         format('SELECT %L::text AS tbl, count(*)::bigint AS n FROM public.%I WHERE last_modified_on_utc >= TIMESTAMPTZ ''2026-08-28 16:00:00+00''',
                table_name, table_name),
         E'\nUNION ALL ' ORDER BY table_name)
       || E'\nORDER BY n DESC, tbl'
  FROM information_schema.columns
 WHERE table_schema='public' AND column_name='last_modified_on_utc'
   AND table_name IN (SELECT table_name FROM information_schema.tables
                       WHERE table_schema='public' AND table_type='BASE TABLE')
\gexec
