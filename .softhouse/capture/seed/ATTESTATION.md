# OH-SEED — Seed rig attestation

Tenant: `gerege` (never `default`).
Repo: `/Users/buv/oh-gerege-seed`, branch `feat/OHSEED-oracle-rig`.
API: `https://localhost:8443/fineract-provider/api/v1`.
Reference oracle: PostgreSQL (`gerege-oracle-db`, db `fineract_gerege`), read-only.

## Pinned business date

- `BUSINESS_DATE = [2026, 9, 1]` → **01 September 2026**
- `COB_DATE      = [2026, 8, 31]`

Every loan date below is relative to this pinned date, never to `date`/`now()`.

## Configuration rows (before / after)

`enable-business-date` is the only configuration row this rig writes. Its
"before" value cannot be reconstructed — a prior session had already set it;
this rig PUTs `{"enabled":true}` idempotently.

| name                   | enabled | value (int) | note                                   |
|------------------------|---------|-------------|----------------------------------------|
| enable-business-date   | t       | (null)      | set by rig, idempotent PUT             |
| rounding-mode          | t       | 4           | **HALF_UP — unchanged**                |

### Rounding-mode re-check

`GET /configurations/name/rounding-mode` → `{"value":4,...}` and SQL
`SELECT value FROM c_configuration WHERE name='rounding-mode'` → `4`.

4 = HALF_UP. Verified unchanged at the end. **Constraint satisfied.**

## IDs created

| Object             | externalId / key | id  | name / code                     | case file(s)                              |
|--------------------|------------------|-----|---------------------------------|-------------------------------------------|
| GL asset           | asset            | 1   | SEED-Provisioning-Asset / SEED-10001 | gl-SEED-10001-raw.json                |
| GL liability       | liability        | 2   | SEED-Provisioning-Liability / SEED-20001 | gl-SEED-20001-raw.json            |
| GL income          | income           | 3   | SEED-Provisioning-Income / SEED-40001 | gl-SEED-40001-raw.json               |
| GL expense         | expense          | 4   | SEED-Provisioning-Expense / SEED-50001 | gl-SEED-50001-raw.json              |
| Provisioning criteria | criteria      | 1   | SEED-Probe-Criteria             | provisioningcriteria-raw.json             |
| Loan product       | loanProduct      | 2   | SEED-Probe-Loan                 | loanproduct-raw.json                      |
| Client             | SEED-C11         | 5   | SEED-C11 Borrower               | client-SEED-C11-raw.json                  |
| Client             | SEED-C12         | 6   | SEED-C12 Borrower               | client-SEED-C12-raw.json                  |
| Client             | SEED-C13         | 7   | SEED-C13 Borrower               | client-SEED-C13-raw.json                  |
| Loan (disbursed)   | SEED-L01         | 1   | —                               | loan-SEED-L01-{submit,approve,disburse}-raw.json |
| Loan (disbursed)   | SEED-L02         | 2   | —                               | loan-SEED-L02-{submit,approve,disburse}-raw.json |
| Loan (disbursed)   | SEED-L03         | 3   | —                               | loan-SEED-L03-{submit,approve,disburse}-raw.json |

## Provisioning criteria definitions (criteria id 1)

| category | categoryId | minAge | maxAge | percentage | liability | expense |
|----------|-----------|--------|--------|------------|-----------|---------|
| STANDARD     | 1 | 0  | 29  | 1.00  | 2 | 4 |
| SUB-STANDARD | 2 | 30 | 59  | 25.00 | 2 | 4 |
| DOUBTFUL     | 3 | 60 | 89  | 50.00 | 2 | 4 |
| LOSS         | 4 | 90 | 36500 | 100.00 | 2 | 4 |

## Loan age bands (relative to pinned business date 2026-09-01)

| Loan     | disbursed / first-overdue | overdue days | provisioning band |
|----------|---------------------------|--------------|-------------------|
| SEED-L01 | overdue since 2026-07-01  | 62           | DOUBTFUL (60–89)  |
| SEED-L02 | overdue since 2026-08-01  | 31           | SUB-STANDARD (30–59) |
| SEED-L03 | due 2026-09-01 (not yet overdue) | 0     | STANDARD (0–29)   |

Three distinct bands — exceeds the "at least two age bands" requirement.

## Read-only SQL verification

```
gl_accounts           = 4   (4 SEED-)
provisioning_criteria = 1   (criteria_definitions = 4)
clients               = 7   (6 SEED-)
loan_products_seed    = 1
loans                 = 3   (3 SEED-, 3 disbursed, loan_status_id = 300)
rounding-mode value   = 4   (HALF_UP)
```

## Two-run idempotence proof

`run.sh` re-ran the full rig a second time. Snapshot (counts of every SEED-
keyed object) captured before and after; `diff` was **empty** — the second run
created nothing new. Every step is check-then-create keyed on `SEED-` externalId
/ name / glCode.

## Stale artifacts from an earlier attempt (honest note)

`m_client` also contains three `SEED-C01`, `SEED-C02`, `SEED-C03` rows (ids 2–4,
activation 2026-09-01) left behind by an earlier aborted attempt. They are
unused (no loans, no transactions), and the current rig keys on `SEED-C11/12/13`
(ids 5–7, activation 2026-05-01) so that back-dated loans pass the
"submitted >= activation" rule. `clients_seed = 6` in the idempotence snapshot
counts both sets; MANIFEST lists only the three clients this rig manages.

## Deviations / notes

- **Step ordering:** the task lists criteria (step 3) before the loan product
  (step 5), but a provisioning criteria must reference an existing loan product
  (`loanProducts[].id`). `run.sh` therefore executes step 05 (loan product)
  before step 03 (criteria). Step numbers are preserved in filenames.
- **enable-business-date "before" value** is unavailable (set by an earlier
  session); only the final state is recorded.
- No schema DDL, no INSERT/UPDATE/DELETE; SQL is read-only verification only.
- Money handled in integer minor units by the rig's own code; no floating point
  in the scripts.
