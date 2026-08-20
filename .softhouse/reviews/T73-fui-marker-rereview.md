# T73 — independent re-review of `softhouse/T72-fui-marker-retry`

Reviewer: independent (T73). Subject: the `futureUnrecognizedInterest` rule block in
`nexus/internal/apps/loanschedule/emi.go`, fourth draft. Read from the BRANCH
(`git show softhouse/T72-fui-marker-retry:...`), diffed `main...softhouse/T72-fui-marker-retry`.
Pinned reference oracle (Fineract) checkout `/Users/buv/fineract` at
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, verified clean before and after
[VERIFIED: `git log -1` = `426a23544e8426a38ae43ae404670a0a7e85b9eb`, `git status --porcelain` empty].
Nothing in the pinned checkout was written, committed or branched. No oracle container,
`c_configuration` row or tenant was touched. No `git push`.

> Terminology: "the oracle" throughout is the **Fineract reference implementation**.
> Oracle Database is prohibited in this program and is not involved.

Honesty rule: every material claim is marked `[VERIFIED: source]` or `[UNVERIFIED]`.

---

## VERDICT: **REJECTED**

Not for anything the previous three reviews found, and not for T71's hole — T71's hole is
genuinely closed, and closed well. It is rejected because **the rule is still INSUFFICIENT
in exactly the way it was rejected for last time**, one call frame further out.

The decisive test I was asked to run is: construct a shape that satisfies EVERY clause the
comment writes and still routes the `futureUnrecognizedInterest` decision outside steps
(a)-(g). **I constructed one, and it is not exotic — it is a mid-term interest rate
variation, which the frozen contract itself names twice as a domain-widening event, and
which reaches the very `:747` seam this block declares safe from inside the same
`generate()` call the block is written about.**

---

## F-T73-1 (P1, THE REJECTION) — `:747` is not one entry, it is FOUR, and condition (6) blesses all four

### The mechanism, from primary source

`calculateLastUnpaidRepaymentPeriodEMI` (`:1160`) is entered at `:747`, at the bottom of
`calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod` (`:730-751`), which is
dispatched from `calculateEMIValueAndRateFactors` (`:718-728`) at `:723`.

The block reasons about `:718` as if it had ONE caller. It has **four**
[VERIFIED: `grep -n "calculateEMIValueAndRateFactors" ProgressiveEMICalculator.java` at
`426a23544` returns call lines `:149`, `:280`, `:317`, `:356` plus the declaration at `:718`;
each resolved by walking up to its enclosing signature]:

| call | enclosing method | `tillDate` handed to `:747` | fenced by the rule? |
|---|---|---|---|
| `:149` | `addDisbursement` (`:137-153`), else arm | `getEffectiveRepaymentDueDate(..., operation.getSubmittedOnDate())` `[:150]` | yes — this is the entry (a)-(g) is about |
| `:280` | `addCapitalizedIncome` (`:274-283`) | `getEffectiveRepaymentDueDate(..., operation.getSubmittedOnDate())` | yes, but **accidentally** — condition (4) excludes capitalized income for a *different* reason (a term of `diff`), never as a second route into `:747` |
| `:317` | `addRepaymentPeriods` (`:300-319`) | `getEffectiveRepaymentDueDate(..., submittedOnDate.minusDays(1))` | **NO** |
| `:356` | `changeInterestRate` (`:350-359`) | `getEffectiveRepaymentDueDate(..., submittedOnDate.minusDays(1))` `[:357]` | **NO** |

[VERIFIED: `:149-151`, `:274-283`/`:280`, `:300-319`/`:317`, `:350-359`/`:351`,`:356-358` all
opened at `426a23544`.]

### Why `:356` is the counterexample and not a theoretical one

`changeInterestRate` is not future work reachable only after a contract change. It is called
**from inside `generate()`**, the Path A seam entry point this whole block exists to describe:

```
ProgressiveLoanScheduleGenerator.generate(mc, loanApplicationTerms, ...)   :87
  for (repaymentPeriod : expectedRepaymentPeriods)                         :116
      applyInterestRateChangesOnPeriod(...)                                :120
          loanApplicationTerms.getLoanTermVariations()
              .getInterestRateFromInstallment()...
              .forEach(change -> emiCalculator.changeInterestRate(...))    :273
                  ProgressiveEMICalculator.changeInterestRate(:350)
                      calculateEMIValueAndRateFactors(:356) -> :718 -> :723 -> :730 -> :747 -> :1160
```

