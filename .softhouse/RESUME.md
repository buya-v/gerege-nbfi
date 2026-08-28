# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, chain iteration 3 — **IN FLIGHT. ONE LIVE WORKER: `T384`.**

**If you are reading this and no driver session is running, `T384` was killed mid-flight.** Mark each
`needs_retry` with the WIP evidence from its branch. `in_progress` never means "work is happening"; it means
"a driver said so, once". Everything else below is either **merged** or **complete on a branch**.

### Why iteration 3 exists
Iteration 2 ended at ~10:35Z on a `five_hour` rate limit, not on a stop condition. The limit had reset by
11:15Z, the tree was clean, `origin/main` was 47 s old, and **zero workers were live**.

## BAR ON `main` RIGHT NOW — re-run after every merge, never inferred

```
bash .softhouse/conformance.sh   →  EXIT 0
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value, P-84
VERDICT: PASS — 46 parity vectors / 7884 cells
ledger parity 7/0 · oracle-refusal 6/0 · inadmissible 0 · 142 cells, 39 money
dead-path frontier GREEN, deadOccurrences 108, frontier 11 == pinned 11
13 ledger-wrong-* implementations all KILLED
```

Reference oracle REACHABLE throughout: `https://localhost:8443/fineract-provider/actuator/health`.
PostgreSQL up on `:5432`. No prohibited-engine port open.

## MERGED THIS ITERATION — four merges, each verified on the MERGE RESULT before touching `main`

| Merge | Commit | What it was |
|---|---|---|
| `T374` + `T382` | `01a7a05a` | A2-11 capture integrity; review APPROVED WITH CONDITIONS → `T393` |
| `T388` + `T389` | `a010f733` | **the first accrual observations in this program** → `T395`, `T396` |
| `T383` + `T385` | `e6cd307f` | fire-wrapper refuse-on-multiplicity → `T400`, `T401` |
| `T381` + `T386` | `5497a85d` | anti-calibration fail-opens → `T402` (**blocks `T399`**) |

Discipline used on all four, and it is not optional: merge into a **scratch worktree**, run the bar there,
only then merge into `main`, then run the bar on `main` again. `bar-on-merge-result.sh` carries a known prose
defect (C12) — `T385` measured it as LOW for correctness, MODERATE as documentation: the operative flag is
`--shared`, not hardlinks, and the residual risk is a concurrent source-side `gc --prune`, which would make
the bar **crash, not lie**. Safe to use; the fix belongs to `T353`'s grant.

## COMPLETE ON BRANCHES, NOT MERGED — and the ORDER is forced

| Task | Branch | Head | Blocked on |
|---|---|---|---|
| `T375` | `softhouse/T375-t364-conditions` | `2c1f5723` | `T384` (live) |
| `T360` | `softhouse/T360-divergence-class` | `d6979763` | **`T375` must land first** |
| `T387` | `softhouse/T387-review-t360` | `026954a4` | merges with `T360` |
| `T370` | `softhouse/T370-t351-retry` | `4925bbef` | **parked** — rejected by `T376`; substance verified good, lands via `T378` |
| `T376` | `softhouse/T376-review-t370` | `9255d1af` | a review; verdict REJECTED |
| `T369` | `softhouse/T369-review-t351` | `e10e3f07` | `T373` |
| `T351` | `softhouse/T351-progress-accounting` | `a0139c5d` | superseded by `T370`/`T378` |

### ⚠ THE MERGE HAZARD THAT WILL BITE THE NEXT DRIVER
**`T360` needs `EXEMPTION_PIN_LEDGER_WRONGIMPLS` bumped 13 → 14. MATCH IT BY NAME, NEVER BY LINE.**
It is `conformance.sh:3923` on `main` and `:4469` on `softhouse/T375-t364-conditions` — a **546-line** shift.
`T375` flagged the hazard from inside its own worktree (estimating ~90) and the driver measured it. Applying
the bump at `:3923` after `T375` merges would silently edit an unrelated line. `T375` has **not** touched the
pin; its diff is confined to `guard_guards_dir_registration` and its docs, so the two changes collide
positionally, never semantically.

**`T360`'s branch is `exit 2` and that is CORRECT.** Probe line **PRINTED**, reads `up`, sole refusal
`WRONG-IMPLEMENTATION POPULATION 14, PINNED 13`. Under **P-84** that is **the pin working** — not an oracle
outage, not a corpus defect. **Do not park vector work over it.** `T387` verified 14 by counting from the
binary's own `-list-implementations`, and confirmed the pin-patched merge result is exit 0.

## THE TWO RESULTS OF THIS FIRE

