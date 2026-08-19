# T8-promote — promoting Path A pass 3b into the parity vector store

Task `T8-promote` (`test_writer`), run `2026-08-17-run1-harness-schedule-poc`, context
`tier0-harness-schedule-poc`. Branch `softhouse/T8-promote-parity-vectors`.

---

## Headline

**11 of 11 pass-3b production candidates promoted. Nothing was withheld and nothing was
fabricated.** `schedule.core` is now backed. `monthend.reanchor` is **not**, and cannot be at
this harness revision — its only graders kill on **dates**, and `graded_against` is money-only.

**The bottleneck is half cleared, and the other half is a harness gap, not a corpus gap.**

```
BEFORE  UNBACKED in_graded_domain claims: monthend.reanchor, schedule.core
AFTER   UNBACKED in_graded_domain claims: monthend.reanchor
```

Three harness defects were surfaced by this promotion. Only one (D-4) was known before I
started; **D-5 and D-6 are new, and D-6 makes `go test ./...` red after *any* successful
promotion, independently of everything else I did.** All three are in `nexus/`, which I am
scoped out of. Details in §5.

`.softhouse/conformance.sh` still exits **2** with `VERDICT: UNUSABLE — THIS IS NOT A PASS`,
which is correct: no Go implementation is registered (T10 has not run). **No parity claim is
made by this task and none may be read into it.**

---

## 1. What was promoted

All under `.softhouse/vectors/loanschedule/`, one file per capture case, `class: "parity"`,
seam `path_a_embeddable`, provenance `.softhouse/capture/out/capture-prod3b-raw.json`
(`capture_sha256` `8d23c48f…c945c79`, verified against the file and against the corpus's own
`capture-prod3b-sha256.txt`).

| capture case | file | rows | `capabilities_required` |
|---|---|---|---|
| `P-00` | `P-00-baseline-6x7pct.json` | 7 | schedule.core |
| `P-01` | `P-01-18x18pt5pct-principal-87654321.json` | 19 | schedule.core |
| `P-02` | `P-02-monthend-seed-day-31.json` | 7 | schedule.core, monthend.reanchor |
| `P-02b` | `P-02b-monthend-seed-day-30.json` | 7 | schedule.core, monthend.reanchor |
| `P-03` | `P-03-disbursement-on-repayment-due-date.json` | 7 | schedule.core |
| `P-04f` | `P-04f-fulltermfortranche-false.json` | 7 | schedule.core |
| `P-04t` | `P-04t-fulltermfortranche-true.json` | 7 | schedule.core |
| `P-MNT-5M` | `P-MNT-5M-18x18pt5pct.json` | 19 | schedule.core |
| `P-MNT-1M2` | `P-MNT-1M2-12x21pt6pct.json` | 13 | schedule.core |
| `P-MNT-50M` | `P-MNT-50M-36x16pt8pct.json` | 37 | schedule.core |
| `P-MNT-4M999` | `P-MNT-4M999-18x18pt5pct.json` | 19 | schedule.core |

`P-CAL` was **not** promoted: it is the pass-3b rig calibration at precision 12, listed in
`calibrationCaptureIds` and on `PIN.json`'s never-promotable list. The promotion script asserts
against that list per case.

**NOT PROMOTED, and why: nothing.** No candidate was found inadmissible on evidence. Two
honest caveats belong on the record instead, because they reduce what the set *distinguishes*
without reducing what it *contains*:

- **`P-00`, `P-04f` and `P-04t` are ONE shape, observed three times.**
  `allowFullTermForTranche` has no field in the frozen contract, so all three vectors' `request`
  blocks are byte-identical, and their `expect` blocks are byte-identical too (verified across
  all seven rows and all plan totals — `P-00`/`P-04f`/`P-04t` observed blocks compare equal in
  the capture). They add **zero** discriminating power over `P-00`. I promoted them because they
  are genuine, admissible observations and the brief asked for all 11, but a `DUPLICATE-SHAPE
  WARNING` is written into each file's `_note` and the coverage claim should be read as
  **9 distinct shapes, not 11**. `P-04t`'s value is evidence that the flag is INERT on the Path A
  seam — but that evidence lives in the *capture*, not in the vector, which cannot express the
  flag at all.
