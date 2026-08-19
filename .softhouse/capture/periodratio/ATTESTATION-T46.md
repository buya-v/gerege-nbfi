# `periodratio` — attestation corrections and a second pass (T46)

**Task:** T46, branch `softhouse/T46-capture-corrections`. **Corrects:** T44 findings **F39-1**,
**F39-2**, **F39-3**, **F39-4** against `.softhouse/capture/periodratio/`, and adds two new passes.

**This file supersedes `ATTESTATION.md` §4 and §5's framing where they disagree. `ATTESTATION.md`
itself is left as T39 committed it** — it is T39's evidence, and `patterns.md` forbids mutating a
committed capture's record. Corrections to *claims* live here.

**Reference oracle (Fineract) reachability, this fire: REACHABLE** [VERIFIED by this task: pinned image
`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, pinned checkout
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status --porcelain` empty, classpath 348 entries digest
`68e681486ae5890f7cded85b4a3e2588672d66dd5e1380dd897ef72213b5f95f`, **zero** Oracle Database / MySQL /
MariaDB entries — all asserted by `src/run-t46-periodratio.sh` on both new passes].

> **RAW OBSERVED FORM ONLY. NOTHING PROMOTED, NOTHING CONTRACT-SHAPED.** Gate G-1 is open; DEC-1 is
> unratified.

**Both new passes are proved failable and the `arms` pass is proved deterministic** — see
`NEGATIVE-TESTS-T46.md`: the threaded-rounding-mode leg exits 1 with 13 breaches read **off the
`MathContext` object**, the seam-sha leg exits 1 before any capture runs, and a second `arms` execution
from a fresh container is **byte-identical**
(`sha256 eab5dc0cd8e9b74e428c9d8cd0d87a8ea72129c01fe1375ec679b624fb893fc4`).

---

## 1. F39-1 — the month-end special case **cannot be separated by itself, anywhere.** Proved.

T44 asked for one of two outcomes: *"either capture a shape that separates the special case by itself,
or establish that none exists inside the graded domain and say so plainly with the argument."*

**It is the second, and the result is stronger than "inside the graded domain": the special case has no
separating shape at all, in the MONTHS arm or out of it.** Three legs, each independent of the others.

### 1.1 The argument

`calculatePeriodRatio` [`ProgressiveEMICalculator.java:1419-1459`] returns a pure function of
`(seedDate, fromDate, dueDate, n)`, where `n` is
`numberOfPeriodBetweenSeedDateAndActualRepaymentPeriod`. `n` is read at `:1441` and `:1449` and
**nowhere else** [VERIFIED: the method opened by this task]. So two readings that agree on `n` return
byte-equal ratios for every `(seed, from, due)`, hence identical money.

Write `k = (b.year*12 + b.month) − (a.year*12 + a.month)` and `len(b)` for the length of `b`'s month.

- **Packed** (`ChronoUnit.MONTHS.between`, which `DateUtils.getExactDifference` calls
  [`DateUtils.java:308-317`]) is `k − [a.day > b.day]`.
- **Naive** ("count calendar months, step back one if `plusMonths` overshoots") is
  `k − [min(a.day, len(b)) > b.day]`, because `a.plusMonths(k)` has day `min(a.day, len(b))`.

They differ **iff** `a.day > b.day` **and** `min(a.day, len(b)) ≤ b.day`. Given `a.day > b.day`, the
second condition forces `len(b) ≤ b.day`, and since `b.day ≤ len(b)` always, that means
**`b.day = len(b)`** — `b` is the last day of its month — **and** `a.day > b.day`. That is *verbatim*
the special case's predicate at `:1432`
(`targetDateLastDay == targetDateDay && seedDateDay > targetDateDay`).

And when the predicate fires, the oracle's `n` is `packed(a, b+1day)`. `b+1day` is the first of the next
month, so `k' = k+1` and `a.day > 1` (it is ≥ 29, since it exceeds a month length), giving
`packed(a, b+1) = k+1−1 = k` — which is exactly what **naive** returns.

**So: `nOracle ≡ nNaive` identically, and `nPacked ≠ nNaive` on precisely the firing set.** The special
case is *definitionally* the compensation for the packed rule's month-end undercount. No input can
separate one from the other.

### 1.2 The exhaustive measurement

