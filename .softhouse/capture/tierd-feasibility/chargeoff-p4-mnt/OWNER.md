# OWNER — Tier D `LoanChargeOff-Part4.feature` MNT capture **plus a full journal-entry sweep** (OH-TIERD23-DC)

Whole-file replay of `LoanChargeOff-Part4.feature` (14 scenarios) against the throwaway reference oracle, tenant `tierd` (Asia/Ulaanbaatar, rounding mode 4 HALF_UP, currency MNT), with the Feign capture on, **and then — while the throwaway was still up — one bounded `GET /journalentries?loanId=<id>&limit=-1` for every one of the 14 loans the replay created.** Capture only: no vector, no drive, no `.go`. Money in this file and in the join is integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies under `journalentries-sweep/` and `loans/` keep the decimal major units the oracle emitted, unchanged.

The target is the INTEREST-REFUND / merchant-issued-refund / repayment posting family that follows a charge-off: `interestRefund`, `merchantIssuedRefund` and `payoutRefund` (the merchant-issued refunds, normal / payout / fraud variants), the `repayment` legs, the `accrualAdjustment` recognition legs and the `chargeOff` legs themselves. The feature is graded on whether it adds the interest-refund postings the earlier captures only saw on non-charged-off loans. This capture joins every swept leg to its transaction TYPE and to the loan's CHARGED-OFF state at that transaction, and gives each required arm's DISTINCT leg shapes.

## Provenance

OH-TIERD23-DC ran the rig, the replay (14/14), the extraction, the sweep, the product mappings, the teardown and the type join over the captured JSON. Every command ran in the FOREGROUND with a bound (curl `--max-time 30`; the copied run script for Gradle). No background job, no `&`, no `jobs`, no `wait`, no `sleep > 60`. The throwaway is DOWN (`teardown-isolation.txt`). Nothing was written into `/Users/buv/fineract`; the replay was done in the disposable copy `/Users/buv/fineract-tierd`. PostgreSQL only; no Oracle.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file |
| `replay-result-table.md` / `scenario-results.json` | per-scenario PASSED/FAILED, loan mapping, steps |
| `run-chargeoff-p4-mnt.sh` | the exact replay driver |
| `replay-chargeoff-p4-mnt.log` | raw cucumber/Gradle replay log |
| `loans/loan-<id>/` | per-loan read-backs of the 14 PASSED scenarios |
| `manifest-chargeoff-p4.json` / `-passed.json` | all extracted bodies with sha256 and `committed` flag |
| `summary-chargeoff-p4.json` | extractor totals and per-loan counts |
| `journalentries-sweep/loan-<id>.json` | verbatim `GET /journalentries?loanId=<id>&limit=-1` bodies, 14/14 HTTP 200 |
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

**14 scenarios, 14 PASSED, 0 FAILED; 503 steps (503 passed, 0 skipped, 0 failed).** Recorded, not diagnosed.

| # | TestRailId | feature line | result | loan | product |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | C3622 | 5 | PASSED | 1 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_REFUND_FULL` |
| 2 | C3623 | 100 | PASSED | 2 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF` |
| 3 | C3624 | 195 | PASSED | 3 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ACC_MATUR_CHARGE_OFF` |
| 4 | C3643 | 281 | PASSED | 4 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON` |
| 5 | C3644 | 371 | PASSED | 5 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON_INTEREST_RECALC` |
| 6 | C3719 | 461 | PASSED | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 7 | C3757 | 568 | PASSED | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 8 | C3988 | 657 | PASSED | 8 | `LP2_ADV_PYMNT_INTEREST_RECOGNITION_DISBURSEMENT_DAILY_EMI_360_30_ACCRUAL_ACTIVITY` |
| 9 | C4016 | 683 | PASSED | 9 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_ZERO_CHARGE_OFF` |
| 10 | C4017 | 849 | PASSED | 10 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_ZERO_CHARGE_OFF` |
| 11 | C4153 | 1018 | PASSED | 11 | `LP2_ADV_PYMNT_360_30_ZERO_INTEREST_CHARGE_OFF_ACCRUAL_ACTIVITY` |
| 12 | C4228 | 1091 | PASSED | 12 | `LP2_ADV_PYMNT_360_30_ZERO_INTEREST_CHARGE_OFF_ACCRUAL_ACTIVITY` |
| 13 | C4579 | 1147 | PASSED | 13 | `LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL` |
| 14 | C4580 | 1211 | PASSED | 14 | `LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL` |

