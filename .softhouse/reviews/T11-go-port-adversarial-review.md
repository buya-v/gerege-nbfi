# T11 — independent adversarial review: the Go schedule port

- **Run:** `2026-08-17-run1-harness-schedule-poc`  **Context:** `loan-schedule`  **Task:** T11 (independent reviewer)
- **Artefact:** `nexus/internal/apps/loanschedule/{generator.go,emi.go,rounding.go}` (719 + 832 + 189 lines)
- **Reviewed tree:** branch `softhouse/T11-go-port-review`, cut from `main` @ `4f6390a`
  [VERIFIED: `git log --oneline -3` → `4f6390a conformance: de-stale two proofs`, `3a59885 merge T56`, `57c0c60 patterns`]
- **Reference oracle (Fineract):** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean
  [VERIFIED: `git -C /Users/buv/fineract log --oneline -1` → `426a23544 Merge pull request #5946`; `git status --short` empty]
- **Baseline:** `.softhouse/conformance.sh` → **VERDICT: PASS (exit 0)**, 13 parity vectors, 1350 cells, 6/6 invariants
  [VERIFIED: run in this review, `/tmp/t11-baseline.txt`]

> Throughout, **"the oracle" is the Fineract reference implementation**. Oracle Database is a prohibited
> product in this program and appears nowhere in this stack. This port touches no database at all.

---

## 0. The base was wrong again — third recurrence of pattern P-5

My worktree was checked out at **`2c0adab`**, which predates the T10 merge (`8f7623b`). `nexus/internal/apps/loanschedule/`
contained only `conformance/` and `contract/` — **no `generator.go`, no `emi.go`, no `rounding.go`.**

[VERIFIED: `git log --oneline -8` in the supplied worktree → HEAD `2c0adab`; `ls -la nexus/internal/apps/loanschedule/`
→ two directories, zero `.go` files. `git merge-base --is-ancestor HEAD main` → HEAD is an ancestor of `main`,
i.e. the worktree was simply behind by 5 commits including all three artefacts.]

Had I graded what I was handed I would have reviewed **an absent artefact and reported it clean.** I re-cut onto
`main` before reading anything, as the brief required.

This is the **third** occurrence in two fires (T9's F-9, T57's N-5, T56, now T11). `patterns.md` P-5 already
states the rule. The rule is not the gap — the *mechanism* is: the brief names the artefact, and the worktree is
still cut from wherever the fire lock happened to be. **Driver finding (P2): make worktree creation take the
merge commit of the artefact as an argument, and fail the dispatch if the named path is absent.** A written rule
that has been violated three times after being written is not being enforced by anything.

---

## 1. Method

The pipeline's rule is that a reviewer re-derives money math **against the vectors and the Fineract source,
never against the code under review**. Reading the port and agreeing with it is not a review. I did four things,
and only the first is the one previous rounds have done:

1. **Re-derived every money path from the Java**, opening each cited `file:line` and checking the port
   reproduces the *sequence of finite-precision operations*, not the algebraic result (§2).
2. **Mutation-tested the port against 22 counterfactuals I derived myself from the source** — not T10's list —
   and recorded which the 13 vectors kill and which they do not (§3).
3. **Built four off-lattice probe shapes and measured the margin** each surviving mutation moves on them, so a
   "the corpus is blind" claim comes with a number and an executable shape (§4).
4. **Replayed 15 oracle observations that are already in the committed tree and have never been promoted**
   against the port, cell for cell (§5). This is the strongest evidence in the review and it required no
   oracle run.

Every mutation ran in a scratch copy at `/tmp/t11mut`. The committed tree was never mutated
[VERIFIED: `git status --porcelain` on the review branch is empty apart from this file; `git diff --stat main --
nexus/.../contract.go .softhouse/vectors/` is empty, so `contract.go`, every vector, `capabilities.json` and
`PIN.json` are untouched].

---

## 2. The arithmetic, re-derived from source

All Java paths are relative to `/Users/buv/fineract` at the pinned commit.
`PEC` = `fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java`.

### 2.1 The EMI fold — T10's "first multiply against ONE is not a no-op" claim

**The claim is TRUE, and the port reproduces it.**

`calculateRateFactorPlus1NForEmi` is `periods.stream().map(...).reduce(BigDecimal.ONE, (acc, value) ->
acc.multiply(value, mc))` [VERIFIED: `PEC:1816-1820`]. `Stream.reduce(identity, accumulator)` evaluates
`((ONE ⊗ v₁) ⊗ v₂) …`, so **the first operation is genuinely `ONE.multiply(v₁, mc)`**.

`v₁` is `getRateFactorPlus1()` = `interestPeriods.stream().map(getRateFactor).reduce(BigDecimal.ONE,
BigDecimal::add)` [VERIFIED: `RepaymentPeriod.java:216-218`] — **a plain `add` with no MathContext, so the sum is
exact.** Each rate factor carries `.setScale(mc.getPrecision(), mc.getRoundingMode())` = 19 *decimal places*
[VERIFIED: `PEC:1962`]. So `v₁ = 1.dddddddddddddddddd d` — one integer digit plus 19 fraction digits =
**20 significant digits** — and `multiply(…, MathContext(19, HALF_UP))` rounds it to 19. The first product drops
a digit. Worked: at 7.0 % / 30-360 the rate factor is `0.0058333333333333333`, `v₁ = 1.0058333333333333333`
(20 sig digits), and `round₁₉(v₁) = 1.005833333333333333`.

