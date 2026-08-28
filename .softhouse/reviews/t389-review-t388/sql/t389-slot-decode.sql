\echo '=== T389 S-1: acc_gl_account state -- codes vector-pinned, and whether ANY pre-existing account was EDITED ==='
select id, gl_code, name, classification_enum, manual_journal_entries_allowed, disabled, account_usage, parent_id
from acc_gl_account where gl_code in ('10000','10201','10300','10400','20100','40100','40300','99008') order by id;
\echo '-- gl 15,16,17,18,21,22 --'
select id, gl_code, name, manual_journal_entries_allowed, disabled from acc_gl_account where id in (15,16,17,18,21,22) order by id;
\echo '-- code collision between T388 accounts (>=35) and any vector-pinned code --'
select count(*) as collisions from acc_gl_account where id>=35 and gl_code in ('10000','10201','10300','10400','20100','40100','40300','99008','T305-1000','T305-1100','T305-2000','T305-3000','T327-1000','T327-1100','T327-2000');

\echo ''
\echo '=== T389 S-2: product 63 -- accounting_type and its FULL account mapping ==='
select id, name, accounting_type, currency_code, currency_digits, currency_multiplesof from m_product_loan where id in (28,63) order by id;
\echo '-- acc_product_mapping for product 63 --'
select id, product_id, gl_account_id, product_type, payment_type, charge_id, financial_account_type
from acc_product_mapping where product_id=63 order by financial_account_type;
\echo '-- is gl_account_id -> financial_account_type a FUNCTION on product 63? (distinct accounts vs distinct mappings) --'
select count(*) as mappings, count(distinct gl_account_id) as distinct_accounts, count(distinct financial_account_type) as distinct_slots from acc_product_mapping where product_id=63;
\echo '-- do any of product 63 accounts also appear on ANOTHER product with a DIFFERENT slot? (the gl-16 trap) --'
select m.gl_account_id, m.product_id, m.financial_account_type
from acc_product_mapping m
where m.gl_account_id in (select gl_account_id from acc_product_mapping where product_id=63)
order by m.gl_account_id, m.product_id;

\echo ''
\echo '=== T389 S-3: the nine claimed receivable-slot entries, decoded via acc_product_mapping JOIN (independent of T388 SQL) ==='
select j.id as je, j.transaction_id, j.entry_date, 
       case j.type_enum when 1 then 'CREDIT' when 2 then 'DEBIT' else '?' end as dr_cr,
       j.account_id as gl, a.gl_code, j.amount, j.currency_code, j.manual_entry,
       lt.id as loan_txn, lt.transaction_type_enum as txn_type,
       l.id as loan, l.product_id, p.accounting_type,
       pm.financial_account_type as slot
from acc_gl_journal_entry j
join acc_gl_account a on a.id=j.account_id
left join m_loan_transaction lt on lt.id=j.loan_transaction_id
left join m_loan l on l.id=lt.loan_id
left join m_product_loan p on p.id=l.product_id
left join acc_product_mapping pm on pm.product_id=l.product_id and pm.gl_account_id=j.account_id
where j.id>75 order by j.id;

\echo ''
\echo '=== T389 S-4: double entry, in INTEGER MINOR UNITS, per transaction (no float) ==='
select transaction_id,
       sum(case when type_enum=2 then (amount*100)::numeric(30,0) else 0 end) as debit_minor,
       sum(case when type_enum=1 then (amount*100)::numeric(30,0) else 0 end) as credit_minor,
       sum(case when type_enum=2 then (amount*100)::numeric(30,0) else -(amount*100)::numeric(30,0) end) as diff_minor,
       count(*) legs
from acc_gl_journal_entry where transaction_id in ('L28','L29','L30','L31')
group by transaction_id order by transaction_id;
\echo '-- do any T388 amounts have a non-zero third decimal (would mean sub-minor-unit precision)? --'
select id, amount, (amount*100)::numeric(30,6) as minor_units_exact from acc_gl_journal_entry where id>75 and (amount*100) <> trunc(amount*100);

\echo ''
\echo '=== T389 S-5: loan transactions 28-31 ==='
select id, loan_id, transaction_type_enum, transaction_date, amount, is_reversed, created_on_utc
from m_loan_transaction where loan_id=8 order by id;

\echo ''
\echo '=== T389 S-6: enum meaning check -- ALL journal entries in the tenant that arrived through a receivable slot (7,8,9) on an ACCRUAL product ==='
select j.id, j.transaction_id, j.account_id, pm.financial_account_type as slot, p.accounting_type
from acc_gl_journal_entry j
join m_loan_transaction lt on lt.id=j.loan_transaction_id
join m_loan l on l.id=lt.loan_id
join m_product_loan p on p.id=l.product_id
join acc_product_mapping pm on pm.product_id=l.product_id and pm.gl_account_id=j.account_id
where pm.financial_account_type in (7,8,9) and p.accounting_type=3
order by j.id;
