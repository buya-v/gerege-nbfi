# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-080001`, chain iteration 2 — **IN FLIGHT. SIX WORKERS DISPATCHED. NOT CLOSED.**

**Read this before believing `HEAD`.** The previous chain iteration of this same fire closed clean and its
`RESUME.md` said so. That manifest is now stale by design: this iteration re-opened work. If you are a second
orchestrator reading this, the lock at `.softhouse/LOCK` is held by pid 86145 on `Buyanmunkhs-Mac-mini` and
six workers are live. **Do not dispatch anything from the READY list below.**

This file, `.softhouse/tasks.json` with all six tasks already `in_progress` and carrying their `branch`, and
the `LOCK` were **committed and pushed BEFORE the first `git worktree add` of this batch** — the obligation in
STEP 0 of the `softhouse-program` skill that was missed on 2026-08-22 (101 s late) and again on 2026-08-28
(135 s late, two of three artefacts late). It is being obeyed here in the same fire that recorded the second
miss.

## Batch 1 — dispatched, all six with `isolation: "worktree"`, all `opus`

| Task | Branch | What it is |
|---|---|---|
| `T323` | `softhouse/T323-wire-unwired-guards` | Wire the guards three authors built and could not wire. Holds `conformance.sh` — **nothing else in this batch may touch it.** |
| `T280` | `softhouse/T280-review-t279` | Independent review of T279's lock-partition fix; drives the post-checkout hook RED. Third layer of the same fix. |
| `T266` | `softhouse/T266-linter-ownership` | Fail-open linter's variable-indirect ownership blind spot — tier is currently a property of the linting **host**, not the file. |
| `T270` | `softhouse/T270-superseded-trap` | A superseded guard that still prints `ok … 0 failed` is a trap, not preserved evidence. |
| `T258` | `softhouse/T258-frontier-rot-residuals` | A live broken assertion (`all 9 rows` vs a frontier of 109) plus the **rot mechanism** that produced it. |
| `T335` | `softhouse/T335-rvpa-list-traversal` | T291's `F-T291-1`: R-VPA recurses into mappings, not lists. **Third repair in this lineage and the last the driver will file** — a rejection parks it. |

**Serialisation:** `T323` alone holds `.softhouse/conformance.sh`. The other five have disjoint `files_hint`.

## Filed this iteration, NOT yet dispatched

- `T336` — **install** the post-checkout push-before-spawn hook (`FU-T279-3`). Depends on `T280`, deliberately:
  a hook that refuses worktree creation can brick every future fire, so it does not get installed unreviewed.
- `T337`–`T341` — paired independent reviewers for `T323`, `T266`, `T270`, `T258`, `T335`.

## Closed by the driver without dispatch

- `T310` → **`superseded`**. Its whole brief (reverse T295's declination, promote `A2-02`) was discharged by
  `T307` (`ca745981`) in the previous iteration. Driver-verified against the vector's own `provenance` block
  (`capture_ref` = `…/A2-02-preclosure-before.json`, `capture_sha256` `c12e977f…`), not assumed.

## Bar on `main` at dispatch — inherited, measured by the previous iteration

```
bash .softhouse/conformance.sh   →  exit 0
  probe line PRESENT (presence tested BEFORE value) reading "up"
  46 parity vectors / 7884 cells / 0 FAIL / 0 inadmissible
  LEDGER parity 7 | oracle-refusal 6 | money cells 39 | all 13 wrong impls dying
  dead-path frontier 109 == pinned | corpus 1281 | P-number citations PASS
```

## Pause reason

**None — work is in flight.** The oracle is REACHABLE. If this fire is interrupted before the batch is
awaited, every task above is `in_progress` with a branch: recover WIP from the branch, mark each
`needs_retry` with `worker killed mid-flight; completeness unverified`, and **do not** trust this table as a
record of what finished.
