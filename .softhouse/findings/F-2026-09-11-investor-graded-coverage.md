# F-2026-09-11 — the investor graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written, no port code was changed. This run makes the `investor` corpus *measurable* and
triages the result. Grading anything it names is a later run's work.
**Task:** `OH-INVCOV-AS`, bounded context `investor`, branch `feat/OHINVCOVas`.
**Found by:** Go coverage of the investor port, measured with the port as `-coverpkg` and
the **conformance package** as the test target — the instrument the driver validated on
the savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`).

## 1. The missing control, added

The map said it plainly: `investor` had **no committed-store test**, so "coverage from
conformance is NOT meaningful for this context". That was true. Before this run, the
prescribed command reported **0.0% of statements** and **every one of the 21 port
functions at 0.0%** — not because the port is unexercised in general, but because no test
in the conformance package drove the *committed corpus* through the grading path, so no
vector could ever move the number.

Added `nexus/internal/apps/investor/conformance/committed_store_test.go`, modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against the
  reference `investor-go`, exactly as the grading binary does;
* it **calls no port function directly** — every statement it reaches is reached *through
  the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors; it asserts every vector is
  admissible, that the corpus passes, and that **both seams stay committed**
  (`external-asset-owner-transfer-read` and `external-asset-owner-transfer-settlement`),
  so deleting the only settlement vector is a failing test rather than a silent return of
  the derived-total rule to 0.0% coverage.

The committed corpus passes: `vectors_loaded=3 parity_pass=3 parity_fail=0 refused=0
inadmissible=0 harness_error=0`, `graded_cells=32 invariant_violations=0`
(`capcount.sh … investor investor-go` → 0).

## 2. Before / after, and which figure is honest

    go test -count=1 -coverpkg=./internal/apps/investor -coverprofile=/tmp/c.cov \
        ./internal/apps/investor/conformance/...

| run | statements | coverage | functions at 0.0% |
|---|---:|---:|---:|
| before (no committed-store test) | 143 | **0.0%** | **21 of 21** |
| after, package-wide (all conformance tests) | 143 | **0.7%** | **20 of 21** |
| after, committed-store-test-only (`-run TestCommittedCorpusPassesTheReferenceImplementation`) | 143 | **0.7%** | **20 of 21** |

**Both after figures are identical and both are honest.** Unlike the `charges` case — where
`conformance_test.go`'s direct port calls inflated the package-wide number and only the
committed-store-test-only figure was honest — here the two numbers agree exactly, and the
whole-corpus `go tool cover -func` output is byte-identical between the two runs (verified
with `diff`). The reason is checkable: running the *entire* conformance package without the
new test produced **0.0% for all 21 functions**. The probes in `conformance_test.go`
exercise the harness (`Admit`, `gradeOne`, `Lookup`, `AssertInvariants`), not the port;
they never enter `internal/apps/investor`. So the only thing that moves the instrument is
the committed corpus, and the reading is vector-driven.

The delta is one function, and it is narrow:

* `transfer.go:51` `DeriveTotalOutstanding` — `0.0% → 100.0%`, reached by `INV-03` (the
  settled transfer 28 details snapshot) through `toSettlementExpect` at
  `conformance/impl.go:278`.

The port's own unit tests (`internal/apps/investor/investor_test.go`) separately cover
`DeriveTotalOutstanding`, `StoredValue`, `MinorUnitsFromDecimalText`, `FormatDecimal` and
`OutstandingInterestStrategyFor`. They are **not run by the prescribed command** (the test
target is `.../conformance/...`), so the 0.0% below is a *conformance-vector* reading —
"no golden vector routes through this function" — not "this code has no test". That
distinction is the whole point of the triage.

## 3. Triage method, and the scope of the graded corpus

A `0.0%` is a **candidate, not a gap**. Following the loan/charges findings, each candidate
that implements a **money rule** (not a getter, a `String()`, an enum decoder, an attribute
decoder, a persistence method, an error constructor) is asked one question:

> **Does an observation behind it already exist in a committed capture?**

The **graded investor corpus** is the 3 vectors in `.softhouse/vectors/investor/` and the
captures they cite:

    .softhouse/capture/investor/out/transfer-read-loan-6-raw.json         (INV-01)
    .softhouse/capture/investor/out/transfer-read-loan-1-raw.json         (INV-02)
    .softhouse/capture/investor-asset-transfer-100/out/transfer-28-je-post.json (INV-03)

The two `capture/investor/` read captures are tenant `gerege` by their vector stamps, but
`capture/investor/` carries **no `OWNER.md`** (only `MANIFEST.json`, `out/`, `req/`); only
`capture/investor-asset-transfer-100/OWNER.md` names the instance explicitly (tenant
`gerege`, pinned commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`). Neither is an
early-instance `t*`/`A2-*` capture, so the map's earlier-instance warning does not bite
here, but the read captures' ownership is inferred, not stated.

