# F-2026-09-11 — the `provisioning` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** The missing control is committed (`43dac820`); this run
measures it and triages the result. No capture was taken, no `POST`/`PUT`/`DELETE` was
issued, no vector and no drive was written, no port code changed. Grading any candidate
this note names is a later run's work.
**Task:** `OH-PROVCOV-AH`, bounded context `provisioning`, branch `feat/OHPROVCOVah`.
**Found by:** Go coverage of the `provisioning` port, measured with the port as
`-coverpkg` and the **conformance package** as the test target — the instrument the driver
validated on the savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`), the loan
corpus (`F-2026-09-11-loan-graded-coverage.md`) and the charges corpus
(`F-2026-09-11-charges-graded-coverage.md`), not the grep it replaced.

## 1. The missing control, added

The map said the `provisioning` committed-store test was **ABSENT**, so coverage measured
from conformance meant nothing for this context: without a store-driven test in the
package, the number could not be attributed to the committed corpus.

Added `nexus/internal/apps/provisioning/conformance/committed_store_test.go` (commit
`43dac820`, 141 insertions), copied in shape from
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it resolves the store from the **module layout**, never the working directory
  (`committedStoreRoot` → `filepath.Join(repoRoot(t), ".softhouse", "vectors")` +
  `ProvisioningContext`), so `go test` grades the same corpus `conformance.sh` grades;
* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against the
  reference `provisioning-go`, exactly as the grading binary does (`conformance/vector.go`
  `LoadStore`, `conformance/admit.go` `Admit`, `conformance/grade.go` `Run`);
* it **calls no port function and does not import the port package** — every statement it
  reaches is reached *through the vectors* (verified: `grep -n 'internal/apps/provisioning"'
  conformance_test.go` → no direct import; the helper `repoRoot` lives in
  `conformance_test.go:37`);
* anti-vacuity: it fails if the store loads **zero** vectors
  (`committed_store_test.go:72-74`), asserts every loaded vector is admissible, `Run` is not
  fatal, `VectorsLoaded != 0`, `parity_fail + refused + inadmissible + errored == 0`, and
  `invariant_violations == 0`;
* it pins the two seams and the multi-entry (DISTINCT-KEY) observation
  (`committed_store_test.go:105-140`), so a later deletion of a seam or of the distinct-key
  observation is a failing test rather than a silent fall back to `0.0%`.

The committed corpus passes the reference:

    go test -count=1 -run '^TestCommittedCorpusPassesTheReferenceImplementation$' \
        ./internal/apps/provisioning/conformance/...
    → ok ... coverage: 56.8% of statements in ./internal/apps/provisioning

## 2. Measurement

The prescribed command (from `nexus/`):

    go test -count=1 -coverpkg=./internal/apps/provisioning \
        -coverprofile=/tmp/c.cov ./internal/apps/provisioning/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

Three readings were taken, because the package contains both the store-driven control and
`conformance_test.go`, whose probes construct `NewGoEvaluator()` and grade hand-built
vectors through the same evaluator:

| run | test target | statements | functions at 0.0% |
|---|---|---:|---:|
| probes-only (control file temporarily absent) | whole conformance package | 56.8% | 5 |
| **prescribed** (control present) | whole conformance package | **56.8%** | **5** |
| **committed-store-only** (probes filtered out) | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | **56.8%** | **5** |

The three `go tool cover -func` outputs are **byte-identical** (`diff` empty): the
probes-only, prescribed and committed-store-only profiles differ in **no** function. That is
the honest reading: unlike the charges package, where `conformance_test.go` calls the port
directly and manufactures reach, here the package's probes reach the evaluator (which
reaches the port) but reach **exactly the same port statements** the committed vectors
reach. So there is no manufactured coverage to discount, and 56.8% / 5 functions is the
corpus's true reach. The committed-store-only row is the one that answers "what the graded
corpus reaches"; the prescribed row is the command to compare against future changes; they
coincide.

Function-level, the package's entire reach:

| function | `file:line` | coverage |
|---|---|---:|
| `GenerateReserveEntries` | `entry.go:81` | 100.0% |
| `GenerateReserveEntriesWith` | `entry.go:88` | 92.3% |
| `PercentageOf` | `money.go:45` | 87.5% |
| `roundHalfAwayFromZero` | `money.go:65` | 83.3% |
| `Matches` | `criteria.go:29` | **0.0%** |
| `Overlaps` | `criteria.go:38` | **0.0%** |
| `ReserveRate` | `criteria.go:58` | **0.0%** |
| `OverlappingPairs` | `criteria.go:72` | **0.0%** |
| `ValidateRange` | `criteria.go:92` | **0.0%** |

The 56.8% total is low because the unreached `criteria.go` bodies are a large share of the
package's statements (14 uncovered blocks there; `entry.go` and `money.go` have only three
uncovered error/negative branches, section 7). **All five `0.0%` functions are in
`criteria.go`.** No money-arithmetic function reads `0.0%`.

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Each candidate is checked against one question only:

> **Does the function implement a money rule?** If not — a getter, `String()`, enum
> decoder, status predicate, validation helper, or error constructor — it is out of scope
> for grading and stays at `0.0%` without being a gap.
>
> If it *does* implement a money rule: **does an observation behind it already exist in a
> committed capture?** If yes, name the file and the figures a vector would take (a grading
> run the driver can dispatch next). If no, say what a capture would need.

The corpus scope is the 9 vectors in `.softhouse/vectors/provisioning/`, all class
`parity`, whose captures are `CAT-00`, `CRI-02` and `ENT-04` under
`.softhouse/capture/provisioning/out/`. No capture was taken by this run.

## 4. Triage of the `0.0%` candidates — all in `criteria.go`

`criteria.go` is the age-band machinery: the closed-interval membership predicate, the
band→rate selector, and the write-path overlap invariant. In the oracle all three are
**functions of the criteria DEFINITIONS**, and the graded reserve seam does not carry
definitions at all.

### 4.1 `criteria.go:58` `ReserveRate` and `criteria.go:29` `Matches` — money-affecting selection rule, OBSERVED but not representable → future grading run needs a seam, not a capture

*Rule.* `Matches` ports the oracle's join predicate
`pcd.min_age <= overdueInDays AND overdueInDays <= pcd.max_age`
(`criteria.go:22-31`, `[VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.java:75-77]`).
`ReserveRate` (`criteria.go:54-65`) walks a criteria's definitions and returns the single
one whose closed band contains the overdue age; `!ok` is the gap case the oracle's join
drops. Together they are the rule that maps an overdue age to the reserve percentage and
GL account pair — i.e. to **money** (the percentage is integer micro-per-cent, the accounts
are integers; no float). They are not getters, not `String()`, not status predicates and
not error constructors.

*Observation.* **Exists, and is committed.** The definitions are in
`.softhouse/capture/provisioning/out/CRI-02-criteria-1-raw.json`
(sha256 `fe372a96d8f358a1fc34999e3f76691dd5e133f8968d3637785db43e2a007c43`,
`criteriaId 1` "SEED-Probe-Criteria", loan product 2 "SEED-Probe-Loan"):

| definition id | categoryId / name | `minAge` | `maxAge` | `provisioningPercentage` | liability | expense |
|---:|---|---:|---:|---:|---:|---:|
| 3 | 1 STANDARD | 0 | 29 | 1.0 | 2 | 4 |
| 4 | 2 SUB-STANDARD | 30 | 59 | 25.0 | 2 | 4 |
| 2 | 3 DOUBTFUL | 60 | 89 | 50.0 | 2 | 4 |
| 1 | 4 LOSS | 90 | 36500 | 100.0 | 2 | 4 |

The *selected* band per overdue age is in the sibling capture
`.softhouse/capture/provisioning/out/ENT-04-entry-loan-products-raw.json`
(sha256 `96d596c24df85684c8d8fb1d204adddd9423f3ab101aedcaa890dd757b447ddb`), which is the
**already-cited primary evidence of 5 committed vectors** (PV-05..08 via
`provenance.capture_ref`, PV-09 via `expect_entries`):

| overdueInDays | observed categoryId | band from CRI-02 | percentage |
|---:|---:|---|---:|
| 0 | 1 STANDARD | [0,29] | 1.0 |
| 31 | 2 SUB-STANDARD | [30,59] | 25.0 |
| 62 | 3 DOUBTFUL | [60,89] | 50.0 |
| 92 | 4 LOSS | [90,36500] | 100.0 |

So the four oracle band-selection **decisions** are committed, and the definitions behind
them are committed. A `ReserveRate`/`Matches` vector would take the CRI-02 definitions above
plus an `overdue_in_days` from the left column and expect the matching definition's
`categoryId` / `provisioningPercentage` (micro-per-cent: `1.0 → 1000000`,
`25.0 → 25000000`, `50.0 → 50000000`, `100.0 → 100000000`) / liability `2` / expense `4`.

*Why it is still `0.0%`.* The harness's `Request` (`conformance/vector.go:99-103`) is the
**union of exactly two seams** — a category read (`category_id`) and an entry reserve
(`inputs`) — and neither can carry criteria definitions. The reserve seam supplies the
**already-matched** `Percentage`/`LiabilityAccount`/`ExpenseAccount` on each
`ReserveInputRow` (`conformance/vector.go:120-135`), because the oracle's storage mapper
hands the port the matched percentage (`entry.go:5-14`), not the definitions. The age→band
decision therefore happens *before* the graded observation, in SQL the port never sees.
`doc.go` states this explicitly: "the age-band matching rule (`Matches`/`ReserveRate`) …
[is] still not directly observable from a committed capture", and
`.softhouse/capabilities-provisioning.json` declares them **outside the graded domain**
(no criteria capability exists, so a vector requiring one is refused by default-deny).

*Verdict.* **Observed, ungraded, and not gradeable through the current instrument.** Unlike
the charges cap clamp — where the existing percentage-fee seam could carry two added inputs
— here the existing seams have no field for definitions, so grading needs (a) a new capture
seam `provisioning-criteria-read` with a capability (e.g. `criteria-band-definition`) marked
`exercised` and in the graded domain, evidenced by **CRI-02**, and (b) a new
`Request`/`Expect` shape carrying definitions + an overdue age. Both are port/schema changes,
out of scope for this measurement/triage run. **No new capture is needed** — CRI-02 already
observed the criteria read on the tenant — but the driver must confirm instance ownership
first (section 8). This is a candidate for a later grading run, not a defect.

### 4.2 `criteria.go:38` `Overlaps`, `criteria.go:72` `OverlappingPairs`, `criteria.go:92` `ValidateRange` — write-path validation invariant + error constructor, not money rules

*Rule.* `Overlaps` (`criteria.go:33-40`) ports
`ProvisioningCriteriaDefinition.isOverlapping` — two closed bands intersect.
`OverlappingPairs` (`criteria.go:67-82`) enumerates every `(i,j)` pair that overlaps.
`ValidateRange` (`criteria.go:89-101`) returns an error naming the first overlap, mirroring
`ProvisioningCriteriaAssembler.validateRange`. They guard the partition "one overdue age →
exactly one reserve rate"; they do not compute or select money themselves. `ValidateRange`
is an **error constructor** — an excluded class.

*Observation.* The **valid, non-overlapping** set is committed (CRI-02, four disjoint
bands), so the non-refusal path *could* be observed — calling `OverlappingPairs` on the
CRI-02 definitions reaches `Overlaps`, `OverlappingPairs` and the `return nil` arm of
`ValidateRange`. The **refusal** path (the `append` and the `fmt.Errorf`) is **not**
observed anywhere: CRI-02 is a valid criteria, and observing the oracle's
`ProvisioningCriteriaOverlappingDefinitionException` requires writing a **deliberately
overlapping criteria** to the shared tenant, which the capture contract forbids ("leave the
tenant exactly as found"). `doc.go` and the capability registry record this as the reason
the overlap invariant is out of the graded domain.

*Verdict.* Not money rules (validation/predicate/error-constructor classes). The
non-refusal path is observable from CRI-02 and would move three functions off `0.0%`
together with a criteria seam; the refusal branch needs a capture the contract prohibits,
so it stays out of domain. Candidate only.

## 5. The finding

**No `0.0%` function computes money arithmetic, and no `0.0%` function is a
capture-awaiting money rule.** The reserve arithmetic the context actually grades —
`GenerateReserveEntries` → `GenerateReserveEntriesWith` → `PercentageOf` →
`roundHalfAwayFromZero` — is reached by the committed vectors at 100% / 92.3% / 87.5% /
83.3%. The five unreached functions are the `criteria.go` age-band machinery. `Matches` and
`ReserveRate` implement the money-affecting age→rate rule and their observations **do**
exist in the committed captures CRI-02 and ENT-04, but the harness's two seams cannot
express them: a criteria seam plus a schema shape would be required, which this run must not
add. `Overlaps`/`OverlappingPairs`/`ValidateRange` are the overlap invariant and an error
constructor; their non-refusal path is observable from CRI-02 but their refusal path is
capture-contract-forbidden. **Nothing here is asserted to be a defect.**

This differs from the charges outcome (`MinimumAndMaximumCap`: implemented, observed,
ungraded, **gradeable with no capture and no seam change**). Provisioning's
observed-but-ungraded rule is blocked by a **missing seam**, so the dispatchable next step
is larger: extend the schema/registry, then promote a CRI-02-backed criteria vector.

## 6. Summary of triage

| candidate | `file:line` | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `Matches` | `criteria.go:29` | yes — age→band membership (the join predicate) | **yes** — CRI-02 definitions + ENT-04 selections | needs criteria seam + schema shape; no new capture |
| `ReserveRate` | `criteria.go:58` | yes — band→rate selector | **yes** — CRI-02 `provisioningPercentage`, ENT-04 `categoryId`/`overdueInDays` | needs criteria seam + schema shape; no new capture |
| `Overlaps` | `criteria.go:38` | no — overlap validation predicate | valid set: yes (CRI-02); refusal: no | out of domain for refusal |
| `OverlappingPairs` | `criteria.go:72` | no — validation enumeration | valid set: yes (CRI-02); refusal: no | out of domain for refusal |
| `ValidateRange` | `criteria.go:92` | no — error constructor | valid set: yes; refusal: no | out of domain for refusal |
| `GenerateReserveEntriesWith` error arm | `entry.go:94.17-96.4` | error path | n/a (no failing admissible vector) | not a gap |
| `PercentageOf` overflow arm | `money.go:53.18-55.3` | int64-overflow error | n/a (amounts bounded by `Admit`) | not a gap |
| negative half-round arm | `money.go:73.2-73.32` | negative-quotient branch | n/a (`Admit` rejects negative minor units) | not a gap |

**No candidate is asserted to be a defect.** The strongest candidate is the age→rate
mapping (`Matches`/`ReserveRate`): implemented, observed in CRI-02/ENT-04, and unreached
only because no seam carries definitions.

## 7. Other unreached code (not money rules)

Beyond `criteria.go`, only three blocks in the port are uncovered, all error or negative
branches unreachable for admissible vectors:

* `entry.go:94.17-96.4` — the `if err != nil { return nil, fmt.Errorf(...) }` arm of
  `GenerateReserveEntriesWith`. No admissible vector makes `PercentageOf` fail (all
  balances/percentages are bounded and non-negative), so the arm is unreachable.
* `money.go:53.18-55.3` — `PercentageOf`'s `!q.IsInt64()` int64-overflow error path.
* `money.go:73.2-73.32` — `roundHalfAwayFromZero`'s negative-quotient arm
  (`return q.Sub(q, big.NewInt(1))`). `Admit` rejects negative `balance_minor`, so no
  committed vector reaches it.

The `criteria.go` block detail (all 14 blocks, count 0):

    criteria.go:29.63,31.2   1 0     criteria.go:58.79,59.34  1 0
    criteria.go:38.69,40.2   1 0     criteria.go:59.34,60.31  1 0
    criteria.go:60.31,62.4   1 0     criteria.go:64.2,64.36   1 0
    criteria.go:72.55,74.42  2 0     criteria.go:74.42,75.47  1 0
    criteria.go:75.47,76.51  1 0     criteria.go:76.51,78.5   1 0
    criteria.go:81.2,81.14   1 0     criteria.go:92.41,93.51  1 0
    criteria.go:93.51,99.3   2 0     criteria.go:100.2,100.12 1 0

## 8. Map notes (things the map did not say)

* `.softhouse/capture/provisioning/` has **no `OWNER.md`**, and the OH-3 attestation and
  `.softhouse/PIN-provisioning.json` describe an **earlier** tenant state with
  `criteria|0 criteria_def|0` and list only `CAT-00, CRI-00, CRI-01, ENT-00, ENT-01`. The
  vectors' own evidence is the later `CRI-02` + `ENT-04` (criteria id 1 `SEED-Probe-Criteria`,
  product 2 `SEED-Probe-Loan`), so an earlier-instance warning does **not** apply to them,
  but the absence of an owner file means a future criteria seam must re-verify the instance
  before promoting CRI-02 as a seam capture.
* The map's vector list records one capture per vector (`PV-05..09` → `ENT-04`) and omits
  that the reserve vectors' *notes* also cite **CRI-02** as the source of the band
  percentages. `CRI-02` is therefore already corpus evidence even though the map's
  "captures this context's vectors already cite" section only names the directory.

## 9. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued.
* No vector and no drive was written. `.softhouse/vectors/provisioning/` is unchanged.
* No port code changed. `.softhouse/guards/` (12 pairs) and
  `.softhouse/conformance.sh` (census 17) are untouched (`git diff --stat` empty).
* No gap was graded; sections 4.1 and 4.2 name the seam/schema extension a later run would
  need, and what stays out of domain.
* `TASK.md` was not committed (untracked).

## 10. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass.
* `go test -count=1 -run '^TestCommittedCorpusPassesTheReferenceImplementation$'
  ./internal/apps/provisioning/conformance/...` — PASS.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
  completed and the bar is refused by that recorded decision`. No `HARD guard failed`;
  census 17 preserved.
* `kills.sh provisioning provisioning-wrong-blank-description <worktree>` → **4** (the drive
  still kills).
* `redcount.sh <worktree> provisioning` → **6** (all 6 provisioning drives kill).
* `capcount.sh <worktree> provisioning provisioning-go` → **0** (the reference fails no
  vector).
* `go tool cover -func` profiles for probes-only, prescribed and committed-store-only are
  byte-identical; the new test passes on the current tree.

---

## Appendix A — every function at `0.0%` in the prescribed run (5, all `criteria.go`)

- `criteria.go:29` `Matches`
- `criteria.go:38` `Overlaps`
- `criteria.go:58` `ReserveRate`
- `criteria.go:72` `OverlappingPairs`
- `criteria.go:92` `ValidateRange`

## Appendix B — uncovered blocks outside `criteria.go` (3, all error/negative)

- `entry.go:94.17-96.4` — `GenerateReserveEntriesWith` percentage-error arm
- `money.go:53.18-55.3` — `PercentageOf` int64-overflow error arm
- `money.go:73.2-73.32` — `roundHalfAwayFromZero` negative-quotient arm
