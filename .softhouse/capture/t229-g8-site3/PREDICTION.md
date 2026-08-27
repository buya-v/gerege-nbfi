# T229 — SITE 3's rescue condition, DERIVED, and registered BEFORE the live probe

> ### *** T241 CORRECTION, added at a LATER commit. Read before quoting anything below. ***
>
> **Not one word of T229's registered text has been removed or reworded.** This banner and the two
> in-place `*** T241 CORRECTION ***` notes (at the `TOTAL INTEREST` line of §1 and at **P2** in §2)
> are the only additions. The registered text is still readable in full, and the original file is
> in history at commit `29ed78c` — a **strict ancestor** of the capture commit `bb35cc8`, so the
> falsifiability guarantee this file exists to carry is intact.
>
> **What is wrong:** this file, and `src/site3.py`, state `TOTAL INTEREST = n·E + B` for an
> unrescued cell. **`n·E + B` is the TOTAL REPAYMENT, not the total interest.** The correct form is
> `n·E + B − (principal repaid)`; the two coincide only when the principal repaid is 0, i.e. on a
> **FULL** family-B cell. The error is therefore invisible on exactly the shape T229 was hunting.
>
> **Registered prediction P2 was REFUTED on three of T229's own cells, and this was never reported.**
> `src/classify_t229.py` computed the check and wrote `"P2_totalInterestEqualsNEplusB": false` into
> `out/classify-t229.json` for `T229-R600p0-N200-B201`, `-B251` and `-B299` at capture time
> (`bb35cc8`). Its `verdict` field is a function of the observed outcome and the observed principal
> only and never consults P2, so all three were reported **"AS PREDICTED"**. T241 searched the whole
> repository for `P2_totalInterestEqualsNEplusB` and found it in **no handoff, no gate text and no
> review** — only in the two classifiers and their JSON output. **The refutation was measured,
> printed and committed on the same day as the claim, and went unread for the whole interval.**
> T219 later hit the same defect from outside, on `B3001` and `B4499` (capture at `6eacc06`).
>
> **P2's other two conjuncts STAND** — `total` of row 1 `= E` and `total` of the last row `= E + B`
> held on every unrescued cell T241 checked, so **FACT A itself is unharmed**. Only the third
> conjunct's *label* is wrong, and the corrected form follows from FACT A rather than replacing it:
> the total column sums to `(n−1)·E + (E + B) = n·E + B`, and on the G-8 shape (no fees, no
> penalties) the interest column is that sum minus the principal column.
>
> **Materiality: LOW, and it must not be inflated.** No verdict, gate conclusion, region boundary,
> vector or promoted figure depends on it. `.softhouse/gates.md` already carries the correct form.
> Nothing here touches G-8's conservative superset `B_minor < 1.5·n`, the unproven `δ ≤ 1`
> conjecture, or the standing prohibition on putting options (b)/(c) to Buyan.
>
> Re-derived independently by T241 from the raw `.gz` rows, not transcribed:
> `src/rederive_total_interest_t241.py` (exit 0). T241's figures agree with T219's.

**Registered BEFORE any live observation exists.** This file, `prediction.json`, `src/site3.py` and
`src/cells-t229.json` are committed in a commit that is a **strict ancestor** of the commit carrying
`out/capture-t229-raw.json.gz`. If that ancestry does not hold, this prediction is worthless and
must be treated as such (P-9).

The oracle is the **Fineract reference implementation** at pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, Path A embeddable seam, **(19, HALF_UP)**, MNT dp 2, in
a throw-away `docker run --rm` from the pinned image. No server is started and no database
connection is opened. *Oracle Database is a prohibited product in this program and appears nowhere
in this work.*

---

## 0. WHAT WAS LOOKED AT BEFORE THIS FILE WAS WRITTEN — stated so nobody has to guess

The law below was derived from the **pinned Java source** (§1, citations bound by content). After
deriving it, and before writing this file, I read the **already-committed** observed rows of
**`T159-R600p0-N1000-B801`** (`.softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz`) —
the cell T223 recorded as its outright failure — and the seven live cells T223 tabulates in its
handoff. Those are **retrospective** checks against data that already existed; they are reported as
such and are **not** the test. **The test is the nine `T229-*` cells in `prediction.json`, none of
which has ever been asked by anyone**, and they are registered here in advance.

I did **not** tune anything to them. `src/site3.py` contains one law with no free parameter; the
only inputs are the pinned source's own constants.

---

## 1. SITE 3's RESCUE CONDITION, DERIVED FROM SOURCE — citations BOUND BY CONTENT

Every citation below is the **text that was matched**, not a line number. (T223 established that
`:1962`'s text occurs twice in `ProgressiveEMICalculator.java`, also at `:1979`; that is exactly why
content binding is required.) The full derivation with all quoted strings is the module docstring of
`src/site3.py`, steps **S3.0–S3.8**; this is the summary.

