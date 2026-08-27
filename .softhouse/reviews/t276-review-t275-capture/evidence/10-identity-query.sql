\pset border 2
SELECT m.id, m.product_id, m.financial_account_type AS fat, m.payment_type AS pt,
       m.charge_id, m.gl_account_id AS gl
FROM acc_product_mapping m WHERE m.product_id = 23 ORDER BY m.id;
SELECT max(id) AS max_acc_product_mapping_id FROM acc_product_mapping;
