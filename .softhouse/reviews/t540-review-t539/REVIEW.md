# T540 — INDEPENDENT REVIEW of T539 (`softhouse/T539-t538-conditions`)

**VERDICT: ACCEPT WITH CONDITIONS** — 0 MAJOR, 4 MINOR.

T539's central claim survives independent re-derivation. What landed is a **derivation, not a
restatement**: I enumerated the segment-list mutation surface myself, by a stronger instrument than
T539 used, and found no reachable path that produces `from_j < due_i` for `j > i`. **Axis 2 stays
LATENT and does not return to scope for T533.** The GAP answer is correct and, on the structure of
the call site, stronger than T539 argued for it. The byte-identity proof reproduces to the digit.

The four MINORs are all cases where my re-derivation landed somewhere slightly different from
T539's, in every case in the direction of the landed text being *safe but imprecise*. None of them
requires a re-capture, a code change, or a revision to the axis-2 conclusion. Two of the four are
routed to the driver, not to T539.

---

## 0. Provenance — what I verified before citing a line

| Check | Command | Result |
|---|---|---|
| Pinned reference oracle (Fineract) | `git -C /home/user/fineract rev-parse HEAD` | `426a23544e8426a38ae43ae404670a0a7e85b9eb` ✔ matches the commit of record |
| Subject tip | `git rev-parse origin/softhouse/T539-t538-conditions` | `5e9a9b320fd711da8815fe910ef5da3b8b4b887f` ✔ matches dispatch |
| Merge base | `git merge-base origin/main origin/softhouse/T539-t538-conditions` | `a19ea9674c5f9e4f4bc995c9304c3e0d3fe9c82a` |
| T539 merged? | `git merge-base --is-ancestor <tip> origin/main` | **NO** — the branch is unmerged, so my worktree (based on `main` @ `c2127db3`) does not contain it |

Every Fineract line quoted below I opened myself at `426a23544`. I did not treat T539's handoff as
evidence; I read it only to know which claims to attack, and I ran every measurement again.

### 0.1 T512's defect reproduced — and it would have produced a third false accusation

The two diff forms disagree exactly as T512 filed:

```
$ git diff --stat origin/main..origin/softhouse/T539-t538-conditions
 .softhouse/LOCK                              |   8 +-      <-- NOT T539's
 .softhouse/handoff/T534-t531-conditions.md   |  56 +-
 .softhouse/handoff/T539-t538-conditions.md   | 543 +++++
 .softhouse/tasks.json                        |  59 +--      <-- NOT T539's
 nexus/internal/apps/loanproduct/doc.go       |  40 +-
 nexus/internal/apps/loanproduct/repaymentperiod.go | 89 +-

$ MB=$(git merge-base origin/main origin/softhouse/T539-t538-conditions)
$ git diff --stat $MB..origin/softhouse/T539-t538-conditions
 .softhouse/handoff/T534-t531-conditions.md   |  56 +-
 .softhouse/handoff/T539-t538-conditions.md   | 543 +++++
 nexus/internal/apps/loanproduct/doc.go       |  40 +-
 nexus/internal/apps/loanproduct/repaymentperiod.go | 89 +-
```

Confirmed per-commit rather than by trusting the merge base:

```
$ git log --oneline $MB..origin/softhouse/T539-t538-conditions -- \
      .softhouse/tasks.json .softhouse/LOCK .softhouse/RESUME.md .softhouse/program.json
(no output — zero commits)
```

**`tasks.json`, `LOCK`, `RESUME.md` and `program.json` are untouched by T539.** The `main..branch`
form attributes `LOCK` and `tasks.json` to T539; both are `main` moving on underneath a branch based
on an older commit. Third measured occurrence of the instrument's failure mode; first time it has
been caught before publication.

---

## 1. THE CENTRAL RISK — the enumeration, re-derived independently

### 1.1 The search-space closure is TRUE but is not the instrument T539 says it is → **MINOR-A**

