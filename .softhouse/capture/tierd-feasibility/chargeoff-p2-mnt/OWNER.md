# OWNER — Tier D `LoanChargeOff-Part2.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD26-DJ)

Whole-file replay of `LoanChargeOff-Part2.feature` (50 Gherkin scenarios: 48 executed, 2 `@Skip` excluded by the runner) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 48 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the charge-off family the earlier captures under-sampled: charge-off with zero-interest behaviour and interest recalculation, repayments and backdated repayments AFTER a charge-off, waivers, accrual exclusion and the undo-charge-off steps. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction — using ONLY each loan's LATEST read-back, so a charge-off later undone does NOT count — and gives each required arm's DISTINCT leg shapes. The required arms are `repayment`, `chargeOff`, `accrual`, `accrualAdjustment`, `waiver` and `recoveryRepayment`; a type with no legs is reported as a finding.

## Provenance

OH-TIERD26-DJ ran the rig, the replay (48/48 executed), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-chargeoff-p2-mnt.sh` | the exact replay driver |
| `replay-chargeoff-p2-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 48 PASSED scenarios |
| `manifest-chargeoff-p2.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-chargeoff-p2.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 48/48 HTTP 200 |
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

**50 scenarios, 48 PASSED, 0 FAILED; 1263 steps (1263 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3315 | 5 | PASSED | 1 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` |
| 2 | C3337 | 66 | PASSED | 2 | `LP2_ADV_CUSTOM_PAYMENT_ALLOC_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE` |
| 3 | C3338 | 124 | PASSED | 3 | `LP2_ADV_CUSTOM_PAYMENT_ALLOC_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE` |
| 4 | C3326 | 203 | PASSED | 4 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1` |
| 5 | C3337 | 237 | PASSED | 5 | `LP2_ADV_CUSTOM_PAYMENT_ALLOC_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE` |
| 6 | C3326 | 295 | PASSED | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1` |
| 7 | C3339 | 329 | PASSED | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 8 | C3340 | 386 | PASSED | 8 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 9 | C3341 | 443 | PASSED | 9 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 10 | C3342 | 500 | PASSED | 10 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 11 | C3343 | 563 | PASSED | 11 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 12 | C3344 | 620 | PASSED | 12 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 13 | C3345 | 699 | PASSED | 13 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 14 | C3346 | 778 | PASSED | 14 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 15 | C3347 | 858 | PASSED | 15 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 16 | C3348 | 918 | PASSED | 16 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 17 | C3349 | 977 | PASSED | 17 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 18 | C3412 | 1038 | PASSED | 18 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 19 | C3413 | 1097 | PASSED | 19 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 20 | C3350 | 1137 | PASSED | 20 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 21 | C3351 | 1266 | PASSED | 21 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 22 | C3376 | 1325 | PASSED | 22 | `_(default progressive)_` |
| 23 | C3352 | 1381 | PASSED | 23 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 24 | C3353 | 1461 | PASSED | 24 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 25 | C3354 | 1521 | PASSED | 25 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 26 | C3355 | 1581 | PASSED | 26 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 27 | C3356 | 1659 | PASSED | 27 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 28 | C3357 | 1738 | PASSED | 28 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 29 | C3358 | 1823 | PASSED | 29 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 30 | C3359 | 1904 | PASSED | 30 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 31 | C3360 | 1983 | SKIPPED | -1 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 32 | C3361 | 2046 | SKIPPED | -1 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 33 | C3362 | 2128 | PASSED | 31 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ALLOW_PARTIAL_PERIOD` |
| 34 | C3363 | 2208 | PASSED | 32 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 35 | C3364 | 2265 | PASSED | 33 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 36 | C3365 | 2322 | PASSED | 34 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 37 | C3366 | 2379 | PASSED | 35 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 38 | C3367 | 2442 | PASSED | 36 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 39 | C3368 | 2499 | PASSED | 37 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 40 | C3369 | 2577 | PASSED | 38 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 41 | C3370 | 2655 | PASSED | 39 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 42 | C3371 | 2735 | PASSED | 40 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 43 | C3372 | 2795 | PASSED | 41 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 44 | C3373 | 2854 | PASSED | 42 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 45 | C3414 | 2915 | PASSED | 43 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 46 | C3415 | 2974 | PASSED | 44 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 47 | C3374 | 3014 | PASSED | 45 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 48 | C3375 | 3143 | PASSED | 46 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF` |
| 49 | C3377 | 3202 | PASSED | 47 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR` |
| 50 | C3378 | 3261 | PASSED | 48 | `_(default progressive)_` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 48 loans, 1407 bodies kept under `loans/`, each body sha256-pinned in `manifest-chargeoff-p2.json`; the FAILED scenarios' loans are not committed (`manifest-chargeoff-p2-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **48/48 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 853 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 9 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP2_ADV_CUSTOM_PAYMENT_ALLOC_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ALLOW_PARTIAL_PERIOD.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR.json`
- `create-request-LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **853 legs, 7 types, 152 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction with a LOWER transaction id than the leg's transaction.** (The rule is transaction id order, not date order.) `charged-off latest` = the loan `chargedOff` flag in its CHRONOLOGICALLY LATEST read-back, so a charge-off later undone does not count. The read-backs are numbered PER ENDPOINT (`...-1`, `...-2`, ...), so the file suffix is not a cross-endpoint chronology; the LATEST read-back is the one with the highest manifest `source_line`. That distinction is load-bearing here: for loans 4 and 6 the last transaction-bearing read-back predates the charge-off, so the flag must come from the later `repaymentSchedule` read-backs, which say `chargedOff=true`; and for the undo loans (3, 22, 23, 48) it is the latest read-back's `chargedOff=false` (or dropped chargeOff) that excludes the undone charge-off, while loans 12, 13, 28, 29, 37 and 38 are re-charged off under a NEWER transaction id and stay charged off.

