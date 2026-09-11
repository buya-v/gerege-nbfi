# F-2026-09-11 — `cob` graded coverage: what the committed corpus reaches, and what it never reaches

**Context:** `cob` (Close-Of-Business loan business-step order).
**Worktree:** `/Users/buv/oh-gerege-cobcov` @ `feat/OHCOBCOVar`.
**Method:** add the missing committed-store control, then read coverage from the vector path only.
**Posture:** this run **measures and triages**. No vectors, no drives, no port changes, no captures,
no POST/PUT/DELETE. A 0.0% function is a **candidate**, never a defect.
**Money:** `cob` carries **none** — the graded value is an integer `step_order` (1..6). There is no
minor-unit, rounding or currency surface anywhere in this context, so "money rule" below means
"the context's own rule", not a money computation.

---

## 1. The missing control (added, committed first)

The map (`/.softhouse/maps/cob.md`) recorded the committed-store test as **ABSENT — coverage from
conformance is NOT meaningful for this context**. That is now fixed:

* `nexus/internal/apps/cob/conformance/committed_store_test.go` — commit `ed7bce2b`.
* It resolves the committed store (`LoadStore`, `vector.go`), admits it (`Admit`, `admit.go`) and
  drives every vector through the reference implementation (`Run`, `grade.go`), asserting the
  reference passes all of them, with a guard that **zero vectors loaded fails**.
* It calls **no port function directly**. Every cob statement it reaches is reached through a vector.

## 2. Measurement

From `nexus/`, as prescribed:

```
go test -count=1 -coverpkg=./internal/apps/cob -coverprofile=/tmp/c.cov ./internal/apps/cob/conformance/...
go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'
```

Three readings of the same package (31 instrumented statements, 5 functions):

| Reading | Command | Package total | Functions at 0.0% |
|---|---|---|---|
| **No control** (control withdrawn to `/tmp`, restored immediately) | `go test -count=1 -coverpkg=./internal/apps/cob ... ./conformance/...` | 3.2% (1/31) | 4 |
| **Prescribed, package-wide** | the two commands above | 3.2% (1/31) | 4 |
| **Committed-store-test only** | `go test -count=1 -run '^TestCommittedCorpusPassesTheReferenceImplementation$' -coverpkg=./internal/apps/cob ...` | 3.2% (1/31) | 4 |

**Which figure is honest, and why.** The honest instrument is the committed-store-test-only run: it
reaches port code *only through vectors*. Here it is **identical** to the prescribed package-wide
figure. Unlike `charges`, there is no manufactured divergence in `cob`: the only port function any
vector reaches is `DefaultLoanConfig`, and `conformance_test.go` also reaches that same function
through `NewGoEvaluator()` (`impl.go:94`), which calls `cob.DefaultLoanConfig()` at `impl.go:96`.
So the probes add no reach the vectors deny, and the no-control run reads 3.2% as well.

**Stated plainly:** the new control does **not** move cob's numeric coverage (3.2% before and after).
What it changes is the *meaning* of that number. Before, the 100% on `DefaultLoanConfig` was
manufactured by the conformance probes; now it is also reachable through the committed corpus, and
the four 0.0% functions are confirmed **unreached by any vector**. That is the honest reading this
finding triages.

## 3. Triage method

For each of the four 0.0% functions: (a) is it a rule or a getter/constructor? (b) if a rule, is an
observation behind it already present in a committed capture? (c) if so, name the capture and the
figures a vector would take; if not, say what a capture would need. `cob` has no money, so the
question is whether the context's ordering rule is graded.

## 4. Candidates

### 4.1 `nexus/internal/apps/cob/runner.go:53` — `Order[T any]` (0.0%) — the ordering rule

`Order` resolves a configured `[]StepConfig` against a `map[string]Step` registry, **sorts the steps
ascending by `StepOrder`**, and refuses an unknown step or a duplicate order. This is the cob
context's own rule — the thing the seam exists to pin.

**Why the corpus never reaches it.** The graded path is `goEvaluator.Evaluate`
(`nexus/internal/apps/cob/conformance/impl.go:102`). Its evaluator is built by `NewGoEvaluator`
(`impl.go:94`) as a flat `map[string]int64` seeded directly from `cob.DefaultLoanConfig().BusinessSteps`
(`impl.go:96-98`) via `orderMapFor` (`impl.go:125`); `Evaluate` is then a **single map lookup**. It
never calls `cob.Order`. The vector schema carries one `step_name` request and one `step_order`
expectation, so there is no input that would make the current seam exercise the sort/refuse logic.
All three drives mutate the **seed map** the same way — `cob-wrong-shift-order`
(`impl.go:160`), `cob-wrong-transpose-due-overdue` (`impl.go:168`),
`cob-wrong-skip-delinquency-classification` (`impl.go:183`) — so they validate the seed data, not
the resolution engine.

**Does an observation behind it exist in a committed capture?** The **data `Order` would sort** is
observed, and the capture is on today's instance (pinned tenant `gerege` @ Fineract `426a23544`):

* `.softhouse/capture/cob/out/jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json` —
  `APPLY_CHARGE_TO_OVERDUE_LOANS=1`, `LOAN_DELINQUENCY_CLASSIFICATION=2`,
  `CHECK_LOAN_REPAYMENT_DUE=3`, `CHECK_LOAN_REPAYMENT_OVERDUE=4`,
  `UPDATE_LOAN_ARREARS_AGING=5`, `ADD_PERIODIC_ACCRUAL_ENTRIES=6`.
