# T59 — close T11 F-1 (cancellation) and F-2 (cost) on the Go schedule generator

Branch: `softhouse/T59-cancellation-and-cost`
Scope: `nexus/internal/apps/loanschedule/{generator.go, emi.go}` + tests in that package. Nothing else touched.

## STEP 0 — base verified (P-5)

Worktree cut from `67bee40 softhouse: local fire lock (20260820-080002)`. No rebase was needed:

| artefact | expected | found |
|---|---|---|
| `generator.go` | 719 lines | 719 |
| `emi.go` | 832 lines | 832 |
| `rounding.go` | present | 189 lines |
| `loanschedule_test.go` | present | 300 lines |
| `.softhouse/vectors/loanschedule/P-*.json` | 29 promoted parity vectors | 29 (+4 REFUSE) |
| `git log -1 -- generator.go` | — | `91fcee2 T10: Go native loan-schedule port` |

Baseline conformance on the untouched base was re-run at the end and is unchanged: **29 parity PASS, 2354 cells, exit 0**; `--prove` **20/20, exit 0**.

## The driver correction was right, and I measured it before changing anything

`ctx.Err()` occurred exactly once in the package, at `generator.go:72`, and zero times in `emi.go`. Measured on the untouched base (repo-local Go toolchain, `baseRequest(50,000,000.00 MNT, n, 21.6%)`):

```
n=6    3.32ms      n=120   821.79ms
n=12   10.35ms     n=180   2.737s
n=36   80.94ms     n=240   4.832s
n=60   217.11ms    n=360   10.772s
deadline 50ms, n=360: elapsed=10.82s  err=<nil>     <-- F-1, reproduced exactly
```

So: not "ignores cancellation" — checks it once and never again, and then computes for 10.8 s for a caller who left after 50 ms. Cost fit ≈ n^2.1.

## F-2 — what the cost actually was, and the fix

The port dropped the oracle's `Memo` and recomputed `interestChainUpTo` on every read. Every reader is itself an O(n) loop (`updateOutstandingBalances`, `applyFinalPeriodResidual` twice, the final row-emitting loop, `findLastUnpaidPeriod`'s fallback), so the chain ran O(n) times at O(n) each.

**Fix: restore the oracle's memoisation, as a PREFIX cache.** `chainStep{calculated, due, carried}` per period, `chainValid` = number of valid leading entries. `interestChainUpTo(last)` returns entry `last` if valid, otherwise resumes the fold from `chainValid` instead of restarting at 0.

The invalidation rule is **by period index, not by dependency hash** (the oracle hashes; `Memo.java:56-72`). It is sound for one reason and the code says so: step *i* is a function of periods 0..i and of nothing later, so a write to period *j* leaves every step before *j* intact. Every site that writes a quantity the fold reads now calls `invalidateFrom`:

| site | what it writes |
|---|---|
| `calculateRateFactors` | both rate factors of a period |
| `updateOutstandingBalances` | a segment's outstanding balance |
| `registerBalanceChange` (covers `insertSegment`) | segment amounts, a moved segment due date, an inserted segment |
| `calculateLevelInstallment` | the installment on the related periods |
| `applyFinalPeriodResidual` | the guard loop's installment write, and the residual write at `idx` |
| `adjustEMIIfNeeded` | the trial's installments (on the trial's own memo) and the adopted ones |

`updateOutstandingBalances` needed one ordering change to stay linear: the `duePrincipalMinor(prevPeriod)` read is hoisted into a local **before** `invalidateFrom(i)`, so the prefix that read just paid for survives the write. Same expression, same value.

`deepCopy` starts the trial on an **empty** memo (copying would also be correct — the two models are equal at that instant — but an empty memo cannot be stale).

### Before / after — real numbers

Same request shape, min of 3, repo-local toolchain, same box:

