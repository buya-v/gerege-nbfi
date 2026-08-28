\pset pager off
-- r13 showed 109 of 113 acc_gl_journal_entry rows carry last_modified_on_utc at/after the
-- scheduler window. WHAT changed, WHO changed it, and WHEN -- exactly.
SELECT date_trunc('second', last_modified_on_utc) AS modified_second,
       last_modified_by, count(*) AS rows, min(id) AS lo, max(id) AS hi,
       bool_and(is_running_balance_calculated) AS all_rb_calculated
  FROM acc_gl_journal_entry
 GROUP BY 1,2 ORDER BY 1;
-- creation vs modification for every row, bucketed
SELECT date_trunc('minute', created_on_utc) AS created_minute, created_by, count(*)
  FROM acc_gl_journal_entry GROUP BY 1,2 ORDER BY 1;
-- do the running-balance columns carry values? (this is what job 9 writes)
SELECT is_running_balance_calculated, count(*),
       count(office_running_balance) AS with_office_rb,
       count(organization_running_balance) AS with_org_rb
  FROM acc_gl_journal_entry GROUP BY 1 ORDER BY 1;