Port: `emi.go:622-625` seeds `rateFactorN := big.NewRat(1,1)` and applies `roundSignificant(…, m.precision)` on
**every** iteration including the first. ✓
Port: `emi.go:626-633` folds `fn` as `product := round₁₉(fn × growth); fn := round₁₉(product + 1)`, which is
`fnValue` = `BigDecimal.ONE.add(previousFnValue.multiply(currentRateFactor, mc), mc)` — **two** roundings, the
inner multiply and the outer add [VERIFIED: `PEC:1991-1993`]. ✓ Seeded `ONE` and `skip(1)` [VERIFIED: `PEC:1822-1828`]. ✓
Port: `emi.go:634-637` is `round₁₉(rateFactorN × balance)` then `round₁₉(… ÷ fn)`, matching
`rateFactorPlus1N.multiply(outstandingBalanceForRest, mc).divide(fnResult, mc)` [VERIFIED: `PEC:1838-1840`]. ✓
**No `pow`, no closed form, anywhere in the port.** ✓

Two steps the port *omits* and I checked are genuinely inert:
- `MathUtil.stripTrailingZeros` at `PEC:1725-1726` is `new BigDecimal(value.stripTrailingZeros().toPlainString())`
  [VERIFIED: `MathUtil.java:499-501`] — value-preserving, and the port carries exact rationals with no scale.
- `.add(calculateEMIValueForFixedInterest(...))` at `PEC:1733` sums `getFixedInterest()` over the periods and
  divides by the count [VERIFIED: `PEC:1846-1848`]; `fixedInterest` is a re-age quantity, zero on this seam.

### 2.2 Where rounding happens, and at what scale

| step | source | port |
|---|---|---|
| nominal rate | `rate.divide(100, mc)` [`PEC:1318-1320`] | `generator.go:475-477`, `roundSignificant(num/den, 19)` ✓ |
| rate-factor kernel | 2 mc ops for the fraction, 3 for the factor, then `.setScale(mc.getPrecision(), mc.getRoundingMode())` [`PEC:1956-1962`] | `emi.go:508-519`, five `roundSignificant` then `roundScale(v, m.scale)` ✓ |
| growth factor | plain `add`, **no** mc [`RepaymentPeriod.java:216-218`] | `emi.go:445-451`, exact `big.Rat` add ✓ |
| per-segment interest | **three separately mc-rounded ops in this order** [`InterestPeriod.java:154-157`] | `emi.go:353-357`, `t1`,`t2`,`t3` ✓ |
| period interest → Money | sum the BigDecimals, **then** `Money.of` **once** [`RepaymentPeriod.java:255-257`] | `emi.go:381-385` ✓ |
| Money constructor | `setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())` [`Money.java:52`] | `rounding.go:minorFromMajor` ✓ |

**`RateFactorScale` cannot diverge from the oracle's single `MathContext`.** The port models it as a separate
contract field, which would be a defect if a request could set the two apart — it cannot:
`generator.go:287-293` refuses `RateFactorScale != SignificantDigits` with `ErrUnsupportedConfiguration`, and
`generator.go:344-347` pins both at 19 inside the graded domain. ✓

**One assumption the graded domain is carrying, and it should stay named.** `Money`'s constructor reads
`getMc().getRoundingMode()` — the **ambient** `MoneyHelper` context — not the `mc` it was handed
[VERIFIED: `Money.java:40-52`, the parameter `mc` is stored but `:52` calls `getMc()`]. Likewise
`Money.dividedBy(long)` and `multipliedBy(long)` take the ambient context [VERIFIED: `Money.java:352-358, 380-382`].
The port hard-codes HALF_UP throughout (`rounding.go:roundHalfUpToInt`). That is correct **only because**
`generator.go:348-350` refuses any mode but HALF_UP and the ratified tenant mode is HALF_UP. The port's own
header comment says exactly this. ✓ — but it means the port is not merely "graded at HALF_UP", it is
*implemented only at HALF_UP*, and widening the graded domain to another mode is a code change, not a config
change. Worth a line in the handoff.

### 2.3 The final period

**Confirmed: there is no "final principal := remaining balance" special case.** `getDuePrincipal()` is
`max(negativeToZero(emiPlusCreditedAmounts − dueInterest), paidPrincipal)` on **every** row
[VERIFIED: `RepaymentPeriod.java:345-350`]. The residual lands on the **last unpaid period's EMI**
[VERIFIED: `PEC:1183-1210`, `adjustedEmi = repaymentPeriod.getEmi().add(diff, mc)`]. Port: `emi.go:416-418`
(principal) and `emi.go:651-697` (`applyFinalPeriodResidual`). ✓

Three sub-claims I checked because getting any of them wrong is invisible:
- `totalDuePaidDiff` at `PEC:1162` is `getTotalDuePrincipal()`, which is
  `Σ RepaymentPeriod.getCreditedAmounts()` = **every disbursement**, not the due principal
  [VERIFIED: `ProgressiveLoanInterestScheduleModel.java:347-348` → `RepaymentPeriod.java:385-387` →
  `InterestPeriod.java:193-195`]. Port: `emi.go:663-668` sums `s.disbursedMinor`. ✓
- The recursion guard at `PEC:1211-1215` is `emi < totalPaidAmount − totalCreditedAmount`.
  `getTotalCreditedAmount()` is credited **principal + interest**, i.e. **zero** on this seam — it is *not* the
  disbursements [VERIFIED: `RepaymentPeriod.java:357-360`]. So the guard reduces to `emi < 0`, which is exactly
  what `emi.go:693` tests. I checked this specifically because reading `getCreditedAmounts` (`:385`) instead of
  `getTotalCreditedAmount` (`:357`) — two similarly named methods on the same class, one of which *is* the
  disbursements — would have given `emi < −disbursed` and silently disabled the clamp. The port reads the right one. ✓
- `isFullyPaid()` is `emiPlusCredited == totalPaidAmount` → `emi == 0` unpaid [VERIFIED: `RepaymentPeriod.java:371-373`],
  so "last unpaid period" is "last period with a non-zero installment". Port: `emi.go:704-716`. ✓

