# Replay result table — `LoanWriteOff.feature` in MNT

Worktree `/Users/buv/oh-gerege-tierd10`, task OH-TIERD10-CA. Whole-file replay of all
12 scenarios against the throwaway reference oracle (tenant `tierd`), with the Feign
capture on. Capture only: no vector, no drive, no `.go`. Money in the tables below is
integer minor units (MNT, 2 ISO 4217 digits); the raw oracle bodies carry the decimal
major units the oracle emitted. Feature line numbers are from
`fineract-e2e-tests-runner/src/test/resources/features/LoanWriteOff.feature`.

Result: **12 scenarios (12 passed, 0 failed)**; 257 steps (257 passed, 0 skipped, 0 failed).

| # | TestRailId | feature line | result | loan | product |
| --- | --- | --- | --- | --- | --- |
| 1 | C2934 | 5 | PASSED | 1 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 2 | C2935 | 25 | PASSED | 2 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 3 | C2936 | 45 | PASSED | 3 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 4 | C4006 | 64 | PASSED | 4 | `LP1_INTEREST_FLAT` |
| 5 | C4007 | 100 | PASSED | 5 | `LP1_INTEREST_FLAT` |
| 6 | C4010 | 126 | PASSED | 6 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1` |
| 7 | C4011 | 193 | PASSED | 7 | `LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF` |
| 8 | C4012 | 281 | PASSED | 8 | `LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON` |
| 9 | C4013 | 330 | PASSED | 9 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` |
| 10 | C4111 | 368 | PASSED | 10 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_WRITE_OFF_REASON_MAP` |
| 11 | C4112 | 401 | PASSED | 11 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_WRITE_OFF_REASON_MAP` |
| 12 | C4113 | 434 | PASSED | 12 | `LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CLASSIFICATION_INCOME_MAP` |

## Failures — 0 scenarios

None. Every scenario passed: the charged-off write-off branch
(`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`) was exercised and the oracle
agreed with every `.feature` journal-entry expectation.