## Extraction (step 2)

Extracted with `bin/extract.py` and the copied `organize.py`: 14 loans, 620 bodies kept under `loans/`, each body sha256-pinned in `manifest-chargeoff-p4.json`; the FAILED scenarios' loans are not committed (`manifest-chargeoff-p4-passed.json`). Attribution: validated.

## The sweep (step 3)

For every loan id the replay created, one bounded read:

```
curl -sk --max-time 30 -u mifos:password -H 'Fineract-Platform-TenantId: tierd' \
  'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'
```

**Port 8444, tenant `tierd`, the THROWAWAY only — never 8443, never tenant `gerege` or `default`.** A GET only; no write. Result: **14/14 HTTP 200, 0 curl failures, 0 JSON-invalid bodies, 800 legs total**, each body saved verbatim and sha256-recorded in `journalentries-sweep-manifest.json` with its exact URL.

## Product mappings (step 4)

The copied `extract-product-mappings.py` pulled the accepted `createLoanProduct` bodies for the 10 distinct products this feature's loans use, sha256-pinned in `product-mappings/manifest.json`.

- `create-request-LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL.json`
- `create-request-LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_ZERO_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_360_30_ZERO_INTEREST_CHARGE_OFF_ACCRUAL_ACTIVITY.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_REFUND_FULL.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR.json`
- `create-request-LP2_ADV_PYMNT_INTEREST_RECOGNITION_DISBURSEMENT_DAILY_EMI_360_30_ACCRUAL_ACTIVITY.json`
- `create-request-LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ACC_MATUR_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF.json`
- `create-request-LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON.json`
- `create-request-LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON_INTEREST_RECALC.json`

## Teardown (step 5)

`down.sh` removed the throwaway `tierd-oracle-app` / `tierd-oracle-db` containers, the `tierd-oracle_default` network and every named volume; `docker ps` shows no `tierd-*`. The **standing** `gerege` and `default` tenants moved only by their normal churn: all **12/12** counters equal the preflight baseline (`teardown-isolation.txt`). PostgreSQL only; no Oracle.

## The type join — swept leg → transaction TYPE, CHARGED-OFF (step 6)

Each sweep leg carries only `transactionId` = `L<loanTransactionId>`. It is joined to its transaction type through the loan read-backs (`transactions[].id` → `transactions[].type.code`) and to the transaction's read-back portions and `paymentDetailData.paymentType`. **800 legs, 9 types, 370 unmatched.**

`charged_off` per leg = **a non-reversed `chargeOff` loan transaction with a LOWER transaction id than the leg's transaction.** (The rule is transaction id order, not date order.) `charged-off latest` = the loan `chargedOff` flag in its CHRONOLOGICALLY LATEST read-back, so a charge-off later undone does not count. The read-backs are numbered PER ENDPOINT (`...-1`, `...-2`, ...), so the file suffix is not a cross-endpoint chronology; the LATEST read-back is the one with the highest manifest `source_line`. That distinction is load-bearing here: the `detail-associations-all-*` stream stops before the charge-off for loans 9, 10, 11 and 12, so the flag must come from the later `transactions`/`repaymentSchedule` read-backs, which say `chargedOff=true`.

The charge-off transaction itself is missing from the read-backs for **loans 9, 10 and 12**: the feature charged those loans off AFTER their last transactions read-back. The charge-off command response names the id (`resourceId`, see `chargeoff_supplement` in the join), and that id is injected as the `chargeOff` transaction so the arm and the charged-off dimension are complete for all 14 loans. It is flagged as a supplement, never as a read-back.

The **Credit Balance Refund** step of the feature does not post as `payoutRefund`: it posts as `loanTransactionType.creditBalanceRefund` (14 legs, loans 13 and 14, listed in the all-types table). `payoutRefund` itself has NO legs, and is reported as a finding.

### Type × charged-off → legs → loans (all types)

| transaction type | legs | legs on charged-off loan | loans on charged-off |
| --- | ---: | ---: | --- |
| `(unmapped)` | 370 | 0 | - |
| `loanTransactionType.chargeOff` | 107 | 24 | 1, 2, 3, 4, 5 |
| `loanTransactionType.merchantIssuedRefund` | 87 | 39 | 1, 2, 3, 4, 5 |
| `loanTransactionType.repayment` | 76 | 16 | 4, 5, 6, 7, 8, 13 |
| `loanTransactionType.accrual` | 56 | 2 | 4 |
| `loanTransactionType.disbursement` | 44 | 0 | - |
| `loanTransactionType.interestRefund` | 36 | 0 | - |
| `loanTransactionType.creditBalanceRefund` | 14 | 0 | - |
| `loanTransactionType.accrualAdjustment` | 10 | 10 | 4, 5, 6, 7 |