### 2.4 The EMI re-adjust smoothing loop

`EmiAdjustment.shouldBeAdjusted()` is
`floor(n/2) > 0 && !emiDifference.isZero() && emiDifference.abs().multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalf))`
[VERIFIED: `EmiAdjustment.java:31-36`]. **`Money.copy(double)` REPLACES the amount, it does not scale it**
[VERIFIED: `Money.java:220-222` → `copy(BigDecimal.valueOf(amount))` → `new Money(currency, amount, mc)`], so the
right-hand side is the *bare number* `floor(n/2)` in currency units and the guard has no dependence on
installment size. Port: `emi.go:749-757` compares `|Δ| × 100` against `floor(n/2) × 10^minorDigits` in exact
integers — correct, and correctly refuses to reproduce the Java's doubles. ✓

Loop mechanics, all checked against `PEC:1258-1308`:
divisor is `max(1, n − uncountablePeriods)` with `uncountablePeriods` = count of periods whose total paid exceeds
the original EMI [VERIFIED: `PEC:2027-2031`] = **0** on an unpaid schedule ✓;
the trial is a **rebuild on a copy** with balances recomputed and the residual re-applied [`:1287-1288`] ✓;
the adoption test is **strict** and its failure discards the trial [`:1289`, `EmiAdjustment.java:47`] ✓;
every exit is a `break` ✓; the counter advances only on adoption and bounds the loop at three [`:1307-1308`] ✓;
the write filter is `from ≥ relatedFirstFrom && due ≥ relatedFirstDue` [`:1280`] ✓.

**One structural difference, and it is inert.** Java creates `newScheduleModel` **once** and reuses it across
iterations [`PEC:1274-1276`]; the port takes a fresh `deepCopy()` every iteration [`emi.go:795`]. These agree
because at the end of each adopted iteration Java copies the trial's related-period EMIs back into the live
model and recomputes its balances [`:1298-1306`], while the trial's *non*-related periods were never touched by
`:1279-1286` and (on this seam) are all zero-EMI, so the live model and the retained trial are equal entering
the next iteration. [VERIFIED by construction above; **also** by mutation: the port passes all 13 vectors
including the two shapes T57 captured precisely to make this loop fire.]

### 2.5 Month-end stepping, the two seeds, and row ordering

`adjustDate` fires on `frequencyType.isMonthly() && seedDay > 28 && dateDay >= 28` and yields
`min(lengthOfMonth(date), seedDay)` [VERIFIED: `DefaultScheduledDateGenerator.java:168-176`]. The `>28`/`>=28`
asymmetry and `min` are reproduced exactly at `generator.go:556-568`. ✓

**The two distinct seeds are both correct in the port**, and this is the single most load-bearing thing in the file:
- the re-anchor seed is the **DISBURSEMENT** date [VERIFIED: `LoanApplicationTerms.java:583-589` sets
  `seedDate = modelData.disbursementDate()`, passed to the Builder at `:602`, stored at `:324`;
  `DefaultScheduledDateGenerator.java:130` passes `loanApplicationTerms.getSeedDate()` to `adjustDate`].
  Port: `repaymentDueDates(..., seed = req.Disbursements[0].Date)` [`generator.go:86-87`, `:512-524`]. ✓
- `calculateSeedDate`'s lattice seed is the **SCHEDULE START** [VERIFIED: `PEC:1462`,
  `scheduleModel.getStartDate()` = `repaymentPeriods.getFirst().getFromDate()`,
  `ProgressiveLoanInterestScheduleModel.java:209-210`]. Port: `emi.go:580-596`. ✓

I checked the one thing that would have made all of this moot: `generateNextRepaymentDate` short-circuits to
`getCalculatedRepaymentsStartingFromLocalDate()` on the first repayment if that field is non-null
[`DefaultScheduledDateGenerator.java:121-123`], and `assembleFrom` passes
`.repaymentsStartingFromDate(modelData.scheduleGenerationStartDate())` at `LoanApplicationTerms.java:598` — a
similarly named field. **They are different fields.** `calculatedRepaymentsStartingFromDate` is assigned **only**
in the long private constructor at `:803`; the Builder has no such field and the Builder constructor
(`:304-...`) never assigns it, so on this seam it is null and the shortcut is unreachable
[VERIFIED: `grep -n 'calculatedRepaymentsStartingFromDate' LoanApplicationTerms.java` → `:117, :616, :651, :672,
:726, :754, :803, :1770-1771` and nothing in the Builder]. The port's comment at `generator.go:501-505` says
exactly this and is right. Had it been wrong, **every** due date in the port would be off by one period.

Similarly, `periodStartDate` at `ProgressiveLoanScheduleGenerator.java:94-96` is the expected disbursement date
**iff** `RepaymentStartDateType.DISBURSEMENT_DATE.equals(getRepaymentStartDateType())`. `repaymentStartDateType`
is assigned only at `LoanApplicationTerms.java:873` in the long constructor, so it is **null** on the Builder
path and `.equals(null)` is false — the schedule starts at `submittedOnDate` = `scheduleGenerationStartDate`
[VERIFIED: `:602`]. Port uses `req.ScheduleStartDate`. ✓

**Row ordering.** Disbursements are emitted at the **top** of each period's iteration (`:121`) and the repayment
row at the **bottom** (`:141`); membership is the half-open `!isBefore(periodFromDate) && isBefore(periodDueDate)`
(`:307-308`); there is **no global sort** [VERIFIED: `ProgressiveLoanScheduleGenerator.java:116-145, 299-311`].
So a disbursement dated exactly on period *k*'s due date belongs to period *k+1* and is emitted **after**
repayment *k*. Port: `generator.go:416-444` with `inPeriodM3`. ✓
The disbursement row carries the advanced amount as **both** principal and outstanding balance
[VERIFIED: `LoanSchedulePlan.java:52-56`]. ✓
The installment counter is advanced once per repayment period (`:143`) and additionally by a **down-payment**
row (`:346`) — never by a disbursement row [VERIFIED: `ProgressiveLoanScheduleGenerator.java:340-347`]; down
payment is refused in the graded domain. Port: `generator.go:451-459`. ✓

