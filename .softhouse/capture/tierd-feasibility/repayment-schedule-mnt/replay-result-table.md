# Tier D replay — `LoanRepaymentSchedule.feature` in MNT (capture only)

**Task:** OH-TIERD5-BP · worktree `/Users/buv/oh-gerege-tierd5` · branch `feat/OHTIERD5bp`
**Disposable copy:** `/Users/buv/fineract-tierd` (MNT re-seed, uncommitted local edits; never promoted)
**Standing `/Users/buv/fineract`:** untouched.

## Run provenance

| item | value |
| --- | --- |
| feature | `fineract-e2e-tests-runner/src/test/resources/features/LoanRepaymentSchedule.feature` (1557 lines) |
| scenarios attempted | 12 of 12 — the **whole file** was replayed (no subset needed) |
| tenant | `tierd` (throwaway only) |
| throwaway image | `fineract:latest` = `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` |
| same image as standing oracle | yes — `gerege-oracle-app` and `fineract-fineract-1` both run that exact image id (preflight) |
| timezone / rounding | `Asia/Ulaanbaatar` / rounding mode 4 |
| currency | MNT (ISO 4217 496, 2 minor digits; arithmetic identical to EUR) |
| Feign capture | `feign-repsched-mnt.log` — 159,152,907 bytes, 43,468 lines |
| replay window (UTC) | 2026-09-11T10:34:02Z → 2026-09-11T10:35:03Z |
| cucumber task | 1m 01.65s (whole build 1m 15s); 24 actionable tasks, 1 executed, 23 up-to-date |
| driver | `run-repsched-mnt.sh` (copy committed beside this file) |

## Result table

Literal cucumber summary: **`12 scenarios (11 passed, 1 failed)`**, **`408 steps (359 passed, 48 skipped, 1 failed)`**.
Per-scenario result (`scenario-results.json`):

| # | scenario | feature line | result | loan (resource id) | product (minor-unit principal) |
| --- | --- | --- | --- | --- | --- |
| 1 | UC1 | 5 | PASSED | loan 1 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 2 | UC2 | 76 | PASSED | loan 2 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 3 | UC3 | 147 | PASSED | loan 3 | `LP2_ADV_PYMNT_INTEREST_DECL_BAL_SARP_EMI_360_30_NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` (200000) |
| 4 | UC4 | 218 | PASSED | loan 4 | `..._INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 5 | UC5 | 272 | PASSED | loan 5 | `..._NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 6 | UC6 | 326 | PASSED | loan 6 | `..._NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` (200000) |
| 7 | UC7 | 380 | PASSED | loan 7 | `..._INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 8 | UC8 | 528 | PASSED | loan 8 | `..._NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 9 | UC9 | 676 | PASSED | loan 9 | `..._NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` (200000) |
| 10 | **UC10** | 824 | **FAILED** | loan **10** | `..._INT_RECALC_DAILY_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 11 | UC11 | 1070 | PASSED | loan 11 | `..._NO_INT_RECALC_MULTIDISB_PARTIAL_PERIOD` (200000) |
| 12 | UC12 | 1315 | PASSED | loan 12 | `..._NO_INT_RECALC_MULTIDISB_NO_PARTIAL_PERIOD` (200000) |

Loan ↔ scenario mapping is **not** positional by assumption: it is proven (a) by each loan's
read-back `loanProductName` matching the scenario's product (products rotate in the exact
UC1/4/7/10 → P139, UC2/5/8/11 → P135, UC3/6/9/12 → P137 pattern), and (b) directly, because the
only failure names **resource 10** inside UC10. See `OWNER.md`.

## The one failure (a finding)

**Scenario UC10** — "complex transactions, interest recalculation enabled, partial period interest
calculation enabled" — feature line 824, fails on its 13th step:

> `Then Loan Repayment schedule has 3 periods, with the following data for periods:`
> (feature line **841**) — step def `LoanStepDef.loanRepaymentSchedulePeriodsCheck`, `LoanStepDef.java:2312`.

```
Wrong value in Repayment schedule of resource 10 tab line 4.
Actual values in line (with the same due date) are:
  [2, 28, 01 March 2025, null, 434.77, 429.73, 11.29, 0.0, 0.0, 441.02, 0.0, 0.0, 0.0, 441.02]
But expected values in line:
  [2, 28, 01 March 2025, null, 434.76, 429.74, 11.28, 0.0, 0.0, 441.02, 0.0, 0.0, 0.0, 441.02]
```

Period 2 of the schedule, money in **integer minor units** (MNT, 2 digits):

| cell | expected | actual (oracle) | delta |
| --- | --- | --- | --- |
| Balance of loan | 43476 | 43477 | +1 |
| Principal due | 42974 | 42973 | −1 |
| Interest | 1128 | 1129 | +1 |
| Due | 44102 | 44102 | 0 |

The remaining cells (Nr, Days, Date, Paid date, Fees, Penalties, Paid, In advance, Late,
Outstanding) are identical. Because MNT and EUR share ISO minor digits (2), this 1-minor-unit
principal/interest boundary split is **not** attributable to the currency re-seed; it is the
oracle's rounding of the period-2 split on this complex-transaction path diverging from the
checked-in `.feature` expectation. It is recorded here as the one MNT replay failure; UC10 is
excluded from the committed read-backs (its scenario aborts at feature line 841, so its
subsequent read-backs would be partial).

Full step-level log: `replay-repsched-mnt.log` (ANSI). Machine-readable: `scenario-results.json`.
