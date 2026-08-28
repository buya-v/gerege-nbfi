-- T390 Q9: the SIX labels t327's throwaway rig pins by STRING EQUALITY, re-derived live.
-- The six SELECTs are copied verbatim from the label loop at
--   t327/throwaway/capture.sh:71-76, down.sh:41-46, guard-throwaway-isolation.sh:116-121
-- so this capture answers exactly the question those scripts ask, and no adjacent one.
-- t305's rig pins only the FIRST FOUR of these -- it has no m_loan and no m_office label
-- [VERIFIED T390: `grep -rn m_loan` over the whole t305 throwaway directory = 0 hits].
SELECT 'acc_gl_journal_entry' AS label,
       count(*)||'/'||coalesce(max(id)::text,'null') AS live, '60/64' AS pinned_2026_08_27
FROM acc_gl_journal_entry
UNION ALL
SELECT 'acc_gl_closure', count(*)||'/'||coalesce(max(id)::text,'null'), '0/null' FROM acc_gl_closure
UNION ALL
SELECT 'distinct_transaction_id', count(DISTINCT transaction_id)::text, '26' FROM acc_gl_journal_entry
UNION ALL
SELECT 'm_portfolio_command_source', count(*)||'/'||coalesce(max(id)::text,'null'), '352/352'
FROM m_portfolio_command_source
UNION ALL
SELECT 'm_loan', count(*)::text, '7' FROM m_loan
UNION ALL
SELECT 'm_office', count(*)::text, '1' FROM m_office;
