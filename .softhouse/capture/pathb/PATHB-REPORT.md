# Path B — first captures from the RUNNING reference oracle (server + PostgreSQL)

**Fire:** local `20260818-170002` (Buyan's Mac), 2026-08-18
**Executed by:** the orchestrator (vector capture touches the oracle, so it is orchestrator-only)
**Status:** RAW OBSERVED, **INDEPENDENTLY AUDITED by T22 (2026-08-18) — ACCEPTED WITH REQUIRED CHANGES**;
the audit's oracle-independent corrections are applied in this document (see the CORRECTED / CLARIFIED banners
below), and **three P0 admissibility items remain open** (T22 §10 P0-3 attestation sidecar, P0-4 fail-the-run
preconditions, P0-6 re-point at a production-settings tenant — each needs a live oracle). The fourth, **P0-5**
(the `REPRODUCE.md` capture-loop defect), **is closed** — fixed by T30, no oracle required. The T22 audit was
itself re-checked by T27
(2026-08-18) and its corrections machine-verified against the committed artifacts.
**No vector promoted to the store; no gate answered.**

## Why Path B exists

Every capture before this fire (passes 1–3) used **Path A**: the
`fineract-progressive-loan-embeddable-schedule-generator` seam, called in-process, with no server and no
database. Path A is cheap and reproducible, and it produced the whole parity-candidate corpus.

But pass 2 established that Path A **silently drops two contract inputs**, and pass 3 inherited the defect:

- `installmentAmountInMultiplesOf` — never read by `assembleFrom`.
- `daysInYearCustomStrategy` — read, but never copied by the `Builder` copy-constructor (`:304-351`).

For both, the Path A corpus has **zero discriminating power**: a Go port could honour or ignore them and
score identically. That is why Path B was recorded as a *prerequisite* for the parity corpus rather than an
optimisation. This fire built it and used it.

## Provenance

