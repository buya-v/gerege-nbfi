# The post-fire reconcile demoted a task whose work was already MERGED on main

*Driver measurement, local fire `20260828-080001`. Filed as `FU-RECONCILE-1`; the fix is task `T330`.*

## What happened

The wrapper's post-fire reconcile (`967624ce`, "exit-protocol enforcement") demoted **`T324`** from
`in_progress` to `needs_retry` with this note:

> Its recorded branch `softhouse/T324-worktree-prune-skipbit` **does not exist in this repo.**

The branch did not exist **because it had already been merged and deleted.** T324's work is on `main`:
`a08a64e2` (handoff) and merge commit `d36863ad` — **14 files, 2,338 insertions**, including
`fire-program.sh +218`, three instruments with RED/GREEN drives and a live worktree census, landed with the
bar green.

Had this fire believed its own state file, it would have **re-dispatched a completed task**, and the retry
would have re-derived work already on `main` — or worse, landed a second, divergent implementation of the
same fix in the file that decides whether worktrees get destroyed.

## The reconciler already says the right thing. It takes the wrong ACTION anyway.

This is the interesting half, and it is why the fix is not "improve the message". `ready-tasks.py`'s
`_branch_wip_core` **already** returns exactly the honest text — T319's F1 replaced the flattering assertion
with it [VERIFIED: `.softhouse/bin/ready-tasks.py:836-843`]:

> `"Its recorded branch %s does not exist in this repo. THIS IS NOT EVIDENCE THAT NOTHING WAS DONE: a branch
> that was MERGED and then pruned looks exactly the same from here…"`

So the prose is correct, was deliberately corrected once already, and **changed nothing**, because the code
prints the caveat and then demotes regardless. **A caveat is not a control.** The reconciler is telling a
future reader to go and check something the reconciler is in a strictly better position to check itself, at
the moment it has the repo in hand.

This is the same shape as the program's most-repeated lesson — *a guard that only works when someone
remembers to run it enforces nothing* (recorded five times: `manifest.py verify`, `t44_float_roundtrip_v3`,
T173's float guard, `guard_ledger_invariants`, T257) — one turn further out: **a guard that discharges its
duty by NARRATING the doubt to a human enforces nothing either.**

## The check that was available and not taken

Three mechanical signals distinguish *merged-and-pruned* from *never-started*, all cheap, all local:

| Signal | For T324 | For a genuinely unstarted task |
|---|---|---|
| `git log --oneline main --grep="^Merge <TID>:"` | `d36863ad` | empty |
| `git log --oneline main --grep="^<TID>:"` | `a08a64e2` | empty |
| `git ls-files '.softhouse/handoff/*/<TID>.md'` | present | absent |

**Rule: `absent` must be a THREE-way verdict, not a two-way one** — `merged` / `unstarted` /
`genuinely-indeterminate` — and only the latter two may demote. `merged` should promote to `done` (or at
minimum refuse to demote and say so loudly).

## Population: measured, not assumed

The driver swept **every** task in `tasks.json` not already `done`/`approved` against all three signals.
**Exactly one — `T324` — was demoted while its work sat on `main`.** Ten further tasks (`T271`, `T273`,
`T274`, `T275`, `T283`, `T285`, `T287`, `T289`, `T290`, `T291`) carry merge evidence, and all ten are already
in the terminal `merged` state, so none is a defect. [VERIFIED: driver sweep at `ca89e121`.]

Where the driver looked: `.softhouse/tasks.json`, `git log main --grep`, `git ls-files` over
`.softhouse/handoff/*/`. **"Not found" is a statement about the search** — this sweep does not cover tasks
archived out of `tasks.json` into `.softhouse/runs/*.tasks.json` (P-66's population), and that remains
`[UNVERIFIED]`.

## The generalisation worth keeping

**Branch-absence is not work-absence.** A merged-and-pruned branch, a renamed branch, a case-shadowed branch
(the 2026-08-27 defect T308 caught and T312 closed) and a branch that never existed are **byte-identical from
`git rev-parse`**. Any inference drawn from that one observation is unsound in four directions at once, and
the repair is to ask `main` — the place the work would have landed — rather than to ask the ref that would
have carried it.
