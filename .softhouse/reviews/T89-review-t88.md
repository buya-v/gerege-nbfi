# T89 — independent review of T88 (`softhouse/T88-fui-marker-d6`)

Run `2026-08-17-run1-harness-schedule-poc`, context `loan-schedule`, role `reviewer`.
Reviewing patch `406ad3c` + handoff `722f018`, forked from `softhouse/T78-fui-marker-d5`
(head `b2ebe52`).

**Pin verified before citing anything** [VERIFIED: `git -C /Users/buv/fineract rev-parse HEAD`
= `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git log --oneline -1` =
`426a23544 Merge pull request #5946`]. The checkout was read-only; I did not write,
build, or branch inside it. I did not use the reference oracle instance, did not touch
`.softhouse/capture/`, and did not restart, rebuild or re-seed any container.

> Terminology: "the oracle" here is the **Fineract reference implementation** at
> `426a23544`. Oracle Database is prohibited in this program and nothing here touches a
> database.

Honesty rule: every material claim is marked `[VERIFIED: source]` or `[UNVERIFIED]`.

---

## Verdict: **MICRO-FIX**

One line, mechanical, no money logic, no change to the argument, its structure, its
censuses or its conclusions. See **F-T89-1** below.

**The three edits are all correct and I confirmed no fourth substantive edit rode
along.** I re-derived every source fact from the pinned checkout rather than accepting
T88's or the driver's, recomputed both zero-change proofs and every digest rather than
copying them, and re-ran all five tripwire censuses — not only graph 3 — because T78's
grep attestation had already been shown to fail once.

**The defect I found is in *this patch*, not in the task shape.** The task shape is
sound and I am not asking for it to change. T79's ruling stands: the closed form
CLOSES. T88 applied three findings and stopped, which is exactly what it was asked to
do. F-T89-1 is a *missed* restatement of the finding T88 was already correcting, not
an out-of-scope change and not a re-litigation of the argument. Under P-18 this is
explicitly **not** a fifth rejection of the same kind: the previous four rejections
were all "the rule is true but insufficient"; this is a one-line provenance leak with
the rule itself now correct in every particular I could check.

**What would have made me reject:** if the restored clause had been paraphrased rather
than byte-recovered, or if the withdrawal of the bijection claim had left the closure
resting on anything other than the four-site count plus the rule's own answer — because
either would mean the money bridge from (d) to (e) is still not checkable by the next
porter, which is the whole deliverable (P-13).

---

## The judgement call I was asked to rule on

**I agree with the driver's ruling, and I would go slightly further.**

Correcting *both* statements of the grep's output is **within** F-T79-3, not a fourth
edit. The finding is "the block understates its own grep output"; the block states that
output in exactly two places; a finding is not discharged by fixing one instance of the
value it corrects. Leaving part 9's tally at 7 while fixing part 4 would have produced a
block whose own tripwire contradicts its own prose — strictly worse than the defect T79
filed.

I also confirm T88's F-T88-3 against the primary sources: **T79's F-T79-3 quotes and
anchors its "exact edit" on part 4's prose**, while the dispatch brief named part 9's
GRAPH 3 [VERIFIED: `git show softhouse/T79-review-t78:.softhouse/reviews/T79-review-t78.md`
lines 160-188 — the quoted text is part 4's "grep ... returns call lines :149, :280,
:317 and :356, the declaration :718, and the two dispatch lines :722 and :723", and the
"Exact edit" reads "after 'and the two dispatch lines :722 and :723', add ..."]. So the
review and the brief named *different* single locations, and a worker obeying either one
literally would have shipped the leak. T88 was right to correct both and right to raise
it as a process finding.

**Where I go further:** if correcting every restatement of a finding is within that
finding, then the same rule binds T88 — and there is a **third** restatement it missed.
That is F-T89-1.

---

## F-T89-1 (P3, MICRO-FIX) — the tripwire's own attestation still credits T78 with a count T78 got wrong

**This is the third restatement the driver asked me to sweep for. It is a restatement of
the finding's *verification*, not of its *value*, which is why three greps for the
numeral missed it.**

`emi.go:928`, byte-unchanged by this patch [VERIFIED: identical string at
`b2ebe52:...emi.go:911` and `406ad3c:...emi.go:928`; not present in any of the five diff
hunks]:

