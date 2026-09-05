# T539 — applying T538's five conditions on T534

Branch `softhouse/T539-t538-conditions`, cut from `main` at `a19ea967`.
Scope: comments and documentation only. No executable byte moved (proof in §6).

---

## 0. Provenance

```
$ git -C /home/user/fineract rev-parse HEAD
426a23544e8426a38ae43ae404670a0a7e85b9eb
```

Verified **before** the first citation was opened. Every span quoted below was read from that
checkout at that sha, by `sed -n` on the file, not from T538's review and not from T534's handoff.
I read T538's `REVIEW.md` for the *conditions*; the *enumeration* below is mine, and where it
differs from T538's I say so.

`InterestPeriod.java` is **237 lines** (`wc -l`), unchanged from what T530/T534/T538 measured.

**Search-space closure.** Before claiming any enumeration is complete I bounded it:

```
$ grep -rn "List<InterestPeriod>" --include=*.java . | grep -v /src/test/
ProgressiveLoanInterestScheduleModel.java:293   (local alias inside insertInterestPeriod)
RepaymentPeriod.java:56                          (the field itself)
RepaymentPeriod.java:115                         (the protected constructor parameter)
RepaymentPeriod.java:438                         (a read-only local in getLastInterestPeriod)
```

Four occurrences in the whole non-test tree. There is no other handle on a segment list, so every
mutation must go through `RepaymentPeriod.getInterestPeriods()` (a plain Lombok `@Getter` on the
live `ArrayList` — `RepaymentPeriod.java:54-56`, no defensive copy) or through that one alias at
`:293`. That closes the search; the greps below are then exhaustive over it.

---

## 1. MAJOR-1 — contiguity restated as a property of the INSERTION path

### 1.1 The premise T534 asserted is false, and I confirmed each leg myself

| fact | span read | what it says |
|---|---|---|
| both date fields are publicly settable | `InterestPeriod.java:47-52` | `@Setter @NotNull private LocalDate fromDate;` / `@Setter @NotNull private LocalDate dueDate;` |
| the list is handed out live | `RepaymentPeriod.java:54-56` | `@Getter @Setter private List<InterestPeriod> interestPeriods;` — Lombok getter, no copy |
| nothing re-sorts it | grep for `.sort(`, `Collections.` over the four files | **zero** hits on `interestPeriods`; `InterestPeriod implements Comparable` but its `compareTo` is never used to order this list |
| interior shrink with no truncation | `ProgressiveEMICalculator.java:1791-1794` | `findRepaymentPeriod(t).flatMap(rp -> rp.findInterestPeriod(t)).ifPresent(ip -> ip.setDueDate(t));` — and `:1796-1800` then *iterates the successors* to zero their rate factors, which is positive evidence they are still in the list |
| the contrasting site DOES truncate | `ProgressiveEMICalculator.java:665` then `:666-678` | `ip.setDueDate(targetDate); int index = ...indexOf(ip); int nextIdx = index+1; ... subList(nextIdx, size).clear();` |
| the list is rebuilt wholesale, unchecked | `InterestScheduleModelRepositoryWrapperImpl.java:95-100` → `ProgressiveLoanInterestScheduleModelParserServiceGsonImpl.java:66, :87` | `extractModel` maps `json_model` through `fromJson`; `:66` registers an `InstanceCreator<InterestPeriod>`; `:87` is `gson.fromJson(s, ProgressiveLoanInterestScheduleModel.class)`. Plain reflective population. No ordering validation anywhere. `getSavedModel` (`:110-128`) then re-processes transactions **onto the loaded model**. |

So "contiguous by construction" as an unconditional invariant is wrong, and the comment no longer
says it. What it now says is that contiguity holds **on the insertion path**, and it names the
clamp that makes that true: `calculateNewDueDate`
(`ProgressiveLoanInterestScheduleModel.java:439-442`) returns
`date < prev.from ? prev.from : date > prev.due ? prev.due : date`, so the split point cannot
escape the parent range.

### 1.2 THE CONCLUSION — re-derived here, not restated

**Invariant P.** *For a segment list `s_0 … s_{n-1}`, for all `i < j`: `from_j >= due_i`.*

