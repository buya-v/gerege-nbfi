# T63 — independent adversarial review of T59 (interest-chain memo + cancellation)

Reviewer task: T63. Branch: `softhouse/T63-review-memo-and-cancellation`.
Target: `nexus/internal/apps/loanschedule/{emi.go, generator.go, liveness_test.go, loanschedule_test.go}` as merged by T59 (`d12ef0a`, merged `bb3c898`).

---

## VERDICT: ACCEPTED WITH REQUIRED CHANGES

**P0: 0. P1: 2. P2: 4.**

**The memo is sound and the cancellation is correct. I attacked both hard and
could not break either**, and I say so plainly below alongside everything I
tried — that is the main result of this review. Not one money value is at risk,
no contract clause is violated, conformance is 29/29 and `--prove` is 20/20 on
my own runs.

The two required changes are both about **claims that are wider than what
supports them**, which is the failure mode this program has already declared a
defect twice (T60's silent false green; pattern P-7):

- **P1-1 (F-2)** — `TestGenerationCostIsNotQuadraticInTheTerm` passes on a
  generation that **is** quadratic in the term. `generate` calls
  `installmentNumberOf` once per row and that function rescans every row already
  emitted (`generator.go:459`, `:478-486`): a Θ(n²) that **allocates nothing**,
  and the test asserts a ratio of **allocation counts**. Measured at 4.05–4.22x
  per 2x term. Required: fix the scan (≈3 lines, given below) or narrow the
  test's name and doc to the property it actually grades.
- **P1-2 (F-1)** — the memo's stated soundness rule ("step *i* is a function of
  periods 0..*i* and of nothing later") is **false of the reference oracle**,
  where later periods write onto earlier ones in four places. The code is right;
  the rule that makes it right is a *write-ordering* rule, and it is not the one
  written down. Required: restate it, because the next contributor will check a
  new write site against the sentence in the file.

Neither required change touches money arithmetic and neither should re-open the
vector corpus.

---

## STEP 0 — base

My worktree was cut at `67bee40 softhouse: local fire lock (20260820-080002)`,
which is an **ancestor of `main` and does NOT contain T59**. `liveness_test.go`
was absent. Per pattern P-5 I re-cut onto `main`:

```
git checkout -B softhouse/T63-review-memo-and-cancellation main
-> bb3c898 merge T59: honour cancellation inside the loops; restore the oracle's memo
```

Base now contains the merged T59 work (`emi.go` with the memo, `liveness_test.go`)
and the merged T60 work (`conformance/invariants.go` with placeholder reporting,
`4895e07`). **Stated as required: my base was stale and I rebased.**

## Verification I ran, and the exit codes I observed

| command | observed |
|---|---|
| `cd nexus && go build ./...` | **exit 0** |
| `cd nexus && go test ./...` | **exit 0** — `ok loanschedule 2.570s`, `ok conformance 1.749s` |
| `.softhouse/conformance.sh` | **exit 0** — 29 parity PASS / 0 FAIL, 4 contract-refusal PASS, 2354 cells, 0 invariant violations |
| `.softhouse/conformance.sh --prove` | **exit 0** — `PROOFS: 20 passed, 0 failed` |
| `gofmt -l nexus/` | **exactly** `nexus/internal/apps/loanschedule/contract/contract.go` — the EXPECTED state, gate G-3 |

Non-negotiables graded and clean:

- **No floating point on any money path.** `grep -nE '\bfloat(32|64)\b|math\.(Floor|Ceil|Round|Pow|Abs|Log)|ParseFloat|%f'` over `emi.go`, `generator.go`, `rounding.go`, `liveness_test.go`, `loanschedule_test.go` returns **nothing**. Every money quantity is `int64` minor units; every non-money intermediate is `*big.Rat` with an explicit `roundSignificant`/`roundScale`. `shouldBeAdjusted` (`emi.go:938-947`) reproduces the reference oracle's `double` threshold in exact `big.Int` and says so — correct, and the right call.
- **`contract.go` untouched.** `git show d12ef0a --stat` lists five files, none of them `contract.go`. Verified independently: no DEC-n amended.
- No US payment rail, no Stripe/Plaid/Lithic/Persona, no MySQL/MariaDB/Oracle driver, no `first_name`/`last_name` (the only hits in the package are `contract.go:141-142` *prohibiting* them).

---

# FINDINGS

## F-1 (P1-2) — the memo's soundness argument is stated as a property that is FALSE of the reference oracle. The code is right; the justification is not.

**Where.** `emi.go:176-184` (the `chainStep` doc) and `emi.go:505-511`
(`interestChainUpTo`'s doc), both saying:

> step *i* is a function of periods 0..i only — no quantity of a later period
> appears anywhere in the fold — so a write to period *j* leaves every step
> before *j* intact

and T59's handoff repeating it as "sound because step i is a function of periods
0..i and of nothing later."

**Re-derivation from source.** Read as a claim about *the fold*, that sentence is
true, and I verified it line by line: `interestChainUpTo` (`emi.go:513-553`) reads,
for period *i*, only `p.segments[*].{from, due, outstandingMinor, rateFactorTillDue}`,
`p.due`, `p.emiMinor`, and the `carried` scalar from step *i-1*. Nothing else.

Read as a claim about *the schedule computation*, it is **false**, and the
reference oracle is where it fails. Later periods influence earlier ones in at
least four places:

- `ProgressiveEMICalculator.java:1725-1739` — the annuity fold. `rateFactorN` is
  a product over the rate factors of **every** related period and `fnResult` a
  fold over the same list (`:1816-1828`); the single resulting installment is
  then written onto the **first** related period.
- `ProgressiveEMICalculator.java:1258-1309` — the EMI re-adjust smoothing loop.
  `getEmiAdjustment` (`:1778-1789`) scans **from the end** and takes
  `lastPeriod.getEmi().minus(penultimatePeriod.getEmi())`; the resulting uniform
  installment is stamped at `:1283-1284` / `:1303-1304` onto **every** related
  period, starting at the earliest. A tail rounding residual is smeared
  backwards over the whole window.
- `ProgressiveEMICalculator.java:1160-1219` — the residual. `diff` (`:1202-1203`)
  is a whole-schedule aggregate, and `:1165-1174` writes `emi` on **any** period
  whose outstanding principal exceeds a whole-schedule total.
- `ProgressiveEMICalculator.java:1243-1251` + `:1805-1814` — `futureUnrecognizedInterest`
  on period *i* is literally assigned the `unrecognizedInterest` of a period at
  index **> i** (the `dueDate().isAfter(...)` filter enforces it), and that field
  then feeds `getCalculatedDueInterest` (`RepaymentPeriod.java:260`).

The port reproduces the first three faithfully (`calculateLevelInstallment`
`emi.go:782-816`, `adjustEMIIfNeeded` `emi.go:958-1027`, `applyFinalPeriodResidual`
`emi.go:824-880`). **So the memo lives in a computation that does have backward
data flow.**

**Why the memo is nonetheless sound — the real rule.** The memo does not cache
*the derivation of* period *i*'s state. It caches a pure function of the model's
**current stored fields** for periods 0..*i*. Every later→earlier influence,
in the Java and in the port alike, is realised as a **write to a stored field of
an earlier period** — `setEmi` there, `p.emiMinor = …` here. The correct
soundness condition is therefore not

> no backward dependency exists  *(false)*

but

> **every write to a stored field that the fold reads for period *j* is preceded
> by `invalidateFrom(j)`**  *(true — enumerated exhaustively in §"Write sites")*

which is exactly what the reference oracle's own `Memo` does by a different
mechanism: it re-hashes its declared dependencies on every `get()`
(`Memo.java:43-53`) and recomputes when they move, with **no** invalidation ever
pushed to a neighbour. Index invalidation is the push-form of the same rule.

**Severity P1 (documentation only).** No behaviour is wrong. But the sentence as written is
the rule a future contributor will check a new write site against, and it does
not mention the thing that actually matters (the write ordering). One of this
program's two dead folklores died because three parties agreed on a true-sounding
sentence.

**Minimal correction** (documentation only, `emi.go:176-184`): replace "step *i*
is a function of periods 0..*i* only — no quantity of a later period appears
anywhere in the fold" with the two-part statement — *(a)* the fold reads only
the stored fields listed above, of periods 0..*i*; *(b)* therefore the memo is
sound **iff** every write to one of those fields on period *j* is preceded by
`invalidateFrom(j)`, and note that later periods DO influence earlier ones
(`ProgressiveEMICalculator.java:1258-1309`, `:1725-1739`, `:1202-1203`) — they
just do it by writing, which (b) covers.

## F-2 (P1-1) — `installmentNumberOf` is a non-allocating Θ(n²), and T59's cost regression test is structurally incapable of seeing it.

**Where.** `generator.go:459` calls `installmentNumberOf(periods)` once per
emitted row; `generator.go:478-486` scans **every row already emitted**. Total
Θ(n²) comparisons, **zero allocations**.

**Provenance.** Pre-existing — `git log -S installmentNumberOf` gives `91fcee2`
(T10). T59 did not introduce it and did not claim to have removed it.

**Reproduction — measured, T63F:**

| rows | time in `installmentNumberOf` alone | growth over a 2x term |
|---|---|---|
| 1,000 | 2.217 ms | — |
| 2,000 | 9.359 ms | **4.22x** |
| 4,000 | 38.817 ms | **4.15x** |
| 8,000 | 157.088 ms | **4.05x** |

Textbook quadratic (linear would be 2x). Extrapolated to the term T59's own
liveness test uses — n = 50,000 — that is **≈ 6.1 s of pure scanning**, in a
function T59's commit message describes as reduced to "growth over a 4x term
22.81x -> 4.19x".

**Why the regression test cannot see it.**
`TestGenerationCostIsNotQuadraticInTheTerm` (`liveness_test.go:184-232`) asserts
a ratio of `runtime.MemStats.Mallocs`. `installmentNumberOf` allocates nothing,
so its contribution to that ratio is **exactly zero at every n**. The secondary
5 s wall-clock cap is taken at n=360, where this costs ~0.3 ms. The test is
therefore green on an implementation that is quadratic, which is precisely the
implementation class it exists to reject.

**Honest qualification on when it bites.** At the corpus's terms this costs
nothing, and at the terms T59 benchmarked (n ≤ 720) it is still a rounding
error: the linear part of generation is ~50 µs/period (T63I, 21.6%), so the
quadratic term only becomes the *majority* of the cost somewhere around
n ≈ 25,000. That is not a reason to shrug — it is the term **T59's own
cancellation test uses**. `TestCancellationIsHonouredDuringGeneration`
(`liveness_test.go:74`) picks `term = 50000` on the stated reasoning that "at the
cost measured after the T59 fix a 50,000-period schedule takes seconds", and at
that term most of those seconds are this scan, not the arithmetic the memo
bounds.

To be fair to T59: the substitution of allocation counts for wall clock was
argued carefully and the flakiness measurement behind it is real and correct.
The defect is not the substitution, it is that the doc comment claims the proxy
is "a faithful one: nearly every allocation in a generation is a `big.Rat`
produced by a step of the interest chain, which is precisely the quantity the
memo bounds" — true, and precisely why it is blind to any cost that is *not*
the interest chain.

**Minimal fix** (not applied — review scope): carry the counter as a local in
`generate`, incremented when a payable row is appended, instead of rescanning.
`installmentNumberOf`'s return is a pure function of the number of payable rows
already emitted, so the values are identical:

```go
// in generate(), before the loop
var payable int32
// replace  InstallmentNumber: installmentNumberOf(periods),
//   with   InstallmentNumber: payable + 1,
// and increment payable immediately after each disbursement/down-payment/repayment
// row is appended, matching installmentNumberOf's own Kind predicate.
```

Recommend pairing it with a wall-clock cost assertion at a term where a
non-allocating quadratic is visible (n ≥ 4,000), or the same blind spot returns.

## F-3 (P2-1) — the `ctxCheckStride` doc overstates what the stride bounds.

**Where.** `emi.go:131-139`:

> At this port's measured per-period cost the 256-period stride bounds the tail
> latency of a cancelled call to a few milliseconds

**Re-derivation.** The stride bounds the number of **periods** between two
context reads. It does not bound the **work**, because two stretches do
per-period work that itself grows with n:

1. `generate`'s emitting loop (`generator.go:435-466`) does 256 rows between two
   `checkCancel` calls, and each row costs O(k) in `installmentNumberOf` (F-2) —
   so one stride costs O(256·n), not O(256).
2. `adjustEMIIfNeeded` (`emi.go:958-1027`) contains three **fully uncancellable**
   O(n) stretches: `deepCopy` (`emi.go:212-241`, which also allocates two
   objects per period), the trial write loop (`emi.go:986-991`), and the
   `trialRelated` build plus adopt loop (`emi.go:1005-1021`). `emiAdjustment`
   (`emi.go:910`) and `relatedPeriods` (`emi.go:294`) are two more.

So the tail after cancellation is **O(n)**, not O(stride).

**This is a documentation defect, not a liveness bug**, and the reason matters:
`checkCancel` (`emi.go:152-163`) tests the sticky `m.cancelled` flag **first**,
before the stride mask, so once the flag is set every subsequent check
short-circuits regardless of index and the unwinding is immediate. The
uncancellable stretches are each entered at most once after the flag is set,
because `adjustEMIIfNeeded` re-checks at the head of every outer iteration
(`emi.go:965`) and after the trial (`emi.go:995`). The bound is O(n), which is
still bounded, still monotone in a caller-controlled input, and still not "a few
milliseconds".

**Minimal correction:** say what is true — the stride bounds *periods* between
reads; the tail latency is O(n) because of the uncancellable stretches named
above; on the graded corpus (≤ 36 periods) both are one pass and the cadence is
invisible.

## F-4 (P2-2) — the `applyFinalPeriodResidual` cost cliff is reachable at much shorter terms than the handoff records, by raising the RATE rather than the term.

T59's handoff records this honestly as backlog item 2, at n ≈ 1100 on
near-interest-only shapes, and **refused to touch it unvectored — which was the
right call.** This finding does not contradict T59; it re-prices the backlog item.

**Reproduction — measured, T63I** (min of 3, principal MNT 50,000,000, disbursed
on the schedule start, all inside the graded domain):

| annual rate | n=32 | n=64 | n=128 | n=256 | growth 128→256 |
|---|---|---|---|---|---|
| 21.6% (the rate T59 benchmarked) | 3.54 ms | 6.74 ms | 15.74 ms | 12.63 ms | **0.80x** |
| 200% | 3.71 ms | 8.25 ms | 16.70 ms | 135.07 ms | **8.08x** |
| 500% | 4.20 ms | 8.13 ms | 29.84 ms | 169.81 ms | **5.69x** |

Linear over a 2x term is 2x. The 21.6% column is linear; 200% and 500% are worse
than quadratic in a single step. **The cliff is reachable at n=256, not only at
n≈1100** — T59's benchmark and its regression test both sample exactly one rate,
so neither would ever see it. A stack sample taken during a timed-out run
confirms the mechanism is the one T59 named: `applyFinalPeriodResidual`
self-recursion (`emi.go:879`) observed at depth 11 from inside
`adjustEMIIfNeeded`'s trial (`emi.go:994`) on a 254-related-period model.

Money is unaffected at these shapes — T63B2 confirms principal sums to exactly
the disbursed amount and the final balance is 0 at n ∈ {60,120,254,256,258} at
both 200% and 500%.

**Backlog amendment recommended:** T59's backlog item 3 asks for a *long-term*
capture. It should ask for a **long-term OR high-rate** capture — the shape is
"many rows amortize zero principal", and rate reaches it at a quarter of the term.

## F-5 (P2-3) — `memoiseInterestChain` is a mutable package-level global in production code.

**Where.** `emi.go:187-190`. Its comment ("written only by this package's own
differential test; it is not configuration, and no caller, request field or
deployment can reach it") is a **discipline claim, not an enforcement**. Nothing
in the type system or the build stops a later writer, and it puts hidden
process-global state behind a `Generator` whose own doc says it "holds no state,
so the zero value is usable and every call is independent" (`generator.go:53-55`).

**Today it is benign and I verified that:** `grep -rn 't.Parallel' ` over the
package returns nothing, so no data race exists and no test can observe another
test's flip.

**Minimal fix if wanted:** make it a field on `scheduleModel`, defaulted true by
`newScheduleModel` and overridden only through a test-only constructor; or gate
the off-path behind a `//go:build` tag. Not applied.

---

# THE WRITE-SITE ENUMERATION — performed mechanically, not taken from T59

T59's handoff lists **six** sites. The correct count of `invalidateFrom` **call
sites** is **nine**; the six in the handoff are six *functions*, which is a fair
summary but not the thing to check exhaustiveness against.

I did not count T59's calls. I enumerated the **writes** first and then checked
each one had a guard. Method: every field assignment in the package's non-test
code, mechanically:

```
grep -nE "^\s*[A-Za-z_][A-Za-z0-9_.\[\]]*\.[a-zA-Z][A-Za-z0-9_]* *(=|\+=|-=|\*=)[^=]" *.go
```

The fold reads, for period *i*: `p.segments` (the slice itself), each segment's
`from`, `due`, `outstandingMinor`, `rateFactorTillDue`; the period's `due` and
`emiMinor`; plus model-level constants. That is the complete dependency set —
derived by reading `interestChainUpTo` (`emi.go:513-553`) and
`segmentCalculatedInterest` (`emi.go:480-490`), not from the doc comment.

| # | write | file:line | field | guard | ordering |
|---|---|---|---|---|---|
| 1 | `last.disbursedMinor +=` | `emi.go:357` | disbursed (feeds outstanding) | `invalidateFrom(owner.idx)` `emi.go:348` | guard BEFORE write ✓ |
| 2 | `s.disbursedMinor +=` | `emi.go:365` | " | same, `emi.go:348` | ✓ |
| 3 | `prev.due = newDue` | `emi.go:398` | **segment due — a direct fold input** | same, `emi.go:348` | ✓ |
| 4 | `prev.disbursedMinor +=` | `emi.go:399` | disbursed | same, `emi.go:348` | ✓ |
| 5 | `owner.segments = …` | `emi.go:403` | **the segment slice itself** | same, `emi.go:348` | ✓ |
| 6 | `s.outstandingMinor =` | `emi.go:462` | **direct fold input** | `invalidateFrom(i)` `emi.go:461` | read of `duePrincipalMinor(prev)` hoisted ABOVE the guard, `emi.go:459` — correct and load-bearing ✓ |
| 7 | `s.outstandingMinor =` | `emi.go:468` | " | `invalidateFrom(i)` `emi.go:466` | ✓ |
| 8 | `s.rateFactor =` | `emi.go:625` | (not a fold input) | `invalidateFrom(p.idx)` `emi.go:623` | ✓ |
| 9 | `s.rateFactorTillDue =` | `emi.go:626` | **direct fold input** | same, `emi.go:623` | ✓ |
| 10 | `p.emiMinor = emi` | `emi.go:813` | **direct fold input** | `invalidateFrom(related[0].idx)` `emi.go:810` | reads (`initialBalanceMinor`, `growthFactor`) all precede the guard ✓; `related` is built by an in-order scan (`emi.go:294-302`) so `related[0].idx` is its minimum ✓ |
| 11 | `p.emiMinor -=` | `emi.go:852` | " | `invalidateFrom(i)` `emi.go:851` | read of `duePrincipalMinor(p)` at `:849` precedes ✓ |
| 12 | `p.emiMinor = 0` | `emi.go:854` | " | same | ✓ |
| 13 | `m.periods[idx].emiMinor +=` | `emi.go:876` | " | `invalidateFrom(idx)` `emi.go:875` | all three aggregates read at `:864-873`, before the guard ✓ |
| 14 | `m.periods[idx].emiMinor = 0` | `emi.go:878` | " | same | ✓ |
| 15 | `p.emiMinor = adjusted` | `emi.go:990` | " (on the **trial**) | `trial.invalidateFrom(p.idx)` `emi.go:989` | per-period guard immediately before each write — order-independent ✓ |
| 16 | `p.emiMinor = trialRelated[i].emiMinor` | `emi.go:1019` | " | `m.invalidateFrom(p.idx)` `emi.go:1018` | ✓ |
| 17 | `p.idx = i` | `generator.go:521` | construction only | n/a — before `m.chain` exists (`generator.go:525`) | ✓ |
| 18 | `q.segments = append(…)`, `out.periods = append(…)` | `emi.go:230,232` | construction of the **copy**, whose memo starts empty (`emi.go:223`) | n/a | ✓ |

**A seventh (or nineteenth) unguarded write site does not exist.** The grep above
is the complete set of field assignments in `emi.go` + `generator.go`
non-test code; every entry is in this table. There is no write to a fold input
that is not preceded by an `invalidateFrom` at an index ≤ the written period.

**Ordering — the specific question asked.** No, a read of `chainStep` cannot
occur between a mutation and its `invalidateFrom`: in all nine sites the
`invalidateFrom` textually and dynamically precedes the write, with no
intervening call. The two places where a *read* deliberately precedes the guard
(`emi.go:459` and `emi.go:801-808`) are the load-bearing ones and are both
correct — the value read is of a period strictly *before* the invalidation
point, so the prefix the read paid for is exactly the prefix the write leaves
intact. `chainValid` is never left true across a mutation: `invalidateFrom`
(`emi.go:193-196`) lowers it monotonically and no code ever raises it except
`interestChainUpTo` (`emi.go:550`) immediately after storing the entry it
describes.

---

# CANCELLATION — traced, not assumed

**Can a cancelled generation return a partial but non-empty schedule, or a nil
error with a truncated row list?** **No**, and the guard is where the author
says it is, but the proof runs through three facts and not one:

1. The only `break` in `generate`'s emitting loop (`generator.go:436-438`) is on
   `model.checkCancel(i)`, and `checkCancel` **sets the sticky flag before
   returning true** (`emi.go:159-161`). So `break ⟹ cancelled`.
2. `generate` consults `model.cancelled` **after** the loop
   (`generator.go:467-470`) and returns `contract.Schedule{}` — the zero value,
   `Periods == nil` — with `ctx.Err()`.
3. The flag is never cleared. `grep` finds `cancelled = true` at `emi.go:160` and
   `emi.go:996` and **no** assignment of `false` anywhere; `deepCopy`
   (`emi.go:219`) copies it, and `adjustEMIIfNeeded` propagates the trial's flag
   back to the live model (`emi.go:995-998`) so a cancellation noticed only
   inside a discarded copy still aborts the real one.

**The path I expected to find a hole in, and did not.** `newScheduleModel`
(`generator.go:508-527`) can be cancelled **mid-construction**, returning a model
with a *truncated* `m.periods` and a **nil** `m.chain` (the `make` at
`generator.go:525` is after the loop). `interestChainUpTo` indexes `m.chain[…]`
unguarded. That is a panic if it is ever reached. It is not reachable:
`m.cancelled` is true, `m.chainValid` is 0 so the `last < m.chainValid` read at
`emi.go:517` is dead, and the fold's first `checkCancel` (`emi.go:531`)
short-circuits on the sticky flag before any `m.chain[i]` store. Correct, but
correct by a two-step argument that no comment states.

**Garbage state does escape into the model — and it cannot escape the function.**
When `interestChainUpTo` bails mid-fold it returns a meaningless pair
(`emi.go:531-536`), and `updateOutstandingBalances` will write that meaningless
value into `s.outstandingMinor` at `emi.go:462` before its own outer check fires.
The memo stays truthful (only completed steps are stored, `emi.go:548-551`), the
model is discarded, and `generate` returns the zero `Schedule`. The comment at
`emi.go:532-534` states this. Verified, no leak.

**The stride, on a 50,000-period request.** See F-3: bounded, but O(n), not
O(stride).

**Empirical:** `TestT63H_NoPartialScheduleEverEscapes` fires a deadline at 292
offsets across the window in which an n=3,000 generation is running and asserts
`err != nil ⟺ Periods == nil`, and that every completed run is cell-for-cell
equal to the uncancelled schedule.

---

# WHAT I ATTACKED AND COULD NOT BREAK

Stated plainly, because a failed attack is a result: **five independent attacks,
none exposed a defect in the memo.**

### 1. Differential over the disbursement-date axis T59 never sampled — 34,512 shapes, 0 divergences

T59's `TestInterestChainMemoIsObservationallyInert` sweeps 192 shapes with the
disbursement on **either the schedule start or `due[0]`**. Neither of those is
the interesting one:

- on the schedule start, `insertSegment` produces a **zero-length** leading
  segment;
- on `due[0]`, `registerBalanceChange` takes the "segment already ends on this
  date" fast path (`emi.go:361-367`) and **never splits at all**.

So T59's sweep never once split a segment strictly inside a period other than the
first — which is the only in-graded-domain shape that gives one repayment period
two segments carrying **different** `rateFactorTillDue` values plus a **moved**
segment due date, i.e. three fold inputs rewritten under one `invalidateFrom`.
The ratified contract calls that shape out by name (`contract.go:2224-2226`: "the
STRICTLY-INSIDE-A-PERIOD SEGMENTATION (row 3), the only in-graded-domain shape
that gives one repayment period two interest periods").

`TestT63A_DisbursementOnEveryDayOfTheTerm` places the disbursement on **every
single day** of the term, across 4 schedule starts (incl. the 31st, a 28-Feb, a
30-Nov), 3 rates (0%, 7%, 500%) and 4 principals (1 minor unit to MNT
50,000,000), terms {3,7,13}:

```
T63A: 34512 shapes (33396 answered, 1116 refused) compared memo-on vs memo-off
      cell for cell
--- PASS (237.04s)
```

**Zero divergences.** Refusals agreed on both sides.

### 2. Terms across the 256 stride boundary — `TestT63B`

Terms {1,2,3,4,5,8,17,35,36,37,60,120,254,255,256,257,258,300} × 2 rates × 2
principals × 2 starts × 2 disbursement offsets. The memo-off reference is
quadratic *by construction*, which is what caps the term here.

### 3. Reachability instrumentation — is the attacked machinery even reachable?

Before claiming a sweep covers something I measured whether the graded domain
reaches it at all (`TestT63C`, 30,690 admitted shapes):

| mechanism | admitted shapes reaching it |
|---|---|
| `carried != 0` — the **only** inter-period state in `chainStep`, and the value the memo reads out of `chain[chainValid-1]` when it RESUMES | **386** |
| `shouldBeAdjusted` true — the EMI smoothing loop actually runs its trial-rebuild-and-adopt | **9,206** (30%) |
| a period with more than one interest period | 28,560 (93%) |
| a zero-EMI period carrying positive calculated interest | 101 |

Two things follow. First, the memo's resume path is genuinely exercised — had
`carried` been identically zero, no differential over any number of shapes would
have graded it. Second, **the EMI smoothing loop fires on 30% of admitted shapes
and no promoted vector trips its guard** (`loanschedule_test.go:203-214` states
this; conformance is silent about it). That is a corpus gap, not a T59 defect,
and it is already on the program's radar via T57.

### 4. Differential restricted to exactly those shapes — `TestT63J`

Rather than trust that the broad sweeps happened to contain carry/smoothing
shapes, `TestT63J` selects the shapes where `carried != 0` **or** the smoothing
guard is true and runs the memo-on/memo-off differential on those only.

### 5. Final-state memo audit — 215,289 entries, 0 stale

`TestT63D_MemoAgreesWithScratchOnTheFinalState` is a different question from the
output differential: after driving the exact reads `generate` performs, it copies
`m.chain[:m.chainValid]`, forces a from-scratch recomputation over the model's
**final** stored state, and compares entry by entry. A disagreement would be a
proven stale cell **even where the output happened to agree** — the failure mode
an output-only differential can hide.

```
T63D: 7344 generations, 215289 memo entries audited against a from-scratch
      recomputation
--- PASS (15.13s)
```

**Zero stale entries.**

### Attacks I derived from source and could not turn into a failing input

- The **EMI re-adjust smoothing loop** writing backwards onto earlier periods
  (`emi.go:1017-1020`): guarded per-period, immediately before each write.
- The **residual landing on the last unpaid period** (`emi.go:875-879`) and the
  self-recursion at `emi.go:879`: the recursion re-enters after the guard, and
  every level re-reads.
- `deepCopy` starting the trial on an **empty** memo (`emi.go:223`): conservative
  by construction; a copied memo would also be correct but empty cannot be stale.
- `interestChainUpTo` resuming with `carried` from `chain[chainValid-1]`
  (`emi.go:521-524`): sound because `invalidateFrom(i)` sets `chainValid = i`,
  leaving `chain[i-1]` valid, and period *i-1*'s stored state is by construction
  untouched by the write that triggered the invalidation.
- A **model constant** changing mid-generation (`minorDigits`, `precision`,
  `scale`, `rate`): none is ever assigned after `newScheduleModel`.

---

# THE `NumberOfRepayments` REFUSAL — T59 WAS RIGHT, CONFIRMED

T59 refused to bound `NumberOfRepayments` above and routed it as a `user` gate.
**That refusal was correct.** Verified against the ratified contract, not against
T59's summary of it:

- `contract.go:1344-1348`: "It must be >= 1; a value below 1 is not well formed
  and is `ErrInvalidRequest`, **not a graded-domain refusal** (revision 4,
  P2-T26-1)." No upper bound anywhere.
- `contract.go:1133-1137`: `NumberOfRepayments >= 1` "was listed here in revision
  3 and **is NOT a graded-domain predicate** (revision 4, P2-T26-1)."
- `contract.go:1163-1166`: "AnnualNominalInterestRate, the principal, the dates
  and NumberOfRepayments are continuous or **unbounded** inputs; a corpus cannot
  enumerate them, so they are graded by **sampling**."
- `validateGradedDomain` (`generator.go:344-408`) contains no clause on it, which
  matches.

The contract's own equal-rejection requirement (`contract.go:2480-2483`: "two
implementations must reject the same requests, or a request accepted by one and
refused by the other would be indistinguishable from a conformance failure")
makes the point decisive: a Go-side upper bound would refuse a request the
reference oracle answers, which *is* a conformance failure by the contract's own
definition. Bounding it is a DEC-1 amendment → `user` gate. **A correct refusal,
correctly routed, and worth recording as a result.**

The cancellation convention T59 chose is also contract-licensed and I checked it
directly: `contract.go:2470-2473` — "a purely computational implementation may
honour cancellation and otherwise ignore it" — and `contract.go:2475-2476` — "On
error the returned Schedule is the zero value and must not be inspected."
Returning the bare `ctx.Err()` with a zero `Schedule` satisfies both, and
deliberately using none of the three refusal sentinels is right: a cancelled
request was not refused.

---

# WHERE I DISAGREE WITH T59'S HANDOFF (read last, as instructed)

I formed the account above from source, from the write-site grep and from 34,512
+ 30,690 + 7,344 generated shapes **before** opening
`.softhouse/handoff/T59-cancellation-and-cost.md`. Reconciling:

**Where the handoff is better than I expected.** It is unusually honest. It
discloses the `applyFinalPeriodResidual` cliff with its own measurements, names
the un-fixed resource hazard in plain words ("an uncancelled request with an
enormous NumberOfRepayments is still a resource hazard"), records the flaky
wall-clock experiment that motivated the allocation-count substitution rather
than just asserting the conclusion, and refuses the contract change instead of
quietly making it. Four things I went looking to catch it on, it had already
declared.

**Disagreement 1 — the soundness sentence.** "sound because step i is a function
of periods 0..i and of nothing later" is the *wrong rule stated as the reason*
(F-1). The reference oracle is full of later→earlier flow. What makes the memo
sound is the write-ordering discipline, and the handoff's own table of write
sites is closer to the real argument than the sentence above it.

**Disagreement 2 — "six write sites."** There are nine `invalidateFrom` call
sites and eighteen field writes. Six is a count of *functions*. Exhaustiveness
has to be checked against the **writes**, and the handoff never states the fold's
dependency set, so a reader cannot check it. (The set is: `p.segments`, each
segment's `from`/`due`/`outstandingMinor`/`rateFactorTillDue`, `p.due`,
`p.emiMinor`.)

**Disagreement 3 — "192 shapes … two disbursement shapes."** The two shapes
sampled are the two that do **not** split a segment inside a non-first period.
The handoff calls disbursement-on-`due[0]` "the only shape that registers a
balance change into a period other than the first" — that is true of the sweep,
but it is not the interesting property, and the shape the contract itself
singles out as the discriminating one is absent. My 34,512-shape run closes it,
and found nothing, which is the best possible outcome for T59.

**Disagreement 4 — "the 256-period stride bounds the tail latency … to a few
milliseconds."** F-3: O(n), not O(stride).

**Disagreement 5 — the cost claim's scope.** The handoff's table and the
regression test both sample **one rate**. F-4 shows the cliff at n=256 rather
than n≈1100 by raising the rate. And F-2 shows a residual quadratic the chosen
metric cannot see at any n.

**Not a disagreement, a correction of emphasis.** The handoff's backlog item 3
asks for a *long-term* capture. It should read *long-term **or high-rate***.

---

# BACKLOG (out of this review's scope — recorded, not fixed)

1. **F-2 fix** — replace `installmentNumberOf`'s rescan with a running counter in
   `generate`, and add a wall-clock cost assertion at n ≥ 4,000 so a
   non-allocating quadratic cannot hide behind the allocation ratio again.
2. **F-1 / F-3 doc corrections** in `emi.go` — state the write-ordering rule and
   the true latency bound.
3. **F-4** — amend T59 backlog item 3 to *long-term **or high-rate***; a 500%
   capture at n=256 reaches the same shape at a quarter of the term and would be
   cheaper to capture.
4. **F-5** — move `memoiseInterestChain` off the package globals.
5. **UNPROVEN, port fidelity, pre-existing (T10) — `futureUnrecognizedInterest`
   is not ported.** `ProgressiveEMICalculator.java:1217` calls
   `calculateUnrecognizedInterestTillDateOnScheduleModelCopyAndDefer`, which at
   `:1243-1251` (via `:1805-1814`) copies the `unrecognizedInterest` of a period
   at index **> i** onto period *i*'s `futureUnrecognizedInterest`, a field that
   then feeds `getCalculatedDueInterest` (`RepaymentPeriod.java:260`) and
   `getDueInterest`. `applyFinalPeriodResidual` (`emi.go:824-880`) has no
   counterpart. It is inert whenever the last unpaid period is the last period,
   which is the ordinary case. **I did not construct an input that exhibits a
   divergence and I am reporting it as unproven.** The circumstantial reason to
   look: `TestT63C` found **101 admitted shapes** carrying a zero-EMI period with
   positive calculated interest, which is the *necessary* half of
   `getPeriodWithUnrecognizedInterest`'s precondition (the other half — that such
   a period lie strictly *after* the last unpaid one — I did not test). This is
   a T10-fidelity question, not a T59 one, and it is not gradeable without an
   oracle capture at that shape.
6. **Corpus gap, already known:** the EMI smoothing guard is true on 30% of
   admitted shapes and no promoted vector trips it.

---

# THE REVIEW HARNESS

The eight tests above were run from a temporary file
`nexus/internal/apps/loanschedule/t63_review_test.go`, **removed before commit**
so this review changes nothing in the port. The source is preserved verbatim at
`.softhouse/reviews/T63-memo-differential_test.go.txt`; drop it back into the
package and every number here re-runs.
