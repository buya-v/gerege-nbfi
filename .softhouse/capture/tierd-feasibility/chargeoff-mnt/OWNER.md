# OWNER — Tier D `LoanChargeOff-Part1.feature` MNT capture

This directory owns the MNT read-backs captured by replaying the **whole**
`LoanChargeOff-Part1.feature` (50 scenarios: charge-off after disbursement, after
repayment, after undo, fraud vs non-fraud, NSF/processing/penalty fees, goodwill,
reschedules and re-ages) against the throwaway reference oracle, tenant `tierd`.
Capture only: no vector, no drive, no `.go`.  Money in the tables, manifests and this
file is integer minor units (MNT, 2 ISO 4217 minor digits); the raw oracle bodies under
`loans/` carry the decimal major units the oracle emitted, unchanged.

The journal entries observed here are the **charge-off posting** —
`createJournalEntriesForChargeOff` [AccrualBasedAccountingProcessorForLoan.java:890] — on
31 charge-off transactions (fraud and non-fraud; principal, interest and fee legs), and
**repayments on a charged-off loan** (`createJournalEntriesForRepaymentWhenLoanIsChargedOff`,
:1388; 5 transactions credit `Recoveries`).  No previous capture had observed either.

CORRECTION (driver, 2026-09-11, after merge 77697e49): an earlier text of this file said the
capture reached the charged-off **write-off** branch
(`createJournalEntriesForWriteOffsWhenLoanIsChargedOff`, :1616).  It does not: the read-backs
under `loans/` contain **no** `writeOff` transaction (types seen: disbursement 50, chargeOff 59,
accrual 70, repayment 25, downPayment 7, merchantIssuedRefund 3, payoutRefund 2,
accrualActivity 2, goodwillCredit 2).  That branch remains UNOBSERVED.  See
`.softhouse/findings/F-2026-09-11-tierd-chargeoff-branch-mislabel.md`.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file: feature, each scenario, its loans, and which read-back files belong to it |
| `replay-result-table.md` | the per-scenario PASSED/FAILED result table |
| `replay-chargeoff-mnt.log` | raw cucumber/Gradle replay log, 98211 lines |
| `run-chargeoff-mnt.sh` | the exact driver used for the replay |
| `scenario-results.json` | machine-readable per-scenario result, loan mapping and failed steps |
| `build-results.py` | parses the replay log and feature into the result tables |
| `organize.py` | copies committed bodies into `loans/` and writes the manifests |
| `owner.py` | generates this file |
| `manifest-chargeoff.json` | full extraction manifest (all 1267 bodies, `committed` flag) |
| `manifest-chargeoff-passed.json` | manifest of the committed bodies (1267) |
| `summary-chargeoff.json` | extractor totals and per-loan counts |
| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |
| `journalentries/loan-<id>/` | the observed GL journal entries of the charge-off posting and charged-off repayments (85 responses, 33 loans) |
| `journalentries-manifest.json` | per-response metadata: loan, source line, sha256, GL legs in integer minor units |
| `journalentries-summary.json` | journal-entry totals and GL-account leg counts |
| `extract-journalentries.py` | the supplementary extractor for the `/journalentries` bodies |
| `product-mappings/` | the observed loan-product GL account mappings the charge-off posting resolves through (oracle `retrieveOneLoanProduct` echo + accepted create requests for LP1 / LP1_INTEREST_FLAT; sha256 in `product-mappings/manifest.json`) |
| `extract-product-mappings.py` | extracts `product-mappings/` from the raw Feign log |
| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |

## Source

- feature: `fineract-e2e-tests-runner/src/test/resources/features/LoanChargeOff-Part1.feature`
- throwaway tenant `tierd`; image `fineract:latest` `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`
  (proven identical to the standing reference oracle by `preflight.sh`)
- currency MNT (2 ISO 4217 minor digits, 496); money below is integer minor units
- capture: `/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-chargeoff-mnt.log`
- capture size: 232032919 B / 98211 lines
- extraction: 3714 exchanges, 1010 loan-keyed, 50 loans, 1267 files, 8037943 kept body bytes
- replay: **50 scenarios (50 passed, 0 failed)**; 1106 steps (1106 passed, 0 skipped, 0 failed)
- charge-off coverage: 133 charge-off steps in the feature

## Scenario → loan map

Every scenario creates exactly one client and one loan at the top, in feature order, so
scenario `k` owns loan `k` (50 scenarios, 50 loans).  The mapping is not assumed: each
loan's create-request `clientId` equals the scenario position and the extraction found
exactly loans 1–50 with no unattributed create (`build-results.py`, 0 mismatches;
`attribution_validated: true`).

| # | TestRailId | feature line | result | loan | product | principal (minor) | read-backs | committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C2565 | 5 | PASSED | 1 | `default progressive` | 100000 | 10 | yes |
| 2 | C2566 | 25 | PASSED | 2 | `default progressive` | 100000 | 13 | yes |
| 3 | C2567 | 51 | PASSED | 3 | `default progressive` | 100000 | 16 | yes |
| 4 | C2568 | 81 | PASSED | 4 | `default progressive` | 100000 | 11 | yes |
| 5 | C2569 | 104 | PASSED | 5 | `default progressive` | 100000 | 14 | yes |
| 6 | C2570 | 133 | PASSED | 6 | `default progressive` | 100000 | 12 | yes |
| 7 | C2571 | 157 | PASSED | 7 | `LP1_INTEREST_FLAT` | 100000 | 12 | yes |
| 8 | C2572 | 184 | PASSED | 8 | `LP1_INTEREST_FLAT` | 100000 | 15 | yes |
| 9 | C2573 | 218 | PASSED | 9 | `LP1_INTEREST_FLAT` | 100000 | 15 | yes |
| 10 | C2574 | 252 | PASSED | 10 | `LP1_INTEREST_FLAT` | 100000 | 15 | yes |
| 11 | C2575 | 284 | PASSED | 11 | `default progressive` | 100000 | 11 | yes |
| 12 | C2576 | 305 | PASSED | 12 | `default progressive` | 100000 | 17 | yes |
| 13 | C2577 | 336 | PASSED | 13 | `default progressive` | 100000 | 12 | yes |
| 14 | C2578 | 360 | PASSED | 14 | `default progressive` | 100000 | 13 | yes |
| 15 | C2579 | 385 | PASSED | 15 | `LP1_INTEREST_FLAT` | 100000 | 13 | yes |
| 16 | C2580 | 413 | PASSED | 16 | `LP1_INTEREST_FLAT` | 100000 | 16 | yes |
| 17 | C2581 | 448 | PASSED | 17 | `LP1_INTEREST_FLAT` | 100000 | 16 | yes |
| 18 | C2582 | 483 | PASSED | 18 | `LP1_INTEREST_FLAT` | 100000 | 16 | yes |
| 19 | C2591 | 516 | PASSED | 19 | `LP1_INTEREST_FLAT` | 100000 | 24 | yes |
| 20 | C2592 | 567 | PASSED | 20 | `LP1_INTEREST_FLAT` | 100000 | 19 | yes |
| 21 | C2593 | 627 | PASSED | 21 | `default progressive` | 100000 | 12 | yes |
| 22 | C2594 | 654 | PASSED | 22 | `default progressive` | 100000 | 14 | yes |
| 23 | C2595 | 683 | PASSED | 23 | `default progressive` | 100000 | 10 | yes |
| 24 | C2596 | 708 | PASSED | 24 | `default progressive` | 100000 | 13 | yes |
| 25 | C2597 | 729 | PASSED | 25 | `default progressive` | 100000 | 13 | yes |
| 26 | C2598 | 749 | PASSED | 26 | `default progressive` | 100000 | 10 | yes |
| 27 | C2599 | 775 | PASSED | 27 | `default progressive` | 100000 | 9 | yes |
| 28 | C2600 | 798 | PASSED | 28 | `default progressive` | 100000 | 10 | yes |
| 29 | C2706 | 824 | PASSED | 29 | `LP1_INTEREST_FLAT` | 100000 | 11 | yes |
| 30 | C2761 | 852 | PASSED | 30 | `default progressive` | 100000 | 18 | yes |
| 31 | C3568 | 893 | PASSED | 31 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ACCRUAL_ACTIVITY_POSTING` | 50000 | 23 | yes |
| 32 | C2762 | 967 | PASSED | 32 | `default progressive` | 100000 | 19 | yes |
| 33 | C2763 | 1014 | PASSED | 33 | `default progressive` | 100000 | 19 | yes |
| 34 | C2764 | 1061 | PASSED | 34 | `default progressive` | 100000 | 18 | yes |
| 35 | C2765 | 1100 | PASSED | 35 | `default progressive` | 100000 | 12 | yes |
| 36 | C2766 | 1126 | PASSED | 36 | `default progressive` | 100000 | 12 | yes |
| 37 | C2767 | 1149 | PASSED | 37 | `default progressive` | 100000 | 23 | yes |
| 38 | C2768 | 1210 | PASSED | 38 | `default progressive` | 100000 | 11 | yes |
| 39 | C2779 | 1238 | PASSED | 39 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` | 100000 | 12 | yes |
| 40 | C2780 | 1284 | PASSED | 40 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` | 100000 | 13 | yes |
| 41 | C2781 | 1337 | PASSED | 41 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY` | 100000 | 14 | yes |
| 42 | C3545 | 1387 | PASSED | 42 | `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY_INT_RECALC` | 10000 | 12 | yes |
| 43 | C2782 | 1474 | PASSED | 43 | `default progressive` | 100000 | 18 | yes |
| 44 | C2891 | 1536 | PASSED | 44 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 13 | yes |
| 45 | C2892 | 1563 | PASSED | 45 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 10 | yes |
| 46 | C2893 | 1585 | PASSED | 46 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 13 | yes |
| 47 | C2894 | 1613 | PASSED | 47 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 16 | yes |
| 48 | C2895 | 1645 | PASSED | 48 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 9 | yes |
| 49 | C2896 | 1672 | PASSED | 49 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 12 | yes |
| 50 | C3067 | 1704 | PASSED | 50 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 14 | yes |