T539's §0 rests the closure on `List<InterestPeriod>` occurring exactly 4 times in the non-test
tree. That count is correct — and in fact tighter than claimed:

```
$ grep -rn "List<InterestPeriod>" --include=*.java . | grep -v "/src/test/" | grep -v "/src/integrationTest/"
ProgressiveLoanInterestScheduleModel.java:293
RepaymentPeriod.java:56, :115, :438
$ grep -rn "List<InterestPeriod>" --include=*.java . | wc -l
4                                          # 4 tree-wide, tests included
```

**But counting the type name does not close the search space.** `getInterestPeriods()` is a Lombok
`@Getter` returning the **live** `ArrayList` (`RepaymentPeriod.java:54-56`, read directly — the
field carries both `@Getter` and `@Setter`), so every caller mutates the list through the getter
without ever naming `List<InterestPeriod>`. There are **64** `getInterestPeriods()` call sites in
the non-test tree; the type-name grep sees four of them. A search-space claim that is wrong makes a
complete-looking enumeration incomplete, and this one is load-bearing by T539's own framing.

So I re-closed it with the operation-level instrument instead — every structural mutator and every
date setter, on any receiver:

```
$ grep -rn "nterestPeriods()\.add\|interestPeriods\.add\|nterestPeriods()\.remove\|\
interestPeriods\.remove\|nterestPeriods()\.clear\|interestPeriods\.clear\|\
nterestPeriods()\.subList\|nterestPeriods()\.set(\|nterestPeriods()\.sort" --include=*.java .
$ grep -rn "setDueDate\|setFromDate" --include=*.java . | grep -v "/src/test/"
$ grep -rn "getInterestPeriods()" --include=*.java . | grep -v "/src/test/"
$ grep -rn "extends RepaymentPeriod\|extends InterestPeriod" --include=*.java .   # empty — no subclasses
$ grep -rn "setInterestPeriods" --include=*.java . | grep -v "/src/test/"          # empty — whole-list replace never called
```

**The enumeration T539 landed survives that stronger closure intact.** MINOR-A is that the *stated*
warrant is weaker than the *actual* one, not that anything was missed.

### 1.2 The complete mutation surface, as I measured it

**Construction / insertion — 4 sites.** `RepaymentPeriod.java:149` (`create`, one segment spanning
`[from, due]` — a one-element list cannot contain a pair); `:168` and `:195` (the two copy
constructors, appending into a fresh `ArrayList` in iteration order);
`ProgressiveLoanInterestScheduleModel.java:295` (`add(previousIndex + 1, …)`, the only positional
insert in the tree). `insertInterestPausePeriodsByAdjustedDates` (`:298-315`) adds no new structural
path — it calls `insertInterestPeriod` and then only `setPaused`.

**Date mutation with an `InterestPeriod` receiver, outside `insertInterestPeriod` — 9 sites**, all
in `ProgressiveEMICalculator.java`. I opened every one:

| Site | Receiver / shape | Can it create `from_j < due_i`? |
|---|---|---|
| `:857` | `getFirst().setFromDate(newDueDate)` | No — `j = 0` has no `i < 0` |
| `:838`, `:859`, `:1066`, `:1153`, `:2036` | `…getLast().setDueDate(…)` | No — nothing follows the last segment |
| `:665` | `ip.setDueDate(targetDate)`, tail cleared at `:677-678` | No — `ip` becomes last |
| `:687` | `getFirst().setDueDate(getFirst().getFromDate())`, tail cleared at `:689` | No — one element survives |
| `:1794` | interior shrink, no truncation | **GAP only — see §2** |

**T539's correction (b) is CORRECT and I reproduce it exactly.** The six sites T538 counted —
`:834`, `:846`, `:854`, `:1065`, `:1152`, `:2035` — all have a **`RepaymentPeriod`** receiver
(`targetRepaymentPeriod`, `nextRepaymentPeriod` ×2, `firstPeriod = existingRepaymentPeriods.getFirst()`,
`currentPeriod = periods.get(i)`, and the `repaymentPeriod` parameter of `accelerateRepaymentDueDateTo`).
They move the enclosing period's bounds, not a segment's, and `findInterestPeriod` iterates one
repayment period's own list — so they cannot bear on the property. 15 setter hits − 6 = **9**. ✔

