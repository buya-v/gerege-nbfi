# Replay result table — `LoanChargeOff-Part1.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd8`, task OH-TIERD8-BW. Whole-file replay of all
50 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanChargeOff-Part1.feature`.

Result: **50 scenarios (50 passed, 0 failed)**; 1106 steps (1106 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C2565 | 5 | PASSED | 1 | _(default progressive)_ |
| 2 | C2566 | 25 | PASSED | 2 | _(default progressive)_ |
| 3 | C2567 | 51 | PASSED | 3 | _(default progressive)_ |
| 4 | C2568 | 81 | PASSED | 4 | _(default progressive)_ |
| 5 | C2569 | 104 | PASSED | 5 | _(default progressive)_ |
| 6 | C2570 | 133 | PASSED | 6 | _(default progressive)_ |
| 7 | C2571 | 157 | PASSED | 7 | `LP1_INTEREST_FLAT` |
| 8 | C2572 | 184 | PASSED | 8 | `LP1_INTEREST_FLAT` |
| 9 | C2573 | 218 | PASSED | 9 | `LP1_INTEREST_FLAT` |
| 10 | C2574 | 252 | PASSED | 10 | `LP1_INTEREST_FLAT` |
| 11 | C2575 | 284 | PASSED | 11 | _(default progressive)_ |
| 12 | C2576 | 305 | PASSED | 12 | _(default progressive)_ |
| 13 | C2577 | 336 | PASSED | 13 | _(default progressive)_ |
| 14 | C2578 | 360 | PASSED | 14 | _(default progressive)_ |
| 15 | C2579 | 385 | PASSED | 15 | `LP1_INTEREST_FLAT` |
| 16 | C2580 | 413 | PASSED | 16 | `LP1_INTEREST_FLAT` |
| 17 | C2581 | 448 | PASSED | 17 | `LP1_INTEREST_FLAT` |
| 18 | C2582 | 483 | PASSED | 18 | `LP1_INTEREST_FLAT` |
| 19 | C2591 | 516 | PASSED | 19 | `LP1_INTEREST_FLAT` |
| 20 | C2592 | 567 | PASSED | 20 | `LP1_INTEREST_FLAT` |
| 21 | C2593 | 627 | PASSED | 21 | _(default progressive)_ |
| 22 | C2594 | 654 | PASSED | 22 | _(default progressive)_ |
| 23 | C2595 | 683 | PASSED | 23 | _(default progressive)_ |
| 24 | C2596 | 708 | PASSED | 24 | _(default progressive)_ |
| 25 | C2597 | 729 | PASSED | 25 | _(default progressive)_ |
| 26 | C2598 | 749 | PASSED | 26 | _(default progressive)_ |
| 27 | C2599 | 775 | PASSED | 27 | _(default progressive)_ |
| 28 | C2600 | 798 | PASSED | 28 | _(default progressive)_ |
| 29 | C2706 | 824 | PASSED | 29 | `LP1_INTEREST_FLAT` |
| 30 | C2761 | 852 | PASSED | 30 | _(default progressive)_ |
| 31 | C3568 | 893 | PASSED | 31 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ACCRUAL_ACTIVITY_POSTING` |
| 32 | C2762 | 967 | PASSED | 32 | _(default progressive)_ |
| 33 | C2763 | 1014 | PASSED | 33 | _(default progressive)_ |
| 34 | C2764 | 1061 | PASSED | 34 | _(default progressive)_ |
| 35 | C2765 | 1100 | PASSED | 35 | _(default progressive)_ |
| 36 | C2766 | 1126 | PASSED | 36 | _(default progressive)_ |
| 37 | C2767 | 1149 | PASSED | 37 | _(default progressive)_ |
| 38 | C2768 | 1210 | PASSED | 38 | _(default progressive)_ |
| 39 | C2779 | 1238 | PASSED | 39 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` |
| 40 | C2780 | 1284 | PASSED | 40 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` |
| 41 | C2781 | 1337 | PASSED | 41 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` |
| 42 | C3545 | 1387 | PASSED | 42 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY_INT_RECALC` |
| 43 | C2782 | 1474 | PASSED | 43 | _(default progressive)_ |
| 44 | C2891 | 1536 | PASSED | 44 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 45 | C2892 | 1563 | PASSED | 45 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 46 | C2893 | 1585 | PASSED | 46 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 47 | C2894 | 1613 | PASSED | 47 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 48 | C2895 | 1645 | PASSED | 48 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 49 | C2896 | 1672 | PASSED | 49 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 50 | C3067 | 1704 | PASSED | 50 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |

## Failures — 0 scenarios

None. Every scenario passed: the charged-off write-off branch
(`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`) was exercised and the oracle
agreed with every `.feature` journal-entry expectation.