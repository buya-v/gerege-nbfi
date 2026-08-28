\pset pager off
-- INDEPENDENT WIDE SWEEP. The instrument watches TWO tables. Ask every base table that carries
-- created_on_utc whether ANYTHING was inserted at or after 2026-08-28 16:00:00 UTC -- i.e. in or
-- after the scheduler's 00:01 Asia/Ulaanbaatar run. Generated, then executed, so no table is
-- omitted by hand.
SELECT string_agg(
         format('SELECT %L::text AS tbl, count(*)::bigint AS n FROM public.%I WHERE created_on_utc >= TIMESTAMPTZ ''2026-08-28 16:00:00+00''',
                table_name, table_name),
         E'\nUNION ALL ' ORDER BY table_name)
       || E'\nORDER BY n DESC, tbl'
  FROM information_schema.columns
 WHERE table_schema='public' AND column_name='created_on_utc'
   AND table_name IN (SELECT table_name FROM information_schema.tables
                       WHERE table_schema='public' AND table_type='BASE TABLE')
\gexec
