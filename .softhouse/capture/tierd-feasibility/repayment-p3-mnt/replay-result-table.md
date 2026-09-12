# Replay result table — `LoanRepayment-Part3.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd28`, task OH-TIERD28-DM. Whole-file replay of all
50 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanRepayment-Part3.feature`.

The feature has 50 plain `Scenario:` blocks and no `Scenario Outline`, so the 50
Gherkin scenarios give the 50 rows below, each a distinct loan. This feature drives the
active-loan REFUND posting, the repayment, merchantIssuedRefund, payoutRefund,
creditBalanceRefund and interestRefund families, with charge-off arms across them.

Result: **50 scenarios (46 passed, 4 failed)**; 1360 steps (1335 passed, 21 skipped, 4 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C2908 | 6 | PASSED | 1 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 2 | C2961 | 39 | FAILED | 2 | `LP1_INTEREST_FLAT` |
| 3 | C2962 | 59 | FAILED | 3 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 4 | C3106 | 79 | PASSED | 4 | `LP2_DOWNPAYMENT_AUTO` |
| 5 | C3129 | 99 | PASSED | 5 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 6 | C3130 | 142 | PASSED | 6 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 7 | C3131 | 186 | PASSED | 7 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION_REPAYMENT_START_SUBMITTED` |
| 8 | C3132 | 229 | PASSED | 8 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION_REPAYMENT_START_SUBMITTED` |
| 9 | C3133 | 273 | PASSED | 9 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION_REPAYMENT_START_SUBMITTED` |
| 10 | C3223 | 317 | PASSED | 10 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 11 | C3224 | 394 | PASSED | 11 | `LP1_INTEREST_DECLINING_BALANCE_SAR_RECALCULATION_SAME_AS_REPAYMENT_COMPOUNDING_NONE_MULTIDISB` |
| 12 | C3225 | 444 | PASSED | 12 | `LP1_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 13 | C3247 | 580 | PASSED | 13 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 14 | C3261 | 616 | PASSED | 14 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 15 | C3262 | 652 | PASSED | 15 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 16 | C3263 | 688 | PASSED | 16 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 17 | C3264 | 724 | PASSED | 17 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 18 | C3265 | 760 | PASSED | 18 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 19 | C3266 | 798 | PASSED | 19 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` |
| 20 | C3296 | 835 | PASSED | 20 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_INTEREST_RECALCULATION` |
| 21 | C3293 | 877 | PASSED | 21 | `LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_DOWNPAYMENT` |
| 22 | C3294 | 900 | PASSED | 22 | `LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_DOWNPAYMENT` |
| 23 | C3295 | 929 | PASSED | 23 | `LP2_ADV_PYMNT_INTEREST_RECALCULATION_DAILY_EMI_360_30_MULTIDISBURSE_DOWNPAYMENT` |
| 24 | C3382 | 953 | PASSED | 24 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_ACCRUAL_ACTIVITY` |
| 25 | C3383 | 1007 | FAILED | 25 | `LP2_ADV_PYMNT_INTEREST_DAILY_AUTO_DOWNPAYMENT_EMI_ACTUAL_ACTUAL_ACCRUAL_ACTIVITY` |
| 26 | C3391 | 1068 | PASSED | 26 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` |
| 27 | C3392 | 1129 | PASSED | 27 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` |
| 28 | C3442 | 1191 | PASSED | 28 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ACCRUAL_ACTIVITY_POSTING` |
| 29 | C3520 | 1285 | PASSED | 29 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 30 | C3521 | 1315 | PASSED | 30 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 31 | C3569 | 1345 | PASSED | 31 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 32 | C3589 | 1463 | PASSED | 32 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 33 | C3614 | 1561 | PASSED | 33 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 34 | C3615 | 1742 | PASSED | 34 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 35 | C3616 | 1924 | PASSED | 35 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 36 | C3617 | 2062 | PASSED | 36 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_ACTUAL` |
| 37 | C3590 | 2191 | PASSED | 37 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_INTEREST_RECALCULATION` |
| 38 | C3666 | 2223 | PASSED | 38 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 39 | C3667 | 2272 | PASSED | 39 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 40 | C3840 | 2302 | PASSED | 40 | `LP2_NO_INTEREST_RECALCULATION_ALLOCATION_PENALTY_FIRST` |
| 41 | C3841 | 2386 | PASSED | 41 | `LP2_NO_INTEREST_RECALCULATION_ALLOCATION_PENALTY_FIRST` |
| 42 | C4053 | 2482 | PASSED | 42 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 43 | C4148 | 2585 | PASSED | 43 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 44 | C4149 | 2752 | PASSED | 44 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 45 | C4150 | 2921 | PASSED | 45 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 46 | C4151 | 3094 | PASSED | 46 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 47 | C4152 | 3236 | PASSED | 47 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 48 | C4350 | 3378 | PASSED | 48 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR` |
| 49 | C4351 | 3419 | FAILED | 49 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR` |
| 50 | C4352 | 3466 | PASSED | 50 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR` |

