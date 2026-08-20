# T75 — independent review of `softhouse/T74-pathA-multiplesof`

**Reviewer:** T75, independent. I did not plan T74 and did not observe it run.
**Subject:** branch `softhouse/T74-pathA-multiplesof`, five commits, `git diff main...` = 33 files,
20,365 insertions. **Six vectors promoted**, corpus 36 -> 42.
**Reviewed against:** the branch's own bytes (`git show branch:...`, `git diff main...branch`), the
pinned reference oracle (Fineract) at `426a23544e8426a38ae43ae404670a0a7e85b9eb`, and a **live run
of the oracle image** for one question T74 left open.

> "The oracle" throughout is the **Fineract reference implementation**. Oracle Database is a
> prohibited product in this program and appears nowhere in this work or this review.

**Pinned checkout hygiene:** `/Users/buv/fineract` was at `426a23544` and `git status --porcelain`
empty before my work and after it. No commit, no edit, no branch change, no worktree added there.
My mutated-seam attack ran against a `git clone --shared` at `/tmp/t75fake`, since deleted.

**Shared oracle hygiene:** the two containers were `Up ... (healthy)` before and after. My own probe
(§5) is the same in-JVM Path A seam T74 uses: **no Fineract server started, no database connection
opened, no `c_configuration` write, no container restart, no tenant edit, no REST call.**

---

## VERDICT: **APPROVED**

The six promoted vectors are sound. Every graded cell traces to a raw observation; the
counterfactual is a genuine observation pair and I re-derived it from the two capture arms myself;
the vectors are **not** vacuous — my own independent mutation turns all six red. The branch's
strongest claim (that all multiples-of money movement belongs to `CurrencyData.inMultiplesOf`
alone) is verified from source *and* from the captures, and the harness change that licenses it is
real in all three places it had to be real. The pass-3 supersession reasoning is correct, including
the part I most expected to be wrong.

I found **seven accuracy defects**, all in prose, comments, a `note` string or one line of dead
code. **None touches a vector cell, a money value or any money logic.** They are listed in §9 as
record corrections. I also **settled T74's open follow-up F-2 by capture**, and the answer is
material — see §5. That is a program finding, not a defect in this diff; T74 named the candidate
precisely enough that I could run it, which is the behaviour this pipeline wants.

---

## 1. The six promoted vectors — do they trace to an observation?

**YES. 876 of 876 money cells, zero discrepancies.** [VERIFIED: my own transcription check,
independent of `T74-promote-vectors.py`]

