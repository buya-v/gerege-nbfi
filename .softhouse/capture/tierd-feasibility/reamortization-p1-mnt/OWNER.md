# OWNER — Tier D `LoanReAmortization-Part1.feature` MNT capture **plus a journal-entry sweep and the repayment-schedule inventory** (OH-TIERD30-DR)

Whole-file replay of `LoanReAmortization-Part1.feature` (50 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 50 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the RE-AMORTIZATION surface. The feature drives the loan command `reAmortize`, which rewrites the loan's repayment schedule; the graded surface is the SCHEDULE that results, so this capture keeps, per loan, every read-back that carries a `repaymentSchedule.periods` array and phases it (by the extractor's true `source_line` chronology) before and after each reAmortize call. This capture also joins every swept journal-entry leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD30-DR ran the rig, the replay (45/50), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-reamortization-p1-mnt.sh` | the exact replay driver |
| `replay-reamortization-p1-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 45 PASSED scenarios, including the `repaymentSchedule` / `associations=all` bodies |
| `manifest-reamortization-p1.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-reamortization-p1.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 50/50 HTTP 200 |
| `journalentries-sweep-manifest.json` | sha256 + exact URL + http status + json validity per sweep body |
| `journalentries-sweep.out` | per-loan sweep log |
| `sweep-journalentries.py` | the sweep driver (`curl -sk --max-time 30`, port 8444, tenant `tierd`) |
| `product-mappings/` | accepted create requests of the 11 products the loans use, from THIS replay's log, sha256 in `manifest.json` |
| `journalentry-type-join.json` | every swept leg joined to its transaction type and charged-off state, plus the per-loan schedule inventory |
| `journalentry-type-join.md` | the same, human-readable, per-type leg listing |
| `build-type-join.py` / `build-owner.py` | the join builder and this OWNER writer |
| `organize.py, build-results.py, extract-journalentries.py, extract-product-mappings.py` | the other copied extractors |
| `preflight.txt, up.txt, teardown-isolation.txt` | isolation proof (12/12 standing counters == baseline) |

## Replay result (step 1)

**50 scenarios, 45 PASSED, 5 FAILED; 1354 steps (1319 passed, 30 skipped, 5 failed).** Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3069 | 5 | FAILED | 1 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 2 | C3070 | 50 | FAILED | 2 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 3 | C3071 | 95 | FAILED | 3 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 4 | C3072 | 144 | PASSED | 4 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 5 | C3073 | 164 | FAILED | 5 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 6 | C3074 | 197 | PASSED | 6 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 7 | C3075 | 228 | PASSED | 7 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 8 | C3076 | 277 | PASSED | 8 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 9 | C3077 | 310 | PASSED | 9 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 10 | C3078 | 343 | PASSED | 10 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 11 | C3089 | 392 | PASSED | 11 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 12 | C3112 | 413 | PASSED | 12 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 13 | C3113 | 471 | PASSED | 13 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 14 | C3114 | 526 | PASSED | 14 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 15 | C3115 | 584 | PASSED | 15 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 16 | C3134 | 642 | PASSED | 16 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 17 | C4304 | 748 | PASSED | 17 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 18 | C4305 | 812 | PASSED | 18 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 19 | C4306 | 884 | PASSED | 19 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 20 | C4307 | 952 | PASSED | 20 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_PENALTY_FEE_PRINCIPAL` |
| 21 | C4308 | 1019 | PASSED | 21 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 22 | C4309 | 1084 | PASSED | 22 | `LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_AUTO_DOWNPAYMENT` |
| 23 | C4219 | 1155 | PASSED | 23 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 24 | C4220 | 1223 | PASSED | 24 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 25 | C4221 | 1291 | PASSED | 25 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 26 | C4222 | 1361 | PASSED | 26 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_PENALTY_FEE_PRINCIPAL` |
| 27 | C4223 | 1430 | PASSED | 27 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 28 | C4224 | 1497 | PASSED | 28 | `LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_AUTO_DOWNPAYMENT` |
| 29 | C4374 | 1569 | PASSED | 29 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 30 | C4375 | 1641 | PASSED | 30 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 31 | C4376 | 1712 | PASSED | 31 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_PRINCIPAL_FIRST` |
| 32 | C4377 | 1783 | PASSED | 32 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_PRINCIPAL_FIRST` |
| 33 | C4310 | 1855 | PASSED | 33 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 34 | None | 1912 | PASSED | 34 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 35 | C4311 | 1933 | FAILED | 35 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 36 | C4312 | 1983 | PASSED | 36 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 37 | C4313 | 2026 | PASSED | 37 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 38 | C4389 | 2077 | PASSED | 38 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_NO_CALC_ON_PAST_DUE_TILL_PRECLOSE` |
| 39 | C4390 | 2161 | PASSED | 39 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_NO_CALC_ON_PAST_DUE_TILL_PRECLOSE` |
| 40 | C4396 | 2247 | PASSED | 40 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_NO_CALC_ON_PAST_DUE_TILL_PRECLOSE` |
| 41 | C4397 | 2352 | PASSED | 41 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL` |
| 42 | C4398 | 2459 | PASSED | 42 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_NO_CALC_ON_PAST_DUE_TILL_PRECLOSE` |
| 43 | C4399 | 2569 | PASSED | 43 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_REFUND_INTEREST_RECALC_ACCRUAL_ACTIVITY` |
| 44 | C4400 | 2678 | PASSED | 44 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_MULTIDISBURSE_CHARGEBACK` |
| 45 | C4401 | 2787 | PASSED | 45 | `LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_AUTO_DOWNPAYMENT` |
| 46 | C4402 | 2911 | PASSED | 46 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 47 | C4403 | 2981 | PASSED | 47 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 48 | C4404 | 3050 | PASSED | 48 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 49 | C4405 | 3115 | PASSED | 49 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 50 | C4406 | 3185 | PASSED | 50 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 45 loans, 1692 bodies kept under `loans/`, each body sha256-pinned in `manifest-reamortization-p1.json`; the FAILED scenarios' loans are not committed (`manifest-reamortization-p1-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **50/50 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 539 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 11 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL.json`
- `create-request-LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_PRINCIPAL_FIRST.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_MULTIDISBURSE_CHARGEBACK.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_NO_CALC_ON_PAST_DUE_TILL_PRECLOSE.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_REFUND_INTEREST_RECALC_ACCRUAL_ACTIVITY.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_FEE_PRINCIPAL.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_EMI_360_30_CHARGEBACK_INTEREST_PENALTY_FEE_PRINCIPAL.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_AUTO_DOWNPAYMENT.json`
- `create-request-LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **539 legs, 8 types, 0 unmatched.**

`charged_off` per leg = **a NON-REVERSED `chargeOff` loan transaction, listed in the loan's LATEST read-back, with an EARLIER transaction DATE than the leg's transaction, or the SAME date and a LOWER id.** (The rule is DATE order, not id order: a backdated repayment posts as not charged off even with a higher id.) A charge-off that was later undone is gone from the latest read-back and so never counts.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.repayment` | 257 | 10 | 46, 47, 48, 49, 50 |
| `loanTransactionType.disbursement` | 108 | 0 | - |
| `loanTransactionType.accrual` | 82 | 0 | - |
| `loanTransactionType.downPayment` | 51 | 0 | - |
| `loanTransactionType.chargeOff` | 20 | 0 | - |
| `loanTransactionType.merchantIssuedRefund` | 9 | 0 | - |
| `loanTransactionType.chargeback` | 6 | 0 | - |
| `loanTransactionType.interestRefund` | 6 | 0 | - |

### The four required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.reAmortize` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 257 | 91 | 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 10 | 46, 47, 48, 49, 50 | 247 | 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.accrual` | True | 82 | 36 | 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 0 | - | 82 | 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| `loanTransactionType.chargeOff` | True | 20 | 5 | 46, 47, 48, 49, 50 | 0 | - | 20 | 46, 47, 48, 49, 50 |

### Findings from the join

- **FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.reAmortize.  The re-amortization command succeeds and rewrites the schedule, but the reAmortize transaction itself posts no journal entry.
- **FINDING:** 49 target transaction(s) in the read-backs have NO journal-entry legs: loan 4 tx L12, loan 6 tx L19, loan 7 tx L23, loan 7 tx L25, loan 8 tx L29, loan 9 tx L34, loan 10 tx L40, loan 11 tx L44, loan 12 tx L49, loan 12 tx L50, loan 13 tx L54, loan 13 tx L55, loan 14 tx L60, loan 14 tx L63, loan 15 tx L69, loan 15 tx L70, loan 16 tx L76, loan 17 tx L82, loan 18 tx L89, loan 19 tx L97, loan 20 tx L105, loan 21 tx L110, loan 22 tx L118, loan 23 tx L123, loan 24 tx L130, loan 25 tx L137, loan 26 tx L145, loan 27 tx L150, loan 28 tx L158, loan 29 tx L163, loan 30 tx L172, loan 31 tx L181, loan 31 tx L183, loan 32 tx L190, loan 32 tx L191, loan 33 tx L199, loan 33 tx L201, loan 34 tx L209, loan 34 tx L210, loan 36 tx L218, loan 37 tx L224, loan 38 tx L231, loan 39 tx L236, loan 40 tx L241, loan 41 tx L248, loan 42 tx L254, loan 43 tx L259, loan 44 tx L271, loan 45 tx L278.

### Re-amortization transactions the read-backs expose

The exact type code seen is `loanTransactionType.reAmortize`. It appears as a loan transaction in the read-backs but has **no journal-entry legs** in the sweep, so it is not in the type table above; the table below lists every such transaction by loan.