**Deletion — 5 sites**, and **T539's correction (a) is CORRECT**: `AdvancedPaymentScheduleTransactionProcessor.java:3592`
(`lastPeriod.getInterestPeriods().removeIf(ip -> !ip.getFromDate().isBefore(transactionDate))`) is a
real deletion site on a live segment list, and T538's row omitted it. With `:654`, `:677-678`,
`:689` and `:692` that is the complete set. All five only drop elements; a subsequence of a list
with no strict overlap has no strict overlap.

**Reordering — 0 sites.** No `sort`, no `reverse`, no `set(int, …)` on a segment list.
`InterestPeriod implements Comparable<InterestPeriod>` (`:43`) but nothing calls it to order this
list. `setInterestPeriods` has zero non-test callers. No subclass of either type exists, so the
`protected` constructor at `RepaymentPeriod.java:115` cannot be reached with a caller-supplied list
— all four factories pass `new ArrayList<>()`.

**Copy constructors — order- and date-preserving**, at exactly the spans T539 cites:
`RepaymentPeriod.java:153-171` and `:173-198`.

**Deserialisation — 1 site**, and every citation resolves: `extractModel`
(`InterestScheduleModelRepositoryWrapperImpl.java:95-100`) → `fromJson`
(`ProgressiveLoanInterestScheduleModelParserServiceGsonImpl.java:87`) with the
`InstanceCreator<InterestPeriod>` at `:66`; `getSavedModel` (`:110-128`) re-processes transactions
onto the restored list at `:122`. No ordering check, no validation, no re-sort anywhere on that
path. `@Table(name = "m_loan_progressive_model")` confirmed at `ProgressiveLoanModel.java:34`.

### 1.3 Verdict on the central risk

**No reachable code path in the pinned tree produces `from_j < due_i` for `j > i`.** Two segments
therefore cannot match `findInterestPeriod` at once, `.reduce((one, two) -> two)` is
indistinguishable from first-match, and **axis 2 remains LATENT**. What landed is a derivation. It
does not return to scope for T533.

---

## 2. GAP vs OVERLAP — CONFIRMED, and the "every call path" worry dissolves structurally

The brief asked whether the selector claim holds on *every* call path into `:1794`, or only the one
T539 looked at. **It holds on every path, because there is exactly one and it is not a call.**
`:1791-1794` read at the pin:

```java
1791:    private void calculateRateFactorForScheduleTillDateInclusive(ProgressiveLoanInterestScheduleModel scheduleModelCopy,
1792:            LocalDate targetDate) {
1793:        scheduleModelCopy.findRepaymentPeriod(targetDate).flatMap(rp -> rp.findInterestPeriod(targetDate))
1794:                .ifPresent(ip -> ip.setDueDate(targetDate));
```

`:1794` is a **lambda body inside the single expression begun at `:1793`**, closing over the same
`targetDate` the filter used. There is no signature through which an unfiltered date could arrive.
The same structure holds at the other interior-shrink site, `:664-665`.

The filter, opened end to end:

- `RepaymentPeriod.findInterestPeriod` — `RepaymentPeriod.java:442-447` ✔ exact span
- `LoanRepaymentScheduleProcessingWrapper.isInPeriod` — `:251-253`
- `DateUtils.isDateInRangeInclusive` — `DateUtils.java:407-409` ✔ exact
- `DateUtils.isDateInRangeFromExclusiveToInclusive` — `DateUtils.java:415-417` ✔ exact

**Both** branches require `!DateUtils.isAfter(targetDate, toDate)`, i.e. `targetDate <= due_i`. So
`setDueDate(targetDate)` can only **shrink** `due_i`, while `from_(i+1)` is untouched, leaving
`from_(i+1) >= old due_i >= new due_i`. **GAP, never overlap.** ✔ **T539's answer is correct.**