---

## 3. Mutation testing — 22 counterfactuals derived from the source

Each mutation was applied to a scratch copy and the **real** harness re-run
(`bash .softhouse/conformance.sh`, all 13 parity vectors + 4 refusals + invariants + `--prove`).

### 3.1 Killed by the corpus (the corpus is doing real work)

| # | mutation | source it violates | result |
|---|---|---|---|
| M-E | smoothing adjustment **truncates** instead of HALF_UP | `Money.dividedBy(long)` → `Money.of` → `setScale(2, HALF_UP)` [`Money.java:352-358`, `:52`] | **KILLED**, 2 vectors fail |
| M-G | `getEmiAdjustment` scans **forward** | scan is from the end, `idx > 0` [`PEC:1779`] | **KILLED**, 2 vectors fail |
| M-N | first period's first segment seeded with the disbursement | `updateOutstandingLoanBalance` never assigns it [`InterestPeriod.java:168-179`] | **KILLED**, 1 vector fails |

M-E and M-G are killed **only** by `P-EMI-6-1M014632` / `P-EMI-36-127704`, the two shapes T57 captured this
fire. That closed loop — mutate, find the blind spot, capture the shape, prove the mutation now dies — is
working, and it is the reason those two vectors were worth the fire.

### 3.2 Provably vacuous inside the graded domain — correctly ungraded, NOT a corpus gap

These four survive, and I claim they *cannot* be graded without widening the contract. Recording them so a
future round does not spend a capture on them:

- **M-C2** drop the previous period's unrecognized-interest carry [`RepaymentPeriod.java:261-263`] and
  **M-H** drop the `min(calculatedDueInterest, emi)` cap [`RepaymentPeriod.java:280`]. Both are live only when
  `calculatedDueInterest > emi`. On a level-installment declining-balance schedule with no payments that cannot
  happen: the level installment satisfies EMI ≥ per-period interest by construction, and the final period's
  residual-adjusted EMI equals its own principal **plus** its own interest, hence ≥ its interest. Reachable only
  with **payments** (early/partial repayment), which the seam cannot express.
- **M-I** round each segment to the minor unit *then* add, instead of summing then `Money.of` once
  [`RepaymentPeriod.java:255-257`], and **M-J** compute the growth factor as `Π(1+rᵢ)` instead of `1 + Σrᵢ`
  [`RepaymentPeriod.java:216-218`]. Both are live only when one repayment period has **two segments each
  carrying a non-zero balance**. With `len(Disbursements) == 1` that is impossible: the first segment of the
  first repayment period is never assigned a balance at all, so the split a single disbursement creates always
  leaves exactly one non-zero segment. Reachable only with **multi-tranche**, which the contract refuses.

### 3.3 SURVIVED and money-moving — the corpus is blind

All nine below pass **13 of 13** vectors. For each I state the port's verdict against the source, because
conformance cannot.

| # | mutation | port verdict, from source | separated by an off-lattice shape? |
|---|---|---|---|
| **S-1** | textbook `balance × rateFactor` (3 rounded ops → 1) | **CORRECT** — `InterestPeriod.java:154-157` is three separate mc ops in that order; `emi.go:353-357` reproduces them | not off-lattice, but **YES by sweep — a payable cell, §4.4** |
| **S-2** | rate factor without the trailing `setScale` | **CORRECT** — `PEC:1962` has it; `emi.go:518` `roundScale(v, m.scale)`, and scale ≡ precision is enforced at `generator.go:287-293` | not off-lattice, but **YES by sweep — a payable cell, §4.4** |
| **S-3** | `periodRatio` → `RepaymentEvery` at the interest call site | **CORRECT** — `PEC:1412-1413` passes `periodRatio` into the `repaymentEvery` slot; `PEC:1536-1537` passes `repaymentEvery`. Two call sites, two specifications. `emi.go:469-489` | **YES — MNT 62,595.93** |
| **M-A** | growth factor rounded at 19 sig digits | **CORRECT** — `RepaymentPeriod.java:217` `reduce(ONE, BigDecimal::add)` has **no** MathContext | no |
| **M-B** | `fnValue`'s outer `add` unrounded | **CORRECT** — `PEC:1992` `ONE.add(…, mc)` rounds | no |
| **M-D** | `calculateEMIValue`'s two roundings collapsed into one | **CORRECT** — `PEC:1840` is `multiply(…, mc).divide(…, mc)` | no |
| **M-F** | `shouldBeAdjusted` `>` → `>=` | **CORRECT** — `isGreaterThan` is strict [`EmiAdjustment.java:33`, `Money.java:438`] | boundary shape needed |
| **M-K** | adoption test `<` → `<=` | **CORRECT** — `hasLessEmiDifference` is strict [`EmiAdjustment.java:47`] | boundary shape needed |
| **M-L** | smoothing loop bound 3 → 30 | **CORRECT** — `do { … } while (adjustCounter <= 3)` [`PEC:1308`] | no |
| **M-M** | `calculateSeedDate` always returns the schedule start | **CORRECT** — both conjuncts required [`PEC:1477-1480`] | **YES — MNT 8,545,743.02** |
| **M-O** | month-end special case in `periodRatio` removed | **CORRECT** — `PEC:1432-1436` | no (consistent with T46: the special case **is** the compensation for the packed whole-month rule, so it cancels) |
| **M-P** | re-anchor guard `>=28` → `>28` | **CORRECT** — `DefaultScheduledDateGenerator.java:169` | **YES — MNT 44,960.29** |

