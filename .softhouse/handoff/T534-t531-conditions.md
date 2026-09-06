# T534 — T531's four conditions on T530

**Branch:** `softhouse/T534-t531-conditions`
**Base:** `origin/main` @ `280da3bf` (T530 and T531 both merged).
**Pinned oracle:** `/home/user/fineract`, detached at `426a23544e8426a38ae43ae404670a0a7e85b9eb`
(read from `/home/user/fineract/.git/HEAD`, not assumed).
**Diff:** two files, comments only.

```
nexus/internal/apps/loanproduct/doc.go             | 25 +++++++++
nexus/internal/apps/loanproduct/repaymentperiod.go | 59 +++++++++++++++++++---
2 files changed, 76 insertions(+), 8 deletions(-)
```

**Push proof** — `git ls-remote --heads origin refs/heads/softhouse/T534-t531-conditions`:

```
78976182ba6d486aba06899ea43ae8b06bf917ee	refs/heads/softhouse/T534-t531-conditions
```

(`78976182` is the commit this handoff describes; the amend that inserted this proof line
re-pushed and is re-verified at the bottom of this file.)

---

## CONDITION 1 (MAJOR) — the worked example named an input that does not diverge

**Done.** The DIVERGENCE block on `FindInterestPeriod`
(`nexus/internal/apps/loanproduct/repaymentperiod.go`) now carries the input that actually
diverges, plus an explicit refusal of the one it used to name.

### What I re-derived, and how

I did not take the brief's spans on trust. Every span below was opened in the pinned checkout
and read.

1. `RepaymentPeriod.java:442-447` — `findInterestPeriod` filters with
   `isInPeriod(transactionDate, ip.getFromDate(), ip.getDueDate(), isFirstRepaymentPeriod() && ip.isFirstInterestPeriod())`
   and terminates `.reduce((one, two) -> two)`.
2. `LoanRepaymentScheduleProcessingWrapper.java:251-254` —
   `isFirstPeriod ? DateUtils.isDateInRangeInclusive(...) : DateUtils.isDateInRangeFromExclusiveToInclusive(...)`.
3. `DateUtils.java:415-417` — `isDateInRangeFromExclusiveToInclusive = fromDate != null && isAfter(target, from) && !isAfter(target, to)`.
   (`isDateInRangeInclusive` is at `:407-409`: `!isBefore(target, from) && !isAfter(target, to)`.)
4. `InterestPeriod.java:197-199` — `isFirstInterestPeriod()` is `this.equals(getRepaymentPeriod().getFirstInterestPeriod())`.
5. `ProgressiveLoanInterestScheduleModel.java:280-296` — `insertInterestPeriod` sets the
   predecessor's dueDate to `newDueDate` and then builds the successor with
   `InterestPeriod.withEmptyAmounts(repaymentPeriod, newDueDate, originalDueDate, isPaused)`.
   **This is the contiguity invariant** and it is what makes the old worked example wrong; it was
   not in T530's block, and I added it because without it the correction reads as an assertion.

So the oracle's window is `[from, due]` for the first segment of the first repayment period and
`(from, due]` for every other segment. The port is unconditionally `[from, due]` and returns the
first match.

### The case that diverges (now in the comment)

Non-first repayment period, contiguous segments `[F, D0]`, `[D0, D1]`, `transactionDate == F`
(the period's — and its first segment's — OWN FromDate):

- Oracle: nothing is first-of-first here, so every segment is from-exclusive.
  Segment 1 needs `F` after `F` → false. Segment 2 needs `F` after `D0` → false.
  **`Optional.empty()`**.
- Port: `!F.Before(F) && !F.After(D0)` → true. **Returns segment 1.**

Control that proves it is about the boundary and not about the date: the same `transactionDate`
in the FIRST repayment period, where segment 1 is first-of-first, the inclusive branch applies,
and both sides return segment 1.

### The case that does NOT diverge (now named as a trap in the comment)

`transactionDate == a later segment's from-date` — T530's example. By the contiguity invariant
(item 5) that date is `D0`, the preceding segment's due-date. Non-first period:

- Oracle: `[F, D0]` matches (`D0` after `F`, not after `D0`); `[D0, D1]` does NOT (`D0` is not
  after `D0`). Single match, so `.reduce((one,two)->two)` yields `[F, D0]`.
- Port: first match is `[F, D0]`.

**Identical.** A vector on this input comes back green and would have been filed as parity. T531's
MAJOR rating is correct; I reproduced the agreement rather than accepting it.

### One thing I derived beyond the brief — axis 2 is latent, and cannot be pinned by the boundary case

> **CORRECTED BY T539 (2026-09-05), per T538 review conditions 1 and 2.** The paragraph below
> originally stated contiguity as an *invariant* and named overlapping-or-repeated **boundary
> dates** as the shape that exposes axis 2. Both were wrong. Contiguity holds on the
> INSERTION path only — `fromDate`/`dueDate` carry public `@Setter`s
> (`InterestPeriod.java:47-52`), the list is handed out live (`RepaymentPeriod.java:54-56`),
> `ProgressiveEMICalculator.java:1791-1794` shrinks an interior `dueDate` with no truncation, and
> Gson rebuilds the list from `m_loan_progressive_model.json_model` with no ordering check
> (`InterestScheduleModelRepositoryWrapperImpl.java:95-100`;
> `ProgressiveLoanInterestScheduleModelParserServiceGsonImpl.java:66, :87`). And a boundary date
> that repeats across two adjacent segments IS contiguity — the retired green case, not a
> divergent one. The corrected text follows; the conclusion is unchanged and still holds.

The weaker property that actually holds is that **no reachable path leaves two segments `i < j`
with `from_j < due_i`** — every mutation outside `insertInterestPeriod` touches only the first
segment's `fromDate`, only the last segment's `dueDate`, or a segment whose successors are cleared
in the same block; `:1791-1794` only *shrinks* a `dueDate` (its segment was selected by
`findInterestPeriod`, so `targetDate <= due_i`), which opens a **gap**, never an overlap; deletions
only drop elements; and both copy constructors preserve dates and order. Given that,
**two segments can never match the oracle at once**: a match on segment *i* requires `t <= due_i`,
while a match on any later segment *j* requires `t > from_j >= due_i`. Contradiction. (The
first-of-first inclusive segment does not escape it either: a match there needs `t <= due_0`, and
any later match needs `t > from_j >= due_0`.)

So `.reduce((one, two) -> two)` is **indistinguishable from first-match on any segment list the
model actually builds**, and first-versus-last is observable ONLY on (i) two segments `i < j` in
**strict overlap**, `from_j < due_i`, or (ii) two segments carrying **identical non-empty
`[from, due]` ranges** — case (ii) being the `from_j == from_i < due_i == due_j` instance of
case (i). A **shared boundary** (`from_j == due_i`) does **not** produce a second match: that is
contiguity, it is the retired example, and it comes back green. Neither do zero-length segments,
gaps, or inverted segments. Both facts T531 told me to keep are kept and both are true of the
oracle's code — but a reader must not expect axis 2 to show up in the boundary vector. This is
recorded in the comment because it is the second way to build a green vector and misread it as
parity: the first was the wrong date, this would be the wrong axis. **T533 case (c) already asks
for it as its own case, which is the right shape.**

---

## CONDITION 2 — `interestperiod.go` marked UNSWEPT

**Done, in both required places.**

- **This handoff:** `nexus/internal/apps/loanproduct/interestperiod.go` is **UNSWEPT**. Its
  `[VERIFIED: InterestPeriod.java:a-b]` ranges have not been audited by T530, by T531, or by me.
  T530's measurement — 23 of 28 failing to resolve, 10 past EOF of a **237-line** file — stands as
  a lead. **T532 owns that file.** Nothing in T534 covered it.
- **Doc text:** `doc.go` opened with "Every behavioural claim carries a file:line citation to that
  tree; claims that do not carry an UNVERIFIED marker" — a package-level sentence a reader can
  easily take as "the citations here are sound." I added a
  `# Citation-audit status` section immediately under it: `repaymentperiod.go` SWEPT (T530,
  re-derived row by row by T531), `interestperiod.go` UNSWEPT with the count, the EOF fact, the
  T532 pointer and an explicit "do not apply an offset" (the drift changed sign and was
  non-monotonic on the swept file), every other file UNSWEPT and never claimed otherwise.

