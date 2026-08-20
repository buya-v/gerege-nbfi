# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260820-170001`, oracle REACHABLE)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0
- **Contexts**: 0 done / 17 · `tier0-harness-schedule-poc` **active**
- **Oracle**: UP all fire, never restarted (~47 h). `fineract:latest` + `postgres:18.3`, both healthy.
  Pinned checkout `426a23544` clean at entry and at exit. PostgreSQL only.
- **Seven workers dispatched, seven completed, ZERO live at exit.** No isolation violation, no scope breach.

```
VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle, 5576 cells compared.
         4 contract-refusal · 1 self-test · 0 refused · 0 inadmissible · 0 harness errors
         0 invariant violations · 0 invariant assertions NOT RUN
         build / vet / test (-count=1) 0 / 0 / 0 · gofmt -l names exactly contract.go (G-3 expected)
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**Re-run by the driver on merged main, not inherited from a worker.** The corpus grew **36 → 42 parity
vectors** and 4034 → 5576 graded cells — the first corpus growth in three fires.

---

# THE HEADLINE: the fire's most important finding is UNVECTORED, and a REVIEWER found it

**`MNT 0.01 / 6 × 21.6%` at `MinorUnitDigits = 2` — entirely inside the graded domain, no multiples-of input
— makes the reference oracle emit a schedule whose balance column NEVER REACHES ZERO: `0.01` on every row,
including the last. The Go port returns `0`.** Same at 0.02/6, 0.01/12, 0.01/56; clean at 0.03 and above.

T75 found it while *approving* T74. It registered a prediction, committed it, and only then probed the
pinned image — its calibrations reproduced `T64-ZP-A`/`ZP-B` cell-for-cell with zero input diffs.

This sets two project rules against each other: *Fineract is the oracle* versus *principal amortizes to
zero*. **Conformance is green only because no vector covers the region** — which is exactly the blind spot
the gate exists to eliminate, so the green bar is not evidence against the finding. Raised as **G-8**;
**T83** must re-capture independently and measure the boundary before anyone proposes a remedy.

---

## THE DRIVER WAS WRONG, IT COST A WHOLE WORKER, AND THE WORKER CAUGHT IT FIRST

The driver dispatched **T76** to close T22's `P0-3/4/5/6` "still open, still blocking vector promotion."
**They had been closed on 18 August** — P0-5 by T30 `1b65b1c`, P0-3/P0-4/P0-6 by T36
`78c5bda`/`c3bbf26`/`fab040a`+`60c08ad`, and P1-14 (B-03/B-04 never re-derived) by T30 as well.

**The false sentence was in this very file**, in the paragraph the last fire wrote, and in `T25`'s own park
list — neither updated when T30 and T36 ran. The driver copied it into a dispatch prompt without opening it.
Same failure mode as last fire's F-1, one level up: last time a line number, this time an entire task premise.

T76 checked before touching the oracle and registered the refutation in `t76/PREDICTION.md` — a commit that
is a **parent** of its evidence commit, so it cannot be back-fitted. T77 confirmed it in every particular.
The driver re-verified it from the commits itself (`.softhouse/reviews/driver-rederivation-20260820-170001.md`).

**Standing correction, now in force:** a `parked` list inside a task note is *evidence of what was true when
it was written, not a work queue.* Check whether a later commit already closed the items before dispatching.

---

## What each worker did

| task | verdict | outcome |
|---|---|---|
| **T74** Path A pass-3i | **APPROVED** by T75 | **MERGED. Six vectors promoted, 36 → 42.** |
| **T75** review of T74 | done | The only approval this fire — and it found G-8 |
| **T72** 4th draft of the fui rule | **REJECTED** by T73 | not merged; T78 branches off it |
| **T73** review of T72 | done | Constructed the counterexample rather than just naming a false clause |
| **T76** Path B re-capture | **REJECTED** by T77 | not merged; T80 branches off it |
| **T77** review of T76 | done | Found a worse defect than the one it rejected |
| **T78** 5th draft, closed form | done | **NOT MERGED — awaiting T79, the first task of the next fire** |

**T73's rejection of T72, driver-verified from source before ruling.** A **mid-term interest rate variation**
satisfies every one of T72's eight conditions and still routes the decision outside steps (a)-(g):
`:120 → :273 → :350 → :356 → :718 → :747 → :1160`. `changeInterestRate` anchors on
`submittedOnDate.minusDays(1)`, not the disbursement, voiding step (b); and `:733-735` is a **four-term**
disjunction whose second term is `INTEREST_RATE_CHANGE`, so `:741` is taken on a model that already carries
EMI on every period — the exact mechanism step (e) cited as protection. T72 fenced the callers of `:1160`;
it needed to fence the callers of **`:718`**. **The frozen contract already named the gap twice**
(`contract.go:563-564`, `:2117-2118` — interest pause, mid-term rate change, multi-tranche). T72 fenced two
of the three.

**T77's rejection of T76 found something worse than the item it rejected.** T22 P0-4's fail-the-run property
lives in the *caller*, and its ABORT is **unreachable** — `bad()` writes FAIL to stderr while the gate greps
a stdout-only `tee`. `TENANT=default sh t36/recapture.sh` ran with **five breached preconditions including a
404'd canary, no abort, all four captures taken, exit 0** — written into a hard-coded `recapture-gerege`
directory. **A capture taken on the wrong tenant is filed under the right tenant's name.** T80 fixes it.

**T78 changed strategy on the driver's instruction.** Four rounds of "enumerate the safe conditions" produced
four true-but-insufficient rules. T78 wrote a **closed form**: three censuses each exhaustive by grep, and
the load-bearing one is that the four entries to `:718` are **in bijection with a 4-constant enum fixed by
the compiler** — so a fifth route cannot appear without a compile-visible edit to the pinned oracle. That is
what lets the rule stop enumerating. It also named a **third writer of the field no previous draft found**
(`AdvancedPaymentScheduleTransactionProcessor.java:1995`).

---

## THE NEXT FIRE STARTS HERE

1. **T79** — independent review of T78. **First task, no oracle needed.** Attack whether the closed form
   *closes*, not whether a fifth caller exists.
2. **T83** — **ORACLE ONLY.** Re-capture and measure the G-8 non-amortizing boundary. Highest-value oracle
   work outstanding; the divergence is live and unvectored.
3. **T80** — **ORACLE ONLY.** Retry of T76: make the Path B abort reachable and the canary non-tautological.
4. **T81** — the `sh` vs `bash` trap in `conformance.sh`. Both T76 and T77 hit it independently: under `sh`
   it dies at line 104 and **exits 2**, the harness's real "oracle unusable" code and this driver's third
   stop condition. **A shell-selection typo currently masquerades as a legitimate oracle-down park.**
   **STANDING INSTRUCTION until it lands: invoke as `bash .softhouse/conformance.sh`, NEVER `sh`.**
5. **T82** — T75's seven defects on the pass-3i artefacts. Two are guards that cannot go red (a P-15
   violation inside the check advertised as fixing P-15; a Python chained comparison that passes when both
   arms ran at a non-ratified mode). No oracle needed — good cloud-fire work.
6. **T15** — archive. Now depends on T14, T71, **T73, T75, T77, T79**.
7. **Then Tier A.** `tierA-gl-accounting` is already decomposed in `program.json` into three **measured**
   slices, with the rationale and the rejected alternative recorded: **A2** chart of accounts + product
   mapping (6,636 LOC) → **A1** journal posting, the double-entry engine (11,535) → **A3** period-end
   (4,953). Total re-measured at pinned `426a23544`: **23,161 LOC**. Plan gate rule 5 forces the split
   independently of the 25,000 threshold, because `fineract-accounting` is a whole 12,752-LOC module.

**T12 remains `done_partial`** — the mid-flight checkpoint drill is **still unexercised for a FIFTH fire**.
All seven workers this fire ran to completion again. It needs a fire that genuinely hits the soft limit
with a worker in flight.

**Worktree debt:** ~60 stale `softhouse/*` worktrees are still registered. STEP 9 hygiene has never run.
Harmless today, but it is unbounded growth on a real disk.

---

## Open decisions for Buyan — **none blocking, three open, none RESERVED**

- **G-4** — DEC-1's ACT/ACT promotion condition is provably too strong (wording only).
- **G-5** — DEC-1 contradicts itself on a zero interest rate (wording only).
- **G-8** — **new this fire.** The non-amortizing MNT 0.01 shape. Blocks nothing; **T83 measures it before
  anyone proposes a remedy.** Driver's recommendation, recorded but not acted on: prefer promoting a parity
  vector with an explicit invariant exemption, because it keeps the oracle authoritative and makes the
  divergence measured rather than defined away — and it may need no DEC-n amendment at all. Refusing the
  region or diverging deliberately both amend the graded domain and are hard `user` gates.

**G-2, G-3, G-6** — closed in earlier fires. **G-7** was proposed inside T76's handoff and is *not* yet
promoted to a gate, because T76 was rejected; T80 should re-raise it if it survives.

**RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
facts. None is in Run 1's path.
