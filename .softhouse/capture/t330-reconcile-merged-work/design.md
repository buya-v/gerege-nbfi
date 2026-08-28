# T330 — the verdict table, and the argued `merged` action

## The defect in one line

`git rev-parse --verify <branch>` answers **rc=1, empty** in four different worlds, and
`_branch_wip_core` inferred one of them. `red.txt` shows all four arms producing
`rc=1 out=''` — byte-identical — and the pre-T330 code returning `absent` for all four
and demoting all four.

## Why "improve the message" was already tried and already failed

T319's F1 had **already** replaced the flattering assertion with the correct caveat:

> *"THIS IS NOT EVIDENCE THAT NOTHING WAS DONE: a branch that was MERGED INTO main AND
> THEN PRUNED — this repo's stated habit — looks exactly the same from here…"*

T312 had **already** added a `/CASE-VARIANT` suffix for arm (d). `red.txt` arm (d) prints
`VERDICT: absent/CASE-VARIANT` — **both** warnings fired, correctly, and the task was
demoted anyway.

**A caveat is not a control.** This is `P-45` — *"**P-45 — A test-only guard is not a
guard.**"* [VERIFIED: `.softhouse/patterns.md:1472`] — one turn further out. P-45's shape
is *a guard nobody remembers to run*. This one is *a guard that runs every time, is
printed every time, and discharges its duty by narrating the doubt to a human*. On the
signal path there is no human: `on_signal` is racing launchd's ~20 s SIGTERM→SIGKILL
grace and its only reader is a log file, which is the exact failure the reconcile
function's own header already records ("*two fires in a row proved that a correct warning
printed to the log changes nothing at all*").

So the fix is not prose. It is **an action attached to the verdict**, in one place:
`reconcile_action(kind)`.

## The verdict table

`_absent_verdict(branch, tid)` — reached only when `rev-parse` says the recorded branch
does not exist.

| verdict | evidence required | action | why |
|---|---|---|---|
| `merged` | ≥1 commit subject on `main` matching `<TID>:` or `Merge <TID>:`, **or** `.softhouse/handoff/*/<TID>.md` tracked on `main` | **REFUSE to demote** | work is on main; `needs_retry` would offer it for re-dispatch |
| `relocated` | ≥1 live ref (loose **or** packed) whose name carries `<TID>` under a different spelling or case | **REFUSE to demote** | the line still exists; re-dispatch would fork it |
| `unstarted` | all signals **ran** and all came back empty | demote → `needs_retry` | the only world the pre-T330 code was right about |
| `indeterminate` | any signal **did not run** — budget exhausted, git absent, ref store unreadable, no task id passed | demote → `needs_retry`, note says UNVERIFIED | fail-closed: an unrun probe may not buy a reprieve |

The brief asked for three. `relocated` is the fourth because arms (c) and (d) are
required to come out right and neither is a *merge*: T302 measured a rename on T299, and
T308's 2026-08-27 case-shadow hid 4 commits on T297 and 8 on T305. Folding them into
`merged` would have made the note lie about *why* it refused.

Order of evaluation is **positives first**: a positive signal is a measurement and
survives a later degradation (see `failclosed.txt` case 7). Only after both positives
miss does an *unavailable* signal downgrade the answer to `indeterminate`.

## THE ARGUED DECISION: what `merged` should DO

Four options were on the table. The reconciler runs **unattended, inside a SIGTERM
handler**, so "a human will notice" is not available to any of them.

### Option 1 — promote to `done` (or `merged`). **REJECTED.**

What the reconciler actually establishes is: *a commit subject or a handoff path bearing
this id is reachable from `main`*. What `done` asserts is: *this dispatch completed, a
reviewer saw it, and the handoff was signed off*. Those are different propositions, and
the gap is not narrow:

- a partial `TID: WIP` commit landing on main looks identical to a completed one;
- a task re-opened for follow-up work under the same id carries the *previous*
  dispatch's merge evidence;
- this function's own note has said **"Completeness UNVERIFIED: no handoff was signed off
  and no reviewer saw this"** since before T330 and that sentence is still true.

`P-22` — *"A guard, a canary, or a control that cannot fail is worse than none — because
it is believed"* [VERIFIED: `.softhouse/patterns.md:442`] — applies to a **fact** the same
way. A `done` written by a signal handler is believed by everything downstream, satisfies
dependency edges (`TERMINAL = {"done", "approved", "merged"}`, `ready-tasks.py:164`), and
is **unfalsifiable afterwards, because a terminal task is never looked at again**.

**The asymmetry is the whole argument.** A wrong demotion costs one duplicated worker and
gets a human who *looks*. A wrong promotion costs a silently dropped task and gets
**nobody, ever**. Under a REFUSE policy a false-positive `merged` costs one human glance;
under a PROMOTE policy it costs the work. So the false-positive rate the probes actually
have — 96.3 % of pre-T330 `absent` verdicts on the live file turn out to have reachable
work, but the probes are *subject-prefix matches* and can over-match — is affordable
under refusal and not under promotion.

### Option 2 — a new status, e.g. `needs_adjudication`. **REJECTED.**

`NOT_RUNNABLE` (`ready-tasks.py:165`) is a **closed allow-list**. A status not in it is
**runnable** — so a new vocabulary word that the orchestrator prose, the ready-list and
`resolve()` do not know is a fail-OPEN by default, in the direction of dispatching. That
is the P-77 shape this file has been bitten by twice. Adding the word to *this* file does
not add it to the skill prose or to any human's head.

### Option 3 — `parked`. **REJECTED.**