The charge-off transaction id is missing from every read-back for **loans 4, 6, 17, 42** (the feature charged those loans off AFTER their last transactions read-back) and for the re-charged loans it is superseded. The charge-off command response names the id (`resourceId`, see `chargeoff_supplement` in the join), and an id absent from the read-backs is injected as the `chargeOff` transaction so the arm type is complete. It is flagged as a supplement, never as a read-back, and is NOT used for the charged-off rule.

The **Credit Balance Refund** step of the feature posts as `loanTransactionType.creditBalanceRefund` (12 legs, loans 20 and 45, listed in the all-types table); `loanTransactionType.payoutRefund` does not appear at all.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `loanTransactionType.chargeOff` | 275 | 0 | - |
| `loanTransactionType.repayment` | 212 | 17 | 1, 12, 14, 28, 30, 37, 39 |
| `(unmapped)` | 152 | 0 | - |
| `loanTransactionType.accrual` | 102 | 2 | 13 |
| `loanTransactionType.disbursement` | 96 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 12 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 4 | 2 | 28 |

### The six required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.repayment` | True | 212 | 66 | 1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 | 17 | 1, 12, 14, 28, 30, 37, 39 | 195 | 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47 |
| `loanTransactionType.chargeOff` | True | 275 | 54 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 | 0 | - | 275 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 |
| `loanTransactionType.accrual` | True | 102 | 51 | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 | 2 | 13 | 100 | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 |
| `loanTransactionType.accrualAdjustment` | True | 4 | 2 | 12, 28 | 2 | 28 | 2 | 12 |
| `loanTransactionType.waiver` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.recoveryRepayment` | False | 0 | 0 | - | 0 | - | 0 | - |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.waiver, loanTransactionType.recoveryRepayment.  The arm was NOT exercised by this feature.

**FINDING:** chargeOff supplement (NOT a read-back): loan 4 tx L54, loan 6 tx L98, loan 17 tx L151, loan 42 tx L273.  For these loans the feature charged the loan off AFTER its last read-back, so the charge-off transaction id is in no read-back; the charge-off command response (`charge-off-response.json` `resourceId`) is the evidence and it is injected as the `chargeOff` transaction so the arm type is complete.  It is NOT used for the charged-off rule (which reads the latest read-back).

**FINDING:** undone charge-off(s): loan 3 L12 (listed as manuallyReversed/reversed in the LATEST read-back), loan 12 L125 (present in an earlier read-back, absent from the LATEST read-back), loan 13 L132 (present in an earlier read-back, absent from the LATEST read-back), loan 22 L177 (listed as manuallyReversed/reversed in the LATEST read-back), loan 23 L181 (listed as manuallyReversed/reversed in the LATEST read-back), loan 28 L204 (present in an earlier read-back, absent from the LATEST read-back), loan 29 L211 (present in an earlier read-back, absent from the LATEST read-back), loan 37 L249 (present in an earlier read-back, absent from the LATEST read-back), loan 38 L255 (present in an earlier read-back, absent from the LATEST read-back), loan 48 L303 (listed as manuallyReversed/reversed in the LATEST read-back).  Each is excluded from the charged-off dimension because it does not appear as a NON-REVERSED chargeOff in the loan's latest read-back; the evidence and the transactions posted before and after the undo are listed under `undone_chargeoffs` and in OWNER.md.

**FINDING:** (unmapped): 152 swept legs on 76 transactions have no read-back type: loan 4 (38 legs, L16-L53); that loan's chargeOff is L54; loan 6 (38 legs, L60-L97); that loan's chargeOff is L98.  These are postings made AFTER the loan read-backs were last captured (predominantly the daily accruals), so they cannot be typed from a read-back.  They are a join gap, reported as a finding; they are NOT missing required arms.

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:6` | 1, 5, 6 | CREDIT 1, CREDIT 5, DEBIT 6 | 56 | 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47 | 7 | L100 | P 1643 / I 58 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:15 DEBIT:6` | 6, 15 | CREDIT 15, DEBIT 6 | 4 | 1, 14, 30, 39 | 1 | L4 | P 31285 / I 2167 / F 10548 / Pen 6000 / OP 0 / UI 0 | 9 |
| `CREDIT:1 CREDIT:5 CREDIT:6 DEBIT:1 DEBIT:5 DEBIT:6` | 1, 5, 6 | CREDIT 1, CREDIT 5, CREDIT 6, DEBIT 1, DEBIT 5, DEBIT 6 | 3 | 13, 29, 38 | 13 | L130 | P 1643 / I 58 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |
| `CREDIT:1 CREDIT:5 CREDIT:6 CREDIT:17 DEBIT:1 DEBIT:5 DEBIT:6 DEBIT:17` | 1, 5, 6, 17 | CREDIT 1, CREDIT 5, CREDIT 6, CREDIT 17, DEBIT 1, DEBIT 5, DEBIT 6, DEBIT 17 | 2 | 20, 45 | 20 | L166 | P 1690 / I 10 / F 0 / Pen 0 / OP 300 / UI 0 | 9 |
| `CREDIT:5 DEBIT:6` | 5, 6 | CREDIT 5, DEBIT 6 | 1 | 21 | 21 | L172 | P 1701 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 9 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 CREDIT:5 DEBIT:6`: loan 7, tx L100, P 1643 / I 58 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 56 transaction(s) across loan(s) 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47.
- shape `CREDIT:15 DEBIT:6`: loan 1, tx L4, P 31285 / I 2167 / F 10548 / Pen 6000 / OP 0 / UI 0, paymentType id 9 — 4 transaction(s) across loan(s) 1, 14, 30, 39.
- shape `CREDIT:1 CREDIT:5 CREDIT:6 DEBIT:1 DEBIT:5 DEBIT:6`: loan 13, tx L130, P 1643 / I 58 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 3 transaction(s) across loan(s) 13, 29, 38.
- shape `CREDIT:1 CREDIT:5 CREDIT:6 CREDIT:17 DEBIT:1 DEBIT:5 DEBIT:6 DEBIT:17`: loan 20, tx L166, P 1690 / I 10 / F 0 / Pen 0 / OP 300 / UI 0, paymentType id 9 — 2 transaction(s) across loan(s) 20, 45.
- shape `CREDIT:5 DEBIT:6`: loan 21, tx L172, P 1701 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 9 — 1 transaction(s) across loan(s) 21.

#### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 CREDIT:5 DEBIT:13 DEBIT:19` | 1, 5, 13, 19 | CREDIT 1, CREDIT 5, DEBIT 13, DEBIT 19 | 35 | 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 20, 21, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 42, 45, 46, 47 | 2 | L8 | P 25000 / I 523 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:1 CREDIT:5 CREDIT:13 CREDIT:19 DEBIT:1 DEBIT:5 DEBIT:13 DEBIT:19` | 1, 5, 13, 19 | CREDIT 1, CREDIT 5, CREDIT 13, CREDIT 19, DEBIT 1, DEBIT 5, DEBIT 13, DEBIT 19 | 10 | 3, 12, 13, 22, 23, 28, 29, 37, 38, 48 | 3 | L12 | P 25000 / I 523 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:1 CREDIT:5 DEBIT:11 DEBIT:13 DEBIT:19` | 1, 5, 11, 13, 19 | CREDIT 1, CREDIT 5, DEBIT 11, DEBIT 13, DEBIT 19 | 7 | 1, 15, 16, 18, 40, 41, 43 | 1 | L3 | P 100000 / I 5475 / F 10548 / Pen 6000 / OP 0 / UI 0 | - |
| `CREDIT:1 CREDIT:5 CREDIT:11 CREDIT:13 CREDIT:19 DEBIT:1 DEBIT:5 DEBIT:11 DEBIT:13 DEBIT:19` | 1, 5, 11, 13, 19 | CREDIT 1, CREDIT 5, CREDIT 11, CREDIT 13, CREDIT 19, DEBIT 1, DEBIT 5, DEBIT 11, DEBIT 13, DEBIT 19 | 2 | 17, 42 | 17 | L151 | - | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 CREDIT:5 DEBIT:13 DEBIT:19`: loan 2, tx L8, P 25000 / I 523 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 35 transaction(s) across loan(s) 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 20, 21, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 42, 45, 46, 47.
- shape `CREDIT:1 CREDIT:5 CREDIT:13 CREDIT:19 DEBIT:1 DEBIT:5 DEBIT:13 DEBIT:19`: loan 3, tx L12, P 25000 / I 523 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 10 transaction(s) across loan(s) 3, 12, 13, 22, 23, 28, 29, 37, 38, 48.
- shape `CREDIT:1 CREDIT:5 DEBIT:11 DEBIT:13 DEBIT:19`: loan 1, tx L3, P 100000 / I 5475 / F 10548 / Pen 6000 / OP 0 / UI 0, paymentType id - — 7 transaction(s) across loan(s) 1, 15, 16, 18, 40, 41, 43.
- shape `CREDIT:1 CREDIT:5 CREDIT:11 CREDIT:13 CREDIT:19 DEBIT:1 DEBIT:5 DEBIT:11 DEBIT:13 DEBIT:19`: loan 17, tx L151, -, paymentType id - — 2 transaction(s) across loan(s) 17, 42.

#### `loanTransactionType.accrual`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:7 DEBIT:1` | 1, 7 | CREDIT 7, DEBIT 1 | 51 | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48 | 1 | L2 | P 0 / I 3696 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:7 DEBIT:1`: loan 1, tx L2, P 0 / I 3696 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 51 transaction(s) across loan(s) 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48.

#### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 DEBIT:7` | 1, 7 | CREDIT 1, DEBIT 7 | 2 | 12, 28 | 12 | L126 | P 0 / I 9 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 DEBIT:7`: loan 12, tx L126, P 0 / I 9 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 12, 28.

#### `loanTransactionType.waiver`

_No legs for this type — see the finding above._

#### `loanTransactionType.recoveryRepayment`

_No legs for this type — see the finding above._

### Undone charge-offs (transactions before / after the undo)

A charge-off is UNDONE when the loan's LATEST read-back marks it `manuallyReversed`/`reversed`, or when an earlier read-back listed it and the latest read-back dropped it entirely (it vanished). Each such charge-off is EXCLUDED from the charged-off dimension. The before/after transactions are read from the loan's latest transaction-bearing read-back — its final state.

#### loan 3 — `L12` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-3/loan-3-detail-associations-transactions-5.json` (manifest source_line 26528); ordering read-back `loans/loan-3/loan-3-detail-associations-transactions-5.json` (source_line 26528).
- transactions posted BEFORE the undo: L9 loanTransactionType.disbursement 25000, L10 loanTransactionType.accrual 7, L11 loanTransactionType.accrual 7
- the undone charge-off: `L12`
- transactions posted AFTER the undo: L13 loanTransactionType.accrual 14, L14 loanTransactionType.accrual 7

