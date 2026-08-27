# T58 — closing the surviving mutations: 16 vectors promoted, three survivors killed

- **Run:** `2026-08-17-run1-harness-schedule-poc`  **Context:** `harness`  **Task:** T58 (`test_writer`)
- **Branch:** `softhouse/T58-close-surviving-mutations`
- **Raised by:** T11's adversarial review, findings **C-1** (promote the T39 drift captures) and **C-2**
  (capture the two shapes that separate the rounding-placement survivors).

> Throughout, **"the oracle" is the Fineract reference implementation** at the pinned commit.
> Oracle Database is a prohibited product in this program and appears nowhere in this work.
> Nothing here opens a database connection of any kind; PostgreSQL remains the only permitted engine.

---

## 0. The base — checked first, and it was wrong for the fifth time

The brief warned this had gone wrong four times in one fire. It had gone wrong a fifth.

`.softhouse/reviews/T11-go-port-adversarial-review.md` **did not exist in my worktree, and does not
exist on `main`.** T11's work sits unmerged on `softhouse/T11-go-port-review`, two commits ahead of
`main` @ `4f6390a`.

[VERIFIED: `git log --oneline -3` → `e103fe8 program: append fire 20260819-200001 history`;
`ls .softhouse/reviews/T11-go-port-adversarial-review.md` → *No such file*;
`git log --oneline -3 softhouse/T11-go-port-review` → `c3b7048`, `036e240` on top of `4f6390a`.]

`nexus/internal/apps/loanschedule/generator.go` **was** present (T10 is merged). So the failure this
time is one layer up from T11's own: not "the worktree is behind" but **"the named artefact was never
merged and the brief assumed it was."**

I cut `softhouse/T58-close-surviving-mutations` from `main` and merged
`softhouse/T11-go-port-review` into it before reading anything. That merge adds exactly one file — a
review document, 593 lines, no code
[VERIFIED: `git merge` → `1 file changed, 593 insertions(+)`, `create mode 100644
.softhouse/reviews/T11-go-port-adversarial-review.md`].

> **Driver finding T58-N0 (P2).** P-5's mechanism fix has to cover this case too: the dispatcher must
> verify the named artefact exists in the worker's tree **and** that the branch it lives on is an
> ancestor of the worker's base. Checking only the first would have passed here and I would have been
> reading `main`'s absence of a review as "there is no review".

**Baseline of the tree I started from** [VERIFIED: `/tmp/t58-baseline.txt`]:
`.softhouse/conformance.sh` → **PASS (exit 0)**, 13 parity vectors, 1,350 graded cells, 26 ungraded,
27 money kills + 3 structural, 0 inadmissible, 0 invariant violations.

---

## 1. What was promoted — 16 vectors, 13 → 29 parity

| vectors | source capture | what they close |
|---|---|---|
| `P-DRIFT-A` … `P-DRIFT-H` (8) | pass 3e | survivor 3 (`periodRatio`→`RepaymentEvery`), plus `M-M` and `M-P` |
| `P-ME-A` … `P-ME-D` (4) | pass 3e | the month-end special case; **`P-ME-A` also kills survivor 1** |
| `P-LAT-Q0a`, `P-LAT-MID` (2) | pass 3e | on-lattice and mid-month-start controls |
| `P-RND-S1-21021587pt50-6x21pt6pct` | pass 3d | **survivor 1**, the textbook `balance × rateFactor` |
| `P-RND-S2-3139845pt86-6x7pct` | pass 3d | **survivor 2**, the rate factor without the trailing `setScale` |

**Result** [VERIFIED: `/tmp/t58-final.txt`]:

```
parity vectors          PASS 29   FAIL 0      (was 13)
inadmissible            0
cells compared          2354 graded, 58 ungraded   (was 1350 / 26)
kills named             86 money, 7 structural     (was 27 / 3)
invariant violations    0
VERDICT: PASS (exit 0)
```

Parity rose by exactly 16, the number promoted.

### What I declined to promote, and why

| capture case | why not |
|---|---|
| `T39-CAL` | Ran at MathContext **(12, HALF_UP)** in **USD**, not the production (19, HALF_UP). It is a rig calibration and is on `PIN.json`'s `never_promotable_capture_case_ids`. Not promotable, and the harness's own probe guard would refuse it on the numbers even if the list were incomplete. |
| `T39-CTL-1` | **A duplicate request.** MNT 1,014,632.00 / 6 × 7.0% / start == disbursement == 2024-01-01 is byte-for-byte the request already promoted as `P-EMI-6-1M014632` (T57, from pass 3c). Promoting it would raise the parity count without adding one graded behaviour. Its value is as corroboration and it is recorded as such below, not as a vector. |
| `P-CAL`, `P-CAL-P00`, `P-CAL-EMI6` (pass 3d / 3e) | Rig calibrations by role. Their whole purpose is to reproduce a committed observation; promoting a calibration would make the corpus grade itself. |

