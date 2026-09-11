# OWNER — Tier D `LoanDelinquency-Part1.feature` MNT capture

This directory owns the MNT read-backs captured by replaying the **whole**
`LoanDelinquency-Part1.feature` (50 scenarios: installment-level delinquency and
delinquency PAUSE periods) against the throwaway reference oracle, tenant `tierd`.
Capture only: no vector, no drive, no `.go`.

## What is here

| path | what |
| --- | --- |
| `OWNER.md` | this file: feature, scenarios, loans, and which read-back files belong to each |
| `replay-result-table.md` | the per-scenario PASSED/FAILED result table |
| `replay-delinquency-mnt.log` | raw cucumber/Gradle replay log (ANSI), 1,745 lines |
| `run-delinquency-mnt.sh` | the exact driver used for the replay |
| `scenario-results.json` | machine-readable per-scenario result + loan mapping |
| `attribute.py` | validated scenario→loan attribution (product name + clientId) |
| `organize.py` | flattens `stage/` into `loans/` and writes the manifests |
| `manifest-delinquency.json` | full extraction manifest (all 49 loans; `committed` flag) |
| `manifest-delinquency-passed.json` | manifest of the committed files (all PASSED) |
| `summary-delinquency.json` | extractor totals and per-loan counts |
| `loans/loan-<id>/` | the per-loan read-backs committed for the PASSED scenarios |
| `teardown-isolation.txt` | baseline-vs-teardown counter comparison |

## Source

- feature: `fineract-e2e-tests-runner/src/test/resources/features/LoanDelinquency-Part1.feature`
- throwaway tenant `tierd`; image `fineract:latest` `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`
  (proven identical to the standing reference oracle by `preflight.sh`)
- currency MNT (2 ISO 4217 minor digits, 496); money below is integer minor units
- capture: `/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-delinquency-mnt.log`
- capture size: 268334990 B / 94787 lines
- extraction: 3577 exchanges, 860 loan-keyed, 49 loans, 1026 files, 6830716 kept body bytes
- replay: 50 scenarios (50 passed); 1124 steps (1124 passed); no failure

## Scenario → loan map

Every scenario creates exactly one client and one customized loan at the top. Scenario
33 (C3014) deliberately makes its loan creation fail, so it owns no loan id and is the
run's single unattributed `POST /loans`; loan ids are contiguous 1..49 over scenarios
1..32, 34..50 in feature order. The mapping is not assumed: each loan's read-back
`loanProductName` equals its scenario's feature product and its `clientId` equals the
scenario position (`attribute.py`; 0 mismatches over 49 loans).

| # | TestRailId | feature line | result | loan | product | principal (minor) | read-backs | committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C2963 | 5 | PASSED | 1 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 10 | yes |
| 2 | C2964 | 26 | PASSED | 2 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 10 | yes |
| 3 | C2965 | 47 | PASSED | 3 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 10 | yes |
| 4 | C2966 | 69 | PASSED | 4 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 5 | C2967 | 84 | PASSED | 5 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 6 | C2968 | 99 | PASSED | 6 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 7 | C2969 | 114 | PASSED | 7 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 13 | yes |
| 8 | C2970 | 139 | PASSED | 8 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 13 | yes |
| 9 | C2971 | 162 | PASSED | 9 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 10 | C2972 | 179 | PASSED | 10 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 6 | yes |
| 11 | C2973 | 190 | PASSED | 11 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 12 | C2974 | 207 | PASSED | 12 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 13 | C2975 | 224 | PASSED | 13 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 14 | C2992 | 241 | PASSED | 14 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 13 | yes |
| 15 | C2979 | 269 | PASSED | 15 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 7 | yes |
| 16 | C2980 | 286 | PASSED | 16 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 8 | yes |
| 17 | C2981 | 311 | PASSED | 17 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 10 | yes |
| 18 | C2982 | 332 | PASSED | 18 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 10 | yes |
| 19 | C2983 | 354 | PASSED | 19 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 10 | yes |
| 20 | C2984 | 375 | PASSED | 20 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 10 | yes |
| 21 | C2985 | 397 | PASSED | 21 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 9 | yes |
| 22 | C2987 | 417 | PASSED | 22 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 12 | yes |
| 23 | C2988 | 467 | PASSED | 23 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 13 | yes |
| 24 | C2990 | 513 | PASSED | 24 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 8 | yes |
| 25 | C2991 | 531 | PASSED | 25 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 6 | yes |
| 26 | C2999 | 545 | PASSED | 26 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 23 | yes |
| 27 | C3000 | 617 | PASSED | 27 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 17 | yes |
| 28 | C3001 | 667 | PASSED | 28 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 34 | yes |
| 29 | C3002 | 797 | PASSED | 29 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 21 | yes |
| 30 | C3003 | 853 | PASSED | 30 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 21 | yes |
| 31 | C3004 | 912 | PASSED | 31 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 31 | yes |
| 32 | C3013 | 1005 | PASSED | 32 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 24 | yes |
| 33 | C3014 | 1070 | PASSED | — | — | — | 0 | n/a (error scenario) |
| 34 | C3015 | 1078 | PASSED | 33 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 14 | yes |
| 35 | C3016 | 1113 | PASSED | 34 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 19 | yes |
| 36 | C3018 | 1168 | PASSED | 35 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 8 | yes |
| 37 | C3019 | 1184 | PASSED | 36 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 8 | yes |
| 38 | C3032 | 1200 | PASSED | 37 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 7 | yes |
| 39 | C3035 | 1216 | PASSED | 38 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY` | 100000 | 4 | yes |
| 40 | C3047 | 1231 | PASSED | 39 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 7 | yes |
| 41 | C3066 | 1243 | PASSED | 40 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 4 | yes |
| 42 | C3135 | 1257 | PASSED | 41 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 7 | yes |
| 43 | C3136 | 1282 | PASSED | 42 | `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION` | 100000 | 7 | yes |
| 44 | C3137 | 1307 | PASSED | 43 | `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL` | 100000 | 7 | yes |
| 45 | C3930 | 1324 | PASSED | 44 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 100000 | 24 | yes |
| 46 | C3931 | 1394 | PASSED | 45 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30` | 100000 | 22 | yes |
| 47 | C3932 | 1460 | PASSED | 46 | `LP2_INTEREST_FLAT_ADV_PMT_ALLOC_MULTIDISBURSE` | 100000 | 23 | yes |
| 48 | C3933 | 1524 | PASSED | 47 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 100000 | 21 | yes |
| 49 | C3934 | 1586 | PASSED | 48 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 100000 | 27 | yes |
| 50 | C3935 | 1658 | PASSED | 49 | `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE` | 100000 | 26 | yes |

## Per-scenario read-back files

`loans/loan-<id>/` holds **every** exchange the extractor attributed to that loan: the
`create-request`, the `approve`/`disburse`/`delinquency-actions`/`repayment`/... command
request+response pairs, and the `GET` read-backs. The read-backs (kind `read`) belonging
to each PASSED scenario are listed below; command request/response pairs sit in the same
directory and are visible in `manifest-delinquency.json`.

