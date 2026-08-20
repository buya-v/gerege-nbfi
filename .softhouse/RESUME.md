# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260820-110001`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP all fire, **never restarted** (~43 h). `fineract:latest` + `postgres:18.3`, both healthy.
  Pinned checkout `426a23544` clean. PostgreSQL only.
- **Six workers dispatched, six completed, all merged. Nothing lost, no isolation violation, no scope breach.**

```
VERDICT: PASS (exit 0) — 36 parity vectors match the pinned reference oracle, 4034 cells compared.
         --prove 21/21 · 6/6 invariants hold 37 · 0 inadmissible · 0 harness errors
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Every number above was re-run by the driver, not accepted from a worker's report.**

---

# THE HEADLINE: **a diff whose code was correct was rejected, because its written rule was false**

T63 (last fire) found T59's memo **sound** but its stated justification **false**. T65 rewrote the rule.
The independent reviewer **T67 REJECTED T65** — and was right. The driver confirmed two of T67's three
findings from the committed source *before* ruling, rather than settling it on whose report read better:

| the comment said | the source says |
|---|---|
| the fold reads **ONLY** the eight listed stored fields | it also reads `m.minorDigits`, via `minorFromMajor(sum, m.minorDigits)` |
| `period idx` is **NOT read** | `calculatedDueInterestMinor` calls `interestChainUpTo(p.idx)`, and the chain is filled at `m.chain[i]` over `m.periods[i]` — **`p.idx` is the memo's lookup key** |

So the rewritten rule was not merely incomplete, it was **not sufficient**: writing `p.idx`, or reordering
`m.periods`, returns another period's money while satisfying the stated rule at every step.

**T65's executable change was never in doubt** — T67 verified the carried counter by induction *and* its own
3,840-shape / 70,080-row probe, reproduced all four mutations, and confirmed the `applyFinalPeriodResidual`
recursion is faithful to `ProgressiveEMICalculator.java:1211-1214`, vindicating T59's refusal to "optimise"
it. The rejection was on the deliverable that *is* a rule. Recorded as pattern **P-13**.

**T69 fixed it in three clauses — and found a defect in T67's own replacement text**
(`ProgressiveEMICalculator.java:247` sits on the `allowFullTermForTranche` branch; the ordinary path is
`:747`). It also **refused to assert a third reason** for `futureUnrecognizedInterest`, marking it
`[UNVERIFIED]` and naming **T66** as the task that settles it. Three wrong reasons for one bullet is exactly
the failure this pipeline exists to stop, and it stopped at two.

---

## What else this fire established

**T64 — the ungraded path is graded now.** T59 profiled `applyFinalPeriodResidual` as O(n²) on
near-interest-only shapes and correctly did not fix it, because **no vector graded that shape**. T64 derived
from source that a repayment row with zero principal and non-zero interest exists **only at the rounding
floor** (`B ≥ ceil(0.5/r)`, `n ≳ 2·B`, `B` in *minor* units), registered a falsifiable prediction naming all
**221 rows one commit before the capture** (P-9), and the oracle returned
`compared 1539 predicted cells / PREDICTION CONFIRMED — zero mismatches`.

- `ZP-RESIDUAL-NO-RECURSION` — drop the self-re-entry — was **green on all 32** vectors and is **red at 36**,
  killed solely by `T64-ZP-B`. Pattern **P-14**: a mutation no vector can distinguish is a blind spot, not an
  absence.
- **Honest negative kept:** `ZP-PRINCIPAL-NOT-CLAMPED` **survives all 36**. The negative clamp is still
  ungraded and is in the backlog, not glossed.

**T62 — `--prove` now covers the unrecorded-cell path, and the driver reproduced why it had to.** In a
scratch worktree at the pre-fix behaviour, plain conformance returns **exit 0, 32 parity vectors,
`principal_amortizes_to_zero hold 33 not-asserted 0`** — a **silent false green** — while the new proof fails
**0/0** naming `FALSE HOLD`. *The exit code cannot see that defect; the proof can.* That defect class had
already escaped twice.

**T68 — the audit found the correction document was wrong about its own reason, twice.** T64 corrected its
vector text when the harness refuted its first draft, and did not carry the correction into
`MECHANISM-CORRECTION.md`. **P-11 recursing one level up**, now recorded as **P-12**. Verdicts: T62
**APPROVED**, T64 **APPROVED WITH REQUIRED CORRECTIONS**, **P0: 0, no vector withdrawn**. T68 also pinned the
provenance *tighter than T64 claimed* — `capturedAtUtc` falls between the prediction commit and the capture
commit — and re-transcribed all four vectors with its own exact-integer comparator: zero discrepancies.
The driver applied T68's corrections to that document this fire.

---

## THE NEXT FIRE STARTS HERE

**ORACLE-ONLY — only a local fire can do this:**
1. **T66** — settle T63's two unproven items, chiefly that `futureUnrecognizedInterest` is **not ported**
   (101 admitted shapes carry half its precondition). T69 has now marked the comment `[UNVERIFIED]` and
   named T66 explicitly, so this is the task that closes a claim three tasks have declined to assert.
   Item 2 (the per-iteration trial copy under multi-tranche) needs no oracle.
   *Not run this fire: T64 held the capture rig, and two capture workers collide in `.softhouse/capture/`.*

**Then:** T12's remaining half → T13 `/softhouse-uat` → T14 (`user` gate: accept the PoC slice, **no
cutover**) → T15.

**T12 is `done_partial`, deliberately not `done`.** The rehydration half is committed as a re-runnable
assertion (`.softhouse/bin/rehydrate-check.sh`; this fire: 61 terminal tasks, none re-selected). **The
mid-flight checkpoint half is still untested** — all six workers this fire ran to completion, which is the
better outcome but leaves the drill unexercised for a third fire running. The next fire that approaches the
soft limit with a worker in flight should treat that as the drill.

---

## Open decisions for Buyan — **none blocking, two open, none RESERVED**

- **G-4** (DEC-1's ACT/ACT promotion condition is provably too strong — wording only).
- **G-5** (DEC-1 contradicts itself on a zero interest rate — wording only).

Both are wording amendments to a **ratified DEC-n**, which no automation may cross. Both block nothing; the
corrected readings are already in force.

- **G-3 (`gofmt` vs the frozen `contract.go`) — CLOSED this fire by the driver, Option A.** ENGINEERING, no
  RESERVED content. The feared *silent* mutation is impossible: a byte change makes the harness exit 2 naming
  both digests, and T68 independently demonstrated the digest guard fires at `grade.go:237` **before**
  `LoadStore`, on both a `_selftest`-scoped run and an empty store. Standing instruction, already in force:
  no task may `gofmt -w` that path, and `gofmt -l` reporting exactly that one file is the EXPECTED state.
  Buyan may reverse.

**RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
facts. **None is in Run 1's path.**

## Backlog carried
- **B-1** — ACT/ACT arm must be ported before the fold-vs-closed-form question is decidable (91 ACT/ACT
  captures sit unpromoted; the bottleneck is the port, not the oracle).
- `ZP-PRINCIPAL-NOT-CLAMPED` survives all 36 — the negative clamp is still ungraded.
- **`report.go:113` still prints that no vector separates HALF_UP from HALF_EVEN — `T61` falsified that three
  commits before this fire.** A stale fact inside the reporter itself.
- Proof 8b carries a literal `self-test fixtures PASS 1`; single-vector-kill fragility for
  `ZP-RESIDUAL-NO-RECURSION`.
- Nothing enforces that the vector-store README's counts track the corpus (they were stale 29-vs-36 until
  T64 fixed them in the promotion commit — third recurrence).
- `conformance.sh` grades **no liveness property at all**; the cost/cancellation tests are package tests.
- **CLOSED as already-satisfied:** T62's follow-up F-1 — `VerifyContractDigest` already fires at
  `grade.go:237` before `LoadStore` (driver-confirmed by grep, T68-confirmed by demonstration).
