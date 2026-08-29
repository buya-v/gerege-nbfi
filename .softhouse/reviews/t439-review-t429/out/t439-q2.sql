\echo === R02.1 ref_num distribution -- T429 JSON claims "NULL on every row in this tenant"
select count(*) total, count(ref_num) non_null, count(*)-count(ref_num) as null_cnt from acc_gl_journal_entry;
\echo === R02.2 sample of non-null ref_num
select id, transaction_id, ref_num, entity_type_enum, amount from acc_gl_journal_entry where ref_num is not null order by id limit 12;
\echo === R02.3 distinct ref_num values
select ref_num, count(*) from acc_gl_journal_entry where ref_num is not null group by 1 order by 2 desc limit 20;
\echo === R02.4 reversed / reversal_id -- T429 handoff says "3 reversals"
select count(*) filter (where reversed) reversed_true, count(reversal_id) reversal_id_non_null from acc_gl_journal_entry;
\echo === R02.5 the reversal rows
select id, transaction_id, reversed, reversal_id, type_enum, amount, account_id from acc_gl_journal_entry where reversed or reversal_id is not null order by id;