**What I deliberately did NOT do:** I did not put the marker inside `interestperiod.go` itself.
T532 is rewriting that file's comment blocks wholesale; a banner from me would collide with it for
no gain, and `doc.go` is where a reader forms the "the citations are audited" impression in the
first place. If the reviewer wants it in-file as well, it is a one-hunk addition — say so and it
goes in.

**One honesty repair inside my own edit.** My first draft of that section closed with "the two
arguments below rest only on ranges from the swept file." **That was false** — the RETIRED-1 and
RETIRED-2 arguments cite `InterestPeriod.java` heavily. So I opened the six ranges those
arguments actually stand on and read them:

| doc.go cites | pinned source | verdict |
|---|---|---|
| `InterestPeriod.java:43-73` | class decl + field block | resolves |
| `:45` | `@JsonExclude` above `repaymentPeriod` (field itself at `:46`) | resolves — the annotation is what the sentence cites |
| `:65` | `private Money balanceCorrectionAmount;` | resolves |
| `:66` | `private Money outstandingLoanBalance;` | resolves |
| `:68` | the second `@JsonExclude`, above `mc` at `:70` | resolves |
| `:178` | `.plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc())` | resolves |

The section now states exactly that: a spot check of the six ranges those arguments stand on,
explicitly **not** a sweep of `interestperiod.go`, with "do not cite it as one" in the text. This
is the same failure mode as Condition 1 — a true-sounding sentence that would let an unswept
remainder look accounted for — so I would rather report catching it in my own draft than leave it.

---

## CONDITION 3 — two accuracy corrections

**(a) `InterestPeriod.java` is 237 lines, not 238.** Measured two ways in the pinned checkout:
`wc -l` = 237 and `awk END{NR}` = 237 (they agree, so the file ends with a newline and neither
count is a trailing-newline artefact); line 237 is the closing `}`. **Confirmed, third independent
measurement** after the driver's and T531's.

The two "238" occurrences are in `.softhouse/handoff/T530-t529-conditions.md:245` and `:251`.
**I did not edit that file** — my scope guard is `nexus/internal/apps/loanproduct/` and this
handoff only, and T530's handoff is neither. The correction is recorded here, and the live doc
text I *am* allowed to write (`doc.go`) says **237**. If the driver wants T530's handoff amended
in place, that is a one-line fix for whoever owns it.

**(b) "zero executable statements changed" — restated precisely, not dropped.**

The claim's conclusion is TRUE. Its phrasing was loose. Precisely:

> T530 changed exactly one non-comment byte range in the package: the string literal
> `"...oracle leaves it stale (RepaymentPeriod.java:173-197)."` → `":173-198)."`, inside the
> **failure-message format string of a `t.Fatalf`** in `interestperiod_test.go` (the
> `got != wantAfterFirstSweep` branch). That string is evaluated only when the assertion has
> already failed, and its text is compared to nothing. **No vector, no assertion and no computed
> value can move.** So "zero executable statements changed" is wrong as literal English — a string
> literal inside a call expression is part of an executable statement — while **"no observable
> behaviour changed" is exactly right**, and it is the claim that matters.

Verified independently for T534's own diff, same standard: see the AST proof below.

---

## CONDITION 4 — T533's brief

**Verified, not duplicated.** I read T533 in `.softhouse/tasks.json`. It has already been
corrected by the driver and now names the right input. Specifically it carries:

- a `*** THIS BRIEF WAS CORRECTED BY THE DRIVER AFTER T531 ***` banner;
- both source spans (`LoanRepaymentScheduleProcessingWrapper.java:251-254`,
  `DateUtils.java:415-417`);
- a **"WHERE IT DOES *NOT* DIVERGE"** paragraph retiring the later-segment's-from-date case with
  the reason (same segment on both sides; "comes back GREEN"), tagged `[T531 F-MAJOR]`;