**Six honest vectors would have beaten eight fabricated ones. Sixteen is what the evidence carried** —
every one of them separates at least one named wrong implementation, measured, with a positive margin
or a non-empty set of divergent date cells.

---

## 2. Part 1 — the T39 evidence, and the reason it was RE-OBSERVED rather than transcribed

T11's finding C-1 said the evidence to kill survivor 3 was already in the tree and needed no oracle
run. **That was true, and I could not use it directly.** The reason is a finding in its own right.

### Finding T58-N2 (P1) — a D-5-class harness defect, one layer down

T39's harness `CapturePeriodRatio.java` records **four fields on a DISBURSEMENT row** —
`{type, fromDate, dueDate, principal}` — and **not that row's outstanding balance**
[VERIFIED: every one of the 16 records in `t39-periodratio.json` has exactly those four keys on
period 0]. A vector transcribed honestly from it must therefore put
`outstanding_principal_minor` in that row's `unrecorded_fields`. I built all fourteen that way first.

The store's README says of `unrecorded_fields`: *"The replay implementation answers `0` for it and
**nothing compares that placeholder**."* **The invariant layer does compare it.**
`CheckInvariants` takes only the returned `contract.Schedule` and has no access to the vector's
`unrecorded_fields`, so in `--self-test` mode `balance_roll_forward` reads the replay's `0` and fires:

```
--- P-LAT-Q0a : FAIL
    invariant balance_roll_forward VIOLATED: row 0 DISBURSEMENT: outstanding 0 != principal advanced 120000000
```

[VERIFIED: 14 of 14 T39-sourced vectors failed exactly this way; `go test ./...` went red and
`--prove` fell to 10/20. The *plain* conformance run against the Go port was unaffected —
`balance_roll_forward` held 30 of 30 — because a real port returns the real balance.]

This is **D-5's defect one layer down**: D-5 taught the *cell comparison* to skip an unrecorded cell;
the *invariant* layer still grades the placeholder. It is a **false FAIL** — about a capture's column
set, not about any implementation.

**I did not exempt the invariant.** `invariant_exemptions` would have made the run green and quietly
removed a check that currently passes on every vector in the store — the exact "make the harness
easier to pass" move the brief forbids. **The correct fix is in the harness** (thread the vector's
`unrecorded_fields` into `CheckInvariants`), and I am forbidden to edit the harness, so it is raised
here rather than applied.

### What I did instead — pass 3e

The oracle was up. I **re-observed all fourteen shapes** through the pass-3b/3c/3d rig, which *does*
record `outstandingLoanBalance` on the disbursement row. New artefacts:

- `.softhouse/capture/src/Capture3e.java`, `.softhouse/capture/src/run-pass3e.sh`
- `.softhouse/capture/out/capture-prod3e-{raw.json,raw.txt,log.txt,stderr.txt,attestation.json,classpath-sha256.txt,sha256.txt}`

Every precondition check of pass 3d — all twelve — carried over, **not one weakened**. The only
structural addition to the harness is a `prodDates(...)` builder that takes distinct schedule-start
and disbursement dates; every other field of every case is C-00's, unchanged.

### Cross-harness reproduction — the strongest single result in this task

Because pass 3e asks T39's requests field for field, the two observations are comparable. I compared
them, by meaning rather than by key name (T39 spells them `fromDate`/`fee`/`penalty`; pass 3e
`periodFromDate`/`feeAmount`/`penaltyAmount`), on the oracle's **own emitted characters** with no
parsing and no normalisation:

```
CROSS-HARNESS REPRODUCTION -- pass 3e (Capture3e.java) against T39 (CapturePeriodRatio.java)
  case pairs compared      14
  schedule rows compared   134
  cells compared           1698
  DIFFERENCES              0
```

[VERIFIED: `.softhouse/capture/t58-counterfactuals/src/cross-harness-t39-vs-pass3e.py`, exit 0.]

**Two independent Path A harnesses, two fires apart, agree on every cell either of them recorded.**
T39's observation is corroborated rather than discarded, and the promoted vectors cite the capture
that actually recorded every cell they grade.

