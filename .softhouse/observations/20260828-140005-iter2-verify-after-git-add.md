# THREE tasks in one fire shipped a branch that reddens the bar, all for the same reason

## The defect, stated once

**A file that is not yet tracked is invisible to `guard_dead_path_frontier`'s census**, because the census
reads `git grep` / `git ls-files` over **tracked** `.softhouse/**/*.sh`. So a task that:

1. writes its own `drive-red.sh` (or evidence script),
2. runs `bash .softhouse/conformance.sh` and records **`exit 0`**,
3. then runs `git add -A` and commits,

records a **[VERIFIED] green bar that was never true of the thing it shipped.** The verification and the
artefact are measured in two different states of the world, and the order is the wrong way round.

## Three instances, this fire, all independent

| Task | Branch | What entered the census | Frontier |
|---|---|---|---|
| `T361` | `softhouse/T361-review-t353` | 12 tracked `.sh`/`.zsh` (frozen `_src-` snapshots + a census instrument) | 112 vs 109 |
| `T369` | `softhouse/T369-review-t351` | 1 tracked `.sh` (`drive-red.sh`) | 111 vs 109 |
| `T370` | `softhouse/T370-t351-retry` | 1 tracked `.sh` (`drive-red.sh`) | 112 vs 109 |

`T370`'s is the cleanest proof because its own handoff contains both numbers: it recorded baseline
`corpus=1315`, and the shipped tree measures `corpus=1316` — **exactly one more tracked
`.softhouse/*.sh`**, its own. [Measured by T376; re-confirmed by the driver.]

`T361`'s cost was real and already paid: the driver merged it, `main` went RED, and the merge was
reverted (`2fa4015b`). `T369`'s and `T370`'s were caught **before** `main` was touched, by building the
merge result in a scratch worktree first.

## The fix that costs nothing

**Run the bar AFTER `git add`, never before.** Every worker prompt should say so, and this one now does:

> Your own new `.sh`/`.zsh`/`.py` files under `.softhouse/` are INVISIBLE to the dead-path census until
> they are TRACKED. `git add -A` FIRST, then run `bash .softhouse/conformance.sh`. A green bar recorded
> before `git add` is not evidence about the branch you are shipping — three tasks in fire
> `20260828-140005` recorded exactly that, and all three branches reddened the bar.

## What this is NOT

It is not a defect in `guard_dead_path_frontier`. The guard is **fail-closed**, it caught all three, and it
named the culprit file and the exact added rows every time. It did its job perfectly. The defect is in
**when tasks measure**, and the guard is the only reason we know.

## Standing work

`T366` is chartered to answer the general question — *how does this repository land review/evidence scripts
at all* — and now has **three** cases to satisfy rather than one. `T373` (lands T369) and `T378` (lands
T370's verified substance) are the per-instance tasks and are told to adopt T366's mechanism rather than
compete with it.