#### loan 12 — `L125` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-12/loan-12-detail-associations-transactions-3.json` (manifest source_line 39646); ordering read-back `loans/loan-12/loan-12-detail-associations-transactions-5.json` (source_line 39795).
- transactions posted BEFORE the undo: L122 loanTransactionType.disbursement 10000, L123 loanTransactionType.repayment 1701, L124 loanTransactionType.accrual 154
- the undone charge-off: `L125`
- transactions posted AFTER the undo: L126 loanTransactionType.accrualAdjustment 9, L127 loanTransactionType.chargeOff 6743, L128 loanTransactionType.repayment 1701

#### loan 13 — `L132` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-13/loan-13-detail-associations-transactions-3.json` (manifest source_line 41244); ordering read-back `loans/loan-13/loan-13-detail-associations-transactions-6.json` (source_line 41417).
- transactions posted BEFORE the undo: L129 loanTransactionType.disbursement 10000, L130 loanTransactionType.repayment 1701, L131 loanTransactionType.accrual 105
- the undone charge-off: `L132`
- transactions posted AFTER the undo: L133 loanTransactionType.chargeOff 10114, L134 loanTransactionType.accrual 9

#### loan 22 — `L177` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-22/loan-22-detail-associations-transactions-3.json` (manifest source_line 56160); ordering read-back `loans/loan-22/loan-22-detail-associations-transactions-3.json` (source_line 56160).
- transactions posted BEFORE the undo: L175 loanTransactionType.disbursement 10000, L176 loanTransactionType.accrual 85
- the undone charge-off: `L177`
- transactions posted AFTER the undo: _(none)_

