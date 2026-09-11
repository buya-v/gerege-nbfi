# Replay result table — `LoanInterestPaymentWaiver.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd14`, task OH-TIERD14-CL. Whole-file replay of all
15 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanInterestPaymentWaiver.feature`.

Result: **15 scenarios (15 passed, 0 failed)**; 468 steps (468 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C3141 | 5 | PASSED | 1 | `LP1_INTEREST_FLAT` |
| 2 | C3142 | 40 | PASSED | 2 | `LP1_INTEREST_FLAT` |
| 3 | C3143 | 77 | PASSED | 3 | `LP1_INTEREST_FLAT` |
| 4 | C3144 | 111 | PASSED | 4 | `LP1_INTEREST_FLAT` |
| 5 | C3145 | 204 | PASSED | 5 | `LP1_INTEREST_FLAT` |
| 6 | C3146 | 302 | PASSED | 6 | `LP1_INTEREST_FLAT` |
| 7 | C3147 | 399 | PASSED | 7 | `LP1_INTEREST_FLAT` |
| 8 | C3148 | 443 | PASSED | 8 | `LP1_INTEREST_FLAT` |
| 9 | C3149 | 495 | PASSED | 9 | `LP1_INTEREST_FLAT` |
| 10 | C3150 | 558 | PASSED | 10 | `LP1_INTEREST_FLAT` |
| 11 | C3151 | 626 | PASSED | 11 | `LP1_INTEREST_FLAT` |
| 12 | C4200 | 695 | PASSED | 12 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_ZERO_CHARGE_OFF` |
| 13 | C4204 | 751 | PASSED | 13 | `LP2_ADV_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OF_ACCRUAL` |
| 14 | C4205 | 953 | PASSED | 14 | `LP2_ADV_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OF_ACCRUAL` |
| 15 | C4206 | 1194 | PASSED | 15 | `LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL` |

## Failures — 0 scenarios

None. Every scenario passed: the interest-payment-waiver replay — and with it the
interest-payment-waiver posting
(`createJournalEntriesForInterestPaymentWaiverOrInterestRefund`) plus the UC12
after-charge-off payout-refund and goodwill-credit scenarios — was exercised and
the oracle agreed with every `.feature` expectation.