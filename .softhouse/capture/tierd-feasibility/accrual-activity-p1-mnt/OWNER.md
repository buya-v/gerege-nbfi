# OWNER — Tier D `LoanAccrualActivity-Part1.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD12-CE)

Replay of the whole `LoanAccrualActivity-Part1.feature` (50 scenarios) against the throwaway reference oracle,
tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency re-seeded to MNT), with the Feign capture on,
**and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every
one of the 50 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and the
join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies keep the decimal major units the oracle
emitted.

Part2 (`tierd-feasibility/accrual-activity-mnt/`) recorded 509 accrual-type transactions but **zero accrual
journal-entry legs**, because the runner reads `/journalentries` only for scenarios that carry a journal-entry table.
This capture adds the one step the runner does not do: after the replay, before teardown, read **every** loan's
journal entries from the throwaway. Target of interest:
`createJournalEntriesForAccruals` [AccrualBasedAccountingProcessorForLoan.java:2015] — types `accrual`,
`accrualAdjustment`, `accrualActivity`.

## Provenance of this directory
OH-TIERD12-CE ran the rig, the replay (50/50), the extraction, the sweep, the product mappings and the teardown, and
wrote the type join and this file. Every command was run in the foreground with a bound (curl `--max-time`; the
copied run script for Gradle). No background job, no `jobs`, no `wait`. The throwaway is DOWN
(`teardown-isolation.txt`); the remaining work was offline over the captured JSON.

## What is here