P is strictly weaker than contiguity (contiguity is `from_{i+1} == due_i`); it permits gaps,
zero-length segments and inverted segments. P is what the conclusion actually needs, because the
oracle's match window is `(from, due]` for every segment except the first segment of the first
repayment period, where it is `[from, due]`
(`LoanRepaymentScheduleProcessingWrapper.java:251-254`; `DateUtils.java:415-417` and `:407-409`).
Two segments `i < j` both matching `t` requires `t <= due_i` **and** `t > from_j`, i.e.
`from_j < due_i` — the negation of P. So **P ⟹ axis 2 is latent.**

Below, every site. "Preserves P" means: if the list satisfied P before, it satisfies P after.

#### A. Construction / insertion — 4 sites (grep: `InterestPeriod.(withEmptyAmounts|copy|empty)`, `new InterestPeriod(`, and every `.add(` on a segment list)

| # | site | span | effect | preserves P? |
|---|---|---|---|---|
| A1 | `RepaymentPeriod.create` | `RepaymentPeriod.java:143-151` (add at `:149`) | fresh `new ArrayList<>()` (`:145-146`) then **one** segment `[fromDate, dueDate]` | yes — P is vacuous on a singleton |
| A2 | `RepaymentPeriod.copy` | `:153-171` (loop `:167-169`) | iterates the source **in order**, appends `InterestPeriod.copy(…, mc)` which passes `getFromDate()`/`getDueDate()` straight through (`InterestPeriod.java:75-80`) | yes — same dates, same order ⇒ P inherited from the source |
| A3 | `RepaymentPeriod.copyWithoutPaidAmounts` | `:173-198` (loop `:190-196`) | same, via the 2-arg `InterestPeriod.copy` (`InterestPeriod.java:86-92`); only `balanceCorrectionAmount` is touched, never a date | yes — same reason |
| A4 | `ProgressiveLoanInterestScheduleModel.insertInterestPeriod` | `:280-296` (`setDueDate` `:287`, `add(previousIndex+1, …)` `:295`) | split in place | yes — proved below |

**A4 in full.** Let `P` be the selected segment at true index `p`, `OD = due_P` before the call,
`ND = calculateNewDueDate(P, balanceChangeDate)`. The selector is
`findPreviousInterestPeriod` (`:327-329`): the **last** segment whose from-exclusive window contains
the date, else the **first** segment. The clamp (`:439-442`) gives, for a non-inverted `P`
(`from_P <= OD`), `from_P <= ND <= OD`. Then, with the successor `N = [ND, OD]` inserted at `p+1`:

- **`due_P` only shrinks** (`ND <= OD`). Pairs `(P, j>p)` need `from_j >= ND`; we had
  `from_j >= OD >= ND`. ✔
- Pairs `(i<p, P)` need `from_P >= due_i`; `from_P` is untouched. ✔
- Pair `(P, N)`: `from_N = ND = due_P` — **equal, not less**. ✔
- Pairs `(i<p, N)`: need `from_N = ND >= due_i`. `ND >= from_P` (clamp) and `from_P >= due_i` (P). ✔
- Pairs `(N, j>p)`: need `from_j >= due_N = OD`. That is exactly old P for the pair `(P, j)`. ✔

Note this proof uses **only P**, never contiguity — so it holds **over a pre-existing gap**, which
is the case T538 said it checked and which I have now checked independently.

#### B. Date mutation on an `InterestPeriod`, outside `insertInterestPeriod` — 9 sites

`grep -rn "setFromDate\|setDueDate"` over the non-test tree returns 23 hits. I classified every one
by receiver type; only these 9 have an `InterestPeriod` receiver. (`ProgressiveEMICalculator.java`
`:834`, `:846`, `:854`, `:1065`, `:1152`, `:2035` and
`AdvancedPaymentScheduleTransactionProcessor.java` `:1849`, `:3271-3272`, `:3405-3406`, `:3591`,
`:3860` are `RepaymentPeriod` or `LoanRepaymentScheduleInstallment` receivers — they move the
*enclosing period's* bounds or an installment's, not a segment's, so they cannot bear on P.
`fineract-rates`, `fineract-working-capital-loan`, `fineract-core` and `fineract-loan` hits are on
unrelated types.)

