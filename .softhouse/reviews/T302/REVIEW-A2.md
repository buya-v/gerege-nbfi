# T302 attempt 2 — INDEPENDENT review of T288 **as it stands on `main` after T309**

**Subject** T288 (`d8cf2c1`), as amended by T309 (merge `2dfbe422`). Files
`.softhouse/bin/fire-program.sh`, `.softhouse/bin/ready-tasks.py`.
**Reviewer** T302, branch `softhouse/T302-review-t288`, worktree
`agent-a3e635faba72121c8`.

## Provenance — one branch, two attempts, and I graded both

`softhouse/T302-review-t288` already carried **four commits** (`a1edd2b1` … `ab9b3b68`)
from an attempt killed mid-flight on 2026-08-23, forked from `5964ab5` — i.e. **before**
T309 existed. Its verdict (`REVIEW.md`, 351 lines) is REJECTED on four defects F1–F4.

I continued that ref rather than opening a case-variant, per the brief and per
`.softhouse/observations/20260827-branch-case-collision-shadows-committed-work.md`. The
branch is now merged onto `main` post-T309 (merge `f504d2c3`), so
`git diff main...softhouse/T302-review-t288` is attempt 1's evidence plus mine.

**Mechanical note the orchestrator needs:** the dead worktree
`agent-af389a54fb1b2ca43` still holds this branch checked out at `ab9b3b68`, so `git
checkout` of it from any other worktree fails. I advanced the ref with `git update-ref`
(fast-forward from `ab9b3b68`, old-value asserted). That worktree's on-disk `HEAD` is
now stale; it holds no uncommitted work I can see and should be pruned.

---

## VERDICT: **REJECTED** (split)

| part | verdict |
|---|---|
| T288's **core judgement** — REPAIR the artefacts the next fire reads rather than WARN | **APPROVED.** Unchanged from attempt 1. |
| T309's **defect-1 fix** — reconciler reachable from `on_signal`, defined at top level, bounded | **APPROVED.** Re-derived; it is correct and it is the strongest part of the diff. |
| T309's **fail-direction SPLIT** (two predicates, not one widened) | **APPROVED in design.** It is the right answer to P-91/T292. |
| T309's **replacement discriminator** (`in_session` ownership) | **REJECTED — F5, CRITICAL.** It demotes seven live workers of the very fire it was written for. Same shape, same direction, same magnitude as the near-miss T309 caught in attempt 1. |
| the **`wrapper`-mode authority grant** | **REJECTED — F7, HIGH.** |
| **F1, F2, F3** from attempt 1 | **STILL REJECTED.** T309 closed none of them. F1 now confirmed on real corpse data. |
| **F4** | **PARTIALLY CLOSED.** One of its three false paths was fixed; the sentence is still unconditional. |
| T309's **budget** claim | **UPHELD.** Re-measured. This is a negative result and I report it as one. |

Not a MICRO-FIX. F5 alone is a redesign of the ownership evidence, and F7 is a
cross-file contract change. It goes back.

---

## Bar — conformance, re-run by this reviewer

`bash .softhouse/conformance.sh` (bash, never `sh`), staged to a file, unpiped.
**P-84** — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT
THE VALUE."* [VERIFIED: `.softhouse/patterns.md:2782`]. Read in that order:

1. **PRESENCE first** — `grep -c "reference oracle"` → **7 lines**; `grep -c "probe = "` → **1**. The probe line is PRESENT.
2. **THEN the value** — `conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up`
3. **THEN the verdict** — `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.` `EXIT=0`.

Identical to the bar attempt 1 recorded and to `main`'s. Transcript:
`.softhouse/reviews/T302/a2/out-conformance.txt`.
**No finding in this review moves a money cell.** No `.go` file, no `nexus/`, no DEC or
contract file, no schema column, no fixture is touched by T288+T309 or by me
[VERIFIED: `git show 2dfbe422 --stat`, 35 files, all under `.softhouse/`].

---

# What T309 CLOSED, and what it did NOT

