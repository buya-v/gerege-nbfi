# OWNER — Tier D `LoanChargesInstallmentFee.feature` MNT capture

This directory owns the MNT read-backs captured by replaying the **whole**
`LoanChargesInstallmentFee.feature` (28 scenarios: installment fees charged, partly
paid, and WAIVED) against the throwaway reference oracle, tenant `tierd`.  Capture
only: no vector, no drive, no `.go`.  Money in the tables, manifests and this file is
integer minor units (MNT, 2 ISO 4217 minor digits); the raw oracle bodies under
`loans/` carry the decimal major units the oracle emitted, unchanged.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file: feature, each scenario, its loans, and which read-back files belong to it |
| `replay-result-table.md` | the per-scenario PASSED/FAILED result table and failure deltas |
| `replay-installmentfee-mnt.log` | raw cucumber/Gradle replay log, 63490 lines |
| `run-installmentfee-mnt.sh` | the exact driver used for the replay |
| `scenario-results.json` | machine-readable per-scenario result, loan mapping and failed steps |
| `build-results.py` | parses the replay log and feature into the result tables |
| `organize.py` | copies committed bodies into `loans/` and writes the manifests |
| `owner.py` | generates this file |
| `manifest-installmentfee.json` | full extraction manifest (all 777 bodies, `committed` flag) |
| `manifest-installmentfee-passed.json` | manifest of the committed bodies (570) |
| `summary-installmentfee.json` | extractor totals and per-loan counts |
| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |
| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |

## Source

- feature: `fineract-e2e-tests-runner/src/test/resources/features/LoanChargesInstallmentFee.feature`
- throwaway tenant `tierd`; image `fineract:latest` `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`
  (proven identical to the standing reference oracle by `preflight.sh`)
