# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, batch 1 — **IN FLIGHT. FIVE WORKERS. NOT CLOSED.**

**Read this before believing `HEAD`.** The previous fire's manifest said six workers were live; that fire
(`20260828-080001`) was **killed by a `five_hour` rate limit** at 12:25 (+08) and its wrapper reconciled the
survivors. This manifest replaces it. If you are a second orchestrator, the lock at `.softhouse/LOCK` is held
by pid 75306 on `Buyanmunkhs-Mac-mini` and five workers are live. **Do not dispatch anything below.**

This file, `.softhouse/tasks.json` with all five tasks already `in_progress` and carrying their `branch`, and
the `LOCK` were **committed and pushed BEFORE the first `git worktree add` of this batch** — STEP 0's
push-before-spawn obligation, missed 101 s late on 2026-08-22 and 135 s late on 2026-08-28.

## What the killed fire actually left behind (measured, not assumed)

Four `coder` tasks **finished and are sitting unmerged on their branches, each awaiting the independent
reviewer that was killed before it started.** That is the whole shape of this fire: the bottleneck is review,
not authorship.

| Finished, unmerged | Head | Size | Reviewer (killed unstarted) |
|---|---|---|---|
| `T258` frontier-rot residuals | `0928fa16` | 19 files / +3955 | `T340` |
| `T270` superseded-guard trap | `512040fc` | 15 files / +3558 | `T339` |
| `T336` post-checkout decision | `f86c2e4a` | 18 files / +1627 | `T347` |
| `T342` `released_at` fail-open | `d870db1d` | 23 files / +1759 | `T346` |

## Batch 1 — dispatched, all five `isolation: "worktree"`, all `opus`

| Task | Branch | What it is |
|---|---|---|
| `T339` | `softhouse/T339-review-t270` | Review T270. **Re-dispatched over a T330 refusal — see the correction below.** |
| `T340` | `softhouse/T340-review-t258` | Review T258. Never started; all three T330 signals empty. |
| `T346` | `softhouse/T346-review-t342` | Review T342. Never started. |
| `T347` | `softhouse/T347-review-t336` | Review T336. Never started. |
| `T323` | `softhouse/T323-wire-unwired-guards` | **Continuation**, 5 commits already on the branch, completeness unverified. Holds `.softhouse/conformance.sh` **exclusively**. |

**Serialisation:** the four reviewers write only under `.softhouse/reviews/t3*/` — disjoint. `T323` alone
touches `conformance.sh`.

## Correction the driver made to the previous fire's reconcile

**T330's refusal to demote `T339` was keyed on the NAME of a rescue branch, not its CONTENT.** The ref
`softhouse/rescued-t339-base-20260828-080001` was read as "a live ref carries id T339, demotion would fork a
line that still exists". Measured: that ref holds **two** files — a 219-line deletion from
`.softhouse/reviews/A2-11/TRANSCRIPT-A2-11.txt` and `.t347-postcheckout-marker`, which is **T347's**
post-checkout probe — and `git ls-tree -r` finds **no path naming T339 anywhere on it**. It is a
*worktree-base* rescue, named after the worktree `t339-base`, carrying another task's marker. T339 produced
no review. Re-dispatched clean; the rescue ref is **left unpruned as evidence**.

This is a real gap in the reconciler and is filed, not just noted → `T350`.

## Bar on `main` at dispatch — driver-run this fire, not quoted

```
bash .softhouse/conformance.sh   →  EXIT=0
  probe line PRESENT (presence tested BEFORE value, P-83) reading "up"
  VERDICT: PASS (exit 0) — 46 parity vectors / 7884 cells / 0 FAIL / 0 inadmissible
  LEDGER parity 7 == pinned | money cells 39 == pinned | 142 ledger cells graded
  fail-open frontier 11 == pinned | host-state census 18 == pinned | corpus 1283
```

## Pause reason

**None — work is in flight.** Oracle REACHABLE. If this fire is interrupted before the batch is awaited,
every task above is `in_progress` with a branch: recover WIP from the branch, mark each `needs_retry` with
`worker killed mid-flight; completeness unverified`, and **do not** trust this table as a record of what
finished.
