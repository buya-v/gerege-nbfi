-- T390 Q7: created_by = 2 on L32-L34 vs created_by = 1 on T388's L28-L31.
-- Who are those two app users? If 2 is the scheduler's system user, created_by separates
-- autonomous movement from API-driven movement.
-- (First attempt named is_self_service_user, which does not exist on this schema; ON_ERROR_STOP
--  made that a rc=3 refusal rather than a silent empty capture.)
SELECT id, username, firstname, lastname, email, is_deleted
FROM m_appuser
ORDER BY id;