| attempt-1 finding | status after T309 | evidence |
|---|---|---|
| **defect 1** — `on_signal` never reached the reconciler | **CLOSED, and the root was stronger than stated.** `reconcile_tasks_json` was *defined inside* `run_exit_guard`, so on a first chain iteration the name did not exist when the traps were armed — **uncallable**, not merely uncalled. `reconcile_bounded()` now guards on `typeset -f reconcile_tasks_json` explicitly. | `fire-program.sh:647-662`, and T309's matrix 3/3 |
| **F1** — `main..B` cannot tell MERGED from NEVER-COMMITTED | **NOT CLOSED.** `branch_wip()` is byte-identical: `n == 0` still prints *"has NO commit ahead of main — nothing was ever committed to it"*. **Now confirmed on real data: 3 of the 8 real corpses hit it.** | F9 below, `ready-tasks.py:526-553` |
| **F2** — the worktree rescue discards all three git rcs and logs `rescued` unconditionally | **NOT CLOSED.** `fire-program.sh:1326-1331` unchanged; `RESCUE_PAIRS+=` still appended on a rescue that may not have happened. The fail-closed twin at `:1211-1224` is still applied to the main tree only. | `fire-program.sh:1324-1337` |
| **F3a** — `[[ "${first:t}" == claude ]] \|\| continue` is a one-way filter, so `examined=0` → `return 1` → *authorise the rewrite* | **NOT CLOSED.** Line unchanged. T309 added a `STOPPED_TREE` skip, which narrows nothing here. | `fire-program.sh:1040` |
| **F3b** — an idle interactive `claude` in the repo root makes the reconciler refuse forever | **NOT CLOSED.** The skip list holds only `DRIVER_TREE`. Measured live today: exactly one in-repo `claude`, and it is the driver — so the assumption holds *today* and the hazard is unchanged. | F11 below |
| **F4** — the STEP-0 report promises a repair on three paths where it does not happen | **PARTIALLY CLOSED.** Path 1 (signal) is fixed. Paths 2 and 3 (both REFUSE verdicts) remain, and the four `print` lines at `ready-tasks.py:787-790` are still **unconditional**. | `ready-tasks.py:787-790` |

---

# NEW findings

## F5 — **CRITICAL, REJECT.** The replacement discriminator demotes SEVEN LIVE WORKERS of the exact fire it was written for

**Where** `ready-tasks.py:369-483` `dispatches_predating_this_fire()`, consumed by
`task_is_demotable_in_session()`.

**The premise, quoted from its own docstring:**

> *"The wrapper commits `.softhouse/tasks.json` as it stood the moment it took the lock…
> **At that instant this fire has dispatched NOTHING** — so every task claiming
> `in_progress` in THAT blob is a claim inherited from an earlier fire."*

The second sentence does not follow from the first. "This fire has dispatched nothing
**yet**" is true. "Therefore nothing in that set will ever be this fire's own dispatch"
is false, **and the counter-example is the incident T309 was written about.**

**Real history, read from this repo** [VERIFIED, all from this checkout]:

| instant | commit | fact |
|---|---|---|
| 14:00:08 | `5428c0a4` | fire `20260823-140001` takes its lock. **8 tasks already `in_progress`** — the corpses `20260823-080004` left. |
| 14:05:01 | `5964ab54` | *"DISPATCH fire 20260823-140001 batch 1 — 8 workers, PUSHED BEFORE SPAWN (P-85)"* — and **7 of the 8 ids it dispatches are the same 7 ids.** |
| 14:24:27 | `ab9b3b68` | `softhouse/T302-review-t288` head — a commit by a **live worker of that fire**, on an id inside the lock blob. |
| 14:23:21 | — | same for `softhouse/T306-adjudicate-admit-widening`. |

**Driven, on `main`'s bytes** (`ready-tasks.py` sha256 `cdc0729107b71696`) —
`.softhouse/reviews/T302/a2/drive-f5-cell.zsh`, transcript `a2/out-f5-cell.txt`. It
re-runs **T309's own cell shape** with one thing changed: the clock.

```
CELL B   (T309's cell)      lock=5428c0a4  state=5428c0a4  -> 8 demotable   OK
CELL B'  (same fire, +5min) lock=5428c0a4  state=5964ab54  -> 7 demotable   WRONG (correct: 0)
             IN-SESSION authority: 7 demotable, 1 WITHHELD
             T297 T298 T302 T304 T305 T306 T308  — every one a LIVE worker
```

**Why the matrix missed it, and this is the important part.** T309's
`run-ownership-matrix.zsh` cell B is literally:

```zsh
cell "B: CORPSES OF 20260823-080004 ..."  5428c0a4  5428c0a4  20260823-140001  0  8
#                                         ^lock     ^state-under-test
```

**The lock commit and the state under test are the same commit.** The clock is frozen
at the instant the lock was taken. Cell A is the only cell that advances it, and cell
A's fire (`20260827-230001`) happens to have dispatched only ids that were **not** in
its lock blob — so the matrix contains no cell in which the clock advances *and* the
fire re-dispatches an inherited id, which is precisely the shape of the incident.
8/8 was earned against a frozen clock.

**This is the sibling the brief asked for.** T309's own headline is that attempt 1's
`task["fire"] != LOCK["fire"]` reported *"6 demotable"* for six live workers. The
replacement reports *"7 demotable"* for seven live workers, in the same direction
(irreversible), on the same incident. The evidence source changed from a field to a
git blob; the **inference** — "state at dispatch-time t₀ determines ownership for all
t > t₀" — did not, and it is the inference that is wrong. A fire that *resumes* rather
than dispatching fresh is not an exotic case: it is the documented reason the driver
opens on inherited `in_progress` tasks at all.

