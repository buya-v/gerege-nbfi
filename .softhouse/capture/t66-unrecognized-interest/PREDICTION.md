# T66 — PREDICTION, registered BEFORE the capture runs

Task **T66**, run `2026-08-17-run1-harness-schedule-poc`, context `loan-schedule`.
Pattern **P-9**: the prediction is committed one commit before `run-pass3h.sh` is
executed, in terms that can be falsified by the oracle's answer alone.

Subject: T63 backlog item 5 — **`futureUnrecognizedInterest` is not ported**, reported
UNPROVEN. `ProgressiveEMICalculator.java:1217` calls
`calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer`, which at
`:1243-1251` uses `getPeriodWithUnrecognizedInterest` (`:1805-1814`) to find a period
whose `getUnrecognizedInterest()` is `> 0` **and** whose `dueDate` is strictly after the
last-unpaid period's, copies that period's unrecognized interest onto the last-unpaid
period's `futureUnrecognizedInterest`, and sets `interestMovedUpward = true` on every
later period. The port (`nexus/internal/apps/loanschedule/emi.go:995-1055`,
`applyFinalPeriodResidual`) has no counterpart to either.

---

## 1. What the capture will observe, and why it has never been observable before

`futureUnrecognizedInterest` **cannot be read off a returned schedule.** It feeds
`calculateCalculatedDueInterest()` (`RepaymentPeriod.java:252-265`) and
`getDueInterest()` (`:271-286`), and `getDueInterest()` is
`min(calculatedDueInterest, emiPlusCreditedAmountsPlusFutureUnrecognizedInterest)`. On a
zero-EMI period that minimum is `min(cdi, 0) = 0` **whatever `cdi` is**, so an observed
`interest` of `0` on a dead row says nothing at all about the quantity the precondition
tests. Every capture pass in this program so far has recorded only the returned plan.

Pass **3h** therefore records the field itself. `Capture3h.java` builds the oracle's own
`ProgressiveLoanScheduleGenerator` around the oracle's own `ProgressiveEMICalculator`
(which is `final`, so it cannot be subclassed) behind a `java.lang.reflect.Proxy` that
delegates every call unchanged and only remembers the
`ProgressiveLoanInterestScheduleModel` returned by `generatePeriodInterestScheduleModel`.
That is the same object the generator then mutates, so after `generate()` returns the
harness reads the oracle's own final state. It reimplements nothing and does not touch
the seam class, whose byte identity against the pinned original is still asserted.

**Path identity is the calibration that licenses this.** Every case is *also* run through
the pristine embeddable seam; both plans are rendered cell for cell by one renderer, and
`run-pass3h.sh` fails the run if any pair differs.

---

## 2. THE PROOF this prediction rests on — derived from the pinned source

Setting: the Path A generate seam, inside DEC-1's graded domain
(`conformance/admit.go:999-1060`) — exactly one disbursement, `RepaymentEvery` 1
`MONTHS`, `DECLINING_BALANCE`, `FIXED_30_360`, no down payment, no installment rounding
multiple, MNT 2 decimals, `(19, HALF_UP)`. Plus the two facts the seam hard-wires: no
charges and no holiday DTO (`ProgressiveLoanScheduleGenerator.java:83`). **Nothing is
ever paid**, so for every period `paidPrincipal = paidInterest = 0`, `credited = 0`,
`capitalizedIncome = 0`, `fixedInterest = 0`.

Write `S_k` for the sum of period *k*'s interest periods' `getCalculatedDueInterest()`,
`emi_k` for its installment, `cdi_k` for `calculateCalculatedDueInterest()` and
`u_k` for `getUnrecognizedInterest()`.

**(a) The lookup runs on a copy whose later rate factors have been zeroed.**
`calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer` deep-copies at
`:1226` and calls `calculateRateFactorForScheduleTillDateInclusive(copy, tillDate)` at
`:1237`, which at `:1798-1802` sets `rateFactor` and `rateFactorTillPeriodDueDate` to
`BigDecimal.ZERO` on **every** interest period with `targetDate.isBefore(ip.getDueDate())`.
`InterestPeriod.getCalculatedDueInterest` multiplies by `getRateFactorTillPeriodDueDate()`
(`InterestPeriod.java:145-157`), so a zeroed interest period contributes exactly `0`.

