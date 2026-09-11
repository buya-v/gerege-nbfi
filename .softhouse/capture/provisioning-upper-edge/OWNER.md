# Provisioning upper-edge capture — OWNER

**Task:** `OH-PROVEDGE-BA`, branch `feat/OHPROVEDGEba`.
**Business date (oracle):** `2026-09-03` — read from `GET /v1/businessdate`
(`out/recon-businessdate-raw.json`), never changed.
**Tenant:** `gerege` only. **Engine:** PostgreSQL 18 via `gerege-oracle-db` (SQL read-only).
**Oracle:** Fineract reference checkout `/Users/buv/fineract`.
**Snapshot before writes:** `pg_dump -Fc fineract_gerege` from `gerege-oracle-db` →
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohprovedgeba-20260911T062333Z.dump`
(not committed).

## Objective and result

Three ACTIVE loans on product 2 (`SEED-Probe-Loan`), whose oldest unpaid instalment is exactly
**29**, **59** and **89** days overdue on `2026-09-03`, then ONE provisioning entry dated that
business date (`createjournalentries:false`), read back per loan.

The oracle ACCEPTED the entry (`HTTP 200`, `{"resourceId":2}`) and the read-back proves that all
three upper band edges are INSIDE their band: the oracle's age-band match is **inclusive on the
upper bound**.

## The three edge loans

| loan | client | product | disbursed | first instalment due | oracle `pastDueDate` | oracle `pastDueDays` | oracle `delinquentDays` | outstanding (MNT) |
|---|---|---|---|---|---|---|---|---|
| `EDGE-L29` (id 16) | `EDGE-C29` (id 18) | 2 `SEED-Probe-Loan` | 2026-07-05 | 2026-08-05 | 2026-08-05 | **29** | 29 | 106618.53 |
| `EDGE-L59` (id 15) | `EDGE-C59` (id 17) | 2 `SEED-Probe-Loan` | 2026-06-06 | 2026-07-06 | 2026-07-06 | **59** | 59 | 106618.53 |
| `EDGE-L89` (id 14) | `EDGE-C89` (id 16) | 2 `SEED-Probe-Loan` | 2026-05-06 | 2026-06-06 | 2026-06-06 | **89** | 89 | 106618.53 |

Each loan was created by submit → approve → disburse at the stated disbursement date with the
product's monthly (30/360) schedule, and **no repayment was made**. The oracle's own read-back
(`delinquent.pastDueDays` / `delinquent.delinquentDays`, in `out/loan-EDGE-L{29,59,89}-detail-raw.json`)
agrees with the arithmetic `2026-09-03 − firstDue`. Raw request/response bodies are committed
under `req/` and `out/`.

## Entry and the band each edge was put in

Entry request `req/ENT-02-create.json`:
`{"date":"03 September 2026","dateFormat":"dd MMMM yyyy","locale":"en","createjournalentries":false}`

Read-back `out/ENT-03-entry-metadata-raw.json`:
`{"id":2,"journalEntry":false,"createdById":1,"createdUser":"mifos","createdDate":"2026-09-03","modifiedById":0,"reservedAmount":290081.630000}`

Criteria definitions in effect (`out/corroboration-readonly-sql.txt` / `out/recon-criteria-1-raw.json`):
`[0,29]` STANDARD 1.00%, `[30,59]` SUB-STANDARD 25.00%, `[60,89]` DOUBTFUL 50.00%,
`[90,36500]` LOSS 100.00%.

| edge observed | loan | oracle band assigned | percentage | amount reserved (MNT) |
|---|---|---|---|---|
| **29 days** | `EDGE-L29` | **STANDARD** (`[0,29]`) | 1.00% | **1066.19** |
| **59 days** | `EDGE-L59` | **SUB-STANDARD** (`[30,59]`) | 25.00% | **26654.63** |
| **89 days** | `EDGE-L89` | **DOUBTFUL** (`[60,89]`) | 50.00% | **53309.27** |

Stated plainly, per edge:

* **29 overdue → the oracle put it in STANDARD `[0,29]`.** A port that treats the upper bound as
  exclusive would place 29 in SUB-STANDARD — the oracle did not. Upper bound is INCLUSIVE.
* **59 overdue → the oracle put it in SUB-STANDARD `[30,59]`.** A port that treats the upper bound
  as exclusive would place 59 in DOUBTFUL — the oracle did not. Upper bound is INCLUSIVE.
* **89 overdue → the oracle put it in DOUBTFUL `[60,89]`.** A port that treats the upper bound as
  exclusive would place 89 in LOSS — the oracle did not. Upper bound is INCLUSIVE.

Amounts are `outstanding × percentage` rounded HALF_UP: `106618.53 × 1% = 1066.19`,
`× 25% = 26654.63`, `× 50% = 53309.27`, matching the `amountreserved` values in
`out/ENT-04-entry-loan-products-raw.json` field-for-field.

## Rule in the oracle source

`fineract-accounting/.../provisioning/service/ProvisioningEntriesReadPlatformServiceImpl.java:73-74`
matches the band with a **closed** interval on both ends:

```
(pcd.min_age <= GREATEST(dateDiff(?, sch.duedate),0) and GREATEST(dateDiff(?, sch.duedate),0) <= pcd.max_age)
```

So `age >= min_age AND age <= max_age`; the observed 29/59/89 landing in STANDARD/SUB-STANDARD/
DOUBTFUL is the executor's rendering of that comparison, not a coincidence of the test data.

## Pre-existing product-2 loans — kept as observations

The entry also contains the pre-existing product-2 loans at their own new ages; they were **kept**.
The read-back row set for history 2 (`out/ENT-04-entry-loan-products-raw.json`,
`totalFilteredRecords=8`) is exactly the SQL row set
(`out/corroboration-readonly-sql.txt`):

| `overdueInDays` | category | amount reserved | which loan(s) |
|---|---|---|---|
| 0 | STANDARD | 977.34 | `SEED-L03` (future due 2026-10-01, clamped to 0) |
| 2 | STANDARD | 1066.72 | `SEED-L06` |
| **29** | **STANDARD** | **1066.19** | **`EDGE-L29`** |
| 33 | SUB-STANDARD | 26654.63 | `SEED-L02` |
| **59** | **SUB-STANDARD** | **26654.63** | **`EDGE-L59`** |
| 64 | DOUBTFUL | 73734.32 | `SEED-L01` + `SEED-L05` (merged, same age) |
| **89** | **DOUBTFUL** | **53309.27** | **`EDGE-L89`** |
| 94 | LOSS | 106618.53 | `SEED-L04` |

`ENT-04` rows carry no loan id (they aggregate by product × category × overdue days), so the
loan-to-row attribution above is corroborated by the read-only per-loan age query, not inferred
from a single row.

## Refusal check

No refusal. The oracle accepted a second entry on a new date (history 1 = `2026-09-01`,
history 2 = `2026-09-03`); the one-entry-per-date rule did not block a distinct date.

## Bar

`bash .softhouse/conformance.sh` → **exit 2**, and the only exit-2 reason in the log is
`conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
completed and the bar is refused by that recorded decision`. `HARD guard failed` count **0**;
graded `parity vectors PASS 49 FAIL 0`. This capture adds no vector and changes no Go code, so the
bar is unchanged.

## Artifacts

Raw JSON under `out/` (vector-citable); all HTTP response bodies unmodified. `req/` holds the
byte-stable request bodies. `out/corroboration-readonly-sql.txt` is read-only SQL corroboration
only, not a vector record. `bin/step01..step05` are the capture rig.
