# Replay result table — `LoanReAmortization-Part1.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd30`, task OH-TIERD30-DR. Whole-file replay of all
50 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanReAmortization-Part1.feature`.

The feature has 50 plain `Scenario:` blocks and no `Scenario Outline`, so the 50
Gherkin scenarios give the 50 rows below, each a distinct loan. The re-amortization
happy path, the undo, the reverse-replay cases and the charged-off-forbidden arms are
spread across them.

Result: **50 scenarios (45 passed, 5 failed)**; 1354 steps (1319 passed, 30 skipped, 5 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
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

## Failures — 5 scenarios

Each failure is recorded with the failing step and the actual-vs-expected values
exactly as the oracle printed them; the cause is NOT decided here (the driver
dispatches an EUR control). Amounts in the log are decimal major units.

### 1 — C3069 — `FAILED` — loan 1 — Verify Loan re-amortization transaction - re-amortization happy path

- failing step (feature line 30): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 1

```
Wrong value in Repayment schedule of resource 1 tab line 4.
Actual values in line (with the same due date) are:
[3, 15, 31 January 2024, null, 187.0, 188.0, 0.0, 0.0, 0.0, 188.0, 0.0, 0.0, 0.0, 188.0] -
But expected values in line:
[3, 15, 31 January 2024, null, 188.0, 187.0, 0.0, 0.0, 0.0, 187.0, 0.0, 0.0, 0.0, 187.0]]
```

### 2 — C3070 — `FAILED` — loan 2 — Verify Loan re-amortization transaction - re-amortization happy path with loan externalId

- failing step (feature line 75): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 2

```
Wrong value in Repayment schedule of resource 2 tab line 4.
Actual values in line (with the same due date) are:
[3, 15, 31 January 2024, null, 187.0, 188.0, 0.0, 0.0, 0.0, 188.0, 0.0, 0.0, 0.0, 188.0] -
But expected values in line:
[3, 15, 31 January 2024, null, 188.0, 187.0, 0.0, 0.0, 0.0, 187.0, 0.0, 0.0, 0.0, 187.0]]
```

### 3 — C3071 — `FAILED` — loan 3 — Verify Loan re-amortization transaction - re-amortization undo happy path

- failing step (feature line 106): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 3

```
Wrong value in Repayment schedule of resource 3 tab line 4.
Actual values in line (with the same due date) are:
[3, 15, 31 January 2024, null, 187.0, 188.0, 0.0, 0.0, 0.0, 188.0, 0.0, 0.0, 0.0, 188.0] -
But expected values in line:
[3, 15, 31 January 2024, null, 188.0, 187.0, 0.0, 0.0, 0.0, 187.0, 0.0, 0.0, 0.0, 187.0]]
```

### 5 — C3073 — `FAILED` — loan 5 — Verify Loan re-amortization transaction - UC1: re-amortization after charge applied on loan

- failing step (feature line 177): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 5

```
Wrong value in Repayment schedule of resource 5 tab line 4.
Actual values in line (with the same due date) are:
[3, 15, 31 January 2024, null, 187.0, 188.0, 0.0, 0.0, 0.0, 188.0, 0.0, 0.0, 0.0, 188.0] -
But expected values in line:
[3, 15, 31 January 2024, null, 188.0, 187.0, 0.0, 0.0, 0.0, 187.0, 0.0, 0.0, 0.0, 187.0]]
```

### 35 — C4311 — `FAILED` — loan 35 — Verify Re-amortization with overdue penalties - Interest calculation: Default Behavior - Re-amortization with overdue penalties

- failing step (feature line 1947): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`
  - resource/loan id in the assertion: 35

```
Wrong value in Repayment schedule of resource 35 tab line 4.
Actual values in line (with the same due date) are:
[3, 31, 01 April 2024, null, 50.43, 16.62, 0.39, 5.0, 10.0, 32.01, 0.0, 0.0, 0.0, 32.01] -
But expected values in line:
[3, 31, 01 April 2024, null, 50.46, 16.59, 0.42, 5.0, 10.0, 32.01, 0.0, 0.0, 0.0, 32.01]]
```