**(b) On the generate path `tillDate` is anchored at the disbursement, not at maturity.**
`calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod` reaches
`calculateLastUnpaidRepaymentPeriodEMI(scheduleModel, calculateFromRepaymentPeriodDueDate)`
at `:747`, and `calculateFromRepaymentPeriodDueDate` is
`getEffectiveRepaymentDueDate(...)` (`:146-151`, `:250-263`) — the due date of the period
the disbursement lands in, or the next period's due date when it lands exactly on a due
date. Call that period's index `f`. On the ordinary shape `f = 0`. Consequently
**`S_k = 0` for every `k > f`** on the copy.

**(c) So beyond `f` the chain is a pure non-increasing cascade.** With payments, credits,
capitalized income, fixed interest and `futureUnrecognizedInterest` all zero,
`calculateCalculatedDueInterest` (`:252-265`) reduces to `cdi_k = S_k + u_{k-1}` and
`getDueInterest` (`:271-286`) reduces to `min(cdi_k, emi_k)`, hence

    u_k = max(0, cdi_k - emi_k)          and, for k > f,     u_k = max(0, u_{k-1} - emi_k)

which telescopes to `u_k = max(0, u_f - Σ_{j=f+1..k} emi_j)`.

**(d) `calculateLastUnpaidRepaymentPeriodEMI` has just enforced an aggregate identity.**
Immediately before the lookup, `:1189-1207` computes
`diff = totalDisbursed + capitalizedIncome + creditedPrincipal + totalDueInterest − totalEMI`
and assigns `emi_L := emi_L + diff` on the selected last-unpaid period `L`. So

    Σ_j emi_j  =  P + I,        where P is the disbursed principal and I = Σ_j dueInterest_j
                                measured on the real model just before the assignment.

**(e) Therefore `u_L = 0`, always.** `emi_j = 0` for every `j > L` (that is what makes `L`
the last **not** fully paid period — `isFullyPaid()` at `RepaymentPeriod.java:371-373` is
`emiPlusCreditedAmountsPlusFutureUnrecognizedInterest == totalPaidAmount`, and with
nothing paid that is `emi_j == 0`). So `Σ_{j=f+1..L} emi_j = P + I - Σ_{j≤f} emi_j`, and

    u_L = max(0, u_f - P - I + Σ_{j≤f} emi_j)  ≤  max(0, cdi_f - P - I + Σ_{j≤f} emi_j).

Two cases. If `cdi_f ≤ emi_f` then `u_f = 0` and `u_L = 0` immediately. Otherwise
`dueInterest_f = emi_f`, so `I ≥ emi_f`, and `u_L = 0` as soon as `cdi_f ≤ P + emi_f` —
which holds whenever the **first period's rate factor is at most 1.00**, i.e. at most
100% per period, because `cdi_f ≤ B·r ≤ P·r` for the balance `B ≤ P`. At `FIXED_30_360`
with monthly repayment the per-period rate factor is `annualRate/12`, so the sufficient
condition is `annualRate ≤ 1200%` on the regular lattice (and `≤ 600%` if the month-end
re-anchor doubles a `periodRatio`).

**(f) And the cascade is dead from `L` onwards.** `u_L = 0` gives `cdi_{L+1} = 0`, hence
`u_{L+1} = 0`, and so on. `getPeriodWithUnrecognizedInterest` requires a period with
`u > 0` **strictly after** `L` (`:1806-1808`). There is none.

**(g) The `:1178-1181` fallback cannot rescue it either.** It only fires when the first
filter yields **empty**, and it then selects the **last** period — after which no period
can be strictly later. Inert by construction.

### Where the driver's hypothesis was right, and where it was incomplete

The driver's chain was right that a zero-EMI period is vacuously `isFullyPaid()` and that
zero-EMI tails exist on admissible shapes (`T64-ZP-B` has 40 of them). It was incomplete
at exactly one place: it did not account for step **(a)/(b)** — that the lookup runs on a
copy in which every period after `tillDate` has had its rate factors **zeroed**, so a
tail period's own interest cannot supply the `u > 0` the precondition needs. The only
route left is inheritance down the `u` chain from period `f`, and step **(e)** closes it.
This is the step T69 named as missing (`emi.go:315-325`, `[UNVERIFIED]`): *"the argument
still needs the tillDate period's OWN unrecognized interest to be zero ... that step is
not established here."* Step (e) establishes it, from the aggregate identity rather than
from a claim about `u_f` itself.

---

## 3. THE PREDICTION — falsifiable, per case, per period