#### loan 23 — `L181` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-23/loan-23-detail-associations-transactions-6.json` (manifest source_line 57813); ordering read-back `loans/loan-23/loan-23-detail-associations-transactions-6.json` (source_line 57813).
- transactions posted BEFORE the undo: L178 loanTransactionType.disbursement 10000, L179 loanTransactionType.repayment 1701, L180 loanTransactionType.accrual 107
- the undone charge-off: `L181`
- transactions posted AFTER the undo: _(none)_

#### loan 28 — `L204` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-28/loan-28-detail-associations-transactions-5.json` (manifest source_line 66119); ordering read-back `loans/loan-28/loan-28-detail-associations-transactions-7.json` (source_line 66267).
- transactions posted BEFORE the undo: L201 loanTransactionType.disbursement 10000, L202 loanTransactionType.repayment 1701, L203 loanTransactionType.accrual 154
- the undone charge-off: `L204`
- transactions posted AFTER the undo: L205 loanTransactionType.chargeOff 6743, L206 loanTransactionType.accrualAdjustment 9, L207 loanTransactionType.repayment 1701

#### loan 29 — `L211` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-29/loan-29-detail-associations-transactions-5.json` (manifest source_line 67927); ordering read-back `loans/loan-29/loan-29-detail-associations-transactions-7.json` (source_line 68076).
- transactions posted BEFORE the undo: L208 loanTransactionType.disbursement 10000, L209 loanTransactionType.repayment 1701, L210 loanTransactionType.accrual 105
- the undone charge-off: `L211`
- transactions posted AFTER the undo: L212 loanTransactionType.accrual 9, L213 loanTransactionType.chargeOff 10114

