\echo === R01.1 clock
select now() at time zone 'utc' as db_utc, current_setting('server_version') as pg;
\echo === R01.2 all columns of acc_gl_journal_entry, ordinal order
select ordinal_position, column_name, data_type, is_nullable
from information_schema.columns
where table_name='acc_gl_journal_entry' and table_schema=current_schema()
order by ordinal_position;
\echo === R01.3 column count
select count(*) as column_count from information_schema.columns
where table_name='acc_gl_journal_entry' and table_schema=current_schema();
\echo === R01.4 I-5 re-measurement
select count(*) total,
       count(*) filter (where last_modified_on_utc > created_on_utc) modified,
       count(*) filter (where last_modified_on_utc = created_on_utc) untouched,
       count(*) filter (where last_modified_on_utc is null) null_lm,
       count(*) filter (where last_modified_on_utc < created_on_utc) negative
from acc_gl_journal_entry;
\echo === R01.5 flag vs modified cross-tab
select is_running_balance_calculated, (last_modified_on_utc > created_on_utc) as modified, count(*)
from acc_gl_journal_entry group by 1,2 order by 1,2;
\echo === R01.6 legacy pair nullness / created_by / last_modified_by
select count(*) filter (where created_date is null) cd_null,
       count(*) filter (where lastmodified_date is null) lmd_null,
       count(*) filter (where last_modified_by=2) lmb_2,
       count(*) filter (where created_by=1) cb_1,
       count(*) filter (where created_by=2) cb_2,
       count(*) filter (where ref_num is null) refnum_null,
       count(*) filter (where reversed) reversed_true
from acc_gl_journal_entry;
