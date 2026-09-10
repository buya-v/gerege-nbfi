# Capture owner — investor / ASSET_TRANSFER settlement

**Subject:** settle external-asset-owner transfer **17** (loan 12, product 3, tenant `gerege`)
by creating the missing **ASSET_TRANSFER (100)** financial-activity account mapping through
the API, then confirm the posted journal entries equal the loan **outstanding**, not
`0.9725 × outstanding`.

- **Context:** `investor` (one bounded context).
- **Run:** OH-INV-Y, branch `feat/OHINVy`, worktree `/Users/buv/oh-gerege-invy`.
- **Oracle:** Fineract reference implementation, pinned commit
  `426a23544e8426a38ae43ae404670a0a7e85b9eb`, tenant `gerege` on PostgreSQL.
- **Auth:** `Authorization: Basic <mifos:password>`, `Fineract-Platform-TenantId: gerege`.
- **Base URL:** `https://localhost:8443/fineract-provider/api/v1` (self-signed TLS).

Names freeze at first commit. `*.dump` under `capture/` is gitignored; snapshots live in
`/Users/buv/gerege-oracle-snapshots/`.

## What inherits

- Transfer 17 on loan 12, status PENDING, `purchasePriceRatio` `"97.25"`, settlementDate
  2026-09-02, details absent. Business date 2026-09-02. `LOAN_CLOSE_OF_BUSINESS` carries
  `EXTERNAL_ASSET_OWNER_TRANSFER` at order 7. Product 3 ACCRUAL PERIODIC with 12 mapping rows.
- The only reference data this run may create is the ASSET_TRANSFER(100) mapping, via
  `POST /v1/financialactivityaccounts`.

## Directory

- `bin/` — capture rig (this run's scripts).
- `req/` — request bodies (byte-stable).
- `out/` — observed responses, statuses, read-backs, log slices.
