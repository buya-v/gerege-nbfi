# T531 — independent review of T530 (`softhouse/T530-t529-conditions`, tip `0d4b0e00`)

Reviewer: independent. Verdict derived from the diff and the pinned Java, re-derived
by hand and by my own tooling. `.softhouse/handoff/T530-t529-conditions.md` was read
**last**, only to check whether it claims anything I disproved.

Pinned reference oracle (Fineract): `/home/user/fineract/.git/HEAD` read directly =
`426a23544e8426a38ae43ae404670a0a7e85b9eb`. `RepaymentPeriod.java` = **537 lines**,
`InterestPeriod.java` = **237 lines** (`wc -l`).

Diff taken at the merge-base, per T512:

```
BASE = dd27570094febf4233c5209be0000c2f38f73bfd   (git merge-base origin/main origin/softhouse/T530-t529-conditions)
5 files changed, 404 insertions(+), 51 deletions(-)
  .softhouse/handoff/T530-t529-conditions.md      | 302 +
  nexus/internal/apps/loanproduct/doc.go          |  43 +-
  nexus/internal/apps/loanproduct/interestperiod.go |  2 +-
  nexus/internal/apps/loanproduct/interestperiod_test.go | 4 +-
  nexus/internal/apps/loanproduct/repaymentperiod.go | 104 +-
```

---

## VERDICT: **ACCEPT WITH CONDITIONS**

The citation work itself — the task's actual subject — is correct and complete.
I re-derived **all 52** citations, not a sample, and every one resolves to a real
construct at `426a23544` and supports the Go sentence above it. My count matches
T530's exactly. Nothing executable moved. Most importantly, T530 was handed the one
temptation this task existed to test — an unsupportable citation on
`FindInterestPeriod` — and it did **not** quietly re-point the range to make the
mismatch disappear. I hunted specifically for that and found no instance anywhere.

The conditions are about a **wrong worked example inside the otherwise-correct
DIVERGENCE block**, which is shipped in the source and will mislead the follow-up
task's vector design.

---

## 1. Re-derivation of every row (no sampling)

I built my own construct map of `RepaymentPeriod.java` by reading all 537 lines, then
resolved every citation against it. Method spans I derived independently:

`empty` 138-141 · `create` 143-151 · `copy` 153-171 · `copyWithoutPaidAmounts` 173-198 ·
`getPrevious` 200-202 · `getRateFactorPlus1` 209-214 · `calculateRateFactorPlus1` 216-218 ·
`getCalculatedDueInterest` 226-233 · `calculateFixedInterestTillDate` 235-250 ·
`calculateCalculatedDueInterest` 252-265 · `getDueInterest` 272-286 ·
`getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest` 293-295 ·
`getCalculatedDuePrincipal` 302-305 · `getCreditedPrincipal` 312-316 ·
`getCreditedInterest` 323-327 · `getCapitalizedIncomePrincipal` 334-338 ·
`getDuePrincipal` 345-350 · `getTotalCreditedAmount` 357-360 · `getTotalPaidAmount` 367-369 ·
`isFullyPaid` 371-373 · `getUnrecognizedInterest` 381-383 · `getCreditedAmounts` 385-387 ·
`getOutstandingLoanBalance` 389-403 · `addPaidPrincipalAmount` 405-407 ·
`addPaidInterestAmount` 409-411 · `getInitialBalanceForEmiRecalculation` 413-427 ·
`getZero` 429-431 · `getFirstInterestPeriod` 433-435 · `getLastInterestPeriod` 437-440 ·
`findInterestPeriod` 442-447 · `isFirstRepaymentPeriod` 449-451 ·
`getOutstandingInterest` 458-460 · `getOutstandingPrincipal` 462-464 ·
`resetDerivedComponents` 466-469 ·
`calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod` 476-492 ·
`getCurrency` 494-499 · `getEmi` 501-503 · `getOriginalEmi` 505-507 ·
`moveOutstandingDueToReAging` 533-536 · field block 46-113 ·
`@Setter emi` 57-58 · `@Setter originalEmi` 59-60 ·
the negated-add statement span inside `copyWithoutPaidAmounts` 192-194.

