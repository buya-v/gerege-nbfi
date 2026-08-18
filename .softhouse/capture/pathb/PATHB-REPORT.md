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

**12 of 12 periods differ.** The EMI is raised to the next multiple of 100 and held constant for periods
1–11, and the **final installment absorbs the residual** — period 12 is principal `109,888.23` + interest
`1,977.99` = `111,866.22`, deliberately *not* the rounded EMI.

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
- **Tenant rounding mode and precision were not asserted** on this path. Path A pins `(19, HALF_UP)`
  explicitly per capture; Path B inherits whatever the running tenant has. Until that is asserted, these are
  **not** production-settings parity vectors in the sense pass 3 is.
- **The server emits JSON numbers, not strings** (`1200000.0`, `144988.47`). A capture pipeline that parses
  before storing round-trips money through a binary float. The committed `out/*.json` files are the **raw
  response bytes**; any downstream tooling must read them as text or exact decimal, never as float.
- **Property invariants were not mechanically re-checked** on these four captures the way pass 3's twelve
  were. That is audit work.
- Fineract's client model splits names; the fixture clients use `fullname` to avoid asserting a
  `first_name`/`last_name` shape. This is the oracle's own schema and is not a Gerege contract surface.

## Reproduction

Full recipe, byte-exact requests and raw responses: `REPRODUCE.md`, `req/`, `out/` in this directory.