An overlap would require `due_i` to *grow* past `from_(i+1)`, i.e. `targetDate > due_i` — exactly
what the filter forbids. The operation is monotone non-increasing on every due date in the list, so
it cannot even convert a pre-existing gap into an overlap.

**One strengthening T539 did not state and could have.** The same filter also requires
`targetDate >= from_i` (`isAfter` on the from-exclusive branch, `!isBefore` on the inclusive one),
so the shrink cannot drive `due_i` below `from_i` either: `:1794` cannot invert a segment. That
closes a case the landed text leaves to the general "inverted segments have empty windows"
argument. Not a defect — a free tightening available to whoever ports this.

---

## 3. The `:294` value-equality corner — my derivation stops one step further than T539's → **MINOR-B**

This is the case the brief told me to attack hardest, and it is where I part company with T539.

T539's algebra is **correct as far as it goes**, and I reproduced it. `insertInterestPeriod`
(`ProgressiveLoanInterestScheduleModel.java:280-296`) locates the split point with
`interestPeriods.indexOf(previousInterestPeriod)` at `:294`, *after* `:287-290` have already mutated
the target. `@EqualsAndHashCode(exclude = { "repaymentPeriod" })` at `InterestPeriod.java:41` —
which I opened, and which excludes **only** `repaymentPeriod`, exactly as T539 states — makes that a
value lookup. If an earlier `s_q` (`q < p`) is value-equal to the mutated `s_p`, the successor lands
at `q+1`. T539 then derives, correctly, that value equality plus the old property plus the clamp
(`calculateNewDueDate`, `:439-442` ✔ exact span) force `ND == from_p == from_q == due_q`.

**But `ND == from_p` is not reachable for any `p` that has a predecessor.** T539 never checks
whether its necessary condition is compatible with how `s_p` was selected. `findPreviousInterestPeriod`
(`:327-329`) is:

```java
327:    private InterestPeriod findPreviousInterestPeriod(final RepaymentPeriod repaymentPeriod, final LocalDate date) {
328:        return repaymentPeriod.getInterestPeriods().stream().filter(ip -> date.isAfter(ip.getFromDate()) && !date.isAfter(ip.getDueDate()))
329:                .reduce((first, second) -> second).orElse(repaymentPeriod.getInterestPeriods().getFirst());
```

Two cases, and they are exhaustive:

1. **`s_p` came through the filter.** Then `date.isAfter(from_p)` **strictly**, and the clamp returns
   `date` unchanged (it is already inside `[from_p, due_p]`). So `ND = date > from_p`, which
   contradicts `ND == from_p`. No bend.
2. **`s_p` came through the `.orElse(getFirst())` fallback.** Then `p = 0`, and there is no `q < 0`
   for the duplicate to sit at. No bend.

**So the `:294` bend is unreachable, not merely harmless.** The simple property
`from_j >= due_i` holds unconditionally on every code-written list, with no exception clause, and
the strengthening to "no two *simultaneously non-empty* overlapping windows" was not needed.

**Why this is MINOR and not MAJOR.** T539 errs strictly on the conservative side: it admits a bend
that cannot occur and then shows the conclusion survives anyway. The landed axis-2 verdict is
unchanged and correct, and the stronger-sounding conclusion is still true (it is implied by the
simple one). The defect is that `repaymentperiod.go:530-536` asserts as fact — "The one corner where
even that weaker property bends is insertInterestPeriod's indexOf at
ProgressiveLoanInterestScheduleModel.java:294" — something the source does not reach. A comment that
tells a porter the invariant has a live exception, when it does not, costs the port a real
simplification.

**Condition:** whoever next owns this comment should either add the two-case selector argument above
and drop the exception, or restate the bend as *"algebraically admissible but unreachable, because
`findPreviousInterestPeriod` is from-exclusive"*. Do not simply delete the paragraph — the value-
equality hazard at `:294` is real for a Go port that reimplements `indexOf` by identity.

