# OH-1 — restore the ratified `gerege` tenant on the reference oracle

WORKING DIRECTORY: /Users/buv/oh-gerege-oh1  (branch ops/OH1-restore-gerege-tenant)
NEVER commit to `main`. NEVER touch the other worktrees.

## Why this is the only task that matters right now
Fourteen contexts are ported and CANNOT BE VERIFIED, because no parity vector can
be captured. The oracle serves ONE tenant:

    id 1 | default | Default Demo Tenant | Asia/Kolkata     (rounding ordinal 6 = HALF_EVEN)

CLAUDE.md ratifies HALF_UP (RoundingMode ordinal 4), MNT, Asia/Ulaanbaatar. A
capture taken from `default` records HALF_EVEN arithmetic under a HALF_UP
contract — worse than no vector, because it looks like evidence.

The `gerege` tenant EXISTED. Task T149 measured the rounding tie live on BOTH
tenants. This is RECOVERY of something that was lost, not invention.

## The oracle
  https://localhost:8443/fineract-provider/actuator/health -> {"status":"UP"}
  container `gerege-oracle-db`, PostgreSQL 18.3, user `postgres`
  databases present: fineract_tenants, fineract_default   (fineract_gerege is GONE)
  Fineract source, pinned: /Users/buv/fineract @ 426a23544
  Build recipe already in repo: .softhouse/bin/build-oracle-image.sh
  Connection facts of record: .softhouse/reference-oracle.md

## What to do
1. Read .softhouse/reference-oracle.md and docker-compose.yml FIRST. The stack is
   PostgreSQL-only by non-negotiable: no MySQL, no MariaDB, no Oracle Database,
   no :1521. If any step would start one, STOP.
2. Create the `gerege` tenant: a row in fineract_tenants.tenants, its
   tenant_server_connections row, and the fineract_gerege schema, migrated to the
   pinned commit's Liquibase state exactly as fineract_default is.
   Tenant parameters, all four ratified:
       identifier    gerege
       timezone_id   Asia/Ulaanbaatar
       rounding mode HALF_UP  (java.math.RoundingMode ordinal 4)
       currency      MNT (ISO 4217 numeric 496, 2 minor units)
3. Do NOT modify, drop or re-migrate `default`. It stays exactly as it is.

## DONE — one number, already measured, that cannot be faked
T149/T136 solved this tie live and recorded both answers:

    1,162,502.50 x 0.018 = 20,925.045
      HALF_UP    -> 20925.05   (gerege)
      HALF_EVEN  -> 20925.04   (default)

Drive that computation through the RUNNING oracle under the `gerege` tenant and
show it answering **20925.05**. Then run the same request under `default` and
show it answering **20925.04**, so the two tenants are demonstrably different and
you have not merely renamed one.

Paste RAW output with exit codes for:
   curl -sk https://localhost:8443/fineract-provider/actuator/health
   the tenants table, showing both rows
   the tie under gerege   -> 20925.05
   the tie under default  -> 20925.04

## Record it
Append the connection facts to .softhouse/reference-oracle.md: tenant identifier,
timezone, rounding mode AND ordinal, currency and minor units, schema name,
Postgres version, and the pinned Fineract commit. A later capture must be able to
state which tenant produced it.

## Refusals
- Do NOT edit any Go code, guard, harness, vector or pin.
- Do NOT start any non-PostgreSQL database engine.
- If the tenant cannot be created — a migration fails, an image will not build —
  record EXACTLY what failed in .softhouse/reference-oracle.md and STOP. Do not
  work around it by pointing anything at `default`.
- Never say complete / done / goal achieved. Report the two numbers.