`T39-CTL-1` is included in that reasoning separately: its request is `P-EMI-6-1M014632`'s, and pass
3e's own calibration `P-CAL-EMI6` reproduces pass 3c's observation of that request digit for digit.

---

## 3. Part 2 — the two oracle captures, and what the oracle said about T11's prediction

`.softhouse/capture/src/Capture3d.java` + `run-pass3d.sh`, 5 cases: three rig calibrations and the
two named shapes. **All eleven of pass 3c's precondition checks carried over unweakened, and one was
added.**

### The calibrations — what they reproduced, and that they matched

| calibration | reproduces | from | at | result |
|---|---|---|---|---|
| `P-CAL` | pass 3b's `P-CAL` | `capture-prod3b-raw.json` (sha `8d23c48c…`) | (12, HALF_UP), USD | **inputs and observed both identical** |
| `P-CAL-P00` | pass 3b's `P-00` | `capture-prod3b-raw.json` | **(19, HALF_UP)**, USD | **inputs and observed both identical** |
| `P-CAL-EMI6` — **added by pass 3d (check 12)** | pass 3c's `P-EMI-6-1M014632` | `capture-prod3c-raw.json` (sha `cae566d3…`) | **(19, HALF_UP), MNT** | **inputs and observed both identical** |

The twelfth check exists because the two inherited calibrations are both **USD 100** shapes. Check 12
calibrates on the **currency, magnitude and term the new candidates actually use**, and its target is
a case whose observation is *already a promoted parity vector* — so a drift there would mean this run
and the committed corpus disagreed about the same request. It did not.

**If any calibration had failed the run would have been refused outright and nothing else from it
would be trustworthy.** None did — in pass 3d or in pass 3e.

`capturesCanonicalSha256` was **identical across two independent runs** of pass 3d
(`2e1f7c7e9bb2c256934d7cc250566da701300c0aedc69342105a0d0054c947e0`) and across two of pass 3e
(`5bd3105abf319566cd89063294f97f81bdc3480193063682d2580a9d1d7d94c8`). The oracle container was
**never restarted** (`Up 29 hours (healthy)` at the start); these passes run the image in a fresh
throwaway container against the in-process embeddable seam and touch the running instance not at all.

### Did the oracle confirm T11's prediction? — YES, cell for cell

T11's predicted values were treated as a **hypothesis** and never transcribed. Here is the oracle's
answer against T11's prediction:

**`MNT 21,021,587.50, 6 × monthly, 21.6 %`** (T11 §4.4 table)

| row | column | T11 predicted (correct reading) | **oracle OBSERVED** | agree? |
|---|---|---|---|---|
| 1 | principal | `334921682` | `3349216.82` = **334921682** | ✔ |
| 1 | interest | `37838857` | `378388.57` = **37838857** | ✔ |
| 2 | principal | `340950272` | `3409502.72` = **340950272** | ✔ |
| 2 | outstanding | `1426286796` | `14262867.96` = **1426286796** | ✔ |
| 6 | principal | `366169491` | `3661694.91` = **366169491** | ✔ |

**`MNT 3,139,845.86, 6 × monthly, 7.0 %`** — T11's headline claim was *"interest MNT 15,307.35 vs
15,307.36"*.

| row | column | T11 predicted (correct reading) | **oracle OBSERVED** | agree? |
|---|---|---|---|---|
| 2 | interest | `15307.35` | **`15307.35`** | ✔ |
| 2 | principal | `51873628` | `518736.28` = **51873628** | ✔ |
| 2 | outstanding | `210538172` | `2105381.72` = **210538172** | ✔ |
| 3 | outstanding | `158361948` | `1583619.48` = **158361948** | ✔ |

> **The oracle CONFIRMED T11's prediction on every cell T11 named, in both shapes. It contradicted
> nothing.** Both shapes DO separate their target mutation, in a payable amount, on the oracle's own
> numbers. The folklore is over: a rounding step twice dismissed in this program's history as
> "redundant" and twice found to be a money defect is now **observed** to be one, on a request.

---

## 4. The derived margins — arithmetic shown, derived from the captures, not transcribed from T11

Every margin below was **measured**, not asserted: a scratch copy of the port at `/tmp/t58mut` with
exactly one named change, run on the vector's own request, compared cell by cell against the
capture's OBSERVED value.
[`.softhouse/capture/t58-counterfactuals/`, `out/t58-counterfactuals-pass3{d,e}.json`]