I wrote my own verifier that reads `.softhouse/capture/out/capture-prod3i-raw.json`
(sha256 `e0ea0bcf...cde430`, matching every vector's `provenance.capture_sha256`) and re-derives
each vector's `expect` block from the named capture case by exact textual major->minor scaling
(`Decimal.scaleb`, integral assertion, no float). For each of the six:

| vector | capture case | periods | money cells re-derived | discrepancies |
|---|---|---|---|---|
| `T74-E-P4` | `T74-E-P4` | 37 | 146 | 0 |
| `T74-E-P59` | `T74-E-P59` | 37 | 146 | 0 |
| `T74-E-P72` | `T74-E-P72` | 37 | 146 | 0 |
| `T74-E-P340` | `T74-E-P340` | 37 | 146 | 0 |
| `T74-E-P426` | `T74-E-P426` | 37 | 146 | 0 |
| `T74-E-P6940` | `T74-E-P6940` | 37 | 146 | 0 |

The check also re-derived, per vector, the request block against the capture's own `inputs`
(principal, term, frequency, decimal places, precision, mode, currency code, both dates, interest
method, and the rate as an exact rational `21/125 == 16.8 %`), the `*_major_text` cross-check
fields against the oracle's emitted characters, the DISBURSEMENT row's `unrecorded_fields`, and
`observed_total_interest_minor`. **Both multiples-of inputs are `null` on all six**, in the capture
itself.

**Stronger check — nothing was hand-edited into a vector after generation.** I deleted the six
committed vectors from a scratch copy and re-ran the author's own
`.softhouse/handoff/T74-promote-vectors.py`. All six regenerated files are **byte-identical** to
the committed ones (`cmp` clean, 6/6). [VERIFIED: re-run at `/tmp/t75rep`]

### Non-vacuity — I ran the mutation myself

I did **not** reuse the author's `/tmp/t74mut`. I mutated a fresh copy of the port at three points
in `nexus/internal/apps/loanschedule/generator.go` — `precision:` (:503), `scale:` (:504) and the
rate rounding argument (:512) — from `req.Rounding.SignificantDigits` / `RateFactorScale` to a
hard-coded `12`, asserting each replacement was unique.

```
BASELINE (branch, unmutated)   parity PASS 42  FAIL 0   5576 graded  102 money kills   exit 0
MUTATED (precision 12)         parity PASS 34  FAIL 8   invariant violations 8         exit 1
```

The eight are `P-01`, `P-RND-S1` and **all six `T74-E-*`**. [VERIFIED: my run]

So the author's **corrected** count is exactly right: this defect was caught by **2 of the previous
36** and is caught by **8 of 42** now. The two pre-existing catchers are MNT 87,654,321 and
MNT 21,021,587.50; the six new ones run MNT 4.00 to MNT 6,940.00. I confirm the substantive point:
precision sensitivity here is a rounding-boundary property of the `(principal, n, rate)` triple,
not of magnitude — `P-MNT-50M` is the *same* `36 x 16.8 %` shape at MNT 50,000,000 and stays green
under the mutation.

I also confirm the author's self-correction was the *honest* direction: the first reading named only
`P-01`, and `PASS 34 FAIL 8` did not add up to it. Recounting gives two. Recording that in the
handoff rather than quietly fixing it is the P-16 behaviour this pipeline asks for.

### The counterfactual: it really does contain no model

`MATHCONTEXT-PRECISION-12-INSTEAD-OF-RATIFIED-19`. Both arms are capture cases in the **same
artefact** from the **same run** (`T74-E-P4` and `T74-E-P4-p12`, etc.).

I re-derived, from the two capture arms alone, the exact set of divergent graded cells for each
shape and compared it with the committed
`.softhouse/capture/t74-multiplesof/out/t74-counterfactuals-pass3i.json`:

| shape | counterfactual claims | I re-derived | set-equal |
|---|---|---|---|
| P4 | 23 of 146 | 23 | **yes** |
| P59 | 27 of 146 | 27 | **yes** |
| P72 | 2 of 146 | 2 | **yes** |
| P340 | 25 of 146 | 25 | **yes** |
| P426 | 39 of 146 | 39 | **yes** |
| P6940 | 18 of 146 | 18 | **yes** |

Every `margin_minor` equals the maximum absolute single-cell delta of its own set (1, 1, 1, 1,
**2** for P426, 1). Every `evidence` string's "diverges on N of 146" matches. [VERIFIED]

And the mutation output matches the counterfactual **cell for cell** — for `T74-E-P4` the harness
reports row 17 `principal 10 -> 11`, row 17 `interest 4 -> 3`, rows 17-35 `outstanding -1`, row 36
`principal 24 -> 23`, plus `splits_sum_to_whole VIOLATED` on the 23rd cell (row 36
`observed_total_due_minor`, which the store consumes as an invariant input rather than a direct
parity cell). That is the same 23 cells I derived from the two oracle arms. **A counterfactual
measured from the oracle predicted, exactly, what a port defect does.** That is the strongest
counterfactual evidence in this store and the claim is justified.

`build-counterfactuals.py:66-76` does assert input equality field by field, refusing any pair
differing outside an allow-set. See defect **N3** in §9 about what that allow-set actually contains.

---

## 2. The multiples-of rule, re-derived from pinned source

All line numbers are at `426a23544`. [VERIFIED: source read directly]

**The gate is FOUR conjuncts. The author is right and the previously documented three were
incomplete.** `Money.java:48-49`, in the private constructor `Money.java:40-53`:

```java
if (currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 && currency.getInMultiplesOf() > 0
        && MathUtil.isGreaterThanZero(amountScaled)) {
```

1. `currency.getInMultiplesOf() != null` — :48
2. `currency.getDecimalPlaces() == 0` — :48
3. `currency.getInMultiplesOf() > 0` — :48
4. `MathUtil.isGreaterThanZero(amountScaled)` — **:49**, `value != null && value.compareTo(ZERO) > 0`
   [VERIFIED: `MathUtil.java:196-198`]

Conjunct 4 guards the **input**: a zero or negative amount is not rounded. It is **not** the
zero-guard the installment channel has, which guards the **output** (a positive EMI that would
round to zero). The author's distinction between the two is correct and it is the whole basis of
§4's finding (b).

**The rule is round-to-NEAREST under the tenant mode.** The constructor calls the two-argument
`BigDecimal` overload at `Money.java:150-157`:
`existingVal.divide(inMultiplesOfValue, 0, MoneyHelper.getRoundingMode()).multiply(inMultiplesOfValue)`,
guarded by its own `inMultiplesOf > 0` test at :153. Scale-0 division under HALF_UP is nearest, ties
away from zero — not floor. The `Money`-typed overloads at `:159-161` / `:163-170` are the same rule
but take the mode from a `MathContext` parameter (`:167`) defaulted to `MoneyHelper.getMathContext()`.
Note `amountScaled` is `stripTrailingZeros()`'d at `:45` *before* the gate.

**Channel 2** is `ProgressiveEMICalculator.applyInstallmentAmountInMultiplesOf` at **:1761-1766**,
gated on `scheduleModel.installmentAmountInMultiplesOf()`, delegating to `safeRoundingForEMI` at
**:1770-1776**, whose zero-guard is `if (roundedEMI.isZero() && unRoundedEMI.isGreaterThanZero())
return unRoundedEMI;`. Its three call sites are :1270, :1636, :1734. The author's cited range
`:1761-1776` is right.

**Money handled as integer minor units throughout the diff.** No float in `Capture3i.java`
(`BigDecimal` only), and the four Python tools scale by exact integer string arithmetic and refuse a
significant digit beyond the currency scale rather than rounding a transcription. The harness's own
`guard_no_float_in_vectors` passes on the new files. [VERIFIED]

*Aside, not a finding against T74:* `Money.java:134-148` carries a `double`-based
`roundToMultiplesOf` with `Math.ceil`/`Math.floor`. It is Fineract's, it is not on this path, and
nothing in this diff touches it — but any Go port must not reach for it as the reference.

---

## 3. The strongest claim: is the split real, and is the blindness observed?

**YES on both, and the split is real in all three of the places it had to be.**
[VERIFIED: `Capture3i.java`]

| where | line | what it does |
|---|---|---|
| `record Case` | :142-145 | two components, `currencyMultiplesOf` and `installmentMultiplesOf` |
| model construction | :663-664 | `new CurrencyData(code, code, digits, **c.currencyMultiplesOf()**, ...)` — the 4th argument, which is `inMultiplesOf` [VERIFIED: `CurrencyData.java:59,64`] |
| model construction | :666-670 | `LoanRepaymentScheduleModelData(...)` receives `**c.installmentMultiplesOf()**` at positional argument **13**, which is that record's `installmentAmountInMultiplesOf` component |
| emitted JSON | :696 | `"currencyInMultiplesOf": c.currencyMultiplesOf()` |
| emitted JSON | :702 | `"installmentAmountInMultiplesOf": c.installmentMultiplesOf()` |

Two different components, two different arguments, two different keys. Confirmed independently by
the data: `T74-A1` emits `(cur=100, inst=null)` and `T74-A2` emits `(cur=null, inst=100)` — an
aliased harness cannot produce both.

**Byte-identity, checked from the captures themselves** (canonical JSON of each `observed` block):

| pair | `observed` byte-identical | inputs that differ |
|---|---|---|
| `T74-A2-DP0-INST100` vs `T74-A0-DP0-NONE` | **yes** | `installmentAmountInMultiplesOf` null->100, tenantId |
| `T74-A3-DP0-BOTH100` vs `T74-A1-DP0-CUR100` | **yes** | `installmentAmountInMultiplesOf` null->100, tenantId |
| `T74-D2-DP0-SMALL-INST1000` vs `T74-D0-DP0-SMALL-NONE` | **yes** | `installmentAmountInMultiplesOf` null->1000, tenantId |
| `T74-B2-DP2-INST100` vs `P-CAL-MNT5M` | **yes** | `installmentAmountInMultiplesOf` null->100, tenantId |

Four independent installment-only arms, four byte-identical answers. **The blindness is now
OBSERVED**, not only derived. [VERIFIED]

**The source agrees, and I checked the part that matters most.** `LoanRepaymentScheduleModelData`
*does* carry an `installmentAmountInMultiplesOf` component — so the seam **accepts** the input and
**silently drops it**. `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
at `:579-607` contains zero occurrences of `MultiplesOf` and builds only through `Builder`; the
`Builder` class body (`:353-577`) contains zero occurrences of `MultiplesOf`, so there is no setter
and no builder field; and the `Builder`-taking constructor at `:304-351` never assigns
`this.installmentAmountInMultiplesOf`, whose sole assignment in the file is `:828` in a positional
constructor this path never reaches. [VERIFIED]

**One residual gap the recipe cannot close, named for the record.** Precondition 16b proves the two
*emitted keys* are independent; it cannot prove the *model* got what the JSON says. A harness that
aliased the model while emitting honestly would defeat it. But the **data refutes that scenario**:
if `T74-A2`'s model had actually received `inMultiplesOf = 100`, it would have moved money (`T74-A1`
proves the channel moves 106 minor units on that shape), and `T74-A2` is byte-identical to the
`(null, null)` baseline. The claim survives the attack.

---

## 4. The two surprising money-moving behaviours, and the reassuring one

All three verified **from the capture**, not from the report. [VERIFIED:
`capture-prod3i-raw.json`]

**(a) The channel rounds the disbursed principal itself.** `T74-C4-DP0-CUR7` requested
MNT 5,000,000 at `inMultiplesOf = 7` and the oracle emitted `totalDisbursedAmount` **5,000,002**,
with the DISBURSEMENT row's `principal` and `balance` both `5000002`. The arithmetic is exactly the
constructor's: `assembleFrom:580` builds `Money.of(currency, disbursementAmount, mc)` straight
through the leaking constructor; `stripTrailingZeros` gives `5E+6`;
`divide(7, scale 0, HALF_UP)` = 714286; `x 7` = 5,000,002. **A borrower is lent two tugriks nobody
asked for**, and the schedule then amortizes them correctly.

**(b) The channel has no zero-guard.** `T74-D1-DP0-SMALL-CUR1000` (MNT 1,000 / 6 x 21.6 %,
`inMultiplesOf = 1000`) returns EMIs `['0','0','0','0','0','1000']`, `totalInterestAmount` **0**,
and **every one of the six rows carries `balance 1000`** — including the row that repays the whole
principal. Its `(null, null)` baseline `T74-D0` amortizes correctly (`175 ... balance 0`).
`safeRoundingForEMI` exists precisely to stop this and does not fire, because it belongs to the
channel this seam never reaches. The author's framing — *a mechanism identified by the absence of
the guard that would have stopped it* — is accurate.

Round-to-**nearest** is confirmed on the same family: `T74-A1` period 1 emits interest **77100** for
an exact 77,083.33 (`77083/100 = 770.83`, HALF_UP at scale 0 -> 771, x100 -> 77100). Floor would
give 77,000. `inMultiplesOf` of **0** and **-100** are inert (`T74-C2`, `T74-C3` byte-identical to
`T74-A0`) and **1** is arithmetically inert at scale 0 (`T74-C1`). Total interest moves
763,994 -> **764,100** at 100, **764,015** at 7, **766,000** at 1000.

**(c) The reassuring claim is TRUE, and I checked it because it is the one that protects
production.** At the production `MinorUnitDigits = 2`, `T74-B1` (currency 100), `T74-B2`
(installment 100) and `T74-B3` (both 100) are **all three byte-identical** to `P-CAL-MNT5M`, whose
inputs are byte-identical to the already-promoted `P-MNT-5M`. **Neither input moves a single cell at
the production currency scale.** The production configuration is not exposed by this channel.
[VERIFIED]

---

## 5. The refuted prediction S2, and **F-2 settled by capture**

### The refutation itself

`check-prediction.py` run by me against the committed capture: **1,083 predictions over 875 money
cells, 1,082 held, 1 refuted, exit 1.** [VERIFIED: my run] The refuted one is S2, reported in full
in the handoff rather than buried. Credit where due — and the script honestly exits non-zero.

**The source explanation is correct, with one citation slip.**
`RepaymentPeriod.getOutstandingLoanBalance()` is a `Memo` at **:389-402** whose dependency array at
**:400** is `{paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount}` — **`emi` is not
in it**. `getDueInterest()`'s memo *does* list `emi`, but its dependency array is at **:282-283**,
not the `:288-289` the handoff cites (`:288-289` is the javadoc of a different method). Substance
right, citation wrong — defect **N5**.

`isFullyPaid()` at **:371-372** is
`getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())`, i.e.
`0 == 0` when every EMI quantizes to zero. `calculateLastUnpaidRepaymentPeriodEMI` (`:1160`) then
takes its `:1178-1181` fallback, whose last filter at **:1180** is
`rp.getOutstandingLoanBalance().isGreaterThanZero()` — **which populates the memo on the target
period** — and `:1210` raises that period's EMI through a plain `@Setter` that invalidates nothing.
**The guard that selects the target period is what stales that period's balance.** [VERIFIED at
every cited line]

### F-2: I settled it, and the answer is YES

T74 named a fully specified candidate and marked reachability `[UNVERIFIED]`. I had a live oracle,
so I ran it.

**P-9 discipline observed on my own work.** I committed my prediction to this branch **before**
building or running anything: `.softhouse/reviews/T75-F2-REACHABILITY-PREDICTION.md`, commit
`b4c8186` at `2026-08-20T18:17:17+08:00`. The probe was built and run after it.

**Method.** `CaptureF2.java`, derived mechanically from `Capture3i.java` with the case list replaced
and the class renamed, compiled and run in the pinned image
(`sha256:e596339626bfca...0459a`, verified) against the same seam source
(sha256 `bf397f0b...a80714`, identical to the pinned checkout's copy). In-JVM, no server, no
database. Attestation read inside the JVM: Fineract commit `426a23544e84...b9eb`, `git.dirty=false`,
`MoneyHelper.PRECISION` 19, effective MathContext `(19, HALF_UP)` ordinal 4,
`matchesRatifiedProductionSetting: true`. `pathIdentity.identical` true on all 9 cases.

**Rig calibration.** `T64-ZP-A` and `T64-ZP-B` — both already-promoted parity vectors at the
rounding floor at dp 2 — reproduced pass 3g's committed `observed` blocks **cell for cell, with
zero input differences including tenant id**. [VERIFIED]

**Result — my prediction R4 HELD.** MNT **0.01** / **6 x 21.6 %**, `MinorUnitDigits = 2`,
`(19, HALF_UP)`, single disbursement on the schedule start date, **no multiples-of anything** —
every input **squarely inside DEC-1's graded domain**:

```
D    principal 0.01  balance 0.01
R1   principal 0.00  interest 0.00  total 0.00  balance 0.01
R2..R5                     (identical)          balance 0.01
R6   principal 0.01  interest 0.00  total 0.01  balance 0.01   <-- does NOT reach zero
emis ['0.00','0.00','0.00','0.00','0.00','0.01']
totalInterestAmount 0.00   totalOutstandingAmount "0"   (the oracle's own totals disagree with its own column)
```

**The stale-balance mechanism IS reachable inside the graded domain.** The oracle emits a
graded-domain schedule whose outstanding-principal column never amortizes to zero — which
contradicts this project's stated `principal_amortizes_to_zero` and `balance_roll_forward`
invariants.

**And the Go port diverges on it.** I ran the port's own `Generator.Generate` on the same requests:

| shape (dp 2, 19/HALF_UP, no multiples-of) | oracle final-row balance | Go port final-row balance |
|---|---|---|
| MNT 0.01 / 6 x 21.6 % | **1 minor** | **0 minor** |
| MNT 0.02 / 6 x 21.6 % | **2 minor** | **0 minor** |
| MNT 0.01 / 12 x 21.6 % | **1 minor** | **0 minor** |
| MNT 0.01 / 56 x 21.6 % | **1 minor** | **0 minor** |
| MNT 0.03 / 6 x 21.6 % | 0 | 0 (agree) |
| MNT 0.04 / 6 x 21.6 % | 0 | 0 (agree) |
| MNT 0.05 / 6 x 21.6 % | 0 | 0 (agree) |

This is a **live, unvectored money divergence inside the graded domain** on `schedule.core`. It is
not a blanket disagreement — it is exactly the poisoned-memo region, and the boundary for the
`6 x 21.6 %` shape falls between MNT **0.02** (poisoned) and MNT **0.03** (clean). My registered
prediction R6 bracketed it as "between 0.02 and 0.05", which is true but looser than the observed
boundary; recorded as a partial refinement of my own prediction rather than a clean hit.

**T74's reasoning about why `T64-ZP-B` does not reproduce it is confirmed by observation**: at
MNT 0.03/0.04/0.05 the head EMIs are non-zero, `findLastUnpaidRepaymentPeriod` is non-empty, the
poisoning branch never runs, and those schedules amortize to zero.

**This is not a defect in T74's diff.** T74 promoted nothing from any of it, the 42 promoted vectors
all hold the six invariants, and the follow-up was specified precisely enough that a reviewer could
execute it. It is a **program finding** and it should be raised as a task in its own right: it forces
a decision between "match the oracle" and "hold the invariant", which is a design call above a
worker's pay grade. My capture, the calibrated probe source and the Go comparison are reproducible
from this review.

---

## 6. Pass-3 supersession — the reasoning is CORRECT, including the part I expected to be wrong

**The underlying claim holds.** [VERIFIED: whole-store scan of `provenance.capture_ref`]

| capture | vectors |
|---|---|
| `capture-prod3b-raw.json` | 11 |
| `capture-prod3c-raw.json` | 2 |
| `capture-prod3d-raw.json` | 2 |
| `capture-prod3e-raw.json` | 14 |
| `capture-prod3f-raw.json` | 3 |
| `capture-prod3g-raw.json` | 4 |
| pass 3i (`capture-prod3i-raw.json`) | **6** |
| *(none — contract-refusal)* | 4 |
| **`capture-prod-raw.json`** | **0** |

42 parity + 4 refusal. Zero name pass 3.

**Reason (a) is right, and I checked it rather than believing it.** Pass 3 and pass 3b carry the
**identical twelve case ids** (`P-CAL, P-00, P-01, P-02, P-02b, P-03, P-04f, P-04t, P-MNT-5M,
P-MNT-1M2, P-MNT-50M, P-MNT-4M999`), and **eleven of them are the `capture_case_id` of a currently
promoted vector**. Adding them to `never_promotable_capture_case_ids` would refuse all eleven.
[VERIFIED]

**Reason (b) is right.** `LoadPin` (`admit.go:52-68`) decodes through `strictDecode`, which is
`json.Decoder` + `DisallowUnknownFields()` [VERIFIED: `enums.go:138-146` — the author cites
`admit.go:60-66`, which is the *call*; the flag itself is in `enums.go`]. A new
`never_promotable_capture_files` key would fail the decode and exit 2.

**And the mechanism the author says does not exist, does not exist.** I looked specifically for one
the author might have missed. `provenance.capture_ref` **is** validated (`admit.go:574-595`: it must
be non-empty, must resolve to a file in the repo, must not be a directory, and its sha256 must match
`capture_sha256` when given) — but there is **no denylist keyed on it**. The denylist at
`admit.go:603` is exact string equality against `Provenance.CaptureCaseID` (no prefix match, no
`strings.HasPrefix` — clean of the T77 defect class). **So the mark is in the best place available
today, and the residual risk the author names in F-3 is real: nothing mechanical stops a future fire
from promoting a pass-3 capture.**

**One thing the author overlooked, offered as a cheaper F-3.** `conformance.sh` already has a HARD
guard mechanism that needs no Go change and no `PIN.json` schema change: `run_guards` (:155-161)
runs `guard_no_float_in_vectors` (:96) and **exits 2** if any guard fails. A
`guard_no_superseded_capture_ref` that greps every vector for `capture-prod-raw.json` would enforce
the supersession **today**, mechanically, in ten lines of shell. That is strictly better than
waiting for a Go change, and I recommend it be recorded against F-3.

`PASS3-REPORT.md` and `PASS3-REPORT-shared.md` remain `cmp`-identical with the banner in both.

---

## 7. P-9 discipline, and the P-16 check on T21

**Commit ordering — checked from the commits and their timestamps, not the prose.**
Author and committer times are identical on all five. [VERIFIED: `git log --format` on
`main..branch`]

| commit | time (+08 / UTC) | subject |
|---|---|---|
| `ecd8a71` | 17:25:24 / **09:25:24Z** | register the pass-3i prediction BEFORE the capture runs (P-9) |
| `93745db` | 17:25:37 / 09:25:37Z | pass-3i harness — the two multiples-of inputs get separate slots |
| `d4bfff1` | 17:39:05 / 09:39:05Z | pass-3i capture, and six precision-boundary vectors promoted |
| `25661fb` | 17:46:41 / 09:46:41Z | pass-3i report, recipe README, pass-3 supersession mark, handoff |
| `20609d2` | 17:47:01 / 09:47:01Z | handoff |

The prediction commit is **first**, 13 seconds before the harness and two commits before the
capture. `PREDICTION.md` and `predicted.json` are introduced by `ecd8a71` and are **touched by no
later commit on the branch** — `git log --name-only main..branch -- <both paths>` returns `ecd8a71`
and nothing else. So they cannot have been rewritten after the results were seen. [VERIFIED]

The committed capture's attestation carries `runId pass3i-20260820T093826Z` and
`capturedAtUtc 2026-08-20T09:38:27.945Z`, i.e. **13 minutes after the prediction commit** and 38
seconds before the commit that carries it. The author also reports an earlier run
`pass3i-20260820T092556Z` — 32 seconds after the prediction commit and 19 seconds after the
harness commit — with an identical `capturesCanonicalSha256`, a free determinism control.

**A corroboration I can offer because I ran the same rig.** The gap between the runner's host
`date -u` (which stamps `runId`) and the JVM's own `Instant.now()` (which stamps `capturedAtUtc`)
is **1.94 s** on T74's committed capture. On my own probe run of the same image on the same machine
the same gap was **1.85 s** (`t75f2-20260820T101804Z` -> `2026-08-20T10:18:05.848Z`). The
unzip + `javac` + JVM-start interval is genuinely that short here, so the two timestamps are
mutually consistent with a real execution of that recipe rather than a hand-written pair.

**The P-16 check is the strongest evidence that the prediction was not written after the fact.**
`predicted.json` names the total interest **and** total repayment of all six group-E shapes at
**both** precisions — twelve numbers — with `basis: "T21v2-2"`. I traced every one of the twelve to
`.softhouse/reviews/t21v2/t21v2-probe2-oracle-out.txt` lines 52, 55, 58, 61, 64, 67 (a file already
on `main`), and every one to the observed capture:

| principal | predicted p19 / p12 | T21v2 transcript | oracle observed |
|---|---|---|---|
| 4 | 1.14 / 1.13 | 1.14 / 1.13 | 1.14 / 1.13 |
| 59 | 16.51 / 16.52 | 16.51 / 16.52 | 16.51 / 16.52 |
| 72 | 20.14 / 20.13 | 20.14 / 20.13 | 20.14 / 20.13 |
| 340 | 95.15 / 95.16 | 95.15 / 95.16 | 95.15 / 95.16 |
| 426 | 119.18 / 119.20 | 119.18 / 119.20 | 119.18 / 119.20 |
| 6940 | 1942.65 / 1942.66 | 1942.65 / 1942.66 | 1942.65 / 1942.66 |

**Twelve for twelve.** The T21 audit under review here was right about all of them, and the
prediction is a faithful transcription of a document that predates this branch. [VERIFIED]

*(The delegated timestamp audit — author/committer times, and whether any later commit touches
`PREDICTION.md` or `predicted.json` — is reported in §10.)*

---

## 8. Hygiene, and I attacked the recipe rather than reading it

**`nexus/` untouched.** `git diff main...branch -- nexus/` is **empty**. [VERIFIED]

**`contract.go`.** sha256 `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139`,
equal to `PIN.json.contract_sha256`. `gofmt -l nexus/` over the whole tree names **exactly**
`nexus/internal/apps/loanschedule/contract/contract.go` and nothing else — the expected G-3 Option A
state, and `VerifyContractDigest`'s own doc comment records why. [VERIFIED]

**Nothing pre-existing altered.** `git diff --stat main...branch -- .softhouse/vectors/` is
`PIN.json` (+25/-4 lines), `README.md` (+50/-14), `capabilities.json` (2 `evidence` strings
rewritten) and the six new files. **No existing vector file is modified.** `capabilities.json` keeps
`in_graded_domain: false` on both touched capabilities and flips nothing to `exercised`. `PIN.json`
changes only its `note` and appends to `never_promotable_capture_case_ids` — no digest, no
`contract_sha256`, no `production_rounding`, no entry removed or reordered. All 46 vectors carry
`dec1_revision: 12`, matching the pin. [VERIFIED]

**Verification claims reproduced independently.**

```
main baseline    parity PASS 36  FAIL 0  4034 graded  96 money kills   exit 0
branch           parity PASS 42  FAIL 0  5576 graded  102 money kills  exit 0
conformance.sh --prove                   PROOFS: 21 passed, 0 failed   exit 0
go build ./...                                                        exit 0
go test ./...                            all ok                       exit 0
```

(Invoked as `bash .softhouse/conformance.sh` throughout — the `sh`/exit-2 collision of T81 did not
arise and no oracle problem was observed.)

### The mutated-seam attack

The brief asked me to try to make the recipe pass with a mutated seam. I did, twice, against a
scratch tree and a `--shared` clone — **never against `/Users/buv/fineract`**.

| attack | result |
|---|---|
| mutate **only** the repo-local seam copy, `PINNED_FINERACT=/Users/buv/fineract` | **exit 1**, precondition 4 — `seam class DRIFT` |
| mutate **both** copies identically; clone at the right commit; `git update-index --assume-unchanged` so `git status --porcelain` is empty and precondition 3 passes; `cmp` confirms the two files are **equal** so precondition 4 passes | **exit 1**, precondition **4b** — `sha256 f2956cfe... expected bf397f0b...` |

I reproduced the author's own falsification independently and reached the same conclusion: **`cmp`
has two operands and a caller controls both; a literal digest has neither.** The seam byte-identity
check is a real precondition that fails the run, and I could not defeat it by editing a file.

**T77-class attack surface, checked rather than assumed.** `run-pass3i.sh` has no `grep -qF` prefix
gate, no `case X*)`, no stdout/stderr mismatch: `fail()` writes to stderr **and exits 1**, every
Python abort is `sys.exit("...")` (exit 1), and the only `set +e` (:215) is re-armed on the next
line. No `|| true`, no `; true`, no `exit 0` anywhere. No bashisms under its `#!/bin/sh` shebang
(no `[[`, no process substitution, no arrays). Every output path is a literal filename — the T22
P0-5 glob defect is genuinely avoided. The `admit.go:603` denylist is exact equality, not a prefix
match. [VERIFIED]

