# OWNER — chargeback-mnt capture (OH-TIERD9-BX)

Replay of `fineract-e2e-tests-runner/src/test/resources/features/LoanChargeback-Part1.feature`
with the Feign capture on, in the throwaway reference-oracle tenant `tierd` (MNT).

## Ownership rule

Cucumber ran scenarios sequentially in file order (`--max-workers=1`) and each scenario
creates exactly one loan; loans are numbered by the resourceId returned by `POST /loans`.
Therefore **scenario S*k* owns loan *k*** and **every body under `loans/loan-*k*/`**.
This is corroborated, not merely assumed:
- 50 scenarios, 50 loans, one `create` per loan (counts agree);
- scenario principals/terms match their loan's create-request at distinctive points
  (S1/S2 P=1000 n=1; S3-S6 P=750 n=3; S10-S12 P=3000 n=3; S33 P=1000 n=1;
  S34-S45 P=400 n=3 downpayment product; S46 P=1000 productId 26 progressive-loan-schedule-horizontal;
  S49 P=1000 productId 28 credit-allocation; S50 P=500);
- `manifest-chargeback.json` enumerates every file with `loan_id`, `source_line`, `url`,
  `sha256` and the oracle's HTTP status.

`manifest-chargeback.json` (all 50 loans, `committed: true` on each) and
`manifest-chargeback-passed.json` are identical here because **all 50 scenarios passed**.

## Scenario -> loan -> read-backs

Read-back files are the `detail-*` bodies (loan detail / associations / transactions);
command bodies (`create`/`approve`/`disburse`/`repayment`/`chargeback` request+response)
are captured alongside so a copy is self-contained. Exact names are in the manifest.

