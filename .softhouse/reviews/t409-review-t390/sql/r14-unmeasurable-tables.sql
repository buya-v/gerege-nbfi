\pset pager off
-- HOW BIG IS THE BLIND SPOT? Base tables carrying NONE of the four audit columns: for these no
-- "when was this row written" question can be asked at all, by this instrument or by me.
SELECT count(*) AS base_tables_with_no_audit_column
  FROM information_schema.tables t
 WHERE t.table_schema='public' AND t.table_type='BASE TABLE'
   AND NOT EXISTS (SELECT 1 FROM information_schema.columns c
                    WHERE c.table_schema='public' AND c.table_name=t.table_name
                      AND c.column_name IN ('created_on_utc','created_date',
                                            'last_modified_on_utc','lastmodified_date'));
-- of those, which are non-empty (a populated table with no audit column is the real blind spot)
SELECT string_agg(
         format('SELECT %L::text AS tbl, count(*)::bigint AS n FROM public.%I', t.table_name, t.table_name),
         E'\nUNION ALL ' ORDER BY t.table_name) || E'\nORDER BY n DESC, tbl'
  FROM information_schema.tables t
 WHERE t.table_schema='public' AND t.table_type='BASE TABLE'
   AND NOT EXISTS (SELECT 1 FROM information_schema.columns c
                    WHERE c.table_schema='public' AND c.table_name=t.table_name
                      AND c.column_name IN ('created_on_utc','created_date',
                                            'last_modified_on_utc','lastmodified_date'))
\gexec
