# DEC-1 — Schedule-generator adapter contract

**Status: DRAFT (revision 3) — awaiting independent re-review, then ratification**

| | |
|---|---|
| Decision id | DEC-1 |
| Bounded context | `loanschedule` (loan repayment schedule generation) |
| Run | `2026-08-17-run1-harness-schedule-poc`, task T24 (revision 3; revision 2 was T4 attempt 2) |
| Artefact specified | `nexus/internal/apps/loanschedule/contract/contract.go` |
| Reference oracle | Fineract, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
| Supersedes | DEC-1 revision 2 (ACCEPTED WITH REQUIRED CHANGES by re-review T23), which superseded revision 1 (rejected by review T5) |

**Terminology.** In this document "the reference oracle" always means **the Fineract reference implementation** at the pinned commit — the implementation this program grades Go output against. It never means **Oracle Database**, which is a prohibited product in this program.

**Every `file:line` citation in this document is to that pinned checkout, and every citation naming the schedule algorithm is to the PROGRESSIVE generator (`fineract-progressive-loan/…`), never the cumulative one.** A bare `` `:N-M` `` always inherits the file named immediately before it; where revision 2 left five such citations inheriting the wrong antecedent, revision 3 names the file explicitly. Every numeric figure is either an observed capture from the pinned oracle (labelled *observed*) or a re-derivation from source that is shown (labelled *re-derived*). Nothing is asserted from memory.

**What revision 3 changed, and why.** Independent re-review T23 (`.softhouse/reviews/T23-DEC-1-v2-rereview.md`) accepted revision 2's structure, verified all 101 distinct source citations, and reproduced eight of the twelve captures from scratch — but found three normative statements that observation contradicts. Revision 3 corrects exactly those three (§4.3 and §9 on the EMI re-adjust loop; §3.1/§4.6 on the disbursement window; §4.10 on `FrequencyYears`), adds the two rules their correction requires (the error-precedence rule, §4.12; the graded-domain widening mechanism, §5.1), and applies T23's seven P1 corrections. New observations taken for revision 3 are in `.softhouse/reviews/t24-probe/`; the re-derivation that proves the corrected §4.3 is `t24_rederive_with_loop.py`.

---

## 1. What ratification means, and what changing it later means

**Ratifying this ADR is a decision the driver may take** once it passes an independent review with no rejection-grade findings (standing policy **P-2**, `.softhouse/gates-proposed-answers.md`). The driver records the rationale and proceeds; Buyan may reverse it at any time before cutover.

**Amending a RATIFIED DEC-n is not an agent's call.** Once this document is ratified, adding, removing, renaming, retyping or re-documenting any identifier in `contract.go`, or changing any behaviour its doc comments specify, requires raising a gate. Three reasons, each with teeth:

1. **The contract is the strangler boundary.** Every call site in Gerege Nexus that needs a repayment schedule depends on `contract.ScheduleGenerator` and on nothing else. Both implementations are written to this shape; a change to the shape is a simultaneous change to two implementations and every caller.
2. **The contract is the golden-vector encoding.** Each captured vector is a `GenerateRequest` and its oracle-produced `Schedule`. A field added, removed, renamed or retyped invalidates the corpus, and every parity claim already made is void until re-capture.
3. **The contract is what a regulator is shown.** The parity argument for FRC / parallel-run sign-off is "these two implementations answer the same question identically". That argument is auditable only if the question stopped moving.

**Widening the graded domain (§3) is NOT an amendment.** It is behaviour, not shape: no type changes, no vector's field set moves, no ratified sentence is contradicted. This distinction is the single most important structural decision in this revision, and §3 exists to make it precise. Re-review T23 attacked it and confirmed it holds: widening admits a value the frozen types already accept, so none of the three triggers above fires, and a vector captured before a widening remains a legal encoding after it. **Because the licence is real, it needs a procedure**, and revision 2 had none — §5.1 supplies it. A widening recorded any other way is not a widening; it is an undocumented change to what the port is allowed to answer.

**Unchanged and untouched by ratification:** cutover from Fineract to Go, regulatory / parallel-run sign-off, and licence facts remain hard `user` gates. A conformance PASS means "matches the reference oracle on captured vectors, inside the graded domain". It never means "safe to cut over".

---

## 2. Context

The migration ports Fineract to Go one bounded context at a time behind a frozen adapter contract. The first context is loan repayment schedule generation, whose Fineract implementation is the progressive-loan schedule generator, entered through a Spring-free embeddable seam of roughly 182 lines.

The reference oracle's own entry point is:

```java
LoanSchedulePlan generate(MathContext mc, LoanRepaymentScheduleModelData modelData)
```

— a 19-component input record [`LoanRepaymentScheduleModelData.java:32-39`] and a plan carrying a heterogeneous list of disbursement / down-payment / repayment rows plus **seven** aggregate `BigDecimal` totals [`LoanSchedulePlan.java:34-43`: `periods`, `currency`, `loanTermInDays`, then `totalDisbursedAmount`, `totalPrincipalAmount`, `totalInterestAmount`, `totalFeeAmount`, `totalPenaltyAmount`, `totalRepaymentAmount`, `totalOutstandingAmount` — **ten members in all**; revision 2 said eight totals and eleven members, and both were one too many]. That signature is unusable as a migration boundary as it stands:

- **`MathContext`** is a Java type. What it carries is a real input to the answer; the class is not portable — and, as §4.1 shows, its single integer is consumed in two different senses.
- **`BigDecimal` principal and a percentage-shaped `BigDecimal` rate** are the oracle's money and rate representations. This program's non-negotiable is integer minor units and no floating point anywhere on a money path, including intermediates.
- **`CurrencyData`, `DaysInMonthType`, `DaysInYearType`, `DaysInYearCustomStrategyType`, `InterestMethod`, `PeriodFrequencyType`** are Fineract types and enum names.
- **Six components are behaviour switches or overrides** rather than loan terms; they must be pinned, and *why* each is safe to pin is load-bearing (§4.4).
- **Seven aggregate totals in the response**, every one a sum or a span over the period rows.
- **No time zone anywhere**, only bare `LocalDate`.

### 2.1 The behavioural facts the contract must accommodate

All established against the pinned checkout and re-derived independently at least twice:

