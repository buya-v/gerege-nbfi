# OWNER — Tier D `LoanChargesCumulativeLoan.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD19-CW)

Whole-file replay of `LoanChargesCumulativeLoan.feature` (25 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 25 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSV is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the CHARGE-ADJUSTMENT posting family of `AccrualBasedAccountingProcessorForLoan.java` :997-1214 — `createJournalEntriesForChargeAdjustment` → `...ForLoanChargeAdjustment` / `...ForChargeOffLoanChargeAdjustment` — which had been barely observed (6 legs). `LoanChargesCumulativeLoan.feature` (25 scenarios) exercises it: its charge-adjustment scenario C2472 drives eight `chargeAdjustment` transactions (with and without reversal). This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at the transaction date, and lists every charge-related leg, each charge-related transaction's amount and its read-back portions.

## Provenance

OH-TIERD19-CW ran the rig, the replay (25/25), the extraction, the sweep, the product mappings, the teardown and the type join. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the join was built offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-charges-cumulative-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the OH-TIERD17-CR copy) |
| `replay-charges-cumulative-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 25 PASSED scenarios (955 bodies) |
| `manifest-charges-cumulative.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-charges-cumulative.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 25/25 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 4 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `charge-related-legs.tsv` | flat listing of every charge-related leg (required columns) |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**25 scenarios, 25 PASSED, 0 FAILED; 691 steps (691 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | tag | line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C50 | 5 | PASSED | 1 | `None` |
| 2 | C51 | 16 | PASSED | 2 | `None` |
| 3 | C2450 | 27 | PASSED | 3 | `None` |
| 4 | C2451 | 48 | PASSED | 4 | `None` |
| 5 | C2452 | 73 | PASSED | 5 | `None` |
| 6 | C2453 | 100 | PASSED | 6 | `None` |
| 7 | C2472 | 126 | PASSED | 7 | `None` |
| 8 | C2532 | 916 | PASSED | 8 | `None` |
| 9 | C2533 | 932 | PASSED | 9 | `None` |
| 10 | C2534 | 949 | PASSED | 10 | `None` |
| 11 | C2535 | 967 | PASSED | 11 | `None` |
| 12 | C2536 | 988 | PASSED | 12 | `None` |
| 13 | C2537 | 1011 | PASSED | 13 | `None` |
| 14 | C2538 | 1033 | PASSED | 14 | `None` |
| 15 | C2601 | 1055 | PASSED | 15 | `None` |
| 16 | C2606 | 1075 | PASSED | 16 | `None` |
| 17 | C2607 | 1091 | PASSED | 17 | `None` |
| 18 | C2635 | 1107 | PASSED | 18 | `None` |
| 19 | C2672 | 1127 | PASSED | 19 | `None` |
| 20 | C2673 | 1152 | PASSED | 20 | `None` |
| 21 | C2674 | 1176 | PASSED | 21 | `LP1_INTEREST_FLAT` |
| 22 | C2675 | 1204 | PASSED | 22 | `LP1_INTEREST_FLAT_OVERDUE_FROM_AMOUNT` |
| 23 | C2676 | 1238 | PASSED | 23 | `LP1_INTEREST_FLAT_OVERDUE_FROM_AMOUNT_INTEREST` |
| 24 | C2790 | 1272 | PASSED | 24 | `None` |
| 25 | C2909 | 1305 | PASSED | 25 | `None` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 25 loans, 955 bodies kept under `loans/`, each body sha256-pinned in `manifest-charges-cumulative.json`; the FAILED scenarios' loans are not committed (`manifest-charges-cumulative-passed.json`).

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **25/25 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 353 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). **353 legs, 9 types, 0 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the leg's transaction date.** `fraud` per leg = the loan's fraud flag (`markAsFraud` request/read-back).

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 161 | 0 | – |
| `loanTransactionType.accrual` | 72 | 0 | – |
| `loanTransactionType.disbursement` | 50 | 0 | – |
| `loanTransactionType.chargeAdjustment` | 28 | 0 | – |
| `loanTransactionType.goodwillCredit` | 20 | 0 | – |
| `loanTransactionType.chargeback` | 11 | 0 | – |
| `loanTransactionType.payoutRefund` | 7 | 0 | – |
| `loanTransactionType.creditBalanceRefund` | 2 | 0 | – |
| `loanTransactionType.repaymentAtDisbursement` | 2 | 0 | – |

### The charge-related arms (step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.

| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.chargeAdjustment` | True | 28 | 8 | 7 | 0 | – | 28 | 7 |
| `loanTransactionType.waiveCharges` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.chargeback` | True | 11 | 3 | 4, 11 | 0 | – | 11 | 4, 11 |
| `loanTransactionType.goodwillCredit` | True | 20 | 4 | 13, 14 | 0 | – | 20 | 13, 14 |
| `loanTransactionType.payoutRefund` | True | 7 | 2 | 18 | 0 | – | 7 | 18 |
| `loanTransactionType.creditBalanceRefund` | True | 2 | 1 | 18 | 0 | – | 2 | 18 |