**One limit of the recipe worth naming, since precondition 4b's strength invites over-reading.** The
harness-integrity check (`srcs['/cap/src/Capture3i.java'] != harness_sha`) is **circular**: the
in-container sha is measured *by the harness itself*, so a mutated harness reports its own mutated
digest and matches the host measurement. It catches a file swap between the host measurement and the
container run; it does **not** catch a mutated harness. What actually defends that is depth — nine
rig calibrations against five independently committed artefacts, each sha-pinned as a literal, plus
whole-plan `pathIdentity`. A lying harness would have to reproduce nine committed observations cell
for cell. That is adequate, and it is worth writing down so nobody mistakes 4b for harness
integrity.

---

## 9. Defects found — seven, all prose, comment, `note` or dead code

**None of these touches a vector cell, a money value, or any money logic.** Listed most to least
consequential.

**N1 — a wrong count in the handoff.** The handoff's Changes table says "**18** pass-3i case ids
added to `never_promotable_capture_case_ids`". The diff adds **21**: six `T74-E-*-p12`, four
`T74-A*`, three `T74-B*`, five `T74-C*`, three `T74-D*`. [VERIFIED: `git diff -- PIN.json`]

**N2 — `PIN.json`'s expanded `note` enumerates the denylist's reasons and omits three of the ids it
denylists.** The note declares "THE DENYLIST BELOW CARRIES TWO DIFFERENT REASONS", gives (1)
precision probe / rig calibration and (2) "out of the graded domain by currency scale — pass 3i's
`T74-A*`, `T74-C*` and `T74-D*` run at currencyDecimalPlaces 0". **`T74-B1/B2/B3` are on the list
and are covered by neither**: they run at `decimalPlaces = 2`, inside the graded domain. Their real
reason (they would duplicate the promoted `P-MNT-5M` while claiming to grade an input that cannot
move them) is stated in the handoff and in the promotion script's docstring but **not in the file
that claims to state the reasons**. Denylisting them is conservative and creates no false green —
their ids are unique to pass 3i, so no promoted vector is affected — but a file whose whole purpose
is to be read by someone who did not run this task should not leave three entries unexplained.