- **"WHERE IT DIVERGES — capture THIS"** with case **(a) `transactionDate == the period's OWN
  FromDate` in a NON-FIRST period → oracle `Optional.empty()`, port the first segment**, marked
  "THE CASE"; plus (b) the first-of-first control and (c) a multi-match case pinning first-vs-last
  independently.

That is the correct spec. **I did not edit `tasks.json`** — the orchestrator owns it.

One note for whoever executes T533, from the derivation above — **corrected by T539 per T538
review condition 1; the original wording named overlapping-or-repeated boundary dates, and a
boundary date repeated across two adjacent segments IS contiguity, i.e. the retired green
case**: case (c) needs a segment list
carrying either (i) two segments `i < j` in **strict overlap**, `from_j < due_i`, or (ii) two
segments with **identical non-empty `[from, due]` ranges**. Nothing else works, because no other
shape can produce two simultaneous oracle matches — a **shared** boundary (`from_j == due_i`),
a zero-length segment, a gap and an inverted segment each yield at most one match. Constructing
(c) out of an ordinary contiguous schedule will produce a single-match input and another
green-and-meaningless vector.

---

## What I did not do

- **No executable line changed.** Comments only, as instructed. Nothing in the port's behaviour
  was repaired — `FindInterestPeriod` still diverges from the oracle exactly as before, by design:
  no Go change lands before T533's vectors exist (CLAUDE.md — no ported context is correct until
  its vectors match).
- Did not touch `nexus/internal/apps/savings/`, `.softhouse/conformance.sh`,
  `.softhouse/guards/ledgerguard/`, or `.softhouse/tasks.json`. `git status --porcelain` shows
  exactly two modified files, both under `nexus/internal/apps/loanproduct/`.
- Did not sweep `interestperiod.go` (T532's file) — beyond the six-range spot check disclosed
  above, which is labelled as a spot check in the doc text itself.
- Did not edit `.softhouse/handoff/T530-t529-conditions.md` (out of scope; correction recorded
  here instead).

---

## Verification

From `nexus/`:

| check | result |
|---|---|
| `go build ./...` | clean |
| `go vet ./...` | clean |
| `gofmt -l .` | 4 pre-existing hits — `loanschedule/contract/contract.go`, `parties/client.go`, `parties/group.go`, `parties/legalform.go`. **Zero in `loanproduct/`**, and none of the four is touched by this branch. |
| `go test ./internal/apps/loanproduct/...` | `ok github.com/gerege/nexus/internal/apps/loanproduct 0.003s` |

**AST-level proof that behaviour did not move** (T531's standard). I built a small `go/parser` +
`go/printer` tool that renders every `*.go` file in a directory with **all comments stripped** —
`File.Comments`, `File.Doc`, and the `Doc`/`Comment` fields on every `FuncDecl`, `GenDecl`,
`Field`, `ValueSpec`, `TypeSpec` and `ImportSpec` — then compared that rendering for
`origin/main` (extracted via `git archive`) against this branch:

```
2621 base.ast
2621 head.ast
diff base.ast head.ast  ->  no output
AST IDENTICAL - no executable statement changed
```

All 14 files in the package, byte-identical once comments are removed. This is a stronger claim
than T530 made about its own diff (see Condition 3b): here there is genuinely **no** non-comment
byte changed, string literals included.

Tool kept out of the repo, in the session scratchpad.

---

## Note on the red bar

The repo-wide bar is red for an unrelated guard repair that is not on `main`, and
`ready-tasks.py` exits 5 by design until the five unpushed branches are published. Neither is
caused by this branch and I did not touch either. This branch **is** pushed — proof at the top.

**On the hashes in this file.** The branch was pushed three times: the work commit, an amend that
inserted the `ls-remote` proof into this file, and an amend that added this paragraph. Each amend
necessarily changes the hash of the commit that *contains* the proof of its own hash, so the
hashes quoted above are the earlier ones. The single authoritative check, which the reviewer
should run rather than trust a hash typed inside the artefact it names:

```
$ git ls-remote --heads origin refs/heads/softhouse/T534-t531-conditions
```

It returned a hash on every one of the three pushes; the branch exists on `origin` and its current
head is the commit to review. The tree contents are identical across all three — only this
paragraph and the proof block differ.
