# OWNER — Tier D `LoanChargesProgressiveLoan.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD20-CX)

Whole-file replay of `LoanChargesProgressiveLoan.feature` (42 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 42 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSV is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the CHARGE-ADJUSTMENT posting family of `AccrualBasedAccountingProcessorForLoan.java` :997-1214 — `createJournalEntriesForChargeAdjustment` → `...ForLoanChargeAdjustment` / `...ForChargeOffLoanChargeAdjustment`. The charge-off arm had never been observed. `LoanChargesProgressiveLoan.feature` exercises both: scenario `C3544` / loan 40 charges the loan off, then adjusts a charge on the charged-off loan (accrual activity), while `C3543` / loan 39 does the same with accounting rule NONE. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at the transaction date, lists every charge-related leg, and gives each charge-related transaction's amount and its read-back portions.

## Provenance

OH-TIERD20-CX ran the rig, the replay (42/42), the extraction, the sweep, the product mappings, the teardown and the type join. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the join was built offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-charges-progressive-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the OH-TIERD17-CR copy) |
| `replay-charges-progressive-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 42 PASSED scenarios (1437 bodies) |
| `manifest-charges-progressive.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-charges-progressive.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 42/42 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 12 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `charge-related-legs.tsv` | flat listing of every charge-related leg (required columns) |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**42 scenarios, 42 PASSED, 0 FAILED; 1032 steps (1032 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | tag | line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C2910 | 5 | PASSED | 1 | `LP2_DOWNPAYMENT_AUTO` |
| 2 | C2911 | 48 | PASSED | 2 | `LP2_DOWNPAYMENT` |
| 3 | C2912 | 92 | PASSED | 3 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 4 | C2914 | 135 | PASSED | 4 | `None` |
| 5 | C2915 | 166 | PASSED | 5 | `LP2_DOWNPAYMENT_AUTO` |
| 6 | C2916 | 209 | PASSED | 6 | `LP2_DOWNPAYMENT` |
| 7 | C2917 | 253 | PASSED | 7 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 8 | C2918 | 296 | PASSED | 8 | `None` |
| 9 | C2919 | 324 | PASSED | 9 | `LP2_DOWNPAYMENT_AUTO` |
| 10 | C2920 | 358 | PASSED | 10 | `LP2_DOWNPAYMENT` |
| 11 | C2921 | 391 | PASSED | 11 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 12 | C2923 | 425 | PASSED | 12 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 13 | C2924 | 462 | PASSED | 13 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 14 | C2925 | 499 | PASSED | 14 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 15 | C2926 | 536 | PASSED | 15 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 16 | C2927 | 573 | PASSED | 16 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 17 | C2928 | 610 | PASSED | 17 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 18 | C2929 | 644 | PASSED | 18 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 19 | C2930 | 678 | PASSED | 19 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 20 | C2931 | 712 | PASSED | 20 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 21 | C2932 | 745 | PASSED | 21 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 22 | C2933 | 778 | PASSED | 22 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 23 | C2993 | 812 | PASSED | 23 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 24 | C2994 | 859 | PASSED | 24 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 25 | C2995 | 904 | PASSED | 25 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 26 | C4014 | 939 | PASSED | 26 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 27 | C4018 | 989 | PASSED | 27 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 28 | C4678 | 1148 | PASSED | 28 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_MULTIDISBURSE` |
| 29 | C4689 | 1223 | PASSED | 29 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_CHARGES` |
| 30 | C3260 | 1284 | PASSED | 30 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 31 | C3319 | 1320 | PASSED | 31 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 32 | C3320 | 1362 | PASSED | 32 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 33 | С3335 | 1404 | PASSED | 33 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 34 | C3321 | 1447 | PASSED | 34 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 35 | C3336 | 1490 | PASSED | 35 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 36 | C3425 | 1535 | PASSED | 36 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 37 | C3501 | 1614 | PASSED | 37 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 38 | C3502 | 1656 | PASSED | 38 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 39 | C3543 | 1708 | PASSED | 39 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_ACCOUNTING_RULE_NONE` |
| 40 | C3544 | 1756 | PASSED | 40 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_ACCRUAL_ACTIVITY` |
| 41 | C3571 | 1806 | PASSED | 41 | `None` |
| 42 | C3613 | 1833 | PASSED | 42 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 42 loans, 1437 bodies kept under `loans/`, each body sha256-pinned in `manifest-charges-progressive.json`; the FAILED scenarios' loans are not committed (`manifest-charges-progressive-passed.json`).

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **42/42 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 536 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). **536 legs, 8 types, 0 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the leg's transaction date.** `fraud` per leg = the loan's fraud flag (`markAsFraud` request/read-back).

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 263 | 2 | 40 |
| `loanTransactionType.accrual` | 96 | 2 | 40 |
| `loanTransactionType.disbursement` | 82 | 0 | – |
| `loanTransactionType.downPayment` | 36 | 0 | – |
| `loanTransactionType.merchantIssuedRefund` | 30 | 0 | – |
| `loanTransactionType.interestRefund` | 16 | 0 | – |
| `loanTransactionType.chargeAdjustment` | 8 | 2 | 40 |
| `loanTransactionType.chargeOff` | 5 | 5 | 40 |