**N3 — "differing in exactly one input" is stated three times and is not what the code asserts.**
The handoff, the store `README.md` and every one of the six vectors' `evidence` strings say the two
counterfactual arms differ "in exactly one input". They differ in **two recorded inputs**:
`mathContextPrecision` **and** `tenantId`. `build-counterfactuals.py:73` says so explicitly —
`allowed = {"mathContextPrecision", "tenantId"}`. The substance survives: `tenantId` selects a
`MoneyHelper` rounding-mode cache entry and both arms record `ambientMoneyHelperPrecision` 19 and
`ambientMoneyHelperRoundingModeOrdinal` 4, so it is arithmetically inert here — but the prose
overstates what the assertion actually enforces, and this text is now inside six promoted vectors.

**N4 — an unfalsifiable guard, inside the pass that invokes P-15 against exactly that.**
Precondition 17 builds its "exhaustive per-id table" from `EXPECTED_IDS` itself:

```python
CASE_PRECISION = {'P-CAL': 12}
for _id in EXPECTED_IDS:
    if _id not in CASE_PRECISION:
        CASE_PRECISION[_id] = 12 if _id.endswith('-p12') else 19
_unregistered = [i for i in EXPECTED_IDS if i not in CASE_PRECISION]
if _unregistered:
    sys.exit("RUN FAILED: no expected MathContext precision registered for %r" % _unregistered)
```

