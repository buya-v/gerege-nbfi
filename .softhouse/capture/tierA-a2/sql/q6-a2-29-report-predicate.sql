-- A2-29 / G-12: how load-bearing is the ONE report predicate that reads
-- office_running_balance?
--
-- READ-ONLY. Every statement is a SELECT.
--
-- `GeneralLedgerReport Table` (stretchy_report id 194, use_report = true on this oracle)
-- computes its `openingbalance` money cell with `... and je.office_running_balance is not
-- null ...` in the WHERE clause. On the ADOPTED schema the column is NOT NULL DEFAULT
-- 0.000000, so that predicate cannot exclude anything and the cell is a pure SUM over
-- je.amount. This measures how many rows the predicate admits vs excludes, so the claim
-- "it is a no-op HERE" is a count and not an assertion.
--
-- The `is null` arm CANNOT be exercised against this oracle at all: the NOT NULL
-- constraint makes the state unreachable. What is below is therefore a measurement of the
-- CURRENT population, not a demonstration of what a NULL-tolerant port would do.
\pset border 2

\echo '=== Q6.0 the constraint that makes the predicate a no-op HERE ==='
SELECT column_name, data_type, numeric_precision, numeric_scale, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'acc_gl_journal_entry'
  AND column_name IN ('office_running_balance','organization_running_balance',
                      'is_running_balance_calculated')
ORDER BY column_name;

\echo '=== Q6.1 rows the predicate ADMITS vs EXCLUDES, over the whole table ==='
SELECT count(*) AS all_rows,
       count(*) FILTER (WHERE office_running_balance IS NOT NULL) AS admitted_by_predicate,
       count(*) FILTER (WHERE office_running_balance IS NULL)     AS excluded_by_predicate
FROM acc_gl_journal_entry;

\echo '=== Q6.2 the openingbalance cell A2-472 observed, re-derived here in MINOR UNITS ==='
\echo '--- report parameters: officeId 1, GLAccountNO 4, startDate 2026-05-01 ---'
\echo '--- the report SQL uses `entry_date <= date(startDate) - interval 3 day` ---'
SELECT SUM(CASE WHEN je.type_enum = 2 THEN (je.amount*100)::numeric(19,0) ELSE 0 END)
     - SUM(CASE WHEN je.type_enum = 1 THEN (je.amount*100)::numeric(19,0) ELSE 0 END)
         AS openingbalance_minor_asset_or_expense,
       count(*) AS rows_summed
FROM m_office o
LEFT JOIN m_office ounder ON ounder.hierarchy LIKE concat(o.hierarchy, '%')
LEFT JOIN acc_gl_journal_entry je ON je.office_id = ounder.id
LEFT JOIN acc_gl_account aga1 ON aga1.id = je.account_id
WHERE je.entry_date <= date('2026-05-01') - interval '3 day'
  AND je.office_running_balance IS NOT NULL
  AND o.id = 1
  AND je.account_id = 4;