This map was derived before I looked at T530's; it agrees with T530's span table
line-for-line.

### My count vs T530's

| | mine | T530 | agree |
|---|---|---|---|
| `RepaymentPeriod.java` citations in the package | **52** | 52 | yes |
| in `repaymentperiod.go` | **39** | 39 | yes |
| cross-file (`doc.go` 4, `interestperiod.go` 5, `interestperiod_test.go` 4) | **13** | 13 | yes |
| unchanged by T530 and independently verified already correct | **12** | 12 | yes |
| changed by T530 and independently verified now correct | **40** | 38 moved + 2 tightened = 40 | yes |
| unsupported by the Java after correction | **1** (`FindInterestPeriod`) | 1 | yes |
| unresolved after T530 | **0** | 0 | yes |

**No disagreement in the count.** The 12/40 split reconciles exactly: the unchanged 12
are the three `:389-403` / `:405-407` / `:192-194` families
(`repaymentperiod.go` ×3, `doc.go` ×3, `interestperiod.go` ×4, `interestperiod_test.go` ×2).

Every one of the 40 changed ranges was resolved against my own map. All 40 land on the
construct the Go sentence names. Spot-notes on the ones with judgement in them:

- **`:46-113` (field list)**, widened from `:60-97`. Line 46 is the first field
  annotation (`@JsonExclude` on `previous`), 113 the last field (`private Money
  fixedInterest`). The widening is correct, not padding: the old range omitted
  `previous`, `fromDate`, `dueDate`, `interestPeriods`, `emi` at the head and the
  re-age/fixed-interest fields at the tail, all of which are in the Go struct.
- **`:209-218` (`RateFactorPlus1`)**, spanning two Java methods. I checked whether this
  was a range widened to swallow a mismatch. It is not: `:216-218` is
  `reduce(BigDecimal.ONE, BigDecimal::add)`, which the Go reproduces exactly, and the
  span is explicitly annotated in the comment as covering the memoised accessor the
  port deliberately drops (documented at the type level, `repaymentperiod.go:19-21`).
  Honest and self-declaring.
- **`:57-58` / `:59-60`** replacing a bare `@Setter`. Java 57 is `@Setter`, 58
  `private Money emi;`; 59 `@Setter`, 60 `private Money originalEmi;`. Exact.
- **`:192-194`** (unchanged). Java 192 `if (!interestPeriodCopy.getBalanceCorrectionAmount().isZero()) {`,
  193 the negated `addBalanceCorrectionAmount`, 194 `}`. The Go comment claims exactly
  that this nets the cell to zero. Supports.

---

## 2. Enumeration completeness

I did **not** reuse T530's enumerator. I wrote my own regex scanner over every `.go`
file in `nexus/internal/apps/loanproduct/` on the T530 branch, matching
`<Name>.java` with an optional `:a-b` range, printing file, line, target and range,
independent of whether the word `VERIFIED` appears anywhere.

Result: **52** `RepaymentPeriod.java` citations, all carrying a range; **zero**
range-less `RepaymentPeriod.java` citations remain (the two bare `@Setter` ones were
tightened). Nothing is unenumerated. The scanner also confirms the class T530 describes
exists — **7** lines in the package carry a `RepaymentPeriod.java` citation with no
`VERIFIED` token on that line:

```
doc.go:125              -> RepaymentPeriod.java:389-403   (dataflow diagram)
interestperiod.go:82    RepaymentPeriod.java:389-403 ->   (trace arrow)
interestperiod.go:241   -> RepaymentPeriod.java:389-403 ->
interestperiod.go:320   RepaymentPeriod.java:192-194; ... (bracket continuation)
interestperiod_test.go:16  RepaymentPeriod.java:173-198]. (bracket continuation)
interestperiod_test.go:77  ...(RepaymentPeriod.java:173-198).  (inside a t.Fatalf string)
repaymentperiod.go:523  RepaymentPeriod.java:153-171].  (bracket continuation)
```

A single-line `VERIFIED.*RepaymentPeriod\.java` grep sees 45 of 52 and misses these 7.
T530 says the mechanical pass found **five** such and that this is "why the total is 52
and not 47"; I get 7 and 45. **The bookkeeping does not reconcile, but the outcome
does** — the total of 52 and the "zero unenumerated / zero unresolved" claim are both
independently confirmed. Recorded as MINOR below, not as a defect in the work.

