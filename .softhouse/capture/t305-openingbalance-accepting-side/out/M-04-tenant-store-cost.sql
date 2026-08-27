-- T305 M-2 -- WHAT A FRESH TENANT WOULD ACTUALLY COST.  READ-ONLY, against fineract_tenants.
--
-- The brief asks whether a new tenant "can be created and torn down cleanly". Fineract's
-- own answer, from the pinned checkout @426a23544, is that there is NO RUNTIME PATH AT ALL:
--
--   * there is no tenant-administration REST resource in this build. `grep -rn
--     "TenantsApiResource" --include="*.java"` over /Users/buv/fineract matches NOTHING;
--     the only file whose name contains Tenant and ApiResource is
--     fineract-security/.../TenantOidcConfigApiResource.java, which serves OIDC config.
--   * tenant onboarding is a STARTUP path. TenantDatabaseUpgradeService implements
--     InitializingBean and does its work in afterPropertiesSet() -- upgradeTenantStore()
--     then upgradeIndividualTenants(), which iterates tenantDetailsService.findAllTenants()
--     and runs liquibase per tenant. Nothing re-enters it while the process is live.
--
-- So creating a tenant means: make a PostgreSQL database by hand, hand-write rows into the
-- SHARED registry below, and RESTART THE REFERENCE ORACLE so liquibase migrates it. This
-- query measures the two halves of that cost that are measurable from here: how large the
-- migrated schema is, and how much of the shared registry the write would touch.

\echo '== A. the registry rows a new tenant would have to be hand-written into.'
SELECT t.id, t.identifier, t.name, t.timezone_id, t.oltp_id, t.report_id
  FROM tenants t ORDER BY t.id;

SELECT c.id, c.schema_name, c.schema_server, c.schema_server_port, c.schema_username
  FROM tenant_server_connections c ORDER BY c.id;

\echo '== B. every table in the shared registry -- the blast radius of a hand-written row.'
SELECT table_name
  FROM information_schema.tables
 WHERE table_schema = 'public' ORDER BY table_name;

\echo '== C. the liquibase state a restart would re-enter, and how big a tenant schema is.'
SELECT count(*) AS tenant_store_changelog_rows,
       max(dateexecuted) AS last_executed,
       max(orderexecuted) AS last_order
  FROM databasechangelog;

\echo '== D. the databases on this server -- a new tenant adds one, permanently or not.'
SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
  FROM pg_database WHERE datistemplate = false ORDER BY datname;
