# F-2026-09-11 — the `parties` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written, no port code changed. This run makes the parties corpus *measurable* and
triages the result. Grading any gap it finds is a later run's work, after a capture if
one is needed.
**Task:** `OH-PTCOV-AN`, bounded context `parties`, branch `feat/OHPTCOVan`.
**Found by:** Go coverage of the parties port, measured with the port as `-coverpkg` and
the **conformance package** as the test target — the instrument the driver validated on
the savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`), the loan corpus
(`F-2026-09-11-loan-graded-coverage.md`) and the charges corpus
(`F-2026-09-11-charges-graded-coverage.md`), not the grep it replaced.

## 1. The missing control, added

The map recorded the parties committed-store test as **ABSENT**, so coverage measured
from conformance meant nothing: the only tests in the package were
`conformance_test.go`'s probes, and a probe that builds `NewGoEvaluator()` and calls
`Evaluate` directly is the manufactured reach the brief forbids.

Added `nexus/internal/apps/parties/conformance/committed_store_test.go` (commit
`623760d7`), modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against
  the reference `parties-go`, exactly as the grading binary does
  (`conformance/vector.go` `LoadStore`, `conformance/admit.go` `Admit`,
  `conformance/grade.go` `Run`);
* it **calls no port function directly** — every statement it reaches is reached
  *through the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors, and asserts every loaded
  vector is admissible, `Run` is not fatal, `VectorsLoaded != 0`,
  `parity_fail + refused + inadmissible + errored == 0`, and
  `invariant_violations == 0`;
* it guards the observation dimension: the test fails if any of the three enum seams
  (`client-status-ordinal`, `legal-form-ordinal`, `grouping-status-ordinal`) loses every
  committed vector, so deleting a vocabulary's vectors is a failing test rather than a
  silent return to `0.0%` graded coverage of that ordinal table.

The committed corpus passes the reference:

    go run ./internal/apps/parties/conformance/cmd/conformance -root ..
    → VERDICT: PASS (exit 0)
      vectors_loaded=16 parity_pass=16 parity_fail=0 refused=0 inadmissible=0
      harness_error=0 graded_cells=16 invariant_violations=0
      nofloat: packages=48 files=386 tokens=402683 imports=1137 violations=0

The 16 committed vectors split across the three seams as: client-status 8 (`CS-01..08`),
legal-form 2 (`LF-01..02`), grouping-status 6 (`GS-01..06`).

## 2. Measurement

The prescribed command (from `nexus/`):

    go test -count=1 -coverpkg=./internal/apps/parties \
        -coverprofile=/tmp/c.cov ./internal/apps/parties/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

| run | test target | statements | coverage | functions at 0.0% |
|---|---|---:|---:|---:|
| no control (control file temporarily absent) | whole conformance package | — | 6.4% | 60 |
| **prescribed** (control present) | whole conformance package | — | **6.4%** | **60** |
| **vector-only** (control alone, probes filtered out) | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | — | **6.4%** | **60** |

Two readings are reported because the package contains *both* the store-driven control
and `conformance_test.go`, whose probes construct `NewGoEvaluator()` and grade hand-built
vectors **by calling the port directly** (`conformance_test.go:180,189,234,264,274`,
the `gradeOne` and direct `NewGoEvaluator().Evaluate` calls). That probe coverage is
exactly the manufactured kind the brief
forbids. The **vector-only** row is the honest "what the graded corpus reaches" number;
the prescribed package-wide row is the command the brief specifies and is the one to
compare against future changes.

**Why the two numbers coincide here (unlike charges).** In `charges` the probes reached
fifteen extra port functions through direct calls. In `parties` the probe path and the
vector path are the *same* path: `NewGoEvaluator().Evaluate` → `goEvaluator.Evaluate` →
each vocabulary's `StoredValue()` (`conformance/impl.go:122-145`). No port function is
reached by a probe that a vector does not also reach, so the coefficient is the same
`6.4%` / `60` in all three rows. The vector-only row is still the honest one *by
construction*; it merely happens to have no probe-only functions to separate out.

**What the graded corpus does reach — only four functions.**

| function | `file:line` | coverage |
|---|---|---:|
| `ClientStatus.StoredValue` | `internal/apps/parties/clientstatus.go:58` | 75.0% |
| `GroupingTypeStatus.StoredValue` | `internal/apps/parties/group.go:46` | 75.0% |
| `LegalForm.StoredValue` | `internal/apps/parties/legalform.go:29` | 100.0% |
| `clientstatus.init` | `internal/apps/parties/clientstatus.go:93` | 75.0% |
| `group.init` | `internal/apps/parties/group.go:77` | 75.0% |

The three `StoredValue` methods and the two package `init`s that build their decode
tables are the entire reach of the twenty-four committed observations. Each seam's
`StoredValue` sits at 75% because the unknown-member `panic` arm
(`clientstatus.go:61`, `group.go:49`) is unreachable through `Admit`, which refuses an
out-of-vocabulary ordinal before evaluation. Everything else in the port reads `0.0%`.

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the holds case, each candidate is
checked against one question only:

> **Does the function implement a money rule?** If not — a getter, `String()`, enum
> decoder, status predicate, constructor, or error constructor — it is out of scope for
> grading and stays at `0.0%` without being a gap.
>
> If it *does* implement a rule: **does an observation behind it already exist in a
> committed capture?** If yes, name the file and the figures a vector would take (a
> grading run the driver can dispatch next). If no, say what a capture would need.

**`parties` grades no money.** Its capability registry states it outright: *"No money,
minor-unit, or rounding surface exists in this context; the only graded integer is the
enum ordinal"* (`.softhouse/capabilities-parties.json`), and the committed store's
manifest agrees — its `roundingSurface.seam` is `"none — this context carries no
money"`, *"No minor-unit, rounding or currency surface exists"*
(`.softhouse/capture/parties/MANIFEST.json`). The ordinary money-rule filter therefore
yields **zero** candidates: there is no arithmetic, no minor-unit fold, no rounding arm
in the port. The only in-scope candidates are the two CLAUDE.md non-negotiables the
brief extends scope to:

* **Names are three fields** — ovog (clan), patronymic, given name; never
  `first_name`/`last_name`.
* **National ID is 10 characters** — 2 Cyrillic letters + 8 digits; validate structurally.

## 4. Triage of the `0.0%` candidates

### 4.1 `internal/apps/parties/client.go:75` `DeriveDisplayName` — the name rule, NO complete observation → needs a capture and a seam

*Rule.* The three-field name derivation, ported from `Client.deriveDisplayName`
[Cited: Client.java:457-481]. `NewClient`
(`internal/apps/parties/client.go:54`) calls it. The rule has three arms:

* `client.go:76-79` — a non-blank `fullname` wins outright;
* `client.go:80-88` — otherwise, for a person (or unset legal form), present parts of
  `firstname`, `middlename`, `lastname` are space-joined, blanks skipped;
* `client.go:90` — an ENTITY contributes no parts and yields an empty display name.

This is the CLAUDE.md "names are three fields" non-negotiable in code. It is not
arithmetic, but the brief places it in scope for triage anyway.

*Why `0.0%`.* The vector contract has **no shape that can carry a name**. `Request` is
`{vocabulary, name}` → `Expect{ordinal}` (`internal/apps/parties/conformance/vector.go:126,135`),
and `Admit` refuses any `oracle.seam` outside the three ordinal seams
(`internal/apps/parties/conformance/admit.go:39-42`). No vector can reach
`DeriveDisplayName`, and neither can any registered drive: all four drives
(`parties-wrong-iota-ordinals`, `parties-wrong-legalform-person-as-unset`,
`parties-wrong-swap-active-pending`, `parties-wrong-transfer-states-swapped`) mutate the
name→ordinal maps and never construct a `Client`. The `0.0%` is structural, not a
missing vector.

