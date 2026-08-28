-- T390 Q5: loan 8's transactions. T388's EXECUTE PERIODICACCRUALACCOUNTING produced 29/30/31
-- with tillDate 15 April 2026; L32/L33/L34 point at loan transactions 32/33/34, which T388
-- never asked for. This asks the loan's own ledger who created them and when.
SELECT t.id, t.loan_id, t.transaction_type_enum, t.transaction_date, t.amount,
       t.interest_portion_derived, t.fee_charges_portion_derived,
       t.penalty_charges_portion_derived, t.is_reversed, t.created_on_utc, t.created_by
FROM m_loan_transaction t
WHERE t.loan_id = 8
ORDER BY t.id;
