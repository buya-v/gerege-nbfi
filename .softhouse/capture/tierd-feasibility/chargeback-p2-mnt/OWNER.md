# OWNER — Tier D `LoanChargeback-Part2.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD15-CM)

Whole-file replay of `LoanChargeback-Part2.feature` (50 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 50 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSVs is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is `createJournalEntriesForChargeback` [`AccrualBasedAccountingProcessorForLoan.java:1215-1308`], which was previously graded only for a loan that is NOT charged off. On a CHARGED-OFF loan its `getPrincipalAccount` / `getFeeAccount` / `getPenaltyAccount` switch to `CHARGE_OFF_EXPENSE` (or the fraud expense) and the charge-off income accounts. Part2 charges loans off, so this capture is the first look at those charged-off chargeback legs. It also lists every chargeback portion split (principal / fee / penalty / overpayment) from the loan read-backs.

This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at the transaction date, and lists every `chargeback` leg and every chargeback transaction's portions.

## Provenance

OH-TIERD15-CM ran the rig, the replay (50/50), the extraction, the sweep, the product mappings, the teardown and the type join. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the join was built offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-chargeback-p2-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the OH-TIERD14-CL copy) |
| `replay-chargeback-p2-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 50 PASSED scenarios (1947 bodies) |
| `manifest-chargeback-p2.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-chargeback-p2.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 50/50 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 11 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `chargeback-legs.tsv` | flat listing of every chargeback leg (required columns) |
| `accrual-legs.tsv` | flat listing of every accrual-type leg |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**50 scenarios, 50 PASSED, 0 FAILED; 1365 steps (1365 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | tag | line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3080 | 5 | PASSED | 1 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 2 | C3081 | 85 | PASSED | 2 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 3 | C3082 | 123 | PASSED | 3 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 4 | C3083 | 163 | PASSED | 4 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 5 | C3084 | 203 | PASSED | 5 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 6 | C3085 | 245 | PASSED | 6 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 7 | C3086 | 285 | PASSED | 7 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 8 | C3087 | 333 | PASSED | 8 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 9 | C3088 | 375 | PASSED | 9 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 10 | C3094 | 416 | PASSED | 10 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 11 | C3095 | 458 | PASSED | 11 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 12 | C3096 | 503 | PASSED | 12 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 13 | C3097 | 548 | PASSED | 13 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 14 | C3098 | 594 | PASSED | 14 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 15 | C3099 | 645 | PASSED | 15 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 16 | C3100 | 690 | PASSED | 16 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 17 | C3101 | 733 | PASSED | 17 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 18 | C3102 | 779 | PASSED | 18 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 19 | C3111 | 825 | PASSED | 19 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 20 | C3116 | 953 | PASSED | 20 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 21 | C3117 | 1074 | PASSED | 21 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 22 | C3118 | 1207 | PASSED | 22 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 23 | C3138 | 1369 | PASSED | 23 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION` |
| 24 | C3406 | 1463 | PASSED | 24 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 25 | C3407 | 1496 | PASSED | 25 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 26 | C3408 | 1529 | PASSED | 26 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 27 | C3409 | 1582 | PASSED | 27 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 28 | C3410 | 1616 | PASSED | 28 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 29 | C3411 | 1664 | PASSED | 29 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 30 | C3417 | 1739 | PASSED | 30 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 31 | C3418 | 1801 | PASSED | 31 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 32 | C3419 | 1863 | PASSED | 32 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_PRINCIPAL_INTEREST_FEE` |
| 33 | C3420 | 1925 | PASSED | 33 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_PRINCIPAL_INTEREST_FEE` |
| 34 | C3421 | 2008 | PASSED | 34 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 35 | C3422 | 2071 | PASSED | 35 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 36 | C3423 | 2154 | PASSED | 36 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 37 | C3490 | 2219 | PASSED | 37 | `LP2_NO_INTEREST_RECALCULATION_CHARGEBACK_ALLOCATION_INTEREST_FIRST` |
| 38 | C3491 | 2280 | PASSED | 38 | `LP2_NO_INTEREST_RECALCULATION_CHARGEBACK_ALLOCATION_INTEREST_FIRST` |
| 39 | C3492 | 2341 | PASSED | 39 | `LP2_NO_INTEREST_RECALCULATION_CHARGEBACK_ALLOCATION_PRINCIPAL_FIRST` |
| 40 | C3493 | 2402 | PASSED | 40 | `LP2_NO_INTEREST_RECALCULATION_CHARGEBACK_ALLOCATION_PRINCIPAL_FIRST` |
| 41 | C3427 | 2483 | PASSED | 41 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 42 | C3428 | 2516 | PASSED | 42 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 43 | C3429 | 2549 | PASSED | 43 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 44 | C3430 | 2602 | PASSED | 44 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 45 | C3431 | 2636 | PASSED | 45 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 46 | C3432 | 2684 | PASSED | 46 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 47 | C3443 | 2759 | PASSED | 47 | `LP2_NO_INTEREST_RECALCULATION_CHARGEBACK_ALLOCATION_INTEREST_FIRST` |
| 48 | C3445 | 2899 | PASSED | 48 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_PENALTY_FEE_PRINCIPAL` |
| 49 | C3446 | 2961 | PASSED | 49 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 50 | C3447 | 3023 | PASSED | 50 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_PRINCIPAL_INTEREST_FEE` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 50 loans, 1947 bodies kept under `loans/`, each body sha256-pinned in `manifest-chargeback-p2.json`; the FAILED scenarios' loans are not committed (`manifest-chargeback-p2-passed.json`).

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **50/50 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 956 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). **956 legs, 8 types, 0 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the leg's transaction date.** `fraud` per leg = the loan's fraud flag (`markAsFraud` request/read-back).

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 432 | 0 | – |
| `loanTransactionType.accrual` | 252 | 0 | – |
| `loanTransactionType.chargeback` | 157 | 8 | 16, 17, 18 |
| `loanTransactionType.disbursement` | 100 | 0 | – |
| `loanTransactionType.chargeOff` | 6 | 6 | 16, 17, 18 |
| `loanTransactionType.merchantIssuedRefund` | 4 | 0 | – |
| `loanTransactionType.payoutRefund` | 3 | 0 | – |
| `loanTransactionType.downPayment` | 2 | 0 | – |

### The chargeback arm `createJournalEntriesForChargeback` (step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.

| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.chargeback` | True | 157 | 68 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 8 | 16, 17, 18 | 149 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |

### Every `chargeback` leg — required listing

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged_off | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- |
| `loanTransactionType.chargeback` | 1 | L4 | DEBIT | 17 | l1 | Overpayment account | 2500 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.chargeback` | 1 | L4 | CREDIT | 6 | 145023 | Suspense/Clearing account | 2500 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.chargeback` | 2 | L8 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 2 | L8 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 3 | L14 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 3 | L14 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 3 | L14 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12800 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 4 | L21 | DEBIT | 5 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 4 | L21 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 4 | L21 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5300 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 5 | L28 | DEBIT | 5 | 112601 | Loans Receivable | 4300 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 5 | L28 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 400 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 5 | L28 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 5 | L28 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 6 | L35 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 6 | L35 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 6 | L36 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 6 | L36 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 7 | L44 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L44 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L45 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L45 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L46 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L46 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L47 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 7 | L47 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 8 | L54 | DEBIT | 5 | 112601 | Loans Receivable | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 8 | L54 | CREDIT | 6 | 145023 | Suspense/Clearing account | 12500 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.chargeback` | 9 | L59 | DEBIT | 5 | 112601 | Loans Receivable | 7500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 9 | L59 | CREDIT | 6 | 145023 | Suspense/Clearing account | 7500 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.chargeback` | 9 | L60 | DEBIT | 5 | 112601 | Loans Receivable | 5000 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.chargeback` | 9 | L60 | CREDIT | 6 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.chargeback` | 10 | L68 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 10 | L68 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 11 | L75 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 11 | L75 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 11 | L75 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 12 | L82 | DEBIT | 5 | 112601 | Loans Receivable | 25000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 12 | L82 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 3000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 12 | L82 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 13 | L88 | DEBIT | 5 | 112601 | Loans Receivable | 10000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 13 | L88 | DEBIT | 17 | l1 | Overpayment account | 15000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 13 | L88 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 14 | L95 | DEBIT | 17 | l1 | Overpayment account | 10000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 14 | L95 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 15 | L101 | DEBIT | 17 | l1 | Overpayment account | 10000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 15 | L101 | CREDIT | 6 | 145023 | Suspense/Clearing account | 10000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.chargeback` | 16 | L107 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | False | True | MNT | 2024-04-01 | L106 |
| `loanTransactionType.chargeback` | 16 | L107 | CREDIT | 6 | 145023 | Suspense/Clearing account | 25000 | False | True | MNT | 2024-04-01 | L106 |
| `loanTransactionType.chargeback` | 17 | L113 | DEBIT | 14 | 404008 | Fee Charge Off | 3000 | False | True | MNT | 2024-04-01 | L112 |
| `loanTransactionType.chargeback` | 17 | L113 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | False | True | MNT | 2024-04-01 | L112 |
| `loanTransactionType.chargeback` | 17 | L113 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | True | MNT | 2024-04-01 | L112 |
| `loanTransactionType.chargeback` | 18 | L119 | DEBIT | 14 | 404008 | Fee Charge Off | 3000 | False | True | MNT | 2024-04-01 | L118 |
| `loanTransactionType.chargeback` | 18 | L119 | DEBIT | 16 | 744007 | Credit Loss/Bad Debt | 25000 | False | True | MNT | 2024-04-01 | L118 |
| `loanTransactionType.chargeback` | 18 | L119 | CREDIT | 6 | 145023 | Suspense/Clearing account | 28000 | False | True | MNT | 2024-04-01 | L118 |
| `loanTransactionType.chargeback` | 19 | L125 | DEBIT | 17 | l1 | Overpayment account | 700 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.chargeback` | 19 | L125 | CREDIT | 6 | 145023 | Suspense/Clearing account | 700 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.chargeback` | 19 | L126 | DEBIT | 5 | 112601 | Loans Receivable | 400 | False | False | MNT | 2024-04-16 | - |
| `loanTransactionType.chargeback` | 19 | L126 | DEBIT | 17 | l1 | Overpayment account | 300 | False | False | MNT | 2024-04-16 | - |
| `loanTransactionType.chargeback` | 19 | L126 | CREDIT | 6 | 145023 | Suspense/Clearing account | 700 | False | False | MNT | 2024-04-16 | - |
| `loanTransactionType.chargeback` | 20 | L130 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 20 | L130 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 20 | L131 | DEBIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.chargeback` | 20 | L131 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.chargeback` | 20 | L131 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.chargeback` | 21 | L135 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 300 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.chargeback` | 21 | L135 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.chargeback` | 21 | L136 | DEBIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT | 2024-04-20 | - |
| `loanTransactionType.chargeback` | 21 | L136 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT | 2024-04-20 | - |
| `loanTransactionType.chargeback` | 21 | L136 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-04-20 | - |
| `loanTransactionType.chargeback` | 22 | L142 | DEBIT | 17 | l1 | Overpayment account | 300 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.chargeback` | 22 | L142 | CREDIT | 6 | 145023 | Suspense/Clearing account | 300 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.chargeback` | 22 | L143 | DEBIT | 5 | 112601 | Loans Receivable | 300 | False | False | MNT | 2024-04-20 | - |
| `loanTransactionType.chargeback` | 22 | L143 | DEBIT | 17 | l1 | Overpayment account | 700 | False | False | MNT | 2024-04-20 | - |
| `loanTransactionType.chargeback` | 22 | L143 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-04-20 | - |
| `loanTransactionType.chargeback` | 23 | L147 | DEBIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L147 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L147 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L147 | CREDIT | 5 | 112601 | Loans Receivable | 800 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L147 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L147 | CREDIT | 10 | 112603 | Interest/Fee Receivable | 200 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L149 | DEBIT | 5 | 112601 | Loans Receivable | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L149 | DEBIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L149 | CREDIT | 5 | 112601 | Loans Receivable | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L149 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L150 | DEBIT | 5 | 112601 | Loans Receivable | 500 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L150 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 23 | L150 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.chargeback` | 24 | L156 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 24 | L156 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 25 | L160 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 25 | L160 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 26 | L164 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 26 | L164 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 26 | L165 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 26 | L165 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 27 | L169 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.chargeback` | 27 | L169 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.chargeback` | 28 | L178 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 28 | L178 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 29 | L187 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 29 | L187 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 29 | L188 | DEBIT | 5 | 112601 | Loans Receivable | 1700 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 29 | L188 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 30 | L192 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 30 | L192 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 31 | L196 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 31 | L196 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 32 | L200 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 32 | L200 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 33 | L204 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 33 | L204 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 33 | L205 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 33 | L205 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 34 | L209 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.chargeback` | 34 | L209 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.chargeback` | 35 | L218 | DEBIT | 5 | 112601 | Loans Receivable | 1681 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 35 | L218 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 36 | L227 | DEBIT | 5 | 112601 | Loans Receivable | 1681 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 36 | L227 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 36 | L228 | DEBIT | 5 | 112601 | Loans Receivable | 1690 | False | False | MNT | 2024-07-30 | - |
| `loanTransactionType.chargeback` | 36 | L228 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | False | False | MNT | 2024-07-30 | - |
| `loanTransactionType.chargeback` | 37 | L232 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 37 | L232 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 38 | L236 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 38 | L236 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 39 | L240 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 39 | L240 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 40 | L244 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 40 | L244 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 40 | L245 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 40 | L245 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 41 | L249 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 41 | L249 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 42 | L253 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 42 | L253 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 43 | L257 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 43 | L257 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 43 | L258 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 43 | L258 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 44 | L262 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.chargeback` | 44 | L262 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.chargeback` | 45 | L271 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 45 | L271 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 46 | L280 | DEBIT | 5 | 112601 | Loans Receivable | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 46 | L280 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 46 | L281 | DEBIT | 5 | 112601 | Loans Receivable | 1700 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 46 | L281 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1700 | False | False | MNT | 2024-07-15 | - |
| `loanTransactionType.chargeback` | 47 | L332 | DEBIT | 5 | 112601 | Loans Receivable | 33042 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 47 | L332 | DEBIT | 10 | 112603 | Interest/Fee Receivable | 500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 47 | L332 | CREDIT | 6 | 145023 | Suspense/Clearing account | 34517 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 48 | L398 | DEBIT | 5 | 112601 | Loans Receivable | 1652 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 48 | L398 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1701 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 49 | L402 | DEBIT | 5 | 112601 | Loans Receivable | 1451 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 49 | L402 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 50 | L406 | DEBIT | 5 | 112601 | Loans Receivable | 1500 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.chargeback` | 50 | L406 | CREDIT | 6 | 145023 | Suspense/Clearing account | 1500 | False | False | MNT | 2024-03-01 | - |

### Every chargeback loan transaction and its read-back portions

Portions are integer minor units; `-` means the read-back did not carry that field. The amount is the transaction `amount`; portions are the oracle's `principalPortion`, `interestPortion`, `feeChargesPortion`, `penaltyChargesPortion`, `overpaymentPortion` and `unrecognizedIncomePortion`.

| loan | tx | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| 1 | L4 | 2024-01-10 | 2500 | 0 | 0 | 0 | 0 | 2500 | 0 | False | False | False | MNT | 2 |
| 2 | L8 | 2024-01-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 3 | L14 | 2024-01-20 | 12800 | 12500 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 3 |
| 4 | L21 | 2024-01-20 | 5300 | 5000 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 3 |
| 5 | L28 | 2024-01-20 | 5000 | 4300 | 0 | 400 | 300 | 0 | 0 | False | False | False | MNT | 4 |
| 6 | L35 | 2024-01-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L36 | 2024-01-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L44 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L45 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L46 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L47 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 8 | L54 | 2024-02-20 | 12500 | 12500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L59 | 2024-01-20 | 7500 | 7500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 9 | L60 | 2024-01-25 | 5000 | 5000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 10 | L68 | 2024-04-01 | 25000 | 25000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 11 | L75 | 2024-04-01 | 28000 | 25000 | 0 | 3000 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 12 | L82 | 2024-04-01 | 28000 | 25000 | 0 | 0 | 3000 | 0 | 0 | False | False | False | MNT | 3 |
| 13 | L88 | 2024-04-01 | 25000 | 25000 | 0 | 0 | 0 | 15000 | 0 | False | False | False | MNT | 3 |
| 14 | L95 | 2024-04-01 | 10000 | 7000 | 0 | 3000 | 0 | 10000 | 0 | False | False | False | MNT | 2 |
| 15 | L101 | 2024-04-01 | 10000 | 10000 | 0 | 0 | 0 | 10000 | 0 | False | False | False | MNT | 2 |
| 16 | L107 | 2024-04-01 | 25000 | 25000 | 0 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 17 | L113 | 2024-04-01 | 28000 | 25000 | 0 | 3000 | 0 | 0 | 0 | False | True | False | MNT | 3 |
| 18 | L119 | 2024-04-01 | 28000 | 25000 | 0 | 0 | 3000 | 0 | 0 | False | True | False | MNT | 3 |
| 19 | L125 | 2024-04-15 | 700 | 200 | 0 | 0 | 500 | 700 | 0 | False | False | False | MNT | 2 |
| 19 | L126 | 2024-04-16 | 700 | 700 | 0 | 0 | 0 | 300 | 0 | False | False | False | MNT | 3 |
| 20 | L130 | 2024-03-01 | 300 | 0 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 2 |
| 20 | L131 | 2024-03-05 | 1000 | 800 | 0 | 0 | 200 | 0 | 0 | False | False | False | MNT | 3 |
| 21 | L135 | 2024-04-15 | 300 | 0 | 0 | 0 | 300 | 0 | 0 | False | False | False | MNT | 2 |
| 21 | L136 | 2024-04-20 | 1000 | 800 | 0 | 0 | 200 | 0 | 0 | False | False | False | MNT | 3 |
| 22 | L142 | 2024-04-15 | 300 | 0 | 0 | 0 | 300 | 300 | 0 | False | False | False | MNT | 2 |
| 22 | L143 | 2024-04-20 | 1000 | 800 | 0 | 0 | 200 | 700 | 0 | False | False | False | MNT | 3 |
| 23 | L147 | 2024-01-07 | 1000 | 800 | 0 | 0 | 200 | 0 | 0 | False | False | False | MNT | 6 |
| 23 | L149 | 2024-01-07 | 1000 | 1000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 23 | L150 | 2024-01-07 | 1000 | 500 | 0 | 0 | 500 | 0 | 0 | False | False | False | MNT | 3 |
| 24 | L156 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 25 | L160 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L164 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L165 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L169 | 2024-03-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L178 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L187 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L188 | 2024-07-15 | 1700 | 1700 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L192 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L196 | 2024-03-01 | 1500 | 1451 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L200 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L204 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L205 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L209 | 2024-03-15 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L218 | 2024-07-15 | 1701 | 1681 | 20 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L227 | 2024-07-15 | 1701 | 1681 | 20 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L228 | 2024-07-30 | 1700 | 1690 | 10 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L232 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L236 | 2024-03-01 | 1500 | 1451 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L240 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L244 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L245 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L249 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L253 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L257 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L258 | 2024-03-01 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L262 | 2024-03-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L271 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L280 | 2024-07-15 | 1701 | 1701 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L281 | 2024-07-15 | 1700 | 1700 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L332 | 2024-03-01 | 34517 | 33042 | 975 | 0 | 500 | 0 | 0 | False | False | False | MNT | 3 |
| 48 | L398 | 2024-03-01 | 1701 | 1652 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 49 | L402 | 2024-03-01 | 1500 | 1451 | 49 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 50 | L406 | 2024-03-01 | 1500 | 1500 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |

### Per-loan currency, charge-off and fraud state

| loan | currency | fraud | non-reversed chargeOff transactions |
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
| 16 | MNT | False | L106@2024-03-15 |
| 17 | MNT | False | L112@2024-03-15 |
| 18 | MNT | False | L118@2024-03-15 |
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
| 45 | MNT | False | - |
| 46 | MNT | False | - |
| 47 | MNT | False | - |
| 48 | MNT | False | - |
| 49 | MNT | False | - |
| 50 | MNT | False | - |

Every loan in this capture is **MNT**.

## Findings — what the sweep observed and did not

* **Observed — `createJournalEntriesForChargeback` at the GL level:** 157 legs on 68 loan transaction(s) across loans 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50; 8 leg(s) on a charged-off loan (loans 16, 17, 18). See the listing above for each leg and its account.
* **Portion arms (step 6) — FEE: OBSERVED, PENALTY: OBSERVED.** Chargeback transactions carry a non-zero FEE portion on loan(s) 5, 11, 14, 17 and a non-zero PENALTY portion on loan(s) 3, 4, 5, 12, 18, 19, 20, 21, 22, 23, 47; the column listing above gives each amount. `interest`, `overpayment` and `unrecognized income` arms are observed/observed/not observed respectively.
* **`paid > credited` leg — FINDING.** FINDING -- no genuine `paid > credited` leg: the only CREDIT(s) to a principal/fee/penalty account (3 leg(s) on loan 23 tx L147, loan 23 tx L149) each have an equal DEBIT under the same transactionId, i.e. a chargeback reversal/replay pair, not the `credited < paid` difference posting.  The `paid > credited` arm is NOT exercised in this replay.
* **Fraud:** no loan in this feature is fraud-flagged, so the `isMarkedFraud` / `chargeOffFraudExpense` variants are not exercised (every `fraud` above is `false`).