### 1 — C2963 — `PASSED` — loan 1 — Verify Loan delinquency pause API - PAUSE and RESUME by loanId

Feature line 5; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 10.

```
loans/loan-1/loan-1-detail-associations-all-1.json
loans/loan-1/loan-1-detail-associations-empty.json
loans/loan-1/loan-1-detail-no-associations.json
loans/loan-1/loan-1-detail-associations-all-2.json
loans/loan-1/loan-1-detail-associations-transactions.json
loans/loan-1/loan-1-detail-associations-all-3.json
loans/loan-1/loan-1-detail-associations-all-4.json
loans/loan-1/loan-1-delinquency-actions-no-associations-1.json
loans/loan-1/loan-1-detail-associations-all-5.json
loans/loan-1/loan-1-delinquency-actions-no-associations-2.json
```

### 2 — C2964 — `PASSED` — loan 2 — Verify Loan delinquency pause API - PAUSE and RESUME by loanExternalId

Feature line 26; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 10.

```
loans/loan-2/loan-2-detail-associations-all-1.json
loans/loan-2/loan-2-detail-associations-empty.json
loans/loan-2/loan-2-detail-no-associations.json
loans/loan-2/loan-2-detail-associations-all-2.json
loans/loan-2/loan-2-detail-associations-transactions.json
loans/loan-2/loan-2-detail-associations-all-3.json
loans/loan-2/loan-2-detail-associations-all-4.json
loans/loan-2/loan-2-delinquency-actions-no-associations-1.json
loans/loan-2/loan-2-detail-associations-all-5.json
loans/loan-2/loan-2-delinquency-actions-no-associations-2.json
```

### 3 — C2965 — `PASSED` — loan 3 — Verify Loan delinquency pause API - PAUSE and RESUME actions supported only

Feature line 47; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 10.

```
loans/loan-3/loan-3-detail-associations-all-1.json
loans/loan-3/loan-3-detail-associations-empty.json
loans/loan-3/loan-3-detail-no-associations.json
loans/loan-3/loan-3-detail-associations-all-2.json
loans/loan-3/loan-3-detail-associations-transactions.json
loans/loan-3/loan-3-detail-associations-all-3.json
loans/loan-3/loan-3-detail-associations-all-4.json
loans/loan-3/loan-3-delinquency-actions-no-associations-1.json
loans/loan-3/loan-3-detail-associations-all-5.json
loans/loan-3/loan-3-delinquency-actions-no-associations-2.json
```

### 4 — C2966 — `PASSED` — loan 4 — Verify Loan delinquency pause API - PAUSE with start date on actual business date

Feature line 69; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-4/loan-4-detail-associations-all-1.json
loans/loan-4/loan-4-detail-associations-empty.json
loans/loan-4/loan-4-detail-no-associations.json
loans/loan-4/loan-4-detail-associations-all-2.json
loans/loan-4/loan-4-detail-associations-transactions.json
loans/loan-4/loan-4-detail-associations-all-3.json
loans/loan-4/loan-4-detail-associations-all-4.json
loans/loan-4/loan-4-delinquency-actions-no-associations.json
```

### 5 — C2967 — `PASSED` — loan 5 — Verify Loan delinquency pause API - PAUSE with start date later than actual business date

Feature line 84; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-5/loan-5-detail-associations-all-1.json
loans/loan-5/loan-5-detail-associations-empty.json
loans/loan-5/loan-5-detail-no-associations.json
loans/loan-5/loan-5-detail-associations-all-2.json
loans/loan-5/loan-5-detail-associations-transactions.json
loans/loan-5/loan-5-detail-associations-all-3.json
loans/loan-5/loan-5-detail-associations-all-4.json
loans/loan-5/loan-5-delinquency-actions-no-associations.json
```

### 6 — C2968 — `PASSED` — loan 6 — Verify Loan delinquency pause API - PAUSE with start date before than actual business date is possible

Feature line 99; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-6/loan-6-detail-associations-all-1.json
loans/loan-6/loan-6-detail-associations-empty.json
loans/loan-6/loan-6-detail-no-associations.json
loans/loan-6/loan-6-detail-associations-all-2.json
loans/loan-6/loan-6-detail-associations-transactions.json
loans/loan-6/loan-6-detail-associations-all-3.json
loans/loan-6/loan-6-detail-associations-all-4.json
loans/loan-6/loan-6-delinquency-actions-no-associations.json
```

### 7 — C2969 — `PASSED` — loan 7 — Verify Loan delinquency pause API - PAUSE action on non-active loan result an error

Feature line 114; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 13.

```
loans/loan-7/loan-7-detail-associations-all-1.json
loans/loan-7/loan-7-detail-no-associations-1.json
loans/loan-7/loan-7-detail-associations-empty.json
loans/loan-7/loan-7-detail-no-associations-2.json
loans/loan-7/loan-7-detail-no-associations-3.json
loans/loan-7/loan-7-detail-associations-all-2.json
loans/loan-7/loan-7-detail-associations-transactions-1.json
loans/loan-7/loan-7-detail-associations-all-3.json
loans/loan-7/loan-7-detail-associations-transactions-2.json
loans/loan-7/loan-7-detail-associations-all-4.json
loans/loan-7/loan-7-detail-no-associations-4.json
loans/loan-7/loan-7-detail-associations-all-5.json
loans/loan-7/loan-7-detail-no-associations-5.json
```

### 8 — C2970 — `PASSED` — loan 8 — Verify Loan delinquency pause API - RESUME action on non-active loan result an error

Feature line 139; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 13.

```
loans/loan-8/loan-8-detail-associations-all-1.json
loans/loan-8/loan-8-detail-associations-empty.json
loans/loan-8/loan-8-detail-no-associations-1.json
loans/loan-8/loan-8-detail-associations-all-2.json
loans/loan-8/loan-8-detail-associations-transactions-1.json
loans/loan-8/loan-8-detail-associations-all-3.json
loans/loan-8/loan-8-detail-associations-all-4.json
loans/loan-8/loan-8-delinquency-actions-no-associations.json
loans/loan-8/loan-8-detail-associations-transactions-2.json
loans/loan-8/loan-8-detail-associations-all-5.json
loans/loan-8/loan-8-detail-no-associations-2.json
loans/loan-8/loan-8-detail-associations-all-6.json
loans/loan-8/loan-8-detail-no-associations-3.json
```

### 9 — C2971 — `PASSED` — loan 9 — Verify Loan delinquency pause API - Overlapping PAUSE periods result an error

Feature line 162; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-9/loan-9-detail-associations-all-1.json
loans/loan-9/loan-9-detail-associations-empty.json
loans/loan-9/loan-9-detail-no-associations.json
loans/loan-9/loan-9-detail-associations-all-2.json
loans/loan-9/loan-9-detail-associations-transactions.json
loans/loan-9/loan-9-detail-associations-all-3.json
loans/loan-9/loan-9-detail-associations-all-4.json
loans/loan-9/loan-9-delinquency-actions-no-associations.json
```