| path | what |
| --- | --- |
| `replay-result-table.md` | per-scenario PASSED/FAILED, failing step and values |
| `scenario-results.json` | the same, machine-readable |
| `run-accrualactivity-p1-mnt.sh` | the exact replay driver (FEATURE/LOG/container changed from the Part2 copy) |
| `replay-accrualactivity-p1-mnt.log` | cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 50 PASSED scenarios (1,609 files) |
| `manifest-accrual-activity-p1.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-accrual-activity-p1.json` | extractor totals |
| `journalentries-sweep/loan-<id>.json` | **the new step:** verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 50/50 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 11 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `accrual-legs.tsv` | flat listing of every accrual-type leg (loan, tx, type, inferred, entry, GL id/code/name, minor amount, currency) |
| `build-type-join.py, organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the extractors (copied from the Part2 capture; `build-type-join.py` extended with the inferred classifier) |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof |

## Replay result
**50 scenarios, 50 PASSED, 0 FAILED; 1666 steps (1666 passed, 0 skipped, 0 failed).** Recorded, not diagnosed; no
scenario failed this time, so there is nothing to diagnose.

## Extraction (step 2)
`extract.py` + `organize.py`: source log 292,436,678 bytes / 113,698 lines; 4,323 exchanges (1,406 loan-attributed,
2,917 skipped = 246,605,314 bytes, 84% of source bytes); 50 loans; 1,609 bodies kept (26,372,345 bytes) under
`loans/`; each body sha256-pinned in the manifest.

## The new step — journal-entry sweep (step 3)
For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no
write. Result: **50/50 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 2,563 legs total**, each body saved verbatim
and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## The type join — swept journal-entry leg → transaction TYPE (step 6)

The sweep leg carries only `transactionId` = `L<loanTransactionId>`. Each leg is joined to its transaction type
through the loan read-backs (`transactions[].id` → `transactions[].type.code`). **2,563 legs, 8 types, 80 unmatched.**

| transaction type | legs | transactions | loans |
| --- | ---: | ---: | --- |
| `loanTransactionType.accrual` | 2,098 | 1,021 | 48 |
| `loanTransactionType.accrualAdjustment` | 16 | 8 | 15, 21, 29, 30, 31, 34, 40, 49 |
| `loanTransactionType.disbursement` | 110 | 53 | 50 |
| `loanTransactionType.repayment` | 245 | 66 | 38 |
| `loanTransactionType.chargeAdjustment` | 6 | 2 | 26 |
| `loanTransactionType.goodwillCredit` | 6 | 2 | 26 |
| `loanTransactionType.interestPaymentWaiver` | 2 | 1 | 38 |
| `(unmapped — inferred `accrual`)` | 80 | 20 | 20, 22, 23, 25 |

### Accrual type `accrual` — 2,098 read-back-confirmed legs / 1,021 transactions / 48 loans
Loans 17 and 45 have no accrual legs. Every leg is two-sided and balanced; the GL pair is almost always
interest accrual:

| GL account id | code | name | legs |
| --- | --- | --- | ---: |
| 7 | 112603 | Interest/Fee Receivable | (debit side) |
| 8 | 404000 | Interest Income | (credit side) |
| 5 | 404007 | Fee Income | 24 (fee-accrual legs) |

Amount range (minor units) 1–3000. Pattern per transaction: `DEBIT 7 Interest/Fee Receivable / CREDIT 8 Interest
Income` (fee accruals post against 5/404007). **The full leg list — every loan, every `L<tx>`, GL id + name, entry
and minor amount — is in `accrual-legs.tsv` (rows `loanTransactionType.accrual`, `inferred=False`) and in
`journalentry-type-join.md` under the `loanTransactionType.accrual` section.** Representative (loan 1):

| loan | tx | entry | GL id | GL name | amount minor |
| --- | --- | --- | --- | --- | ---: |
| 1 | L2 | DEBIT | 7 | Interest/Fee Receivable | 33 |
| 1 | L2 | CREDIT | 8 | Interest Income | 33 |
| 1 | L3 | DEBIT | 7 | Interest/Fee Receivable | 33 |
| 1 | L3 | CREDIT | 8 | Interest Income | 33 |
| 1 | L4 | DEBIT | 7 | Interest/Fee Receivable | 32 |
| 1 | L4 | CREDIT | 8 | Interest Income | 32 |

Per-loan accrual transaction counts: 1:5, 2:5, 3:6, 4:5, 5:5, 6:6, 7:5, 8:5, 9:6, 10:5, 11:5, 12:6, 13:1, 14:1,
15:2, 16:6, 18:5, 19:9, 20:8, 21:17, 22:26, 23:20, 24:5, 25:8, 26:1, 27:15, 28:32, 29:4, 30:4, 31:7, 32:24,
33:31, 34:30, 35:31, 36:1, 37:83, 38:1, 39:2, 40:60, 41:1, 42:1, 43:1, 44:1, 46:172, 47:182, 48:182, 49:1, 50:2.

### Accrual type `accrualAdjustment` — 16 legs / 8 transactions / 8 loans
Two-sided and balanced; all 16 legs:

| loan | tx | entry | GL id | GL name | amount minor |
| --- | --- | --- | --- | --- | ---: |
| 15 | L107 | DEBIT | 8 | Interest Income | 279 |
| 15 | L107 | CREDIT | 7 | Interest/Fee Receivable | 279 |
| 21 | L183 | DEBIT | 8 | Interest Income | 972 |
| 21 | L183 | CREDIT | 7 | Interest/Fee Receivable | 972 |
| 29 | L331 | DEBIT | 8 | Interest Income | 60 |
| 29 | L331 | CREDIT | 7 | Interest/Fee Receivable | 60 |
| 30 | L342 | DEBIT | 8 | Interest Income | 119 |
| 30 | L342 | CREDIT | 7 | Interest/Fee Receivable | 119 |
| 31 | L349 | DEBIT | 8 | Interest Income | 37 |
| 31 | L349 | CREDIT | 7 | Interest/Fee Receivable | 37 |
| 34 | L444 | DEBIT | 8 | Interest Income | 454 |
| 34 | L444 | CREDIT | 7 | Interest/Fee Receivable | 454 |
| 40 | L615 | DEBIT | 8 | Interest Income | 69 |
| 40 | L615 | CREDIT | 7 | Interest/Fee Receivable | 69 |
| 49 | L1244 | DEBIT | 8 | Interest Income | 15 |
| 49 | L1244 | CREDIT | 7 | Interest/Fee Receivable | 15 |

### Accrual type `accrualActivity` — 0 swept legs, but 74 transactions
The read-backs hold **74 `accrualActivity` transactions across 40 loans**, and **none of them posts a
`/journalentries` leg carrying its `L<id>`.** Loans with accrualActivity: 1–25, 28, 29, 30, 36, 39, 40, 41, 42, 43,
44, 46, 47, 48, 49, 50 (absent on 26, 27, 31, 32, 33, 34, 35, 37, 38, 45). This is the Part2 finding reproduced at
scale with the full sweep on: an `accrualActivity` transaction does not (in this build/seed) leave its own GL
journal-entry leg keyed to the loan transaction id.

### Unmatched — 80 legs / 20 transactions, type INFERRED (not a read-back type)
80 legs on loans 20, 22, 23, 25 carry a `transactionId` that appears in **no** `transactions` read-back, so no
read-back type exists for them. Their posting shape infers a *reverted* interest accrual: a net-zero 4-leg pair —
`DEBIT 7 Interest/Fee Receivable / CREDIT 8 Interest Income` followed by its exact reversal — i.e. the original
accrual transactions that the accrual-activity replay superseded and the `transactions` association no longer
returns.

**These 80 legs are marked INFERRED in `accrual-legs.tsv` (`inferred=True`) and in the join's `(unmapped)` section,
and are NEVER counted as a read-back-confirmed `accrual` type.** Per-transaction shape (all 20 net-zero):

| loan | tx | legs | GL accounts | net-zero | inferred type |
| --- | --- | ---: | --- | --- | --- |
| 20 | L159 | 4 | 7, 8 | yes | `loanTransactionType.accrual` |
| 22 | L192, L194, L196, L198, L202, L204, L206, L208, L211, L212, L213, L214 | 4 each | 7, 8 | yes | `loanTransactionType.accrual` |
| 23 | L219, L227, L237, L238, L239, L240 | 4 each | 7, 8 | yes | `loanTransactionType.accrual` |
| 25 | L259 | 4 | 7, 8 | yes | `loanTransactionType.accrual` |

(20 transactions × 4 legs = 80; the full per-leg listing is in `accrual-legs.tsv`, `inferred=True`, and in the
join's `## Unmatched legs` section.)