**Two further `indexOf` sites I checked while I was there**, neither of which changes anything:
`InterestPeriod.java:181-182` (`indexOf(this)` in `updateOutstandingLoanBalance`) is a read, not a
list mutation; `ProgressiveEMICalculator.java:666` (`indexOf(ip)` feeding the `subList(…).clear()` at
`:677-678`) could, on a mis-hit, clear *more* elements than intended — still deletion only, which
cannot create a pair.

---

## 4. The deserialisation caveat is applied to contiguity but not to the weaker property → **MINOR-C**

`repaymentperiod.go:490-507` names the Gson path — no ordering check, no validation, a list written
by a different code version restored unchecked — as the reason **contiguity** is not an invariant.
Then `:516-517` states the weaker property absolutely: *"no reachable path leaves two segments
`i < j` with `from_j < due_i`."*

**The same hole applies to the weaker property.** Everything I verified in §1 establishes that no
path *in this tree* creates such a pair; it does not establish that no such pair can be *loaded*
from `m_loan_progressive_model.json_model`. T539's handoff §1.2-E states this honestly ("P is not
*enforced* on this path; it holds only because the blob was written by a JVM in which the producer
paths above ran"), but that caveat does not survive into `doc.go`/`repaymentperiod.go`, which is
what a porter actually reads.

For the T533 vector decision this is immaterial — a foreign blob is not a capture path, and axis 2
stays latent. It matters for the port: the paragraph correctly forbids porting contiguity as an
invariant (binary search, assertion, deriving one boundary from its neighbour), and by the same
argument a Go port must not *assert* on the weaker property either.

**Condition:** carry the §1.2-E caveat into the code comment — one clause, e.g. *"on any list this
code wrote; the Gson path above is unchecked for this property too."*

---

## 5. MAJOR-2 — the axis-2 sentence, verified in both places ✔

**Wording.** `repaymentperiod.go:537-546` and `.softhouse/handoff/T534-t531-conditions.md` both now
name only **(i)** strict overlap `from_j < due_i` and **(ii)** two IDENTICAL non-empty `[from, due]`
ranges, with (ii) noted as the `from_j == from_i < due_i == due_j` instance of (i). Both state
explicitly that a **shared** boundary `from_j == due_i` does **not** produce a second match, that it
IS contiguity, that it is verbatim the retired example, and that it comes back green — and the same
for zero-length, gap and inverted segments. ✔

**Both places, not one.** `T534-t531-conditions.md` was corrected in **two** locations, not one: the
"One thing I derived beyond the brief" derivation *and* the "One note for whoever executes T533"
prescription (which carried the same defect). Each correction is marked with a visible
`CORRECTED BY T539 (2026-09-05)` block naming what was wrong rather than silently overwriting. That
is better than the instruction required.

**Residual check.**

```
$ git grep -n -i "duplicated bound\|overlapping or duplicated\|overlapping or repeated" \
      origin/softhouse/T539-t538-conditions -- .
```

Surviving hits are only: T539's own handoff (describing the fix), `.softhouse/reviews/t538-review-t534/REVIEW.md`
(a historical document, pre-existing on `main`, not T539's to edit), and `tasks.json` (where the
phrase appears inside the T533 correction that **repudiates** it). **Zero residual occurrences in
`doc.go`, `repaymentperiod.go` or `T534-t531-conditions.md`.** ✔

**T533's brief** (read from `origin/main:.softhouse/tasks.json`) names both (i) strict overlap
`from_j < due_i` and (ii) two identical non-empty ranges, and already carries the
"contiguity is not an invariant / `:1794` produces GAPS, never overlap" note. ✔ Correct, and
consistent with my independent GAP derivation in §2.

**T539 did not edit `tasks.json`.** ✔ Proven per-commit in §0.1, not inferred from the merge base.

---

## 6. MINOR-1 — the spot-check appositive ✔