### 10 — C2972 — `PASSED` — loan 10 — Verify Loan delinquency pause API - RESUME without an active PAUSE period results an error

Feature line 179; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 6.

```
loans/loan-10/loan-10-detail-associations-all-1.json
loans/loan-10/loan-10-detail-associations-empty.json
loans/loan-10/loan-10-detail-no-associations.json
loans/loan-10/loan-10-detail-associations-all-2.json
loans/loan-10/loan-10-detail-associations-transactions.json
loans/loan-10/loan-10-detail-associations-all-3.json
```

### 11 — C2973 — `PASSED` — loan 11 — Verify Loan delinquency pause API - RESUME with start date before than actual business date results an error

Feature line 190; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-11/loan-11-detail-associations-all-1.json
loans/loan-11/loan-11-detail-associations-empty.json
loans/loan-11/loan-11-detail-no-associations.json
loans/loan-11/loan-11-detail-associations-all-2.json
loans/loan-11/loan-11-detail-associations-transactions.json
loans/loan-11/loan-11-detail-associations-all-3.json
loans/loan-11/loan-11-detail-associations-all-4.json
loans/loan-11/loan-11-delinquency-actions-no-associations.json
```

### 12 — C2974 — `PASSED` — loan 12 — Verify Loan delinquency pause API - RESUME with start date later than actual business date results an error

Feature line 207; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-12/loan-12-detail-associations-all-1.json
loans/loan-12/loan-12-detail-associations-empty.json
loans/loan-12/loan-12-detail-no-associations.json
loans/loan-12/loan-12-detail-associations-all-2.json
loans/loan-12/loan-12-detail-associations-transactions.json
loans/loan-12/loan-12-detail-associations-all-3.json
loans/loan-12/loan-12-detail-associations-all-4.json
loans/loan-12/loan-12-delinquency-actions-no-associations.json
```

### 13 — C2975 — `PASSED` — loan 13 — Verify Loan delinquency pause API - RESUME with end date results an error