**FINDING:** charge-related transaction type(s) with NO legs at all: loanTransactionType.waiveCharges.

**FINDING:** 3 charge-related transaction(s) in the read-backs have NO journal-entry legs: loan 5 tx L25, loan 6 tx L31, loan 24 tx L124.

**FINDING:** no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan, so the `...ForChargeOffLoanChargeAdjustment` arm is NOT exercised by this feature.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

### Every charge-related leg — required listing

Every leg of every charge-related transaction type, with the leg's GL account (id + name), entry side, amount in minor units, the loan fraud flag and whether the loan was charged off at the transaction date.  `charged-off at tx date` = a NON-REVERSED `chargeOff` dated on or before the leg's transaction date; `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged-off at tx date | charged-off latest | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `loanTransactionType.chargeback` | 4 | L17 | DEBIT | 2 | 112601 | Loans Receivable | 25000 | False | False | False | MNT | 2022-05-01 | - |
| `loanTransactionType.chargeback` | 4 | L17 | CREDIT | 5 | 145023 | Suspense/Clearing account | 25000 | False | False | False | MNT | 2022-05-01 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | DEBIT | 7 | 112603 | Interest/Fee Receivable | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | DEBIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L36 | CREDIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | DEBIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | DEBIT | 7 | 112603 | Interest/Fee Receivable | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | DEBIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | CREDIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L38 | CREDIT | 9 | 404007 | Fee Income | 300 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | DEBIT | 7 | 112603 | Interest/Fee Receivable | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | DEBIT | 9 | 404007 | Fee Income | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L40 | CREDIT | 9 | 404007 | Fee Income | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L41 | DEBIT | 9 | 404007 | Fee Income | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L41 | CREDIT | 2 | 112601 | Loans Receivable | 400 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L43 | DEBIT | 9 | 404007 | Fee Income | 500 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L43 | CREDIT | 2 | 112601 | Loans Receivable | 500 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | DEBIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | DEBIT | 9 | 404007 | Fee Income | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | CREDIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L45 | CREDIT | 9 | 404007 | Fee Income | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L46 | DEBIT | 9 | 404007 | Fee Income | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L46 | CREDIT | 2 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | DEBIT | 9 | 404007 | Fee Income | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | DEBIT | 19 | l1 | Overpayment account | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | CREDIT | 9 | 404007 | Fee Income | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeAdjustment` | 7 | L47 | CREDIT | 19 | l1 | Overpayment account | 200 | False | False | False | MNT | 2022-11-04 | - |
| `loanTransactionType.chargeback` | 11 | L61 | DEBIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | DEBIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | CREDIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | CREDIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L61 | CREDIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L63 | DEBIT | 2 | 112601 | Loans Receivable | 11000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L63 | DEBIT | 19 | l1 | Overpayment account | 19000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.chargeback` | 11 | L63 | CREDIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | DEBIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | DEBIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | DEBIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | CREDIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | CREDIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 13 | L75 | CREDIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | DEBIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | DEBIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | DEBIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | CREDIT | 2 | 112601 | Loans Receivable | 10000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | CREDIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L81 | CREDIT | 19 | l1 | Overpayment account | 20000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | DEBIT | 2 | 112601 | Loans Receivable | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | DEBIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | CREDIT | 2 | 112601 | Loans Receivable | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L82 | CREDIT | 18 | 744003 | Goodwill Expense Account | 30000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | DEBIT | 13 | 404008 | Fee Charge Off | 1000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | DEBIT | 18 | 744003 | Goodwill Expense Account | 29000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | CREDIT | 2 | 112601 | Loans Receivable | 29000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.goodwillCredit` | 14 | L83 | CREDIT | 7 | 112603 | Interest/Fee Receivable | 1000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | DEBIT | 19 | l1 | Overpayment account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | CREDIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L98 | CREDIT | 19 | l1 | Overpayment account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L100 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L100 | CREDIT | 2 | 112601 | Loans Receivable | 1000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.payoutRefund` | 18 | L100 | CREDIT | 19 | l1 | Overpayment account | 4000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.creditBalanceRefund` | 18 | L102 | DEBIT | 19 | l1 | Overpayment account | 4000 | False | False | False | MNT | 2023-01-10 | - |
| `loanTransactionType.creditBalanceRefund` | 18 | L102 | CREDIT | 5 | 145023 | Suspense/Clearing account | 4000 | False | False | False | MNT | 2023-01-10 | - |

### Every charge-related transaction and its read-back amount / portions

Portions are integer minor units; `-` means the read-back did not carry that field. The `amount` is the transaction `amount`; portions are the oracle's `principalPortion`, `interestPortion`, `feeChargesPortion`, `penaltyChargesPortion`, `overpaymentPortion` and `unrecognizedIncomePortion`.

| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| 4 | L17 | `loanTransactionType.chargeback` | 2022-05-01 | 25000 | 25000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 5 | L25 | `loanTransactionType.waiveCharges` | 2022-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | False | False | False | MNT | 0 |
| 6 | L31 | `loanTransactionType.waiveCharges` | 2022-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | True | False | False | MNT | 0 |
| 7 | L36 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 300 | 0 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 4 |
| 7 | L38 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 300 | 100 | 0 | 0 | 200 | 0 | 0 | True | False | False | MNT | 6 |
| 7 | L40 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 400 | 0 | 0 | 200 | 200 | 0 | 0 | False | False | False | MNT | 4 |
| 7 | L41 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 400 | 400 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L43 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L45 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 7 | L46 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L47 | `loanTransactionType.chargeAdjustment` | 2022-11-04 | 200 | 0 | 0 | 0 | 0 | 200 | 0 | True | False | False | MNT | 4 |
| 11 | L61 | `loanTransactionType.chargeback` | 2023-01-10 | 30000 | 10000 | 0 | 0 | 0 | 20000 | 0 | False | False | False | MNT | 6 |
| 11 | L63 | `loanTransactionType.chargeback` | 2023-01-10 | 30000 | 11000 | 0 | 0 | 0 | 19000 | 0 | False | False | False | MNT | 3 |
| 13 | L75 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 10000 | 0 | 0 | 0 | 20000 | 0 | True | False | False | MNT | 6 |
| 14 | L81 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 10000 | 0 | 0 | 0 | 20000 | 0 | False | False | False | MNT | 6 |
| 14 | L82 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 30000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 14 | L83 | `loanTransactionType.goodwillCredit` | 2023-01-10 | 30000 | 29000 | 0 | 1000 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 18 | L98 | `loanTransactionType.payoutRefund` | 2023-01-10 | 5000 | 0 | 0 | 0 | 0 | 5000 | 0 | False | False | False | MNT | 4 |
| 18 | L100 | `loanTransactionType.payoutRefund` | 2023-01-10 | 5000 | 1000 | 0 | 0 | 0 | 4000 | 0 | False | False | False | MNT | 3 |
| 18 | L102 | `loanTransactionType.creditBalanceRefund` | 2023-01-10 | 4000 | 0 | 0 | 0 | 0 | 4000 | 0 | False | False | False | MNT | 2 |
| 24 | L124 | `loanTransactionType.waiveCharges` | 2023-01-20 | 9500 | 0 | 0 | 0 | 0 | 0 | 9500 | False | False | False | MNT | 0 |

### Per-loan currency, charge-off and fraud state

| loan | currency | fraud | charged-off latest read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- | --- |
| 1 | MNT | False | False | - |
| 2 | MNT | False | False | - |
| 3 | MNT | False | False | - |
| 4 | MNT | False | False | - |
| 5 | MNT | False | False | - |
| 6 | MNT | False | False | - |
| 7 | MNT | False | False | - |
| 8 | MNT | False | False | - |
| 9 | MNT | False | False | - |
| 10 | MNT | False | False | - |
| 11 | MNT | False | False | - |
| 12 | MNT | False | False | - |
| 13 | MNT | False | False | - |
| 14 | MNT | False | False | - |
| 15 | MNT | False | False | - |
| 16 | MNT | False | False | - |
| 17 | MNT | False | False | - |
| 18 | MNT | False | False | - |
| 19 | MNT | False | False | - |
| 20 | MNT | False | False | - |
| 21 | MNT | False | False | - |
| 22 | MNT | False | False | - |
| 23 | MNT | False | False | - |
| 24 | MNT | False | False | - |
| 25 | MNT | False | False | - |

Every loan in this capture is **MNT**.

## Findings — what the sweep observed and did not

* **Observed — `loanTransactionType.chargeAdjustment` at the GL level:** 28 leg(s) on 8 loan transaction(s) across loans 7; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **FINDING — `loanTransactionType.waiveCharges` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **Observed — `loanTransactionType.chargeback` at the GL level:** 11 leg(s) on 3 loan transaction(s) across loans 4, 11; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.goodwillCredit` at the GL level:** 20 leg(s) on 4 loan transaction(s) across loans 13, 14; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.payoutRefund` at the GL level:** 7 leg(s) on 2 loan transaction(s) across loans 18; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.creditBalanceRefund` at the GL level:** 2 leg(s) on 1 loan transaction(s) across loans 18; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **FINDING — charge-related transaction(s) without journal-entry legs:** loan 5 tx L25, loan 6 tx L31, loan 24 tx L124. The charge-related arms should post for every such transaction, so a leg-less transaction is a shape worth checking.
* **Fraud:** no loan in this feature is fraud-flagged, so the `isMarkedFraud` / charge-off-fraud variants are not exercised (every `fraud` above is `false`).