| # | span | receiver | why it preserves P |
|---|---|---|---|
| B1 | `PEMIC:665` (+ truncation at `:666-678`) | `rp.findInterestPeriod(t)` — possibly interior | `due` shrinks (see D-answer §2), **and** every successor is cleared at `:677-678`, leaving it last. Nothing after it to overlap. ✔ |
| B2 | `PEMIC:687` (+ truncation at `:688-690`) | `getFirst()` | sets `due_0 := from_0`. If `s_0` were inverted this **grows** `due_0` and could break P — but `:689` then clears `subList(1, size)`, leaving a singleton, where P is vacuous. Guarded by `size() > 1`; if size == 1 there is nothing to break. ✔ |
| B3 | `PEMIC:838` | `getLast()` | only the LAST segment's `dueDate`. P constrains a segment's `due` only against **later** `from`s; the last segment has none. Direction irrelevant. ✔ |
| B4 | `PEMIC:857` | `getFirst().setFromDate` | only the FIRST segment's `fromDate`. P constrains a segment's `from` only against **earlier** `due`s; the first has none. Direction irrelevant. ✔ |
| B5 | `PEMIC:859` | `getLast()` | as B3 ✔ |
| B6 | `PEMIC:1066` | `getInterestPeriods().getLast()` | as B3 ✔ |
| B7 | `PEMIC:1153` | `getInterestPeriods().getLast()` | as B3 ✔ |
| B8 | `PEMIC:1794` | `rp.findInterestPeriod(t)` — possibly interior, **no truncation** | shrink only ⇒ opens a **gap**. Full answer in §2. ✔ |
| B9 | `PEMIC:2036` | `getInterestPeriods().getLast()` | as B3 ✔ |

B3–B7 and B9 are the load-bearing structural observation: **a `dueDate` write on the last element
and a `fromDate` write on the first element can never violate P, in either direction, even when
they produce an inverted segment** — because P only ever compares a `due` leftwards against a
later `from`.

#### C. Deletion / removal — 5 sites

| # | span | shape |
|---|---|---|
| C1 | `PEMIC:654` | `rp.getInterestPeriods().clear()` |
| C2 | `PEMIC:677-678` | `subList(nextIdx, size).clear()` — suffix |
| C3 | `PEMIC:689` | `subList(1, size).clear()` — suffix |
| C4 | `PEMIC:692` | `clear()` |
| C5 | **`AdvancedPaymentScheduleTransactionProcessor.java:3592`** | `lastPeriod.getInterestPeriods().removeIf(ip -> !ip.getFromDate().isBefore(transactionDate))` — arbitrary-position removal |

All five preserve P for one reason: **removal produces a subsequence.** Every surviving pair `(i,j)`
was a pair of the original in the same order, and no date changed. If no original pair had
`from_j < due_i`, no surviving pair does. ✔

**C5 is a site T538 did not list.** T538's deletion row named only `:654, :678, :689, :692`. I found
`:3592` by grepping mutating calls on `interestPeriods` across the whole non-test tree rather than
only inside `ProgressiveEMICalculator`. It is harmless, but a *complete* enumeration is the whole
claim here, so it is recorded.

#### D. Reordering — 0 sites

No `sort`, no `Collections.reverse`, no `set(int, …)`, no `swap` on a segment list anywhere in the
non-test tree. `InterestPeriod implements Comparable<InterestPeriod>` (`:43`) but nothing calls it
to order this list.

#### E. Deserialisation — 1 site, and it is the honest hole

`extractModel` (`InterestScheduleModelRepositoryWrapperImpl.java:95-100`) → `fromJson`
(`…ParserServiceGsonImpl.java:87`) with an `InstanceCreator<InterestPeriod>` at `:66`. Gson
populates the `ArrayList` reflectively from `m_loan_progressive_model.json_model`. **There is no
ordering check, no validation, no re-sort.** So P is not *enforced* on this path; it holds only
because the blob was written by a JVM in which the producer paths above ran. The row carries its
own `json_model_version` stamp, i.e. a list serialised by a different code version is restored
unchecked. I state this as a caveat rather than folding it into the proof, because it is not
provable from this tree — it is an assumption about what wrote the row.

#### F. The one corner where P itself bends — and it still cannot produce two matches

