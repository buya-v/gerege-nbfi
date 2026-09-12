# OWNER — Tier D `LoanRepayment-Part1.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD21-DA)

Whole-file replay of `LoanRepayment-Part1.feature` (50 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 50 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the REPAYMENT-family posting arms of the loan accounting processor: `repayment`, `goodwillCredit`, `merchantIssuedRefund`, `payoutRefund` and `recoveryRepayment`. Previous captures graded repayment postings only on principal / fee / overpayment for one product and the recovery arm on two charged-off loans. This feature adds interest and penalty portions, more payment types (channel-mapped fund sources), repayments on charged-off loans and goodwill credits. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD21-DA ran the rig, the replay (50/50), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-repayment-p1-mnt.sh` | the exact replay driver |
| `replay-repayment-p1-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 50 PASSED scenarios |
| `manifest-repayment-p1.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-repayment-p1.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 50/50 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 9 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**50 scenarios, 50 PASSED, 0 FAILED; 1590 steps (795 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C49 | 15 | PASSED | 1 | `_(default progressive)_` |
| 2 | C32 | 18 | PASSED | 2 | `_(default progressive)_` |
| 3 | C44 | 28 | PASSED | 3 | `_(default progressive)_` |
| 4 | C45 | 38 | PASSED | 4 | `_(default progressive)_` |
| 5 | C2430 | 49 | PASSED | 5 | `_(default progressive)_` |
| 6 | C2431 | 60 | PASSED | 6 | `_(default progressive)_` |
| 7 | C2432 | 71 | PASSED | 7 | `_(default progressive)_` |
| 8 | C2433 | 82 | PASSED | 8 | `_(default progressive)_` |
| 9 | C2434 | 93 | PASSED | 9 | `_(default progressive)_` |
| 10 | C2435 | 104 | PASSED | 10 | `_(default progressive)_` |
| 11 | C2436 | 115 | PASSED | 11 | `_(default progressive)_` |
| 12 | C2437 | 126 | PASSED | 12 | `_(default progressive)_` |
| 13 | C2464 | 137 | PASSED | 13 | `_(default progressive)_` |
| 14 | C2465 | 155 | PASSED | 14 | `_(default progressive)_` |
| 15 | C2466 | 173 | PASSED | 15 | `_(default progressive)_` |
| 16 | C2467 | 191 | PASSED | 16 | `_(default progressive)_` |
| 17 | C2468 | 209 | PASSED | 17 | `_(default progressive)_` |
| 18 | C2469 | 227 | PASSED | 18 | `_(default progressive)_` |
| 19 | C2470 | 245 | PASSED | 19 | `_(default progressive)_` |
| 20 | C2471 | 263 | PASSED | 20 | `_(default progressive)_` |
| 21 | C2485 | 281 | PASSED | 21 | `_(default progressive)_` |
| 22 | C2689 | 295 | PASSED | 22 | `LP1_DUE_DATE` |
| 23 | C2490 | 311 | PASSED | 23 | `LP1_INTEREST_FLAT` |
| 24 | C2492 | 343 | PASSED | 24 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 25 | C2493 | 375 | PASSED | 25 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` |
| 26 | C2494 | 407 | PASSED | 26 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 27 | C2495 | 439 | PASSED | 27 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 28 | C2496 | 471 | PASSED | 28 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 29 | C2497 | 503 | PASSED | 29 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 30 | C2498 | 535 | PASSED | 30 | `_(default progressive)_` |
| 31 | C2499 | 547 | PASSED | 31 | `_(default progressive)_` |
| 32 | C2500 | 559 | PASSED | 32 | `_(default progressive)_` |
| 33 | C2531 | 571 | PASSED | 33 | `_(default progressive)_` |
| 34 | C2555 | 582 | PASSED | 34 | `LP1_1MONTH_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_MONTHLY` |
| 35 | C2556 | 606 | PASSED | 35 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 36 | C2557 | 630 | PASSED | 36 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 37 | C2558 | 654 | PASSED | 37 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 38 | C2559 | 678 | PASSED | 38 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 39 | C2560 | 702 | PASSED | 39 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 40 | C2561 | 726 | PASSED | 40 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 41 | C2562 | 750 | PASSED | 41 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 42 | C2563 | 774 | PASSED | 42 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 43 | C2564 | 798 | PASSED | 43 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 44 | C2625 | 822 | PASSED | 44 | `LP1_INTEREST_FLAT` |
| 45 | C2626 | 861 | PASSED | 45 | `LP1_INTEREST_FLAT` |
| 46 | C2627 | 907 | PASSED | 46 | `LP1_INTEREST_FLAT` |
| 47 | C2628 | 952 | PASSED | 47 | `LP1_INTEREST_FLAT` |
| 48 | C2629 | 1004 | PASSED | 48 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_RESCHEDULE_REDUCE_NR_INST` |
| 49 | C2630 | 1029 | PASSED | 49 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 50 | C2631 | 1055 | PASSED | 50 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_RESCHEDULE_RESCH_NEXT_REP` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 50 loans, 924 bodies kept under `loans/`, each body sha256-pinned in `manifest-repayment-p1.json`; the FAILED scenarios' loans are not committed (`manifest-repayment-p1-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **50/50 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 285 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 9 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP1.json`
- `create-request-LP1_1MONTH_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_MONTHLY.json`
- `create-request-LP1_DUE_DATE.json`
- `create-request-LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE.json`
- `create-request-LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_RESCHEDULE_REDUCE_NR_INST.json`
- `create-request-LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_RESCHEDULE_RESCH_NEXT_REP.json`
- `create-request-LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY.json`
- `create-request-LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT.json`
- `create-request-LP1_INTEREST_FLAT.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **285 legs, 7 types, 0 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction with a LOWER transaction id than the leg's transaction.** (The rule is transaction id order, not date order.) `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 150 | 0 | - |
| `loanTransactionType.disbursement` | 86 | 0 | - |
| `loanTransactionType.goodwillCredit` | 29 | 12 | 45, 47 |
| `loanTransactionType.chargeOff` | 10 | 0 | - |
| `loanTransactionType.accrual` | 4 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 4 | 0 | - |
| `loanTransactionType.payoutRefund` | 2 | 0 | - |

### The five repayment-family arms (required)

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.repayment` | True | 150 | 59 | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 0 | - | 150 | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.goodwillCredit` | True | 29 | 5 | 30, 44, 45, 46, 47 | 12 | 45, 47 | 17 | 30, 44, 46 |
| `loanTransactionType.merchantIssuedRefund` | True | 4 | 2 | 32, 33 | 0 | - | 4 | 32, 33 |
| `loanTransactionType.payoutRefund` | True | 2 | 1 | 31 | 0 | - | 2 | 31 |
| `loanTransactionType.recoveryRepayment` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target repayment-family type(s) with NO journal-entry legs at all: loanTransactionType.recoveryRepayment.  The arm was NOT exercised by this feature.

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:8 DEBIT:10` | 8, 10 | CREDIT 8, DEBIT 10 | 23 | 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33 | 1 | L2 | P 20000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:6 CREDIT:8 DEBIT:10` | 6, 8, 10 | CREDIT 6, CREDIT 8, DEBIT 10 | 16 | 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 48, 49, 50 | 34 | L71 | P 81268 / I 4932 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:14 DEBIT:10` | 10, 14 | CREDIT 14, DEBIT 10 | 8 | 13, 14, 15, 16, 17, 18, 19, 20 | 13 | L27 | P 0 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0 | 9 |
| `CREDIT:8 CREDIT:10 DEBIT:8 DEBIT:10` | 8, 10 | CREDIT 8, CREDIT 10, DEBIT 8, DEBIT 10 | 8 | 13, 14, 15, 16, 17, 18, 19, 20 | 13 | L25 | P 500000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:6 DEBIT:10` | 6, 10 | CREDIT 6, DEBIT 10 | 4 | 44, 45, 46, 47 | 44 | L91 | P 0 / I 0 / F 9000 / Pen 1000 / OP 0 / UI 0 | 9 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:8 DEBIT:10`: loan 1, tx L2, P 20000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 23 transaction(s) across loan(s) 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33.
- shape `CREDIT:6 CREDIT:8 DEBIT:10`: loan 34, tx L71, P 81268 / I 4932 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 16 transaction(s) across loan(s) 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 48, 49, 50.
- shape `CREDIT:14 DEBIT:10`: loan 13, tx L27, P 0 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0, paymentType id 9 — 8 transaction(s) across loan(s) 13, 14, 15, 16, 17, 18, 19, 20.
- shape `CREDIT:8 CREDIT:10 DEBIT:8 DEBIT:10`: loan 13, tx L25, P 500000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 8 transaction(s) across loan(s) 13, 14, 15, 16, 17, 18, 19, 20.
- shape `CREDIT:6 DEBIT:10`: loan 44, tx L91, P 0 / I 0 / F 9000 / Pen 1000 / OP 0 / UI 0, paymentType id 9 — 4 transaction(s) across loan(s) 44, 45, 46, 47.

#### `loanTransactionType.goodwillCredit`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:13 CREDIT:17 CREDIT:18 CREDIT:20 DEBIT:13 DEBIT:17 DEBIT:18 DEBIT:20` | 13, 17, 18, 20 | CREDIT 13, CREDIT 17, CREDIT 18, CREDIT 20, DEBIT 13, DEBIT 17, DEBIT 18, DEBIT 20 | 1 | 47 | 47 | L105 | P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:13 DEBIT:17 DEBIT:18 DEBIT:20` | 13, 17, 18, 20 | CREDIT 13, DEBIT 17, DEBIT 18, DEBIT 20 | 1 | 45 | 45 | L97 | P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:14 DEBIT:20` | 14, 20 | CREDIT 14, DEBIT 20 | 1 | 30 | 30 | L60 | P 0 / I 0 / F 0 / Pen 0 / OP 20000 / UI 0 | 9 |
| `CREDIT:6 CREDIT:8 CREDIT:17 CREDIT:18 CREDIT:20 DEBIT:6 DEBIT:8 DEBIT:17 DEBIT:18 DEBIT:20` | 6, 8, 17, 18, 20 | CREDIT 6, CREDIT 8, CREDIT 17, CREDIT 18, CREDIT 20, DEBIT 6, DEBIT 8, DEBIT 17, DEBIT 18, DEBIT 20 | 1 | 46 | 46 | L100 | P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:6 CREDIT:8 DEBIT:17 DEBIT:18 DEBIT:20` | 6, 8, 17, 18, 20 | CREDIT 6, CREDIT 8, DEBIT 17, DEBIT 18, DEBIT 20 | 1 | 44 | 44 | L92 | P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0 | 9 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:13 CREDIT:17 CREDIT:18 CREDIT:20 DEBIT:13 DEBIT:17 DEBIT:18 DEBIT:20`: loan 47, tx L105, P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 47.
- shape `CREDIT:13 DEBIT:17 DEBIT:18 DEBIT:20`: loan 45, tx L97, P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 45.
- shape `CREDIT:14 DEBIT:20`: loan 30, tx L60, P 0 / I 0 / F 0 / Pen 0 / OP 20000 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 30.
- shape `CREDIT:6 CREDIT:8 CREDIT:17 CREDIT:18 CREDIT:20 DEBIT:6 DEBIT:8 DEBIT:17 DEBIT:18 DEBIT:20`: loan 46, tx L100, P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 46.
- shape `CREDIT:6 CREDIT:8 DEBIT:17 DEBIT:18 DEBIT:20`: loan 44, tx L92, P 27700 / I 1000 / F 1300 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 44.

#### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:14 DEBIT:10` | 10, 14 | CREDIT 14, DEBIT 10 | 1 | 32 | 32 | L66 | P 0 / I 0 / F 0 / Pen 0 / OP 20000 / UI 0 | 9 |
| `CREDIT:8 DEBIT:10` | 8, 10 | CREDIT 8, DEBIT 10 | 1 | 33 | 33 | L68 | P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:14 DEBIT:10`: loan 32, tx L66, P 0 / I 0 / F 0 / Pen 0 / OP 20000 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 32.
- shape `CREDIT:8 DEBIT:10`: loan 33, tx L68, P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 33.

#### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:14 DEBIT:10` | 10, 14 | CREDIT 14, DEBIT 10 | 1 | 31 | 31 | L63 | P 0 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0 | 9 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:14 DEBIT:10`: loan 31, tx L63, P 0 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 31.

#### `loanTransactionType.recoveryRepayment`

_No legs for this type — see the finding above._

### Per-loan currency and charge-off state

| loan | currency | charged-off latest read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- |
| 1 | MNT | False | - |
| 2 | MNT | False | - |
| 3 | MNT | False | - |
| 4 | MNT | False | - |
| 5 | MNT | False | - |
| 6 | MNT | False | - |
| 7 | MNT | False | - |
| 8 | MNT | False | - |
| 9 | MNT | False | - |
| 10 | MNT | False | - |
| 11 | MNT | False | - |
| 12 | MNT | False | - |
| 13 | MNT | False | - |
| 14 | MNT | False | - |
| 15 | MNT | False | - |
| 16 | MNT | False | - |
| 17 | MNT | False | - |
| 18 | MNT | False | - |
| 19 | MNT | False | - |
| 20 | MNT | False | - |
| 21 | MNT | False | - |
| 22 | MNT | False | - |
| 23 | MNT | False | - |
| 24 | MNT | False | - |
| 25 | MNT | False | - |
| 26 | MNT | False | - |
| 27 | MNT | False | - |
| 28 | MNT | False | - |
| 29 | MNT | False | - |
| 30 | MNT | False | - |
| 31 | MNT | False | - |
| 32 | MNT | False | - |
| 33 | MNT | False | - |
| 34 | MNT | False | - |
| 35 | MNT | False | - |
| 36 | MNT | False | - |
| 37 | MNT | False | - |
| 38 | MNT | False | - |
| 39 | MNT | False | - |
| 40 | MNT | False | - |
| 41 | MNT | False | - |
| 42 | MNT | False | - |
| 43 | MNT | False | - |
| 44 | MNT | False | - |
| 45 | MNT | True | L96@2023-01-10 |
| 46 | MNT | False | - |
| 47 | MNT | True | L104@2023-01-10 |
| 48 | MNT | False | - |
| 49 | MNT | False | - |
| 50 | MNT | False | - |

### Findings

- target repayment-family type(s) with NO journal-entry legs at all: loanTransactionType.recoveryRepayment.  The arm was NOT exercised by this feature.

Other observations from the join:

- `goodwillCredit` legs (12) appear on CHARGED-OFF loans 45 and 47, i.e. after the charge-off transaction — the goodwill arm posts on charged-off loans in this feature.
- No `repayment` leg sits on a charged-off loan (0 legs): every repayment transaction has a LOWER id than its loan's charge-off, so the feature does not exercise the repaid-after-charge-off arm.
- The payment type on the required arms comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