All 50 scenarios PASSED, so every loan directory is committed.  The `principal (minor)`
column comes from each loan's `create-request` body, converted from the decimal major
units the oracle emitted.

## Per-scenario read-back files

`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the
`create-request`, the `approve`/`disburse`/`charge-off`/`repayment`/`undo`/... command
request+response pairs, and the `GET` read-backs.  The read-backs (kind `read`) belonging
to each scenario are listed below; command request/response pairs sit in the same
directory and are visible in `manifest-chargeoff-passed.json`.

### 1 — C2565 — `PASSED` — loan 1 — As a user I want to do a Charge-off for non-fraud loan after disbursement

Feature line 5; product `default progressive`; principal 100000 minor units; read-backs: 10; all
committed under `loans/loan-1/`.

```
loans/loan-1/loan-1-detail-associations-all-1.json
loans/loan-1/loan-1-detail-associations-empty.json
loans/loan-1/loan-1-detail-no-associations-1.json
loans/loan-1/loan-1-detail-associations-all-2.json
loans/loan-1/loan-1-detail-associations-transactions-1.json
loans/loan-1/loan-1-detail-associations-all-3.json
loans/loan-1/loan-1-detail-no-associations-2.json
loans/loan-1/loan-1-detail-no-associations-3.json
loans/loan-1/loan-1-detail-associations-transactions-2.json
loans/loan-1/loan-1-detail-associations-transactions-3.json
```

### 2 — C2566 — `PASSED` — loan 2 — As a user I want to do a Charge-off for non-fraud loan after repayment

Feature line 25; product `default progressive`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-2/`.

```
loans/loan-2/loan-2-detail-associations-all-1.json
loans/loan-2/loan-2-detail-associations-empty.json
loans/loan-2/loan-2-detail-no-associations-1.json
loans/loan-2/loan-2-detail-associations-all-2.json
loans/loan-2/loan-2-detail-associations-transactions-1.json
loans/loan-2/loan-2-detail-associations-all-3.json
loans/loan-2/loan-2-detail-associations-transactions-2.json
loans/loan-2/loan-2-detail-associations-all-4.json
loans/loan-2/loan-2-detail-no-associations-2.json
loans/loan-2/loan-2-detail-no-associations-3.json
loans/loan-2/loan-2-detail-associations-transactions-3.json
loans/loan-2/loan-2-detail-associations-transactions-4.json
loans/loan-2/loan-2-detail-associations-transactions-5.json
```

### 3 — C2567 — `PASSED` — loan 3 — As a user I want to do a Repayment undo after Charge-off for non-fraud

Feature line 51; product `default progressive`; principal 100000 minor units; read-backs: 16; all
committed under `loans/loan-3/`.

```
loans/loan-3/loan-3-detail-associations-all-1.json
loans/loan-3/loan-3-detail-associations-empty.json
loans/loan-3/loan-3-detail-no-associations-1.json
loans/loan-3/loan-3-detail-associations-all-2.json
loans/loan-3/loan-3-detail-associations-transactions-1.json
loans/loan-3/loan-3-detail-associations-all-3.json
loans/loan-3/loan-3-detail-associations-transactions-2.json
loans/loan-3/loan-3-detail-associations-all-4.json
loans/loan-3/loan-3-detail-no-associations-2.json
loans/loan-3/loan-3-detail-associations-transactions-3.json
loans/loan-3/loan-3-detail-associations-all-5.json
loans/loan-3/loan-3-detail-no-associations-3.json
loans/loan-3/loan-3-detail-associations-transactions-4.json
loans/loan-3/loan-3-detail-associations-transactions-5.json
loans/loan-3/loan-3-detail-associations-transactions-6.json
loans/loan-3/loan-3-detail-associations-transactions-7.json
```

### 4 — C2568 — `PASSED` — loan 4 — As a user I want to do Charge-off for fraud loan when FEE is added

Feature line 81; product `default progressive`; principal 100000 minor units; read-backs: 11; all
committed under `loans/loan-4/`.

```
loans/loan-4/loan-4-detail-associations-all-1.json
loans/loan-4/loan-4-detail-associations-empty.json
loans/loan-4/loan-4-detail-no-associations-1.json
loans/loan-4/loan-4-detail-associations-all-2.json
loans/loan-4/loan-4-detail-associations-transactions-1.json
loans/loan-4/loan-4-detail-associations-all-3.json
loans/loan-4/loan-4-detail-associations-all-4.json
loans/loan-4/loan-4-detail-no-associations-2.json
loans/loan-4/loan-4-detail-no-associations-3.json
loans/loan-4/loan-4-detail-associations-transactions-2.json
loans/loan-4/loan-4-detail-associations-transactions-3.json
```

### 5 — C2569 — `PASSED` — loan 5 — As a user I want to do a Merchant Refund after charge-off (fee portion)

Feature line 104; product `default progressive`; principal 100000 minor units; read-backs: 14; all
committed under `loans/loan-5/`.

```
loans/loan-5/loan-5-detail-associations-all-1.json
loans/loan-5/loan-5-detail-associations-empty.json
loans/loan-5/loan-5-detail-no-associations-1.json
loans/loan-5/loan-5-detail-associations-all-2.json
loans/loan-5/loan-5-detail-associations-transactions-1.json
loans/loan-5/loan-5-detail-associations-all-3.json
loans/loan-5/loan-5-detail-associations-all-4.json
loans/loan-5/loan-5-detail-no-associations-2.json
loans/loan-5/loan-5-detail-associations-transactions-2.json
loans/loan-5/loan-5-detail-associations-all-5.json
loans/loan-5/loan-5-detail-no-associations-3.json
loans/loan-5/loan-5-detail-associations-transactions-3.json
loans/loan-5/loan-5-detail-associations-transactions-4.json
loans/loan-5/loan-5-detail-associations-transactions-5.json
```

### 6 — C2570 — `PASSED` — loan 6 — As a user I want to do a Charge-off for non-fraud loan when FEE and PENALTY added

Feature line 133; product `default progressive`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-6/`.

```
loans/loan-6/loan-6-detail-associations-all-1.json
loans/loan-6/loan-6-detail-associations-empty.json
loans/loan-6/loan-6-detail-no-associations-1.json
loans/loan-6/loan-6-detail-associations-all-2.json
loans/loan-6/loan-6-detail-associations-transactions-1.json
loans/loan-6/loan-6-detail-associations-all-3.json
loans/loan-6/loan-6-detail-associations-all-4.json
loans/loan-6/loan-6-detail-associations-all-5.json
loans/loan-6/loan-6-detail-no-associations-2.json
loans/loan-6/loan-6-detail-no-associations-3.json
loans/loan-6/loan-6-detail-associations-transactions-2.json
loans/loan-6/loan-6-detail-associations-transactions-3.json
```

### 7 — C2571 — `PASSED` — loan 7 — As a user I want to do Charge-off for non-fraud loan when FEE and PENALTY added (interest portion)

Feature line 157; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-7/`.

```
loans/loan-7/loan-7-detail-associations-all-1.json
loans/loan-7/loan-7-detail-associations-empty.json
loans/loan-7/loan-7-detail-no-associations-1.json
loans/loan-7/loan-7-detail-associations-all-2.json
loans/loan-7/loan-7-detail-associations-transactions-1.json
loans/loan-7/loan-7-detail-associations-all-3.json
loans/loan-7/loan-7-detail-associations-all-4.json
loans/loan-7/loan-7-detail-associations-all-5.json
loans/loan-7/loan-7-detail-no-associations-2.json
loans/loan-7/loan-7-detail-no-associations-3.json
loans/loan-7/loan-7-detail-associations-transactions-2.json
loans/loan-7/loan-7-detail-associations-transactions-3.json
```

