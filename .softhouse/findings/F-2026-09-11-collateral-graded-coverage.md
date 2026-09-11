# F-2026-09-11 — the `collateral` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written. This run makes the collateral corpus *measurable* and triages the result.
The one money rule the corpus never reaches (`UpdateQuantityAfterLoanClosed`) is
also beyond the reach of every current seam, so grading it needs a capture **and** a
new seam — a later run's work.
**Task:** `OH-COLCOV-AM`, bounded context `collateral`, branch `feat/OHCOLCOVam`.
**Found by:** Go coverage of the `collateral` port, measured with the port as
`-coverpkg` and the **conformance package** as the test target — the instrument the
driver validated on the savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`),
the loan corpus (`F-2026-09-11-loan-graded-coverage.md`) and the charges corpus
(`F-2026-09-11-charges-graded-coverage.md`).

## 1. The missing control, added

The map said the `collateral` committed-store test was **ABSENT**, so coverage measured
from conformance meant nothing: without a store-driven test in the package, no vector
can move the number and every port function reads `0.0%` no matter how many vectors
exist.

Added `nexus/internal/apps/collateral/conformance/committed_store_test.go` (commit
`cbaf1a07`), modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against
  the reference `collateral-go`, exactly as the grading binary does
  (`conformance/vector.go` `LoadStore`, `conformance/admit.go` `Admit`,
  `conformance/grade.go` `Run`);
* it **calls no port function directly** — every statement it reaches is reached
  *through the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors, and asserts every loaded
  vector is admissible, `Run` is not fatal, `VectorsLoaded != 0`,
  `parity_fail + refused + inadmissible + errored == 0`, and
  `invariant_violations == 0`;
* it pins the observations per seam (product ≥ 2, link ≥ 1, client ≥ 1,
  **valuation ≥ 2**). The valuation seam is the one that reaches the port's arithmetic
  `ClientCollateral.Total` / `TotalCollateral` (`conformance/impl.go`); with that guard,
  deleting `CL-04`/`CL-06` is a failing test rather than a silent return to `0.0%`
  coverage of the valuation rule.

The committed corpus passes the reference:

    go run ./internal/apps/collateral/conformance/cmd/conformance -root ..
    → VERDICT: PASS (exit 0)
      vectors_loaded=6 parity_pass=6 parity_fail=0 refused=0 inadmissible=0
      harness_error=0 graded_cells=25 invariant_violations=0
      nofloat: packages=48 files=385 tokens=402133 imports=1132 violations=0

## 2. Measurement

The prescribed command (from `nexus/`):

    go test -count=1 -coverpkg=./internal/apps/collateral \
        -coverprofile=/tmp/c.cov ./internal/apps/collateral/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

Because the package's other test file (`conformance_test.go`) grades **hand-built**
probes through the evaluator, the prescribed package-wide run was compared against the
committed-store-test-only run:

    go test -count=1 -run '^TestCommittedCorpusPassesTheReferenceImplementation$' \
        -coverpkg=./internal/apps/collateral \
        -coverprofile=/tmp/c_vec.cov ./internal/apps/collateral/conformance/...

| run | test target | statements | functions at 0.0% |
|---|---|---:|---:|
| **prescribed** (whole conformance package) | all tests | **3.3%** | **26** |
| **committed-store-only** (control alone) | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | **3.3%** | **26** |

Both figures are **identical, down to the function set** (verified with `diff` on the
`0.0%` `file:line:name` triples): `conformance_test.go` builds probes
(`productProbe`/`linkProbe`/`clientProbe`/valuation probe) that drive
`NewGoEvaluator()` (`conformance_test.go:248,275,296,348`) but use the **same four
seams** as the committed vectors, so they reach no port function the committed corpus
does not already reach. Unlike the charges package — where direct probes inflated the
package-wide row and only the committed-store-only row was honest — here the two rows
coincide, so the honest "what the graded corpus reaches" figure is **3.3%** and it is
also the prescribed figure. There is no manufactured-coverage inflation in this package.

**Three port functions are reached** (`Total` `100.0%`, `TotalCollateral` `66.7%`,
`scaleFactor` `100.0%`); **26 are at `0.0%`** (full list in Appendix A).

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the holds case, each candidate is
checked against one question only:

> **Does the function implement a money rule?** If not — a getter, constructor,
> `String()`/codec, enum decoder, status predicate, validation-list lookup, repository
> accessor, or error constructor — it is out of scope for grading and stays at `0.0%`
> without being a gap.
>
> If it *does* implement a money rule: **does an observation behind it already exist in
> a committed capture?** If yes, name the file and the figures a vector would take (a
> grading run the driver can dispatch next). If no, say what a capture would need.

## 4. Triage of the `0.0%` candidates

### 4.1 Non-money classes — out of scope (24 of the 26)

| class | functions (`file:line`) |
|---|---|
| constructors | `collateral.go:34` `NewClientCollateral`; `collateral.go:83` `NewLoanCollateralLink`; `collateral.go:102` `NewLoanCollateral` |
| decimal codec (render / parse) | `money.go:26` `FormatDecimal`; `money.go:54` `ScaledIntFromText` |
| repository I/O (PostgreSQL accessors) | `postgres.go:28,34,51,97,102,113,137,161,184,189,201,230,259,280,285,296,321,346,355,362` |

The three constructors are ported by direct struct literal at the seam (the evaluator
builds `ClientCollateral`/`LoanCollateral`/`LoanCollateralLink` values), so they are
never entered by a read. `FormatDecimal`/`ScaledIntFromText` are the exact-integer
codec; they are exercised by the port's own unit tests
(`collateral_test.go:7,27`), i.e. by *direct port calls*, which is exactly the
manufactured coverage the brief excludes from the graded-corpus measurement. The twenty
`postgres.go` functions are row I/O; they need a live PostgreSQL integration test, not a
vector, and no capture can make them part of the graded corpus.

### 4.2 Money-rule candidate — `collateral.go:65` `UpdateQuantityAfterLoanClosed`

*Rule.* "The released quantity is returned to the holding" — it adds a scale-5
`quantity` to `ClientCollateral.Quantity` (`collateral.go:65-67`), the same quantity the
graded valuation multiplies by the base price. Integer minor units, no float. This is a
money rule, and it is the **only** `0.0%` function that is one.

*Observation.* **None, anywhere in the committed capture tree.**

* Why no observation: the two collateral capture directories
  (`.softhouse/capture/collateral/`, `.softhouse/capture/collateral-nonround-money/`)
  are read-backs of *products and live holdings*. A full-text scan of the capture tree
  for `released`/`Released` finds nothing; the loan captures carry `"collateral":[]`
  (`loan/out/loan-1-detail-raw.json`, `loan11-writeoff-four-bucket/out/loan-11-after-detail-raw.json`)
  and `parties/out/clients-1-raw.json` carries `"clientCollateralManagements":[]`. No
  capture shows a loan linked to a client holding, a loan closure, or a holding whose
  quantity rose by a released amount.
* **Stronger blocker — no seam reaches it.** The four graded seams are all reads:
  `collateral-product-read`, `collateral-link-read`, `collateral-client-read`,
  `collateral-valuation-read` (`.softhouse/maps/collateral.md`; the six vectors
  `CL-01..CL-06` use exactly these). The `CollateralEvaluator` interface exposes only
  `Evaluate` over those seams; no seam constructs a `LoanCollateralLink`, applies a
  release, or reads a post-release holding. So even a capture of the release event would
  grade **zero** until a release seam is added to the harness and the port's release path
  is wired to it. A vector cannot reach a function no seam calls — the loan
  (`F-2026-09-11-loan-graded-coverage.md` §4.3) and this are the same shape.

*What a capture would need (if the seam is ever added).* A client with a
`m_client_collateral_management` holding, a loan with a `m_loan_collateral_management`
link of a known `quantity` against that holding, the loan driven to closure (or
equivalent release), then read back: the holding's `quantity` after release (it must
equal the pre-release quantity **plus** the link quantity) and the link's `is_released`
/ `quantity` row. On tenant `gerege` (oracle `gerege-oracle-db`), the arithmetic is a
single integer addition, so the capture must expose the pre-release and post-release
quantities to be a usable observation.

### 4.3 Uncovered branch of a graded money rule — `collateral.go:56.16,58.3` (zero guard)

`TotalCollateral` (`collateral.go:55`) is graded to `66.7%`; the one uncovered block is
the `if total == 0 { return 0 }` early return (`collateral.go:56.16,58.3`, **0 hits**
in both runs). No committed vector has a zero total: `CL-04` has quantity `1.50000`
(base price `100000.00000`) and `CL-06` has quantity `2.50000` (base price
`41850.08000`), so `Total()` is nonzero on every graded observation. This branch is a
defensive guard, reachable only via a zero-quantity or zero-base-price holding, and no
such capture exists. It is low value to grade (the guard returns `0`, trivially) but it
is recorded here so a later reader does not mistake the `66.7%` for a fully graded rule.

## 5. Summary of triage

| candidate | `file:line` | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `UpdateQuantityAfterLoanClosed` | `collateral.go:65` | **yes** (release increments holding quantity) | **no** (no release row, no closed loan, empty `loanTransactionData` / `clientCollateralManagements` on every capture) | **needs capture + new seam** |
| `TotalCollateral` zero guard | `collateral.go:56.16,58.3` | branch of a money rule | **no** (no zero-quantity/zero-price holding) | low value; needs capture |
| `NewClientCollateral` | `collateral.go:34` | no (constructor) | n/a | not a rule |
| `NewLoanCollateralLink` | `collateral.go:83` | no (constructor) | n/a | not a rule |
| `NewLoanCollateral` | `collateral.go:102` | no (constructor) | n/a | not a rule |
| `FormatDecimal` | `money.go:26` | no (codec) | n/a | not a rule |
| `ScaledIntFromText` | `money.go:54` | no (codec) | n/a | not a rule |
| postgres repository accessors (20) | `postgres.go:28–362` | no (row I/O) | n/a | not a rule; needs a DB test |

**No candidate here is asserted to be a defect.** The evidence decides: the graded
valuation rule (`Total`/`TotalCollateral`) is already reached by `CL-04`/`CL-06`, and
`UpdateQuantityAfterLoanClosed` is ungraded because the harness has no seam for it at
all, not because the port is wrong.

## 6. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` issued.
* No vector and no drive was written. `.softhouse/vectors/collateral/` is unchanged
  (still `CL-01..CL-06`).
