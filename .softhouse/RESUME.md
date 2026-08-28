# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-080001`, chain iteration 2 — **IN FLIGHT. SEVEN WORKERS. NOT CLOSED.**

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
| `T258` | `softhouse/T258-frontier-rot-residuals` | A live broken assertion (`all 9 rows`) plus the **rot mechanism** that produced it. **The driver's brief said the true value was 109; it is 11 — see the correction below.** |
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
  dead-path frontier 109 == pinned | FAIL-OPEN frontier 11 == pinned | corpus 1281 | P-number citations PASS
```

## Pause reason

**None — work is in flight.** The oracle is REACHABLE. If this fire is interrupted before the batch is
awaited, every task above is `in_progress` with a branch: recover WIP from the branch, mark each
`needs_retry` with `worker killed mid-flight; completeness unverified`, and **do not** trust this table as a
record of what finished.

---

## UPDATE — batch 2 dispatched, and batch 1's first result

**`T280` came back REJECTED and is MERGED (`346b7a1d`).** It is the only batch-1 task that is finished. The
other five are still live. Its three findings all became work rather than notes:

| New/changed | From | Why |
|---|---|---|
| `T342` **dispatched** → `softhouse/T342-releasedat-failopen` | F-A | `lock_released_at()` cuts at the first **comma** and its strip class has no `}`, so a LOCK with `"released_at": null` as its **last key** reads as `null}`, arm 1 fires, and **a live lock is declared FREE**. P-85 failure mode. Driver re-derived it from `fire-program.sh:120-131` before filing. |
| `T343` filed, **blocked on `T342`** | F-B | The seven arms partition **only inside `rules.py`, and there by construction**. The shipped prose multi-matches 36 states; the shipped wrapper is first-match-wins and transposing arms 3/4 flips 3 of 192 verdicts. STEP 0's stated protection against P-85 is not actually there. |
| `T336` **REFRAMED and dispatched** → `softhouse/T336-post-checkout-decision` | F-C | The hook **cannot refuse**: on `/usr/bin/git` 2.50.1, `enforce` returns rc=1 **and git creates the worktree anyway**. The task filed an hour ago as "install it" is now "decide what mechanism is available and worth having", with *nothing is worth it* listed as a legitimate answer. |

**This is why `T336` was gated on `T280` rather than shipped in batch 1** — the review refuted the task
before the task ran.

**Serialisation now:** `T323` holds `conformance.sh`. `T342` holds `fire-program.sh` — `T336` has been told
in its prompt that it may not touch that file this batch even if its own analysis points there, and must hand
the patch to `T343` instead.

---

## UPDATE 2 — `T270` complete and awaiting review; batch 3 dispatched

`T270` committed to `softhouse/T270-superseded-trap` (`512040fc`). **NOT merged** — it is a `coder` task and
gets an independent reviewer first. Driver scope-check passed: 15 files / 3558 insertions, nothing outside
`files_hint`, and `prove-mkreq7-guard-red.py` is **byte-identical** (T114 honoured) and no longer invoked.

**It reported three things past its brief, and the first is the sharpest:**

1. `.softhouse/reviews/A2-11/run-all.sh` §§2,4,5,6,7 **abort with tracebacks** — five hard-coded paths into a
   retired worktree — while the committed transcript records §§3–8 all at `exit=0`. So **exactly one section
   was producing a real verdict, and the superseded trap was the only other thing on screen printing green.**
2. Widened census over **5 registers / 1,345 callers → 54 live in-place invocations**, none named by the
   brief: `cap.sh` ×52, `cap9.sh` ×1, and **`resolve7.py` ×1, graded MATERIAL — a P-25 float site on the
   transport that captures oracle evidence.** Reported, not fixed (correctly — another task's remit). → `T344`.
3. **T263's F-5 premise is false.** "Evidence names its producer" holds for **3 of 6** live records, not 6;
   a JSON request body has nowhere to name its producer. Enforcing it as written would have turned the guard
   permanently red on two MATERIAL records.

It also disclosed **two defects in its own work** unprompted — a red-drive that briefly committed this task's
own defect (an assertion satisfied by the census's own prose), and a census first cut that over-reported.

**Dispatched:** `T339` → `softhouse/T339-review-t270`.
**Filed, blocked on `T270`+`T339`:** `T344` — the 54 live invocations, `resolve7.py` first, because whether
any vector in `.softhouse/vectors/` was captured through a float-carrying transport is a **parity-corpus**
question, not a hygiene one.
