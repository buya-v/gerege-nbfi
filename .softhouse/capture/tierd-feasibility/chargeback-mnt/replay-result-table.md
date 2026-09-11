# OH-TIERD9-BX — `LoanChargeback-Part1.feature` replay result (MNT)

- feature file: `fineract-e2e-tests-runner/src/test/resources/features/LoanChargeback-Part1.feature`
- worktree (disposable copy): `/Users/buv/fineract-tierd`, branch `develop`, HEAD `426a23544e8426a38ae43ae404670a0a7e85b9eb`
- run window (UTC): `2026-09-11T13:52:55Z` -> `2026-09-11T13:54:31Z`
- cucumber: **50 scenarios (50 passed), 1367 steps (1367 passed)**; `BUILD SUCCESSFUL in 1m 35s` (no recompile — all tasks UP-TO-DATE)
- tenant: `tierd` (Asia/Ulaanbaatar), currency **MNT**; the Feign log holds 0 `EUR` tokens and 1524 `MNT` tokens
- Feign capture: `feign-chargeback-mnt.log`, 253580995 bytes, sha256 `bb21464b3094e8461caa982e57359ac177a1dc758c7eb8d43f20da6704db6557`
- cucumber log: `replay-chargeback-mnt.log`, sha256 `e5810ae0aab305e0e49a8eb54c6e33dc46285f70de3f6886d3004e25daf9a322`
- extractor: 5402 exchanges total, 1504 loan-attributed, 50 loans, 1830 bodies written

**Every scenario passed, so every loan is committed.** A failure would have been recorded here as a
finding (step, actual vs expected); none occurred.