- **The whole set is one day-count arm at one frequency.** Every case is
  `FIXED_30_360` / `MONTHS` / `repayment_every 1` / `DECLINING_BALANCE` / 2 decimals /
  down payment 0/1 / no installment-rounding multiple. Nothing here grades ACT/ACT, charges,
  holidays, non-monthly frequency, HALF_EVEN, or precision 19-vs-12. The `WHAT THIS RUN DOES NOT
  GRADE` block already says the last of these; the rest stay refused by `capabilities.json`, and
  I changed nothing there.

**`capabilities.json`, `PIN.json` and `contract.go` are untouched.** `git diff` against the merge
base shows changes only under `.softhouse/vectors/loanschedule/` and `.softhouse/handoff/`.

---

## 2. Counterfactuals priced, with the arithmetic

Every margin below is a **derivation about a hypothetical wrong port**, never a claim about the
oracle. Each vector's `evidence` field carries the same arithmetic so it is re-derivable without
running my script.

| vector | counterfactual | kind | `margin_minor` |
|---|---|---|---|
| P-00 | LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT | money | 1 |
| P-00 | STRAIGHT-LINE-PRINCIPAL-DIVISION | money | 24 |
| P-01 | STRAIGHT-LINE-PRINCIPAL-DIVISION | money | **65,885,070** |
| P-02 | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 1 / 24 |
| P-02 | **MONTHEND-CONTINUE-FROM-CLAMPED-DAY** | **structural** | **0** |
| P-02b | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 1 / 24 |
| P-02b | **MONTHEND-CONTINUE-FROM-CLAMPED-DAY** | **structural** | **0** |
| P-03 | LEVEL-INSTALLMENT-… | money | 1 |
| P-03 | **EMI-DENOMINATOR-USES-NUMBER-OF-REPAYMENTS-NOT-PERIODS-AFTER-DISBURSEMENT** | money | **334** |
| P-03 | ROW-ORDER-SORT-BY-DATE-DISBURSEMENT-FIRST | **structural** | **0** |
| P-04f | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 1 / 24 |
| P-04t | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 1 / 24 |
| P-MNT-5M | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 5 / 3,758,228 |
| P-MNT-1M2 | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 3 / 1,010,059 |
| P-MNT-50M | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 4 / 36,423,098 |
| P-MNT-4M999 | LEVEL-INSTALLMENT-… / STRAIGHT-LINE-… | money | 8 / 3,758,240 |

### 2.1 `LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT`

A port that emits the level installment in the final period too, so the final principal is
`installment − interest` instead of the whole remaining balance. Worked example, P-MNT-4M999,
every input transcribed:

```
observed level installment (row total, every non-final paying period) = 320221.84
observed FINAL row total                                              = 320221.92   (≠, so the oracle rebalances)
counterfactual final principal = 320221.84 − 4861.80 (observed final interest) = 315360.04
observed final principal                                                        = 315360.12
margin = |31536012 − 31536004| = 8 minor units
```
The counterfactual's closing balance is also non-zero, so `principal_amortizes_to_zero` catches
it independently.

**Genuinely 0 on `P-01`, so it is NOT listed there.** On `P-01` every row total, including the
final, is `5613766.78`, and `5613766.78 − 85231.58 = 5528535.20` is *exactly* the observed final
principal. The balancing adjustment happens to be a no-op on that shape, so that vector does not
kill this candidate and does not claim to. Recording it would have been a fabricated margin.

### 2.2 `STRAIGHT-LINE-PRINCIPAL-DIVISION`

A port that splits principal evenly (`P / n`) and adds declining-balance interest on top, instead
of taking principal as the balancing remainder of a level installment. P-01:

```
counterfactual per-period principal = 87654321 / 18 = 4869684.50   (HALF_UP, 2dp)
widest disagreement at paying period 18:
  observed    5528535.20  = 552853520 minor units
  counterfactual 4869684.50 = 486968450 minor units
margin = 65,885,070 minor units
```

### 2.3 `EMI-DENOMINATOR-…` on P-03 — 334 minor units

Driver-derived and **independently re-derived here**; I agree with the driver digit for digit.

```
observed level installment on P-03 = 20.35  (row total, paying periods 2..5)
observed period-2 principal        = 19.77   interest 0.58   period 1 all-zero
r = 7.0/100 × 30/360 = 0.005833333333333333333
counterfactual EMI over n = 6: 100.00 × r / (1 − (1+r)^−6) = 17.01
   — and 17.01 is exactly the level installment the oracle OBSERVES on P-00,
     the same shape with six paying periods, so the counterfactual value is
     corroborated by an observation rather than resting on my arithmetic alone.
counterfactual period-2 principal = 17.01 − 0.58 = 16.43   (= 1643 minor units,
     again the value observed on P-00 period 1)
margin = 1977 − 1643 = 334 minor units on the first paying period alone
```
This is the strongest single grader in the pass-3b set and I agree with the driver's judgement
that it is the most valuable `graded_against` entry available here.

### 2.4 The two structural counterfactuals — real kills at zero money margin

Written in the shape the driver specified (`kind: "structural"`, `margin_minor: "0"`,
`divergent_cells` non-empty naming only non-money cells, `evidence` giving both values).

**`P-02` / `P-02b` — `MONTHEND-CONTINUE-FROM-CLAMPED-DAY`, capability `monthend.reanchor`.**
I verified the driver's correction against the capture before writing it. Row indices 0-based,
matching `diffSchedule`'s `row %d`:

| | P-02 observed | P-02 counterfactual | P-02b observed | P-02b counterfactual |
|---|---|---|---|---|
| [1] | 2024-02-29 | 2024-02-29 (agrees) | 2024-02-29 | 2024-02-29 (agrees) |
| [2] | **2024-03-31** | 2024-03-29 | **2024-03-30** | 2024-03-29 |
| [3] | 2024-04-30 | 2024-04-29 | 2024-04-30 | 2024-04-29 |
| [4] | 2024-05-31 | 2024-05-29 | 2024-05-30 | 2024-05-29 |
| [5] | 2024-06-30 | 2024-06-29 | 2024-06-30 | 2024-06-29 |
| [6] | 2024-07-31 | 2024-07-29 | 2024-07-30 | 2024-07-29 |

**The zero money margin is an OBSERVATION, not an assumption.** `P-00` (seed day 1), `P-02`
(seed 31) and `P-02b` (seed 30) are byte-identical in every money column of this same capture —
principal `16.43 / 16.52 / 16.62 / 16.72 / 16.81 / 16.90`, interest `0.58 / 0.49 / 0.39 / 0.29 /
0.20 / 0.10`, total interest `2.05` — because `daysInMonth=DAYS_30` / `daysInYear=DAYS_360` makes
a whole-month period 30/360 whatever the calendar dates. I re-ran that comparison myself and it
holds cell for cell. The counterfactual's own due dates are also whole-month steps (29→29), so it
too is packed at 30/360 and its money is unchanged. **The kill is entirely in `due_date` and
`from_date`.**

**`P-03` — `ROW-ORDER-SORT-BY-DATE-DISBURSEMENT-FIRST`, attributed to `schedule.core`.**
Observed order: `[0]` all-zero `REPAYMENT 1` (2024-01-01 → 2024-02-01), `[1]` `DISBURSEMENT`
(2024-02-01, principal 100.00), `[2..6]` `REPAYMENT 2..6`. The naive rule transposes `[0]` and
`[1]`; `kind` and `installment_number` then disagree on both rows while every money column of the
pair is unchanged. `divergent_cells: ["row_order"]`.