*Observation.* **None for the two join arms, and no client three-part name anywhere in
the committed tree.**

* `clients-1-raw.json` (`GET /clients/1`, cited by `CS-03-active.json`) carries
  `fullname` = `displayName` = `"Path B Fixture Borrower"` — the **fullname-wins arm
  only** — and exposes **no `firstname`/`middlename`/`lastname`**.
* `m-client-readback-raw.json` (cited by `CS-03-active.json`) is a four-column read-back
  `{id, external_id, status_enum, legal_form_enum}` — **no name column at all**.
* The `firstname`/`lastname` in `clients-template-raw.json` and
  `groups-template-raw.json` are **staff** name parts rendered in Fineract's staff
  display format (`"Probe, SMOKE"`), not the Client derivation; they are cited by no
  vector and are not the rule in question.

*What a capture would need.* A client read-back that exposes the *separate* name parts
and the derived display name on the same row: e.g. a read-only select of
`m_client.firstname, middlename, lastname, fullname, display_name, legal_form_enum`, or
a `GET /clients/{id}` on a client whose parts are distinct — for **three rows**: distinct
non-blank parts (person join), a blank middle part (blank-skip), and an ENTITY (empty).
`clients-1-raw.json` already proves the fullname-wins arm, so only the other two arms
need new observations. Grading also requires a **schema/seam extension**: `Request` needs
to carry name parts, `Expect` needs a display-string cell, and a fourth seam would have
to be admitted by `Admit`/`IsSchemaSeam` — none of which this run may add. **Candidate;
not a defect.**

### 4.2 National ID — **no function implements it**, so there is no `0.0%` to triage

