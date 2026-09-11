# F-2026-09-11 — the `origination` graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written. This run makes the `origination` corpus *measurable* and triages the result; the
committed-store control it added is committed (`7e846fdd`). Grading anything this finding
names is a later run's work, and for `origination` that is a larger dispatch than the usual
vector promotion — see §5.5.
**Task:** `OH-ORIGCOV-AT`, bounded context `origination`, branch `feat/OHORIGCOVat`.
**Found by:** Go coverage of the `origination` port, measured with the port as `-coverpkg`
and the **conformance package** as the test target — the instrument the driver validated on
the savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`), the loan corpus
(`F-2026-09-11-loan-graded-coverage.md`) and the charges cap clamp
(`F-2026-09-11-charges-graded-coverage.md`), not the grep it replaced.

## 1. The missing control, added

The map said the `origination` committed-store test was **ABSENT**, so coverage measured
from conformance meant nothing: without a store-driven test in the package, no vector can
move the number and every port function reads `0.0%` no matter how many vectors exist.

Added `nexus/internal/apps/origination/conformance/committed_store_test.go` (commit
`7e846fdd`), modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` (`conformance/vector.go`) →
  `Admit` (`conformance/admit.go`) → `Run` (`conformance/grade.go`) against the reference
  `origination-go`, exactly as the grading binary does;
* it **calls no port function directly** — it grades through
  `NewGoEvaluator().Evaluate` (`conformance/impl.go:103`), whose only port call is
  `StoredValue` (`status.go:31`), reached *through the vectors*; the coverage is real, not
  manufactured;
* anti-vacuity: it fails if the store loads zero vectors, and asserts every loaded vector is
  admissible, `Run` is not fatal, `VectorsLoaded != 0`,
  `parity_fail + refused + inadmissible + errored == 0`, and `invariant_violations == 0`;
* it pins the one graded seam (`SeamLoanOriginatorStatus`, `conformance/vector.go:28`) and
  asserts the corpus still carries all three loan-originator-status names
  (`committed_store_test.go:106`), so a later deletion of a vocabulary member is a failing
  test rather than a silent return to `0.0%`.

The committed corpus passes the reference:

    go run ./internal/apps/origination/conformance/cmd/conformance -root ..
    → VERDICT: PASS (exit 0)
      vectors_loaded=3 parity_pass=3 parity_fail=0 refused=0 inadmissible=0
      harness_error=0 graded_cells=3 invariant_violations=0
      nofloat: packages=48 files=392 tokens=406572 imports=1161 violations=0

**The control adds zero coverage delta here** — a fact worth stating plainly, because the
loan and charges findings both show a delta. All three profiles in §2 are byte-identical
(`md5 d702983b064b4f12a0a77bc4fcac5329`): the package's `conformance_test.go` probes already
drive `NewGoEvaluator()`/`Evaluate` directly (`conformance_test.go:118,131,155,164,176,185`)
and therefore already reach the *same two* functions the vectors reach — `StoredValue` and
`String` — and no function beyond them. There is no manufactured coverage here to
discount; the control is still required as the valid instrument and the anti-vacuity guard,
but it does not move the number. This is a real difference from charges, where the
package-wide reading (57.5%) was inflated well above the honest vector-only reading (41.2%).

## 2. Measurement

The prescribed command (from `nexus/`):

    go test -count=1 -coverpkg=./internal/apps/origination \
        -coverprofile=/tmp/c.cov ./internal/apps/origination/conformance/...
    go tool cover -func=/tmp/c.cov | awk '$3=="0.0%"'

| run | test target | statements | total | functions at 0.0% | profile md5 |
|---|---|---:|---:|---:|---|
| before (control file temporarily absent) | whole conformance package | 126 | 2.4% | 36 | `d702983b…` |
| **prescribed** (control present) | whole conformance package | 126 | **2.4%** | **36** | `d702983b…` |
| **vector-only** (control alone, all probes filtered out) | `-run '^TestCommittedCorpusPassesTheReferenceImplementation$'` | 126 | **2.4%** | **36** | `d702983b…` |