| loan | reAmortize transactions (id@date) | reversed | currency |
| ---: | --- | --- | --- |
| 4 | L12@2024-01-25 | False | MNT |
| 6 | L19@2024-02-01 | False | MNT |
| 7 | L23@2024-02-01 | False | MNT |
| 7 | L25@2024-02-01 | False | MNT |
| 8 | L29@2024-02-01 | False | MNT |
| 9 | L34@2024-01-31 | False | MNT |
| 10 | L40@2024-01-30 | False | MNT |
| 11 | L44@2024-02-01 | False | MNT |
| 12 | L49@2024-02-20 | False | MNT |
| 12 | L50@2024-02-20 | False | MNT |
| 13 | L54@2024-02-20 | False | MNT |
| 13 | L55@2024-02-20 | False | MNT |
| 14 | L60@2024-02-20 | False | MNT |
| 14 | L63@2024-02-20 | False | MNT |
| 15 | L69@2024-02-20 | False | MNT |
| 15 | L70@2024-02-20 | False | MNT |
| 16 | L76@2024-02-20 | True | MNT |
| 17 | L82@2024-03-15 | False | MNT |
| 18 | L89@2024-03-15 | False | MNT |
| 19 | L97@2024-03-15 | False | MNT |
| 20 | L105@2024-03-15 | False | MNT |
| 21 | L110@2024-03-15 | False | MNT |
| 22 | L118@2024-03-15 | False | MNT |
| 23 | L123@2024-03-15 | False | MNT |
| 24 | L130@2024-03-15 | False | MNT |
| 25 | L137@2024-03-15 | False | MNT |
| 26 | L145@2024-03-15 | False | MNT |
| 27 | L150@2024-03-15 | False | MNT |
| 28 | L158@2024-03-15 | False | MNT |
| 29 | L163@2024-03-15 | False | MNT |
| 30 | L172@2024-03-15 | False | MNT |
| 31 | L181@2024-03-15 | False | MNT |
| 31 | L183@2024-03-15 | False | MNT |
| 32 | L190@2024-03-15 | False | MNT |
| 32 | L191@2024-03-15 | False | MNT |
| 33 | L199@2024-03-15 | False | MNT |
| 33 | L201@2024-05-15 | False | MNT |
| 34 | L209@2024-03-15 | False | MNT |
| 34 | L210@2024-05-01 | False | MNT |
| 36 | L218@2024-04-15 | False | MNT |
| 37 | L224@2024-03-15 | False | MNT |
| 38 | L231@2024-03-15 | True | MNT |
| 39 | L236@2024-03-15 | True | MNT |
| 40 | L241@2024-03-15 | True | MNT |
| 41 | L248@2024-03-15 | True | MNT |
| 42 | L254@2024-03-15 | True | MNT |
| 43 | L259@2024-03-15 | True | MNT |
| 44 | L271@2024-03-15 | True | MNT |
| 45 | L278@2024-03-15 | True | MNT |

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.reAmortize`

_No legs for this type — see the finding above._

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:8 CREDIT:10 DEBIT:2` | 2, 8, 10 | CREDIT 8, CREDIT 10, DEBIT 2 | 67 | 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 | 8 | L30 | P 37500 / I 0 / F 0 / Pen 1000 / OP 0 / UI 0 | 6 |
| `CREDIT:8 DEBIT:2` | 2, 8 | CREDIT 8, DEBIT 2 | 16 | 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 31, 32, 43 | 4 | L13 | P 37500 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 6 |
| `CREDIT:14 DEBIT:2` | 2, 14 | CREDIT 14, DEBIT 2 | 5 | 46, 47, 48, 49, 50 | 46 | L288 | P 8357 / I 49 / F 0 / Pen 0 / OP 0 / UI 0 | 6 |
| `CREDIT:2 CREDIT:8 DEBIT:2 DEBIT:8` | 2, 8 | CREDIT 2, CREDIT 8, DEBIT 2, DEBIT 8 | 2 | 12, 15 | 12 | L48 | P 12000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 6 |
| `CREDIT:2 CREDIT:8 CREDIT:10 DEBIT:2 DEBIT:8 DEBIT:10` | 2, 8, 10 | CREDIT 2, CREDIT 8, CREDIT 10, DEBIT 2, DEBIT 8, DEBIT 10 | 1 | 40 | 40 | L242 | P 2034 / I 98 / F 0 / Pen 0 / OP 0 / UI 0 | 6 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:8 CREDIT:10 DEBIT:2`: loan 8, tx L30, P 37500 / I 0 / F 0 / Pen 1000 / OP 0 / UI 0, paymentType id 6 — 67 transaction(s) across loan(s) 8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50.
- shape `CREDIT:8 DEBIT:2`: loan 4, tx L13, P 37500 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 6 — 16 transaction(s) across loan(s) 4, 6, 7, 10, 11, 12, 13, 14, 15, 16, 31, 32, 43.
- shape `CREDIT:14 DEBIT:2`: loan 46, tx L288, P 8357 / I 49 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 6 — 5 transaction(s) across loan(s) 46, 47, 48, 49, 50.
- shape `CREDIT:2 CREDIT:8 DEBIT:2 DEBIT:8`: loan 12, tx L48, P 12000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 6 — 2 transaction(s) across loan(s) 12, 15.
- shape `CREDIT:2 CREDIT:8 CREDIT:10 DEBIT:2 DEBIT:8 DEBIT:10`: loan 40, tx L242, P 2034 / I 98 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 6 — 1 transaction(s) across loan(s) 40.

#### `loanTransactionType.accrual`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:9 DEBIT:10` | 9, 10 | CREDIT 9, DEBIT 10 | 28 | 17, 20, 21, 22, 23, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 50 | 17 | L84 | P 0 / I 129 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:5 CREDIT:9 DEBIT:10 DEBIT:10` | 5, 9, 10 | CREDIT 5, CREDIT 9, DEBIT 10 | 5 | 18, 19, 24, 25, 42 | 18 | L91 | P 0 / I 129 / F 1000 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:5 DEBIT:10` | 5, 10 | CREDIT 5, DEBIT 10 | 3 | 8, 9, 15 | 8 | L31 | P 0 / I 0 / F 0 / Pen 1000 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:9 DEBIT:10`: loan 17, tx L84, P 0 / I 129 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 28 transaction(s) across loan(s) 17, 20, 21, 22, 23, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 50.
- shape `CREDIT:5 CREDIT:9 DEBIT:10 DEBIT:10`: loan 18, tx L91, P 0 / I 129 / F 1000 / Pen 0 / OP 0 / UI 0, paymentType id - — 5 transaction(s) across loan(s) 18, 19, 24, 25, 42.
- shape `CREDIT:5 DEBIT:10`: loan 8, tx L31, P 0 / I 0 / F 0 / Pen 1000 / OP 0 / UI 0, paymentType id - — 3 transaction(s) across loan(s) 8, 9, 15.

#### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:8 CREDIT:10 DEBIT:11 DEBIT:19` | 8, 10, 11, 19 | CREDIT 8, CREDIT 10, DEBIT 11, DEBIT 19 | 5 | 46, 47, 48, 49, 50 | 46 | L287 | P 8357 / I 49 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:8 CREDIT:10 DEBIT:11 DEBIT:19`: loan 46, tx L287, P 8357 / I 49 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 5 transaction(s) across loan(s) 46, 47, 48, 49, 50.

### Per-loan currency and charge-off state

| loan | currency | charged-off latest read-back | latest transactions read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- | --- |
| 1 | MNT | False | `stage/loan-1-detail-associations-transactions-2.json` | - |
| 2 | MNT | False | `stage/loan-2-detail-associations-transactions-2.json` | - |
| 3 | MNT | False | `stage/loan-3-detail-associations-all-3.json` | - |
| 4 | MNT | False | `loans/loan-4/loan-4-detail-associations-all-4.json` | - |
| 5 | MNT | False | `stage/loan-5-detail-associations-all-3.json` | - |
| 6 | MNT | False | `loans/loan-6/loan-6-detail-associations-all-4.json` | - |
| 7 | MNT | False | `loans/loan-7/loan-7-detail-associations-all-5.json` | - |
| 8 | MNT | False | `loans/loan-8/loan-8-detail-associations-all-4.json` | - |
| 9 | MNT | False | `loans/loan-9/loan-9-detail-associations-all-4.json` | - |
| 10 | MNT | False | `loans/loan-10/loan-10-detail-associations-all-5.json` | - |
| 11 | MNT | False | `loans/loan-11/loan-11-detail-associations-all-4.json` | - |
| 12 | MNT | False | `loans/loan-12/loan-12-detail-associations-all-6.json` | - |
| 13 | MNT | False | `loans/loan-13/loan-13-detail-associations-all-5.json` | - |
| 14 | MNT | False | `loans/loan-14/loan-14-detail-associations-all-6.json` | - |
| 15 | MNT | False | `loans/loan-15/loan-15-detail-associations-all-5.json` | - |
| 16 | MNT | False | `loans/loan-16/loan-16-detail-associations-all-7.json` | - |
| 17 | MNT | False | `loans/loan-17/loan-17-detail-associations-all-5.json` | - |
| 18 | MNT | False | `loans/loan-18/loan-18-detail-associations-all-5.json` | - |
| 19 | MNT | False | `loans/loan-19/loan-19-detail-associations-all-5.json` | - |
| 20 | MNT | False | `loans/loan-20/loan-20-detail-associations-all-6.json` | - |
| 21 | MNT | False | `loans/loan-21/loan-21-detail-associations-all-5.json` | - |
| 22 | MNT | False | `loans/loan-22/loan-22-detail-associations-all-5.json` | - |
| 23 | MNT | False | `loans/loan-23/loan-23-detail-associations-all-5.json` | - |
| 24 | MNT | False | `loans/loan-24/loan-24-detail-associations-all-5.json` | - |
| 25 | MNT | False | `loans/loan-25/loan-25-detail-associations-all-5.json` | - |
| 26 | MNT | False | `loans/loan-26/loan-26-detail-associations-all-6.json` | - |
| 27 | MNT | False | `loans/loan-27/loan-27-detail-associations-all-5.json` | - |
| 28 | MNT | False | `loans/loan-28/loan-28-detail-associations-all-5.json` | - |
| 29 | MNT | False | `loans/loan-29/loan-29-detail-associations-all-6.json` | - |
| 30 | MNT | False | `loans/loan-30/loan-30-detail-associations-all-6.json` | - |
| 31 | MNT | False | `loans/loan-31/loan-31-detail-associations-all-6.json` | - |
| 32 | MNT | False | `loans/loan-32/loan-32-detail-associations-all-6.json` | - |
| 33 | MNT | False | `loans/loan-33/loan-33-detail-associations-all-6.json` | - |
| 34 | MNT | False | `loans/loan-34/loan-34-detail-associations-all-5.json` | - |
| 35 | MNT | False | `stage/loan-35-detail-associations-all-4.json` | - |
| 36 | MNT | False | `loans/loan-36/loan-36-detail-associations-all-4.json` | - |
| 37 | MNT | False | `loans/loan-37/loan-37-detail-associations-all-5.json` | - |
| 38 | MNT | False | `loans/loan-38/loan-38-detail-associations-all-5.json` | - |
| 39 | MNT | False | `loans/loan-39/loan-39-detail-associations-all-5.json` | - |
| 40 | MNT | False | `loans/loan-40/loan-40-detail-associations-all-6.json` | - |
| 41 | MNT | False | `loans/loan-41/loan-41-detail-associations-all-6.json` | - |
| 42 | MNT | False | `loans/loan-42/loan-42-detail-associations-all-5.json` | - |
| 43 | MNT | False | `loans/loan-43/loan-43-detail-associations-all-6.json` | - |
| 44 | MNT | False | `loans/loan-44/loan-44-detail-associations-all-7.json` | - |
| 45 | MNT | False | `loans/loan-45/loan-45-detail-associations-all-7.json` | - |
| 46 | MNT | True | `loans/loan-46/loan-46-detail-associations-all-5.json` | L287@2024-03-01 |
| 47 | MNT | True | `loans/loan-47/loan-47-detail-associations-all-5.json` | L292@2024-03-01 |
| 48 | MNT | True | `loans/loan-48/loan-48-detail-associations-all-5.json` | L300@2024-03-01 |
| 49 | MNT | True | `loans/loan-49/loan-49-detail-associations-all-5.json` | L305@2024-03-01 |
| 50 | MNT | True | `loans/loan-50/loan-50-detail-associations-all-5.json` | L310@2024-03-01 |

### Repayment schedules before/after each re-amortization (step 6)

Every read-back that carries a `repaymentSchedule.periods` array, per loan, in capture order. `phase` is computed from the extractor `source_line` (the true chronology): read-backs with a line below the first reAmortize call are `before-reAmortize`; between call k and k+1 they are `after-reAmortize-k`; after the last call, `after-reAmortize-<n>`. The `periods sha256` pins the exact schedule so a before/after pair can be compared byte-for-byte. **559 schedule bodies across 50 loans (MNT).**

#### loan 1 — MNT

reAmortize calls (source line): 22886; reAmortize transactions: -

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `stage/loan-1-detail-associations-all-1.json` | 22531 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `stage/loan-1-detail-associations-all-2.json` | 22687 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `stage/loan-1-detail-associations-all-3.json` | 22735 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `stage/loan-1-detail-associations-repaymentSchedule-1.json` | 22814 | associations-repaymentSchedule | 5 | `90a2d04297fa0ff5` | before-reAmortize |
| `stage/loan-1-detail-associations-repaymentSchedule-2.json` | 22838 | associations-repaymentSchedule | 5 | `90a2d04297fa0ff5` | before-reAmortize |
| `stage/loan-1-detail-associations-repaymentSchedule-3.json` | 22915 | associations-repaymentSchedule | 5 | `1e98a7f1e732e142` | after-reAmortize-1 |

#### loan 2 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `stage/loan-2-detail-associations-all-1.json` | 23879 | associations-all | 5 | `bff8c96130158ddc` | no-reAmortize |
| `stage/loan-2-detail-associations-all-2.json` | 24009 | associations-all | 5 | `247e25fadfc67075` | no-reAmortize |
| `stage/loan-2-detail-associations-all-3.json` | 24057 | associations-all | 5 | `247e25fadfc67075` | no-reAmortize |
| `stage/loan-2-detail-associations-repaymentSchedule-1.json` | 24136 | associations-repaymentSchedule | 5 | `90a2d04297fa0ff5` | no-reAmortize |
| `stage/loan-2-detail-associations-repaymentSchedule-2.json` | 24160 | associations-repaymentSchedule | 5 | `90a2d04297fa0ff5` | no-reAmortize |
| `stage/loan-2-detail-associations-repaymentSchedule-3.json` | 24237 | associations-repaymentSchedule | 5 | `1e98a7f1e732e142` | no-reAmortize |

#### loan 3 — MNT

reAmortize calls (source line): 25458; reAmortize transactions: -

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `stage/loan-3-detail-associations-all-1.json` | 25201 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `stage/loan-3-detail-associations-all-2.json` | 25331 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `stage/loan-3-detail-associations-all-3.json` | 25379 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `stage/loan-3-detail-associations-repaymentSchedule.json` | 25487 | associations-repaymentSchedule | 5 | `1e98a7f1e732e142` | after-reAmortize-1 |

#### loan 4 — MNT

reAmortize calls (source line): 26816; reAmortize transactions: L12@2024-01-25

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-4/loan-4-detail-associations-all-1.json` | 26451 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `loans/loan-4/loan-4-detail-associations-all-2.json` | 26581 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-4/loan-4-detail-associations-all-3.json` | 26629 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-4/loan-4-detail-associations-all-4.json` | 26945 | associations-all | 5 | `b7addeb2bffea8b0` | after-reAmortize-1 |
| `loans/loan-4/loan-4-detail-associations-repaymentSchedule.json` | 26969 | associations-repaymentSchedule | 5 | `b7addeb2bffea8b0` | after-reAmortize-1 |