**REPRODUCTION**
```
zsh .softhouse/reviews/T302/a2/drive-f5-cell.zsh
```
Read-only against the repo, `--dry-run`, everything under `$TMPDIR`.

**Remedy** (author's call). The set must be recomputed, not frozen — e.g. re-read the
blob at *this fire's most recent dispatch commit* and take the intersection with the
lock blob, or record a per-dispatch marker that a re-dispatch necessarily rewrites
because writing it is how the dispatch happens. Any fix must be graded by a cell whose
**state-under-test is strictly later than its lock commit**; T309's matrix has exactly
one such cell and it is the easy one.

---

## F6 — **HIGH, REJECT.** The anchor is a substring search over prose, and `-1` takes the newest match

**Where** `ready-tasks.py:447-449`:

```python
subject = "softhouse: local fire lock (%s)" % lock_fire
rc, sha, err = _run([GIT, "log", "-1", "--format=%H", "--fixed-strings",
                     "--grep", subject])
```

`--grep` matches the **whole commit message**, subject *and body*. `-1` returns the
**newest** match. So the anchor is not "the wrapper's lock commit"; it is "the most
recent commit that mentions that string anywhere".

The docstring anticipates only the absence case and calls it safe:

> *"If the wrapper's commit subject is ever changed, this stops finding the commit and
> REFUSES — which is the safe direction, and it is why the subject is quoted rather than
> pattern-matched."*

True for **absence**. It says nothing about **multiplicity**, and multiplicity fails the
other way — toward demoting.

**Driven** — `a2/drive-f6-grep.zsh`, transcript `a2/out-f6-grep.txt`, on the real
`20260823-140001` blobs:

| cell | anchor picked | demotions (correct: 0) |
|---|---|---|
| 1 baseline — only the real lock commit carries the string | the lock commit | **7** (this is F5) |
| 2 — a later **review** commit whose *body* quotes the subject with a real fire id | the review commit | **8** |
| 3 — a second commit with the same subject (lock re-acquire) | the second one | **8** |

Cells 2 and 3 escalate 7 → 8: the anchor moves past the dispatch, so even the one task
the correct anchor withheld is swept in.

**The population that writes such messages is reviewers and handoffs describing this
mechanism.** T309's own merge message `2dfbe422` quotes the subject — with a `<id>`
placeholder, so it is inert. A reviewer who quotes it with a real id arms this. I
checked the current repo: `git log --fixed-strings --grep` for each of five real fire
ids returns **exactly one** commit each, so **no live instance exists today**
[VERIFIED: `20260827-230001`→`558ef320`, `20260823-140001`→`5428c0a4`,
`20260823-080004`→`3198b657`, one line each].

`STAMP="$(date +%Y%m%d-%H%M%S)"` [VERIFIED: `fire-program.sh:41`] is second-resolution,
so cell 3 from the wrapper itself needs two fires in one second — unlikely. Cell 2 needs
one sentence in one commit message.

**REPRODUCTION** `zsh .softhouse/reviews/T302/a2/drive-f6-grep.zsh`

**Remedy** Anchor on something a message cannot imitate: `git log --format=%H
--diff-filter=A -- .softhouse/LOCK` (the commit that *added* the lock file), or
`git log -1 --grep "^softhouse: local fire lock" --extended-regexp` anchored to the
subject only, plus **refuse on more than one match** rather than taking the newest.

---

## F7 — **HIGH, REJECT.** `wrapper` authority is granted to callers that established nothing

**Where** `ready-tasks.py:323-328`, the first leg of `caller_is_lock_holder()`:

```python
if not os.path.exists(lock):
    return "wrapper", "no .softhouse/LOCK on disk -- nobody holds this repo", None
```

T309's fail-direction table justifies `wrapper` mode's demote-everything like this:

> *"The caller has already established out of band that there is nothing live to
> destroy"* — naming `foreign_live_session_in_repo()` as the thing that established it.

**That gate lives in `fire-program.sh:1136`, not in `ready-tasks.py`.** The precondition
is **assumed by the callee and enforced by exactly one caller**. Any other caller — and
the module docstring at `ready-tasks.py:89` publishes the invocation — gets the authority
for free the moment the lock file is not on disk.

**Driven** — `a2/drive-f7-nolock.zsh`, transcript `a2/out-f7-nolock.txt`:

```
CELL 1  no LOCK on disk, 8 live workers in tasks.json
        lock: no .softhouse/LOCK on disk -- nobody holds this repo
        mode: wrapper
        RESULT: DRY RUN -- 8 task(s) WOULD be demoted
```

and `ready-tasks.py` contains **no liveness check of its own** — no `lsof` call, no cwd
read; its six `/bin/ps` references are all `ps_ancestors()`, which answers *"who am I"*,
never *"is anyone else alive in this checkout"* [VERIFIED: transcript section 0].

**T309 knew.** Its own comment in `on_signal` says the first draft removed the lock
before reconciling and that driving it showed *"its authority check had NOTHING TO CHECK
and every caller would have been granted `wrapper` mode by default … the same 'wired to
the wrong path' shape this task exists to fix, reintroduced by the fix"*
[VERIFIED: `fire-program.sh:722-736`]. It fixed the ordering on **its** path and left
the leg armed for everyone else.

Reachable windows: the P-85 two-orchestrator day (*"TWO ORCHESTRATORS HELD THE LOCK AT
ONCE, AND THE CAUSE WAS AN UNPUSHED IN-FLIGHT STATE"* [VERIFIED:
`.softhouse/patterns.md:2791`]); any hand invocation between fires while a session is
working; and a `cat > "$LOCK"` that failed — its rc is not read
[VERIFIED: `fire-program.sh:204-219`].

