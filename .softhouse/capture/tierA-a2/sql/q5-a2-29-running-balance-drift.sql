-- A2-29 / G-12: is acc_gl_journal_entry.{office,organization}_running_balance a CACHE
-- of the derived sum, or a SECOND SOURCE OF TRUTH that can disagree with it?
--
-- READ-ONLY. Every statement is a SELECT.
--
-- The derivation re-implements JournalEntryRunningBalanceUpdateServiceImpl
-- .calculateRunningBalance [VERIFIED: fineract-provider/src/main/java/org/apache/fineract/
-- accounting/journalentry/service/JournalEntryRunningBalanceUpdateServiceImpl.java:220-250]
-- FROM SCRATCH -- i.e. with no seed taken from a previously stored balance --
-- in the order the writer itself uses, `order by je.entry_date, je.id`
-- [VERIFIED: same file:258,265].
--
--   ASSET(1) / EXPENSE(5):            DEBIT (type_enum=2) increases, CREDIT (1) decreases
--   LIABILITY(2) / EQUITY(3) / INCOME(4): CREDIT (1) increases, DEBIT (2) decreases
--
-- Classification is read from acc_gl_account AS IT IS TODAY, exactly as the writer's
-- own SQL does (it joins acc_gl_account at recompute time, not at posting time)
-- [VERIFIED: same file:256-257,263-264].
--
-- NO FLOATING POINT ANYWHERE. amount is numeric(19,6); MNT minor unit is 2, so the
-- integer minor unit is (amount*100)::numeric(19,0), and every comparison below is
-- made on numeric, never on a float.
\pset border 2

\echo '=== Q5.0 tenant / row counts ==='
SELECT current_database() AS db,
       (SELECT count(*) FROM acc_gl_journal_entry) AS entries,
       (SELECT count(*) FROM acc_gl_journal_entry WHERE is_running_balance_calculated) AS flagged_calculated,
       (SELECT count(*) FROM acc_gl_journal_entry WHERE NOT is_running_balance_calculated) AS flagged_not_calculated,
       (SELECT count(DISTINCT office_id) FROM acc_gl_journal_entry) AS offices_with_entries;

\echo '=== Q5.1 STORED vs DERIVED-FROM-SCRATCH, every row, integer minor units ==='
WITH signed AS (
  SELECT j.id, j.office_id, j.account_id, j.entry_date, j.type_enum, j.reversed,
         j.is_running_balance_calculated AS calc,
         (j.amount * 100)::numeric(19,0) AS amt_minor,
         CASE
           WHEN g.classification_enum IN (1,5) AND j.type_enum = 2 THEN  (j.amount*100)::numeric(19,0)
           WHEN g.classification_enum IN (1,5) AND j.type_enum = 1 THEN -(j.amount*100)::numeric(19,0)
           WHEN g.classification_enum IN (2,3,4) AND j.type_enum = 1 THEN  (j.amount*100)::numeric(19,0)
           ELSE -(j.amount*100)::numeric(19,0)
         END AS signed_minor,
         (j.office_running_balance      * 100)::numeric(19,0) AS stored_office_minor,
         (j.organization_running_balance* 100)::numeric(19,0) AS stored_org_minor
  FROM acc_gl_journal_entry j JOIN acc_gl_account g ON g.id = j.account_id
)
SELECT id, office_id, account_id, entry_date, type_enum, reversed, calc,
       stored_org_minor,
       SUM(signed_minor) OVER (PARTITION BY account_id            ORDER BY entry_date, id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS derived_org_minor,
       stored_org_minor
       - SUM(signed_minor) OVER (PARTITION BY account_id          ORDER BY entry_date, id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS org_delta_minor,
       stored_office_minor,
       SUM(signed_minor) OVER (PARTITION BY office_id, account_id ORDER BY entry_date, id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS derived_office_minor,
       stored_office_minor
       - SUM(signed_minor) OVER (PARTITION BY office_id,account_id ORDER BY entry_date, id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS office_delta_minor
FROM signed ORDER BY id;

\echo '=== Q5.2 DRIFT SUMMARY: how many rows disagree, split by the calculated flag ==='
WITH signed AS (
  SELECT j.id, j.office_id, j.account_id, j.entry_date,
         j.is_running_balance_calculated AS calc,
         CASE
           WHEN g.classification_enum IN (1,5) AND j.type_enum = 2 THEN  (j.amount*100)::numeric(19,0)
           WHEN g.classification_enum IN (1,5) AND j.type_enum = 1 THEN -(j.amount*100)::numeric(19,0)
           WHEN g.classification_enum IN (2,3,4) AND j.type_enum = 1 THEN  (j.amount*100)::numeric(19,0)
           ELSE -(j.amount*100)::numeric(19,0)
         END AS signed_minor,
         (j.office_running_balance      * 100)::numeric(19,0) AS stored_office_minor,
         (j.organization_running_balance* 100)::numeric(19,0) AS stored_org_minor
  FROM acc_gl_journal_entry j JOIN acc_gl_account g ON g.id = j.account_id
), d AS (
  SELECT id, calc,
         stored_org_minor - SUM(signed_minor) OVER (PARTITION BY account_id ORDER BY entry_date, id
              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS org_delta,
         stored_office_minor - SUM(signed_minor) OVER (PARTITION BY office_id, account_id ORDER BY entry_date, id
              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS office_delta
  FROM signed
)
SELECT calc AS is_running_balance_calculated,
       count(*) AS rows,
       count(*) FILTER (WHERE org_delta    = 0) AS org_agrees,
       count(*) FILTER (WHERE org_delta   <> 0) AS org_DISAGREES,
       count(*) FILTER (WHERE office_delta = 0) AS office_agrees,
       count(*) FILTER (WHERE office_delta<> 0) AS office_DISAGREES,
       max(abs(org_delta))    AS max_abs_org_delta_minor,
       max(abs(office_delta)) AS max_abs_office_delta_minor
FROM d GROUP BY calc ORDER BY calc;

\echo '=== Q5.3 the writer is also a READER: the seed query it uses to resume ==='
\echo '--- JournalEntryRunningBalanceUpdateServiceImpl:110-116 verbatim, entityDate = MIN ---'
\echo '--- entry_date of the not-yet-calculated rows. It SELECTS organization_running_balance. ---'
SELECT MIN(je.entry_date) AS entity_date_the_job_would_use
FROM acc_gl_journal_entry je WHERE je.is_running_balance_calculated = false;

\echo '=== Q5.4 offices in this tenant ==='
SELECT id, parent_id, name, hierarchy, opening_date FROM m_office ORDER BY id;