#### loan 5 — MNT

reAmortize calls (source line): 28373; reAmortize transactions: -

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `stage/loan-5-detail-associations-all-1.json` | 27982 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `stage/loan-5-detail-associations-all-2.json` | 28112 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `stage/loan-5-detail-associations-all-3.json` | 28160 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `stage/loan-5-detail-associations-repaymentSchedule.json` | 28402 | associations-repaymentSchedule | 5 | `527d25c2334d5a31` | after-reAmortize-1 |

#### loan 6 — MNT

reAmortize calls (source line): 29623; reAmortize transactions: L19@2024-02-01

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-6/loan-6-detail-associations-all-1.json` | 29366 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `loans/loan-6/loan-6-detail-associations-all-2.json` | 29496 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-6/loan-6-detail-associations-all-3.json` | 29544 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-6/loan-6-detail-associations-repaymentSchedule-1.json` | 29652 | associations-repaymentSchedule | 5 | `325a04c632adf047` | after-reAmortize-1 |
| `loans/loan-6/loan-6-detail-associations-repaymentSchedule-2.json` | 29676 | associations-repaymentSchedule | 5 | `325a04c632adf047` | after-reAmortize-1 |
| `loans/loan-6/loan-6-detail-associations-all-4.json` | 29801 | associations-all | 5 | `0b9163633063ea97` | after-reAmortize-1 |
| `loans/loan-6/loan-6-detail-associations-repaymentSchedule-3.json` | 29825 | associations-repaymentSchedule | 5 | `0b9163633063ea97` | after-reAmortize-1 |

#### loan 7 — MNT

reAmortize calls (source line): 31094; reAmortize transactions: L23@2024-02-01, L25@2024-02-01

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-7/loan-7-detail-associations-all-1.json` | 30837 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `loans/loan-7/loan-7-detail-associations-all-2.json` | 30967 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-7/loan-7-detail-associations-all-3.json` | 31015 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-7/loan-7-detail-associations-repaymentSchedule-1.json` | 31123 | associations-repaymentSchedule | 5 | `325a04c632adf047` | after-reAmortize-1 |
| `loans/loan-7/loan-7-detail-associations-repaymentSchedule-2.json` | 31147 | associations-repaymentSchedule | 5 | `325a04c632adf047` | after-reAmortize-1 |
| `loans/loan-7/loan-7-detail-associations-all-4.json` | 31303 | associations-all | 5 | `42fd8a1b7ddeaa18` | after-reAmortize-1 |
| `loans/loan-7/loan-7-detail-associations-repaymentSchedule-3.json` | 31327 | associations-repaymentSchedule | 5 | `42fd8a1b7ddeaa18` | after-reAmortize-1 |
| `loans/loan-7/loan-7-detail-associations-repaymentSchedule-4.json` | 31351 | associations-repaymentSchedule | 5 | `42fd8a1b7ddeaa18` | after-reAmortize-1 |
| `loans/loan-7/loan-7-detail-associations-all-5.json` | 31476 | associations-all | 5 | `e5b8d8c436f5c9ce` | after-reAmortize-1 |
| `loans/loan-7/loan-7-detail-associations-repaymentSchedule-5.json` | 31499 | associations-repaymentSchedule | 5 | `e5b8d8c436f5c9ce` | after-reAmortize-1 |

#### loan 8 — MNT

reAmortize calls (source line): 32824; reAmortize transactions: L29@2024-02-01

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-8/loan-8-detail-associations-all-1.json` | 32512 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `loans/loan-8/loan-8-detail-associations-all-2.json` | 32642 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-8/loan-8-detail-associations-all-3.json` | 32690 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-8/loan-8-detail-associations-repaymentSchedule-1.json` | 32853 | associations-repaymentSchedule | 6 | `d7df2f1193f2492f` | after-reAmortize-1 |
| `loans/loan-8/loan-8-detail-associations-repaymentSchedule-2.json` | 32877 | associations-repaymentSchedule | 6 | `d7df2f1193f2492f` | after-reAmortize-1 |
| `loans/loan-8/loan-8-detail-associations-all-4.json` | 33002 | associations-all | 6 | `435367f808263d33` | after-reAmortize-1 |
| `loans/loan-8/loan-8-detail-associations-repaymentSchedule-3.json` | 33026 | associations-repaymentSchedule | 6 | `435367f808263d33` | after-reAmortize-1 |

#### loan 9 — MNT

reAmortize calls (source line): 34404; reAmortize transactions: L34@2024-01-31

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-9/loan-9-detail-associations-all-1.json` | 34037 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `loans/loan-9/loan-9-detail-associations-all-2.json` | 34167 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-9/loan-9-detail-associations-all-3.json` | 34215 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-9/loan-9-detail-associations-repaymentSchedule-1.json` | 34433 | associations-repaymentSchedule | 5 | `a61f445845cd1d40` | after-reAmortize-1 |
| `loans/loan-9/loan-9-detail-associations-repaymentSchedule-2.json` | 34457 | associations-repaymentSchedule | 5 | `a61f445845cd1d40` | after-reAmortize-1 |
| `loans/loan-9/loan-9-detail-associations-all-4.json` | 34582 | associations-all | 5 | `8279c7ac0fe57a6b` | after-reAmortize-1 |
| `loans/loan-9/loan-9-detail-associations-repaymentSchedule-3.json` | 34606 | associations-repaymentSchedule | 5 | `8279c7ac0fe57a6b` | after-reAmortize-1 |

#### loan 10 — MNT