```
//     [VERIFIED at T78: all five counts re-derived by grep at 426a23544. T73
```

This sentence closes part 9 and vouches for **all five** tripwire graphs. But graph 3's
count is no longer T78's: T78 grepped and got **7**, T79 refuted it, and T88 corrected it
to **9**. As committed, the block certifies that T78 re-derived by grep a number T78
never produced.

**Why it matters, and why only a little.** Part 9's entire mechanism is "re-run these
greps; if any count changed, this block is STALE." Its force depends on the counts being
trustworthy *and* on the reader knowing who established each one. A mis-attributed
attestation does not make any count wrong — I independently verified that all five are
now correct (below) — but it silently over-credits the one attestor demonstrated to have
miscounted, in the one sentence a later contributor would use to decide how much
re-checking to do. That is P-12's exact shape ("a right conclusion on a wrong reason
recurs in the artefact written to record it") landing in the artefact that records the
verification rather than in the artefact that records the value, and P-12 is recorded in
`patterns.md` as "the single most reliable defect in this pipeline."

It is **fail-safe in direction**, like the defect it descends from: a reader who
distrusts the attestation re-greps and gets the right answer. Hence P3, not higher.

**Exact edit — 1 line becomes 2, nothing else touched.** The wording is not load-bearing;
any phrasing that stops crediting T78 with graph 3 discharges this.

```
-//     [VERIFIED at T78: all five counts re-derived by grep at 426a23544. T73
+//     [VERIFIED at 426a23544: graphs 1, 2, 4 and 5 re-derived by grep at T78,
+//     graph 3 re-derived at T88 after T79 refuted T78's 7-line count. T73
```

Both added lines are 78 and 74 columns, inside the block's existing 81-82 column wrap
[VERIFIED: measured]. It is a full-line comment inside the same doc-comment list item, so
it cannot disturb gate G-3 — but re-run `gofmt -l` after applying, as T78's first draft
tripped exactly there.

**I did not apply this edit.** My branch is forked from `main`, not from
`softhouse/T88-fui-marker-d6`; editing `emi.go` here would create a competing seventh
version of the file, which is the failure mode this chain has been burned by. It belongs
on T88's branch or in the merge.

---

## Edit 1 (F-T79-1) — the restored clause: **CORRECT, and the bridge really does reconnect**

### The bytes are the parent's, not a paraphrase

Occurrence counts, re-run by me [VERIFIED]:

| commit | occurrences of `Hence sum of emi_j over` |
|---|---|
| `4507109` (parent) | **1**, at `emi.go:403` |
| `b2ebe52` (T78 head, rejected) | **0** |
| `406ad3c` (T88 head) | **1**, at `emi.go:413` |

Byte identity, established independently of T88's digest by extracting the clause and its
governed lines from both commits and running `cmp` [VERIFIED]:

```
cmp <4507109 lines 403-405, leading text stripped to "Hence sum">
    <406ad3c lines 413-415, same>   → BYTE-IDENTICAL
sha256 both: 434377795d63186ba40e363e28c0999f81f6de18519b87721b470050085d8efd
```

I also reproduced T88's own quoted digest exactly:
`sha256("Hence sum of emi_j over\n//     f < j <= L is (P + I) - emi_f, so u_L = max(0, u_f - (P + I) + emi_f),\n//     which is 0 as soon as cdi_f <= P.")`
= `270e29d34ffb5248a694eae0352e714ea36b1ecb93f9485296595ba9e279cc89`, no trailing newline
[VERIFIED, computed by me]. **Not paraphrased, not re-derived, not reflowed.**

### I re-derived the substitution myself, in the new surrounding text

This is the part that mattered, because T78 rewrote the sentences *preceding* the clause,
so verbatim restoration is necessary but not sufficient — the premises the clause consumes
must still be delivered by the rewritten preamble. They are [VERIFIED: `emi.go:362-421` at
`406ad3c`, read end to end]:

- **(c)** telescopes to `u_k = max(0, u_f - sum_{f<j<=k} emi_j)` for `k > f`.
- **(d)** gives `sum_j emi_j = P + I`, on the pre-assignment `I` — qualifier intact.
- **(e)** establishes **both** zero-premises before the clause fires: `emi_j = 0` for
  `j > L` (from `isFullyPaid()`, `RepaymentPeriod.java:371-373`) and `emi_j = 0` for
  `j < f` (from the `isEmpty()` disjunct — T78's rewritten four-term passage still
  delivers exactly this premise, and says so: "The premise this step needs — the level
  installment landing on a model whose EARLIER periods carry no EMI — holds when the
  FIRST disjunct fires").

Splitting (d)'s sum on those two premises:
`sum_j emi_j = 0 + emi_f + sum_{f<j<=L} emi_j + 0`, hence
**`sum_{f<j<=L} emi_j = (P + I) - emi_f`** — the restored clause, exactly.
Substituting into (c) at `k = L`: **`u_L = max(0, u_f - (P + I) + emi_f)`** — the clause's
second half, exactly.

And I checked the closing step, which the clause hands off to. With
`u_f = max(0, cdi_f - min(cdi_f, emi_f))` [VERIFIED: `RepaymentPeriod.java:272-286` min at
`:280`; `:381-383`], the `u_f > 0` branch gives `u_f + emi_f = cdi_f`, so
`u_L = max(0, cdi_f - (P + I))`, which is 0 whenever `cdi_f <= P + I` — and `cdi_f <= P`
suffices because `I >= 0` is **dropped** from the bound. That is precisely what the block
means by "(e) uses I only as a non-negative quantity dropped from a bound", and it is
also precisely why the bound is **not tight**, which the block still says. The `u_f = 0`
branch is also 0, since `emi_f <= P + I`. **The money argument closes.**

Without the clause, step (e) read `f < j <= L is (P + I) - emi_f` — an index interval
asserted equal to a money quantity, with `sum_{f<j<=L} emi_j` never defined and (d)
therefore never consumed. T79's diagnosis was right and T88's repair is the right repair.

### The article — **I agree with T88, and not with T79**

T79's "Exact edit" reads "Hence **the** sum of emi_j"; `4507109` has no article; T88 took
the parent's bytes. **T88 is right**, for a reason stronger than "the brief said
verbatim":

1. T79's own finding says the wording "is recoverable **verbatim** from `4507109`", and
   quotes the parent text without the article three paragraphs above its own suggested
   edit [VERIFIED: T79 review lines 55-61 vs 89-92]. T79's edit block is internally
   inconsistent with T79's own quotation; the parent is the authority, not the paraphrase
   of it.
2. Verbatim restoration is **mechanically provable** — an occurrence count and a digest
   against a named commit, which is what let me settle this in two commands. Inserting
   "the" would have destroyed that property and forced the reviewer to re-read for
   paraphrase drift, on a comment that has already been rejected four times for wording.
3. T79's edit reflows two lines; T88's touches one. On a patch whose entire defence is
   "exactly three edits", the smaller diff is the correct choice.

The missing article is terse, not ambiguous — "sum of emi_j over f < j <= L" reads as a
named quantity. **No change wanted.**

---

## Edit 2 (F-T79-2) — the bijection claim withdrawn: **CORRECT, and T88's extra finding is real**

### All three source facts re-derived by me at the pin

| claim | my verification at `426a23544` |
|---|---|
| `withZeroAmount()` preserves `action` for `DISBURSEMENT` **and** `CAPITALIZED_INCOME`, returns `null` otherwise | **CONFIRMED** — `EmiChangeOperation.java:64-69` opened. Body is `if (action == Action.DISBURSEMENT \|\| action == Action.CAPITALIZED_INCOME) { return new EmiChangeOperation(action, submittedOnDate, amount.zero(), null, 0); } return null;` — first constructor argument is `action`, passed through unchanged. Span `:64-69` is **exact**. |
| `:1751`/`:1752` pass it into the **private** `addDisbursement`/`addCapitalizedIncome` | **CONFIRMED** — `ProgressiveEMICalculator.java:1751-1752` are `addDisbursement(scheduleModelCopy, operation.withZeroAmount());` and `addCapitalizedIncome(scheduleModelCopy, operation.withZeroAmount());`, resolving to the private overloads declared at `:137` and `:274`. Enclosing method `calculateEMIOnNewModelAndMerge` spans **exactly `:1744-1759`**. |
| `:1107` is a **further** `addDisbursement` call site | **CONFIRMED** — `grep -n "addDisbursement\|addCapitalizedIncome"` returns `:126` (public decl), `:134` (public→private), `:137` (private decl), **`:1107`**, `:1751`; plus `:269`, `:271`, `:274`, `:1752` for capitalized income. |

### T88 went beyond the brief and its extra claim holds — I checked both directions

- **`DISBURSEMENT` → `:280`.** Private `addCapitalizedIncome` (`:274-284`) has **no action
  guard at all** — it unconditionally reaches `calculateEMIValueAndRateFactors` at `:280`
  with whatever operation it was handed [VERIFIED: `:274-284` opened; the only conditional
  is `.ifPresent(...)` on the balance change, which does not inspect `action`]. So `:1752`
  can hand a `DISBURSEMENT` op straight to `:280`. **Confirmed.**
- **`CAPITALIZED_INCOME` → `:149`.** Private `addDisbursement` (`:137-153`) guards the
  full-term-tranche arm on `operation.getAction().equals(Action.DISBURSEMENT)` at
  `:142-144`; a `CAPITALIZED_INCOME` op fails that term, takes the `:145-151` else arm, and
  reaches `:718` at `:149` [VERIFIED: `:137-153` opened]. **Confirmed.**

So the site→Action map is genuinely **not injective**, in both directions, and "THAT
BIJECTION IS THE CLOSURE" was false. The withdrawal is warranted and T88's independent
extension of it is a real strengthening, not scope creep — it lives inside F-T79-2 and
makes the withdrawal load-bearing rather than merely retracted.

### The restatement rests only on the count plus the rule's own answer

I checked that the new closure sentence imports nothing else, and verified its every step:

- `:733-735` is a **four**-term disjunction, `scheduleModel.isEmpty() ||
  INTEREST_RATE_CHANGE || ADD_REPAYMENT_PERIODS || scheduleModel.isCopy()`; term 1 is
  `isEmpty()` [VERIFIED: `:733-735` opened].
- `:741` is `calculateEMIOnActualModel(...)`, `:743` is
  `calculateEMIOnNewModelAndMerge(...)` [VERIFIED: `:740-744` opened].
- **`:743` is the SOLE caller of `calculateEMIOnNewModelAndMerge`** [VERIFIED:
  `grep -n "calculateEMIOnNewModelAndMerge"` returns exactly `:743` and the declaration
  `:1744`]. This is the load-bearing fact and the block does not state it explicitly — but
  it is what makes "`:743` is never entered, so `:1744-1759` is never called" airtight
  rather than merely suggestive. I record it as corroboration, **not** as a finding; the
  sentence is true as written.

So: one `DISBURSEMENT` into an empty model fires term 1 → `:741` runs → `:743` never
entered → `:1744-1759`, where `:1751`/`:1752` live, is never called → the cross-edges
cannot be traversed under the rule. **Sound.**

### Injectivity is nowhere claimed

- `grep -ni "bijection"` at head → **zero hits** [VERIFIED, exit 1].
- `grep -ni "injectiv"` → **2 hits**, `:643` and `:653`, **both explicit non-claims**
  ("THE SITE-TO-ACTION MAP IS NOT INJECTIVE"; "INJECTIVITY OF SITE -> ACTION IS NOT PART
  OF THIS ARGUMENT AND IS NOT CLAIMED ANYWHERE IN THIS BLOCK") [VERIFIED].

**On T88's open `[UNVERIFIED]`** — whether some other sentence restates the site→Action
correspondence in words neither grep catches. I checked, and there **is** such a passage:
part 4's site-by-site listing, "DISBURSEMENT enters at `:149` … CAPITALIZED_INCOME enters
at `:280` … ADD_REPAYMENT_PERIODS enters at `:317` … INTEREST_RATE_CHANGE enters at
`:356`" (`emi.go:630-639`), which read alone does imply a one-to-one correspondence.
**It is adequately handled and I am raising no finding:** T88's disclaimer sits inside the
*same* `[VERIFIED: …]` bracket, two lines later, and explicitly rescopes the listing to
"confirms which Action each **PUBLIC WRAPPER** constructs" before stating the
non-injectivity and both counterexamples. A reader cannot reach the end of the bracket
without the correction. I consider T88's `[UNVERIFIED]` **closed, negative**.

**One further check of the new sentence's literal truth:** "Every operation that reaches
any of those four sites carries one of the constants of `EmiChangeOperation.Action`" — true,
including in the `null` case, because `withZeroAmount()` returns `null` for the other two
actions and `:138` dereferences it (`operation.getSubmittedOnDate()`) before any site is
reached, so a `null` operation throws rather than arriving. The block already notes the NPE
in part 5 [VERIFIED: `:138` and `:64-69` opened]. **No defect.**

Four factory spans also spot-checked exact: `:47-49`, `:51-53`, `:55-57`, `:59-62`, and the
enum `:32-37` [VERIFIED: `EmiChangeOperation.java` opened].

---

## Edit 3 (F-T79-3) — the grep count: **CORRECT**

Run by me from the pinned checkout, not copied [VERIFIED]:

```
grep -n "calculateEMIValueAndRateFactors" \
  fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java
→ 149, 280, 317, 356, 703, 718, 722, 723, 730      (grep -c → 9)
```

**Nine lines, exactly the nine T88 lists.** Classification confirmed by opening each:

| line | what it is | a call into `:718`? |
|---|---|---|
| `:149` | private `addDisbursement`, else arm | **yes** |
| `:280` | private `addCapitalizedIncome` | **yes** |
| `:317` | private `addRepaymentPeriods` | **yes** |
| `:356` | private `changeInterestRate` | **yes** |
| `:703` | decl of `…ForFlatInterestMethod` | no — prefix-sharing declaration |
| `:718` | decl of `calculateEMIValueAndRateFactors` | no — the target itself |
| `:722` | dispatch **from** `:718` to Flat | no |
| `:723` | dispatch **from** `:718` to DecliningBalance | no |
| `:730` | decl of `…ForDecliningBalanceInterestMethod` | no — prefix-sharing declaration |

**Only the first four are calls into `:718`, so the four-site count — the thing the closure
rests on — is unaffected.** T78's 7 omitted `:703` and `:730`; T88's 9 is right.

**Exhaustive repo-wide**, which the closure needs and which I verified independently:
`grep -rl "calculateEMIValueAndRateFactors" --include "*.java"`, excluding `/src/test/`,
returns **exactly one file**, `ProgressiveEMICalculator.java` [VERIFIED]. T79's wider
re-run confirmed.

---

## Diff shape: exactly the claimed patch

[VERIFIED, all recomputed by me]

- `git diff softhouse/T78-fui-marker-d5..406ad3c -- nexus/` → **1 file, 32 insertions,
  15 deletions, 5 hunks**. Matches the claim exactly.
- All 32 added and 15 removed lines are **comment lines** (`//`). No code line in either
  direction.
- Hunk → finding mapping, which I checked by reading all five rather than accepting the
  table: hunk 1 (`:413`) = F-T79-1; hunk 2 (`:617-621`) = F-T79-3 prose + F-T79-2's
  `stand in BIJECTION with`, genuinely one sentence; hunk 3 (`:639-646`) = F-T79-2;
  hunk 4 (`:906-910`) = F-T79-3 GRAPH 3; hunk 5 (`:943-945`) = F-T79-2's last
  `in bijection with`. **One-to-one. No fourth substantive edit rode along.**
- The full branch diff vs `main` touches exactly five paths: `emi.go` and four handoffs
  (`T70.md`, `T72.md`, `T78.md`, `T88.md`). No vector store, no `.softhouse/capture/`,
  no signed review artefact, no `contract.go`.
- `git diff 406ad3c 722f018` touches **only** the T88 handoff — the handoff commit does
  not smuggle a source change.

## Preserved verbatim — confirmed

Since the diff is confined to five hunks I read in full, everything outside them is
byte-unchanged by construction; I additionally confirmed the named survivors are present
and equinumerous at both heads [VERIFIED: combined `grep -c` over
`OUTPUT IDENTITY ON ONE SHAPE`, `NOT TIGHT`, `allowFullTermForTranche`, `P-04t`,
`STRICTLY NEGATIVE`, `IT NEEDS A CAPTURE`, `Do NOT cite` → **15 at `b2ebe52`, 15 at
`406ad3c`**]. No citation was lost: every line number in the removed lines (`:149`,
`:280`, `:317`, `:356`, `:718`, `:722`, `:723`) reappears in the added lines. Step (e)'s
non-tightness, condition (7)'s admission, the `P-04t` material and the DO-NOT-CITE
prohibition are intact, and **`emi_L < 0` is still `[UNVERIFIED]` and still routed to a
capture, not softened** [VERIFIED].

## Zero executable change — both proofs recomputed, digests not copied

**Proof (a) — non-comment changed lines under `nexus/`** [VERIFIED, run by me at final
head `722f018`]:

```
git diff main...722f018 -- nexus/ | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vcE '^[+-][[:space:]]*//'
→ 0
git diff softhouse/T78-fui-marker-d5..722f018 -- nexus/ | (same filter)
→ 0
```

**Proof (b) — comment-stripped byte identity with `main`** [VERIFIED, computed by me]:

| | lines | sha256 |
|---|---|---|
| `main` | **609** | `e660867196b5bea6aa1abd98bb843e917f8bc7de0af1d574c74384b2a1133a4d` |
| `722f018` | **609** | `e660867196b5bea6aa1abd98bb843e917f8bc7de0af1d574c74384b2a1133a4d` |

`cmp` → **byte-identical**. Both the line count and the digest match T88's claim exactly,
independently derived.

**Consequence, which I agree with:** the compiled surface is byte-identical to `main`, so
`go test` and `.softhouse/conformance.sh` would grade `main`, not this branch. I did not
run them, and I did not touch the reference oracle containers other workers are using.
This is a comment-only change; **no parity claim is made or affected, and nothing is cut
over.**

## Gate G-3 — holds

[VERIFIED, run by me over T88's **whole tree** extracted via `git archive 722f018`, using
the repo-local toolchain at `.softhouse/toolchain/go/bin/gofmt`, list mode only, never
`-w`]:

```
gofmt -l . → nexus/internal/apps/loanschedule/contract/contract.go
```

**Exactly one path, and it is the frozen contract — the expected G-3 state. `emi.go` is
NOT named**, so the doc-comment list-item constraint that tripped T78's first draft is
respected. 21 `.go` files scanned. `contract.go` sha256 is
`0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` on **both** `main` and
this branch, and `git diff --stat main...722f018 -- .../contract/contract.go` is empty
[VERIFIED]. The frozen contract is untouched.

Longest line T88 added is **81 columns**, inside the block's existing wrap [VERIFIED,
measured over the diff's added lines].

---

## Probing the region around the work (P-19)

A green check on the three edits says nothing about the parts nobody pointed at. Since
T78's grep attestation had already failed once on graph 3, I re-ran **all five** tripwire
censuses rather than only the one under review.

| graph | block's claim | my independent re-derivation at `426a23544` |
|---|---|---|
| 1 — `setFutureUnrecognizedInterest` | 3 assignment sites in main: `:1184`, `:1246`, `AdvancedPaymentScheduleTransactionProcessor.java:1995`; plus `RepaymentPeriod.java:127` fed by `:156`, propagating only | **EXACT.** Repo-wide grep excluding `/src/test/` returns those three and no others. `:127` is `this.futureUnrecognizedInterest = futureUnrecognizedInterest;` in the constructor and `:156` passes `repaymentPeriod.getFutureUnrecognizedInterest()` through the copy constructor — **propagation only, confirmed** |
| 2 — `…OnScheduleModelCopyAndDefer` | 2 callers (`:392`, `:1217`), 1 declaration (`:1221`) | **EXACT** |
| 3 — `calculateEMIValueAndRateFactors` | 9 lines, 4 of them calls | **EXACT as corrected by T88** (was wrong before this patch) |
| 4 — `EmiChangeOperation.Action` | 4 constants, `:32-37` | **EXACT** |
| 5 — `calculateLastUnpaidRepaymentPeriodEMI` | 17 call sites; `13 + 4 = 17` | **EXACT.** grep returns 18 hits = 17 calls + declaration `:1160`. All thirteen post-origination sites listed in the block (`:368, :380, :404, :442, :505, :626, :698, :868, :879, :937, :1091, :2024, :2129`) match the grep line-for-line, and the four reasoned sites are `:747, :247, :1214, :1288` |

**All five counts are now correct.** Graph 3 was the only defect and T88 fixed it. This is
what makes F-T89-1 a provenance leak rather than a live error.

### I closed T88's own follow-up F-T88-1, and it comes back clean

T88 declined the private-callee census for the other three `:718` entry sites as outside a
three-edit budget and recorded it as a follow-up. It is two commands, so I ran it
[VERIFIED: `grep -n "addCapitalizedIncome(\|addRepaymentPeriods(\|changeInterestRate("`
over `ProgressiveEMICalculator.java` at the pin]:

- `addCapitalizedIncome`: `:269` public decl, `:271` public→private, `:274` private decl,
  `:1752`. **No unnamed caller** — `:1752` is already named in the block.
- `changeInterestRate`: `:287` public decl, `:289` public→private, `:350` private decl.
  **No further caller.**
- `addRepaymentPeriods`: `:293` public decl, `:295-296` public→private, `:300` private
  decl. **No further caller.**

Private methods are file-scoped, so this grep is exhaustive by construction.
**`:1107` was the only unnamed private-method caller in the file, and the block now names
it. F-T88-1 can be closed as done-and-negative rather than scheduled.**

### Observation, not a finding: the inherited T78 handoff still states the old count

`T78.md:100-105`, carried onto this branch and headed for `main`, still reads "Exactly
four call sites, in **BIJECTION** with a compiler-fixed enum … grep returns call lines
`:149`, `:280`, `:317`, `:356`, the declaration `:718`, and dispatch lines `:722`,
`:723`" — i.e. both the withdrawn bijection framing and the 7-line enumeration [VERIFIED].

**I am explicitly NOT asking for this to be edited.** A handoff is a dated record of what
a task actually claimed; rewriting it to match a later correction would falsify the audit
trail, and the correction is discoverable from T79's review and T88's handoff, both of
which merge alongside it. I record it only so a future grep for the stale count finds a
ruling attached rather than an open question.

---

## Non-negotiables (graded against `CLAUDE.md` and `.softhouse/patterns.md` read from this worktree)

Comment-only, zero executable change, so most do not engage:

- **No floating point** introduced, in code, fixture, schema or prose. The money symbols
  the edits touch (`emi_f`, `P + I`, `u_L`, `cdi_f`) are inherited verbatim from `4507109`
  and the port's residual remains integer minor units. **PASS.**
- **No MySQL / MariaDB / Oracle Database** driver, dialect, `ojdbc`, `oracle.jdbc` or port
  1521 in the diff; no database contacted. "Oracle" appears only in the test-oracle sense.
  **PASS.**
- **No deposit / insured / protected / guaranteed** language. **PASS.**
- **No `first_name`/`last_name`**, no hard-coded time-zone offset, no US payment rails or
  vendors. **PASS.**
- **Frozen adapter contract untouched** — `contract.go` byte-identical on `main` and
  branch, never `gofmt -w`ed, gate G-3 in its expected state. **PASS.**
- **Scope guard** — one source file, inside the assigned `loan-schedule` context. **PASS.**
- **Ledger / idempotency** — not engaged by a comment-only patch. **N/A.**
- **Honesty rule** — T88's handoff marks its inherited claims as inherited and does not
  hedge a `[VERIFIED]` tag. I found no overclaim in it; every proof it states, I
  reproduced. **PASS.**

## Summary for the driver

Apply **F-T89-1** (one line → two, `emi.go:928`), re-run `gofmt -l` to confirm G-3 is
undisturbed, and the block is done. Everything else in T88 is correct and independently
reproduced. **Do not reopen the argument, the censuses or the task shape** — the closed
form closes, and I verified all five of its censuses myself, not only the one under
review.

## Follow-ups

- **F-T89-2 (P3, inherited from T88's F-T88-2).** `emi_L < 0` remains the only open money
  question in the block and has now survived T66, T70, T71, T72, T78, T79, T88 and this
  review. **Stop sending readers at it.** Schedule a capture task with a single named
  integer detector — the final period's EMI — as T88 proposed.
- **F-T89-3 (P4, process, endorsing T88's F-T88-3).** A retry brief that names one
  location for a corrections finding invites P-12. Briefs should say "**and every
  restatement of it**", and reviewers should state findings against the *claim*, not
  against a line number. F-T89-1 is the proof that this still bites even when the worker
  gets it right: T88 swept the value and still missed the attestation.
- **F-T89-4 (P4).** Consider adding `:743` is the sole caller of
  `calculateEMIOnNewModelAndMerge` to part 9 as a sixth tripwire graph. The closure's
  unreachability argument depends on it, and it is currently unstated and uncounted — a
  second caller could appear in the pinned oracle without any of the five counts moving.
  **Not a defect today** (I verified it holds), and explicitly **not** something to fold
  into this patch.