Feature line 224; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-13/loan-13-detail-associations-all-1.json
loans/loan-13/loan-13-detail-associations-empty.json
loans/loan-13/loan-13-detail-no-associations.json
loans/loan-13/loan-13-detail-associations-all-2.json
loans/loan-13/loan-13-detail-associations-transactions.json
loans/loan-13/loan-13-detail-associations-all-3.json
loans/loan-13/loan-13-detail-associations-all-4.json
loans/loan-13/loan-13-delinquency-actions-no-associations.json
```

### 14 — C2992 — `PASSED` — loan 14 — Verify Loan level loan delinquency - loan goes into delinquency pause then will be resumed

Feature line 241; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 13.

```
loans/loan-14/loan-14-detail-associations-all-1.json
loans/loan-14/loan-14-detail-associations-empty.json
loans/loan-14/loan-14-detail-no-associations.json
loans/loan-14/loan-14-detail-associations-all-2.json
loans/loan-14/loan-14-detail-associations-transactions.json
loans/loan-14/loan-14-detail-associations-all-3.json
loans/loan-14/loan-14-detail-associations-collection-1.json
loans/loan-14/loan-14-detail-associations-all-4.json
loans/loan-14/loan-14-delinquency-actions-no-associations-1.json
loans/loan-14/loan-14-detail-associations-collection-2.json
loans/loan-14/loan-14-detail-associations-all-5.json
loans/loan-14/loan-14-delinquency-actions-no-associations-2.json
loans/loan-14/loan-14-detail-associations-collection-3.json
```

### 15 — C2979 — `PASSED` — loan 15 — Verify Installment level loan delinquency - loan goes into delinquency bucket

Feature line 269; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 7.

```
loans/loan-15/loan-15-detail-associations-all-1.json
loans/loan-15/loan-15-detail-associations-empty.json
loans/loan-15/loan-15-detail-no-associations.json
loans/loan-15/loan-15-detail-associations-all-2.json
loans/loan-15/loan-15-detail-associations-transactions.json
loans/loan-15/loan-15-detail-associations-all-3.json
loans/loan-15/loan-15-detail-associations-collection.json
```

### 16 — C2980 — `PASSED` — loan 16 — Verify Installment level loan delinquency - loan goes from one delinquency bucket to an other

Feature line 286; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 8.

```
loans/loan-16/loan-16-detail-associations-all-1.json
loans/loan-16/loan-16-detail-associations-empty.json
loans/loan-16/loan-16-detail-no-associations.json
loans/loan-16/loan-16-detail-associations-all-2.json
loans/loan-16/loan-16-detail-associations-transactions.json
loans/loan-16/loan-16-detail-associations-all-3.json
loans/loan-16/loan-16-detail-associations-collection-1.json
loans/loan-16/loan-16-detail-associations-collection-2.json
```

### 17 — C2981 — `PASSED` — loan 17 — Verify Installment level loan delinquency - loan goes out from delinquency by late repayment

Feature line 311; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 10.

```
loans/loan-17/loan-17-detail-associations-all-1.json
loans/loan-17/loan-17-detail-associations-empty.json
loans/loan-17/loan-17-detail-no-associations.json
loans/loan-17/loan-17-detail-associations-all-2.json
loans/loan-17/loan-17-detail-associations-transactions-1.json
loans/loan-17/loan-17-detail-associations-all-3.json
loans/loan-17/loan-17-detail-associations-collection-1.json
loans/loan-17/loan-17-detail-associations-transactions-2.json
loans/loan-17/loan-17-detail-associations-all-4.json
loans/loan-17/loan-17-detail-associations-collection-2.json
```

### 18 — C2982 — `PASSED` — loan 18 — Verify Installment level loan delinquency - some of the installments go out from delinquency by late repayment

Feature line 332; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 10.

```
loans/loan-18/loan-18-detail-associations-all-1.json
loans/loan-18/loan-18-detail-associations-empty.json
loans/loan-18/loan-18-detail-no-associations.json
loans/loan-18/loan-18-detail-associations-all-2.json
loans/loan-18/loan-18-detail-associations-transactions-1.json
loans/loan-18/loan-18-detail-associations-all-3.json
loans/loan-18/loan-18-detail-associations-collection-1.json
loans/loan-18/loan-18-detail-associations-transactions-2.json
loans/loan-18/loan-18-detail-associations-all-4.json
loans/loan-18/loan-18-detail-associations-collection-2.json
```

### 19 — C2983 — `PASSED` — loan 19 — Verify Installment level loan delinquency - loan goes out from delinquency by Goodwill credit transaction

Feature line 354; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 10.

```
loans/loan-19/loan-19-detail-associations-all-1.json
loans/loan-19/loan-19-detail-associations-empty.json
loans/loan-19/loan-19-detail-no-associations.json
loans/loan-19/loan-19-detail-associations-all-2.json
loans/loan-19/loan-19-detail-associations-transactions-1.json
loans/loan-19/loan-19-detail-associations-all-3.json
loans/loan-19/loan-19-detail-associations-collection-1.json
loans/loan-19/loan-19-detail-associations-transactions-2.json
loans/loan-19/loan-19-detail-associations-all-4.json
loans/loan-19/loan-19-detail-associations-collection-2.json
```

### 20 — C2984 — `PASSED` — loan 20 — Verify Installment level loan delinquency - some of the installments go out from delinquency by Goodwill credit transaction

Feature line 375; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 10.

```
loans/loan-20/loan-20-detail-associations-all-1.json
loans/loan-20/loan-20-detail-associations-empty.json
loans/loan-20/loan-20-detail-no-associations.json
loans/loan-20/loan-20-detail-associations-all-2.json
loans/loan-20/loan-20-detail-associations-transactions-1.json
loans/loan-20/loan-20-detail-associations-all-3.json
loans/loan-20/loan-20-detail-associations-collection-1.json
loans/loan-20/loan-20-detail-associations-transactions-2.json
loans/loan-20/loan-20-detail-associations-all-4.json
loans/loan-20/loan-20-detail-associations-collection-2.json
```

### 21 — C2985 — `PASSED` — loan 21 — Verify Installment level loan delinquency - loan with charges goes into delinquency bucket

Feature line 397; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 9.

```
loans/loan-21/loan-21-detail-associations-all-1.json
loans/loan-21/loan-21-detail-associations-empty.json
loans/loan-21/loan-21-detail-no-associations.json
loans/loan-21/loan-21-detail-associations-all-2.json
loans/loan-21/loan-21-detail-associations-transactions.json
loans/loan-21/loan-21-detail-associations-all-3.json
loans/loan-21/loan-21-charges-1-no-associations.json
loans/loan-21/loan-21-charges-2-no-associations.json
loans/loan-21/loan-21-detail-associations-collection.json
```

### 22 — C2987 — `PASSED` — loan 22 — Verify Installment level loan delinquency - loan goes into delinquency pause

Feature line 417; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 12.

```
loans/loan-22/loan-22-detail-associations-all-1.json
loans/loan-22/loan-22-detail-associations-empty.json
loans/loan-22/loan-22-detail-no-associations.json
loans/loan-22/loan-22-detail-associations-all-2.json
loans/loan-22/loan-22-detail-associations-transactions.json
loans/loan-22/loan-22-detail-associations-all-3.json
loans/loan-22/loan-22-detail-associations-collection-1.json
loans/loan-22/loan-22-detail-associations-all-4.json
loans/loan-22/loan-22-delinquency-actions-no-associations.json
loans/loan-22/loan-22-detail-associations-collection-2.json
loans/loan-22/loan-22-detail-associations-collection-3.json
loans/loan-22/loan-22-detail-associations-collection-4.json
```

### 23 — C2988 — `PASSED` — loan 23 — Verify Installment level loan delinquency - loan goes into delinquency pause then will be resumed

Feature line 467; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 13.

```
loans/loan-23/loan-23-detail-associations-all-1.json
loans/loan-23/loan-23-detail-associations-empty.json
loans/loan-23/loan-23-detail-no-associations.json
loans/loan-23/loan-23-detail-associations-all-2.json
loans/loan-23/loan-23-detail-associations-transactions.json
loans/loan-23/loan-23-detail-associations-all-3.json
loans/loan-23/loan-23-detail-associations-collection-1.json
loans/loan-23/loan-23-detail-associations-all-4.json
loans/loan-23/loan-23-delinquency-actions-no-associations-1.json
loans/loan-23/loan-23-detail-associations-collection-2.json
loans/loan-23/loan-23-detail-associations-all-5.json
loans/loan-23/loan-23-delinquency-actions-no-associations-2.json
loans/loan-23/loan-23-detail-associations-collection-3.json
```

### 24 — C2990 — `PASSED` — loan 24 — Verify that a non-super user with CREATE_DELINQUENCY_ACTION permission can initiate a DELINQUENCY PAUSE

Feature line 513; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 8.

```
loans/loan-24/loan-24-detail-associations-all-1.json
loans/loan-24/loan-24-detail-associations-empty.json
loans/loan-24/loan-24-detail-no-associations.json
loans/loan-24/loan-24-detail-associations-all-2.json
loans/loan-24/loan-24-detail-associations-transactions.json
loans/loan-24/loan-24-detail-associations-all-3.json
loans/loan-24/loan-24-detail-associations-all-4.json
loans/loan-24/loan-24-delinquency-actions-no-associations.json
```

### 25 — C2991 — `PASSED` — loan 25 — Verify that a non-super user with no CREATE_DELINQUENCY_ACTION permission gets an error when initiate a DELINQUENCY PAUSE

Feature line 531; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 6.

```
loans/loan-25/loan-25-detail-associations-all-1.json
loans/loan-25/loan-25-detail-associations-empty.json
loans/loan-25/loan-25-detail-no-associations.json
loans/loan-25/loan-25-detail-associations-all-2.json
loans/loan-25/loan-25-detail-associations-transactions.json
loans/loan-25/loan-25-detail-associations-all-3.json
```

### 26 — C2999 — `PASSED` — loan 26 — Verify Loan delinquency pause E2E - full PAUSE period

Feature line 545; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 23.

```
loans/loan-26/loan-26-detail-associations-all-1.json
loans/loan-26/loan-26-detail-associations-empty.json
loans/loan-26/loan-26-detail-no-associations.json
loans/loan-26/loan-26-detail-associations-all-2.json
loans/loan-26/loan-26-detail-associations-transactions.json
loans/loan-26/loan-26-detail-associations-all-3.json
loans/loan-26/loan-26-detail-associations-collection-1.json
loans/loan-26/loan-26-detail-associations-collection-2.json
loans/loan-26/loan-26-detail-associations-collection-3.json
loans/loan-26/loan-26-detail-associations-collection-4.json
loans/loan-26/loan-26-detail-associations-collection-5.json
loans/loan-26/loan-26-detail-associations-collection-6.json
loans/loan-26/loan-26-detail-associations-all-4.json
loans/loan-26/loan-26-detail-associations-collection-7.json
loans/loan-26/loan-26-delinquency-actions-no-associations.json
loans/loan-26/loan-26-detail-associations-collection-8.json
loans/loan-26/loan-26-detail-associations-collection-9.json
loans/loan-26/loan-26-detail-associations-collection-10.json
loans/loan-26/loan-26-detail-associations-collection-11.json
loans/loan-26/loan-26-detail-associations-collection-12.json
loans/loan-26/loan-26-detail-associations-collection-13.json
loans/loan-26/loan-26-detail-associations-collection-14.json
loans/loan-26/loan-26-detail-associations-collection-15.json
```

### 27 — C3000 — `PASSED` — loan 27 — Verify Loan delinquency pause E2E - PAUSE period with RESUME

Feature line 617; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 17.

```
loans/loan-27/loan-27-detail-associations-all-1.json
loans/loan-27/loan-27-detail-associations-empty.json
loans/loan-27/loan-27-detail-no-associations.json
loans/loan-27/loan-27-detail-associations-all-2.json
loans/loan-27/loan-27-detail-associations-transactions.json
loans/loan-27/loan-27-detail-associations-all-3.json
loans/loan-27/loan-27-detail-associations-all-4.json
loans/loan-27/loan-27-detail-associations-collection-1.json
loans/loan-27/loan-27-delinquency-actions-no-associations-1.json
loans/loan-27/loan-27-detail-associations-collection-2.json
loans/loan-27/loan-27-detail-associations-collection-3.json
loans/loan-27/loan-27-detail-associations-all-5.json
loans/loan-27/loan-27-detail-associations-collection-4.json
loans/loan-27/loan-27-detail-associations-collection-5.json
loans/loan-27/loan-27-delinquency-actions-no-associations-2.json
loans/loan-27/loan-27-detail-associations-collection-6.json
loans/loan-27/loan-27-detail-associations-collection-7.json
```

### 28 — C3001 — `PASSED` — loan 28 — Verify Loan delinquency pause E2E - PAUSE period with RESUME and second PAUSE

Feature line 667; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 34.

```
loans/loan-28/loan-28-detail-associations-all-1.json
loans/loan-28/loan-28-detail-associations-empty.json
loans/loan-28/loan-28-detail-no-associations.json
loans/loan-28/loan-28-detail-associations-all-2.json
loans/loan-28/loan-28-detail-associations-transactions.json
loans/loan-28/loan-28-detail-associations-all-3.json
loans/loan-28/loan-28-detail-associations-all-4.json
loans/loan-28/loan-28-detail-associations-collection-1.json
loans/loan-28/loan-28-delinquency-actions-no-associations-1.json
loans/loan-28/loan-28-detail-associations-collection-2.json
loans/loan-28/loan-28-detail-associations-collection-3.json
loans/loan-28/loan-28-detail-associations-all-5.json
loans/loan-28/loan-28-detail-associations-collection-4.json
loans/loan-28/loan-28-detail-associations-collection-5.json
loans/loan-28/loan-28-delinquency-actions-no-associations-2.json
loans/loan-28/loan-28-detail-associations-collection-6.json
loans/loan-28/loan-28-detail-associations-collection-7.json
loans/loan-28/loan-28-detail-associations-collection-8.json
loans/loan-28/loan-28-delinquency-actions-no-associations-3.json
loans/loan-28/loan-28-detail-associations-collection-9.json
loans/loan-28/loan-28-detail-associations-collection-10.json
loans/loan-28/loan-28-detail-associations-all-6.json
loans/loan-28/loan-28-detail-associations-collection-11.json
loans/loan-28/loan-28-delinquency-actions-no-associations-4.json
loans/loan-28/loan-28-detail-associations-collection-12.json
loans/loan-28/loan-28-detail-associations-collection-13.json
loans/loan-28/loan-28-detail-associations-collection-14.json
loans/loan-28/loan-28-delinquency-actions-no-associations-5.json
loans/loan-28/loan-28-detail-associations-collection-15.json
loans/loan-28/loan-28-detail-associations-collection-16.json
loans/loan-28/loan-28-detail-associations-collection-17.json
loans/loan-28/loan-28-delinquency-actions-no-associations-6.json
loans/loan-28/loan-28-detail-associations-collection-18.json
loans/loan-28/loan-28-detail-associations-collection-19.json
```

### 29 — C3002 — `PASSED` — loan 29 — Verify Loan delinquency pause E2E - full repayment (late/due date) during PAUSE period

Feature line 797; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 21.

```
loans/loan-29/loan-29-detail-associations-all-1.json
loans/loan-29/loan-29-detail-associations-empty.json
loans/loan-29/loan-29-detail-no-associations.json
loans/loan-29/loan-29-detail-associations-all-2.json
loans/loan-29/loan-29-detail-associations-transactions-1.json
loans/loan-29/loan-29-detail-associations-all-3.json
loans/loan-29/loan-29-detail-associations-all-4.json
loans/loan-29/loan-29-detail-associations-collection-1.json
loans/loan-29/loan-29-delinquency-actions-no-associations-1.json
loans/loan-29/loan-29-detail-associations-collection-2.json
loans/loan-29/loan-29-detail-associations-collection-3.json
loans/loan-29/loan-29-detail-associations-collection-4.json
loans/loan-29/loan-29-delinquency-actions-no-associations-2.json
loans/loan-29/loan-29-detail-associations-collection-5.json
loans/loan-29/loan-29-detail-associations-collection-6.json
loans/loan-29/loan-29-detail-associations-transactions-2.json
loans/loan-29/loan-29-detail-associations-all-5.json
loans/loan-29/loan-29-detail-associations-collection-7.json
loans/loan-29/loan-29-delinquency-actions-no-associations-3.json
loans/loan-29/loan-29-detail-associations-collection-8.json
loans/loan-29/loan-29-detail-associations-collection-9.json
```

### 30 — C3003 — `PASSED` — loan 30 — Verify Loan delinquency pause E2E - partial repayment during PAUSE period

Feature line 853; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 21.

```
loans/loan-30/loan-30-detail-associations-all-1.json
loans/loan-30/loan-30-detail-associations-empty.json
loans/loan-30/loan-30-detail-no-associations.json
loans/loan-30/loan-30-detail-associations-all-2.json
loans/loan-30/loan-30-detail-associations-transactions-1.json
loans/loan-30/loan-30-detail-associations-all-3.json
loans/loan-30/loan-30-detail-associations-all-4.json
loans/loan-30/loan-30-detail-associations-collection-1.json
loans/loan-30/loan-30-delinquency-actions-no-associations-1.json
loans/loan-30/loan-30-detail-associations-collection-2.json
loans/loan-30/loan-30-detail-associations-collection-3.json
loans/loan-30/loan-30-detail-associations-collection-4.json
loans/loan-30/loan-30-delinquency-actions-no-associations-2.json
loans/loan-30/loan-30-detail-associations-collection-5.json
loans/loan-30/loan-30-detail-associations-collection-6.json
loans/loan-30/loan-30-detail-associations-transactions-2.json
loans/loan-30/loan-30-detail-associations-all-5.json
loans/loan-30/loan-30-detail-associations-collection-7.json
loans/loan-30/loan-30-delinquency-actions-no-associations-3.json
loans/loan-30/loan-30-detail-associations-collection-8.json
loans/loan-30/loan-30-detail-associations-collection-9.json
```

### 31 — C3004 — `PASSED` — loan 31 — Verify Loan delinquency pause E2E - full repayment (only late) during PAUSE period then RESUME

Feature line 912; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 31.

```
loans/loan-31/loan-31-detail-associations-all-1.json
loans/loan-31/loan-31-detail-associations-empty.json
loans/loan-31/loan-31-detail-no-associations.json
loans/loan-31/loan-31-detail-associations-all-2.json
loans/loan-31/loan-31-detail-associations-transactions-1.json
loans/loan-31/loan-31-detail-associations-all-3.json
loans/loan-31/loan-31-detail-associations-all-4.json
loans/loan-31/loan-31-detail-associations-collection-1.json
loans/loan-31/loan-31-delinquency-actions-no-associations-1.json
loans/loan-31/loan-31-detail-associations-collection-2.json
loans/loan-31/loan-31-detail-associations-collection-3.json
loans/loan-31/loan-31-detail-associations-collection-4.json
loans/loan-31/loan-31-delinquency-actions-no-associations-2.json
loans/loan-31/loan-31-detail-associations-collection-5.json
loans/loan-31/loan-31-detail-associations-collection-6.json
loans/loan-31/loan-31-detail-associations-transactions-2.json
loans/loan-31/loan-31-detail-associations-all-5.json
loans/loan-31/loan-31-detail-associations-collection-7.json
loans/loan-31/loan-31-delinquency-actions-no-associations-3.json
loans/loan-31/loan-31-detail-associations-collection-8.json
loans/loan-31/loan-31-detail-associations-collection-9.json
loans/loan-31/loan-31-detail-associations-all-6.json
loans/loan-31/loan-31-detail-associations-collection-10.json
loans/loan-31/loan-31-detail-associations-collection-11.json
loans/loan-31/loan-31-delinquency-actions-no-associations-4.json
loans/loan-31/loan-31-detail-associations-collection-12.json
loans/loan-31/loan-31-detail-associations-collection-13.json
loans/loan-31/loan-31-detail-associations-collection-14.json
loans/loan-31/loan-31-delinquency-actions-no-associations-5.json
loans/loan-31/loan-31-detail-associations-collection-15.json
loans/loan-31/loan-31-detail-associations-collection-16.json
```

### 32 — C3013 — `PASSED` — loan 32 — Verify that in case of resume on end/start date of continous pause periods first period ends automatically, second period ended by resume

Feature line 1005; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 24.

```
loans/loan-32/loan-32-detail-associations-all-1.json
loans/loan-32/loan-32-detail-associations-empty.json
loans/loan-32/loan-32-detail-no-associations.json
loans/loan-32/loan-32-detail-associations-all-2.json
loans/loan-32/loan-32-detail-associations-transactions.json
loans/loan-32/loan-32-detail-associations-all-3.json
loans/loan-32/loan-32-detail-associations-all-4.json
loans/loan-32/loan-32-delinquency-actions-no-associations-1.json
loans/loan-32/loan-32-detail-associations-collection-1.json
loans/loan-32/loan-32-detail-associations-all-5.json
loans/loan-32/loan-32-delinquency-actions-no-associations-2.json
loans/loan-32/loan-32-detail-associations-collection-2.json
loans/loan-32/loan-32-detail-associations-collection-3.json
loans/loan-32/loan-32-detail-associations-collection-4.json
loans/loan-32/loan-32-detail-associations-all-6.json
loans/loan-32/loan-32-detail-associations-collection-5.json
loans/loan-32/loan-32-detail-associations-collection-6.json
loans/loan-32/loan-32-delinquency-actions-no-associations-3.json
loans/loan-32/loan-32-detail-associations-collection-7.json
loans/loan-32/loan-32-detail-associations-collection-8.json
loans/loan-32/loan-32-detail-associations-collection-9.json
loans/loan-32/loan-32-detail-associations-collection-10.json
loans/loan-32/loan-32-detail-associations-collection-11.json
loans/loan-32/loan-32-detail-associations-collection-12.json
```

### 33 — C3014 — `PASSED` (error scenario) — no loan

Feature line 1070: the loan creation is expected to fail, so no loan id and no
read-backs exist.

### 34 — C3015 — `PASSED` — loan 33 — Verify Backdated Pause Delinquency - Event Trigger: LoanDelinquencyRangeChangeBusinessEvent, LoanAccountDelinquencyPauseChangedBusinessEvent check

Feature line 1078; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 14.

```
loans/loan-33/loan-33-detail-associations-all-1.json
loans/loan-33/loan-33-detail-associations-empty.json
loans/loan-33/loan-33-detail-no-associations.json
loans/loan-33/loan-33-detail-associations-all-2.json
loans/loan-33/loan-33-detail-associations-transactions.json
loans/loan-33/loan-33-detail-associations-all-3.json
loans/loan-33/loan-33-detail-associations-collection-1.json
loans/loan-33/loan-33-detail-associations-collection-2.json
loans/loan-33/loan-33-detail-associations-all-4.json
loans/loan-33/loan-33-detail-associations-collection-3.json
loans/loan-33/loan-33-delinquency-actions-no-associations.json
loans/loan-33/loan-33-detail-associations-collection-4.json
loans/loan-33/loan-33-detail-associations-collection-5.json
loans/loan-33/loan-33-detail-associations-collection-6.json
```

### 35 — C3016 — `PASSED` — loan 34 — Verify that for pause period calculations business date is being used instead of COB date

Feature line 1113; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 19.

```
loans/loan-34/loan-34-detail-associations-all-1.json
loans/loan-34/loan-34-detail-associations-empty.json
loans/loan-34/loan-34-detail-no-associations.json
loans/loan-34/loan-34-detail-associations-all-2.json
loans/loan-34/loan-34-detail-associations-transactions-1.json
loans/loan-34/loan-34-detail-associations-all-3.json
loans/loan-34/loan-34-detail-associations-transactions-2.json
loans/loan-34/loan-34-detail-associations-all-4.json
loans/loan-34/loan-34-detail-associations-all-5.json
loans/loan-34/loan-34-detail-associations-collection-1.json
loans/loan-34/loan-34-detail-associations-collection-2.json
loans/loan-34/loan-34-detail-associations-collection-3.json
loans/loan-34/loan-34-detail-associations-collection-4.json
loans/loan-34/loan-34-detail-associations-collection-5.json
loans/loan-34/loan-34-detail-associations-collection-6.json
loans/loan-34/loan-34-detail-associations-collection-7.json
loans/loan-34/loan-34-detail-associations-collection-8.json
loans/loan-34/loan-34-detail-associations-collection-9.json
loans/loan-34/loan-34-delinquency-actions-no-associations.json
```

### 36 — C3018 — `PASSED` — loan 35 — Verify that if Global configuration: next-payment-due-date is set to: earliest-unpaid-date then in Loan details delinquent.nextPaymentDueDate will be the first unpaid installment date

Feature line 1168; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 8.

```
loans/loan-35/loan-35-detail-associations-all-1.json
loans/loan-35/loan-35-detail-associations-empty.json
loans/loan-35/loan-35-detail-no-associations.json
loans/loan-35/loan-35-detail-associations-all-2.json
loans/loan-35/loan-35-detail-associations-transactions.json
loans/loan-35/loan-35-detail-associations-all-3.json
loans/loan-35/loan-35-detail-associations-collection-1.json
loans/loan-35/loan-35-detail-associations-collection-2.json
```

### 37 — C3019 — `PASSED` — loan 36 — Verify that if Global configuration: next-payment-due-date is set to: next-unpaid-due-date then in Loan details delinquent.nextPaymentDueDate will be the next unpaid installment date regardless of the status of previous installments

Feature line 1184; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 8.

```
loans/loan-36/loan-36-detail-associations-all-1.json
loans/loan-36/loan-36-detail-associations-empty.json
loans/loan-36/loan-36-detail-no-associations.json
loans/loan-36/loan-36-detail-associations-all-2.json
loans/loan-36/loan-36-detail-associations-transactions.json
loans/loan-36/loan-36-detail-associations-all-3.json
loans/loan-36/loan-36-detail-associations-collection-1.json
loans/loan-36/loan-36-detail-associations-collection-2.json
```

### 38 — C3032 — `PASSED` — loan 37 — Verify that delinquencyRange field in LoanAccountDelinquencyRangeDataV1 is not null in case of delinquent Loan

Feature line 1200; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 7.

```
loans/loan-37/loan-37-detail-associations-all-1.json
loans/loan-37/loan-37-detail-associations-empty.json
loans/loan-37/loan-37-detail-no-associations.json
loans/loan-37/loan-37-detail-associations-all-2.json
loans/loan-37/loan-37-detail-associations-transactions.json
loans/loan-37/loan-37-detail-associations-all-3.json
loans/loan-37/loan-37-detail-associations-collection.json
```

### 39 — C3035 — `PASSED` — loan 38 — Verify that delinquency is NOT applied after loan submitted and approved

Feature line 1216; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL_INSTALLMENT_LEVEL_DELINQUENCY`; principal 100000 minor units; read-backs: 4.