reAmortize calls (source line): -; reAmortize transactions: L40@2024-01-30

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-10/loan-10-detail-associations-all-1.json` | 35618 | associations-all | 5 | `bff8c96130158ddc` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-all-2.json` | 35748 | associations-all | 5 | `247e25fadfc67075` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-all-3.json` | 35796 | associations-all | 5 | `247e25fadfc67075` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-all-4.json` | 35928 | associations-all | 5 | `192407f320a27698` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-repaymentSchedule-1.json` | 35952 | associations-repaymentSchedule | 5 | `192407f320a27698` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-repaymentSchedule-2.json` | 35976 | associations-repaymentSchedule | 5 | `192407f320a27698` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-repaymentSchedule-3.json` | 36107 | associations-repaymentSchedule | 5 | `a7c2e7a4aa217d55` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-repaymentSchedule-4.json` | 36131 | associations-repaymentSchedule | 5 | `a7c2e7a4aa217d55` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-all-5.json` | 36256 | associations-all | 5 | `0ffca80910c3ae94` | no-reAmortize |
| `loans/loan-10/loan-10-detail-associations-repaymentSchedule-5.json` | 36280 | associations-repaymentSchedule | 5 | `0ffca80910c3ae94` | no-reAmortize |

#### loan 11 — MNT

reAmortize calls (source line): 37634; reAmortize transactions: L44@2024-02-01

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-11/loan-11-detail-associations-all-1.json` | 37293 | associations-all | 5 | `bff8c96130158ddc` | before-reAmortize |
| `loans/loan-11/loan-11-detail-associations-all-2.json` | 37423 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-11/loan-11-detail-associations-all-3.json` | 37471 | associations-all | 5 | `247e25fadfc67075` | before-reAmortize |
| `loans/loan-11/loan-11-detail-associations-all-4.json` | 37740 | associations-all | 5 | `0b9163633063ea97` | after-reAmortize-1 |
| `loans/loan-11/loan-11-detail-associations-repaymentSchedule.json` | 37764 | associations-repaymentSchedule | 5 | `0b9163633063ea97` | after-reAmortize-1 |

#### loan 12 — MNT

reAmortize calls (source line): 39165; reAmortize transactions: L49@2024-02-20, L50@2024-02-20

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-12/loan-12-detail-associations-all-1.json` | 38776 | associations-all | 7 | `1c399fb2127a7d44` | before-reAmortize |
| `loans/loan-12/loan-12-detail-associations-all-2.json` | 38906 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-12/loan-12-detail-associations-all-3.json` | 38954 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-12/loan-12-detail-associations-all-4.json` | 39086 | associations-all | 7 | `40469959536ec034` | before-reAmortize |
| `loans/loan-12/loan-12-detail-associations-repaymentSchedule-1.json` | 39194 | associations-repaymentSchedule | 7 | `9131b5cfa15e6406` | after-reAmortize-1 |
| `loans/loan-12/loan-12-detail-associations-repaymentSchedule-2.json` | 39218 | associations-repaymentSchedule | 7 | `9131b5cfa15e6406` | after-reAmortize-1 |
| `loans/loan-12/loan-12-detail-associations-all-5.json` | 39374 | associations-all | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-12/loan-12-detail-associations-repaymentSchedule-3.json` | 39398 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-12/loan-12-detail-associations-repaymentSchedule-4.json` | 39422 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-12/loan-12-detail-associations-all-6.json` | 39547 | associations-all | 7 | `9577110712accad7` | after-reAmortize-1 |
| `loans/loan-12/loan-12-detail-associations-repaymentSchedule-5.json` | 39571 | associations-repaymentSchedule | 7 | `9577110712accad7` | after-reAmortize-1 |

#### loan 13 — MNT

reAmortize calls (source line): 40840; reAmortize transactions: L54@2024-02-20, L55@2024-02-20

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-13/loan-13-detail-associations-all-1.json` | 40584 | associations-all | 7 | `1c399fb2127a7d44` | before-reAmortize |
| `loans/loan-13/loan-13-detail-associations-all-2.json` | 40713 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-13/loan-13-detail-associations-all-3.json` | 40761 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-13/loan-13-detail-associations-repaymentSchedule-1.json` | 40869 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-13/loan-13-detail-associations-repaymentSchedule-2.json` | 40893 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-13/loan-13-detail-associations-all-4.json` | 41049 | associations-all | 7 | `9131b5cfa15e6406` | after-reAmortize-1 |
| `loans/loan-13/loan-13-detail-associations-repaymentSchedule-3.json` | 41073 | associations-repaymentSchedule | 7 | `9131b5cfa15e6406` | after-reAmortize-1 |
| `loans/loan-13/loan-13-detail-associations-repaymentSchedule-4.json` | 41097 | associations-repaymentSchedule | 7 | `9131b5cfa15e6406` | after-reAmortize-1 |
| `loans/loan-13/loan-13-detail-associations-all-5.json` | 41222 | associations-all | 7 | `125ec41b5ed18494` | after-reAmortize-1 |
| `loans/loan-13/loan-13-detail-associations-repaymentSchedule-5.json` | 41246 | associations-repaymentSchedule | 7 | `125ec41b5ed18494` | after-reAmortize-1 |

#### loan 14 — MNT

reAmortize calls (source line): 42516; reAmortize transactions: L60@2024-02-20, L63@2024-02-20

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-14/loan-14-detail-associations-all-1.json` | 42259 | associations-all | 7 | `1c399fb2127a7d44` | before-reAmortize |
| `loans/loan-14/loan-14-detail-associations-all-2.json` | 42389 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-14/loan-14-detail-associations-all-3.json` | 42437 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-14/loan-14-detail-associations-repaymentSchedule-1.json` | 42545 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-repaymentSchedule-2.json` | 42569 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-all-4.json` | 42725 | associations-all | 9 | `bc26cfc7aa8c4445` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-all-5.json` | 42773 | associations-all | 9 | `bc26cfc7aa8c4445` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-repaymentSchedule-3.json` | 42797 | associations-repaymentSchedule | 9 | `bc26cfc7aa8c4445` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-repaymentSchedule-4.json` | 42821 | associations-repaymentSchedule | 9 | `bc26cfc7aa8c4445` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-all-6.json` | 42946 | associations-all | 9 | `e78b911cb20a6502` | after-reAmortize-1 |
| `loans/loan-14/loan-14-detail-associations-repaymentSchedule-5.json` | 42970 | associations-repaymentSchedule | 9 | `e78b911cb20a6502` | after-reAmortize-1 |

#### loan 15 — MNT

reAmortize calls (source line): 44372; reAmortize transactions: L69@2024-02-20, L70@2024-02-20

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-15/loan-15-detail-associations-all-1.json` | 43983 | associations-all | 7 | `1c399fb2127a7d44` | before-reAmortize |
| `loans/loan-15/loan-15-detail-associations-all-2.json` | 44113 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-15/loan-15-detail-associations-all-3.json` | 44161 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-15/loan-15-detail-associations-all-4.json` | 44293 | associations-all | 7 | `ad750d6de35c4803` | before-reAmortize |
| `loans/loan-15/loan-15-detail-associations-repaymentSchedule-1.json` | 44401 | associations-repaymentSchedule | 7 | `23e2d7651c0fd4c7` | after-reAmortize-1 |
| `loans/loan-15/loan-15-detail-associations-repaymentSchedule-2.json` | 44425 | associations-repaymentSchedule | 7 | `23e2d7651c0fd4c7` | after-reAmortize-1 |
| `loans/loan-15/loan-15-detail-associations-repaymentSchedule-3.json` | 44583 | associations-repaymentSchedule | 7 | `60ba1aa2d0b4776e` | after-reAmortize-1 |
| `loans/loan-15/loan-15-detail-associations-repaymentSchedule-4.json` | 44607 | associations-repaymentSchedule | 7 | `60ba1aa2d0b4776e` | after-reAmortize-1 |
| `loans/loan-15/loan-15-detail-associations-all-5.json` | 44731 | associations-all | 7 | `3b490699d557ae16` | after-reAmortize-1 |
| `loans/loan-15/loan-15-detail-associations-repaymentSchedule-5.json` | 44755 | associations-repaymentSchedule | 7 | `3b490699d557ae16` | after-reAmortize-1 |

#### loan 16 — MNT

reAmortize calls (source line): 46024; reAmortize transactions: L76@2024-02-20

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-16/loan-16-detail-associations-all-1.json` | 45767 | associations-all | 7 | `1c399fb2127a7d44` | before-reAmortize |
| `loans/loan-16/loan-16-detail-associations-all-2.json` | 45897 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-16/loan-16-detail-associations-all-3.json` | 45945 | associations-all | 7 | `1329478ff803af25` | before-reAmortize |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-1.json` | 46053 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-2.json` | 46077 | associations-repaymentSchedule | 7 | `440e2e5d2ffdb4fe` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-all-4.json` | 46233 | associations-all | 9 | `6ce5eba3f680c23c` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-all-5.json` | 46281 | associations-all | 9 | `6ce5eba3f680c23c` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-3.json` | 46305 | associations-repaymentSchedule | 9 | `6ce5eba3f680c23c` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-4.json` | 46329 | associations-repaymentSchedule | 9 | `6ce5eba3f680c23c` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-all-6.json` | 46485 | associations-all | 9 | `93d77865518a307a` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-5.json` | 46509 | associations-repaymentSchedule | 9 | `93d77865518a307a` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-6.json` | 46533 | associations-repaymentSchedule | 9 | `93d77865518a307a` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-7.json` | 46665 | associations-repaymentSchedule | 9 | `399947b62e4d29fa` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-8.json` | 46689 | associations-repaymentSchedule | 9 | `399947b62e4d29fa` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-all-7.json` | 46814 | associations-all | 9 | `dce276659be768d5` | after-reAmortize-1 |
| `loans/loan-16/loan-16-detail-associations-repaymentSchedule-9.json` | 46838 | associations-repaymentSchedule | 9 | `dce276659be768d5` | after-reAmortize-1 |

#### loan 17 — MNT