---

## 3. Resolving ≠ supporting

Resolution is necessary, not sufficient, so I read the Java for every corrected citation
and asked whether it backs the sentence. On the money paths I re-derived
operation-for-operation rather than trusting the method name:

- **`OutstandingLoanBalance` / `:389-403`.** Java order: `last.outstandingLoanBalance`
  `+ balanceCorrectionAmount` `+ capitalizedIncomePrincipal` `+ disbursementAmount`
  `+ paidPrincipal` `− duePrincipal`, then `negativeToZero`. Go: identical operations in
  identical order. Summand order matters for rounding; it agrees.
- **`CalculateCalculatedDueInterest` / `:252-265`.** Guard `!isInterestMovedUpward &&
  !isInterestMovedDownward` gating the segment sum; `reduce(ZERO, add)` over
  `InterestPeriod::getCalculatedDueInterest` wrapped once at the `Money` boundary; then
  `+ fixedInterest`, `+ futureUnrecognizedInterest`, `+ previous.getUnrecognizedInterest()`
  if present; `negativeToZero`. Go matches step for step, exact `big.Rat` sum normalised
  once. I checked the "plus credited interest" wording that the range does not literally
  contain: it *is* backed, because `InterestPeriod.getCalculatedDueInterest`
  (`InterestPeriod.java:134-143`) adds `getCreditedInterest()` into every segment term.
- **`DueInterest` / `:272-286`.** `max( paidPrincipal > calculatedDuePrincipal ?
  paidInterest : min(calculatedDueInterest, emiPlusCredited…), paidInterest )`, with the
  `isInterestPaymentGrace` early return. Go identical, including which operand of `max`.
- **`DuePrincipal` / `:345-350`**, **`CalculatedDuePrincipal` / `:302-305`**,
  **`UnrecognizedInterest` / `:381-383`**, **`OutstandingInterest` / `:458-460`**,
  **`OutstandingPrincipal` / `:462-464`** — `negativeToZero` placement and `max` operands
  all agree.
- **`TotalCreditedAmount` / `:357-360`.** `creditedPrincipal + creditedInterest −
  creditedInterestMovedDueReAge − creditedPrincipalMovedDueReAge`, in that order. Go
  same order.
- **`InitialBalanceForEmiRecalculation` / `:413-427`.** Java runs two separate reduces
  (disbursements, then capitalized income) and Go fuses them into one loop. I checked
  this specifically because loop fusion can change a rounding sequence: it does not
  here — each accumulator still sees its own operands in list order, and the two final
  adds are in the same order. Equivalent.
- **`CalculateFixedInterestTillDate` / `:235-250`.** `divide(length, mc)` then
  `multiply(fixedInterest, mc)` — two rounding points. Go's two `roundSignificant` calls
  sit at exactly those two points.
- **`calculateTotalDisbursedAndCapitalizedIncome… / :476-492`.** Base
  `totalDisbursed + totalCapitalized`, then per segment `+ disbursement` then
  `+ capitalizedIncome`, skipping segments whose `dueDate` equals the period's
  `fromDate`, breaking at `till`. Go matches (see MINOR 5 for the `equals`-vs-identity
  note, which is pre-existing).

No floating point anywhere on these paths; `big.Rat` exact sums normalised once at the
`Money` boundary, mirroring the oracle's BigDecimal-then-`Money.of` shape.

The 12 unchanged cross-file citations were checked for support too, not just resolution:
`doc.go:184`'s claim that the Memo "invalidation key includes `interestPeriods`" is
backed literally by `RepaymentPeriod.java:400`
(`() -> new Object[] { paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount }`).

---

## 4. The substantive mismatch — and the hunt for a quiet re-point

### 4a. No quiet re-point anywhere

I resolved all 40 changed ranges against my own construct map before reading T530's
account. **None of them lands on code that merely resembles the Go sentence.** In
particular the one range that could have been used to bury a mismatch —
`FindInterestPeriod`, `:436-443` → `:442-447` — was moved *onto* `findInterestPeriod`,
which is the honest target, and the Go sentence was then rewritten to declare the
divergence rather than re-worded to fit. That is the correct outcome, and it is the
outcome this task was most tempted away from.

