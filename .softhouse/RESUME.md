# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

> **INTERIM — fire `20260819-080001` is IN FLIGHT.** Three workers are running in isolated worktrees and
> the orchestrator is awaiting all three. If you are reading this, that fire was killed mid-flight; see
> **"If this fire died"** at the bottom.

## Current state (local fire `20260819-080001`, oracle **REACHABLE**)

- **Program**: `fineract-to-go-full-codebase` — **active**
- **Active run**: `2026-08-17-run1-harness-schedule-poc` — Tier 0, not terminal
- **Contexts**: 0 done / 17. Tier 0 open; the other 16 are READY-FOR-ANALYSIS behind it.
- **Reference oracle**: **UP** — `https://localhost:8443/fineract-provider/actuator/health` → `{"status":"UP"}`;
  `fineract-fineract-1` (fineract:latest) and `fineract-db-1` (postgres:18.3) both healthy. PostgreSQL only;
  no prohibited-engine port open.
- **Background-task wait ceiling is DISABLED** (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, set by
  `fire-program.sh:167`). This was the real cause of four fires losing their workers — **not** a
  dispatch-and-exit bug in `fire-program.sh`, as two earlier manifests wrongly claimed.

## G-1 is not a user gate — corrected this fire

The gate record listed six items as *"decisions only Buyan can make"*. **All six are answered** — five inside
DEC-1 revisions 3–6, and the sixth (the tenant rounding mode) by Buyan's ratified parameters of 18 Aug 2026:
`HALF_UP` (ordinal 4), precision 19, production `MathContext` **(19, HALF_UP)**. Full triage table in
`.softhouse/gates.md` under *"G-1 · UPDATE from local fire 20260819-080001"*.

**G-1's `decisions_reserved_for_user` is now empty.** What actually gates it: **one clean independent
re-review of DEC-1**. Ratification is agent-decidable under policy P-2; Buyan retains veto.

## Why the gate is still open: six rounds, six new P0s

T23, T26, T29, T32, T34 each found a **new** P0 on a surface no prior round had examined, and T37 then
*observed* a sixth defect. In every case **the committed corpus reproduced both the right reading and the
wrong one.** Six corpus-invisible wrong readings are now known: ratio-is-always-1; textbook
`balance × rateFactor`; wrong-`n`; `RepaymentEvery`-instead-of-`periodRatio`; the whole-principal
pre-disbursement balance; and the third date-membership rule. **Plan for the next review to find something —
a clean verdict is the surprise, not the default.**

## Tasks in flight this fire (all opus, all worktree-isolated)

| Task | Branch | Needs oracle | What it is |
|---|---|---|---|
| **T38** | `softhouse/T38-dec1-v7` | no | DEC-1 v6 → **v7**: T34's P0 (`periodRatio`, not `RepaymentEvery`) + P1-T34-1/2 + P2; T37's **observed** P0 (pre-disbursement balance and the third date-membership rule `[from, due)`); fold in the five captured binding shapes. |
| **T39** | `softhouse/T39-periodratio-observation` | **yes** (Path A, throwaway containers) | Turn P0-T34-1 from a re-derivation into an **observation**: capture the `periodRatio` drift region and measure on the disagreeing cells only. |
| **T40** | `softhouse/T40-charges-capture` | **yes** (Path B, sole owner of the running server) | Close the corpus's **zero** discriminating power over charges — every fee and penalty in the whole corpus is `0.00`. |

Write surfaces are partitioned by directory, one owner each, as in fire `20260818-230002`; T40 alone may
touch the running containers, and additively only.

## Task state (terminal ones)

| Task | State |
|---|---|
| T1, T3, T3b, T4, T5, T16, T16b, T17–T19, T21–T24, T26–T37 | done |
| T25 | done_partial (oracle-free slice) |
| T2 | **parked** — unpark = gate **G-2** (Buyan: *yes, once, reshaped*) |
| T6 | blocked — **G-1**, now ENGINEERING_ONLY |
| T7, T9–T15, T20 | pending (T7 harness gates most of them) |
| T8 | in_progress — captures taken, **no vector promoted** |
| T38, T39, T40 | **in_flight this fire** |

## Next action, in order

1. **Await and merge T38/T39/T40**, then raise the **independent re-review of DEC-1 revision 7**. If it comes
   back clean, **the driver ratifies under P-2 and G-1 closes without reaching Buyan.**
2. Reconcile revision 7 against **T39's observations** — an observation outranks a re-derivation of the same
   defect, so if T39 refutes T34, revision 7 is wrong and must move before any review.
3. **T7** (build the conformance harness) is the real bottleneck behind T9–T15 and it depends on **T6/G-1**.
   Nothing is promotable to the parity vector store while G-1 is open.
4. **G-2** — Buyan approved one reshaped T2 attempt.

## Open decisions for Buyan

- **None blocking Run 1.** G-1 carries no RESERVED item.
- **RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation, licence
  facts. None is in Run 1's path.

## If this fire died

Check each branch for commits — every worker was told to commit early and often:
`git log --oneline main..softhouse/T38-dec1-v7` (and `T39-*`, `T40-*`). A branch with commits holds rescuable
WIP; mark that task `needs_retry` with `note: worker killed mid-flight; rescued WIP on <branch>, completeness
unverified` — **never leave it `in_flight`**, which tells the next fire that work is happening when nothing is.