| scenario | feature line | loan | read-back dir | read-backs | committed files | result |
|----------|-------------:|-----:|---------------|-----------:|----------------:|--------|
| S1 As an admin I would like to check chargeback function is wor | 5 | 1 | `loans/loan-1/` | 14 | 23 | PASSED |
| S2 As an admin I would like to check chargeback function is wor | 21 | 2 | `loans/loan-2/` | 14 | 23 | PASSED |
| S3 As an admin I would like to check chargeback function is wor | 37 | 3 | `loans/loan-3/` | 17 | 30 | PASSED |
| S4 As an admin I would like to check chargeback function is wor | 57 | 4 | `loans/loan-4/` | 19 | 34 | PASSED |
| S5 As an admin I would like to check chargeback function is wor | 78 | 5 | `loans/loan-5/` | 23 | 40 | PASSED |
| S6 As an admin I would like to check chargeback function is wor | 103 | 6 | `loans/loan-6/` | 27 | 46 | PASSED |
| S7 As an admin I would like to check that the loan goes to ACTI | 133 | 7 | `loans/loan-7/` | 14 | 23 | PASSED |
| S8 As an admin I would like to check that the loan remains OVER | 149 | 8 | `loans/loan-8/` | 14 | 23 | PASSED |
| S9 As an admin I would like to check that the loan goes to CLOS | 165 | 9 | `loans/loan-9/` | 14 | 23 | PASSED |
| S10 As an admin I would like to check that delinquency and overd | 181 | 10 | `loans/loan-10/` | 13 | 24 | PASSED |
| S11 As an admin I would like to check that delinquency and overd | 203 | 11 | `loans/loan-11/` | 16 | 29 | PASSED |
| S12 As an admin I would like to check that delinquency and overd | 223 | 12 | `loans/loan-12/` | 20 | 35 | PASSED |
| S13 As an admin I would like to check that Goodwill credit, Payo | 246 | 13 | `loans/loan-13/` | 32 | 49 | PASSED |
| S14 When charge backs comes in after the loan is closed, before  | 276 | 14 | `loans/loan-14/` | 22 | 35 | PASSED |
| S15 When repayment happens again on the charge backs | 321 | 15 | `loans/loan-15/` | 26 | 41 | PASSED |
| S16 When repayment 1 is reversed | 373 | 16 | `loans/loan-16/` | 28 | 45 | PASSED |
| S17 When 2 repayments are reversed (repayment 1 & 3) | 428 | 17 | `loans/loan-17/` | 30 | 49 | PASSED |
| S18 When chargeback happens after the charge addition on maturit | 486 | 18 | `loans/loan-18/` | 31 | 50 | PASSED |
| S19 When chargeback comes in after the loan overpayment-1 | 555 | 19 | `loans/loan-19/` | 23 | 36 | PASSED |
| S20 When chargeback comes in after the loan overpayment-2 | 603 | 20 | `loans/loan-20/` | 23 | 36 | PASSED |
| S21 When chargeback comes in after the loan overpayment-3 | 651 | 21 | `loans/loan-21/` | 23 | 36 | PASSED |
| S22 When chargeback comes in after the loan overpayment-4 with r | 700 | 22 | `loans/loan-22/` | 26 | 41 | PASSED |
| S23 When charge backs comes in after the loan is closed for the  | 753 | 23 | `loans/loan-23/` | 22 | 35 | PASSED |
| S24 When repayment happens again on the charge backs (after matu | 800 | 24 | `loans/loan-24/` | 26 | 41 | PASSED |
| S25 When repayment 1 is reversed (after maturity) | 853 | 25 | `loans/loan-25/` | 28 | 45 | PASSED |
| S26 When 2 repayments are reversed (repayment 1 & 3) (after matu | 909 | 26 | `loans/loan-26/` | 30 | 49 | PASSED |
| S27 When second charge back happens for the repayment 01-04-2022 | 968 | 27 | `loans/loan-27/` | 30 | 47 | PASSED |
| S28 When chargeback happens after the charge addition on maturit | 1027 | 28 | `loans/loan-28/` | 32 | 51 | PASSED |
| S29 When chargeback comes in after the loan overpayment-1 (after | 1093 | 29 | `loans/loan-29/` | 23 | 36 | PASSED |
| S30 When chargeback comes in after the loan overpayment-2 (after | 1141 | 30 | `loans/loan-30/` | 23 | 36 | PASSED |
| S31 When chargeback comes in after the loan overpayment-3 (after | 1189 | 31 | `loans/loan-31/` | 23 | 36 | PASSED |
| S32 When chargeback comes in after the loan overpayment-4 with r | 1239 | 32 | `loans/loan-32/` | 26 | 41 | PASSED |
| S33 As an admin I would like to verify principal portion for par | 1293 | 33 | `loans/loan-33/` | 29 | 44 | PASSED |
| S34 Verify chargeback function for advanced payment allocation o | 1324 | 34 | `loans/loan-34/` | 21 | 34 | PASSED |
| S35 Verify chargeback function for advanced payment allocation o | 1366 | 35 | `loans/loan-35/` | 21 | 34 | PASSED |
| S36 Verify chargeback function for advanced payment allocation w | 1408 | 36 | `loans/loan-36/` | 23 | 38 | PASSED |
| S37 Verify chargeback function for advanced payment allocation w | 1452 | 37 | `loans/loan-37/` | 23 | 38 | PASSED |
| S38 Verify chargeback function for advanced payment allocation w | 1496 | 38 | `loans/loan-38/` | 23 | 38 | PASSED |
| S39 Verify chargeback function for advanced payment allocation w | 1541 | 39 | `loans/loan-39/` | 23 | 38 | PASSED |
| S40 Verify chargeback function for advanced payment allocation w | 1586 | 40 | `loans/loan-40/` | 25 | 42 | PASSED |
| S41 Verify chargeback function for advanced payment allocation - | 1634 | 41 | `loans/loan-41/` | 21 | 34 | PASSED |
| S42 Verify chargeback function for advanced payment allocation - | 1676 | 42 | `loans/loan-42/` | 21 | 34 | PASSED |
| S43 Verify chargeback function for advanced payment allocation - | 1717 | 43 | `loans/loan-43/` | 21 | 34 | PASSED |
| S44 Verify chargeback function for advanced payment allocation - | 1758 | 44 | `loans/loan-44/` | 20 | 33 | PASSED |
| S45 Verify chargeback function for advanced payment allocation - | 1796 | 45 | `loans/loan-45/` | 30 | 47 | PASSED |
| S46 Verify chargeback function for advanced payment allocation - | 1846 | 46 | `loans/loan-46/` | 31 | 52 | PASSED |
| S47 Verify chargeback function for advanced payment allocation - | 1875 | 47 | `loans/loan-47/` | 12 | 19 | PASSED |
| S48 Verify chargeback function for advanced payment allocation - | 1902 | 48 | `loans/loan-48/` | 12 | 19 | PASSED |
| S49 Verify chargeback function for advanced payment allocation - | 1929 | 49 | `loans/loan-49/` | 14 | 29 | PASSED |
| S50 Verify chargeback function for advanced payment allocation - | 1946 | 50 | `loans/loan-50/` | 26 | 35 | PASSED |

Total: 50 scenarios / 50 loans / 1830 bodies, 100%% committed.