| # | feature line | scenario | loan | read-backs | all files | result |
|---|-------------:|----------|-----:|-----------:|----------:|--------|
| S1 | 5 | As an admin I would like to check chargeback function is working properly on a closed loan in case of payment  | 1 | 14 | 23 | **PASSED** |
| S2 | 21 | As an admin I would like to check chargeback function is working properly on a closed loan in case of payment  | 2 | 14 | 23 | **PASSED** |
| S3 | 37 | As an admin I would like to check chargeback function is working properly when chargeback comes after the loan | 3 | 17 | 30 | **PASSED** |
| S4 | 57 | As an admin I would like to check chargeback function is working properly when repayment happens again after c | 4 | 19 | 34 | **PASSED** |
| S5 | 78 | As an admin I would like to check chargeback function is working properly when a second chargeback happens aft | 5 | 23 | 40 | **PASSED** |
| S6 | 103 | As an admin I would like to check chargeback function is working properly when chargeback happens after NSF fe | 6 | 27 | 46 | **PASSED** |
| S7 | 133 | As an admin I would like to check that the loan goes to ACTIVE when the loan is OVERPAID but the chargeback am | 7 | 14 | 23 | **PASSED** |
| S8 | 149 | As an admin I would like to check that the loan remains OVERPAID when the loan is OVERPAID but the chargeback  | 8 | 14 | 23 | **PASSED** |
| S9 | 165 | As an admin I would like to check that the loan goes to CLOSED when the loan is OVERPAID but the chargeback am | 9 | 14 | 23 | **PASSED** |
| S10 | 181 | As an admin I would like to check that delinquency and overdue treatment of chargeback works properly | 10 | 13 | 24 | **PASSED** |
| S11 | 203 | As an admin I would like to check that delinquency and overdue treatment of chargeback works properly when all | 11 | 16 | 29 | **PASSED** |
| S12 | 223 | As an admin I would like to check that delinquency and overdue treatment of chargeback works properly when all | 12 | 20 | 35 | **PASSED** |
| S13 | 246 | As an admin I would like to check that Goodwill credit, Payout refund, Merchant Issued refund works properly w | 13 | 32 | 49 | **PASSED** |
| S14 | 276 | When charge backs comes in after the loan is closed, before the maturity date | 14 | 22 | 35 | **PASSED** |
| S15 | 321 | When repayment happens again on the charge backs | 15 | 26 | 41 | **PASSED** |
| S16 | 373 | When repayment 1 is reversed | 16 | 28 | 45 | **PASSED** |
| S17 | 428 | When 2 repayments are reversed (repayment 1 & 3) | 17 | 30 | 49 | **PASSED** |
| S18 | 486 | When chargeback happens after the charge addition on maturity date for repayment 01-03-2022 | 18 | 31 | 50 | **PASSED** |
| S19 | 555 | When chargeback comes in after the loan overpayment-1 | 19 | 23 | 36 | **PASSED** |
| S20 | 603 | When chargeback comes in after the loan overpayment-2 | 20 | 23 | 36 | **PASSED** |
| S21 | 651 | When chargeback comes in after the loan overpayment-3 | 21 | 23 | 36 | **PASSED** |
| S22 | 700 | When chargeback comes in after the loan overpayment-4 with reverse and replay | 22 | 26 | 41 | **PASSED** |
| S23 | 753 | When charge backs comes in after the loan is closed for the repayment 01-03-2022 (after maturity) | 23 | 22 | 35 | **PASSED** |
| S24 | 800 | When repayment happens again on the charge backs (after maturity) | 24 | 26 | 41 | **PASSED** |
| S25 | 853 | When repayment 1 is reversed (after maturity) | 25 | 28 | 45 | **PASSED** |
| S26 | 909 | When 2 repayments are reversed (repayment 1 & 3) (after maturity) | 26 | 30 | 49 | **PASSED** |
| S27 | 968 | When second charge back happens for the repayment 01-04-2022 (after maturity) | 27 | 30 | 47 | **PASSED** |
| S28 | 1027 | When chargeback happens after the charge addition on maturity date for repayment 01-03-2022 (after maturity) | 28 | 32 | 51 | **PASSED** |
| S29 | 1093 | When chargeback comes in after the loan overpayment-1 (after maturity) | 29 | 23 | 36 | **PASSED** |
| S30 | 1141 | When chargeback comes in after the loan overpayment-2 (after maturity) | 30 | 23 | 36 | **PASSED** |
| S31 | 1189 | When chargeback comes in after the loan overpayment-3 (after maturity) | 31 | 23 | 36 | **PASSED** |
| S32 | 1239 | When chargeback comes in after the loan overpayment-4 with reverse and replay (after maturity) | 32 | 26 | 41 | **PASSED** |
| S33 | 1293 | As an admin I would like to verify principal portion for partial chargeback for OVERPAID loan | 33 | 29 | 44 | **PASSED** |
| S34 | 1324 | Verify chargeback function for advanced payment allocation on a closed loan in case of payment type: REPAYMENT | 34 | 21 | 34 | **PASSED** |
| S35 | 1366 | Verify chargeback function for advanced payment allocation on a closed loan in case of payment type: REPAYMENT | 35 | 21 | 34 | **PASSED** |
| S36 | 1408 | Verify chargeback function for advanced payment allocation when full repayment happens after chargeback, on th | 36 | 23 | 38 | **PASSED** |
| S37 | 1452 | Verify chargeback function for advanced payment allocation when partial repayment happens after chargeback, on | 37 | 23 | 38 | **PASSED** |
| S38 | 1496 | Verify chargeback function for advanced payment allocation when full repayment happens after chargeback, on a  | 38 | 23 | 38 | **PASSED** |
| S39 | 1541 | Verify chargeback function for advanced payment allocation when partial repayment happens after chargeback, on | 39 | 23 | 38 | **PASSED** |
| S40 | 1586 | Verify chargeback function for advanced payment allocation when a second chargeback happens after the repaymen | 40 | 25 | 42 | **PASSED** |
| S41 | 1634 | Verify chargeback function for advanced payment allocation -loan goes to ACTIVE when the it is OVERPAID but th | 41 | 21 | 34 | **PASSED** |
| S42 | 1676 | Verify chargeback function for advanced payment allocation -loan remains OVERPAID when the it is OVERPAID but  | 42 | 21 | 34 | **PASSED** |
| S43 | 1717 | Verify chargeback function for advanced payment allocation -loan goes to CLOSED when the loan is OVERPAID but  | 43 | 21 | 34 | **PASSED** |
| S44 | 1758 | Verify chargeback function for advanced payment allocation - chargeback after the loan is closed, before the m | 44 | 20 | 33 | **PASSED** |
| S45 | 1796 | Verify chargeback function for advanced payment allocation - repayment 1 is reversed | 45 | 30 | 47 | **PASSED** |
| S46 | 1846 | Verify chargeback function for advanced payment allocation - overpayment handling | 46 | 31 | 52 | **PASSED** |
| S47 | 1875 | Verify chargeback function for advanced payment allocation - chargeback on downpayment | 47 | 12 | 19 | **PASSED** |
| S48 | 1902 | Verify chargeback function for advanced payment allocation - partial chargeback on downpayment | 48 | 12 | 19 | **PASSED** |
| S49 | 1929 | Verify chargeback function for advanced payment allocation - credit allocation UC1 | 49 | 14 | 29 | **PASSED** |
| S50 | 1946 | Verify chargeback function for advanced payment allocation - full chargeback on overpaid loan | 50 | 26 | 35 | **PASSED** |
