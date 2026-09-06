# T538 — INDEPENDENT REVIEW of T534 (`softhouse/T534-t531-conditions`, tip `7cfcd157`)

**VERDICT: ACCEPT WITH CONDITIONS** — 2 MAJOR, 3 MINOR.

The correction T531 demanded landed and it is right: the worked example now names an input that
genuinely diverges, and the retired example is correctly shown to agree. The two MAJOR findings are
both in the part T534 went *beyond* the brief to add — the contiguity derivation. Its **conclusion**
survives my attack; its **stated warrant is false**, and the sentence that tells T533 how to pin
axis 2 names a shape that would produce another green vector — the exact failure mode this whole
chain exists to stop, reintroduced one paragraph after the paragraph that warns about it.

---

## 0. Provenance and method

Pinned oracle: `/home/user/fineract`, `.git/HEAD` = `426a23544e8426a38ae43ae404670a0a7e85b9eb`.
Verified before any citation was opened.

**Base-drift note (procedural, not a finding against T534).** The brief's
`BASE=$(git merge-base origin/main origin/softhouse/T534-t531-conditions)` returns `7cfcd157` — the
branch tip itself — because T534 has already been merged into `main` (`afb1535e`). That form yields
an **empty diff** and would have made this review vacuous. The branch tip is a single-parent commit;
its parent `280da3bf` was `main` at the time the branch was cut, so the honest "what T534 changed"
range is `280da3bf..7cfcd157`, which is what I graded. Anyone re-running this review should use that
range, not the merge-base form, for any branch already merged.

Everything below was re-derived from the pinned tree. No T534 artefact was read as evidence; the
handoff was opened only at the end (§7).

---

## 1. THE REWRITTEN WORKED EXAMPLE — CLEAN

Re-derived from source, not from the block.

`LoanRepaymentScheduleProcessingWrapper.java:251-254` (opened, resolves verbatim):

```java
public static boolean isInPeriod(LocalDate targetDate, LocalDate fromDate, LocalDate toDate, boolean isFirstPeriod) {
    return isFirstPeriod ? DateUtils.isDateInRangeInclusive(targetDate, fromDate, toDate)
            : DateUtils.isDateInRangeFromExclusiveToInclusive(targetDate, fromDate, toDate);
}
```

`DateUtils.java:415-417` → `isAfter(target, from) && !isAfter(target, to)` — from-EXCLUSIVE,
due-inclusive. `:407-409` → `!isBefore(target, from) && !isAfter(target, to)` — both-inclusive.
Both resolve verbatim.

The fourth argument is supplied by `RepaymentPeriod.java:442-447`:

```java
.filter(interestPeriod -> isInPeriod(transactionDate, interestPeriod.getFromDate(), interestPeriod.getDueDate(),
        isFirstRepaymentPeriod() && interestPeriod.isFirstInterestPeriod()))
.reduce((one, two) -> two);
```

`isFirstRepaymentPeriod()` is `previous == null` (`RepaymentPeriod.java:449-450`), which the port's
`IsFirstRepaymentPeriod()` reproduces exactly. The Go body is unconditionally
`!t.Before(FromDate) && !t.After(DueDate)` — both-inclusive, first match.

**Divergent case, re-derived independently.** Non-first repayment period, segments `[F, D0]`,
`[D0, D1]`, `t == F`:

- Oracle: no segment is first-of-first, so all are from-exclusive. Seg 1 needs `isAfter(F, F)` →
  false. Seg 2 needs `isAfter(F, D0)` → false. `Optional.empty()`.
- Port: `!F.Before(F) && !F.After(D0)` → true → seg 1.

Empty vs a segment. **Confirmed.** The block names `transactionDate == the period's OWN FromDate` in
a NON-first period. Correct.