**REPRODUCTION** `zsh .softhouse/reviews/T302/a2/drive-f7-nolock.zsh`

**Remedy** No LOCK must mean **refused**, not **wrapper**. Give the wrapper an explicit
`--i-have-established-no-live-session` argument it must pass (it *has* established it;
nobody else has), and make the absent-lock leg refuse. That inverts the burden —
*"require the document to POSITIVELY DEMONSTRATE coverage in a form the rule CONSTRUCTS
rather than RECOGNISES"*, which is P-91's own escape [VERIFIED: `patterns.md:2947`].

**Minor, same function:** the ancestry test is `pid not in [p for p, _ in anc]`, and
`ps_ancestors` walks up to and including **pid 1**. A LOCK naming pid 1 therefore always
passes ancestry [VERIFIED: cell 2 of the same transcript reached `in_session`, not
`refused`]. Low severity today — the wrapper writes `"pid": $$` — but the check is
weaker than it reads.

---

## F8 — **NEGATIVE RESULT.** The budget claim is UPHELD on re-measurement

The brief said re-measure, do not accept. I did, and **T309 is right**.

`reconcile()` calls `branch_wip()` **once per demoted task**, and `branch_wip` makes
**two** `git` subprocess calls. In `wrapper` mode — the signal path — every `in_progress`
task is demoted, so cost is linear in the number of corpses. (T309's "two git calls
total, not per task" saving applies to `dispatches_predating_this_fire`, which the
signal path never calls.)

**End-to-end, real 792 KB `tasks.json`, N real branches, `--dry-run`, 3 trials, median**
(`a2/drive-f8-cost.zsh`, transcript `a2/out-f8-cost.txt`):

| N | median | git calls | vs the ~7 s signal budget |
|---|---|---|---|
| 0 | 0.106 s | 0 | startup + parse only |
| 4 | 0.449 s | 8 | fits |
| 8 | **0.715 s** | 16 | fits |
| 16 | 1.300 s | 32 | fits |
| 32 | 2.457 s | 64 | fits |
| **40** | **3.037 s** | 80 | **fits** |
| 64 | 3.876 s | 128 | fits |

**Calibrated against the real repo's 583 refs / 47,763-byte `packed-refs`**
(`a2/drive-f8b-realgit.zsh`): `rev-parse --verify` 0.0312 s, `rev-list --count`
0.0368 s → **0.0679 s per task**. Scratch and real agree, so the scratch numbers are
representative. Crossover with the ~7 s budget is at **N ≈ 100** — half of the 203 tasks
in `tasks.json`.

The budget itself is `SIGNAL_GRACE_SECS(20) − elapsed − GIT_PUSH_TIMEOUT_SECS(10) − 2`
[VERIFIED: `fire-program.sh:745`] ≈ 7 s with the shipped defaults.

**Answer to the brief: at 40 tasks it costs ~3 s and fits.** The A/B is on comparable
bytes: the same `ready-tasks.py`, the same real `tasks.json`, only N varying.

**What I did NOT re-measure:** T309's headline **2.12 s vs 6.83 s** wrapper A/B. That
needs a full scratch wrapper harness with a fake `claude` and a reparented wrapper, and I
judged F5 the better use of the time. I did re-derive it from source and it is
arithmetically consistent: `stop_driver` replaced `/bin/sleep "$DRIVER_STOP_GRACE_SECS"`
(an unconditional 5 s) with a 0.1 s poll of the same maximum
[VERIFIED: `fire-program.sh:454-500`], and 6.83 − 2.12 = 4.71 ≈ 5 s minus poll cost.
**[UNVERIFIED by me: the 2.12 / 6.83 figures themselves.]**