#### loan 37 — `L249` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-37/loan-37-detail-associations-transactions-3.json` (manifest source_line 80572); ordering read-back `loans/loan-37/loan-37-detail-associations-transactions-5.json` (source_line 80721).
- transactions posted BEFORE the undo: L246 loanTransactionType.disbursement 10000, L247 loanTransactionType.repayment 1701, L248 loanTransactionType.accrual 145
- the undone charge-off: `L249`
- transactions posted AFTER the undo: L250 loanTransactionType.chargeOff 6743, L251 loanTransactionType.repayment 1701

#### loan 38 — `L255` — present in an earlier read-back, absent from the LATEST read-back

- evidence: `loans/loan-38/loan-38-detail-associations-transactions-3.json` (manifest source_line 82171); ordering read-back `loans/loan-38/loan-38-detail-associations-transactions-6.json` (source_line 82344).
- transactions posted BEFORE the undo: L252 loanTransactionType.disbursement 10000, L253 loanTransactionType.repayment 1701, L254 loanTransactionType.accrual 105
- the undone charge-off: `L255`
- transactions posted AFTER the undo: L256 loanTransactionType.chargeOff 10105

#### loan 48 — `L303` — listed as manuallyReversed/reversed in the LATEST read-back

- evidence: `loans/loan-48/loan-48-detail-associations-transactions-3.json` (manifest source_line 98665); ordering read-back `loans/loan-48/loan-48-detail-associations-transactions-3.json` (source_line 98665).
- transactions posted BEFORE the undo: L301 loanTransactionType.disbursement 10000, L302 loanTransactionType.accrual 81
- the undone charge-off: `L303`
- transactions posted AFTER the undo: _(none)_

### Per-loan currency and charge-off state

| loan | currency | charged-off latest read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- |
| 1 | MNT | True | L3@2024-02-28 |
| 2 | MNT | True | L8@2024-06-03 |
| 3 | MNT | False | - |
| 4 | MNT | True | - |
| 5 | MNT | True | L58@2024-06-03 |
| 6 | MNT | True | - |
| 7 | MNT | True | L102@2024-03-01 |
| 8 | MNT | True | L106@2024-02-29 |
| 9 | MNT | True | L110@2024-02-14 |
| 10 | MNT | True | L117@2024-07-15 |
| 11 | MNT | True | L121@2024-03-31 |
| 12 | MNT | True | L127@2024-03-31 |
| 13 | MNT | True | L133@2024-02-29 |
| 14 | MNT | True | L138@2024-02-29 |
| 15 | MNT | True | L143@2024-02-29 |
| 16 | MNT | True | L147@2024-02-29 |
| 17 | MNT | True | L153@2024-02-29 |
| 18 | MNT | True | L157@2024-02-29 |
| 19 | MNT | False | - |
| 20 | MNT | True | L170@2024-07-15 |
| 21 | MNT | True | L174@2024-02-29 |
| 22 | MNT | False | - |
| 23 | MNT | False | - |
| 24 | MNT | True | L185@2024-02-29 |
| 25 | MNT | True | L189@2024-02-14 |
| 26 | MNT | True | L196@2024-07-15 |
| 27 | MNT | True | L200@2024-03-31 |
| 28 | MNT | True | L205@2024-03-31 |
| 29 | MNT | True | L213@2024-02-29 |
| 30 | MNT | True | L217@2024-02-29 |
| 31 | MNT | True | L222@2024-04-02 |
| 32 | MNT | True | L226@2024-03-01 |
| 33 | MNT | True | L230@2024-02-29 |
| 34 | MNT | True | L234@2024-02-14 |
| 35 | MNT | True | L241@2024-07-15 |
| 36 | MNT | True | L245@2024-03-31 |
| 37 | MNT | True | L250@2024-03-31 |
| 38 | MNT | True | L256@2024-02-29 |
| 39 | MNT | True | L260@2024-02-29 |
| 40 | MNT | True | L265@2024-02-29 |
| 41 | MNT | True | L269@2024-02-29 |
| 42 | MNT | True | L275@2024-02-29 |
| 43 | MNT | True | L279@2024-02-29 |
| 44 | MNT | False | - |
| 45 | MNT | True | L292@2024-07-15 |
| 46 | MNT | True | L296@2024-02-29 |
| 47 | MNT | True | L300@2024-02-29 |
| 48 | MNT | False | - |

