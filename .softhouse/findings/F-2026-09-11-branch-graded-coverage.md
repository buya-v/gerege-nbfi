# F-2026-09-11 — the branch graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written, no port code changed. This run makes the branch corpus *measurable* and triages
the result. Grading anything it finds is a later run's work.
**Task:** `OH-BRCOV-AQ`, bounded context `branch`, branch `feat/OHBRCOVaq`.
**Found by:** Go coverage of the branch port, measured with the port as `-coverpkg` and
the **conformance package** as the test target — the instrument the driver validated on
the savings-holds case and reused for `loan`/`charges`, not the grep it replaced.

## 1. The missing control, added

`branch`'s map recorded the committed-store test as **ABSENT**, so no committed vector
could be *attributed* any reach: the number that came out of the conformance package could
not be read as "what the graded corpus does". Added
`nexus/internal/apps/branch/conformance/committed_store_test.go`, modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against the
  reference `branch-go`, exactly as the grading binary does;
* it **calls no port function directly** — every statement it reaches is reached *through
  the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors, it fails on any load error, it
  fails if any committed vector is inadmissible or fatal, and it asserts one committed
  vector per seam (`cashier-txn-amount`, `cashier-summary`, `teller-status`) so a later
  deletion of an observation is a failing test, not a silent return to no coverage.

Committed as `26e25154` ("branch: measure the committed corpus with a committed-store
test"), before the finding, as required.

The committed corpus passes, through the binary:

    go run ./internal/apps/branch/conformance/cmd/conformance -root ..
    → vectors_loaded=6 parity_pass=6 parity_fail=0 refused=0 inadmissible=0
      harness_error=0 graded_cells=16 money_cells=9 invariant_violations=0
      nofloat: packages=48 files=390 tokens=405341 imports=1151 violations=0

## 2. Before / after — and which figure is honest

    go test -count=1 -coverpkg=./internal/apps/branch \
        -coverprofile=/tmp/c.cov ./internal/apps/branch/conformance/...

`./internal/apps/branch` is **154 statements in 24 functions**.

| run | statements covered | coverage | functions at 0.0% |
|---|---:|---:|---:|
| **before** (no committed-store test; the nine probe tests in `conformance_test.go`) | 39 / 154 | 25.3% | 19 |
| **after** (all of the above plus the committed-store test — the prescribed command) | 39 / 154 | **25.3%** | 19 |
| **committed-store-test only** (`-run TestCommittedCorpusPassesTheReferenceImplementation`) | 35 / 154 | **22.7%** | 19 |

**The prescribed package-wide figure does not move, and the honest figure is the
committed-store-test-only 22.7%, not the 25.3%.** The reason is different from the
`charges` case and has to be stated precisely:

* branch's `conformance_test.go` does **not** import the port (unlike charges'
  `conformance_test.go:10`, which does) — grep for `internal/apps/branch` in it finds only
  the schema literal `gerege.branch.vector/v2` at line 313. What it does is build **probe
  vectors** and run them through `gradeOne(..., Options{Implementation: NewGoEvaluator()})`,
  i.e. through `impl.go`'s `goEvaluator`, which calls the port. Those probes are not in the
  committed store.
* Those probes already reach every statement the committed corpus reaches (the union of the
  two is 39, the same as the probes alone), **plus two arms the committed corpus never
  reaches**. So 25.3% overstates the committed corpus by 2.6 points; 22.7% is the figure
  that answers "what does the graded corpus reach". The two probe-only arms are:

| arm | committed-store run | package-wide run | reached by |
|---|---:|---:|---|
| `money.go:78.33,80.3` + `:81.33,82.21` + `:82.21,86.4` — the sub-minor-unit **residue refusal** | 0 hits | 1 hit | the `"100000.505"` probe in `conformance_test.go:360-364` |
| `status.go:90.10,91.33` — the **unknown-id default** arm of `CashierTxnTypeFromID` | 0 hits | 1 hit | the `TxnType = 0` probe in `conformance_test.go:354-358` |

Block-level, those are the *only* differences between the two profiles; every other branch
block has the same hit count. The committed-store test therefore does not enlarge the
number — it makes the number **attributable to the corpus**, which is what the map marked
ABSENT.