[VERIFIED: `ProgressiveLoanScheduleGenerator.java:87`, `:116`, `:120`, `:265-279`, `:271-274`
opened at `426a23544`. Fineract's own comment at `:119` reads "in same repayment period the
logic firstly applies interest rate changes and just after the disbursements".]

Now check the shape against every clause the block writes. Single disbursement, flag false,
nothing paid, no credits, no capitalized income, no fixed interest, no re-aging, no interest
pause, the five other pins held, `GradedDomain` byte-for-byte unchanged — plus one
`interestRateFromInstallment` term variation:

- **(1) `allowFullTermForTranche = false`** — satisfied.
- **(2) exactly one disbursement** — satisfied (`len(r.Disbursements) == 1`).
- **(3) nothing is ever paid** — satisfied. A rate variation is not a payment.
- **(4) no credited amounts / no capitalized income** — satisfied.
- **(5) no fixed interest, no re-aging, no interest pause** — satisfied. **The clause names
  `applyInterestPause`, which lives THREE LINES BELOW the rate-change call in the same
  method (`ProgressiveLoanScheduleGenerator.java:276-278`), driven off the same
  `LoanTermVariations` object — and does not name the rate change.**
- **(6) "THE SEAM STAYS THE ORDINARY `:747` ENTRY"** — **satisfied literally and
  affirmatively.** The `:1160` call site on this route IS `:747`. None of the thirteen named
  post-origination sites is used. `13 + 1 + 2 = 16` still reconciles, so the block's own
  staleness detector stays green.
- **(7) the other five pinned oracle inputs** — satisfied. The annual nominal rate is not one
  of the five.
- **(8) `GradedDomain` is not widened in any other respect `[admit.go:999-1060]`** —
  satisfied. `GradedDomain` has **no** predicate about term variations and the contract has
  **no** field for them [VERIFIED: I read `GradedDomain` in full at
  `conformance/admit.go:999-1060` on the branch — its predicates are minor-unit digits,
  significant digits, rate-factor scale, rounding mode, disbursement count, repayment-every,
  frequency unit, interest method, day count, down-payment percentage, installment rounding
  multiple, and the window predicate. Nothing else]. A reader can truthfully say `GradedDomain`
  was not widened by one character.

And on that route the argument is void:

- **Step (b) is FALSE.** `tillDate` is anchored at `submittedOnDate.minusDays(1)` mapped
  through `getEffectiveRepaymentDueDate` `[:351, :357]`, not at the disbursement. The block's
  (b) says in capitals that the anchor is decided by the product flag — true for
  `addDisbursement`, and it is not the only thing that decides an anchor.
- **Step (e) is FALSE, and fails through the exact mechanism (e) cites as its protection.**
  (e) says the level-installment write "IS REACHED ONLY VIA `:741`, under
  `onlyOnActualModelShouldApply` (`:733-735`) -- which is what condition (2) is really
  protecting". On the rate-change route `:741` **is** taken — because `:734` is
  `operation.getAction() == EmiChangeOperation.Action.INTEREST_RATE_CHANGE`, a disjunct of
  the guard, not because the model is empty [VERIFIED: `:733-735` reads
  `isEmpty() || INTEREST_RATE_CHANGE || ADD_REPAYMENT_PERIODS || isCopy()`]. So
  `calculateEMIOnActualModel` writes onto `getRelatedRepaymentPeriods(tillDate')` on a model
  where **every** period already carries a non-zero EMI from origination, and (e)'s premise
  "emi_j = 0 for every j < f", the premise (e) itself calls "the premise the whole step turns
  on", is false.
- **The decision then runs at `:1217` -> `:1221-1252` -> `:1246`** with an anchor and a model
  state that steps (a)-(g) never covered, and that pass 3h never observed.

This is T71's finding again, mirrored. T71 broke T70 because T70 mis-filed an ORIGINATION
call (`:247`) among post-origination sites, so a reader could satisfy the letter while
standing on it. T72 fixes that, and then **omits three post-origination operations from the
enumeration entirely** — because they are not `:1160` call sites — while its condition (6)
puts an affirmative safe label on the seam all three of them reuse. The block's closing
sentence, "This block establishes the `:747` entry, on the domain fenced by (1)-(8), and
nothing else", is the false-comfort sentence: there is no such thing as "the `:747` entry".

### Why this is not a nitpick

The frozen contract the block cites six times names this exact operation, twice, as one of
the three things that widen the domain:

- `contract.go:563-564`: "It stops being inert the moment an interest pause, **a mid-term
  rate change** or a multi-tranche disbursement enters the domain." [VERIFIED: read on the
  branch]