| Fact | Value |
|---|---|
| Path | **B** — running Fineract server, full stack, over PostgreSQL |
| Image digest | `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a` |
| Pinned Fineract commit | `426a23544` |
| PostgreSQL | PostgreSQL 18.3 (Debian 18.3-1.pgdg13+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit |
| Driver asserted | `org.postgresql.Driver`, `jdbc:postgresql://db:5432/fineract_tenants` |
| Endpoint | `POST /loans?command=calculateLoanSchedule` |
| Tenant | `default` (**timezone `Asia/Kolkata`** — see Caveats) |
| Currency | MNT, decimalPlaces 2, inMultiplesOf 0 |
| Product shape | PROGRESSIVE / HORIZONTAL, `advanced-payment-allocation-strategy`, declining balance, equal installments |

The image digest is **identical to the one all three Path A passes ran against**, so a Path A ↔ Path B
comparison is a comparison of two seams into the same pinned build, not of two builds.

## Result 1 — Path B corroborates Path A on the baseline

`B-01` reproduces pass-3 `P-MNT-1M2` (MNT 1,200,000 / 12 × 21.6 %) **to the minor unit**, through a
completely different seam:

| | total interest | total repayment | EMI |
|---|---|---|---|
| Path A `P-MNT-1M2` (in-process seam) | `144,988.47` | `1,344,988.47` | `112,082.37` |
| Path B `B-01` (running server + PostgreSQL) | `144,988.47` | `1,344,988.47` | `112,082.37` |

Every period matches (period 1 principal `90,482.37` / interest `21,600.00`; period 2 `92,111.05` /
`19,971.32`; …). This is the strongest calibration evidence the program has: the corpus is not an artefact
of the embeddable seam.

**Honest caveat on the dates.** Path A disbursed 2024-01-01 (366-day term, `DAYS_30`/`DAYS_360`); Path B
disbursed 2026-01-01 (365 days, product day-count `Actual`/`Actual`, `SAME_AS_REPAYMENT_PERIOD`). The
outputs are identical because **both reduce to an exact 1/12 period fraction**, so the calendar never
enters. This corroborates the baseline arithmetic. It does **NOT** show that day-count settings are ignored
by a progressive schedule — that comparison has no discriminating power and no such claim is made here.

## Result 2 — `installmentAmountInMultiplesOf` IS honoured on the server path

`B-01` vs `B-02`, identical products except this one field, same loan, same dates:

| | EMI | total interest | total repayment |
|---|---|---|---|
| `B-01` field `null` | `112,082.37` | `144,988.47` | `1,344,988.47` |
| `B-02` field `100` | `112,100.00` | `144,966.22` | `1,344,966.22` |

**12 of 12 periods differ.** The EMI is rounded to a multiple of 100 and held constant for periods
1–11, and the **final installment absorbs the residual** — period 12 is principal `109,888.23` + interest
`1,977.99` = `111,866.22`, deliberately *not* the rounded EMI.

> **NORMATIVE RULE — final-installment residual absorption** (added per T22 audit P1-12; re-derived from the
> pinned source by T30 at `ProgressiveEMICalculator.java:1195-1205`, and re-verified independently by T27).
> The worked example above is an *instance*; the rule itself is:
>
> ```
> lastUnpaidPeriod.emi  ←  lastUnpaidPeriod.emi + diff
> diff = totalDisbursed + totalCapitalizedIncome + totalCreditedPrincipal + Σ dueInterest − Σ EMI
> ```
>
> `calculateLastUnpaidRepaymentPeriodEMI` accumulates `Σ dueInterest` (`:1190-1191`), `Σ EMI`
> (`:1192-1194`, over `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest`), `totalDisbursed`
> (`:1195-1197`) and `totalCapitalizedIncome` (`:1198-1200`); forms `diff` at **`:1202-1203`**; and applies it
> at **`:1205`** as `repaymentPeriod.getEmi().add(diff, mc)`. Every accumulation and the addition are under the
> tenant `MathContext`.
>
> Three things a port must get right, all of which the "the last period is whatever is left" reading loses:
>
> 1. **The delta is SIGNED.** It is positive on `B-01` (`112,082.37 → 112,082.40`), negative on `B-02`
>    (`112,100.00 → 111,866.22`), `+0.05` on `B-03` (`112,054.93 → 112,054.98`) and `−0.05` on `B-04`
>    (`112,084.29 → 112,084.24`) — all four values re-derived from source by T30 and matching the committed
>    observations digit-for-digit.
> 2. **It lands on the last UNPAID period** (`:1176-1181`), not unconditionally on the last period.
> 3. **It adjusts the EMI, not the principal.** The period's interest/principal split is then re-taken from the
>    adjusted EMI by the ordinary rules (`RepaymentPeriod.java:272-285`, `:345-349`), so the residual can move
>    either component.
>
> The adjusted EMI then feeds `EmiAdjustment.shouldBeAdjusted` (see the re-adjust-loop note under Caveats); on
> all four Path B captures the residual is far too small to fire it.

> **CORRECTED by the T22 independent audit (2026-08-18), P0 item 1.** An earlier version of this paragraph
> said the EMI is *"raised to the next multiple of 100"*. That rule is **FALSE**. The oracle rounds the EMI
> to the **NEAREST** multiple of `installmentAmountInMultiplesOf` **under the tenant rounding mode**
> (`ProgressiveEMICalculator.java:1770-1776` → `Money.java:163-171`), with a **zero-guard** that returns the
> unrounded EMI if rounding would zero a positive one. `B-02` cannot distinguish the two rules
> (`112,082.37` rounds up either way), so the audit put a round-**down** case to the oracle: at principal
> **MNT 1,190,000** with `installmentAmountInMultiplesOf = 100` at `(19, HALF_UP)`.
>
> **Observed vs derived — kept apart deliberately** (corrected per T27 RC-6; the earlier wording ran the two
> together):
>
> | value | status | source |
> |---|---|---|
> | applied EMI, periods 1–11 = **`111,100.00`** | **OBSERVED** | committed capture `.softhouse/capture/pathb/t22-audit/out-rounddown/rounddown-gerege-raw.json` |
> | unrounded EMI = `111,148.35` | **DERIVED, NOT OBSERVED** | re-derived from source by T22's annuity model and re-derived independently by T27 (model calibrated against the committed `B-01` EMI first). The oracle never emits the unrounded EMI, so no capture can carry it |
> | a round-UP rule would give `111,200` | arithmetic on the derived value | — |
> | round-to-NEAREST under HALF_UP gives `111,100` | arithmetic on the derived value | — |
>
> The observation `111,100.00 < 111,148.35` is what refutes round-up. The conclusion is robust to the rounding
> mode (`111,148.35` rounds to `111,100` under HALF_UP *and* HALF_EVEN), but the *attestation* that this probe
> ran at `(19, HALF_UP)` rests on the filename and T22's prose — there is no attestation sidecar yet, which is
> T22 P0-3. Anything DEC-1 says about this field must be written from the corrected round-to-nearest rule, not
> the round-up sentence.

So the field is **not dead**. It is dropped by the Path A seam and honoured by the server. The residual
absorption rule is a normative semantic the contract must state.

**Server-path citations for Results 2 and 3** (added per T22 audit P1-10; this report previously cited only
the Path A *defect*, and T19 item 5 exists because that omission produced cumulative-generator citations last
time — **every citation below is in the PROGRESSIVE generator**):

| what | pinned source |
|---|---|
| the field the Path A seam drops is passed on the server path | `ProgressiveLoanScheduleGenerator.java:108-110` |
| the Path A path that drops it | `ProgressiveLoanScheduleGenerator.java:81-82` (`LoanApplicationTerms.assembleFrom`) |
| `installmentAmountInMultiplesOf` applied / zero-guard | `ProgressiveEMICalculator.java:1761-1776` |
| round to the **nearest** multiple under the tenant mode | `Money.java:159-171` |
| days-in-year + `daysInYearCustomStrategy` | `ProgressiveEMICalculator.java:1330-1353`, `DaysInYearType.java:81-86` |
| final-installment residual absorption | `ProgressiveEMICalculator.java:1160-1219` (`diff` `:1202-1203`, applied `:1205`) |
| EMI re-adjust loop | `ProgressiveEMICalculator.java:1258-1308` |

## Result 3 — `daysInYearCustomStrategy` IS honoured on the server path

`B-03` vs `B-04`, identical products except this field. To make the field capable of biting at all this
configuration uses `interestCalculationPeriodType = DAILY`, `daysInYearType = Actual`,
`daysInMonthType = Actual`, and a term spanning **29 February 2024**:

| | total interest | total repayment |
|---|---|---|
| `FULL_LEAP_YEAR` | `144,659.21` | `1,344,659.21` |
| `FEB_29_PERIOD_ONLY` | `145,011.43` | `1,345,011.43` |

**12 of 12 periods differ**; delta `352.22` MNT on a 1.2M loan. Both enum values are offered by the
server's own `/loanproducts/template` and both persist on the product.

**Honest caveat.** This configuration differs from Result 2's on more than one axis, because the field
cannot bite under `SAME_AS_REPAYMENT_PERIOD`. The isolated effect of `daysInYearCustomStrategy` under a
non-daily interest calculation period was **not tested** and is not claimed.

> **CLARIFIED per T22 audit P1-7:** the two enum values are **not symmetric**. The audit showed
> `FULL_LEAP_YEAR` is **behaviourally identical to the field being unset** — a probe with
> `daysInYearCustomStrategy` removed entirely returned a capture byte-identical to `B-03`, and source agrees
> (`DaysInYearType.java:81-86` has no `FULL_LEAP_YEAR` branch;
> `ProgressiveEMICalculator.java:1346-1352` special-cases only `FEB_29_PERIOD_ONLY`). So the discriminating
> value is **`FEB_29_PERIOD_ONLY` alone**, and **`B-04` is the only vector with any discriminating power over
> this field**: a port that ignores `daysInYearCustomStrategy` entirely still passes `B-03` and fails `B-04`.
> The field can only bite under `interestCalculationPeriodType = DAILY` **and** `daysInYearType = ACTUAL`
> (`ProgressiveEMICalculator.java:1510-1516` short-circuits everything else).

### The precondition, with its evidence (T22 P1-8, second clause — settled without an oracle)

`daysInYearCustomStrategy` is **inert** under `SAME_AS_REPAYMENT_PERIOD` + monthly/weekly repayment. This is a
theorem about the code, not a property of these inputs: `calculateRateFactorPerPeriodForInterest` reads the
strategy at `:1364-1366`, but the `isSameAsRepaymentPeriod()` + monthly branch at
`ProgressiveEMICalculator.java:1377-1383` (and `:1510-1516` in the non-interest variant) **returns before any
use of it**, with days-in-year hard-set to `12`. The `ACTUAL` half of the precondition is enforced by the
server at product creation — `LoanProduct.java:462-472`.

The committed probes agree, by SHA-256 over files already in the repo (relations re-verified by T27; **no
oracle call was made to settle them**):

| relation | SHA-256 | what it settles |
|---|---|---|
| `t22-audit/out-probe/p05-raw.json` (SARP, `FULL_LEAP_YEAR`) ≡ `p06-raw.json` (SARP, `FEB_29_PERIOD_ONLY`) | `ff92fc5dfb8e…` both | strategy is inert under `SAME_AS_REPAYMENT_PERIOD` |
| `p07-raw.json` (DAILY, ACT/ACT, strategy **absent**) ≡ `out/B-03-diycs-fullleapyear-raw.json` | `892dd6f5…` both | `FULL_LEAP_YEAR` ≡ field-unset |

### Day-count settings on a progressive schedule (T22 P1-9 — settled without an oracle)

The second of the orchestrator's two explicit non-claims. `daysInYearType` / `daysInMonthType` **move** a
progressive schedule under `DAILY`, and are **inert** under `SAME_AS_REPAYMENT_PERIOD` — same
`:1377-1383` / `:1510-1516` short-circuit:

| relation | SHA-256 | reading |
|---|---|---|
| `p07-raw.json` (DAILY, `ACTUAL`/`ACTUAL`) **≠** `p08-raw.json` (DAILY, `360`/`30`) | `892dd6f5…` vs `ff92fc5d…` | day count is **live** under DAILY |
| `p09-raw.json` (SARP, `360`/`30`) **≡** `out/B-01-baseline-raw.json` (SARP, `ACTUAL`/`ACTUAL`) | `713a3560…` both | day count is **inert** under SARP |

### `B-03` and `B-04` re-derived from source (T22 P1-14, first clause — **closed**, no oracle needed)

T22 recorded that `B-03`/`B-04` were reproduced and invariant-clean but **not** independently re-derived,
because they run the DAILY cross-year *partial-period* arm rather than the monthly short-circuit T22's model
covered — "the largest remaining hole in the Path B evidence". **T30 has now rebuilt both from the pinned
source**, and both reproduce **digit-for-digit — all 12 periods, both totals, at `(19, HALF_EVEN)` and at
`(19, HALF_UP)`.** Script and full transcript: `.softhouse/reviews/t30-probe/`
(`t30_rederive_b03_b04.py`, `t30-rederive-output.txt`). **That re-derivation was NOT run against a live
oracle** — it models the oracle from source and is compared against captures already committed here.

Two normative facts the re-derivation makes explicit, neither of which was in the record before:

1. **`FEB_29_PERIOD_ONLY` does two things, not one.** Besides capping days-in-year at 365 for a period that
   does not contain 29 February (`getNumberOfDays` `:1346-1353` → `numberOfDaysFeb29PeriodOnly` `:1342-1344`,
   with the leap day tested on the half-open range `(fromDate, dueDate]` at `:1330-1340`), it **suppresses the
   cross-year partial-period calculation** for such a period: `partialPeriodCalculationNeeded`
   (`:1372-1374` and `:1505-1507`) is `daysInYearType == ACTUAL && yearsDifference > 0 && (strategy !=
   FEB_29_PERIOD_ONLY || periodContainsFeb29)`. In this corpus that is exactly period 12
   (2024-12-01 → 2025-01-01): `B-03` takes the partial arm, `B-04` does **not**.
2. **The partial arm is a sum of per-year day fractions, not a single day-count division.**
   `calculatePeriodFractions` (`:1550-1568`) accumulates `Σ days(segment) / Year.length(year)` under the
   tenant `MathContext`, splitting at 31 December (`:1578-1584`, because
   `isInterestRecognitionOnDisbursementDate` is false here). For `B-03` period 12 that is
   `30/366 + 1/365`, giving rate factor `0.0182966988…` where the non-partial arm would give
   `31/366 → 0.0182950819…`. The result is then `rate × fraction`, `setScale(19, mode)`
   (`rateFactorByRepaymentPartialPeriod`, `:1965-1978`) — note its `interestFractionPerPeriod` multiply is
   **exact**, without the `MathContext`.

   A port that implements only fact 1 returns `B-03`'s period-12 numbers for `B-04`, or vice versa, and fails.

The re-derivation also confirms, from source, that the four captures are **mode-insensitive by construction**
here (identical output at HALF_UP and HALF_EVEN), which independently corroborates the fresh-tenant
re-observation cited under Caveats instead of resting on it alone.

## What this changes

1. Both dropped inputs are now **vectored**. The standing disposition "expose it, but refuse with
   *unsupported: no discriminating vector*" is obsolete for both — refusing an input the oracle
   demonstrably honours would make the Go module diverge from the oracle by construction. T4 (DEC-1 v2) was
   notified mid-flight.
2. Standing policy **P-1** (launch WITHOUT installment rounding to a multiple) still stands — but it is now
   a *product* decision not to use the feature, not an engineering claim that the field is inert.
3. **The conformance rig needs both paths.** Any contract clause touching these two fields can only be
   graded against Path-B vectors. A conformance suite built on Path A alone would score a Go port
   identically whether it implemented them or ignored them.

## Caveats and known defects in this capture set

- **Audited — ACCEPTED WITH REQUIRED CHANGES, and still not promotable.** Four raw captures,
  orchestrator-produced, then **independently audited by T22 (2026-08-18)**, whose audit was itself re-checked
  by **T27**. The audit found real defects in the orchestrator's own work (a false round-up rule; the wrong
  tenant rounding mode; missing admissibility furniture) and every oracle-independent correction it required is
  now applied in this document. **No number in `out/B-0*.json` was voided by the audit**; all four reproduce
  byte-for-byte three ways, including on a fresh tenant. What is still missing is *admissibility*, not
  correctness: T22 §10 **P0-3** (attestation sidecar), **P0-4** (fail-the-run preconditions) and **P0-6**
  (re-point at a production-settings tenant) remain open and each needs a live oracle. Until they close these
  are **audited observations, not parity vectors**.