### 8 — C2572 — `PASSED` — loan 8 — As a user I want to do a Merchant Refund after charge-off for non fraud loan (interest portion)

Feature line 184; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 15; all
committed under `loans/loan-8/`.

```
loans/loan-8/loan-8-detail-associations-all-1.json
loans/loan-8/loan-8-detail-associations-empty.json
loans/loan-8/loan-8-detail-no-associations-1.json
loans/loan-8/loan-8-detail-associations-all-2.json
loans/loan-8/loan-8-detail-associations-transactions-1.json
loans/loan-8/loan-8-detail-associations-all-3.json
loans/loan-8/loan-8-detail-associations-all-4.json
loans/loan-8/loan-8-detail-associations-all-5.json
loans/loan-8/loan-8-detail-no-associations-2.json
loans/loan-8/loan-8-detail-associations-transactions-2.json
loans/loan-8/loan-8-detail-associations-all-6.json
loans/loan-8/loan-8-detail-no-associations-3.json
loans/loan-8/loan-8-detail-associations-transactions-3.json
loans/loan-8/loan-8-detail-associations-transactions-4.json
loans/loan-8/loan-8-detail-associations-transactions-5.json
```

### 9 — C2573 — `PASSED` — loan 9 — As a user I want to do a Payout refund after charge-off for non fraud loan (interest portion)

Feature line 218; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 15; all
committed under `loans/loan-9/`.

```
loans/loan-9/loan-9-detail-associations-all-1.json
loans/loan-9/loan-9-detail-associations-empty.json
loans/loan-9/loan-9-detail-no-associations-1.json
loans/loan-9/loan-9-detail-associations-all-2.json
loans/loan-9/loan-9-detail-associations-transactions-1.json
loans/loan-9/loan-9-detail-associations-all-3.json
loans/loan-9/loan-9-detail-associations-all-4.json
loans/loan-9/loan-9-detail-associations-all-5.json
loans/loan-9/loan-9-detail-no-associations-2.json
loans/loan-9/loan-9-detail-associations-transactions-2.json
loans/loan-9/loan-9-detail-associations-all-6.json
loans/loan-9/loan-9-detail-no-associations-3.json
loans/loan-9/loan-9-detail-associations-transactions-3.json
loans/loan-9/loan-9-detail-associations-transactions-4.json
loans/loan-9/loan-9-detail-associations-transactions-5.json
```

### 10 — C2574 — `PASSED` — loan 10 — As a user I want to do a Repayment after Charge-off for fraud loan when FEE and PENALTY added (product with interest)

Feature line 252; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 15; all
committed under `loans/loan-10/`.

```
loans/loan-10/loan-10-detail-associations-all-1.json
loans/loan-10/loan-10-detail-associations-empty.json
loans/loan-10/loan-10-detail-no-associations-1.json
loans/loan-10/loan-10-detail-associations-all-2.json
loans/loan-10/loan-10-detail-associations-transactions-1.json
loans/loan-10/loan-10-detail-associations-all-3.json
loans/loan-10/loan-10-detail-associations-all-4.json
loans/loan-10/loan-10-detail-associations-all-5.json
loans/loan-10/loan-10-detail-no-associations-2.json
loans/loan-10/loan-10-detail-associations-transactions-2.json
loans/loan-10/loan-10-detail-associations-all-6.json
loans/loan-10/loan-10-detail-no-associations-3.json
loans/loan-10/loan-10-detail-associations-transactions-3.json
loans/loan-10/loan-10-detail-associations-transactions-4.json
loans/loan-10/loan-10-detail-associations-transactions-5.json
```

### 11 — C2575 — `PASSED` — loan 11 — As a user I want to do a Charge-off for fraud loan after disbursement

Feature line 284; product `default progressive`; principal 100000 minor units; read-backs: 11; all
committed under `loans/loan-11/`.

```
loans/loan-11/loan-11-detail-associations-all-1.json
loans/loan-11/loan-11-detail-associations-empty.json
loans/loan-11/loan-11-detail-no-associations-1.json
loans/loan-11/loan-11-detail-associations-all-2.json
loans/loan-11/loan-11-detail-associations-transactions-1.json
loans/loan-11/loan-11-detail-associations-all-3.json
loans/loan-11/loan-11-detail-no-associations-2.json
loans/loan-11/loan-11-detail-no-associations-3.json
loans/loan-11/loan-11-detail-no-associations-4.json
loans/loan-11/loan-11-detail-associations-transactions-2.json
loans/loan-11/loan-11-detail-associations-transactions-3.json
```

### 12 — C2576 — `PASSED` — loan 12 — As a user I want to do a Repayment undo after Charge-off for fraud loan

Feature line 305; product `default progressive`; principal 100000 minor units; read-backs: 17; all
committed under `loans/loan-12/`.

```
loans/loan-12/loan-12-detail-associations-all-1.json
loans/loan-12/loan-12-detail-associations-empty.json
loans/loan-12/loan-12-detail-no-associations-1.json
loans/loan-12/loan-12-detail-associations-all-2.json
loans/loan-12/loan-12-detail-associations-transactions-1.json
loans/loan-12/loan-12-detail-associations-all-3.json
loans/loan-12/loan-12-detail-associations-transactions-2.json
loans/loan-12/loan-12-detail-associations-all-4.json
loans/loan-12/loan-12-detail-no-associations-2.json
loans/loan-12/loan-12-detail-no-associations-3.json
loans/loan-12/loan-12-detail-associations-transactions-3.json
loans/loan-12/loan-12-detail-associations-all-5.json
loans/loan-12/loan-12-detail-no-associations-4.json
loans/loan-12/loan-12-detail-associations-transactions-4.json
loans/loan-12/loan-12-detail-associations-transactions-5.json
loans/loan-12/loan-12-detail-associations-transactions-6.json
loans/loan-12/loan-12-detail-associations-transactions-7.json
```

### 13 — C2577 — `PASSED` — loan 13 — As a user I want to do a Charge-off for fraud loan when FEE is added

Feature line 336; product `default progressive`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-13/`.

```
loans/loan-13/loan-13-detail-associations-all-1.json
loans/loan-13/loan-13-detail-associations-empty.json
loans/loan-13/loan-13-detail-no-associations-1.json
loans/loan-13/loan-13-detail-associations-all-2.json
loans/loan-13/loan-13-detail-associations-transactions-1.json
loans/loan-13/loan-13-detail-associations-all-3.json
loans/loan-13/loan-13-detail-associations-all-4.json
loans/loan-13/loan-13-detail-no-associations-2.json
loans/loan-13/loan-13-detail-no-associations-3.json
loans/loan-13/loan-13-detail-no-associations-4.json
loans/loan-13/loan-13-detail-associations-transactions-2.json
loans/loan-13/loan-13-detail-associations-transactions-3.json
```

### 14 — C2578 — `PASSED` — loan 14 — As a user I want to do a Charge-off for fraud loan when FEE and PENALTY added

Feature line 360; product `default progressive`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-14/`.

```
loans/loan-14/loan-14-detail-associations-all-1.json
loans/loan-14/loan-14-detail-associations-empty.json
loans/loan-14/loan-14-detail-no-associations-1.json
loans/loan-14/loan-14-detail-associations-all-2.json
loans/loan-14/loan-14-detail-associations-transactions-1.json
loans/loan-14/loan-14-detail-associations-all-3.json
loans/loan-14/loan-14-detail-associations-all-4.json
loans/loan-14/loan-14-detail-associations-all-5.json
loans/loan-14/loan-14-detail-no-associations-2.json
loans/loan-14/loan-14-detail-no-associations-3.json
loans/loan-14/loan-14-detail-no-associations-4.json
loans/loan-14/loan-14-detail-associations-transactions-2.json
loans/loan-14/loan-14-detail-associations-transactions-3.json
```

### 15 — C2579 — `PASSED` — loan 15 — As a user I want to do a Charge-off for fraud loan when FEE and PENALTY added (interest portion)