| n | memo OFF (== the pre-T59 port) | memo ON (this branch) | speedup |
|---|---|---|---|
| 6 | 2.85 ms | 0.65 ms | 4.4x |
| 12 | 9.62 ms | 1.25 ms | 7.7x |
| 36 | 70.5 ms | 3.74 ms | 18.9x |
| 90 | 456.3 ms | 9.37 ms | 48.7x |
| 180 | 2.693 s | 22.2 ms | 121x |
| **360** | **10.767 s** | **39.3 ms** | **274x** |
| 720 | (not run) | 80.2 ms | — |

Growth over a 4x term (n=90 → n=360): **22.81x before, 4.19x after** (linear is 4x, quadratic 16x).

Allocation counts, which are deterministic and are what the regression test asserts:

| | n=90 | n=360 | ratio |
|---|---|---|---|
| memo off | 4,114,328 | 92,667,466 | 22.52x |
| memo on | 76,581 | 357,932 | **4.67x** (~1,000 allocations per period, flat) |

## F-1 — cancellation, and the cadence I chose

`ctx` is carried on `scheduleModel` and a sticky `cancelled` flag is set by `checkCancel(i)`, which reads the context **at most once every `ctxCheckStride = 256` periods** and short-circuits forever once set.

**Why the model holds the ctx rather than threading an error return:** the readers of the chain are `duePrincipalMinor`, `dueInterestMinor`, `outstandingLoanBalanceMinor`, `initialBalanceMinor` — they *are* the money arithmetic, and they are consumed inside expressions throughout `emi.go`. Giving them error returns rewrites every money expression in the file. Rewriting money code to fix a liveness defect is a trade with a bad expected value in this program; the diff over money lines is deliberately near-zero.

**Why 256 and not 1:** `context.Context.Err` takes a mutex on a `cancelCtx`. On the innermost fold step that charges every schedule for a property only a cancelled schedule uses. 256 periods of post-fix work is ~28 ms at the measured per-period cost, so a cancelled call unwinds in about that; measured 30–50 ms end to end including the 30 ms the test waits before cancelling. **Every graded shape is 36 periods or fewer, so on the whole corpus the context is read exactly once per pass, at index 0** — the cadence is invisible to conformance by construction.

Checks are placed at the head of the loops where the time is actually spent: `recalculate`'s rate-factor loop, `updateOutstandingBalances`, `calculateLevelInstallment`'s two `big.Rat` folds, both of `applyFinalPeriodResidual`'s period loops, `interestChainUpTo`'s fold, the outer iteration of `adjustEMIIfNeeded` (its inner steps carry their own), `newScheduleModel`'s construction loop, `repaymentDueDates`, and the final row-emitting loop in `generate`.

**Safety property:** a schedule is returned only when the emitting loop ran to completion on a model that was never abandoned. `generate` consults `model.cancelled` *after* the loop and returns `ctx.Err()` if set. Abandonment is only ever reachable through `checkCancel` returning true, which sets the flag first — so a half-built row list cannot be mistaken for an answer. When `interestChainUpTo` bails it records only the steps that **completed**, so the memo stays truthful even on the abandoned path.

**Error convention: the bare `ctx.Err()`,** which is what `generator.go:72` already returned. Not wrapped in a contract sentinel — a cancelled request was not *refused*, and the contract's three sentinels are a refusal taxonomy. The contract licenses this explicitly: "a purely computational implementation may honour cancellation and otherwise ignore it" (`contract.ScheduleGenerator.Generate`).

One allocation change in `repaymentDueDates`: the capacity hint is `min(count, 4096)` instead of `count`. `NumberOfRepayments` is caller-controlled and unbounded, and a hint of two billion is a multi-gigabyte allocation demanded before the first date is computed or the first cancellation noticed. `append` grows at the same amortized cost and returns identical dates.

## The hard constraint: not one computed money value changed

