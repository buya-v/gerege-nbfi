# Replay result table — `LoanChargesInstallmentFee.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd7`, task OH-TIERD7-BU. Whole-file replay of
all 28 scenarios against the throwaway reference oracle (tenant `tierd`), with the
Feign capture on. Capture only: no vector, no drive, no `.go`. Money is integer
minor units (MNT, 2 ISO 4217 digits). Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanChargesInstallmentFee.feature`.

Result: **28 scenarios (15 passed, 13 failed)**; 856 steps (584 passed, 259 skipped, 13 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C3784 | 5 | PASSED | 1 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_DAILY_INSTALLMENT_FEE_FLAT_CHARGES` |
| 2 | C3811 | 89 | PASSED | 2 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALC_DAILY_INSTALLMENT_FEE_FLAT_CHARGES` |
| 3 | C3785 | 173 | PASSED | 3 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_CHARGES` |
| 4 | C3786 | 257 | FAILED | 4 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES` |
| 5 | C3812 | 341 | FAILED | 5 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_INTEREST_CHARGES` |
| 6 | C3787 | 425 | PASSED | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_PERCENT_AMOUNT_INTEREST_CHARGES` |
| 7 | C3788 | 509 | FAILED | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_ALL_CHARGES` |
| 8 | C3789 | 602 | FAILED | 8 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_FLAT_INTEREST_CHARGES_TRANCHE` |
| 9 | C3813 | 716 | FAILED | 9 | `LP2_ADV_PYMNT_INTEREST_DAILY_INSTALLMENT_FEE_FLAT_INTEREST_CHARGES_TRANCHE` |
| 10 | C3814 | 837 | FAILED | 10 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` |
| 11 | C3820 | 952 | PASSED | 11 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_REFUND_INTEREST_RECALCULATION_MULTIDISB` |
| 12 | C3790 | 1071 | PASSED | 12 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 13 | C3815 | 1156 | PASSED | 13 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 14 | C3816 | 1241 | PASSED | 14 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 15 | C3791 | 1254 | PASSED | 15 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 16 | C3792 | 1339 | PASSED | 16 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 17 | C3817 | 1352 | FAILED | 17 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 18 | C3818 | 1437 | PASSED | 18 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` |
| 19 | C3793 | 1450 | PASSED | 19 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 20 | C3794 | 1535 | FAILED | 20 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 21 | C3795 | 1632 | FAILED | 21 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_BEHAVIOUR` |
| 22 | C3796 | 1726 | FAILED | 22 | `LP2_ADV_PYMNT_ACCELERATE_MATURITY_CHARGE_OFF_BEHAVIOUR` |
| 23 | C3797 | 1816 | PASSED | 23 | _(default progressive)_ |
| 24 | C3823 | 1849 | FAILED | 24 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 25 | C3824 | 1923 | FAILED | 25 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_MULTIDISBURSE` |
| 26 | C3890 | 2026 | FAILED | 26 | `LP2_DOWNPAYMENT` |
| 27 | C3891 | 2097 | PASSED | 27 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` |
| 28 | C3892 | 2225 | PASSED | 28 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |

## Failures — 13 scenarios

Every failure is the same step — the periodic repayment-schedule table check
(`LoanStepDef.loanRepaymentSchedulePeriodsCheck`, `LoanStepDef.java:2312`) — and differs
from the `.feature` expectation in one period. Twelve of the thirteen differ by one
minor unit (0.01) in the final period; scenario 26 differs by 100 minor units (1.00)
in period 2. Values are read from the replay log: `Actual values in line` vs
`But expected values in line`.

| # | TestRailId | feature line of failing step | loan | periods | period (tab line) | actual | expected |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | C3786 | 265 | 4 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.01, 0.0, 17.05, 0.0, 0.0, 0.0, 17.05] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.0, 0.0, 17.04, 0.0, 0.0, 0.0, 17.04]]` |
| 5 | C3812 | 349 | 5 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.01, 0.0, 17.05, 0.0, 0.0, 0.0, 17.05] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 0.0, 0.0, 17.04, 0.0, 0.0, 0.0, 17.04]]` |
| 7 | C3788 | 517 | 7 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]]` |
| 8 | C3789 | 610 | 8 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.01, 0.0, 27.05, 0.0, 0.0, 0.0, 27.05] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.0, 0.0, 27.04, 0.0, 0.0, 0.0, 27.04]]` |
| 9 | C3813 | 724 | 9 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.01, 0.0, 27.05, 0.0, 0.0, 0.0, 27.05] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.0, 0.0, 27.04, 0.0, 0.0, 0.0, 27.04]]` |
| 10 | C3814 | 847 | 10 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.01, 0.0, 27.01, 0.0, 0.0, 0.0, 27.01] -` | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.0, 0.0, 27.0, 0.0, 0.0, 0.0, 27.0]]` |
| 17 | C3817 | 1361 | 17 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 0.01, 0.0, 17.01, 0.0, 0.0, 0.0, 17.01] -` | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 0.0, 0.0, 17.0, 0.0, 0.0, 0.0, 17.0]]` |
| 20 | C3794 | 1547 | 20 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.35, 0.0, 27.35, 0.0, 0.0, 0.0, 27.35] -` | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.34, 0.0, 27.34, 0.0, 0.0, 0.0, 27.34]]` |
| 21 | C3795 | 1644 | 21 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]]` |
| 22 | C3796 | 1738 | 22 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.35, 0.0, 27.39, 0.0, 0.0, 0.0, 27.39] -` | `[6, 30, 01 July 2024, null, 0.0, 16.94, 0.1, 10.34, 0.0, 27.38, 0.0, 0.0, 0.0, 27.38]]` |
| 24 | C3823 | 1860 | 24 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.35, 0.0, 27.35, 0.0, 0.0, 0.0, 27.35] -` | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.34, 0.0, 27.34, 0.0, 0.0, 0.0, 27.34]]` |
| 25 | C3824 | 1933 | 25 | 6 | 7 | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.01, 0.0, 27.01, 0.0, 0.0, 0.0, 27.01] -` | `[6, 30, 01 July 2024, null, 0.0, 16.9, 0.1, 10.0, 0.0, 27.0, 0.0, 0.0, 0.0, 27.0]]` |
| 26 | C3890 | 2039 | 26 | 7 | 3 | `[2, 31, 01 February 2024, null, 62.0, 13.0, 0.0, 10.0, 0.0, 23.0, 0.0, 0.0, 0.0, 23.0] -` | `[2, 31, 01 February 2024, null, 63.0, 12.0, 0.0, 10.0, 0.0, 22.0, 0.0, 0.0, 0.0, 22.0]]` |

### Deltas, cell by cell (integer minor units)

The failing line is `[Nr, Days, Date, Paid date, Balance of loan, Principal due, Interest, Fees, Penalties, Due, Paid, In advance, Late, Outstanding]`; the delta is
`actual − expected` and every cell below is integer minor units (MNT, 2 digits).

| # | loan | period (tab line) | Balance | Principal due | Interest | Fees | Due | Outstanding |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 4 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 5 | 5 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 7 | 7 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 8 | 8 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 9 | 9 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 10 | 10 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 17 | 17 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 20 | 20 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 21 | 21 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 22 | 22 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 24 | 24 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 25 | 25 | 7 | 0 | 0 | 0 | +1 | +1 | +1 |
| 26 | 26 | 3 | -100 | +100 | 0 | 0 | +100 | +100 |

### The two failure families

**Final-period fee rounding (12 of 13).** Scenarios 4, 5, 7, 8, 9, 10, 17, 20, 21, 22,
24, 25 fail on the last period: the oracle books one minor unit more to Fees than the
`.feature` table expects, and the period Due/Outstanding follow by the same one minor
unit (for loans 7/20/21/22/24 the fee is 10.35 vs 10.34; for 4/5 it is 0.01 vs 0.00;
for 8/9/10/25 it is 10.01 vs 10.00; for 17 it is 0.01 vs 0.00). The total fee column
is unaffected; only the last-period allocation of the rounding remainder differs.

**Period-2 principal split (scenario 26).** The cumulative-loan scenario fails on
period 2 with principal due 13.00 vs 12.00 expected (balance 62.00 vs 63.00, due 23.00
vs 22.00) — a one-unit principal boundary shift, the same family as the UC10 1-minor-unit
period-2 split recorded in `F-2026-09-11-tierd-repsched-mnt-uc10.md`.

These are pin-vs-feature disagreements, not capture errors: the oracle produced the
actual values. Currency attribution is not tested here (no EUR control in this task);
MNT and EUR share 2 ISO 4217 minor digits, so a currency re-seed cannot by itself
explain a one-minor-unit split.

## Note on the PASSED waiver scenario

Scenario 23 (`C3797`, feature line 1816) — the partially waived installment fee with
reverse-replay logic, the observation behind `loan/charge.go`'s waiver arithmetic and
`UpdateWaivedAmount` — **PASSED**, so its loan 23 read-backs are committed.