`insertInterestPeriod` locates the split point with
`interestPeriods.indexOf(previousInterestPeriod)` (`ProgressiveLoanInterestScheduleModel.java:294`).
`InterestPeriod` is `@EqualsAndHashCode(exclude = {"repaymentPeriod"})` (`InterestPeriod.java:41`),
so that is a **value** lookup, evaluated *after* `:287-290` have already mutated the target. If an
earlier segment `s_q` (`q < p`) is value-equal to the mutated `s_p`, the successor lands at `q+1`
instead of `p+1`.

Working it through: value equality forces `from_q == from_p` and `due_q == ND`; old P for `(q,p)`
forces `from_p >= due_q = ND`; the clamp forces `ND >= from_p`. Hence `ND == from_p == from_q ==
due_q` — `s_q` is **zero-length**, and so is the mutated `s_p`. The successor `N = [ND, OD]` is then
inserted before the segments `s_{q+1} … s_p`. For a `j` in that span, P would need
`from_j >= due_N = OD`, which is **not** guaranteed — so P can genuinely bend here. But old P also
forces `due_j <= from_p = ND` while `from_j >= due_q = ND`, i.e. `due_j <= ND <= from_j`: any such
`s_j` is inverted-or-zero-length, whose from-exclusive window `(from_j, due_j]` is **empty**. An
empty window matches nothing, so the bend cannot produce two simultaneous matches.

The same holds if the selected `P` is itself inverted: the clamp then yields either `ND = OD`
(successor `[OD, OD]`, zero-length, and it is never at index 0 so its window is `(OD, OD]` = empty)
or `ND = from_P` (successor `[from_P, OD]` with `OD < from_P`, inverted, window empty).

**So the correct statement of the conclusion is one notch weaker than P and one notch stronger than
what T538 wrote:** *no reachable path leaves two segments with simultaneously non-empty,
overlapping match windows.* P is the workhorse and holds everywhere except corner F, and corner F
bends only into a pair one of whose windows is empty.

#### G. The zero-length-first-of-first case, checked explicitly

