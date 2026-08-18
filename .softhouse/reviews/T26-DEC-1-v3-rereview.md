# T26 — Independent adversarial re-review of DEC-1 **revision 3**

| | |
|---|---|
| Task | T26 (independent reviewer; zero inherited context) |
| Subject | `docs/adr/DEC-1-schedule-generator-adapter.md` revision 3, and `nexus/internal/apps/loanschedule/contract/contract.go` |
| Predecessors | rev 1 REJECTED (T5); rev 2 ACCEPTED-WITH-REQUIRED-CHANGES, not ratifiable (T23, three P0s); rev 3 produced by T24 |
| Reference oracle | Fineract, pinned checkout — `git -C /home/user/fineract rev-parse HEAD` = **`426a23544e8426a38ae43ae404670a0a7e85b9eb`** ✔ verified |
| Live oracle | **NONE reachable.** No Docker, no PostgreSQL on :5432. No new observation was taken, synthesised or implied. |
| Worktree | `/home/user/wt-T26`, branch `softhouse/T26-dec1-v3-rereview` |

---

## VERDICT

> ## ACCEPTED WITH REQUIRED CHANGES — **NOT ratifiable**
>
> **P0 outstanding: 1** (new; found by this review, not carried from T23).
>
> **P0-T26-1 — The EMI re-adjust loop is specified by its TRIGGER but not by its EFFECT.**
> Revision 3 correctly establishes *that* `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
> fires inside the graded domain and correctly states its guard; it never states what the loop
> then *does*. Two implementations can satisfy every sentence of revision 3 and return
> **different money** for the same in-graded-domain request, and the Run-1 corpus provably
> cannot tell them apart.

**T23's three P0s: two fully resolved, one resolved in substance but incomplete.**

| T23 P0 | Disposition |
|---|---|
| **P0-1** EMI re-adjust loop | **Substantively CORRECT** — reachability, guard formula, placement and the no-float rule all independently re-derived and confirmed. **But the fix is incomplete**: it creates P0-T26-1 (below). |
| **P0-2** disbursement window | **RESOLVED, cleanly.** Source re-derivation confirms the discard; the graded-domain predicate is exactly right; the false ordering clause is gone from **both** artefacts with **no restatement surviving anywhere**. |
| **P0-3** `FrequencyYears` + error precedence | **RESOLVED** on all normative content. One P1 inaccuracy in the *mechanism* prose (P1-T26-1). |

Standing policy **P-2** permits ratification only on a clean review. This review is not clean.
The single required correction (P0-T26-1) needs **no oracle** — it is pure source
re-derivation, and this review supplies the derivation and a working reference model.

---

## 0. Method and evidence classification

Every finding below is tagged:

- **(a) SOURCE RE-DERIVATION** — established by me, this task, from the pinned checkout.
- **(b) COMMITTED PRIOR OBSERVATION** — a value already captured and committed by T21/T22/T23 under `.softhouse/reviews/`. Re-cited, never re-taken.
- **(c) NEEDS A FRESH OBSERVATION** — cannot be settled without a live oracle. Listed in §7.

I did **not** reuse `.softhouse/capture/out/t21-probe-rederive.py` (T23 found its guard model
defective). I did **not** reuse `.softhouse/reviews/t23-probe/t23_rederive.py`. I wrote my own
model from scratch: `.softhouse/reviews/t26-probe/t26_rederive.py` (see §6).

**Independence check that matters:** my from-scratch re-derivation reproduces the two committed
T23 oracle observations **exactly** — level EMI `172,574.64` / final `172,574.62` / total interest
`20,815.82` on MNT 1,014,632 / 6 × 7.0 %, and level `4,540.30` / final `4,540.06` / total interest
`35,746.56` on MNT 127,704 / 36 × 16.8 % — **but only when the loop body is modelled**. Without
the loop it produces `172,574.63` / `172,574.67` and `4,540.29` / `4,540.54` / `35,746.69`. This is
independent confirmation of T23's P0-1 *and* the mechanism by which I found P0-T26-1.

---

## 1. P0-1 (T23) — EMI re-adjust loop. Substantively correct; **incomplete**.

### 1.1 Is the loop truly on the main path? **YES.** (a)

`ProgressiveEMICalculator.java:748-750`, read directly:

```java
        calculateLastUnpaidRepaymentPeriodEMI(scheduleModel, calculateFromRepaymentPeriodDueDate);
        if (onlyOnActualModelShouldApply) {
            checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods(scheduleModel, relatedRepaymentPeriods);
        }
