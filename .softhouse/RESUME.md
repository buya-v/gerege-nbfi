# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-134344`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **TIER 0 IS CLOSED — `done`.** Contexts **1 done / 18**. Slice **A2** analysis+capture merged.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**
- **Oracle**: UP. Pinned checkout `426a23544` clean. PostgreSQL only.
- Previous run archived to `.softhouse/runs/2026-08-17-run1-harness-schedule-poc.tasks.json`.

---

# THE HEADLINE: Buyan ratified P-5, and the hygiene sweep found the failure the hygiene rule names

**P-5** (`gates-proposed-answers.md`, 21 Aug 2026, committed six minutes before this fire started): *a finding
already covered by a passing vector is an **obligation**, not a blocker; **no third draft of a prose item**;
**money-changing findings are exempt**; then **close tier 0 and move to Tier A**.*

Applied its test — *does it change a number the reference oracle would emit?* — to every open task:

- **7 answered yes and stay live**, carried into the Tier A run: `T149`, `T143`, `T132`, `T145`, `T120`,
  `T116`, `T117`. **Three of them are holes in the FIRST non-negotiable in CLAUDE.md** (no floating point in
  any monetary path). These are not tier-0 leftovers to tidy — they are live money work.
- **26 recorded in the new `.softhouse/obligations.md`**, each naming *what grades it*, and closed
  `closed_as_obligation`. Where nothing grades an obligation the register says **Ungraded** in writing.

**The unmerged-branch sweep found six independent review documents that existed only on branches and not on
`main`** — T67, T79, T101, T127, T131, T135, 296 KB, including the review that refused the driver's own
bijection framing. `main` carried the *fixes those reviews forced* but not the *reasoning that forced them*.
For a pipeline whose central control is an independent reviewer who re-derives money math, **losing the review
is losing the control.** All six recovered; their raw capture dumps deliberately left on the branches per the
recipe+hash rule. The other 16 unmerged branches now have an explicit disposition in `obligations.md` §4.

---

## Tier 0 closure evidence — every line re-run by the driver on merged `main`, not taken on report