- The level installment is produced by a **recurrence** — `fn₁ = 1`, `fnₖ = 1 + fnₖ₋₁ × (1 + rateFactorₖ)` [`ProgressiveEMICalculator.java:1822-1828`, `:1991-1993`] — not by the closed-form annuity formula. The recurrence exists so per-period rate factors may differ (interest pauses, rate changes), so the contract must not assume one constant per-period rate. The installment is then `Π(1+rateFactor) × balance ÷ fn` [`:1816-1820`, `:1838-1841`].
- Intermediates are exact decimals rounded to a caller-supplied significant-digit count under a caller-supplied tie rule; **and the per-period rate factor is additionally quantized to that same integer read as a decimal-place count** [`:1959-1962`]. Currency-scale rounding happens where a quantity becomes money [`Money.java:40-53`].
- The addition `1 + rateFactor` is **exact** — performed with no `MathContext` at all [`RepaymentPeriod.java:216-218`].
- The default day count is a **fixed 30/360** with an actual/actual arm also present [`ProgressiveEMICalculator.java:1533-1539`].
- Per period, **interest is computed first and capped at the installment; principal is the balancing non-negative remainder** [`RepaymentPeriod.java:272-286`, `:345-350`].
- **The last period absorbs the entire accumulated residual onto its installment** (§4.3), which is what forces total principal repaid to equal total principal advanced to the minor unit.
- **A bounded EMI re-adjust loop then runs on EVERY generation** and, when its guard trips, moves the level installment by one minor unit and re-splits every period [`ProgressiveEMICalculator.java:1258-1308`, called unconditionally at `ProgressiveEMICalculator.java:749`]. Revision 2 called it reachable only outside the graded domain; that was **false**, and §4.3 now specifies it. It is the last step of the algorithm, not an optional smoothing.

### 2.2 The fact that shaped this revision: the capture seam honours 17 of 19 components

The embeddable seam assembles the oracle's terms object exclusively through a Builder [`LoanApplicationTerms.java:579-607`]. Two of the record's 19 components never survive that assembly:

| Dropped component | Mechanism (verified in this checkout) |
|---|---|
| `installmentAmountInMultiplesOf` | The field exists [`LoanApplicationTerms.java:217`] but the `Builder` has **no setter for it at all**; the only assignment is in a positional constructor [`:828`] this path never reaches. Structurally unreachable, not merely unset. |
| `daysInYearCustomStrategy` | Worse, because it *looks* wired: `assembleFrom` calls `.daysInYearCustomStrategy(...)` [`:604`], and the `Builder` stores it [`:380`, setter `:567-568`] — but the private `LoanApplicationTerms(Builder)` copy constructor [`:304-351`] **never copies it out**. The only assignment in the class is at `:881`, in a positional constructor. A hand-maintained builder copy with one silently skipped entry. |

*Observed*, reflectively, at the production `MathContext` (19, HALF_UP): feeding the record `installmentAmountInMultiplesOf = 999` and `daysInYearCustomStrategy = FULL_LEAP_YEAR` yields `terms.getInstallmentAmountInMultiplesOf() = null` and `toLoanConfigurationDetails().getDaysInYearCustomStrategy() = null`. *Observed*, differentially, at the same setting: `null` versus `100`, and `null` versus `100000`, on an MNT 50,000,000 / 36 × 16.8 % loan produce **identical** schedules, as do `null` versus `FULL_LEAP_YEAR` and `null` versus `FEB_29_PERIOD_ONLY`.

**Consequence, and it is the reason revision 1 was rejected:** for those two inputs the seam-captured corpus has **zero discriminating power**. A Go port that honours them and one that ignores them score identically. A contract frozen in a form that assumes "vectors pass" implies "the contract is covered" would be frozen around a hole.

This revision closes the hole structurally rather than by wishing it away — see §3.

---

## 3. Decision

Adopt the Go package `github.com/gerege/nexus/internal/apps/loanschedule/contract` as the frozen adapter contract for the `loanschedule` bounded context. Its whole surface is:

```go
type ScheduleGenerator interface {
    Generate(ctx context.Context, req GenerateRequest) (Schedule, error)
}
```

with request types `GenerateRequest`, `Currency`, `Rounding`, `Disbursement`, `Rate`, `CivilDate`; the enums `RepaymentFrequencyUnit`, `DayCountConvention`, `InterestMethod`, `RoundingMode`; response types `Schedule`, `Period`, `PeriodKind`; and three sentinel errors.

**Thirteen request fields, seven response fields per row, one response field at the top level.** Nineteen oracle inputs and eleven oracle response members reduce to that, and the reduction is justified component by component in §4.

### 3.1 Two domains, and why the distinction is the decision

| | |
|---|---|
| **Contract domain** | Every value the types admit as well formed. **Frozen by ratification.** |
| **Graded domain** | The strict subset for which a capture exists that can tell a correct implementation from an incorrect one. **Grows as vectors land, with no amendment.** |

A value inside the contract domain but outside the graded domain is **refused with `ErrNoDiscriminatingVector`** — never silently accepted, never silently dropped. This is the standing G-1 disposition: *expose the input, specify the server's semantics normatively, and refuse rather than guess.* An explicit refusal converts a silent wrong answer into a loud missing feature; the failure this program exists to prevent is a port that passes its corpus and is wrong.

**The Run-1 graded domain** (also stated normatively on `GenerateRequest`):

```
Currency.MinorUnitDigits         == 2
Rounding.SignificantDigits       == 19
Rounding.RateFactorScale         == 19
Rounding.Mode                    == RoundingHalfUp
len(Disbursements)               == 1
RepaymentEvery                   == 1
RepaymentFrequencyUnit           == FrequencyMonths
InterestMethod                   == InterestMethodDecliningBalance
DayCount                         == DayCountFixed30Over360
DownPaymentPercentage            == Rate{0, 1}
InstallmentRoundingMultipleMinor == 0
Disbursements[0].Date            is ScheduleStartDate, or one of the computed
                                 repayment due dates other than the last
```

Rates, principals, terms and dates are continuous or unbounded; a corpus cannot enumerate them, so they are graded by **sampling**, and §5 lists what is sampled. **No claim is made that an un-sampled value is safe** — §4.1 records why loan size in particular licenses nothing.

**Two constraints of the CONTRACT domain — refusals that a vector cannot retire.** These are `ErrUnsupportedConfiguration`, not `ErrNoDiscriminatingVector`, because capturing a vector would not make them admissible; only a decision would (§4.12):

```
ScheduleStartDate ≤ Disbursements[0].Date < the last computed repayment due date   (§4.6)
RepaymentFrequencyUnit != FrequencyYears while DayCount == DayCountFixed30Over360  (§4.10)
```

The disbursement-window constraint is the last one added, and §4.6 shows the observation that forced it: outside that half-open window the Run-1 oracle binding **silently discards the principal** and returns an all-zero schedule.

### 3.2 The structural result that makes this contract capturable

The two components the seam drops are **exactly the two the graded domain pins to their inert values**:

- `installmentAmountInMultiplesOf` ← pinned by `InstallmentRoundingMultipleMinor == 0`;
- `daysInYearCustomStrategy` ← pinned `null`, and **provably inert** under `DayCountFixed30Over360` (§4.4).

**Therefore, inside the graded domain, the two dropped components are not a blind spot:** each is pinned to the value the seam forces, so an admissible request is rendered to the oracle without loss, and no answer depends on a component the seam silently discarded. That is what licenses freezing this contract on a seam-captured corpus.

**That is all it licenses, and revision 2 claimed more.** Revision 2 concluded that "a Path-A capture grades everything the request carries". Faithful rendering is not full grading, and re-review T23 broke the inference twice, both times by observation:

- **Rendered but not graded.** The EMI re-adjust loop [`ProgressiveEMICalculator.java:1258-1308`] moves money on ordinary graded-domain requests and **no capture in the Run-1 corpus trips its guard** — *observed*: all nine in-scope `(19, HALF_UP)` captures exit the loop at its first test. A port that omitted the loop entirely would have scored a clean corpus. §4.3 now specifies the loop, and §5 records vectors that discriminate it.
- **Rendered but answered degenerately.** A request can be rendered perfectly and still get an answer that amortizes nothing, because the *generator* discards a disbursement outside the period windows. §4.6.

So the corpus is not dense enough to grade its own graded domain by construction; it is dense enough only where a vector exists that would fail a wrong implementation, and §5 states that field by field.

It also states the price precisely: **widening the graded domain to a non-zero installment multiple requires re-binding the Fineract-JVM adapter to the running-server path** (which does honour the field) *and* capturing there. That is a scheduling fact, not a contract change.

### 3.3 Design rules applied

A field is in the contract if and only if:

1. it changes the numeric answer, **and**
2. it is a property of the loan being scheduled — not of the implementation computing it, not of a neighbouring bounded context, **and**
3. both implementations consume it, **and**
4. it cannot be recomputed from the other fields — with one stated exception, `OutstandingPrincipalMinor` (§4.5).

`TimeZone` is a deliberate, argued exception to (1): it changes no number here, and is carried so that no caller can smuggle an implicit offset across the boundary (§4.2).

Where evolution was foreseeable and cheap, the contract prefers **widening a value domain over changing a shape**: an enum gains a member, a slice gains a legal cardinality. Both are still gated changes, but neither invalidates the struct layout, the wire encoding or a vector's field set.

---

## 4. The load-bearing decisions

### 4.1 Rounding: two integers, one mode — because the oracle reads one integer two ways

`Rounding` carries `SignificantDigits`, `RateFactorScale` and `Mode`.

**The defect this replaces.** Revision 1 carried one field, `IntermediatePrecisionDigits`, documented as "significant decimal digits". The oracle threads one `MathContext` and consumes it in **two incompatible senses** [`ProgressiveEMICalculator.java:1950-1963`]:

```java
final BigDecimal interestFractionPerPeriod = repaymentPeriodMultiplierInDays
        .multiply(repaymentEvery, mc)
        .divide(daysInYear, mc);
return interestRate
        .multiply(interestFractionPerPeriod, mc)
        .multiply(actualDaysInPeriod, mc)
        .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
```

The four `mc`-qualified operations round to **significant digits**; the trailing `setScale(mc.getPrecision(), …)` quantizes to **decimal places**. `setScale` takes a scale, not a precision. The same pattern appears once more, on the cross-year partial-period arm [`:1976-1979`]. These are the only two occurrences in Fineract main code, and both are rate-factor computations.

**Re-derived**, at `SignificantDigits` 12 / HALF_UP, 7 % p.a., 30/360, a 31-day period:

```
interestFractionPerPeriod = 30 × 1 ÷ 360           = 0.0833333333333
0.07 × 0.0833333333333                             = 0.00583333333333
     × 31                                          = 0.180833333333
     ÷ 31                                          = 0.00583333333332   ← 14 dp, 12 significant digits
setScale(12, HALF_UP)                              = 0.005833333333     ← 12 dp, 10 significant digits
```

Because a rate factor is of order 0.005–0.02, a *scale* is strictly lossier than the same count of *significant digits* on this quantity: the leading zeros buy nothing. The two readings are not a fixed offset apart — they have different **shape**. Without the quantization the six periods of that schedule carry three distinct rate factors tracking 31/29/30-day months; with it they collapse to one.

**Why it matters in money.** An implementation applying only the significant-digit sense still passes the oracle's shipped conformance vector — a 100.00 principal absorbs the difference at the currency layer — and then misprices ordinary loans. The corpus could not detect that class of defect at all until a discriminating capture existed; it now does.

**Observed**, on the pinned oracle, 18 monthly installments at 18.5 % p.a. on principal 87,654,321 major units, HALF_UP:

| | period 5 principal | period 5 interest | period 5 outstanding | total interest |
|---|---|---|---|---|
| `SignificantDigits` 12 | 4,531,420.**25** | 1,082,346.**53** | 65,674,840.**83** | 13,393,481.**05** |
| `SignificantDigits` 19 | 4,531,420.**26** | 1,082,346.**52** | 65,674,840.**82** | 13,393,481.**04** |

Seventeen per-period divergences, never healing.

**The equality constraint.** The oracle derives both senses from one integer, so `RateFactorScale` **must equal** `SignificantDigits`; a request where they differ describes a configuration no deployment can produce and is `ErrUnsupportedConfiguration`. Two fields rather than one is therefore not new configuration surface — it is a naming decision: one integer with two documented meanings is precisely the ambiguity that cost a minor unit, and a captured vector must echo both so it can never be replayed under a policy it was not captured at.

**The production value is 19 and it is not a choice.** `MoneyHelper.PRECISION` is the compile-time constant 19 [`MoneyHelper.java:35`] and `getMathContext()` returns `new MathContext(19, tenantRoundingMode)` [`:91-93`]. Only the mode is tenant-configurable, and Gerege's ratified mode is `HALF_UP` (Fineract ordinal 4). **The production `MathContext` is `(19, HALF_UP)`**, and any prose implying precision is tenant-configurable is wrong. A capture at 12 is a rig calibration and can never be a parity vector.

**There is no size threshold.** *Observed*: the oracle's own 12-vs-19 pair diverges at a principal of **4.00** on a 36-period 16.8 % shape and is **identical** at 50,000,000 on that same shape and at 87,654,321 on a 6-period 7.0 % shape. Sensitivity is a rounding-boundary property of the `(principal, term, rate)` triple, not a magnitude property of the principal. All four MNT captures in the corpus are 12/19-identical, so nothing in the corpus shows Mongolian sizes are precision-sensitive either. **Any implementation shortcut justified by loan size is unfounded.**

**One mode, not three.** The oracle takes every tie rule from one of two places — the threaded `MathContext` where one is passed, and the tenant-global one where one is not [`Money.java:52`; `:102-104`; `:150-157`; `:159-161` and `:163-170`, whose return path goes through the two-argument `Money.of` and therefore reads tenant-global state even though its own division used the threaded context]. Independently settable modes would admit combinations no deployment can produce.

**Adapter obligation, widened.** The Fineract-JVM adapter must initialise the tenant rounding mode to `Rounding.Mode` before **every** call — not only when an installment multiple is set. *Every* path that constructs `Money` without an explicit `MathContext` reads the tenant-global context, and outside an initialised tenant those paths throw `IllegalStateException` [`MoneyHelper.java:74-82`]. The tenant **precision** cannot be pinned the same way; within the graded domain that is harmless, and the evidence is direct rather than assumed: the calibration capture ran with a threaded precision of 12 while the ambient tenant context was 19 and still reproduced the oracle's shipped conformance literal exactly, so no reached call site consulted the tenant-global precision.