### The six required arms

| type | present | legs | transactions | loans | legs on charged-off | loans on charged-off | legs on not-charged-off | loans on not-charged-off |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `loanTransactionType.interestRefund` | True | 36 | 16 | 9, 10, 13, 14 | 0 | - | 36 | 9, 10, 13, 14 |
| `loanTransactionType.merchantIssuedRefund` | True | 87 | 24 | 1, 2, 3, 4, 5, 9, 10, 13, 14 | 39 | 1, 2, 3, 4, 5 | 48 | 9, 10, 13, 14 |
| `loanTransactionType.payoutRefund` | False | 0 | 0 | - | 0 | - | 0 | - |
| `loanTransactionType.repayment` | True | 76 | 22 | 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14 | 16 | 4, 5, 6, 7, 8, 13 | 60 | 1, 2, 3, 6, 7, 11, 12, 13, 14 |
| `loanTransactionType.accrualAdjustment` | True | 10 | 5 | 4, 5, 6, 7 | 10 | 4, 5, 6, 7 | 0 | - |
| `loanTransactionType.chargeOff` | True | 107 | 19 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 | 24 | 1, 2, 3, 4, 5 | 83 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 |

**FINDING:** target type(s) with NO journal-entry legs at all: loanTransactionType.payoutRefund.  The arm was NOT exercised by this feature.

**FINDING:** chargeOff supplement (NOT a read-back): loan 9 tx L179, loan 10 tx L296, loan 12 tx L317.  For these loans the feature charged the loan off AFTER its last read-back, so the charge-off transaction id is in no read-back; the charge-off command response (`charge-off-response.json` `resourceId`) is the evidence and it is injected as the `chargeOff` transaction so the arm is complete.  The charge-off is non-reversed (no reversal transaction/command is captured for these loans).

**FINDING:** (unmapped): 370 swept legs on 185 transactions have no read-back type: loan 9 (92 legs, L84-L107, L109-L138, L140-L170, L172-L178); that loan's chargeOff is L179; loan 10 (92 legs, L201-L224, L226-L255, L257-L287, L289-L295); that loan's chargeOff is L296; loan 12 (1 legs, L316); that loan's chargeOff is L317.  These are postings made AFTER the loan read-backs were last captured (predominantly the daily accruals), so they cannot be typed from a read-back.  They are a join gap, reported as a finding; they are NOT missing required arms.

### Distinct leg shapes per required arm (account ids + sides, example, count)