```
loans/loan-38/loan-38-detail-associations-all.json
loans/loan-38/loan-38-detail-associations-collection-1.json
loans/loan-38/loan-38-detail-associations-empty.json
loans/loan-38/loan-38-detail-associations-collection-2.json
```

### 40 — C3047 — `PASSED` — loan 39 — Verify that delinquent.lastRepaymentAmount is calculated correctly in case of auto downpayment

Feature line 1231; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 7.

```
loans/loan-39/loan-39-detail-associations-all-1.json
loans/loan-39/loan-39-detail-associations-empty.json
loans/loan-39/loan-39-detail-no-associations.json
loans/loan-39/loan-39-detail-associations-all-2.json
loans/loan-39/loan-39-detail-associations-transactions.json
loans/loan-39/loan-39-detail-associations-all-3.json
loans/loan-39/loan-39-detail-associations-collection.json
```

### 41 — C3066 — `PASSED` — loan 40 — Verify that on Loans in SUBMITTED_AND_PENDING_APPROVAL or APPROVED status delinquency is not applied

Feature line 1243; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 4.

```
loans/loan-40/loan-40-detail-associations-all.json
loans/loan-40/loan-40-detail-associations-collection-1.json
loans/loan-40/loan-40-detail-associations-empty.json
loans/loan-40/loan-40-detail-associations-collection-2.json
```