`analysis/T46MonthDiffExhaustive.java`, run **inside the pinned oracle image** so the `java.time`
semantics measured are the oracle's own, over **every ordered date pair** in 2000-01-01 … 2040-12-31
[`analysis/t46_monthdiff_exhaustive-output.txt`, `analysis/run-t46-monthdiff.sh`]:

```
java.vm.version                             : 21.0.11+10-LTS
ordered date pairs swept                    : 112147776
month-end special case FIRES (:1432)        : 45253
nPacked != nNaive                           : 45253
fires AND nPacked == nNaive                 : 0
does NOT fire AND nPacked != nNaive         : 0
nOracle != nNaive   [R2 vs R4]              : 0
nOracle != nPacked  [R2 vs R3]              : 45253
first R2-vs-R4 separator found              : (none)
YEARS arm: yPacked != yNaive                : 165
first YEARS separator found                 : seed=2000-02-29 from=2001-02-28 yPacked=0 yNaive=1
```

**112,147,776 pairs, zero R2-vs-R4 separators**, and the firing set equals the disagreement set exactly
(45,253 = 45,253, both cross-terms **0**) — the closed-form argument, measured. T44 swept 59,130
`(start, period)` pairs; this is the whole date space and it is a superset by construction.

### 1.3 What T44 proposed instead, and why it does not work either

T44's remedy was: *"a discriminator for packed-vs-naive has to come from `calculatePeriodRatio`'s
`YEARS` / `WEEKS` / `DAYS` arms (`:1405`, `:1407`, `:1408`), which call `getExactDifference` with no
special case at all."* Correct as far as it goes, and **all three arms are now captured** (§3). What
they show:

- **`WEEKS` and `DAYS` cannot separate packed from naive at all.** `a.plusWeeks(k)` is `a + 7k` days and
  `a.plusDays(k)` is `a + k` days, so the "step back on overshoot" branch is unreachable and the two
  functions are the same function. Measured as `0` disagreements in the same sweep.
- **`YEARS` *does* separate** — 165 pairs in the swept window, all of the form 29 Feb → 28 Feb — **but
  the YEARS arm is unreachable in a completed schedule.**
  `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` has cases for `DAYS`, `WEEKS`, `MONTHS` and
  then `default -> throw new UnsupportedOperationException("Invalid repayment frequency")`
  [`ProgressiveEMICalculator.java:1602-1610`]. `calculatePeriodRatio`'s YEARS result is computed at
  `:1405` and thrown away into that exception at `:1609`.

**OBSERVED, not read** [`out/t46-periodratio-arms.json`]:

| capture | frequency | result |
|---|---|---|
| `T46-YR-A` | YEARS, seed 29 Feb 2020 — the packed/naive separator | `java.lang.UnsupportedOperationException: Invalid repayment frequency` |
| `T46-YR-B` | YEARS, ordinary 15 Mar seed | `java.lang.UnsupportedOperationException: Invalid repayment frequency` |

**Conclusion. Packed-vs-naive whole-units is not separable anywhere in the progressive generator's
reachable domain**: MONTHS compensates exactly, WEEKS and DAYS have nothing to compensate, and YEARS
throws before the ratio is used. The blind spot T44 marked `TO_BE_CAPTURED` is **permanent for this
generator**, not merely uncaptured — which is a better answer, because "capture it later" would have
been a task that can never succeed.

### 1.4 Required relabelling of the `T39-ME-*` family