| step | file | text bound |
|---|---|---|
| S3.0 | `ProgressiveEMICalculator.java` | `final boolean onlyOnActualModelShouldApply = scheduleModel.isEmpty()` … `if (onlyOnActualModelShouldApply) {` `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods(scheduleModel, relatedRepaymentPeriods);` |
| S3.1 | `ProgressiveEMICalculator.java` | `Money diff = totalDisbursedAmount.plus(totalCapitalizedIncome, mc).plus(scheduleModel.getTotalCreditedPrincipal(), mc)` `.plus(totalDueInterest, mc).minus(totalEMI, mc);` and `Money adjustedEmi = repaymentPeriod.getEmi().add(diff, mc);` |
| S3.2 | `RepaymentPeriod.java` | `: MathUtil.min(getCalculatedDueInterest(), getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest(), false),` |
| S3.3 | `RepaymentPeriod.java` / `Money.java` | `calculatedDueInterest = Money.of(getEmi().getCurrencyData(), …reduce(BigDecimal.ZERO, BigDecimal::add), mc);` / `this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());` |
| S3.4 | `RepaymentPeriod.java` | `calculatedDueInterest = calculatedDueInterest.add(getPrevious().get().getUnrecognizedInterest(), getMc());` and `return MathUtil.negativeToZero(getCalculatedDueInterest().minus(getDueInterest(), getMc()), getMc());` |
| S3.5 | `ProgressiveEMICalculator.java` | `Money emiDifference = lastPeriod.getEmi().minus(penultimatePeriod.getEmi());` … `getUncountablePeriods(repaymentPeriods, penultimatePeriod.getEmi()));` |
| S3.6 | `EmiAdjustment.java` | `double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);` `return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero() && emiDifference.abs()` `.multipliedBy(100)` `.isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));` |
| S3.7 | `EmiAdjustment.java` / `ProgressiveEMICalculator.java` | `return emiDifference.dividedBy(Math.max(1, numberOfRelatedPeriods() - uncountablePeriods));` / `if (adjustedEqualMonthlyInstallmentValue.isEqualTo(emiAdjustment.originalEmi())) {` `break;` |
| S3.8 | `ProgressiveEMICalculator.java` / `EmiAdjustment.java` | `if (!getEmiAdjustment(newScheduleModel.repaymentPeriods()).hasLessEmiDifference(emiAdjustment)) {` `break;` / `return emiDifference.abs().isLessThan(previousAdjustment.emiDifference.abs());` |

### The two facts that decide it, and that T223's note does not contain

**FACT A (S3.2) — `emiDifference` is `B`, EXACTLY, and does not grow with the deficit.**
`getDueInterest()` is `min(calculatedDueInterest, EMI)`. So in the non-amortizing regime
`Σ dueInterest = n·E` and `Σ emi = n·E`, and the `diff` that
`calculateLastUnpaidRepaymentPeriodEMI` adds to the last row is

```
diff = B + Σ dueInterest − Σ emi = B + n·E − n·E = B          (integer minor units, exact)
```

for **every** `n` and however far `E` is below `I₁`. So `emiDifference` handed to site 3 is `B`,
and `shouldBeAdjusted` reduces — after unwinding `multipliedBy(100)` against `copy(floor(n/2))`,
both in MAJOR units — to `B_minor > ⌊n/2⌋`, which is where T223's `B_minor ≳ n/2` came from and is
**correct as far as it goes**.

**FACT B (S3.8) — the guard T223 omits.** The raised instalment is applied to a **copy**, and the
copy's own `emiDifference` must be **strictly smaller in absolute value** or the loop `break`s and
**the copy is discarded** (the `setEmi` write-back sits below the `break`). If the raised instalment
`E + a` is still `≤ I₁`, the copy is in the same non-amortizing regime, so by FACT A its `diff` is
`B` again: `|diff′| = |diff|`, not strictly less — **break, no rescue.** Principal only flows, and
`diff` only shrinks, when `E + a > I₁`.

### THE LAW