The CLAUDE.md rule ("10 characters — 2 Cyrillic letters + 8 digits; validate
structurally") is in scope under the brief's parties-specific clause **only if a `0.0%`
function implements it**. It does not:

* The map's port-function list for `parties` names no national-ID validator
  (`.softhouse/maps/parties.md`, "Port functions"); every listed function is an
  ordinal encode/decode, a status predicate, a display-name derivation, a group-level
  helper, or a Postgres adapter.
* A case-insensitive scan of `nexus/internal/apps/parties/` for
  `national|registration|nin|check.digit` finds no validator (only incidental
  substrings such as `OfficeJoiningDate`).
* A scan of the whole `nexus/internal/` tree for `NationalID` / `NationalId` /
  `national_id` finds **no symbol at all**.

So the national-ID rule has no implementing function to reach `0.0%`, and there is
nothing to grade. Recorded as an observation for the driver — the parties port does not
carry the rule — **not** as a defect and **not** as a coverage gap. If the driver wants
parties to own the rule, that is a port-authoring task, and it would need its own seam
and capture (the ID is not in any committed parties capture either: the read-backs carry
only `id`, `external_id`, `status_enum`, `legal_form_enum`, `fullname`, `displayName`).

### 4.3 Not candidates (excluded classes)

The remaining 59 functions at `0.0%` (all but `DeriveDisplayName`) implement no rule the brief admits:

| class | functions (`file:line`) |
|---|---|
| enum `String()` / decoders | `clientstatus.go:66,76`; `group.go:54,63`; `legalform.go:31,40` |
| status predicates | `clientstatus.go:81,82,83,84,85,86,87,91`; `group.go:68,69,70,71,72,73`; `legalform.go:54,57,60` |
| client constructor / predicates | `client.go:54,94,97,100` |
| group rules / constructors / predicates | `group.go:98,107,111,115,142,158,159,160,161,162,165` |
| Postgres adapters | `postgres.go:30,46,78,83,88,92,109,116,180,185,202,210,217,250,268,273,294,301,308,315,322` |

* `NewGroup` (`group.go:142`) and `NewGroupLevel` (`group.go:98`) do encode the
  active/pending default and the Center/Group level classification, and
  `GroupLevel.IsCenter`/`IsGroup`/`IsIdentifiedByParentID` (`group.go:107,111,115`) test
  the level name. These are grouping rules, not money rules and not the name or ID
  non-negotiables; they are unit-covered by `parties_test.go:105-124` in the port package
  (which the prescribed conformance target does not run), and no committed vector or
  capture observes a `GroupLevel`. Out of scope for this triage.
* The Postgres adapters are unreachable through the pure-evaluator harness — the
  conformance path never touches a database — and no capture observes Go repository
  behaviour. They are persistence, not rules; `parties_test.go` and the module's
  integration surface, not the graded corpus, are their instrument.

## 5. Summary of triage

| candidate | `file:line` | in scope? | observation in corpus? | action |
|---|---|---|---|---|
| `DeriveDisplayName` (three-field name rule) | `internal/apps/parties/client.go:75` | **yes** (CLAUDE.md non-negotiable) | **no** — only the fullname-wins arm (`clients-1-raw.json`); no client name parts anywhere | needs capture **+ seam/schema extension** |
| national-ID validator | — | the rule is in scope | **no function implements it**; zero candidates | not a coverage gap |
| `NewClient` | `client.go:54` | no (constructor) | n/a | out of scope |
| client predicates | `client.go:94,97,100` | no | n/a | out of scope |
| enum decoders / `String()` | `clientstatus.go:66,76`; `group.go:54,63`; `legalform.go:31,40` | no | n/a | out of scope |
| status predicates | `clientstatus.go:81-91`; `group.go:68-73`; `legalform.go:54,57,60` | no | n/a | out of scope |
| group level / group rules | `group.go:98,107,111,115,142,158-165` | no (not money/name/ID) | no | out of scope |
| Postgres adapters | `postgres.go:30-322` (21) | no (persistence) | no | out of scope |

**No candidate here is asserted to be a defect.** The only rule with an implementing
`0.0%` function that the brief puts in scope is the three-field name derivation in
`DeriveDisplayName`; it is implemented, has no complete committed observation, and no
vector *can* reach it under the current schema. The national-ID rule has no implementing
function at all, so it produces no candidate. The evidence, not this list, decides.

## 6. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued.
* No vector and no drive was written. `.softhouse/vectors/parties/` is unchanged.
* No port code changed, and no seam/schema was extended. `.softhouse/guards/`
  (12 pairs) and `.softhouse/conformance.sh` (census 17) are untouched.
* No gap was graded; a future run must capture *and* extend the schema/seam before the
  name rule can be graded at all.

## 7. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass; the committed-store test passes `-count=1`.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded
  run completed and the bar is refused by that recorded decision`. No
  `HARD guard failed`.
* `kills.sh parties parties-wrong-iota-ordinals <worktree>` → **12** (as before).
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <worktree>` → **45**.
* `redcount.sh <worktree> parties` → **4** (all four registered `parties-wrong-*` drives
  kill).
* `capcount.sh <worktree> parties parties-go` → **0** (the reference fails no vector).
* `parties-go` on the committed store: `vectors_loaded=16 parity_pass=16 parity_fail=0`.
* The new test passes on the current tree; its reach is vector-driven (measured with the
  other tests filtered out: 6.4% vector-only, identical to the prescribed run).

## Appendix — all 60 functions at `0.0%` in the prescribed run

`file:line` are lines in each file. This is the full set from
`go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'`; the vector-only run's set is
byte-identical.

- `internal/apps/parties/client.go:54` `NewClient`
- `internal/apps/parties/client.go:75` `DeriveDisplayName`
- `internal/apps/parties/client.go:94` `IsActive`
- `internal/apps/parties/client.go:97` `IsClosed`
- `internal/apps/parties/client.go:100` `IsNotActive`
- `internal/apps/parties/clientstatus.go:66` `String`
- `internal/apps/parties/clientstatus.go:76` `ClientStatusFromStoredValue`
- `internal/apps/parties/clientstatus.go:81` `IsPending`
- `internal/apps/parties/clientstatus.go:82` `IsActive`
- `internal/apps/parties/clientstatus.go:83` `IsClosed`
- `internal/apps/parties/clientstatus.go:84` `IsRejected`
- `internal/apps/parties/clientstatus.go:85` `IsWithdrawn`
- `internal/apps/parties/clientstatus.go:86` `IsTransferInProgress`
- `internal/apps/parties/clientstatus.go:87` `IsTransferOnHold`
- `internal/apps/parties/clientstatus.go:91` `IsUnderTransfer`
- `internal/apps/parties/group.go:54` `String`
- `internal/apps/parties/group.go:63` `GroupingTypeStatusFromStoredValue`
- `internal/apps/parties/group.go:68` `IsPending`
- `internal/apps/parties/group.go:69` `IsActive`
- `internal/apps/parties/group.go:70` `IsClosed`
- `internal/apps/parties/group.go:71` `IsTransferInProgress`
- `internal/apps/parties/group.go:72` `IsTransferOnHold`
- `internal/apps/parties/group.go:73` `IsUnderTransfer`
- `internal/apps/parties/group.go:98` `NewGroupLevel`
- `internal/apps/parties/group.go:107` `IsCenter`
- `internal/apps/parties/group.go:111` `IsGroup`
- `internal/apps/parties/group.go:115` `IsIdentifiedByParentID`
- `internal/apps/parties/group.go:142` `NewGroup`
- `internal/apps/parties/group.go:158` `IsActive`
- `internal/apps/parties/group.go:159` `IsPending`
- `internal/apps/parties/group.go:160` `IsClosed`
- `internal/apps/parties/group.go:161` `IsNotActive`
- `internal/apps/parties/group.go:162` `IsNotPending`
- `internal/apps/parties/group.go:165` `IsCenter`
- `internal/apps/parties/legalform.go:31` `String`
- `internal/apps/parties/legalform.go:40` `LegalFormFromStoredValue`
- `internal/apps/parties/legalform.go:54` `IsPerson`
- `internal/apps/parties/legalform.go:57` `IsEntity`
- `internal/apps/parties/legalform.go:60` `IsUnset`
- `internal/apps/parties/postgres.go:30` `NewPostgresClientRepository`
- `internal/apps/parties/postgres.go:46` `Insert`
- `internal/apps/parties/postgres.go:78` `FindByID`
- `internal/apps/parties/postgres.go:83` `FindByAccountNumber`
- `internal/apps/parties/postgres.go:88` `FindByExternalID`
- `internal/apps/parties/postgres.go:92` `findOne`
- `internal/apps/parties/postgres.go:109` `UpdateStatus`
- `internal/apps/parties/postgres.go:116` `scanClient`
- `internal/apps/parties/postgres.go:180` `NewPostgresGroupRepository`
- `internal/apps/parties/postgres.go:185` `Insert`
- `internal/apps/parties/postgres.go:202` `FindByID`
- `internal/apps/parties/postgres.go:210` `FindByAccountNumber`
- `internal/apps/parties/postgres.go:217` `findOne`
- `internal/apps/parties/postgres.go:250` `UpdateStatus`
- `internal/apps/parties/postgres.go:268` `NewPostgresGroupLevelRepository`
- `internal/apps/parties/postgres.go:273` `List`
- `internal/apps/parties/postgres.go:294` `nullInt`
- `internal/apps/parties/postgres.go:301` `nullStr`
- `internal/apps/parties/postgres.go:308` `nullTime`
- `internal/apps/parties/postgres.go:315` `valInt`
- `internal/apps/parties/postgres.go:322` `valTime`