```

and at `:732-735`:

```java
        final boolean onlyOnActualModelShouldApply = scheduleModel.isEmpty()
                || operation.getAction() == EmiChangeOperation.Action.INTEREST_RATE_CHANGE
                || operation.getAction() == EmiChangeOperation.Action.ADD_REPAYMENT_PERIODS || scheduleModel.isCopy();
```

`scheduleModel.isEmpty()` is true on the initial disbursement of every loan, so the call at `:749`
executes on **every ordinary generation**. Revision 3 §4.3 and `contract.go:990-995` state this
correctly. Revision 2's "reachable only outside the graded domain" was false and is properly struck.

`n` is `relatedRepaymentPeriods.size()`; on initial generation
`ProgressiveLoanInterestScheduleModel.getRelatedRepaymentPeriods(null)` returns **all** periods
(`ProgressiveLoanInterestScheduleModel.java:191-194`), so `n == NumberOfRepayments`. Revision 3's
"3.00 for a 6-period loan, 18.00 for 36" is therefore right.

### 1.2 Is the guard truly `|lastEMI − penultimateEMI| × 100 > floor(n/2)` currency units? **YES.** (a)

`EmiAdjustment.java:31-36`:

```java
    public boolean shouldBeAdjusted() {
        double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
        return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero() && emiDifference.abs()
                .multipliedBy(100)
                .isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));
    }
```

with `ProgressiveEMICalculator.java:1778-1789` supplying `originalEmi = penultimatePeriod.getEmi()`
and `emiDifference = lastPeriod.getEmi().minus(penultimatePeriod.getEmi())`.

**`Money.copy(double)` REPLACES, it does not scale** — `Money.java:216-222`:

```java
    public Money copy(final BigDecimal amount) { return new Money(this.currency, amount, this.mc); }
    public Money copy(final double amount)     { return copy(BigDecimal.valueOf(amount)); }
