# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260819-080001`, oracle REACHABLE, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17
- **Oracle**: UP all fire. `fineract:latest` + `postgres:18.3`, both healthy, **never restarted**. Pinned
  checkout `426a23544` clean throughout. PostgreSQL only; no prohibited engine anywhere.
- **Eight workers dispatched, EIGHT completed, merged and verified.** No worker lost, no isolation
  violation, no scope breach. Every merge was **selective or scope-checked**, and `contract.go`'s
  comment-only claim was re-verified by the orchestrator at each merge (0 non-comment lines, every time).

## THE ONE THING THE NEXT FIRE SHOULD DO FIRST

**One independent re-review of DEC-1 revision 10.** It needs **no oracle**. If it returns **CLEAN**, the
driver ratifies under policy P-2, **G-1 closes without reaching Buyan**, and **T7** (the conformance
harness) unblocks — and T7 is the bottleneck behind T9–T15.

Brief it with: seven rounds found a new P0 each; **round eight (T43) found none**; revisions 9 and 10 were
errata, not rewrites. Least-examined surfaces now are §4.5.1's charge material and decisions C-1/C-2, the
**M1–M5** reconciliation (five conventions now, not four), and §4.1.2, **whose form has changed three times
in three revisions** and should be checked on its own terms.

## G-1 is NOT a user gate — corrected this fire

All six items the gate recorded as *"decisions only Buyan can make"* are **answered** — five inside DEC-1
revisions 3–6, and the tenant rounding mode by Buyan's ratified parameters of 18 Aug (`HALF_UP`, precision
19, threaded `MathContext(19, HALF_UP)`). **`decisions_reserved_for_user` is empty.** Triage table in
`.softhouse/gates.md`.

### The driver DECLINED to ratify, against the reviewer's recommendation

T43 returned **ACCEPTED WITH REQUIRED CHANGES, no P0** — the first round in eight without one — and said it
*"found no reason not to ratify"*. **The driver declined.** Reasons, in `gates.md` and reversible by Buyan:
the written bar is *clean*; **ratification freezes** (a ratified DEC-n needs a gate to amend); and
**P1-T43-3 was a known-wrong sentence about money** — §4.3.2's M4 was stated as deciding which row a charge
lands on, but an `INSTALMENT_FEE` consults **no membership test** and lands on every row (MNT 27,500 on
FC-02's shape). Revisions 9 and 10 fixed it, and the corpus then **refuted** the old reading: revision 8's
M4 reproduces the charge rows on **13 of 21** captures, revision 9's M4+M5 on **21 of 21**.

Ratifying revision 8 that day would also have been defensible and would have unblocked T7 about two rounds
earlier. **If Buyan prefers that trade, say so and it can be ratified now.**

## What this fire established (all raw observed; NOTHING promoted — G-1 is open)

| result | evidence |
|---|---|
| **P0-T34-1 CONFIRMED BY OBSERVATION** — the rate factor's interest call site takes `periodRatio`, not `RepaymentEvery` | 415/415 disagreeing cells to `periodRatio`, **0/415** to `RepaymentEvery`; T34's re-derived worst gap **MNT 398,967.73** observed digit for digit |
| **The charges blind spot opened** — every fee and penalty in the whole corpus had been `0.00` | `totalRepaymentExpected` **omits** every main-loop charge (fails 15/21; **the two generators disagree**); **two ways to lose a charge silently at HTTP 200**; charges sit **alongside** the EMI, never inside it |
| **Which `MathContext` governs — settled** | Path A: threaded is the arithmetic, ambient **provably never read** on 11/13 shapes (an **absence** probe, stronger than a difference probe). Path B: the two are the **same object**, read off deployed bytecode. **Two** ambient leaks now known; **N46-1 is reachable at MNT's 2 dp** |
| **Precision 19 is OBSERVABLE, not just transcribed** | MNT 50,000,000 / 360 / 21.6 % separates 19 from 12 by MNT 2.05 across 861 cells. **Not monotone in principal** — no safe threshold |
| **The month-end special case is NOT SEPARABLE — proved** | closed form (the special case **is** the compensation for packed whole-months) + **all 112,147,776** ordered date pairs 2000–2040 + the `YEARS` escape route observed to throw. Revision 10 **withdrew** the `TO_BE_CAPTURED` |
| **`DayCountActualActual` CAPTURED** — §8 item open since revision 5 | three seams, 18 + 27 + 13 captures + a 28-block exactness probe. `FEB_29_PERIOD_ONLY`'s **second** effect isolated purely; `FULL_LEAP_YEAR` ≡ unset confirmed |
| **All seven §8 binding vectors captured and separating** | verified item by item by T43 |

## Open findings the next reader must not lose

- **T48-N1 (P1)** — `toLoanConfigurationDetails()` passes `isInterestChargedFromDateSameAsDisbursalDateEnabled`
  into the `interestRecognitionOnDisbursementDate` slot [`LoanApplicationTerms.java:1753`,
  `LoanConfigurationDetails.java:66-77`]. **A Go port wiring that getter will diverge.**
- **N46-1 (P1)** — the **charge** rounding mode is **ambient**, reachable at MNT's 2 dp, and **no capture the
  program holds can detect it**. Separating it needs a **tenant write**. `TO_BE_CAPTURED`.
- **Tier B trap** — `(19, tenant mode)` is a **loan-path** rule. Savings/deposits use `DECIMAL64` and
  `MathContext(15|10, …)`, and one precision-8 site is in **share accounts**. A porter assuming
  `(19, HALF_UP)` there is wrong on every compounding calculation.
- **T44-X1** — Path B responses are float-shaped on the wire; T46 added exact-text sidecars. Use them.
- **Two sweep traps** — a month-end sweep must take boundaries from §4.2's re-anchor (plain `plusMonths`
  fires **zero** times and silently proves nothing, T45), and re-transcribing that re-anchor inside the probe
  yields 645 instead of 701 (T47).