reAmortize calls (source line): 48307; reAmortize transactions: L82@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-17/loan-17-detail-associations-all-1.json` | 47774 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-all-2.json` | 47904 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-all-3.json` | 47952 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-1.json` | 47976 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-2.json` | 48000 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-all-4.json` | 48156 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-3.json` | 48180 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-4.json` | 48204 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-5.json` | 48336 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-6.json` | 48360 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-17/loan-17-detail-associations-all-5.json` | 48485 | associations-all | 7 | `40a1325da8dd4abe` | after-reAmortize-1 |
| `loans/loan-17/loan-17-detail-associations-repaymentSchedule-7.json` | 48509 | associations-repaymentSchedule | 7 | `40a1325da8dd4abe` | after-reAmortize-1 |

#### loan 18 — MNT

reAmortize calls (source line): 50135; reAmortize transactions: L89@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-18/loan-18-detail-associations-all-1.json` | 49444 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-all-2.json` | 49574 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-all-3.json` | 49622 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-1.json` | 49646 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-2.json` | 49670 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-all-4.json` | 49826 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-3.json` | 49984 | associations-repaymentSchedule | 7 | `51b357d6d9583f7e` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-4.json` | 50008 | associations-repaymentSchedule | 7 | `51b357d6d9583f7e` | before-reAmortize |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-5.json` | 50164 | associations-repaymentSchedule | 7 | `75600f191353c879` | after-reAmortize-1 |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-6.json` | 50188 | associations-repaymentSchedule | 7 | `75600f191353c879` | after-reAmortize-1 |
| `loans/loan-18/loan-18-detail-associations-all-5.json` | 50337 | associations-all | 7 | `b242b4220a2d6fac` | after-reAmortize-1 |
| `loans/loan-18/loan-18-detail-associations-repaymentSchedule-7.json` | 50361 | associations-repaymentSchedule | 7 | `b242b4220a2d6fac` | after-reAmortize-1 |

#### loan 19 — MNT

reAmortize calls (source line): 51940; reAmortize transactions: L97@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-19/loan-19-detail-associations-all-1.json` | 51297 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-all-2.json` | 51427 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-all-3.json` | 51475 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-1.json` | 51499 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-2.json` | 51523 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-all-4.json` | 51679 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-3.json` | 51813 | associations-repaymentSchedule | 8 | `a1b51ee00d03a1f8` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-4.json` | 51837 | associations-repaymentSchedule | 8 | `a1b51ee00d03a1f8` | before-reAmortize |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-5.json` | 51969 | associations-repaymentSchedule | 8 | `aaf232c98d975be0` | after-reAmortize-1 |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-6.json` | 51993 | associations-repaymentSchedule | 8 | `aaf232c98d975be0` | after-reAmortize-1 |
| `loans/loan-19/loan-19-detail-associations-all-5.json` | 52118 | associations-all | 8 | `2d659f667bb26f14` | after-reAmortize-1 |
| `loans/loan-19/loan-19-detail-associations-repaymentSchedule-7.json` | 52142 | associations-repaymentSchedule | 8 | `2d659f667bb26f14` | after-reAmortize-1 |

#### loan 20 — MNT

reAmortize calls (source line): 53714; reAmortize transactions: L105@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-20/loan-20-detail-associations-all-1.json` | 53077 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-all-2.json` | 53206 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-all-3.json` | 53254 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-1.json` | 53278 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-2.json` | 53302 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-all-4.json` | 53458 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-all-5.json` | 53537 | associations-all | 7 | `1edfd2bfc183c20f` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-3.json` | 53587 | associations-repaymentSchedule | 7 | `1edfd2bfc183c20f` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-4.json` | 53611 | associations-repaymentSchedule | 7 | `1edfd2bfc183c20f` | before-reAmortize |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-5.json` | 53743 | associations-repaymentSchedule | 7 | `6b7e2a337cc2e08a` | after-reAmortize-1 |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-6.json` | 53767 | associations-repaymentSchedule | 7 | `6b7e2a337cc2e08a` | after-reAmortize-1 |
| `loans/loan-20/loan-20-detail-associations-all-6.json` | 53892 | associations-all | 7 | `3870ff1b64b8e6c8` | after-reAmortize-1 |
| `loans/loan-20/loan-20-detail-associations-repaymentSchedule-7.json` | 53916 | associations-repaymentSchedule | 7 | `3870ff1b64b8e6c8` | after-reAmortize-1 |

#### loan 21 — MNT

reAmortize calls (source line): 55462; reAmortize transactions: L110@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-21/loan-21-detail-associations-all-1.json` | 54929 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-all-2.json` | 55059 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-all-3.json` | 55107 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-1.json` | 55131 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-2.json` | 55155 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-all-4.json` | 55311 | associations-all | 7 | `861157f6e309b387` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-3.json` | 55335 | associations-repaymentSchedule | 7 | `861157f6e309b387` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-4.json` | 55359 | associations-repaymentSchedule | 7 | `861157f6e309b387` | before-reAmortize |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-5.json` | 55491 | associations-repaymentSchedule | 7 | `59fda9acdcac46e9` | after-reAmortize-1 |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-6.json` | 55515 | associations-repaymentSchedule | 7 | `59fda9acdcac46e9` | after-reAmortize-1 |
| `loans/loan-21/loan-21-detail-associations-all-5.json` | 55640 | associations-all | 7 | `8786932afbe08581` | after-reAmortize-1 |
| `loans/loan-21/loan-21-detail-associations-repaymentSchedule-7.json` | 55664 | associations-repaymentSchedule | 7 | `8786932afbe08581` | after-reAmortize-1 |

#### loan 22 — MNT

reAmortize calls (source line): 57209; reAmortize transactions: L118@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-22/loan-22-detail-associations-all-1.json` | 56677 | associations-all | 8 | `fec74cf25ff4c7d3` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-all-2.json` | 56807 | associations-all | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-all-3.json` | 56855 | associations-all | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-1.json` | 56879 | associations-repaymentSchedule | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-2.json` | 56903 | associations-repaymentSchedule | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-all-4.json` | 57058 | associations-all | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-3.json` | 57082 | associations-repaymentSchedule | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-4.json` | 57106 | associations-repaymentSchedule | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-5.json` | 57238 | associations-repaymentSchedule | 8 | `b64be318b418b55c` | after-reAmortize-1 |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-6.json` | 57262 | associations-repaymentSchedule | 8 | `b64be318b418b55c` | after-reAmortize-1 |
| `loans/loan-22/loan-22-detail-associations-all-5.json` | 57387 | associations-all | 8 | `0c0d0a552180618a` | after-reAmortize-1 |
| `loans/loan-22/loan-22-detail-associations-repaymentSchedule-7.json` | 57411 | associations-repaymentSchedule | 8 | `0c0d0a552180618a` | after-reAmortize-1 |

#### loan 23 — MNT

reAmortize calls (source line): 58957; reAmortize transactions: L123@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-23/loan-23-detail-associations-all-1.json` | 58424 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-all-2.json` | 58554 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-all-3.json` | 58602 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-1.json` | 58626 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-2.json` | 58650 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-all-4.json` | 58806 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-3.json` | 58830 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-4.json` | 58854 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-5.json` | 58986 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-6.json` | 59010 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-23/loan-23-detail-associations-all-5.json` | 59135 | associations-all | 7 | `b2af527f29b51223` | after-reAmortize-1 |
| `loans/loan-23/loan-23-detail-associations-repaymentSchedule-7.json` | 59159 | associations-repaymentSchedule | 7 | `b2af527f29b51223` | after-reAmortize-1 |

#### loan 24 — MNT

reAmortize calls (source line): 60759; reAmortize transactions: L130@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-24/loan-24-detail-associations-all-1.json` | 60171 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-all-2.json` | 60301 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-all-3.json` | 60349 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-1.json` | 60373 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-2.json` | 60397 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-all-4.json` | 60553 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-3.json` | 60632 | associations-repaymentSchedule | 7 | `93fd4a22e41319cc` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-4.json` | 60656 | associations-repaymentSchedule | 7 | `93fd4a22e41319cc` | before-reAmortize |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-5.json` | 60788 | associations-repaymentSchedule | 7 | `bf00dc51b8f3f91b` | after-reAmortize-1 |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-6.json` | 60812 | associations-repaymentSchedule | 7 | `bf00dc51b8f3f91b` | after-reAmortize-1 |
| `loans/loan-24/loan-24-detail-associations-all-5.json` | 60936 | associations-all | 7 | `5eaf3c7415eebe96` | after-reAmortize-1 |
| `loans/loan-24/loan-24-detail-associations-repaymentSchedule-7.json` | 60960 | associations-repaymentSchedule | 7 | `5eaf3c7415eebe96` | after-reAmortize-1 |

#### loan 25 — MNT

reAmortize calls (source line): 62561; reAmortize transactions: L137@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-25/loan-25-detail-associations-all-1.json` | 61973 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-all-2.json` | 62103 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-all-3.json` | 62151 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-1.json` | 62175 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-2.json` | 62199 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-all-4.json` | 62355 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-3.json` | 62434 | associations-repaymentSchedule | 8 | `55840c23303ff789` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-4.json` | 62458 | associations-repaymentSchedule | 8 | `55840c23303ff789` | before-reAmortize |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-5.json` | 62590 | associations-repaymentSchedule | 8 | `7849b273e44b2f00` | after-reAmortize-1 |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-6.json` | 62614 | associations-repaymentSchedule | 8 | `7849b273e44b2f00` | after-reAmortize-1 |
| `loans/loan-25/loan-25-detail-associations-all-5.json` | 62739 | associations-all | 8 | `6470097dde11835d` | after-reAmortize-1 |
| `loans/loan-25/loan-25-detail-associations-repaymentSchedule-7.json` | 62763 | associations-repaymentSchedule | 8 | `6470097dde11835d` | after-reAmortize-1 |

#### loan 26 — MNT

reAmortize calls (source line): 64335; reAmortize transactions: L145@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-26/loan-26-detail-associations-all-1.json` | 63699 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-all-2.json` | 63829 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-all-3.json` | 63877 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-1.json` | 63901 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-2.json` | 63925 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-all-4.json` | 64081 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-all-5.json` | 64158 | associations-all | 7 | `1edfd2bfc183c20f` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-3.json` | 64208 | associations-repaymentSchedule | 7 | `1edfd2bfc183c20f` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-4.json` | 64232 | associations-repaymentSchedule | 7 | `1edfd2bfc183c20f` | before-reAmortize |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-5.json` | 64364 | associations-repaymentSchedule | 7 | `df491d0fa26806c5` | after-reAmortize-1 |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-6.json` | 64388 | associations-repaymentSchedule | 7 | `df491d0fa26806c5` | after-reAmortize-1 |
| `loans/loan-26/loan-26-detail-associations-all-6.json` | 64513 | associations-all | 7 | `655637ecd6cf371d` | after-reAmortize-1 |
| `loans/loan-26/loan-26-detail-associations-repaymentSchedule-7.json` | 64537 | associations-repaymentSchedule | 7 | `655637ecd6cf371d` | after-reAmortize-1 |

#### loan 27 — MNT

reAmortize calls (source line): 66082; reAmortize transactions: L150@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-27/loan-27-detail-associations-all-1.json` | 65549 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-all-2.json` | 65679 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-all-3.json` | 65727 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-1.json` | 65751 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-2.json` | 65775 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-all-4.json` | 65931 | associations-all | 7 | `861157f6e309b387` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-3.json` | 65955 | associations-repaymentSchedule | 7 | `861157f6e309b387` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-4.json` | 65979 | associations-repaymentSchedule | 7 | `861157f6e309b387` | before-reAmortize |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-5.json` | 66111 | associations-repaymentSchedule | 7 | `3885472a80a2e2b3` | after-reAmortize-1 |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-6.json` | 66135 | associations-repaymentSchedule | 7 | `3885472a80a2e2b3` | after-reAmortize-1 |
| `loans/loan-27/loan-27-detail-associations-all-5.json` | 66260 | associations-all | 7 | `181e21cd51e77dfd` | after-reAmortize-1 |
| `loans/loan-27/loan-27-detail-associations-repaymentSchedule-7.json` | 66284 | associations-repaymentSchedule | 7 | `181e21cd51e77dfd` | after-reAmortize-1 |

