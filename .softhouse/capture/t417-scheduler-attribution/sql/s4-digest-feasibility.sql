\echo '== s4a: how many base tables, and how many carry ANY audit column =='
SELECT count(*) AS base_tables FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE';

SELECT count(DISTINCT t.table_name) AS tables_with_any_audit_column
FROM information_schema.tables t JOIN information_schema.columns c
  ON c.table_schema=t.table_schema AND c.table_name=t.table_name
WHERE t.table_schema='public' AND t.table_type='BASE TABLE'
  AND c.column_name IN ('created_on_utc','last_modified_on_utc','created_date','lastmodified_date',
                        'created_by','last_modified_by','createdby_id','lastmodifiedby_id');

\echo '== s4b: total live row count across every base table, from the planner-independent count -- the digest cost driver =='
SELECT sum(cnt) AS total_rows_all_base_tables, count(*) AS tables_counted FROM (
  SELECT (xpath('/row/c/text()',
          query_to_xml(format('SELECT count(*) AS c FROM %I.%I', table_schema, table_name),
                       false, true, '')))[1]::text::bigint AS cnt
  FROM information_schema.tables
  WHERE table_schema='public' AND table_type='BASE TABLE'
) s;

\echo '== s4c: the ten largest base tables by live row count =='
SELECT table_name, cnt FROM (
  SELECT table_name,
         (xpath('/row/c/text()',
          query_to_xml(format('SELECT count(*) AS c FROM %I.%I', table_schema, table_name),
                       false, true, '')))[1]::text::bigint AS cnt
  FROM information_schema.tables
  WHERE table_schema='public' AND table_type='BASE TABLE'
) s ORDER BY cnt DESC LIMIT 10;

\echo '== s4d: sequences -- exception class (a), a CONSUMED sequence leaves no row =='
SELECT count(*) AS sequences FROM pg_sequences WHERE schemaname='public';
SELECT schemaname, sequencename, last_value FROM pg_sequences
WHERE schemaname='public' AND last_value IS NOT NULL ORDER BY sequencename LIMIT 20;
