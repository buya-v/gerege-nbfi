# OWNER — Tier D `LoanMerchantIssuedRefund.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD22-DB)

Whole-file replay of `LoanMerchantIssuedRefund.feature` (19 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 19 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the MERCHANT-ISSUED-REFUND posting family and the legs that accompany it: `merchantIssuedRefund` (the normal / payout / fraud charged-off arms and the not-charged-off arm), `payoutRefund`, the `accrual` and `accrualAdjustment` recognition legs, the `repayment` legs and the `chargeOff` legs. The MIR posting is graded on the charged-off arms only (normal, payout and fraud; OH-MIRGRADE-CK, OH-MIRFRAUD-CN); the not-charged-off arm is seen on a small number of loans. This feature adds refunds with interest and fee portions, refunds that create overpayment, refunds against accrued interest and the interest-refund and reversal transactions. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD22-DB ran the rig, the replay (19/19), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-merchant-refund-mnt.sh` | the exact replay driver |
| `replay-merchant-refund-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 19 PASSED scenarios |
| `manifest-merchant-refund.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-merchant-refund.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 19/19 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 5 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**19 scenarios, 19 PASSED, 0 FAILED; 528 steps (528 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3731 | 4 | PASSED | 1 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 2 | C3774 | 36 | PASSED | 2 | `LP2_ADV_PYMNT_INTEREST_DAILY_INT_RECALCULATION_ZERO_INT_CHARGE_OFF_INT_RECOGNITION_FROM_DISB_DATE` |
| 3 | C3775 | 54 | PASSED | 3 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF` |
| 4 | C3842 | 72 | PASSED | 4 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 5 | C3843 | 112 | PASSED | 5 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 6 | C3844 | 153 | PASSED | 6 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 7 | C3854 | 194 | PASSED | 7 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 8 | C3855 | 245 | PASSED | 8 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 9 | C3856 | 285 | PASSED | 9 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 10 | C3873 | 339 | PASSED | 10 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 11 | C3874 | 403 | PASSED | 11 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 12 | C3875 | 495 | PASSED | 12 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 13 | C3880 | 537 | PASSED | 13 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 14 | C4127 | 555 | PASSED | 14 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 15 | C4355 | 642 | PASSED | 15 | `LP2_ADV_PMT_ALLOC_ACTUAL_ACTUAL_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 16 | C4570 | 700 | PASSED | 16 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 17 | C4541 | 814 | PASSED | 17 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 18 | C4571 | 928 | PASSED | 18 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 19 | C4542 | 1039 | PASSED | 19 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF_ACCRUAL_ACTIVITY` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 19 loans, 710 bodies kept under `loans/`, each body sha256-pinned in `manifest-merchant-refund.json`; the FAILED scenarios' loans are not committed (`manifest-merchant-refund-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **19/19 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 364 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 5 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL.json`
- `create-request-LP2_ADV_PMT_ALLOC_ACTUAL_ACTUAL_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INT_RECALCULATION_ZERO_INT_CHARGE_OFF_INT_RECOGNITION_FROM_DISB_DATE.json`
- `create-request-LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF_ACCRUAL_ACTIVITY.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **364 legs, 11 types, 16 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction with a LOWER transaction id than the leg's transaction.** (The rule is transaction id order, not date order.) `charged-off latest` = the loan `chargedOff` flag in its LATEST read-back, so a charge-off later undone does not count.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 105 | 3 | 2 |
| `loanTransactionType.merchantIssuedRefund` | 77 | 4 | 2, 3 |
| `loanTransactionType.interestRefund` | 62 | 2 | 3 |
| `loanTransactionType.disbursement` | 44 | 0 | - |
| `loanTransactionType.accrual` | 22 | 0 | - |
| `(unmapped)` | 16 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 14 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 10 | 2 | 2 |
| `loanTransactionType.chargeOff` | 8 | 0 | - |
| `loanTransactionType.payoutRefund` | 4 | 0 | - |
| `loanTransactionType.goodwillCredit` | 2 | 0 | - |

### The six required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.merchantIssuedRefund` | True | 77 | 24 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19 | 4 | 2, 3 | 73 | 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19 |
| `loanTransactionType.payoutRefund` | True | 4 | 2 | 8, 17 | 0 | - | 4 | 8, 17 |
| `loanTransactionType.accrual` | True | 22 | 11 | 1, 2, 3, 9, 14, 16, 17, 18, 19 | 0 | - | 22 | 1, 2, 3, 9, 14, 16, 17, 18, 19 |
| `loanTransactionType.accrualAdjustment` | True | 10 | 5 | 2, 3, 16, 17, 18 | 2 | 2 | 8 | 3, 16, 17, 18 |
| `loanTransactionType.repayment` | True | 105 | 30 | 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 | 3 | 2 | 102 | 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 |
| `loanTransactionType.chargeOff` | True | 8 | 2 | 2, 3 | 0 | - | 8 | 2, 3 |

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:7 DEBIT:10` | 7, 10 | CREDIT 7, DEBIT 10 | 9 | 4, 5, 6, 8, 10, 12, 13, 19 | 4 | L36 | P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |
| `CREDIT:7 CREDIT:10 DEBIT:7 DEBIT:10` | 7, 10 | CREDIT 7, CREDIT 10, DEBIT 7, DEBIT 10 | 3 | 7, 11, 15 | 7 | L46 | P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |
| `CREDIT:13 DEBIT:10` | 10, 13 | CREDIT 13, DEBIT 10 | 2 | 2, 3 | 2 | L24 | P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |
| `CREDIT:16 DEBIT:10` | 10, 16 | CREDIT 16, DEBIT 10 | 2 | 9, 16 | 9 | L55 | P 0 / I 0 / F 0 / Pen 0 / OP 1000 / UI 0 | 8 |
| `CREDIT:4 CREDIT:7 CREDIT:10 CREDIT:16 DEBIT:4 DEBIT:7 DEBIT:10 DEBIT:16` | 4, 7, 10, 16 | CREDIT 4, CREDIT 7, CREDIT 10, CREDIT 16, DEBIT 4, DEBIT 7, DEBIT 10, DEBIT 16 | 2 | 1 | 1 | L4 | P 11383 / I 21 / F 0 / Pen 0 / OP 7395 / UI 0 | 8 |
| `CREDIT:4 CREDIT:7 CREDIT:16 DEBIT:10` | 4, 7, 10, 16 | CREDIT 4, CREDIT 7, CREDIT 16, DEBIT 10 | 2 | 1, 14 | 1 | L14 | P 17640 / I 160 / F 0 / Pen 280 / OP 719 / UI 0 | 8 |
| `CREDIT:4 CREDIT:7 DEBIT:10` | 4, 7, 10 | CREDIT 4, CREDIT 7, DEBIT 10 | 2 | 15, 19 | 15 | L86 | P 6426 / I 215 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |
| `CREDIT:4 CREDIT:7 CREDIT:10 DEBIT:4 DEBIT:7 DEBIT:10` | 4, 7, 10 | CREDIT 4, CREDIT 7, CREDIT 10, DEBIT 4, DEBIT 7, DEBIT 10 | 1 | 15 | 15 | L79 | P 6420 / I 221 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |
| `CREDIT:7 CREDIT:16 DEBIT:10` | 7, 10, 16 | CREDIT 7, CREDIT 16, DEBIT 10 | 1 | 19 | 19 | L137 | P 382 / I 0 / F 0 / Pen 0 / OP 22515 / UI 0 | 8 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:7 DEBIT:10`: loan 4, tx L36, P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 9 transaction(s) across loan(s) 4, 5, 6, 8, 10, 12, 13, 19.
- shape `CREDIT:7 CREDIT:10 DEBIT:7 DEBIT:10`: loan 7, tx L46, P 5000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 3 transaction(s) across loan(s) 7, 11, 15.
- shape `CREDIT:13 DEBIT:10`: loan 2, tx L24, P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 2 transaction(s) across loan(s) 2, 3.
- shape `CREDIT:16 DEBIT:10`: loan 9, tx L55, P 0 / I 0 / F 0 / Pen 0 / OP 1000 / UI 0, paymentType id 8 — 2 transaction(s) across loan(s) 9, 16.
- shape `CREDIT:4 CREDIT:7 CREDIT:10 CREDIT:16 DEBIT:4 DEBIT:7 DEBIT:10 DEBIT:16`: loan 1, tx L4, P 11383 / I 21 / F 0 / Pen 0 / OP 7395 / UI 0, paymentType id 8 — 2 transaction(s) across loan(s) 1.
- shape `CREDIT:4 CREDIT:7 CREDIT:16 DEBIT:10`: loan 1, tx L14, P 17640 / I 160 / F 0 / Pen 280 / OP 719 / UI 0, paymentType id 8 — 2 transaction(s) across loan(s) 1, 14.
- shape `CREDIT:4 CREDIT:7 DEBIT:10`: loan 15, tx L86, P 6426 / I 215 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 2 transaction(s) across loan(s) 15, 19.
- shape `CREDIT:4 CREDIT:7 CREDIT:10 DEBIT:4 DEBIT:7 DEBIT:10`: loan 15, tx L79, P 6420 / I 221 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 1 transaction(s) across loan(s) 15.
- shape `CREDIT:7 CREDIT:16 DEBIT:10`: loan 19, tx L137, P 382 / I 0 / F 0 / Pen 0 / OP 22515 / UI 0, paymentType id 8 — 1 transaction(s) across loan(s) 19.

#### `loanTransactionType.payoutRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:16 DEBIT:10` | 10, 16 | CREDIT 16, DEBIT 10 | 1 | 17 | 17 | L105 | P 0 / I 0 / F 0 / Pen 0 / OP 813 / UI 0 | 8 |
| `CREDIT:7 DEBIT:10` | 7, 10 | CREDIT 7, DEBIT 10 | 1 | 8 | 8 | L50 | P 2000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:16 DEBIT:10`: loan 17, tx L105, P 0 / I 0 / F 0 / Pen 0 / OP 813 / UI 0, paymentType id 8 — 1 transaction(s) across loan(s) 17.
- shape `CREDIT:7 DEBIT:10`: loan 8, tx L50, P 2000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 1 transaction(s) across loan(s) 8.

#### `loanTransactionType.accrual`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 DEBIT:4` | 4, 9 | CREDIT 9, DEBIT 4 | 10 | 1, 2, 3, 9, 14, 16, 17, 18, 19 | 1 | L6 | P 0 / I 190 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:5 DEBIT:4` | 4, 5 | CREDIT 5, DEBIT 4 | 1 | 1 | 1 | L16 | P 0 / I 0 / F 0 / Pen 280 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:9 DEBIT:4`: loan 1, tx L6, P 0 / I 190 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 10 transaction(s) across loan(s) 1, 2, 3, 9, 14, 16, 17, 18, 19.
- shape `CREDIT:5 DEBIT:4`: loan 1, tx L16, P 0 / I 0 / F 0 / Pen 280 / OP 0 / UI 0, paymentType id - — 1 transaction(s) across loan(s) 1.

#### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:4 DEBIT:9` | 4, 9 | CREDIT 4, DEBIT 9 | 5 | 2, 3, 16, 17, 18 | 2 | L22 | P 0 / I 5 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:4 DEBIT:9`: loan 2, tx L22, P 0 / I 5 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 5 transaction(s) across loan(s) 2, 3, 16, 17, 18.

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:4 CREDIT:7 DEBIT:10` | 4, 7, 10 | CREDIT 4, CREDIT 7, DEBIT 10 | 19 | 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 19 | 1 | L2 | P 1159 / I 41 / F 0 / Pen 0 / OP 0 / UI 0 | 7 |
| `CREDIT:4 CREDIT:7 CREDIT:10 DEBIT:4 DEBIT:7 DEBIT:10` | 4, 7, 10 | CREDIT 4, CREDIT 7, CREDIT 10, DEBIT 4, DEBIT 7, DEBIT 10 | 5 | 1, 15, 16, 17, 18 | 1 | L3 | P 6257 / I 128 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |
| `CREDIT:4 CREDIT:7 CREDIT:16 DEBIT:10` | 4, 7, 10, 16 | CREDIT 4, CREDIT 7, CREDIT 16, DEBIT 10 | 3 | 16, 17, 18 | 16 | L95 | P 11689 / I 17 / F 0 / Pen 0 / OP 6 / UI 0 | 8 |
| `CREDIT:7 DEBIT:10` | 7, 10 | CREDIT 7, DEBIT 10 | 3 | 2, 3, 15 | 2 | L18 | P 1000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 8 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:4 CREDIT:7 DEBIT:10`: loan 1, tx L2, P 1159 / I 41 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 7 — 19 transaction(s) across loan(s) 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 19.
- shape `CREDIT:4 CREDIT:7 CREDIT:10 DEBIT:4 DEBIT:7 DEBIT:10`: loan 1, tx L3, P 6257 / I 128 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 5 transaction(s) across loan(s) 1, 15, 16, 17, 18.
- shape `CREDIT:4 CREDIT:7 CREDIT:16 DEBIT:10`: loan 16, tx L95, P 11689 / I 17 / F 0 / Pen 0 / OP 6 / UI 0, paymentType id 8 — 3 transaction(s) across loan(s) 16, 17, 18.
- shape `CREDIT:7 DEBIT:10`: loan 2, tx L18, P 1000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 8 — 3 transaction(s) across loan(s) 2, 3, 15.

#### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:4 CREDIT:7 DEBIT:13 DEBIT:17` | 4, 7, 13, 17 | CREDIT 4, CREDIT 7, DEBIT 13, DEBIT 17 | 2 | 2, 3 | 2 | L21 | P 44432 / I 15 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:4 CREDIT:7 DEBIT:13 DEBIT:17`: loan 2, tx L21, P 44432 / I 15 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 2, 3.

### Per-loan currency and charge-off state

| loan | currency | charged-off latest read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- |
| 1 | MNT | False | - |
| 2 | MNT | True | L21@2025-06-10 |
| 3 | MNT | True | L31@2025-06-10 |
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

### Findings

- `(unmapped)`: 16 swept legs on 2 transaction(s) (L20, L28) across loan(s) 2, 3 have NO transaction TYPE — those transaction ids appear in no captured loan read-back, so the join cannot name them. Their legs carry the charge-off account shape and its exact reversal mirror: CREDIT:13 CREDIT:17 CREDIT:4 CREDIT:7 DEBIT:13 DEBIT:17 DEBIT:4 DEBIT:7. That is an earlier charge-off the replay went on to reverse (the surviving charge-off is L21 on loan 2 and L31 on loan 3). No required arm is missing; this is the only join gap.

Other observations from the join:

- `loanTransactionType.merchantIssuedRefund`: 77 legs on 24 transaction(s) / 17 loan(s); 4 legs on charged-off loan(s) (2, 3); 73 on not-charged-off loan(s) (1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19).
- `loanTransactionType.payoutRefund`: 4 legs on 2 transaction(s) / 2 loan(s); 0 legs on charged-off loan(s) (-); 4 on not-charged-off loan(s) (8, 17).
- `loanTransactionType.accrual`: 22 legs on 11 transaction(s) / 9 loan(s); 0 legs on charged-off loan(s) (-); 22 on not-charged-off loan(s) (1, 2, 3, 9, 14, 16, 17, 18, 19).
- `loanTransactionType.accrualAdjustment`: 10 legs on 5 transaction(s) / 5 loan(s); 2 legs on charged-off loan(s) (2); 8 on not-charged-off loan(s) (3, 16, 17, 18).
- `loanTransactionType.repayment`: 105 legs on 30 transaction(s) / 17 loan(s); 3 legs on charged-off loan(s) (2); 102 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19).
- `loanTransactionType.chargeOff`: 8 legs on 2 transaction(s) / 2 loan(s); 0 legs on charged-off loan(s) (-); 8 on not-charged-off loan(s) (2, 3).

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

