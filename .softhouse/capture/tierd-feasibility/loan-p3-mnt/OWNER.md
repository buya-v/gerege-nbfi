# OWNER — Tier D `Loan-Part3.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD27-DL)

Whole-file replay of `Loan-Part3.feature` (50 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP; the loan currency is stated per loan below — the feature mixes MNT and EUR steps), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 49 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The arm this capture is after is the REFUND transaction on an **ACTIVE** loan (`createJournalEntriesForRefundForActiveLoan`), which had never been observed at the GL level. `Loan-Part3.feature` (50 scenarios; 35 lines mentioning REFUND; no charge-off, no USD product) exercises it alongside the repayment, merchant-issued-refund, payout-refund, credit-balance-refund and interest-refund families. Every swept leg is joined to its transaction TYPE through the loan read-backs and to the loan's CHARGED-OFF state at that transaction, and each of the six required arms gets its DISTINCT leg shapes (account ids + sides, one example, and the count of transactions per shape).

## Provenance

OH-TIERD27-DL ran the rig, the replay (47/50), the extraction, the sweep while the throwaway was still UP, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-loan-p3-mnt.sh` | the exact replay driver |
| `replay-loan-p3-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 46 PASSED scenarios |
| `manifest-loan-p3.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-loan-p3.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 49/49 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 10 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**50 scenarios, 47 PASSED, 3 FAILED; 1244 steps (1226 passed, 15 skipped, 3 failed).** Recorded, not diagnosed.

Loan ids are attributed by client id, not by row position: scenario k creates client k and each loan is attributed to the scenario whose `clientId` it was created for. Scenario 34 (`... UC7 ... results an ERROR`) attempts a loan, gets a 403 and creates none, so loan ids no longer equal row positions after it.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C2946 | 5 | PASSED | 1 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 2 | C2947 | 119 | PASSED | 2 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 3 | C2948 | 233 | PASSED | 3 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 4 | C2949 | 347 | PASSED | 4 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 5 | C2950 | 461 | PASSED | 5 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 6 | C2951 | 575 | PASSED | 6 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 7 | C2952 | 689 | PASSED | 7 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 8 | C2953 | 803 | PASSED | 8 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 9 | C2954 | 917 | PASSED | 9 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 10 | C2955 | 1031 | PASSED | 10 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 11 | C2956 | 1145 | PASSED | 11 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 12 | C2957 | 1259 | PASSED | 12 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 13 | C2958 | 1373 | PASSED | 13 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 14 | C2959 | 1487 | PASSED | 14 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL` |
| 15 | C2960 | 1601 | PASSED | 15 | `LP1` |
| 16 | C2976 | 1623 | PASSED | 16 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 17 | C2977 | 1669 | PASSED | 17 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 18 | C2978 | 1714 | PASSED | 18 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 19 | C2986 | 1763 | PASSED | 19 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 20 | C3042 | 1829 | FAILED | 20 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 21 | C3043 | 1866 | FAILED | 21 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 22 | C3046 | 1903 | PASSED | 22 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 23 | C3049 | 1938 | PASSED | 23 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 24 | C3068 | 1975 | PASSED | 24 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 25 | C3090 | 2011 | FAILED | 25 | `LP2_DOWNPAYMENT_AUTO` |
| 26 | C3103 | 2101 | PASSED | 26 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 27 | C3104 | 2113 | PASSED | 27 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 28 | C3119 | 2125 | PASSED | 28 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 29 | C3120 | 2148 | PASSED | 29 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 30 | C3121 | 2172 | PASSED | 30 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 31 | C3122 | 2196 | PASSED | 31 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 32 | C3123 | 2220 | PASSED | 32 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 33 | C3124 | 2244 | PASSED | 33 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 34 | C3125 | 2268 | PASSED | _(none)_ | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 35 | C3126 | 2276 | PASSED | 34 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 36 | C3127 | 2316 | PASSED | 35 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH` |
| 37 | C3192 | 2359 | PASSED | 36 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 38 | C3242 | 2373 | PASSED | 37 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 39 | C3282 | 2441 | PASSED | 38 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL` |
| 40 | C3283 | 2485 | PASSED | 39 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL` |
| 41 | C3324 | 2529 | PASSED | 40 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL` |
| 42 | C3325 | 2572 | PASSED | 41 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL` |
| 43 | C3300 | 2615 | PASSED | 42 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 44 | C3483 | 2677 | PASSED | 43 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_REST_FREQUENCY_DATE` |
| 45 | C3484 | 2738 | PASSED | 44 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 46 | C3485 | 2760 | PASSED | 45 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 47 | C3486 | 2782 | PASSED | 46 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 48 | C3487 | 2806 | PASSED | 47 | `LP1_INTEREST_DECLINING_BALANCE_SAR_RECALCULATION_SAME_AS_REPAYMENT_COMPOUNDING_NONE_MULTIDISB` |
| 49 | C3488 | 2821 | PASSED | 48 | `LP1_INTEREST_DECLINING_BALANCE_SAR_RECALCULATION_SAME_AS_REPAYMENT_COMPOUNDING_NONE_MULTIDISB` |
| 50 | C3489 | 2837 | PASSED | 49 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_IR_DAILY_TILL_PRECLOSE_LAST_INSTALLMENT_STRATEGY` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 46 loans, 1518 bodies kept under `loans/`, each body sha256-pinned in `manifest-loan-p3.json`; the FAILED scenarios' loans are not committed (`manifest-loan-p3-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **49/49 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 349 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 10 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP1.json`
- `create-request-LP1_INTEREST_DECLINING_BALANCE_SAR_RECALCULATION_SAME_AS_REPAYMENT_COMPOUNDING_NONE_MULTIDISB.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_REST_FREQUENCY_DATE.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_IR_DAILY_TILL_PRECLOSE_LAST_INSTALLMENT_STRATEGY.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_FULL.json`
- `create-request-LP2_DOWNPAYMENT_ADV_PMT_ALLOC_FIXED_LENGTH.json`
- `create-request-LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL.json`
- `create-request-LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_VERTICAL.json`
- `create-request-LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **349 legs, 11 types, 6 unmatched.**