```

The new `Money` takes `floor(n/2)` as its **amount**, scaled to the currency's decimal places by the
constructor at `Money.java:52`. The threshold is `floor(n/2)` currency units flat, with **no**
dependence on the EMI and **no** dependence on `InstallmentRoundingMultipleMinor`. Revision 3 §4.3
and `contract.go:998-1004` state this correctly, and the integer form given —
`|lastEMI − penultEMI| × 100 > floor(n/2) × 10^MinorUnitDigits` in `int64` minor units — is
arithmetically exact (LHS `|d|ₘ × 100`, RHS `floor(n/2) × 10²`).

This also disposes of the defect T23 identified in the T21 probe: the threshold is **not** multiplied
by the EMI. Confirmed from source, independently.

### 1.3 Is it recorded as a Go-module obligation in the right places? **YES.** (a)

- ADR **§9**, line 515 — in the "the **Go module** must reproduce …" list.
- `contract.go:984-1028` — on the **`Period` type doc comment**, a live response type, **not** the
  doc comment of `InstallmentRoundingMultipleMinor` (the field pinned to zero). This is exactly what
  T23 required.
- ADR §4.7 line 343 and §8 item 3 line 484 are both correctly re-scoped away from the
  installment-rounding framing.

### 1.4 Is the no-float rule correct and sufficient? **YES.** (a)

ADR §4.3 line 273 and `contract.go:1021-1028`. `Math.floor(n/2.0)` and the
`BigDecimal.valueOf(double)` inside `Money.copy(double)` operate only on exact small integers, so
`int`/`int64` arithmetic reproduces them exactly. The prohibition on `float32`/`float64` is stated
explicitly and correctly. No float exists anywhere in the Go artefact (§5).

### 1.5 **P0-T26-1 — but the loop's EFFECT is nowhere specified.** (a)

Revision 3 tells an implementer **when** the loop acts. It never tells them **what it does**.

What the source actually does — `ProgressiveEMICalculator.java:1258-1308`, with
`EmiAdjustment.java:38-48`, `Money.java:352-358` and `ProgressiveEMICalculator.java:2027-2031`:

| Step | Source | Stated in rev 3? |
|---|---|---|
| guard | `EmiAdjustment.java:31-36` | ✔ fully |
| iteration cap = 3 | `:1307-1308` | ✔ |
| **adjustment magnitude** `emiDifference ÷ max(1, n − uncountablePeriods)`, via `Money.dividedBy(long)` (mc division, then currency-scale rounding under the mode) | `EmiAdjustment.java:38-40`; `Money.java:352-358` | ✘ **absent** |
| **`uncountablePeriods`** = count of periods whose `totalPaidAmount` exceeds `originalEmi` (0 on a fresh schedule) | `:2027-2031` | ✘ absent |
| **`adjustedEmi = penultimateEMI + adjustment`** | `EmiAdjustment.java:42-44` | ✘ absent |
| **break when the multiple-rounded adjusted EMI equals the original** | `:1270-1273` | ✘ absent |
| **apply the adjusted EMI to every related period, then recompute balances and re-apply the final residual** | `:1279-1288` | ✘ absent |
| **adoption test — keep the new model only if `|newDiff| < |oldDiff|`, otherwise DISCARD and stop** | `:1289-1291`; `EmiAdjustment.java:46-48` | partial: ADR §4.3 line 264 says "adopts it if the last-vs-penultimate gap shrinks"; **`contract.go` says nothing at all** |
| guard conjuncts `floor(n/2) > 0` and `emiDifference ≠ 0`; and the degenerate `EmiAdjustment` for a 1-period schedule at `:1788` | `EmiAdjustment.java:33-34`, `:1788` | ✘ absent (and `contract.go`'s graded domain admits `NumberOfRepayments >= 1`) |

**Why this is rejection-grade, not a nit.** DEC-1 §1 states that the contract is what *both*
implementations are written to, that it is the golden-vector encoding, and that a port which passes
its corpus and is still wrong is the failure this program exists to prevent. Revision 3 itself says
(§4.3, `contract.go:1016-1019`) that **no Run-1 capture trips this guard**, so conformance cannot
detect a wrong loop body. An unspecified *and* ungradable money rule inside the graded domain is
precisely the compound failure the document is built to exclude — and after ratification, adding the
missing text costs a `user` gate.

**Measured, by source re-derivation** (`.softhouse/reviews/t26-probe/t26_variants.py`,
`t26_scan.py`; no oracle contacted). Over 24,000 in-graded-domain shapes
(n ∈ {6,12,18,24,36,60}, principals 100,000–103,999 MNT, rates 7.0/16.8/18.5/21.6 %), the guard
**fires on 2,855** — roughly one loan in eight. Comparing the source-faithful body (V0) against two
bodies that are each consistent with everything revision 3 *says*:

| Alternative body, all consistent with rev 3's text | Shapes where it returns **different money** |
|---|---|
| **V1** — same adjustment, omit the `hasLessEmiDifference` adoption test (`contract.go` never mentions it) | **2,156 / 2,855** — first: MNT 100,025 / 12 × 16.8 % → level `9,113.26`/final `9,113.33` vs `9,113.27`/`9,113.20` |
| **V2** — put the whole residual onto the level EMI, a plain reading of "an adjusted installment" | **699 / 2,855** — first: MNT 100,017 / 6 × 7.0 % → `17,011.48`/`17,011.50` vs `17,011.49`/`17,011.45` |

On revision 3's own worked example the spread is **0.13 in total interest**
(35,746.56 vs 35,746.69) in a document that grades to the minor unit.

**Required correction.** State the loop body normatively — in ADR §4.3 **and** in `contract.go`
(the artefact is the boundary; the ADR is not compiled into anything) — to the same standard §4.3
already applies to the final-period residual, which it correctly refused to leave "named rather than
defined". Minimum content: the adjustment magnitude and its rounding, `uncountablePeriods`, the
break-on-equal test, the apply-and-recompute step, the adoption test, and the two guard conjuncts
plus the `n == 1` degenerate case. `t26_rederive.py::readjust_loop` is a working reference model
that reproduces both committed observations exactly and may be transcribed.

---

## 2. P0-2 (T23) — disbursement window. **RESOLVED.**

### 2.1 Does the source really discard such a disbursement? **YES.** (a)

`ProgressiveLoanScheduleGenerator.java:299-311`:

```java
            boolean hasDisbursementAfterLastRepaymentPeriod = includeDisbursementsAfterMaturityDate
                    && !disbursementDate.isBefore(maturityDate);
            boolean hasDisbursementInCurrentRepaymentPeriod = !includeDisbursementsAfterMaturityDate
                    && !disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate);
            if (!hasDisbursementAfterLastRepaymentPeriod && !hasDisbursementInCurrentRepaymentPeriod) {
                continue;
            }