`_unregistered` is **empty by construction** and that `sys.exit` is unreachable, yet the script
header advertises "an id absent from that table FAILS THE RUN" and the report cites P-15 ("a guard
that cannot go red is decoration"). **The substantive improvement over pass 3h is real** — a `-p12`
id now maps to 12 instead of silently defaulting to 19 — and the per-case comparison in the `bad`
loop is genuinely falsifiable and was demonstrated red. Only the pre-check is decoration. Either
make the table a literal dict and let the check bite, or delete the pre-check and stop claiming it.

**N5 — citation slip.** The handoff cites `getDueInterest()`'s memo as listing `emi` "at
`:288-289`". The dependency array is at `RepaymentPeriod.java:282-283`; `:288-289` is the javadoc of
`getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest`. Claim true, line wrong.

**N6 — off-by-one in a harness comment.** `Capture3i.java:129-130` and `run-pass3i.sh`'s header both
call `installmentAmountInMultiplesOf` "the **12th** argument of `LoanRepaymentScheduleModelData`".
It is the **13th** (the 12th is `downPaymentPercentage`). The actual constructor call at :666-670 is
correct; only the comment is wrong.

**N7 — citation imprecision.** `DisallowUnknownFields` is cited as `admit.go:60-66`; that is
`LoadPin` calling `strictDecode`, and the flag is at `enums.go:140`. Conclusion unaffected.

---

## 10. The promotion script, and the attestation's own labelling

**`.softhouse/handoff/T74-promote-vectors.py` asserts rather than narrates.** Its refusals are
executable: it refuses to write a `margin_minor` the counterfactual report does not contain, it
asserts both multiples-of inputs are `null` on every promoted case, and it scales major->minor by
exact integer string arithmetic with no float and no fallback. The decisive evidence is §1's
re-run: deleting the six committed vectors and re-running the script reproduces all six **byte for
byte**, which is only possible if every value in them came out of the capture. [VERIFIED]

**One labelling wrinkle, offered as context for N2 rather than as a defect.** The attestation
sidecar's `parityCandidateCaptureIds` lists **21** ids — every case that is neither a `-p12` probe
nor a rig calibration, so all of groups A, B, C and D land there by mechanical residual. The author
then refused every one of them and put all 21 on `PIN.json`'s denylist. The sidecar's own
`admissibilityNote` says promotion is a separate gated decision, so the two are not in conflict —
but "parity candidate" in the sidecar means only "not a probe and not a calibration", and a later
reader should not take it as a recommendation. `discriminationProbeCaptureIds` correctly names
exactly the six `-p12` companions, and `fieldSeparation.currencyOnlyCaptureIds` (8) and
`installmentOnlyCaptureIds` (3) are both non-empty, which is what precondition 16b demands.
[VERIFIED: `capture-prod3i-attestation.json`]

---

## 11. What I checked and found nothing wrong with

Stated so that silence is distinguishable from not looking.

- No float token in any new vector, in `Capture3i.java`, or in the four Python tools — the harness's
  own `guard_no_float_in_vectors` passes and I read the scaling code.
- No US payment rail, vendor, MySQL/MariaDB/Oracle-Database driver, dialect or port 1521 anywhere in
  the diff.
- No deposit-taking string, no "insured / protected / guaranteed" language.
- No hard-coded time-zone offset; the vectors' `time_zone` is `Asia/Ulaanbaatar` and the `_note`
  correctly records that the Path A seam takes `LocalDate` only, so the field grades nothing.
- No change to `contract.go`, no DEC-1 amendment, no cutover implied, no `user` gate crossed.
- `capabilities.json`: nothing flipped to `exercised`, no `in_graded_domain` flipped to true.
- The two rewritten `evidence` strings: every factual statement in them re-checked against the
  capture or the source; all correct (the "four conjuncts" phrasing is clumsy but not wrong).
- `never_promotable_capture_case_ids` matching is exact equality (`admit.go:603-607`), not a prefix
  match — the T77 hole is absent here.
- `observed_total_due_minor` and `observed_total_interest_minor` are consumed by `invariants.go`
  (:505, :531) rather than as direct parity cells; under my mutation they went red as invariant
  violations, so they do grade.
- Store totals: main 36 / 4,034 / 96; branch 42 / 5,576 / 102. Exactly as claimed.
- One-per-run scope: the diff stays inside the Path A capture rig, the vector store and the handoff.
  Nothing wandered into another bounded context.

---

## 12. Recommendations to the driver

1. **Raise the F-2 result as its own task.** MNT 0.01 / 6 x 21.6 % at `MinorUnitDigits = 2` is a
   graded-domain shape on which the oracle and the Go port **disagree today** and no vector has
   power. Deciding it means choosing between parity with the oracle and a stated property
   invariant — that is a design call, not a worker's. My probe, its calibration and the Go
   comparison are reproducible from §5.
2. **Apply N1-N7 as record corrections.** All prose, one `note` string, one line of dead code. None
   is a money number and none changes a vector.
3. **Record the cheaper F-3 from §6:** a `guard_no_superseded_capture_ref` HARD guard in
   `conformance.sh` enforces the pass-3 supersession today, mechanically, with no Go change and no
   `PIN.json` schema change.
4. **Carry F-1, F-4, F-5 and F-6 forward as written.** F-1's caution — refusing to weaken a standing
   precondition to buy one observation — is the right instinct and should be kept.
