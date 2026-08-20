# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260820-200002`, oracle REACHABLE, CLEAN EXIT)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP at entry and at exit. Containers **never restarted, rebuilt or re-seeded** all fire, with
  three workers sharing them. Pinned checkout `426a23544` clean at entry and exit. PostgreSQL only.
- **TEN workers dispatched, TEN completed, ZERO live at exit.** No isolation violation, no scope breach.

```
VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576 cells compared.
         0 invariant violations · 0 invariant assertions NOT RUN
         build / vet / test (-count=1) 0 / 0 / 0 · gofmt -l names exactly contract.go (G-3 expected)
         sh conformance.sh -> exit 3, ZERO verdict tokens (new this fire)
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Corpus unchanged at 42 vectors — and that is correct, not a shortfall.** No capture task promoted anything
this fire; both oracle tasks were *told* to promote nothing. What grew was the trustworthiness of the rigs.

---

# THE HEADLINE: five guards that could not fail, and a driver that was wrong three times

**The fire's dominant finding is a class, not an instance (P-22).** Five separate guards, canaries or controls
were found to be structurally incapable of failing — a canary that printed a sha256 without comparing it and
so certified `HALF_UP` **on a HALF_EVEN JVM**; an abort that wrote FAIL to stderr while the gate grepped a
stdout-only `tee`; a precondition whose table was built by looping over the ids it then checked; a green
control with zero discriminating power that **printed that it had some**; and an `attest.py` that stamped
provenance *before* testing its gate, mislabelling 11 captures while printing "no attestation written".

**Every one was found by ATTACKING the rig, never by reading it. Two were found inside the task sent to fix
the previous one.**

**The driver was wrong three times and workers caught all three (P-20).** T79 refused the bijection framing;
T81 refused the bash-via-`sh` constraint; **T84 refuted the driver's own G-8 reframing on the driver's own
stated discriminator.** A compliant worker would have shipped each error into a specification or a harness.

---

## Merged this fire (5 branches) — all verified by the driver on merged main

| branch | what landed |
|---|---|
| **T81 + T86** | `conformance.sh` interpreter guard, **exit 3**. A `sh` typo no longer masquerades as exit-2 "oracle unusable". |
| **T88 + T89** | The `futureUnrecognizedInterest` comment **CLOSED** after six workers and five rejections. |
| **T80 + T85** | Path B recipe hardened: canary pinned by digest comparison, abort reachable, output dir derived from tenant, `attest.py` gates before it stamps. |
| **T84** | Review evidence for G-8, incl. **342 new cells** it measured itself. |

## NOT merged, and why that is the right state

- **T83** (G-8 measurement) — REJECTED by T84 **for its write-up, not its numbers**. T84 reproduced the
  capture byte-identically (canonical sha256 `01b41d9c…`). **T100** reworks the write-up; **T101** reviews it.
- **T82 + T87** (pass-3i guards) — all findings applied and confirmed, then **the driver merged, ran T82's own
  proof harness, got 7/25 red, and backed the merge out.** See P-24 and **T102**. One literal-sha change away.

**`main` therefore carries nothing false**, which is why neither rejection is a loss.

---

## G-8 — measured, reproduced, REWRITTEN ON MAIN, still OPEN

`.softhouse/gates.md` now carries the true state (the old "T83 must first re-capture" wording is superseded).
**There are TWO phenomena under one gate id:**

- **Family A — a stale derived column.** Principal column sums to the disbursement, `totalOutstandingAmount`
  reads 0, forced memo recompute drives the balance to `0.00`. Mechanism verified from source three times:
  `ProgressiveEMICalculator.java:1180` reads the balance while `emi` is `0.00`, `:1210` raises the EMI in the
  same method, and `RepaymentPeriod.java:400`'s memo **omits `emi`** while the sibling at `:272-286` declares
  it. First stated by **T75**.
- **Family B — a genuine non-amortization.** 600 % p.a., MNT 0.01, n ≥ 104, **22 cells**: the principal column
  sums to **0.00** against a 0.01 disbursement and a forced recompute does **not** move the balance. **The Go
  port reproduces all 22 cell for cell — there is no divergence there at all.**

**Two corrections to what was previously believed:** option **(a) is reachable today for Family A with ZERO
port change** (761 cells, 0 cell diffs, FAIL without the exemption on two invariants, PASS with it); and the
region reaches **MNT 1.09 at 3.6 % over 360 periods — an ordinary 30-year term**, not sub-MNT-0.25 dust.

**(b) and (c) amend the graded domain — hard `user` gates. No agent has decided them and none may.**

---

## THE NEXT FIRE STARTS HERE

1. **T102** — pin T82's counterproof baseline to a **literal sha**, and **verify on a scratch merge into main,
   not on the branch**. Small, fully specified. Unblocks merging T82+T87.
2. **T100 / T101** — rework G-8's write-up as two families and review it. **No oracle needed.**
3. **T90** — harness report nondeterminism (`report.go:102` ranges an unsorted map; measured 27/3 over 30 runs
   of one binary). Byte-identity of harness output is used as *evidence* throughout this pipeline.
4. **T97** — the interpreter guard's probe is a **negative** test: `bash -r` is admitted, then dies with a
   fabricated "no Go toolchain" and **exit 2**, the defect class T81 closed, one layer in.
5. **T91, T92, T93, T94, T96, T99** — the rest of this fire's registered findings. Several need no oracle and
   are good cloud-fire work: **T93, T94, T96**.
6. **T15** — archive. Now depends on T79, T84–T89, T98, T100, T101.
7. **Then Tier A.** `tierA-gl-accounting` is decomposed into three measured slices: **A2** chart of accounts +
   product mapping (6,636 LOC) → **A1** journal posting (11,535) → **A3** period-end (4,953); 23,161 total.

## STANDING INSTRUCTIONS

- The **`bash`-not-`sh` instruction is RETIRED** — T81's guard enforces it structurally (`sh` → exit 3).
  **Exit 3 is NOT an oracle outage; never park anything on it.** Only exit **2** is the oracle-down condition.
- **Never `gofmt -w` `contract.go`** (G-3). `gofmt -l` naming exactly that file is EXPECTED.
- **A parked list inside a task note is evidence of what was true when written, not a work queue** (P-17).
- **Ship no guard you have not driven RED** (P-22), and run a fix's counterproof against the **real pre-fix
  bytes** — a proof that only shows the "after" cannot tell a fix from a no-op.
- **Verify post-merge assertions on a scratch merge** (P-24).

## Open gates — none blocks work today

- **G-4**, **G-5** (OPEN, ENGINEERING) — wording-only amendments to a **ratified** DEC-1. This driver does not
  cross them: the skill's never-cross list names *any change to a ratified DEC-n*, and that is the stricter of
  the two readings in play. Both corrected readings are already operationally in force. **Buyan decides.**
- **G-8** (OPEN) — above. Blocks nothing today.

## Exit report

**CLEAN EXIT.** Ten workers dispatched, ten completed, zero live at exit, nothing uncommitted, nothing
stranded. `git status --porcelain` empty; every branch listed above retains its work; main pushed.