- **Tenant timezone is `Asia/Kolkata`**, the stock demo tenant, not `Asia/Ulaanbaatar` or `Asia/Hovd`. No
  capture here is timezone-sensitive (all dates are civil dates on monthly boundaries), but a Mongolian
  tenant must be configured before any Path-B capture that depends on a clock.
- **Tenant rounding mode and precision were not asserted** on this path, and the T22 audit showed the
  omission mattered. Path A pins `(19, HALF_UP)` explicitly per capture; Path B inherited whatever the running
  tenant had. **CORRECTED per T22 audit P0-2:** the `default` tenant these four captures ran on is at
  **HALF_EVEN** (`c_configuration.rounding-mode = 6`; the server logged
  `Initialized rounding mode for tenant 'default': HALF_EVEN`), **not** the ratified HALF_UP — so every
  capture on record was taken at `(19, HALF_EVEN)`. Precision 19 is not in doubt
  (`MoneyHelper.PRECISION = 19`, compile-time). The mode is demonstrably **live** on this path (the audit
  exhibited `20,925.05` vs `20,925.04` in period 1 on the same server), so it is not a dead knob. The four
  captures are nevertheless mode-insensitive — established by **re-observing** them on a fresh
  `(19, HALF_UP)` tenant, which returned the same four SHA-256 digests
  (`.softhouse/capture/pathb/t22-audit/out-fresh-tenant/`), **not** by assumption. They are admissible at
  `(19, HALF_UP)` only on the strength of that committed re-observation, and remain **not** production-settings
  parity vectors until the attestation/re-point items (parked, oracle-dependent) are closed.