**1. The first accrual observations in this program (`T388`).** 9 journal entries through three RECEIVABLE
slots — `INTEREST` (gl 41), `FEES` (gl 42), `PENALTIES` (gl 43). The bar's every-run assertion *"NOT ONE
JOURNAL ENTRY IN THIS TENANT ARRIVED THROUGH A RECEIVABLE SLOT"* is now false. It took the **expensive
route** `T352` had costed and correctly declined — a NEW `ACCRUAL_PERIODIC` product on CLEAN GL accounts —
because the cheap route posts into gl 16, a promoted leg of three graded vectors. **No promoted account
moved**, and `T389` re-derived that on four independent axes against the live database.

**2. A MEASURED remedy would have made the bar grade BACKWARDS (`T387`).** `T359` measured a one-line fix and
recommended it; `T360` declined on reasoning; `T387` ran it against **both** a correct and a deliberately
wrong implementation:

| implementation | candidate vector | ledger parity | exit |
|---|---|---|---|
| `ledger-go` (CORRECT) | FAIL | PASS 7 **FAIL 1** | **1** |
| `ledger-wrong-residue-rounding` (WRONG) | **PASS** | PASS 8 FAIL 0 | **0** |

The wrong port passes and greens the bar. **`T359`'s measurement was correct and reproduces exactly** —
measuring that the stuck case FAILS is not measuring that the harness grades RIGHT, and from one
implementation the two are indistinguishable. Recorded **DO-NOT-APPLY**; `T398` gives it a P-number, because
a later reader finding `T359`'s review alone would find a measured, confident, wrong recommendation with
nothing marking it.

## THE P-45 CENSUS — SEVEN GUARDS BUILT AND WIRED TO NOTHING, ALL SURFACED IN THIS ONE FIRE
`oracle-state-baseline.sh` (would have been the net when `T388` moved the oracle) · `run-all.sh` (the rig
three tasks have been hardening) · `casualty-sweep.sh` (**`T381` filed this against itself**) · plus the
still-pending `T311`, `T303`, `T313`, `T333`. **`T333` guards a MONEY non-negotiable.** Filed as **`T399`**,
which **now depends on `T402`** — wiring `casualty-sweep.sh` before its scratch-file fail-open is closed
would let a filesystem hiccup produce **a green bar on a blind instrument**, strictly worse than unwired.
`T399` must gate on the **exit code**, not the `SWEEP-RESULT` cardinals: a refused selector is counted in
neither.

## OPEN GATES — none blocks anything
`G-19` · `G-20` (the effort ratio: 60% of the Go is the instrument, 39% the port it grades) · `G-21` (a
**ratified** DEC-2 carries a cardinal the oracle moved out from under; **nothing has ever swept `docs/`**).
The driver has **not** edited DEC-2 — `T395` makes that edit citing the gate.

## QUEUE FOR THE NEXT FIRE, IN ORDER
`T384` verdict → land `T375` → land `T360`+`T387` **with the pin bumped by name** → `T402` → `T399` →
`T393`/`T394` → `T390`, `T391`, `T395`, `T396`, `T397`, `T400`, `T401` → `T392`+`T398` (**these two must
agree their P-numbers or land in one commit** — this repo has already shipped one P-number collision).

## ⚠ DRIVER ERROR FOUND AND CORRECTED AT 14:40Z — `T393` WAS NEVER DISPATCHED

The driver wrote `T393`'s dispatch record — `status: in_progress`, `branch:
softhouse/T393-t382-conditions` — and **pushed it at `25e910b4`, in a commit whose own message says "pushed
before its worktree"** — then processed another worker's result and **never called the Agent tool.** For
**2 h 20 m** `tasks.json` told anyone reading it that a task was in flight while **nothing was running**.

Proven empty rather than assumed: `git rev-parse --verify softhouse/T393-t382-conditions` → fatal, the branch
never existed locally or on origin; zero worktrees match; the session's own agent list holds no such
subagent. **Nothing was lost, because nothing ever ran.** Reset to `pending`.

**THE SHAPE IS WORTH MORE THAN THE INCIDENT.** The push-before-spawn protocol exists so the record cannot
claim **less** than reality — the 2026-08-22 and 2026-08-28 incidents were both "workers running, record
silent". This is the same record claiming **more** than reality, and **no guard in this program looks for
it**. `ready-tasks.py` already flags an `in_progress` task with no `branch` as a suspected isolation
violation — **the driver simply never re-ran it after dispatching.** A cheap fix exists and should be a task:
re-run `ready-tasks.py` after every dispatch wave and treat a branchless `in_progress` as an alarm.

Not dispatched now, deliberately: the fire is 8.7 h old against a 9.52 h record, and STEP 5.5 says only
dispatch what you have the budget to see through.

## Pause reason
**Not paused.** `T384` dispatched and being awaited. Fire is 8.2 h old at the time of writing;
longest on record is 9.52 h. `T384` was dispatched with its verdict-critical checks ordered FIRST and the
95-minute full drive LAST, so a kill mid-review still leaves a usable verdict.