## Failures — 4 scenarios

Each failure is recorded with the failing step and the actual-vs-expected values
exactly as the oracle printed them; the cause is NOT decided here (the driver
dispatches an EUR control). Amounts in the log are decimal major units.

### 2 — C2961 — `FAILED` — loan 2 — Verify that outstanding amounts are rounded correctly in case of: installmentAmountInMultiplesOf=1, interestType: FLAT, amortizationType: EQUAL_INSTALLMENTS

- failing step (feature line 47): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 2

```
Wrong value in Repayment schedule of resource 2 tab line 2.
Actual values in line (with the same due date) are:
[1, 30, 01 October 2023, null, 936.63, 313.37, 15.63, 0.0, 0.0, 329.0, 0.0, 0.0, 0.0, 329.0] -
But expected values in line:
[1, 30, 01 October 2023, null, 937.62, 312.38, 15.62, 0.0, 0.0, 328.0, 0.0, 0.0, 0.0, 328.0]]
```

### 3 — C2962 — `FAILED` — loan 3 — Verify that outstanding amounts are rounded correctly in case of: installmentAmountInMultiplesOf=1, interestType: DECLINING_BALANCE, amortizationType: EQUAL_INSTALLMENTS

- failing step (feature line 67): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 3

```
Wrong value in Repayment schedule of resource 3 tab line 2.
Actual values in line (with the same due date) are:
[1, 30, 01 October 2023, null, 943.63, 306.37, 15.63, 0.0, 0.0, 322.0, 0.0, 0.0, 0.0, 322.0] -
But expected values in line:
[1, 30, 01 October 2023, null, 943.62, 306.38, 15.62, 0.0, 0.0, 322.0, 0.0, 0.0, 0.0, 322.0]]
```

### 25 — C3383 — `FAILED` — loan 25 — Verify repayment reversal on interest bearing loan with NSF fee with down payment when accrual activity is present

- failing step (feature line 1016): `Then Loan Repayment schedule has 4 periods, with the following data for periods:`
  - resource/loan id in the assertion: 25

```
Wrong value in Repayment schedule of resource 25 tab line 2.
Actual values in line (with the same due date) are:
[null, null, 22 December 2024, null, 6080.58, null, null, 0.0, null, 0.0, 0.0, null, null, null]
[1, 0, 22 December 2024, 22 December 2024, 4560.43, 1520.15, 0.0, 0.0, 0.0, 1520.15, 1520.15, 0.0, 0.0, 0.0] -
But expected values in line:
[1, 0, 22 December 2024, 22 December 2024, 4560.44, 1520.14, 0.0, 0.0, 0.0, 1520.14, 1520.14, 0.0, 0.0, 0.0]]
```

### 49 — C4351 — `FAILED` — loan 49 — Verify the loan creation with total calculated EMI less than 1 for progressive loan - 3 repayment periods

- failing step (feature line 3436): `Then Loan Repayment schedule has 3 periods, with the following data for periods:`
  - resource/loan id in the assertion: 49

```
Wrong value in Repayment schedule of resource 49 tab line 2.
Actual values in line (with the same due date) are:
[1, 31, 26 November 2025, null, 0.5, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0] -
But expected values in line:
[1, 31, 26 November 2025, null, 1.0, 0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.5]]
```
