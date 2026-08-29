\echo === S01.1 observation instant, database clock ===
SELECT now() AS db_now, current_database() AS db, version() AS pg_version;

\echo === S01.2 the I-5 pin: modified vs total, whole table ===
SELECT count(*) AS total,
       count(*) FILTER (WHERE last_modified_on_utc > created_on_utc) AS modified,
       count(*) FILTER (WHERE last_modified_on_utc = created_on_utc) AS untouched,
       count(*) FILTER (WHERE last_modified_on_utc IS NULL)          AS null_lm,
       min(created_on_utc) AS oldest_created,
       max(created_on_utc) AS newest_created,
       max(last_modified_on_utc) AS newest_modified
FROM acc_gl_journal_entry;

\echo === S01.3 by cohort of id, as T391 measured it ===
SELECT CASE WHEN id <= 75 THEN 'a: id <= 75 (pre-T388)'
            WHEN id <= 95 THEN 'b: id 76-95 (T388)'
            WHEN id <= 113 THEN 'c: id 96-113 (scheduled job, T391)'
            ELSE 'd: id > 113 (new since T391)' END AS cohort,
       count(*) AS total,
       count(*) FILTER (WHERE last_modified_on_utc > created_on_utc) AS modified,
       count(*) FILTER (WHERE last_modified_on_utc = created_on_utc) AS untouched
FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;

\echo === S01.4 who last modified, and who made ===
SELECT last_modified_by, count(*) AS n, min(last_modified_on_utc) AS lo, max(last_modified_on_utc) AS hi
FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
SELECT created_by, count(*) AS n FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;

\echo === S01.5 app users named ===
SELECT id, username, firstname, lastname FROM m_appuser ORDER BY id;
