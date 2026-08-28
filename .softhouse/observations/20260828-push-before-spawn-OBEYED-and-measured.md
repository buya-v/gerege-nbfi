# push-before-spawn: obeyed, and measured forward rather than audited backward

**Fire** `20260828-080001`, chain iteration 2, batch 1. **Recorded by the driver, about the driver.**

## Why this file exists

The obligation in STEP 0 of `.claude/skills/softhouse-program/SKILL.md` — *push the LOCK, the machine-readable
dispatch record and the in-flight `RESUME.md` **before** the first `git worktree add` of a batch* — has been
missed **twice, six days apart, by drivers who had read the paragraph**:

| Fire | What was late | By how much |
|---|---|---|
| `20260822-…` | dispatch record | **101 s** after the first worker spawned |
| `20260828-080001` iter 1 | dispatch record **and** in-flight `RESUME.md` (commit `59fc41b4`) | **135 s** after the first `git worktree add` at 10:44:04 |

That is P-45 applied to the rule about P-45: *a guard that only works when someone remembers to run it
enforces nothing.* The paragraph has zero mechanical backing — the `post-checkout` hook that would enforce it
at the exact instant it must hold is **built and not installed**
(`.softhouse/capture/t279-lock-partition/post-checkout`).

## What this iteration did, measured

All three artefacts went out in **one** commit, `fc23ad0b`, pushed to `origin/main` at **11:34:18 +0800**
(epoch `1787888058`): `tasks.json` with all six tasks already `in_progress` and carrying their `branch`, the
in-flight `RESUME.md`, and the refreshed `LOCK`.

Worktree creation times, read from the filesystem birth time of each agent worktree (`stat -f '%B'`), not
from any log the driver wrote about itself:

```
  agent-ac70608b49d46f77a   11:34:58   push +40 s
  agent-adcb0122e4f0d6738   11:35:26   push +68 s
  agent-a2b34ba7fee3c2de6   11:35:47   push +89 s
  agent-a932bd0ee5b1bb219   11:36:05   push +107 s
  agent-aac32d39717605690   11:36:24   push +126 s
  agent-afc904cf109cb64cf   11:36:43   push +145 s
```

**Six of six after the push. Minimum margin +40 s.** [VERIFIED: `git log -1 --format='%H %ct' origin/main`
and `stat -f '%B'` over `git worktree list --porcelain`, run in this session at 11:37.]

## The part that is NOT a success

**This is one compliant batch, not a fixed process.** The two prior misses were also by drivers intending to
comply. Nothing here changes the mechanics: the next driver is still the only thing enforcing the paragraph.
**The measurement is not the guard** — reading a margin of +40 s after the fact is exactly what
`audit-this-fire.py` did on iteration 1, and it discovered the violation instead of preventing it.

The real fix is `T336`, filed this iteration: **install** the hook. It is deliberately gated on `T280`'s
independent review, because a `post-checkout` hook that refuses worktree creation can brick every future fire,
and installing an unreviewed one would be the worse defect. `T280` has been told to measure whether a non-zero
`post-checkout` exit actually aborts `git worktree add` on this host's `/usr/bin/git` at all — if it only
warns, `T336`'s premise changes and the driver expects to hear that rather than an installation.

## Also unclear, and left as a question rather than an assumption

The harness creates each worktree on an auto-generated branch (`worktree-agent-<id>`); the worker switches to
`softhouse/<taskid>-<slug>` itself. So at the instant `git worktree add` runs, **the dispatch record's `branch`
field names a branch that does not yet exist**. A hook checking "is the dispatch record for THIS branch
pushed" would therefore be checking a branch it cannot see. `T336` must resolve what the hook can actually
observe at hook time; this is recorded here so it is not discovered late as a defect.
