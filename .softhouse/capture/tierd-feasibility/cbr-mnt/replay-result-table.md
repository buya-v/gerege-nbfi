# Replay result table — `LoanCBR.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd16`, task OH-TIERD16-CO. Whole-file replay of all
41 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanCBR.feature`.

The feature contains one `Scenario Outline` with two `Examples:` blocks; Cucumber
expands it into two scenarios, so the 39 plain `Scenario:` blocks plus 2 outline
examples give the 41 rows below. Each expanded example is a distinct loan.

Result: **41 scenarios (41 passed, 0 failed)**; 1333 steps (1333 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C2505 | 5 | PASSED | 1 | _(default progressive)_ |
| 2 | C2511 | 50 | PASSED | 2 | _(default progressive)_ |
| 3 | C2515 | 88 | PASSED | 3 | _(default progressive)_ |
| 4 | C2516 | 122 | PASSED | 4 | _(default progressive)_ |
| 5 | C2517 | 161 | PASSED | 5 | _(default progressive)_ |
| 6 | C2518 | 202 | PASSED | 6 | _(default progressive)_ |
| 7 | C2519 | 241 | PASSED | 7 | _(default progressive)_ |
| 8 | C2520 | 280 | PASSED | 8 | _(default progressive)_ |
| 9 | C2521 | 319 | PASSED | 9 | _(default progressive)_ |
| 10 | C2522 | 368 | PASSED | 10 | _(default progressive)_ |
| 11 | C2523 | 422 | PASSED | 11 | _(default progressive)_ |
| 12 | C2524 | 455 | PASSED | 12 | _(default progressive)_ |
| 13 | C2525 | 494 | PASSED | 13 | _(default progressive)_ |
| 14 | C2526 | 535 | PASSED | 14 | _(default progressive)_ |
| 15 | C2527 | 574 | PASSED | 15 | _(default progressive)_ |
| 16 | C2528 | 613 | PASSED | 16 | _(default progressive)_ |
| 17 | C2529 | 652 | PASSED | 17 | _(default progressive)_ |
| 18 | C2530 | 701 | PASSED | 18 | _(default progressive)_ |
| 19 | C2841 | 755 | PASSED | 19 | _(default progressive)_ |
| 20 | C2885 | 804 | PASSED | 20 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 21 | C2886 | 875 | PASSED | 21 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 22 | C2887 | 941 | PASSED | 22 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 23 | C2888 | 1018 | PASSED | 23 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 24 | C2889 | 1091 | PASSED | 24 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 25 | C2890 | 1170 | PASSED | 25 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 26 | C2989 | 1240 | PASSED | 26 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 27 | C3020 | 1258 | PASSED | 27 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 28 | C3021 | 1305 | PASSED | 28 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 29 | C3040 | 1351 | PASSED | 29 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 30 | C3041 | 1427 | PASSED | 30 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 31 | C3092 | 1496 | PASSED | 31 | `LP2_DOWNPAYMENT_ADVANCED_PAYMENT_ALLOCATION` |
| 32 | C3140 | 1541 | PASSED | 32 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 33 | C3203 | 1653 | PASSED | 33 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 34 | C3734 | 1677 | PASSED | 34 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_CUSTOM_PAYMENT_ALLOCATION` |
| 35 | C78812 | 1874 | PASSED | 35 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF_ACC_LAST_INSTALLMENT` |
| 36 | C78853 | 1879 | PASSED | 36 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF_ACCRUAL_ACTIVITY` |
| 37 | C78851 | 1882 | PASSED | 37 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF_ACC_LAST_INSTALLMENT` |
| 38 | C78852 | 1912 | PASSED | 38 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_INT_REFUND_FULL_ZERO_INT_CHARGE_OFF_ACC_LAST_INSTALLMENT` |
| 39 | C85446 | 1943 | PASSED | 39 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ACC_MATUR_CHARGE_OFF` |
| 40 | C85447 | 2078 | PASSED | 40 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ACC_MATUR_CHARGE_OFF` |
| 41 | C85448 | 2121 | PASSED | 41 | `LP2_ADV_PYMNT_INT_DAILY_EMI_ACTUAL_ACTUAL_NO_INTEREST_RECALC_INT_REFUND_FULL_ACC_MATUR_CHARGE_OFF` |

## Failures — 0 scenarios

None. Every scenario passed: the CBR replay — and with it the credit-balance-refund
posting (`createJournalEntriesForCreditBalanceRefund` /
`createJournalEntriesForLoanCreditBalanceRefund`) plus the charged-off, payoutRefund
and goodwillCredit shapes — was exercised and the oracle agreed with every
`.feature` expectation.