#### loan 28 — MNT

reAmortize calls (source line): 67752; reAmortize transactions: L158@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-28/loan-28-detail-associations-all-1.json` | 67219 | associations-all | 8 | `fec74cf25ff4c7d3` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-all-2.json` | 67349 | associations-all | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-all-3.json` | 67397 | associations-all | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-1.json` | 67421 | associations-repaymentSchedule | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-2.json` | 67445 | associations-repaymentSchedule | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-all-4.json` | 67601 | associations-all | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-3.json` | 67625 | associations-repaymentSchedule | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-4.json` | 67649 | associations-repaymentSchedule | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-5.json` | 67781 | associations-repaymentSchedule | 8 | `596606836346732f` | after-reAmortize-1 |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-6.json` | 67805 | associations-repaymentSchedule | 8 | `596606836346732f` | after-reAmortize-1 |
| `loans/loan-28/loan-28-detail-associations-all-5.json` | 67930 | associations-all | 8 | `2fb92c8e676d29e6` | after-reAmortize-1 |
| `loans/loan-28/loan-28-detail-associations-repaymentSchedule-7.json` | 67954 | associations-repaymentSchedule | 8 | `2fb92c8e676d29e6` | after-reAmortize-1 |

#### loan 29 — MNT

reAmortize calls (source line): 69427; reAmortize transactions: L163@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-29/loan-29-detail-associations-all-1.json` | 68967 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-29/loan-29-detail-associations-all-2.json` | 69097 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-29/loan-29-detail-associations-all-3.json` | 69145 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-29/loan-29-detail-associations-all-4.json` | 69277 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-1.json` | 69301 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-2.json` | 69325 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-3.json` | 69456 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-4.json` | 69480 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-29/loan-29-detail-associations-all-5.json` | 69636 | associations-all | 7 | `b9d9fe13c18d76ff` | after-reAmortize-1 |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-5.json` | 69660 | associations-repaymentSchedule | 7 | `b9d9fe13c18d76ff` | after-reAmortize-1 |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-6.json` | 69684 | associations-repaymentSchedule | 7 | `b9d9fe13c18d76ff` | after-reAmortize-1 |
| `loans/loan-29/loan-29-detail-associations-all-6.json` | 69809 | associations-all | 7 | `41b8fb7b66ee5de3` | after-reAmortize-1 |
| `loans/loan-29/loan-29-detail-associations-repaymentSchedule-7.json` | 69833 | associations-repaymentSchedule | 7 | `41b8fb7b66ee5de3` | after-reAmortize-1 |

#### loan 30 — MNT

reAmortize calls (source line): 71307; reAmortize transactions: L172@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-30/loan-30-detail-associations-all-1.json` | 70846 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-30/loan-30-detail-associations-all-2.json` | 70976 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-30/loan-30-detail-associations-all-3.json` | 71024 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-30/loan-30-detail-associations-all-4.json` | 71156 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-1.json` | 71180 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-2.json` | 71204 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-3.json` | 71336 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-4.json` | 71360 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-30/loan-30-detail-associations-all-5.json` | 71516 | associations-all | 7 | `b9d9fe13c18d76ff` | after-reAmortize-1 |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-5.json` | 71540 | associations-repaymentSchedule | 7 | `b9d9fe13c18d76ff` | after-reAmortize-1 |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-6.json` | 71564 | associations-repaymentSchedule | 7 | `b9d9fe13c18d76ff` | after-reAmortize-1 |
| `loans/loan-30/loan-30-detail-associations-all-6.json` | 71689 | associations-all | 7 | `a911d4c14c0654e1` | after-reAmortize-1 |
| `loans/loan-30/loan-30-detail-associations-repaymentSchedule-7.json` | 71713 | associations-repaymentSchedule | 7 | `a911d4c14c0654e1` | after-reAmortize-1 |

#### loan 31 — MNT

reAmortize calls (source line): 73110; reAmortize transactions: L181@2024-03-15, L183@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-31/loan-31-detail-associations-all-1.json` | 72649 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-31/loan-31-detail-associations-all-2.json` | 72779 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-31/loan-31-detail-associations-all-3.json` | 72827 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-31/loan-31-detail-associations-all-4.json` | 72959 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-1.json` | 72983 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-2.json` | 73007 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-3.json` | 73139 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-4.json` | 73163 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-31/loan-31-detail-associations-all-5.json` | 73319 | associations-all | 7 | `9cf2140f3079f814` | after-reAmortize-1 |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-5.json` | 73342 | associations-repaymentSchedule | 7 | `9cf2140f3079f814` | after-reAmortize-1 |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-6.json` | 73366 | associations-repaymentSchedule | 7 | `9cf2140f3079f814` | after-reAmortize-1 |
| `loans/loan-31/loan-31-detail-associations-all-6.json` | 73491 | associations-all | 7 | `fbd8ae1e0a532b66` | after-reAmortize-1 |
| `loans/loan-31/loan-31-detail-associations-repaymentSchedule-7.json` | 73515 | associations-repaymentSchedule | 7 | `fbd8ae1e0a532b66` | after-reAmortize-1 |

#### loan 32 — MNT

reAmortize calls (source line): 74911; reAmortize transactions: L190@2024-03-15, L191@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-32/loan-32-detail-associations-all-1.json` | 74450 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-32/loan-32-detail-associations-all-2.json` | 74580 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-32/loan-32-detail-associations-all-3.json` | 74628 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-32/loan-32-detail-associations-all-4.json` | 74760 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-1.json` | 74784 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-2.json` | 74808 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-3.json` | 74940 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-4.json` | 74964 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-32/loan-32-detail-associations-all-5.json` | 75120 | associations-all | 7 | `2cf13fdd5fc13d65` | after-reAmortize-1 |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-5.json` | 75144 | associations-repaymentSchedule | 7 | `2cf13fdd5fc13d65` | after-reAmortize-1 |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-6.json` | 75168 | associations-repaymentSchedule | 7 | `2cf13fdd5fc13d65` | after-reAmortize-1 |
| `loans/loan-32/loan-32-detail-associations-all-6.json` | 75293 | associations-all | 7 | `b7e60dc796625147` | after-reAmortize-1 |
| `loans/loan-32/loan-32-detail-associations-repaymentSchedule-7.json` | 75317 | associations-repaymentSchedule | 7 | `b7e60dc796625147` | after-reAmortize-1 |

#### loan 33 — MNT

reAmortize calls (source line): 76642, 76930; reAmortize transactions: L199@2024-03-15, L201@2024-05-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-33/loan-33-detail-associations-all-1.json` | 76253 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-33/loan-33-detail-associations-all-2.json` | 76383 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-33/loan-33-detail-associations-all-3.json` | 76431 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-33/loan-33-detail-associations-all-4.json` | 76563 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-33/loan-33-detail-associations-repaymentSchedule-1.json` | 76671 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-33/loan-33-detail-associations-repaymentSchedule-2.json` | 76695 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-33/loan-33-detail-associations-all-5.json` | 76851 | associations-all | 7 | `f94a7567da0d4fc7` | after-reAmortize-1 |
| `loans/loan-33/loan-33-detail-associations-repaymentSchedule-3.json` | 76959 | associations-repaymentSchedule | 7 | `5ba355155724de11` | after-reAmortize-2 |
| `loans/loan-33/loan-33-detail-associations-repaymentSchedule-4.json` | 76983 | associations-repaymentSchedule | 7 | `5ba355155724de11` | after-reAmortize-2 |
| `loans/loan-33/loan-33-detail-associations-all-6.json` | 77108 | associations-all | 7 | `20d948d97631d6c6` | after-reAmortize-2 |
| `loans/loan-33/loan-33-detail-associations-repaymentSchedule-5.json` | 77132 | associations-repaymentSchedule | 7 | `20d948d97631d6c6` | after-reAmortize-2 |

#### loan 34 — MNT

reAmortize calls (source line): 78456, 78569; reAmortize transactions: L209@2024-03-15, L210@2024-05-01

REJECTED reAmortize attempt(s): loans/loan-34/loan-34-reAmortize-response-2.json HTTP 403 (error.msg.loan.reamortize.reamortize.transaction.interest.handling.strategy.missmatch)

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-34/loan-34-detail-associations-all-1.json` | 78067 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-34/loan-34-detail-associations-all-2.json` | 78197 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-34/loan-34-detail-associations-all-3.json` | 78245 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-34/loan-34-detail-associations-all-4.json` | 78377 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-34/loan-34-detail-associations-all-5.json` | 78730 | associations-all | 7 | `c66e1f11601599be` | after-reAmortize-2 |
| `loans/loan-34/loan-34-detail-associations-repaymentSchedule.json` | 78754 | associations-repaymentSchedule | 7 | `c66e1f11601599be` | after-reAmortize-2 |

#### loan 35 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `stage/loan-35-detail-associations-all-1.json` | 79690 | associations-all | 7 | `a12613e57ed9ef7f` | no-reAmortize |
| `stage/loan-35-detail-associations-all-2.json` | 79820 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `stage/loan-35-detail-associations-all-3.json` | 79868 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `stage/loan-35-detail-associations-all-4.json` | 80000 | associations-all | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `stage/loan-35-detail-associations-repaymentSchedule.json` | 80244 | associations-repaymentSchedule | 7 | `8d59ae6e37db868d` | no-reAmortize |

#### loan 36 — MNT

reAmortize calls (source line): 81436; reAmortize transactions: L218@2024-04-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-36/loan-36-detail-associations-all-1.json` | 81131 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-36/loan-36-detail-associations-all-2.json` | 81261 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-36/loan-36-detail-associations-all-3.json` | 81309 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-36/loan-36-detail-associations-repaymentSchedule-1.json` | 81333 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-36/loan-36-detail-associations-repaymentSchedule-2.json` | 81357 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-36/loan-36-detail-associations-repaymentSchedule-3.json` | 81465 | associations-repaymentSchedule | 7 | `8ac0782a5db3a0c0` | after-reAmortize-1 |
| `loans/loan-36/loan-36-detail-associations-repaymentSchedule-4.json` | 81489 | associations-repaymentSchedule | 7 | `8ac0782a5db3a0c0` | after-reAmortize-1 |
| `loans/loan-36/loan-36-detail-associations-all-4.json` | 81614 | associations-all | 7 | `9404608807a4fedc` | after-reAmortize-1 |
| `loans/loan-36/loan-36-detail-associations-repaymentSchedule-5.json` | 81638 | associations-repaymentSchedule | 7 | `9404608807a4fedc` | after-reAmortize-1 |