**Which reading is honest.** The **vector-only** row is the honest "what the graded corpus
reaches" figure, and it is the one this finding triages. In `origination` it coincides with
the prescribed package-wide figure because the package's other tests call `NewGoEvaluator()`
only to produce the *same* `Evaluate` path the vectors produce, so the two readings are the
same byte-for-byte (`md5 d702983b064b4f12a0a77bc4fcac5329` for all three). Unlike charges,
there is no gap between them; the prescribed number is not inflated. All three rows reduce
to **3 of 126 statements** covered:

* `status.go:31.52,31.73` — `StoredValue`, the port function the seam exists to grade;
* `status.go:33.47,34.42` — the map-hit arm of `String`;
* `status.go:34.42,36.3` — the `return n` of that arm.

Everything else in the port — 123 statements across `mapping.go`, `originator.go`,
`postgres.go`, `reconcile.go` and the rest of `status.go` — is at `0.0%`.

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the holds/loan/charges cases, each
candidate is checked against one question only:

> **Does the function implement a money rule?** If not — a getter, `String()`, enum
> decoder, status predicate, validation-list lookup, error constructor, factory or
> repository method — it is out of scope for grading and stays at `0.0%` without being a
> gap.
>
> If it *does* implement a money rule: **does an observation behind it already exist in a
> committed capture?** If yes, name the file and the figures a vector would take (a grading
> run the driver can dispatch next). If no, say what a capture would need.

### Corpus scope, and the standing no-money answer

The graded `origination` corpus is the **3 vectors** in `.softhouse/vectors/origination/`
(`OR-01-active.json`, `OR-02-pending.json`, `OR-03-inactive.json`). All three transcribe the
one committed capture `.softhouse/capture/origination/out/loan-originators-template-raw.json`
(GET `/loan-originators/template`, tenant `gerege`, `sha256 59d4a563…`), and all three grade
the one seam `origination-loan-originator-status`.

There is no money in this bounded context, by the registry's own declaration, twice over:

* `.softhouse/capabilities-origination.json` `note`: *"No money, minor-unit, or rounding
  surface exists in this context; the only graded cell is the stored status string."*
* `.softhouse/capture/origination/MANIFEST.json` `roundingSurface`: *"none — this context
  carries no money … No minor-unit, rounding or currency surface exists."*

So the money-rule filter returns **zero** candidates by construction, and no `0.0%` function
is a money gap. That is not a dodge: it is the registry's own scoping. The triage below
still classifies all 36 and then answers the stronger question this context poses — what
*rule* (money or not) does the corpus never reach, and can a vector ever reach it.

## 4. Triage of the 36 `0.0%` candidates

`file:line` are lines in each file. All 36, classified:

| class | count | functions (`file:line`) |
|---|---:|---|
| PostgreSQL repository (persistence) | 22 | `postgres.go:20,27,51,56,69,75,80,107,118,140,145,155,160,164,182,207,212,222,227,231,249,257` |
| typed error constructors | 4 | `reconcile.go:18,30,41,52` |
| linking rule set (behavioural rules) | 4 | `reconcile.go:60,77,87,98` |
| aggregate factories / mutator | 4 | `originator.go:27,39`; `mapping.go:14,31` |
| status predicate / enum decoder | 2 | `status.go:43,48` |

**Money rules found among the candidates: 0.** §3 gives the standing reason.

The excluded classes, briefly:

* **`postgres.go` (22 functions)** — `nullString:20`, `nullInt64:27`, `int64Value:257`, the
  two repository constructors (`:51,:140,:207`), and `Insert`/`FindByID`/`FindByExternalID`/
  `findOne`/`Update`/`Delete`/`find` in three families. Persistence over
  `m_loan_originator` / `m_loan_originator_mapping` / `m_wc_loan_originator_mapping`; not a
  rule surface, requires a live database, and unreachable from the pure conformance path.
* **`reconcile.go:18,30,41,52`** — `Error()` methods on the four typed rule outcomes
  (`ErrOriginatorNotActive`, `ErrLoanNotSubmitted`, `ErrMappingAlreadyExists`,
  `ErrOriginatorCannotBeDeleted`). Error constructors; excluded.