The one non-empty window a zero-length segment can have is `[d, d]` for the **first segment of the
first repayment period** (the inclusive branch). Zero-length segments are deliberately created —
see the comment at `ProgressiveLoanInterestScheduleModel.java:269-270` ("we want to create a 0
length interest period … for any credit activity occurs on maturity date") and `PEMIC:687`. Could
`[d,d]` at index 0 co-match with a later `s_j`? That needs `from_j < d <= due_j`. P gives
`from_j >= due_0 = d`. So no. ✔

### 1.3 Verdict on MAJOR-1

Premise corrected, conclusion **retained and re-derived**. Axis 2 remains **LATENT** and does not
return to scope for T533.

---

## 2. The direction question for `:1794` — **GAP, not overlap**

Answered from source, explicitly, as instructed.

`ProgressiveEMICalculator.java:1791-1794`:

```java
1791: private void calculateRateFactorForScheduleTillDateInclusive(ProgressiveLoanInterestScheduleModel scheduleModelCopy,
1792:         LocalDate targetDate) {
1793:     scheduleModelCopy.findRepaymentPeriod(targetDate).flatMap(rp -> rp.findInterestPeriod(targetDate))
1794:             .ifPresent(ip -> ip.setDueDate(targetDate));
```

The mutated segment is whatever `RepaymentPeriod.findInterestPeriod` returned
(`RepaymentPeriod.java:442-447`), and that filter is
`isInPeriod(targetDate, ip.getFromDate(), ip.getDueDate(), …)`, which in **both** of its branches
ends in `!isAfter(target, to)` (`DateUtils.java:415-417` from-exclusive, `:407-409` inclusive).
So the returned segment necessarily satisfies **`targetDate <= due_ip`**.

Therefore `setDueDate(targetDate)` can only **shrink** `due_ip` (or leave it unchanged). `from_{ip+1}`
is not touched — `:1796-1800` walks the successors only to zero their `rateFactor`, and nothing in
`:1791-1803` removes or re-dates them. The result is

```
due_ip(new) <= due_ip(old) <= from_{ip+1}
```

i.e. **`due_i <= from_{i+1}` — a GAP.** Harmless to the reduction: a gap strictly *shrinks* the
match set, and P (`from_j >= due_i`) is preserved, not violated.

**What would have to be true for the other answer.** An overlap needs `due_ip` to **grow past**
`from_{ip+1}`, which needs `targetDate > due_ip(old)`. That is exactly the condition
`findInterestPeriod`'s filter excludes; the only way `:1794` could open an overlap is if the
segment it returned had failed its own filter, which is not reachable. The direction is decided by
the selector, not by the setter — and that is why the site falsifies contiguity without touching
the conclusion.

---

## 3. MAJOR-2 — the axis-2 sentence, fixed in BOTH places

The necessary condition is now stated as: **(i) two segments `i < j` in STRICT overlap,
`from_j < due_i`; or (ii) two segments with IDENTICAL non-empty `[from, due]` ranges** — with (ii)
noted as the `from_j == from_i < due_i == due_j` instance of (i). Both files also state explicitly
that a **shared** boundary (`from_j == due_i`) does **not** produce a second match, that it IS
contiguity, that it is verbatim the retired example, and that it comes back green — plus the same
for zero-length segments, gaps and inverted segments.

Applied in **two** places, per the "a correction applied in one of two places is a half-correction"
instruction:

1. `nexus/internal/apps/loanproduct/repaymentperiod.go` — the axis-2 paragraph.
2. `.softhouse/handoff/T534-t531-conditions.md` — **both** occurrences: the "One thing I derived
   beyond the brief" section (heading at `:81`, correction block `:83-…`) and the "One note for
   whoever executes T533" note (`:210-…`). Each carries a visible `CORRECTED BY T539` marker naming
   what was wrong, so the record shows the correction rather than silently overwriting it.

**Check.** `grep -n "duplicated boundaries"` over both files returns nothing. The only surviving
occurrence of the word "duplicated" anywhere in the T534 handoff is at `:195`, in the unrelated
sentence "**Verified, not duplicated.** I read T533 in `.softhouse/tasks.json`."

**Scope note, raised rather than buried.** My brief's HARD CONSTRAINTS list says I may touch only
`nexus/internal/apps/loanproduct/` and this handoff, while MAJOR-2 explicitly instructs me to fix
the same wording in `.softhouse/handoff/T534-t531-conditions.md`, and T540's brief says it will
check that I did. That file is on neither forbidden list (`savings/`, `conformance.sh`,
`.softhouse/guards/ledgerguard/`, `tasks.json`, `LOCK`, `RESUME.md`, `program.json`). I resolved the
tension in favour of the explicit instruction and the reviewer's stated check, and I am flagging it
here so the reviewer grades the decision rather than discovering it.

### T533's brief — confirmed correct, and NOT edited

I read `T533` out of `.softhouse/tasks.json` (read-only, via `python3 -c "json.load(...)"`). Its
case (c) block carries a section headed "*** CORRECTED A THIRD TIME AFTER T538 ***" which states,
verbatim:

> `Do NOT read "overlapping boundary" as "shared/duplicated boundary". A DUPLICATED boundary IS
> contiguity: [F,D0],[D0,D1] with t == D0 is verbatim the RETIRED green case … ONLY these two
> expose first-vs-last: (i) STRICT overlap — from_j < due_i, and (ii) two IDENTICAL non-empty
> ranges.`

So the driver's correction is in place and **names both (i) strict overlap `from_j < due_i` and
(ii) two identical non-empty ranges**, exactly as required. It also already carries the
"contiguity is not an invariant / `:1794` produces GAPS, never overlap" note.

**I did not edit `.softhouse/tasks.json`.** `git status` and the commit diff show it untouched.

---

## 4. MINOR-1 — the spot-check appositive in `doc.go`

I enumerated every `InterestPeriod.java` range `doc.go` cites, in **both** spellings it uses:
four written out in full (`:43-73` at `doc.go:237`, `:151` at `doc.go:166` and `:189`, `:168-188`
at `doc.go:196`, `:178` at `doc.go:290` — line numbers post-edit) and four written bare inside
RETIRED 1 at `doc.go:248-249` as `(:45)`, `(:65)`, `(:66)`, `(:68)`. Eight distinct ranges. The appositive named six; `:151` and `:168-188`
were missing, and both are load-bearing — `:151` is the entire warrant for evidence item 2 and
`:168-188` for item 3.

I chose to **add them** rather than weaken the sentence, because I opened both at `426a23544` and
both resolve and support what they are cited for:

- `:151` → `case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount();`, inside
  `getCalculatedDueInterest` (`:145-…`). Cited for "its single arithmetic consumer is the
  declining-balance branch". ✔
- `:168-188` → the whole body of `updateOutstandingLoanBalance()`, in which
  `balanceCorrectionAmount` sits beside `disbursementAmount` and `capitalizedIncomePrincipal` as
  summands of the roll-forward. ✔ (`:178` — `.plus(previousRepaymentPeriod.get().getPaidPrincipal(),
  getMc())` — is line 11 of that block, consistent.)

The sentence now names all eight, says which spelling each uses so a re-measure catches them both,
and keeps the disclaimer verbatim: still a spot check, still **not** a sweep of `interestperiod.go`.

I also re-confirmed the fact the `:45`/`:68` pair rests on:
`grep -c "@JsonExclude" InterestPeriod.java` = **2**.

---

## 5. MINOR-2 — both counts, re-derived

Measured myself:

```
$ grep -o "InterestPeriod\.java:[0-9]*\(-[0-9]*\)\?" interestperiod.go | sort | uniq -c
```

**28 occurrences across 26 distinct ranges** (`:151` and `:178` each occur twice; both are inside
the file). `wc -l InterestPeriod.java` = **237**.

- **WHOLLY past the end** (range start > 237): **TEN** — `:252-254`, `:256-259`, `:299-301`,
  `:303-305`, `:307-309`, `:311-313`, `:315-317`, `:319-321`, `:323-325`, `:327-329`.
- **OVERRUNNING the end** (start ≤ 237 < end): **ONE** — `:237-250`, which starts on the file's
  last line and runs 13 lines past it.
- **Total citing at least one nonexistent line: ELEVEN.**

Each of those eleven appears exactly once, so the range count and the occurrence count coincide
here. `:233-235`, `:229-231` and `:203-219` all end at or before 237 and are *inside*; they are
not part of either count.

`doc.go` now states both numbers separately and says which is which, so a reader re-measuring gets
the number they were quoted.

*A note on my brief's phrasing.* It said "10 **WHOLLY** past plus 11 that **OVERRUN** (`:237-250`)".
Since only one range overruns, I read "11" as "an eleventh". If the driver meant something else,
the raw measurement above is the thing to grade — 10 wholly past, 1 overrunning, 11 total.

---

## 6. MINOR-3 — the hard-coded oracle path

`doc.go:14` said the oracle is "at /Users/buv/fineract", which is right on Buyan's Mac and wrong on
the cloud fire — the same defect class as a citation that resolves on one machine. It now names the
**commit as the identity** of the oracle, states that the checkout path is not part of that
identity, names **both** known checkouts (`/home/user/fineract` cloud, `/Users/buv/fineract` Mac),
and tells the reader to confirm `git -C <checkout> rev-parse HEAD` prints `426a23544e…` before
trusting a line number.

The routing part of T538's condition 5 — `money.go:133` citing `InterestPeriod.java:215` for
`baseAmount.multiply(rateFactorTillPeriodDueDate, mc)` when the expression is at `:155` — is
**not** mine to fix (`money.go` is outside the comment blocks I was sent to correct, and re-pointing
a citation is exactly what I am forbidden to do). Filed as a proposed follow-up in §9.

---

## 7. BEHAVIOUR — comment-only, proved by construction

A renderer that parses each file with **comments off** (`parser.ParseFile(fset, f, nil, 0)`), then
additionally nils `File.Comments`, `File.Doc` and every `Doc`/`Comment` field on `GenDecl`,
`FuncDecl`, `Field`, `ValueSpec`, `TypeSpec` and `ImportSpec`, runs `ast.SortImports`, and prints
with `printer.Config{Mode: printer.RawFormat, Tabwidth: 8}`. Two renderings can differ only if a
**non-comment** byte differs.

```
$ git archive origin/main nexus/internal/apps/loanproduct | tar -x -C $SP/base
$ git archive HEAD        nexus/internal/apps/loanproduct | tar -x -C $SP/tip
$ cp nexus/internal/apps/loanproduct/*.go $SP/tip/nexus/internal/apps/loanproduct/   # working tree overlay
$ astcmp $SP/base/nexus/internal/apps/loanproduct > base.ast
$ astcmp $SP/tip/nexus/internal/apps/loanproduct  > tip.ast
$ wc -l -c base.ast tip.ast
  2621  78887 base.ast
  2621  78887 tip.ast
$ cmp base.ast tip.ast   ->   BYTE-IDENTICAL
$ sha256sum base.ast tip.ast
49470856bf2b0d5481d13b97348844b435249231ad8cca45d0ffc549ef91d819  base.ast
49470856bf2b0d5481d13b97348844b435249231ad8cca45d0ffc549ef91d819  tip.ast
```

**14 files each side. 2621 lines, 78,887 bytes each side. Identical sha256.**

`origin/main` at the time of the run was `6aa31e5e`; my branch was cut from `a19ea967`
(`git merge-base origin/main HEAD` = `a19ea967`). I ran the proof a second time against `a19ea967`
directly so the result does not depend on which base is used — also **BYTE-IDENTICAL**.

The renderer source is `astcmp/main.go` in this run's scratchpad; it is 60 lines of stdlib and is
reproduced in full in §10 so the reviewer can rebuild it rather than trust it.

Also run in the worktree:

```
$ gofmt -l nexus/internal/apps/loanproduct/     ->  (no output)
$ go build ./...                                ->  exit 0, no output
$ go test ./internal/apps/loanproduct/...       ->  ok  github.com/gerege/nexus/internal/apps/loanproduct  0.002s
```

---

## 8. Where my enumeration differs from T538's

Recorded because "a weaker premise supporting the same conclusion needs the support written down".

1. **T538 says "13 date-mutation sites in `ProgressiveEMICalculator`"; I count 9** with an
   `InterestPeriod` receiver (B1–B9). The other six `set{From,Due}Date` hits in that file
   (`:834`, `:846`, `:854`, `:1065`, `:1152`, `:2035`) have a **`RepaymentPeriod`** receiver. They
   move the enclosing period's bounds, not a segment's, and cannot bear on P. If T538 counted those
   too, 9 + 6 = 15, still not 13; either way the *set* is what matters and mine is closed by the
   `List<InterestPeriod>` grep in §0.
2. **T538's deletion row misses `AdvancedPaymentScheduleTransactionProcessor.java:3592`**
   (`removeIf` on a segment list). Harmless — removal yields a subsequence — but it is a real site
   (C5) and an enumeration that claims completeness must contain it.
3. **T538 could not construct the value-equality corner and left it as "not a finding".** I worked
   it through (§1.2 F): it is constructible in principle, it **does** bend P, and it still cannot
   produce two matches because the intervening segment must have an empty window. That is a
   strictly stronger result than "I could not construct one", and it is why the comment now states
   the conclusion as *non-empty overlapping windows* rather than as P alone.
4. **T538's "18 construction/mutation/deletion sites" resolves, on my count, to 19**: 4 construction
   + 9 date-mutation + 5 deletion + 1 deserialisation. The number is not the claim; the closure is.

None of these changes the conclusion. All three of T538's load-bearing negatives survive
independent re-derivation.

---

## 9. Proposed follow-up tasks (NOT done here — comments/docs only)

1. **`money.go:133` citation is broken.** It cites `InterestPeriod.java:215` for
   `baseAmount.multiply(rateFactorTillPeriodDueDate, mc)`; at `426a23544` line 215 is a closing
   brace and the expression is at `:155`. I did **not** re-point it — re-pointing a citation to make
   a mismatch disappear is forbidden, and `money.go` is outside my correction scope. Needs an owner
   (T532 if its scope covers `money.go`-class defects, otherwise a new citation-integrity task).
2. **`interestperiod.go`'s 28 citations are still UNSWEPT** — 11 of them cite lines that do not
   exist (§5). Owned by T532; unchanged by this task.
3. **No executable repair to `FindInterestPeriod`.** It still diverges from the oracle on both axes,
   by design: no Go change lands before T533's vectors exist. T533 is PARKED (needs the live
   reference oracle, unreachable from the cloud fire).

