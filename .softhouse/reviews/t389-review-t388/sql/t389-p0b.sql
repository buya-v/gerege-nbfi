\echo '=== T389 P0-3b: REDONE on created_on_utc (created_date is NULL in this schema) ==='
select 'T388 first write (L28-L31)' k, min(created_on_utc)::text v from acc_gl_journal_entry where transaction_id in ('L28','L29','L30','L31')
union all
select 'forbidden-account LAST write', max(created_on_utc)::text from acc_gl_journal_entry where account_id in (1,2,4,6,8,10,15,16,17,18,21,22)
union all
select 'forbidden rows at/after T388 first write', count(*)::text from acc_gl_journal_entry
  where account_id in (1,2,4,6,8,10,15,16,17,18,21,22)
    and created_on_utc >= (select min(created_on_utc) from acc_gl_journal_entry where transaction_id in ('L28','L29','L30','L31'));

\echo ''
\echo '=== T389 P0-3c: MAX je id per forbidden account vs T388 first je id (76) ==='
select max(id) as max_forbidden_je_id, (select min(id) from acc_gl_journal_entry where transaction_id in ('L28','L29','L30','L31')) as t388_min_je_id
from acc_gl_journal_entry where account_id in (1,2,4,6,8,10,15,16,17,18,21,22);

\echo ''
\echo '=== T389 P0-6b: gl_account_code -> id bindings the standing-oracle vectors pin ==='
select id, gl_code, name, classification_enum, manual_entries_allowed, disabled, parent_id
from acc_gl_account where gl_code in ('10000','10201','10300','10400','20100','40100','40300','99008') order by id;

\echo ''
\echo '=== T389 P0-6c: gl 15,18,22 (the three the brief singled out) ==='
select id, gl_code, name, manual_entries_allowed, disabled from acc_gl_account where id in (15,16,17,18,21,22) order by id;

\echo ''
\echo '=== T389 P0-9: gl 16 history -- when did it reach 21 rows? (T352 hazard account) ==='
select id, transaction_id, type_enum, amount, manual_entry, entry_date, created_on_utc
from acc_gl_journal_entry where account_id=16 order by id;

\echo ''
\echo '=== T389 P0-10: currencies present in the ledger ==='
select currency_code, count(*) from acc_gl_journal_entry group by currency_code order by 1;

\echo ''
\echo '=== T389 P0-11: MNT currency definition (ISO 496 / minor unit 2) ==='
select code, decimal_places, currency_multiplesof, name, internationalized_name_code from m_organisation_currency where code in ('MNT','USD');
select code, decimal_places, name from m_currency where code='MNT';
