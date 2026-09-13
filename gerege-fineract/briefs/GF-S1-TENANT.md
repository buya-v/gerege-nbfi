# GF-S1 — configure a Gerege tenant on a throwaway Fineract, and measure what configuration cannot do

Worktree: `/Users/buv/gf-s1` (branch `feat/GF-S1`). Read `gerege-fineract/SPIKE-PLAN.md` and
`gerege-fineract/DECISIONS.md` first; nothing else in the repository concerns you.
**Write and commit ONLY under `gerege-fineract/spike/s1-tenant/`.** Touch no other folder. Never write into
`/Users/buv/fineract` (read-only reference source). Never touch the standing reference instance (port 8443, containers
`gerege-oracle-*`, `fineract-db-1`) or any `tierd-*` / `gf2-*` container. The driver pushes; never push.

## Why
Buyan is testing whether Apache Fineract can be Gerege NBFI's production core. This step proves the Gerege tenant can be
set up with configuration alone, and measures honestly what configuration CANNOT do. Those gaps become extensions in S3.

## Steps — commit after each (`git commit -F <file> </dev/null`, message file inside the worktree)
1. **Throwaway up.** Write `compose.yml`: containers `gf1-db` (image `postgres:18.3`) and `gf1-app` (image
   `fineract:latest`, id `e596339626bf`), host port **8445** → 8443. Copy the shape of
   `.softhouse/capture/tierd-feasibility/throwaway/docker-compose.tierd.yml` (read it; do not edit it). Tenant
   identifier `gspike`, DB `fineract_gspike`, `FINERACT_DEFAULT_TENANTDB_TIMEZONE: Asia/Ulaanbaatar`,
   `FINERACT_CONFIG_ROUNDING_MODE: "4"`. The env files and init script under `/Users/buv/fineract/config/docker` may
   be mounted READ-ONLY. Before starting, record `docker ps` and read-only counts on the standing reference in
   `isolation-before.txt`: for EACH of the databases `fineract_gerege` (holds the 18 standing loans) and
   `fineract_default`, run `docker exec gerege-oracle-db psql -U root -d <db> -tAc 'select count(*) from m_loan'`, and
   the same for `m_portfolio_command_source`. Wait for health with a bounded loop.
2. **Configure by REST.** Write an idempotent `configure.sh` (`curl -sk --max-time 30`, tenant header `gspike`, stock
   demo credentials `mifos:password`, API `https://localhost:8445/fineract-provider/api/v1`) that:
   - enables currency **MNT** (2 decimal places);
   - creates a minimal chart of GL accounts: loan portfolio, interest/fee/penalty receivable, interest income, fee
     income, fund source, overpayment liability, write-off, suspense;
   - creates payment types `Cash`, `Banksuljee RTGS`, `ACH+`;
   - creates TWO loan products in MNT with accrual accounting mapped to those accounts: (a) declining-balance EMI,
     monthly, and (b) flat interest, monthly.
   Save every request and response body under `evidence/` with a `manifest.json` (path, sha256).
3. **Smoke a loan end to end.** Create a client, a loan on product (a), approve, disburse MNT 1,000,000.00, then
   repay one instalment. Read back the loan, its schedule and `GET /journalentries?loanId=<id>&limit=-1`. Save all
   bodies to `evidence/`.
4. **Measure the three gaps** and record each result, with its evidence file, in `FINDINGS.md`:
   - **Deposits:** list the savings products (there must be none). List the savings permissions. Remove them from
     every role except the super user, and record whether a NON-super user can still reach savings endpoints: create a
     user with a role that lacks them, and try `GET /savingsproducts` and `POST /savingsproducts`. Record exactly what
     config can and cannot prevent.
   - **Idempotency:** send the same repayment twice with header `Idempotency-Key: gf1-test-1`, and once with no
     header. Record whether the duplicate is deduplicated (the status and resourceId of both) and whether the request
     without a header is accepted. Also search the pinned source READ-ONLY for how the key is handled
     (`fineract-command/.../CommandProperties.java`) and cite file:line.
   - **Reversals:** undo the repayment, then read the journal entries again. Record whether the original legs are
     untouched and reversal legs are appended, citing leg ids before and after.
5. **Tear down.** `docker compose -f compose.yml down -v` for the `gf1-*` containers only. Repeat the isolation
   counts into `isolation-after.txt`; they must equal the "before" values. Write `OWNER.md`: what configured natively,
   what did not, and the three findings. Money in `OWNER.md` and `FINDINGS.md` is integer minor units (MNT: 2 digits),
   for example 100000000 for MNT 1,000,000.00.

## Rules
- Every command in the FOREGROUND with a bound; never `&`, `jobs`, `wait`, or `sleep` over 60 seconds.
- Never create or edit `AGENTS.md`. Never bypass a git hook (`-c core.hooksPath`, `--no-verify`). If a commit does not
  return, STOP and say so.
- PostgreSQL only; **Oracle Database is prohibited.** Never write to tenants `gerege` or `default` on the standing
  reference instance. SQL against it is read-only counts only.
- If a step fails, record the failure and the evidence, still tear down, and finish. A documented gap is a result.
- About 300 iterations. Commit the throwaway compose and first evidence by iteration 100.