- currency MNT (2 ISO 4217 minor digits, 496); money below is integer minor units
- capture: `/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-installmentfee-mnt.log`
- capture size: 199302532 B / 63490 lines
- extraction: 2417 exchanges, 641 loan-keyed, 29 loans, 777 files, 6556008 kept body bytes
- replay: **28 scenarios (15 passed, 13 failed)**; 856 steps (584 passed, 259 skipped, 13 failed)
- waiver coverage: 77 waiver steps in the feature (the observations behind
  `loan/charge.go`'s waiver arithmetic and `UpdateWaivedAmount` at 40%)

## Scenario → loan map

Every scenario creates exactly one client and one customized loan at the top, in
feature order, so scenario `k` owns loan `k` (28 scenarios, 28 loans).  The mapping
is not assumed: each loan's read-back `loanProductName` equals its scenario's product
and its `clientId` equals the scenario position (`build-results.py`; 0 mismatches).
The one extra key in the extraction, "loan 131", is not a loan: it is the
external-id-keyed `reAge` transaction on loan 28, mis-keyed because the command
response's `resourceId` is a transaction id.  It is `committed: false` and carries a
`note` in `manifest-installmentfee.json`.

| # | TestRailId | feature line | result | loan | product | principal (minor) | read-backs | committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C3784 | 5 | PASSED | 1 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_DAILY_INSTALLMENT_FEE_FLAT_CHARGES` | 10000 | 29 | yes |
| 2 | C3811 | 89 | PASSED | 2 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_DAILY_INSTALLMENT_FEE_FLAT_CHARGES` | 10000 | 29 | yes |
| 3 | C3785 | 173 | PASSED | 3 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_CHARGES` | 10000 | 29 | yes |
| 4 | C3786 | 257 | FAILED | 4 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES` | 10000 | 7 | no (not committed) |
| 5 | C3812 | 341 | FAILED | 5 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES` | 10000 | 7 | no (not committed) |
| 6 | C3787 | 425 | PASSED | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_INTEREST_CHARGES` | 10000 | 29 | yes |
| 7 | C3788 | 509 | FAILED | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_ALL_CHARGES` | 10000 | 7 | no (not committed) |
| 8 | C3789 | 602 | FAILED | 8 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_FLAT_INTEREST_CHARGES_TRANCHE` | 100000 | 7 | no (not committed) |
| 9 | C3813 | 716 | FAILED | 9 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_FLAT_INTEREST_CHARGES_TRANCHE` | 100000 | 7 | no (not committed) |
| 10 | C3814 | 837 | FAILED | 10 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` | 100000 | 7 | no (not committed) |
| 11 | C3820 | 952 | PASSED | 11 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_INTEREST_RECALCULATION_MULTIDISB` | 20000 | 41 | yes |
| 12 | C3790 | 1071 | PASSED | 12 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 10000 | 29 | yes |
| 13 | C3815 | 1156 | PASSED | 13 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 29 | yes |
| 14 | C3816 | 1241 | PASSED | 14 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 10000 | 12 | yes |
| 15 | C3791 | 1254 | PASSED | 15 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 29 | yes |
| 16 | C3792 | 1339 | PASSED | 16 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 10000 | 12 | yes |
| 17 | C3817 | 1352 | FAILED | 17 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 7 | no (not committed) |
| 18 | C3818 | 1437 | PASSED | 18 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 10000 | 12 | yes |
| 19 | C3793 | 1450 | PASSED | 19 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 29 | yes |
| 20 | C3794 | 1535 | FAILED | 20 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 7 | no (not committed) |
| 21 | C3795 | 1632 | FAILED | 21 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR` | 10000 | 7 | no (not committed) |
| 22 | C3796 | 1726 | FAILED | 22 | `LP2_ADV_PYMNT_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` | 10000 | 7 | no (not committed) |
| 23 | C3797 | 1816 | PASSED | 23 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` | 100000 | 21 | yes |
| 24 | C3823 | 1849 | FAILED | 24 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 3 | no (not committed) |
| 25 | C3824 | 1923 | FAILED | 25 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` | 20000 | 7 | no (not committed) |
| 26 | C3890 | 2026 | FAILED | 26 | `LP2_DOWNPAYMENT` | 10000 | 11 | no (not committed) |
| 27 | C3891 | 2097 | PASSED | 27 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 10000 | 23 | yes |
| 28 | C3892 | 2225 | PASSED | 28 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` | 100000 | 32 | yes |

A PASSED scenario has its loan directory committed; a FAILED scenario's bodies stay
in the git-ignored `stage/` and are listed (with `committed: false`) in the full
manifest only.  The `principal (minor)` column comes from each loan's
`create-request` body, converted from the decimal major units the oracle emitted.

## Per-scenario read-back files

`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the
`create-request`, the `approve`/`disburse`/`charge`/`repayment`/`waiver`/... command
request+response pairs, and the `GET` read-backs.  The read-backs (kind `read`)
belonging to each PASSED scenario are listed below; command request/response pairs sit
in the same directory and are visible in `manifest-installmentfee-passed.json`.

### 1 — C3784 — `PASSED` — loan 1 — Progressive loan - Verify the loan creation with installment fee charge: flat charge type, interestRecalculation = true

Feature line 5; product `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_DAILY_INSTALLMENT_FEE_FLAT_CHARGES`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-1/`.

```
loans/loan-1/loan-1-detail-associations-all-1.json
loans/loan-1/loan-1-detail-associations-empty.json
loans/loan-1/loan-1-detail-no-associations-1.json
loans/loan-1/loan-1-detail-associations-all-2.json
loans/loan-1/loan-1-detail-associations-transactions-1.json
loans/loan-1/loan-1-detail-associations-all-3.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-1.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-2.json
loans/loan-1/loan-1-detail-associations-transactions-2.json
loans/loan-1/loan-1-detail-associations-charges-1.json
loans/loan-1/loan-1-detail-associations-transactions-3.json
loans/loan-1/loan-1-detail-associations-all-4.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-3.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-4.json
loans/loan-1/loan-1-detail-associations-transactions-4.json
loans/loan-1/loan-1-detail-associations-charges-2.json
loans/loan-1/loan-1-detail-associations-transactions-5.json
loans/loan-1/loan-1-detail-associations-all-5.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-5.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-6.json
loans/loan-1/loan-1-detail-associations-transactions-6.json
loans/loan-1/loan-1-detail-associations-charges-3.json
loans/loan-1/loan-1-detail-associations-transactions-7.json
loans/loan-1/loan-1-transactions-template-no-associations-prepayLoan.json
loans/loan-1/loan-1-detail-associations-transactions-8.json
loans/loan-1/loan-1-detail-associations-all-6.json
loans/loan-1/loan-1-detail-associations-repaymentSchedule-7.json
loans/loan-1/loan-1-detail-no-associations-2.json
loans/loan-1/loan-1-detail-no-associations-3.json
```

### 2 — C3811 — `PASSED` — loan 2 — Progressive loan - Verify the loan creation with installment fee charge: flat charge type, interestRecalculation = true, early repayment

Feature line 89; product `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_DAILY_INSTALLMENT_FEE_FLAT_CHARGES`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-2/`.

```
loans/loan-2/loan-2-detail-associations-all-1.json
loans/loan-2/loan-2-detail-associations-empty.json
loans/loan-2/loan-2-detail-no-associations-1.json
loans/loan-2/loan-2-detail-associations-all-2.json
loans/loan-2/loan-2-detail-associations-transactions-1.json
loans/loan-2/loan-2-detail-associations-all-3.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-1.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-2.json
loans/loan-2/loan-2-detail-associations-transactions-2.json
loans/loan-2/loan-2-detail-associations-charges-1.json
loans/loan-2/loan-2-detail-associations-transactions-3.json
loans/loan-2/loan-2-detail-associations-all-4.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-3.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-4.json
loans/loan-2/loan-2-detail-associations-transactions-4.json
loans/loan-2/loan-2-detail-associations-charges-2.json
loans/loan-2/loan-2-detail-associations-transactions-5.json
loans/loan-2/loan-2-detail-associations-all-5.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-5.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-6.json
loans/loan-2/loan-2-detail-associations-transactions-6.json
loans/loan-2/loan-2-detail-associations-charges-3.json
loans/loan-2/loan-2-detail-associations-transactions-7.json
loans/loan-2/loan-2-transactions-template-no-associations-prepayLoan.json
loans/loan-2/loan-2-detail-associations-transactions-8.json
loans/loan-2/loan-2-detail-associations-all-6.json
loans/loan-2/loan-2-detail-associations-repaymentSchedule-7.json
loans/loan-2/loan-2-detail-no-associations-2.json
loans/loan-2/loan-2-detail-no-associations-3.json
```

### 3 — C3785 — `PASSED` — loan 3 — Progressive loan - Verify the loan creation with installment fee charge: percentage amount charge type, interestRecalculation = false

Feature line 173; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_CHARGES`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-3/`.

```
loans/loan-3/loan-3-detail-associations-all-1.json
loans/loan-3/loan-3-detail-associations-empty.json
loans/loan-3/loan-3-detail-no-associations-1.json
loans/loan-3/loan-3-detail-associations-all-2.json
loans/loan-3/loan-3-detail-associations-transactions-1.json
loans/loan-3/loan-3-detail-associations-all-3.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-1.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-2.json
loans/loan-3/loan-3-detail-associations-transactions-2.json
loans/loan-3/loan-3-detail-associations-charges-1.json
loans/loan-3/loan-3-detail-associations-transactions-3.json
loans/loan-3/loan-3-detail-associations-all-4.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-3.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-4.json
loans/loan-3/loan-3-detail-associations-transactions-4.json
loans/loan-3/loan-3-detail-associations-charges-2.json
loans/loan-3/loan-3-detail-associations-transactions-5.json
loans/loan-3/loan-3-detail-associations-all-5.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-5.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-6.json
loans/loan-3/loan-3-detail-associations-transactions-6.json
loans/loan-3/loan-3-detail-associations-charges-3.json
loans/loan-3/loan-3-detail-associations-transactions-7.json
loans/loan-3/loan-3-transactions-template-no-associations-prepayLoan.json
loans/loan-3/loan-3-detail-associations-transactions-8.json
loans/loan-3/loan-3-detail-associations-all-6.json
loans/loan-3/loan-3-detail-associations-repaymentSchedule-7.json
loans/loan-3/loan-3-detail-no-associations-2.json
loans/loan-3/loan-3-detail-no-associations-3.json
```

### 4 — C3786 — `FAILED` — loan 4 — Progressive loan - Verify the loan creation with installment fee charge: percentage interest charge type, interestRecalculation = false

Feature line 257; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES`; principal 10000 minor units; **not committed**.

Failing step (feature line 265): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 4
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.01, 0.0, 17.05, 0.0, 0.0, 0.0, 17.05] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.0, 0.0, 17.04, 0.0, 0.0, 0.0, 17.04]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 5 — C3812 — `FAILED` — loan 5 — Progressive loan - Verify the loan creation with installment fee charge: percentage interest charge type, interestRecalculation = false, early repayment