* corroborated by `.softhouse/capture/cob/out/m-batch-business-steps-readback-raw.json`
  (`step_order` 1..6 for `LOAN_CLOSE_OF_BUSINESS`).

But the **algorithm's** observation — given `(config, registry)`, produce the sorted slice; refuse
unknown/duplicate — cannot be expressed by any vector under the current one-scalar seam. So no
vector the driver can dispatch today reaches `Order`; reaching it requires a **seam/evaluator
extension** (model the resolution step, or route `NewGoEvaluator` through `cob.Order`), not a new
capture. That extension is out of scope for a measurement run.

**Verdict:** candidate, not a gap and not a defect. The capability registry scopes `cob` to
*mapping a step name to its order*, which `DefaultLoanConfig` does and which **is** graded at 100%;
`Order` is the internal sort/refuse engine, which is ungraded by construction. Recorded here so the
next grading run can decide whether the seam should widen to cover it.

### 4.2 `nexus/internal/apps/cob/runner.go:31` — `Run[T any]` (0.0%) — orchestration

`Run` threads an accumulating item through a step slice in order, stops at the first error and wraps
it, and refuses an empty execution (`ErrEmptyExecution`). This is orchestration, not a graded rule:
there is **no REST observation** behind sequential pipeline execution, and no committed capture
carries one — the corpus observes only the step list, never execution. It is reachable only from the
port's own `runner_test.go` (`TestRunEmptyExecution:29`, `TestRunThreadsValuesInOrder:36`,
`TestRunStopsOnErrorAndWraps:62`), which is a direct-call test and therefore manufactured from the
conformance instrument's point of view.

**Verdict:** candidate, not a defect. A capture cannot supply an observation for it; it is testable
only directly, and the port already tests it there.

### 4.3 `nexus/internal/apps/cob/category.go:18` — `(Category).String` (0.0%) — getter

`String()` on an enum type. Out of scope by the triage rule (String()/getter). `Category` is not
referenced by the graded path.

### 4.4 `nexus/internal/apps/cob/lockowner.go:17` — `(LockOwner).String` (0.0%) — getter

`String()` on an enum type. Out of scope by the triage rule. `LockOwner` is not referenced by the
graded path.

### 4.5 (for completeness, not a candidate) `nexus/internal/apps/cob/loancob.go:30` — `DefaultLoanConfig` (100%)

The only port function the committed corpus reaches. It is the **seed data** (the six
`(StepName, StepOrder)` pairs), not a computation. Its reference value passes 6/6 parity vectors
(§7). `businessstep.go` defines only interfaces/types — no instrumented functions.

## 5. What the committed corpus never reaches

| Function | file:line | Cov | Class | Observation in a committed capture? |
|---|---|---|---|---|
| `Order[T any]` | `nexus/internal/apps/cob/runner.go:53` | 0.0% | ordering rule | data observed (`jobs-LOAN_CLOSE_OF_BUSINESS-steps-raw.json`); algorithm not expressible under current seam |
| `Run[T any]` | `nexus/internal/apps/cob/runner.go:31` | 0.0% | orchestration | none possible (no API surface) |
| `(Category).String` | `nexus/internal/apps/cob/category.go:18` | 0.0% | getter | out of scope |
| `(LockOwner).String` | `nexus/internal/apps/cob/lockowner.go:17` | 0.0% | getter | out of scope |
| `DefaultLoanConfig` | `nexus/internal/apps/cob/loancob.go:30` | 100.0% | seed data | graded: 6/6 parity vectors |

**The finding.** After making cob's coverage measurable, the committed corpus reaches exactly one
port function, and that function is the seed data. Cob's actual resolution/sort engine (`Order`) and
its executor (`Run`) sit at 0.0% and are not reachable by any vector under the current one-scalar
seam. The observation for `Order`'s *data* is already committed; the observation for `Order`'s
*behaviour* would need a seam/evaluator extension, which a later grading run can decide on. No
candidate is asserted to be a defect.

## 6. What this run did NOT do

* No vectors authored or modified; no drives added or changed; no port code touched.
* No captures taken; no POST/PUT/DELETE issued.
* Did not touch `.softhouse/guards/` (12 pairs) or `.softhouse/conformance.sh` (census 17).
* Did not touch the driver checkout `/Users/buv/gerege-nbfi` or the push gate.
* Did not commit `TASK.md` or `.softhouse/maps/`.

## 7. Controls

| Control | Result |
|---|---|
| `kills.sh cob cob-wrong-shift-order <wt>` | **6** kills (exit 0) |
| `kills.sh cob cob-wrong-transpose-due-overdue <wt>` | **2** kills |
| `kills.sh cob cob-wrong-skip-delinquency-classification <wt>` | **4** kills |
| `redcount.sh <wt> cob` | **3** (all cob drives kill) |
| `capcount.sh <wt> cob cob-go` | **0** (reference fails no vector) |
| `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <wt>` | **45** (as pinned) |
| `kills.sh parties parties-wrong-iota-ordinals <wt>` | **12** (as pinned) |
| reference on committed store (`go run ./internal/apps/cob/conformance/cmd/conformance -root ..`) | `VERDICT: PASS` — `vectors_loaded=6 parity_pass=6 parity_fail=0` |
| `go build ./...` | exit 0 |
| `go test ./...` | all pass |
| `bash .softhouse/conformance.sh` | exit 2, **only** on `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline …`; no `HARD guard failed` |

Commits: `ed7bce2b` (the committed-store control).
