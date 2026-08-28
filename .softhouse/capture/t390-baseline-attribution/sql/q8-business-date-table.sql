-- T390 Q8: Q6's first branch returned NO ROWS, which is a statement about m_business_date,
-- not about the query. Confirm the table exists and is empty -- if it is, the tenant has no
-- BUSINESS_DATE row and Fineract falls back to the system date, which is why job 11 accrued
-- loan 8 all the way to its 2026-07-15 maturity in one nightly run.
SELECT 'm_business_date exists' AS what, count(*)::text AS n
FROM information_schema.tables WHERE table_name = 'm_business_date'
UNION ALL
SELECT 'm_business_date rows', count(*)::text FROM m_business_date
UNION ALL
SELECT 'enabled business-date config', count(*)::text
FROM c_configuration WHERE name LIKE '%business%date%' AND enabled;