### 42 — C3135 — `PASSED` — loan 41 — Verify that the delinquency is not applied on Loan with Rejected status

Feature line 1257; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 7.

```
loans/loan-41/loan-41-detail-associations-all.json
loans/loan-41/loan-41-detail-associations-collection-1.json
loans/loan-41/loan-41-detail-associations-empty-1.json
loans/loan-41/loan-41-detail-associations-collection-2.json
loans/loan-41/loan-41-detail-associations-empty-2.json
loans/loan-41/loan-41-detail-no-associations.json
loans/loan-41/loan-41-detail-associations-collection-3.json
```

### 43 — C3136 — `PASSED` — loan 42 — Verify that the delinquency is not applied on Loan with Withdrawn status

Feature line 1282; product `LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION`; principal 100000 minor units; read-backs: 7.

```
loans/loan-42/loan-42-detail-associations-all.json
loans/loan-42/loan-42-detail-associations-collection-1.json
loans/loan-42/loan-42-detail-associations-empty-1.json
loans/loan-42/loan-42-detail-associations-collection-2.json
loans/loan-42/loan-42-detail-associations-empty-2.json
loans/loan-42/loan-42-detail-no-associations.json
loans/loan-42/loan-42-detail-associations-collection-3.json
```

### 44 — C3137 — `PASSED` — loan 43 — Verify Installment level loan delinquency can be applied on loan account level in case of non-installment level delinquency loan product

