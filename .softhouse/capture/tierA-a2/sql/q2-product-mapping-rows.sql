-- A2: what the oracle ACTUALLY STORES in acc_product_mapping for the products
-- created by run-060-mappings.sh.
--
-- product_type 1 = LOAN (PortfolioProductType.LOAN)
-- financial_account_type is the CashAccountsForLoan / AccrualAccountsForLoan
-- ordinal-valued key. The SAME smallint means DIFFERENT things depending on the
-- product's accounting rule, so the product's accounting_type is joined in.
\pset border 2
SELECT m.product_id,
       p.accounting_type,
       m.product_type,
       m.financial_account_type,
       m.payment_type,
       m.charge_id,
       m.gl_account_id,
       g.gl_code,
       g.name AS gl_name,
       g.account_usage,
       g.classification_enum
FROM acc_product_mapping m
JOIN acc_gl_account g ON g.id = m.gl_account_id
JOIN m_product_loan p ON p.id = m.product_id
WHERE m.product_id >= 22
ORDER BY m.product_id, m.financial_account_type, m.payment_type NULLS FIRST, m.id;