- **The server emits JSON numbers, not strings** (`1200000.0`, `144988.47`). A capture pipeline that parses
  before storing round-trips money through a binary float. The committed `out/*.json` files are the **raw
  response bytes**; any downstream tooling must read them as text or exact decimal, never as float.
- **Property invariants HAVE been mechanically re-checked.** *(This bullet previously read "Property
  invariants were not mechanically re-checked on these four captures… That is audit work." That statement is
  **false** as of the T22 audit and is retracted here per T27 RC-1.)* T22 wrote
  `t22-audit/t22_invariants.py` from scratch and ran **ten** invariants on all four captures and on its six
  probe captures: `I1` Σprincipal = disbursed, `I2` final balance = 0, `I3` Σinterest = totalInterestCharged,
  `I4` Σtotal = totalRepaymentExpected, `I5` splits sum to whole, `I6` P+I+F+Pen = total, `S1` every money
  literal exactly representable in **integer minor units**, `S2` running balance ties, `S3` the disbursement
  row ties, `S4` term days = span = Σ `daysInPeriod` (365 for `B-01`/`B-02`, 366 for `B-03`/`B-04`).
  **All PASS on all four.** T27 then proved the checks are genuinely *failable* by mutating a committed
  capture by one minor unit and confirming they FAIL (`.softhouse/reviews/t27-probe/t27_mutate.py`). Note the
  rescued WIP checker `t22-probe/invariants.py` had `I5` hard-coded to PASS (T22 P1-13); it is fixed, and its
  `PROVENANCE-NOTE.md` records the defect.