Feature line 1307; product `LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL`; principal 100000 minor units; read-backs: 7.

```
loans/loan-43/loan-43-detail-associations-all-1.json
loans/loan-43/loan-43-detail-associations-empty.json
loans/loan-43/loan-43-detail-no-associations.json
loans/loan-43/loan-43-detail-associations-all-2.json
loans/loan-43/loan-43-detail-associations-transactions.json
loans/loan-43/loan-43-detail-associations-all-3.json
loans/loan-43/loan-43-detail-associations-collection.json
```

### 45 — C3930 — `PASSED` — loan 44 — Verify nextPaymentAmount value with repayment on first installment - progressive loan, no interest recalculation, zero interest rate - UC1

Feature line 1324; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 100000 minor units; read-backs: 24.

```
loans/loan-44/loan-44-detail-associations-all-1.json
loans/loan-44/loan-44-detail-associations-empty.json
loans/loan-44/loan-44-detail-no-associations.json
loans/loan-44/loan-44-detail-associations-all-2.json
loans/loan-44/loan-44-detail-associations-transactions-1.json
loans/loan-44/loan-44-detail-associations-all-3.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-1.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-2.json
loans/loan-44/loan-44-detail-associations-transactions-2.json
loans/loan-44/loan-44-detail-associations-collection-1.json
loans/loan-44/loan-44-detail-associations-transactions-3.json
loans/loan-44/loan-44-detail-associations-all-4.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-3.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-4.json
loans/loan-44/loan-44-detail-associations-transactions-4.json
loans/loan-44/loan-44-detail-associations-collection-2.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-5.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-6.json
loans/loan-44/loan-44-detail-associations-transactions-5.json
loans/loan-44/loan-44-detail-associations-collection-3.json
loans/loan-44/loan-44-transactions-template-no-associations-prepayLoan.json
loans/loan-44/loan-44-detail-associations-transactions-6.json
loans/loan-44/loan-44-detail-associations-all-5.json
loans/loan-44/loan-44-detail-associations-repaymentSchedule-7.json
```

### 46 — C3931 — `PASSED` — loan 45 — Verify nextPaymentAmount value with penalty on first installment - progressive loan, no interest recalculation, non-zero interest rate - UC2