## Task state

| Task | State |
|---|---|
| T1, T3, T3b, T4, T5, T16–T19, T21–T24, T26–T48 | **done** (37 of 50) |
| T25 | done_partial (oracle-free slice) |
| T2 | **parked** — unpark = gate **G-2** (Buyan: *yes, once, reshaped*) |
| T6 | blocked — **G-1**, ENGINEERING_ONLY, no reserved item |
| T7, T9–T15, T20 | pending — **T7 is the bottleneck**, and it depends on T6/G-1 |
| T8 | in_progress — captures taken, **no vector promoted** |

## Open decisions for Buyan

- **None blocking.** G-1 carries no RESERVED item.
- **One reversible judgement:** the driver declined to ratify revision 8 on a no-P0 review. Overturn it and
  T7 unblocks sooner.
- **RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
  facts. None is in Run 1's path.

## Stranded work found during this fire's exit sweep — NOT merged, now durable

Two branches from fire `20260818-200001` hold **23 files that are absent from `main`**, and they were
**local to this Mac only** until this fire pushed them. They are now on `origin`:

- `softhouse/rescued-agent-a2027f85cea4effc9-20260818-200001` — 8 files, the **T24 probe** harness and its
  outputs (`t24-probe/T24Probe.java`, `t24_rederive_with_loop.py`, `t24_count_p12_p19_divergences.py`, …).
  **Probably superseded**: T24 was re-done from scratch by the cloud fire.
- `softhouse/rescued-agent-a353b03c0dea4dd41-20260818-200001` — 15 files: Path B **attestation** sidecars
  (`B-01`…`B-04-attestation.json`), `pathb/capture.sh`, `run-pass3.sh`, `tools/compare-pass3-v1-v2.py`,
  `tools/invariants-patha.py`, and two precondition self-tests. **The raw observations themselves are on
  `main`** (`pathb/out/B-0*-raw.json`); what is stranded is attestation and tooling, and T35/T36 later
  produced their own (`capture/src/run-pass3b.sh`, `capture/pathb/t36/`).

**Not merged deliberately** — merging a stale attestation over T36's would be a regression, and T42's
eight-point rule has since changed what an attestation must say. **Triage task for a future fire:** diff
these against T35/T36's equivalents and either delete the branches or salvage the genuinely-unique tooling.

## If a fire dies mid-flight

Check each `softhouse/T*` branch for commits — every worker is told to commit early and often. A branch with
commits holds rescuable WIP: mark that task `needs_retry` with `note: worker killed mid-flight; rescued WIP
on <branch>, completeness unverified`. **Never leave it `in_flight`**, which tells the next fire work is
happening when nothing is. And **always check for an existing `softhouse/<taskid>-*` branch before
dispatching** — a previous fire left a *complete* T38 unmerged with `tasks.json` still saying `pending`, and
this fire nearly redid fifteen commits of it.