```

- The **in-loop** call passes `includeDisbursementsAfterMaturityDate = false` (`:121-122`), so the only
  admitting window is the **half-open** `[periodFromDate, periodDueDate)`.
- The **post-loop** call, the only one that passes `true`, is gated on
  `loanApplicationTerms.isMultiDisburseLoan()` (`:147-150`), which is `false` on this
  single-disbursement seam.
- `emiCalculator.addDisbursement` (`:351`) is therefore never reached, and the principal vanishes —
  an all-zero schedule. Confirmed.

Corroborating **(b)**: T23's committed cases Q1a/Q1b/Q2 in
`.softhouse/reviews/t23-probe/t23-probe-output.txt`.

### 2.2 Is the graded-domain predicate closed against it? **YES — and it is exactly right.** (a)

The predicate `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment DueDate`
(ADR line 126, `contract.go:640`) is the **exact** union of the oracle's admitting windows, because:

- `DefaultScheduledDateGenerator.java:55` sets `lastRepaymentDate = scheduleStartDate`, so
  `FromDate₁ == ScheduleStartDate`;
- `:69-71` emits `repayment(k, lastRepaymentDate, nextRepaymentDate)` then assigns
  `lastRepaymentDate = nextRepaymentDate`, so periods are **contiguous** —
  `⋃ₖ [Fromₖ, Dueₖ) = [ScheduleStartDate, Dueₙ)`.

No off-by-one, no gap. The predicate is also genuinely computable without the oracle: the due dates
depend on `ScheduleStartDate`, the count, the frequency and the month-end seed (which is the
disbursement date, `LoanApplicationTerms.java:583-589` — verified), all of which the implementation
already has. No circularity.

### 2.3 Is the refusal path coherent? **YES.** (a)

`ErrNoDiscriminatingVector` is the right sentinel under the standing G-1 "refuse rather than guess"
disposition: the oracle *does* answer (degenerately), so it is a missing-vector refusal, not a
missing-answer one. It widens with no amendment when multi-tranche vectors land — consistent with
§3.1's two-domain structure. The Run-1 capture that separates `ScheduleStartDate` from
`Disbursement.Date` (start 2024-01-01, disbursement 2024-02-01, six monthly periods) remains **inside**
the window (2024-02-01 < 2024-07-01), so no existing capture is invalidated. ✔

### 2.4 Was the false ordering clause removed **everywhere**? **YES.** (a)

I grepped both artefacts for every phrasing of the deleted claim
(`after every repayment`, `sorts after`, `on or after`, `after the last`, `maturity`, `beyond the last`).
Every surviving hit is either the explicit deletion note or the refusal statement. **No restatement
survives.** This was the known failure mode T23 warned about; it did not occur.

The corrected window-key rule also reproduces the observed order: for a disbursement on the schedule
start, its key is period 1's `DueDate`, tying with repayment 1 and breaking to disbursement-first —
matching the oracle, which calls `processDisbursements` (`:121`) before `periods.add` (`:141`).

---

## 3. P0-3 (T23) — `FrequencyYears` and error precedence. **RESOLVED** (one P1 in the prose).

### 3.1 Does it throw only on the fixed-30/360 arm? **YES.** (a)

`ProgressiveEMICalculator.java:1533-1539`:

```java
        return switch (daysInMonthType) {
            case ACTUAL -> rateFactorByRepaymentPeriod(...);
            case DAYS_30 -> calculateRateFactorPerPeriodBasedOnRepaymentFrequency(...);
            default -> throw new UnsupportedOperationException("Unsupported combination: Days in month: " + daysInMonthType);
        };
