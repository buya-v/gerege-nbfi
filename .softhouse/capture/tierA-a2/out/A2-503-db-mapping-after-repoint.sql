-- T275: acc_product_mapping WITH ITS PRIMARY KEY.
--
-- WHY THIS FILE EXISTS AND q2 IS NOT ENOUGH.
-- sql/q2-product-mapping-rows.sql selects everything about a mapping EXCEPT `m.id`.
-- The question CAPTURE-PLAN.md §5 row 1 left open is "does a product UPDATE mutate the
-- existing mapping row, or DELETE it and INSERT a replacement?" -- and those two are
-- INDISTINGUISHABLE in q2's projection. The identity value IS the observation, so it is
-- selected first here.
--
-- The ORDER BY is on m.id, not on the semantic key, for the same reason: insertion order
-- is what shows a recreate. Nothing is filtered by product beyond q2's own `>= 22` floor,
-- so a row that moves between products, or a row created with charge_id /
-- write_off_reason_id set for the first time on this oracle, cannot hide.
--
-- product_type 1 = LOAN (PortfolioProductType.LOAN).
-- financial_account_type is the CashAccountsForLoan / AccrualAccountsForLoan
-- ordinal-valued key; the SAME smallint means DIFFERENT things per the product's
-- accounting rule, so p.accounting_type is joined in.
\pset border 2
SELECT m.id AS mapping_id,
       m.product_id,
       p.accounting_type,
       m.product_type,
       m.financial_account_type,
       m.payment_type,
       m.charge_id,
       m.charge_off_reason_id,
       m.write_off_reason_id,
       m.capitalized_income_classification_id AS cap_inc_class_id,
       m.buydown_fee_classification_id AS buydown_class_id,
       m.gl_account_id,
       g.gl_code,
       g.name AS gl_name,
       g.account_usage,
       g.classification_enum
FROM acc_product_mapping m
JOIN acc_gl_account g ON g.id = m.gl_account_id
JOIN m_product_loan p ON p.id = m.product_id
WHERE m.product_id >= 22
ORDER BY m.id;

-- The high-water mark of the identity sequence. A recreate consumes identity values even
-- when the row COUNT is unchanged, so this discriminates "updated in place" from
-- "deleted and reinserted" independently of the projection above.
SELECT max(id) AS max_mapping_id, count(*) AS mapping_rows FROM acc_product_mapping;
