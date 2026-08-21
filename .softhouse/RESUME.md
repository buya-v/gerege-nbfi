# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260821-054355`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- Contexts **1 done / 18**. Tier 0 closed. Active run `2026-08-21-run2-tierA-gl-accounting-A2`, slice **A2**.
- **Oracle**: UP. Pinned checkout `426a23544` clean. PostgreSQL only.
- **⚠ THIS SECTION IS A MID-FIRE SAFETY CHECKPOINT.** Two workers were still live when it was written
  (**T154** no-float guards, **A2-10** review of A2-5). If the fire died before the final rewrite, treat
  both as **killed mid-flight**: check `softhouse/T154-nofloat-guards` and `softhouse/A2-10-review-a2-5`
  for commits, mark them `needs_retry` with completeness unverified, and DO NOT assume they finished.

---

# THE HEADLINE: `main` is at 43 parity vectors, and the 43rd arrived WITH its review

**`main` moved 42 → 43.** T149's vector — the first in the store ever observed through the **running
Fineract server**, where all 42 others come from the in-process Path A seam — was held unmerged last fire
because the driver had dispatched it **without a paired reviewer**, its own plan-gate rule-1 violation.
**T153 is that review, and it is done: MICRO-FIX → APPROVED, no defect in any money path.** The promotion
entered `main` with its review, never without. The violation is closed.

T153 did not take T149 on report. It re-observed the tie live under **its own** request sha
`b126725a…` and got responses **byte-for-byte identical** to T149's committed captures on both arms — and
got a *cleaner* counterfactual than T149 had (same request bytes at the **same product id 1** on both
tenants). It ran two checks T149 never did: **all twelve periods re-derived in exact rational arithmetic**
(12/12 + total agree, EMI 10858003), and transcription checked **in both directions** (0 mismatches, every
`unrecorded_fields` cell verified genuinely absent).

**Driver re-ran conformance on merged `main` after applying the micro-fix** — not taken on the reviewer's
report either:

```
probe line PRESENT at line 1: conformance: reference oracle (https://localhost:8443/...) probe = up
VERDICT: PASS (exit 0) — 43 parity vectors, 5664 cells graded
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**The micro-fix the driver applied**: two sentences claimed a tighter control than they held —
(1) "differing in exactly one input" ignored that `tenants.timezone_id` **also** differs (Asia/Kolkata vs
Asia/Ulaanbaatar); inertness `[UNVERIFIED]`, since testing it means **writing** to the shared oracle;
(2) "ICPM is the only remaining difference" ignored that the start year differs too (2024-01-01 vs
2026-01-01) — **T153 measured the missing control and found 0 money-cell differences**, so the conclusion
survived and only the wording was wrong. T153's coverage caveat was written **onto the vector**: it
**cannot discriminate day count** (products 9, 11 and 1 all return digest `39f56dc2…`), so `FIXED_30_360`
is TRUE but must never be read as coverage.

## G-9 CLOSED — and closing it exposed that the A2 coder had never been planned at all

**Decision** (PRODUCT, `chosen_by: agent`, Buyan may reverse): the chart of accounts is **DATA, not code**;
launch with the minimal chart the vectors exercise; an FRC-aligned production chart is a separate data-only
deliverable downstream of CUTOVER. Porting "the chart" as Go code would invent a structure Fineract does not
have, and **an invented structure cannot be graded against the oracle**.

Premise **re-derived by the driver**, not taken from A2-1: across the two tenant seed changelogs,
**0 of 1,918 `<insert>` elements target `acc_gl_account`**; across all of `db/changelog/tenant/parts/` the
table appears only as `createTable` + two `createIndex`. Fineract ships the table and no rows.

**Two consequences that were not visible before:**
1. **The decision alone does not unblock the coder.** The whole A2 capture holds **four** GL accounts, **all
   ASSET**, while `LoanProductDataValidator.java:663-710` makes **nine** mandatory for cash-based accounting
   (twelve for accrual, `:761-777`). **The corpus holds 2 of the 9.** Raised as **A2-7**.
2. **The A2 coder did not exist in the plan.** G-9 had blocked it from being *written*, not just run.
   Registered as **A2-8** with reviewer **A2-9**.

## THE NEXT FIRE STARTS HERE

1. **Adjudicate T154 and A2-10** (see the warning above — verify they actually finished).
2. **A2-7** — capture the seven missing mandatory GL accounts. **Needs the oracle.** Depends on A2-5.
3. **A2-8 → A2-9** — the A2 port itself, then its independent review.
4. **T155** — review of T154. **T156** — the unguarded `mv` that leaves a green `PASS 42`.
5. Remaining carried money tasks: **T116**, **T117**, **T145** (all collide with `.softhouse/capture/`;
   serialise them behind A2-5/A2-7).

## Driver self-catches this fire (P-20 — worth measuring, the count keeps rising)

- **A2-5 was dispatched as a `coder` with no paired reviewer** — the *same* plan-gate rule-1 violation that
  left T149 unmerged. Caught mid-flight by running the plan gate over the driver's own additions; **A2-10**
  registered while A2-5 was still running.
- **T153's `files_hint` was too narrow for the task the driver commissioned** — `.softhouse/reviews/` alone,
  while the brief *ordered* it to re-observe from the live oracle, which necessarily writes captures. The
  worker was right to write them; the plan was wrong. Not charged against the worker.
- **The driver re-derived its own brief before dispatching it.** A2-8's three "already measured" traps were
  re-checked against source: both A2-1 claims **confirmed exactly** (`fromInt` is a 3-cycle 3→5→4→3; the
  enums collide at exactly 22/24/25, and at code 24 an INCOME member faces an EXPENSE one, so a cross-map
  hits the wrong **side**). The check found **a third hazard nobody had recorded**: the name↔code relation
  is **not a function in either direction** — `FEES_RECEIVABLE` is 25 under cash but 8 under accrual — so
  keying on the code cross-maps *and* keying on the name cross-maps. The brief now requires two entirely
  separate Go types. The fourth trap was deliberately **not** checked and is marked as A2-1's, not confirmed.
- **T120 + T132 + T143 consolidated into T154** (+ reviewer T155): one defect surface, colliding
  `files_hint`; three concurrent workers would have produced contradictory guards.
- **`git diff main..branch` (two dots) is the wrong scope check during a fire** — `main` moves, and its own
  advances render as branch deletions. A2-6 looked like it had deleted 71 lines of `gates.md`. **Use three
  dots.** The skill's STEP 5 text says two; it is wrong.

## STANDING INSTRUCTIONS

- **Invoke the harness with `bash`, never `sh`.** Exit 3 is the interpreter guard's **refusal** — *not* an
  oracle outage. Only exit **2** *with a probe line that was actually PRINTED and reads `down`* is the
  oracle-down condition; **test for the line's presence first**, since a failed HARD guard exits 2 in silence.
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **Ship no guard you have not driven RED** (P-22). A2-5 modelled this correctly: its provers read the real
  pre-fix bytes from **immutable git blobs** and refuse on sha mismatch, so they cannot drift into testing
  the fixed code. Copy that shape.
- **Verify post-merge assertions on a scratch merge** (P-24), against the **real pre-fix bytes**.
- **An obligation is not a proof.** Where `obligations.md` says *Ungraded*, nothing runs that would catch it.

## Open gates — none blocks work today

- **G-4**, **G-5** (OPEN, ENGINEERING) — wording-only amendments to a **ratified** DEC-1. Not crossed: the
  skill's never-cross list names *any change to a ratified DEC-n*. Both corrected readings are already
  operationally in force. **Buyan decides.**
- **G-8** (OPEN) — options (b) and (c) amend the graded domain and are hard `user` gates.
- **N9 / N10** (OPEN) — only FU-1 (obligation T139) closes them.
- **G-9** — **CLOSED this fire** (agent-decided, reversible).
- **CUTOVER** — untouched, every context. Needs vectors passing **and** a clean shadow-parity window **and**
  regulatory/parallel-run sign-off. The latter two do not exist.