**No mutation I could construct exposed a defect in the port.** Every one of them makes the port *wrong* and
every one of them is a reading the source refutes.

---

## 4. What shape would grade the survivors — with measured margins

T10's brief asks for shapes "concrete enough that a capture task could execute it". Here they are, with the
money each one moves. All four probe shapes are **inside the graded domain** — the port answers them
[VERIFIED: `/tmp/t11mut/.../t11dump_test.go`, `t11sep_test.go`].

### 4.1 The off-lattice family — kills S-3, M-M and M-P at once

The mechanism is the **two seeds**: the month-end re-anchor is seeded on the **disbursement**, `calculateSeedDate`
on the **schedule start**. Every promoted vector has `ScheduleStartDate == Disbursements[0].Date` (or a day-1
start), so every period sits on the schedule-start lattice and nothing separates. **Move the two apart by one or
two days across a month end and the lattice breaks from period 2 onward.**

Named shape **S1**: `ScheduleStartDate 2024-01-29`, disbursement `2024-01-31`, 12 × monthly, 18.5 %, MNT 5,000,000.
Measured: 11 of 12 periods leave the schedule-start lattice, and `periodRatio` is `1.0645161290322580645` /
`1.0322580645161290323` on 5 of 12 periods — i.e. **≠ RepaymentEvery (= 1)**
[VERIFIED: probe output, `periodRatioSeed` and `periodRatio` printed per period].

| mutation | S1 (12×18.5%, MNT 5M) | S2 (36×16.8%, MNT 50M) | S4 (24×18.5%, start 30 / disb 31) | S3 on-lattice control |
|---|---|---|---|---|
| S-3 `periodRatio`→`RepaymentEvery` | 34 cells, max **457,495** minor | 106 cells, max **6,259,593** minor | 70 cells, max **505,908** minor | **0 cells** |
| M-M seed always schedule start | 34 cells, max **4,401,604** minor | 106 cells, max **854,574,302** minor | 70 cells, max **7,684,179** minor | **0 cells** |
| M-P `>=28` → `>28` | 0 | 61 cells, max **4,496,029** minor | 49 cells, max **361,253** minor | **0 cells** |

At MNT minor unit 2, M-M's worst is **MNT 8,545,743.02** on a MNT 50,000,000 loan. The on-lattice control moves
**zero** cells for all three — which is precisely why 13 vectors and 1,350 cells see none of it.

### 4.2 The rounding-placement class — S-1, S-2, M-A, M-B, M-D

These five all perturb the arithmetic at the ~10⁻¹⁹ relative level and are invisible on all 13 vectors **and on
all four off-lattice probes**. They sit below the currency layer, so a separating shape must land the exact EMI
within ~10⁻¹⁹ relative of a half-minor-unit boundary: such a shape must be **searched for**, not designed. I ran
that search — **and found one for S-1 and one for S-2.** See §4.4.

### 4.3 The strict-inequality boundaries — M-F and M-K

M-F needs `|lastEMI − penultimateEMI|` to equal `floor(n/2)` **whole currency units exactly**, evaluated on the
**pre-smoothing** model — screening on the oracle's emitted schedule is the error `patterns.md` P-2 names, and I
avoided it by exposing a pre-smoothing entry point in the scratch copy. M-K needs a trial whose new difference
*equals* the old one. Both are enumerable by sweep over principal at fixed `n`; see §4.4.

### 4.4 The sweep — S-1 and S-2 ARE separable, and here are the two shapes

I swept 6,000 in-graded-domain shapes (5 rates × 6 monthly installments × 1,200 principals spread over five
orders of magnitude), running each of the five rounding-placement counterfactuals in-process against the port:

```
SWEEP shapes tried = 6000
SWEEP SURV-1 textbook        separating shapes = 6   max margin(minor) = 4   MNT 2102158750 minor, 6x, rate 27/125
SWEEP SURV-2 no-setScale     separating shapes = 2   max margin(minor) = 1   MNT  313984586 minor, 6x, rate 7/100
SWEEP M-D emi-one-round      separating shapes = 0
SWEEP M-A growth-rounded     separating shapes = 0
SWEEP M-B fn-no-round        separating shapes = 0
```

**So the two headline survivors are not merely "capturable in principle" — they are capturable now, at a
density of roughly 1 in 1,000 on the simplest possible shape.** Both separating requests are ordinary
on-lattice loans: `ScheduleStartDate == Disbursements[0].Date == 2024-01-01`, monthly, 30/360, HALF_UP, MNT.

**Named shape for S-1 — `MNT 21,021,587.50`, 6 × monthly, 21.6 %:**

| row | due | port (correct) P / I / OS | counterfactual P / I / OS |
|---|---|---|---|
| 1 | 2024-02-01 | 334921682 / **37838857** / 1767237068 | 334921682 / **37838858** / 1767237068 |
| 2 | 2024-03-01 | **340950272** / 31810267 / **1426286796** | **340950273** / 31810267 / **1426286795** |
| 6 | 2024-07-01 | **366169491** / 6591051 / 0 | **366169487** / 6591051 / 0 |

(rows 3–5 diverge likewise; the outstanding balance drifts to a **4 minor-unit** gap by the final row)

**Named shape for S-2 — `MNT 3,139,845.86`, 6 × monthly, 7.0 %:**

| row | due | port (correct) P / I / OS | counterfactual P / I / OS |
|---|---|---|---|
| 2 | 2024-03-01 | 51873628 / **1530735** / 210538172 | 51873627 / **1530736** / 210538173 |
| 3 | 2024-04-01 | 52176224 / 1228139 / **158361948** | 52176224 / 1228139 / **158361949** |