### F8b — **LOW.** The two-layer budget gives the graceful layer zero margin over the brutal one

`on_signal` sets `RECONCILE_DEADLINE_SECS=$budget` and then calls
`reconcile_bounded "$budget"` — **the same number** [VERIFIED: `fire-program.sh:753-754`].
The design's stated polarity is that the inner deadline degrades gracefully (WIP evidence
→ UNVERIFIED, **demotion still lands**) while the outer bound is brutal (subtree killed,
**nothing written**). But the inner path only *begins* degrading at the instant the outer
kill is due, so the graceful path can never complete before the brutal one fires. The
inner deadline should be the outer budget minus the time the degraded tail needs to write
(measured above at ~0.1 s for parse+write). As shipped, the two-layer design collapses to
one layer in exactly the case it was built for.

---

## F9 — **F1 CONFIRMED ON REAL CORPSES.** This is the brief's item 1, and it lands

**The brief's central claim** — *"the reconciliation has never been driven against a REAL
killed `claude` worker"* — needs splitting, because two different gaps hide under it.

**Gap A, the process gap: not real, and I say so rather than pretending to close it.**
A corpse is defined by **absence** from the process table. The reconciler's process-facing
inputs are `ps` name/stat, `kill -0`, and `lsof -d cwd`; a killed real `claude` and a
never-started fake are byte-identical to all four. The *live* side of that probe was
already driven against a **real live `claude`** by attempt 1 (`out/3-liveness-probe.txt`,
pid 4692) and re-driven by me today (F11). So there is no discriminating power to be won
by spending a real `claude` on it, and I did not.

**Gap B, the evidence gap: real, still open, and I closed it.** T309's matrix builds a
fresh `git init` repo per cell and plants real *blobs* in it — but **no real refs**. So
every `branch_wip()` call in every cell answers `absent` for a reason that has nothing to
do with any corpse. **The WIP evidence — the entire content of the note T288 exists to
write — has never once been graded against a real branch.**

**Driven** — `a2/drive-f9-realcorpses.zsh`, transcript `a2/out-f9-realcorpses.txt`.
A `--shared` clone with **all 528 heads** fetched, `tasks.json` = the real blob at
`5428c0a4`, run in both modes:

```
in_session (real anchor found)  -> 8 demotable, 0 withheld, 0.910s
wrapper                         -> 8 demoted,                0.749s
```

and the ground truth for the eight notes it printed:

| branch (as recorded on the corpse) | ahead of main | merged? | the note T288 writes |
|---|---|---|---|
| `softhouse/T297-review-t295` | 0 | **MERGED** | *"nothing was ever committed to it"* — **FALSE** |
| `softhouse/T298-review-t256` | 0 | **MERGED** | *"nothing was ever committed to it"* — **FALSE** |
| `softhouse/T308-review-t292` | 0 | **MERGED** | *"nothing was ever committed to it"* — **FALSE** |
| `softhouse/T299-t256-flagged-defects` | — | **REF ABSENT** | *"no WIP was found under that name"* — the branch was **renamed** to `softhouse/t299-t256-namespace-collision`, which exists at `7b664474` |
| `softhouse/T302-review-t288` | 7 | unmerged | correct |
| `softhouse/T304-evidence-destruction` | 7 | unmerged | correct |
| `softhouse/T305-openingbalance-…` | 5 | unmerged | correct |
| `softhouse/T306-adjudicate-…` | 5 | unmerged | correct |

**Three of eight real corpses — 37.5% — get a note that states the opposite of the
truth, and all three are demoted to `needs_retry`, which is the status that offers a
task for re-dispatch.** The next fire is invited to redo work that is already on `main`.
A fourth gets a false "no WIP" because the recorded branch name is stale.

That fourth row is a **third instance of the field-shaped defect** the brief asked me to
hunt: after `task["fire"]` and `task["dispatched_at"]`, `task["branch"]` is also stamped
at dispatch and not refreshed, and it drives both the WIP evidence *and* the rescue
pairing (`RESCUE_PAIRS` matches a worktree's prior branch against `tasks.json .branch`,
`fire-program.sh:1333-1337`).

**REPRODUCTION** `zsh .softhouse/reviews/T302/a2/drive-f9-realcorpses.zsh`

---

## F10 — **MEDIUM, informational but present-tense.** The shipped discriminator is inert on the machine it shipped to

The LOCK the **currently running** fire wrote carries **no `fire` field**
[VERIFIED: `git show HEAD:.softhouse/LOCK` → `grep -c '"fire"'` = **0**; identical on
disk at `.softhouse/LOCK`, read only]. `caller_is_lock_holder()` therefore sets
`lock_fire=None`, and `dispatches_predating_this_fire()` returns
*"the LOCK records no `fire` id … REFUSING (fail-closed)"* — so **`in_session` mode is
100% inert for this fire**.