- `contract.go:2117-2118`: "nothing tests it under multi-tranche, an interest pause **or a
  rate change**. [UNVERIFIED outside the graded domain]" [VERIFIED: read on the branch]

The rule fences the flag (1), multi-tranche (2) and the interest pause (5). It is silent on
the third member of the contract's own triple. That is not a gap nobody could have seen; it
is a gap named in the document the author quoted from five separate line ranges.

### No money has moved and no vector is wrong today

To be explicit, because the honesty rule cuts both ways: **this is a defect in the RULE, not
a live parity failure.** The route is held off today by the adapter handing the seam a
`LoanApplicationTerms` whose `getLoanTermVariations()` is null or carries no
`interestRateFromInstallment` entry, so `:267-269` returns early [VERIFIED: `:265-269` read at
`426a23544`; that the seam's assembler in fact supplies none is **[UNVERIFIED]** — I did not
find an assembler source in `.softhouse/capture/` that sets it, and the contract has no field
for it]. Nothing in the 36-vector corpus is red and nothing needs re-capturing for this. The
rule's entire job is to be the fence that a future porter reads before widening; a fence with
this hole in it is the thing this task family exists to prevent.

### What would fix it

A new lapse condition, or a rewrite of (6). Not a micro-fix — it is a new clause plus a
correction to (e)'s forward pointer, and it is money-adjacent prose, so it goes back to the
author. Sketch, for the retry to verify rather than copy:

- Fence the rate change by name: **no mid-term interest rate variation**, citing
  `ProgressiveLoanScheduleGenerator.java:120` and `:271-274` and
  `ProgressiveEMICalculator.java:350-359`/`:356`, with the reason: it re-enters `:747` inside
  the same `generate()` on a non-empty model with an anchor at
  `submittedOnDate.minusDays(1)`, voiding (b) and (e).
- Recast (6) so the fence is on **the callers of `:718`**, not only on the callers of
  `:1160`. State that `:718` has four callers and name all four with their anchors.
- Correct (e): `:741` is reached under a **four-term disjunction**, and condition (2) protects
  only the first term.

---

## F-T73-2 (P2) — condition (2)'s stated mechanism reduces a four-term disjunction to one term

Condition (2) reads:

> "so unless every EMI is still zero, `onlyOnActualModelShouldApply` is FALSE
> [VERIFIED: `:733-735`] and the write path (e) depends on, `:741`'s
> `calculateEMIOnActualModel`, is NOT taken"

`:733-735` is [VERIFIED, read at `426a23544`]:

```java
final boolean onlyOnActualModelShouldApply = scheduleModel.isEmpty()
        || operation.getAction() == EmiChangeOperation.Action.INTEREST_RATE_CHANGE
        || operation.getAction() == EmiChangeOperation.Action.ADD_REPAYMENT_PERIODS || scheduleModel.isCopy();
```

The sentence is a biconditional-shaped reduction of a four-term disjunction to its first
term, marked `[VERIFIED]` against the very line that carries the other three. On a second
DISBURSEMENT the second and third disjuncts are false, so the sentence's *conclusion* holds
today; but `scheduleModel.isCopy()` is not excluded by the stated hedge and is not mentioned
anywhere in the block [VERIFIED: `isCopy()` is `modifiers.get(COPY)`,
`ProgressiveLoanInterestScheduleModel.java:452-454`, set true by the private copy constructor
used by `deepCopy` `:130-134`]. I checked reachability rather than assert it: no `deepCopy` /
`copyWithoutPaidAmounts` caller in Fineract main routes back into `addDisbursement`
[VERIFIED: `grep -rn "deepCopy(\|copyWithoutPaidAmounts("` over
`fineract-progressive-loan/src/main` and `fineract-provider/src/main` returns
`ProgressiveEMICalculator.java:623, :650, :1224, :1275, :1749` and the two definitions, none
of which disburses], so the omission is **not** currently exploitable. It is still a guard
transcribed as something narrower than it is, in a block whose own standing instruction is
"Resolve ... every guard to its actual condition, before you write it down." The same
one-term reading is what F-T73-1 rides through `:734`.

