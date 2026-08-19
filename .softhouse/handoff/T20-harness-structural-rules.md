# T20 — T17 follow-ups F2–F6 as structural harness rules, plus driver findings D-4, D-5, D-6

| | |
|---|---|
| **Task** | T20 (`test_writer`), run `2026-08-17-run1-harness-schedule-poc`, context `tier0-harness-schedule-poc` |
| **Branch** | `softhouse/T20-harness-structural-rules` |
| **Scope** | `.softhouse/conformance.sh`, `nexus/internal/apps/loanschedule/conformance/**`, `.softhouse/vectors/README.md` (driver-authorised), `docs/analysis/tier0-vector-capture-plan.md` (§4.0 check 4 + §6 backlog, per the F2 and F4 instructions) |
| **Not touched** | `nexus/internal/apps/loanschedule/contract/contract.go` (ratified, frozen), any file under `.softhouse/vectors/loanschedule/` or `_selftest/`, `.softhouse/vectors/capabilities.json`, `.softhouse/vectors/PIN.json`, anything under `.softhouse/capture/` |
| **Reference oracle** | Not needed and not contacted for this task. All source citations are against the pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` `[VERIFIED: git -C /Users/buv/fineract rev-parse HEAD → 426a23544e8426a38ae43ae404670a0a7e85b9eb]`. |

**The harness still exits 2.** With no Go implementation registered (T10 has not run) the verdict text is
unchanged and no rule added here can turn a 2 into a 0. Every rule is a refusal, a fatal reason, or a
disclosure line.

---

## 0. Baseline first, then the delta

The brief said `go test ./...` must be green and `--prove` 10/10; the driver warned those were not meetable at
the revision I started from. **Both statements are true, of different trees**, and the distinction matters:

| tree | `go test ./...` | `.softhouse/conformance.sh --prove` | `.softhouse/conformance.sh` |
|---|---|---|---|
| **main @ `2ec5976`, store as committed** | **ok** | **10 passed, 0 failed** | exit **2**, `VERDICT: UNUSABLE` |
| **main @ `2ec5976` + T8-promote's 11 vectors** | **FAIL** — 3 tests (`TestStoreIsAdmissible`, `TestHarnessGoesGreenAndRed`, `TestStaleRefusalVectorIsDetected`), all `decode: json: unknown field "kind"` | **8 passed, 2 failed** | exit 2 |
| **this branch, store as committed** | **ok** | **15 passed, 0 failed** | exit **2**, `VERDICT: UNUSABLE` |
| **this branch + T8-promote's 11 vectors** | **ok** | **15 passed, 0 failed** | exit **2**, 0 inadmissible, 0 refused |

`[VERIFIED: measured, not inferred. Baselines were run from `git archive HEAD` into /tmp/t20-baseline and, with
`git archive softhouse/T8-promote-parity-vectors -- .softhouse/vectors` overlaid, into /tmp/t20-basevec. The
"this branch + T8" tree is /tmp/t20-combined, built the same way from the working tree. No vector file was
written into this worktree's store at any point.]`

So the red the driver was told about is a property of **main + T8's vectors**, not of main alone — and this
branch closes it in both directions: it is green with the vectors and green without them.

Combined-tree evidence that D-4 actually landed (my harness, T8's vectors):

```
counterfactuals named by admissible vectors: 24  (21 money kills, 3 structural kills)
schedule.core       killed by … ROW-ORDER-SORT-BY-DATE-DISBURSEMENT-FIRST [structural], …
monthend.reanchor   killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural], MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural]
inadmissible            0
refused                 0
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

`monthend.reanchor` is no longer an unsatisfiable UNBACKED complaint. It is backed, by structural kills, and the
report says `[structural]` so nobody reads it as a graded amount.

---

## 1. F2 — a partial match must not read as a full one

### 1.1 The nine columns are **six**, and I implemented six

The brief said "scope it to the nine columns the capture README actually reports … establish which nine from the
corpus, not from memory". **I established six.** T17's D8 says the README block "covers 9 of 10 period columns"
and names only `totalOutstandingBalance` as missing. The block itself omits **four**:

| | what the block prints, per row | of the ten |
|---|---|---|
| repayment row | `period_number`, `due_date`, `outstanding_balance` ("Balance"), `principal`, `interest`, `total_due` ("Total") | **6** |
| disbursement row | `due_date` ("Date"), `principal` ("Amount") | **2** |
| **silent on** (repayment) | `from_date`, `fee`, `penalty`, `total_outstanding_balance` | 4 |

**How I established it, mechanically rather than by reading:** the block is copied verbatim into
`nexus/internal/apps/loanschedule/conformance/testdata/embeddable-readme-ci-stdout.txt`, and
`TestReadmeAttestationMatchesTheReadmeText` **parses the labels out of that text** and asserts the harness's
declared column set equals the parsed one, in both directions, on every `go test` run. When the pinned checkout
is present the test also verifies the excerpt line by line against the live README.

`[VERIFIED: fineract-progressive-loan-embeddable-schedule-generator/README.md:48-63 @ the pinned commit;
diff of `sed -n '49,62p' README.md` against the testdata excerpt reported IDENTICAL.]`

**T17-F2 is therefore partly refuted, in the direction that makes the finding stronger, and I have flagged it
rather than worked around it** — in `structural.go` ("SIX, NOT NINE"), in the test's failure message, in
`.softhouse/vectors/README.md`, and in the capture plan's §4.0 check 4.

Two further traps found while establishing it, both now declared and printed every run:

* **The block is stale relative to its own producer.** `misc/Main.java:86` prints a **seventh** field, `Total
  Outstanding Balance`, that the committed block does not show. The block attests what an older build emitted.
  `[VERIFIED: misc/Main.java:86 — the repayment printf carries rp.getTotalOutstandingLoanBalance(); README.md:57-62 does not.]`
* **`Number of Periods: 6` is a filtered count** — `Main.java:73` excludes disbursement periods — while the
  corpus's `getPeriods().size()` is **7**. Cross-checking one against the other is a defect, not a
  corroboration. `[VERIFIED: misc/Main.java:73; plan §2.1 transcribes getPeriods().size() = 7.]`

### 1.2 In code

* `structural.go` — `AttestationSource`, the `readmeCIStdout` declaration (columns per row kind, citation,
  four caveats), `PeriodColumns()` (the ten-column denominator, from the `checkPeriod` overload at
  `EmbeddableProgressiveLoanScheduleGeneratorTest.java:100-102`), `Attests`, `Unattested`.
* `vector.go` — `Provenance.CorroboratedBy []Corroboration` (optional).
* `admit.go` — `admitCorroborations`: unknown source, unattested column, a row kind the source is silent about,
  a name that is not one of the ten, and an empty column list are each INADMISSIBLE, and the message prints
  what the source *does* attest and what it is silent on.
* `report.go` — a `CROSS-CHECK SOURCES, AND THE COLUMNS THEY DO NOT COVER (T17-F2)` section printed on **every**
  run, source by source, row kind by row kind, with the silent columns and the caveats.

### 1.3 Also applied to the document the finding was about

`docs/analysis/tier0-vector-capture-plan.md` §4.0 acceptance check 4 now states the six columns, the two
disbursement columns, the four silent ones, both traps, and "a match here is never a whole-row match". This is
the one place a capture fire would have read the over-scoped instruction.

---

## 2. F3 — RESTATED, because observation refutes the original wording

**Original (T17 follow-up F3):** *"Add to C-00 an assertion that `MoneyHelper` is **never** statically
initialised on the embeddable path — instrument or stub it to throw."*

**Refuted by observation.** Capture pass 1's `D-04` ran the embeddable path with `allowFullTermForTranche =
true` and died with `IllegalStateException: No tenant context available. MoneyHelper requires a valid tenant
context` — which is `MoneyHelper` being reached, on that path, in process. Pass 2 supplied a tenant, `T-04t`
ran to completion, and the flag was confirmed live and schedule-neutral on a single-disbursement loan.
`[VERIFIED: .softhouse/capture/PASS2-REPORT.md:34 (the D-04 failure, citing MoneyHelper.java:178-179) and
:59-77 (T-04f vs T-04t identical on all 7 periods; T-04f-big vs T-04t-big identical on all 19; ambient
precision read from the running oracle as 19).]`

**What I implemented is the narrower, true claim:** *not observed to be reached when the flag is FALSE.* And
because "not observed in the shapes we captured" is not "unreachable", the operative rule is the opposite of
an exemption:

* `structural.go` — the claim register. `Claims()` carries `T17-F3` with
  `Status: NARROWED-BY-OBSERVATION`, the **original wording verbatim**, the **observation that narrowed it**,
  and the evidence. `HarnessDeclarationDefects` makes it a **fatal harness defect** to keep the status while
  dropping either the original wording or the observation — so the wider wording cannot creep back in silently.
* `admit.go` — a parity vector whose `ambient_mathcontext` is unrecorded is INADMISSIBLE, on **every** seam,
  and the refusal quotes the D-04 observation rather than merely asserting a rule.
* `report.go` — a `STANDING CLAIMS THIS HARNESS'S RULES DEPEND ON` section, printed every run, showing the
  claim, its status, the refuted wording and the evidence.

I did **not** implement F3's instrumentation (stub `MoneyHelper` to throw during C-00). It would assert a
statement that is false on the flag-true branch, and it is capture-rig work, not harness work.

---

## 3. F4 — the coverage gap, made visible on every run

`structural.go` — `CoverageGaps()` declares `T17-F4-rate-schedule-from-origination`, `OPEN`, owner **Tier A**.
`report.go` prints a `STRUCTURAL COVERAGE GAPS IN THE CORPUS (closed by capture, never by code)` section on
every run. `HarnessDeclarationDefects` refuses to let a gap be marked `CLOSED` without naming the capture that
closed it — a gap is closed by an observation, never by an assertion.

The statement, re-established rather than copied:

* every rate-variation expectation in the corpus is `changeInterestRate` on an already-built model — mid-term
  rescheduling — and there are exactly **12** such call sites, no more.
  `[VERIFIED: grep -n "changeInterestRate" over fineract-progressive-loan/src/test → 12 hits, all in
  ProgressiveEMICalculatorTest.java at :410, :459, :505, :549, :1725, :1726, :1770, :1771, :1772, :1773, :1814,
  :1815. The plan's "and beyond" is complete at 12.]`
* the Path A seam **cannot express** the origination form: `LoanRepaymentScheduleModelData` carries a single
  scalar `annualNominalInterestRate` and no rate schedule at all.
  `[VERIFIED: LoanRepaymentScheduleModelData.java:32-39, the record header, 19 components ending in
  allowFullTermForTranche.]`

Also written into `docs/analysis/tier0-vector-capture-plan.md` §6 as an explicit **TIER-A BACKLOG** bullet, as
the brief instructed. **Not closed, and not attempted** — closing it needs server-path captures.

---

## 4. F5 — scale > 2 in a money column is a harness bug

`money.go` — `ScaleOfWireText`, which returns a wire text's scale and rejects exponent notation (the oracle
emits `toPlainString()`).

`admit.go`, in `admitPeriods`, for every money column carrying `*_major_text`:

| case | outcome |
|---|---|
| scale ≤ currency minor-unit digits | admitted, as before |
| scale > digits, some excess digit **non-zero** | **INADMISSIBLE** — unchanged; `MinorFromMajorText` still refuses to round a transcription |
| scale > digits, excess all zero, **undeclared** | **INADMISSIBLE** (new) — this is the silence F5 is about |
| scale > digits, excess all zero, **declared** in `over_scaled_wire_text_fields` | admitted, **counted**, printed in the report |
| declared but the text is not over-scaled | **INADMISSIBLE** — a declaration that does not match the text teaches a reader to ignore declarations |
| a non-money column named in the declaration | **INADMISSIBLE** |

**Why declaration rather than outright rejection.** The failure mode F5 names is a rig *silently rounding* an
over-scaled value. Non-zero excess digits were already refused, so the only remaining case converts **exactly** —
and the corpus is genuinely not uniform in scale (Path B persists product rows at scale 6). Rejecting an exact
value outright would delete usable observations; accepting it silently is the defect. Declaration removes the
silence and keeps the value, and the count is printed every run. **This is a schema addition
(`over_scaled_wire_text_fields`, optional).** T8-promote's 11 vectors do not use it and are unaffected — all
their period money text is scale 2 `[VERIFIED: the combined tree admits all 15 vector files, 0 inadmissible]`.

---

## 5. F6 — a transcribed rate factor is a 12-dp rounding

`structural.go` — `RoundedTranscriptions()` declares `rate_factor`: transcribed scale **12**, parity status
**`TO_BE_CAPTURED`**, the citation, and the trap in one sentence. `HarnessDeclarationDefects` refuses to let the
status become `CAPTURED` without naming the capture.

`[VERIFIED: the rateFactor argument asserted by checkPeriod is compared after
value.setScale(MoneyHelper.getMathContext().getPrecision(), MoneyHelper.getRoundingMode()) —
ProgressiveEMICalculatorTest.java:5241, applyMathContext at :5256-5258 — and the tests mock that precision to 12.]`

`vector.go` — `ExpectPeriod.ObservedRateFactor *RateFactorObservation` (optional): `text` (a decimal **string**),
`transcribed_at_scale`, `precision_status`, `citation`.

`admit.go` — `admitRateFactor`: `precision_status` must be exactly `TRANSCRIBED-ROUNDED`; **`"EXACT"` is
INADMISSIBLE** and the refusal says exact rate-factor parity is `TO_BE_CAPTURED` and states the trap; the
declared scale must equal the text's own scale; digits past 12 are refused; the citation is required.

**The value is never compared against anything.** It is counted separately (`RateFactorsRecorded`) and the
report prints `rate-factor observations carried by this run: N — recorded, NEVER compared`, plus the
`TRANSCRIBED-ROUNDED at 12 decimal places, parity status TO_BE_CAPTURED` disclosure with its citation, on every
run. The harness therefore says out loud what it cannot check, instead of implying parity it cannot check.

---

## 6. D-4 — structural counterfactuals (driver specification, implemented as specified)

Implemented exactly to the driver's spec, **in the order the correction demanded**: the fields went onto
`Counterfactual` in `vector.go` **first**, because `LoadVector` decodes with `DisallowUnknownFields` and an
admit-only change would have turned every structural vector into a load error rather than a rule.

* `vector.go` — `Kind string \`json:"kind,omitempty"\``, `DivergentCells []string
  \`json:"divergent_cells,omitempty"\``, constants `CounterfactualMoney` / `CounterfactualStructural` /
  `DivergentCellRowOrder`, plus `StructuralCellFields()` and `MoneyCellFields()`.
* `admit.go` — `admitCounterfactualKind` and `admitDivergentCell`:
  * `kind` empty or `"money"` → `margin_minor` parses and is **> 0** (today's rule, untouched) **and**
    `divergent_cells` must be empty;
  * `kind == "structural"` → `margin_minor` must be exactly `"0"`; `divergent_cells` non-empty; each entry is
    `row_order` or `period[<n>].<field>` with `<n>` a real row of this vector's schedule and `<field>` one of
    `due_date`, `from_date`, `kind`; **a money column is INADMISSIBLE** ("that is a money kill wearing a
    structural label"); duplicates refused; and `evidence` must state **both** values;
  * any other `kind` → INADMISSIBLE.
* `capability.go` — a structural counterfactual's id is printed as `ID [structural]` in the coverage map.
* `grade.go` / `report.go` — `MoneyKills` and `StructuralKills` counted and printed separately, never merged,
  in both the "what this run grades" section and the summary.

**Verification of the "both values" rule.** The driver required the evidence to state the wrong value and the
observed one. There is no way to check that semantically, so the check is deliberately crude and says so: the
evidence must contain `observed` **and** one of `instead` / `rather than` / `wrong` / `emits`, and the refusal
message names those words so an author is never left guessing. I judged a crude check that fires better than a
sentence in a document that does not — flagged here because it is the one place I chose a heuristic.

**One deliberate narrowing, stated rather than slipped in:** `installment_number` is a non-money cell that
`diffSchedule` compares, but it is **not** in `StructuralCellFields()`. The spec listed `due_date`, `from_date`,
the row `kind` and `row_order`, and no observed grader in the corpus turns on `installment_number`. Adding it is
a widening and a widening needs a reason; T8-promote's `P-03` evidence mentions it alongside `kind`, so if a
future vector needs it, that is a one-line change with a stated reason. **I did not make the change silently.**

---

## 7. D-5 — the replay implementation no longer drops a vector in silence

`registry.go`, `NewReplayImplementation`: an **unrecorded** money cell is now skipped **as a cell** (the replay
answers 0, and `diffSchedule` never compares an unrecorded cell — it counts it UNGRADED). Anything genuinely
unparseable — a bad kind, a request that does not map, a malformed sentinel, a money cell that is neither
recorded nor declared unrecorded — is a **hard error naming the vector, the period and the field**, and tells
the reader to use `unrecorded_fields`. Nothing `continue`s silently any more.

This was the harness's own cardinal sin: the dropped vector then surfaced as *"no vector in the replay store
carries this request"* — absence of evidence dressed as evidence of absence.

---

## 8. D-6 — and its sibling, which the driver had not seen

`conformance_test.go` carried **two** frozen facts about the store, not one. Both are the same defect class:
an assertion about what the corpus contained on the day it was written, which any successful promotion falsifies.

**D-6 (`TestHarnessGoesGreenAndRed`), was:** `ParityPass != 0 → "the store has no promoted capture yet"`.
**Replaced with the property it was protecting: a parity PASS must be EARNED.** New helper
`parityPassViolations` reports one line per parity PASS that is not backed by all of —

1. something registered to grade (no implementation ⇒ no parity pass);
2. a result of class `parity` matching a vector of class `parity`;
3. `provenance.kind == oracle-capture` — not hand-authored, not derived from the contract;
4. a named `capture_ref` **and** `capture_case_id`, and a seam that is not `""`/`none`;
5. and `ParityPass` equal to the number of passing parity results (no phantom count).

Plus, in the same subtest: with **no implementation registered**, `ParityPass == 0` and exit **2**; and a
self-test report always carries `SELF-TEST` and `NOT a conformance PASS`.

**The sibling (`TestGradeabilityIsNotPairDifference`), was:** "the real store has no parity vector, so
`uncovered` must be non-empty" — which failed the moment T8's vectors backed both graded capabilities
`[VERIFIED: measured — with T8's vectors overlaid and only D-4/D-5 fixed, this test failed with
"with no parity vector promoted, every in_graded_domain capability must be reported unbacked … unbacked: []"]`.
**Replaced with the property:** a capability is reported UNBACKED **exactly when** no admissible parity vector
names a counterfactual for it (checked in both directions, per capability), **and** the unbacked path is shown
to be able to fire at all — over an empty vector set every graded capability must be unbacked, so "nothing
unbacked" can never mean "the check examines nothing".

Neither guard was deleted and neither was relaxed to `>= 0`.

---

## 9. Red/green proofs — command and output

### 9.1 `.softhouse/conformance.sh --prove`, this branch, store as committed

```
$ ./.softhouse/conformance.sh --prove
PROOF OK   exit 2 (wanted 2)   no implementation to grade
PROOF OK   exit 2 (wanted 2)   reference oracle unreachable (probe aimed at a closed port; live instance untouched)
PROOF OK   exit 0 (wanted 0)   harness self-test over the pristine store
PROOF OK   exit 1 (wanted 1)   one-minor-unit perturbation of an expected value
PROOF OK   exit 2 (wanted 2)   integer perturbed but the oracle wire text not (transcription error)
PROOF OK   exit 2 (wanted 2)   empty vector store
PROOF OK   exit 2 (wanted 2)   absent vector store
PROOF OK   exit 2 (wanted 2)   self-test fixture excluded from the parity count
PROOF OK   exit 0               the fixture PASSES and parity stays 0, stamped NOT a conformance PASS
PROOF OK   exit 2 (wanted 2)   float token in a vector file
PROOF OK   exit 2 (wanted 2)   T17-F5: an UNDECLARED over-scaled money wire text is inadmissible
PROOF OK   exit 2 (wanted 2)   T17-F6: a rate factor claiming exactness is inadmissible
PROOF OK   exit 2 (wanted 2)   T17-F2: a corroboration claiming an unattested column is inadmissible
PROOF OK   exit 2 (wanted 2)   D-4: a structural counterfactual naming a money column is inadmissible
PROOF OK   exit 0 (wanted 0)   D-5: an unrecorded money cell costs the CELL, not the vector
PROOFS: 15 passed, 0 failed
```

The five new proofs use a new `expect_saying` helper that asserts the exit code **and a required substring of
the output**, because a proof that checked only the code would pass if the vector were refused for some
unrelated reason — which is how a rule quietly stops being the rule that fires. Each is guarded by
`assert_mutated`, which fails the proof if its perturbation did not apply, so no proof can be vacuous.

### 9.2 Each new rule demonstrated to go RED when the rule itself is removed

Method: disable one rule in the harness, run `--prove`, restore. Verbatim results, one line each:

| rule disabled | edit | result |
|---|---|---|
| **F5** over-scale refusal | `case scale > digits && !overScaled[…]` → `case false && …` | `PROOF FAIL exit 0 (wanted 2)   T17-F5: an UNDECLARED over-scaled money wire text is inadmissible` — `PROOFS: 14 passed, 1 failed` |
| **F6** precision-status check | `if rf.PrecisionStatus != PrecisionTranscribedRounded` → `if false && …` | `PROOF FAIL exit 0 (wanted 2)   T17-F6: a rate factor claiming exactness is inadmissible` — 14/1 |
| **F2** corroboration scoping | `admitCorroborations` returns `nil` immediately | `PROOF FAIL exit 0 (wanted 2)   T17-F2: a corroboration claiming an unattested column is inadmissible` — 14/1 |
| **D-4** money-column rejection | `if containsString(MoneyCellFields(), field)` → `if false && …` | `PROOF FAIL exit 2 (wanted 2)   D-4: …` — 14/1. **Note the exit code is still 2**: the cell is then caught by the "not a cell this harness compares" branch instead, so only the *message* assertion catches it. This is the case that justifies `expect_saying`. |
| **D-5** unrecorded-cell skip | `if unrecorded[field]` → `if false && unrecorded[field]` | `PROOF FAIL exit 2 (wanted 0)   D-5: an unrecorded money cell costs the CELL, not the vector` — 14/1 |

The same D-5 mutation, in process:

```
--- FAIL: TestUnrecordedMoneyCellIsNotADroppedVector
    a vector with an unrecorded money cell must still load: replay store: vector
    SELFTEST-01-two-period-zero-rate (_selftest/SELFTEST-01-two-period-zero-rate.json) period 0
    interest_minor = "": empty monetary value … If the capture never recorded this cell, name it in that
    period's unrecorded_fields …
```

All mutations were reverted; the tree as committed is 15/15 and `go test ./...` green.

### 9.3 In-process proofs (`structural_test.go`, `conformance_test.go`)

Every rule is proven in **both** directions where both exist — the violating shape refused, the compliant shape
admitted — so no rule can pass by refusing everything.

| test | proves |
|---|---|
| `TestReadmeAttestationMatchesTheReadmeText` | the declared column set is **re-derived from the README's own text**, both directions; the counts are pinned at 6 attested / 4 silent; the excerpt is verified line-by-line against the live checkout when present |
| `TestCorroborationIsScopedToWhatTheSourcePrints` | 7 cases: the six attested columns admitted; `total_outstanding_balance` refused; `from_date` refused; a silent row kind refused; an undeclared source refused; an empty column list refused; a non-column refused |
| `TestF3ClaimRecordsWhatNarrowedIt` | the claim is stored NARROWED, names `allowFullTermForTranche`, `D-04` and `No tenant context available`; **red** when the observation or the original wording is dropped; the shipped declarations are defect-free |
| `TestAmbientMathContextMustBeRecorded` | an unrecorded ambient context is refused, quoting the observation; a recorded one is admitted |
| `TestCoverageGapIsVisibleOnEveryRun` | the F4 gap, its id, `[OPEN]`, `changeInterestRate` and `Tier A` appear in the report of a real run; **red** when a gap is marked CLOSED with no capture |
| `TestScaleOfWireText` | 9 cases including exponent notation, a bare `.50`, a trailing `100.` |
| `TestOverScaledMoneyTextMustBeDeclared` | undeclared over-scale refused; declared admitted; declaration/text mismatch refused; a non-zero excess digit refused **even when declared**; a non-money column refused |
| `TestRateFactorIsRecordedNeverGraded` | `TRANSCRIBED-ROUNDED` admitted; `EXACT` refused naming `TO_BE_CAPTURED` and the digits-13+ trap; scale-vs-text mismatch refused; digits past 12 refused; missing citation refused; the report's disclosure text asserted; **red** when the quantity is promoted to `CAPTURED` with no capture |
| `TestStructuralCounterfactuals` | 12 subtests — the driver's five mirror cases plus row_order, malformed names, repeated cells, out-of-range rows, unknown kinds, and **the ZERO-MARGIN money case still refused** |
| `TestReportNeverMergesMoneyAndStructuralKills` | the two counts are printed separately in both places |
| `TestNewSchemaFieldsDecode` | a **real document** carrying `kind`, `divergent_cells`, `corroborated_by`, `observed_rate_factor` and `over_scaled_wire_text_fields` decodes through `LoadVector` (the D-4 correction) and is then admissible |
| `TestUnrecordedMoneyCellIsNotADroppedVector` | D-5 green and red |
| `TestHarnessGoesGreenAndRed` / `the earned-parity check itself goes red` | D-6: the replacement assertion holds on the real run, and is shown to fire for a fabricated parity PASS and for one with no implementation registered |

### 9.4 The gates from the brief

```
$ go build ./...   → exit 0
$ go vet ./...     → exit 0
$ go test ./...    → ok  github.com/gerege/nexus/internal/apps/loanschedule/conformance
$ gofmt -l nexus/  → internal/apps/loanschedule/contract/contract.go        (ONLY this file — expected, gate G-3)
$ ./.softhouse/conformance.sh ; echo $?
  … VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
  2
```

`contract.go` was never opened for writing, never formatted, and its digest still matches `PIN.json` (the
harness verifies this on every run and would have reported a fatal reason otherwise).

---

## 10. What I deliberately did NOT do

1. **No vector file authored, edited or deleted.** Not in `.softhouse/vectors/loanschedule/`, not in
   `_selftest/`, not `PIN.json`, not `capabilities.json`. Every test that needed a structural or over-scaled
   vector builds it in `t.TempDir()` or as a Go value; every shell proof perturbs a copy under `mktemp -d`.
   T8-promote's branch and mine touch disjoint files.
2. **No `in_graded_domain` flag flipped**, in either direction. `monthend.reanchor` stays `true` and is now
   backed by T8's structural counterfactuals.
3. **F3's instrumentation not implemented** — see §2. It asserts something false of the flag-true branch.
4. **F4 not closed** — it needs server-path captures I was not taking. It is declared, printed and owned.
5. **`installment_number` not admitted to `StructuralCellFields()`** — see §6.
6. **No new invariant, no new grading channel.** Nothing here compares a value that was not already compared,
   and nothing here can make a failing run pass.

## 11. Things in T17's findings that further evidence refutes or narrows

| finding | status after this task |
|---|---|
| **F2 / D8** — "the README covers **9** of 10 period columns; only `totalOutstandingBalance` is missing" | **REFUTED as arithmetic, upheld and strengthened as a finding.** It covers **six**; `from_date`, `fee` and `penalty` are missing too. Implemented at six. |
| **F3** — "`MoneyHelper` is **never** statically initialised on the embeddable path" | **REFUTED as written** by capture pass 1's `D-04`. Implemented as the narrower "not observed when `allowFullTermForTranche` is false", with the refuting observation attached to the claim in code. |
| **F5** — "any value with scale > 2 in a money column is a harness bug" | **Upheld**, implemented as a two-tier rule (see §4). The non-zero-excess half was already enforced; the new half is the silence. |
| **F6** — "record rate factors as TRANSCRIBED-ROUNDED, treat exact parity as TO_BE_CAPTURED" | **Upheld**, implemented literally. |
| **F4** — "carry the origination-rate-schedule question forward" | **Upheld**, and both halves of the claim independently re-verified (12 call sites; the seam carries one scalar rate). |
| Plan §3.4's "lines 410, 459, 505, 549, 1725–1726, 1770–1773, 1814–1815 **and beyond**" | **Narrowed:** there is no "and beyond". The grep returns exactly those 12. |

## 12. For whoever merges

* Merge order is unchanged: **this branch first**, then `softhouse/T8-promote-parity-vectors`, then re-run the
  harness. This branch depends on **no** vector file; §0 shows it green both with and without T8's.
* After both are merged the expected state is: `go test ./...` green, `--prove` 15/15, `conformance.sh` **exit
  2** with `NO PARITY VECTOR WAS GRADED` — because T10 has not run and there is still no Go implementation to
  grade. Exit 2 is the correct state, not a regression.
* `.softhouse/vectors/README.md` documents `kind`, `divergent_cells`, `corroborated_by`,
  `over_scaled_wire_text_fields` and `observed_rate_factor`. It also **amends** one paragraph my F5 change
  falsified (the converter no longer accepts over-scaled trailing zeros *silently*); leaving a now-false
  sentence in the promotion contract would have been worse than the small out-of-section edit, and it is
  flagged here rather than made quietly.