`charged_off` per leg = **a leg is on a charged-off loan only if the loan's LATEST read-back (highest manifest source_line) has chargedOff=true and lists a NON-REVERSED chargeOff transaction with an EARLIER transaction DATE than the leg, or the SAME date and a LOWER id (DATE order, not id order -- OH-TIERD26-DJ)**

The exact target type codes seen in this capture: `loanTransactionType.refund` → `loanTransactionType.refund`, `loanTransactionType.repayment` → `loanTransactionType.repayment`, `loanTransactionType.merchantIssuedRefund` → `loanTransactionType.merchantIssuedRefund`, `loanTransactionType.payoutRefund` → `loanTransactionType.payoutRefund`, `loanTransactionType.creditBalanceRefund` → `loanTransactionType.creditBalanceRefund`, `loanTransactionType.interestRefund` → `loanTransactionType.interestRefund`.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 120 | 0 | - |
| `loanTransactionType.disbursement` | 119 | 0 | - |
| `loanTransactionType.goodwillCredit` | 26 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 22 | 0 | - |
| `loanTransactionType.payoutRefund` | 15 | 0 | - |
| `loanTransactionType.downPayment` | 14 | 0 | - |
| `loanTransactionType.interestRefund` | 12 | 0 | - |
| `(unmapped)` | 6 | 0 | - |
| `loanTransactionType.accrual` | 6 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 6 | 0 | - |
| `loanTransactionType.refund` | 3 | 0 | - |

### The six required arms