### 4b. The divergence is real — mechanism verified

Confirmed from primary source, not trusted:

- `RepaymentPeriod.java:21` statically imports `LoanRepaymentScheduleProcessingWrapper.isInPeriod`,
  so the 4-arg call at `:444-445` resolves to that class.
- `LoanRepaymentScheduleProcessingWrapper.java:251-254` **resolves exactly** and reads:
  ```java
  public static boolean isInPeriod(LocalDate targetDate, LocalDate fromDate, LocalDate toDate, boolean isFirstPeriod) {
      return isFirstPeriod ? DateUtils.isDateInRangeInclusive(targetDate, fromDate, toDate)
                           : DateUtils.isDateInRangeFromExclusiveToInclusive(targetDate, fromDate, toDate);
  }
  ```
- `DateUtils.java:407-409` — `isDateInRangeInclusive` = `!isBefore(target, from) && !isAfter(target, to)`.
- `DateUtils.java:415-417` — `isDateInRangeFromExclusiveToInclusive` = `isAfter(target, from) && !isAfter(target, to)`.
- `InterestPeriod.java:197-199` — `isFirstInterestPeriod()` = `this.equals(getRepaymentPeriod().getFirstInterestPeriod())`.

So **yes**: from-exclusive/due-inclusive everywhere except the first segment of the first
repayment period, which is inclusive on both ends. And `.reduce((one, two) -> two)` on an
ordered sequential stream does return the **last** match. Both axes as stated. The
`:251-254` citation resolves — verified, not trusted.

Side-claims in the new block, all verified true:
`isInPeriod` and `isDateInRangeFromExclusiveToInclusive` exist in `dates.go:106-127`
(and correctly mirror the Java);
`IsFirstInterestPeriod` exists at `interestperiod.go:157`;
`grep -rn FindInterestPeriod` over the whole module returns only its own definition and
doc comment — **no caller**, so nothing live is moving.

### 4c. MAJOR — the worked consequence is wrong

`repaymentperiod.go:448-450` (and handoff lines 154-156) says:

> "…so it accepts a transaction dated exactly on a later segment's from-date, which the
> oracle assigns to the PRECEDING segment."

I derived the boundary cases and **that input is not a divergence — the two agree there.**
Take contiguous segments `[f1,d1],[d1,d2],[d2,d3]` in a non-first repayment period
(4th arg false for every segment):