* No port code changed. `.softhouse/guards/` (12 pairs) and
  `.softhouse/conformance.sh` (census 17) are untouched.
* No gap was graded; the one money-rule candidate needs a seam before a capture can be
  graded.

## 7. Controls

* `go build ./...` — clean; `gofmt -l internal/apps/collateral/conformance/` — clean.
* `go test ./...` — all packages pass; the committed-store test passes `-count=1`.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `§4.4.2-RECORDED-DECISION-EXIT`; no `HARD guard failed`.
* `capcount.sh <wt> collateral collateral-go` → **0** (reference fails no vector).
* `redcount.sh <wt> collateral` → **8** registered `collateral-wrong-*` drives, every
  one kills at least one vector.
* `kills.sh collateral collateral-wrong-base-price-hardcoded <wt>` → **1** (still kills,
  as before; zero would mean the new test broke the measurement).
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <wt>` → **45** (control).
* `kills.sh parties parties-wrong-iota-ordinals <wt>` → **12** (control).
* `collateral-go` on the committed store: `vectors_loaded=6 parity_pass=6 parity_fail=0`.

## Appendix A — all 26 functions at `0.0%` in the prescribed run

`file:line` are lines in each file. The committed-store-only run has the identical set.

- `collateral.go:34` `NewClientCollateral`
- `collateral.go:65` `UpdateQuantityAfterLoanClosed`
- `collateral.go:83` `NewLoanCollateralLink`
- `collateral.go:102` `NewLoanCollateral`
- `money.go:26` `FormatDecimal`
- `money.go:54` `ScaledIntFromText`
- `postgres.go:28` `NewPostgresCollateralProductRepository`
- `postgres.go:34` `Upsert`
- `postgres.go:51` `FindByID`
- `postgres.go:97` `NewPostgresClientCollateralRepository`
- `postgres.go:102` `Insert`
- `postgres.go:113` `FindByID`
- `postgres.go:137` `FindByClientID`
- `postgres.go:161` `UpdateQuantity`
- `postgres.go:184` `NewPostgresLoanCollateralLinkRepository`
- `postgres.go:189` `Insert`
- `postgres.go:201` `FindByID`
- `postgres.go:230` `FindByLoanID`
- `postgres.go:259` `MarkReleased`
- `postgres.go:280` `NewPostgresLoanCollateralRepository`
- `postgres.go:285` `Insert`
- `postgres.go:296` `FindByID`
- `postgres.go:321` `FindByLoanID`
- `postgres.go:346` `Update`
- `postgres.go:355` `nullIfZero`
- `postgres.go:362` `nullIfEmpty`