| target | exact code | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs not charged-off | loans not charged-off |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.refund` | `loanTransactionType.refund` | True | 3 | 1 | 19 | 0 | - | 3 | 19 |
| `loanTransactionType.repayment` | `loanTransactionType.repayment` | True | 120 | 48 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 24, 25, 37, 42, 43, 46, 49 | 0 | - | 120 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 24, 25, 37, 42, 43, 46, 49 |
| `loanTransactionType.merchantIssuedRefund` | `loanTransactionType.merchantIssuedRefund` | True | 22 | 8 | 11, 12, 13, 14, 37, 38, 40 | 0 | - | 22 | 11, 12, 13, 14, 37, 38, 40 |
| `loanTransactionType.payoutRefund` | `loanTransactionType.payoutRefund` | True | 15 | 5 | 21, 22, 23, 39, 41 | 0 | - | 15 | 21, 22, 23, 39, 41 |
| `loanTransactionType.creditBalanceRefund` | `loanTransactionType.creditBalanceRefund` | True | 6 | 2 | 37 | 0 | - | 6 | 37 |
| `loanTransactionType.interestRefund` | `loanTransactionType.interestRefund` | True | 12 | 4 | 38, 39, 40, 41 | 0 | - | 12 | 38, 39, 40, 41 |

**FINDING:** no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan.

**FINDING:** no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).

### Distinct leg shapes per required arm (account ids + sides, one example, count)

#### `loanTransactionType.refund` (exact code `loanTransactionType.refund`)

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 DEBIT:7 DEBIT:10` | 7, 9, 10 | CREDIT 9, DEBIT 7, DEBIT 10 | 1 | 19 | 19 | L71 | P 13000 / I 0 / F 2000 / Pen 0 / OP 0 / UI 0 | - |

One example per distinct shape (loan, tx id, portions in integer minor units, paymentType id) with the count of transactions of that shape:

- shape `CREDIT:9 DEBIT:7 DEBIT:10` — example loan 19, tx L71, P 13000 / I 0 / F 2000 / Pen 0 / OP 0 / UI 0, paymentType id -; 1 transaction(s) across loan(s) 19.

#### `loanTransactionType.repayment` (exact code `loanTransactionType.repayment`)

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:7 DEBIT:9` | 7, 9 | CREDIT 7, DEBIT 9 | 35 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 24, 25, 49 | 1 | L2 | P 25000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:2 CREDIT:7 DEBIT:9` | 2, 7, 9 | CREDIT 2, CREDIT 7, DEBIT 9 | 7 | 19, 42, 43, 46, 49 | 19 | L70 | P 25500 / I 0 / F 6000 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:7 CREDIT:9 CREDIT:18 DEBIT:7 DEBIT:9 DEBIT:18` | 7, 9, 18 | CREDIT 7, CREDIT 9, CREDIT 18, DEBIT 7, DEBIT 9, DEBIT 18 | 3 | 24, 25 | 24 | L91 | P 65000 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0 | 10 |
| `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` | 7, 9 | CREDIT 7, CREDIT 9, DEBIT 7, DEBIT 9 | 2 | 24, 37 | 24 | L90 | P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:7 CREDIT:18 DEBIT:9` | 7, 9, 18 | CREDIT 7, CREDIT 18, DEBIT 9 | 1 | 20 | 20 | L74 | P 37500 / I 0 / F 0 / Pen 0 / OP 12500 / UI 0 | 10 |

One example per distinct shape (loan, tx id, portions in integer minor units, paymentType id) with the count of transactions of that shape:

- shape `CREDIT:7 DEBIT:9` — example loan 1, tx L2, P 25000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 35 transaction(s) across loan(s) 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 24, 25, 49.
- shape `CREDIT:2 CREDIT:7 DEBIT:9` — example loan 19, tx L70, P 25500 / I 0 / F 6000 / Pen 0 / OP 0 / UI 0, paymentType id 10; 7 transaction(s) across loan(s) 19, 42, 43, 46, 49.
- shape `CREDIT:7 CREDIT:9 CREDIT:18 DEBIT:7 DEBIT:9 DEBIT:18` — example loan 24, tx L91, P 65000 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0, paymentType id 10; 3 transaction(s) across loan(s) 24, 25.
- shape `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` — example loan 24, tx L90, P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 2 transaction(s) across loan(s) 24, 37.
- shape `CREDIT:7 CREDIT:18 DEBIT:9` — example loan 20, tx L74, P 37500 / I 0 / F 0 / Pen 0 / OP 12500 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 20.

