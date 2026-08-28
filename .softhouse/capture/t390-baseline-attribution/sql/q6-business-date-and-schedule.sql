-- T390 Q6: is the autonomous accrual a ONE-OFF CATCH-UP or a DAILY DRIP?
-- Job 11 "Add Accrual Transactions" accrues up to the tenant's BUSINESS DATE. Job 32
-- "Increase Business Date by 1 day" reads is_active = f in q3-jobs.txt, so the business date
-- may be frozen -- in which case tomorrow's 00:01 run finds nothing left to accrue.
SELECT 'business dates' AS what, type::text AS a, date::text AS b, ''::text AS c
FROM m_business_date
UNION ALL
SELECT 'loan 8 dates', 'disbursedon=' || coalesce(l.disbursedon_date::text,'null'),
       'maturedon=' || coalesce(l.maturedon_date::text,'null'),
       'expected_maturedon=' || coalesce(l.expected_maturedon_date::text,'null')
FROM m_loan l WHERE l.id = 8
UNION ALL
SELECT 'loan 8 schedule periods', count(*)::text,
       'min=' || min(s.duedate)::text, 'max=' || max(s.duedate)::text
FROM m_loan_repayment_schedule s WHERE s.loan_id = 8
UNION ALL
SELECT 'loan 8 periods with duedate <= today''s business date',
       count(*)::text, '', ''
FROM m_loan_repayment_schedule s
WHERE s.loan_id = 8
  AND s.duedate <= (SELECT date FROM m_business_date WHERE type = 'BUSINESS_DATE')
UNION ALL
SELECT 'loan 8 accrual transactions so far (type 10)', count(*)::text,
       'max txn date=' || max(t.transaction_date)::text, ''
FROM m_loan_transaction t WHERE t.loan_id = 8 AND t.transaction_type_enum = 10 AND NOT t.is_reversed;