Feature line 385; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-15/`.

```
loans/loan-15/loan-15-detail-associations-all-1.json
loans/loan-15/loan-15-detail-associations-empty.json
loans/loan-15/loan-15-detail-no-associations-1.json
loans/loan-15/loan-15-detail-associations-all-2.json
loans/loan-15/loan-15-detail-associations-transactions-1.json
loans/loan-15/loan-15-detail-associations-all-3.json
loans/loan-15/loan-15-detail-associations-all-4.json
loans/loan-15/loan-15-detail-associations-all-5.json
loans/loan-15/loan-15-detail-no-associations-2.json
loans/loan-15/loan-15-detail-no-associations-3.json
loans/loan-15/loan-15-detail-no-associations-4.json
loans/loan-15/loan-15-detail-associations-transactions-2.json
loans/loan-15/loan-15-detail-associations-transactions-3.json
```

### 16 — C2580 — `PASSED` — loan 16 — As a user I want to do a Merchant issue refund for fraud loan when FEE and PENALTY added (interest portion)

Feature line 413; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 16; all
committed under `loans/loan-16/`.

```
loans/loan-16/loan-16-detail-associations-all-1.json
loans/loan-16/loan-16-detail-associations-empty.json
loans/loan-16/loan-16-detail-no-associations-1.json
loans/loan-16/loan-16-detail-associations-all-2.json
loans/loan-16/loan-16-detail-associations-transactions-1.json
loans/loan-16/loan-16-detail-associations-all-3.json
loans/loan-16/loan-16-detail-associations-all-4.json
loans/loan-16/loan-16-detail-associations-all-5.json
loans/loan-16/loan-16-detail-no-associations-2.json
loans/loan-16/loan-16-detail-no-associations-3.json
loans/loan-16/loan-16-detail-associations-transactions-2.json
loans/loan-16/loan-16-detail-associations-all-6.json
loans/loan-16/loan-16-detail-no-associations-4.json
loans/loan-16/loan-16-detail-associations-transactions-3.json
loans/loan-16/loan-16-detail-associations-transactions-4.json
loans/loan-16/loan-16-detail-associations-transactions-5.json
```

### 17 — C2581 — `PASSED` — loan 17 — As a user I want to do Payout refund for fraud loan when FEE and PENALTY added (interest portion)

Feature line 448; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 16; all
committed under `loans/loan-17/`.

```
loans/loan-17/loan-17-detail-associations-all-1.json
loans/loan-17/loan-17-detail-associations-empty.json
loans/loan-17/loan-17-detail-no-associations-1.json
loans/loan-17/loan-17-detail-associations-all-2.json
loans/loan-17/loan-17-detail-associations-transactions-1.json
loans/loan-17/loan-17-detail-associations-all-3.json
loans/loan-17/loan-17-detail-associations-all-4.json
loans/loan-17/loan-17-detail-associations-all-5.json
loans/loan-17/loan-17-detail-no-associations-2.json
loans/loan-17/loan-17-detail-no-associations-3.json
loans/loan-17/loan-17-detail-associations-transactions-2.json
loans/loan-17/loan-17-detail-associations-all-6.json
loans/loan-17/loan-17-detail-no-associations-4.json
loans/loan-17/loan-17-detail-associations-transactions-3.json
loans/loan-17/loan-17-detail-associations-transactions-4.json
loans/loan-17/loan-17-detail-associations-transactions-5.json
```

### 18 — C2582 — `PASSED` — loan 18 — As a user I want to do a Repayment after Charge-off for fraud loan when FEE and PENALTY added

Feature line 483; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 16; all
committed under `loans/loan-18/`.

```
loans/loan-18/loan-18-detail-associations-all-1.json
loans/loan-18/loan-18-detail-associations-empty.json
loans/loan-18/loan-18-detail-no-associations-1.json
loans/loan-18/loan-18-detail-associations-all-2.json
loans/loan-18/loan-18-detail-associations-transactions-1.json
loans/loan-18/loan-18-detail-associations-all-3.json
loans/loan-18/loan-18-detail-associations-all-4.json
loans/loan-18/loan-18-detail-associations-all-5.json
loans/loan-18/loan-18-detail-no-associations-2.json
loans/loan-18/loan-18-detail-no-associations-3.json
loans/loan-18/loan-18-detail-associations-transactions-2.json
loans/loan-18/loan-18-detail-associations-all-6.json
loans/loan-18/loan-18-detail-no-associations-4.json
loans/loan-18/loan-18-detail-associations-transactions-3.json
loans/loan-18/loan-18-detail-associations-transactions-4.json
loans/loan-18/loan-18-detail-associations-transactions-5.json
```

### 19 — C2591 — `PASSED` — loan 19 — As a user I want to repay a loan which was charged-off

Feature line 516; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 24; all
committed under `loans/loan-19/`.

```
loans/loan-19/loan-19-detail-associations-all-1.json
loans/loan-19/loan-19-detail-associations-empty.json
loans/loan-19/loan-19-detail-no-associations-1.json
loans/loan-19/loan-19-detail-associations-all-2.json
loans/loan-19/loan-19-detail-associations-transactions-1.json
loans/loan-19/loan-19-detail-associations-all-3.json
loans/loan-19/loan-19-detail-associations-all-4.json
loans/loan-19/loan-19-detail-associations-all-5.json
loans/loan-19/loan-19-detail-no-associations-2.json
loans/loan-19/loan-19-detail-no-associations-3.json
loans/loan-19/loan-19-detail-associations-transactions-2.json
loans/loan-19/loan-19-detail-associations-all-6.json
loans/loan-19/loan-19-detail-no-associations-4.json
loans/loan-19/loan-19-detail-associations-transactions-3.json
loans/loan-19/loan-19-detail-associations-all-7.json
loans/loan-19/loan-19-detail-no-associations-5.json
loans/loan-19/loan-19-detail-no-associations-6.json
loans/loan-19/loan-19-detail-no-associations-7.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-1.json
loans/loan-19/loan-19-detail-associations-repaymentSchedule-2.json
loans/loan-19/loan-19-detail-associations-transactions-4.json
loans/loan-19/loan-19-detail-associations-transactions-5.json
loans/loan-19/loan-19-detail-associations-transactions-6.json
loans/loan-19/loan-19-detail-associations-transactions-7.json
```

### 20 — C2592 — `PASSED` — loan 20 — As a user I want to do a charge-off undo before any other transactions on the loan

Feature line 567; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 19; all
committed under `loans/loan-20/`.

```
loans/loan-20/loan-20-detail-associations-all-1.json
loans/loan-20/loan-20-detail-associations-empty.json
loans/loan-20/loan-20-detail-no-associations-1.json
loans/loan-20/loan-20-detail-associations-all-2.json
loans/loan-20/loan-20-detail-associations-transactions-1.json
loans/loan-20/loan-20-detail-associations-all-3.json
loans/loan-20/loan-20-detail-associations-all-4.json
loans/loan-20/loan-20-detail-associations-all-5.json
loans/loan-20/loan-20-detail-no-associations-2.json
loans/loan-20/loan-20-detail-no-associations-3.json
loans/loan-20/loan-20-detail-associations-repaymentSchedule-1.json
loans/loan-20/loan-20-detail-associations-repaymentSchedule-2.json
loans/loan-20/loan-20-detail-associations-transactions-2.json
loans/loan-20/loan-20-detail-associations-transactions-3.json
loans/loan-20/loan-20-detail-associations-transactions-4.json
loans/loan-20/loan-20-detail-associations-all-6.json
loans/loan-20/loan-20-detail-associations-transactions-5.json
loans/loan-20/loan-20-detail-associations-transactions-6.json
loans/loan-20/loan-20-detail-associations-transactions-7.json
```

### 21 — C2593 — `PASSED` — loan 21 — As a user I want to do a Charge-off before the last repayment

Feature line 627; product `default progressive`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-21/`.

```
loans/loan-21/loan-21-detail-associations-all-1.json
loans/loan-21/loan-21-detail-associations-empty.json
loans/loan-21/loan-21-detail-no-associations.json
loans/loan-21/loan-21-detail-associations-all-2.json
loans/loan-21/loan-21-detail-associations-transactions-1.json
loans/loan-21/loan-21-detail-associations-all-3.json
loans/loan-21/loan-21-detail-associations-transactions-2.json
loans/loan-21/loan-21-detail-associations-all-4.json
loans/loan-21/loan-21-detail-associations-repaymentSchedule-1.json
loans/loan-21/loan-21-detail-associations-repaymentSchedule-2.json
loans/loan-21/loan-21-detail-associations-transactions-3.json
loans/loan-21/loan-21-detail-associations-transactions-4.json
```

### 22 — C2594 — `PASSED` — loan 22 — As a user I want to do a Charge-off between 2 repayments

Feature line 654; product `default progressive`; principal 100000 minor units; read-backs: 14; all
committed under `loans/loan-22/`.

```
loans/loan-22/loan-22-detail-associations-all-1.json
loans/loan-22/loan-22-detail-associations-empty.json
loans/loan-22/loan-22-detail-no-associations.json
loans/loan-22/loan-22-detail-associations-all-2.json
loans/loan-22/loan-22-detail-associations-transactions-1.json
loans/loan-22/loan-22-detail-associations-all-3.json
loans/loan-22/loan-22-detail-associations-transactions-2.json
loans/loan-22/loan-22-detail-associations-all-4.json
loans/loan-22/loan-22-detail-associations-transactions-3.json
loans/loan-22/loan-22-detail-associations-all-5.json
loans/loan-22/loan-22-detail-associations-repaymentSchedule-1.json
loans/loan-22/loan-22-detail-associations-repaymentSchedule-2.json
loans/loan-22/loan-22-detail-associations-transactions-4.json
loans/loan-22/loan-22-detail-associations-transactions-5.json
```