I enumerated `doc.go`'s `InterestPeriod.java` citations myself, in **both** spellings:

```
$ grep -no "InterestPeriod\.java:[0-9]*\(-[0-9]*\)\?" doc.go
34:InterestPeriod.java:      <- the metavariable "[VERIFIED: InterestPeriod.java:a-b]", not a range
166:InterestPeriod.java:151   189:InterestPeriod.java:151
196:InterestPeriod.java:168-188   237:InterestPeriod.java:43-73   290:InterestPeriod.java:178
$ grep -n "(:[0-9]" doc.go        # bare form, inside RETIRED 1
248: … repaymentPeriod (:45) and mc (:68) — while balanceCorrectionAmount (:65)
249: … and outstandingLoanBalance (:66) carry none
```

**Eight distinct ranges, and the claim that these are all of them is correct.** All eight resolve at
`426a23544`, and each supports what it is cited for:

- `:151` — `case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount();` — **verbatim** the
  string `doc.go:188` quotes. ✔
- `:168-188` — `updateOutstandingLoanBalance()`, exactly that span, and `:174-176` / `:184-186` do
  add `balanceCorrectionAmount` alongside `disbursementAmount` and `capitalizedIncomePrincipal`,
  which is precisely the claim at `doc.go:194-196`. ✔
- `:43-73` — class declaration through `isPaused`. ✔
- `:45` `@JsonExclude` (on `repaymentPeriod`), `:68` `@JsonExclude` (on `mc`), `:65`
  `private Money balanceCorrectionAmount;` and `:66` `private Money outstandingLoanBalance;` —
  the latter two carry **no** annotation. Exactly what RETIRED 1 asserts. ✔
- `:178` — inside `updateOutstandingLoanBalance`. ✔

**Wording claims a spot check and no more**: *"It is still a spot check of the eight ranges these
arguments stand on, and it is NOT a sweep of interestperiod.go; do not cite it as one."* ✔

---

## 7. MINOR-2 — both counts, re-derived from the file, and they settle the disagreement ✔

```
$ wc -l InterestPeriod.java                                      -> 237
$ grep -o "InterestPeriod\.java:[0-9]*\(-[0-9]*\)\?" interestperiod.go | sort | uniq -c
```

**26 distinct ranges / 28 occurrences** (`:151` and `:178` each appear twice, both inside the file).

- **WHOLLY past EOF** (start > 237) — **TEN**: `:252-254`, `:256-259`, `:299-301`, `:303-305`,
  `:307-309`, `:311-313`, `:315-317`, `:319-321`, `:323-325`, `:327-329`.
- **OVERRUNNING** (start ≤ 237 < end) — **ONE**: `:237-250`.
- **Total citing at least one nonexistent line — ELEVEN.**
- `:203-219`, `:229-231`, `:233-235` all end at or before 237 and are inside; correctly excluded.

**My numbers are T539's numbers, to the range.** T538's brief said *"10 wholly past plus 11 that
overrun"*; there is exactly **one** overrunning range, so the brief was wrong and **T539 settled it
correctly**. `doc.go:35-42` now states both numbers separately, lists the ten by name, names
`:237-250` as the overrunning one, and tells the reader to quote whichever they mean. ✔

---

## 8. MINOR-3 — the hard-coded path ✔

`doc.go:14-21` no longer makes any checkout path the oracle's identity. It names the **commit** as
the identity, states that the path is not, names **both** known checkouts (`/home/user/fineract`
cloud, `/Users/buv/fineract` Mac), and instructs the reader to confirm
`git -C <checkout> rev-parse HEAD` prints `426a23544e…` first. **Correct for both fires.** The Mac
path survives only as one of two labelled environment paths, which is the right fix, not a residual.
✔

---

## 9. BEHAVIOUR — the byte-identity proof re-run, and it reproduces exactly ✔

I rebuilt the renderer from the handoff §10 source and ran it against both trees myself:

```
$ git archive $MB           nexus/internal/apps/loanproduct | tar -x -C base
$ git archive origin/softhouse/T539-t538-conditions nexus/internal/apps/loanproduct | tar -x -C head
$ ./rend base/nexus/internal/apps/loanproduct > base.txt
$ ./rend head/nexus/internal/apps/loanproduct > head.txt
BASE: files=14 lines=2621 bytes=78887
HEAD: files=14 lines=2621 bytes=78887
$ cmp base.txt head.txt   -> BYTE-IDENTICAL
$ sha256sum base.txt head.txt
49470856bf2b0d5481d13b97348844b435249231ad8cca45d0ffc549ef91d819  base.txt
49470856bf2b0d5481d13b97348844b435249231ad8cca45d0ffc549ef91d819  head.txt
```

**14 files, 2621 lines, 78,887 bytes, sha256 `49470856…` — every figure T539 claimed, reproduced
independently.** ✔

Because a comment-nilling renderer is blind to compiler **directives** hidden in comments, I added
two checks T539 did not run:

```
$ git diff $MB..<branch> -- '*.go' | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' \
      | sed -E 's/^[+-]//' | grep -vE '^\s*//' | grep -vE '^\s*$'
(empty — every changed line in the Go diff is a comment line)
$ grep -n "go:build\|go:generate\|+build" doc.go repaymentperiod.go
(empty — no directives in either changed file)
```

And the toolchain, run against the branch's files materialised into my own worktree and then
reverted:

```
gofmt -l ./internal/apps/loanproduct/   -> clean
go build ./...                          -> rc=0
go vet ./internal/apps/loanproduct/     -> rc=0
go test ./internal/apps/loanproduct/    -> ok  github.com/gerege/nexus/internal/apps/loanproduct  0.002s
```

**Zero executable change. No non-comment byte moved.** ✔

---

## 10. SCOPE — clean, and the one raised tension is judged CORRECT ✔

Forbidden-path check against the real (merge-base) diff:

```
$ git diff --name-only $MB..<branch> | grep -E "savings/|conformance\.sh|guards/ledgerguard/|\
tasks\.json|LOCK|RESUME\.md|program\.json|\.softhouse/vectors/|\.softhouse/capture/"
(empty)
```

Four files, all in scope: the two `loanproduct/` comment files, T539's own handoff, and
`T534-t531-conditions.md`. No vector moved. ✔

**On the `T534-t531-conditions.md` tension**, which T539 raised in its §3 rather than burying:
**I judge the call correct.** Its HARD CONSTRAINTS named `loanproduct/` plus its own handoff, but
MAJOR-2 explicitly instructed *"Fix the sentence AND the same wording in T534's handoff"*, T540's
brief pre-committed to checking that it had been done, and the file appears on no forbidden list.
The specific instruction governs the general constraint. Recording the conflict in the handoff so
the reviewer grades it, rather than leaving it to be discovered, is the behaviour this pipeline
wants; it is the reason I could grade it in one read.

---

## 11. The filed-not-fixed follow-up (T542) — T539's placement is CORRECT ✔

```
money.go:131:  // Reproduces a MathContext-qualified BigDecimal operation, e.g.
money.go:132:  // baseAmount.multiply(rateFactorTillPeriodDueDate, mc)
money.go:133:  // [VERIFIED: InterestPeriod.java:215].
```

At `426a23544`, `InterestPeriod.java:215` is `}` — the closing brace of `getDisbursementAmount()`.
The cited expression is `.multiply(getRateFactorTillPeriodDueDate(), getMc())` at
**`InterestPeriod.java:155`**, inside `getCalculatedDueInterest` (`:145-158`), with `baseAmount`
introduced at `:154`. **T539's `:155` is right**; a stricter citation for the whole expression would
be `:154-157`, which is a refinement for T542, not a correction.

`money.go` is **byte-identical** between merge base and branch (`cmp` — no output), so T539 filed the
defect rather than silently re-pointing the citation, exactly as it claims and as the rules require.
✔

---