#### `loanTransactionType.interestRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:2 DEBIT:5` | 2, 5 | CREDIT 2, DEBIT 5 | 10 | 9, 10 | 9 | L67 | P 0 / I 24 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:1 DEBIT:5` | 1, 5 | CREDIT 1, DEBIT 5 | 2 | 14 | 14 | L339 | P 44 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:16 DEBIT:5` | 5, 16 | CREDIT 16, DEBIT 5 | 2 | 13, 14 | 13 | L328 | P 0 / I 0 / F 0 / Pen 0 / OP 145 / UI 0 | - |
| `CREDIT:5 CREDIT:16 DEBIT:5 DEBIT:16` | 5, 16 | CREDIT 5, CREDIT 16, DEBIT 5, DEBIT 16 | 2 | 13, 14 | 13 | L320 | P 0 / I 0 / F 0 / Pen 0 / OP 144 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:2 DEBIT:5`: loan 9, tx L67, P 0 / I 24 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 10 transaction(s) across loan(s) 9, 10.
- shape `CREDIT:1 DEBIT:5`: loan 14, tx L339, P 44 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 14.
- shape `CREDIT:16 DEBIT:5`: loan 13, tx L328, P 0 / I 0 / F 0 / Pen 0 / OP 145 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 13, 14.
- shape `CREDIT:5 CREDIT:16 DEBIT:5 DEBIT:16`: loan 13, tx L320, P 0 / I 0 / F 0 / Pen 0 / OP 144 / UI 0, paymentType id - — 2 transaction(s) across loan(s) 13, 14.

#### `loanTransactionType.merchantIssuedRefund`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 DEBIT:8` | 1, 8 | CREDIT 1, DEBIT 8 | 12 | 9, 10, 14 | 9 | L68 | P 6119 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:1 CREDIT:2 CREDIT:16 DEBIT:8` | 1, 2, 8, 16 | CREDIT 1, CREDIT 2, CREDIT 16, DEBIT 8 | 3 | 4, 13, 14 | 4 | L28 | P 977 / I 49 / F 0 / Pen 0 / OP 48974 / UI 0 | 10 |
| `CREDIT:8 CREDIT:12 CREDIT:16 CREDIT:20 DEBIT:8 DEBIT:12 DEBIT:16 DEBIT:20` | 8, 12, 16, 20 | CREDIT 8, CREDIT 12, CREDIT 16, CREDIT 20, DEBIT 8, DEBIT 12, DEBIT 16, DEBIT 20 | 3 | 1, 2, 3 | 1 | L5 | P 80000 / I 1875 / F 0 / Pen 0 / OP 8125 / UI 0 | 10 |
| `CREDIT:1 CREDIT:2 CREDIT:8 CREDIT:16 DEBIT:1 DEBIT:2 DEBIT:8 DEBIT:16` | 1, 2, 8, 16 | CREDIT 1, CREDIT 2, CREDIT 8, CREDIT 16, DEBIT 1, DEBIT 2, DEBIT 8, DEBIT 16 | 2 | 13, 14 | 13 | L321 | P 12216 / I 45 / F 0 / Pen 0 / OP 2239 / UI 0 | 10 |
| `CREDIT:12 CREDIT:20 DEBIT:8` | 8, 12, 20 | CREDIT 12, CREDIT 20, DEBIT 8 | 2 | 1, 2 | 1 | L7 | P 88310 / I 1690 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:1 CREDIT:16 DEBIT:8` | 1, 8, 16 | CREDIT 1, CREDIT 16, DEBIT 8 | 1 | 5 | 5 | L36 | P 311 / I 0 / F 0 / Pen 0 / OP 49689 / UI 0 | 10 |
| `CREDIT:12 DEBIT:8` | 8, 12 | CREDIT 12, DEBIT 8 | 1 | 3 | 3 | L21 | P 90000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 DEBIT:8`: loan 9, tx L68, P 6119 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 12 transaction(s) across loan(s) 9, 10, 14.
- shape `CREDIT:1 CREDIT:2 CREDIT:16 DEBIT:8`: loan 4, tx L28, P 977 / I 49 / F 0 / Pen 0 / OP 48974 / UI 0, paymentType id 10 — 3 transaction(s) across loan(s) 4, 13, 14.
- shape `CREDIT:8 CREDIT:12 CREDIT:16 CREDIT:20 DEBIT:8 DEBIT:12 DEBIT:16 DEBIT:20`: loan 1, tx L5, P 80000 / I 1875 / F 0 / Pen 0 / OP 8125 / UI 0, paymentType id 10 — 3 transaction(s) across loan(s) 1, 2, 3.
- shape `CREDIT:1 CREDIT:2 CREDIT:8 CREDIT:16 DEBIT:1 DEBIT:2 DEBIT:8 DEBIT:16`: loan 13, tx L321, P 12216 / I 45 / F 0 / Pen 0 / OP 2239 / UI 0, paymentType id 10 — 2 transaction(s) across loan(s) 13, 14.
- shape `CREDIT:12 CREDIT:20 DEBIT:8`: loan 1, tx L7, P 88310 / I 1690 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 2 transaction(s) across loan(s) 1, 2.
- shape `CREDIT:1 CREDIT:16 DEBIT:8`: loan 5, tx L36, P 311 / I 0 / F 0 / Pen 0 / OP 49689 / UI 0, paymentType id 10 — 1 transaction(s) across loan(s) 5.
- shape `CREDIT:12 DEBIT:8`: loan 3, tx L21, P 90000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 1 transaction(s) across loan(s) 3.

#### `loanTransactionType.payoutRefund`

_No legs for this type — see the finding above._

#### `loanTransactionType.repayment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 CREDIT:2 DEBIT:8` | 1, 2, 8 | CREDIT 1, CREDIT 2, DEBIT 8 | 14 | 4, 5, 6, 7, 11, 12, 14 | 4 | L26 | P 49023 / I 977 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:1 CREDIT:2 CREDIT:8 DEBIT:1 DEBIT:2 DEBIT:8` | 1, 2, 8 | CREDIT 1, CREDIT 2, CREDIT 8, DEBIT 1, DEBIT 2, DEBIT 8 | 3 | 13, 14 | 13 | L319 | P 501 / I 99 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:1 CREDIT:8 DEBIT:1 DEBIT:8` | 1, 8 | CREDIT 1, CREDIT 8, DEBIT 1, DEBIT 8 | 3 | 1, 2, 3 | 1 | L2 | P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |
| `CREDIT:11 DEBIT:8` | 8, 11 | CREDIT 11, DEBIT 8 | 2 | 8, 13 | 8 | L61 | P 100000 / I 14248 / F 0 / Pen 0 / OP 0 / UI 0 | 10 |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 CREDIT:2 DEBIT:8`: loan 4, tx L26, P 49023 / I 977 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 14 transaction(s) across loan(s) 4, 5, 6, 7, 11, 12, 14.
- shape `CREDIT:1 CREDIT:2 CREDIT:8 DEBIT:1 DEBIT:2 DEBIT:8`: loan 13, tx L319, P 501 / I 99 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 3 transaction(s) across loan(s) 13, 14.
- shape `CREDIT:1 CREDIT:8 DEBIT:1 DEBIT:8`: loan 1, tx L2, P 10000 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 3 transaction(s) across loan(s) 1, 2, 3.
- shape `CREDIT:11 DEBIT:8`: loan 8, tx L61, P 100000 / I 14248 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id 10 — 2 transaction(s) across loan(s) 8, 13.