> **I checked, as instructed: there is no `contract_row_ordering` capability in
> `capabilities.json`** — the registry's 15 capabilities are schedule.core, monthend.reanchor,
> charges, holiday.adjustment, workingday.adjustment, installment.rounding.multiple,
> daysinyear.custom.strategy, daycount.actual.actual,
> interest.recognition.on.disbursement.date, fixed.length, downpayment,
> multi.tranche.disbursement, currency.zero.decimals, rounding.half.even,
> frequency.non.monthly. `contract_row_ordering` is an **invariant** name only. I attributed the
> entry to `schedule.core`, whose description already covers "repayment period windows", and I
> **did not invent a capability row**.

---

## 3. `unrecorded_fields` — every cell I marked, and the evidence

**Two cells per DISBURSEMENT row, on all 11 vectors: `installment_number` and `interest_minor`.**
22 cells in total; nothing else is marked anywhere.

The evidence is stronger than "the capture did not record it" — the **oracle has no such value**:

- `LoanSchedulePlanDisbursementPeriod` declares exactly four fields —
  `periodFromDate`, `periodDueDate`, `principalAmount`, `outstandingLoanBalance` — and its
  `periodNumber()` returns `null`. There is **no interest accessor at all.**
  [VERIFIED: `/Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/data/LoanSchedulePlanDisbursementPeriod.java:25-35`]
- `Capture3b.java:459-462` emits **every field the record carries**. So the absence is a property
  of the oracle's own type, not an omission by the capture harness.
  [VERIFIED: `.softhouse/capture/src/Capture3b.java:459-462`]
- DEC-1 says of a disbursement row: *"its `InterestMinor` is 0, and its `InstallmentNumber` is 0
  because it is not payable"* [VERIFIED: `contract.go:1508-1511`]. **That is a CONTRACT
  normalisation of a value the oracle never emitted, not an oracle observation.** Writing it into
  an `expect` block would be storing a derivation as an observation — precisely the defect
  `unrecorded_fields` exists to prevent, and precisely the argument the README makes about
  pass-3 disbursement balances.

Everything else is fully recorded: pass 3b gives `balance` on the DISBURSEMENT row on 12 of 12
(this is why 3b and not 3 is the promotion source), and every REPAYMENT row carries
`periodNumber`, `periodFromDate`, `dueDate`, `principal`, `interest`, `balance` and `total`.

**If the reviewer judges DEC-1's null→0 normalisation to be part of the response *shape* rather
than an observation, flipping those 22 cells to graded is a one-line change** to
`.softhouse/handoff/T8-promote-vectors.py` (delete the `row["unrecorded_fields"] = [...]`
assignment). I did not make that call myself because the store's own rule is written the other
way. **It is also entangled with defect D-5 below — see §5.2 before deciding.**

Two capture columns were deliberately **not** promoted, and both are worth naming:

- **`totalOutstandingBalance`.** On P-03's leading all-zero row it is `101.76` — principal
  `100.00` plus the full `1.76` of interest still to accrue, recorded before any payment. It is
  **not** an outstanding-principal figure and the frozen contract has no field for it. It is not
  routed into any principal column on any vector; the promoted
  `outstanding_principal_minor` is always the capture's `balance` cell. (Driver's warning,
  independently confirmed here by reading the row.)
- **`totalOutstandingAmount`.** Scale-0 `"0"` on every record, a hard-coded pass-through
  (`patterns.md`); no schema field, not promoted.

---

## 4. Verification

Toolchain: `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`, wrapped for auditability as
`.softhouse/handoff/T8-run-conformance.sh`.