## F-T73-3 (P2) — the `13 + 1 + 2 = 16` staleness detector counts the wrong call graph

The block offers that arithmetic as its tripwire: "If that arithmetic stops reconciling, the
call graph moved and this whole block is stale." It counts callers of `:1160` only. The two
graph edges that actually carry this argument are not in the count:

1. **`:718` has four callers** (F-T73-1). Adding a fifth leaves 16 reconciling.
2. **`calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer` (`:1221`), the method
   that performs the decision and writes the field at `:1246`, has TWO callers, not one**:
   `:1217` (inside `:1160`) and **`:392`, inside `payInterest` (`:385-405`)**
   [VERIFIED: `grep -n "calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer"`
   returns `:392`, `:1217` and the declaration `:1221`; `:392` resolved to its enclosing
   signature at `:385`]. `:392` reaches `:1246` **without passing through `:1160` at all**.

`:392` is excluded today by condition (3) ("NOTHING IS EVER PAID"), so this one is closed —
but again by accident, and the block nowhere states that the decision has a second, non-`:1160`
entrance. A reader auditing "how can this field get written" is handed a `:1160` call-site
census and will conclude, wrongly, that it is exhaustive. A correct tripwire counts callers
of `:718` and of `:1221` as well.

## F-T73-4 (P3) — the "231" figure in the handoff is stale, though the claim behind it holds

The handoff states the unfiltered non-comment changed-line count is 231, "all 231 ... markdown
lines of the inherited `T70.md`". I checked rather than accepted it.