Feature line 341; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES`; principal 10000 minor units; **not committed**.

Failing step (feature line 349): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 5
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.01, 0.0, 17.05, 0.0, 0.0, 0.0, 17.05] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.0, 0.0, 17.04, 0.0, 0.0, 0.0, 17.04]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 6 — C3787 — `PASSED` — loan 6 — Progressive loan - Verify the loan creation with installment fee charge: percentage amount + interest charge type, interestRecalculation = false

Feature line 425; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_INTEREST_CHARGES`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-6/`.

```
loans/loan-6/loan-6-detail-associations-all-1.json
loans/loan-6/loan-6-detail-associations-empty.json
loans/loan-6/loan-6-detail-no-associations-1.json
loans/loan-6/loan-6-detail-associations-all-2.json
loans/loan-6/loan-6-detail-associations-transactions-1.json
loans/loan-6/loan-6-detail-associations-all-3.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-1.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-2.json
loans/loan-6/loan-6-detail-associations-transactions-2.json
loans/loan-6/loan-6-detail-associations-charges-1.json
loans/loan-6/loan-6-detail-associations-transactions-3.json
loans/loan-6/loan-6-detail-associations-all-4.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-3.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-4.json
loans/loan-6/loan-6-detail-associations-transactions-4.json
loans/loan-6/loan-6-detail-associations-charges-2.json
loans/loan-6/loan-6-detail-associations-transactions-5.json
loans/loan-6/loan-6-detail-associations-all-5.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-5.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-6.json
loans/loan-6/loan-6-detail-associations-transactions-6.json
loans/loan-6/loan-6-detail-associations-charges-3.json
loans/loan-6/loan-6-detail-associations-transactions-7.json
loans/loan-6/loan-6-transactions-template-no-associations-prepayLoan.json
loans/loan-6/loan-6-detail-associations-transactions-8.json
loans/loan-6/loan-6-detail-associations-all-6.json
loans/loan-6/loan-6-detail-associations-repaymentSchedule-7.json
loans/loan-6/loan-6-detail-no-associations-2.json
loans/loan-6/loan-6-detail-no-associations-3.json
```

### 7 — C3788 — `FAILED` — loan 7 — Progressive loan - Verify the loan creation with installment fee charge: all charge types, interestRecalculation = false

Feature line 509; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_ALL_CHARGES`; principal 10000 minor units; **not committed**.

Failing step (feature line 517): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 7
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 8 — C3789 — `FAILED` — loan 8 — Progressive loan - Verify the loan creation with installment fee charge: flat + % interest charge types, tranche loan, interestRecalculation = false