* **`originator.go:27` `NewLoanOriginator`** — create factory. It does carry a *default*
  (newly created originators are ACTIVE, `originator.go:31`), but it is a factory default,
  not a callable rule surface under the seam; it is exercised only by the unit test
  `TestNewLoanOriginatorDefaultsActive` (`origination_test.go:35`).
* **`originator.go:39` `Update`** — aggregate field mutator; no rule.
* **`mapping.go:14,31`** — mapping factories; no rule.
* **`status.go:43` `IsActive`** — status predicate; unit-tested at `origination_test.go:30`.
* **`status.go:48` `LoanOriginatorStatusFromString`** — enum decoder (the inverse direction);
  unit-tested at `origination_test.go:8`. See §6.

## 5. The finding — the linking rule set the corpus never reaches, and cannot under the declared seam

### 5.1 The rule set

`doc.go:8-24` calls this *"the testable core (the part Fineract ships as ~1,657 test LOC)"*.
It is four rule functions plus the four typed outcomes they return:

* `reconcile.go:60` `ValidateAttach(loanID, loanSubmittedAndPendingApproval, loanStatusName, originator, mappingExists)`
  — loan must be `SUBMITTED_AND_PENDING_APPROVAL`, originator must be ACTIVE, the mapping
  must not already exist (`doc.go:13-19`; Fineract
  `LoanOriginatorWritePlatformServiceImpl.java:196-216`).
* `reconcile.go:77` `ValidateDetach(loanSubmittedAndPendingApproval, loanID, loanStatusName)`
  — detach only while submitted-and-pending (Fineract `…Impl.java:228-233`).
* `reconcile.go:87` `ValidateDelete(originatorID, hasMappings)` — a mapped originator cannot
  be deleted (Fineract `…Impl.java:179-183`).
* `reconcile.go:98` `ReconcileMappings(currentOriginatorIDs, requestedOriginatorIDs)` — the
  disbursement delta that drives the loan's mapping set to exactly the requested set
  (Fineract `LoanOriginatorLinkingServiceImpl.java:102-138`).

These are real behavioural rules — the only non-money rules in the port — and all four are
`0.0%` from the graded corpus. They are, however, **already unit-tested**:
`TestValidateAttachRuleChain` (`origination_test.go:49`),
`TestValidateDetachAndDelete` (`origination_test.go:80`) and
`TestReconcileMappings` (`origination_test.go:95`).

### 5.2 Why they are `0.0%` — structurally unreachable, not merely ungraded

Unlike the charges cap clamp, this is not a case of a vector being absent while the seam
could express one. The declared seam **cannot** express a linking vector at all:

* `Admit` refuses any oracle whose seam is not `SeamLoanOriginatorStatus`
  (`conformance/admit.go:39-41`); that is the only admitted seam
  (`conformance/vector.go:28`).
* The vector request schema is a single field, `Request{Name string}` (`vector.go:76-77`),
  and the expected value is a single stored string, `Expect{Stored string}` (`vector.go:85-86`).
  There is no field for a loan status, an originator status, mapping existence, or id sets.
* The reference evaluator's whole behaviour is name→stored string
  (`conformance/impl.go:103-108`); it never calls `ValidateAttach`, `ValidateDetach`,
  `ValidateDelete` or `ReconcileMappings`. Neither do the wrong drives
  (`impl.go:117,141`) — `origination-wrong-default-active` re-implements a constant at the
  *evaluator* level, it does not exercise `NewLoanOriginator`.

So a vector of the existing shape, however many are promoted, will reach these functions
zero times. They are `0.0%` because the graded domain was declared as the status vocabulary
only.

### 5.3 Observation: ABSENT in every committed capture

Even if a seam existed, there is no committed observation of an attachment to grade. Checked
across the whole committed capture tree (`.softhouse/capture/`):

* Every `"originators"` array is **empty** — `loan/out/loan-1-detail-raw.json`,
  `tierA-a2/out/A2-336-loan-state-after-disburse.json`,
  `t388-accrual-capture/out/T388-A07-loan-8-readback-after-accrual.json`,
  `workingcapital/out/wc-loan-detail-raw.json`, and the rest. No `originatorId` key occurs
  anywhere in `.softhouse/capture/`. No loan in the corpus has an originator attached.
