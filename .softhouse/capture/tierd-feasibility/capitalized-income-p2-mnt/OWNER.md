# OWNER — Tier D `LoanCapitalizedIncome-Part2.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD29-DO)

Whole-file replay of `LoanCapitalizedIncome-Part2.feature` (35 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 34 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the CAPITALIZED-INCOME posting family: `capitalizedIncome` (the initial income capitalization), `capitalizedIncomeAdjustment` (the capitalized income adjustment postings, `createJournalEntriesForCapitalizedIncomeAdjustment`), `capitalizedIncomeAmortization` (the periodic amortization) and `capitalizedIncomeAmortizationAdjustment` (the amortization adjustment postings, `createJournalEntriesForCapitalizedIncomeAmortizationAdjustment`), plus the `chargeOff` arm. The two ADJUSTMENT postings have never been graded before and are the reason for this sweep. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD29-DO ran the rig, the replay (34/35), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-capitalized-income-p2-mnt.sh` | the exact replay driver |
| `replay-capitalized-income-p2-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 34 PASSED scenarios |
| `manifest-capitalized-income-p2.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-capitalized-income-p2.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 34/34 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 7 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**35 scenarios, 34 executed, 34 PASSED, 0 FAILED; 983 steps (983 passed, 0 skipped, 0 failed).** The 1 skipped scenario has no loan. Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3742 | 5 | PASSED | 1 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME` |
| 2 | C3743 | 53 | PASSED | 2 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 3 | C3744 | 724 | SKIPPED | -1 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 4 | C3745 | 1187 | PASSED | 3 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 5 | C3746 | 1760 | PASSED | 4 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 6 | C3747 | 2158 | PASSED | 5 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 7 | C3748 | 2194 | PASSED | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 8 | C3749 | 2233 | PASSED | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 9 | C3750 | 2284 | PASSED | 8 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 10 | C3751 | 2337 | PASSED | 9 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 11 | C3752 | 2395 | PASSED | 10 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 12 | C3753 | 2458 | PASSED | 11 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 13 | C3754 | 2523 | PASSED | 12 | `LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 14 | C3755 | 2562 | PASSED | 13 | `LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 15 | C3735 | 2620 | PASSED | 14 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 16 | C3758 | 2649 | PASSED | 15 | `LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_OVER_APPLIED_PERCENTAGE_CAPITALIZED_INCOME` |
| 17 | C3759 | 2666 | PASSED | 16 | `LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_OVER_APPLIED_PERCENTAGE_CAPITALIZED_INCOME` |
| 18 | C3782 | 2683 | PASSED | 17 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 19 | C3899 | 2790 | PASSED | 18 | `LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 20 | C3913 | 2814 | PASSED | 19 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_MULTIDISBURSAL_CAPITALIZED_INCOME` |
| 21 | C3914 | 2845 | PASSED | 20 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_MULTIDISBURSAL_CAPITALIZED_INCOME` |
| 22 | C3915 | 2872 | PASSED | 21 | `LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_OVER_APPLIED_PERCENTAGE_CAPITALIZED_INCOME` |
| 23 | C4005 | 2897 | PASSED | 22 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_CAPITALIZED_INCOME` |
| 24 | C4008 | 2937 | PASSED | 23 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 25 | C4020 | 2991 | PASSED | 24 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 26 | C4021 | 3091 | PASSED | 25 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 27 | C4041 | 3263 | PASSED | 26 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 28 | C4042 | 3345 | PASSED | 27 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 29 | C4095 | 3487 | PASSED | 28 | `LP2_PROGRESSIVE_ADV_PMNT_ALLOCATION_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC_CLASSIFICATION_INCOME_MAP` |
| 30 | C4096 | 3511 | PASSED | 29 | `LP2_PROGRESSIVE_ADV_PMNT_ALLOCATION_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC_CLASSIFICATION_INCOME_MAP` |
| 31 | C4097 | 3535 | PASSED | 30 | `LP2_PROGRESSIVE_ADV_PMNT_ALLOCATION_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC_CLASSIFICATION_INCOME_MAP` |
| 32 | C4114 | 3571 | PASSED | 31 | `LP2_PROGRESSIVE_ADV_PMNT_ALLOCATION_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC_CLASSIFICATION_INCOME_MAP` |
| 33 | C4115 | 3663 | PASSED | 32 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 34 | C85353 | 3754 | PASSED | 33 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |
| 35 | C85354 | 3829 | PASSED | 34 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 34 loans, 1249 bodies kept under `loans/`, each body sha256-pinned in `manifest-capitalized-income-p2.json`; the FAILED scenarios' loans are not committed (`manifest-capitalized-income-p2-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **34/34 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 1769 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 7 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_MULTIDISBURSAL_CAPITALIZED_INCOME.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_RECALC_EMI_360_30_MULTIDISB_OVER_APPLIED_PERCENTAGE_CAPITALIZED_INCOME.json`
- `create-request-LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_CAPITALIZED_INCOME.json`
- `create-request-LP2_PROGRESSIVE_ADV_PMNT_ALLOCATION_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC_CLASSIFICATION_INCOME_MAP.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **1769 legs, 12 types, 0 unmatched.**

The exact type codes seen for the required arms are `loanTransactionType.capitalizedIncome`, `loanTransactionType.capitalizedIncomeAdjustment`, `loanTransactionType.capitalizedIncomeAmortization`, `loanTransactionType.capitalizedIncomeAmortizationAdjustment` and `loanTransactionType.chargeOff`.

`charged_off` per leg = **the loan's LATEST read-back has `chargedOff=true` and lists a NON-REVERSED `chargeOff` transaction with an EARLIER transaction DATE than the leg's transaction, or the SAME date and a LOWER transaction id.** (Date order, not id order: OH-TIERD26-DJ, a backdated repayment has a higher id but posts as not charged off.) `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count (OH-TIERD23-DC).

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.capitalizedIncomeAmortization` | 682 | 2 | 27 |
| `loanTransactionType.accrual` | 670 | 0 | - |
| `loanTransactionType.repayment` | 150 | 2 | 27 |
| `loanTransactionType.capitalizedIncome` | 102 | 0 | - |
| `loanTransactionType.disbursement` | 80 | 0 | - |
| `loanTransactionType.capitalizedIncomeAdjustment` | 45 | 0 | - |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | 14 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 10 | 0 | - |
| `loanTransactionType.payoutRefund` | 6 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 4 | 0 | - |
| `loanTransactionType.chargeOff` | 4 | 0 | - |
| `loanTransactionType.downPayment` | 2 | 0 | - |

### The five required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.capitalizedIncome` | True | 102 | 48 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 | 0 | - | 102 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 |
| `loanTransactionType.capitalizedIncomeAdjustment` | True | 45 | 20 | 2, 6, 8, 10, 11, 12, 14, 17, 20, 22, 25, 26, 27, 31, 32 | 0 | - | 45 | 2, 6, 8, 10, 11, 12, 14, 17, 20, 22, 25, 26, 27, 31, 32 |
| `loanTransactionType.capitalizedIncomeAmortization` | True | 682 | 336 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 | 2 | 27 | 680 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 |
| `loanTransactionType.capitalizedIncomeAmortizationAdjustment` | True | 14 | 7 | 1, 2, 14, 17, 25, 26 | 0 | - | 14 | 1, 2, 14, 17, 25, 26 |
| `loanTransactionType.chargeOff` | True | 4 | 1 | 27 | 0 | - | 4 | 27 |

**No required arm is empty:** all five target types have journal-entry legs in this replay.

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.capitalizedIncome`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:24 DEBIT:9` | 9, 24 | CREDIT 24, DEBIT 9 | 45 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 | 1 | L4 | P 20000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 4 |
| `CREDIT:9 CREDIT:24 DEBIT:9 DEBIT:24` | 9, 24 | CREDIT 9, CREDIT 24, DEBIT 9, DEBIT 24 | 3 | 1, 14, 24 | 1 | L2 | P 30000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 4 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:24 DEBIT:9`: loan 1, tx L4, P 20000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 4 — 45 transaction(s) across loan(s) 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34.
- shape `CREDIT:9 CREDIT:24 DEBIT:9 DEBIT:24`: loan 1, tx L2, P 30000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 4 — 3 transaction(s) across loan(s) 1, 14, 24.

#### `loanTransactionType.capitalizedIncomeAdjustment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 DEBIT:24` | 9, 24 | CREDIT 9, DEBIT 24 | 15 | 6, 8, 10, 11, 12, 20, 22, 25, 26, 27, 31, 32 | 6 | L523 | P 4000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 4 |
| `CREDIT:1 CREDIT:9 DEBIT:24` | 1, 9, 24 | CREDIT 1, CREDIT 9, DEBIT 24 | 3 | 11, 17, 25 | 11 | L573 | P 5998 / I 2 / F 0 / Pen 0 / OP 0 / UI 0 | 4 |
| `CREDIT:17 DEBIT:24` | 17, 24 | CREDIT 17, DEBIT 24 | 1 | 2 | 2 | L198 | P 0 / I 0 / F 0 / Pen 0 / OP 1500 / UI 0 | 4 |
| `CREDIT:9 CREDIT:24 DEBIT:9 DEBIT:24` | 9, 24 | CREDIT 9, CREDIT 24, DEBIT 9, DEBIT 24 | 1 | 14 | 14 | L600 | P 1000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 4 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:9 DEBIT:24`: loan 6, tx L523, P 4000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 4 — 15 transaction(s) across loan(s) 6, 8, 10, 11, 12, 20, 22, 25, 26, 27, 31, 32.
- shape `CREDIT:1 CREDIT:9 DEBIT:24`: loan 11, tx L573, P 5998 / I 2 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 4 — 3 transaction(s) across loan(s) 11, 17, 25.
- shape `CREDIT:17 DEBIT:24`: loan 2, tx L198, P 0 / I 0 / F 0 / Pen 0 / OP 1500 / UI 0, paymentType id 4 — 1 transaction(s) across loan(s) 2.
- shape `CREDIT:9 CREDIT:24 DEBIT:9 DEBIT:24`: loan 14, tx L600, P 1000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 4 — 1 transaction(s) across loan(s) 14.

#### `loanTransactionType.capitalizedIncomeAmortization`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:5 DEBIT:24` | 5, 24 | CREDIT 5, DEBIT 24 | 326 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 32, 33, 34 | 1 | L7 | P 0 / I 50000 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:11 DEBIT:24` | 11, 24 | CREDIT 11, DEBIT 24 | 3 | 29, 31 | 29 | L792 | P 0 / I 55 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:5 CREDIT:24 DEBIT:5 DEBIT:24` | 5, 24 | CREDIT 5, CREDIT 24, DEBIT 5, DEBIT 24 | 3 | 24, 25, 32 | 24 | L678 | P 0 / I 112 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:5 CREDIT:11 DEBIT:24` | 5, 11, 24 | CREDIT 5, CREDIT 11, DEBIT 24 | 2 | 30 | 30 | L801 | P 0 / I 77 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:14 DEBIT:24` | 14, 24 | CREDIT 14, DEBIT 24 | 1 | 27 | 27 | L782 | P 0 / I 20 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:5 CREDIT:24 DEBIT:11 DEBIT:24` | 5, 11, 24 | CREDIT 5, CREDIT 24, DEBIT 11, DEBIT 24 | 1 | 31 | 31 | L812 | P 0 / I 2500 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:5 DEBIT:24`: loan 1, tx L7, P 0 / I 50000 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 326 transaction(s) across loan(s) 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 32, 33, 34.
- shape `CREDIT:11 DEBIT:24`: loan 29, tx L792, P 0 / I 55 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 3 transaction(s) across loan(s) 29, 31.
- shape `CREDIT:5 CREDIT:24 DEBIT:5 DEBIT:24`: loan 24, tx L678, P 0 / I 112 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 3 transaction(s) across loan(s) 24, 25, 32.
- shape `CREDIT:5 CREDIT:11 DEBIT:24`: loan 30, tx L801, P 0 / I 77 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 30.
- shape `CREDIT:14 DEBIT:24`: loan 27, tx L782, P 0 / I 20 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 1 transaction(s) across loan(s) 27.
- shape `CREDIT:5 CREDIT:24 DEBIT:11 DEBIT:24`: loan 31, tx L812, P 0 / I 2500 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 1 transaction(s) across loan(s) 31.

#### `loanTransactionType.capitalizedIncomeAmortizationAdjustment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:24 DEBIT:5` | 5, 24 | CREDIT 24, DEBIT 5 | 7 | 1, 2, 14, 17, 25, 26 | 1 | L10 | P 0 / I 30000 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:24 DEBIT:5`: loan 1, tx L10, P 0 / I 30000 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 7 transaction(s) across loan(s) 1, 2, 14, 17, 25, 26.

#### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 CREDIT:9 DEBIT:14 DEBIT:20` | 1, 9, 14, 20 | CREDIT 1, CREDIT 9, DEBIT 14, DEBIT 20 | 1 | 27 | 27 | L781 | P 10070 / I 38 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 CREDIT:9 DEBIT:14 DEBIT:20`: loan 27, tx L781, P 10070 / I 38 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 1 transaction(s) across loan(s) 27.

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
| 27 | MNT | True | L781@2024-01-16 |
| 28 | MNT | False | - |
| 29 | MNT | False | - |
| 30 | MNT | False | - |
| 31 | MNT | False | - |
| 32 | MNT | False | - |
| 33 | MNT | False | - |
| 34 | MNT | False | - |

### Findings

- none (all required arms present; every swept leg joined to a type; the charged-off dimension is populated by loan 27).

Other observations from the join:

- `loanTransactionType.capitalizedIncome`: 102 legs on 48 transaction(s) / 33 loan(s); 0 legs on charged-off loan(s) (-); 102 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34).
- `loanTransactionType.capitalizedIncomeAdjustment`: 45 legs on 20 transaction(s) / 15 loan(s); 0 legs on charged-off loan(s) (-); 45 on not-charged-off loan(s) (2, 6, 8, 10, 11, 12, 14, 17, 20, 22, 25, 26, 27, 31, 32).
- `loanTransactionType.capitalizedIncomeAmortization`: 682 legs on 336 transaction(s) / 33 loan(s); 2 legs on charged-off loan(s) (27); 680 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34).
- `loanTransactionType.capitalizedIncomeAmortizationAdjustment`: 14 legs on 7 transaction(s) / 6 loan(s); 0 legs on charged-off loan(s) (-); 14 on not-charged-off loan(s) (1, 2, 14, 17, 25, 26).
- `loanTransactionType.chargeOff`: 4 legs on 1 transaction(s) / 1 loan(s); 0 legs on charged-off loan(s) (-); 4 on not-charged-off loan(s) (27).

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

