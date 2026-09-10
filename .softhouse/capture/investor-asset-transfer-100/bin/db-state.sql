-- OH-INV-Y READ-ONLY state capture. No writes. Tenant fineract_gerege.
\echo '## external_asset_owner_transfer 17'
SELECT id, loan_id, owner_id, external_loan_id, external_id, status,
       purchase_price_ratio, settlement_date, effective_date_from, effective_date_to, sub_status
FROM m_external_asset_owner_transfer WHERE id = 17;

\echo '## external_asset_owner_transfer_details rows (all)'
SELECT count(*) AS details_rows FROM m_external_asset_owner_transfer_details;
\echo '## details rows for transfer 17'
SELECT * FROM m_external_asset_owner_transfer_details WHERE asset_owner_transfer_id = 17;

\echo '## acc_gl_financial_activity_account'
SELECT id, financial_activity_type, gl_account_id FROM acc_gl_financial_activity_account ORDER BY id;

\echo '## acc_product_mapping for product 3 (count + rows)'
SELECT count(*) AS mapping_rows FROM acc_product_mapping WHERE product_id = 3;
SELECT mp.id, mp.product_id, mp.financial_account_type, mp.gl_account_id, ga.gl_code, ga.name
FROM acc_product_mapping mp JOIN acc_gl_account ga ON ga.id = mp.gl_account_id
WHERE mp.product_id = 3 ORDER BY mp.financial_account_type;

\echo '## gl account 6'
SELECT id, gl_code, name, classification_enum, account_usage FROM acc_gl_account WHERE id = 6;

\echo '## loan 12 product + principal'
SELECT ln.id, ln.product_id, ln.principal_amount, ln.loan_status_id, ln.loan_type_enum
FROM m_loan ln WHERE ln.id = 12;
SELECT pl.id, pl.name, pl.accounting_type FROM m_product_loan pl WHERE pl.id = 3;

\echo '## journal entries for entity_id = 17'
SELECT count(*) AS je_rows FROM acc_gl_journal_entry WHERE entity_id = 17;
SELECT id, office_id, account_id, entity_type_enum, entity_id, manual_entry, amount,
       transaction_date, reversed
FROM acc_gl_journal_entry WHERE entity_id = 17 ORDER BY id;

\echo '## loan 12 outstanding components (accounting accumulators)'
SELECT id, principal_amount, total_overpaid_derived, interest_outstanding_derived,
       fee_charges_outstanding_derived, penalty_charges_outstanding_derived,
       principal_outstanding_derived, total_outstanding_derived
FROM m_loan WHERE id = 12;

\echo '## rounding-mode + business date config'
SELECT id, name, value, enabled FROM c_configuration WHERE name IN
  ('rounding-mode','enable-business-date') ORDER BY name;