#### `loanTransactionType.merchantIssuedRefund` (exact code `loanTransactionType.merchantIssuedRefund`)

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:2 DEBIT:9` | 2, 9 | CREDIT 2, DEBIT 9 | 4 | 11, 12, 13, 14 | 11 | L44 | P 0 / I 0 / F 0 / Pen 3000 / OP 0 / UI 0 | 10 |
| `CREDIT:7 DEBIT:9` | 7, 9 | CREDIT 7, DEBIT 9 | 2 | 37, 40 | 37 | L115 | P 40000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:7 CREDIT:9 CREDIT:18 DEBIT:7 DEBIT:9 DEBIT:18` | 7, 9, 18 | CREDIT 7, CREDIT 9, CREDIT 18, DEBIT 7, DEBIT 9, DEBIT 18 | 1 | 37 | 37 | L112 | P 30000 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0 | 10 |
| `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` | 7, 9 | CREDIT 7, CREDIT 9, DEBIT 7, DEBIT 9 | 1 | 38 | 38 | L117 | P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |

One example per distinct shape (loan, tx id, portions in integer minor units, paymentType id) with the count of transactions of that shape:

- shape `CREDIT:2 DEBIT:9` — example loan 11, tx L44, P 0 / I 0 / F 0 / Pen 3000 / OP 0 / UI 0, paymentType id 10; 4 transaction(s) across loan(s) 11, 12, 13, 14.
- shape `CREDIT:7 DEBIT:9` — example loan 37, tx L115, P 40000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 2 transaction(s) across loan(s) 37, 40.
- shape `CREDIT:7 CREDIT:9 CREDIT:18 DEBIT:7 DEBIT:9 DEBIT:18` — example loan 37, tx L112, P 30000 / I 0 / F 0 / Pen 0 / OP 10000 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 37.
- shape `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` — example loan 38, tx L117, P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 38.

#### `loanTransactionType.payoutRefund` (exact code `loanTransactionType.payoutRefund`)

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:7 CREDIT:18 DEBIT:9` | 7, 9, 18 | CREDIT 7, CREDIT 18, DEBIT 9 | 3 | 21, 22, 23 | 21 | L78 | P 37500 / I 0 / F 0 / Pen 0 / OP 12500 / UI 0 | 10 |
| `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` | 7, 9 | CREDIT 7, CREDIT 9, DEBIT 7, DEBIT 9 | 1 | 39 | 39 | L120 | P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:7 DEBIT:9` | 7, 9 | CREDIT 7, DEBIT 9 | 1 | 41 | 41 | L126 | P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |

One example per distinct shape (loan, tx id, portions in integer minor units, paymentType id) with the count of transactions of that shape:

- shape `CREDIT:7 CREDIT:18 DEBIT:9` — example loan 21, tx L78, P 37500 / I 0 / F 0 / Pen 0 / OP 12500 / UI 0, paymentType id 10; 3 transaction(s) across loan(s) 21, 22, 23.
- shape `CREDIT:7 CREDIT:9 DEBIT:7 DEBIT:9` — example loan 39, tx L120, P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 39.
- shape `CREDIT:7 DEBIT:9` — example loan 41, tx L126, P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 41.