### Findings

- target type(s) with NO journal-entry legs at all: loanTransactionType.waiver, loanTransactionType.recoveryRepayment.  The arm was NOT exercised by this feature.
- chargeOff supplement (NOT a read-back): loan 4 tx L54, loan 6 tx L98, loan 17 tx L151, loan 42 tx L273.  For these loans the feature charged the loan off AFTER its last read-back, so the charge-off transaction id is in no read-back; the charge-off command response (`charge-off-response.json` `resourceId`) is the evidence and it is injected as the `chargeOff` transaction so the arm type is complete.  It is NOT used for the charged-off rule (which reads the latest read-back).
- undone charge-off(s): loan 3 L12 (listed as manuallyReversed/reversed in the LATEST read-back), loan 12 L125 (present in an earlier read-back, absent from the LATEST read-back), loan 13 L132 (present in an earlier read-back, absent from the LATEST read-back), loan 22 L177 (listed as manuallyReversed/reversed in the LATEST read-back), loan 23 L181 (listed as manuallyReversed/reversed in the LATEST read-back), loan 28 L204 (present in an earlier read-back, absent from the LATEST read-back), loan 29 L211 (present in an earlier read-back, absent from the LATEST read-back), loan 37 L249 (present in an earlier read-back, absent from the LATEST read-back), loan 38 L255 (present in an earlier read-back, absent from the LATEST read-back), loan 48 L303 (listed as manuallyReversed/reversed in the LATEST read-back).  Each is excluded from the charged-off dimension because it does not appear as a NON-REVERSED chargeOff in the loan's latest read-back; the evidence and the transactions posted before and after the undo are listed under `undone_chargeoffs` and in OWNER.md.
- (unmapped): 152 swept legs on 76 transactions have no read-back type: loan 4 (38 legs, L16-L53); that loan's chargeOff is L54; loan 6 (38 legs, L60-L97); that loan's chargeOff is L98.  These are postings made AFTER the loan read-backs were last captured (predominantly the daily accruals), so they cannot be typed from a read-back.  They are a join gap, reported as a finding; they are NOT missing required arms.
- `(unmapped)` leg shapes (152 legs / 76 transaction(s) across loan(s) 4, 6, all with no read-back type; per-loan id ranges are in the finding above): CREDIT:7 DEBIT:1. These are post-read-back daily accrual legs — a join gap, not a missing required arm.

Other observations from the join:

- `loanTransactionType.repayment`: 212 legs on 66 transaction(s) / 41 loan(s); 17 legs on charged-off loan(s) (1, 12, 14, 28, 30, 37, 39); 195 on not-charged-off loan(s) (7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47).
- `loanTransactionType.chargeOff`: 275 legs on 54 transaction(s) / 46 loan(s); 0 legs on charged-off loan(s) (-); 275 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48).
- `loanTransactionType.accrual`: 102 legs on 51 transaction(s) / 44 loan(s); 2 legs on charged-off loan(s) (13); 100 on not-charged-off loan(s) (1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 48).
- `loanTransactionType.accrualAdjustment`: 4 legs on 2 transaction(s) / 2 loan(s); 2 legs on charged-off loan(s) (28); 2 on not-charged-off loan(s) (12).
- `loanTransactionType.waiver`: NO legs at all — the arm was NOT exercised by this feature.
- `loanTransactionType.recoveryRepayment`: NO legs at all — the arm was NOT exercised by this feature.

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