Feature line 602; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_FLAT_INTEREST_CHARGES_TRANCHE`; principal 100000 minor units; **not committed**.

Failing step (feature line 610): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 8
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.01, 0.0, 27.05, 0.0, 0.0, 0.0, 27.05] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.0, 0.0, 27.04, 0.0, 0.0, 0.0, 27.04]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 9 — C3813 — `FAILED` — loan 9 — Progressive loan - Verify the loan creation with installment fee charge: flat + % interest charge types, tranche loan, interestRecalculation = false, early repayment

Feature line 716; product `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_FLAT_INTEREST_CHARGES_TRANCHE`; principal 100000 minor units; **not committed**.

Failing step (feature line 724): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 9
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.01, 0.0, 27.05, 0.0, 0.0, 0.0, 27.05] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.0, 0.0, 27.04, 0.0, 0.0, 0.0, 27.04]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 10 — C3814 — `FAILED` — loan 10 — Progressive loan - Verify add installment fee charge: flat + % interest charge types, tranche loan, interestRecalculation = false

Feature line 837; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE`; principal 100000 minor units; **not committed**.

Failing step (feature line 847): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 10
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.01, 0.0, 27.01, 0.0, 0.0, 0.0, 27.01] -
expected [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.0, 0.0, 27.0, 0.0, 0.0, 0.0, 27.0]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 11 — C3820 — `PASSED` — loan 11 — Progressive loan - Verify add installment fee charge: flat charge type, tranche loan, interestRecalculation = true, early repayment

Feature line 952; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_INTEREST_RECALCULATION_MULTIDISB`; principal 20000 minor units; read-backs: 41; all
committed under `loans/loan-11/`.

```
loans/loan-11/loan-11-detail-associations-all-1.json
loans/loan-11/loan-11-detail-associations-empty.json
loans/loan-11/loan-11-detail-no-associations-1.json
loans/loan-11/loan-11-detail-associations-all-2.json
loans/loan-11/loan-11-detail-associations-transactions-1.json
loans/loan-11/loan-11-detail-associations-all-3.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-1.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-2.json
loans/loan-11/loan-11-detail-associations-transactions-2.json
loans/loan-11/loan-11-detail-associations-charges-1.json
loans/loan-11/loan-11-detail-associations-transactions-3.json
loans/loan-11/loan-11-detail-associations-all-4.json
loans/loan-11/loan-11-detail-associations-transactions-4.json
loans/loan-11/loan-11-detail-associations-all-5.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-3.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-4.json
loans/loan-11/loan-11-detail-associations-transactions-5.json
loans/loan-11/loan-11-detail-associations-charges-2.json
loans/loan-11/loan-11-detail-associations-transactions-6.json
loans/loan-11/loan-11-detail-associations-transactions-7.json
loans/loan-11/loan-11-detail-no-associations-2.json
loans/loan-11/loan-11-detail-associations-all-6.json
loans/loan-11/loan-11-detail-associations-transactions-8.json
loans/loan-11/loan-11-detail-associations-all-7.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-5.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-6.json
loans/loan-11/loan-11-detail-associations-transactions-9.json
loans/loan-11/loan-11-detail-associations-charges-3.json
loans/loan-11/loan-11-detail-associations-transactions-10.json
loans/loan-11/loan-11-detail-associations-all-8.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-7.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-8.json
loans/loan-11/loan-11-detail-associations-transactions-11.json
loans/loan-11/loan-11-detail-associations-charges-4.json
loans/loan-11/loan-11-detail-associations-transactions-12.json
loans/loan-11/loan-11-transactions-template-no-associations-prepayLoan.json
loans/loan-11/loan-11-detail-associations-transactions-13.json
loans/loan-11/loan-11-detail-associations-all-9.json
loans/loan-11/loan-11-detail-associations-repaymentSchedule-9.json
loans/loan-11/loan-11-detail-no-associations-3.json
loans/loan-11/loan-11-detail-no-associations-4.json
```

### 12 — C3790 — `PASSED` — loan 12 — Progressive loan - Verify add installment fee charge: flat charge type, interestRecalculation = true

Feature line 1071; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-12/`.

```
loans/loan-12/loan-12-detail-associations-all-1.json
loans/loan-12/loan-12-detail-associations-empty.json
loans/loan-12/loan-12-detail-no-associations-1.json
loans/loan-12/loan-12-detail-associations-all-2.json
loans/loan-12/loan-12-detail-associations-transactions-1.json
loans/loan-12/loan-12-detail-associations-all-3.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-1.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-2.json
loans/loan-12/loan-12-detail-associations-transactions-2.json
loans/loan-12/loan-12-detail-associations-charges-1.json
loans/loan-12/loan-12-detail-associations-transactions-3.json
loans/loan-12/loan-12-detail-associations-all-4.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-3.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-4.json
loans/loan-12/loan-12-detail-associations-transactions-4.json
loans/loan-12/loan-12-detail-associations-charges-2.json
loans/loan-12/loan-12-detail-associations-transactions-5.json
loans/loan-12/loan-12-detail-associations-all-5.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-5.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-6.json
loans/loan-12/loan-12-detail-associations-transactions-6.json
loans/loan-12/loan-12-detail-associations-charges-3.json
loans/loan-12/loan-12-detail-associations-transactions-7.json
loans/loan-12/loan-12-transactions-template-no-associations-prepayLoan.json
loans/loan-12/loan-12-detail-associations-transactions-8.json
loans/loan-12/loan-12-detail-associations-all-6.json
loans/loan-12/loan-12-detail-associations-repaymentSchedule-7.json
loans/loan-12/loan-12-detail-no-associations-2.json
loans/loan-12/loan-12-detail-no-associations-3.json
```