Feature line 1394; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30`; principal 100000 minor units; read-backs: 22.

```
loans/loan-45/loan-45-detail-associations-all-1.json
loans/loan-45/loan-45-detail-associations-empty.json
loans/loan-45/loan-45-detail-no-associations.json
loans/loan-45/loan-45-detail-associations-all-2.json
loans/loan-45/loan-45-detail-associations-transactions-1.json
loans/loan-45/loan-45-detail-associations-all-3.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-1.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-2.json
loans/loan-45/loan-45-detail-associations-transactions-2.json
loans/loan-45/loan-45-detail-associations-collection-1.json
loans/loan-45/loan-45-charges-3-no-associations.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-3.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-4.json
loans/loan-45/loan-45-detail-associations-transactions-3.json
loans/loan-45/loan-45-detail-associations-collection-2.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-5.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-6.json
loans/loan-45/loan-45-detail-associations-collection-3.json
loans/loan-45/loan-45-transactions-template-no-associations-prepayLoan.json
loans/loan-45/loan-45-detail-associations-transactions-4.json
loans/loan-45/loan-45-detail-associations-all-4.json
loans/loan-45/loan-45-detail-associations-repaymentSchedule-7.json
```

### 47 — C3932 — `PASSED` — loan 46 — Verify nextPaymentAmount value with repayment at 2nd installment - progressive loan, no interest recalculation, the same as repayment period - UC3

Feature line 1460; product `LP2_INTEREST_FLAT_ADV_PMT_ALLOC_MULTIDISBURSE`; principal 100000 minor units; read-backs: 23.

```
loans/loan-46/loan-46-detail-associations-all-1.json
loans/loan-46/loan-46-detail-associations-empty.json
loans/loan-46/loan-46-detail-no-associations.json
loans/loan-46/loan-46-detail-associations-all-2.json
loans/loan-46/loan-46-detail-associations-transactions-1.json
loans/loan-46/loan-46-detail-associations-all-3.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-1.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-2.json
loans/loan-46/loan-46-detail-associations-transactions-2.json
loans/loan-46/loan-46-detail-associations-collection-1.json
loans/loan-46/loan-46-detail-associations-transactions-3.json
loans/loan-46/loan-46-detail-associations-all-4.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-3.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-4.json
loans/loan-46/loan-46-detail-associations-transactions-4.json
loans/loan-46/loan-46-detail-associations-collection-2.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-5.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-6.json
loans/loan-46/loan-46-detail-associations-collection-3.json
loans/loan-46/loan-46-transactions-template-no-associations-prepayLoan.json
loans/loan-46/loan-46-detail-associations-transactions-5.json
loans/loan-46/loan-46-detail-associations-all-5.json
loans/loan-46/loan-46-detail-associations-repaymentSchedule-7.json
```

### 48 — C3933 — `PASSED` — loan 47 — Verify nextPaymentAmount value - progressive loan, interest recalculation daily - UC4

Feature line 1524; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 100000 minor units; read-backs: 21.

```
loans/loan-47/loan-47-detail-associations-all-1.json
loans/loan-47/loan-47-detail-associations-empty.json
loans/loan-47/loan-47-detail-no-associations.json
loans/loan-47/loan-47-detail-associations-all-2.json
loans/loan-47/loan-47-detail-associations-transactions-1.json
loans/loan-47/loan-47-detail-associations-all-3.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-1.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-2.json
loans/loan-47/loan-47-detail-associations-transactions-2.json
loans/loan-47/loan-47-detail-associations-collection-1.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-3.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-4.json
loans/loan-47/loan-47-detail-associations-transactions-3.json
loans/loan-47/loan-47-detail-associations-collection-2.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-5.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-6.json
loans/loan-47/loan-47-detail-associations-collection-3.json
loans/loan-47/loan-47-transactions-template-no-associations-prepayLoan.json
loans/loan-47/loan-47-detail-associations-transactions-4.json
loans/loan-47/loan-47-detail-associations-all-4.json
loans/loan-47/loan-47-detail-associations-repaymentSchedule-7.json
```

### 49 — C3934 — `PASSED` — loan 48 — Verify nextPaymentAmount value with chargeback - progressive loan, interest recalculation daily - UC5

Feature line 1586; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 100000 minor units; read-backs: 27.

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
loans/loan-48/loan-48-detail-associations-collection-1.json
loans/loan-48/loan-48-detail-associations-transactions-3.json
loans/loan-48/loan-48-detail-associations-all-4.json
loans/loan-48/loan-48-detail-associations-transactions-4.json
loans/loan-48/loan-48-detail-associations-all-5.json
loans/loan-48/loan-48-transactions-151-no-associations.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-3.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-4.json
loans/loan-48/loan-48-detail-associations-transactions-5.json
loans/loan-48/loan-48-detail-associations-collection-2.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-5.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-6.json
loans/loan-48/loan-48-detail-associations-collection-3.json
loans/loan-48/loan-48-detail-associations-collection-4.json
loans/loan-48/loan-48-transactions-template-no-associations-prepayLoan.json
loans/loan-48/loan-48-detail-associations-transactions-6.json
loans/loan-48/loan-48-detail-associations-all-6.json
loans/loan-48/loan-48-detail-associations-repaymentSchedule-7.json
```

### 50 — C3935 — `PASSED` — loan 49 — Verify nextPaymentAmount value with full repayment on first installment - progressive loan, interest recalculation daily - UC6

Feature line 1658; product `LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE`; principal 100000 minor units; read-backs: 26.

```
loans/loan-49/loan-49-detail-associations-all-1.json
loans/loan-49/loan-49-detail-associations-empty.json
loans/loan-49/loan-49-detail-no-associations.json
loans/loan-49/loan-49-detail-associations-all-2.json
loans/loan-49/loan-49-detail-associations-transactions-1.json
loans/loan-49/loan-49-detail-associations-all-3.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-1.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-2.json
loans/loan-49/loan-49-detail-associations-transactions-2.json
loans/loan-49/loan-49-detail-associations-collection-1.json
loans/loan-49/loan-49-detail-associations-transactions-3.json
loans/loan-49/loan-49-detail-associations-all-4.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-3.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-4.json
loans/loan-49/loan-49-detail-associations-transactions-4.json
loans/loan-49/loan-49-detail-associations-collection-2.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-5.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-6.json
loans/loan-49/loan-49-detail-associations-collection-3.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-7.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-8.json
loans/loan-49/loan-49-detail-associations-collection-4.json
loans/loan-49/loan-49-transactions-template-no-associations-prepayLoan.json
loans/loan-49/loan-49-detail-associations-transactions-5.json
loans/loan-49/loan-49-detail-associations-all-5.json
loans/loan-49/loan-49-detail-associations-repaymentSchedule-9.json
```

## Currency

Every committed body carrying a currency object resolves to `code = "MNT"` (1941 occurrences); the literal token `EUR` appears in 0 committed bodies.

## Isolation

`preflight.sh` wrote the standing baseline before the throwaway started; `down.sh`
compared against that exact file and reported every counter equal to baseline
(`teardown-isolation.txt`). All `tierd-*` containers, the `tierd-oracle` network and its
volume are gone; standing tenants `gerege` and `default` were never written.