**Caveat on the map.** `.softhouse/maps/branch.md` says coverage "from conformance is NOT
meaningful for this context". That is true about *attribution*, but it does not mean the
reading was 0.0%: the probe tests have always put 25.3% on the board. The map's promise
that "without a store-driven test in the package, every port function reads 0.0%" holds for
`loan`/`savings` where `conformance_test.go` did not drive the evaluator; it does not hold
verbatim for branch, and this finding corrects that reading. (Map nit: the Registration
section lists `main.go` among the conformance package files; the package has no `main.go`,
the binary's is `nexus/internal/apps/branch/conformance/cmd/conformance/main.go`.)

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Each candidate is checked against one question
only:

> **Does an observation behind it exist in the committed corpus?**

If yes, name the capture file and the figures a vector would take; if no, say what a
capture would need. Only functions that implement a **money rule** (not a getter, a
`String()`, a status predicate, an error constructor) are candidates. Nothing below is
asserted to be a defect.

### Corpus scope

The **graded branch corpus** is the 6 vectors in `.softhouse/vectors/branch/`. Their
capture refs are the only observations in play:

    branch/out/{summary-cashier2-pre-raw,summary-cashier2-post-raw,
                summary-cashier2-final-raw,txns-cashier2-raw,tellers-list-raw}.json
    branch/req/{allocate,settle,settle-3dp-probe}.json

They are the context's **own** captures (tenant `gerege`, `MNT`, 2 minor units,
`Asia/Ulaanbaatar`, Fineract `426a23544`), not one of the earlier `t*`/`A2-*` instances the
map warns about. `branch/` carries **no `OWNER.md`**, so there is no explicit
instance-attestation title to lean on — but these are the exact files the committed vectors
already hash and cite, so the warning does not apply to them.

## 4. The money-rule candidate

### 4.1 `money.go:22` `FormatDecimal` — a money rule, observed, but not on any graded path

*Rule.* `func (m MinorUnits) FormatDecimal(minorDigits int) string` (`money.go:22-44`)
renders an integer minor-unit count into major-unit decimal text (it handles the negative
sign at `:23-26`, the `minorDigits == 0` case at `:33`, and zero-pads the fraction at
`:34-39`). It is the **write-side** money conversion — the mirror of the graded
`MinorUnitsFromDecimalText` (`money.go:48`) — and it is the text the port hands to
PostgreSQL. Money rule, integer minor units, no float.

*Why 0.0%.* It is called from exactly one place:
`postgres.go:165` `t.TxnAmount.FormatDecimal(MNTMinorDigits)` inside
`PostgresCashierTransactionRepository.Insert`. The comparator's `Run` never calls `Insert`
— `doc.go:71-73` states the comparator "runs against vectors … and does not touch a
database" — and `evaluateMovement` (`impl.go:115-129`) calls only
`MinorUnitsFromDecimalText`, never `FormatDecimal`. The `Expect` struct
(`vector.go:133-143`) has a `txn_amount_minor` cell and **no rendered-text cell**. So no
vector, and no path any vector can take, reaches this function. Its 0.0% is structural,
not a coverage accident.

*Observation.* **Exists, for every movement the corpus carries.** The committed captures
record the amount as exact DECIMAL(19,6) text, and the port's 2dp render of the same value
is the 2dp projection of that text:

| capture | row | observed `txnAmount` | minor units | `FormatDecimal(MNTMinorDigits)` |
|---|---|---|---|---|
| `branch/out/summary-cashier2-final-raw.json` | id 7 | `100000.500000` | 10000050 | `100000.50` |
| `branch/out/summary-cashier2-final-raw.json` | id 8 | `40000.250000` | 4000025 | `40000.25` |
| `branch/out/summary-cashier2-final-raw.json` | id 6 | `12345.670000` | 1234567 | `12345.67` |
| `branch/out/txns-cashier2-raw.json` | id 6 | `12345.670000` | 1234567 | `12345.67` |
| `branch/req/allocate.json` | — | `100000.50` (the text the oracle received) | 10000050 | `100000.50` |
| `branch/req/settle.json` | — | `40000.25` (the text the oracle received) | 4000025 | `40000.25` |

*Verdict.* **Not dispatchable as a vector.** This is the important difference from the
`charges` cap clamp: there the clamp arithmetic was already inside the graded evaluator and
only a vector was missing. Here the observation exists but the graded seam has no cell for
it, and the evaluator never calls `FormatDecimal`. Grading it needs a **conformance-seam
extension**, not a port change:

1. add an expected rendered-text cell (e.g. `txn_amount_text`) to `Expect` in
   `vector.go:133-143`;
2. have `evaluateMovement` (`impl.go:115-129`) fill it via
   `branch.MinorUnitsFromDecimalText(...).FormatDecimal(branch.MNTMinorDigits)`;