## 12. Driver-owned residual found while verifying §5 → **MINOR-D** (not T539's)

`tasks.json` cites **`InterestPeriod.java:45-52`** for "public `@Setter` on **both** dates" in two
places — T533's corrected brief and T539's own brief. Read at the pin:

```
45:    @JsonExclude
46:    private final RepaymentPeriod repaymentPeriod;      <- final, NO setter
47:    @Setter
48:    @NotNull
49:    private LocalDate fromDate;
50:    @Setter
51:    @NotNull
52:    private LocalDate dueDate;
```

The span is off by two at the start: `:45-46` is the `final` `repaymentPeriod` field, which carries
no setter at all. **The correct span is `:47-52`** — which is exactly what T539 wrote into `doc.go`
and `T534-t531-conditions.md`. T539 silently used the right span while being forbidden to edit the
stale one; **credit to T539, and the residual belongs to the driver.**

Two smaller staleness items in the same brief, same routing: T533's case (c) still says *"T538
enumerated **18** construction/mutation sites"* (T539 re-derived **19** = 4 + 9 + 5 + 1, and I
reproduce 19), and its T534 correction block still contains the falsified
`t > from_j == due_(j-1) >= due_i` derivation, contradicted three paragraphs later by the T538
block. The layering is chronologically honest but a first-time reader meets the false form first.

**Condition (driver):** before T533 is unparked on a local fire, fix `:45-52` → `:47-52`, update 18
→ 19, and consider collapsing the three stacked corrections into one current statement. This brief
has now been corrected three times; each correction removed a way to file a green run as parity, and
a reader who stops early still meets the retracted text.

---

## 13. Findings summary

| # | Grade | Finding |
|---|---|---|
| MINOR-A | MINOR | Search-space closure rests on a `List<InterestPeriod>` type-name count (4, verified). The list is handed out live via `getInterestPeriods()` (64 non-test call sites), so the type name does not close the space. Re-closed by operation-level grep; **the enumeration survives intact**. §1.1 |
| MINOR-B | MINOR | The `:294` value-equality bend is **unreachable**, not merely harmless: `findPreviousInterestPeriod` (`PLISM:327-329`) is from-**exclusive**, so a filtered selection gives `ND > from_p`, and the `.orElse(getFirst())` fallback forces `p = 0` where no `q < p` exists. `repaymentperiod.go:530-536` asserts a live exception the source does not reach. Errs safe; costs the port a simplification. §3 |
| MINOR-C | MINOR | The Gson no-ordering-check caveat is applied to contiguity but not carried into the absolute statement of the weaker property at `repaymentperiod.go:516-517`. Honest in the handoff §1.2-E, absent from the code comment a porter reads. §4 |
| MINOR-D | MINOR | **Driver-owned.** `tasks.json` cites `InterestPeriod.java:45-52` for setters that are at `:47-52` (`:45-46` is the `final` `repaymentPeriod`), in both T533's and T539's briefs; plus "18 sites" (should be 19) and a retracted derivation left ahead of its own correction. §12 |

**Everything T539 was sent to do, it did, and every load-bearing figure reproduces:** the
enumeration is a derivation and not a restatement; the GAP answer is right and structurally
airtight; both of T539's upstream corrections to T538 (`APSTP:3592` missed, `9` not `13`) are
correct; MAJOR-2 landed in both places with no residual; MINOR-1's eight ranges are exhaustive and
all resolve; MINOR-2's 10 / 1 / 11 reproduces exactly and settles T538's wrong number; MINOR-3 is
correct for both fires; behaviour is provably unmoved to the byte; scope is clean; `tasks.json` was
not touched; and the T542 follow-up was filed with the right line number rather than fixed.

**VERDICT: ACCEPT WITH CONDITIONS.** Conditions are MINOR-B and MINOR-C on the next owner of the
`repaymentperiod.go` comment, and MINOR-D on the driver before T533 unparks. **Axis 2 stays LATENT;
it does not return to scope for T533.**
