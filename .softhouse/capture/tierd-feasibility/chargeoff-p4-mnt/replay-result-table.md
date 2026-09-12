# Replay result table — `LoanChargeOff-Part4.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd23`, task OH-TIERD23-DC. Whole-file replay of all
14 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanChargeOff-Part4.feature`.

The feature has 14 plain `Scenario:` blocks and no `Scenario Outline`, so the 14
Gherkin scenarios give the 14 rows below, each a distinct loan. The
interest-refund / merchant-issued-refund / repayment-after-charge-off arms and the
reversal transactions are spread across them.

Result: **14 scenarios (14 passed, 0 failed)**; 503 steps (503 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
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

## Failures — 0 scenarios

None. Every scenario passed: the charge-off replay — and with it the
interest-refund, merchant-issued-refund and repayment postings after a
charge-off, the charge-off and reversal transactions, and the per-portion
principal/interest/fee/penalty allocation — was exercised and the oracle agreed
with every `.feature` expectation. A failure, had there been one, would be
recorded (not diagnosed) with the actual-vs-expected values the oracle printed.