### 23 — C2595 — `PASSED` — loan 23 — As a user I want to do a backdated Charge-off when only disbursement transaction happened

Feature line 683; product `default progressive`; principal 100000 minor units; read-backs: 10; all
committed under `loans/loan-23/`.

```
loans/loan-23/loan-23-detail-associations-all-1.json
loans/loan-23/loan-23-detail-associations-empty.json
loans/loan-23/loan-23-detail-no-associations.json
loans/loan-23/loan-23-detail-associations-all-2.json
loans/loan-23/loan-23-detail-associations-transactions-1.json
loans/loan-23/loan-23-detail-associations-all-3.json
loans/loan-23/loan-23-detail-associations-repaymentSchedule-1.json
loans/loan-23/loan-23-detail-associations-repaymentSchedule-2.json
loans/loan-23/loan-23-detail-associations-transactions-2.json
loans/loan-23/loan-23-detail-associations-transactions-3.json
```

### 24 — C2596 — `PASSED` — loan 24 — As a user I want to do an undo on a transaction which was created before the Charge-off

Feature line 708; product `default progressive`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-24/`.

```
loans/loan-24/loan-24-detail-associations-all-1.json
loans/loan-24/loan-24-detail-associations-empty.json
loans/loan-24/loan-24-detail-no-associations.json
loans/loan-24/loan-24-detail-associations-all-2.json
loans/loan-24/loan-24-detail-associations-transactions-1.json
loans/loan-24/loan-24-detail-associations-all-3.json
loans/loan-24/loan-24-detail-associations-transactions-2.json
loans/loan-24/loan-24-detail-associations-all-4.json
loans/loan-24/loan-24-detail-associations-transactions-3.json
loans/loan-24/loan-24-detail-associations-all-5.json
loans/loan-24/loan-24-detail-associations-transactions-4.json
loans/loan-24/loan-24-detail-associations-repaymentSchedule-1.json
loans/loan-24/loan-24-detail-associations-repaymentSchedule-2.json
```

### 25 — C2597 — `PASSED` — loan 25 — As a user I want to do an undo on a transaction which was created on the Charge-off day

Feature line 729; product `default progressive`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-25/`.

```
loans/loan-25/loan-25-detail-associations-all-1.json
loans/loan-25/loan-25-detail-associations-empty.json
loans/loan-25/loan-25-detail-no-associations.json
loans/loan-25/loan-25-detail-associations-all-2.json
loans/loan-25/loan-25-detail-associations-transactions-1.json
loans/loan-25/loan-25-detail-associations-all-3.json
loans/loan-25/loan-25-detail-associations-transactions-2.json
loans/loan-25/loan-25-detail-associations-all-4.json
loans/loan-25/loan-25-detail-associations-transactions-3.json
loans/loan-25/loan-25-detail-associations-all-5.json
loans/loan-25/loan-25-detail-associations-transactions-4.json
loans/loan-25/loan-25-detail-associations-repaymentSchedule-1.json
loans/loan-25/loan-25-detail-associations-repaymentSchedule-2.json
```

### 26 — C2598 — `PASSED` — loan 26 — As a user I want to do a second Charge-off

Feature line 749; product `default progressive`; principal 100000 minor units; read-backs: 10; all
committed under `loans/loan-26/`.

```
loans/loan-26/loan-26-detail-associations-all-1.json
loans/loan-26/loan-26-detail-associations-empty.json
loans/loan-26/loan-26-detail-no-associations.json
loans/loan-26/loan-26-detail-associations-all-2.json
loans/loan-26/loan-26-detail-associations-transactions-1.json
loans/loan-26/loan-26-detail-associations-all-3.json
loans/loan-26/loan-26-detail-associations-repaymentSchedule-1.json
loans/loan-26/loan-26-detail-associations-repaymentSchedule-2.json
loans/loan-26/loan-26-detail-associations-transactions-2.json
loans/loan-26/loan-26-detail-associations-transactions-3.json
```

### 27 — C2599 — `PASSED` — loan 27 — As a user I want to do a second Charge-off undo

Feature line 775; product `default progressive`; principal 100000 minor units; read-backs: 9; all
committed under `loans/loan-27/`.

```
loans/loan-27/loan-27-detail-associations-all-1.json
loans/loan-27/loan-27-detail-associations-empty.json
loans/loan-27/loan-27-detail-no-associations.json
loans/loan-27/loan-27-detail-associations-all-2.json
loans/loan-27/loan-27-detail-associations-transactions-1.json
loans/loan-27/loan-27-detail-associations-all-3.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-1.json
loans/loan-27/loan-27-detail-associations-repaymentSchedule-2.json
loans/loan-27/loan-27-detail-associations-transactions-2.json
```

### 28 — C2600 — `PASSED` — loan 28 — As a user I want to add charge after Charge-off

Feature line 798; product `default progressive`; principal 100000 minor units; read-backs: 10; all
committed under `loans/loan-28/`.

```
loans/loan-28/loan-28-detail-associations-all-1.json
loans/loan-28/loan-28-detail-associations-empty.json
loans/loan-28/loan-28-detail-no-associations.json
loans/loan-28/loan-28-detail-associations-all-2.json
loans/loan-28/loan-28-detail-associations-transactions-1.json
loans/loan-28/loan-28-detail-associations-all-3.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-1.json
loans/loan-28/loan-28-detail-associations-repaymentSchedule-2.json
loans/loan-28/loan-28-detail-associations-transactions-2.json
loans/loan-28/loan-28-detail-associations-transactions-3.json
```

### 29 — C2706 — `PASSED` — loan 29 — Verify that Charge-off NOT results an error anymore when to be applied on a loan with an interest

Feature line 824; product `LP1_INTEREST_FLAT`; principal 100000 minor units; read-backs: 11; all
committed under `loans/loan-29/`.

```
loans/loan-29/loan-29-detail-associations-all-1.json
loans/loan-29/loan-29-detail-associations-empty.json
loans/loan-29/loan-29-detail-no-associations.json
loans/loan-29/loan-29-detail-associations-all-2.json
loans/loan-29/loan-29-detail-associations-transactions-1.json
loans/loan-29/loan-29-detail-associations-all-3.json
loans/loan-29/loan-29-detail-associations-all-4.json
loans/loan-29/loan-29-detail-associations-all-5.json
loans/loan-29/loan-29-detail-associations-repaymentSchedule-1.json
loans/loan-29/loan-29-detail-associations-repaymentSchedule-2.json
loans/loan-29/loan-29-detail-associations-transactions-2.json
```

### 30 — C2761 — `PASSED` — loan 30 — Verify that charge-off is reversed/replayed if Scheduled repayment which was placed on a date before the charge-off is reversed after the charge-off

Feature line 852; product `default progressive`; principal 100000 minor units; read-backs: 18; all
committed under `loans/loan-30/`.

```
loans/loan-30/loan-30-detail-associations-all-1.json
loans/loan-30/loan-30-detail-associations-empty.json
loans/loan-30/loan-30-detail-no-associations.json
loans/loan-30/loan-30-detail-associations-all-2.json
loans/loan-30/loan-30-detail-associations-transactions-1.json
loans/loan-30/loan-30-detail-associations-all-3.json
loans/loan-30/loan-30-charges-30-no-associations.json
loans/loan-30/loan-30-detail-associations-transactions-2.json
loans/loan-30/loan-30-detail-associations-all-4.json
loans/loan-30/loan-30-detail-associations-repaymentSchedule-1.json
loans/loan-30/loan-30-detail-associations-repaymentSchedule-2.json
loans/loan-30/loan-30-detail-associations-transactions-3.json
loans/loan-30/loan-30-detail-associations-transactions-4.json
loans/loan-30/loan-30-detail-associations-all-5.json
loans/loan-30/loan-30-detail-associations-repaymentSchedule-3.json
loans/loan-30/loan-30-detail-associations-repaymentSchedule-4.json
loans/loan-30/loan-30-detail-associations-transactions-5.json
loans/loan-30/loan-30-detail-associations-transactions-6.json
```

### 31 — C3568 — `PASSED` — loan 31 — Verify that charge-off is reversed/replayed if repayment is reversed after the charge-off with COB process

