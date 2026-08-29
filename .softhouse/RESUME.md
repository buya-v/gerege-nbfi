# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260829-080002` **ITERATION 5** (local, Buyan's Mac) — **FIVE WORKERS DISPATCHED.**
Written and pushed BEFORE the first `git worktree add`, per softhouse-program STEP 0.

Oracle **REACHABLE** for this whole fire: `https://localhost:8443/fineract-provider/actuator/health`,
PostgreSQL at `localhost:5432`, pinned Fineract `/Users/buv/fineract @ 426a23544`.

## BAR ON `main` AT DISPATCH — GREEN, measured on the tree that actually landed

```
bash .softhouse/conformance.sh   →  EXIT 0
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value
VERDICT: PASS — 46 parity vectors match the pinned reference oracle, 7884 cells compared
dead-path frontier GREEN, deadOccurrences 108 · frontier 11 == pinned 11
```

Graded at `main` = `2a1dac46`, which is the tree iteration 4 pushed. This is T412's own complaint
applied to this iteration: the bar was run on the commit that IS on `main`, not on a scratch tree.

## ⚠ WHAT THIS ITERATION FOUND IN THE INHERITED RECORD, BEFORE IT DISPATCHED ANYTHING

`tasks.json` carried **two tasks whose work is merged on `main`** in non-terminal states, and one of
them in the dangerous direction:

| Task | Record said | Truth on `main` |
|---|---|---|
| `T428` | `needs_retry` — *"worker killed mid-flight … a killed worker is dead, not paused"* | **MERGED.** `git merge-base --is-ancestor softhouse/T428-review-t421 main` → **YES**; 35 tracked files under `.softhouse/reviews/t428-review-t421/`. The worker **finished**. |
| `T421` | `needs_review` | **MERGED.** 33 tracked files under `.softhouse/capture/t421-t406-conditions/`, and its review (`T428`) landed too. Branch deleted post-merge. |

`T428` is **`T403` observed in the opposite direction** — the reconciler "cannot tell a killed worker
from a worker that never existed", and here it wrote the *killed* story for a worker that **finished and
merged**. `T421` is the **`T350`** shape: the reconciler keys on a branch that no longer exists rather
than on whether the content is on `main`. Both records are corrected in this commit, and both tasks are
dispatched this wave with this as first-hand evidence.

**Iteration 4's own summary was right and the machine-readable record was wrong.** The prose cursor in
`program.json` said "T421+T428 merged"; `ready-tasks.py` offered neither. Prose and record disagreed and
only the prose was true.

## IN FLIGHT — FIVE WORKERS (all `opus`, all worktree-isolated, file sets disjoint)

| Task | Branch | What it is |
|---|---|---|
| `T445` | `softhouse/T445-case-route` | **MAJOR, LIVE ON `main`.** M-1 from T444: a **fifth** witness-forgery route survives all three of T431's new lines — the closing grep reads the **filesystem**, and T375's own argument was never applied to the deciding test. Sole writer to `conformance.sh` this wave. |
| `T442` | `softhouse/T442-t440-conditions` | **MAJOR, CONFIRMED.** C-T440-1: T424's comment-claims drive **fails on the tree it ships in**, and its committed transcript records the opposite. Plus T440's five remaining conditions. |
| `T433` | `softhouse/T433-t423-c1` | **MAJOR, CONFIRMED.** C-T423-1: T393 ships a **false impossibility claim** in two tracked executable files, and sends the next task to build an artefact it does not need. |
| `T350` | `softhouse/T350-reconcile-content` | The reconciler's refusal-to-demote is keyed on a branch **NAME**, not its **CONTENT**. Raised again, first-hand, by this iteration's `T421` finding. |
| `T412` | `softhouse/T412-driver-selfgrading` | The driver pushes to `main` without ever running the bar on its own commits — and reddened `main` doing it. Filed by a driver against itself. |

**Disjointness checked before dispatch:** `conformance.sh` has exactly one writer (`T445`);
`bin/ready-tasks.py` has exactly one writer (`T350`); `T442`, `T433`, `T412` write only their own
capture/review directories. No serialising dependency was needed.

## NEXT WAVE (reviewers, one per branch, independent, re-deriving)
`T446`→T445, `T447`→T442, `T448`→T433, `T449`→T350, `T450`→T412.

## QUEUE AFTER THAT
`T403` (the reconciler's other half — held out only because `T350` owns `ready-tasks.py` this wave) →
`T443` + `T441` (both write `conformance.sh`, serialised behind `T445`) → `T419` → `T437` → `T434`,
`T435`, `T436` → `T399`, `T425`, `T394`, `T395`.

## OPEN GATES — none blocks anything, and no CONTRACT gate is open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`, `G-22`. `ready-tasks.py` reports
`OPEN CONTRACT GATES … NONE open. Every gate id in program.json.gates_pending was inspected.`

## Pause reason
None yet — this manifest is the pre-dispatch record, not an exit record. If you are reading it because
the fire died, the five tasks above were **in flight and are now dead**; check each branch for commits
(`git rev-list --count main..<branch>`) and mark each `needs_retry` with what it actually carried.
**A branch that exists is not evidence of work — that is the `T350` defect this very wave is fixing.**
