# The dead-path frontier pin encodes HOST STATE, and wiring it HARD would have made the bar's colour depend on whether an untracked directory exists

**Found by** the driver of fire `20260827-230001`, by running the bar itself on the merged tree instead of
accepting the worker's transcript. **T323's merge was ABORTED; `main` was not left red.**

## What happened

`T323` wired three guards HARD into `run_guards`, purely additively (2,896 insertions, 0 deletions), and
reported a green bar plus a 12/12 red drive in its own worktree. The driver merged it **locally, without
committing**, and ran `bash .softhouse/conformance.sh`:

```
EXIT=2   wall=43s
probe-line count: 0            ← P-84: read the ABSENCE, not the value
T316-DEADPATH-FRONTIER: REFUSED rows=78 pinned=98 added=4 removed=24
conformance: guard_dead_path_frontier FAILED.
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

**Exit 2 with no probe line printed is a failed HARD guard, not an oracle outage** (P-84). The oracle was up
throughout; it was simply never reached, because `run_guards` precedes the probe.

`T323` had anticipated the **`added=4`** — those are `T305`'s red-drive paths, and it carried them in a
delta list with an anti-amnesty arm. **It did not anticipate `removed=24`.**

## The measurement

| question | answer |
|---|---|
| Does `.softhouse/toolchain` exist in the main checkout? | **YES** |
| How many of its files are **tracked**? | **0** — `git ls-files .softhouse/toolchain` is empty |
| Did it exist in `T323`'s worker worktree? | **NO** |
| How many of the 24 disappeared rows name it? | **23 of 24** |

**So the same commit yields a different frontier on two machines**, and the difference is whether an
**untracked** directory has been materialised. `T316`'s pin of 98 was taken on a tree without the toolchain
unpacked; the driver's checkout has it, so 23 formerly-dead paths now resolve and the guard — correctly —
refuses.

## Why this is a rejection and not a pin refresh

**Wiring it HARD makes the bar's verdict a function of host state.** This program is driven by **two fires**
— a launchd fire on Buyan's Mac and a **cloud fire that never runs on that host** — and `T256`/`T298` spent
themselves establishing that no graded path may depend on where it runs. The repo already has
`guard_no_host_state_in_lint_corpus` for exactly this class. **A new guard that is itself host-dependent, wired
HARD, would make the two fires disagree about whether the corpus passes** — and the failure would present as
`exit 2, no probe line`, which the driver is trained to read as *"a money non-negotiable was violated."*

That is the worst available failure mode: **a host-state defect wearing the costume of a float violation.**

The guard is **not** wrong to refuse. It is doing precisely what `T316` built it to do, and it caught a
defect in its own pin on its first contact with a different machine. **The pin is the defect, not the guard.**

## What was done

- **`git merge --abort`.** `main` stays green at `b50c6828`. A red bar on `main` blocks every subsequent
  fire, and this one would have been red **only on hosts without an unpacked toolchain** — or green only on
  them, depending which way you look, which is the whole problem.
- `T323`'s branch is intact and pinned at `refs/rescue/20260827-230001/t323-wiring-branch`, pushed. **Nothing
  is lost**; 2,896 insertions of wiring, red-drive and census evidence survive for the retry.
- Filed as **`T326`**.

## What `T323` got right, and should not be re-done

- The root measurement moved: `grep -c 'fire-program\|ready-tasks\|reconcile\|in_progress' conformance.sh`
  **0 → 23**.
- **The reconciler guard ran and worked**, in both legs: `reconciler ownership: GREEN 13/13 cells correct /
  RED 8/13` — the planted `T309` single-term predicate drives cell B′ RED while the shipped tool keeps it
  GREEN. `--selftest` is not optional and both legs executed.
- Cost measured, not estimated: **15.9 s → 49.4 s**, of which the reconciler guard is **30.3 s** — more than
  everything else combined. Kept on `T319`'s argument rather than on preference.
- It found and repaired a real wiring defect: `T299`'s guard resolves its root from
  `git rev-parse --show-toplevel`, i.e. the **caller's** cwd, so run from the main repo against a worktree it
  reports the wrong tree. Wired naively that reintroduces the `T165`/`T201` divergence.
- **Its own guards caught it twice** and both transcripts are kept: a comment quoting `T305`'s paths verbatim
  added 3 dead-path rows, and the discrimination arm caught it over-pinning its own red drive's five paths.

## And one standing figure it retired

Re-running `T304`'s instruments unmodified: hard sites **223 → 307 (+37.7%) in one day** — and three
instruments newly contributing were **last touched before `T304`'s census with unchanged bytes**. `T304`'s
resolver calls a target tracked if it *"is a directory prefix of at least one tracked path"*, so
classification depends on the **whole corpus** and rows move for reasons no diff contains.

**`T304`'s 223-site classification is already stale by 84 rows.** Anyone citing it as a standing fact is
citing a number that moves on its own. That is also why `T323` declined to wire the `T304` census: a frontier
pin is only reviewable when a moved row is attributable to the diff that moved it.

## The rule this yields

**A derived pin must be derived from TRACKED content only.** If regenerating it on a different machine — or
in a worktree, or on a fresh clone — yields a different set, it is not a pin, it is a snapshot of somebody's
disk. Wire such a thing HARD and the bar stops being a property of the commit.

**And the driver's own lesson: run the bar yourself before merging anything that edits `conformance.sh`.**
The worker's transcript was honest and its bar was genuinely green — *in a worktree without an unpacked
toolchain*. Neither the worker nor its red drive could have seen this, because both ran on the same machine
in the same condition. **A green bar is a claim about the tree AND the host it ran on**, and only a second
host distinguishes them.