## 10. The renderer, for re-running §7

```go
package main

import (
	"fmt"; "go/ast"; "go/parser"; "go/printer"; "go/token"
	"os"; "path/filepath"; "sort"; "strings"
)

func main() {
	dir := os.Args[1]
	var files []string
	filepath.Walk(dir, func(p string, info os.FileInfo, err error) error {
		if err != nil { return err }
		if !info.IsDir() && strings.HasSuffix(p, ".go") { files = append(files, p) }
		return nil
	})
	sort.Strings(files)
	var out strings.Builder
	fset := token.NewFileSet()
	for _, f := range files {
		node, err := parser.ParseFile(fset, f, nil, 0) // ParseComments OFF
		if err != nil { panic(err) }
		node.Comments = nil
		node.Doc = nil
		ast.Inspect(node, func(n ast.Node) bool {
			switch d := n.(type) {
			case *ast.GenDecl: d.Doc = nil
			case *ast.FuncDecl: d.Doc = nil
			case *ast.Field: d.Doc, d.Comment = nil, nil
			case *ast.ValueSpec: d.Doc, d.Comment = nil, nil
			case *ast.TypeSpec: d.Doc, d.Comment = nil, nil
			case *ast.ImportSpec: d.Doc, d.Comment = nil, nil
			}
			return true
		})
		ast.SortImports(fset, node)
		cfg := printer.Config{Mode: printer.RawFormat, Tabwidth: 8}
		fmt.Fprintf(&out, "===== %s =====\n", filepath.Base(f))
		cfg.Fprint(&out, fset, node)
		out.WriteString("\n")
	}
	os.Stdout.WriteString(out.String())
	fmt.Fprintf(os.Stderr, "files=%d\n", len(files))
}
```