```
VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576 cells compared.
         probe = up · 0 invariant violations · 0 invariant assertions NOT RUN · 0 refused · 0 inadmissible
         go build / vet / test -count=1 → 0 / 0 / 0  (go1.26.6, repo-local toolchain)
         gofmt -l names exactly contract.go — EXPECTED under G-3 option A
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

Corpus: 42 parity + 4 contract-refusal + 1 self-test = 47 files. DEC-1 **revision 12** ratified and frozen.

**Merged this fire:** `T151` and `T152` — both had *completed on their branches* at the 08:00 fire, which then
hit its session limit without checkpointing. Verified on a **scratch merge** per P-24, not on the branches.

---

## Slice A2 — analysis and capture halves DONE and MERGED

Five workers dispatched, **five completed, zero live at exit.** No isolation violation, no scope breach.
Four branches merged after a **P-24 scratch merge** re-run by the driver: `probe = up`, `VERDICT PASS exit 0`,
42 parity, 0 invariant violations.

| task | verdict | what landed |
|---|---|---|
| **A2-1** | — | Behaviour extraction, ~60 cited claims. **The mapping-resolution answer is delivered**, which was the gate on planning the A1 coder. |
| **A2-2** | **MICRO-FIX** | All five priorities **re-derived from source and confirmed**. Of ~60 citations opened, one wrong path, **zero wrong line numbers**. "Slice A1 can safely build account resolution on §4." |
| **A2-3** | — | 327 live observations, 406 files hashed, **promoted nothing** (correct — it had no mandate). |
| **A2-4** | **MICRO-FIX** | Twelve defects, two of them P-22 "cannot fail" guards. Also **confirmed the corpus is real**: 24 of 27 recipes re-issue **byte-identically 17 h later**. |
| **T149** | **held** | See below — deliberately unmerged. |

## THE NEXT FIRE STARTS HERE

1. **T153 — review T149, then merge it.** T149 promoted **the first parity vector in the store ever observed
   through the RUNNING Fineract server** (all 42 others are the in-process Path A seam), conformance
   **42 → 43 PASS** on its branch. It is **deliberately not on `main`**: the driver dispatched it **without a
   paired reviewer** — its own plan-gate rule-1 violation — and a promotion into the graded corpus does not
   enter `main` unreviewed. `main` stays at 42; the 43rd arrives with its review. **Needs the oracle.**
2. **A2-5 — fix the capture rig before the next capture task uses it.** `cap.sh`'s transport-failure handler
   is **unreachable** under `set -e`, so **a stale body and stale status survive under a FRESH
   `captured-at-utc`** — a rig that can present old bytes as newly observed. Plus `manifest.py verify` passing
   vacuously on empty input, non-recursively, and not covering the plan, the rig, or itself.
3. **G-9 — decide the chart of accounts (PRODUCT).** Fineract ships **no default COA**. This **gates the A2
   coder**. Leaning: port the COA as *data*, launch with the minimal chart the vectors exercise.
4. **A2-6** — apply A2-2's micro-fix and three missing `[UNVERIFIED]` markers. No oracle. Good cloud-fire work.
5. **Then the A2 coder**, then slices **A1** (journal posting, 11,535 LOC — check at plan time whether it
   needs splitting again) and **A3** (period-end, 4,953).

## Two driver errors this fire, both caught by workers (P-20, now five and six)

- **T149 refuted its own brief.** *"0 of 46 vectors carry either tie answer **so** nothing would notice a
  `HALF_EVEN` port"* is **false by three vectors** — `T61-HE-A/B/C`, mutation `M7`, `parity PASS 39 FAIL 3`.
  The worker **refused to write the false sentence** into the vector's own note. T136 stated the count
  correctly with a *"but"*; T147 and then the driver replaced it with a *"so"*. Recorded as **P-13** and
  corrected at source in `obligations.md`, `RESUME.md` and `T147.md`.
- **A2-2's F-1 corrected the driver's own `OBL-A3-1` ruling** at the mechanism level: `closing_balance` is
  written **at insert from an UNSIGNED `SUM`**, not by the running-balance accumulator — which is gated on
  `IS NULL` against a `NOT NULL` column and whose only NULL-producing constructor has **zero callers**.
  Unreachable dead code that A3 would otherwise have faithfully ported.

**A2 scope was widened** 6,636 → **9,007 LOC / 79 files** after A2-1's B-1: the slice's own core types
(`GLAccount`, both enums, `AccountingConstants`, `PortfolioProductType`) live in `fineract-core`, and the
declared `fineract-provider` path does **not** hold the mapping helper at all. Left as written, the A2 coder
would have been rejected for going to get the types it cannot work without.

**Two findings that are design inputs to A1, not defects:** `acc_gl_journal_entry` stores **no
classification**, so posted entries **retroactively re-render** under a retyped account — an append-only
ledger displaying mutated history. The Go port must carry classification **on the entry**. And
`PortfolioProductType.fromInt` **permutes 3/4/5** relative to `getValue()`, while `CashAccountsForLoan` and
`AccrualAccountsForLoan` **collide at 22/24/25** with different meanings.

## STANDING INSTRUCTIONS

- **Invoke the harness with `bash`, never `sh`.** Exit 3 is the interpreter guard's **refusal** — *not* an
  oracle outage. Never park anything on it. Only exit **2** *with a printed probe line reading `down`* is the
  oracle-down condition, and **the probe line is not printed unconditionally** — test for its presence first.
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **Ship no guard you have not driven RED** (P-22) — at least five that structurally could not fail were found
  in tier 0, two of them inside the task sent to fix the previous one.
- **Verify post-merge assertions on a scratch merge** (P-24), against the **real pre-fix bytes**.
- **A parked list inside a task note is evidence of what was true when written, not a work queue** (P-17).
- **An obligation is not a proof.** `obligations.md` records findings; where it says *Ungraded*, nothing runs
  that would catch the thing, and citing it as established is the P-22 error again.

## Open gates — none blocks work today

- **G-4**, **G-5** (OPEN, ENGINEERING) — wording-only amendments to a **ratified** DEC-1. Not crossed: the
  skill's never-cross list names *any change to a ratified DEC-n*. Both corrected readings are already
  operationally in force. **Buyan decides.**
- **G-8** (OPEN) — two phenomena under one id (family A: a stale derived column; family B: a genuine
  non-amortization the Go port reproduces cell for cell). Options **(b)** and **(c)** amend the graded domain
  and are **hard user gates**. Closing tier 0 did not close or decide G-8.
- **N9 / N10** (OPEN) — only FU-1 (obligation T139) closes them; the disclosures on `main` saying so survive.
- **CUTOVER** — untouched, for every context. Needs vectors passing **and** a clean shadow-parity window
  **and** regulatory/parallel-run sign-off. The latter two do not exist.