Cause is version skew, and it is structural: the wrapper is edited by the fires it runs.

| fact | evidence |
|---|---|
| wrapper pid 68244 started `Thu Aug 27 23:00:01 2026` | `/bin/ps -o lstart=` |
| `"fire": "$STAMP"` was introduced by T309 attempt 1 `825c8e8f` and merged at `2026-08-27 23:24:36` (`2dfbe422`) | `git log -1 --date=iso` |
| `git merge` renames into place → new inode → the running zsh keeps its original bytes | T309's own probe, LEG C: `TAIL: ORIGINAL` |

**Consequences the driver needs to know, today:**
- `wrapper` mode is unaffected — it never calls the discriminator, and `--fire` comes
  from `$STAMP` on the command line, not from the LOCK.
- **If this fire is SIGTERMed it runs the PRE-T309 `on_signal`** (`stop_driver;
  release_lock; exit`). T288's defect 1 is still live for the process currently holding
  the lock. T309's fix takes effect on the next fire.

**The deeper point.** T309's thesis is *"derived from doing the work rather than
maintained beside it"*. Its replacement still **gates on `lock_fire`, a field on the
LOCK** — the maintained-field shape it was rejecting — and that field is missing right
now. The derivation is only as good as the field that unlocks it.

**REPRODUCTION** `bash .softhouse/reviews/T302/a2/drive-f10-liveskew.sh` (read-only).

---

## F11 — F3b re-driven on today's process table: the assumption holds, the hazard does not go away

`a2/drive-f11-probe-live.sh`, read-only (`ps` + `lsof`, no signals):

```
PID      STAT   IN-REPO   CWD
68308    SN     YES       /Users/buv/gerege-nbfi
claude processes examined=1 in-repo=1
```

- **T288's in-process-subagent assumption still holds** [VERIFIED]: six workers were
  live and there is exactly **one** `claude` process. F3c stays latent.
- Its cwd is the repo root, so `foreign_live_session_in_repo()` returns **0 = REFUSE**.
  On the *signal* path `STOPPED_TREE` skips it, so T309's fix works there. On the
  *normal tail* the driver has already been waited on, so the probe is clean.
- **But T309's fail-direction argument leans on this:** in-session's tolerated lie is
  said to be safe *"because that lie has a second reader: the wrapper's own exit path, in
  `wrapper` mode, clears whatever is left"*. That second reader fires **only when this
  probe returns 1**. F3b is unfixed: any interactive `claude` in the repo root — the
  documented `/softhouse` entry point — returns 0, and the second reader never fires.
  The argument is conditionally true and is stated unconditionally.

---

# Adjudicating T309's own follow-ups

### (a) the `fire` / `dispatched_at` re-stamp — **COSMETIC AND HALF-DONE**

The driver re-stamped `fire` for this fire's tasks in `6490ab90`. Measured against
`tasks.json` at HEAD:

| claim | measurement |
|---|---|
| *"all seven are re-stamped to dispatch-truth"* | `fire` yes; **`dispatched_at` NO** — T299/T302/T304/T305 still carry `2026-08-23T03:57:24Z`, four days stale, and `main()` prints it beside `fire` as a matched pair |
| the two tasks this fire dispatched in batch 2 | T312, T314 carry `fire` but **`dispatched_at` is absent entirely** |
| coverage | **12 of 203** tasks carry `fire` at all |
| the writer | **unchanged.** The re-stamp is a hand-edit in a commit; the next re-dispatch reproduces the staleness exactly |

That last row is decisive. **P-45 — *"a guard that only works when someone remembers to
run it enforces nothing"*** [VERIFIED: `.softhouse/patterns.md:1472`, *"Rule: when
hardening a check, verify the path that actually executes in CI/conformance calls it,
not merely that a test does."*]. A field that only stays true when someone remembers to
re-stamp it is the same rule with the verb changed, and the measurement is that this
round of remembering already missed half the fields. **Sufficient? No — cosmetic.** And
F5 shows it buys nothing anyway: the discriminator does not read `fire`.

**My recommendation: delete `fire` and `dispatched_at`.** T309's own follow-up offers
the choice ("either re-stamp both on every dispatch, or delete the fields") and the
evidence now favours deletion: three consecutive attempts to make a dispatch-time field
authoritative have failed, and nothing left in the code depends on them.

### (b) branch names differing only in case — **CONFIRMED, NOT DUPLICATED (T312 owns it)**