The **only** money observation in the corpus is the settlement capture
`transfer-28-je-post.json`. Its figures (decimal → integer minor units at 2 digits) are:

    transferData.details
      totalPrincipalOutstanding  100000.000000  -> 10000000
      totalInterestOutstanding     6618.530000  ->   661853
      totalFeeChargesOutstanding    100.000000  ->    10000
      totalPenaltyChargesOutstanding 57.000000  ->     5700
      totalOutstanding            106775.530000  -> 10677553   (the oracle's stored sum)
      totalOverpaid                  0.000000  ->        0

    journalEntryData.content (10 entries, transactionId I28)
      amounts 100000.000000, 6618.530000, 100.000000, 57.000000,
              106775.530000, 100000.000000, 6618.530000, 100.000000, 57.000000, 106775.530000
      debit total 213551.060000 == credit total 213551.060000  -> 21355106 each

The read captures carry **no money** (the only decimal there is `purchasePriceRatio`
`"97.25"`, a ratio string, not a rendered amount).

## 4. Triage of the money-rule candidates

### 4.1 `transfer.go:58` `NormalizedTotalOutstanding` — OBSERVED but UNGRADED, and a wrapper over the graded rule

*Rule.* Returns the transfer-details total outstanding. The implementation is one line,
`return d.DeriveTotalOutstanding()` — it is a convenience wrapper around the rule that
`INV-03` already grades.

*Observation.* **Exists** — `transfer-28-je-post.json` `transferData.details` carries the
four buckets (100000.000000 / 6618.530000 / 100.000000 / 57.000000) and the stored total
106775.530000, exactly the input `NormalizedTotalOutstanding` folds.

*Why 0.0%.* The settlement seam calls `DeriveTotalOutstanding`, not this wrapper:
`conformance/impl.go:278` `TotalOutstandingMinor: int64(d.DeriveTotalOutstanding())`. No
vector `Expect` cell maps to the wrapper, so no vector can reach it as the harness stands.

*Verdict.* **Implemented, observed, ungraded — but low marginal value.** It is a one-line
delegation to the now-100% rule and returns the identical value; grading it would need a
one-line seam change (call `NormalizedTotalOutstanding` instead of `DeriveTotalOutstanding`
at `impl.go:278`) and would grade the wrapper, not a new money rule. Its doc says it
returns the derived total "when it differs from the stored total", but the body never
consults `d.TotalOutstanding`; because the port never stores an independent total, no
observation can make the two differ, so there is nothing to discriminate. **Not a gap and
not a defect**; recorded so the driver can decide. (The loan finding treated the analogous
one-line `AllocateCredit` wrapper the same way.)

### 4.2 `money.go:20` `FormatDecimal` — OBSERVED, but no vector-addressable cell

*Rule.* Renders an integer minor-unit count back into major-unit decimal text with exactly
`minorDigits` fraction digits (pure integer/string arithmetic; no float).

*Observation.* **Exists.** The settlement capture carries decimal-formatted money —
`106775.530000` (details total), the four buckets, and the ten journal amounts including
the `213551.060000` debit/credit totals. `FormatDecimal(10677553, 2)` renders `"106775.53"`;
at the capture's own scale 6 it renders `"106775.530000"`.

*Why 0.0%.* Neither graded seam calls `FormatDecimal`, and no `Expect` cell is decimal
text: the vector cells are **integer minor units** plus string identity/date fields, and the
only string money-adjacent cell (`purchase_price_ratio`) is a ratio, not a rendered amount.
So a vector cannot reach this function without the seam being extended to render an amount
through the port and compare it to the captured decimal text.

*Verdict.* **Implemented, observed (no capture needed), but outside the vector-addressable
surface.** Grading it is a seam-plumbing change plus a vector, not a capture; this run
does not do seam work. Figures a later run would take, all from
`transfer-28-je-post.json`: `10677553` → `"106775.530000"` (scale 6) or `"106775.53"`
(scale 2); `21355106` → `"213551.06"`; `10000000` → `"100000.00"`. **Candidate; not a defect**
(the port's own `TestMinorUnitsRoundTrip` exercises it).

### 4.3 `money.go:47` `MinorUnitsFromDecimalText` — OBSERVED for the accept path, UNOBSERVED for the residue-refusal arm

*Rule.* Parses exact major-unit decimal text into integer minor units using only integer
and string arithmetic, and **refuses** any non-zero digit beyond `minorDigits` rather than
silently truncating.

*Observation.* The accept path **exists**: the settlement capture's decimal strings are
parse inputs, e.g. `MinorUnitsFromDecimalText("106775.530000", 2)` → `10677553` (the
trailing zeroes beyond 2 decimals are tolerated), same for `100000.000000` →
`10000000`, `6618.530000` → `661853`, `213551.060000` → `21355106`. The **refusal arm has
no observation anywhere in the committed capture tree**: every captured money string
carries only two significant decimals even though the oracle serialises at scale 6 (the
rest are zeroes), so no capture shows a non-zero sub-minor residue (`1.001`-shaped).

*Why 0.0%.* As with `FormatDecimal`, no graded seam parses decimal text: vectors
transcribe to integer minor units by hand, and the `Expect` holds integers only.

*Verdict.* **Implemented, observed for the accept path; the refusal arm needs a capture.**
Grading the accept path needs the seam extended to parse the captured decimal text through
the port (no capture needed). Grading the refusal arm needs a capture of a money value
whose 3rd+ decimal digit is non-zero, which the corpus does not contain. **Candidate; not a
defect** (the port's own `TestMinorUnitsRefusesSubMinorResidue` covers the refusal).

## 5. The other 17 functions at 0.0% — not money rules

They are enumerated in the appendix. None is a money rule:

* `attribute.go:20` `StoredValue` — enum getter (`return string(s)`).
* `attribute.go:40` `OutstandingInterestStrategyFor` — attribute key/value decoder.
* `owner.go:17` `ExternalIDFor` — nil-safe accessor.
* `status.go:25`, `status.go:44` `StoredValue` — enum getters.
* `postgres.go:60,66,80,115,140,176,191,195,248,253,264,283` — the PostgreSQL storage layer
  (constructors, `Upsert`, `FindByExternalID`, `Insert`, `FindByID`, `FindByLoanID`,
  `find`, `FindByProduct`, `nullIfEmpty`). They transport ids, status strings, dates and
  the `purchase_price_ratio` string; **no statement performs money arithmetic**. They are
  also **outside this harness by design**: the conformance port is DB-free
  (`conformance/doc.go`), and these methods execute SQL against a live PostgreSQL. Their
  0.0% is a domain boundary, not a gap.

## 6. Summary of triage

| candidate | `file:line` | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `NormalizedTotalOutstanding` | `transfer.go:58` | yes (wrapper over the graded rule) | **yes** — `transfer-28-je-post.json` details | low value; one-line seam change would grade it, no capture |
| `FormatDecimal` | `money.go:20` | **yes** | **yes** — `transfer-28-je-post.json` decimal amounts | needs seam plumbing + vector, no capture |
| `MinorUnitsFromDecimalText` (accept) | `money.go:47` | **yes** | **yes** — same capture | needs seam plumbing + vector, no capture |
| `MinorUnitsFromDecimalText` (residue refusal) | `money.go:47` | **yes** | **no** (all captured decimals have only 2 significant digits) | needs a capture with a non-zero 3rd+ decimal |
| 17 getters/decoders/persistence | appendix | no | n/a | out of scope |

**No candidate is asserted to be a defect.** The graded investor corpus reaches exactly one
money rule (`DeriveTotalOutstanding`, now 100%). The three other money functions are
*implemented and unit-tested*, and the accept-path observations they would grade already sit
in `transfer-28-je-post.json`; what is missing is a seam that routes captured decimal money
through them — a plumbing change plus vectors, **not** a capture, except for the
sub-minor-residue refusal arm, which has no observation at all.

## 7. Defects found in the map (the map is generated; the driver fixes the generator)

* The map's **"conformance package files"** list is wrong: it names `main.go`, which does
  not exist, and omits `conformance_test.go` and `cmd/`. The package actually contains
  `admit.go`, `capability.go`, `conformance_test.go`, `doc.go`, `grade.go`, `impl.go`,
  `invariants.go`, `nofloat.go`, `report.go`, `vector.go`, plus `cmd/conformance`.
* The map correctly stated the committed-store test was **ABSENT**; that is now fixed.
* `.softhouse/capture/investor/` has **no `OWNER.md`** (the map notes this too). The read
  vectors' tenant is therefore inferred from the pin/vector stamps rather than stated by
  the capture's owner doc, unlike `investor-asset-transfer-100/`. Worth a capture-owner
  note, but it did not block this measurement (the vectors are admissible against the
  committed captures and their hashes).

## 8. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` was issued.
* No vector and no drive was written. `.softhouse/vectors/investor/` is unchanged.
* No port code changed. `.softhouse/guards/` (12 pairs) and `.softhouse/conformance.sh`
  (census 17) are untouched.
* No gap was graded. Section 6 names what a later run may grade and what would need a
  capture first.
* `TASK.md` and `.softhouse/maps/` were not committed.

## 9. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass.
* `bash .softhouse/conformance.sh` — **exit 2**, `HARD guard failed` count **0**, and the
  only exit line is
  `conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
  completed and the bar is refused by that recorded decision`. Verdict PASS.
* `kills.sh investor investor-wrong-blank-status <worktree>` → **1** (still kills, as before).
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365 <worktree>` → **45**.
* `kills.sh parties parties-wrong-iota-ordinals <worktree>` → **12**.
* `redcount.sh <worktree> investor` → **4** (all 4 registered `investor-wrong-*` drives kill).
* `capcount.sh <worktree> investor investor-go` → **0** (the reference fails no vector).
* The new committed-store test passes on the current tree, `-count=1`, and its reach is
  vector-driven (the two after figures in §2 are byte-identical, and the pre-test run was
  0.0%).

---

## Appendix A — all 20 functions at `0.0%` in the prescribed run

`file:line` are lines in the file.

- `attribute.go:20` `StoredValue`
- `attribute.go:40` `OutstandingInterestStrategyFor`
- `money.go:20` `FormatDecimal`
- `money.go:47` `MinorUnitsFromDecimalText`
- `owner.go:17` `ExternalIDFor`
- `postgres.go:60` `NewPostgresOwnerRepository`
- `postgres.go:66` `Upsert`
- `postgres.go:80` `FindByExternalID`
- `postgres.go:115` `NewPostgresTransferRepository`
- `postgres.go:140` `Insert`
- `postgres.go:176` `FindByID`
- `postgres.go:191` `FindByLoanID`
- `postgres.go:195` `find`
- `postgres.go:248` `NewPostgresLoanProductAttributeRepository`
- `postgres.go:253` `Upsert`
- `postgres.go:264` `FindByProduct`
- `postgres.go:283` `nullIfEmpty`
- `status.go:25` `StoredValue`
- `status.go:44` `StoredValue`
- `transfer.go:58` `NormalizedTotalOutstanding`

Reached through the vectors (the one function the corpus grades):

- `transfer.go:51` `DeriveTotalOutstanding` — **100.0%**, via `INV-03` and
  `conformance/impl.go:278`.