#### `loanTransactionType.accrualAdjustment`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:2 DEBIT:5` | 2, 5 | CREDIT 2, DEBIT 5 | 5 | 4, 5, 6, 7 | 4 | L25 | P 0 / I 24 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:2 DEBIT:5`: loan 4, tx L25, P 0 / I 24 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 5 transaction(s) across loan(s) 4, 5, 6, 7.

#### `loanTransactionType.chargeOff`

| shape (side:account) | account ids | sides | transactions | loans | example loan | example tx | example portions (minor) | example paymentType id |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| `CREDIT:1 CREDIT:2 CREDIT:12 CREDIT:20 DEBIT:1 DEBIT:2 DEBIT:12 DEBIT:20` | 1, 2, 12, 20 | CREDIT 1, CREDIT 2, CREDIT 12, CREDIT 20, DEBIT 1, DEBIT 2, DEBIT 12, DEBIT 20 | 8 | 1, 2, 3, 4, 5, 6, 7 | 1 | L4 | P 80000 / I 1875 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:1 CREDIT:2 DEBIT:12 DEBIT:20` | 1, 2, 12, 20 | CREDIT 1, CREDIT 2, DEBIT 12, DEBIT 20 | 8 | 1, 2, 3, 8, 9, 11, 12, 14 | 1 | L6 | P 90000 / I 1875 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:1 CREDIT:12 DEBIT:1 DEBIT:12` | 1, 12 | CREDIT 1, CREDIT 12, DEBIT 1, DEBIT 12 | 1 | 4 | 4 | L27 | P 977 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | - |
| `CREDIT:1 CREDIT:2 DEBIT:12 DEBIT:13 DEBIT:20` | 1, 2, 12, 13, 20 | CREDIT 1, CREDIT 2, DEBIT 12, DEBIT 13, DEBIT 20 | 1 | 10 | 10 | L296 | - | - |
| `CREDIT:1 DEBIT:12` | 1, 12 | CREDIT 1, DEBIT 12 | 1 | 13 | 13 | L334 | P 600 / I 0 / F 0 / Pen 0 / OP 0 / UI 0 | - |

Examples (loan, tx id, portions, paymentType id):

- shape `CREDIT:1 CREDIT:2 CREDIT:12 CREDIT:20 DEBIT:1 DEBIT:2 DEBIT:12 DEBIT:20`: loan 1, tx L4, P 80000 / I 1875 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 8 transaction(s) across loan(s) 1, 2, 3, 4, 5, 6, 7.
- shape `CREDIT:1 CREDIT:2 DEBIT:12 DEBIT:20`: loan 1, tx L6, P 90000 / I 1875 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 8 transaction(s) across loan(s) 1, 2, 3, 8, 9, 11, 12, 14.
- shape `CREDIT:1 CREDIT:12 DEBIT:1 DEBIT:12`: loan 4, tx L27, P 977 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 1 transaction(s) across loan(s) 4.
- shape `CREDIT:1 CREDIT:2 DEBIT:12 DEBIT:13 DEBIT:20`: loan 10, tx L296, -, paymentType id - — 1 transaction(s) across loan(s) 10.
- shape `CREDIT:1 DEBIT:12`: loan 13, tx L334, P 600 / I 0 / F 0 / Pen 0 / OP 0 / UI 0, paymentType id - — 1 transaction(s) across loan(s) 13.