`T39-ME-A` … `T39-ME-D` **grade the PAIR** — `month-end special case ∧ packed whole-months` — and grade
it on **12 periods** across the four captures [`analysis/t46_arms_ratio-output.txt`, independently
re-derived by this task from the pinned source, not from T39's `analysis/`]. They do **not** grade the
special case alone, and no capture can. A port with **two cancelling defects** (naive whole-months *and*
no special case) passes all four and is, on this arm, *correct* — which is the honest way to say it.

**DEC-1 consequence** (for T45, whose surface this is — T46 does not edit `docs/adr/**`): the month-end
obligation must pin the **packed** rule normatively alongside the special case. Neither clause is safe
stated alone: the special case without the packed rule is *wrong*, and the packed rule without the
special case is *wrong*. State them as one obligation, or state the naive rule with no special case —
the three are equivalent only in the pairing, never clause by clause.

## 2. F39-2 / F39-3 — attestation corrected, and the threaded context re-emitted off the object

### 2.1 The correction to `ATTESTATION.md` §4

- The heading *"The `MathContext` actually in force, as the oracle itself reports it"* is the phrasing
  T42's rule 1 exists to ban. **Read it as: "the AMBIENT `MoneyHelper` context, as the oracle reports
  it".** On Path A the ambient context is **not** the arithmetic — T42's experiment E1 shows it is
  provably never read for a 2-dp currency.
- *"Two independent witnesses to the mode, both from the oracle"* is **wrong: they are ONE witness.**
  The SLF4J line and `MoneyHelper.getMathContext()` are one cache write, logged and then read back
  [VERIFIED by this task: `MoneyHelper.java:59-64` computes `roundingMode`, does
  `roundingModeCache.put(...)` and emits the log line from that same local; `:74-82` reads the cache;
  `:91-94` `computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()))`].
  This is verbatim the defect T42 raised against T37 §5. **T42's correction list named T35, T36, T37 and
  `reference-oracle.md`, and missed T39.**
- The word *"effective"* in `run-periodratio.sh:196`'s breach text must be read as **"ambient"**.
- **What survives untouched:** §4's own closing paragraph draws the ambient/threaded distinction
  correctly and says *"only the second is a statement about the arithmetic"*, and the N7 negative leg is
  a genuine **threaded** behavioural canary. **No captured value is affected by this finding.**

### 2.2 The re-emission — the threaded `MathContext` echoed off the OBJECT

T39 wrote `c.precision()` and `c.mode()` — the case record's **intent** — under keys named
`threadedMathContext…`. Nothing read `mc`, so `run-periodratio.sh`'s assertion 10 was tautological with
respect to the object handed to `generate`.

`src/CapturePeriodRatio2.java` (new) echoes, per case, off the reference actually passed to
`EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData)`:

```
"threadedMathContext":             mc.toString()
"threadedMathContextPrecision":    mc.getPrecision()
"threadedMathContextRoundingMode": mc.getRoundingMode()
"wiring":                          "PATH_A -- this MathContext object is the argument of …"
```

and `src/run-t46-periodratio.sh` asserts **those**, plus that `mc.toString()` agrees with its own
getters, plus that intent has not drifted from object. Assertion 9's breach text now says **AMBIENT**.
The SLF4J lines are recorded as **one ambient witness**, so labelled in the script's own output.

**IDENTITY PROOF, required by `patterns.md` before anything new may be trusted**
[`analysis/t46_reemit_identity.py`, `analysis/t46_reemit_identity-output.txt`]:

```
captures compared            : 16
leaves + top-level compared  : 2072
RESULT: 2072 of 2072 published values IDENTICAL.
```

Every leaf T39 published is present in the re-emission with a byte-identical value; the only new leaves
are the four listed above; **no new case appears in this pass**, because that would have destroyed the
identity check (T35's lesson). New cases are in a separate pass with separate ids (§3).

The re-emission also confirms, on a different day through a different harness, that the threaded context
really was `(19, HALF_UP)` on fifteen of sixteen and `(12, HALF_UP)` on `T39-CAL` — now read off the
object rather than off the intent.

## 3. New pass: the uncaptured arms, and `RepaymentEvery > 1`

`-Dt46.set=arms`, **new ids**, separate payload `out/t46-periodratio-arms.json`. This closes T44's
periodratio blind spots **2** (the `YEARS`/`WEEKS`/`DAYS` arms) and **3** (`RepaymentEvery` pinned to 1
on all 16 captures).

| capture | frequency | every | observed |
|---|---|---|---|
| `T46-ARM-CTL` | MONTHS | 1 | control; identical inputs to `T39-CTL-Q0a`; term 182 d, total interest `76723.70` |
| `T46-YR-A` | YEARS | 1 | **THROWS** `UnsupportedOperationException: Invalid repayment frequency` |
| `T46-YR-B` | YEARS | 1 | **THROWS** — same |
| `T46-WK-A` | WEEKS | 1 | term 42 d, total interest `17701.61`, p1 `5040.00` |
| `T46-WK-B` | WEEKS | 1 | disbursement after start; term 42 d, total interest `15518.91` |
| `T46-WK-C` | WEEKS | 2 | term 84 d, total interest `35525.93` |
| `T46-DY-A` | DAYS | 1 | term 6 d, total interest `2521.26` |
| `T46-DY-B` | DAYS | 10 | term 60 d, total interest `25325.62` |
| `T46-RE-2` | MONTHS | 2 | term 366 d, total interest `155652.82` |
| `T46-RE-3` | MONTHS | 3 | drift anchoring; term 550 d, total interest `236687.94` |
| `T46-RE-2ME` | MONTHS | 2 | 31 Jan seed; term 366 d, total interest `155652.82` |

### What this pass DISCRIMINATES — measured, not assumed

`analysis/t46_arms_ratio.py` re-implements `calculatePeriodRatio` and `calculateSeedDate` **from the
pinned source only**, in exact integer date arithmetic, and reports the ratio (never a money value)
under each of T44's four readings, over **186 repayment periods** across both T46 passes
[`analysis/t46_arms_ratio-output.txt`]:

```
periods where R1 (RepaymentEvery) differs from the pinned R2 : 41
periods where R3 (no month-end special case) differs from R2 : 12
periods where R4 (naive whole-units, no special case) != R2  : 0
```

- It **reproduces T39's own separation independently**: the eight `T39-P0-*` drift captures separate
  R1 on 38 periods and the four `T39-ME-*` captures separate R3 on 10 — through a re-implementation that
  never reads `analysis/readings.py`, `t34_model.py` or `t34_periodratio.py`.
- **`T46-RE-3` separates R1 on 3 periods at `repaymentEvery = 3`** — the first capture in the program to
  discriminate `periodRatio` from `RepaymentEvery` at `RepaymentEvery ≠ 1`. T44 blind spot 3 said a port
  could get the multiplier right and `RepaymentEvery` wrong and still pass all 16; it no longer can.
- **`T46-RE-2ME` separates R3 on 2 periods at `repaymentEvery = 2`** — month-end anchoring outside the
  every-1 lattice, also new.
- **`T46-RE-2`, `T46-WK-*`, `T46-DY-*` and `T46-ARM-CTL` separate NOTHING** among R1/R3/R4, and that is
  stated because it is true: they add *arm coverage* — the WEEKS and DAYS arms are exercised at all for
  the first time — and **zero discriminating power** over the contested readings. A corpus is what it can
  distinguish.
- **R4 = R2 on all 186 periods**, on real observed schedules, which is §1's proof arriving a third way.

## 4. F39-4 — the line citations

Corrected, each re-opened in the pinned checkout by this task:

| claim | T39/T44 said | correct |
|---|---|---|
| the month-end special case | `:1429-1434` (handoff), `:1426-1436` (verdict) | **`:1432` (the predicate) and `:1433` (the nudged call)**. `:1429` is the continuation of the `targetDateLastDay` declaration opened at `:1428`; `:1434` is `} else {`; `:1426-1436` is the whole `case MONTHS ->` arm. Deleting `:1429-1434` literally does not compile. |
| `daysInMonth` computed | prose `:1509`, tag `:1508` | **`:1508`** |
| `calculatePeriodRatio` | — | **`:1419-1459`**; the MONTHS arm is `:1425-1437`; `n` is consumed at `:1441` and `:1449` only |
| the YEARS/WEEKS/DAYS throw | — | **`:1602-1610`**, `default -> throw new UnsupportedOperationException("Invalid repayment frequency")` at **`:1609`** |

---

## 5. Admissibility, restated

**May be promoted once G-1 closes**

- `T39-P0-A` … `T39-P0-H` — unchanged; the strongest parity candidates in the set.
- `T39-ME-A` … `T39-ME-D` — **only** under the label *"grades the month-end special case **jointly with**
  the packed whole-months rule"*. As "grades the special case" they are misleading (§1).
- `T46-RE-3` and `T46-RE-2ME` — **new**, and the only captures that discriminate at `RepaymentEvery ≠ 1`.
- `T39-CTL-1`, `T39-CTL-2`, `T39-CTL-Q0a`, `T46-ARM-CTL` — as **controls**, never as discriminators.
- `T46-WK-*`, `T46-DY-*`, `T46-RE-2` — as **arm-coverage observations**, explicitly labelled
  non-discriminating.

**May NOT be promoted**

- `T39-CAL` — threaded `(12, HALF_UP)`, and its transcription source asserts through `double`. Rig
  calibration only.
- **Anything claiming to grade the month-end special case in isolation** — no such vector exists (§1).
- `T46-YR-A` / `T46-YR-B` — they record a **throw**, not money. Keep them as the evidence that the YEARS
  arm is unreachable; they are negative observations, never parity vectors.

**Blind spots after T46**

1. ~~packed vs naive whole-months~~ → **closed as unanswerable**: provably indistinguishable on MONTHS,
   identical on WEEKS/DAYS, and unreachable on YEARS (§1). Not `TO_BE_CAPTURED`; **not capturable**.
2. ~~the `YEARS`/`WEEKS`/`DAYS` arms are entirely uncaptured~~ → **closed** (§3), with YEARS closed by a
   throw rather than by a schedule.
3. ~~`RepaymentEvery > 1`~~ → **closed for MONTHS at 2 and 3, and for WEEKS at 2 / DAYS at 10** (§3).
   `RepaymentEvery > 3` and the drift × every interaction beyond `T46-RE-3` remain uncaptured.
4. `DaysInMonth = ACTUAL` (a different arm at `:1400-1402` / `:1534`) and `DaysInYear = ACTUAL` — still
   uncaptured.
5. **Charges** — every fee and penalty is `0.00` on all 27 Path A captures; the `charges` set answers
   this, and its `ATTESTATION-T46.md` now records that the charge rounding mode is **ambient**, not
   threaded.
6. `installmentAmountInMultiplesOf` and `daysInYearCustomStrategy` — Path A **drops both**
   (`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)` at
   `LoanApplicationTerms.java:579-606` sets neither) [VERIFIED by this task: the builder chain contains
   **zero** occurrences of `MultiplesOf`]. And T44's **M-4** applies: the field is honoured or lost **by
   caller** — the REST `calculateLoanSchedule` path honours it, and
   `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement` (`:44` reads the ambient
   `mc`, then builds a `LoanRepaymentScheduleModelData` and calls `generate(mc, modelData)`) inherits the
   same drop. DEC-1 must not state the field's behaviour unconditionally.
7. Multi-disbursement, down payments, `fixedLength`, `interestRecognitionOnDisbursementDate`.
8. The EMI re-adjust loop — pinned by the `dec1-binding` set, not this one.
9. T39's N-2 disjointness sweep remains **uncommitted**; T46 did not reproduce it.
10. **Precision.** Every new T46 capture runs at threaded `(19, HALF_UP)`. Whether precision 19 is
    *observable* at all on this seam is still open — T39 found 19 and 12 indistinguishable across its
    sixteen shapes, and nothing in T46's eleven new shapes changes that.

---

## 6. Unverified

- **That §1's closed-form argument covers `LocalDate`'s whole range.** The measurement is exhaustive
  over ordered pairs in **2000-01-01 … 2040-12-31** (112,147,776 pairs); the argument itself is
  arithmetic over `(k, a.day, b.day, len(b))` and has no year dependence, but it is a re-derivation, not
  a machine-checked proof. `[VERIFIED on the swept range and by closed form; UNVERIFIED as a machine
  proof]`
- **That `n` is the only thing the three readings change.** Read off `:1419-1459` by this task: `n` is
  used at `:1441` and `:1449` only. `[VERIFIED by reading; UNVERIFIED by instrumentation]`
- **That the YEARS throw is unconditional.** Observed on two shapes, and re-derived from `:1602-1610`
  where YEARS falls to `default`. A caller that reached `rateFactorByRepaymentPeriod` some other way is
  not excluded by these two observations. `[VERIFIED on T46-YR-A and T46-YR-B; UNVERIFIED as universal]`
- **That `analysis/t46_arms_ratio.py` is a complete model of `calculatePeriodRatio`.** It reproduces
  T39's own R1 and R3 separations independently, which is the check that matters, but it models the
  *ratio* only — it predicts no money and is not a schedule model. `[VERIFIED against T39's separations;
  UNVERIFIED as a money model]`
- **`T46-WK-B`'s "disbursement after start" shape.** It was authored to probe drift on the WEEKS arm and
  it separates nothing; whether *any* weekly shape can produce a non-integer `periodRatio` was not
  swept. `[UNVERIFIED]`
- **Generalisation.** Twenty-seven captures grade twenty-seven shapes. Nothing here licenses a claim
  about an unsampled tuple.
- **This pass's own coverage.** T44 found what T39 could not distinguish; T46 found what T44's proposed
  remedy could not reach. Assume a further one exists.