```

and `:1602-1610` — the per-frequency `switch` reached only from the `DAYS_30` arm — handles DAYS,
WEEKS, MONTHS and `default -> throw new UnsupportedOperationException("Invalid repayment frequency")`.
So `FrequencyYears` + `DayCountFixed30Over360` throws; the ACTUAL day-count arms never reach that
dispatch. Confirmed. Corroborating **(b)**: T23 cases Q3a/Q3b.

### 3.2 Is the error-precedence rule complete and unambiguous? **YES.** (a)

`ErrInvalidRequest` ≻ `ErrUnsupportedConfiguration` ≻ `ErrNoDiscriminatingVector`, first applicable
wins (ADR §4.11 lines 403-409; `contract.go:1202-1225`). I checked it for total determinism:

- The taxonomy has exactly three sentinel **values**, so ordering the three classes totally orders
  every refusal; within a class the returned value is literally identical, so no residual ambiguity.
- I walked every refusal condition named anywhere in either artefact
  (`len(Disbursements) != 1`, `RateFactorScale != SignificantDigits`, `Rate{1,3}`,
  `InstallmentRoundingMultipleMinor` not a whole major unit, non-zero installment multiple,
  `HALF_EVEN`, `DayCountActualActual`, `FrequencyDays`/`Weeks`/`Years`, `DownPaymentPercentage != 0`,
  `MinorUnitDigits != 2`, `RepaymentEvery != 1`, precision ≠ 19, the disbursement window) and found
  **no condition whose class is stated inconsistently between the ADR and `contract.go`**, and no
  request for which two classes could both be "first".
- The worked example resolves as claimed: `FrequencyYears` + 30/360 + `HALF_EVEN` →
  `ErrUnsupportedConfiguration`, deterministically.

The reasoning offered for the ordering (the stronger, more permanent obstruction wins, consistent
with the wrapping direction) is sound.

### 3.3 **P1-T26-1 — the mechanism prose names the wrong ACTUAL arm.** (a)

ADR line 381 and `contract.go:245-247` both assert: *"the **`ACTUAL` arm at `:1534-1535`** never
reaches that dispatch: it calls `rateFactorByRepaymentPeriod` directly"*.

For an **annual** repayment period this is not the line that executes. `:1505-1507`:

```java
        final boolean partialPeriodCalculationNeeded = daysInYearType == DaysInYearType.ACTUAL && numberOfYearsDifferenceInPeriod > 0
                && (!DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY.equals(daysInYearCustomStrategy) || ...);
