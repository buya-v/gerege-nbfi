\echo === S02.1 every column of acc_gl_journal_entry, in ordinal order ===
SELECT ordinal_position, column_name, data_type, numeric_precision, numeric_scale, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'acc_gl_journal_entry'
ORDER BY ordinal_position;

\echo === S02.2 the running-balance columns, populated? ===
SELECT count(*) AS total,
       count(organization_running_balance) AS org_rb_notnull,
       count(office_running_balance)       AS off_rb_notnull,
       count(*) FILTER (WHERE is_running_balance_calculated) AS rb_calculated_true,
       count(*) FILTER (WHERE NOT is_running_balance_calculated) AS rb_calculated_false,
       min(organization_running_balance) AS min_org_rb,
       max(organization_running_balance) AS max_org_rb
FROM acc_gl_journal_entry;

\echo === S02.3 the three derived columns per cohort ===
SELECT CASE WHEN id <= 75 THEN 'a: id <= 75' WHEN id <= 95 THEN 'b: 76-95'
            WHEN id <= 113 THEN 'c: 96-113' ELSE 'd: > 113' END AS cohort,
       count(*) AS n,
       count(*) FILTER (WHERE is_running_balance_calculated) AS calc_true,
       count(*) FILTER (WHERE organization_running_balance <> 0) AS org_rb_nonzero,
       count(*) FILTER (WHERE office_running_balance <> 0) AS off_rb_nonzero
FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;

\echo === S02.4 a worked sample: gl account 41 ordered by entry date, showing the running balance walking ===
SELECT id, office_id, account_id, entry_date, type_enum, amount,
       organization_running_balance, office_running_balance, is_running_balance_calculated,
       created_on_utc, last_modified_on_utc
FROM acc_gl_journal_entry WHERE account_id = 41 ORDER BY entry_date, id;