3. add a vector whose expected text is the 2dp projection above (e.g. `"100000.50"` from
   `summary-cashier2-final-raw.json` row id 7, `"40000.25"` from row id 8).

That is harness/schema work a later run may choose to do; it is not a measurement this run
makes. Recorded so the driver can decide. **No capture is needed** — the observation is
already committed.

## 5. Partial-coverage money-shaped arms the corpus does not reach

These are not `0.0%` functions, but the triage would be dishonest without them: they are
the arms of *graded* functions the committed corpus leaves cold.

### 5.1 `money.go:48` `MinorUnitsFromDecimalText` — the residue-refusal arm is deliberately ungradeable

Committed-store run **64.9%**, package-wide **73.0%**. The difference is the
sub-minor-unit **residue refusal** (`money.go:78-86`): block `78.33,80.3`
(`if len(fracPart) > minorDigits { keep, rest = … }`), `81.33,82.21` (the `rest` scan) and
`82.21,86.4` (the `ErrInvalidRequest`-style refusal) read **0 hits** in the committed-store
run and 1 hit package-wide.

*Observation.* It exists: `branch/out/summary-cashier2-final-raw.json` row id 9 carries
`txnAmount 40000.245000` — the 3dp probe.

*But no vector may grade it.* `admit.go:117-119` calls `MinorUnitsFromDecimalText` on the
request and refuses any vector whose amount carries residue, and `doc.go:44-60` records the
refusal as a **ratified deliberate departure** (Buyan, 2026-09-09, gate G-19, DEC-2) — "no
parity vector is derived from the final read that includes 40000.245, and none ever
should be". So this arm is reached only by the `"100000.505"` probe in
`conformance_test.go:360-364`, by design. Not a gap; a recorded decision, and the coverage
instrument now makes that decision visible.

### 5.2 `status.go:80` `CashierTxnTypeFromID` — cash-in/cash-out and the unknown id are unobserved

Committed-store run **50.0%**, package-wide **66.7%**. Three arms are cold:

* `status.go:86.11,87.29` — `TxnInwardCash` (103): **0 hits in both runs**;
* `status.go:88.11,89.30` — `TxnOutwardCash` (104): **0 hits in both runs**;
* `status.go:90.10,91.33` — the unknown-id `default`: 0 committed, 1 package-wide (the
  `TxnType = 0` probe in `conformance_test.go:354-358`).

*Observation.* **None exists.** No capture in the branch tree records a cash-in (103) or
cash-out (104) `m_cashier_transactions` row, and no capture records an unknown id. This is
a dispatch-table predicate, not a money fold, so it is a low-value candidate; but it is
honest to say the two non-allocate/settle movement types are invisible to the corpus.

*What a capture would need.* A cashier-txn-amount observation from a `POST` that creates a
103 or 104 row (`summary-cashier2-*-raw.json` would then carry it), transcribed exactly as
the allocate/settle vectors already are. The map's `cashier-txn-amount` capability is
`in_graded_domain: True` and does not restrict the txn type, so such a vector would be
admissible without any harness change. The unknown-id arm is a refusal observation and
cannot be a parity vector (the harness has only `ClassParity`), so it stays probe-reached.

## 6. Everything else at 0.0% (not money rules — out of scope)

The remaining 17 of the 19 `0.0%` functions are neither money rules nor observed:

* **PostgreSQL storage, 12 functions** — `postgres.go:28` `NewPostgresTellerRepository`,
  `:33` `Insert`, `:47` `FindByID`, `:60` `FindByOffice`, `:64` `find`, `:98`
  `NewPostgresCashierRepository`, `:103` `Insert`, `:116` `FindByTeller`, `:155`
  `NewPostgresCashierTransactionRepository`, `:161` `Insert`, `:174` `FindByCashier`,
  `:206` `nullIfEmpty`. The comparator does not touch a database (`doc.go:71-73`); these
  are the persistence surface, not the graded money vocabulary. Note `Insert`
  (`postgres.go:161-171`) is the only caller of `FormatDecimal` and `FindByCashier`
  (`postgres.go:174-204`) is a caller of `MinorUnitsFromDecimalText`, but both are DB I/O.
* **`status.go:26` `TellerStatusFromInt`** — the stored-value→enum decoder, the inverse of
  the graded teller-status mapping. It is reached only by `postgres.find`
  (`postgres.go:76`) and by `branch_test.go:5-21`. No capture serialises the stored integer
  directly (`tellers-list-raw.json` carries only the label `"ACTIVE"`), so a label-only
  corpus cannot reach stored→enum. Not money; no capture would change that without a
  seam that reads the column.