```

Under `DayCountActualActual` the year type **is** `ACTUAL`, and an annual period *always* spans a
calendar-year boundary, so `numberOfYearsDifferenceInPeriod > 0` always holds and the method returns
at `:1526-1531` via `rateFactorByRepaymentPartialPeriod` — the `switch` at `:1533` is never reached
at all. `:1534-1535` is in fact **unreachable** for `FrequencyYears`.

The **conclusion is unaffected** (neither ACTUAL path reaches `:1602-1610`; the schedule generates;
the refusal and its sentinel are unchanged), which is why this is P1 and not P0. But it matters for
two reasons: it is a normative-adjacent source claim in a frozen document, and it **contradicts
`contract.go`'s own `DayCountActualActual` doc** at `:317-319`, which correctly says ACTUAL selects
`:1505-1507 → :1526-1531` on a cross-year period. It also means Q3b's answer came from the very arm
ADR §8 item 5 calls "the largest un-re-derived hole in the evidence" — worth saying out loud.

**Correction:** *"neither ACTUAL arm reaches that dispatch — for an annual period, which always
crosses a calendar-year boundary, `:1505-1507` diverts to the partial-period arm at `:1526-1531`
before the `:1533` switch is evaluated; the `case ACTUAL` arm at `:1534-1535` is reached only for
sub-annual periods that stay within one calendar year."*

---

## 4. New findings

### P0-T26-1 — EMI re-adjust loop body unspecified. **See §1.5.** (a)

### P1-T26-1 — `FrequencyYears` mechanism names the wrong ACTUAL arm. **See §3.3.** (a)

### P1-T26-2 — Revision 3 now **self-contradicts** on `Money.java:220-222`. (a)

ADR §8 item 7, line 488, still reads:

> The oracle's own `Money` exposes `double` overloads [`Money.java:134-148`, **`:220-222`**] … —
> **traps for a harness author, not parts of the calculation.**

Revision 3's own §4.3 (line 264) and `contract.go:1000-1002` now assert the opposite: `Money.copy(double)`
at `:220-222` is the constructor of the re-adjust guard's threshold, on the **live calculation path**
(`EmiAdjustment.java:35`, and again at `ProgressiveEMICalculator.java:1788`). T23 raised this as its
P1-2; T24 correctly scoped itself to P0s and left it, so revision 3 ships a direct internal
contradiction. It is P1, not P0, because §8 is explicitly "Backlog (out of scope for DEC-1)" and
nothing normative depends on it — but it is exactly the "corrected claim left restated elsewhere"
pattern, and a harness author reading §8 would draw the wrong conclusion.
**Correction:** split the citation — `:134-148` are traps; `:220-222` is live.

### P1-T26-3 — the "seventeen per-period divergences" figure is still wrong in three places. (b)

ADR line 200 ("Seventeen per-period divergences"), ADR line 421 ("17 divergent periods"), and
`contract.go:471` ("seventeen per-period divergences"). T23's P1-1 established from the committed
capture files that **all 18** repayment rows differ. Carried, unfixed. Non-blocking, but it is a
factual claim about the evidence base in a document about to be frozen.

### P2-T26-1 — the graded-domain block differs between the two artefacts. (a)

ADR §3.1 (lines 114-127) lists twelve predicates; `contract.go:628-640` lists thirteen, adding
`NumberOfRepayments >= 1`. The ADR says the block is "also stated normatively on `GenerateRequest`",
which is now not literally true. `NumberOfRepayments >= 1` is arguably a well-formedness condition
(`ErrInvalidRequest`) rather than a graded-domain one, and its presence interacts with the unstated
`n == 1` degenerate case in §1.5. Align the two lists and decide which sentinel `n < 1` yields.

### P2-T26-2 — §4.1's calibration inference is weaker than the conclusion it supports. (a)

ADR line 210 infers, from a precision-12-threaded capture on a precision-19 tenant reproducing the
shipped conformance literal, that "no reached call site consulted the tenant-global precision".
That inference is not valid on its own: §4.1 itself establishes that the shipped 100.00 / 6 × 7 %
shape is largely precision-insensitive, so reproducing it is weak evidence. The **conclusion** is
nevertheless independently supportable from source — inside the graded domain every `Money` is
constructed through a three-argument `Money.of(..., mc)` carrying the threaded context, and
`Money.java:52` reads only the *rounding mode* from `getMc()`, never the precision; the
tenant-global-precision reads (`Money.java:103`, `:115`, `:160`, and `:377`) all sit on the
installment-multiple / `multipliedBy(double)` paths, which are outside the graded domain. Replace
the weak evidence with the source argument.

---

## 5. Non-negotiables scan (CLAUDE.md)

| Non-negotiable | Result |
|---|---|
| Integer minor units only; **no float on any money path** | **PASS.** Only Go file is `contract.go`. `grep -rn "float32\|float64\|big.Float\|math/big"` over `nexus/` returns exactly two hits, `:66` and `:1027`, both prose that **prohibits** floats. All money is `int64` minor units; rates are `Rate{Numerator, Denominator}` exact rationals. |
| Oracle Database / MySQL / MariaDB tokens (`ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`) | **PASS.** Zero hits in the ADR and in `nexus/`. The only match in the worktree is T24's own handoff describing its scan pattern. The ADR's Terminology block (line 20) correctly separates "reference oracle (Fineract)" from the prohibited "Oracle Database". |
| PostgreSQL only | **PASS** — n/a to this contract; no database token of any kind appears. |
| No US payment rails/vendors (Stripe/Plaid/Lithic/Persona) | **PASS.** Zero hits. |
| Three-field Mongolian names; never `first_name`/`last_name` | **PASS.** ADR line 290 and `contract.go:86-87` both state the rule *prohibitively*; no identity field exists in the contract at all, which is the stronger position. |
| No hard-coded timezone offsets | **PASS.** `TimeZone` is an IANA zone **name**; `contract.go:737-739` explicitly rejects `"+08:00"`, `"UTC+8"`, `"GMT+8"` with `ErrInvalidRequest`. Both Mongolian zones named, DST-free noted. |
| No hard-coded payment threshold | **PASS.** The one `5,000,000` occurrence (`contract.go:660`) is a **sampled principal** in the corpus description, not a rail threshold. |
| Never "insured / protected / guaranteed" | **PASS.** Zero hits; ADR line 290 forbids the notion explicitly. |
| Ledger double-entry / append-only | **N/A** — `Generate` is pure and posts nothing (§6.8). Correctly out of scope. |
| `Idempotency-Key` on money-movement POST | **N/A** — no endpoint, no money movement. |

## 5.1 Build / vet / format / test

Run in `/home/user/wt-T26/nexus`:

```
go build ./...   -> exit 0, no output          CLEAN
go vet ./...     -> exit 0, no output          CLEAN
gofmt -l .       -> no output                  CLEAN
go test ./...    -> ? github.com/gerege/nexus/internal/apps/loanschedule/contract [no test files]
```

`contract.go` is declarations and doc comments only, so "no test files" is expected at this stage,
not a defect. It is worth noting for the driver that **nothing in this repository executes the
contract**, so build/vet/gofmt cleanliness carries no behavioural assurance whatever — which is
precisely why the specification gap in §1.5 is the whole risk.

---

## 6. Re-derivation artefacts

Under `.softhouse/reviews/t26-probe/`. **None was run against a live oracle** — no Fineract instance
is reachable in this sandbox. Every number they emit is a re-derivation from the pinned checkout
`426a23544`; where they print an `ORACLE` line, that value is quoted from a **committed T23
observation** and is labelled as such.

| File | What it is |
|---|---|
| `t26_rederive.py` | From-scratch model of the progressive schedule at `(19, HALF_UP)`: rate factor with the significant-digit / decimal-place double reading (`:1950-1963`), exact `1 + rateFactor` (`RepaymentPeriod.java:216-218`), the `fn` recurrence (`:1822-1828`, `:1991-1993`), the EMI (`:1838-1841`), the interest-first/principal-balancing split, the final-period residual (`:1160-1219`), **and the re-adjust loop** (`:1258-1308`). Every rule carries its source citation. Reproduces both committed T23 observations exactly, and only with the loop. |
| `t26_variants.py` | Runs the same shapes under three alternative loop bodies, each consistent with everything revision 3 *says*, and prints the money each returns. |
| `t26_scan.py` | Sweeps 24,000 in-graded-domain shapes; counts guard firings (2,855) and disagreements between the source-faithful body and the alternatives (V1: 2,156; V2: 699). |

Reproduce with `cd .softhouse/reviews/t26-probe && python3 t26_rederive.py` (then `t26_variants.py`,
`t26_scan.py`). Pure Python `decimal`; no dependencies, no network, no oracle.

**Honest limit on these artefacts:** they establish what the **source** does. They are not vectors
and must never be promoted to the vector store.

---

## 7. Items that NEED a fresh oracle observation

Recorded for the next oracle-reaching fire. None of them blocks fixing P0-T26-1, which is settled by
source alone.

1. **(c) A discriminating vector that trips the EMI re-adjust guard inside the graded domain**
   (ADR §8 item 3). Ready-made candidates from the ten committed T23 cases: **MNT 1,014,632 / 6 × 7.0 %**
   and **MNT 127,704 / 36 × 16.8 %**.
2. **(c) A vector that separates the loop's *adoption test* from its absence.** This is a new
   requirement from this review and the more important of the two: the two committed observations do
   **not** discriminate V0 from V1 — my re-derivation shows both bodies agree on those exact shapes.
   A case where they diverge is needed to confirm empirically the body I re-derived from source.
   First such shape found by `t26_scan.py`: **MNT 100,025 / 12 × 16.8 %**, schedule start 2024-01-01
   (source-faithful body → level `9,113.26`, final `9,113.33`; adoption-test-omitted → `9,113.27`,
   `9,113.20`).
3. **(c) Promotion of the eleven `(19, HALF_UP)` captures to the vector store** (ADR §8 item 1) —
   attestation block, the three missing per-period columns, committed run recipe. Unchanged by this
   review, and still a precondition on any production-parity claim.
4. **(c) `DayCountActualActual` vectors and an independent re-derivation of the cross-year
   partial-period arm** (`:1505-1507`, `:1526-1531`) — ADR §8 item 5. P1-T26-1 raises its priority:
   revision 3's only `FrequencyYears` evidence (Q3b) came from that un-re-derived arm.

**Not** needing an observation, contrary to how they might read: P1-T26-1 (settled from source,
above), P1-T26-3 (settleable from the already-committed capture files), and P0-T26-1 itself.

---

## 8. Should ratification wait on capturing vectors that trip the EMI guard?

**My view: NO — and the driver should not treat the missing capture as a ratification blocker.**
Fix P0-T26-1 and ratify. Reasoning, since this is a judgement call:

1. **It would collapse the contract's own central structure.** §3.1 makes the graded domain the thing
   that *grows as vectors land, with no amendment*, and §1 makes ratification a freeze of **shape and
   normative semantics**. A capture is evidence, not shape. Gating the freeze on evidence erases the
   distinction the whole document is organised around, and would equally imply DEC-1 cannot be
   ratified until `DayCountActualActual`, down payments, `HALF_EVEN` and the installment multiple are
   all captured — i.e. never.
2. **No cloud fire has reached a live oracle.** Waiting parks Tier 0 indefinitely on an unreachable
   resource. The program's own stop conditions say analysis and specification work continues while
   the oracle is unreachable; this is exactly that case.
3. **The specification, unlike the capture, must precede the freeze.** After ratification, correcting
   §4.3 costs a `user` gate. That asymmetry is the whole argument for fixing P0-T26-1 *now* — and it
   needs no oracle, as §6 demonstrates.
4. **But the corpus gap must be converted into a hard conformance precondition, not left as a wish.**
   Revision 3 concedes that no capture can currently grade the loop. I recommend the driver record —
   in ADR §8 item 3 and/or `.softhouse/gates-proposed-answers.md` — that **no conformance PASS may be
   claimed for `loanschedule`, and no cutover may be proposed, until at least one admissible vector
   trips the EMI re-adjust guard inside the graded domain, and at least one separates the adoption
   test.** That is a UAT/cutover gate, where it belongs, not a ratification gate. Cutover is a hard
   `user` gate anyway, so nothing unsafe is enabled by ratifying first.

In short: **the missing vector is a reason to keep the refusal discipline and to bind the conformance
gate — it is not a reason to keep the contract unfrozen. The missing *specification* is.**

---

## 9. Required changes

### P0 — blocks ratification (1)

**P0-T26-1.** Specify the EMI re-adjust loop's **effect**, normatively, in ADR §4.3 **and** in
`contract.go` (`Period` doc, alongside the guard at `:984-1028`): the adjustment magnitude
`emiDifference ÷ max(1, n − uncountablePeriods)` and its rounding (`Money.dividedBy(long)`,
`Money.java:352-358` — mc division then currency-scale rounding under `Rounding.Mode`);
`uncountablePeriods` (`ProgressiveEMICalculator.java:2027-2031`, zero on a fresh schedule);
`adjustedEmi = penultimateEMI + adjustment` (`EmiAdjustment.java:42-44`); the break when the
multiple-rounded adjusted EMI equals the original (`:1270-1273`); the apply-to-all-related-periods
and recompute-residual step (`:1279-1288`); the adoption test `|newDiff| < |oldDiff|`, otherwise
discard and stop (`:1289-1291`, `EmiAdjustment.java:46-48`); the three-iteration cap (`:1307-1308`);
and the guard conjuncts `floor(n/2) > 0` and `emiDifference ≠ 0` plus the `n == 1` degenerate
`EmiAdjustment` (`EmiAdjustment.java:33-34`, `ProgressiveEMICalculator.java:1788`). All in exact
integer arithmetic. Reference model: `.softhouse/reviews/t26-probe/t26_rederive.py::readjust_loop`.

### P1 — fix, none blocks the freeze (3)

- **P1-T26-1.** ADR line 381 / `contract.go:245-247`: neither ACTUAL arm reaches `:1602-1610`; for an
  annual period it is the cross-year partial-period arm `:1505-1507 → :1526-1531` that runs, not
  `:1534-1535`. Currently contradicts `contract.go:317-319`.
- **P1-T26-2.** ADR §8 item 7 line 488: split the citation — `Money.java:134-148` are harness traps;
  `:220-222` is on the live re-adjust path and revision 3 now says so elsewhere.
- **P1-T26-3.** "Seventeen per-period divergences" → eighteen, at ADR lines 200 and 421 and
  `contract.go:471` (T23 P1-1, carried).

### P2 — housekeeping (2)

- **P2-T26-1.** Align the graded-domain block between ADR §3.1 and `contract.go:628-640`
  (`NumberOfRepayments >= 1`), and decide its sentinel.
- **P2-T26-2.** Replace §4.1 line 210's weak calibration inference with the source argument
  (§4 above).

Also still open from T23 and untouched by revision 3, correctly scoped out by T24 and re-affirmed
here as non-blocking: T23 P1-3 (a stated mechanism for *recording* a graded-domain widening — without
it "widening is not an amendment" is an unbounded licence, and this reviewer thinks it should be
closed soon after ratification) and T23 P1-4 (Path-B `interestCalculationPeriodMethod`).

---

## 10. Summary for the driver

- **VERDICT: ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable.** P-2 is not satisfied.
- **P0 outstanding: 1** — the EMI re-adjust loop's effect is unspecified, so two conforming
  implementations return different money on roughly one in eight in-graded-domain loans, and the
  corpus cannot detect it.
- **T23's three P0s:** P0-2 and P0-3 fully resolved; P0-1 correct in everything it asserts but
  incomplete in what it omits.
- **The fix needs no oracle.** It is source re-derivation, supplied in §1.5 and §9 with a working
  reference model. This is a short, mechanical task — plausibly one more revision (T27-class) and one
  more independent review.
- **Do not wait on vectors to ratify** (§8) — but bind the conformance/cutover gate to them.