---

## 11. What I could not do, and why

- **No golden vector was captured or moved.** The live reference oracle (Fineract) is unreachable
  from the cloud fire, T533 is PARKED for that reason, and this task is comments/docs only. Nothing
  here claims parity.
- **The Gson path (§1.2 E) is a caveat, not a proof.** P is not enforced on deserialisation; I can
  show there is no ordering check, but I cannot show from this tree what wrote any given
  `json_model` row. Recorded as an assumption rather than folded into the derivation.
- **I did not re-run T530's full 28-citation sweep of `interestperiod.go`.** I re-derived only the
  two counts MINOR-2 asked for (§5) plus the eight `doc.go` ranges (§4). The banner's "23 of 28
  failing" is still T530's measurement, attributed as such, and `interestperiod.go` is still
  correctly labelled UNSWEPT.
- **`money.go:133`'s broken citation is left broken** and filed as §9.1 rather than fixed, per the
  standing rule against re-pointing citations.

---

## 12. Branch proof

```
$ git push -u origin softhouse/T539-t538-conditions
 * [new branch]        softhouse/T539-t538-conditions -> softhouse/T539-t538-conditions
   (succeeded on attempt 1; no retry needed)

$ git ls-remote --heads origin softhouse/T539-t538-conditions
e25e3f05fe9d7380e88e150769403f6fd5e9585b	refs/heads/softhouse/T539-t538-conditions
```

Pasted verbatim from the run immediately after pushing commit `e25e3f05`. This note is itself a
further commit on the branch, so the live tip is one commit ahead of the sha above — a commit
cannot contain its own hash. Re-run
`git ls-remote --heads origin softhouse/T539-t538-conditions` at any time for the authoritative tip;
the sha reported in T539's report message is the one to grade.

Files in this branch (`git diff --name-status a19ea967..HEAD`):

```
M  .softhouse/handoff/T534-t531-conditions.md
A  .softhouse/handoff/T539-t538-conditions.md
M  nexus/internal/apps/loanproduct/doc.go
M  nexus/internal/apps/loanproduct/repaymentperiod.go
```

Four files. `nexus/internal/apps/savings/`, `.softhouse/conformance.sh`,
`.softhouse/guards/ledgerguard/`, `.softhouse/tasks.json`, `.softhouse/LOCK`,
`.softhouse/RESUME.md` and `.softhouse/program.json` are all untouched.
