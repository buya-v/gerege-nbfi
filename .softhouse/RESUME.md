<!-- T288-WRAPPER-BANNER — written by fire-program.sh, not by a driver -->
> ## STALE — this manifest was NOT rewritten by fire `20260827-140002`, which ended 2026-08-27T06:00:25Z.
>
> Everything below predates that fire, so its task table, its "next action" and its
> pause reason are all claims about a world that has moved. The driver did not reach
> STEP 5.5, which is why a shell script is writing this.
>
> - driver outcome: rc=`1` — **QUOTA: THIS FIRE NEVER GOT A TURN** — 0 model turns, rate limit 'seven_day' rejected (resetsAt=1787835600). This is NOT a driver crash and nothing in the repo advanced; the window was spent on nothing.
> - tasks.json reconcile: ran clean (see the reconcile| lines in /Users/buv/Library/Logs/gerege-nbfi/fire-20260827-140002.log)
> - a task shown below as `in_progress` is a DEAD dispatch unless the reconcile line
>   above says it was refused; read `tasks.json` notes, not this table.
> - fire log: `/Users/buv/Library/Logs/gerege-nbfi/fire-20260827-140002.log`
>
> This banner is not maintained by anyone. It disappears when a driver rewrites
> RESUME.md per STEP 5.5.4, and it comes back on any fire that fails to.
<!-- /T288-WRAPPER-BANNER -->
























# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260823-140001` — 8 WORKERS DISPATCHED, RECORD PUSHED BEFORE THE FIRST SPAWN

> **P-85 compliance:** this manifest, the lock and the `in_progress` rows in `tasks.json` were
> committed and **pushed before any worker was spawned**. If you are reading this and no fire is
> running, these eight are **corpses, not workers**. Check each branch
> (`git log --oneline main..<branch>`) and demote anything empty to `needs_retry`.

---

## WHAT THIS FIRE FOUND BEFORE IT DISPATCHED ANYTHING

### The previous fire's 8 dispatches were ALL dead, and the reconciler that exists to say so never ran

Fire `20260823-080004` session 2 dispatched 8 workers and was **SIGTERMed at 12:06:13**
(`~/Library/Logs/gerege-nbfi/fire-20260823-080004.log`: *"driver stopped on SIGTERM; no survivors"*).
This fire opened on a `tasks.json` claiming all 8 still `in_progress`. Measured, not assumed:

| Branch state | Count | Tasks |
|---|---|---|
| Branch exists at dispatch commit `a58604b4f`, **0 commits ahead of main** | 4 | T297, T299, T304, T308 |
| Branch **never created at all** | 4 | T298, T302, T305, T306 |

**Zero WIP survived.** `ps` confirmed no survivors from that fire's process tree.

### THE ROOT, LOCATED — filed as T309 and dispatched this fire

`fire-program.sh` calls `reconcile_tasks_json()` at **line 1032, in the script's NORMAL tail**.
`on_signal()` at **line 426** calls `release_lock` and then `exit $rc` **directly**. So SIGTERM / INT /
HUP release the lock and terminate **without ever reaching the reconciler**.

**T288 wired its repair exclusively to the path that does not need it.** A driver that exits cleanly
already runs its own STEP 5.5 exit protocol and leaves `tasks.json` truthful. The killed driver — the
only case where the wrapper is the last honest witness — is the case the reconciler never sees. This is
the sixth entry in the P-45 lineage (*"a guard that only works when someone remembers to run it enforces
nothing"*), in a new costume: **not unrun, but wired to the wrong path.**

**T302 PREDICTED THIS BEFORE THE MEASUREMENT EXISTED.** Its title, written last fire: *"the
reconciliation has never been driven against a REAL killed claude worker, and it is fail-closed in the
direction that makes it inert."* It is dispatched again this fire with the confirmation in hand.

### A second, independent defect — the supported tool could not be used

`ready-tasks.py`'s `caller_is_lock_holder()` (~`:225-245`) refuses any ancestry containing `claude`,
reasoning *"a driver or worker must not reconcile its own siblings"*. **Sound for live siblings, wrong
for corpses:** the guard has no notion of **fire identity**, so it cannot tell the `140001` driver
clearing `080004`'s dead dispatches from a live driver demoting its own running workers. The driver
therefore open-coded the demotion — exactly the hand-repair the tool exists to replace. Also T309's job.

### BAR at dispatch — run by the driver on the merged tree, exit read WITHOUT a pipe

```
bash .softhouse/conformance.sh  ->  REAL_EXIT=0   (captured via $? on an unpiped run)
                                    probe line PRESENT at :103, reads `up`
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
                                    all 9 wrong ledger implementations DIED through the harness
```

---

## IN-FLIGHT — 8 dispatched, all `isolation: worktree`, all `opus`

| Task | Role | Branch | Ownership / what it must not do |
|---|---|---|---|
| T305 | test_writer | `softhouse/T305-openingbalance-accepting-side` | **Owns `.softhouse/conformance.sh` this batch.** Accepting-side capture on a fresh tenant. Any oracle mutation is refuse-before-write. |
| T306 | reviewer | `softhouse/T306-adjudicate-admit-widening` | **Sole owner of `admit.go`.** Adjudicates the driver's own unreviewed merge-time widening. |
| T309 | coder | `softhouse/T309-sigterm-reconcile-bypass` | **Owns `.softhouse/bin/fire-program.sh` + `ready-tasks.py` this batch.** Must bound any SIGTERM-path work inside launchd's ~20s grace. |
| T302 | reviewer | `softhouse/T302-review-t288` | Reviews T288. **READ-ONLY on `fire-program.sh` — T309 holds the write.** Must find what ELSE T288 got wrong; the SIGTERM bypass is already assigned. |
| T297 | reviewer | `softhouse/T297-review-t295` | Must not fire a T287 probe. Verifies from the live oracle that nothing was posted. |
| T308 | reviewer | `softhouse/T308-review-t292` | Fifth link in the R-VPA lineage — must attack by construction, not by reading. |
| T298 | reviewer | `softhouse/T298-review-t256` | — |
| T304 | coder | `softhouse/T304-evidence-destruction` | Must derive its own population; 4 is T284's count, not a verified total. |

**HELD BACK DELIBERATELY, on file collision — dispatch in batch 2, not forgotten:**
- **T303** (wire T284's registry guard) — `.softhouse/conformance.sh` collides with T305.
- **T301** (wrapper self-modification snapshot) — `.softhouse/bin/fire-program.sh` collides with T309.
- **T299** (T256's two flagged defects, sonnet) — deferred to keep batch 1 at 8.

**Blocked:** T307 (needs T306), T269 (needs T268), T278 (needs T277), T280 (needs T279).
