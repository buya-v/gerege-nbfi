# Path B — first captures from the RUNNING reference oracle (server + PostgreSQL)

**Fire:** local `20260818-170002` (Buyan's Mac), 2026-08-18
**Executed by:** the orchestrator (vector capture touches the oracle, so it is orchestrator-only)
**Status:** RAW OBSERVED, **NOT YET INDEPENDENTLY AUDITED**. No vector promoted to the store; no gate answered.

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

> **CORRECTED by the T22 independent audit (2026-08-18), P0 item 1.** An earlier version of this paragraph
> said the EMI is *"raised to the next multiple of 100"*. That rule is **FALSE**. The oracle rounds the EMI
> to the **NEAREST** multiple of `installmentAmountInMultiplesOf` **under the tenant rounding mode**
> (`ProgressiveEMICalculator.java:1770-1776` → `Money.java:163-171`), with a **zero-guard** that returns the
> unrounded EMI if rounding would zero a positive one. `B-02` cannot distinguish the two rules
> (`112,082.37` rounds up either way), so the audit put a round-**down** case to the oracle: at principal
> **MNT 1,190,000** with `installmentAmountInMultiplesOf = 100` at `(19, HALF_UP)`, the unrounded EMI
> `111,148.35` becomes **`111,100.00`** — rounded DOWN. Committed observation:
> `.softhouse/capture/pathb/t22-audit/out-rounddown/rounddown-gerege-raw.json`. Anything DEC-1 says about
> this field must be written from the corrected round-to-nearest rule, not the round-up sentence.

So the field is **not dead**. It is dropped by the Path A seam and honoured by the server. The residual
absorption rule is a normative semantic the contract must state.

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

- **Not audited.** Four raw captures, orchestrator-produced. The last three capture passes were each audited
  and each audit found real defects in the orchestrator's own work. Treat every number here as
  observed-but-unaudited.
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
- **Property invariants were not mechanically re-checked** on these four captures the way pass 3's twelve
  were. That is audit work.
- Fineract's client model splits names; the fixture clients use `fullname` to avoid asserting a
  `first_name`/`last_name` shape. This is the oracle's own schema and is not a Gerege contract surface.

## Reproduction

Full recipe, byte-exact requests and raw responses: `REPRODUCE.md`, `req/`, `out/` in this directory.
