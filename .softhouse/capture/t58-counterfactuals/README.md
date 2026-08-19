# T58 — the counterfactual measurements behind this fire's `graded_against` margins

**This directory contains no oracle observation.** Every OBSERVED number in the vectors T58
promoted is transcribed from `.softhouse/capture/out/capture-prod3e-raw.json` or
`.softhouse/capture/out/capture-prod3d-raw.json`. What lives here is the *other* half of a
`graded_against` claim: the **derived** value a named wrong implementation would have produced,
and therefore the margin.

> "The oracle" here is the Fineract reference implementation. Oracle Database is a prohibited
> product in this program and appears nowhere in this stack. Nothing here opens a database
> connection of any kind; PostgreSQL remains the only permitted engine for this program.

## What was run

A **scratch copy** of the Go port at `/tmp/t58mut` — never the committed tree. Eight named
counterfactuals were added behind a single package variable `MutT58`, each one a reading of the
pinned Fineract source that the source refutes. `src/apply-mutations-{1,2,3}.py` are the exact,
re-runnable patches; `src/t58cf.go.txt` is the runner.

| `MutT58` | the wrong reading | what the source says |
|---|---|---|
| `TEXTBOOK` | the textbook `balance x rateFactor`: the three separately MathContext-rounded operations collapsed into one exact expression rounded once | `InterestPeriod.java:154-157` — three separate `mc` operations, in that order |
| `NOSETSCALE` | the rate factor without its trailing `setScale(RateFactorScale)` | `ProgressiveEMICalculator.java:1962` has it |
| `PERIODRATIO` | `RepaymentEvery` in the slot the interest call site fills with `periodRatio` | `PEC:1412-1413` passes `periodRatio`; `PEC:1536-1537` passes `repaymentEvery`. Two call sites, two specifications |
| `SEEDSTART` | `calculateSeedDate` always returns the schedule start | `PEC:1477-1480` requires BOTH conjuncts |
| `REANCHORGT` | the month-end re-anchor guard `dateDay >= 28` weakened to `dateDay > 28` | `DefaultScheduledDateGenerator.java:169` is `>= 28` |
| `MONTHENDCLAMP` | clamp into the short month and then continue from the CLAMPED day, never re-anchoring on the disbursement seed | `DefaultScheduledDateGenerator.java:168-176` re-anchors on the seed |
| `SMOOTHINGOFF` | omit `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` entirely | `PEC:749` calls it on every ordinary generation |
| `NOFINALADJ` | the final row keeps the level installment instead of absorbing the residual | `PEC:1160-1219` |

## The control, and why it is the load-bearing part

The runner reports, for every case, `baselineMismatches` — the number of graded money cells on
which the **unmutated** port disagrees with the capture's OBSERVED value.

```
t58-counterfactuals-pass3e.json   16 in-domain cases, 428 graded money cells, baselineMismatches 0
t58-counterfactuals-pass3d.json    4 in-domain cases,  80 graded money cells, baselineMismatches 0
```

**508 cells, zero mismatches.** A counterfactual model whose unmutated form did *not* reproduce
the oracle would be measuring its own defect and calling it a margin; this one reproduces every
cell it is compared against, so the only thing the reported margin can be measuring is the named
change.

`P-CAL` is skipped and reported as skipped: it runs at MathContext precision 12, outside the
graded domain and on `PIN.json`'s never-promotable list.

## Reading the output

Each record is one capture case. `maxMargin[<MUT>]` is the widest single-cell disagreement in
minor units, `nDivergentCells[<MUT>]` how many graded money cells moved, and `divergent[<MUT>]`
lists every one with its observed and counterfactual values. `dateDivergent[<MUT>]` lists date
cells that moved — a counterfactual with date divergence and **zero** money divergence is a
structural kill in the vector store's sense, and is recorded as `kind: "structural"` with
`margin_minor: "0"`.

Money is int64 minor units throughout, and the capture's decimal text is converted by exact
integer string manipulation (`minorFromText`). **There is no floating point anywhere in this
directory's code**, and a text carrying a significant digit beyond the currency scale is an error
rather than something to round.

## `src/cross-harness-t39-vs-pass3e.py` — a second, separate thing

Not a counterfactual. Pass 3e re-asked the fourteen requests task **T39** put to the same pinned
oracle two fires ago through a **different** Path A harness (`CapturePeriodRatio.java`). This
script compares the two observations cell for cell, by meaning rather than by key name, on the
oracle's own emitted characters:

```
14 case pairs, 134 schedule rows, 1,698 cells, 0 differences
```

Two independent Path A harnesses, two fires apart, agree on every cell either recorded. Pass 3e
records **more** than T39 does — `outstandingLoanBalance` on the DISBURSEMENT row — which is the
reason it was run at all (see the handoff, finding **T58-N2**).

## Reproducing

```sh
cp -R nexus /tmp/t58mut/nexus
python3 .softhouse/capture/t58-counterfactuals/src/apply-mutations-1.py
python3 .softhouse/capture/t58-counterfactuals/src/apply-mutations-2.py
python3 .softhouse/capture/t58-counterfactuals/src/apply-mutations-3.py
# add src/t58cf.go.txt as /tmp/t58mut/nexus/internal/apps/loanschedule/t58cf/main.go
# and a file declaring `var MutT58 = ""` in package loanschedule
go run ./internal/apps/loanschedule/t58cf <capture.json>
```

The scratch copy is deliberately not committed: the port in this repository has exactly one
reading, and a mutation switch living beside it is a switch somebody eventually ships.