Feature line 893; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_ACCRUAL_ACTIVITY_POSTING`; principal 50000 minor units; read-backs: 23; all
committed under `loans/loan-31/`.

```
loans/loan-31/loan-31-detail-associations-all-1.json
loans/loan-31/loan-31-detail-associations-empty.json
loans/loan-31/loan-31-detail-no-associations.json
loans/loan-31/loan-31-detail-associations-all-2.json
loans/loan-31/loan-31-detail-associations-transactions-1.json
loans/loan-31/loan-31-detail-associations-all-3.json
loans/loan-31/loan-31-detail-associations-repaymentSchedule-1.json
loans/loan-31/loan-31-detail-associations-repaymentSchedule-2.json
loans/loan-31/loan-31-detail-associations-transactions-2.json
loans/loan-31/loan-31-charges-31-no-associations.json
loans/loan-31/loan-31-detail-associations-transactions-3.json
loans/loan-31/loan-31-detail-associations-all-4.json
loans/loan-31/loan-31-detail-associations-repaymentSchedule-3.json
loans/loan-31/loan-31-detail-associations-repaymentSchedule-4.json
loans/loan-31/loan-31-detail-associations-transactions-4.json
loans/loan-31/loan-31-detail-associations-transactions-5.json
loans/loan-31/loan-31-detail-associations-all-5.json
loans/loan-31/loan-31-detail-associations-repaymentSchedule-5.json
loans/loan-31/loan-31-detail-associations-repaymentSchedule-6.json
loans/loan-31/loan-31-detail-associations-transactions-6.json
loans/loan-31/loan-31-detail-associations-transactions-7.json
loans/loan-31/loan-31-detail-associations-transactions-8.json
loans/loan-31/loan-31-detail-associations-transactions-9.json
```

### 32 — C2762 — `PASSED` — loan 32 — Verify that charge-off is reversed/replayed if Real time repayment which was placed on a date before the charge-off is reversed after the charge-off

Feature line 967; product `default progressive`; principal 100000 minor units; read-backs: 19; all
committed under `loans/loan-32/`.

```
loans/loan-32/loan-32-detail-associations-all-1.json
loans/loan-32/loan-32-detail-associations-empty.json
loans/loan-32/loan-32-detail-no-associations.json
loans/loan-32/loan-32-detail-associations-all-2.json
loans/loan-32/loan-32-detail-associations-transactions-1.json
loans/loan-32/loan-32-detail-associations-all-3.json
loans/loan-32/loan-32-charges-32-no-associations.json
loans/loan-32/loan-32-detail-associations-transactions-2.json
loans/loan-32/loan-32-detail-associations-all-4.json
loans/loan-32/loan-32-charges-33-no-associations.json
loans/loan-32/loan-32-detail-associations-repaymentSchedule-1.json
loans/loan-32/loan-32-detail-associations-repaymentSchedule-2.json
loans/loan-32/loan-32-detail-associations-transactions-3.json
loans/loan-32/loan-32-detail-associations-transactions-4.json
loans/loan-32/loan-32-detail-associations-all-5.json
loans/loan-32/loan-32-detail-associations-repaymentSchedule-3.json
loans/loan-32/loan-32-detail-associations-repaymentSchedule-4.json
loans/loan-32/loan-32-detail-associations-transactions-5.json
loans/loan-32/loan-32-detail-associations-transactions-6.json
```

### 33 — C2763 — `PASSED` — loan 33 — Verify that charge-off is reversed/replayed if Autopay repayment which was placed on a date before the charge-off is reversed after the charge-off

Feature line 1014; product `default progressive`; principal 100000 minor units; read-backs: 19; all
committed under `loans/loan-33/`.

```
loans/loan-33/loan-33-detail-associations-all-1.json
loans/loan-33/loan-33-detail-associations-empty.json
loans/loan-33/loan-33-detail-no-associations.json
loans/loan-33/loan-33-detail-associations-all-2.json
loans/loan-33/loan-33-detail-associations-transactions-1.json
loans/loan-33/loan-33-detail-associations-all-3.json
loans/loan-33/loan-33-charges-34-no-associations.json
loans/loan-33/loan-33-detail-associations-transactions-2.json
loans/loan-33/loan-33-detail-associations-all-4.json
loans/loan-33/loan-33-charges-35-no-associations.json
loans/loan-33/loan-33-detail-associations-repaymentSchedule-1.json
loans/loan-33/loan-33-detail-associations-repaymentSchedule-2.json
loans/loan-33/loan-33-detail-associations-transactions-3.json
loans/loan-33/loan-33-detail-associations-transactions-4.json
loans/loan-33/loan-33-detail-associations-all-5.json
loans/loan-33/loan-33-detail-associations-repaymentSchedule-3.json
loans/loan-33/loan-33-detail-associations-repaymentSchedule-4.json
loans/loan-33/loan-33-detail-associations-transactions-5.json
loans/loan-33/loan-33-detail-associations-transactions-6.json
```

### 34 — C2764 — `PASSED` — loan 34 — Verify that charge-off is NOT reversed/replayed if OCA repayment which was placed and reversed on a date after the charge-off

Feature line 1061; product `default progressive`; principal 100000 minor units; read-backs: 18; all
committed under `loans/loan-34/`.

```
loans/loan-34/loan-34-detail-associations-all-1.json
loans/loan-34/loan-34-detail-associations-empty.json
loans/loan-34/loan-34-detail-no-associations.json
loans/loan-34/loan-34-detail-associations-all-2.json
loans/loan-34/loan-34-detail-associations-transactions-1.json
loans/loan-34/loan-34-detail-associations-all-3.json
loans/loan-34/loan-34-charges-36-no-associations.json
loans/loan-34/loan-34-detail-associations-repaymentSchedule-1.json
loans/loan-34/loan-34-detail-associations-repaymentSchedule-2.json
loans/loan-34/loan-34-detail-associations-transactions-2.json
loans/loan-34/loan-34-detail-associations-transactions-3.json
loans/loan-34/loan-34-detail-associations-all-4.json
loans/loan-34/loan-34-detail-associations-transactions-4.json
loans/loan-34/loan-34-detail-associations-all-5.json
loans/loan-34/loan-34-detail-associations-repaymentSchedule-3.json
loans/loan-34/loan-34-detail-associations-repaymentSchedule-4.json
loans/loan-34/loan-34-detail-associations-transactions-5.json
loans/loan-34/loan-34-detail-associations-transactions-6.json
```

### 35 — C2765 — `PASSED` — loan 35 — Verify that charge-off is reversed/replayed if Goodwill credit transaction is placed on a date before the charge-off on business date after the charge-off

Feature line 1100; product `default progressive`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-35/`.

```
loans/loan-35/loan-35-detail-associations-all-1.json
loans/loan-35/loan-35-detail-associations-empty.json
loans/loan-35/loan-35-detail-no-associations.json
loans/loan-35/loan-35-detail-associations-all-2.json
loans/loan-35/loan-35-detail-associations-transactions-1.json
loans/loan-35/loan-35-detail-associations-all-3.json
loans/loan-35/loan-35-charges-37-no-associations.json
loans/loan-35/loan-35-detail-associations-transactions-2.json
loans/loan-35/loan-35-detail-associations-all-4.json
loans/loan-35/loan-35-detail-associations-repaymentSchedule-1.json
loans/loan-35/loan-35-detail-associations-repaymentSchedule-2.json
loans/loan-35/loan-35-detail-associations-transactions-3.json
```

### 36 — C2766 — `PASSED` — loan 36 — As a user I want to do a undo Charge-off with reversal external Id