- **The EMI re-adjust loop is real, and no vector pins it** (T22 P1-11, first clause — recorded here; the
  capture that would pin it is still open and needs an oracle).
  `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` (`ProgressiveEMICalculator.java:1258-1308`, at most
  **3** iterations) re-rounds `EmiAdjustment.adjustedEmi()` through `applyInstallmentAmountInMultiplesOf` and
  adopts the new schedule only if the last-vs-penultimate EMI gap *shrinks* (`:1289-1291`). It can therefore
  **absorb a `multiplesOf` rounding difference entirely** — T22 demonstrated exactly that with a negative
  probe (`t22-audit/out-modeprobe/`), where HALF_UP and HALF_EVEN converged to the same schedule. Its entry
  condition is `EmiAdjustment.shouldBeAdjusted()`: `|emiDifference| × 100 > originalEmi.copy(floor(n/2))`, and
  `Money.copy(double)` **replaces** the amount (`Money.java:219-221` → `:215-217`), so the right-hand side is
  `Money(floor(n/2))` — **not** `EMI × floor(n/2)`. Misreading that as a multiply is a known trap: it is the
  defect that got three T21 probe scripts retracted. On all four Path B captures the residual is `±0.05`, so
  `5 > 6` is false and the loop does not fire — which is why the from-source re-derivations reproduce them
  without modelling it. **A Go port that implements the rounding but not the loop will diverge on inputs this
  corpus does not yet contain.**
- Fineract's client model splits names; the fixture clients use `fullname` to avoid asserting a
  `first_name`/`last_name` shape. This is the oracle's own schema and is not a Gerege contract surface.

## Reproduction

Full recipe, byte-exact requests and raw responses: `REPRODUCE.md`, `req/`, `out/` in this directory.