`parked` is already in `NOT_RUNNABLE` and would work mechanically, but in this program it
means **"blocked on a `user` gate"** and is read out of `.softhouse/gates.md`. Writing it
here would assert a gate that does not exist. A status that means two things is a status
that means neither.

### Option 4 — **REFUSE to demote: leave the status, rewrite the note. CHOSEN.**

`in_progress` is *already* the status whose ready-list line reads **"ALREADY DISPATCHED,
do not dispatch again"**. It is **not** in `TERMINAL`, so no downstream dependency
unblocks on the strength of a signal handler's inference. It is **not** in
`NOT_RUNNABLE`… and does not need to be, because the ready-list filters `in_progress`
into its own bucket before that test. So it already has exactly the two properties
wanted: *not dispatchable* and *not terminal*, with **zero vocabulary invention**.

And the decisive property: **the note is written into `tasks.json`, which is committed.**
The finding survives the fire, in the diff, in the file the next fire actually reads —
rather than in a log nobody opens, which is the failure this function's own header
records. A refusal that changes nothing on disk would be one more caveat.

**The cost, stated rather than glossed:** the file keeps an `in_progress` line with no
live worker, which is the lie `--reconcile` exists to withdraw. Three mitigations, all
implemented:

1. the note says so in as many words — *"`in_progress` here does NOT mean a worker is
   alive — it is not, and this line is a placeholder for an adjudication"*;
2. the run report prints `*** REFUSED TO DEMOTE ***` per task and a `T330 REFUSALS:` roll-up,
   and the `RESULT:` line carries the count;
3. `--list` now prints `RECONCILE WOULD: …` beside every in-progress task, so the driver
   at STEP 0 reads the same verdict the reconciler would act on.

**It is a strictly smaller lie than the alternative**, which was to write `needs_retry` —
a lie *and* an invitation.

**The second cost, also stated:** `in_progress` is not in `TERMINAL`
[VERIFIED: `ready-tasks.py:164`], so `resolve()` reports a refused task's dependency edge
as **unmet** and every downstream task stays `BLOCKED` until a human adjudicates. That is
the fail-closed direction — nothing should be built on work whose completeness is
unestablished — but it is a real cost and it is not hidden: the refusal note ends with
*"WHAT A HUMAN MUST DO: read the history named above and set this task to its true
terminal status by hand"*, the roll-up names every refused id, and `--list` prints the
verdict at STEP 0. The alternative shape — promote so the graph flows — is Option 1,
rejected above. **A blocked successor is recoverable; a silently-dropped predecessor is
not.**

### Idempotence, which the refusal introduces and which is measured

A refused task keeps its status, so the refusal branch runs on **every** subsequent fire.
The pre-existing note writer appends `[prior note: …]` each time — unbounded growth in a
962 KB file. The refusal note therefore carries a marker `[T330-REFUSED-DEMOTION]` and a
note this function already wrote is **replaced, not nested**. Measured over five
consecutive reconciles: **1911 chars, unchanged** (`e2e.txt`).

## Budget

The three signals as the observation phrased them are **per-task git calls**:
`0.2743 s/task` measured → `5.49 s` at N=20, `60.08 s` at N=219, against an inner budget
of ~6 s (`SIGNAL_GRACE_SECS 20 − elapsed − GIT_PUSH_TIMEOUT_SECS 10 − 2`, then
`− RECONCILE_TAIL_RESERVE_SECS 1`), below `SIGNAL_RECONCILE_MIN_SECS` of which the whole
reconcile is **skipped loudly**.

So they are not run per task. They are built **once, as an index**:

| source | call | cost | scales with N? |
|---|---|---|---|
| commit subjects on main | `git log main --format=%H%x09%s` (~1,800 commits) | 0.1196 s | **no** |
| handoff paths on main | `git ls-tree -r --name-only main -- .softhouse/handoff` | 0.0402 s | **no** |
| ref store | `branch_sweep.RefIndex` — `os.walk` + `packed-refs` parse | 0 subprocesses | **no** |
| **total** | | **0.1598 s for any N** | |

`--grep` was **measured and rejected**: one generic `--grep` costs 0.154 s against
0.131 s with no grep, because git walks every commit either way and the regex is pure
overhead.

End-to-end over the worst case (all 140 branched tasks in the live file, not the
convenient `in_progress` = 3): **+0.642 s, +5.5 %** — of which 0.1598 s is the one-time
index, so the *marginal* per-task cost does not grow with N.

**These figures move between runs, and that is the measurement, not noise.** `budget.txt`
was captured three times during this task and the branched-task count went 137 → 137 →
140 and `commits` 8 → 6 → 8 as other workers merged into `main` underneath it. `P-69` —
*"The measured claim went stale between the review and the revision — inside a single
fire"* [VERIFIED: `.softhouse/patterns.md:1881`]. The committed `budget.txt` is the run at
the merged HEAD; re-running it will produce different absolute numbers and the same
shape.

`ls-tree main` is used rather than the `git ls-files` the observation named: same cost
(0.04 s) but it asks **`main`**, whereas `ls-files` answers about the index of whatever
checkout it runs in — and a worker worktree's index is not `main`.

## Fail-closed

The property, stated as a property: **no degradation of any input may produce a
refusal.** `failclosed.txt` drives arm (a) — the one arm whose honest verdict is `merged`
— against seven degradations. Six must demote; the seventh (index built *before* the
budget expired) must still say `merged`, because dropping a cached positive would demote
merged work, i.e. would re-commit FU-RECONCILE-1. **7 of 7 hold, 0 fail-open.**