### The charge-related arms (step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.

| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.chargeAdjustment` | True | 8 | 4 | 30, 36, 40, 41 | 2 | 40 | 6 | 30, 36, 41 |
| `loanTransactionType.chargeOff` | True | 5 | 1 | 40 | 5 | 40 | 0 | – |
| `loanTransactionType.chargeback` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.creditBalanceRefund` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.goodwillCredit` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.interestRefund` | True | 16 | 5 | 26, 27 | 0 | – | 16 | 26, 27 |
| `loanTransactionType.merchantIssuedRefund` | True | 30 | 5 | 26, 27 | 0 | – | 30 | 26, 27 |
| `loanTransactionType.payoutRefund` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.waiveCharges` | False | 0 | 0 | – | 0 | – | 0 | – |
| `loanTransactionType.writeoff` | False | 0 | 0 | – | 0 | – | 0 | – |

**FINDING:** charge-related transaction type(s) with NO legs at all: loanTransactionType.chargeback, loanTransactionType.creditBalanceRefund, loanTransactionType.goodwillCredit, loanTransactionType.payoutRefund, loanTransactionType.waiveCharges, loanTransactionType.writeoff.

**FINDING:** 5 charge-related transaction(s) in the read-backs have NO journal-entry legs: loan 23 tx L132, loan 24 tx L138, loan 25 tx L141, loan 39 tx L226, loan 39 tx L227.

### Every charge-related leg — required listing

Every leg of every charge-related transaction type, with the leg's GL account (id + name), entry side, amount in minor units, the loan fraud flag and whether the loan was charged off at the transaction date.  `charged-off at tx date` = a NON-REVERSED `chargeOff` dated on or before the leg's transaction date; `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged-off at tx date | charged-off latest | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `loanTransactionType.interestRefund` | 26 | L148 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L148 | DEBIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L148 | CREDIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L148 | CREDIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | DEBIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L149 | CREDIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L156 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 26 | L156 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L157 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L157 | CREDIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 26 | L157 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 1060 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | DEBIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | CREDIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L173 | CREDIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | DEBIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 8 | 112601 | Loans Receivable | 17820 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 12 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L174 | CREDIT | 19 | l1 | Overpayment account | 1048 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | DEBIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | CREDIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L177 | CREDIT | 19 | l1 | Overpayment account | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 8 | 112601 | Loans Receivable | 18620 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 9 | 112603 | Interest/Fee Receivable | 202 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | DEBIT | 19 | l1 | Overpayment account | 58 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 8 | 112601 | Loans Receivable | 18620 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 202 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L178 | CREDIT | 19 | l1 | Overpayment account | 58 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L179 | DEBIT | 4 | 404000 | Interest Income | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.interestRefund` | 27 | L179 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 787 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L180 | DEBIT | 7 | 145023 | Suspense/Clearing account | 18880 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L180 | CREDIT | 8 | 112601 | Loans Receivable | 18620 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.merchantIssuedRefund` | 27 | L180 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 260 | False | False | False | MNT | 2025-08-13 | - |
| `loanTransactionType.chargeAdjustment` | 30 | L190 | DEBIT | 3 | 404007 | Fee Income | 100 | False | False | False | MNT | 2024-09-27 | - |
| `loanTransactionType.chargeAdjustment` | 30 | L190 | CREDIT | 8 | 112601 | Loans Receivable | 100 | False | False | False | MNT | 2024-09-27 | - |
| `loanTransactionType.chargeAdjustment` | 36 | L213 | DEBIT | 3 | 404007 | Fee Income | 2000 | False | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.chargeAdjustment` | 36 | L213 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 2000 | False | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.chargeOff` | 40 | L231 | DEBIT | 11 | 744007 | Credit Loss/Bad Debt | 10000 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | DEBIT | 12 | 404008 | Fee Charge Off | 500 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | DEBIT | 17 | 404001 | Interest Income Charge Off | 214 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | CREDIT | 8 | 112601 | Loans Receivable | 10000 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeOff` | 40 | L231 | CREDIT | 9 | 112603 | Interest/Fee Receivable | 714 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeAdjustment` | 40 | L232 | DEBIT | 3 | 404007 | Fee Income | 500 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeAdjustment` | 40 | L232 | CREDIT | 12 | 404008 | Fee Charge Off | 500 | False | True | True | MNT | 2024-03-01 | L231 |
| `loanTransactionType.chargeAdjustment` | 41 | L239 | DEBIT | 3 | 404007 | Fee Income | 1000 | False | False | False | MNT | 2025-03-25 | - |
| `loanTransactionType.chargeAdjustment` | 41 | L239 | CREDIT | 8 | 112601 | Loans Receivable | 1000 | False | False | False | MNT | 2025-03-25 | - |

### Every charge-related transaction and its read-back amount / portions

Portions are integer minor units; `-` means the read-back did not carry that field. The `amount` is the transaction `amount`; portions are the oracle's `principalPortion`, `interestPortion`, `feeChargesPortion`, `penaltyChargesPortion`, `overpaymentPortion` and `unrecognizedIncomePortion`.

| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| 23 | L132 | `loanTransactionType.waiveCharges` | 2023-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | False | False | False | MNT | 0 |
| 24 | L138 | `loanTransactionType.waiveCharges` | 2023-04-05 | 1000 | 0 | 0 | 0 | 0 | 0 | 1000 | False | False | False | MNT | 0 |
| 25 | L141 | `loanTransactionType.waiveCharges` | 2023-02-22 | 10000 | 0 | 0 | 0 | 0 | 0 | 10000 | False | False | False | MNT | 0 |
| 26 | L148 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 0 | 0 | 0 | 787 | 0 | False | False | False | MNT | 4 |
| 26 | L149 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 17820 | 12 | 0 | 0 | 1048 | 0 | False | False | False | MNT | 8 |
| 26 | L156 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 12 | 0 | 775 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L157 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 17820 | 0 | 0 | 1060 | 0 | 0 | False | False | False | MNT | 3 |
| 27 | L173 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 0 | 0 | 0 | 787 | 0 | False | False | False | MNT | 4 |
| 27 | L174 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 17820 | 12 | 0 | 0 | 1048 | 0 | False | False | False | MNT | 8 |
| 27 | L177 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 0 | 0 | 0 | 787 | 0 | False | False | False | MNT | 4 |
| 27 | L178 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 18620 | 202 | 0 | 0 | 58 | 0 | False | False | False | MNT | 8 |
| 27 | L179 | `loanTransactionType.interestRefund` | 2025-08-13 | 787 | 0 | 12 | 0 | 775 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L180 | `loanTransactionType.merchantIssuedRefund` | 2025-08-13 | 18880 | 18620 | 190 | 0 | 70 | 0 | 0 | False | False | False | MNT | 3 |
| 30 | L190 | `loanTransactionType.chargeAdjustment` | 2024-09-27 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L213 | `loanTransactionType.chargeAdjustment` | 2024-02-01 | 2000 | 0 | 0 | 0 | 2000 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L226 | `loanTransactionType.chargeOff` | 2024-03-01 | 10714 | 10000 | 214 | 500 | 0 | 0 | 0 | False | True | False | MNT | 0 |
| 39 | L227 | `loanTransactionType.chargeAdjustment` | 2024-03-01 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | True | False | MNT | 0 |
| 40 | L231 | `loanTransactionType.chargeOff` | 2024-03-01 | 10714 | 10000 | 214 | 500 | 0 | 0 | 0 | False | True | False | MNT | 5 |
| 40 | L232 | `loanTransactionType.chargeAdjustment` | 2024-03-01 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 41 | L239 | `loanTransactionType.chargeAdjustment` | 2025-03-25 | 1000 | 1000 | 0 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |

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
| 26 | MNT | False | False | - |
| 27 | MNT | False | False | - |
| 28 | MNT | False | False | - |
| 29 | MNT | False | False | - |
| 30 | MNT | False | False | - |
| 31 | MNT | False | False | - |
| 32 | MNT | False | False | - |
| 33 | MNT | False | False | - |
| 34 | MNT | False | False | - |
| 35 | MNT | False | False | - |
| 36 | MNT | False | False | - |
| 37 | MNT | False | False | - |
| 38 | MNT | False | False | - |
| 39 | MNT | False | True | L226@2024-03-01 |
| 40 | MNT | False | True | L231@2024-03-01 |
| 41 | MNT | False | False | - |
| 42 | MNT | False | False | - |

Every loan in this capture is **MNT**.

## Findings — what the sweep observed and did not

* **Observed — `loanTransactionType.chargeAdjustment` at the GL level:** 8 leg(s) on 4 loan transaction(s) across loans 30, 36, 40, 41; 2 leg(s) on a charged-off loan (loans 40). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.chargeOff` at the GL level:** 5 leg(s) on 1 loan transaction(s) across loans 40; 5 leg(s) on a charged-off loan (loans 40). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **FINDING — `loanTransactionType.chargeback` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **FINDING — `loanTransactionType.creditBalanceRefund` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **FINDING — `loanTransactionType.goodwillCredit` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **Observed — `loanTransactionType.interestRefund` at the GL level:** 16 leg(s) on 5 loan transaction(s) across loans 26, 27; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.merchantIssuedRefund` at the GL level:** 30 leg(s) on 5 loan transaction(s) across loans 26, 27; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **FINDING — `loanTransactionType.payoutRefund` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **FINDING — `loanTransactionType.waiveCharges` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **FINDING — `loanTransactionType.writeoff` has NO legs:** the type is absent from every swept body. The charge-related arm it names was not exercised at the GL level by this replay (or its loan was not extracted). This is a finding, not a silent gap.
* **FINDING — charge-related transaction(s) without journal-entry legs:** loan 23 tx L132, loan 24 tx L138, loan 25 tx L141, loan 39 tx L226, loan 39 tx L227. The charge-related arms should post for every such transaction, so a leg-less transaction is a shape worth checking.
* **Fraud:** no loan in this feature is fraud-flagged, so the `isMarkedFraud` / charge-off-fraud variants are not exercised (every `fraud` above is `false`).

### The charge-off charge-adjustment arm — the new observation (step 6)

The charge-adjustment family splits on the loan's charged-off state at posting time. In this capture:

* **loan 40 (scenario `C3544`, accrual activity) — charged off, and the arm posts.** `chargeOff` tx `L231` (2024-03-01) posts 5 legs: Dr Credit Loss/Bad Debt `744007` 10 000, Dr Fee Charge Off `404008` 500, Dr Interest Income Charge Off `404001` 214; Cr Loans Receivable `112601` 10 000, Cr Interest/Fee Receivable `112603` 714. The immediately following `chargeAdjustment` tx `L232` (same date) posts 2 legs: **Dr Fee Income `404007` 500 / Cr Fee Charge Off `404008` 500**. That two-leg shape — debit the original fee income, credit the charge-off account — is the `...ForChargeOffLoanChargeAdjustment` arm, observed here for the first time. It is flagged `charged_off` because non-reversed `L231` is dated on or before `L232`, and loan 40's LATEST read-back keeps `chargedOff = true` (no later reversal).
* **loan 39 (scenario `C3543`, accounting rule NONE) — charged off, but nothing posts.** `chargeOff` `L226` and `chargeAdjustment` `L227` exist as read-back transactions and carry **no journal-entry legs at all** — the product's accounting rule is NONE, so the arm cannot be observed at the GL level. This is the paired control for loan 40, and the reason the two `L226`/`L227` leg-less transactions appear in the finding above.
* **not charged off.** `chargeAdjustment` on loans 30 (`L190`), 36 (`L213`) and 41 (`L239`) posts the non-charge-off two-leg shape — Dr Fee Income `404007` / Cr Loans Receivable `112601` (loans 30, 41) or Cr Interest/Fee Receivable `112603` (loan 36) — i.e. `...ForLoanChargeAdjustment`.

So the sweep observed **both** charge-adjustment posting arms: `...ForLoanChargeAdjustment` on not-charged-off loans 30 / 36 / 41, and `...ForChargeOffLoanChargeAdjustment` on charged-off loan 40, with loan 39 as the accounting-rule-NONE control that posts nothing. The transaction TYPE the read-backs carry is the single code `loanTransactionType.chargeAdjustment` for both arms — the arm is distinguished only by the loan's charged-off state, which is exactly why the charged-off join was required. `waiveCharges` is carried by the read-backs on loans 23 (`L132`), 24 (`L138`) and 25 (`L141`) but posts no legs; `interestRefund` / `merchantIssuedRefund` post on loans 26 / 27. All are listed above. No charge-off was later undone in this capture, so `charged-off at tx date` and `charged-off latest` agree on every leg.