`run-pass3h.sh` runs 18 cases: 8 rig calibrations and 10 mechanism probes. The probes
push the two axes DEC-1 leaves unbounded (nominal rate up to 12000%, i.e. a per-period
rate factor of 10.00 — ten times past the proof's sufficient condition — and terms to
120), plus the month-end drift region where the per-period rate factor is **not** uniform,
plus the `f = 1` shape where the disbursement lands on a repayment due date.

**P1.** For **every period of every one of the 18 cases**,
`mechanism.periods[*].futureUnrecognizedInterest == "0.00"`.

**P2.** For **every period of every one of the 18 cases**,
`mechanism.periods[*].interestMovedUpward == false`.

**P3.** All 18 cases report `pathIdentity.identical == true`.

**P4.** All 8 calibrations reproduce their committed counterparts cell for cell:
`P-CAL`→pass-3b `P-CAL` (12, HALF_UP); `P-CAL-P00`→pass-3b `P-00`;
`P-CAL-EMI6`→pass-3c `P-EMI-6-1M014632`; `P-CAL-LATQ0a`→pass-3e `P-LAT-Q0a`;
`P-CAL-MNT50M`→pass-3b `P-MNT-50M`; `P-CAL-DRIFTF`→pass-3e `P-DRIFT-F`;
`P-CAL-ZPA`→pass-3g `T64-ZP-A`; `P-CAL-ZPB`→pass-3g `T64-ZP-B`.

**P5.** `P-CAL-ZPB` reports at least one period with `emi == "0.00"` and
`isFullyPaid == true` while `totalPaidAmount == "0"` — i.e. the capture will show the
**vacuously fully-paid zero-EMI period** the driver's hypothesis is built on really does
exist, and will show `futureUnrecognizedInterest` staying `"0.00"` anyway. If instead no
case has a zero-EMI period, the observation is uninformative about the hypothesis and I
will say so rather than claim a proof was corroborated.

### What falsifies this, and what happens then

**If any case returns a `futureUnrecognizedInterest` other than `"0.00"`, or any
`interestMovedUpward == true`, the proof above is WRONG.** T66's verdict on ITEM 1 is
then **(A) A DIVERGENCE EXISTS**, the port has a **P0** at
`nexus/internal/apps/loanschedule/emi.go:995-1055` (`applyFinalPeriodResidual` has no
counterpart to `:1243-1251`, and `dueInterestMinor`/`duePrincipalMinor` at `emi.go:727-753`
have none to the `+futureUnrecognizedInterest` terms of `RepaymentPeriod.java:252-265`,
`:271-286`, `:293-295`, `:302-304`), and the money delta is reported in minor units from
the case that moved. I will not fix it — T66's charter is `test`.

**If `pathIdentity` is false anywhere**, the mechanism columns are not evidence about the
seam and I will report the whole capture as void rather than quote a number from it.

**If a calibration drifts**, nothing from the run may be believed and the run is refused.
The expected value is never adjusted to make a calibration pass.

---

## 4. What this prediction does NOT claim

- It does **not** predict `unrecognizedInterest == "0.00"` on the periods of the **real**
  model. The proof is about the **copy**, and `u_k` on the real model is only an upper
  bound for `u_k` on the copy — a non-zero real-model `u_k` before `L` would be
  interesting but would refute nothing here. The port already reproduces that cascade
  (`emi.go:684-723`, `carriedUnrecognized`).
- It does **not** claim the mechanism is dead on the **smoothing loop's trial copy**
  (`:1288`). The proof applies there too — same `tillDate`, and `:1288` re-establishes the
  same aggregate identity before the adjustment is judged — but the probe reads the real
  model only, so that half is proof and not observation. Stated as such in the handoff.
- It says nothing about **multi-tranche disbursement**, **payments**, **charges**,
  **re-aging**, **capitalized income** or **interest pauses**. Every one of them breaks a
  premise: the `allowFullTermForTranche` branch reaches
  `calculateLastUnpaidRepaymentPeriodEMI` at `:247` with `tillDate` = the **disbursement
  date** rather than a period due date, a payment makes `totalPaidAmount` non-zero so
  `isFullyPaid()` stops meaning `emi == 0`, and a credit or capitalized income breaks the
  aggregate identity of step (d). **The moment any of those enters the graded domain this
  proof lapses and the port needs the field.**

---

Registered by T66 before `sh .softhouse/capture/src/run-pass3h.sh` was executed.
Pinned reference oracle (Fineract) `426a23544e8426a38ae43ae404670a0a7e85b9eb`,
image `sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`.
"Oracle" here means the Fineract reference implementation; Oracle Database is a
prohibited product in this program and no part of this capture touches any database.