- `.softhouse/conformance.sh` → **29 parity PASS / 0 FAIL, 2354 cells, exit 0**.
- `.softhouse/conformance.sh --prove` → **20 passed, 0 failed, exit 0**.
- `TestInterestChainMemoIsObservationallyInert` generates **192 shapes twice**, once with `memoiseInterestChain` true and once false, and compares every cell. Memo-off is bit-for-bit the arithmetic the 29 vectors were passed with before this branch. Sweep covers 4 schedule starts (incl. 31st, 30th, last-day-of-short-month), 3 rates, 2 principals, terms {1,2,6,12,18} and two disbursement shapes (on the start, and on repayment period 1's due date — the row-ordering trap and the only shape that registers a balance change into a period other than the first).

## Contract conflict on bounding — NOT DONE, and why

**`NumberOfRepayments` cannot be bounded above without amending DEC-1.** The ratified contract states it "must be >= 1; a value below 1 is not well formed and is `ErrInvalidRequest`" (`contract.go:1344-1348`) and the graded-domain list (`contract.go:1113-1137`) explicitly **removed** `NumberOfRepayments` as a graded-domain predicate in revision 4 (P2-T26-1), noting it is "continuous or unbounded" and "graded by sampling". Refusing `n = 100,000` would refuse a request the graded domain admits. That is a **contract change → `user` gate**, and per the task instruction I did not make it. Only the contract-safe half of F-2 is implemented (memoisation + cancellation + the allocation-hint cap).

Consequence, stated plainly: **an uncancelled request with an enormous `NumberOfRepayments` is still a resource hazard.** At `int32` max the due-date slice alone is ~24 GB. The mitigation available today is a *caller-side* deadline, which now works. A production deployment behind this contract should set one at the adapter boundary.

## Residual cost characteristic I found and did NOT fix (backlog)

Cost is linear in n up to ~n=1000 for ordinary shapes, then cliffs on **near-interest-only shapes**:

```
n=720   96.9ms   zero-principal rows 0
n=800  284.1ms   zero-principal rows 255
n=900  118.7ms   zero-principal rows 2
n=1000 118.2ms   zero-principal rows 11
n=1100  2.313s   zero-principal rows 929
n=1200  2.748s   zero-principal rows 1025
```

CPU profile attributes 34.9% cumulative to `applyFinalPeriodResidual`. Mechanism: when the term is long enough relative to the rate that many rows amortize zero principal, the residual write drives `emiMinor` negative, the function zeroes it and **recurses**, `findLastUnpaidPeriod` walks back one period per level, and the depth guard is `len(periods)+2` — so depth is O(n) and each level is O(n). That is O(n²) chain steps.

I did **not** touch it. It is a faithful port of `ProgressiveEMICalculator.java:1160-1219`, it is the innermost money code in the file, and no vector grades that shape — changing it is a money risk with no oracle to check against. Note the memo already improved this path from cubic to quadratic, and the cancellation checks inside it mean a caller with a deadline is protected. **Backlog: capture a long-term / near-interest-only vector from the reference oracle, then revisit the residual iteration.**

## Tests added — `nexus/internal/apps/loanschedule/liveness_test.go`

1. **`TestCancellationIsHonouredDuringGeneration`** — a 50,000-period request with (a) an explicit cancel and (b) a deadline, both firing 30 ms in. Asserts the error is the *context's* (`errors.Is` on `context.Canceled` / `context.DeadlineExceeded`) and **not** a contract refusal sentinel; that the returned `Schedule` is the zero value as the contract requires on error; and that the call returned inside a **2 s budget**.
   *Margin:* measured 30–50 ms on this box (30 ms of deadline + at most one stride of work). 2 s is ~40x that, so a box twenty times slower still passes. The bound is enforced by a `select` rather than a stopwatch read afterwards, because on the implementation this test rejects the call does not return for *hours* at this term — a test that hangs when it fails is a test that gets deleted.
   *Mutation-checked:* with `checkCancel` forced to `return false`, both subtests FAIL at exactly 2 s with the intended message.

2. **`TestGenerationCostIsNotQuadraticInTheTerm`** — asserts the ratio of **heap allocation counts** between n=90 and n=360 is under **9.00x**, plus a crude 5 s wall-clock cap at n=360.
   *Why allocations and not a stopwatch — this is the important part.* I first wrote it as min-of-five wall clock and **measured it flaky**: on a box carrying twice as many spinners as cores it produced 12.06x, 15.13x and 14.32x on three consecutive runs, against a 16x quadratic figure. There is no threshold separating "linear under load" from "quadratic idle", because the longer run absorbs proportionally more preemption and GC and taking the minimum does not fix a bias present in every repetition. Allocation count is a deterministic property of the computation: drift across runs is under 0.1% (45,005 then 44,992 at n=45), it is unaffected by load, and nearly every allocation is a `big.Rat` from a chain step — precisely the quantity the memo bounds. Threshold 9.00x sits at ~2x the observed 4.67x and well under the 22.52x the un-memoised port produces.
   *Verified robust:* three consecutive runs under 2x CPU oversubscription all reported exactly 4.67x and passed.

3. **`TestInterestChainMemoIsObservationallyInert`** — described above. Writes a package-level switch, so it is documented as never-parallel.

## Verification — actual output

```
go build ./...      exit 0
go vet ./...        exit 0
go test ./...
  ok  github.com/gerege/nexus/internal/apps/loanschedule                  2.361s
  ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance      1.351s
  ?   .../conformance/cmd/conformance   [no test files]
  ?   .../contract                      [no test files]
(also green at -count=3, and green three times under 2x CPU oversubscription)

.softhouse/conformance.sh          exit 0
--- SUMMARY ---
    parity vectors          PASS 29   FAIL 0
    contract-refusal        PASS 4    FAIL 0   (derived from the ratified contract, NOT oracle-observed)
    self-test fixtures      PASS 1    FAIL 0   (hand-authored; EXCLUDED from the parity count)
    refused                 0
    inadmissible            0
    harness errors          0
    cells compared          2354 graded, 58 ungraded (never recorded by the capture)
    kills named             86 money, 7 structural (zero-margin by construction, never merged)
    recorded, never graded  0 rate factors (TRANSCRIBED-ROUNDED), 0 declared over-scaled money cells
    invariant violations    0
VERDICT: PASS (exit 0) — 29 parity vectors match the pinned reference oracle, 2354 cells compared.

.softhouse/conformance.sh --prove  exit 0
PROOFS: 20 passed, 0 failed
```

Gate G-3 respected: `gofmt -l` over the package flags **exactly** `internal/apps/loanschedule/contract/contract.go` and nothing else. `contract.go` was not opened for writing and no DEC-n was amended.

Non-negotiables: no `float64`/`float32` anywhere in the package outside a comment in `conformance_test.go` (the earlier draft of the cost test had one for a timing ratio; it was removed and the comparison is exact integer nanoseconds / integer allocation counts). No database code exists in this context at all — schedule generation is pure computation.

## Backlog

1. **Unbounded `NumberOfRepayments` is a resource hazard** — bounding it is a DEC-1 amendment and therefore a `user` gate. Either raise the gate, or require an adapter-side deadline as a deployment obligation. (Blocked on `user`.)
2. **`applyFinalPeriodResidual` recursion is O(n²) on near-interest-only shapes** — capture a long-term vector from the reference oracle first; do not touch that code unvectored.
3. **The corpus samples terms 6/12/18/36 only.** Nothing in the vector store grades any shape where a repayment row amortizes zero principal, which is the exact shape the cliff above lives on. A capture there would grade money *and* let item 2 be worked safely.
4. `.softhouse/conformance.sh` still grades no liveness property. The three tests here are package tests, not vectors; if the harness ever grows a "cost/liveness" class, they are the obvious first entries.
