\echo === R03.1 is ref_num the empty string?
select coalesce('['||ref_num||']','NULL') as val, length(ref_num) as len, count(*)
from acc_gl_journal_entry group by 1,2 order by 3 desc;
\echo === R03.2 attribution window -- the 91 modified rows
select count(*) n, count(distinct last_modified_by) distinct_modifiers,
       min(last_modified_on_utc) win_start, max(last_modified_on_utc) win_end
from acc_gl_journal_entry where last_modified_on_utc > created_on_utc;
\echo === R03.3 the 8 reversed rows -- are they inside the 91, and what is their last_modified?
select id, created_on_utc, last_modified_on_utc, (last_modified_on_utc>created_on_utc) modified
from acc_gl_journal_entry where reversed order by id;
\echo === R03.4 the 18 untouched rows creation window
select count(*) n, min(created_on_utc), max(created_on_utc), min(id), max(id)
from acc_gl_journal_entry where last_modified_on_utc = created_on_utc;
\echo === R03.5 job_run_history around that instant
select jrh.id, j.job_name, jrh.start_time, jrh.end_time, jrh.status, jrh.trigger_type
from job_run_history jrh join job j on j.id=jrh.job_id
where jrh.start_time >= timestamp '2026-08-28 16:00:00' and jrh.start_time < timestamp '2026-08-28 16:05:00'
order by jrh.start_time;
\echo === R03.6 entry 96 -- derived running balance on account 41
select id, transaction_id, entry_date, type_enum, amount, account_id,
       is_running_balance_calculated, organization_running_balance, office_running_balance
from acc_gl_journal_entry where account_id=41 order by entry_date, id;
\echo === R03.7 account 41 classification
select id, gl_code, name, classification_enum from acc_gl_account where id=41;