**The control that makes the margins mean anything:** with every change switched **off**, the model
reproduces **508 of 508** graded money cells across the 20 in-domain capture cases, `baselineMismatches`
**0**. A counterfactual model whose unmutated form did not reproduce the oracle would be measuring its
own defect and calling it a margin.

| survivor / counterfactual | worst cell | arithmetic | margin |
|---|---|---|---|
| **S-3** `periodRatio` → `RepaymentEvery` | `P-DRIFT-D` period[14] `outstanding_principal_minor` | `\|3428726651 − 3419691994\|` | **9,034,657** minor = **MNT 90,346.57** |
| **M-M** seed always the schedule start | `P-DRIFT-D` period[29] `outstanding_principal_minor` | `\|1240755688 − 68655501\|` | **1,172,100,187** minor = **MNT 11,721,001.87** |
| **M-P** re-anchor guard `>=28` → `>28` | `P-DRIFT-D` period[14] `outstanding_principal_minor` | `\|3428726651 − 3419518341\|` | **9,208,310** minor = **MNT 92,083.10** |
| **S-1** textbook `balance × rateFactor` | `P-RND-S1` period[5] `outstanding_principal_minor` | `\|366169491 − 366169487\|` | **4** minor |
| **S-1** again, on a capture already in the tree | `P-ME-A` period[3] `principal_minor` | `\|64931114 − 64931113\|` | **1** minor |
| **S-2** rate factor without the trailing `setScale` | `P-RND-S2` period[2] `principal_minor` | `\|51873628 − 51873627\|` | **1** minor |

### These do not match T11's numbers, and that is correct

T11 reported M-M at **MNT 8,545,743.02**, S-3 at **MNT 62,595.93** and M-P at **MNT 44,960.29**. Mine
are larger. **This is not a disagreement.** T11 measured on its own constructed probe shapes (§4.1
`S1`/`S2`/`S4`, e.g. 36 × **16.8 %** on MNT 50M); I measured on the shapes the oracle was actually
asked about, which include `P-DRIFT-D` at 36 × **21.6 %** on MNT 50M. Different shape, different
margin. I derived mine from the captures rather than transcribing T11's, exactly as the brief
required, and the two are consistent in sign, mechanism and order of magnitude.

### Finding T58-N1 — survivor 1 was killable without an oracle run, and nobody had checked

T11 recorded S-1 and S-2 as separable only by a 6,000-shape sweep and priced them at one oracle run
each. **`T39-ME-A` — MNT 3,924,149.00 / 6 × 16.8 % / start == disbursement == 2024-01-31, captured two
fires ago and sitting unpromoted in the tree — separates the textbook reading on six of its graded
cells by one minor unit.** [VERIFIED: `t58-counterfactuals-pass3e.json`, `P-ME-A`, `TEXTBOOK` 6 cells,
max margin 1; and the acceptance test below, where `P-ME-A` goes red under the mutation.]

No contradiction with T11 — T11 replayed the T39 captures only for *baseline agreement* and never ran
the rounding-placement counterfactuals against them. But the lesson is the one T11 itself drew about
C-1, sharpened: **before pricing a capture, run the counterfactual against the captures you already
have.** The oracle run for S-1 turned out to be a confirmation, not a necessity. It is still worth
having: `P-RND-S1` separates the reading by **4** minor units on an interest cell of installment 1
rather than by 1 on a mid-schedule principal, and it does so on an ordinary on-lattice loan.

---

## 5. The acceptance test — verbatim before and after

For each mutation: apply it to the port, run with the 16 new vectors **moved aside** (BEFORE), then
with them **restored** (AFTER), then `git checkout` the port and confirm the tree is clean.
[Script `/tmp/t58_accept.sh`, mutations `/tmp/t58_mutate.py`; transcripts `/tmp/t58-acc-*-{before,after}.txt`.]

### 1. `periodRatio` → `RepaymentEvery`

```
BEFORE  parity vectors PASS 13   FAIL 0
        VERDICT: PASS (exit 0) — 13 parity vectors match the pinned reference oracle, 1350 cells compared.
        EXIT=0
AFTER   parity vectors PASS 21   FAIL 8
        VERDICT: FAIL (exit 1) — 8 mismatched vector(s), 8 invariant violation(s).
        EXIT=1
```
Named cell, from `P-DRIFT-A`:
`row 2 interest_minor: expected 1930345 minor units, got 1812853 (delta -117492)`.

### 2. textbook `balance × rateFactor` (three rounded operations collapsed into one)