#### loan 37 — MNT

reAmortize calls (source line): 83111; reAmortize transactions: L224@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-37/loan-37-detail-associations-all-1.json` | 82650 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-37/loan-37-detail-associations-all-2.json` | 82780 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-37/loan-37-detail-associations-all-3.json` | 82828 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-37/loan-37-detail-associations-all-4.json` | 82960 | associations-all | 7 | `1dcc8cb23800e0a7` | before-reAmortize |
| `loans/loan-37/loan-37-detail-associations-repaymentSchedule-1.json` | 82984 | associations-repaymentSchedule | 7 | `1dcc8cb23800e0a7` | before-reAmortize |
| `loans/loan-37/loan-37-detail-associations-repaymentSchedule-2.json` | 83008 | associations-repaymentSchedule | 7 | `1dcc8cb23800e0a7` | before-reAmortize |
| `loans/loan-37/loan-37-detail-associations-repaymentSchedule-3.json` | 83140 | associations-repaymentSchedule | 7 | `1ee7b94190c21e62` | after-reAmortize-1 |
| `loans/loan-37/loan-37-detail-associations-repaymentSchedule-4.json` | 83164 | associations-repaymentSchedule | 7 | `1ee7b94190c21e62` | after-reAmortize-1 |
| `loans/loan-37/loan-37-detail-associations-all-5.json` | 83289 | associations-all | 7 | `e0e790a92412fcc3` | after-reAmortize-1 |
| `loans/loan-37/loan-37-detail-associations-repaymentSchedule-5.json` | 83313 | associations-repaymentSchedule | 7 | `e0e790a92412fcc3` | after-reAmortize-1 |

#### loan 38 — MNT

reAmortize calls (source line): 84782; reAmortize transactions: L231@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-38/loan-38-detail-associations-all-1.json` | 84249 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-all-2.json` | 84379 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-all-3.json` | 84427 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-1.json` | 84451 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-2.json` | 84475 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-all-4.json` | 84631 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-3.json` | 84655 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-4.json` | 84679 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-5.json` | 84811 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-6.json` | 84835 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-7.json` | 84967 | associations-repaymentSchedule | 7 | `ce788e50f972b73e` | after-reAmortize-1 |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-8.json` | 84991 | associations-repaymentSchedule | 7 | `ce788e50f972b73e` | after-reAmortize-1 |
| `loans/loan-38/loan-38-detail-associations-all-5.json` | 85116 | associations-all | 7 | `ecef8deda9748dc3` | after-reAmortize-1 |
| `loans/loan-38/loan-38-detail-associations-repaymentSchedule-9.json` | 85140 | associations-repaymentSchedule | 7 | `ecef8deda9748dc3` | after-reAmortize-1 |

#### loan 39 — MNT

reAmortize calls (source line): 86608; reAmortize transactions: L236@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-39/loan-39-detail-associations-all-1.json` | 86076 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-all-2.json` | 86206 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-all-3.json` | 86254 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-1.json` | 86278 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-2.json` | 86302 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-all-4.json` | 86458 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-3.json` | 86481 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-4.json` | 86505 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-5.json` | 86637 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-6.json` | 86661 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-7.json` | 86793 | associations-repaymentSchedule | 7 | `ce788e50f972b73e` | after-reAmortize-1 |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-8.json` | 86817 | associations-repaymentSchedule | 7 | `ce788e50f972b73e` | after-reAmortize-1 |
| `loans/loan-39/loan-39-detail-associations-all-5.json` | 86942 | associations-all | 7 | `45c367ae7355eb5d` | after-reAmortize-1 |
| `loans/loan-39/loan-39-detail-associations-repaymentSchedule-9.json` | 86966 | associations-repaymentSchedule | 7 | `45c367ae7355eb5d` | after-reAmortize-1 |

#### loan 40 — MNT

reAmortize calls (source line): 88434; reAmortize transactions: L241@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-40/loan-40-detail-associations-all-1.json` | 87901 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-all-2.json` | 88031 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-all-3.json` | 88079 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-1.json` | 88103 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-2.json` | 88127 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-all-4.json` | 88283 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-3.json` | 88307 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-4.json` | 88331 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-5.json` | 88463 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-6.json` | 88487 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-all-5.json` | 88643 | associations-all | 7 | `f94a7567da0d4fc7` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-7.json` | 88667 | associations-repaymentSchedule | 7 | `f94a7567da0d4fc7` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-8.json` | 88691 | associations-repaymentSchedule | 7 | `f94a7567da0d4fc7` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-9.json` | 88768 | associations-repaymentSchedule | 7 | `3123e0f7c1415ac8` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-10.json` | 88792 | associations-repaymentSchedule | 7 | `3123e0f7c1415ac8` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-all-6.json` | 88917 | associations-all | 7 | `45c367ae7355eb5d` | after-reAmortize-1 |
| `loans/loan-40/loan-40-detail-associations-repaymentSchedule-11.json` | 88941 | associations-repaymentSchedule | 7 | `45c367ae7355eb5d` | after-reAmortize-1 |

#### loan 41 — MNT

reAmortize calls (source line): 90409; reAmortize transactions: L248@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-41/loan-41-detail-associations-all-1.json` | 89877 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-all-2.json` | 90007 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-all-3.json` | 90055 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-1.json` | 90079 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-2.json` | 90103 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-all-4.json` | 90259 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-3.json` | 90283 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-4.json` | 90307 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-5.json` | 90438 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-6.json` | 90462 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-all-5.json` | 90594 | associations-all | 7 | `8489ac3f200addf5` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-7.json` | 90644 | associations-repaymentSchedule | 7 | `8489ac3f200addf5` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-8.json` | 90668 | associations-repaymentSchedule | 7 | `8489ac3f200addf5` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-9.json` | 90745 | associations-repaymentSchedule | 7 | `dac6815760e9fe69` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-10.json` | 90769 | associations-repaymentSchedule | 7 | `dac6815760e9fe69` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-all-6.json` | 90894 | associations-all | 7 | `2e856ac263ac465f` | after-reAmortize-1 |
| `loans/loan-41/loan-41-detail-associations-repaymentSchedule-11.json` | 90918 | associations-repaymentSchedule | 7 | `2e856ac263ac465f` | after-reAmortize-1 |

#### loan 42 — MNT

reAmortize calls (source line): 92387; reAmortize transactions: L254@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-42/loan-42-detail-associations-all-1.json` | 91854 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-all-2.json` | 91984 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-all-3.json` | 92032 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-1.json` | 92056 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-2.json` | 92080 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-all-4.json` | 92236 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-3.json` | 92260 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-4.json` | 92284 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-5.json` | 92416 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-6.json` | 92440 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-7.json` | 92622 | associations-repaymentSchedule | 7 | `ec0cecd8284801a9` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-8.json` | 92646 | associations-repaymentSchedule | 7 | `ec0cecd8284801a9` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-9.json` | 92723 | associations-repaymentSchedule | 7 | `8667a5a4d8dc3d9b` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-10.json` | 92747 | associations-repaymentSchedule | 7 | `8667a5a4d8dc3d9b` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-all-5.json` | 92896 | associations-all | 7 | `73caa87810ba3ed6` | after-reAmortize-1 |
| `loans/loan-42/loan-42-detail-associations-repaymentSchedule-11.json` | 92920 | associations-repaymentSchedule | 7 | `73caa87810ba3ed6` | after-reAmortize-1 |

#### loan 43 — MNT

reAmortize calls (source line): 94388; reAmortize transactions: L259@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-43/loan-43-detail-associations-all-1.json` | 93856 | associations-all | 7 | `a12613e57ed9ef7f` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-all-2.json` | 93986 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-all-3.json` | 94034 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-1.json` | 94058 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-2.json` | 94082 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-all-4.json` | 94238 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-3.json` | 94262 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-4.json` | 94285 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-5.json` | 94417 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-6.json` | 94441 | associations-repaymentSchedule | 7 | `9fb458fb4dc10ba7` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-all-5.json` | 94597 | associations-all | 7 | `3465d701ad30e47e` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-7.json` | 94621 | associations-repaymentSchedule | 7 | `3465d701ad30e47e` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-8.json` | 94645 | associations-repaymentSchedule | 7 | `3465d701ad30e47e` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-9.json` | 94722 | associations-repaymentSchedule | 7 | `a96d07f1d046201c` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-10.json` | 94746 | associations-repaymentSchedule | 7 | `a96d07f1d046201c` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-all-6.json` | 94871 | associations-all | 7 | `f4e8685702bd66f5` | after-reAmortize-1 |
| `loans/loan-43/loan-43-detail-associations-repaymentSchedule-11.json` | 94895 | associations-repaymentSchedule | 7 | `f4e8685702bd66f5` | after-reAmortize-1 |

#### loan 44 — MNT

reAmortize calls (source line): 96363; reAmortize transactions: L271@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-44/loan-44-detail-associations-all-1.json` | 95830 | associations-all | 7 | `42240cbb78f45f36` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-all-2.json` | 95960 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-all-3.json` | 96008 | associations-all | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-1.json` | 96032 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-2.json` | 96056 | associations-repaymentSchedule | 7 | `019706d8130347f4` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-all-4.json` | 96212 | associations-all | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-3.json` | 96236 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-4.json` | 96260 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | before-reAmortize |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-5.json` | 96392 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-6.json` | 96416 | associations-repaymentSchedule | 7 | `738a6f8d36ccc2ad` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-all-5.json` | 96572 | associations-all | 8 | `fc8266951907e08c` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-all-6.json` | 96620 | associations-all | 8 | `fc8266951907e08c` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-7.json` | 96644 | associations-repaymentSchedule | 8 | `fc8266951907e08c` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-8.json` | 96668 | associations-repaymentSchedule | 8 | `fc8266951907e08c` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-9.json` | 96745 | associations-repaymentSchedule | 8 | `5b47956f8487904e` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-10.json` | 96769 | associations-repaymentSchedule | 8 | `5b47956f8487904e` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-all-7.json` | 96894 | associations-all | 8 | `f9a6dbf65d002df6` | after-reAmortize-1 |
| `loans/loan-44/loan-44-detail-associations-repaymentSchedule-11.json` | 96918 | associations-repaymentSchedule | 8 | `f9a6dbf65d002df6` | after-reAmortize-1 |

