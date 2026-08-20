# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260820-080002`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP all fire, **never restarted** (~39 h; several captures' comparability rests on that).
  `fineract:latest` + `postgres:18.3`, both healthy. Pinned checkout `426a23544` clean. PostgreSQL only.
- **Four workers dispatched, four completed, all merged. Nothing lost, no isolation violation, no scope breach.**

```
VERDICT: PASS (exit 0) — 32 parity vectors match the pinned reference oracle, 2495 cells compared.
         --prove 20/20 · 6/6 invariants hold · 0 inadmissible · 0 harness errors
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Every number above was re-run by the driver, not accepted from a worker's report.**

---

# THE HEADLINE: **a port using Fineract's stock rounding default passed all 29 vectors**

The corpus began this fire green at 29 vectors / 2,354 cells. The driver applied **one** mutation to
`roundHalfUpToInt` — the `HALF_EVEN` tie rule, which is **Fineract's own stock default** — and re-ran the real
harness in a scratch worktree:

| `MONEY-QUANTIZATION-HALF-EVEN` | verdict |
|---|---|
| **at 29 vectors** | **PASS, exit 0**, 2,354 cells |
| **at 32 vectors** | **FAIL, exit 1** — `T61-HE-A/B/C`, on the predicted cells |

**So a Go port that inherited the upstream default instead of reading Buyan's ratified `HALF_UP` tenant pin
matched the reference oracle on every graded cell.** That is a money defect that would have shipped, and it is
the exact class `CLAUDE.md` ratifies as non-negotiable ("Rounding mode: `HALF_UP` for MNT… never inherit a
default").

**Why the corpus could not see it:** a rounding tie is measure-zero on an arbitrary lattice. You do not reach
one by sampling ordinary loans — you *solve* for one. T61 did the algebra from source (at 21.6 % on this
lattice period-1 interest is `18·B/1000` minor units, an exact tie exactly when `B ≡ 250 (mod 500)`) and
**committed the prediction one commit before the capture ran** (`d543fd0` → `0e75bef`), in falsifiable terms:

> *"`T61-HE-B`, period 1, interest: the oracle will emit `18000.95`, not `18000.94`. If the oracle emits
> `18000.94`, the prediction is WRONG, and the ratified tenant rounding mode is not what we think."*

The oracle returned **`1800095`**. Recorded as pattern **P-9**.

---

## What else this fire established

**T60 — the reported defect was the lesser of three forms.** `unrecorded_fields` was honoured by
`diffSchedule` and **ignored by all six property invariants**, which read the same struct the replay had
filled with placeholders. The driver reproduced the worst form from scratch at the pre-fix commit: withdrawing
the **final** row's outstanding balance gave `exit 0` with `principal_amortizes_to_zero hold 30`, asserting
*"final outstanding == 0"* against a placeholder `0` nobody observed — **a silent false green**. Post-fix the
same perturbation reports `not-asserted 1` and names the vector under a new *INVARIANT ASSERTIONS THAT COULD
NOT RUN* section. **No passing check was traded away**: the real corpus still shows all six invariants
`hold 30+ / violated 0`.

**T59 — cancellation and cost.** The port checked `ctx.Err()` **once at entry and never again**, so a 50 ms
deadline returned at **10.82 s with `err=nil`**. Now checked inside the loops, sticky flag consulted *after*
the emitting loop so no partial schedule escapes. The oracle's memo was restored as a prefix cache:
**n=360 → 10.767 s → 39.3 ms (274×)**, allocations 92.7 M → 358 k. It **correctly refused** to bound
`NumberOfRepayments` — DEC-1 has no upper bound and revision 4 removed it from the graded-domain predicates,
so that is a `user` gate — and it **reported its own cost test as flaky** before replacing it.

**T63 — the reviewer the driver added.** T59 was a money-path change with **no paired reviewer**, which
plan-gate rule 1 requires; conformance cannot settle it, because every promoted vector runs **≤36 periods**
while the memo's speedup is at n=360. Verdict **ACCEPTED WITH REQUIRED CHANGES** (P0: 0, P1: 2). The memo is
**sound** — ~74,000 shapes, no divergence, no seventh unguarded write site, enumeration done from the *writes*
(18 assignments, 9 `invalidateFrom`) rather than from T59's stated count. Two P1s stand:

- **P1-2, the delay fuse.** The memo is right; **its stated reason is false of the oracle**, which writes
  later→earlier in four places. The true condition is *every write to a fold input on period j is preceded by
  `invalidateFrom(j)`*. The written-down rule is what the next contributor checks a new write site against.
  Pattern **P-11**.
- **P1-1.** `TestGenerationCostIsNotQuadraticInTheTerm` is **green on a port that is quadratic**, twice over:
  `installmentNumberOf` rescans every emitted row inside the emission loop (`generator.go:459`, `:478-486`) —
  Θ(n²) that **allocates nothing**, while the test grades allocation *counts* — and a timing cliff at n=2,000
  sits above both sample points. *(Driver re-read the source and confirmed the rescan; the cliff stands as
  T63 measured it.)* Pattern **P-10**.

T63 also **withdrew one of its own findings** after measuring 30 combinations to n=50,000 and finding T59's
claim survived.

---

## A hypothesis answered NO — with a measurement, not a null sweep

The driver sent T61 after the biggest documented blind spot: the oracle **folds** the rate factors rather than
using the closed-form EMI, and both agree on the corpus only *because every promoted vector has equal rᵢ*.

Step 1 **confirmed the caveat is not stale** — all 29 prior vectors are `FIXED_30_360`/`MONTHS`/`every=1`.
But `CLOSED-FORM-POW-EMI` **cannot be closed by any capture in the current graded domain**: the gap under
equal rᵢ is **~1e-11 minor units**, thirteen orders of magnitude below a cent. The only route to unequal rᵢ is
`ACTUAL_ACTUAL` across two calendar years of differing length, which **needs the ACT/ACT arm ported first**.
T61 declined to spend the oracle there and said why — **91 ACT/ACT captures already sit unpromoted; the
bottleneck is the port, not the oracle.** Backlog **B-1**, with a ready-to-run acceptance test.

Three further survivors were reclassified as **provably unreachable** rather than open gaps (M6, M8, M10).
**M11 remains genuinely open** (0 of 72,003; needs a targeted solve, not a sweep).

---

## Gate G-2 — CLOSED, DECLINED, and the real hazard was the document that EXISTS

Closed by the driver under `CLAUDE.md` § *Answering gates* (PRODUCT/process, no RESERVED content). **No third
attempt at T2.** Specification of record: **DEC-1 rev 12** (ratified, frozen), **the parity corpus**, **T3b's
re-review**.

The decisive find was not the missing document but the parked one still on disk. Its **§7.4 told a Go
implementer that clamp-and-continue month-end stepping (`2026-01-31 → 02-28 → 03-28`) is what a port "must
replicate bit-for-bit."** That is the **killed counterfactual** `MONTHEND-CONTINUE-FROM-CLAMPED-DAY`: parity
vector `P-02` has period 2 due **`2024-03-31`**, re-anchored on the disbursement seed. A port built from that
paragraph **fails conformance**, at a money margin of exactly zero. Neutralised at zero model cost with a
**⛔ SUPERSEDED** banner and inline corrections at the three sites T3b enumerated, plus the `ls-008` row that
restated it a fourth time.

---

## THE NEXT FIRE STARTS HERE

**Needs NO oracle — run these first:**
1. **T65** — T63's two P1s. Do **P1-2 first** (the false justification; it is the delay fuse), then P1-1.
   Touches money-path files, so it **needs a paired reviewer** per plan-gate rule 1.
2. **T62** — `--prove` has no proof covering the unrecorded-cell path. This defect class has now escaped
   **twice**, and `--prove` is what the driver re-runs independently. Follow **P-7**: assert the property,
   not today's counts.

**ORACLE-ONLY — only a local fire can do these. Do NOT run both alongside another capture task; two capture
workers collide in `.softhouse/capture/`:**
3. **T64** — capture a shape where a repayment row amortizes **zero principal**. The corpus has zero
   discriminating power there, which is why T59's O(n²) residual path is ungraded.
4. **T66** — settle T63's two unproven items, chiefly that `futureUnrecognizedInterest` is **not ported**
   (101 admitted shapes carry half its precondition). Both are pre-existing **T10** issues, not T59 regressions.

**Then:** T12's remaining half → T13 `/softhouse-uat` → T14 (`user` gate: accept the PoC slice, **no
cutover**) → T15.

**T12 is `done_partial`, deliberately not `done`.** The rehydration half is exercised and now committed as a
re-runnable assertion — `.softhouse/bin/rehydrate-check.sh`, which fails loudly if any terminal task would be
re-executed (this fire: 60 terminal, none re-selected). **The mid-flight checkpoint half is still untested**,
because all four workers ran to completion. The next fire that approaches the soft limit with a worker in
flight should treat that as the drill.

---

## Open decisions for Buyan — **none blocking, three open, none RESERVED**

- **G-3** (`gofmt` vs the frozen `contract.go`). **De-risked by demonstration this fire:** the driver appended
  one inert newline and the next run returned **exit 2 UNUSABLE**, naming both digests
  (`admit.go:87-93` enforces `PIN.json`'s `contract_sha256`). The feared *silent* mutation is impossible —
  it halts the harness loudly. Option A costs nothing; **safe to leave open indefinitely.**
- **G-4** (DEC-1's ACT/ACT promotion condition is provably too strong — wording only).
- **G-5** (DEC-1 contradicts itself on a zero interest rate; the harness's own self-test sits on the
  contradiction — wording only).

G-4 and G-5 are wording amendments to a **ratified DEC-n**, which no automation may cross. Both are recorded
as blocking nothing; the corrected readings are already in force.

**RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
facts. **None is in Run 1's path.**

## Backlog carried
- **B-1** — ACT/ACT arm must be ported before the fold-vs-closed-form question is decidable.
- `conformance.sh:31` defines `CONTRACT_REL` and never uses it — a vestigial shell variable that reads like a
  guard. Delete it or wire it up.
- Nothing enforces that the vector-store README's counts track the corpus; T60 corrected them and added an
  instruction, but an assertion would be a **new rule** needing its own review.
- `conformance.sh` grades **no liveness property at all**; T59's three tests are package tests, not vectors.