**Control, re-derived.** Same `t == F` in the FIRST repayment period: seg 1 is first-of-first →
inclusive → `F ∈ [F, D0]` → match; seg 2 is not first-of-first → `isAfter(F, D0)` false → no match;
last-match reduction yields seg 1; the port yields seg 1. Both sides agree. The control holds the
date fixed and varies only the `isFirstPeriod` flag, so it does isolate the boundary rule.
**Correct.**

**Retired case, re-derived.** `t == D0` (a later segment's from-date), non-first period: oracle
matches `[F, D0]` (`D0 > F`, `D0 ≤ D0`) and not `[D0, D1]` (`D0 > D0` false) → single match → `[F, D0]`;
port's first match is `[F, D0]`. Identical. Also identical in the first repayment period. The block
marks it **"DO NOT BUILD A VECTOR ON IT"** and explains why it comes back green. **Correct, and
explicitly retired.**

T531's worry — right about the rule, wrong about the example — is not reproduced here in either
direction. The rule statement (`[from, due]` first-of-first, `(from, due]` elsewhere) and the example
now agree with each other and with the oracle.

---

## 2. THE CONTIGUITY DERIVATION — 2 MAJOR

I attacked this the way the brief asked: by hunting every path that builds, mutates, reorders,
truncates or restores a segment list. `InterestPeriod` (the progressive-loan one) is confined to
`fineract-progressive-loan/src/main` — the only other `InterestPeriod*` hits in the tree are savings
`InterestPeriodType` enums, unrelated. So the search space is closed and I enumerated it.

### 2.1 The full mutation surface (what I searched, and what I found)

`InterestPeriod.java:47-52` carries **public Lombok `@Setter` on both `fromDate` and `dueDate`**.
`RepaymentPeriod.getInterestPeriods()` hands out the **live** `ArrayList`. Nothing validates,
asserts or re-sorts it. So contiguity is not enforced anywhere — it is at best a property of the
producers. Producers and mutators, all of them:

**Construction / insertion (4 sites)**
| site | effect |
|---|---|
| `RepaymentPeriod.java:149` (`create`) | one segment `[from, due]` |
| `RepaymentPeriod.java:167-169` (`copy`) | order-preserving deep copy |
| `RepaymentPeriod.java:190-196` (`copyWithoutPaidAmounts`) | order-preserving deep copy |
| `ProgressiveLoanInterestScheduleModel.java:280-296` (`insertInterestPeriod`) | split-in-place; successor `[newDueDate, originalDueDate]` at `previousIndex+1` |

`insertInterestPeriod` is contiguity-safe, and more so than the citation shows: `calculateNewDueDate`
(`:439-442`) **clamps** `newDueDate` into `[previous.from, previous.due]`, so the split can never
invert or escape the parent range. T534's citation resolves and supports what it is cited for.

**Date mutation outside `insertInterestPeriod` (13 sites — `ProgressiveEMICalculator.java`)**
| site | segment touched | contiguity effect |
|---|---|---|
| `:665` + `:677-678` | interior, then **all successors cleared** | safe (becomes last) |
| `:687` + `:688-690` | first, then **rest cleared** | safe (single segment) |
| `:838` | **last** only | safe (may invert `[from>due]`, never overlaps) |
| `:857` | **first**'s `fromDate` only | safe (interior boundaries untouched) |
| `:859`, `:1066`, `:1153`, `:2036` | **last** only | safe |
| **`:1794`** | **interior, NO truncation** | **BREAKS CONTIGUITY — leaves a GAP** |

**Deletion:** `:654`, `:678`, `:689`, `:692` — `clear()` / `subList(k,n).clear()`. Suffix removal or
full clear; prefix order preserved.

**Deserialisation (the path the brief named):**
`InterestScheduleModelRepositoryWrapperImpl.extractModel` (`:95-100`) →
`ProgressiveLoanInterestScheduleModelParserServiceGsonImpl.fromJson` (`:87`, with an
`InstanceCreator` registered for `InterestPeriod` at `:66`) — **plain Gson reflective population of
the list out of `m_loan_progressive_model.json_model`, with no ordering validation and no re-sort.**
`getSavedModel` (`:110-128`) then re-processes transactions **onto that loaded model**. So an entire
segment list is reconstituted without any producer path having run in this JVM, and the blob carries
its own `json_model_version` stamp — i.e. a list written by a different code version is restored
unchecked.

**One further fragility worth recording:** `InterestPeriod` carries
`@EqualsAndHashCode(exclude = {"repaymentPeriod"})`, so `interestPeriods.indexOf(previousInterestPeriod)`
at `ProgressiveLoanInterestScheduleModel.java:294` is a **value** lookup, not identity. Two
value-equal segments in one list would make the insert land at the wrong index. I could not
construct a reachable list with two value-equal segments *and* a resulting overlap (equal-dated
adjacent segments must be zero-length under contiguity, and zero-length segments never match), so
this is not a finding — but it is a second reason "by construction" is doing more work than the code
supports.

### 2.2 FINDING 1 (MAJOR) — contiguity is NOT invariant; `:1794` falsifies it

The comment states, flatly:

> Segments inside a repayment period are contiguous by construction — `insertInterestPeriod`
> truncates the predecessor to `newDueDate` and inserts the successor with `FromDate == that same
> newDueDate` `[VERIFIED: ProgressiveLoanInterestScheduleModel.java:280-296]`

and the derivation then uses `from_j == due_(j-1)` as an equality. That equality is **false** after
`ProgressiveEMICalculator.calculateRateFactorForScheduleTillDateInclusive`:

```java
1791: private void calculateRateFactorForScheduleTillDateInclusive(ProgressiveLoanInterestScheduleModel scheduleModelCopy,
1792:         LocalDate targetDate) {
1793:     scheduleModelCopy.findRepaymentPeriod(targetDate).flatMap(rp -> rp.findInterestPeriod(targetDate))
1794:             .ifPresent(ip -> ip.setDueDate(targetDate));
1795:
1796:     calculateRateFactorForPeriods(scheduleModelCopy.repaymentPeriods(), scheduleModelCopy);
```

I read `:1791-1803` in full: **there is no truncation of the successors** (unlike `:665`, which does
truncate at `:677-678`). `findInterestPeriod` guarantees `targetDate ≤ due_ip`, so `setDueDate`
**shrinks** the segment while `from_(ip+1)` keeps the OLD `due_ip`. Result: `from_(ip+1) > due_ip` —
a **gap**, in a list the comment says is contiguous by construction.

**The conclusion survives.** A gap only shrinks the match set: two simultaneous matches need
`from_j < due_i`, and a gap gives `from_j > due_i`. I worked the same test over every one of the 13
mutation sites, over both copy constructors, over `insertInterestPeriod` with a pre-existing gap, and
over the inverted (`due < from`) segments that `:838`/`:859`/`:2036` can produce — **none of them can
produce `from_j < due_i` for `i < j`.** Inverted segments have empty match windows; zero-length
segments never match under from-exclusive; gaps only remove matches. So **axis 2 does not come back
into scope for T533**, and I say so as the load-bearing negative result of this review.

But the *warrant* as written does not carry the conclusion. A porter who reads "contiguous by
construction" as an invariant — and implements `FindInterestPeriod` as a binary search, or asserts
`DueDate == next.FromDate`, or derives one boundary from its neighbour — is wrong on the `:1794`
path, and that path is inside the interest-recalculation money math. The claim is a load-bearing
statement about a money path, resting on one citation that only covers one of eighteen mutation
sites.

### 2.3 FINDING 2 (MAJOR) — "overlapping or duplicated boundaries" names a GREEN case

The axis-2 paragraph (`repaymentperiod.go:491-494`) closes:

> First-versus-last is therefore only observable on a segment list with **overlapping or duplicated
> boundaries**; pin it with its own case, not as a by-product of the boundary case.

A *boundary* here is a date. A **duplicated boundary** — the same date appearing as one segment's
due and the next segment's from — **is exactly what contiguity is**. On that reading the sentence
asserts axis 2 is observable on a contiguous list, contradicting the sentence immediately before it,
and pointing a T533 executor at `[F, D0], [D0, D1]` with `t == D0` — **which is verbatim the retired
example three paragraphs above, the one this very block proves comes back green.**

I checked the alternative readings against the oracle rather than arguing about the English:

| shape | can two segments match at once? |
|---|---|
| shared boundary `[F,D0],[D0,D1]`, `t=D0` | **NO** — seg 2 needs `D0 > D0`. Single match. |
| zero-length segment `[D0,D0]` anywhere | **NO** — from-exclusive window is empty; also never matches inclusive unless `t == D0` and it is first-of-first, still a single match |
| gap (`:1794`) | **NO** — strictly fewer matches |
| inverted `[from > due]` (`:838`) | **NO** — empty window |
| **strict overlap `from_j < due_i`, `i<j`** | **YES** |
| **two segments with identical non-empty `[from,due]`** | **YES** |

Only the last two rows expose the `.reduce((one,two)->two)` vs first-match difference. The comment
names one of them ("overlapping") and one non-case ("duplicated boundaries"), and the non-case is
the one a reader is most likely to be able to construct. This is the second-order version of the
defect T531 caught, sitting in the paragraph written to prevent it — and §7 shows it has already been
handed to T533.

---

## 3. THE SELF-CAUGHT ERROR — CLEAN (with MINOR 1)

All six ranges opened against `426a23544` and checked against what they are cited *for*:

| range | content at the pinned commit | cited for | verdict |
|---|---|---|---|
| `:43-73` | `class InterestPeriod` decl through `private boolean isPaused;` | "carries no `@Entity`, `@Table` or `@Column`" | **resolves**; annotations in range are only `@JsonExclude`/`@Setter`/`@NotNull`/`@Getter` |
| `:45` | `@JsonExclude` (on `repaymentPeriod`, field at `:46`) | "`@JsonExclude` on exactly two fields — repaymentPeriod (:45)" | **resolves** |
| `:65` | `private Money balanceCorrectionAmount;` | "carries none" | **resolves** |
| `:66` | `private Money outstandingLoanBalance;` | "carries none" | **resolves** |
| `:68` | `@JsonExclude` (on `mc`, field at `:70`) | "…and mc (:68)" | **resolves** |
| `:178` | `.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc())` | "updateOutstandingLoanBalance folds previousRepaymentPeriod.getPaidPrincipal()" | **resolves**, verbatim |

I also independently checked the "exactly two fields" claim the `:45`/`:68` pair rests on:
`grep -c "@JsonExclude" InterestPeriod.java` = **2**. Correct.

The final wording — "That is a spot check of the six ranges those arguments stand on, and it is not
a sweep of interestperiod.go; do not cite it as one" — claims no more than a spot check. **The
self-correction is sound and the relabelling is honest.**

**MINOR 1 — the enumeration is not the set it says it is.** The sentence reads "the InterestPeriod.java
ranges cited in the arguments below — :43-73, :45, :65, :66, :68 and :178". The appositive reads as
exhaustive, and it is not: **`:151`** (cited at `doc.go:150` and `:173`, the whole warrant for
evidence item 2 — "its single arithmetic consumer is the declining-balance branch") and
**`:168-188`** (cited at `doc.go:180`, the warrant for evidence item 3) are also InterestPeriod.java
ranges cited in the arguments below. I opened both: `:151` is
`case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount();` and `:168-188` is
`updateOutstandingLoanBalance()` — both resolve and both support their claims, so the omission costs
no accuracy. But a sentence whose job is to bound a claim must bound it correctly.

---

## 4. THE UNSWEPT BANNER — CLEAN (with MINOR 2)

Every number independently re-measured:

- **Citation count.** `grep -o 'InterestPeriod\.java:[0-9]*(-[0-9]*)?' interestperiod.go` → **28
  occurrences** across 26 distinct ranges (`:178` and `:151` each appear twice). Banner says 28. ✓
- **File length.** `InterestPeriod.java` is **237 lines**. Banner says 237. ✓
- **"23 of 28 failing to resolve."** I did not re-run T532's sweep, but I cross-checked the arithmetic
  and it is self-consistent: 10 ranges lie wholly beyond EOF, 1 more (`:237-250`) runs past it,
  17 occurrences fall inside the file. Of those 17 I spot-opened five and found `:193-201` (cited for
  `getCalculatedDueInterest`, actually `getCreditedAmounts`/`isFirstInterestPeriod`) and `:165-167`
  (cited for `addBalanceCorrectionAmount`, actually `getLengthTillPeriodDueDate`) both **fail**,
  while `:151`, `:178` and `:65-66` **resolve** — exactly the 5-that-resolve the banner's arithmetic
  implies. The claim is corroborated, not merely repeated.
- **Ownership.** Attributed to T530's measurement and T532's sweep, with "nothing here has covered
  it". Accurate — the diff touches neither file.
- **"do not apply an offset."** Correct and important: the ranges are not a shifted copy of anything;
  10 of them are past EOF by 60-90 lines while others are off by ~30 in the other direction.
- **Placement.** Lines 20-44 — immediately after the "Every behavioural claim carries a file:line
  citation" paragraph (`:14-18`) and **before** every argument section, opening with "Do not read the
  paragraph above as a warrant for the whole package." A reader meets the warning before they can
  mistake the package doc for an audit. ✓

**The decision NOT to banner `interestperiod.go` — I endorse it.** T532 owns that file and is
rewriting its citation block; a second banner would collide on merge and be deleted by the task that
fixes the underlying problem, for no reading benefit — `doc.go` already names `interestperiod.go`
explicitly and by task number, so the package doc a reader actually starts from carries the warning.
Putting a duplicate marker in a file about to be rewritten would trade a merge conflict for nothing.

**MINOR 2 — "10 of them citing past the end" is off by one under the natural reading.** Ten ranges
(`:299-301, :303-305, :307-309, :311-313, :315-317, :319-321, :323-325, :327-329, :252-254, :256-259`)
lie **wholly** beyond line 237, but an eleventh, `:237-250`, also cites lines that do not exist. Say
"ten lie wholly past the end of a 237-line file" (or "eleven cite past it") — either supports UNSWEPT,
but the number as written is not the number a reader re-measuring will get.

**MINOR 3 (pre-existing, NOT T534's — routing note only).** `doc.go:14` still names the oracle
checkout as `/Users/buv/fineract`; this environment's pinned checkout is `/home/user/fineract`. The
line is present at `280da3bf` and is outside T534's diff, so it is not a defect of this branch. Also
outside this branch: `money.go:133` cites `InterestPeriod.java:215` for
`baseAmount.multiply(rateFactorTillPeriodDueDate, mc)` — line 215 is the closing brace of
`getDisbursementAmount()`; the cited expression is at `:155`. That is a broken citation in a file the
banner correctly classifies as UNSWEPT, so it argues *for* the banner rather than against it, but it
needs an owner.

---

## 5. BEHAVIOUR — CLEAN, independently reproduced

I did not take T534's number. I wrote my own renderer
(`parser.ParseFile` with comment parsing **off**, `node.Comments = nil`, `ast.SortImports`,
`printer.Config{Mode: RawFormat}`), ran it over both trees extracted with `git archive`, and diffed:

```
14 files each side
2621 lines  base (280da3bf)
2621 lines  tip  (7cfcd157)
cmp base.ast tip.ast  ->  BYTE-IDENTICAL
```

(2607 code lines + 14 per-file separators my renderer emits. The 14-file count and byte-identity are
the load-bearing parts and both hold.)

Also run in the worktree at the tip:

- `go build ./...` → exit 0, no output.
- `go test ./internal/apps/loanproduct/...` → `ok github.com/gerege/nexus/internal/apps/loanproduct 0.003s`.

**Comment-only is confirmed by construction, not by assertion.**

---

## 6. SCOPE — CLEAN

`git diff --name-status 280da3bf..7cfcd157`:

```
A  .softhouse/handoff/T534-t531-conditions.md
M  nexus/internal/apps/loanproduct/doc.go
M  nexus/internal/apps/loanproduct/repaymentperiod.go
```

Three files. Filtering the change list for `savings/`, `.softhouse/conformance.sh`,
`.softhouse/guards/ledgerguard/` and `.softhouse/tasks.json` returns **nothing**. No money-path code,
no float, no ledger write, no schema, no config. The task's own statement that the orchestrator owns
`tasks.json` is borne out by the diff.

---

## 7. THE HANDOFF (read last, per the independence rule)

Checked only against what I proved. It claims nothing I disproved about the worked example — its
re-derivations of the divergent case, the control and the retired case match mine line for line, and
its supporting citations (`DateUtils.java:407-409`, `InterestPeriod.java:197-199`) both resolve.

Two things it does carry that my findings hit:

1. It labels `ProgressiveLoanInterestScheduleModel.java:280-296` **"This is the contiguity
   invariant"** — the claim Finding 1 falsifies at `ProgressiveEMICalculator.java:1794`.
2. **It has already propagated Finding 2 downstream.** Under "one note for whoever executes T533":
   *"case (c) needs a segment list with **overlapping or duplicated boundaries**, because a
   contiguous list can never produce two simultaneous oracle matches. Constructing (c) out of an
   ordinary contiguous schedule will produce a single-match input and another green-and-meaningless
   vector."* The warning is right and the prescription contains the trap: "duplicated boundaries" IS
   an ordinary contiguous schedule. T533 must not be executed against that sentence as written.

Note also: the handoff leans on a seventh InterestPeriod.java range (`:197-199`) beyond doc.go's
enumerated six. It resolves, but it is further evidence for MINOR 1 — the "six" is a count of what
was checked, not of what the reasoning stands on.

---

## Conditions (numbered, independently checkable)

1. **[MAJOR — Finding 2, do this first; it is already downstream]** In
   `repaymentperiod.go` replace "only observable on a segment list with **overlapping or duplicated
   boundaries**" with the actual necessary condition: *two segments `i < j` with `from_j < due_i`
   (strict overlap), or two segments carrying identical non-empty `[from, due]`*. State explicitly
   that a **shared boundary (`from_j == due_i`) and zero-length segments do NOT produce a second
   match** — and say so in one line that points back at the retired example, since that is the shape
   a reader will otherwise build. Apply the identical correction to the T533 note in
   `.softhouse/handoff/T534-t531-conditions.md`. **Check:** the phrase "duplicated boundaries" no
   longer appears in either file, and the replacement text names `from_j < due_i`.

2. **[MAJOR — Finding 1]** Restate the contiguity paragraph on a warrant that carries it. Contiguity
   is a property of the **producer paths**, not an invariant: `fromDate`/`dueDate` are public
   `@Setter`s (`InterestPeriod.java:47-52`), the segment list is handed out live, and nothing
   validates or re-sorts it. Record the actual weaker property I verified — *every mutation outside
   `insertInterestPeriod` touches only the first segment's `fromDate`, only the last segment's
   `dueDate`, or a segment whose successors are cleared in the same block; therefore no path
   produces `from_j < due_i`, and at most one segment can match* — and cite
   `ProgressiveEMICalculator.java:1794` as the one site that **breaks strict contiguity, leaving a
   gap (`from_j > due_i`) that only shrinks the match set**. Also note that `extractModel` →
   Gson `fromJson` (`InterestScheduleModelRepositoryWrapperImpl.java:95-100`;
   `ProgressiveLoanInterestScheduleModelParserServiceGsonImpl.java:66, :87`) rebuilds the whole list
   from `m_loan_progressive_model.json_model` with no ordering check. **Check:** the block no longer
   asserts `from_j == due_(j-1)` as an unconditional equality, `:1794` is cited, and the conclusion
   "axis 2 is LATENT" is retained — it is correct and I could not falsify it.

3. **[MINOR — Finding MINOR 1]** In `doc.go`, either add `:151` and `:168-188` to the spot-checked
   list (both resolve; I opened them) or reword the appositive so it does not read as the full set of
   InterestPeriod.java ranges cited below — e.g. "six of the InterestPeriod.java ranges cited below".
   **Check:** every InterestPeriod.java range appearing in `doc.go` after the banner is either listed
   or the sentence no longer claims to list them all.

4. **[MINOR — Finding MINOR 2]** In `doc.go`, correct "10 of them citing past the end of a 237-line
   file" to "ten of them lying wholly past the end of a 237-line file" (an eleventh, `:237-250`, also
   overruns it). **Check:** re-measuring the ranges reproduces the stated number.

5. **[MINOR — routing, not T534's defect]** Raise `doc.go:14`'s stale `/Users/buv/fineract` path and
   `money.go:133`'s broken `InterestPeriod.java:215` citation (the cited expression is at `:155`)
   against whichever task owns those files — T532 for the `money.go`-class defects if its scope
   covers them, otherwise a new citation-integrity task. **Check:** both appear in `.softhouse` as
   owned work.

None of these is a behavioural change; all five are comment/handoff edits and no golden vector moves.
Condition 1 is the one that must land before T533 is executed.

---

## Checks that came back clean (listed, per the brief)

- Worked example re-derived from `LoanRepaymentScheduleProcessingWrapper.java:251-254`,
  `DateUtils.java:415-417` and `:407-409`, `RepaymentPeriod.java:442-447` and `:449-450` — the
  divergent case, its first-of-first control, and the retired case all check out in both directions.
- Retired case explicitly marked "DO NOT BUILD A VECTOR ON IT" and its agreement re-derived.
- The block is now right about the rule **and** right about the example; T531's failure mode is not
  reproduced.
- All six spot-checked InterestPeriod.java ranges resolve and support their citations;
  `@JsonExclude` count independently confirmed at exactly 2.
- Banner numbers (28 citations, 237 lines, ownership, no-offset) re-measured and corroborated,
  including a five-range spot check of the "23 of 28 failing" arithmetic.
- Banner placement precedes every argument and disclaims the paragraph above it.
- Decision not to banner `interestperiod.go` — endorsed, with reasons.
- Comment-stripped AST byte-identical across 14 files, reproduced with my own renderer; build and
  tests green.
- Scope: three files; none of the four forbidden paths touched.
- **Axis 2:** searched all 18 construction/mutation/deletion sites, both copy constructors,
  `insertInterestPeriod` under a pre-existing gap, inverted and zero-length segments, the
  value-equality `indexOf` at `:294`, and the Gson deserialisation path. **No path produces
  `from_j < due_i`.** Axis 2 stays LATENT; it does not return to scope for T533.

---

## Branch proof

```
$ git ls-remote --heads origin refs/heads/softhouse/T538-review-t534
9ba3b1ee990aa5becdcd920c8066932639d4a16f	refs/heads/softhouse/T538-review-t534
```

Pasted verbatim from the run immediately after pushing commit `9ba3b1ee`. The branch has since taken
one further commit adding this note, so the live tip is one commit ahead of the sha above — a commit
cannot contain its own hash. The reported tip in the T538 report message is the authoritative one;
`git ls-remote --heads origin refs/heads/softhouse/T538-review-t534` re-run at any time gives it.
