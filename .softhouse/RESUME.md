# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260829-080002` **ITERATION 5** (local, Buyan's Mac) — IN FLIGHT, 3 PAIRS MERGED, 2 TASKS LIVE

Oracle **REACHABLE** all iteration: `https://localhost:8443/fineract-provider/actuator/health`,
PostgreSQL `localhost:5432`, pinned Fineract `/Users/buv/fineract @ 426a23544`.

## BAR ON `main` — GREEN, and now ATTESTED rather than merely asserted

Every merge this iteration was graded **on the merge result, in a scratch worktree outside the repo,
before `main` was touched**, then attested by tree sha and pushed only after the pushed tree was
confirmed to BE the graded tree. Latest: `EXIT 0`, probe PRESENT ×1 `up`,
`VERDICT: PASS — 46 parity vectors, 7884 cells`, frontier `11 == 11`, `deadOccurrences 108`.

## MERGED THIS ITERATION — THREE REVIEWED PAIRS

| Pair | Verdict | What landed |
|---|---|---|
| `T350` + `T449` | APPROVED WITH CONDITIONS (2 MAJOR) → **`T451`** | The reconciler now refuses to demote on **CONTENT**, not on a branch NAME. T449 ran a **256-state partition enumeration by EXECUTING the predicates**: 0 states with no verdict, 0 with two. |
| `T442` + `T447` | APPROVED WITH CONDITIONS (3 MAJOR) → **`T452`** | C-T440-1 closed: the probe is assembled at runtime, not respelled to evade `git grep`. Class sweep: 1704 scripts / 399 searches, 4 self-matching probes, all fail-CLOSED. |
| `T412` + `T450` | APPROVED WITH CONDITIONS (2 MAJOR) → **`T453`** | The **driver push gate**, installed and enforcing. C1 gitlink refusal, C2 write-path allowlist, C3 tree-identity + cheap subset on the PUSHED tree. |

## ⚠ THE THREE THINGS THE NEXT FIRE MOST NEEDS TO KNOW

**1. `T453` IS URGENT AND MONEY-ADJACENT.** The push gate is **live with a driven hole**. T450 drove
three STATE-set-confined deltas that pass the cheap subset, get a CHEAP attestation written, and are
ALLOWED — and the full bar on that exact tree then goes `EXIT 2` with no probe line. One is
`guard_no_float_in_capture_requests`, a **money non-negotiable**. The reasoning error in one sentence:
*the STATE-set table asks which files each guard READS; three guards resolve against the tree's
INVENTORY, so an ADDITION is the same hazard as the DELETION already excluded.* Nine of the 108 pinned
dead-path literals live inside the STATE set, including `.softhouse/uat.md` — ordinary driver work.

**2. `NOTHING INSTALLS THE GATE` (T453 M-2).** Zero hits repo-wide outside T412's own files. `.git/hooks`
is untracked, so **the cloud fire and any CI runner are silently ungated**. It protects exactly one
machine because one worker ran the installer by hand, once. P-45 for the eighth time.

**3. THE GATE REFUSED THE DRIVER, AND WAS RIGHT.** At the `T350`+`T449` merge the driver had graded the
merge result and verified tree identity by hand — and was still refused, because a transcript is bytes
and nothing binds it to the tree it claims to have graded. The remedy was to attest properly
(`bar-attest.sh` checks the tree out itself), never to bypass. **`bypass.log` still does not exist.**

## IN FLIGHT — TWO WORKERS

| Task | Branch | State |
|---|---|---|
| `T433` | `softhouse/T433-t423-c1` | 3 commits, **no handoff yet.** ARM F landed inside section 10; false impossibility corrected at both executable sites. |
| `T446` | `softhouse/T446-review-t445` | Just dispatched, **no commits yet.** Reviewing T445. |

## HELD, COMPLETE, UNMERGED PENDING REVIEW
`T445` (`softhouse/T445-case-route`, 10 commits, tip `236fc829`, own bar EXIT 0, scope clean, merges
clean onto current `main`) — **blocked on `T446`.** T444 found ONE fail-open; T445 found **four**, three
of them new and all driven RED on **unmutated `main`**: `MCASE` (directories differing only in case),
`LEGDIRTY` and `WDIRTY` (rows/witnesses existing only in the working tree). Remedy: every graded read now
comes from the **tracked blob**. Proposed pattern `FU-T445-8`: *a test that reads the WORKING TREE cannot
decide a question about what is COMMITTED* — six fail-opens in one function have had that shape.

## QUEUE FOR THE NEXT FIRE
`T453` (urgent, money-adjacent) → `T451`, `T452` → `T403` (the reconciler's other half; `T350` held
`ready-tasks.py` this wave) → `T443` + `T441` (both write `conformance.sh`, serialised behind `T445`) →
`T419` → `T437` → `T434`/`T435`/`T436` → `T399`, `T425`, `T394`, `T395`.

## RECORD DEFECTS CORRECTED THIS ITERATION
`T421` (`needs_review`) and `T428` (`needs_retry`, "worker killed mid-flight") were both **merged on
`main`** — 33 and 35 tracked files respectively. `T428` is `T403` in the mirror: the reconciler wrote the
*killed* story for a worker that **finished**. Both corrected before dispatch; both fed to `T350`.

**Also corrected: a DRIVER measurement error.** The scope check must run against the **merge-base**, not
`git diff main..branch`. Once `main` advances under live workers the two-dot diff attributes the
**driver's own later commits** to the branch as deletions — it made all five branches look like they had
clobbered `tasks.json` and deleted a live task. None had.

## OPEN GATES — none blocks anything, no CONTRACT gate open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`, `G-22`.

## NEEDS A HUMAN EVENTUALLY (not a gate, but no agent should guess)
`T286` is **partially landed**: 27 of its files are on `main`, its branch is 2 commits ahead and is
**not** an ancestor. Found by `T350`, confirmed by `T449`. It printed nothing before this iteration.

## Pause reason
None — this is an in-flight checkpoint, not an exit record. If you are reading it because the fire died:
`T433` and `T446` were **live and are now dead**. Check each branch for commits
(`git rev-list --count main..<branch>`) and mark each `needs_retry` with what it actually carried.
`T445` is COMPLETE and unmerged — do not restart it, review it.
