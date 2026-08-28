# The driver conflated two different frontiers, and T258 caught it by obeying the one instruction that saved it

**Fire** `20260828-080001`, chain iteration 2. **Recorded by the driver, about the driver. Corrected forward, not buried.**

## The error

This program has **two** independently pinned frontiers, and the driver wrote as though it had one:

| Frontier | Where it is pinned | Rows |
|---|---|---|
| **fail-open** | `FAILOPEN_PIN_FILE_LIST` in `.softhouse/conformance.sh` | **11** |
| **dead-path** | `.softhouse/guards/dead-path-frontier.pin` | **109** |

[VERIFIED: driver counted both directly — the `FAILOPEN_PIN_FILE_LIST` heredoc holds 11 `TIER1/TIER1B/TIER2`
rows; `grep -cvE '^\s*(#|$)' .softhouse/guards/dead-path-frontier.pin` returns 109. Not taken from T258's
report.]

`.softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh` asserts the **fail-open** frontier. The
driver's T258 brief told it *"the frontier … is 109 as of the previous chain iteration of this fire"* and
`RESUME.md` printed only `dead-path frontier 109 == pinned`, never naming the fail-open frontier at all — so
the one number on screen was the wrong one for the instrument under repair.

## Why it would have been worse than the bug it replaced

The instrument was asserting `all 9 rows`, stale since T248 moved the fail-open frontier to 10. Had T258
followed the brief and typed **109**, the instrument would have been **more wrong than before** — and wrong in
the direction that *looks* current, because 109 is a real, live, correctly-pinned number from the guard next
door. A stale 9 is visibly stale. A confidently wrong 109 is not.

## What actually prevented it

One sentence in the brief, and it is the only reason this is an observation rather than an incident:

> *"Read the live number yourself from `conformance.sh`'s output at your own commit; do NOT take 109 or 11
> from any task text, including this one."*

T258 did exactly that, found `frontier 11, pinned at 11`, and **reported the driver's number as wrong rather
than reconciling to it**. That is the sixth time in two fires a worker has refuted its own brief and been
right.

**The lesson is not "the driver should be more careful."** It is that *"do not trust this brief's cardinals,
re-read them live"* is worth writing into every brief that quotes a number, because the driver's numbers rot
exactly as fast as anything else this program has measured — and unlike an instrument, a brief has no guard.
Note the compounding evidence in the same task: T258 also found **its own task description's LEDGER bar had
rotted** (it says 4 parity + 2 refusal / 21 cells; the pinned values are **7 / 6 / 39**, moved on `main` at
`e2e62f83`). Three rotted cardinals in one task record, in three different currencies.

## Corrected

- `.softhouse/RESUME.md` — the bar block now names **both** frontiers; the T258 row carries the correction.
- This file.
- **NOT** retro-edited: merged handoffs, and T258's own task `description` in `tasks.json`, which is the
  historical record of what it was actually told. The `note` field carries the correction instead.