#### `loanTransactionType.creditBalanceRefund` (exact code `loanTransactionType.creditBalanceRefund`)

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 CREDIT:18 DEBIT:9 DEBIT:18` | 9, 18 | CREDIT 9, CREDIT 18, DEBIT 9, DEBIT 18 | 1 | 37 | 37 | L113 | P 0 / I 0 / F 0 / Pen 0 / OP 9121 / UI 0 | 10 |
| `CREDIT:9 DEBIT:7` | 7, 9 | CREDIT 9, DEBIT 7 | 1 | 37 | 37 | L114 | P 9121 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |

One example per distinct shape (loan, tx id, portions in integer minor units, paymentType id) with the count of transactions of that shape:

- shape `CREDIT:9 CREDIT:18 DEBIT:9 DEBIT:18` — example loan 37, tx L113, P 0 / I 0 / F 0 / Pen 0 / OP 9121 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 37.
- shape `CREDIT:9 DEBIT:7` — example loan 37, tx L114, P 9121 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10; 1 transaction(s) across loan(s) 37.

#### `loanTransactionType.interestRefund` (exact code `loanTransactionType.interestRefund`)

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:5 CREDIT:7 DEBIT:5 DEBIT:7` | 5, 7 | CREDIT 5, CREDIT 7, DEBIT 5, DEBIT 7 | 2 | 38, 39 | 38 | L118 | P 57 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:7 DEBIT:5` | 5, 7 | CREDIT 7, DEBIT 5 | 2 | 40, 41 | 40 | L123 | P 57 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | - |

One example per distinct shape (loan, tx id, portions in integer minor units, paymentType id) with the count of transactions of that shape:

- shape `CREDIT:5 CREDIT:7 DEBIT:5 DEBIT:7` — example loan 38, tx L118, P 57 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id -; 2 transaction(s) across loan(s) 38, 39.
- shape `CREDIT:7 DEBIT:5` — example loan 40, tx L123, P 57 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id -; 2 transaction(s) across loan(s) 40, 41.

### Per-loan currency and charge-off state

Currency is read per loan from the swept journal-entry bodies (`currency.code`) and falls back to the loan detail read-back. Distinct currencies in this capture: MNT. Charged-off latest = the loan `chargedOff` flag in its LATEST read-back.

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
| 20 | MNT | None | - |
| 21 | MNT | None | - |
| 22 | MNT | False | - |
| 23 | MNT | False | - |
| 24 | MNT | False | - |
| 25 | MNT | None | - |
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

### Findings

- no non-reversed `chargeOff` loan transaction appears in ANY read-back: no leg is on a charged-off loan.
- no loan's LATEST read-back has `chargedOff=true`: the charged-off dimension is empty (every leg charged-off=no).
- `(unmapped)`: 6 swept leg(s) on transaction(s) L137, L139, L142 across loan(s) 44, 45, 46 have NO transaction TYPE — those transaction ids appear in no captured loan read-back.

Other observations from the join:

- `loanTransactionType.refund` (code `loanTransactionType.refund`, type id(s) 18): 3 legs on 1 transaction(s) / 1 loan(s); 0 legs on charged-off loan(s) (-); 3 on not-charged-off loan(s) (19).
- `loanTransactionType.repayment` (code `loanTransactionType.repayment`, type id(s) 2): 120 legs on 48 transaction(s) / 26 loan(s); 0 legs on charged-off loan(s) (-); 120 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 24, 25, 37, 42, 43, 46, 49).
- `loanTransactionType.merchantIssuedRefund` (code `loanTransactionType.merchantIssuedRefund`, type id(s) 21): 22 legs on 8 transaction(s) / 7 loan(s); 0 legs on charged-off loan(s) (-); 22 on not-charged-off loan(s) (11, 12, 13, 14, 37, 38, 40).
- `loanTransactionType.payoutRefund` (code `loanTransactionType.payoutRefund`, type id(s) 22): 15 legs on 5 transaction(s) / 5 loan(s); 0 legs on charged-off loan(s) (-); 15 on not-charged-off loan(s) (21, 22, 23, 39, 41).
- `loanTransactionType.creditBalanceRefund` (code `loanTransactionType.creditBalanceRefund`, type id(s) 20): 6 legs on 2 transaction(s) / 1 loan(s); 0 legs on charged-off loan(s) (-); 6 on not-charged-off loan(s) (37).
- `loanTransactionType.interestRefund` (code `loanTransactionType.interestRefund`, type id(s) 33): 12 legs on 4 transaction(s) / 4 loan(s); 0 legs on charged-off loan(s) (-); 12 on not-charged-off loan(s) (38, 39, 40, 41).

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

