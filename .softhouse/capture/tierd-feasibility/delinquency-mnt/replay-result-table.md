# OH-TIERD6-BS — `LoanDelinquency-Part1.feature` replayed in MNT: 50/50 PASS (capture only)

Worktree `/Users/buv/oh-gerege-tierd6`, branch `feat/OHTIERD6bs`. Whole-file replay of
`LoanDelinquency-Part1.feature` (50 scenarios, installment-level delinquency and delinquency
PAUSE periods) against the throwaway reference oracle on the disposable MNT-reseeded copy
`/Users/buv/fineract-tierd`, tenant `tierd`, Feign capture on. This is capture only: **no vector,
no drive, no `.go`**.

## Run

* Driver: `run-delinquency-mnt.sh` (copy of OH-TIERD5-BP's `run-repsched-mnt.sh`; only `FEATURE`
  and `LOG` changed). Raw log: `replay-delinquency-mnt.log` (1,745 lines).
* Window: `2026-09-11T11:51:42Z` → `11:53:02Z` (1m 5.562s test time; BUILD SUCCESSFUL in 1m 19s).
* Throwaway: tenant `tierd`, image `fineract:latest` =
  `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, `Europe/Amsterdam`,
  rounding mode 4. Business-date moves stayed inside the throwaway tenant only.
* Result: **50 scenarios (50 passed); 1124 steps (1124 passed). No failure.**

```
50 scenarios (50 passed)
1124 steps (1124 passed)
1m 5.562s
```

## Result table

Loan ids are the Feign `resourceId`s. Scenario 33 (C3014) deliberately creates a loan that
fails validation, so it owns no loan id (the run's single unattributed `POST /loans`); loan ids
are contiguous 1..49 over scenarios 1..32, 34..50. The mapping is validated, not assumed: each
loan's read-back `loanProductName` equals that scenario's feature product name and its `clientId`
equals the scenario position (see `attribute.py`).

| # | TestRailId | scenario | feature line | loan | result |
| --- | --- | --- | --- | --- | --- |
| 1 | C2963 | Verify Loan delinquency pause API - PAUSE and RESUME by loanId | 5 | 1 | PASSED |
| 2 | C2964 | Verify Loan delinquency pause API - PAUSE and RESUME by loanExternalId | 26 | 2 | PASSED |
| 3 | C2965 | Verify Loan delinquency pause API - PAUSE and RESUME actions supported only | 47 | 3 | PASSED |
| 4 | C2966 | Verify Loan delinquency pause API - PAUSE with start date on actual business date | 69 | 4 | PASSED |
| 5 | C2967 | Verify Loan delinquency pause API - PAUSE with start date later than actual business date | 84 | 5 | PASSED |
| 6 | C2968 | Verify Loan delinquency pause API - PAUSE with start date before than actual business date is possible | 99 | 6 | PASSED |
| 7 | C2969 | Verify Loan delinquency pause API - PAUSE action on non-active loan result an error | 114 | 7 | PASSED |
| 8 | C2970 | Verify Loan delinquency pause API - RESUME action on non-active loan result an error | 139 | 8 | PASSED |
| 9 | C2971 | Verify Loan delinquency pause API - Overlapping PAUSE periods result an error | 162 | 9 | PASSED |
| 10 | C2972 | Verify Loan delinquency pause API - RESUME without an active PAUSE period results an error | 179 | 10 | PASSED |
| 11 | C2973 | Verify Loan delinquency pause API - RESUME with start date before than actual business date results an error | 190 | 11 | PASSED |
| 12 | C2974 | Verify Loan delinquency pause API - RESUME with start date later than actual business date results an error | 207 | 12 | PASSED |
| 13 | C2975 | Verify Loan delinquency pause API - RESUME with end date results an error | 224 | 13 | PASSED |
| 14 | C2992 | Verify Loan level loan delinquency - loan goes into delinquency pause then will be resumed | 241 | 14 | PASSED |
| 15 | C2979 | Verify Installment level loan delinquency - loan goes into delinquency bucket | 269 | 15 | PASSED |
| 16 | C2980 | Verify Installment level loan delinquency - loan goes from one delinquency bucket to an other | 286 | 16 | PASSED |
| 17 | C2981 | Verify Installment level loan delinquency - loan goes out from delinquency by late repayment | 311 | 17 | PASSED |
| 18 | C2982 | Verify Installment level loan delinquency - some of the installments go out from delinquency by late repayment | 332 | 18 | PASSED |
| 19 | C2983 | Verify Installment level loan delinquency - loan goes out from delinquency by Goodwill credit transaction | 354 | 19 | PASSED |
| 20 | C2984 | Verify Installment level loan delinquency - some of the installments go out from delinquency by Goodwill credit transaction | 375 | 20 | PASSED |
| 21 | C2985 | Verify Installment level loan delinquency - loan with charges goes into delinquency bucket | 397 | 21 | PASSED |
| 22 | C2987 | Verify Installment level loan delinquency - loan goes into delinquency pause | 417 | 22 | PASSED |
| 23 | C2988 | Verify Installment level loan delinquency - loan goes into delinquency pause then will be resumed | 467 | 23 | PASSED |
| 24 | C2990 | Verify that a non-super user with CREATE_DELINQUENCY_ACTION permission can initiate a DELINQUENCY PAUSE | 513 | 24 | PASSED |
| 25 | C2991 | Verify that a non-super user with no CREATE_DELINQUENCY_ACTION permission gets an error when initiate a DELINQUENCY PAUSE | 531 | 25 | PASSED |
| 26 | C2999 | Verify Loan delinquency pause E2E - full PAUSE period | 545 | 26 | PASSED |
| 27 | C3000 | Verify Loan delinquency pause E2E - PAUSE period with RESUME | 617 | 27 | PASSED |
| 28 | C3001 | Verify Loan delinquency pause E2E - PAUSE period with RESUME and second PAUSE | 667 | 28 | PASSED |
| 29 | C3002 | Verify Loan delinquency pause E2E - full repayment (late/due date) during PAUSE period | 797 | 29 | PASSED |
| 30 | C3003 | Verify Loan delinquency pause E2E - partial repayment during PAUSE period | 853 | 30 | PASSED |
| 31 | C3004 | Verify Loan delinquency pause E2E - full repayment (only late) during PAUSE period then RESUME | 912 | 31 | PASSED |
| 32 | C3013 | Verify that in case of resume on end/start date of continous pause periods first period ends automatically, second period ended by resume | 1005 | 32 | PASSED |
| 33 | C3014 | Verify that creating a loan with Advanced payment allocation with product no Advanced payment allocation set results an error | 1070 | — | PASSED |
| 34 | C3015 | Verify Backdated Pause Delinquency - Event Trigger: LoanDelinquencyRangeChangeBusinessEvent, LoanAccountDelinquencyPauseChangedBusinessEvent check | 1078 | 33 | PASSED |
| 35 | C3016 | Verify that for pause period calculations business date is being used instead of COB date | 1113 | 34 | PASSED |
| 36 | C3018 | Verify that if Global configuration: next-payment-due-date is set to: earliest-unpaid-date then in Loan details delinquent.nextPaymentDueDate will be the first unpaid installment date | 1168 | 35 | PASSED |
| 37 | C3019 | Verify that if Global configuration: next-payment-due-date is set to: next-unpaid-due-date then in Loan details delinquent.nextPaymentDueDate will be the next unpaid installment date regardless of the status of previous installments | 1184 | 36 | PASSED |
| 38 | C3032 | Verify that delinquencyRange field in LoanAccountDelinquencyRangeDataV1 is not null in case of delinquent Loan | 1200 | 37 | PASSED |
| 39 | C3035 | Verify that delinquency is NOT applied after loan submitted and approved | 1216 | 38 | PASSED |
| 40 | C3047 | Verify that delinquent.lastRepaymentAmount is calculated correctly in case of auto downpayment | 1231 | 39 | PASSED |
| 41 | C3066 | Verify that on Loans in SUBMITTED_AND_PENDING_APPROVAL or APPROVED status delinquency is not applied | 1243 | 40 | PASSED |
| 42 | C3135 | Verify that the delinquency is not applied on Loan with Rejected status | 1257 | 41 | PASSED |
| 43 | C3136 | Verify that the delinquency is not applied on Loan with Withdrawn status | 1282 | 42 | PASSED |
| 44 | C3137 | Verify Installment level loan delinquency can be applied on loan account level in case of non-installment level delinquency loan product | 1307 | 43 | PASSED |
| 45 | C3930 | Verify nextPaymentAmount value with repayment on first installment - progressive loan, no interest recalculation, zero interest rate - UC1 | 1324 | 44 | PASSED |
| 46 | C3931 | Verify nextPaymentAmount value with penalty on first installment - progressive loan, no interest recalculation, non-zero interest rate - UC2 | 1394 | 45 | PASSED |
| 47 | C3932 | Verify nextPaymentAmount value with repayment at 2nd installment - progressive loan, no interest recalculation, the same as repayment period - UC3 | 1460 | 46 | PASSED |
| 48 | C3933 | Verify nextPaymentAmount value - progressive loan, interest recalculation daily - UC4 | 1524 | 47 | PASSED |
| 49 | C3934 | Verify nextPaymentAmount value with chargeback - progressive loan, interest recalculation daily - UC5 | 1586 | 48 | PASSED |
| 50 | C3935 | Verify nextPaymentAmount value with full repayment on first installment - progressive loan, interest recalculation daily - UC6 | 1658 | 49 | PASSED |

## Notes

* **No failures.** Every scenario that asserts the installment-level delinquency
  (`AggregateInstallmentDelinquency`) and PAUSE-period / grace behaviour of `DelinquentDays`
  reproduced the checked-in `.feature` expectations under MNT. There is no failed step and no
  failed value to record.
* One loan-creation attempt is deliberately made to fail (scenario 33, C3014: a loan product
  without `Advanced payment allocation` used with that strategy). Its `POST /loans` returns no
  `resourceId`, which the extractor counts as the run's single `unattributed_creates`; this is the
  expected outcome of an error scenario, not a replay failure.
* `extract.py` classifies `/loans/external-id/<uuid>/<sub-path>` (used by the PAUSE/RESUME-by-
  externalId and delinquency-action scenarios) as a bare create because the route has no numeric
  loan id; its response `resourceId` still resolves to the correct loan, so those bodies are
  attached to the right loan (three loans consequently show a second `create-request` body).
  This is an extractor labelling nuance, not a loss of data.
