# T76 — prediction registered BEFORE any capture (P-9)

Written and committed **before** a single request was sent to the reference oracle (Fineract).
Anything below that the observations refute is a finding, and I will report it as a refutation of
*this* document rather than quietly restating the observed value.

Author: T76. Branch `softhouse/T76-pathb-gerege-recapture`.
Written at UTC **2026-08-20T09:09:06Z** (`date -u`), committed immediately, before the first
`curl` to the oracle.

## What I have already read (repo only, no oracle contact) and am NOT predicting

* The four T22 P0 items this task names as open are, on the evidence in git, **already closed**:
  P0-5 by T30 (commit `1b65b1c`), P0-3 / P0-4 / P0-6 by T36 (commits `c3bbf26`, `fab040a`,
  `78c5bda`, `60c08ad`, `6c13f2a`, `5f53f79`). So T76 is a **re-verification and a promotion
  decision**, not a first close. This is a driver-claim check (P-16) and it is stated here, before
  the run, so it cannot be back-fitted.
* `contract.go` is at **REVISION 11** (`:50`) and `PIN.json`/`capabilities.json` at
  `dec1_revision` **12** — the task brief says REVISION 10.

## Predictions about the oracle (falsifiable, one line each)

| # | Prediction | How it is falsified |
|---|---|---|
| P-A | `t36/preconditions.sh gerege` exits **0** with **0 FAIL** lines (15 assertions) | any FAIL line |
| P-B | the same script against tenant `default` exits **1** with **5** breaches (timezone, rounding-mode row, mode-in-force, `schema_connection_parameters`, canary) | any other count |
| P-C | tenant `gerege` reads: `timezone_id = Asia/Ulaanbaatar`, `c_configuration.rounding-mode = 4` → name `HALF_UP`, `MoneyHelper.PRECISION = 19` (javap over deployed bytecode), `schema_connection_parameters = ''`, `schema_server_port = 5432`, PostgreSQL `18.3` | any field differing |
| P-D | the behavioural half-cent canary returns period-1 `interestOriginalDue` = **20925.05** (HALF_UP). `20925.04` would mean HALF_EVEN is in force | any other value |
| P-E | **the four re-captures on `gerege` at (19, HALF_UP) are BYTE-IDENTICAL to the committed HALF_EVEN originals taken on `default`** — sha256 `713a3560…`, `9de8757d…`, `892dd6f5…`, `c80f62b0…`. Predicted difference: **0 minor units in every cell of all four.** Grounds: T22 §7(b)3 and T36 both observed identity; the mode only bites at an exact half-minor-unit tie and none of these four inputs produces one | any digest differing; then the delta in minor units is the finding and the original is retracted, not patched |
| P-F | the products behind the captures still read `installment_amount_in_multiples_of` NULL/100.000000 on ids 1/2 and `days_in_year_custom_strategy` `FULL_LEAP_YEAR`/`FEB_29_PERIOD_ONLY` on ids 3/4 in `fineract_gerege` | any drift |

## Prediction about PROMOTION (the decision this task actually turns on)

**I predict I will promote NOTHING, and that this is the correct outcome**, on these grounds,
registered before the captures so the captures cannot be used to rationalise a promotion:

* **B-02** (`installmentAmountInMultiplesOf = 100`) — `capabilities.json` marks
  `installment.rounding.multiple` `exercised` on `path_b_server`, so the *seam* test passes; but
  the capability's `in_graded_domain` is **false**, and `contract.go:114-118` says
  `InstallmentRoundingMultipleMinor` "stays in this contract and is **refused for Run 1**
  (DEC-1 section 4.7)". The graded-domain list at `contract.go:1130` requires
  `InstallmentRoundingMultipleMinor == 0`. A parity vector carrying `100` would assert numbers
  where the ratified contract requires `ErrNoDiscriminatingVector`. Promoting it needs a DEC-1
  amendment → **a gate, not a worker decision**.
* **B-03 / B-04** (`daysInYearCustomStrategy`) — same shape, doubled: `daysinyear.custom.strategy`
  is `in_graded_domain: false`, and both captures are ACT/ACT + DAILY, so they also need
  `daycount.actual.actual` in the graded domain, which `REFUSE-01` currently asserts is refused.
  Two ungraded capabilities, and the contract carries **no field at all** for a
  days-in-year custom strategy (`contract.go:133-134` names `DaysInYearCustomStrategyType` among
  the Java concepts that must never cross the boundary).
* **B-01** (baseline) — the only one whose capabilities are all in the graded domain… except that
  its product is ACT/ACT, so it is not expressible in the ratified request shape without claiming
  a day-count the oracle was not configured with. And its money is already in the store: T22 §6
  showed B-01 equals the promoted Path A vector `P-MNT-1M2` in all 12 periods and all three totals.
  A parity vector must kill a **named** wrong implementation (`graded_against` non-empty); I do not
  expect to find one B-01 kills that `P-MNT-1M2` does not.

## Prediction about the harness

* P-G: `.softhouse/conformance.sh` exits **0** with 36 parity PASS / 0 FAIL / 0 inadmissible, i.e.
  unchanged by this task, because I expect to add no vector file.

## Prediction about B-03/B-04 re-derivation (T22 P1-14)

* P-H: T22 says B-03/B-04 were never re-derived from source; I expect to find that **T30 did
  re-derive them** and **T36 re-checked it** (`t36/t36_rederive_check.py`,
  `t36/out/rederive-check.txt`), i.e. P1-14 is closed too and the task brief is stale on this point
  as well. I will verify by executing the checker, not by reading its committed transcript.
