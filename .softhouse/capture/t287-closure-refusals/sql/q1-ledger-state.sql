-- T287 ARM 2 BLAST-RADIUS MEASUREMENT, part 1.
--
-- Answers, from the live tenant database and not from memory:
--   1. what offices exist, and their hierarchy (a closure is looked up BY OFFICE ID with
--      no hierarchy walk -- see GLClosureRepository.getLatestGLClosureByBranch)
--   2. is acc_gl_closure actually empty, as capabilities-ledger.json claims
--   3. the journal-entry date range PER OFFICE, which is what a closure date would poison
--   4. the tenant business date, which is what "future date" is measured against
--
-- PostgreSQL. Read-only: every statement is a SELECT.
\pset pager off
\echo '=== 1. offices (id, name, hierarchy, opening date) ==='
SELECT id, name, hierarchy, parent_id, opening_date
FROM m_office
ORDER BY id;

\echo ''
\echo '=== 2. acc_gl_closure -- ALL ROWS (registry claims this is empty) ==='
SELECT id, office_id, closing_date, is_deleted, created_date, comments
FROM acc_gl_closure
ORDER BY id;

\echo ''
\echo '=== 2b. acc_gl_closure row count ==='
SELECT count(*) AS closure_rows FROM acc_gl_closure;

\echo ''
\echo '=== 3. journal entries PER OFFICE: count, earliest and latest entry_date ==='
SELECT je.office_id,
       o.name AS office_name,
       count(*)             AS entries,
       min(je.entry_date)   AS earliest_entry_date,
       max(je.entry_date)   AS latest_entry_date,
       count(*) FILTER (WHERE je.is_manual_entry) AS manual_entries
FROM acc_gl_journal_entry je
JOIN m_office o ON o.id = je.office_id
GROUP BY je.office_id, o.name
ORDER BY je.office_id;

\echo ''
\echo '=== 3b. journal entries: whole-tenant totals ==='
SELECT count(*) AS entries, min(entry_date) AS earliest, max(entry_date) AS latest
FROM acc_gl_journal_entry;

\echo ''
\echo '=== 4. tenant business date rows (m_business_date) ==='
SELECT id, type, date FROM m_business_date ORDER BY id;

\echo ''
\echo '=== 5. currencies enabled on this tenant ==='
SELECT code, decimal_places, currency_multiplesof FROM m_organisation_currency ORDER BY code;
