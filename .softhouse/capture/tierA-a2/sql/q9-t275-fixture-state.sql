-- T275: the FIXTURE STATE the §5 exclusions were justified by.
--
-- CAPTURE-PLAN.md §5 excluded three groups of captures on fixture grounds:
--   * fee/penalty charge mappings   -- "needs an m_charge fixture; none exists on gerege"
--   * charge-off / write-off reason -- "need m_code_value code values seeded first"
--   * capitalized-income / buy-down -- "needs capitalized-income / buy-down product config"
--
-- A successor must not inherit those exclusions on the strength of the sentence alone.
-- This query MEASURES each of them against the oracle as it stands, so the next worker
-- reads a fact with a timestamp on it rather than a claim from an earlier fire. The
-- acc_product_mapping DDL is included because which of the four reason/classification
-- columns carries a foreign key is the whole of §3 row 15.
\pset border 2

\echo '--- m_charge: is there a charge fixture at all, and are any of them penalties? ---'
SELECT id, name, currency_code, is_penalty, charge_applies_to_enum, charge_time_enum,
       charge_calculation_enum, amount, is_active, is_deleted
FROM m_charge
ORDER BY id;

\echo '--- m_code: do the reason code TYPES exist? ---'
SELECT id, code_name, is_system_defined
FROM m_code
WHERE code_name IN ('WriteOffReasons', 'ChargeOffReasons')
ORDER BY id;

\echo '--- m_code_value: are any reason VALUES seeded under them? (the actual blocker) ---'
SELECT cv.id, cv.code_id, c.code_name, cv.code_value, cv.is_active
FROM m_code_value cv
JOIN m_code c ON c.id = cv.code_id
WHERE c.code_name IN ('WriteOffReasons', 'ChargeOffReasons')
ORDER BY cv.id;

\echo '--- m_code_value: total row count, so an empty result above is not read as an empty table ---'
SELECT count(*) AS total_code_values FROM m_code_value;

\echo '--- m_payment_type: the second resolution dimension, for reference ---'
SELECT id, value, is_cash_payment, code_name, is_system_defined
FROM m_payment_type
ORDER BY id;

\echo '--- acc_product_mapping DDL: which reason/classification columns carry an FK ---'
\d acc_product_mapping