[VERIFIED: `/tmp/t11mut/.../t11sweep_test.go`, `t11named_test.go`; the counterfactual is selected by a
package-level flag in the scratch copy so both readings run in one process on identical input.]

Note **what** moves: an **interest** cell on row 1/2 and a **principal** cell thereafter. These are payable
amounts, which is exactly the claim `contract.go` makes about the trailing `setScale` — *"the loss reaches a
payable amount"* — now demonstrated on a concrete request rather than argued.

**M-D, M-A and M-B were not separated in 6,000 shapes.** That is a statement about the search, not about the
mutations: all three are non-vacuous (each drops or adds a rounding the source specifies), and the S-1/S-2
result shows this class *does* surface at low density. A wider sweep over **term** is the obvious next step —
`patterns.md` already records that precision 19 vs 12 was invisible across 16 shapes and then separated at 360
periods, and that the separation is **not monotone in principal**.

**The M-F / M-K strict-inequality boundary was NOT located.** I swept 3,000 principals at n ∈ {6, 12} for
`|lastEMI − penultimateEMI| == floor(n/2)` whole currency units, evaluated on the **pre-smoothing** model
(exposing a pre-smoothing entry point rather than screening on the emitted schedule — `patterns.md` P-2), and
found none. Recorded as an unfinished search, not as a closed question.

---

## 5. The decisive result: 15 oracle observations already in the tree reproduce cell-for-cell

`contract.go:744-762` records that task **T39 captured 8 drift shapes from the pinned reference oracle** and that
the oracle agreed with `periodRatio` on 415 of 415 disagreeing cells. **Those captures are committed** at
`.softhouse/capture/periodratio/out/t39-periodratio.json` — 16 captures, at `mathContextPrecision: 19`,
`mathContextRoundingMode: HALF_UP`, `currencyDecimalPlaces: 2`, `tenantRoundingModeOrdinal: 4`,
`ambientMoneyHelperMathContext: precision=19 roundingMode=HALF_UP`.

**They were never promoted into `.softhouse/vectors/`.** So the harness has never graded the port against them.

I replayed all 16 against the port, comparing **every** principal, interest, outstanding-balance and date cell:

```
REPLAY T39-CAL      SKIPPED (precision 12 — outside the graded domain)
REPLAY T39-CTL-Q0a  start=2024-01-01 disb=2024-01-01 n= 6 rate=21.6  cells=19  bad=0  MATCH
REPLAY T39-CTL-1    start=2024-01-01 disb=2024-01-01 n= 6 rate=7.0   cells=19  bad=0  MATCH
REPLAY T39-CTL-2    start=2024-01-15 disb=2024-01-15 n= 6 rate=21.6  cells=19  bad=0  MATCH
REPLAY T39-P0-A     start=2024-01-28 disb=2024-01-31 n= 6 rate=21.6  cells=19  bad=0  MATCH
REPLAY T39-P0-B     start=2024-01-28 disb=2024-01-29 n= 6 rate=21.6  cells=19  bad=0  MATCH
REPLAY T39-P0-C     start=2024-01-29 disb=2024-01-31 n=12 rate=16.8  cells=37  bad=0  MATCH
REPLAY T39-P0-D     start=2024-01-28 disb=2024-01-31 n=36 rate=21.6  cells=109 bad=0  MATCH
REPLAY T39-P0-E     start=2025-01-28 disb=2025-01-31 n= 6 rate=21.6  cells=19  bad=0  MATCH
REPLAY T39-P0-F     start=2024-01-28 disb=2024-01-31 n= 6 rate=21.6  cells=19  bad=0  MATCH   (MNT 100 principal)
REPLAY T39-P0-G     start=2024-03-28 disb=2024-03-31 n= 6 rate=16.8  cells=19  bad=0  MATCH
REPLAY T39-P0-H     start=2024-11-28 disb=2024-11-30 n= 6 rate=16.8  cells=19  bad=0  MATCH
REPLAY T39-ME-A..D  month-end special case, 4 shapes              cells=19 ea bad=0  MATCH
```

[VERIFIED: `/tmp/t11mut/.../t11t39_test.go`, decimal strings parsed to minor units by exact integer string
manipulation — **no float anywhere in the comparison**; 393 cells across 15 captures, zero mismatches.]

**Consequence — and this is the most important sentence in this review:**

> **Survivor 3 is no longer only re-derived. It is CLOSED BY OBSERVATION.** The port's `periodRatio` reading
> reproduces 8 oracle-observed drift shapes, on the very shapes where the `RepaymentEvery` reading moves
> MNT 62,595.93. The evidence needed to kill the corpus's largest known blind spot **already exists in the
> committed tree** and requires no oracle run — only a promotion.

Promoting `T39-P0-A … T39-P0-H` (and `T39-ME-A … D` as month-end controls) would kill **S-3, M-M and M-P**
simultaneously. That is 3 of the 9 surviving money-moving mutations, including the two largest margins in this
review, for the cost of a promotion task.

---

## 6. Defects found in the port

### F-1 (P1) — `Generate` accepts a `context.Context` and then ignores cancellation for the whole computation

`ctx.Err()` is read **once**, at `generator.go:72-74`, before any work. `generate()` takes no `ctx` and nothing
downstream consults it. Measured:

```
CANCEL pre-cancelled ctx, n=240 -> err=context canceled  elapsed=0s
CANCEL 50ms deadline,     n=240 -> err=<nil>             elapsed=5.902s  (deadline honoured = false)
```

[VERIFIED: `/tmp/t11mut/.../t11sep_test.go` `TestT11Cancel`.]

