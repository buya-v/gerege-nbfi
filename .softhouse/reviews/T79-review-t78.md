# T79 — independent review of T78 (`softhouse/T78-fui-marker-d5`, head `b2ebe52`)

Run `2026-08-17-run1-harness-schedule-poc`, context `loan-schedule`, role `reviewer`.
Reviewing the FIFTH draft of the `futureUnrecognizedInterest` rule in
`nexus/internal/apps/loanschedule/emi.go`.

> Terminology: "the oracle" is the **Fineract reference implementation** at pinned
> commit `426a23544`. Oracle Database is prohibited in this program and nothing in
> this review touches a database.

**Pin verified by me before citing anything**: `git -C /Users/buv/fineract log --oneline -1`
= `426a23544 Merge pull request #5946`; `git -C /Users/buv/fineract status --porcelain`
empty. Every Fineract line below was opened by me at that pin. I did not write to the
checkout.

Honesty rule: each material claim is marked `[VERIFIED: source]` or `[UNVERIFIED]`.

---

## Verdict

**REJECTED** — three findings, all textual, none of them a defect in the *rule*.

I want the routing of this rejection to be unambiguous, because this is the fifth
round and P-18 is in force:

- **The task shape was RIGHT and must not be changed again.** The four previous
  rejections (T67, T71, T73, and T65's) were all the same kind: the fence was an
  enumeration of forbidden shapes, and each reviewer found the next uncovered caller
  one frame further out. **That failure mode is gone in this draft.** I attacked the
  closure the way the brief directed and it holds — see "What I verified positively",
  which is the longer half of this review.
- **My three findings are of a different kind**: one deleted clause, one overstated
  word, one under-counted grep. They are consistency and precision defects *inside a
  sound argument*, not insufficiency of the fence.
- **The remedy is roughly eight lines of targeted edit, not a sixth rewrite.** Exact
  edits are given under each finding. A sixth draft that rewrites the block would be
  a regression.

I rejected rather than issuing MICRO-FIX for one reason: F-T79-1 breaks a sentence
inside the money derivation that the entire omission decision rests on, and the
MICRO-FIX budget is explicitly barred from money logic. The fix is a verbatim
restoration from the parent commit, so it is cheap — but it is not mine to make.

---

## F-T79-1 (P1) — step (e)'s derivation sentence was truncated by this draft; the aggregate identity is gone

**This defect was introduced by T78, not inherited.**

T78's change #1 replaced step (e)'s three-line forward pointer with thirteen lines.
The replacement consumed half a sentence that belonged to the *following*, unchanged
text and did not restore it.

Parent `4507109` (T72), lines 402-404 [VERIFIED: `git show 4507109:...emi.go | sed -n '392,410p'`]:

```
//     the forEach/setEmi at :1736-1741]. THAT WRITE PATH IS REACHED ONLY VIA
//     :741, under onlyOnActualModelShouldApply (:733-735) -- which is what
//     condition (2) is really protecting; see there. Hence sum of emi_j over
//     f < j <= L is (P + I) - emi_f, so u_L = max(0, u_f - (P + I) + emi_f),
```

Head `b2ebe52` [VERIFIED: `git diff 4507109 b2ebe52 -- .../emi.go`, the deleted line
ends `Hence sum of emi_j over` and no added line restores it]:

```
//     by riding the second term. What protects (e) is the CLOSURE TEST below,
//     part 6; all four disjuncts are resolved in part 5.
//     f < j <= L is (P + I) - emi_f, so u_L = max(0, u_f - (P + I) + emi_f),
//     which is 0 as soon as cdi_f <= P. CITE T66.md:100-108 FOR THIS STEP
```

The subject of the sentence — **"the sum of emi_j over"** — is deleted. As committed,
step (e) asserts that an index interval `f < j <= L` *is* a money quantity
`(P + I) - emi_f`. That is not a statement a reader can evaluate, and the quantity it
was defining is the bridge from (d)'s aggregate identity `sum_j emi_j = P + I` to
(e)'s conclusion `u_L = 0` — which is the entire reason the field may be omitted.

Why this is P1 and not cosmetic: P-13 says that for a specification-bearing comment
**the comment is the deliverable**. The next sentence instructs the reader to cite
`T66.md:100-108` "FOR THIS STEP". A porter who follows that instruction cannot check
the step against the citation, because the step no longer states what it computes.
The zero-executable-change proofs are silent about this by construction.

**Exact edit** (restore the deleted clause; 2 lines touched):

```
//     part 6; all four disjuncts are resolved in part 5. Hence the sum of emi_j
//     over f < j <= L is (P + I) - emi_f, so u_L = max(0, u_f - (P + I) + emi_f),
```

The wording is recoverable verbatim from `4507109`; no new money reasoning is
required, and no number changes.

---

## F-T79-2 (P2) — "BIJECTION" is false, and the block's own part 5 refutes it

Part 4 states, and nominates as the closure:

> "…those four stand in **BIJECTION** with `EmiChangeOperation.Action`…"
> "**THAT BIJECTION IS THE CLOSURE.**"

and part 9's closing sentence repeats "4 callers of `:718` **in bijection with** a
4-constant enum".

The site↔Action correspondence is **not** a bijection, and the counterexample is
printed in the same comment block, eighty lines further down.

`calculateEMIOnNewModelAndMerge` (`:1744-1759`) is the `:743` else branch. At `:1751`
and `:1752` it calls the **private** `addDisbursement` and `addCapitalizedIncome` with
`operation.withZeroAmount()`, and `withZeroAmount()` **preserves the action**
[VERIFIED: `EmiChangeOperation.java:64-69` — returns a new operation carrying the same
`action` for `DISBURSEMENT` and `CAPITALIZED_INCOME`, `null` otherwise; and
`ProgressiveEMICalculator.java:1751-1752` opened at the pin]. So:

- an operation with `action == CAPITALIZED_INCOME` reaches private `addDisbursement`
  (`:137`), fails the `:142-144` guard's `action == DISBURSEMENT` term, takes the else
  arm, and enters `:718` **at `:149`** — the site the table labels `DISBURSEMENT`;
- symmetrically an operation with `action == DISBURSEMENT` reaches `:280` via `:1752`.

[VERIFIED: guard read at `:142-144`; else arm `:145-151`; call at `:149`.]

There is also a **third caller of private `addDisbursement` that census 3 never names**:
`:1107`, `addDisbursement(temporaryReAgedScheduleModel, EmiChangeOperation.disburse(...))`
inside the re-age model builder [VERIFIED: `grep -n "addDisbursement("` returns `:134`,
`:1107`, `:1751`; `:1100-1109` opened]. It carries `DISBURSEMENT`, so it does not
contradict the table's label, and it is fenced by part 8's NO RE-AGING clause — but a
census the block calls exhaustive should name it.

**The closure itself survives, and I want that on the record.** The operative sentence —
"a fifth route into `:718` cannot appear without either a fifth `Action` constant or a
fifth call site, and both are compile-visible edits" — is **TRUE**, and it rests on the
*call-site count*, which I re-derived independently: `grep -rn "calculateEMIValueAndRateFactors"`
repo-wide over `/Users/buv/fineract` returns call lines **only** at `:149`, `:280`,
`:317`, `:356`, all inside `ProgressiveEMICalculator.java`, and **nothing anywhere else
in the repository** [VERIFIED]. Injectivity of site→Action is not needed for that, and
the per-site tillDate column of the table is stated per *site*, so it is unaffected.
Nor can the cross-edge be traversed under the rule's own answer: `(alpha) = exactly one
DISBURSEMENT into an empty model` makes term 1 `isEmpty()` fire, `:741` runs, `:743` is
never entered, and `:1751` is unreachable.

So this is a false load-bearing *word* inside a sound argument, not a hole. I record it
as P2 rather than P0 for exactly that reason. **I therefore reject the brief's framing
that "if the bijection fails, the closed form does not close"** — it closes on the
grep-reproducible call-site count (tripwire graph 3), which is stronger than the
bijection and does not depend on it.

**Exact edit** (word substitutions only; 4 lines touched):
- part 4: "those four stand in **BIJECTION** with" → "those four are **CLOSED BY**";
- part 4: "**THAT BIJECTION IS THE CLOSURE.**" → "**THAT FOUR-SITE COUNT IS THE CLOSURE.**";
- part 4: "confirms the bijection" → "confirms which Action each **public wrapper**
  constructs; the private methods have further callers at `:1107`, `:1751` and `:1752`,
  so a site does NOT carry only one Action — see part 5";
- part 9: "in bijection with a 4-constant enum" → "closed by a 4-constant enum".

---

## F-T79-3 (P3) — tripwire graph 3 understates its own grep output, so a faithful re-run reads as STALE

Part 9 says the block is STALE if any of the five counts changes, and instructs the
reader to re-run the greps. Graph 3 is stated as:

> "grep `"calculateEMIValueAndRateFactors"` in the pinned file returns call lines
> `:149`, `:280`, `:317` and `:356`, the declaration `:718`, and the two dispatch lines
> `:722` and `:723`"  — i.e. **7 lines**.

The grep as literally written returns **9 lines** [VERIFIED at `426a23544`:
`grep -n "calculateEMIValueAndRateFactors" ProgressiveEMICalculator.java` → `149, 280,
317, 356, 703, 718, 722, 723, 730`]. The two unaccounted lines are the declarations of
the two dispatch targets, whose names share the prefix:

- `:703` `calculateEMIValueAndRateFactorsForFlatInterestMethod`
- `:730` `calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod`

The block already cites both elsewhere (`:730-751` in part 3, `:723` dispatching to
`:730` in step (b)), so this is bookkeeping, not a missed route. But a porter following
part 9's instruction gets 9 where the block promises 7 and must conclude the census is
stale. The failure is **fail-safe** — it errs toward re-examination, never toward a
false green — which is why it is P3 and not higher.

**Exact edit** (1-2 lines): after "and the two dispatch lines `:722` and `:723`", add
"plus the two dispatch-target declarations `:703` (Flat) and `:730` (DecliningBalance),
which share the name prefix — 9 lines in total, 4 of them calls into `:718`."

---

## What I verified positively — so silence is distinguishable from not looking

Every item the brief directed me to attack, and the result.

### 1. Fence scoped to the port's input surface, not `GradedDomain` — **CORRECT**

Part 7 binds "the union of every field, value and combination the Go seam will accept
from ANY caller — adapter, assembler, capture harness, vector, test, or a future Nexus
module — WHETHER OR NOT `GradedDomain` has a predicate for it, and whether or not the
frozen contract has a field for it." It then names T72's scoping error explicitly and
says why (8) failed. T73's counterexample class (a term variation the contract has no
field for) is inside this fence. **The T72 scoping error is not reintroduced under new
wording** [VERIFIED: part 7 read at `b2ebe52`].

### 2. The SECOND writer, `:392` inside `payInterest` — **COVERED**

Part 2, entry E2. `[VERIFIED at the pin: grep for
`calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer` in
`ProgressiveEMICalculator.java` returns exactly `:392`, `:1217` and the declaration
`:1221` — two callers, as claimed.]` The block states the consequence rather than just
naming the site: on the `:392` route nothing in `:1160` runs, so steps (d), (e), (f) are
**inapplicable rather than weakened**, and it is held off by one thing only — nothing is
ever paid. That is T73's F-T73-3 discharged correctly, and it is routed into the closure
test as question (beta).

### 3. The THIRD writer, `AdvancedPaymentScheduleTransactionProcessor.java:1995` — **EVERY CITATION EXACT**

The brief warned that a misplaced citation here would make the census worthless. It is
not misplaced. I re-opened the file at the pin [VERIFIED]:

| T78 claim | verified |
|---|---|
| write at `:1995` | yes — `currentRepaymentPeriod.setFutureUnrecognizedInterest(outstandingAmountsTillDate.getOutstandingInterest());` |
| method `calculateUnrecognizedInterestForClosedPeriodByInterestRecalculationStrategy` | yes — declared at `:1981` |
| span `:1981-1999` | yes |
| called once at `:1975` | yes — `grep` returns exactly one call |
| from `handleRepayment` at `:1971` | yes — `private void handleRepayment(...)` at `:1971` |
| gate `isPrepayAttempt() && isRepaymentLikeType() && calculateTillRestFrequencyEnabled()` + `isFullyPaid()`, at `:1983-1990` | yes |

T78 found a write site four previous drafts and three previous reviewers all missed. It
is genuinely unreachable from the Path A seam (`generate()` constructs no
`LoanTransaction`), and recording it anyway is the correct call for a census that claims
completeness.

### 4. The four-term disjunction at `:733-735` — **STATED IN FULL**

Read at the pin [VERIFIED]:

```java
final boolean onlyOnActualModelShouldApply = scheduleModel.isEmpty()
        || operation.getAction() == EmiChangeOperation.Action.INTEREST_RATE_CHANGE
        || operation.getAction() == EmiChangeOperation.Action.ADD_REPAYMENT_PERIODS || scheduleModel.isCopy();
```

Part 5 states all four terms, resolves each one, and says `:741` runs when ANY is true
and `:743` only when ALL FOUR are false — which matches `:740-744` exactly. It also
names which single disjunct (term 1) gives step (e) its premise, and that terms 2 and 3
fire on a non-empty model. **T73's F-T73-2 reduction-to-`isEmpty()` is fully repaired.**

### 5. Are the three censuses exhaustive? — **YES; I re-ran them wider than T78 did**

- **Census 1.** T78 scoped its grep to `fineract-progressive-loan/src/main` and
  `fineract-provider/src/main`. I ran it **repo-wide and case-insensitively**, which also
  catches direct field assignment that `set…` would miss:
  `grep -rni --include='*.java' 'futureUnrecognizedInterest' /Users/buv/fineract`.
  Result [VERIFIED]: the same **three** assignment sites (`:1184`, `:1246`, `APSTP:1995`),
  plus `RepaymentPeriod.java:127` (the constructor storing the parameter) and `:156`
  (`RepaymentPeriod.copy` passing it through) — both of which the block names as
  propagation, not origination. `RepaymentPeriod.create` passes `zero` into that
  parameter [VERIFIED: `:143-151`], so origination is zero. **The census is complete, and
  more robustly than T78 established it.** The residual gap the block does not claim to
  close is reflection; it does not claim reflection-proofness.
- **Census 2.** Re-run; exactly two callers. See item 2 above.
- **Census 3.** Re-run **repo-wide**; `calculateEMIValueAndRateFactors` appears in no
  file other than `ProgressiveEMICalculator.java` [VERIFIED], and there are exactly four
  call lines into `:718`. See F-T79-3 for the line-count bookkeeping defect.

On the brief's test "would the grep catch a case the author did not think of": yes — it
demonstrably did. W2 (`APSTP:1995`) is a site no previous draft named, and the block says
so.

### 6. The bijection — **enum side TRUE, site side FALSE**

`EmiChangeOperation.Action` has **exactly four constants** at `:32-37` — `DISBURSEMENT`,
`INTEREST_RATE_CHANGE`, `CAPITALIZED_INCOME`, `ADD_REPAYMENT_PERIODS` — and the four
factories are at `:47-49`, `:51-53`, `:55-57`, `:59-62`, each constructing exactly one
Action [VERIFIED: file read in full].

**A point in T78's favour that T78 did not claim**: the class is annotated
`@AllArgsConstructor(access = AccessLevel.PRIVATE)` [VERIFIED: `:29`], so the constructor
is **private** and no code outside `EmiChangeOperation` can mint an operation except
through the four factories and `withZeroAmount()`. That is a stronger closure than the
handoff argues for. There is no switch-default that produces a fifth Action; `:718`'s
switch is over `getInterestMethod()`, not over `Action`, and its `default` throws
`UnsupportedOperationException` [VERIFIED: `:720-727`]. I found no reflective
construction.

The **site**→Action side fails, per F-T79-2. The closure does not depend on it.

### 7. Zero executable change — **BOTH PROOFS REPRODUCED INDEPENDENTLY**

I recomputed rather than accepting the stated digest.

| measurement | T78 claimed | I measured |
|---|---|---|
| non-comment changed lines under `nexus/` at `741686a` | 0 | **0** |
| same at head `b2ebe52` | 0 | **0** |
| unfiltered non-comment changed lines at `741686a` | 613 | **613** |
| same at head | 941 | **941** |
| comment-stripped `emi.go`, `main` | 609 lines, `e660867196b5bea6…33a4d` | **609**, `e660867196b5bea6aa1abd98bb843e917f8bc7de0af1d574c74384b2a1133a4d` |
| comment-stripped `emi.go`, `741686a` | identical | **identical** |
| comment-stripped `emi.go`, head | identical | **identical** |
| files changed vs `main` | 4 (emi.go + 3 handoffs) | **4** — `emi.go`, `T70.md`, `T72.md`, `T78.md` |

`T70.md` and `T72.md` are inherited from the branch ancestry, as the handoff states.
**Zero executable change is proven.** I did not re-run `go build` / `go test` /
conformance: with the compiled content byte-identical to `main`, those runs grade `main`,
not this branch, and would be evidence of nothing. `gofmt` parsing the file successfully
(item 8) establishes it still compiles as valid Go.

### 8. `contract.go` untouched, gate G-3 holds — **VERIFIED**

- `contract.go` sha256 `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` on
  **both** `main` and `b2ebe52` — byte-identical [VERIFIED, recomputed].
- `gofmt -l nexus/internal` at `main` names **exactly**
  `nexus/internal/apps/loanschedule/contract/contract.go` and nothing else — the expected
  G-3 Option A state [VERIFIED].
- `emi.go` at head `b2ebe52` piped through `gofmt -l -d` produces **empty output** — it is
  gofmt-clean [VERIFIED, recomputed].
- `emi.go` is the only changed `.go` file on the branch, so `gofmt -l` on the branch names
  exactly `contract.go`. **G-3 is not broken**, and T78's F-T78-2 (the doc-comment
  list-item trap) was correctly identified and fixed.

### 9. F-T78-1 — T78's correction of its own reviewer — **T78 IS RIGHT, T73 WAS WRONG**

Adjudicated from source at the pin, every element [VERIFIED]:

| claim | verdict |
|---|---|
| `:1749` is `scheduleModel.copyWithoutPaidAmounts()` | **TRUE** |
| its copy IS disbursed into at `:1751`, `addDisbursement(scheduleModelCopy, operation.withZeroAmount())` | **TRUE** — and `:1752` is `addCapitalizedIncome` on the same copy |
| `calculateEMIOnNewModelAndMerge` spans `:1744-1759` and is the `:743` else branch | **TRUE** |
| `deepCopy` passes `COPY=false` at `:132` | **TRUE** — `ProgressiveLoanInterestScheduleModel.java:130-135` |
| `copyWithoutPaidAmounts` passes `true` at `:141` | **TRUE** — `:137-142` |
| `isCopy()` is `modifiers.get(COPY)` at `:452-454` | **TRUE** |
| therefore the `:1224` deep copy the W1 decision runs on is **NOT** `isCopy()` | **TRUE**, and no earlier draft had settled the direction |
| `withZeroAmount()` returns `null` for the other two Actions (`:64-69`), so `:138` would NPE | **TRUE** |

**T73's F-T73-2 sentence "no `deepCopy` / `copyWithoutPaidAmounts` caller in Fineract main
routes back into `addDisbursement`", marked `[VERIFIED]`, is false.** T78 caught a
`[VERIFIED]`-tagged error in a signed review artefact and did not fix it in place, which
is the right call for a signed artefact. This is the second time in this chain a worker
has corrected its own reviewer (T69 on T67), and it should be credited.

Ironically, this same finding is what refutes T78's own "bijection" (F-T79-2) — T78
assembled the counterexample and did not notice it applied to its part 4. Its handoff
nonetheless told me where to look ("check `:1751`'s `withZeroAmount()` in particular,
since it preserves the action"), which is honest signposting.

### Other citations I spot-checked, all exact

`ProgressiveLoanScheduleGenerator.java` `:116` loop, `:119` comment (quoted verbatim
correctly), `:120`, `:265-279`, `:267-269` null early return, `:271-274` rate-change
forEach, `:276-278` interest pause, `:273` and `:351` [all VERIFIED].
`ProgressiveLoanInterestScheduleModel.java:394-399` `isEmpty()` [VERIFIED].
`AdvancedPaymentScheduleTransactionProcessor.java:502` `addRepaymentPeriods` and `:1767`
`addCapitalizedIncome` [VERIFIED].
`OverdueBalanceCorrection.java:26` is indeed the only other mention of the name in main,
and it is a javadoc line [VERIFIED].
Tripwire graph 2 (2 callers + 1 declaration) and graph 5 (17 call sites + 1 declaration;
the thirteen post-origination sites listed are `:368, :380, :404, :442, :505, :626, :698,
:868, :879, :937, :1091, :2024, :2129` = 13, and `13 + 4 = 17`) both **re-derived exactly
by me** [VERIFIED]. Graph 1 and graph 4 verified above.
Contract citations `contract.go:563-564`, `:2117-2118`, `:866-869`, `:1177-1181` all read
on the branch and quoted accurately [VERIFIED].

**Across roughly forty citations I re-opened, F-T79-3's grep line count is the only
numeric discrepancy I found.** For a block of this size that is a good ratio, and it is
consistent with T73's report of zero citation defects in the inherited material.

---

## Non-negotiables

Graded against `CLAUDE.md` and `.softhouse/patterns.md` read from this worktree.
The diff is comment-only with a byte-identical compiled surface, so most do not engage:

- **No floating point** introduced or described as acceptable, including intermediate
  calculation; the port's residual is discussed as `emiMinor`, an integer minor-unit
  quantity. PASS.
- **No MySQL / MariaDB / Oracle Database** driver, dialect, `ojdbc`, `oracle.jdbc`, or
  port `1521` in the diff; PostgreSQL untouched. The block uses "oracle" only in the
  test-oracle sense. PASS.
- **No deposit / insured / protected / guaranteed** language. PASS.
- **No `first_name` / `last_name`**, no hard-coded time-zone offset, no US payment rails
  or vendors. PASS.
- **Frozen adapter contract untouched** — `contract.go` byte-identical, never `gofmt`ed.
  PASS.
- **Scope guard** — the diff stays inside the `loan-schedule` context. PASS.
- **Honesty rule** — I found no hedged `[VERIFIED]` tag in the block. The `[UNVERIFIED]`
  on whether `emi_L` can go strictly negative is correctly retained and correctly routed
  to a capture rather than argued away; T78 declining to settle it by reading was right.
  PASS.

---

## What would have made me approve

Restoring the four deleted words in step (e), striking the word "bijection", and
correcting graph 3's line count. Nothing else. Had T78's `APSTP:1995` citation been
invented or misplaced — the specific failure the brief told me to hunt — I would have
rejected on the census being worthless; it was exact in all six particulars.

**REJECTED**