Feature line 1126; product `default progressive`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-36/`.

```
loans/loan-36/loan-36-detail-associations-all-1.json
loans/loan-36/loan-36-detail-associations-empty.json
loans/loan-36/loan-36-detail-no-associations-1.json
loans/loan-36/loan-36-detail-associations-all-2.json
loans/loan-36/loan-36-detail-associations-transactions-1.json
loans/loan-36/loan-36-detail-associations-all-3.json
loans/loan-36/loan-36-detail-no-associations-2.json
loans/loan-36/loan-36-detail-no-associations-3.json
loans/loan-36/loan-36-detail-associations-transactions-2.json
loans/loan-36/loan-36-detail-associations-transactions-3.json
loans/loan-36/loan-36-transactions-121-no-associations.json
loans/loan-36/loan-36-detail-associations-transactions-4.json
```

### 37 — C2767 — `PASSED` — loan 37 — Verify that charge-off is reversed/replayed in case of partial payment, charge-off, second part of payment, reverse 1st payment

Feature line 1149; product `default progressive`; principal 100000 minor units; read-backs: 23; all
committed under `loans/loan-37/`.

```
loans/loan-37/loan-37-detail-associations-all-1.json
loans/loan-37/loan-37-detail-associations-empty.json
loans/loan-37/loan-37-detail-no-associations.json
loans/loan-37/loan-37-detail-associations-all-2.json
loans/loan-37/loan-37-detail-associations-transactions-1.json
loans/loan-37/loan-37-detail-associations-all-3.json
loans/loan-37/loan-37-detail-associations-transactions-2.json
loans/loan-37/loan-37-detail-associations-all-4.json
loans/loan-37/loan-37-detail-associations-transactions-3.json
loans/loan-37/loan-37-detail-associations-all-5.json
loans/loan-37/loan-37-detail-associations-repaymentSchedule-1.json
loans/loan-37/loan-37-detail-associations-repaymentSchedule-2.json
loans/loan-37/loan-37-detail-associations-transactions-4.json
loans/loan-37/loan-37-detail-associations-transactions-5.json
loans/loan-37/loan-37-detail-associations-all-6.json
loans/loan-37/loan-37-detail-associations-repaymentSchedule-3.json
loans/loan-37/loan-37-detail-associations-repaymentSchedule-4.json
loans/loan-37/loan-37-detail-associations-transactions-6.json
loans/loan-37/loan-37-detail-associations-transactions-7.json
loans/loan-37/loan-37-detail-associations-transactions-8.json
loans/loan-37/loan-37-detail-associations-transactions-9.json
loans/loan-37/loan-37-detail-associations-transactions-10.json
loans/loan-37/loan-37-detail-associations-transactions-11.json
```

### 38 — C2768 — `PASSED` — loan 38 — Verify that charge-off is results an error in case of partial payment, charge-off, fee added after charge-off

Feature line 1210; product `default progressive`; principal 100000 minor units; read-backs: 11; all
committed under `loans/loan-38/`.

```
loans/loan-38/loan-38-detail-associations-all-1.json
loans/loan-38/loan-38-detail-associations-empty.json
loans/loan-38/loan-38-detail-no-associations.json
loans/loan-38/loan-38-detail-associations-all-2.json
loans/loan-38/loan-38-detail-associations-transactions-1.json
loans/loan-38/loan-38-detail-associations-all-3.json
loans/loan-38/loan-38-detail-associations-transactions-2.json
loans/loan-38/loan-38-detail-associations-all-4.json
loans/loan-38/loan-38-detail-associations-repaymentSchedule-1.json
loans/loan-38/loan-38-detail-associations-repaymentSchedule-2.json
loans/loan-38/loan-38-detail-associations-transactions-3.json
```

### 39 — C2779 — `PASSED` — loan 39 — Verify that on interest bearing loans the accrual of interest is stopped when the loan is charged-off

Feature line 1238; product `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-39/`.

```
loans/loan-39/loan-39-detail-associations-all-1.json
loans/loan-39/loan-39-detail-associations-empty.json
loans/loan-39/loan-39-detail-no-associations.json
loans/loan-39/loan-39-detail-associations-all-2.json
loans/loan-39/loan-39-detail-associations-transactions-1.json
loans/loan-39/loan-39-detail-associations-all-3.json
loans/loan-39/loan-39-detail-associations-repaymentSchedule-1.json
loans/loan-39/loan-39-detail-associations-repaymentSchedule-2.json
loans/loan-39/loan-39-detail-associations-transactions-2.json
loans/loan-39/loan-39-detail-associations-repaymentSchedule-3.json
loans/loan-39/loan-39-detail-associations-repaymentSchedule-4.json
loans/loan-39/loan-39-detail-associations-transactions-3.json
```

### 40 — C2780 — `PASSED` — loan 40 — Verify that on interest bearing loans the accrual of interest is resumed and aggregated when the charge-off is reverted

Feature line 1284; product `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-40/`.

```
loans/loan-40/loan-40-detail-associations-all-1.json
loans/loan-40/loan-40-detail-associations-empty.json
loans/loan-40/loan-40-detail-no-associations.json
loans/loan-40/loan-40-detail-associations-all-2.json
loans/loan-40/loan-40-detail-associations-transactions-1.json
loans/loan-40/loan-40-detail-associations-all-3.json
loans/loan-40/loan-40-detail-associations-repaymentSchedule-1.json
loans/loan-40/loan-40-detail-associations-repaymentSchedule-2.json
loans/loan-40/loan-40-detail-associations-transactions-2.json
loans/loan-40/loan-40-detail-associations-repaymentSchedule-3.json
loans/loan-40/loan-40-detail-associations-repaymentSchedule-4.json
loans/loan-40/loan-40-detail-associations-transactions-3.json
loans/loan-40/loan-40-detail-associations-transactions-4.json
```

### 41 — C2781 — `PASSED` — loan 41 — Verify that on interest bearing loans the accrual of interest is stopped when the loan is charged-off even if fully paid after the charge-off

Feature line 1337; product `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY`; principal 100000 minor units; read-backs: 14; all
committed under `loans/loan-41/`.

```
loans/loan-41/loan-41-detail-associations-all-1.json
loans/loan-41/loan-41-detail-associations-empty.json
loans/loan-41/loan-41-detail-no-associations.json
loans/loan-41/loan-41-detail-associations-all-2.json
loans/loan-41/loan-41-detail-associations-transactions-1.json
loans/loan-41/loan-41-detail-associations-all-3.json
loans/loan-41/loan-41-detail-associations-repaymentSchedule-1.json
loans/loan-41/loan-41-detail-associations-repaymentSchedule-2.json
loans/loan-41/loan-41-detail-associations-transactions-2.json
loans/loan-41/loan-41-detail-associations-transactions-3.json
loans/loan-41/loan-41-detail-associations-all-4.json
loans/loan-41/loan-41-detail-associations-repaymentSchedule-3.json
loans/loan-41/loan-41-detail-associations-repaymentSchedule-4.json
loans/loan-41/loan-41-detail-associations-transactions-4.json
```

### 42 — C3545 — `PASSED` — loan 42 — Accrual handling in case of charged-off loan when charge-off behavior is regular, interestRecalculation = true, cumulative loan

Feature line 1387; product `LP1_INTEREST_DECLINING_BALANCE_PERIOD_DAILY_INT_RECALC`; principal 10000 minor units; read-backs: 12; all
committed under `loans/loan-42/`.

```
loans/loan-42/loan-42-detail-associations-all-1.json
loans/loan-42/loan-42-detail-associations-empty.json
loans/loan-42/loan-42-detail-no-associations.json
loans/loan-42/loan-42-detail-associations-all-2.json
loans/loan-42/loan-42-detail-associations-transactions-1.json
loans/loan-42/loan-42-detail-associations-all-3.json
loans/loan-42/loan-42-detail-associations-repaymentSchedule-1.json
loans/loan-42/loan-42-detail-associations-repaymentSchedule-2.json
loans/loan-42/loan-42-detail-associations-repaymentSchedule-3.json
loans/loan-42/loan-42-detail-associations-repaymentSchedule-4.json
loans/loan-42/loan-42-detail-associations-transactions-2.json
loans/loan-42/loan-42-detail-associations-transactions-3.json
```

### 43 — C2782 — `PASSED` — loan 43 — Verify that the accrual of charges is not happened when the loan is charged-off on charge's due date but resumed when the charge-off is reverted

Feature line 1474; product `default progressive`; principal 100000 minor units; read-backs: 18; all
committed under `loans/loan-43/`.

```
loans/loan-43/loan-43-detail-associations-all-1.json
loans/loan-43/loan-43-detail-associations-empty.json
loans/loan-43/loan-43-detail-no-associations.json
loans/loan-43/loan-43-detail-associations-all-2.json
loans/loan-43/loan-43-detail-associations-transactions-1.json
loans/loan-43/loan-43-detail-associations-all-3.json
loans/loan-43/loan-43-charges-38-no-associations.json
loans/loan-43/loan-43-detail-associations-repaymentSchedule-1.json
loans/loan-43/loan-43-detail-associations-repaymentSchedule-2.json
loans/loan-43/loan-43-detail-associations-transactions-2.json
loans/loan-43/loan-43-charges-39-no-associations.json
loans/loan-43/loan-43-detail-associations-repaymentSchedule-3.json
loans/loan-43/loan-43-detail-associations-repaymentSchedule-4.json
loans/loan-43/loan-43-detail-associations-transactions-3.json
loans/loan-43/loan-43-detail-associations-repaymentSchedule-5.json
loans/loan-43/loan-43-detail-associations-repaymentSchedule-6.json
loans/loan-43/loan-43-detail-associations-transactions-4.json
loans/loan-43/loan-43-detail-associations-transactions-5.json
```

### 44 — C2891 — `PASSED` — loan 44 — Verify that the user is able to do a Charge-off for fraud loan when FEE and PENALTY added - LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION product

Feature line 1536; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-44/`.

```
loans/loan-44/loan-44-detail-associations-all-1.json
loans/loan-44/loan-44-detail-associations-empty.json
loans/loan-44/loan-44-detail-no-associations-1.json
loans/loan-44/loan-44-detail-associations-all-2.json
loans/loan-44/loan-44-detail-associations-transactions-1.json
loans/loan-44/loan-44-detail-associations-all-3.json
loans/loan-44/loan-44-detail-associations-all-4.json
loans/loan-44/loan-44-detail-associations-all-5.json
loans/loan-44/loan-44-detail-no-associations-2.json
loans/loan-44/loan-44-detail-no-associations-3.json
loans/loan-44/loan-44-detail-no-associations-4.json
loans/loan-44/loan-44-detail-associations-transactions-2.json
loans/loan-44/loan-44-detail-associations-transactions-3.json
```

### 45 — C2892 — `PASSED` — loan 45 — Verify that the user is able to do a Charge-off for non-fraud loan after disbursement - LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION product

Feature line 1563; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 10; all
committed under `loans/loan-45/`.