Recording only the count so it is on the record: `refs/heads/softhouse/` contains both
`softhouse/T305-openingbalance-accepting-side` and
`softhouse/t305-openingbalance-accepting-side`, and `tasks.json` at HEAD mixes cases
inside one file (`softhouse/T302-review-t288` beside `softhouse/t299-…`,
`softhouse/t304-…`, `softhouse/t305-…`). Everything else is T312's.

### (c) **none of this is covered by `conformance.sh`** — **UPHELD, and it is the root of F5, F6 and F7**

```
grep -c "fire-program\|ready-tasks\|reconcile\|in_progress" .softhouse/conformance.sh
0
```

Not one mention, in 3,101 lines [VERIFIED, this checkout].

The standard this repo holds itself to is **in the same file**, at `conformance.sh:909-915`:

> *"EACH GUARD RUNS ITS OWN SELFTEST FIRST, IN THE SAME INVOCATION. A wired guard that
> has been quietly neutered is worse than an unwired one, because it is believed (P-22).
> So the selftest — which drives the guard RED on a planted defect AND requires it to
> stay GREEN on a clean tree (P-50) — runs on every conformance run, **not on the day
> someone remembers**."*

**P-22 — *"A guard, a canary, or a control that cannot fail is worse than none — because
it is believed"*** [VERIFIED: `.softhouse/patterns.md:442`].

This is the finding underneath the other findings. T309 built an eight-cell ownership
matrix and a three-cell SIGTERM matrix — good harnesses, and one more cell in the
ownership matrix would have caught F5. They live in `.softhouse/capture/` and **nothing
runs them**. So the diff shipped 8/8 green against a frozen clock, and the code that now
decides whether to destroy live work has **zero** automated coverage. That is **P-45
moved one level out**: the *guards* are correctly wired to the signal path; their
*tests* are wired to nothing.