### 13 — C3815 — `PASSED` — loan 13 — Progressive loan - Verify add installment fee charge: flat charge type, interestRecalculation = false

Feature line 1156; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-13/`.

```
loans/loan-13/loan-13-detail-associations-all-1.json
loans/loan-13/loan-13-detail-associations-empty.json
loans/loan-13/loan-13-detail-no-associations-1.json
loans/loan-13/loan-13-detail-associations-all-2.json
loans/loan-13/loan-13-detail-associations-transactions-1.json
loans/loan-13/loan-13-detail-associations-all-3.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-1.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-2.json
loans/loan-13/loan-13-detail-associations-transactions-2.json
loans/loan-13/loan-13-detail-associations-charges-1.json
loans/loan-13/loan-13-detail-associations-transactions-3.json
loans/loan-13/loan-13-detail-associations-all-4.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-3.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-4.json
loans/loan-13/loan-13-detail-associations-transactions-4.json
loans/loan-13/loan-13-detail-associations-charges-2.json
loans/loan-13/loan-13-detail-associations-transactions-5.json
loans/loan-13/loan-13-detail-associations-all-5.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-5.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-6.json
loans/loan-13/loan-13-detail-associations-transactions-6.json
loans/loan-13/loan-13-detail-associations-charges-3.json
loans/loan-13/loan-13-detail-associations-transactions-7.json
loans/loan-13/loan-13-transactions-template-no-associations-prepayLoan.json
loans/loan-13/loan-13-detail-associations-transactions-8.json
loans/loan-13/loan-13-detail-associations-all-6.json
loans/loan-13/loan-13-detail-associations-repaymentSchedule-7.json
loans/loan-13/loan-13-detail-no-associations-2.json
loans/loan-13/loan-13-detail-no-associations-3.json
```

### 14 — C3816 — `PASSED` — loan 14 — Progressive loan - Verify add installment fee charge: percentage amount charge type is NOT allowed when interestRecalculation = true

Feature line 1241; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 10000 minor units; read-backs: 12; all
committed under `loans/loan-14/`.

```
loans/loan-14/loan-14-detail-associations-all-1.json
loans/loan-14/loan-14-detail-associations-empty.json
loans/loan-14/loan-14-detail-no-associations-1.json
loans/loan-14/loan-14-detail-associations-all-2.json
loans/loan-14/loan-14-detail-associations-transactions-1.json
loans/loan-14/loan-14-detail-associations-all-3.json
loans/loan-14/loan-14-transactions-template-no-associations-prepayLoan.json
loans/loan-14/loan-14-detail-associations-transactions-2.json
loans/loan-14/loan-14-detail-associations-all-4.json
loans/loan-14/loan-14-detail-associations-repaymentSchedule.json
loans/loan-14/loan-14-detail-no-associations-2.json
loans/loan-14/loan-14-detail-no-associations-3.json
```

### 15 — C3791 — `PASSED` — loan 15 — Progressive loan - Verify add installment fee charge: percentage amount charge type, interestRecalculation = false

Feature line 1254; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-15/`.

```
loans/loan-15/loan-15-detail-associations-all-1.json
loans/loan-15/loan-15-detail-associations-empty.json
loans/loan-15/loan-15-detail-no-associations-1.json
loans/loan-15/loan-15-detail-associations-all-2.json
loans/loan-15/loan-15-detail-associations-transactions-1.json
loans/loan-15/loan-15-detail-associations-all-3.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-1.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-2.json
loans/loan-15/loan-15-detail-associations-transactions-2.json
loans/loan-15/loan-15-detail-associations-charges-1.json
loans/loan-15/loan-15-detail-associations-transactions-3.json
loans/loan-15/loan-15-detail-associations-all-4.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-3.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-4.json
loans/loan-15/loan-15-detail-associations-transactions-4.json
loans/loan-15/loan-15-detail-associations-charges-2.json
loans/loan-15/loan-15-detail-associations-transactions-5.json
loans/loan-15/loan-15-detail-associations-all-5.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-5.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-6.json
loans/loan-15/loan-15-detail-associations-transactions-6.json
loans/loan-15/loan-15-detail-associations-charges-3.json
loans/loan-15/loan-15-detail-associations-transactions-7.json
loans/loan-15/loan-15-transactions-template-no-associations-prepayLoan.json
loans/loan-15/loan-15-detail-associations-transactions-8.json
loans/loan-15/loan-15-detail-associations-all-6.json
loans/loan-15/loan-15-detail-associations-repaymentSchedule-7.json
loans/loan-15/loan-15-detail-no-associations-2.json
loans/loan-15/loan-15-detail-no-associations-3.json
```