```
loans/loan-45/loan-45-detail-associations-all-1.json
loans/loan-45/loan-45-detail-associations-empty.json
loans/loan-45/loan-45-detail-no-associations-1.json
loans/loan-45/loan-45-detail-associations-all-2.json
loans/loan-45/loan-45-detail-associations-transactions-1.json
loans/loan-45/loan-45-detail-associations-all-3.json
loans/loan-45/loan-45-detail-no-associations-2.json
loans/loan-45/loan-45-detail-no-associations-3.json
loans/loan-45/loan-45-detail-associations-transactions-2.json
loans/loan-45/loan-45-detail-associations-transactions-3.json
```

### 46 — C2893 — `PASSED` — loan 46 — Verify that the user is able to do a Charge-off for non-fraud loan after repayment - LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION product

Feature line 1585; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 13; all
committed under `loans/loan-46/`.

```
loans/loan-46/loan-46-detail-associations-all-1.json
loans/loan-46/loan-46-detail-associations-empty.json
loans/loan-46/loan-46-detail-no-associations-1.json
loans/loan-46/loan-46-detail-associations-all-2.json
loans/loan-46/loan-46-detail-associations-transactions-1.json
loans/loan-46/loan-46-detail-associations-all-3.json
loans/loan-46/loan-46-detail-associations-transactions-2.json
loans/loan-46/loan-46-detail-associations-all-4.json
loans/loan-46/loan-46-detail-no-associations-2.json
loans/loan-46/loan-46-detail-no-associations-3.json
loans/loan-46/loan-46-detail-associations-transactions-3.json
loans/loan-46/loan-46-detail-associations-transactions-4.json
loans/loan-46/loan-46-detail-associations-transactions-5.json
```

### 47 — C2894 — `PASSED` — loan 47 — Verify that the user is able to do a Repayment undo after Charge-off for non-fraud - LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION product

Feature line 1613; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 16; all
committed under `loans/loan-47/`.

```
loans/loan-47/loan-47-detail-associations-all-1.json
loans/loan-47/loan-47-detail-associations-empty.json
loans/loan-47/loan-47-detail-no-associations-1.json
loans/loan-47/loan-47-detail-associations-all-2.json
loans/loan-47/loan-47-detail-associations-transactions-1.json
loans/loan-47/loan-47-detail-associations-all-3.json
loans/loan-47/loan-47-detail-associations-transactions-2.json
loans/loan-47/loan-47-detail-associations-all-4.json
loans/loan-47/loan-47-detail-no-associations-2.json
loans/loan-47/loan-47-detail-associations-transactions-3.json
loans/loan-47/loan-47-detail-associations-all-5.json
loans/loan-47/loan-47-detail-no-associations-3.json
loans/loan-47/loan-47-detail-associations-transactions-4.json
loans/loan-47/loan-47-detail-associations-transactions-5.json
loans/loan-47/loan-47-detail-associations-transactions-6.json
loans/loan-47/loan-47-detail-associations-transactions-7.json
```

### 48 — C2895 — `PASSED` — loan 48 — Verify that the user is able to do a backdated Charge-off when only disbursement transaction happened - LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION product

Feature line 1645; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 9; all
committed under `loans/loan-48/`.

```
loans/loan-48/loan-48-detail-associations-all-1.json
loans/loan-48/loan-48-detail-associations-empty.json
loans/loan-48/loan-48-detail-no-associations.json
loans/loan-48/loan-48-detail-associations-all-2.json
loans/loan-48/loan-48-detail-associations-transactions-1.json
loans/loan-48/loan-48-detail-associations-all-3.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-1.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-2.json
loans/loan-48/loan-48-detail-associations-transactions-2.json
```

### 49 — C2896 — `PASSED` — loan 49 — Verify that charge-off is reversed/replayed if Goodwill credit transaction is placed on a date before the charge-off on business date after the charge-off - - LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION product

Feature line 1672; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 12; all
committed under `loans/loan-49/`.

```
loans/loan-49/loan-49-detail-associations-all-1.json
loans/loan-49/loan-49-detail-associations-empty.json
loans/loan-49/loan-49-detail-no-associations.json
loans/loan-49/loan-49-detail-associations-all-2.json
loans/loan-49/loan-49-detail-associations-transactions-1.json
loans/loan-49/loan-49-detail-associations-all-3.json
loans/loan-49/loan-49-charges-42-no-associations.json
loans/loan-49/loan-49-detail-associations-transactions-2.json
loans/loan-49/loan-49-detail-associations-all-4.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-1.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-2.json
loans/loan-49/loan-49-detail-associations-transactions-3.json
```

### 50 — C3067 — `PASSED` — loan 50 — Verify charge-off GL entries in case of reverse-replay on fraud loan

Feature line 1704; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 14; all
committed under `loans/loan-50/`.

```
loans/loan-50/loan-50-detail-associations-all-1.json
loans/loan-50/loan-50-detail-associations-empty.json
loans/loan-50/loan-50-detail-no-associations-1.json
loans/loan-50/loan-50-detail-associations-all-2.json
loans/loan-50/loan-50-detail-associations-transactions-1.json
loans/loan-50/loan-50-detail-associations-all-3.json
loans/loan-50/loan-50-detail-associations-transactions-2.json
loans/loan-50/loan-50-detail-associations-all-4.json
loans/loan-50/loan-50-detail-no-associations-2.json
loans/loan-50/loan-50-detail-associations-transactions-3.json
loans/loan-50/loan-50-detail-associations-transactions-4.json
loans/loan-50/loan-50-detail-associations-all-5.json
loans/loan-50/loan-50-detail-associations-transactions-5.json
loans/loan-50/loan-50-detail-associations-transactions-6.json
```

## The write-off branch — `/journalentries` evidence

The journal entries here are the charge-off posting (`createJournalEntriesForChargeOff`, :890)
and repayments on a charged-off loan (:1388) — NOT the charged-off write-off branch (:1616),
which this capture never reached (see the correction at the top).  Their output is GL journal
entries.  Those do not appear under `loans/`: the control-tested extractor is
loan-keyed and emits only `/loans` traffic.  The branch is observed directly in the
runner's `GET /journalentries?runningBalance=true&transactionId=L<loanId>` responses,
captured here by `extract-journalentries.py` and committed under `journalentries/`.

* **85** responses, **240** journal-entry legs, over **33** loans (2–5 responses each).
* Attribution is not assumed: every leg's `entityType` is `LOAN`, every response's
  `entityId` set is the single loan `N` and its `transactionId` is `L<N>`; every leg's
  `currency.code` is `MNT` (`decimalPlaces 2`).
* **43** of the 85 responses carry a charge-off leg.  Payments, refunds and
  running-balance reads make up the rest.

GL accounts seen across the 240 legs:

| GL account | code | legs |
| --- | --- | --- |
| Loans Receivable | 112601 | 81 |
| Suspense/Clearing account | 145023 | 56 |
| Fee Charge Off | — | 23 |
| Credit Loss/Bad Debt | 744007 | 21 |
| Interest/Fee Receivable | — | 19 |
| Credit Loss/Bad Debt-Fraud | — | 19 |
| Interest Income Charge Off | — | 16 |
| Recoveries | — | 5 |

Example — loan 1, feature line 5, `journalentries/loan-1/loan-1-journalentries-2.json`:
`DEBIT Credit Loss/Bad Debt 744007 100000` / `CREDIT Loans Receivable 112601 100000`
(minor units; the raw body carries `1000.0`).  That pair is the charge-off posting of the
principal (CHARGE_OFF_EXPENSE debit, LOAN_PORTFOLIO credit).

The manifest's `amount_minor` values are integer minor units (MNT, 2 ISO 4217 digits);
the raw bodies under `journalentries/` carry the decimal major units the oracle emitted,
unchanged, exactly as under `loans/`.  Each body's sha256 is in
`journalentries-manifest.json`; the GL-account leg counts are in
`journalentries-summary.json`.

## Failures

None. Every scenario passed; the charge-off posting (`createJournalEntriesForChargeOff`) was
exercised and the oracle agreed with every `.feature` journal-entry expectation.  The branch's GL legs are
committed above (`journalentries/`), so that claim is observation, not inference.  No EUR
control was run in this capture task.

## Currency

Every committed body carrying a currency object resolves to `code = "MNT"` (2950 occurrences across 788 bodies, including the 85 `journalentries/` read-backs); the literal token `EUR` appears in 0 committed bodies.  So the
oracle emitted MNT observations, not synthesis.

## Isolation

`preflight.sh` wrote the standing baseline before the throwaway started; `down.sh`
compared against that exact file and reported every counter equal to baseline
(`teardown-isolation.txt`).  All `tierd-*` containers, the `tierd-oracle` network and
its volume are gone; standing tenants `gerege` and `default` were never written.

---

This capture was created by an AI agent (OpenHands) on behalf of the user.
