# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260829-080002` (local, Buyan's Mac) — **SIX WORKERS DISPATCHED.** Written BEFORE the first `git worktree add`.

Oracle **REACHABLE** for this whole fire: `https://localhost:8443/fineract-provider/actuator/health`,
PostgreSQL at `localhost:5432`, pinned Fineract `/Users/buv/fineract @ 426a23544`.

## BAR ON `main` AT FIRE START — GREEN, measured, not assumed

```
bash .softhouse/conformance.sh   →  EXIT 0
probe line PRESENT (grep -c 'probe = ' == 1), reads `up`     ← presence tested BEFORE value
VERDICT: PASS — 46 parity vectors match the pinned reference oracle, 7884 cells compared
dead-path frontier GREEN, deadOccurrences 108 · frontier 11 == pinned 11
```

## ⚠ WHAT THIS FIRE FOUND IN THE INHERITED RECORD, BEFORE IT DISPATCHED ANYTHING

The previous fire (`20260828-140005`, iteration 4) ended with **nine workers in flight**. All nine died
with the session. The wrapper's reconciler ran, and **it got one of them exactly backwards**:

**`ready-tasks.py` reported `T431` as `WIP: MERGED … The work LANDED. Do NOT read this as an unstarted
task.` `git rev-list --count main..softhouse/T431-t407-conditions` is `0`.** The branch points **at** the
driver's own dispatch commit `280817a1` — which is on `main`, because that is the commit `git worktree add`
branched from. The worker never committed a line. `C-T407-1` (**MAJOR**, the pathspec-magic witness
forgery) is **UNSTARTED**, and the record was telling the next driver the opposite.

This is the first **live** instance of the class `T350` and `T403` are already filed for — the reconciler
keys its refusal-to-demote on a branch **name**, not on whether that branch carries a commit. It is the
**P-45** shape once more: a control that runs and reports, and reports the reverse of the truth. `T350`
and `T403` are both READY and neither is dispatched yet; this fire's evidence raises both.

Six other tasks the record carried as `needs_retry` with a `branch` field (`T417 T419 T422 T424 T429
T266`) have **no branch at all** — `git rev-parse` fails on every one. They were never dispatched. Their
records now say so.

`T423` is the third shape: its branch carries **1 real commit** of instruments and drive output, and
**no `REVIEW.md`** — verified with `git ls-tree -r --name-only`. Evidence real, verdict never written.

## MERGED THIS FIRE

| Merge | What it was |
|---|---|
| `T421` + `T428` | T406's six conditions on the accrual vectors, **and its independent review**. `T428` verdict: `APPROVED WITH CONDITIONS`, four findings, **all LOW, none blocking**. Bar run on the **MERGE RESULT** in a scratch worktree at `/tmp/t429-merge` before `main` was touched. |

## IN FLIGHT — SIX WORKERS

| Task | Branch | What it is |
|---|---|---|
| `T422` | `softhouse/T422-review-t416` | **INDEPENDENT review of T416 — a MONEY-REPORTING fix.** A one-minor-unit ledger mismatch announced to a human as `0 mismatched vector(s)`. Verify the count is now RIGHT, not merely non-zero. |
| `T423` | `softhouse/T423-review-t393` | **RESUME, do not restart.** Its 1 commit of evidence is real; the verdict is what is missing. |
| `T431` | `softhouse/T431-t407-conditions` | **UNSTARTED, MAJOR.** `C-T407-1` — the witness-side lookup at `conformance.sh:3677` is still a pathspec, so `:(literal)` magic spelled as a real tracked directory disables two refusals at once. |
| `T417` | `softhouse/T417-scheduler-attribution` | **G-22, oracle-only work.** The reference oracle edits itself overnight — nineteen active jobs, one caught by luck. Pin the scheduler WITHOUT trusting app user 2. |
| `T429` | `softhouse/T429-oracle-derived-columns` | **G-22(c), a divergence of principle.** The oracle writes running balances onto posted rows; `CLAUDE.md` says balances are DERIVED, NEVER WRITTEN. Declare the oracle-derived columns so the port is not "fixed" into violating the non-negotiable. |
| `T424` | `softhouse/T424-t408-conditions` | T408's conditions on T402 — an attribution wrong in the **shipped source comment**, and a guard correct only by accident of this host's `tee` buffering. |

## COMPLETE, HELD UNMERGED PENDING REVIEW
`T393` (`softhouse/T393-t382-conditions`, 11 commits, its own final bar EXIT 0) — **blocked on `T423`.**
`T416` (`softhouse/T416-t405-conditions`, 10 commits) — **blocked on `T422`.** Money-path; will not merge unreviewed.

## QUEUE FOR THE NEXT FIRE
`T419` (the grep BRE defect, held out of this wave only because three writers to `conformance.sh` is
already two more than merges cleanly) → `T350` + `T403` (both raised by this fire's own T431 finding) →
`T412` (the driver never grades its own commits) → `T399` (needs `T424`) → `T425` (needs `T393`+`T423`) →
`T413`, `T394`, `T395`.

## OPEN GATES — none blocks anything, and no CONTRACT gate is open
`G-4`, `G-5`, `G-8`, `G-10`, `G-12`, `G-19`, `G-20`, `G-21`, `G-22`. `ready-tasks.py` reports
`OPEN CONTRACT GATES … NONE open. Every gate id in program.json.gates_pending was inspected.`
