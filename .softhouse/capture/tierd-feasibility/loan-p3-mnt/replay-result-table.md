# Replay result table — `Loan-Part3.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd27`, task OH-TIERD27-DL. Whole-file replay of all
50 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/Loan-Part3.feature`.

The feature has 50 plain `Scenario:` blocks and no `Scenario Outline`, so the 50
Gherkin scenarios give the 50 rows below. Forty-nine create a loan; scenario 34
(`... UC7 ... results an ERROR`) attempts a loan and gets a 403, so it creates none.
Loan ids are attributed by client id, not by row position: scenario k owns client k
and a loan is attributed to the scenario whose `clientId` it was created for.

Result: **50 scenarios (47 passed, 3 failed)**; 1244 steps (1226 passed, 15 skipped, 3 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
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

## Failures — 3 scenarios

Each failure is recorded with the failing step and the actual-vs-expected values
exactly as the oracle printed them; the cause is NOT decided here (the driver
dispatches an EUR control). Amounts in the log are decimal major units.

### 20 — C3042 — `FAILED` — loan 20 — Verify that second disbursement is working on overpaid accounts in case of NEXT_INSTALLMENT future installment allocation rule

- failing step (feature line 1845): `Then Loan Repayment schedule has 5 periods, with the following data for periods:`
  - resource/loan id in the assertion: 20

```
Wrong value in Repayment schedule of resource 20 tab line 6.
Actual values in line (with the same due date) are:
[4, 15, 31 January 2024, null, 312.0, 313.0, 0.0, 0.0, 0.0, 313.0, 125.0, 125.0, 0.0, 188.0] -
But expected values in line:
[4, 15, 31 January 2024, null, 313.0, 312.0, 0.0, 0.0, 0.0, 312.0, 125.0, 125.0, 0.0, 187.0]]
```

### 21 — C3043 — `FAILED` — loan 21 — Verify that second disbursement is working on overpaid accounts in case of REAMORTIZATION future installment allocation rule

- failing step (feature line 1882): `Then Loan Repayment schedule has 5 periods, with the following data for periods:`
  - resource/loan id in the assertion: 21

```
Wrong value in Repayment schedule of resource 21 tab line 6.
Actual values in line (with the same due date) are:
[4, 15, 31 January 2024, null, 312.0, 313.0, 0.0, 0.0, 0.0, 313.0, 125.0, 125.0, 0.0, 188.0] -
But expected values in line:
[4, 15, 31 January 2024, null, 313.0, 312.0, 0.0, 0.0, 0.0, 312.0, 125.0, 125.0, 0.0, 187.0]]
```

### 25 — C3090 — `FAILED` — loan 25 — Verify that disbursement can be done on overpaid loan in case of cummulative loan schedule

- failing step (feature line 2049): `Then Loan Repayment schedule has 6 periods, with the following data for periods:`
  - resource/loan id in the assertion: 25

```
Wrong value in Repayment schedule of resource 25 tab line 7.
Actual values in line (with the same due date) are:
[4, 29, 01 March 2024, 02 February 2024, 525.0, 262.0, 0.0, 0.0, 0.0, 262.0, 262.0, 262.0, 0.0, 0.0] -
But expected values in line:
[4, 29, 01 March 2024, 02 February 2024, 524.0, 263.0, 0.0, 0.0, 0.0, 263.0, 263.0, 263.0, 0.0, 0.0]]
```