```
BEFORE  parity vectors PASS 13   FAIL 0
        VERDICT: PASS (exit 0) — 13 parity vectors match the pinned reference oracle, 1350 cells compared.
        EXIT=0
AFTER   parity vectors PASS 27   FAIL 2
        VERDICT: FAIL (exit 1) — 2 mismatched vector(s), 2 invariant violation(s).
        EXIT=1
```
Named cells:
`P-RND-S1 row 1 interest_minor: expected 37838857 minor units, got 37838858 (delta 1)` … through to
`row 5 outstanding_principal_minor: expected 366169491, got 366169487 (delta -4)`; and
`P-ME-A row 3 principal_minor: expected 64931114 minor units, got 64931113 (delta -1)`.
`splits_sum_to_whole` also fires on both.

### 3. rate factor without the trailing `setScale`

```
BEFORE  parity vectors PASS 13   FAIL 0
        VERDICT: PASS (exit 0) — 13 parity vectors match the pinned reference oracle, 1350 cells compared.
        EXIT=0
AFTER   parity vectors PASS 28   FAIL 1
        VERDICT: FAIL (exit 1) — 1 mismatched vector(s), 1 invariant violation(s).
        EXIT=1
```
Named cells, `P-RND-S2`:
`row 2 principal_minor: expected 51873628 minor units, got 51873627 (delta -1)`,
`row 2 interest_minor: expected 1530735 minor units, got 1530736 (delta 1)`,
and the outstanding balance on rows 2–5.

**The port was restored after every mutation** and `git status --porcelain nexus/` was **empty** each
time. The committed tree passes: `.softhouse/conformance.sh` → PASS, exit 0, 29 parity, 0 inadmissible.

---

## 6. Verification

| check | result |
|---|---|
| `.softhouse/conformance.sh` | **PASS (exit 0)** — parity **13 → 29** (+16, exactly the number promoted), `inadmissible 0`, 2,354 graded cells, 0 invariant violations |
| `go build ./...` | clean, exit 0 |
| `go vet ./...` | clean, exit 0 |
| `go test ./...` | `ok` on both packages, exit 0 |
| `gofmt -l` | flags **only** `internal/apps/loanschedule/contract/contract.go` — expected under gate **G-3**; not touched |
| `--prove` | **19 of 20.** The one failure is diagnosed below and is caused by the promotion *adding* coverage |
| float scan over `.softhouse/vectors/` | **36 JSON files, 0 bare number tokens containing `.`, `e` or `E`** (string literals stripped first, so a decimal inside a `*_major_text` or an evidence string is not a false positive) |
| transcription audit | **1,932 cells checked, 1,932 matched, 0 discrepancies**, over 16 vectors and 148 schedule rows |
| frozen artefacts | `contract.go`, `PIN.json`, `capabilities.json`, the conformance package and `conformance.sh` **all unmodified** [VERIFIED: `git diff --stat main -- …` empty] |

### The transcription audit

`.softhouse/handoff/T58-transcription-audit.py` was **written against the vectors, not with them**. It
shares no line with the promotion script, and its major→minor converter is a deliberately different
second implementation: `decimal.Decimal` with the exponent read off `as_tuple()` and the coefficient
scaled by integer multiplication, versus the promoter's string padding. Neither constructs a float.
It re-derives, from the referenced capture alone: the whole request (dates, principal, term, rate as
an exact `Fraction`, currency, MathContext, pinned commit), every money cell in minor units, every
`*_major_text` against the oracle's own characters, every date, row kinds, installment numbers,
per-row observed totals and the plan-level total interest — **and** that every cell marked
`unrecorded_fields` really is absent from the capture and that no recorded cell was silently dropped.

```
vectors audited 16 | schedule rows audited 148 | cells checked 1932 | cells matched 1932 | discrepancies 0
```

### Finding T58-N3 (P2) — `--prove` 19/20, and it is a stale proof, not a defect

**Proof 19** (`T9-F1b: withdrawn cells STOP backing the kill`) fails. It is the only failure.

It builds a store in which `P-02` and `P-02b` withdraw the nine date cells that back
`MONTHEND-CONTINUE-FROM-CLAMPED-DAY`, and then asserts on the report text:

```sh
grep -q 'UNBACKED in_graded_domain claims: monthend.reanchor' || ok19=0
grep -q 'killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY' && ok19=0
```

Both assertions assume **`P-02` and `P-02b` are the only vectors backing `monthend.reanchor`.** After
this promotion they are not: the report line now reads