* **`status.go:42` `IsPending`, `:45` `IsActive`, `:48` `IsInactive`, `:51` `IsClosed`** —
  status predicates, explicitly excluded.
* **`teller.go:24` `OfficeIDFor`** — a getter, explicitly excluded.

## 7. Summary of triage

| candidate | `file:line` | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `FormatDecimal` | `money.go:22` | **yes** | **yes** — `summary-cashier2-final-raw.json` ids 6/7/8, `txns-cashier2-raw.json` id 6, `req/{allocate,settle}.json` | **needs a seam extension**, not a vector alone |
| residue-refusal arm | `money.go:78.33,80.3`, `:81.33,82.21`, `:82.21,86.4` | yes (refusal) | yes — `summary-cashier2-final-raw.json` id 9 `40000.245` | deliberately ungradeable (G-19/DEC-2); not a gap |
| `TxnInwardCash` arm | `status.go:86.11,87.29` | no | **no** | needs a 103 capture to grade |
| `TxnOutwardCash` arm | `status.go:88.11,89.30` | no | **no** | needs a 104 capture to grade |
| unknown-id arm | `status.go:90.10,91.33` | no | **no** (refusal) | stays probe-reached |
| 12 storage functions | `postgres.go:28,33,47,60,64,98,103,116,155,161,174,206` | no | n/a | out of the graded domain by design |
| `TellerStatusFromInt` | `status.go:26` | no (decoder) | no (label-only) | out of scope |
| 4 status predicates | `status.go:42,45,48,51` | no | n/a | excluded |
| `OfficeIDFor` | `teller.go:24` | no | n/a | excluded (getter) |

**No candidate is asserted to be a defect.** The one implemented, observed money rule the
graded corpus never reaches is `FormatDecimal`, and reaching it costs a seam extension, not
a capture. The one non-money observation the corpus is missing is a cash-in/cash-out
movement (103/104).

## 8. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued.
* No vector and no drive was written. `.softhouse/vectors/branch/` is unchanged at 6 files.
* No port code changed. `.softhouse/guards/` (12 pairs) and `.softhouse/conformance.sh`
  (census 17) are untouched.
* No gap was graded; §4 names what a later run may grade, §5 names what would need a
  capture first.

## 9. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass; the new test passes `-count=1`.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
  completed and the bar is refused by that recorded decision`. Verdict PASS. No
  `HARD guard failed` (grep count 0).
* `kills.sh branch branch-wrong-off-by-one <worktree>` → **6** (all 6 branch vectors; as
  before).
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <worktree>` → **45** (control
  holds).
* `kills.sh parties parties-wrong-iota-ordinals <worktree>` → **12** (control holds).
* `capcount.sh <worktree> branch branch-go` → **0** (the reference fails no vector).
* `redcount.sh <worktree> branch` → **6** (all registered branch drives kill).
* `branch-go` on the committed store: `vectors_loaded=6 parity_pass=6 parity_fail=0`.
* The new test's coverage is vector-driven: the package-wide number is unchanged by it
  (the probe tests already reached the evaluator), so nothing in this finding rests on
  manufactured reach.

## Appendix A — all 19 functions at `0.0%` in the prescribed run

`file:line` are lines in each file.

- `money.go:22` `FormatDecimal`
- `postgres.go:28` `NewPostgresTellerRepository`
- `postgres.go:33` `Insert`
- `postgres.go:47` `FindByID`
- `postgres.go:60` `FindByOffice`
- `postgres.go:64` `find`
- `postgres.go:98` `NewPostgresCashierRepository`
- `postgres.go:103` `Insert`
- `postgres.go:116` `FindByTeller`
- `postgres.go:155` `NewPostgresCashierTransactionRepository`
- `postgres.go:161` `Insert`
- `postgres.go:174` `FindByCashier`
- `postgres.go:206` `nullIfEmpty`
- `status.go:26` `TellerStatusFromInt`
- `status.go:42` `IsPending`
- `status.go:45` `IsActive`
- `status.go:48` `IsInactive`
- `status.go:51` `IsClosed`
- `teller.go:24` `OfficeIDFor`

## Appendix B — the five functions the graded corpus does reach

- `money.go:48` `MinorUnitsFromDecimalText` — 64.9% (residue arm cold; §5.1)
- `status.go:21` `StoredValue` — 100.0%
- `status.go:80` `CashierTxnTypeFromID` — 50.0% (103/104/default cold; §5.2)
- `summary.go:24` `NetCash` — 100.0%
- `summary.go:33` `FoldCashierSummary` — 66.7%
