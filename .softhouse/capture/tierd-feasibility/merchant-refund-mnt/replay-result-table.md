# Replay result table — `LoanMerchantIssuedRefund.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd22`, task OH-TIERD22-DB. Whole-file replay of all
19 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanMerchantIssuedRefund.feature`.

The feature has 19 plain `Scenario:` blocks and no `Scenario Outline`, so the 19
Gherkin scenarios give the 19 rows below, each a distinct loan. The charged-off arms
(normal / payout / fraud) and the not-charged-off arm are spread across them.

Result: **19 scenarios (19 passed, 0 failed)**; 528 steps (528 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
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

## Failures — 0 scenarios

None. Every scenario passed: the merchant-issued-refund replay — and with it the
MIR postings (principal/interest/fee/penalty portions), the normal, payout and fraud
charged-off arms and the not-charged-off arm, plus the interest-refund and reversal
transactions — was exercised and the oracle agreed with every `.feature` expectation.