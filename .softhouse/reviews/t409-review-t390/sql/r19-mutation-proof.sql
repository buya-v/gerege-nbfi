\pset pager off
-- DECISIVE TEST for "the scheduler MUTATED rows that already existed", as opposed to merely
-- stamping last_modified_on_utc at insert time: last_modified_on_utc STRICTLY LATER than
-- created_on_utc, and created strictly before the scheduler window.
SELECT count(*) AS rows_created_before_the_window_and_modified_inside_it
  FROM acc_gl_journal_entry
 WHERE created_on_utc < TIMESTAMPTZ '2026-08-28 16:00:00+00'
   AND last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00';
SELECT count(*) AS rows_where_modified_is_strictly_later_than_created
  FROM acc_gl_journal_entry WHERE last_modified_on_utc > created_on_utc;
SELECT min(created_on_utc) AS oldest_mutated_row_created,
       min(last_modified_on_utc) AS earliest_mutation,
       max(last_modified_on_utc) AS latest_mutation,
       count(*) AS n
  FROM acc_gl_journal_entry
 WHERE created_on_utc < TIMESTAMPTZ '2026-08-28 16:00:00+00'
   AND last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00';
-- and the writer of those mutations
SELECT last_modified_by, count(*) FROM acc_gl_journal_entry
 WHERE created_on_utc < TIMESTAMPTZ '2026-08-28 16:00:00+00'
   AND last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00'
 GROUP BY 1;
-- which job run brackets THOSE mutations?
WITH w AS (SELECT min(last_modified_on_utc AT TIME ZONE 'UTC') a,
                  max(last_modified_on_utc AT TIME ZONE 'UTC') b
             FROM acc_gl_journal_entry
            WHERE created_on_utc < TIMESTAMPTZ '2026-08-28 16:00:00+00'
              AND last_modified_on_utc >= TIMESTAMPTZ '2026-08-28 16:00:00+00')
SELECT h.id, h.job_id, j.name, h.start_time, h.end_time, w.a AS first_mutation, w.b AS last_mutation
  FROM job_run_history h JOIN job j ON j.id=h.job_id, w
 WHERE h.start_time <= w.b AND h.end_time >= w.a
 ORDER BY h.start_time;