```
monthend.reanchor   killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY ×9, … [structural] ×3,
                             MONTHEND-REANCHOR-GUARD-STRICTLY-GREATER-THAN-28 ×7, … [structural]
```

— 20 claims from the 14 new vectors. So the capability is no longer UNBACKED and the `killed by` line
does not disappear. [VERIFIED: `/tmp/t58_diag19.sh` reproduces the mutated store and prints exactly
this; `UNBACKED` appears **nowhere** in that run's output.]

**Decisive evidence that this is staleness and not a defect:** with the 16 new vectors moved aside and
nothing else changed, `--prove` is **20 passed, 0 failed, exit 0**
[VERIFIED: `/tmp/t58_prove_pre.sh` → `PROOFS: 20 passed, 0 failed`]. The proof fails *because coverage
was added*, which is the outcome the corpus exists to produce.

This is **finding D-6, fourth recurrence, in the same proof**. Commit `4f6390a` de-staled this proof's
frozen *count* with the comment *"a literal here would go stale on every promotion (finding D-6, third
recurrence). Assert the PROPERTY, never a frozen count"* — and left a frozen **sole-backer assumption**
three lines above it.

**I did not fix it, and the two ways to make it green from my side are both worse than leaving it red:**

- **Editing `conformance.sh`** is forbidden by this task's brief, and "the harness must never be made
  easier to pass" is the rule I would be closest to breaking.
- **Dropping the `monthend.reanchor` counterfactuals from the 14 new vectors** would make it green — I
  checked which claims cause it — but it would discard 20 measured, honest kills, including
  `P-ME-C`, **the only vector in the store that grades the `dateDay >= 28` comparison** (structurally:
  nine dates move, no money does). Gutting real grading to satisfy a stale proof is a false green.

**Recommended fix (harness owner's call, one line of judgement):** in proof 19, either build the
`withdrawn-kill` store from a store containing only `P-02`/`P-02b`, or assert the property at the
**vector** level — *this vector no longer credits the kill* — instead of at the capability level, which
is now backed by many vectors and always will be. The proof's actual claim is about a vector's cells,
not about a capability's total coverage.

---

## 7. Contradictions, flagged rather than reconciled

- **Against T11 — none on the money.** The oracle confirmed its predicted cells exactly (§3). Its
  reported margins for S-3/M-M/M-P differ from mine because they were measured on different shapes,
  and I say so rather than quietly adopting either number (§4).
- **Against T11 — one on the pricing.** T11 priced S-1 at one oracle run. `T39-ME-A`, a capture already
  in the tree, kills it (§4, finding T58-N1). T11 did not claim otherwise; it simply never ran that
  counterfactual against those captures.
- **Against the store README — one, and it is a defect.** *"The replay implementation answers `0` for
  it and nothing compares that placeholder"* is **false today**: `CheckInvariants` compares it
  (finding T58-N2). The README describes the intended behaviour; the harness does not implement it at
  the invariant layer.
- **Against `conformance.sh`'s own D-6 comment — one.** Proof 19 still carries a frozen corpus-shape
  assumption three lines above the comment warning against exactly that (finding T58-N3).
- **Against DEC-1 — none.** No vector required an amendment, no refusal retired, `dec1_revision` stays
  12, and `contract.go`'s bytes are untouched so `PIN.json`'s `contract_sha256` still holds.

## 8. Standing notes for the next round

- **T11's review is still unmerged on `softhouse/T11-go-port-review`.** This branch merges it; if this
  branch is not taken, that review is still not on `main`.
- T11's port findings **F-1** (ignored `context.Context`) and **F-2** (superlinear cost, unbounded
  `NumberOfRepayments`) are untouched by T58 — this was a corpus task, and the port was mutated only in
  scratch and restored every time.
- T11's **C-3** (M-A, M-B, M-D, and the M-F/M-K strict-inequality boundary — unfinished searches) and
  **C-4** (a zero-rate capture, which would settle **G-5** on evidence) remain open. C-4 is one oracle
  run and the rig is now three passes deep; pass 3f is a case-list edit.
- Of T11's nine surviving money-moving mutations, **five are now killed by promoted vectors**
  (S-1, S-2, S-3, M-M, M-P). M-A, M-B, M-D and M-L survive; M-F/M-K were never located.

---

*A green conformance run means "matches the reference oracle on captured vectors, within the graded
domain". It has never meant safe to cut over. **Cutover remains a `user` gate.***