- `transactionDate = d1` (a later segment's from-date): oracle — seg1 matches
  (`d1 > f1`, `d1 <= d1`), seg2 does not (`d1 > d1` false); `reduce` last = **seg1**.
  Go — first match scanning forward is **seg1** (inclusive on `DueDate`). **Same answer.**
- `transactionDate = f1` (the repayment period's own from-date): oracle — seg1 requires
  `f1 > f1`, false; no segment matches; returns **`Optional.empty()`**. Go — seg1 matches
  (`!f1.Before(f1)`), returns **seg1, true**. **This is the divergence.**

In the *first* repayment period both cases agree (seg1 is inclusive on both ends there).

So the block names an input where the port is correct, and misses the input where it is
wrong — and the real failure is worse than the one described: the oracle finds *nothing*
where the port finds a segment. This is a doc comment, so no number moves today, but it
is precisely the text the recommended follow-up will use to build its golden vector. A
vector built on "a later segment's from-date" comes back showing parity, which would be
read as evidence the port is fine. Rated **MAJOR** for that reason, not CRITICAL: nothing
executable depends on it and the function has no caller.

Related, recorded so the follow-up does not chase it: **axis 2 is not independently
observable once axis 1 is fixed.** Under the oracle's own filter, contiguous
non-degenerate segments admit at most one match, so `.reduce((one, two) -> two)` is
defensive. The statement T530 makes about the Java is true; the implication that
first-vs-last is a second source of numeric divergence is not, for contiguous segments.

---

## 5. Behaviour did not move — verified independently

I did not take the driver's measurement on trust. I parsed **every one of the 14 `.go`
files** in the package on both `BASE` and the T530 tip with `go/parser` (comments
dropped) and re-printed each through `go/printer`, then diffed the two directories.
Across the whole package the **only** surviving token difference is:

```
-  "oracle leaves it stale (RepaymentPeriod.java:173-197).",
+  "oracle leaves it stale (RepaymentPeriod.java:173-198).",
```

That string is the format argument of `t.Fatalf` at `interestperiod_test.go:74-78`,
inside the failure branch of `if got := …OutstandingLoanBalance().Minor(); got !=
wantAfterFirstSweep`. It is **evaluated only when the test has already failed**. The
compared values are `got` and the untyped constant `wantAfterFirstSweep = 90000`; the
string participates in no comparison, no fixture and no vector. **No vector can move.**
Not CRITICAL — confirmed clean.

Build and test on the T530 tree (package overlaid onto a full checkout with its vector
store present):

```
go build ./...                          BUILD_OK
go vet ./internal/apps/loanproduct/      VET_OK
go test ./internal/apps/loanproduct/     ok
go test ./...                            18 packages ok, 0 FAIL
```

(An initial run showed `loanschedule/conformance` failing on `ResolveRepoRoot`; that is
the T165 anti-drift guard refusing a tree with no `.softhouse/vectors`, an artifact of my
scratch copy, and it clears once the vector store is present. Not a T530 regression.)

---

## 6. Condition 2 — verified clean

- The false clause **"the same shape as the four sites above" is gone**. The parenthesis
  now reads "on a VALUE receiver and returns a new summary … a pure fold over a copy,
  not itself a write to stored state" — no equivalence asserted between the value-receiver
  fold and the pointer-receiver mutations. No surviving equivalence anywhere in `doc.go`.
- Receiver claims verified in the Go source, not taken from T530:
  `savings/summary.go:52-55` = `func (s SavingsAccountSummary) Add(effect MinorUnits) SavingsAccountSummary`
  — value receiver, `s.AccountBalance += effect`, `return s`;
  `interestperiod.go:272` = `func (ip *InterestPeriod) UpdateOutstandingLoanBalance()` — pointer;
  `interestperiod.go:326` = `func (ip *InterestPeriod) AddBalanceCorrectionAmount(additional Money)` — pointer.
- **T529's reachability argument survived intact, not as collateral damage.** It is
  preserved and reinforced: "the folded `AccountBalance` field is what
  `PostgresSummaryRepository.Upsert` sends as `account_balance_derived` … That
  reachability, not the value-receiver mutation itself, is why this one belongs in the
  guard-flagged class." All three supporting citations resolve exactly:
  ```
  savings/postgres.go:113   if _, err := r.db.Exec(ctx, `INSERT INTO m_savings_account_summary
  savings/postgres.go:120    account_balance_derived)
  savings/postgres.go:149    summary.AccountBalance.FormatDecimal(MNTMinorDigits)); err != nil {
  ```
  Exec site, column name, and the bound field — the whole chain, pinned.
- The added "DO NOT restate that parenthesis" paragraph strengthens rather than dilutes:
  it states that receiver semantics were never the criterion and that if they were, the
  verdicts would invert. Correct and worth its space.

---

## 7. Scope — clean

Five files touched, all inside `nexus/internal/apps/loanproduct/` plus the handoff.
**Untouched, confirmed against the merge-base diff:** `nexus/internal/apps/savings/`,
`.softhouse/conformance.sh`, `.softhouse/guards/ledgerguard/`. `savings/` was read only
(to resolve the citations above), never written.

---

## 8. The not-swept decision — declining was RIGHT

I measured `InterestPeriod.java` myself with the same enumerator, against the real
**237-line** file:

- **28** ranged `InterestPeriod.java` citations in `interestperiod.go` — matches T530's
  denominator.
- **10** of them start past EOF and cannot resolve to anything:
  `:252-254`, `:256-259`, `:299-301`, `:303-305`, `:307-309`, `:311-313`, `:315-317`,
  `:319-321`, `:323-325`, `:327-329`. Exactly the ten T530 lists. (An eleventh,
  `:237-250`, starts on the file's closing brace and runs past the end.)
- Confirmed by reading: `Length` cites `:229-231` = `getRateFactor`;
  `LengthTillPeriodDueDate` cites `:233-235` = `getRateFactorTillPeriodDueDate` (true
  span `:164-166`); `IsFirstInterestPeriod` cites `:252-254`, past EOF (true span
  `:197-199`). All three as reported.

**Declining was the right call, and the tree is not worse for it.** Three reasons:
(a) the scope guard is one bounded unit of work per run, and a second file's full sweep
is a task of T530's own size; (b) a *partial* audit of a second citation set reproduces
the exact defect under repair — it makes an unswept remainder look accounted for, which
is what T526 did and T529 caught; (c) `interestperiod.go`'s `InterestPeriod.java`
citations are byte-identical to the merge-base (my AST diff proves only the one
`173-197`→`173-198` line changed there), so nothing was degraded, and the broken ranges
are now enumerated in writing so the follow-up needs no re-discovery.

The one residual risk is that `repaymentperiod.go` is now trustworthy while
`interestperiod.go` is not, with nothing *in the file* saying so. Condition 2 below.

---

## Findings

| # | severity | finding |
|---|---|---|
| 1 | **MAJOR** | The `FindInterestPeriod` DIVERGENCE block's worked consequence is wrong (`repaymentperiod.go:448-450`; handoff 154-156). It names an input where port and oracle **agree** and misses the one where they disagree. See §4c. |
| 2 | MINOR | Handoff states `InterestPeriod.java` is **238 lines** (twice); it is **237**. Does not change the past-EOF verdict — all ten cited starts are ≥ 252. |
| 3 | MINOR | The "five citations my grep missed / 47 → 52" arithmetic does not reproduce. My independent enumerator finds **7** citation-bearing lines with no on-line `VERIFIED` (45 with). The substantive claims — total 52, nothing unenumerated, zero unresolved — are confirmed. Bookkeeping only. |
| 4 | MINOR | "Zero executable statements changed" is slightly overstated: one string literal in call-argument position changed. It is a failure-path diagnostic, never compared, so the conclusion "no vector can move" holds — but the precise statement is "one diagnostic string literal changed; no evaluated value did." |
| 5 | MINOR (pre-existing, **not** introduced by T530) | Java uses value equality where the Go uses pointer identity, in two places: `calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod` breaks on `interestPeriod.equals(tillPeriod)` (`RepaymentPeriod.java:479`) vs Go `ip == till`; and `isFirstInterestPeriod()` is `this.equals(getFirstInterestPeriod())` (`InterestPeriod.java:198`) vs Go `ip == …FirstInterestPeriod()`. `InterestPeriod` carries `@EqualsAndHashCode(exclude={"repaymentPeriod"})`, so two distinct segments with identical dates and amounts compare **equal** in the oracle and **unequal** in the port — the oracle can break earlier. Latent, present at the merge-base, on a money path. Flagging for a follow-up task, not against T530. |
| 6 | MINOR (informational) | Axis 2 of the divergence ("returns the LAST match") is not independently observable once axis 1 is fixed: the oracle's own from-exclusive filter admits at most one contiguous non-degenerate segment. T530's statement about the Java is true; do not build a vector expecting first-vs-last to move numbers on its own. |

No CRITICAL findings.

---

## Conditions (each independently checkable)

1. **Correct the worked consequence in the `FindInterestPeriod` DIVERGENCE block.**
   Replace the sentence at `repaymentperiod.go:448-450` so it names the input that
   actually diverges: `transactionDate` equal to the **repayment period's own
   `FromDate`** in a **non-first** repayment period, where the oracle returns
   `Optional.empty()` and this function returns the first segment. State explicitly
   that on a *later* segment's from-date the port and the oracle agree (both select the
   preceding segment), so that case is not evidence of anything. Mirror the correction
   in the handoff. *Checkable:* the block names `p.FromDate` / a non-first period and
   the empty-vs-found asymmetry, and no longer claims the oracle "assigns it to the
   PRECEDING segment" as the divergence.

2. **Mark `interestperiod.go` as unswept.** Add a short header note stating that this
   file's own `InterestPeriod.java` citations are **not** verified against `426a23544`
   (28 ranged citations, 10 starting past the 237-line EOF), and naming the follow-up
   task. Without it a reader sees `RepaymentPeriod.java` citations that are now sound
   and generalises that trust. *Checkable:* `grep` the file for the marker.

3. **Fix `238 lines` → `237 lines`** in the handoff (both occurrences), and restate the
   "zero executable statements changed" line as "one diagnostic string literal in a
   `t.Fatalf` failure message changed; no evaluated value did." *Checkable:* `grep` the
   handoff.

4. **Constrain the follow-up `FindInterestPeriod` fix task.** Its golden vector must
   include `transactionDate == P.FromDate` for a **non-first** repayment period — the
   only contiguous-segment input where the port and the oracle actually disagree — and
   must not treat first-vs-last match as an independent observable (finding 6).
   *Checkable:* the vector spec names that case.

---

## Checks run that came back clean

Listed because "found nothing" is only legitimate with the evidence attached.

1. All 52 `RepaymentPeriod.java` citations resolve to a real construct at `426a23544`. Zero unresolved.
2. All 52 **support** the Go sentence above them (read the Java for each; did not sample).
3. Count reconciliation 12 + 40 = 52 matches T530's 12 + 38 + 2 exactly.
4. Independent enumerator (my own, regex over the whole package, `VERIFIED`-agnostic): 52 found, none unenumerated, zero range-less `RepaymentPeriod.java` citations left.
5. No quiet re-point: all 40 changed ranges verified against my own construct map; the single unsupportable one got a DIVERGENCE block, not a moved range.
6. Money paths re-derived operation-for-operation — `OutstandingLoanBalance`, `CalculateCalculatedDueInterest`, `DueInterest`, `DuePrincipal`, `CalculatedDuePrincipal`, `TotalCreditedAmount`, `InitialBalanceForEmiRecalculation`, `CalculateFixedInterestTillDate`, `RateFactorPlus1`, `calculateTotalDisbursedAndCapitalizedIncome…` — summand order, `negativeToZero` placement, `max`/`min` operands and rounding points all agree. No floating point in any money path.
7. Behaviour: `go/parser` + `go/printer` comment-stripped AST diff over all 14 package files, both revisions — exactly one token differs, and it is a `t.Fatalf` diagnostic.
8. `go build ./...` clean; `go vet ./internal/apps/loanproduct/` clean; `go test ./...` 18 packages ok, 0 FAIL.
9. `LoanRepaymentScheduleProcessingWrapper.java:251-254` resolves and reads exactly as claimed; `DateUtils.java:407-409` and `:415-417` confirm inclusive vs from-exclusive; the static import at `RepaymentPeriod.java:21` confirms the overload.
10. Condition 2: false clause removed, no surviving receiver-based equivalence, reachability argument intact; `savings/summary.go:52-55` and `savings/postgres.go:113,120,149` all resolve exactly.
11. Scope: only 5 files; `savings/`, `.softhouse/conformance.sh`, `.softhouse/guards/ledgerguard/` untouched.
12. Side-claims: `isInPeriod` / `isDateInRangeFromExclusiveToInclusive` present in `dates.go`; `IsFirstInterestPeriod` present in `interestperiod.go`; `FindInterestPeriod` has no caller module-wide.
13. `InterestPeriod.java` measurement independently reproduced: 28 ranged citations, 10 past EOF, the three named misfires confirmed.

---

## Push proof

T530's branch on origin (matches the dispatch tip `0d4b0e00`):

```
$ git ls-remote --heads origin refs/heads/softhouse/T530-t529-conditions
0d4b0e008b62a8fbb3c25999b4a7d49a0a6cd680	refs/heads/softhouse/T530-t529-conditions
```

This review's branch on origin:

```
$ git ls-remote --heads origin refs/heads/softhouse/T531-review-t530
04ff4f561858970ce7616f33f5287f95f0e635dc	refs/heads/softhouse/T531-review-t530
```

That hash is the commit carrying this review before the amend that inserted this
proof block; the amend is pushed on top, so re-running the command shows the current
head. The branch is on origin either way — it is not one of the five branches this
fire found stranded on a single machine.
