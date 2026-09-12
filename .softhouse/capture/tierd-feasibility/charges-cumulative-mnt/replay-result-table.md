# Replay result table — `LoanChargesCumulativeLoan.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd19`, task OH-TIERD19-CW. Whole-file replay of all
25 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanChargesCumulativeLoan.feature`.

The feature has 25 plain `Scenario:` blocks and no `Scenario Outline`, so the 25
Gherkin scenarios give the 25 rows below, each a distinct loan.  The charge-adjustment
scenario is C2472 at line 126; the charge-off / COB-accrual scenarios are near the end.

Result: **25 scenarios (25 passed, 0 failed)**; 691 steps (691 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C50 | 5 | PASSED | 1 | _(default progressive)_ |
| 2 | C51 | 16 | PASSED | 2 | _(default progressive)_ |
| 3 | C2450 | 27 | PASSED | 3 | _(default progressive)_ |
| 4 | C2451 | 48 | PASSED | 4 | _(default progressive)_ |
| 5 | C2452 | 73 | PASSED | 5 | _(default progressive)_ |
| 6 | C2453 | 100 | PASSED | 6 | _(default progressive)_ |
| 7 | C2472 | 126 | PASSED | 7 | _(default progressive)_ |
| 8 | C2532 | 916 | PASSED | 8 | _(default progressive)_ |
| 9 | C2533 | 932 | PASSED | 9 | _(default progressive)_ |
| 10 | C2534 | 949 | PASSED | 10 | _(default progressive)_ |
| 11 | C2535 | 967 | PASSED | 11 | _(default progressive)_ |
| 12 | C2536 | 988 | PASSED | 12 | _(default progressive)_ |
| 13 | C2537 | 1011 | PASSED | 13 | _(default progressive)_ |
| 14 | C2538 | 1033 | PASSED | 14 | _(default progressive)_ |
| 15 | C2601 | 1055 | PASSED | 15 | _(default progressive)_ |
| 16 | C2606 | 1075 | PASSED | 16 | _(default progressive)_ |
| 17 | C2607 | 1091 | PASSED | 17 | _(default progressive)_ |
| 18 | C2635 | 1107 | PASSED | 18 | _(default progressive)_ |
| 19 | C2672 | 1127 | PASSED | 19 | _(default progressive)_ |
| 20 | C2673 | 1152 | PASSED | 20 | _(default progressive)_ |
| 21 | C2674 | 1176 | PASSED | 21 | `LP1_INTEREST_FLAT` |
| 22 | C2675 | 1204 | PASSED | 22 | `LP1_INTEREST_FLAT_OVERDUE_FROM_AMOUNT` |
| 23 | C2676 | 1238 | PASSED | 23 | `LP1_INTEREST_FLAT_OVERDUE_FROM_AMOUNT_INTEREST` |
| 24 | C2790 | 1272 | PASSED | 24 | _(default progressive)_ |
| 25 | C2909 | 1305 | PASSED | 25 | _(default progressive)_ |

## Failures — 0 scenarios

None. Every scenario passed: the loan-charges-cumulative replay — and with it the
charge-adjustment postings (`createJournalEntriesForChargeAdjustment` →
`...ForLoanChargeAdjustment` / `...ForChargeOffLoanChargeAdjustment`) plus the
charge accrual/waiver/charge-off shapes — was exercised and the oracle agreed
with every `.feature` expectation.