#### loan 45 — MNT

reAmortize calls (source line): 98386; reAmortize transactions: L278@2024-03-15

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-45/loan-45-detail-associations-all-1.json` | 97854 | associations-all | 8 | `0f307c7288a11aef` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-all-2.json` | 97984 | associations-all | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-all-3.json` | 98032 | associations-all | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-1.json` | 98056 | associations-repaymentSchedule | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-2.json` | 98080 | associations-repaymentSchedule | 8 | `4acea114bd5ded6e` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-all-4.json` | 98235 | associations-all | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-3.json` | 98259 | associations-repaymentSchedule | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-4.json` | 98283 | associations-repaymentSchedule | 8 | `986d1afe321ef37a` | before-reAmortize |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-5.json` | 98415 | associations-repaymentSchedule | 8 | `596606836346732f` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-6.json` | 98439 | associations-repaymentSchedule | 8 | `596606836346732f` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-all-5.json` | 98595 | associations-all | 10 | `4381c09bb446ae5b` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-all-6.json` | 98643 | associations-all | 10 | `4381c09bb446ae5b` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-7.json` | 98667 | associations-repaymentSchedule | 10 | `4381c09bb446ae5b` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-8.json` | 98691 | associations-repaymentSchedule | 10 | `4381c09bb446ae5b` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-9.json` | 98768 | associations-repaymentSchedule | 10 | `faf782f9737c5a42` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-10.json` | 98792 | associations-repaymentSchedule | 10 | `faf782f9737c5a42` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-all-7.json` | 98917 | associations-all | 10 | `6ab89f9263e84fd0` | after-reAmortize-1 |
| `loans/loan-45/loan-45-detail-associations-repaymentSchedule-11.json` | 98941 | associations-repaymentSchedule | 10 | `6ab89f9263e84fd0` | after-reAmortize-1 |

#### loan 46 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

REJECTED reAmortize attempt(s): loans/loan-46/loan-46-reAmortize-response.json HTTP 403 (error.msg.loan.reamortize.not.allowed.on.charged.off)

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-46/loan-46-detail-associations-all-1.json` | 99954 | associations-all | 7 | `a12613e57ed9ef7f` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-all-2.json` | 100084 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-all-3.json` | 100132 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-1.json` | 100156 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-2.json` | 100180 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-all-4.json` | 100336 | associations-all | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-3.json` | 100360 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-4.json` | 100384 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-5.json` | 100516 | associations-repaymentSchedule | 7 | `33f18338ae643545` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-6.json` | 100540 | associations-repaymentSchedule | 7 | `33f18338ae643545` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-all-5.json` | 100749 | associations-all | 7 | `a964685890ee3fe1` | no-reAmortize |
| `loans/loan-46/loan-46-detail-associations-repaymentSchedule-7.json` | 100773 | associations-repaymentSchedule | 7 | `a964685890ee3fe1` | no-reAmortize |

#### loan 47 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

REJECTED reAmortize attempt(s): loans/loan-47/loan-47-reAmortize-response.json HTTP 403 (error.msg.loan.reamortize.not.allowed.on.charged.off)

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-47/loan-47-detail-associations-all-1.json` | 101786 | associations-all | 7 | `a12613e57ed9ef7f` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-all-2.json` | 101916 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-all-3.json` | 101964 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-1.json` | 101988 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-2.json` | 102012 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-all-4.json` | 102167 | associations-all | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-3.json` | 102191 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-4.json` | 102215 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-5.json` | 102347 | associations-repaymentSchedule | 7 | `11c137753e360b53` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-6.json` | 102371 | associations-repaymentSchedule | 7 | `11c137753e360b53` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-all-5.json` | 102580 | associations-all | 7 | `b114c822d3424c30` | no-reAmortize |
| `loans/loan-47/loan-47-detail-associations-repaymentSchedule-7.json` | 102604 | associations-repaymentSchedule | 7 | `b114c822d3424c30` | no-reAmortize |

#### loan 48 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

REJECTED reAmortize attempt(s): loans/loan-48/loan-48-reAmortize-response.json HTTP 403 (error.msg.loan.reamortize.not.allowed.on.charged.off)

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-48/loan-48-detail-associations-all-1.json` | 103616 | associations-all | 7 | `a12613e57ed9ef7f` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-all-2.json` | 103746 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-all-3.json` | 103794 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-1.json` | 103818 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-2.json` | 103842 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-all-4.json` | 103998 | associations-all | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-3.json` | 104022 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-4.json` | 104046 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-5.json` | 104178 | associations-repaymentSchedule | 3 | `c7b6dd6cb7a39a4c` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-6.json` | 104202 | associations-repaymentSchedule | 3 | `c7b6dd6cb7a39a4c` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-all-5.json` | 104356 | associations-all | 3 | `17e99f047f6989fd` | no-reAmortize |
| `loans/loan-48/loan-48-detail-associations-repaymentSchedule-7.json` | 104380 | associations-repaymentSchedule | 3 | `17e99f047f6989fd` | no-reAmortize |

#### loan 49 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

REJECTED reAmortize attempt(s): loans/loan-49/loan-49-reAmortize-response.json HTTP 403 (error.msg.loan.reamortize.not.allowed.on.charged.off)

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-49/loan-49-detail-associations-all-1.json` | 105393 | associations-all | 7 | `a12613e57ed9ef7f` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-all-2.json` | 105523 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-all-3.json` | 105571 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-1.json` | 105595 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-2.json` | 105619 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-all-4.json` | 105775 | associations-all | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-3.json` | 105799 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-4.json` | 105823 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-5.json` | 105955 | associations-repaymentSchedule | 7 | `33f18338ae643545` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-6.json` | 105979 | associations-repaymentSchedule | 7 | `33f18338ae643545` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-all-5.json` | 106187 | associations-all | 7 | `a964685890ee3fe1` | no-reAmortize |
| `loans/loan-49/loan-49-detail-associations-repaymentSchedule-7.json` | 106211 | associations-repaymentSchedule | 7 | `a964685890ee3fe1` | no-reAmortize |

#### loan 50 — MNT

reAmortize calls (source line): -; reAmortize transactions: -

REJECTED reAmortize attempt(s): loans/loan-50/loan-50-reAmortize-response.json HTTP 403 (error.msg.loan.reamortize.not.allowed.on.charged.off)

| read-back file | source line | kind | periods | periods sha256 | phase |
| --- | ---: | --- | ---: | --- | --- |
| `loans/loan-50/loan-50-detail-associations-all-1.json` | 107224 | associations-all | 7 | `a12613e57ed9ef7f` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-all-2.json` | 107354 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-all-3.json` | 107402 | associations-all | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-1.json` | 107426 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-2.json` | 107450 | associations-repaymentSchedule | 7 | `019706d8130347f4` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-all-4.json` | 107606 | associations-all | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-3.json` | 107630 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-4.json` | 107654 | associations-repaymentSchedule | 7 | `ea93f49b3bc6f96c` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-5.json` | 107786 | associations-repaymentSchedule | 7 | `11c137753e360b53` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-6.json` | 107810 | associations-repaymentSchedule | 7 | `11c137753e360b53` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-all-5.json` | 108019 | associations-all | 7 | `b114c822d3424c30` | no-reAmortize |
| `loans/loan-50/loan-50-detail-associations-repaymentSchedule-7.json` | 108043 | associations-repaymentSchedule | 7 | `b114c822d3424c30` | no-reAmortize |

### Findings

- target type(s) with NO journal-entry legs at all: loanTransactionType.reAmortize.  The re-amortization command succeeds and rewrites the schedule, but the reAmortize transaction itself posts no journal entry.
- 49 target transaction(s) in the read-backs have NO journal-entry legs: loan 4 tx L12, loan 6 tx L19, loan 7 tx L23, loan 7 tx L25, loan 8 tx L29, loan 9 tx L34, loan 10 tx L40, loan 11 tx L44, loan 12 tx L49, loan 12 tx L50, loan 13 tx L54, loan 13 tx L55, loan 14 tx L60, loan 14 tx L63, loan 15 tx L69, loan 15 tx L70, loan 16 tx L76, loan 17 tx L82, loan 18 tx L89, loan 19 tx L97, loan 20 tx L105, loan 21 tx L110, loan 22 tx L118, loan 23 tx L123, loan 24 tx L130, loan 25 tx L137, loan 26 tx L145, loan 27 tx L150, loan 28 tx L158, loan 29 tx L163, loan 30 tx L172, loan 31 tx L181, loan 31 tx L183, loan 32 tx L190, loan 32 tx L191, loan 33 tx L199, loan 33 tx L201, loan 34 tx L209, loan 34 tx L210, loan 36 tx L218, loan 37 tx L224, loan 38 tx L231, loan 39 tx L236, loan 40 tx L241, loan 41 tx L248, loan 42 tx L254, loan 43 tx L259, loan 44 tx L271, loan 45 tx L278.
- `loanTransactionType.reAmortize`: 49 transaction(s) across 40 loan(s); loans with NO captured reAmortize transaction: 1, 2, 3, 5, 35, 46, 47, 48, 49, 50.
- reAmortize commands: 44 SUCCESSFUL call(s) and 6 REJECTED attempt(s) on loan(s) 34, 46, 47, 48, 49, 50.  Rejection reasons: error.msg.loan.reamortize.not.allowed.on.charged.off (loan(s) 46, 47, 48, 49, 50); error.msg.loan.reamortize.reamortize.transaction.interest.handling.strategy.missmatch (loan(s) 34).  Those attempts did NOT rewrite the schedule and are not phase boundaries.

Other observations from the join:

- `loanTransactionType.reAmortize`: NO legs at all — the re-amortization transaction itself posts no journal entry (the schedule rewrite is not a cash posting).
- `loanTransactionType.repayment`: 257 legs on 91 transaction(s) / 46 loan(s); 10 legs on charged-off loan(s) (46, 47, 48, 49, 50); 247 on not-charged-off loan(s) (4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50).
- `loanTransactionType.accrual`: 82 legs on 36 transaction(s) / 36 loan(s); 0 legs on charged-off loan(s) (-); 82 on not-charged-off loan(s) (8, 9, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50).
- `loanTransactionType.chargeOff`: 20 legs on 5 transaction(s) / 5 loan(s); 0 legs on charged-off loan(s) (-); 20 on not-charged-off loan(s) (46, 47, 48, 49, 50).

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