In **integer minor units**, with `E` the instalment on periods 1..n−1, `I₁q` = `B_minor·r` quantized
HALF_UP to whole minor units (S3.3 — the code compares against the **quantized** interest, not
T223's exact product), `δ = I₁q − E`, and `a = ⌊B_minor/n + ½⌋` (S3.7):

```
SITE 3 RESCUES  ⟺  B_minor > ⌊n/2⌋   ∧   a > δ
                ⟺  2·B_minor ≥ (2δ + 1)·n            [for δ ≥ 1 the first conjunct is implied]
```

**T223's rule is exactly this law with `δ` forced to 0** (`2B ≥ n`). That, and nothing else, is why
it fails on `T159-R600p0-N1000-B801`. T223's second conjunct `2·B_minor ≥ n` is not a second
condition at all — for `diff > 0` it is **implied** by `B_minor > ⌊n/2⌋`.

### And the SHAPE of an unrescued cell falls out of the same two facts

```
last row EMI       = E + B
last row interest  = min( I₁q + (n−1)·δ ,  E + B )              (S3.4: the deficit carries)
TOTAL PRINCIPAL    = max(0, B_minor − n·δ)
TOTAL INTEREST     = n·E + B
*** T241 CORRECTION — the line directly above is FALSE and is kept verbatim as the record.
    n·E + B is the TOTAL REPAYMENT.  TOTAL INTEREST = n·E + B − (principal repaid)
                                                    = n·E + B − max(0, B_minor − n·δ).
    Falsified by B201/B251/B299 in T229's OWN capture (bb35cc8) and by B3001/B4499 in
    T219's (6eacc06).  Affects no verdict.  See the banner at the top of this file. ***
```

so

- **FULL family B** (principal column sums to `0.00`) ⟺ `δ ≥ 1` **and** `B_minor ≤ n·δ`;
- **PARTIAL family B** ⟺ `δ ≥ 1` and `n·δ < B_minor < (δ + ½)·n`, repaying **exactly `B_minor − n·δ`**;
- `δ = 0` ⟹ the last row repays the **whole** principal in one go (T223's "`E_q = I₁` → not family B");
- `B_minor ≥ (δ + ½)·n` ⟹ site 3 rescues and the schedule is re-derived (not modelled here).

**The region ceiling this implies is `B_minor < (δ + ½)·n`, not T223's `≈ n/2`.** At `δ = 1` that is
**three times** the ceiling `gates.md` currently carries: `B_minor < 1.5·n`, i.e. **MNT `0.015·n`**,
so **MNT 5.40 at n = 360** rather than MNT 1.80. If `δ` can exceed 1 the ceiling grows with it.
**I predict `δ ∈ {0,1}` for this shape** and that is falsifiable too.

---

## 2. FALSIFIABLE CELL PREDICTIONS — nine cells, none ever asked by anyone

Every `T229-*` cell below is new: **600.0 % has never been asked at `n = 200`** at any principal
above MNT 0.01, and **36.0 % has never been asked at `n = 1400`** at any principal. `E` is
predicted by **T223's committed emulator** `emi_mechanism.py` (imported unmodified as
`src/emi_mechanism_t223.py`), which reproduces the oracle's instalment on 971/1035 committed cells.

| id | rate % | n | B minor | `E` pred | `I₁q` | `δ` | `a` | **T229 predicts** | principal (minor) | **T223's rule predicts** |
|---|---|---|---|---|---|---|---|---|---|---|
| `T229-R600p0-N200-B199`  | 600.0 | 200  | 199  | 99  | 100 | 1 | 1 | **FAMILY B, FULL** | **0** | rescued (amortizes) |
| `T229-R600p0-N200-B201`  | 600.0 | 200  | 201  | 100 | 101 | 1 | 1 | **FAMILY B, PARTIAL** | **1** | rescued (amortizes) |
| `T229-R600p0-N200-B251`  | 600.0 | 200  | 251  | 125 | 126 | 1 | 1 | **FAMILY B, PARTIAL** | **51** | rescued (amortizes) |
| `T229-R600p0-N200-B299`  | 600.0 | 200  | 299  | 149 | 150 | 1 | 1 | **FAMILY B, PARTIAL** | **99** | rescued (amortizes) |
| `T229-R600p0-N200-B301`  | 600.0 | 200  | 301  | 150 | 151 | 1 | 2 | **RESCUED — amortizes** | 301 | rescued (amortizes) |
| `T229-R600p0-N200-B303`  | 600.0 | 200  | 303  | 151 | 152 | 1 | 2 | **RESCUED — amortizes** | 303 | rescued (amortizes) |
| `T229-R36p0-N1400-B150`  | 36.0  | 1400 | 150  | 4   | 5   | 1 | 0 | **FAMILY B, FULL** | **0** | not rescued |
| `T229-R36p0-N1400-B1450` | 36.0  | 1400 | 1450 | 43  | 44  | 1 | 1 | **FAMILY B, PARTIAL** | **50** | rescued (amortizes) |
| `T229-R36p0-N1400-B2150` | 36.0  | 1400 | 2150 | 64  | 65  | 1 | 2 | **RESCUED — amortizes** | 2150 | rescued (amortizes) |

**Five of the nine are cells where T229 and T223 give OPPOSITE verdicts** (B199, B201, B251, B299,
B1450). On four of those T229 also predicts the **exact number of minor units repaid** — 0, 1, 51,
99 and 50 — which no rule anyone has written predicts at all. A single wrong principal on those
four kills this law.

`T229-R36p0-N1400-B1450` is the headline cell: **MNT 14.50 at 36.0 % p.a.**, predicted to repay
**MNT 0.50 of MNT 14.50 over 1,400 instalments**. T223's stated ceiling (`≈ n/2` minor units =
MNT 7.00 at n = 1400) says that cell cannot fail. This law says it fails, and says by how much.

