# OWNER — Tier D `LoanBuyDownFees.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD17-CR)

Whole-file replay of `LoanBuyDownFees.feature` (47 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 47 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file, in the join and in the TSV is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the BUY-DOWN-FEE posting family of `AccrualBasedAccountingProcessorForLoan.java` :530-792 — `createJournalEntriesForBuyDownFee`, `...BuyDownFeeAdjustment`, `...BuyDownFeeAmortization`, `...ChargeOffLoanBuyDownFeeAmortization` and `...BuyDownFeeAmortizationAdjustment` — which had never been observed at the GL level. `LoanBuyDownFees.feature` exercises all of them, with charge-offs on part of the file. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at the transaction date, and lists every buy-down-fee leg, each buy-down-fee transaction's amount and its read-back portions.

## Provenance

OH-TIERD17-CR ran the rig, the replay (47/47), the extraction, the sweep, the product mappings, the teardown and the type join. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`); the join was built offline over the captured JSON. Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-buydown-fees-mnt.sh` | the exact replay driver (only FEATURE / LOG / container changed from the OH-TIERD15-CM copy) |
| `replay-buydown-fees-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 47 PASSED scenarios (1850 bodies) |
| `manifest-buydown-fees.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-buydown-fees.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 47/47 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 6 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off/fraud state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `buydown-fees-legs.tsv` | flat listing of every buy-down-fee leg (required columns) |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**47 scenarios, 47 PASSED, 0 FAILED; 1612 steps (1612 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | tag | line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3770 | 5 | PASSED | 1 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 2 | C3827 | 66 | PASSED | 2 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 3 | C3771 | 311 | PASSED | 3 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 4 | C3828 | 371 | PASSED | 4 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 5 | C3772 | 563 | PASSED | 5 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 6 | C3829 | 637 | PASSED | 6 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 7 | C3848 | 842 | PASSED | 7 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 8 | C3849 | 942 | PASSED | 8 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 9 | C3850 | 1043 | PASSED | 9 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CHARGE_OFF_REASON` |
| 10 | C3851 | 1106 | PASSED | 10 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CHARGE_OFF_REASON` |
| 11 | C3852 | 1168 | PASSED | 11 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CHARGE_OFF_REASON` |
| 12 | C3886 | 1255 | PASSED | 12 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 13 | С3825 | 1342 | PASSED | 13 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 14 | С3826 | 1449 | PASSED | 14 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 15 | C3853 | 1567 | PASSED | 15 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 16 | C3881 | 1628 | PASSED | 16 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 17 | C3887 | 2188 | PASSED | 17 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 18 | C3888 | 2471 | PASSED | 18 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 19 | C3889 | 2534 | PASSED | 19 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 20 | C3981 | 2676 | PASSED | 20 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT` |
| 21 | C3982 | 2741 | PASSED | 21 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT` |
| 22 | C3983 | 2803 | PASSED | 22 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT` |
| 23 | C3984 | 2904 | PASSED | 23 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT` |
| 24 | C3985 | 3005 | PASSED | 24 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT_CHARGE_OFF_REASON` |
| 25 | С3986 | 3092 | PASSED | 25 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT` |
| 26 | C4004 | 3226 | PASSED | 26 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 27 | C4009 | 3265 | PASSED | 27 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 28 | C4019 | 3318 | PASSED | 28 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 29 | C4022 | 3417 | PASSED | 29 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 30 | C4040 | 3588 | PASSED | 30 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 31 | C4043 | 3670 | PASSED | 31 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 32 | C4092 | 3812 | PASSED | 32 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` |
| 33 | C4093 | 3836 | PASSED | 33 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` |
| 34 | C4094 | 3860 | PASSED | 34 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` |
| 35 | C4116 | 3896 | PASSED | 35 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` |
| 36 | C4117 | 3990 | PASSED | 36 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 37 | CXXXX | 4171 | PASSED | 37 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 38 | CXXXX | 4172 | PASSED | 38 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CHARGE_OFF_REASON` |
| 39 | CXXXX | 4173 | PASSED | 39 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT_CHARGE_OFF_REASON` |
| 40 | CXXXX | 4174 | PASSED | 40 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 41 | CXXXX | 4175 | PASSED | 41 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT` |
| 42 | CXXXX | 4176 | PASSED | 42 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` |
| 43 | C85357 | 4179 | PASSED | 43 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_FEE_INCOME` |
| 44 | C85358 | 4262 | PASSED | 44 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_FEE_INCOME` |
| 45 | C85359 | 4323 | PASSED | 45 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_FEE_INCOME` |
| 46 | C85355 | 4427 | PASSED | 46 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |
| 47 | C85356 | 4506 | PASSED | 47 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 47 loans, 1850 bodies kept under `loans/`, each body sha256-pinned in `manifest-buydown-fees.json`; the FAILED scenarios' loans are not committed (`manifest-buydown-fees-passed.json`).

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **47/47 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 4850 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF, FRAUD (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`). **4850 legs, 11 types, 1638 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction dated on or before the leg's transaction date.** `fraud` per leg = the loan's fraud flag (`markAsFraud` request/read-back).

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `(unmapped)` | 1638 | 0 | – |
| `loanTransactionType.buyDownFeeAmortization` | 1344 | 24 | 5, 6, 9, 10, 12, 31 |
| `loanTransactionType.accrual` | 1284 | 12 | 5, 6, 9, 10, 12, 31 |
| `loanTransactionType.repayment` | 185 | 12 | 5, 6, 9, 10, 12, 31 |
| `loanTransactionType.buyDownFee` | 132 | 0 | – |
| `loanTransactionType.disbursement` | 94 | 0 | – |
| `loanTransactionType.chargeOff` | 72 | 24 | 5, 6, 9, 10, 12, 31 |
| `loanTransactionType.buyDownFeeAdjustment` | 68 | 0 | – |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 24 | 0 | – |
| `loanTransactionType.payoutRefund` | 6 | 0 | – |
| `loanTransactionType.writeOff` | 3 | 0 | – |

### The buy-down-fee arms (step 6)

Charged-off rule: a NON-REVERSED chargeOff loan transaction dated on or before the transaction/leg date.

| type | present | legs | transactions | loans | legs on charged-off loan | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.buyDownFee` | True | 132 | 61 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 | 0 | – | 132 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 |
| `loanTransactionType.buyDownFeeAdjustment` | True | 68 | 24 | 13, 14, 16, 19, 25, 26, 29, 30, 31, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45 | 0 | – | 68 | 13, 14, 16, 19, 25, 26, 29, 30, 31, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45 |
| `loanTransactionType.buyDownFeeAmortization` | True | 1344 | 661 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 | 24 | 5, 6, 9, 10, 12, 31 | 1320 | 1, 2, 3, 4, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | True | 24 | 12 | 17, 19, 29, 30, 37, 38, 39, 40, 41, 42, 43 | 0 | – | 24 | 17, 19, 29, 30, 37, 38, 39, 40, 41, 42, 43 |

### Every buy-down-fee leg — required listing

Every leg of every buy-down-fee transaction type, with the leg's GL account (id + name), entry side, amount in minor units, the loan fraud flag and whether the loan was charged off at the transaction date.

| type | loan | tx | entry | account id | account code | account name | amount (minor) | fraud | charged_off | currency | tx date | charge-off tx |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- |
| `loanTransactionType.buyDownFee` | 1 | L2 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 1 | L2 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 1 | L6 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 1 | L6 | CREDIT | 24 | 450281 | Income From Buy Down | 5000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 2 | L10 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 2 | L10 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L11 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L11 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L14 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L14 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L16 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L16 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L18 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L18 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L20 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L20 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L22 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L22 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L24 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L24 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L26 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L26 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L28 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L28 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L30 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L30 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L32 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L32 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L34 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L34 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L36 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L36 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L38 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L38 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L40 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L40 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L42 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L42 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L44 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L44 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L46 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L46 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L48 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L48 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L50 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L50 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L52 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L52 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L54 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L54 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L56 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L56 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L58 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L58 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L60 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L60 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L62 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L62 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L64 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L64 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L66 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L66 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L68 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L68 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L70 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L70 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L72 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L72 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L74 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L74 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L76 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L76 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L78 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L78 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L80 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L80 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L82 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L82 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L84 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L84 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L86 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L86 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L88 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L88 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L90 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L90 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L92 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L92 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L94 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L94 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L96 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L96 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L98 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L98 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L100 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L100 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L102 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L102 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L104 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L104 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L106 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L106 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L108 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L108 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L110 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L110 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L112 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L112 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L114 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L114 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L116 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L116 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L118 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L118 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L120 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L120 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L122 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L122 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L124 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L124 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L126 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L126 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L128 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L128 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L130 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L130 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L133 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L133 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L135 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L135 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L136 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L136 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L138 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L138 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-03-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L140 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L140 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L141 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L141 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L143 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L143 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L144 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L144 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L146 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L146 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L148 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L148 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L149 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L149 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L151 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L151 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L153 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L153 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L154 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L154 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L156 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L156 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L157 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L157 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L159 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L159 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L161 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L161 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L162 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L162 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L164 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L164 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L166 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L166 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L167 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L167 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L169 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L169 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L171 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L171 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L172 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L172 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L174 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L174 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L175 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L175 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L177 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L177 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L179 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L179 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L180 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L180 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L182 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 2 | L182 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 3 | L186 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 3 | L186 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 3 | L190 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 3 | L190 | CREDIT | 24 | 450281 | Income From Buy Down | 5000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFee` | 4 | L192 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 4 | L192 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L193 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L193 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L196 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L196 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L198 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L198 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L200 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L200 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L202 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L202 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L204 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L204 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L206 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L206 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L208 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L208 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L210 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L210 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L212 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L212 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L214 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L214 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L216 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L216 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L218 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L218 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L220 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L220 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L222 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L222 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L224 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L224 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L226 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L226 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L228 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L228 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L230 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L230 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L232 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L232 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L234 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L234 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L236 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L236 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L238 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L238 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L240 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L240 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L242 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L242 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L244 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L244 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L246 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L246 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L248 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L248 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L250 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L250 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L252 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L252 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L254 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L254 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L256 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L256 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L258 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L258 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L260 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L260 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L262 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L262 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L264 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L264 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L266 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L266 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L268 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L268 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L270 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L270 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L272 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L272 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L274 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L274 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L276 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L276 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L278 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L278 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L280 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L280 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L282 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L282 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L284 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L284 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L286 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L286 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L288 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L288 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L290 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L290 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L292 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L292 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L294 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L294 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L296 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L296 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L298 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L298 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L300 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L300 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L302 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L302 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L304 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L304 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L306 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L306 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L308 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L308 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L310 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L310 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L312 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L312 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L315 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1703 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 4 | L315 | CREDIT | 24 | 450281 | Income From Buy Down | 1703 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFee` | 5 | L317 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 5 | L317 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 5 | L319 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3352 | False | True | MNT | 2024-03-01 | L321 |
| `loanTransactionType.buyDownFeeAmortization` | 5 | L319 | CREDIT | 24 | 450281 | Income From Buy Down | 3352 | False | True | MNT | 2024-03-01 | L321 |
| `loanTransactionType.buyDownFeeAmortization` | 5 | L322 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1648 | False | True | MNT | 2024-03-01 | L321 |
| `loanTransactionType.buyDownFeeAmortization` | 5 | L322 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 1648 | False | True | MNT | 2024-03-01 | L321 |
| `loanTransactionType.buyDownFee` | 6 | L325 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 6 | L325 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L326 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L326 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L329 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L329 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L331 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L331 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L333 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L333 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L335 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L335 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L337 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L337 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L339 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L339 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L341 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L341 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L343 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L343 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L345 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L345 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L347 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L347 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L349 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L349 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L351 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L351 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L353 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L353 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L355 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L355 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L357 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L357 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L359 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L359 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L361 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L361 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L363 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L363 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L365 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L365 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L367 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L367 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L369 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L369 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L371 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L371 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L373 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L373 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L375 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L375 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L377 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L377 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L379 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L379 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L381 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L381 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L383 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L383 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L385 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L385 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L387 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L387 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L389 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L389 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L391 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L391 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L393 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L393 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L395 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L395 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L397 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L397 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L399 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L399 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L401 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L401 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L403 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L403 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L405 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L405 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L407 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L407 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L409 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L409 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L411 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L411 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L413 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L413 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L415 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L415 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L417 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L417 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L419 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L419 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L421 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L421 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L423 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L423 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L425 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L425 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L427 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L427 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L429 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L429 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L431 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L431 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L433 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L433 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L435 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L435 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L437 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L437 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L439 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L439 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L441 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L441 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L443 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L443 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L445 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L445 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L446 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | True | MNT | 2024-03-01 | L448 |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L446 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | True | MNT | 2024-03-01 | L448 |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L449 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1648 | False | True | MNT | 2024-03-01 | L448 |
| `loanTransactionType.buyDownFeeAmortization` | 6 | L449 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 1648 | False | True | MNT | 2024-03-01 | L448 |
| `loanTransactionType.buyDownFee` | 7 | L452 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 7 | L452 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L453 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L453 | CREDIT | 24 | 450281 | Income From Buy Down | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L456 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L456 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L456 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L456 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L458 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 7 | L458 | CREDIT | 24 | 450281 | Income From Buy Down | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFee` | 8 | L460 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 8 | L460 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L461 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1758 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L461 | CREDIT | 24 | 450281 | Income From Buy Down | 1758 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L464 | DEBIT | 16 | 744037 | Credit Loss/Bad Debt-Fraud | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L464 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L464 | CREDIT | 16 | 744037 | Credit Loss/Bad Debt-Fraud | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L464 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L466 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 8 | L466 | CREDIT | 24 | 450281 | Income From Buy Down | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFee` | 9 | L468 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 9 | L468 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 9 | L469 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1374 | True | True | MNT | 2024-01-25 | L471 |
| `loanTransactionType.buyDownFeeAmortization` | 9 | L469 | CREDIT | 24 | 450281 | Income From Buy Down | 1374 | True | True | MNT | 2024-01-25 | L471 |
| `loanTransactionType.buyDownFeeAmortization` | 9 | L472 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | True | MNT | 2024-01-25 | L471 |
| `loanTransactionType.buyDownFeeAmortization` | 9 | L472 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 3626 | True | True | MNT | 2024-01-25 | L471 |
| `loanTransactionType.buyDownFee` | 10 | L475 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 10 | L475 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 10 | L476 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1374 | True | True | MNT | 2024-01-25 | L478 |
| `loanTransactionType.buyDownFeeAmortization` | 10 | L476 | CREDIT | 24 | 450281 | Income From Buy Down | 1374 | True | True | MNT | 2024-01-25 | L478 |
| `loanTransactionType.buyDownFeeAmortization` | 10 | L479 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | True | MNT | 2024-01-25 | L478 |
| `loanTransactionType.buyDownFeeAmortization` | 10 | L479 | CREDIT | 16 | 744037 | Credit Loss/Bad Debt-Fraud | 3626 | True | True | MNT | 2024-01-25 | L478 |
| `loanTransactionType.buyDownFee` | 11 | L482 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 11 | L482 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L483 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1374 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L483 | CREDIT | 24 | 450281 | Income From Buy Down | 1374 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L486 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L486 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L486 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L486 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L488 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 11 | L488 | CREDIT | 24 | 450281 | Income From Buy Down | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFee` | 12 | L490 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 12 | L490 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 12 | L492 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1703 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 12 | L492 | CREDIT | 24 | 450281 | Income From Buy Down | 1703 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFee` | 12 | L493 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFee` | 12 | L493 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 12 | L494 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4149 | False | True | MNT | 2024-03-01 | L496 |
| `loanTransactionType.buyDownFeeAmortization` | 12 | L494 | CREDIT | 24 | 450281 | Income From Buy Down | 4149 | False | True | MNT | 2024-03-01 | L496 |
| `loanTransactionType.buyDownFeeAmortization` | 12 | L497 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4148 | False | True | MNT | 2024-03-01 | L496 |
| `loanTransactionType.buyDownFeeAmortization` | 12 | L497 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 4148 | False | True | MNT | 2024-03-01 | L496 |
| `loanTransactionType.buyDownFee` | 13 | L500 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 13 | L500 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 13 | L502 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 13 | L502 | CREDIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 13 | L504 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 13 | L504 | CREDIT | 24 | 450281 | Income From Buy Down | 4000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 14 | L509 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 14 | L509 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 14 | L511 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 14 | L511 | CREDIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 14 | L512 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 500 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 14 | L512 | CREDIT | 23 | 450280 | Buy Down Expense | 500 | False | False | MNT | 2024-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 14 | L514 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3500 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 14 | L514 | CREDIT | 24 | 450281 | Income From Buy Down | 3500 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 15 | L519 | DEBIT | 23 | 450280 | Buy Down Expense | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 15 | L519 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 15 | L521 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 15 | L521 | CREDIT | 15 | e4 | Written off | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 16 | L523 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 16 | L523 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L524 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L524 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L527 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L527 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L529 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L529 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L531 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L531 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L533 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L533 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L535 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L535 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L537 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L537 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L539 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L539 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L541 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L541 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L543 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L543 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L545 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L545 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L547 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L547 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L549 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L549 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L551 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L551 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L553 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L553 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L555 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L555 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L557 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L557 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L559 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L559 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L561 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L561 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L563 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L563 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L565 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L565 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L567 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L567 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L569 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L569 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L571 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L571 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L573 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L573 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L575 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L575 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L577 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L577 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L579 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L579 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L581 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L581 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L583 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L583 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L585 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L585 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L588 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L588 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L590 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L590 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L592 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L592 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L594 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L594 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L596 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L596 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L598 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L598 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L600 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L600 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L602 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L602 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L604 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L604 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L606 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L606 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L608 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L608 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L610 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L610 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L612 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L612 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L614 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L614 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L616 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L616 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L618 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L618 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L620 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L620 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L622 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L622 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L624 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L624 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L626 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L626 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L628 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L628 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L630 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L630 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L632 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L632 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L634 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L634 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L636 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L636 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L638 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L638 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L640 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L640 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L642 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L642 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L644 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L644 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-29 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 16 | L645 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 16 | L645 | DEBIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 16 | L645 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 16 | L645 | CREDIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L647 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 22 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L647 | CREDIT | 24 | 450281 | Income From Buy Down | 22 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L649 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 88 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L649 | CREDIT | 24 | 450281 | Income From Buy Down | 88 | False | False | MNT | 2024-03-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L651 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1593 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 16 | L651 | CREDIT | 24 | 450281 | Income From Buy Down | 1593 | False | False | MNT | 2024-03-03 | - |
| `loanTransactionType.buyDownFee` | 17 | L653 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 17 | L653 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 17 | L653 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 17 | L653 | CREDIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L654 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L654 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L657 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L657 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L659 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L659 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L661 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L661 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L663 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L663 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L665 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L665 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L667 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L667 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L669 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L669 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L671 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L671 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L673 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L673 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L675 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L675 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L677 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L677 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L679 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L679 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L681 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L681 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L683 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L683 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L685 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L685 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L687 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L687 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L689 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L689 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L691 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L691 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L693 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L693 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L695 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L695 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L697 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L697 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L699 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L699 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L701 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L701 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L703 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L703 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L705 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L705 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L707 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L707 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L709 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L709 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L711 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L711 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L713 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L713 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L715 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L715 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L717 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L717 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L719 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L719 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L721 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L721 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L723 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L723 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L725 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L725 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L727 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L727 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L729 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L729 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L731 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L731 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L733 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L733 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L735 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L735 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L737 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L737 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L739 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L739 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L741 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L741 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L743 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L743 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-02-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L745 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 17 | L745 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-02-15 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 17 | L747 | DEBIT | 24 | 450281 | Income From Buy Down | 2527 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 17 | L747 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 2527 | False | False | MNT | 2024-02-16 | - |
| `loanTransactionType.buyDownFee` | 18 | L751 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 18 | L751 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 18 | L751 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 18 | L751 | CREDIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 19 | L755 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 19 | L755 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 19 | L755 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 19 | L755 | CREDIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L756 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L756 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 19 | L757 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 19 | L757 | DEBIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 19 | L757 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 19 | L757 | CREDIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L759 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L759 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L761 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L761 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L763 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L763 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L765 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L765 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L767 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L767 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L769 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L769 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L771 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L771 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L773 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L773 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L775 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 19 | L775 | CREDIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 19 | L777 | DEBIT | 24 | 450281 | Income From Buy Down | 549 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 19 | L777 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 549 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFee` | 20 | L781 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 20 | L781 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 20 | L785 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 20 | L785 | CREDIT | 24 | 450281 | Income From Buy Down | 5000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 21 | L789 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 21 | L789 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 21 | L789 | CREDIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 21 | L789 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 22 | L793 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 22 | L793 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L794 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L794 | CREDIT | 24 | 450281 | Income From Buy Down | 1758 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L797 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L797 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L797 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L797 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L799 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 22 | L799 | CREDIT | 24 | 450281 | Income From Buy Down | 3242 | False | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFee` | 23 | L801 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 23 | L801 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L802 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1758 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L802 | CREDIT | 24 | 450281 | Income From Buy Down | 1758 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L805 | DEBIT | 16 | 744037 | Credit Loss/Bad Debt-Fraud | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L805 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L805 | CREDIT | 16 | 744037 | Credit Loss/Bad Debt-Fraud | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L805 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L807 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 23 | L807 | CREDIT | 24 | 450281 | Income From Buy Down | 3242 | True | False | MNT | 2024-02-01 | - |
| `loanTransactionType.buyDownFee` | 24 | L809 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 24 | L809 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | True | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L810 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1374 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L810 | CREDIT | 24 | 450281 | Income From Buy Down | 1374 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L813 | DEBIT | 18 | 744007 | Credit Loss/Bad Debt | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L813 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L813 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L813 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L815 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 24 | L815 | CREDIT | 24 | 450281 | Income From Buy Down | 3626 | True | False | MNT | 2024-01-25 | - |
| `loanTransactionType.buyDownFee` | 25 | L817 | DEBIT | 5 | 145023 | Suspense/Clearing account | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 25 | L817 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 25 | L819 | DEBIT | 5 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 25 | L819 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 25 | L819 | CREDIT | 5 | 145023 | Suspense/Clearing account | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 25 | L819 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 25 | L821 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 25 | L821 | CREDIT | 24 | 450281 | Income From Buy Down | 4000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 25 | L825 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 25 | L825 | CREDIT | 24 | 450281 | Income From Buy Down | 1000 | False | False | MNT | 2024-04-01 | - |
| `loanTransactionType.buyDownFee` | 26 | L827 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 26 | L827 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 26 | L828 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 26 | L828 | CREDIT | 23 | 450280 | Buy Down Expense | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 26 | L830 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 26 | L830 | CREDIT | 24 | 450281 | Income From Buy Down | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 27 | L832 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 27 | L832 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 27 | L833 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 27 | L833 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 27 | L834 | DEBIT | 23 | 450280 | Buy Down Expense | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 27 | L834 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 27 | L836 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 166 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 27 | L836 | CREDIT | 24 | 450281 | Income From Buy Down | 166 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 27 | L839 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 14779 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 27 | L839 | CREDIT | 24 | 450281 | Income From Buy Down | 14779 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFee` | 28 | L841 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 28 | L841 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 28 | L841 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 28 | L841 | CREDIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L842 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L842 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 28 | L843 | DEBIT | 23 | 450280 | Buy Down Expense | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 28 | L843 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 20000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L845 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 277 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L845 | CREDIT | 24 | 450281 | Income From Buy Down | 277 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L847 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 222 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L847 | DEBIT | 24 | 450281 | Income From Buy Down | 110 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L847 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 110 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L847 | CREDIT | 24 | 450281 | Income From Buy Down | 222 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L849 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 223 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L849 | CREDIT | 24 | 450281 | Income From Buy Down | 223 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L852 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 19333 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 28 | L852 | CREDIT | 24 | 450281 | Income From Buy Down | 19333 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFee` | 29 | L854 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 29 | L854 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L855 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L855 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 29 | L856 | DEBIT | 23 | 450280 | Buy Down Expense | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 29 | L856 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L858 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 166 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L858 | CREDIT | 24 | 450281 | Income From Buy Down | 166 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 29 | L859 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 29 | L859 | CREDIT | 23 | 450280 | Buy Down Expense | 4000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L861 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 111 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L861 | DEBIT | 24 | 450281 | Income From Buy Down | 34 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L861 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 34 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L861 | CREDIT | 24 | 450281 | Income From Buy Down | 111 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L863 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 121 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L863 | CREDIT | 24 | 450281 | Income From Buy Down | 121 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 29 | L864 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 6000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 29 | L864 | CREDIT | 23 | 450280 | Buy Down Expense | 6000 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 29 | L866 | DEBIT | 24 | 450281 | Income From Buy Down | 14 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 29 | L866 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 14 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 29 | L867 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 29 | L867 | CREDIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 29 | L869 | DEBIT | 24 | 450281 | Income From Buy Down | 54 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 29 | L869 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 54 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L872 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3649 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 29 | L872 | CREDIT | 24 | 450281 | Income From Buy Down | 3649 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFee` | 30 | L874 | DEBIT | 23 | 450280 | Buy Down Expense | 100 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 30 | L874 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 100 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L875 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L875 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L877 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L877 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L879 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L879 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L881 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L881 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L883 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L883 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L885 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L885 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L887 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L887 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L889 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L889 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L891 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L891 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L893 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L893 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L895 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L895 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L897 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L897 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L899 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L899 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L901 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 30 | L901 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 30 | L902 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 70 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 30 | L902 | CREDIT | 23 | 450280 | Buy Down Expense | 70 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 30 | L904 | DEBIT | 24 | 450281 | Income From Buy Down | 17 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 30 | L904 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 17 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFee` | 31 | L917 | DEBIT | 23 | 450280 | Buy Down Expense | 100 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 31 | L917 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 100 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L918 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L918 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L920 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L920 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L922 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L922 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L924 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L924 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L926 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L926 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L928 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L928 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L930 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L930 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L932 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L932 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L934 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L934 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L936 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L936 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L938 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L938 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L940 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L940 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L942 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L942 | CREDIT | 24 | 450281 | Income From Buy Down | 3 | False | False | MNT | 2024-01-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L944 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L944 | CREDIT | 24 | 450281 | Income From Buy Down | 4 | False | False | MNT | 2024-01-14 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 31 | L945 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 31 | L945 | CREDIT | 23 | 450280 | Buy Down Expense | 30 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L947 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L947 | CREDIT | 24 | 450281 | Income From Buy Down | 1 | False | False | MNT | 2024-01-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L948 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2 | False | True | MNT | 2024-01-16 | L950 |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L948 | CREDIT | 24 | 450281 | Income From Buy Down | 2 | False | True | MNT | 2024-01-16 | L950 |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L951 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 20 | False | True | MNT | 2024-01-16 | L950 |
| `loanTransactionType.buyDownFeeAmortization` | 31 | L951 | CREDIT | 18 | 744007 | Credit Loss/Bad Debt | 20 | False | True | MNT | 2024-01-16 | L950 |
| `loanTransactionType.buyDownFee` | 32 | L954 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 32 | L954 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 32 | L955 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 32 | L955 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 32 | L958 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4945 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 32 | L958 | CREDIT | 24 | 450281 | Income From Buy Down | 4945 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 33 | L960 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 33 | L960 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 33 | L961 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 33 | L961 | CREDIT | 7 | 404007 | Fee Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 33 | L964 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4945 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 33 | L964 | CREDIT | 7 | 404007 | Fee Income | 4945 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 34 | L966 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 34 | L966 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L967 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L967 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 34 | L968 | DEBIT | 23 | 450280 | Buy Down Expense | 2000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 34 | L968 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 2000 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L970 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 77 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L970 | CREDIT | 7 | 404007 | Fee Income | 22 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L970 | CREDIT | 24 | 450281 | Income From Buy Down | 55 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L972 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 6868 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L972 | CREDIT | 7 | 404007 | Fee Income | 1978 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 34 | L972 | CREDIT | 24 | 450281 | Income From Buy Down | 4890 | False | False | MNT | 2024-01-02 | - |
| `loanTransactionType.buyDownFee` | 35 | L974 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 35 | L974 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 35 | L975 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 35 | L975 | CREDIT | 23 | 450280 | Buy Down Expense | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 35 | L977 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2500 | False | False | MNT | 2024-04-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 35 | L977 | CREDIT | 7 | 404007 | Fee Income | 2500 | False | False | MNT | 2024-04-14 | - |
| `loanTransactionType.buyDownFee` | 35 | L978 | DEBIT | 23 | 450280 | Buy Down Expense | 3000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 35 | L978 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 35 | L979 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 35 | L979 | CREDIT | 23 | 450280 | Buy Down Expense | 500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 35 | L980 | DEBIT | 7 | 404007 | Fee Income | 500 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 35 | L980 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3000 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 35 | L980 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 500 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 35 | L980 | CREDIT | 24 | 450281 | Income From Buy Down | 3000 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFee` | 36 | L984 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 36 | L984 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 36 | L985 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 36 | L985 | CREDIT | 23 | 450280 | Buy Down Expense | 2500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 36 | L987 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 2500 | False | False | MNT | 2024-04-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 36 | L987 | CREDIT | 24 | 450281 | Income From Buy Down | 2500 | False | False | MNT | 2024-04-14 | - |
| `loanTransactionType.buyDownFee` | 36 | L988 | DEBIT | 23 | 450280 | Buy Down Expense | 3000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 36 | L988 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 3000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 36 | L989 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 36 | L989 | CREDIT | 23 | 450280 | Buy Down Expense | 500 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 36 | L990 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 3000 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 36 | L990 | DEBIT | 24 | 450281 | Income From Buy Down | 500 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 36 | L990 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 500 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 36 | L990 | CREDIT | 24 | 450281 | Income From Buy Down | 3000 | False | False | MNT | 2024-04-15 | - |
| `loanTransactionType.buyDownFee` | 37 | L994 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 37 | L994 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 37 | L995 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 37 | L995 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L996 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L996 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L998 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L998 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1000 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1000 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1002 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1002 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1004 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1004 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1006 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1006 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1008 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1008 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1010 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1010 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1012 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1012 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1014 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1014 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1016 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1016 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1018 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1018 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1020 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1020 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1022 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1022 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1024 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1024 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1026 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1026 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1028 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1028 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1030 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1030 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1032 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1032 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1034 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1034 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1036 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1036 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1038 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1038 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1040 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1040 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1042 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1042 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1044 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1044 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1046 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1046 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1048 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1048 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1050 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1050 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1052 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1052 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1054 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1054 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1056 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1056 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1058 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1058 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 37 | L1059 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 37 | L1059 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 37 | L1059 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 37 | L1059 | CREDIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 37 | L1061 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 37 | L1061 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1063 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 37 | L1063 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 38 | L1182 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 38 | L1182 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 38 | L1183 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 38 | L1183 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1184 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1184 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1186 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1186 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1188 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1188 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1190 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1190 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1192 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1192 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1194 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1194 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1196 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1196 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1198 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1198 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1200 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1200 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1202 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1202 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1204 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1204 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1206 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1206 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1208 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1208 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1210 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1210 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1212 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1212 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1214 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1214 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1216 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1216 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1218 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1218 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1220 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1220 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1222 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1222 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1224 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1224 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1226 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1226 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1228 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1228 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1230 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1230 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1232 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1232 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1234 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1234 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1236 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1236 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1238 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1238 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1240 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1240 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1242 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1242 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1244 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1244 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1246 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1246 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 38 | L1247 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 38 | L1247 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 38 | L1247 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 38 | L1247 | CREDIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 38 | L1249 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 38 | L1249 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1251 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 38 | L1251 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 39 | L1370 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 39 | L1370 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 39 | L1371 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 39 | L1371 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1372 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1372 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1374 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1374 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1376 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1376 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1378 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1378 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1380 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1380 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1382 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1382 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1384 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1384 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1386 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1386 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1388 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1388 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1390 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1390 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1392 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1392 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1394 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1394 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1396 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1396 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1398 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1398 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1400 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1400 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1402 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1402 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1404 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1404 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1406 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1406 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1408 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1408 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1410 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1410 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1412 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1412 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1414 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1414 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1416 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1416 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1418 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1418 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1420 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1420 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1422 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1422 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1424 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1424 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1426 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1426 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1428 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1428 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1430 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1430 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1432 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1432 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1434 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1434 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 39 | L1435 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 39 | L1435 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 39 | L1435 | CREDIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 39 | L1435 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 39 | L1437 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 39 | L1437 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1439 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 39 | L1439 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 40 | L1558 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 40 | L1558 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 40 | L1559 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 40 | L1559 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1560 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1560 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1562 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1562 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1564 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1564 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1566 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1566 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1568 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1568 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1570 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1570 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1572 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1572 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1574 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1574 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1576 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1576 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1578 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1578 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1580 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1580 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1582 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1582 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1584 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1584 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1586 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1586 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1588 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1588 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1590 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1590 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1592 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1592 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1594 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1594 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1596 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1596 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1598 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1598 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1600 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1600 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1602 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1602 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1604 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1604 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1606 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1606 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1608 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1608 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1610 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1610 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1612 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1612 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1614 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1614 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1616 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1616 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1618 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1618 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1620 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1620 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1622 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1622 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 40 | L1623 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 40 | L1623 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 40 | L1623 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 40 | L1623 | CREDIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 40 | L1625 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 40 | L1625 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1627 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 40 | L1627 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 41 | L1746 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 41 | L1746 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 41 | L1747 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 41 | L1747 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1748 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1748 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1750 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1750 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1752 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1752 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1754 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1754 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1756 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1756 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1758 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1758 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1760 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1760 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1762 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1762 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1764 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1764 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1766 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1766 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1768 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1768 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1770 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1770 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1772 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1772 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1774 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1774 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1776 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1776 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1778 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1778 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1780 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1780 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1782 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1782 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1784 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1784 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1786 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1786 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1788 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1788 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1790 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1790 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1792 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1792 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1794 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1794 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1796 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1796 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1798 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1798 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1800 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1800 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1802 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1802 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1804 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1804 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1806 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1806 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1808 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1808 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1810 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1810 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 41 | L1811 | DEBIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 41 | L1811 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 41 | L1811 | CREDIT | 5 | 145023 | Suspense/Clearing account | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 41 | L1811 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 41 | L1813 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 41 | L1813 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1815 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 41 | L1815 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 42 | L1934 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 42 | L1934 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 42 | L1935 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 42 | L1935 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1936 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1936 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1938 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1938 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1940 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1940 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1942 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1942 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1944 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1944 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1946 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1946 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1948 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1948 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1950 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1950 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1952 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1952 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1954 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1954 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1956 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1956 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1958 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1958 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1960 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1960 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1962 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1962 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1964 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1964 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1966 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1966 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1968 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1968 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1970 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1970 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1972 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1972 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1974 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1974 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1976 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1976 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1978 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1978 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1980 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1980 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1982 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1982 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1984 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1984 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1986 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1986 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1988 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1988 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1990 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1990 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1992 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1992 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1994 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1994 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1996 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1996 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1998 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L1998 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 42 | L1999 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 42 | L1999 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 42 | L1999 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 42 | L1999 | CREDIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 42 | L2001 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 42 | L2001 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L2003 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 42 | L2003 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 43 | L2122 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 43 | L2122 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 43 | L2123 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFee` | 43 | L2123 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2124 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2124 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2126 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2126 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2128 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2128 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2130 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2130 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-14 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2132 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2132 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-15 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2134 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2134 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-16 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2136 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2136 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-17 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2138 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2138 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-18 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2140 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2140 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-19 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2142 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2142 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-20 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2144 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2144 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-21 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2146 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2146 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-22 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2148 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2148 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-23 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2150 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2150 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-24 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2152 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2152 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-25 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2154 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2154 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-26 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2156 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2156 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-27 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2158 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2158 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-03-28 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2160 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2160 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-29 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2162 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2162 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-30 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2164 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2164 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2166 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2166 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2168 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2168 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-02 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2170 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2170 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2172 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2172 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-04 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2174 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2174 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-05 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2176 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2176 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-06 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2178 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2178 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-07 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2180 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2180 | CREDIT | 24 | 450281 | Income From Buy Down | 654 | False | False | MNT | 2026-04-08 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2182 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2182 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-09 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2184 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2184 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-10 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2186 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2186 | CREDIT | 24 | 450281 | Income From Buy Down | 652 | False | False | MNT | 2026-04-11 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 43 | L2187 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 43 | L2187 | DEBIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 43 | L2187 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 43 | L2187 | CREDIT | 23 | 450280 | Buy Down Expense | 30000 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 43 | L2189 | DEBIT | 24 | 450281 | Income From Buy Down | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortizationAdjustment` | 43 | L2189 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 10109 | False | False | MNT | 2026-04-12 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2191 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFeeAmortization` | 43 | L2191 | CREDIT | 24 | 450281 | Income From Buy Down | 11413 | False | False | MNT | 2026-04-13 | - |
| `loanTransactionType.buyDownFee` | 44 | L2310 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 44 | L2310 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 44 | L2314 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 44 | L2314 | CREDIT | 24 | 450281 | Income From Buy Down | 5000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 45 | L2318 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFee` | 45 | L2318 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2024-01-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 45 | L2320 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAdjustment` | 45 | L2320 | CREDIT | 23 | 450280 | Buy Down Expense | 1000 | False | False | MNT | 2024-03-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 45 | L2322 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFeeAmortization` | 45 | L2322 | CREDIT | 24 | 450281 | Income From Buy Down | 4000 | False | False | MNT | 2024-03-31 | - |
| `loanTransactionType.buyDownFee` | 46 | L2327 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFee` | 46 | L2327 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 46 | L2328 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 46 | L2328 | CREDIT | 24 | 450281 | Income From Buy Down | 56 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 46 | L2331 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4944 | False | False | MNT | 2026-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 46 | L2331 | CREDIT | 24 | 450281 | Income From Buy Down | 4944 | False | False | MNT | 2026-01-03 | - |
| `loanTransactionType.buyDownFee` | 47 | L2336 | DEBIT | 23 | 450280 | Buy Down Expense | 5000 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFee` | 47 | L2336 | CREDIT | 22 | 145024 | Deferred Capitalized Income | 5000 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 47 | L2337 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 56 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 47 | L2337 | CREDIT | 24 | 450281 | Income From Buy Down | 56 | False | False | MNT | 2026-01-01 | - |
| `loanTransactionType.buyDownFeeAmortization` | 47 | L2340 | DEBIT | 22 | 145024 | Deferred Capitalized Income | 4944 | False | False | MNT | 2026-01-03 | - |
| `loanTransactionType.buyDownFeeAmortization` | 47 | L2340 | CREDIT | 24 | 450281 | Income From Buy Down | 4944 | False | False | MNT | 2026-01-03 | - |

### Every buy-down-fee transaction and its read-back amount / portions

Portions are integer minor units; `-` means the read-back did not carry that field. The `amount` is the transaction `amount`; portions are the oracle's `principalPortion`, `interestPortion`, `feeChargesPortion`, `penaltyChargesPortion`, `overpaymentPortion` and `unrecognizedIncomePortion`.

| loan | tx | type | date | amount (minor) | principal | interest | fee | penalty | overpayment | unrecognized income | reversed | charged_off | fraud | currency | legs |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| 1 | L2 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 1 | L6 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L10 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L11 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L14 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L16 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L18 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L20 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L22 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L24 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L26 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L28 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L30 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L32 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L34 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L36 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L38 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L40 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L42 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L44 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L46 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L48 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L50 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L52 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L54 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L56 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L58 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L60 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L62 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L64 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L66 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L68 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L70 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L72 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L74 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L76 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L78 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L80 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L82 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L84 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L86 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L88 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L90 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L92 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L94 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L96 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L98 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L100 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L102 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L104 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L106 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L108 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L110 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L112 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L114 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L116 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L118 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L120 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L122 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L124 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L126 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L128 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L130 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L133 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L135 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L136 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L138 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-04 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L140 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L141 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L143 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L144 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L146 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L148 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L149 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L151 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L153 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L154 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L156 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L157 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L159 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L161 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L162 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L164 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L166 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L167 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-22 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L169 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L171 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L172 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L174 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L175 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L177 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L179 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L180 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 2 | L182 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 3 | L186 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 3 | L190 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L192 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L193 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L196 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L198 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L200 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L202 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L204 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L206 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L208 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L210 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L212 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L214 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L216 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L218 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L220 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L222 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L224 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L226 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L228 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L230 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L232 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L234 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L236 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L238 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L240 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L242 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L244 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L246 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L248 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L250 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L252 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L254 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L256 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L258 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L260 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L262 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L264 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L266 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L268 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L270 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L272 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L274 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L276 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L278 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L280 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L282 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L284 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L286 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L288 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L290 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L292 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L294 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L296 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L298 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L300 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L302 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L304 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L306 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L308 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L310 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L312 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 4 | L315 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 1703 | 0 | 1703 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 5 | L317 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 5 | L319 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 3352 | 0 | 3352 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 5 | L322 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 1648 | 0 | 1648 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 6 | L325 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L326 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L329 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L331 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L333 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L335 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L337 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L339 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L341 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L343 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L345 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L347 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L349 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L351 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L353 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L355 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L357 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L359 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L361 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L363 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L365 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L367 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L369 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L371 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L373 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L375 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L377 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L379 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L381 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L383 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L385 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L387 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L389 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L391 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L393 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L395 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L397 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L399 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L401 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L403 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L405 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L407 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L409 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L411 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L413 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L415 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L417 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L419 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L421 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L423 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L425 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L427 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L429 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L431 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L433 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L435 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L437 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L439 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L441 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L443 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L445 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 6 | L446 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 6 | L449 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 1648 | 0 | 1648 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 7 | L452 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L453 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 7 | L456 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 7 | L458 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 8 | L460 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 8 | L461 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 8 | L464 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | True | MNT | 4 |
| 8 | L466 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 9 | L468 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 9 | L469 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 1374 | 0 | 1374 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 9 | L472 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 3626 | 0 | 3626 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 10 | L475 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 10 | L476 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 1374 | 0 | 1374 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 10 | L479 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 3626 | 0 | 3626 | 0 | 0 | 0 | 0 | False | True | True | MNT | 2 |
| 11 | L482 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 11 | L483 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 1374 | 0 | 1374 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 11 | L486 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 3626 | 0 | 3626 | 0 | 0 | 0 | 0 | False | False | True | MNT | 4 |
| 11 | L488 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 3626 | 0 | 3626 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 12 | L490 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 12 | L492 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-31 | 1703 | 0 | 1703 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 12 | L493 | `loanTransactionType.buyDownFee` | 2024-02-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 12 | L494 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 4149 | 0 | 4149 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 12 | L497 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 4148 | 0 | 4148 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 13 | L500 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 13 | L502 | `loanTransactionType.buyDownFeeAdjustment` | 2024-03-01 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 13 | L504 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 4000 | 0 | 4000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L509 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L511 | `loanTransactionType.buyDownFeeAdjustment` | 2024-03-01 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L512 | `loanTransactionType.buyDownFeeAdjustment` | 2024-03-15 | 500 | 0 | 500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 14 | L514 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 3500 | 0 | 3500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 15 | L519 | `loanTransactionType.buyDownFee` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 15 | L521 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L523 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L524 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L527 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L529 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L531 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L533 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L535 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L537 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L539 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L541 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L543 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L545 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L547 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L549 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L551 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L553 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L555 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L557 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L559 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L561 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L563 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L565 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L567 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L569 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L571 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L573 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L575 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L577 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L579 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L581 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L583 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L585 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L588 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L590 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L592 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L594 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L596 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L598 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L600 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L602 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L604 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L606 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L608 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L610 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L612 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L614 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L616 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L618 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L620 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L622 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L624 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L626 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L628 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L630 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L632 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L634 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L636 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L638 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L640 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L642 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-28 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L644 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L645 | `loanTransactionType.buyDownFeeAdjustment` | 2024-03-01 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 16 | L647 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-01 | 22 | 0 | 22 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L649 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-02 | 88 | 0 | 88 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 16 | L651 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-03 | 1593 | 0 | 1593 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L653 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 17 | L654 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L657 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L659 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L661 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L663 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L665 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L667 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L669 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L671 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L673 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L675 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L677 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L679 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L681 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L683 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-15 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L685 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L687 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-17 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L689 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-18 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L691 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-19 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L693 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-20 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L695 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-21 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L697 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-22 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L699 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-23 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L701 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-24 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L703 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L705 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-26 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L707 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-27 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L709 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-28 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L711 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-29 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L713 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-30 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L715 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-31 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L717 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L719 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L721 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L723 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L725 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L727 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L729 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L731 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L733 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L735 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-10 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L737 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-11 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L739 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-12 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L741 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-13 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L743 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-14 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L745 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-15 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 17 | L747 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2024-02-16 | 2527 | 0 | 2527 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 18 | L751 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 19 | L755 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 19 | L756 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L757 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-10 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 19 | L759 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L761 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L763 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L765 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L767 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L769 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L771 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L773 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L775 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 19 | L777 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2024-01-11 | 549 | 0 | 549 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 20 | L781 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 20 | L785 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 21 | L789 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 22 | L793 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L794 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 22 | L797 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 22 | L799 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 23 | L801 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 23 | L802 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 1758 | 0 | 1758 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 23 | L805 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | True | MNT | 4 |
| 23 | L807 | `loanTransactionType.buyDownFeeAmortization` | 2024-02-01 | 3242 | 0 | 3242 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 24 | L809 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 24 | L810 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 1374 | 0 | 1374 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 24 | L813 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 3626 | 0 | 3626 | 0 | 0 | 0 | 0 | False | False | True | MNT | 4 |
| 24 | L815 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-25 | 3626 | 0 | 3626 | 0 | 0 | 0 | 0 | False | False | True | MNT | 2 |
| 25 | L817 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 25 | L819 | `loanTransactionType.buyDownFeeAdjustment` | 2024-03-01 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 25 | L821 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 4000 | 0 | 4000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 25 | L825 | `loanTransactionType.buyDownFeeAmortization` | 2024-04-01 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L827 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L828 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-01 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 26 | L830 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L832 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L833 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L834 | `loanTransactionType.buyDownFee` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L836 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 166 | 0 | 166 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 27 | L839 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 14779 | 0 | 14779 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L841 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 28 | L842 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L843 | `loanTransactionType.buyDownFee` | 2024-01-02 | 20000 | 0 | 20000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L845 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 277 | 0 | 277 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L847 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 112 | 0 | 112 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 28 | L849 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 223 | 0 | 223 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 28 | L852 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 19333 | 0 | 19333 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L854 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L855 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L856 | `loanTransactionType.buyDownFee` | 2024-01-02 | 10000 | 0 | 10000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L858 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 166 | 0 | 166 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L859 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-02 | 4000 | 0 | 4000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L861 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 77 | 0 | 77 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 29 | L863 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 121 | 0 | 121 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L864 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-04 | 6000 | 0 | 6000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L866 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2024-01-05 | 14 | 0 | 14 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L867 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-05 | 1000 | 0 | 1000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L869 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2024-01-06 | 54 | 0 | 54 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 29 | L872 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 3649 | 0 | 3649 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L874 | `loanTransactionType.buyDownFee` | 2024-01-01 | 100 | 0 | 100 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L875 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L877 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L879 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L881 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L883 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L885 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L887 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L889 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L891 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L893 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L895 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L897 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L899 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L901 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L902 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-15 | 70 | 0 | 70 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 30 | L904 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2024-01-15 | 17 | 0 | 17 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L917 | `loanTransactionType.buyDownFee` | 2024-01-01 | 100 | 0 | 100 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L918 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L920 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L922 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-03 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L924 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-04 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L926 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-05 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L928 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-06 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L930 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-07 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L932 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-08 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L934 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-09 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L936 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-10 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L938 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-11 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L940 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-12 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L942 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-13 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L944 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-14 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L945 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-15 | 30 | 0 | 30 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L947 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-15 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 31 | L948 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 31 | L951 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-16 | 20 | 0 | 20 | 0 | 0 | 0 | 0 | False | True | False | MNT | 2 |
| 32 | L954 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L955 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 32 | L958 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 4945 | 0 | 4945 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L960 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L961 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 33 | L964 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 4945 | 0 | 4945 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L966 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L967 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-01 | 55 | 0 | 55 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L968 | `loanTransactionType.buyDownFee` | 2024-01-02 | 2000 | 0 | 2000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 34 | L970 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 77 | 0 | 77 | 0 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 34 | L972 | `loanTransactionType.buyDownFeeAmortization` | 2024-01-02 | 6868 | 0 | 6868 | 0 | 0 | 0 | 0 | False | False | False | MNT | 3 |
| 35 | L974 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L975 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-01 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L977 | `loanTransactionType.buyDownFeeAmortization` | 2024-04-14 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L978 | `loanTransactionType.buyDownFee` | 2024-01-01 | 3000 | 0 | 3000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L979 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-01 | 500 | 0 | 500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 35 | L980 | `loanTransactionType.buyDownFeeAmortization` | 2024-04-15 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 36 | L984 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L985 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-01 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L987 | `loanTransactionType.buyDownFeeAmortization` | 2024-04-14 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L988 | `loanTransactionType.buyDownFee` | 2024-01-01 | 3000 | 0 | 3000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L989 | `loanTransactionType.buyDownFeeAdjustment` | 2024-01-01 | 500 | 0 | 500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 36 | L990 | `loanTransactionType.buyDownFeeAmortization` | 2024-04-15 | 2500 | 0 | 2500 | 0 | 0 | 0 | 0 | False | False | False | MNT | 4 |
| 37 | L994 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L995 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L996 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L998 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1000 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1002 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1004 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1006 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1008 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1010 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1012 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1014 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1016 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1018 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1020 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1022 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1024 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1026 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1028 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1030 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1032 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1034 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1036 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1038 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1040 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1042 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1044 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1046 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1048 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1050 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1052 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1054 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1056 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1058 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1059 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 37 | L1061 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 10109 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 37 | L1063 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 11413 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1182 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1183 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1184 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1186 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1188 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1190 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1192 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1194 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1196 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1198 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1200 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1202 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1204 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1206 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1208 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1210 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1212 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1214 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1216 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1218 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1220 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1222 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1224 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1226 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1228 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1230 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1232 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1234 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1236 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1238 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1240 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1242 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1244 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1246 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1247 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 38 | L1249 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 10109 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 38 | L1251 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 11413 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1370 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1371 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1372 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1374 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1376 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1378 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1380 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1382 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1384 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1386 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1388 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1390 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1392 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1394 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1396 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1398 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1400 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1402 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1404 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1406 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1408 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1410 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1412 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1414 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1416 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1418 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1420 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1422 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1424 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1426 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1428 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1430 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1432 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1434 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1435 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 39 | L1437 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 10109 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 39 | L1439 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 11413 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1558 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1559 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1560 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1562 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1564 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1566 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1568 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1570 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1572 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1574 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1576 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1578 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1580 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1582 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1584 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1586 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1588 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1590 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1592 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1594 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1596 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1598 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1600 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1602 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1604 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1606 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1608 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1610 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1612 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1614 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1616 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1618 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1620 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1622 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1623 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 40 | L1625 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 10109 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 40 | L1627 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 11413 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1746 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1747 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1748 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1750 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1752 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1754 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1756 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1758 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1760 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1762 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1764 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1766 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1768 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1770 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1772 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1774 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1776 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1778 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1780 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1782 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1784 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1786 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1788 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1790 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1792 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1794 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1796 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1798 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1800 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1802 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1804 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1806 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1808 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1810 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1811 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 41 | L1813 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 10109 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 41 | L1815 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 11413 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1934 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1935 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1936 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1938 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1940 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1942 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1944 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1946 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1948 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1950 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1952 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1954 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1956 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1958 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1960 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1962 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1964 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1966 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1968 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1970 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1972 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1974 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1976 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1978 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1980 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1982 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1984 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1986 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1988 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1990 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1992 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 654 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1994 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1996 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1998 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 652 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L1999 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 30000 | 0 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 42 | L2001 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 10109 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 42 | L2003 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 11413 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2122 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 0 | 30000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2123 | `loanTransactionType.buyDownFee` | 2026-03-11 | 30000 | 0 | 0 | 30000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2124 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-11 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2126 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-12 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2128 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-13 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2130 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-14 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2132 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-15 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2134 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-16 | 654 | 0 | 0 | 654 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2136 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-17 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2138 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-18 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2140 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-19 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2142 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-20 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2144 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-21 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2146 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-22 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2148 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-23 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2150 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-24 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2152 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-25 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2154 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-26 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2156 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-27 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2158 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-28 | 654 | 0 | 0 | 654 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2160 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-29 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2162 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-30 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2164 | `loanTransactionType.buyDownFeeAmortization` | 2026-03-31 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2166 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-01 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2168 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-02 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2170 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-03 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2172 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-04 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2174 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-05 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2176 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-06 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2178 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-07 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2180 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-08 | 654 | 0 | 0 | 654 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2182 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-09 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2184 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-10 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2186 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-11 | 652 | 0 | 0 | 652 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2187 | `loanTransactionType.buyDownFeeAdjustment` | 2026-04-12 | 30000 | 0 | 0 | 30000 | 0 | 0 | 0 | True | False | False | MNT | 4 |
| 43 | L2189 | `loanTransactionType.buyDownFeeAmortizationAdjustment` | 2026-04-12 | 10109 | 0 | 0 | 10109 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 43 | L2191 | `loanTransactionType.buyDownFeeAmortization` | 2026-04-13 | 11413 | 0 | 0 | 11413 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L2310 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 0 | 5000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 44 | L2314 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 5000 | 0 | 0 | 5000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L2318 | `loanTransactionType.buyDownFee` | 2024-01-01 | 5000 | 0 | 0 | 5000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L2320 | `loanTransactionType.buyDownFeeAdjustment` | 2024-03-01 | 1000 | 0 | 0 | 1000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 45 | L2322 | `loanTransactionType.buyDownFeeAmortization` | 2024-03-31 | 4000 | 0 | 0 | 4000 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L2327 | `loanTransactionType.buyDownFee` | 2026-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L2328 | `loanTransactionType.buyDownFeeAmortization` | 2026-01-01 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 46 | L2331 | `loanTransactionType.buyDownFeeAmortization` | 2026-01-03 | 4944 | 0 | 4944 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L2336 | `loanTransactionType.buyDownFee` | 2026-01-01 | 5000 | 0 | 5000 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L2337 | `loanTransactionType.buyDownFeeAmortization` | 2026-01-01 | 56 | 0 | 56 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |
| 47 | L2340 | `loanTransactionType.buyDownFeeAmortization` | 2026-01-03 | 4944 | 0 | 4944 | 0 | 0 | 0 | 0 | False | False | False | MNT | 2 |

### Per-loan currency, charge-off and fraud state

| loan | currency | fraud | non-reversed chargeOff transactions |
| ---: | --- | --- | --- |
| 1 | MNT | False | - |
| 2 | MNT | False | - |
| 3 | MNT | False | - |
| 4 | MNT | False | - |
| 5 | MNT | False | L321@2024-03-01 |
| 6 | MNT | False | L448@2024-03-01 |
| 7 | MNT | False | - |
| 8 | MNT | True | - |
| 9 | MNT | True | L471@2024-01-25 |
| 10 | MNT | True | L478@2024-01-25 |
| 11 | MNT | True | - |
| 12 | MNT | False | L496@2024-03-01 |
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
| 23 | MNT | True | - |
| 24 | MNT | True | - |
| 25 | MNT | False | - |
| 26 | MNT | False | - |
| 27 | MNT | False | - |
| 28 | MNT | False | - |
| 29 | MNT | False | - |
| 30 | MNT | False | - |
| 31 | MNT | False | L950@2024-01-16 |
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

Every loan in this capture is **MNT**.

## Findings — what the sweep observed and did not

* **Observed — `loanTransactionType.buyDownFee` at the GL level:** 132 leg(s) on 61 loan transaction(s) across loans 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.buyDownFeeAdjustment` at the GL level:** 68 leg(s) on 24 loan transaction(s) across loans 13, 14, 16, 19, 25, 26, 29, 30, 31, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.buyDownFeeAmortization` at the GL level:** 1344 leg(s) on 661 loan transaction(s) across loans 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47; 24 leg(s) on a charged-off loan (loans 5, 6, 9, 10, 12, 31). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Observed — `loanTransactionType.buyDownFeeAmortizationAdjustment` at the GL level:** 24 leg(s) on 12 loan transaction(s) across loans 17, 19, 29, 30, 37, 38, 39, 40, 41, 42, 43; 0 leg(s) on a charged-off loan (loans -). The per-leg listing above gives each leg and its account; the per-transaction table gives the amount and portions.
* **Unmatched / not type-confirmable:** 1638 legs (819 transactions) carry no entry in any `transactions` read-back; see `journalentry-type-join.md`.
* **Fraud:** no loan in this feature is fraud-flagged, so the `isMarkedFraud` / charge-off-fraud variants are not exercised (every `fraud` above is `false`).