**This must be a filed task, not a sentence.** **P-89 — *"THREE ARTEFACTS SHIPPED WIRED
TO NOTHING IN ONE FIRE … THE FIX IS A FILED TASK, NOT A SENTENCE"*** [VERIFIED:
`patterns.md:2904`, restated at `:3008` as *"prose does not fire on the next fire"*].
I have not filed it — `tasks.json` belongs to the live fire and I write only to
`.softhouse/reviews/T302/`. The task, precisely scoped: **wire
`run-ownership-matrix.zsh` and `run-matrix.zsh` into `conformance.sh` as a HARD guard
with its own RED/GREEN selftest, and add the clock-advanced cell (F5's B′) as a
permanent cell.**

### (d) T309's other two follow-ups

**Follow-up 3** (a killed worker with real commits under a `(pending)` handoff is
invisible to review) — I hit it myself: this branch had four commits and no handoff.
The remedy T309 suggests (lead the demotion note with the commit count and head sha) is
right and **cheap**, and `branch_wip` already computes both.

**Follow-up 4** (the signal path skips the worktree WIP sweep) — accepted as stated, but
note the compounding: attempt 1's F2 (unverified rescue claimed as evidence) is unfixed,
so the *next* fire's sweep — the one that is supposed to absorb the one-fire delay — is
the same sweep that logs `rescued` when git returned 128.

---

# What I checked and found CLEAN, so silence is distinguishable from not looking

- **Money non-negotiables: not engaged.** No `.go` file, no `nexus/`, no DEC or contract
  file, no schema column, no API field, no fixture in T288+T309's 35 files
  [VERIFIED: `git show 2dfbe422 --stat`]. The only arithmetic added is wall-clock
  seconds in signal-budget code — durations, not money.
- **The reconciler never writes under `--dry-run`.** Every drive in this review used it;
  `reconcile()` returns before the `os.replace` [VERIFIED: `ready-tasks.py:696-699`].
- **`reconcile_bounded`'s "defined yet?" guard is real and correct** — it is the direct
  repair for the uncallable-function root, and it fails closed with a named verdict
  [`fire-program.sh:656-661`].
- **`stop_driver`'s `/bin/ps`-not-answering leg fails closed** — it waits the full grace
  and treats the whole tree as surviving, rather than reading silence as death
  [`fire-program.sh:481-488`].
- **`wait_bounded` is wall-clock (`zsh/datetime`), not a tick count** — the specific
  defect it replaced.
- **`_run()`'s polarity is right**: missing binary / timeout / exhausted budget / OSError
  all return `rc=None` and render as UNVERIFIED, never as the reassuring answer.
- **The `BUDGET_NOTE` disclosure is honest** — it says the demotions are unaffected and
  only the evidence is UNVERIFIED, which is true.
- **Cell D's vacuous-green catch is genuine self-criticism and the harness fix is right**
  (any cell producing no `RESULT:` line now fails).
- **`STOPPED_TREE` is set unconditionally at the end of `stop_driver`, including on the
  "still on the process table after SIGKILL" branch** — so the log line *"anything
  downstream that reads process liveness will see them and may REFUSE; that is the safe
  direction"* [`fire-program.sh:528`] is **not true**: the skip list contains those
  pids, so `foreign_live_session_in_repo()` will *not* see them. NIT-level in practice
  (a SIGKILLed process in an uninterruptible wait is not running code) but the comment
  states the opposite of the behaviour and the next author will believe it.
- **`fire-program.sh:197-204` still documents attempt 1's discarded design** — *"`fire`
  IS RECORDED HERE, AND IT IS LOAD-BEARING … `ready-tasks.py --reconcile`, in
  `in_session` mode, demotes an `in_progress` task only when the task's own `fire`
  differs from THIS value"*. Written by `825c8e8f`, contradicted by `0e5eb2ab`, not
  updated. The wrapper now documents a rule the resolver explicitly refuses to follow.
  **This one is a genuine MICRO-FIX** (delete/replace one comment block).
- **`--fixed-strings --grep` cannot be confused by the release commit**: *"softhouse:
  release local fire lock (X)"* does not contain *"softhouse: local fire lock (X)"* as a
  substring [VERIFIED by inspection and by the F6 baseline cell].
- **P-86 compliance:** every P-number in this review carries its rule text and a line
  citation — *"AN ID IS A CARDINAL. Never restate a pattern id without the rule text
  beside it"* [VERIFIED: `.softhouse/patterns.md:2823`].

---

# Severity summary

| # | severity | direction | closed by T309? |
|---|---|---|---|
| **F5** | **CRITICAL** | fail-OPEN toward **demoting live work** (irreversible) | new in T309 |
| **F7** | **HIGH** | fail-OPEN toward **demoting live work** | pre-existing, knowingly left |
| **F6** | **HIGH** | fail-OPEN toward **demoting live work** | new in T309 |
| **F1** | **HIGH** | fail-OPEN in the evidence → duplicated work | **no** |
| **F2** | **HIGH** | fail-OPEN → a rescue claimed but not performed | **no** |
| **F3a** | **MEDIUM** | fail-OPEN (`examined=0` spelled like "nobody") | **no** |
| **F3b** | **MEDIUM** | fail-CLOSED into inertness | **no** |
| **F10** | **MEDIUM** | fail-CLOSED (safe), but the shipped capability is inert today | n/a |
| **F4** | **MEDIUM** | a false promise in the STEP-0 report | partially |
| **(c)** | **HIGH (process)** | zero conformance coverage — the reason F5/F6/F7 shipped green | **no** |
| **F8b** | **LOW** | the graceful budget layer has zero margin | new in T309 |
| **F8** | — | **UPHELD** — the budget claim survives re-measurement | — |

---

# Evidence in this review

All under `.softhouse/reviews/T302/a2/`. Every harness writes only to `$TMPDIR`, runs
`--dry-run`, reads the live repo read-only, and **never** touches `.softhouse/LOCK`,
`tasks.json`, `RESUME.md`, `conformance.sh` or `fire-program.sh`. **No signal was sent to
any process, and no process this reviewer did not start was ever signalled.**

| path | what it is |
|---|---|
| `cmp-lockset.py` | F5 — in_progress set at a lock commit vs a later commit |
| `drive-f5.sh` / `out-f5.txt` | F5 — the real 140001 timeline and the live workers' commit dates |
| `drive-f5-cell.zsh` / `out-f5-cell.txt` | F5 — T309's own cell shape with the clock advanced: **7 live workers demoted** |
| `drive-f6-grep.zsh` / `out-f6-grep.txt` | F6 — anchor poisoning by a body quote and by subject reuse |
| `drive-f7-nolock.zsh` / `out-f7-nolock.txt` | F7 — no LOCK → `wrapper` → 8 demotions, and the absent liveness check |
| `drive-f8-cost.zsh` / `out-f8-cost.txt` | F8 — end-to-end cost at N = 0,4,8,16,32,40,64 |
| `drive-f8b-realgit.zsh` / `out-f8b-realgit.txt` | F8 — per-call calibration on the real repo's 583 refs |
| `drive-f9-realcorpses.zsh` / `out-f9-realcorpses.txt` | F9 — 528 real refs, real corpse blob, both modes, ground truth |
| `drive-f10-liveskew.sh` / `out-f10-liveskew.txt` | F10 — the live LOCK has no `fire`; version skew |
| `drive-f11-probe-live.sh` / `out-f11-probe-live.txt` | F11 — today's `claude` process table and cwds |
| `out-conformance.txt` | the bar: exit 0, probe present then `up`, 46/0, 7884 cells |

Attempt 1's evidence (`REVIEW.md`, `drive-branch-wip.sh`, `drive-phantom-rescue.sh`,
`drive-probe.sh`, `out/1..3`) is on the same branch and still stands.
