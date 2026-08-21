# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-134344`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **TIER 0 IS CLOSED — `done`.** Contexts **1 done / 18**.
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

## THE NEXT FIRE STARTS HERE

**Tier A, slice A2** — chart of accounts + product-to-account mapping + financial activity accounts.
6,636 LOC / 58 files, re-verified against the pin this fire. `tierA-gl-accounting` won context selection
because it **unblocks six downstream contexts** against loan-product-schedule's one; A2 is first because a
journal-entry vector has nowhere to post until a chart of accounts and a mapping exist.

| task | what | needs oracle |
|---|---|---|
| **A2-1** | behaviour extraction from pinned source, every claim cited | no |
| **A2-2** | independent review of A2-1 — **re-derive**, do not read and agree | no |
| **A2-3** | corpus mining + **RAW observed** capture from the live oracle | **yes** |
| **A2-4** | independent review of A2-3 — **attack the rig**, do not read it | some |
| **T149** | promote the **HALF_UP/HALF_EVEN tie** parity vector (explicit promotion mandate) | **yes** |

**A2-1's mapping-resolution answer is the gate on planning the A1 coder.** If it returns `[UNVERIFIED]`, the
posting engine cannot be planned yet — say so rather than proceeding on a guess.

**T149 is the highest-value money item outstanding.** `HALF_UP` is ratified, yet **0 of 46 vectors carry
either tie answer**, so nothing in the parity corpus would notice a port that inherited Fineract's stock
`HALF_EVEN`. Measured tie: `1,162,502.50 × 0.018 = 20,925.045` → `20925.05` (gerege) vs `20925.04` (default).

Then: **A2 coder** (only once vectors exist), then slices **A1** (journal posting, 11,535 LOC — check at plan
time whether it needs splitting again) and **A3** (period-end, 4,953).

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