* `capture/origination/out/m-loan-originator-readback-raw.json` is **1 byte** (a newline),
  and its `.status` is `0` — the only attempt to read an originator back captured nothing.
* `capture/t417-scheduler-attribution/witness/*.tsv` record, in every probe and both
  boundaries, `tbl m_loan_originator 0 EMPTY`, `tbl m_loan_originator_mapping 0 EMPTY`,
  `tbl m_wc_loan_originator_mapping 0 EMPTY`, and `m_loan_originator_id_seq`,
  `m_loan_originator_mapping_id_seq`, `m_wc_loan_originator_mapping_id_seq` all `unset`.
* The only `originator`-named capture content is the template catalogue
  (`loan-originators-template-raw.json`): `statusOptions`, `originatorTypeOptions`,
  `channelTypeOptions`, and the pinned-source note `loan-originator-status-source.txt`. That
  is the status vocabulary, not an attachment. `capture/out/t35-rc6-gerege-configurations.json`
  only enables `enable-originator-creation-during-loan-application`.

This matches the MANIFEST's scope: the committed `origination` capture was taken for the
vocabulary alone. There is no capture of an originator create, attach, detach, delete or
disbursement reconcile.

### 5.4 What a grading run would need — a capture *and* a seam extension

Because §5.2 and §5.3 are independent blockers, grading the linking rules is not a
vector-promotion like the charges cap clamp. It needs both:

1. **A capture** exercising the oracle's rules: create an originator
   (`POST /loan-originators`) and read it back; attach it to a loan in
   `SUBMITTED_AND_PENDING_APPROVAL`; attempt an attach of a PENDING/INACTIVE originator
   (expect refusal); attempt a duplicate attach (expect refusal); attempt detach on a
   non-submitted loan (expect refusal); attempt to delete a mapped originator (expect
   refusal); and a disbursement whose reconcile drives the mapping set to a requested set —
   each with the readback that makes the rule observable. No POST/PUT/DELETE may be issued
   by this run.
2. **A seam and schema extension**: a new `Seam` constant, a new capability registered
   `in_graded_domain`, a `Request`/`Expect` shape that can carry the loan status, originator
   status, `mappingExists`/`hasMappings`, and the current/requested id sets, an evaluator arm
   for each rule, and `Admit` widened to the new seam (`admit.go:39`). Without this, the
   linking rules remain ungradeable regardless of how many captures exist.

The same two gaps apply to the aggregate default (`NewLoanOriginator` → ACTIVE,
`originator.go:27-34`): it is implemented and unit-tested, but the seam has no originator
construction and no committed capture creates one.

### 5.5 Verdict

**Implemented, unit-tested, unobserved, and ungradeable under the declared seam — not a
defect.** The `origination` port reaches exactly what the registry declares gradeable (the
name→stored-string mapping), and nothing in the committed corpus reaches the rest. This is
the strongest form of "what it never reaches": it is a scoping fact about the bounded
context, recorded here, not a bug. The driver can dispatch a capture-and-seam run later if
the linking rule set is wanted in the graded domain; this triage run takes no capture,
writes no vector, registers no drive and changes no port.

## 6. Secondary observations (recorded, not gaps)

* `status.go:48` `LoanOriginatorStatusFromString` is `0.0%`. The graded seam is
  one-directional (name → stored string), so no vector calls the inverse decoder; the
  corpus also never supplies an out-of-vocabulary name. It is an enum decoder (excluded
  class) and is unit-tested (`origination_test.go:8`).
* `status.go:37.2,37.58` — the `String()` fallback for an unknown ordinal — is unreachable
  from the corpus (the admitted names are exactly the three known ones), which is why
  `String` reads `66.7%` rather than `100.0%`. Same class: a formatting fallback, not a
  rule.
* `status.go:43` `IsActive` is a status predicate, unit-tested (`origination_test.go:30`),
  and not reachable from the name→stored seam.

## 7. Summary of triage