### 16 — C3792 — `PASSED` — loan 16 — Progressive loan - Verify add installment fee charge: percentage interest charge type is NOT allowed when interestRecalculation = true

Feature line 1339; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 10000 minor units; read-backs: 12; all
committed under `loans/loan-16/`.

```
loans/loan-16/loan-16-detail-associations-all-1.json
loans/loan-16/loan-16-detail-associations-empty.json
loans/loan-16/loan-16-detail-no-associations-1.json
loans/loan-16/loan-16-detail-associations-all-2.json
loans/loan-16/loan-16-detail-associations-transactions-1.json
loans/loan-16/loan-16-detail-associations-all-3.json
loans/loan-16/loan-16-transactions-template-no-associations-prepayLoan.json
loans/loan-16/loan-16-detail-associations-transactions-2.json
loans/loan-16/loan-16-detail-associations-all-4.json
loans/loan-16/loan-16-detail-associations-repaymentSchedule.json
loans/loan-16/loan-16-detail-no-associations-2.json
loans/loan-16/loan-16-detail-no-associations-3.json
```

### 17 — C3817 — `FAILED` — loan 17 — Progressive loan - Verify add installment fee charge: percentage interest charge type, interestRecalculation = false

Feature line 1352; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; **not committed**.

Failing step (feature line 1361): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 17
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 0.01, 0.0, 17.01, 0.0, 0.0, 0.0, 17.01] -
expected [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 0.0, 0.0, 17.0, 0.0, 0.0, 0.0, 17.0]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 18 — C3818 — `PASSED` — loan 18 — Progressive loan - Verify add installment fee charge: percentage amount + interest charge type is NOT allowed when interestRecalculation = true

Feature line 1437; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 10000 minor units; read-backs: 12; all
committed under `loans/loan-18/`.

```
loans/loan-18/loan-18-detail-associations-all-1.json
loans/loan-18/loan-18-detail-associations-empty.json
loans/loan-18/loan-18-detail-no-associations-1.json
loans/loan-18/loan-18-detail-associations-all-2.json
loans/loan-18/loan-18-detail-associations-transactions-1.json
loans/loan-18/loan-18-detail-associations-all-3.json
loans/loan-18/loan-18-transactions-template-no-associations-prepayLoan.json
loans/loan-18/loan-18-detail-associations-transactions-2.json
loans/loan-18/loan-18-detail-associations-all-4.json
loans/loan-18/loan-18-detail-associations-repaymentSchedule.json
loans/loan-18/loan-18-detail-no-associations-2.json
loans/loan-18/loan-18-detail-no-associations-3.json
```

### 19 — C3793 — `PASSED` — loan 19 — Progressive loan - Verify add installment fee charge: percentage amount + interest charge type, interestRecalculation = false

Feature line 1450; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; read-backs: 29; all
committed under `loans/loan-19/`.

```
loans/loan-19/loan-19-detail-associations-all-1.json
loans/loan-19/loan-19-detail-associations-empty.json
loans/loan-19/loan-19-detail-no-associations-1.json
loans/loan-19/loan-19-detail-associations-all-2.json
loans/loan-19/loan-19-detail-associations-transactions-1.json
loans/loan-19/loan-19-detail-associations-all-3.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-1.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-2.json
loans/loan-19/loan-19-detail-associations-transactions-2.json
loans/loan-19/loan-19-detail-associations-charges-1.json
loans/loan-19/loan-19-detail-associations-transactions-3.json
loans/loan-19/loan-19-detail-associations-all-4.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-3.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-4.json
loans/loan-19/loan-19-detail-associations-transactions-4.json
loans/loan-19/loan-19-detail-associations-charges-2.json
loans/loan-19/loan-19-detail-associations-transactions-5.json
loans/loan-19/loan-19-detail-associations-all-5.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-5.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-6.json
loans/loan-19/loan-19-detail-associations-transactions-6.json
loans/loan-19/loan-19-detail-associations-charges-3.json
loans/loan-19/loan-19-detail-associations-transactions-7.json
loans/loan-19/loan-19-transactions-template-no-associations-prepayLoan.json
loans/loan-19/loan-19-detail-associations-transactions-8.json
loans/loan-19/loan-19-detail-associations-all-6.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-7.json
loans/loan-19/loan-19-detail-no-associations-2.json
loans/loan-19/loan-19-detail-no-associations-3.json
```

### 20 — C3794 — `FAILED` — loan 20 — Progressive loan - Verify add installment fee charge: all charge types, interestRecalculation = false

Feature line 1535; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; **not committed**.

Failing step (feature line 1547): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 20
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.35, 0.0, 27.35, 0.0, 0.0, 0.0, 27.35] -
expected [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.34, 0.0, 27.34, 0.0, 0.0, 0.0, 27.34]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 21 — C3795 — `FAILED` — loan 21 — Progressive loan - Verify add installment fee charge, then make zero-interest charge-off: all charge types, interestRecalculation = false

Feature line 1632; product `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR`; principal 10000 minor units; **not committed**.

Failing step (feature line 1644): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 21
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 22 — C3796 — `FAILED` — loan 22 — Progressive loan - Verify add installment fee charge, then make accelerate maturity date charge-off: all charge types, interestRecalculation = false