| check | result |
|---|---|
| `go build ./...` | **exit 0** |
| `go vet ./...` | **exit 0** |
| `gofmt -l internal` | **only `contract/contract.go`** — the expected G-3 state, unmodified |
| float-shaped JSON number tokens under `.softhouse/vectors/` | **0** (string-stripped token scan over all 16 files) |
| `dec1_revision` / `oracle.fineract_commit` / threaded + ambient MathContext vs `PIN.json` | **11 of 11 agree**; `request.rounding` = `(19,19,HALF_UP)` on all 11 |
| never-promotable list | asserted per case in the script; `P-CAL` excluded |
| `.softhouse/conformance.sh` | **exit 2, `VERDICT: UNUSABLE — THIS IS NOT A PASS`** — correct, no implementation registered |
| `.softhouse/conformance.sh --prove` | **8 passed, 2 failed** — see §5, NOT 10/10 |
| `go test ./...` | **FAIL** — see §5, and note D-6: unsatisfiable by *any* promotion |
| transcription audit | **726 cells, 0 mismatches** on the two named vectors; **1,779 cells, 0 mismatches** across all 11 |

### 4.1 Verbatim before / after

**BEFORE** (measured by moving the 11 files out of the store and re-running):

```
    counterfactuals named by admissible vectors: 0
    UNBACKED in_graded_domain claims: monthend.reanchor, schedule.core
    parity vectors          PASS 0    FAIL 0
VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

**AFTER** (as shipped):

```
--- FILES THAT COULD NOT BE READ AS VECTORS (each one makes this run unusable) ---
    loanschedule/P-02-monthend-seed-day-31.json: decode: json: unknown field "kind"
    loanschedule/P-02b-monthend-seed-day-30.json: decode: json: unknown field "kind"
    loanschedule/P-03-disbursement-on-repayment-due-date.json: decode: json: unknown field "kind"

--- WHAT THIS RUN ACTUALLY GRADES (named wrong implementations killed) ---
    counterfactuals named by admissible vectors: 15
    schedule.core                              killed by LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT (×7), STRAIGHT-LINE-PRINCIPAL-DIVISION (×8)
    UNBACKED in_graded_domain claims: monthend.reanchor

--- SUMMARY ---
    parity vectors          PASS 0    FAIL 0
    refused                 0
    inadmissible            0
    harness errors          13
    cells compared          0 graded, 0 ungraded (never recorded by the capture)
    invariant violations    0

--- WHY THIS RUN CANNOT BE TRUSTED ---
    * NO IMPLEMENTATION REGISTERED: there is nothing to grade. …
    * THESE CAPABILITIES ARE MARKED in_graded_domain BUT NO PARITY VECTOR KILLS A NAMED WRONG
      IMPLEMENTATION FOR THEM: monthend.reanchor. …
    * NO PARITY VECTOR WAS GRADED. …

VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

With `--no-structural` (§6): 11 of 11 load, `inadmissible 0`, **21** counterfactuals named,
`UNBACKED … : monthend.reanchor`, still exit 2.

`cells compared 0 graded, 0 ungraded` is expected: the ungraded counter is incremented by
`diffSchedule`, which only runs when there is an implementation to diff against. The 22 ungraded
cells will appear in the count the moment T10 registers a port.

### 4.2 Transcription audit — the two vectors I checked cell by cell

