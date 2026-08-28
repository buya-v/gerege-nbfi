\echo '=== T389 P0-1: EVERY journal entry row on a FORBIDDEN account (T389 independent set) ==='
\echo 'forbidden = {1,2,4,6,8,10,15,16,17,18,21,22}'
select account_id, count(*) as rows,
       min(id) as min_je, max(id) as max_je,
       min(created_date) as first_created, max(created_date) as last_created
from acc_gl_journal_entry
where account_id in (1,2,4,6,8,10,15,16,17,18,21,22)
group by account_id order by account_id;

\echo ''
\echo '=== T389 P0-2: per-forbidden-account count including ZERO-row accounts (left join) ==='
select f.gl, coalesce(count(j.id),0) as rows_now
from (values (1),(2),(4),(6),(8),(10),(15),(16),(17),(18),(21),(22)) f(gl)
left join acc_gl_journal_entry j on j.account_id = f.gl
group by f.gl order by f.gl;

\echo ''
\echo '=== T389 P0-3: THE DECISIVE TEST -- any forbidden-account row created AT OR AFTER the earliest T388 row? ==='
\echo 'If T388 contaminated a promoted account, a forbidden row would carry a T388-era created_date.'
select (select min(created_date) from acc_gl_journal_entry where transaction_id in ('L28','L29','L30','L31')) as t388_first_write,
       (select max(created_date) from acc_gl_journal_entry where account_id in (1,2,4,6,8,10,15,16,17,18,21,22)) as forbidden_last_write;

select 'FORBIDDEN ROWS AT/AFTER T388 FIRST WRITE' as label, count(*) as n
from acc_gl_journal_entry
where account_id in (1,2,4,6,8,10,15,16,17,18,21,22)
  and created_date >= (select min(created_date) from acc_gl_journal_entry where transaction_id in ('L28','L29','L30','L31'));

\echo ''
\echo '=== T389 P0-4: EVERY journal entry with id > 75 (T388 declared before-max = 75) ==='
select id, transaction_id, account_id, type_enum, amount, currency_code, manual_entry,
       loan_transaction_id, entry_date, created_date
from acc_gl_journal_entry where id > 75 order by id;

\echo ''
\echo '=== T389 P0-5: distinct accounts touched by entries id>75, and intersection with forbidden ==='
select distinct account_id from acc_gl_journal_entry where id > 75 order by account_id;
select 'INTERSECTION (must be EMPTY)' as label, array_agg(distinct account_id order by account_id) as accts
from acc_gl_journal_entry
where id > 75 and account_id in (1,2,4,6,8,10,15,16,17,18,21,22);

\echo ''
\echo '=== T389 P0-6: gl_account_code pins read by standing-oracle vectors -- are code->id bindings intact? ==='
select id, gl_code, name, classification_enum, manual_entries_allowed, disabled
from acc_gl_account
where gl_code in ('10000','10201','10300','10400','20100','40100','40300','99008')
order by id;

\echo ''
\echo '=== T389 P0-7: did T388 mint any gl_code colliding with a vector-pinned code? ==='
select id, gl_code, name from acc_gl_account where id >= 35 order by id;

\echo ''
\echo '=== T389 P0-8: total ledger counters now ==='
select 'acc_gl_journal_entry' t, count(*) n, max(id) mx from acc_gl_journal_entry
union all select 'distinct transaction_id', count(distinct transaction_id), null from acc_gl_journal_entry
union all select 'm_portfolio_command_source', count(*), max(id) from m_portfolio_command_source
union all select 'acc_gl_account', count(*), max(id) from acc_gl_account
union all select 'm_product_loan', count(*), max(id) from m_product_loan
union all select 'acc_product_mapping', count(*), max(id) from acc_product_mapping
union all select 'm_client', count(*), max(id) from m_client
union all select 'm_loan', count(*), max(id) from m_loan
union all select 'm_loan_transaction', count(*), max(id) from m_loan_transaction
union all select 'acc_gl_closure', count(*), max(id) from acc_gl_closure
union all select 'm_office', count(*), max(id) from m_office;
