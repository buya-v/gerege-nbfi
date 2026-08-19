# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260819-170001`, oracle REACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP all fire. `fineract:latest` + `postgres:18.3`, both healthy, **never restarted**. Pinned
  checkout `426a23544` clean. PostgreSQL only; no prohibited engine anywhere.
- **Three workers dispatched, two completed and merged, one killed by a transient API 529.** No isolation
  violation, no scope breach, nothing left uncommitted.

## THE HEADLINE: **two structural blockers fell in one fire**

### 1. The no-Go-toolchain gap is CLOSED — and the ratified `contract.go` COMPILES

`go1.26.6 darwin/arm64`, sha256 asserted against go.dev's published value **before** extraction, installed
**repo-locally** at `GOROOT=.softhouse/toolchain/go`, **gitignored**, activated by
`. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`, reversible with one `rm -rf`.

The previous fire's refusal was right and was **not** overridden. Its objection was never *"is a toolchain
allowed"* (it is not RESERVED — no money, no endpoint, no third party); it was *"may an agent modify Buyan's
machine unattended"*. **Re-scoping the install location dissolved the objection without weakening it.**
Nothing outside this repo was touched; there is no Homebrew on this host and no `PATH` was changed.

**First ever compile of the ratified artefact:** `go build ./...` **exit 0**, `go vet ./...` **exit 0**.
`[UNVERIFIED: that the package compiles]` is **retired**. Ten review rounds of shape-grading are **not**
invalidated, and the worst-case discovery the previous fire warned about — a type error frozen into a
ratified artefact — **did not happen.**

> **A fresh clone will find no toolchain.** That is the price of not touching the host: one verified 65 MB
> fetch. If Buyan would rather have `go` on the host PATH, say so.

### 2. T7 — the bottleneck behind seven tasks — is DONE and MERGED

**T9, T10, T11, T13, T14, T15 and T20 are all unblocked for the first time in the program.**

`.softhouse/conformance.sh` + `.softhouse/vectors/` + `nexus/internal/apps/loanschedule/conformance/`
(22 files, 6,228 insertions, zero deletions, `contract.go` byte-identical: sha256 `0db73d4af996737d…`).

**The driver re-ran everything rather than accepting the report:**

| check | result |
|---|---|
| `go build ./...` / `go vet ./...` | **exit 0** / **exit 0** |
| `go test ./...` | **ok** — conformance 0.582 s |
| `gofmt -l internal` | **only** `contract/contract.go` — expected, gate **G-3** |
| `conformance.sh` (default) | **exit 2**, *"VERDICT: UNUSABLE — THIS IS NOT A PASS"* |
| `conformance.sh --prove` | **10 passed, 0 failed** |
| driver's own float scans | **0** float-shaped JSON numbers in the store; **0** float types in the Go tree |

**The harness refuses to claim all-pass over an empty corpus** — the single worst outcome its brief named.
It names its own untrustworthiness in words: no Go port registered, no parity vector promoted.

## NOTHING IS PROMOTED. NO CONTEXT IS AT PARITY. The harness says so out loud.

`.softhouse/vectors/` holds a schema, a pin, a capabilities table, one hand-authored `_selftest` fixture
(structurally barred from the parity count) and four contract-refusal vectors. **Zero parity vectors.**

## THE ONE THING THE NEXT FIRE SHOULD DO FIRST

**T8 — promote the capture corpus into the new store**, then **T9** (independent review of harness +
vectors). One trap its author must not discover late:

> **PROMOTION ORDERING MATTERS.** Promote a covering vector **before** flipping `in_graded_domain`, or the
> run is fatal with `UNBACKED in_graded_domain claims`. The harness already reports exactly that today for
> `schedule.core` and `monthend.reanchor` — which is honest, not a defect.

**T10, the port, is compilable for the first time.**

## The biggest transferable result: **pair-difference is the WRONG promotion filter** (T55-N2)

The intuitive rule — *"a vector discriminates a setting iff two captures differing only in that setting
differ in some cell"* — is **false in both directions**:

- `LB-DEC31` reports **0 cells** differing across the day-count setting, yet its observed value kills a
  no-arm port by **6,015 minor units**.
- `LB-F29CROSS` and `LB-MULTI3F` report **0 cells** on every pair, yet kill naive ports by **17,850** and
  **71,014** minor units.

**A non-zero-pair rule would have discarded the three best graders in the set.** The setting decides only
*whether* the arm fires, never its denominators. Gradeability is now the `graded_against[]` field: *which
named wrong implementations does this vector kill, and by how much.* **An all-products-identical capture is
not evidence of non-gradeability.**

## Driver catches this fire — each re-derived, none accepted on report

- **T55-N1 — CONFIRMED digit for digit.** `LB-DEC31` has a **zero** first segment and still grades the
  ACT/ACT arm by **6,015 minor units**: ARM `0/366 + 31/365` → **`22014.25`** (*observed* on p3/p4/p7 and in
  the re-runs); PLAIN `31/366` → `21954.10` (counterfactual). **The mechanism is the result:** PLAIN takes
  its denominator from the period-**start** year (366) while ARM assigns days to the year they land in (365),
  so **segment length is irrelevant — year lengths are what matter.** DEC-1's *"non-zero first segment"* is
  therefore known-wrong → **G-4**. Correct condition: **spans two calendar years of differing length.**
  Neither T55 nor the driver amended DEC-1; a ratified DEC-n is not an agent's call.