Feature line 1726; product `LP2_ADV_PYMNT_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR`; principal 10000 minor units; **not committed**.

Failing step (feature line 1738): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 22
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39] -
expected [6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 23 — C3797 — `PASSED` — loan 23 — Verify that partially waived installment fee applied correctly in reverse-replay logic, Progressive loan

Feature line 1816; product `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL`; principal 100000 minor units; read-backs: 21; all
committed under `loans/loan-23/`.

```
loans/loan-23/loan-23-detail-associations-all-1.json
loans/loan-23/loan-23-detail-associations-empty.json
loans/loan-23/loan-23-detail-no-associations-1.json
loans/loan-23/loan-23-detail-associations-all-2.json
loans/loan-23/loan-23-detail-associations-transactions-1.json
loans/loan-23/loan-23-detail-associations-all-3.json
loans/loan-23/loan-23-detail-no-associations-2.json
loans/loan-23/loan-23-detail-associations-transactions-2.json
loans/loan-23/loan-23-detail-associations-all-4.json
loans/loan-23/loan-23-detail-associations-transactions-3.json
loans/loan-23/loan-23-detail-associations-all-5.json
loans/loan-23/loan-23-detail-associations-repaymentSchedule-1.json
loans/loan-23/loan-23-detail-associations-repaymentSchedule-2.json
loans/loan-23/loan-23-detail-associations-transactions-4.json
loans/loan-23/loan-23-detail-associations-charges.json
loans/loan-23/loan-23-transactions-template-no-associations-prepayLoan.json
loans/loan-23/loan-23-detail-associations-transactions-5.json
loans/loan-23/loan-23-detail-associations-all-6.json
loans/loan-23/loan-23-detail-associations-repaymentSchedule-3.json
loans/loan-23/loan-23-detail-no-associations-3.json
loans/loan-23/loan-23-detail-no-associations-4.json
```

### 24 — C3823 — `FAILED` — loan 24 — Progressive loan - Verify non-tranche loan with all installment fee charge types and repayments

Feature line 1849; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; **not committed**.

Failing step (feature line 1860): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 24
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.35, 0.0, 27.35, 0.0, 0.0, 0.0, 27.35] -
expected [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.34, 0.0, 27.34, 0.0, 0.0, 0.0, 27.34]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 25 — C3824 — `FAILED` — loan 25 — Progressive loan - Verify tranche loan with installment fee charges, repayments and multiple disbursements

Feature line 1923; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE`; principal 20000 minor units; **not committed**.

Failing step (feature line 1933): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`

- resource id (loan): 25
- tab line (period) on the schedule table: 7

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.01, 0.0, 27.01, 0.0, 0.0, 0.0, 27.01] -
expected [6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.0, 0.0, 27.0, 0.0, 0.0, 0.0, 27.0]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 26 — C3890 — `FAILED` — loan 26 — Cumulative loan - Verify final income accrual with multiple fee charges created successfully

Feature line 2026; product `LP2_DOWNPAYMENT`; principal 10000 minor units; **not committed**.

Failing step (feature line 2039): `Then Loan Repayment schedule has 7 periods, with the following data for periods:`

- resource id (loan): 26
- tab line (period) on the schedule table: 3

Actual / expected schedule rows (amounts are decimal major units in the
log; `replay-result-table.md` gives the integer minor-unit deltas):

```
actual   [2, 31, 01 February 2024, null, 62.0, 13.0, 0.0, 10.0, 0.0, 23.0, 0.0, 0.0, 0.0, 23.0] -
expected [2, 31, 01 February 2024, null, 63.0, 12.0, 0.0, 10.0, 0.0, 22.0, 0.0, 0.0, 0.0, 22.0]]
```

Full per-cell deltas are in `replay-result-table.md`.

### 27 — C3891 — `PASSED` — loan 27 — Progressive loan - Verify final income accrual with multiple fee charges created successfully

Feature line 2097; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 10000 minor units; read-backs: 23; all
committed under `loans/loan-27/`.

```
loans/loan-27/loan-27-detail-associations-all-1.json
loans/loan-27/loan-27-detail-associations-empty.json
loans/loan-27/loan-27-detail-no-associations-1.json
loans/loan-27/loan-27-detail-associations-all-2.json
loans/loan-27/loan-27-detail-associations-transactions-1.json
loans/loan-27/loan-27-detail-associations-all-3.json
loans/loan-27/loan-27-charges-47-no-associations.json
loans/loan-27/loan-27-charges-48-no-associations.json
loans/loan-27/loan-27-charges-49-no-associations.json
loans/loan-27/loan-27-charges-50-no-associations.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-1.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-2.json
loans/loan-27/loan-27-detail-associations-transactions-2.json
loans/loan-27/loan-27-detail-associations-charges-1.json
loans/loan-27/loan-27-detail-associations-transactions-3.json
loans/loan-27/loan-27-detail-associations-all-4.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-3.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-4.json
loans/loan-27/loan-27-detail-associations-transactions-4.json
loans/loan-27/loan-27-detail-associations-charges-2.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-5.json
loans/loan-27/loan-27-detail-no-associations-2.json
loans/loan-27/loan-27-detail-no-associations-3.json
```