**Mode value domain.** `RoundingHalfUp` (ratified, and the only mode in the graded domain) and `RoundingHalfEven` (the oracle's stock configuration default, so a deployment inheriting it must be expressible). The mode is demonstrably live, not a dead knob: *observed*, the same request put to two tenants of one running oracle differing only in rounding mode returned period-1 interest **20,925.05** under HALF_UP and **20,925.04** under HALF_EVEN on principal MNT 1,162,502.50, the tie taken at `Money.java:52`. The remaining five Java modes are not admitted; each would be surface carrying an unproven claim.

### 4.2 Dates: civil dates, one named zone, and a month-end rule anchored to the disbursement

`CivilDate{Year, Month, Day}` — proleptic Gregorian, no time, no offset, no instant — plus one IANA `TimeZone` name on the request. Not `time.Time` (carries a location and an instant, either of which reintroduces a midnight-boundary bug); not a date string (parsing is a second place to disagree); **never a fixed offset**, because an offset literal encodes a fact about a zone into a field that should name the zone.

**Why `TimeZone` exists at all**, given that it changes no number here. The generation arithmetic is zone-free civil-date arithmetic, and no capture can discriminate the field — *observed*: four server-path captures re-taken on a tenant whose zone was changed to `Asia/Ulaanbaatar` came back byte-identical, because every date in them is an explicit civil date. It is carried anyway so that no caller can smuggle an implicit offset across the boundary, and so downstream contexts (aging, COB, delinquency) inherit an explicit zone rather than guessing one. Gerege operates in two zones — `Asia/Ulaanbaatar` (UTC+08) and `Asia/Hovd` (UTC+07), neither observing DST — and that equivalence will **not** hold for any later operation that depends on "today"; for those, both zones must be exercised before capture.

**The month-end rule (normative, monthly only), corrected.** Revision 1 stated it backwards and attached it to the wrong field. The rule is two steps:

1. **Step**: add `RepaymentEvery` calendar months to the previous boundary, clamping the day to the target month's length [`DefaultScheduledDateGenerator.java:128-129`, `:311-333`].
2. **Re-anchor**: if the frequency is monthly **and the SEED day-of-month > 28 and the stepped date's day ≥ 28**, set the day to `min(days in target month, seed day)` [`:168-176`, called at `:130-131`]:

```java
if (frequencyType.isMonthly() && seedDate.get(ChronoField.DAY_OF_MONTH) > 28 && date.get(ChronoField.DAY_OF_MONTH) >= 28) {
    int noOfDaysInCurrentMonth = YearMonth.from(date).lengthOfMonth();
    int seedDay = seedDate.get(ChronoField.DAY_OF_MONTH);
    int adjustedDay = Math.min(noOfDaysInCurrentMonth, seedDay);
    return date.with(ChronoField.DAY_OF_MONTH, adjustedDay);
}
```

**The clamped day IS remembered — in the seed — and the seed is the DISBURSEMENT DATE, not `ScheduleStartDate`** [`LoanApplicationTerms.java:583-589`]. The rule is therefore documented on `Disbursement.Date`.

*Observed*, 6 monthly periods, 100.00 at 7 % p.a., seed = schedule start:

| seed | due dates | term |
|---|---|---|
| 2024-01-31 | 02-29, **03-31**, 04-30, **05-31**, 06-30, **07-31** | **182 days** |
| 2024-01-30 | 02-29, 03-30, 04-30, 05-30, 06-30, 07-30 | **182 days** |

Revision 1's text ("the clamped day is not remembered") yields 2024-03-29 for the second period of the first schedule and a 180-day term — wrong on every date after the first. Month-end disbursement is routine in retail lending.

**`ScheduleStartDate` is a separate input and the separation is real.** It becomes the schedule generation start [`ProgressiveLoanScheduleGenerator.java:94-96`; the seam never sets a repayment-start-date type], while the disbursement date becomes the month-end seed. It is also the anchor for the loan term, which the oracle measures as the span from the first period's from-date to the last period's due date — so a loan disbursed after its schedule starts still reports a term measured from the schedule start. *Observed*: schedule start 2024-01-01, disbursement 2024-02-01, six monthly periods, term **182 days**, first repayment row entirely zero.

### 4.3 The final-period residual, defined rather than named

Revision 1 said the last period "absorbs the whole accumulated rounding residual" and never defined it. Two implementers could equally read that as "make the final balance exactly zero" or "make Σ principal equal principal advanced"; those coincide on the shipped vector and are not identical in general, because the algorithm clamps negatives at two points [`RepaymentPeriod.java:348`, `:399`].

**The rule** [`ProgressiveEMICalculator.java:1160-1219`, `diff` at `:1202-1203`, applied at `:1205`, stored at `:1210`]:

```
diff        = Σ disbursed + Σ capitalizedIncome + creditedPrincipal + Σ dueInterest − Σ installments
lastEmi    ← lastEmi + diff
```

with every Σ accumulated **at currency scale** (each term is already money) rather than at `SignificantDigits`, and the target being the last not-fully-paid period — on a freshly generated schedule, simply the last one [`:1176-1181`]. The period's principal then falls out as installment − interest [`RepaymentPeriod.java:345-350`].

It is emphatically **not** "the last principal is whatever balance remains". `diff` is **signed**: *observed* −0.01 on the shipped 100.00 / 6 × 7 % schedule (final installment 17.01 → **17.00**), and *observed* +0.03 on a 12 × 21.6 % MNT 1,200,000 schedule (112,082.37 → 112,082.40).

Revision 1's phrase "final **unpaid** period" was also a dangling term: this contract has no notion of payment. The Go artefact says "the last period".

**A second smoothing pass exists and is unpinned.** `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` [`:1258-1308`, at most three iterations, gated on `EmiAdjustment.shouldBeAdjusted` at `EmiAdjustment.java:31-36`] re-rounds an adjusted installment and adopts it if the last-vs-penultimate gap shrinks. It fires on none of the twelve Run-1 captures, but it **does** fire on nearby inputs, and it can absorb an installment-multiple rounding difference entirely — *observed* converging two different rounding modes to one identical schedule. It is named here because an implementation that implements the multiple-rounding but not this loop will diverge; it is reachable only outside the graded domain, and a vector that forces it to iterate is backlogged (§8).

### 4.4 The six pinned oracle inputs, each with the reason it is safe

This table is **normative**: it is what makes the adapter fully determined by the contract, and it is a conformance obligation on the Go module to behave as if these constants held. Revision 1 got two of the reasons wrong; the reasons matter, because a future reader will use them to decide whether a pin can be relaxed.

| Oracle input | Pinned to | Why it is not a contract field, and why the pin is safe |
|---|---|---|
| `allowFullTermForTranche` | `false` | **A real behavioural pin, not a dead field** (revision 1 said "no builder setter reaches it" — false). The setter is reached [`LoanApplicationTerms.java:606`, copied out at `:348`] and the guard consuming it never consults multi-disbursement: `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` [`ProgressiveEMICalculator.java:142-144`]. `true` routes into a full re-amortization through a synthetic terms object and a temporary schedule model [`:155-174`]. Fineract forbids the combination only at *product* validation, a layer this entry point does not pass through. **Graded**: two captures differing only in this flag were taken at (19, HALF_UP) and are *observed* identical — a measurement that the alternative path coincides on that shape, not a licence to ignore the flag. |
| `allowPartialPeriodInterestCalculation` | `true` | Inert — but not for the obvious reason (revision 1 said sub-periods coincide with repayment periods). Its only calculation-path uses [`ProgressiveEMICalculator.java:128-133`] sit behind a guard that first requires `interestCalculationPeriodMethod` to be non-null and same-as-repayment-period. That field has no initialiser and is never set by the seam's assembler [`LoanApplicationTerms.java:579-607`], so it is `null` and the branch short-circuits. |
| `interestRecognitionOnDisbursementDate` | `false` | A real switch: it shifts the year-end fraction boundary [`ProgressiveEMICalculator.java:1578-1584`], reachable only on the actual/actual arm, which is outside the graded domain. |
| `fixedLength` | `null` | A real pin: a non-null value overrides the final due date in days [`DefaultScheduledDateGenerator.java:62-65`, `:108-111`, `:184-188`] and interacts ambiguously with `NumberOfRepayments`. Backlogged (§8). |
| `daysInYearCustomStrategy` | `null` | **Provably inert inside the graded domain, twice over.** Its only effect is substituting a 365/366-day year for a period containing 29 February, and that requires the year length to be 366 to begin with [`ProgressiveEMICalculator.java:1346-1352`]; a fixed 360-day year never is. The oracle also rejects the field at product creation unless days-in-year is `ACTUAL` [`LoanProduct.java:462-472`]. It is **not** inert in general — through a running server at a daily interest calculation with an actual/actual year, `FEB_29_PERIOD_ONLY` *observed* moves all twelve periods of a one-year schedule and both totals — so it becomes a contract question the moment `DayCountActualActual` enters the graded domain, and not before. See §4.7 for the further finding that `FULL_LEAP_YEAR` is behaviourally identical to the field being unset. |
| `currency.inMultiplesOf` | `null` | Inert because the oracle applies it only when the currency has **zero** decimal places [`Money.java:48-51`] and MNT has two. *Observed* at zero decimal places it moves money (total interest 763,994 versus 764,100 on an 18 × 18.5 % MNT 5,000,000 loan), which is a second reason `Currency.MinorUnitDigits == 2` is in the graded domain. It is a **different thing** from `InstallmentRoundingMultipleMinor`, which is the loan-product rounding and *is* in the contract. |

Also pinned by omission: `interestCalculationPeriodMethod`, which the seam's assembler never populates. It is not a contract field because the seam cannot express it; if the JVM adapter is ever re-bound to the running-server path (§3.2), whether to expose it becomes a gate.

**Also absent, and never to be added here:** borrower or party identity of any kind — should a party ever be required anywhere in this program, names are three fields, *ovog*, patronymic, given name, never `first_name` / `last_name` — loan or account identifiers, product catalogue references, tenant identifiers, business dates, charges, taxes, ledger accounts, and any notion of insurance, protection or guarantee.

### 4.5 Response shape: derive everything derivable, carry one exception

The oracle's eight aggregate totals, its currency echo, its loan term in days, its per-row total due and its per-row total outstanding are all sums or spans over the rows. Carrying them would create a second source of truth: an implementation could be right about the split and wrong about the sum, and conformance would have to decide which is authoritative. Callers that want a total sum the rows.

Two omissions carry their own argument:

- **No level-installment field.** The installment is `PrincipalMinor + InterestMinor` on any ordinary row. Omitting it is what makes the final-period residual expressible **without loss**: the last row's total simply differs, and there is no separate installment field that could contradict it. *Observed* on the shipped vector: 16.90 + 0.10 = 17.00 ≠ 17.01, and the residual is visible in the split with nothing to disagree with.
- **No per-row fee or penalty.** Charges, rates and taxes are a Tier A bounded context, out of scope here; the oracle's fee and penalty columns are identically zero under the pinned configuration. Named in §6 as the highest forward risk.

`OutstandingPrincipalMinor` is **the one carried-but-arguably-derivable field**, kept because the oracle clamps this roll-forward at zero rather than computing a pure running difference [`RepaymentPeriod.java:389-403`], so the two are not provably identical in every configuration; and because it is the field against which the per-period amortization invariant is checked without summing the whole schedule. *Observed*: it is 0 on a repayment row falling entirely before the disbursement.

**Sign convention.** `PrincipalMinor` is never negative; the direction is carried by `Kind`, never by a sign bit, so no consumer can sum the column without first deciding what it is summing. Same discipline as the ledger non-negotiable.

**Installment numbering.** A dense 1-based counter shared by down-payment and repayment rows — the oracle increments one counter for both [`ProgressiveLoanScheduleGenerator.java:123`, `:143`, `:341`, `:346`] — and `0` on a disbursement row, the one place a Java `null` is normalised, to a value that cannot collide with a real installment.

### 4.6 Ordering: reproduce the oracle's emitted order

**Decided: reproduce it (option a), do not refuse the request.** Fineract is the fallback and the shadow-parity partner; a boundary that refuses an input the oracle accepts cannot be run against the same traffic, and that is what shadow testing *is*. A business restriction, if wanted, belongs in a validation layer in front of both implementations — never inside the parity boundary.

**Revision 1's rule was refuted at a reachable boundary.** It sorted by `DueDate`, then by `Kind` with disbursement first. But the oracle tests disbursement membership against a **half-open** window [`ProgressiveLoanScheduleGenerator.java:307-308`] and emits disbursements at the **top** of each period's iteration while appending that period's repayment row at the **bottom** [`:121` versus `:141`]. A disbursement dated exactly on period *k*'s due date therefore belongs to period *k+1* and is emitted **after** repayment *k*.

*Observed*, schedule start 2024-01-01, disbursement 2024-02-01, six monthly periods at 7 %:

```
repayment 1 (due 2024-02-01, principal 0.00, interest 0.00)
disbursement (2024-02-01, 100.00)
repayment 2 (due 2024-03-01) … repayment 6 (due 2024-07-01)
```

Revision 1's rule puts the disbursement first, and is wrong.

**The corrected rule** assigns each row a **window key**: a repayment row's key is its own `DueDate`; a disbursement or down-payment row's key is the `DueDate` of the repayment period whose half-open window `[FromDate, DueDate)` contains its date, or a key after every repayment row if its date is on or after the last due date. Rows sort by ascending key, then by `Kind` (disbursement, down payment, repayment), then by ascending `InstallmentNumber`, then by ascending row date.

The key is **derivable from the response itself** — the repayment rows carry the windows — so two implementations agree on it without mirroring each other's control flow, which was the property revision 1 claimed and did not have. It reproduces both the observed pre-disbursement case above and the ordinary case where the disbursement opens the schedule.

### 4.7 `InstallmentRoundingMultipleMinor`: exposed, specified truthfully, refused for Run 1

This is the field the standing G-1 disposition was written for, and the field on which the previously recorded rounding rule was **false**.

**The true semantics (normative).** `applyInstallmentAmountInMultiplesOf` [`ProgressiveEMICalculator.java:1761-1766`] → `safeRoundingForEMI` [`:1770-1776`] → `Money.roundToMultiplesOf(Money, Integer)` [`Money.java:159-161`] → [`:163-170`]:

```java
amountScaled = amountScaled.divide(inMultiplesOfValue, 0, mc.getRoundingMode()).multiply(inMultiplesOfValue);
```

- **Round to the NEAREST multiple under the tenant rounding mode.** Not "raise to the next multiple", which is what the prior record said and which would diverge from the oracle on roughly half of all inputs. *Observed* rounding **down** on a running oracle at (19, HALF_UP): principal MNT 1,190,000 with a multiple of 100 major units takes an unrounded installment of **111,148.35** to an applied installment of **111,100.00**.
- **Zero guard**: if rounding would take a positive installment to zero, the *unrounded* installment is used [`:1772-1774`]. The rounding is not unconditional.
- **The last period still absorbs the residual**, so its total is deliberately not a multiple. *Observed*: installments 112,100.00 for periods 1–11 and a final 111,866.22.
- **The tie rule comes from the tenant-global context** (the two-argument overload), which is why §4.1's adapter obligation is stated as widely as it is.
- **The EMI re-adjust loop can absorb the rounding entirely** (§4.3). Unpinned; named.
- **Representable domain**: the oracle's counterpart is an `Integer` count of **MAJOR** units [`LoanRepaymentScheduleModelData.java:36`, consumed at `Money.java:150-157` and `:163-170`], so the value must be `0` or a positive exact multiple of 10^`MinorUnitDigits`. `5000` (50.00 ₮) and `1` (0.01 ₮) have **no** representation the adapter can render and are `ErrUnsupportedConfiguration` rather than silently rounded — the same honesty the `Rate{1,3}` limit gets in §4.8.

**Disposition for Run 1: launch WITHOUT it.** Products ship with no installment rounding; a non-zero value is refused with `ErrNoDiscriminatingVector`. Rounding to whole 100 ₮ is a legitimate Mongolian feature, but the seam this corpus is captured through cannot grade it (§2.2), and shipping it now would mean shipping an unvectored money path. Four server-path captures exist in which a multiple of 100 major units *observed* moves all twelve periods; when those become admissible vectors, the value enters the graded domain **with no amendment**.

**The field stays in the contract regardless**, for two reasons: a contract that cannot express whole-100-₮ installments is wrong for this market; and it changes the value of *every* row, so it could never be layered on later without re-capturing every vector.

**A related finding, recorded so nobody re-litigates it:** on the running-server path `daysInYearCustomStrategy = FULL_LEAP_YEAR` is *observed* **byte-identical** to the field being unset — the enum has no branch for it [`DaysInYearType.java:81-86`; `ProgressiveEMICalculator.java:1346-1352` special-cases only `FEB_29_PERIOD_ONLY`]. Only `FEB_29_PERIOD_ONLY` discriminates, and only under a daily interest calculation with an actual year [`:1510-1516` short-circuits everything else]. Any future work that pairs the two values as symmetric alternatives is wrong.

### 4.8 Rates: exact integer rational, not basis points, not a float

`Rate{Numerator, Denominator}` — a dimensionless fraction in canonical lowest terms, `Denominator > 0`. 7 % p.a. is `Rate{7, 100}`.

- **Not a float.** Non-negotiable, and the oracle has none on the calculation path either; a float rate would diverge after enough compounding periods.
- **Not basis points.** An integer basis-point field cannot express a rate finer than 0.01 % (0.125 % p.a. is 12.5 bp), and a rate is not required to be a whole number of basis points. A rational is exact for every rate the oracle can consume, at the cost of one `int64`. Every rate in the corpus (7.0, 16.8, 18.5, 21.6 %) is expressible either way; the argument is about the rates the contract must not be *unable* to carry later, given that adding a field is a gate.
- **Canonical form is mandatory** so structural equality is value equality — vector comparison and request deduplication are structural. `Rate{}` (0/0) is invalid; a zero rate is exactly `Rate{0, 1}`, consistent with the `Unspecified` enum zero values, so a never-populated request fails loudly instead of silently meaning "0 % declining balance, 30/360, daily".
- **One representable-domain limit, stated rather than hidden.** The adapter must render the rate as the decimal percentage the oracle's record expects, which the oracle divides by 100 under its own policy [`ProgressiveEMICalculator.java:1318-1320`]. A rate whose reduced denominator has a prime factor other than 2 or 5 (`Rate{1, 3}`) has no exact terminating decimal percentage and must be rejected with `ErrUnsupportedConfiguration`.
- **Zero interest** is not special-cased by the algorithm — every rate factor is 0, every growth factor is exactly 1, the recurrence yields exactly the installment count, and the installment is principal ÷ count. It is nonetheless outside the graded domain, because no capture exercises it.

### 4.9 Day count: one enum, with a normative mapping

`DayCountConvention` is **one** field, not the oracle's (days-in-month, days-in-year) pair plus a leap-day override. The mapping is normative, which revision 1 omitted:

| `DayCountConvention` | Oracle pair |
|---|---|
| `DayCountFixed30Over360` | (`DaysInMonthType.DAYS_30`, `DaysInYearType.DAYS_360`) |
| `DayCountActualActual` | (`DaysInMonthType.ACTUAL`, `DaysInYearType.ACTUAL`) |

The pair is load-bearing: it selects between materially different arms [`ProgressiveEMICalculator.java:1533-1539`, plus the cross-year partial-period arm at `:1505-1507` selecting `:1526-1531`, which only `ACTUAL` can reach].

**`DayCountActualActual` stays in the value domain and the computation is refused** — `ErrNoDiscriminatingVector` — until a capture exists. Keeping the member costs nothing (removing it later would be a narrowing and a gate); computing it would mean returning plausible numbers nobody has compared with the oracle, on the one arm of the algorithm no independent re-derivation has yet reproduced from source. Admitting it later is behaviour, not shape — with the one exception named in §4.4: it makes `daysInYearCustomStrategy` live, and *that* is an amendment.

**One consistency result, and it is what lets two different capture seams grade one contract.** For **monthly** repayment, and only monthly, the oracle's 30/360 arm and its same-as-repayment-period arm compute the identical interest fraction: `30 × RepaymentEvery ÷ 360` and `RepaymentEvery ÷ 12` are the same rational evaluated at the same precision [`:1513-1515` versus `:1536` through `:1922-1927`]. *Observed*: a 12-period MNT 1,200,000 loan at 21.6 % captured through the embeddable seam under 30/360 and through a running server under same-as-repayment-period agrees on all twelve periods and all three totals **to the minor unit**. For **weekly** the two arms disagree (`RepaymentEvery ÷ 52` versus `7 × RepaymentEvery ÷ 360`), which is one more reason `FrequencyWeeks` is outside the graded domain.

### 4.10 Repayment frequency: one value the oracle cannot answer

`FrequencyMonths` is graded. `FrequencyDays` and `FrequencyWeeks` are computable but uncaptured → `ErrNoDiscriminatingVector`. **`FrequencyYears` the oracle cannot answer at all**: its per-frequency dispatch handles DAYS, WEEKS and MONTHS and throws `UnsupportedOperationException` for anything else [`ProgressiveEMICalculator.java:1602-1610`]. It is refused with `ErrUnsupportedConfiguration` — not `ErrNoDiscriminatingVector`, because the problem is not a missing vector but a missing answer. It is retained in the enum so an annual product is expressible the day the oracle grows support, and because removing a member is a narrowing.

### 4.11 The error taxonomy is three-valued, and the third value is the point

| Sentinel | Meaning |
|---|---|
| `ErrInvalidRequest` | The request is not well formed. |
| `ErrUnsupportedConfiguration` | Well formed, but this contract does not admit it or the oracle cannot be asked at all. |
| `ErrNoDiscriminatingVector` | Well formed and computable, but outside the **graded domain**. |

`ErrNoDiscriminatingVector` **wraps** `ErrUnsupportedConfiguration`, so `errors.Is(err, ErrUnsupportedConfiguration)` is true and a caller that does not care sees two cases. The distinction records *why* a request was refused, which decides how the refusal is retired: a missing vector is retired by capturing one, which is behaviour and needs no amendment.

---

## 5. The Run-1 corpus this contract is frozen against

Twelve captures from the pinned oracle through the embeddable seam. Eleven at the production `MathContext` `(19, HALF_UP)`; one calibration at `(12, HALF_UP)` which **can never be a parity vector**. All twelve reproduce byte-for-byte on re-run and have been independently re-derived from the pinned source to the minor unit, and six property invariants hold integer-exact on all twelve.

| What the request carries | Graded by | Discriminating evidence |
|---|---|---|
| `Currency.Code` | — | **Not an arithmetic input by construction**: the oracle's currency record reaches the calculation only through decimal places and inMultiplesOf [`Money.java:40-53`]. Corpus covers USD and MNT. |
| `Currency.MinorUnitDigits` | 2 only | No capture varies it. At 0 a second rounding channel switches on [`Money.java:48-51`] and *observed* moves money. |
| `Rounding.SignificantDigits` | 19 | 12-vs-19 pair, 17 divergent periods (§4.1). |
| `Rounding.RateFactorScale` | 19 | Re-derived (§4.1); constrained equal to `SignificantDigits`. No capture can separate them, and none can exist, because the oracle has one integer — which is exactly why the constraint is in the contract. |
| `Rounding.Mode` | HALF_UP | HALF_EVEN *observed* live on a running oracle (20,925.05 vs 20,925.04) but **uncaptured in the corpus** → refused. |
| `ScheduleStartDate` vs `Disbursement.Date` | ✔ | One capture separates them (start 2024-01-01, disbursement 2024-02-01) and pins the ordering rule and the term anchor. |
| Month-end seed rule | ✔ | Two captures, seed day 31 and seed day 30, both spanning a leap February. |
| `Disbursements` cardinality | 1 only | Multi-tranche unreachable from this entry point [`LoanApplicationTerms.java:600`; `ProgressiveLoanScheduleGenerator.java:285-292`]. |
| `NumberOfRepayments` | sampled | 6, 12, 18, 36. |
| `RepaymentEvery` | 1 only | No capture varies it; it enters the interest fraction directly [`:1956-1958`]. |
| `RepaymentFrequencyUnit` | MONTHS only | Every capture is monthly. YEARS throws (§4.10). |
| `AnnualNominalInterestRate` | sampled | 7.0, 16.8, 18.5, 21.6 %. Zero rate uncaptured. |
| `InterestMethod` | DECLINING_BALANCE | The only member. |
| `DayCount` | 30/360 only | All twelve captures. ActualActual refused (§4.9). |
| `DownPaymentPercentage` | 0 only | **No capture has ever produced a down-payment row.** Non-zero refused. |
| `InstallmentRoundingMultipleMinor` | 0 only | **Path A has ZERO discriminating power** (§2.2). Server-path captures exist and are not yet admissible (§4.7). |
| `TimeZone` | — | **Not discriminable by construction** — the arithmetic is zone-free. *Observed*: four server-path captures re-taken on an `Asia/Ulaanbaatar` tenant came back byte-identical. Will not hold for any later operation that depends on "today". |
| pinned `allowFullTermForTranche` | ✔ | Two captures differing only in the flag, at (19, HALF_UP): *observed* identical. |
| pinned `daysInYearCustomStrategy` | provably inert | §4.4. No Path-A capture could ever grade it. |
| pinned `fixedLength`, `interestRecognitionOnDisbursementDate`, `allowPartialPeriodInterestCalculation`, `currency.inMultiplesOf` | pinned | §4.4. |

**Sampled principals**: 100, 1,200,000, 4,999,999, 5,000,000, 50,000,000, 87,654,321 major units, in USD and MNT.

**Two admissibility facts a ratifier should know.** First, the eleven production-setting captures are **audited observations**, not yet vector-store entries: the capture plan's admissibility rules require a machine-readable environment-attestation block, three per-period columns the harness does not yet emit, and a committed run recipe. Nothing here doubts a number — every one reproduces and re-derives — but the promotion is outstanding, and it is capture work, not contract work. Second, the server-path captures were taken on a tenant running HALF_EVEN and are admissible at `(19, HALF_UP)` only on the strength of a fresh-tenant re-observation that returned four identical digests.

---

## 6. Forward-compatibility analysis

Does this contract survive GL/accounting (Tier A), the full loan lifecycle, and charges/rates/tax without a shape change? Ordered by descending risk.

- **6.1 Charges, fees, penalties, tax — the highest unmitigated risk.** The oracle's plan already has fee and penalty columns; when the charges context lands, a repayment row acquires further components. It is acceptable because charges are out of scope here, and because **the response was shaped so the addition is purely additive**: with no total-due column, no existing field's meaning changes when charges arrive. A total-due column would have changed meaning silently — the most dangerous kind of contract change, because it does not break a compile. The likeliest resolution is not amending `Period` at all but composing: charges computed by their own context and applied to a schedule. DEC-1 does not decide that; it does not foreclose it.
- **6.2 Grace periods, interest pauses, mid-term rate changes — real, unmitigated.** The `fn` recurrence exists precisely to support per-period rate factors that differ, so the machinery is there; expressing them needs new request fields, most likely a list of dated term events. Not mitigated speculatively: a wrong guess frozen into the contract is worse than an honest later amendment. `ScheduleStartDate` being independent of the disbursement date already covers the commonest simple case.
- **6.3 Multi-tranche disbursement — mitigated, shape holds.** `Disbursements` is a slice from day one with exactly one legal element. Widening the cardinality is a value-domain change; turning a scalar into a list later would have invalidated the whole corpus. `DownPaymentPercentage` stays a single top-level field under multi-tranche: the oracle computes the down payment per disbursement from one product-level percentage.
- **6.4 A second interest method (flat) — mitigated, shape holds.** An enum member, not a struct change. Without the field the contract would silently mean "declining balance forever" and every vector would be ambiguous about what produced it.
- **6.5 Further day-count conventions — mitigated, with one named exception.** Adding 30/365 or ACT/360 is an enum member. The exception is `DayCountActualActual` activating `daysInYearCustomStrategy`, which needs a field or a member and is therefore an amendment (§4.4, §4.9).
- **6.6 The rounding-mode value domain — low risk.** A mode outside `{HalfUp, HalfEven}` would be a value-domain widening, not a shape change. The production mode is ratified `HALF_UP`, so this is a contingency rather than an expectation.
- **6.7 `interestRecognitionOnDisbursementDate`** — one boolean field if a product ever needs accrual from the disbursement date. Cheap, but a gate. Not added now: a boolean nobody sets is exactly the surface this contract avoids accumulating.
- **6.8 GL and accounting (Tier A) — no risk.** The ledger consumes a schedule; it does not change how one is generated. `Generate` posts nothing and remains pure.
- **6.9 What holds under all of the above.** `Currency`, `Rounding`, `CivilDate`, `TimeZone`, `Rate`, the `int64` minor-unit money representation, the ordering rule, the principal/interest split, and the two-domain structure of §3. None of these is a Fineract artefact and none changes meaning when a neighbouring context arrives.

---

## 7. The switch mechanism (described, not implemented)

**Selection is per bounded context, from deployment configuration, resolved once at process start.**

- **Config key.** One key per bounded context, namespaced: `gerege.contexts.loanschedule.implementation`, value `fineract_jvm` or `go_native`. Per context, never global — the strangler pattern requires contexts to move independently, and a single global switch would make the migration one all-or-nothing step.
- **Default.** Absent configuration resolves to `fineract_jvm` — the reference oracle — never to the Go module. An *unrecognised* value fails startup loudly rather than falling back silently.
- **Resolution.** A registry in the composition root maps the config value to an implementation and returns it as a `contract.ScheduleGenerator`. Resolution happens once, at startup, not per request: a per-request switch would make one business operation's behaviour depend on when it ran and make an incident impossible to reconstruct.
- **Call sites.** Every caller depends on the interface only. No caller imports either implementation, branches on the config value, or type-asserts. A caller importing an implementation package is a rejection.
- **Which binding `fineract_jvm` means.** Run 1 binds it to the **embeddable seam**, which §3.2 proves is faithful inside the graded domain. Re-binding it to the running-server path is what a non-zero installment multiple requires; that re-binding is a design change to be recorded, not a contract amendment, and it must be accompanied by server-path vectors.
- **Observability.** The resolved implementation is recorded at startup and attributed on every generated schedule's audit trail. The mechanism is outside this contract; the requirement is not.
- **Configuration source.** Deployment configuration (environment or config file), per environment. Not a database row and not a runtime feature-flag service: the value must be reconstructible from the deployment artefact for an audit.

**What this section does not do.** It does not describe, plan or authorise changing the value in any live environment. **Flipping a context from `fineract_jvm` to `go_native` is a CUTOVER, and cutover is a hard `user` gate** requiring passing vectors, a clean shadow-parity window and regulatory / parallel-run sign-off.

---

## 8. Backlog (out of scope for DEC-1)

Found while designing this contract; recorded, not acted on.

1. **Promote the eleven `(19, HALF_UP)` captures to the vector store** — needs the attestation block, the three missing per-period columns (`fromDate`, fee, penalty), and a committed run recipe.
2. **Server-path vectors for `InstallmentRoundingMultipleMinor`** on a tenant provisioned at `(19, HALF_UP)` with a Mongolian time zone, plus a machine-readable attestation sidecar. Retires the §4.7 refusal.
3. **A vector that forces the EMI re-adjust loop to iterate** [`ProgressiveEMICalculator.java:1258-1308`]. Currently unpinned behaviour that can absorb an installment-multiple rounding difference entirely.
4. **Down-payment vectors.** No capture has ever produced a down-payment row; the path additionally reaches the multiple-rounding call site at `ProgressiveLoanScheduleGenerator.java:335-338`.
5. **`DayCountActualActual` vectors**, and an independent source re-derivation of the cross-year partial-period arm [`:1505-1507`, `:1526-1531`] — the largest un-re-derived hole in the evidence.
6. **Vectors for the uncaptured frequency and cardinality corners**: `FrequencyDays`, `FrequencyWeeks`, `RepaymentEvery > 1`, zero interest rate, `HALF_EVEN`.
7. **A capture-harness rule**: no amount may be routed through a floating-point type. The oracle's own `Money` exposes `double` overloads [`Money.java:134-148`, `:220-222`] and its shipped test helper converts through `doubleValue()` [`EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122`] — traps for a harness author, not parts of the calculation.
8. **`fixedLength`**, **flat interest**, **holiday / non-working-day due-date adjustment**, and a **finer error taxonomy** — each a new field or member and each a gate, none required by any product today.

---

## 9. Consequences

**Accepted:**

- Every caller depends on one interface with one method; both implementations are interchangeable behind it.
- Money is `int64` minor units across the whole boundary; no float, decimal string or float-backed decimal exists in or is implied by the contract, including for intermediates. Rates are exact rationals. Dates are civil dates in a named IANA zone.
- The rounding policy is expressible without a Java `MathContext` **in both of the senses the oracle uses it**, so two implementations round identically by specification rather than by coincidence.
- The response expresses the per-period split and the final-period residual without loss and cannot encode a schedule that contradicts itself, because every aggregate is derived rather than carried.
- Golden vectors have exactly one legal encoding, so vector comparison is structural equality.
- **Every input in the contract's domain carries an explicit statement of whether the corpus can discriminate it, and refuses rather than guesses when it cannot.** An input the corpus cannot test is unconformance-testable by construction, and that fact is now part of the frozen document rather than a surprise found later.

**Costs, accepted knowingly:**

- Six oracle inputs are pinned to constants (§4.4). If any needs to vary, that is an amendment and a gate.
- The graded domain is much narrower than the contract domain, so Run-1 implementations will refuse requests they could compute. That is deliberate: a refusal is recoverable, a wrong number in a customer's schedule is not.
- Several places carry surface no Run-1 vector exercises — a one-element slice, a one-member interest-method enum, a two-member day-count enum, a `FrequencyYears` the oracle throws on — bought to convert foreseeable shape changes into value-domain widenings.
- Charges will most likely require either an amendment to `Period` or a composing context (§6.1). Largest known unmitigated risk, named rather than papered over.
- Callers wanting totals must sum the rows.

**Obligations created:**

- The **Fineract-JVM adapter** must pin the six constants in §4.4, must initialise its tenant rounding mode to `Rounding.Mode` before every call, must upper-case the currency code, and must convert `int64` minor units and `Rate` to the oracle's decimal inputs without a float ever existing at the boundary.
- The **Go module** must reproduce the recurrence (not the closed-form annuity formula), both rounding senses at the specified points and in the specified order, the exact `1 + rateFactor` addition, the fixed-30/360 convention, the month-end re-anchor to the disbursement seed, the window-key ordering, and the final-period residual absorption — and must refuse, not guess, outside the graded domain.
- The **capture programme** must close §8 items 1 and 2 before any claim of production parity, and must never route an amount through a floating-point type.
- **A PASS on conformance means "matches the reference oracle on captured vectors, inside the graded domain". It never means "safe to cut over".**
