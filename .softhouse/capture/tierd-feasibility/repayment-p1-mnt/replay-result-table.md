# Replay result table — `LoanRepayment-Part1.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd21`, task OH-TIERD21-DA. Whole-file replay of all
50 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanRepayment-Part1.feature`.

The feature has 49 plain `Scenario:` blocks and one `Scenario Outline:` (one example
row), so the 50 Gherkin scenarios give the 50 rows below, each a distinct loan. The
goodwill-credit and charge-off scenarios are concentrated near the end of the file.

Result: **50 scenarios (50 passed, 0 failed)**; 795 steps (795 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C49 | 15 | PASSED | 1 | _(default progressive)_ |
| 2 | C32 | 18 | PASSED | 2 | _(default progressive)_ |
| 3 | C44 | 28 | PASSED | 3 | _(default progressive)_ |
| 4 | C45 | 38 | PASSED | 4 | _(default progressive)_ |
| 5 | C2430 | 49 | PASSED | 5 | _(default progressive)_ |
| 6 | C2431 | 60 | PASSED | 6 | _(default progressive)_ |
| 7 | C2432 | 71 | PASSED | 7 | _(default progressive)_ |
| 8 | C2433 | 82 | PASSED | 8 | _(default progressive)_ |
| 9 | C2434 | 93 | PASSED | 9 | _(default progressive)_ |
| 10 | C2435 | 104 | PASSED | 10 | _(default progressive)_ |
| 11 | C2436 | 115 | PASSED | 11 | _(default progressive)_ |
| 12 | C2437 | 126 | PASSED | 12 | _(default progressive)_ |
| 13 | C2464 | 137 | PASSED | 13 | _(default progressive)_ |
| 14 | C2465 | 155 | PASSED | 14 | _(default progressive)_ |
| 15 | C2466 | 173 | PASSED | 15 | _(default progressive)_ |
| 16 | C2467 | 191 | PASSED | 16 | _(default progressive)_ |
| 17 | C2468 | 209 | PASSED | 17 | _(default progressive)_ |
| 18 | C2469 | 227 | PASSED | 18 | _(default progressive)_ |
| 19 | C2470 | 245 | PASSED | 19 | _(default progressive)_ |
| 20 | C2471 | 263 | PASSED | 20 | _(default progressive)_ |
| 21 | C2485 | 281 | PASSED | 21 | _(default progressive)_ |
| 22 | C2689 | 295 | PASSED | 22 | `LP1_DUE_DATE` |
| 23 | C2490 | 311 | PASSED | 23 | `LP1_INTEREST_FLAT` |
| 24 | C2492 | 343 | PASSED | 24 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 25 | C2493 | 375 | PASSED | 25 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` |
| 26 | C2494 | 407 | PASSED | 26 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 27 | C2495 | 439 | PASSED | 27 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 28 | C2496 | 471 | PASSED | 28 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 29 | C2497 | 503 | PASSED | 29 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_SAME_AS_PAYMENT` |
| 30 | C2498 | 535 | PASSED | 30 | _(default progressive)_ |
| 31 | C2499 | 547 | PASSED | 31 | _(default progressive)_ |
| 32 | C2500 | 559 | PASSED | 32 | _(default progressive)_ |
| 33 | C2531 | 571 | PASSED | 33 | _(default progressive)_ |
| 34 | C2555 | 582 | PASSED | 34 | `LP1_1MONTH_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_MONTHLY` |
| 35 | C2556 | 606 | PASSED | 35 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 36 | C2557 | 630 | PASSED | 36 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 37 | C2558 | 654 | PASSED | 37 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 38 | C2559 | 678 | PASSED | 38 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 39 | C2560 | 702 | PASSED | 39 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 40 | C2561 | 726 | PASSED | 40 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 41 | C2562 | 750 | PASSED | 41 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 42 | C2563 | 774 | PASSED | 42 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 43 | C2564 | 798 | PASSED | 43 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 44 | C2625 | 822 | PASSED | 44 | `LP1_INTEREST_FLAT` |
| 45 | C2626 | 861 | PASSED | 45 | `LP1_INTEREST_FLAT` |
| 46 | C2627 | 907 | PASSED | 46 | `LP1_INTEREST_FLAT` |
| 47 | C2628 | 952 | PASSED | 47 | `LP1_INTEREST_FLAT` |
| 48 | C2629 | 1004 | PASSED | 48 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_RESCHEDULE_REDUCE_NR_INST` |
| 49 | C2630 | 1029 | PASSED | 49 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE` |
| 50 | C2631 | 1055 | PASSED | 50 | `LP1_INTEREST_DECLINING_BALANCE_DAILY_RECALCULATION_COMPOUNDING_NONE_RESCHEDULE_RESCH_NEXT_REP` |

## Failures — 0 scenarios

None. Every scenario passed: the loan-repayment Part 1 replay — and with it the
repayment postings (principal/interest/fee/penalty portions), the channel-mapped
payment types, the repayments on charged-off loans and the goodwill credits — was
exercised and the oracle agreed with every `.feature` expectation.