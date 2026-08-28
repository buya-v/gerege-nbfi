-- T391 -- T389's M-1, re-measured. Read-only.
--
-- T389 found docs/adr/DEC-2-gl-accounting-adapter.md:1061 and :3004 asserting, in the
-- present tense, "60 of the 60 rows in acc_gl_journal_entry carry
-- last_modified_on_utc > created_on_utc", and measured 60 of 91 live. DEC-2 is RATIFIED,
-- so amending it is a `user` gate and not an edit; T391 does not touch it. This query
-- exists so the handoff quotes a MEASURED figure rather than repeating T389's, which was
-- taken before the scheduler ran.
\echo '=== 1. the I-5 pin, live ==='
SELECT count(*) FILTER (WHERE last_modified_on_utc > created_on_utc) AS modified,
       count(*) AS total
FROM acc_gl_journal_entry;

\echo '=== 2. split by whether the row predates T388 ==='
SELECT CASE WHEN id <= 75 THEN 'id <= 75 (predates T388)'
            WHEN id <= 95 THEN 'id 76-95 (T388)'
            ELSE 'id 96-113 (the scheduled job)' END AS cohort,
       count(*) FILTER (WHERE last_modified_on_utc > created_on_utc) AS modified,
       count(*) AS total
FROM acc_gl_journal_entry
GROUP BY 1 ORDER BY 1;

\echo '=== 3. which job could have touched them -- running-balance job 9 ==='
SELECT id, name, cron_expression, is_active, previous_run_start_time
FROM job WHERE id = 9;
