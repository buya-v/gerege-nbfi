\pset pager off
-- Grouped by transaction, distinct authoring users, exact write-time window (UTC, full precision).
SELECT j.transaction_id,
       count(*) AS legs,
       min(j.id) AS lo, max(j.id) AS hi,
       string_agg(DISTINCT j.created_by::text, ',') AS created_by,
       min(j.created_on_utc) AS first_write_utc,
       max(j.created_on_utc) AS last_write_utc,
       min(j.entry_date) AS entry_date,
       sum(CASE WHEN j.type_enum=2 THEN j.amount ELSE 0 END) AS credits,
       sum(CASE WHEN j.type_enum=1 THEN j.amount ELSE 0 END) AS debits
  FROM acc_gl_journal_entry j
 GROUP BY j.transaction_id
 ORDER BY min(j.id);