| question | answer |
|---|---|
| money rules among the 36 `0.0%` candidates | **0** — the registry declares no money surface |
| `0.0%` behavioural rules the corpus never reaches | **4** — `reconcile.go:60,77,87,98` (linking rule set), plus the aggregate default `originator.go:27` |
| observation behind them in a committed capture | **none** — every `originators` array is empty; all three originator tables `EMPTY`; sequences `unset`; the sole readback is 1 byte |
| gradeable by promoting vectors under the current seam | **no** — `Admit` admits one seam and the `Request` schema is `{name}`; a vector cannot express an attachment |
| what is required | a **capture** of the oracle's attach/detach/delete/reconcile rules **and** a **seam + schema extension** (§5.4) |
| defect? | **no** — implementation and unit tests exist; the graded domain is deliberately the status vocabulary |

## 8. What this run did NOT do

* No capture was taken; no POST/PUT/DELETE was issued.
* No vector, drive or port change was made.
* No `0.0%` function was called a defect. The linking rule set is reported as ungraded and
  structurally unreachable under the declared seam, with the evidence that decides it.
* No coverage was manufactured: the committed-store control calls the port only through
  `Evaluate`, and the vector-only and package-wide profiles are byte-identical, so the
  honest and prescribed numbers coincide.

## 9. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass (exit 0); the committed-store control passes
  `-count=1`.
* `bash .softhouse/conformance.sh` — **exit 2**, and the only exit line is
  `§4.4.2-RECORDED-DECISION-EXIT` (line 1394); `HARD guard failed` count **0**.
* `kills.sh origination origination-wrong-default-active` → **2**;
  `kills.sh origination origination-wrong-swap-status` → **2**. Every `origination` drive
  still kills.
* Controls unchanged: `kills.sh loanschedule loanschedule-wrong-days-in-year-365` → **45**;
  `kills.sh parties parties-wrong-iota-ordinals` → **12**.
* `redcount.sh origination` → **2**; `capcount.sh origination origination-go` → **0**
  (the reference fails no committed vector).
* `origination-go` on the committed store: `vectors_loaded=3 parity_pass=3 parity_fail=0`.

## Appendix A — all 36 functions at `0.0%` (prescribed = vector-only)

`file:line` are lines in each file, relative to
`nexus/internal/apps/origination/`.

- `mapping.go:14` `NewLoanOriginatorMapping`
- `mapping.go:31` `NewWorkingCapitalLoanOriginatorMapping`
- `originator.go:27` `NewLoanOriginator`
- `originator.go:39` `Update`
- `postgres.go:20` `nullString`
- `postgres.go:27` `nullInt64`
- `postgres.go:51` `NewPostgresLoanOriginatorRepository`
- `postgres.go:56` `Insert`
- `postgres.go:69` `FindByID`
- `postgres.go:75` `FindByExternalID`
- `postgres.go:80` `findOne`
- `postgres.go:107` `Update`
- `postgres.go:118` `Delete`
- `postgres.go:140` `NewPostgresLoanOriginatorMappingRepository`
- `postgres.go:145` `Insert`
- `postgres.go:155` `FindByLoanID`
- `postgres.go:160` `FindByOriginatorID`
- `postgres.go:164` `find`
- `postgres.go:182` `Delete`
- `postgres.go:207` `NewPostgresWorkingCapitalLoanOriginatorMappingRepository`
- `postgres.go:212` `Insert`
- `postgres.go:222` `FindByLoanID`
- `postgres.go:227` `FindByOriginatorID`
- `postgres.go:231` `find`
- `postgres.go:249` `Delete`
- `postgres.go:257` `int64Value`
- `reconcile.go:18` `Error` (`ErrOriginatorNotActive`)
- `reconcile.go:30` `Error` (`ErrLoanNotSubmitted`)
- `reconcile.go:41` `Error` (`ErrMappingAlreadyExists`)
- `reconcile.go:52` `Error` (`ErrOriginatorCannotBeDeleted`)
- `reconcile.go:60` `ValidateAttach`
- `reconcile.go:77` `ValidateDetach`
- `reconcile.go:87` `ValidateDelete`
- `reconcile.go:98` `ReconcileMappings`
- `status.go:43` `IsActive`
- `status.go:48` `LoanOriginatorStatusFromString`
