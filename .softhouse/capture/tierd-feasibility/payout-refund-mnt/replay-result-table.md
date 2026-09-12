# Replay result table — `LoanPayoutRefund.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd24`, task OH-TIERD24-DE. Whole-file replay of all
9 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanPayoutRefund.feature`.

The feature has 9 plain `Scenario:` blocks and no `Scenario Outline`, so the 9
Gherkin scenarios give the 9 rows below, each a distinct loan. The feature exercises
payout refunds with and without an interest refund, the reversal of a payout refund
and its linked interest refund, manual interest refunds, and the guards that prevent a
manual interest refund when one already exists or the refund is reversed / not a refund.

Result: **9 scenarios (9 passed, 0 failed)**; 210 steps (210 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C3845 | 4 | PASSED | 1 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 2 | C3846 | 44 | PASSED | 2 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 3 | C3847 | 85 | PASSED | 3 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 4 | C3857 | 126 | PASSED | 4 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 5 | C3870 | 198 | PASSED | 5 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 6 | C3871 | 262 | PASSED | 6 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 7 | C3872 | 354 | PASSED | 7 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 8 | C3878 | 396 | PASSED | 8 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |
| 9 | C3879 | 412 | PASSED | 9 | `LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` |

## Failures — 0 scenarios

None. Every scenario passed: the payout-refund replay — and with it the
payout-refund postings, the interest-refund transactions that follow them, the
reversals of both, and the guards against a duplicate or invalid manual interest
refund — was exercised and the oracle agreed with every `.feature` expectation.