### Per-loan currency and charge-off state

| loan | currency | charged-off latest read-back | non-reversed chargeOff transactions |
| ---: | --- | --- | --- |
| 1 | MNT | True | L4@2025-04-14, L6@2025-04-14 |
| 2 | MNT | True | L11@2025-04-14, L13@2025-04-14 |
| 3 | MNT | True | L18@2025-04-14, L20@2025-04-14 |
| 4 | MNT | False | L24@2025-04-14, L27@2025-04-14 |
| 5 | MNT | False | L32@2025-04-14, L35@2025-04-14 |
| 6 | MNT | False | L42@2025-04-01 |
| 7 | MNT | False | L48@2024-03-31 |
| 8 | MNT | True | L53@2025-07-20 |
| 9 | MNT | True | L179@2025-08-14 |
| 10 | MNT | True | L296@2025-08-15 |
| 11 | MNT | True | L307@2025-10-08 |
| 12 | MNT | True | L317@2025-10-01 |
| 13 | MNT | True | L334@2026-01-23 |
| 14 | MNT | True | L359@2023-07-26 |

### Findings

- target type(s) with NO journal-entry legs at all: loanTransactionType.payoutRefund.  The arm was NOT exercised by this feature.
- chargeOff supplement (NOT a read-back): loan 9 tx L179, loan 10 tx L296, loan 12 tx L317.  For these loans the feature charged the loan off AFTER its last read-back, so the charge-off transaction id is in no read-back; the charge-off command response (`charge-off-response.json` `resourceId`) is the evidence and it is injected as the `chargeOff` transaction so the arm is complete.  The charge-off is non-reversed (no reversal transaction/command is captured for these loans).
- (unmapped): 370 swept legs on 185 transactions have no read-back type: loan 9 (92 legs, L84-L107, L109-L138, L140-L170, L172-L178); that loan's chargeOff is L179; loan 10 (92 legs, L201-L224, L226-L255, L257-L287, L289-L295); that loan's chargeOff is L296; loan 12 (1 legs, L316); that loan's chargeOff is L317.  These are postings made AFTER the loan read-backs were last captured (predominantly the daily accruals), so they cannot be typed from a read-back.  They are a join gap, reported as a finding; they are NOT missing required arms.
- `(unmapped)` leg shapes (370 legs / 185 transaction(s) across loan(s) 9, 10, 12, all with no read-back type; per-loan id ranges are in the finding above): CREDIT:5 DEBIT:2. These are post-read-back daily accrual legs — a join gap, not a missing required arm.

Other observations from the join:

- `loanTransactionType.interestRefund`: 36 legs on 16 transaction(s) / 4 loan(s); 0 legs on charged-off loan(s) (-); 36 on not-charged-off loan(s) (9, 10, 13, 14).
- `loanTransactionType.merchantIssuedRefund`: 87 legs on 24 transaction(s) / 9 loan(s); 39 legs on charged-off loan(s) (1, 2, 3, 4, 5); 48 on not-charged-off loan(s) (9, 10, 13, 14).
- `loanTransactionType.payoutRefund`: NO legs at all — the arm was NOT exercised by this feature.
- `loanTransactionType.repayment`: 76 legs on 22 transaction(s) / 12 loan(s); 16 legs on charged-off loan(s) (4, 5, 6, 7, 8, 13); 60 on not-charged-off loan(s) (1, 2, 3, 6, 7, 11, 12, 13, 14).
- `loanTransactionType.accrualAdjustment`: 10 legs on 5 transaction(s) / 4 loan(s); 10 legs on charged-off loan(s) (4, 5, 6, 7); 0 on not-charged-off loan(s) (-).
- `loanTransactionType.chargeOff`: 107 legs on 19 transaction(s) / 14 loan(s); 24 legs on charged-off loan(s) (1, 2, 3, 4, 5); 83 on not-charged-off loan(s) (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14).

The payment type on each arm comes from `paymentDetailData.paymentType.id` in the read-back (channel-mapped fund source); it is listed per shape above.