### 28 — C3892 — `PASSED` — loan 28 — Verify installment fee charge allocation when loan has down payment, additional installment and re-aging

Feature line 2225; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL`; principal 100000 minor units; read-backs: 32; all
committed under `loans/loan-28/`.

```
loans/loan-28/loan-28-detail-associations-all-1.json
loans/loan-28/loan-28-detail-associations-empty.json
loans/loan-28/loan-28-detail-no-associations-1.json
loans/loan-28/loan-28-detail-associations-all-2.json
loans/loan-28/loan-28-detail-associations-transactions-1.json
loans/loan-28/loan-28-detail-associations-all-3.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-1.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-2.json
loans/loan-28/loan-28-detail-associations-transactions-2.json
loans/loan-28/loan-28-detail-associations-charges-1.json
loans/loan-28/loan-28-detail-associations-transactions-3.json
loans/loan-28/loan-28-detail-associations-all-4.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-3.json
loans/loan-28/loan-28-detail-associations-transactions-4.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-4.json
loans/loan-28/loan-28-detail-associations-charges-2.json
loans/loan-28/loan-28-detail-associations-all-5.json
loans/loan-28/loan-28-transactions-130-no-associations.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-5.json
loans/loan-28/loan-28-detail-associations-transactions-5.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-6.json
loans/loan-28/loan-28-detail-associations-charges-3.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-7.json
loans/loan-28/loan-28-detail-associations-transactions-6.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-8.json
loans/loan-28/loan-28-detail-associations-charges-4.json
loans/loan-28/loan-28-transactions-template-no-associations-prepayLoan.json
loans/loan-28/loan-28-detail-associations-transactions-7.json
loans/loan-28/loan-28-detail-associations-all-6.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-9.json
loans/loan-28/loan-28-detail-no-associations-2.json
loans/loan-28/loan-28-detail-no-associations-3.json
```

## The two failure families (a finding)

All 13 failures are the same step, `LoanStepDef.loanRepaymentSchedulePeriodsCheck`,
and each differs from the `.feature` table in one period:

- **Final-period fee rounding (12 of 13).** Scenarios 4, 5, 7, 8, 9, 10, 17, 20, 21,
  22, 24, 25 book one minor unit more Fees in the last period than the feature
  expects; Due and Outstanding follow by the same minor unit.  This is the last-period
  allocation of the installment-fee rounding remainder — the seam `loan/charge.go`
  computes.
- **Period-2 principal split (scenario 26).** The cumulative-loan scenario fails on
  period 2 with principal due 13.00 vs 12.00 expected (balance 62.00 vs 63.00, due
  23.00 vs 22.00) — a 100-minor-unit principal boundary shift, the same family as
  the UC10 1-minor-unit period-2 split recorded in
  `F-2026-09-11-tierd-repsched-mnt-uc10.md`.

These are pin-vs-feature disagreements: the oracle produced the actual values.  No EUR
control was run in this task, but MNT and EUR share 2 ISO 4217 minor digits, so the
currency re-seed cannot by itself explain a one-minor-unit split.

## The waiver scenario

Scenario 23 (`C3797`, feature line 1816), the partially waived installment fee with
reverse-replay logic, **PASSED**, so its loan 23 read-backs are committed.  That loan
is the observation behind `loan/charge.go`'s waiver arithmetic (`UpdateWaivedAmount`).

## Currency

Every committed body carrying a currency object resolves to `code = "MNT"` (1573 occurrences); the literal token `EUR` appears in 0 committed bodies.  So the oracle emitted MNT observations, not synthesis.

## Isolation

`preflight.sh` wrote the standing baseline before the throwaway started; `down.sh`
compared against that exact file and reported every counter equal to baseline
(`teardown-isolation.txt`).  All `tierd-*` containers, the `tierd-oracle` network and
its volume are gone; standing tenants `gerege` and `default` were never written.

## EUR control — OH-CHGCTL-BV (2026-09-11): the 13 failures are NOT caused by the MNT re-seed

A control replay of three of the 13 failing scenarios — **26** (`C3890`, the 100-minor-unit
period-2 split), **4** (`C3786`) and **7** (`C3788`) — was run on the disposable copy with the five
currency constants of `uc6-mnt/currency-seed-mnt.diff` reverted to `EUR` (Feign capture on,
tenant `tierd`, same pinned image). **All three FAIL in EUR, identically**: same steps, same
periods, same cells, same deltas as the MNT whole-file replay above (EUR `actual` == MNT `actual`
in every cell). The five constants were then restored and proven byte-identical to the recorded
seed diff, and the throwaway torn down to the standing baseline.

**Meaning.** The MNT re-seed is not the cause. The pinned build disagrees with its own `.feature`
expectations in EUR too, so the oracle's MNT output is gradeable; the 15 PASSED scenarios stand
and the 13 failures are pin-vs-feature disagreements. Evidence and cell tables:
`../charges-eur-control/OWNER.md` and `scenario-results.json`; finding:
`.softhouse/findings/F-2026-09-11-tierd-charges-mnt-eur-control.md`.

---

This capture was created by an AI agent (OpenHands) on behalf of the user.