## Currency — all MNT
**Every one of the 50 loans is MNT.** The join records `currencies: {1..50: MNT}`. Across the committed read-backs
there are 10,484 `currency` objects, **all MNT, zero USD or any other code**. All **11 products** the 50 loans use
carry `currencyCode: MNT` in their accepted create requests (`product-mappings/`). There is no USD product in this
feature (unlike Part2, which had one). Every amount written above and in the artifacts is integer MNT minor units
(2 ISO 4217 digits); the raw oracle bodies keep decimal major units.

Products: `LP1_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL`,
`LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_ACCRUAL_ACTIVITY`,
`LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY_ACCRUAL_ACTIVITY`,
`LP2_ADV_CUSTOM_PAYMENT_ALLOC_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE`,
`LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL`,
`LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_ACCRUAL_ACTIVITY`,
`LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ACCRUAL_ACTIVITY_POSTING`,
`LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`,
`LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_ACCRUAL_ACTIVITY`,
`LP2_ADV_PYMNT_INTEREST_RECOGNITION_DISBURSEMENT_DAILY_EMI_360_30_ACCRUAL_ACTIVITY`,
`LP2_ADV_PYMNT_INTEREST_RECOGNITION_DISBURSEMENT_DAILY_EMI_ACTUAL_ACTUAL_ACCRUAL_ACTIVITY`.

## Read-back transaction census (deduped by (loan, transaction id))
`accrual` 1,021 / 48 loans; `accrualActivity` 74 / 40; `repayment` 66 / 38; `disbursement` 53 / 50;
`accrualAdjustment` 8 / 8; `goodwillCredit` 2 / 1; `chargeAdjustment` 2 / 1; `interestPaymentWaiver` 1 / 1.

## Isolation
`preflight.txt` (baseline written fail-closed) and `teardown-isolation.txt` (**12/12 standing counters on both
standing DBs == baseline**; standing health 200; every `tierd-*` container/network/volume removed). Standing tenants
`gerege` and `default` untouched. PostgreSQL only; no Oracle anywhere.

## Non-negotiables honoured
Work confined to `/Users/buv/oh-gerege-tierd12` (plus the disposable `/Users/buv/fineract-tierd`); `/Users/buv/fineract`
never written. `nexus/`, `.softhouse/vectors/`, `.softhouse/guards/`, `.softhouse/conformance.sh`, `.softhouse/maps/`
untouched. Every `tierd-*` container torn down. Money integer minor units. Capture only — no push, no vector, no
`.go`; the driver pushes.

## Commit trail (branch `feat/OHTIERD12CE`)
- step 1 `c51b9c35` replay Part1 (50/50 pass) in MNT
- step 1 `499bcac1` extract Part1 loan read-backs (1,609 bodies, 50 loans)
- step 2 `fc3b2244` extraction summary
- step 3 `7f6bb5a6` journal-entry sweep of all 50 loans
- step 4 `bbea56ea` product mappings for the 11 loan products
- step 5 `edb5ea79` teardown, 12/12 standing baseline intact
- step 6 (this) type join, inferred classifier, `accrual-legs.tsv`, OWNER.md