### Also predicted, and stated so it can fail

- **P1** — every case emits exactly `n` REPAYMENT rows plus one DISBURSEMENT row.
- **P2** — on every unrescued cell, `total` of REPAYMENT row 1 = `E`, `total` of the last REPAYMENT
  row = `E + B`, and `totalInterestAmount` = `n·E + B`. **This is the direct observable of FACT A**:
  the last row's excess over the penultimate row IS the disbursement, exactly.
  - > *** T241 CORRECTION — **P2's THIRD CONJUNCT WAS REFUTED, ON T229'S OWN CELLS, AND NOBODY
    > READ IT.*** `out/classify-t229.json` records `"P2_totalInterestEqualsNEplusB": false` for
    > `T229-R600p0-N200-B201`, `-B251` and `-B299`; all three were nonetheless reported
    > **"AS PREDICTED"**, because `classify_t229.py`'s `verdict` consults only the outcome and the
    > principal. `totalInterestAmount` is `n·E + B − (principal repaid)`; `n·E + B` is the total
    > **repayment**. **The first two conjuncts STAND on every unrescued cell checked, so FACT A is
    > unharmed** — the corrected form is a consequence of FACT A, not a replacement for it.
    > Affects no verdict. See the banner at the top of this file. ***
- **P3** — on every unrescued cell, `totalPrincipalAmount` = `max(0, B − n·δ)` **exactly**.
- **P4** — on the RESCUED cells the instalment of row 1 is **strictly greater** than `E` above, and
  `totalPrincipalAmount` = the full disbursement.
- **P5 — an existence claim, so an empty measurement REFUTES rather than passes through**: at least
  one probe cell is family B and at least one is not.
- **P6** — the rig calibrations `P-CAL-ZPA` / `P-CAL-ZPB` reproduce the already-promoted
  `T64-ZP-A` / `T64-ZP-B` cell for cell with zero input differences. If they do not, nothing else in
  this capture is admissible.

---

## 3. WHERE THIS PREDICATE IS KNOWN TO BE WRONG OR SILENT — written down BEFORE the probe

- **`E` is not derived here.** The law takes `E` as an input; `src/site3.py` gets it from T223's
  emulator, which is known to be wrong on **64 of 1,035** committed cells — **and those 64 are
  exactly the site-3 rescue cells**, i.e. the cells this law says are rescued. So on a **RESCUED**
  cell the predicted `E` is the *pre-rescue* instalment and the oracle will emit a *different,
  higher* one. That is expected and is what P4 asserts; it is **not** a refutation. On an
  **unrescued** cell the emulator's `E` must be right, and P2 tests it.
- **The rescued branch is not modelled.** Once site 3 fires, the loop re-runs up to three times with
  `calculateLastUnpaidRepaymentPeriodEMI` in between; T229 predicts only *that it fires* and that the
  loan amortizes fully. **No claim** about the rescued instalment's value.
- **The over-amortization edge of GUARD 3 is not modelled.** `hasLessEmiDifference` compares
  **absolute** values, so a rescue that overshoots so far that `|diff′| ≥ |diff|` would also break.
  `src/site3.py` does not evaluate that branch; it assumes a first-step rescue shrinks `|diff|`.
  Any cell with `a` very large relative to `δ` is outside what is claimed here.
- **`δ ≥ 2` is unobserved.** Every cell in the record has `δ ∈ {0,1}`. The law is written for general
  `δ` but has never been tested at `δ ≥ 2`, and I do not know how to construct such a cell.
- **Scope: the FULL and PARTIAL family-B shapes of the G-8 shape only.** No claim about the THIRD
  OUTCOME (`StackOverflowError`), the Go port, `minorUnitDigits ≠ 2`, Path B / REST, other day-count
  conventions, other frequencies, down payments, charges, multiples-of, or any rate not asked.
- **`I₁q` vs T223's exact `I₁`.** The code quantizes (S3.3). On every cell to hand the two agree;
  they can differ when `B·r` is exactly on a half-minor-unit boundary and `E` sits between them.
  T229 uses the quantized one because that is what `getDuePrincipal` subtracts.
- **Throws are observations.** A `StackOverflowError` is recorded with its attempt count and never
  retried until it agrees (T177: the oracle's SO is a function of JVM state, not of the cell's
  inputs).