- **G-3 — `gofmt` wants to rewrite the frozen `contract.go`** (3 hunks, doc-comment list normalisation,
  semantically inert). **Not applied.** The risk is the failure mode, not the output: a `gofmt -w ./...` or a
  format-on-save would silently mutate a ratified artefact whose doc comments **are** the spec, and it would
  read as harmless formatting noise in review.
- **D-1** — the T50-N2 citation is **`:83`, not `:81`** (`:81` is a different method). Recorded because a
  reviewer checking `:81` would find unrelated code and might think the finding fabricated.
- **D-2 — NEW.** That line hard-wires **two** nulls, not one: `loanCharges` **and `holidayDetailDTO`**. The
  holiday arm is null-guarded at `DefaultScheduledDateGenerator.java:224`, so holiday/non-working-day
  adjustment is a **guaranteed silent no-op on Path A**. **Holiday conformance, like charge conformance, can
  only ever be graded on Path B.**
- **D-2a** — even on **Path B**, this generator adjusts only the **FINAL** period (`:61` guards `:66`).
  *"Adjust every date that lands on a holiday"* is the obvious and **wrong** thing for a Go port to write, and
  it would pass the **entire existing corpus** silently. `[UNVERIFIED: no Path B capture exists — capture it.]`

## What T55 established (33 Path B captures, all raw observed)

**6 discriminating pairs, 5 proven non-discriminating.** Determinism 33/33 byte-identical; negative tests
9/9 breaching; invariants I1–I7 on all 33; additive-only (`m_loan` 0→0, `m_product_loan` 21→21).

`LB-LEAPOUT` 27/65 (8,783 minor) · `LB-LEAPIN` 23/65 (97) · `LB-HALFYR` 23/65 (17,783) · `LB-DEC15IN` 11/43
(2,911) · `LB-DEC15OUT` 11/43 (3,105) · `LB-MULTI3` 11/43 (**41,328**).

- **Path A was disqualified on EVIDENCE, not assumption** — it drops the independent variable
  (`LoanApplicationTerms.java:304-351` never copies `:380` into `:291`): the exact *"capture through a seam
  that drops your variable"* trap.
- **T48's captures were already further along than believed** — `T48B-PUREB-p7` vs `-p4` (23/65, 97 minor),
  `T48B-YEAR` (157/285) and `T48B-QTR` (49/109) **already satisfy** T48-N4's promotion condition.
- **Not witnessed, labelled so:** no T55 shape separates precision 19 from 12, or HALF_UP from HALF_EVEN
  (29/36 agree at all of them; precision 8 does break it at 22/36). For those axes **`(19, HALF_UP)` is
  provenance, not discrimination.**

## Design decisions in the new store that bind every later task

- **Money is an integer STRING** in minor units. Most JSON readers (jq included) decode numbers to doubles,
  so an integral JSON *number* can be corrupted by the **reader**. No JSON number anywhere may contain
  `.`, `e` or `E`.
- **Probe-vs-parity is structural** — a parity vector records threaded **and** ambient MathContext, both
  `(19, HALF_UP)`, cross-checked against `request.rounding`. Relabelling a precision-12 probe fails **on the
  numbers it was produced at**, not on a label.
- **Seam blindness is DATA** (`capabilities.json`; absent ⇒ **default-deny**). A third blind spot is **one
  row** — every affected vector starts refusing with no vector file, schema migration or code change.
- **`unrecorded_fields`** — pass 3 never recorded the disbursement row's balance; filling it from the
  contract's rule would store a **derivation as an observation**.
- **The harness contains no schedule generation or date stepping** — the last due date is *read* from the
  vector, so **T10 cannot borrow an implementation from its own grader.**

## Task state

| Task | State |
|---|---|
| T1, T3, T3b, T4, T5, T6, **T7**, T16–T19, T21–T24, T26–T55 | **done** (45 of 57) |
| T25 | done_partial (oracle-free slice) |
| T2 | **parked** — unpark = gate **G-2** |
| **T8** | in_progress — **THE NEXT BOTTLENECK**: promotion is now possible and nothing is promoted |
| T9–T15, T20 | pending — **all unblocked by T7** |

## Open decisions for Buyan

- **None blocking.** Three gates are open and **not one of them parks the program**: **G-2** (one task),
  **G-3** (nothing — the workaround is in force), **G-4** (nothing — the corrected condition is already in
  force everywhere except DEC-1's own sentence).
- **G-3** — leave `contract.go` unformatted (driver recommends **A**), or authorise the inert `gofmt`?
- **G-4** — authorise a **wording-only** DEC-1 amendment: *"non-zero first segment"* → *"spans two calendar
  years of differing length"*. Declining leaves DEC-1 known-wrong on one sentence.
- **A repo-local Go toolchain now exists** and your machine was not touched. Say if you would rather it were
  installed on the host PATH instead.
- **The DEC-1 ratification remains reversible.**
- **RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
  facts. None is in Run 1's path.