`.softhouse/handoff/T8-transcription-audit.py` is written **independently of** the promotion
script (it does not import it and uses a different minor-unit converter — `Fraction(text) * 100`
with an integrality assertion, against the promotion script's string padding). It re-reads the
capture and compares every promoted cell, then re-derives all six property invariants over the
transcribed expectation.

- **`P-03-disbursement-on-repayment-due-date.json` — 123 cells compared, 0 mismatches.**
- **`P-MNT-50M-36x16pt8pct.json` — 603 cells compared, 0 mismatches.**

**Every cell matched** on both. Compared per row: `kind`, `from_date`, `due_date`,
`principal_minor` + its major text, `outstanding_principal_minor` + its major text,
`installment_number` (or its `unrecorded_fields` membership), `interest_minor` + its major text
(or unrecorded + empty), `observed_total_due_minor` (or null), and the oracle's own
principal + interest = its own total. Plus, per vector: the request's dates, principal, term,
frequency, currency, rate rational, both MathContexts, and total interest; and the invariants
`principal_portions_sum_to_disbursed`, `principal_amortizes_to_zero`, `balance_roll_forward`
(including P-03's pre-disbursement all-zero row), interest column vs observed total interest, and
window non-emptiness / contiguity / strict increase.

For completeness the same audit was run over the other nine: **1,779 cells total, 0 mismatches.**

No capture value anywhere in the 11 carries a significant digit beyond 2 decimal places; the
promotion script asserts this per cell and would have stopped rather than round.

---

## 5. Three harness defects, none in my scope to fix

### 5.1 D-4 (driver-raised, confirmed) — `graded_against` cannot express a non-money kill

Confirmed exactly as the driver described: `admit.go` rejects `margin_minor <= 0`
("a candidate this vector separates by zero is a candidate it does NOT kill"),
`conformance_test.go` asserts that rule with a `ZERO-MARGIN` case, and `vector.go`'s
`Counterfactual.MarginMinor` doc-comment specifies money-only and `> 0`.

**One correction to the driver's expectation, and it matters for sequencing.** The failure is
**not** an admissibility rejection. `LoadVector` decodes with `DisallowUnknownFields`, so `kind`
and `divergent_cells` fail at the **decode** step:

```
loanschedule/P-02-monthend-seed-day-31.json: decode: json: unknown field "kind"
```

Consequences the driver should relay to **T20**:

1. **The fix is not only in `admit.go`.** `Counterfactual` in `vector.go` needs the two new
   fields (`Kind string \`json:"kind"\``, `DivergentCells []string \`json:"divergent_cells"\``)
   or nothing will ever decode. An admissibility-only change will not land D-4.
2. A `LoadError` is **worse** than `INADMISSIBLE`: the vector is not merely ungraded, it is
   invisible — it contributes nothing to `CounterfactualCoverage`, which is computed over
   *admissible* vectors only, and `NewReplayImplementation` refuses the whole store on the first
   load error.
3. **Because I emitted `kind` only on structural entries** (the driver's spec permits omitting it
   on money entries), the blast radius is the minimum possible: **3 files depend on D-4, not 11.**
   `P-02`, `P-02b`, `P-03` await D-4; the other 8 load and back `schedule.core` today.
4. `P-03`'s 334-minor-unit money grader is currently lost with it, since the whole file fails to
   decode. §6 gives the one-command way to recover it if D-4 slips.

### 5.2 D-5 (NEW) — the replay implementation silently ignores `unrecorded_fields`

**`registry.go`, `NewReplayImplementation`.** For every expected period it does:

```go
principal, e1 := ep.PrincipalMinor.Int64()
interest,  e2 := ep.InterestMinor.Int64()
outstanding, e3 := ep.OutstandingPrincipalMinor.Int64()
if e1 != nil || e2 != nil || e3 != nil { bad = true; break }
…
if bad { continue }     // <-- the vector is SILENTLY DROPPED from the replay store
```

An **unrecorded** money cell is the empty string by construction — `admit.go` *requires* it
(`"…is marked unrecorded but carries a value"`) — and `MinorText.Int64("")` errors with
`empty monetary value`. So **every vector that honestly uses `unrecorded_fields` on a money cell
is dropped**, and then reports:

```
FAIL  expected a schedule of 7 rows, got error:
      replay self-test implementation: no vector in the replay store carries this request
```

which points a reader at the request key, not at the real cause. `admit.go` and `diffSchedule`
both honour `unrecorded_fields`; `registry.go` is the only consumer that does not, and mine are
the **first** vectors in the store to exercise the field (the hand-authored self-test fixture has
`"unrecorded_fields": []` on all three of its rows).

**Proved by controlled probe** (applied, measured, reverted — the shipped files are byte-identical
to the committed ones, `git status` clean after regeneration): clearing `unrecorded_fields` and
filling the two disbursement cells with DEC-1's `0` makes **every one of those FAILs disappear**.
That is decisive evidence that `unrecorded_fields`, and nothing about my transcription, is the
cause.

**Suggested fix for T20/T9** (I did not write it): honour `UnrecordedFields` in
`NewReplayImplementation` by substituting `0` for an unrecorded cell — the replay generator is
not a port, and the filled zero is never compared because `diffSchedule` skips unrecorded cells —
**and** turn the silent `continue` into a hard error, because a vector that cannot be converted
should make the run unusable rather than vanish.

### 5.3 D-6 (NEW) — `go test` asserts the store is empty of promotions

`conformance_test.go:120`:

```go
if s.ParityPass != 0 {
    t.Errorf("the store has no promoted capture yet, so ParityPass must be 0, got %d", s.ParityPass)
}
```

Under the D-5 probe (all 11 loading and replaying cleanly) this is the **only** remaining failure:

```
--- FAIL: TestHarnessGoesGreenAndRed/green_on_pristine_store
    conformance_test.go:120: the store has no promoted capture yet, so ParityPass must be 0, got 11
```

**So `go test ./...` cannot be green after ANY successful promotion at this harness revision,
regardless of D-4 and D-5 and regardless of what I wrote.** The assertion encodes the
pre-promotion world as an invariant. It needs to become "ParityPass equals the number of
admissible parity vectors" (or similar) as part of the same sequencing.

I did not touch it: it is in `nexus/`, T20 is in that package, and editing a harness assertion to
make my own output look green is the one thing this pipeline exists to prevent.

### 5.4 What this means for the acceptance criteria I was given

Stated plainly rather than buried:

- **`go test ./...` green — NOT MET, and not meetable.** As shipped it is red from D-4 (3 decode
  errors cascading into `TestStoreIsAdmissible`, six `TestHarnessGoesGreenAndRed` subtests and
  `TestStaleRefusalVectorIsDetected`). With `--no-structural` it is red from D-5 (4 subtests).
  With D-5 also neutralised it is red from D-6. Three independent harness gaps, all in `nexus/`.
- **`--prove` 10/10 — NOT MET.** Shipped: **8 passed, 2 failed** (`harness self-test over the
  pristine store` wanted 0 got 2; `one-minor-unit perturbation` wanted 1 got 2 — both from the
  D-4 decode errors). With `--no-structural`: **7 passed, 3 failed**, from D-5 — note exit 1
  (a FAIL) outranks exit 2, so D-5 masks two proofs that expected 2.
- **`conformance.sh` exit 2 with the UNBACKED line changed — MET**, for `schedule.core`.
  `monthend.reanchor` remains, and D-4 is exactly why.
- **The harness was never edited to produce a nicer verdict.** Nothing under `nexus/` is touched
  on this branch.

---

## 6. If D-4 slips: the one-command fallback

`python3 .softhouse/handoff/T8-promote-vectors.py --no-structural` regenerates the three affected
files with the structural entries **moved verbatim into `_note`** under a
`D-4 FALLBACK APPLIED … SUPPRESSED ENTRY >>>` banner, so nothing is lost and the suppression is
self-documenting. Measured in that state:

- **11 of 11 vectors load**, `inadmissible 0`, `refused 0`;
- **21** counterfactuals named, including P-03's 334-minor-unit grader;
- `UNBACKED in_graded_domain claims: monthend.reanchor` — unchanged, because the only graders for
  it are the structural ones;
- `--prove` 7/10 and `go test` still red, both from D-5.

Re-running the script with no flags restores the shipped state exactly. **Recommended merge
order remains the driver's: T20 (D-4 + D-5 + D-6) first, then this branch, then re-run.**

---

## 7. Things that contradict the README / `capabilities.json` / DEC-1 — flagged, not worked around

1. **README §"`unrecorded_fields`" vs `registry.go`.** The README presents `unrecorded_fields` as
   a fully supported, designed-for outcome. It is not honoured by the replay implementation
   (D-5). The README is right and the code is wrong; I wrote to the README.
2. **README §"Gradeability is NOT pair difference" vs the money-only `margin_minor`.** The README
   argues gradeability is "which named wrong implementations does this vector kill" — a claim
   with no monetary content — and then the schema admits only a money margin `> 0`. `P-02`,
   `P-02b` and `P-03` are the counterexamples the README's own logic predicts. Driver catch D-4;
   T20 owns the fix.
3. **`capabilities.json` → `monthend.reanchor.evidence` names `P-02` and `P-02b` as its graders.**
   That is **correct** — they do grade it — but it cannot be *expressed* today, so the harness
   calls its own registry's claim unbacked. Flipping `in_graded_domain` to `false` would silence
   the complaint and would be **wrong**: the capability really is graded, on dates. I changed
   nothing in `capabilities.json`, as instructed.
4. **No `contract_row_ordering` capability exists** (§2.4). Flagged, not invented.
5. **`request.time_zone` is declared, not observed.** The Path A seam takes `java.time.LocalDate`
   only and has no time-zone input; the capture JVM ran with `defaultTimeZone GMT`. Every vector
   carries `Asia/Ulaanbaatar` as its declared civil-date interpretation zone, and each `_note`
   says so. It grades nothing. `[UNVERIFIED: whether any Path A code path consults a default zone
   at all — I did not audit the seam for that, and no capture varies it.]`
6. **`request.currency.code` is upper-cased** from the capture's `"usd"`, as `admit.go` requires
   and the contract intends. Recorded in every `_note`. The MNT cases were already `"MNT"`.
7. **`rate_factor_scale: 19` comes from `PIN.json`**, not from the capture, which records a single
   `mathContextPrecision` that is both numbers. Recorded in every `_note`.

---

## 8. Claim status

- `[VERIFIED]` — the 11 transcriptions (1,779 cells re-checked by an independently written
  auditor, 0 mismatches); the disbursement-row field absence (Fineract record source + capture
  source, both re-opened and quoted); the P-00/P-02/P-02b money identity (re-run against the
  capture myself); the 334-minor-unit P-03 margin (re-derived, and corroborated by P-00's
  observed 17.01); D-4, D-5 and D-6 (each reproduced and, for D-5, isolated by controlled probe);
  every before/after harness figure quoted above (each from a run I executed on this branch).
- `[UNVERIFIED]` — that `LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT` and
  `STRAIGHT-LINE-PRINCIPAL-DIVISION` are what a real Go port would *plausibly* write. They are
  named in the brief's own candidate list and their margins are exactly re-derivable, but
  plausibility is a judgement, not a measurement.
- `[UNVERIFIED]` — that the pass-3b set contains **no** month-end counterfactual with a non-zero
  money margin. I looked for one and could not construct an honest one: under
  `DAYS_30`/`DAYS_360` every whole-month step is 30/360, and the one candidate that would break
  that (a port that rolls 31 Jan over to 2 March instead of clamping) needs the oracle's
  partial-period rate-factor mechanics, which I have **not** verified from source. I declined to
  price it rather than guess. **A shape that separates month-end handling in MONEY is a
  `TO_BE_CAPTURED` item, and ACT/ACT is where to look.**
- **No parity claim, no cutover claim.** `conformance.sh` exits 2 and says so in five places.

---

## 9. Files

Written (all inside the permitted scope):

- `.softhouse/vectors/loanschedule/P-*.json` — 11 promoted parity vectors.
- `.softhouse/handoff/T8-promote-vectors.py` — the promotion script (deterministic; re-running it
  reproduces the committed bytes exactly, `--no-structural` for the §6 fallback).
- `.softhouse/handoff/T8-transcription-audit.py` — the independent cell-by-cell auditor.
- `.softhouse/handoff/T8-run-conformance.sh` — toolchain-activating verification wrapper.
- `.softhouse/handoff/T8-promote-parity-vectors.md` — this file.

Not touched: `nexus/` (including `contract.go`), `.softhouse/capture/`, `PIN.json`,
`capabilities.json`, `README.md`.