A caller that sets a deadline gets no deadline. Behind the frozen contract this is the difference between a
request timing out and a request pinning a core until it finishes. **Severity is about what it lets through:**
combined with F-2 it makes an unbounded-CPU surface reachable from a single well-formed request, with no way
for the caller or the server to abort it. Fix is small — thread `ctx` into the per-period loops and check it —
but the API currently makes a promise it does not keep.

### F-2 (P2) — superlinear cost, and `NumberOfRepayments` has no upper bound

```
PERF n= 12  elapsed=13ms      PERF n=120  elapsed=1.022s
PERF n= 36  elapsed=90ms      PERF n=240  elapsed=5.995s
PERF n= 60  elapsed=250ms     PERF n=360  elapsed=13.261s
```

[VERIFIED: `/tmp/t11mut/.../t11perf_test.go`, MNT 5,000,000 at 7.0 %.] Roughly **n^2.4**.

The cause is stated in the port's own header: the oracle memoises the four derived quantities
(`RepaymentPeriod`'s `Memo` fields, invalidating on a dependency hash [`Memo.java:56-72`]) and *"this port
recomputes on every read, which is the same function without the cache."* It **is** the same function. It is not
the same cost: `duePrincipalMinor` and `dueInterestMinor` each walk `interestChainUpTo(idx)` from period 0, and
they are called from `updateOutstandingBalances`, `applyFinalPeriodResidual` and the row emitter, so the whole
generation is quadratic-to-cubic in `n` over 19-digit rational arithmetic.

`validateWellFormed` requires only `NumberOfRepayments >= 1` [`generator.go:139-141`] and the graded domain adds
no bound — the contract explicitly says so [`contract.go:1134-1137`: *"NumberOfRepayments >= 1 … is a
WELL-FORMEDNESS condition"*]. So `NumberOfRepayments = 100000` is a well-formed, in-graded-domain request.

Even without an adversary: **a 30-year monthly loan is an ordinary NBFI product and costs 13 seconds per
schedule today.** Memoising the interest chain (one forward pass cached per model mutation) is a local change
that does not alter the arithmetic; it is what the oracle already does.

### F-3 (P2) — G-5: the zero-rate answer is a number backed by no oracle observation

**T10's interim call is right and I would not change it.** Implementing DEC-1's *enumerated list* keeps the port
and the grader consistent with each other, and a ratified DEC-n is not an agent's to amend. I am not amending it.

But the consequence should be on the record rather than left implicit. The port **answers** a zero-rate request:

```
PROBE2 zero rate, 6 x MNT 1,000 -> err=<nil>, 7 rows, P=166.67 x5 + 166.65, I=0 on every row
```

[VERIFIED: `/tmp/t11mut/.../t11probe_test.go`.] The only thing backing that answer is `SELFTEST-01`, which the
harness itself labels *"hand-authored; EXCLUDED from the parity count"* [VERIFIED: conformance summary line
`self-test fixtures PASS 1 (hand-authored; EXCLUDED from the parity count)`]. So whichever way G-5 resolves, the
port is currently returning an ungraded number where DEC-1's prose says it should return a sentinel.

**Cheapest resolution, and it does not need the gate answered:** take a zero-rate capture from the oracle. One
run converts a hand-authored fixture into an observation, and it makes the *list* reading defensible on evidence
rather than on consistency-with-the-grader. If the oracle refuses or throws on a zero rate, that settles G-5 in
the other direction at the same cost.

### Not a finding — int64 overflow, probed and not reproduced

`applyFinalPeriodResidual` sums every period's EMI into one `int64` (`emi.go:684-692`), which overflows for a
principal near `int64` max. I probed `AmountMinor = 9223372036854775807` and the schedule came back
self-consistent (principals summed exactly to the disbursement, no negative cell) because the wraparound cancels
in the subsequent subtraction. **I could not construct a wrong answer, so I am not filing this as a defect** —
recording it only so the next reviewer does not spend the same hour. [VERIFIED: `TestT11ProbeOverflow`.]

---

## 7. Hygiene, determinism, and the non-negotiables

| check | result |
|---|---|
| `float32` / `float64` / `big.Float` / `ParseFloat` in the three port files | **none** (comment text only) [VERIFIED: grep] |
| money quantities | `int64` minor units throughout; `math/big.Rat` for exact rationals, `math/big.Int` for the rounding primitive |
| clock / locale / env / `rand` | **none** [VERIFIED: grep for `time.Now`, `time.Local`, `time.LoadLocation`, `os.Getenv`, `rand.`] |
| map iteration order | **no maps at all** in the port [VERIFIED: grep `map[`] |
| hard-coded UTC offset | none; `+08`/`+07` appear only in prose. Time zone is an IANA **name**, fixed offsets rejected [`generator.go:196-248`] |
| database / US rails / deposit surface | **none** — no `pgx`, `sql`, `postgres`, `oracle.jdbc`, `mysql`, `stripe`, `plaid`, `deposit`, `savings`, `insured`, `guaranteed`, `first_name`, `last_name` [VERIFIED: grep] |
| `go build ./...` | clean |
| `go vet ./internal/apps/loanschedule/...` | clean |
| `go test ./internal/apps/loanschedule/...` | `ok` (both packages) |
| `gofmt -l` | flags **only** `contract/contract.go` — expected and correct under gate **G-3**; I did not touch it |
| division by zero on the `big.Rat` paths | all five `Quo` sites guarded or provably non-zero [checked individually: `emi.go:350`, `:509`, `:566-570` (span ≥ 28 days), `:636` (`fn ≥ 1` since rates are non-negative)] |
| frozen artefacts | `contract.go`, every vector, `capabilities.json`, `PIN.json` **unmodified** [VERIFIED: `git diff --stat main -- …` empty] |

Determinism note: `Generate` is a pure function of its request. The time zone genuinely cannot enter the
arithmetic — every date is a `contract.CivilDate` and every calendar operation is integer arithmetic on
year/month/day, with `epochDay`/`fromEpochDay` transcribed from `java.time.LocalDate` rather than routed through
an instant [`generator.go:641-703`]. ✓

---

## 8. Required changes

Severity is what a defect would let through, not how hard it is to fix.

### On the port

- **F-1 (P1)** — thread `ctx` through generation and check `ctx.Err()` per repayment period. An API that takes a
  `context.Context` and ignores cancellation for 6 seconds is making a promise it does not keep, and it is what
  turns F-2 into an availability surface.
- **F-2 (P2)** — memoise the interest chain (one cached forward pass, invalidated on model mutation, exactly as
  `Memo` does in the oracle), or bound `NumberOfRepayments` in the contract. 13 s for a 360-period schedule is a
  production cost on an ordinary product, not a hypothetical.

### On the corpus — these are findings about the corpus, not the port

- **C-1 (P1)** — **Promote `T39-P0-A … T39-P0-H` and `T39-ME-A … D` as parity vectors.** They are committed
  oracle observations at `(19, HALF_UP)`, they are inside the graded domain, and the port already reproduces all
  393 cells. Promoting them kills S-3 (MNT 62,595.93), M-M (MNT 8,545,743.02) and M-P (MNT 44,960.29). **No
  oracle run is required.** This is the single highest-value, lowest-cost item in this review, and the fact that
  a live-oracle capture has sat unpromoted for two fires while the same blind spot was re-derived three times is
  itself the finding.
- **C-2 (P1)** — **capture these two named shapes**, which separate S-1 and S-2 in a *payable amount* (§4.4).
  Both are ordinary on-lattice MNT loans, `start == disbursement == 2024-01-01`, monthly, 30/360, HALF_UP —
  two oracle runs, no special rig:
  - **MNT 21,021,587.50, 6 × monthly, 21.6 %** — kills S-1 (textbook `balance × rateFactor`); diverges on all
    six rows, interest by MNT 0.01 on row 1 and outstanding by MNT 0.04 by row 6.
  - **MNT 3,139,845.86, 6 × monthly, 7.0 %** — kills S-2 (rate factor without the trailing `setScale`);
    interest on row 2 is MNT 15,307.35 vs MNT 15,307.36.

  This is the folklore that has cost this program the most: a rounding step twice dismissed as "redundant" and
  twice found to be a money defect (`patterns.md`, Run 1). It has been argued from source three times and
  observed **zero** times. Two captures end the argument.
- **C-3 (P2)** — **M-A, M-B, M-D** (the rest of the rounding-placement class) and the strict-inequality
  boundaries **M-F** and **M-K** were **not** separated in my sweep — 6,000 shapes for the former, 3,000 for
  the latter. Record these as *unfinished searches*, not as backlog items: S-1/S-2 prove the class surfaces, so
  widen the sweep over **term** (not principal — `patterns.md` records the separation is not monotone in
  principal). For M-F/M-K the target is `|lastEMI − penultimateEMI| == floor(n/2)` whole currency units
  evaluated on the **pre-smoothing** model — never on the oracle's emitted schedule (`patterns.md` P-2).
- **C-4 (P2)** — **take a zero-rate capture** (F-3). It costs one oracle run, converts `SELFTEST-01` from
  hand-authored to observed, and settles G-5 on evidence either way.
- **C-5 (P2, informational)** — record M-C2/M-H and M-I/M-J as **vacuous inside the graded domain** with the
  arguments in §3.2, so a future round does not spend captures trying to grade behaviour the contract's own
  refusals make unreachable. *"Not captured"* and *"not capturable"* are different facts.

### On the process

- **P-5 recurrence (P2)** — the worktree was cut from `2c0adab`, five commits before the artefact existed. Third
  time in two fires. The written rule is not being enforced by anything; make the dispatcher verify the artefact
  path exists in the worker's tree before handing it over.

---

## 9. Verdict

The port is **faithful**. I re-derived every money path from the Java — the fold-accumulator EMI with no `pow`,
the three separately rounded interest operations, the rate factor's trailing `setScale`, the two rate-factor
call sites, the two distinct date seeds, the residual on the last unpaid period's EMI, the smoothing loop's five
easy-to-get-wrong details — and found **no arithmetic defect**. I constructed 22 counterfactuals from the source
and **none of them exposed a defect**; every one is a reading the source refutes and the port does not hold.
And the port reproduces **393 cells of 15 live-oracle observations**, including 8 drift shapes that no promoted
vector resembles, with **zero** mismatches.

The two defects I did find are real but neither is money: an ignored `context.Context` and a superlinear cost
with an unbounded input. The larger finding is about the **corpus**: nine money-moving wrong implementations
survive all 13 vectors, three of them by margins up to MNT 8.5 million — and the evidence to kill those three
is already sitting in the tree, uncaptured into the vector store. Two more are killed by two named ordinary
loans that cost one oracle run each. **Five of the nine survivors can be closed this fire, and three of them
need no oracle at all.**

> ## ACCEPTED WITH REQUIRED CHANGES
>
> **P1:** F-1 (context cancellation ignored); C-1 (promote the T39 drift captures — no oracle run needed);
> C-2 (capture the two named shapes that separate the rounding-placement survivors in a payable amount).
> **P2:** F-2 (superlinear cost, unbounded `NumberOfRepayments`), F-3/C-4 (zero-rate answer unbacked by any
> observation), C-3, C-5, and the P-5 worktree recurrence.
>
> None of this is a cutover recommendation. A green conformance run means "matches the reference oracle on
> captured vectors, within the graded domain" — and this review's main result is a measurement of how much that
> sentence still leaves out. **Cutover remains a `user` gate.**