- At the true branch head `4507109` the unfiltered count is **613**, not 231
  [VERIFIED: I ran the author's own pipeline].
- The author measured on `d0fbb42`, which they state explicitly ("All runs on the final branch
  head `d0fbb42`"), and at that commit `T70.md` alone yields exactly **231**
  [VERIFIED: `git diff main...T72 -- .../T70.md | ... | grep -vcE '^[+-][[:space:]]*//'` = 231].
  The T72 handoff itself was committed afterwards as `4507109` and adds the other 382.

So the claim was true when measured and is honestly attributed; it is simply not true of the
head a reviewer diffs. Not a defect in the diff. Recording it so the next reviewer does not
re-derive the discrepancy and mistake it for a false claim.

---

## Everything I checked that PASSED

### 5. Zero executable change — verified two independent ways, both by me, at head `4507109`

| proof | result |
|---|---|
| non-comment changed lines under `nexus/` | **0** [VERIFIED: `git diff main...softhouse/T72-fui-marker-retry -- nexus/ \| grep -E '^[+-]' \| grep -v '^[+-][+-]' \| grep -vcE '^[+-][[:space:]]*//'` = 0] |
| comment-stripped byte identity vs `main` | **identical** — both 609 lines, both sha256 `e660867196b5bea6aa1abd98bb843e917f8bc7de0af1d574c74384b2a1133a4d`, `diff` exit 0 [VERIFIED: run by me; the digest matches the author's reported value exactly] |
| files touched | exactly three: `emi.go` and the two handoff markdowns [VERIFIED: `--name-only`] |
| `go build ./...` / `go vet ./...` | exit 0 / exit 0 [VERIFIED: repo-local `go1.26.6 darwin/arm64`] |

### 6. `contract.go` untouched and never `gofmt`ed — the expected G-3 Option A state

- `contract.go` is byte-identical between `main` and the branch [VERIFIED: `diff -q` on both
  extracted blobs, exit 0].
- `gofmt -l internal` from `nexus/` names **exactly** `internal/apps/loanschedule/contract/contract.go`
  and nothing else [VERIFIED: run by me].
- The branch's `emi.go` is gofmt-clean, so the 344-line comment is format-stable
  [VERIFIED: extracted the branch blob to a temp path and ran `gofmt -l` on it — empty output].

### 1. Line citations — I re-opened every one at `426a23544`; all resolve

I did not spot-check. I dumped all ~100 cited lines and walked each `:1160` call site up to its
enclosing signature. Everything the block cites resolves to the method the text names,
including the three the driver had already blessed and the corrections T70 made:

- `:1224` is `scheduleModel.deepCopy(mc)`; **`:1226` is a comment line** — the drifted value in
  `T66.md` / `PASS3H-REPORT.md` / the driver's own re-derivation is confirmed WRONG and the
  block's `:1224` is confirmed RIGHT.
- `:1246` is `setFutureUnrecognizedInterest(period.getUnrecognizedInterest())`; **`:1250` is
  `});`**.
- `:1205` is `getEmi().add(diff, mc)`, `:1210` is `setEmi(adjustedEmi)`, and **`:1207` is the
  second line of the `getFixedInterest()` `if` condition**, exactly as the block says.
- `ProgressiveEMICalculator.java:259` is `// Currently N+1 scenario is not supported.` — R-2's
  file qualifier is necessary and correct.
- `RepaymentPeriod.java:259` is `calculatedDueInterest.add(getFixedInterest())` — the intended
  referent.
- `RepaymentPeriod.java:282-283` — the `Memo.of` dependency array **does** literally list
  `emi`. R-3's load-bearing qualifier is correct.
- `InterestPeriod.java:168-188` — `updateOutstandingLoanBalance` really does span to `:188` and
  really does assign only `outstandingLoanBalance` (`:173`, `:183`). T70's `:168-186` was two
  lines short; T72's widening is right.
- `ProgressiveLoanInterestScheduleModel.java:394-399` is `isEmpty()`; `:191-198`/`:196` is
  `getRelatedRepaymentPeriods` and its `!isBefore` filter; `:106-108` is `recordOverdueCorrection`,
  and `:377` is its **only** caller in Fineract main [VERIFIED: repo-wide grep], which is what
  step (a)'s overdue-branch dismissal needs.
- All sixteen `:1160` call sites resolve to the methods the block labels them with — I walked
  every one to its signature: `:368`←`:362` `addBalanceCorrection`, `:380`←`:372`, `:404`←`:385`
  `payInterest`, `:442`←`:408` `payPrincipal`, `:505`←`:498` `addCredit`, `:626`←`:621`,
  `:698`←`:647`, `:868`←`:831` `changeDueDate`, `:879`←`:872` and `:937`←`:884` re-amortization,
  `:1091`←`:1039` re-age attach, `:2024`←`:2020` interest pause, `:2129`←`:2079`
  `reAgeEqualAmortization`, `:247`←`:206`, `:1214`←`:1160`, `:1288`←`:1258`.
- Port-side: `contract.go:1173-1186` (the six pins), `:1179`, `:1191-1202`, `:866-869` ("a PIN
  (DEC-1 section 4.4), NOT a section 3.1 graded-domain predicate"), `:1330-1342`;
  `admit.go:999-1060` and `:1018-1020`; `structural.go:257-276` (`T17-F3`,
  `ClaimNarrowedByObservation`) — all confirmed on the branch.

**Zero citation defects found.** Given the citation drift that propagated through three
documents in the previous fire, this is the strongest part of the diff and the author's claim
to have re-opened every one, including the driver's known-good list, holds up under a full
independent re-derivation.

### 8. The `P-04t` claim — independently verified, and it is TRUE

This is the most important assertion in the diff and I re-derived it from the artefacts rather
than from the handoff:

- `.softhouse/vectors/loanschedule/P-04t-fulltermfortranche-true.json` has `"class": "parity"`
  and `request.disbursements` with **exactly one** element [VERIFIED: parsed the JSON myself].
- Its `provenance.capture_ref` is `.softhouse/capture/out/capture-prod3b-raw.json`,
  `capture_case_id` `P-04t`; in that file **`captures[7].id == "P-04t"` and
  `inputs.allowFullTermForTranche == true`**, and every other capture in the file is `false`
  [VERIFIED: I walked the raw capture JSON].
- All 18 pass-3h cases carry `inputs.allowFullTermForTranche == false`
  [VERIFIED: `{False: 18}` over `capture-prod3h-raw.json`].
- `GradedDomain` contains **no** predicate that could distinguish them [VERIFIED: I read the
  entire function at `admit.go:999-1060`; the eleven scalar predicates plus the window
  predicate are listed in F-T73-1 above, and `allowFullTermForTranche` is not among them, nor
  is there a contract field for it].

So the finding stands exactly as written: **a `parity` vector is admitted, graded and green
while its oracle run took the `:247` entry.** The block is right to name it, right to call the
byte-identity "OUTPUT IDENTITY ON ONE SHAPE -- a measurement, and NOT coverage", and right to
forbid citing `P-04t` as evidence for (a)-(g). The vector's own `title` and `_note` already
carry the DUPLICATE-SHAPE WARNING and say the evidence "lives in the CAPTURE, not in this
file", which corroborates it from a third artefact.

**Is the comment's mitigation sufficient for a reader who only ever reads the port?** For this
one flag, yes, and it is the best part of the draft: the "HOW TO CHECK CONDITION (1), BECAUSE
THE HARNESS CANNOT" sub-paragraph tells the reader the check is on
`inputs.allowFullTermForTranche` in the capture JSON and never on the vector request, names the
offending vector by filename, and says in terms that a vector can be green while its oracle run
took `:247`. A reader who reads only the port learns everything they need. F-6's proposed
provenance-carried harness refusal is the right mechanical follow-up and is correctly scoped
out of a comment-only task.

But note the shape of that admission, because F-T73-1 is the same shape one level up: the
author established that **a pin the contract states is not enforceable by the harness**, and
then fenced exactly one such pin by prose. The rate-change route is a second unenforceable
condition that the prose does not fence at all.

### 2. Nothing is asserted that the capture did not observe

Clean. (i) opens "THE COPY'S INTERNAL STATE WAS NEVER OBSERVED, by anyone", separates "Steps
(a)-(g) are proof; the 416 rows are observation of the outcome", and says explicitly that pass
3h reads the REAL model and not "the copy's intermediate u_k cascade". Steps (a) and (c) do
reason about the copy — as deduction, correctly labelled. The OBSERVED paragraph's figures are
attributed to `capture-prod3h-raw.json` and the digest to the attestation, and the census is
marked NOT re-run at T70 or T72 with the reason (the harness survives only as a `.txt`). I
found no sentence anywhere in the block that upgrades a reading to an observation. The R-4
correction is real and well handled: the block now claims LAST-ness rather than once-ness,
prints an explicit DO NOT WRITE prohibition against the false sentence, cites `:1214` as the
falsifier, and records that the upstream attestation still carries the false sentence and is
deliberately not edited from a comment-only task.

### 3. The lapse list

Present, and each premise it names is correctly attached to the step it protects — payments
(3) to (c) and (e), credits and capitalized income (4) to `diff` in (d) and to
`totalCreditedAmount` in (ii), fixed interest / re-aging / interest pause (5) to `cdi_k` in (c),
multi-tranche (2), the flag (1). **Incomplete** — see F-T73-1 for the missing member.

### 4. `(e)`'s non-tightness

Preserved verbatim and in the right place: "THE BOUND IN (e) IS NOT TIGHT above a per-period
rate factor of 1.00. Above that the conclusion is carried by the capture and the census below,
not by the inequality. Do not restate it as a tight bound." The two rate-factor-10.00 captures
are named. No drift toward a tight-bound restatement anywhere.

### 7. Conditions (7) and (8) — honest scoping, but (8) does not do the work it looks like it does

**(7) is honest scoping and deserves credit.** It names the five un-analysed pins and says in
the comment itself that "NONE of them was analysed against (a)-(g) by T66, T70 or T72; they are
listed here so that relaxing one is a DECISION and not an oversight." That converts an unknown
into a named, checkable pin instead of claiming coverage it does not have. This is the right
move and the right way to write it. The handoff repeats the admission rather than burying it.

**(8) is the clause I would push back on.** It reads as the catch-all that makes the rule
sufficient, and it is scoped to `GradedDomain` — "THE GRADED DOMAIN IS NOT WIDENED IN ANY OTHER
RESPECT `[conformance/admit.go:999-1060]`", with examples that are all `GradedDomain`
predicates (down payments, repayment frequency or unit, rounding mode). But this block is a
marker on PORT code, and the failure mode it must fence is a porter growing the port, not only
a vector being admitted. F-T73-1's counterexample **does not widen `GradedDomain` at all** —
there is no predicate there to widen, because the contract has no field for a term variation.
So (8) does not catch it, and the reader who checks (8) honestly gets a green light.

That is the difference between a cautious clause and a constraining one, and it is why I am
not treating (8) as covering the gap: an over-hedged catch-all that is scoped to the wrong
artefact fails to constrain exactly as badly as a missing clause.

---

## Non-negotiables

No engagement. There is no executable change at all, so: no floating point introduced or
described as acceptable; no MySQL / MariaDB / **Oracle Database** driver, dialect, `ojdbc`,
`oracle.jdbc` or port 1521 anywhere in the diff; no deposit / insured / protected / guaranteed
language; no `first_name` / `last_name`; no hard-coded time-zone offset; no US payment rails or
vendors; PostgreSQL untouched. Money is not described in anything but integer minor units — the
port's residual is referred to as `emiMinor` by name only. The one money-math *correction* in
the draft (the pre-assignment qualifier on `Σ_j emi_j = P + I` in (d)) is correct and its
justification via the `emi`-bearing memo key at `RepaymentPeriod.java:282-283` checks out.

## What I did NOT do

- I did not re-run `.softhouse/conformance.sh` or `--prove`. The comment-stripped byte identity
  against `main` makes the conformance numbers a property of `main`, not of this diff, and the
  oracle is in concurrent use by another worker.
- I did not re-take any capture and did not touch the reference-oracle instance in any way.
- I did not re-run the 21,060-shape census (same reason the author did not: it would mean adding
  a test file under a zero-executable-change constraint).
- I did not attempt to settle whether `emi_L` can go strictly negative on an admitted shape. The
  block's `[UNVERIFIED]` on it, and its instruction to settle it by capture rather than by
  reading, are correct and I am not second-guessing them.
- **[UNVERIFIED]** whether the capture harness's `LoanApplicationTerms` assembler in fact leaves
  `loanTermVariations` null/empty. I looked for an assembler source under `.softhouse/capture/`
  and found only decompiled Path B wiring dumps. This does not affect F-T73-1, which is about
  what the rule permits, not about what today's captures did.

---

## Summary for the driver

| # | finding | pri | who |
|---|---|---|---|
| F-T73-1 | A mid-term interest rate variation satisfies all of (1)-(8) and re-enters `:747` from `ProgressiveLoanScheduleGenerator.java:120` → `:273` → `ProgressiveEMICalculator.java:356`, on a non-empty model with a non-disbursement anchor, voiding (b) and (e). `:718` has four callers; condition (6) fences only `:1160`'s. The contract itself names "a mid-term rate change" twice as a widening event. **THE REJECTION.** | P1 | `coder` (fifth draft) |
| F-T73-2 | Condition (2) reduces the four-term disjunction at `:733-735` to `isEmpty()`, marked `[VERIFIED]` against the line carrying the other three. Not exploitable today (`isCopy()` unreachable from `addDisbursement` — I checked every `deepCopy` caller), but it is the same one-term reading F-T73-1 rides through `:734`. | P2 | same draft |
| F-T73-3 | `13 + 1 + 2 = 16` counts callers of `:1160` only. `:718` has four callers and `:1221` has two — `:1217` and **`:392` inside `payInterest`, which reaches the `:1246` write without passing through `:1160`**. The tripwire cannot detect the moves that matter. | P2 | same draft |
| F-T73-4 | Handoff's "231" is correct at `d0fbb42` but is 613 at branch head `4507109` (the T72 handoff commit adds the rest). Honest and attributed; recorded so the next reviewer does not re-derive it. | P3 | none |

T71's hole is closed and closed well; the citation work is the cleanest in this task family so
far; and the `P-04t` finding is real, correctly characterised, and the single most valuable
thing in the diff. The block is nonetheless not yet sufficient, for the same reason as last
time: a condition that names a mechanism the reader will take as protective, whose real
predicate is wider than the text admits.
