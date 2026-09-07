# The five "stranded" commits: ONE was republished, THREE were pushed intact, ONE is lost

**Fire `cloud-20260906-2000` (cloud, 20:00 Asia/Ulaanbaatar, reference oracle UNREACHABLE).**
This file is the audit trail for the `tasks.json` reconciliation done that fire. It is an
**incident record**, not a claim about current state: every commit id below that is marked
*dead* has been measured non-existent, and nothing in this program should treat a dead id here
as a landing.

## What the record said, and what origin actually holds

For four fires `ready-tasks.py` exited 5 with up to 21 unbacked claims, and `RESUME.md` carried
the headline *"five money-core commits exist on exactly one laptop; only Buyan can fix this."*
That headline was **half right, and the wrong half was load-bearing** — it sent three independent
reviews to `parked` under `branch_unpushed` and kept the critical path unreviewable.

Measured in a fresh clone at `origin/main = 3644eab3`:

| Task | Recorded claim | Claimed sha | Reality on origin |
|---|---|---|---|
| **T509** | `done`, branch `softhouse/T509-ledgerguard-blindspot` | `857dd4d8` — **dead** | **REPUBLISHED as `23966a65`**, ancestor of `origin/main` |
| **T508** | `done` | `1abd3a11` — **ALIVE** | **PUSHED INTACT**, ancestor of `origin/main`; handoff tracked |
| **T515** | `done` | `84dc208e` — **ALIVE** | **PUSHED INTACT**, ancestor of `origin/main`; handoff tracked |
| **T510** | `needs_retry` | `5c4233fc` — **ALIVE** | **PUSHED INTACT**, ancestor of `origin/main`; handoff tracked |
| **T512** | `needs_conditions` | `8ff5ff15` — **dead** | **NOTHING. UNRECOVERED.** |

**ERRATUM — THIS TABLE'S FIRST VERSION WAS WRONG, AND WRONG THE SAME WAY THE THING IT DOCUMENTS WAS
WRONG.** Its first version said *"four of the five were republished under new hashes"* and marked
`1abd3a11` and `84dc208e` **dead**. They are not dead. `git cat-file -t` succeeds on both and
`git merge-base --is-ancestor <sha> origin/main` returns TRUE for both. The driver had carried
"dead" over from the stale `RESUME.md` **without measuring it** — inside the very document written
to correct claims carried without measurement. Corrected the same fire, on measurement.

**The true shape is: ONE republished under a new hash (T509), THREE pushed intact (T508, T515,
T510), ONE genuinely lost (T512).** The Mac evidently re-created the work as
fresh commits (T509's landing is authored `SoftFactory`, 2026-09-04 11:00:10 +0800) instead of
pushing the original branches, so the original shas and branch pointers died with the rewrite while
the *substance* travelled. `git rev-parse` cannot tell that apart from work that never existed —
the same blindness `check-branch-published.py` was built for, arriving from the other direction.

Substance verified rather than assumed, for T509: `balanceSynonymRe` is present at
`origin/main:.softhouse/guards/ledgerguard/main.go:199` as `regexp.MustCompile("(?i)outstanding")`
and is wired into the predicate at `:341`.

## The one real loss

**T512's deliverable does not exist.** Where I looked, stated so the search is gradeable:

1. `git cat-file -t 8ff5ff15` → `Not a valid object name`
2. `git ls-remote --heads origin refs/heads/softhouse/T512-*` → nothing
3. `git log --all --oneline --diff-filter=A -- '*scope-check*'` across all **3070** reachable
   commits → **empty**; neither `.softhouse/bin/scope-check.sh` nor `scope-check-demo.sh` was ever
   added on any ref
4. `find . -name '*scope-check*'` in the working tree → nothing
5. `git ls-tree -r origin/main -- .softhouse/handoff` → no T512 handoff

The only surviving trace of T512 is **other tasks' prose about it** (T517's rejection, `RESUME.md`,
fire commit subjects) — which is exactly the second-hand dependence this pipeline forbids grading
on. It is reclassified `needs_retry`, and a redo must re-derive the instrument from **P-41**, not
from T512's description of it.

**Consequence, still live:** the two-dot `git diff main..<branch>` scope form that P-41 recorded as
wrong is *still prescribed* by `softhouse/SKILL.md` STEP 5, because the executable meant to replace
it never landed. And T517's REJECTION of T512 cannot be actioned against a diff nobody can read.

## Verbatim prior notes, preserved

Retained here rather than in `tasks.json` for the reason given in the next section.

- **T509** — *"landed 857dd4d8 on softhouse/T509-ledgerguard-blindspot (merge base 10baca08). THE
  CRITICAL PATH IS CLEARED. DRIVER-VERIFIED BY EXECUTION, not by reading the report: ran
  check-ledger-invariants.sh in a detached worktree at the branch — Findings: 42, class breakdown
  26 I3-FIELD-WRITE / 8 I3-SQL-BALANCE / 6 I3-COMPOSITE-BALANCE / 1 I3-SQL-BALANCE-TABLE / 1
  OPAQUE-SQL…"*
- **T512** — *"landed 8ff5ff15 on softhouse/T512-scope-instrument. DRIVER-VERIFIED scope with the
  merge-base form: 5 files, all inside files_hint… Shipped TWO executables
  (.softhouse/bin/scope-check.sh + scope-check-demo.sh) rather than a prose warning… Census: 6
  prescription sites fixed, 4 checked-and-clean stated explicitly."*

Both sha claims above are **dead**. They are quoted as history, not asserted.

## A guard finding this reconciliation produced about itself

`check-branch-published.py` scans task `note` text for branch- and commit-shaped strings and reads
each as a **claim**. It cannot distinguish *"the record asserts X landed"* from *"the record
documents that the claim X landed was FALSE."* When the reconciliation first kept the prior notes
verbatim inside `tasks.json`, the refutation itself re-tripped the guard — 3 residual unbacked
claims, all of them sentences whose plain meaning is *this sha does not exist*.

Two ways out, and only one is legitimate:

- **Rewording the note until the scanner stops matching** is the F-1 laundering move T536/T537 are
  arguing about, applied by the driver to its own record. Rejected.
- **Putting the historical prose in an incident document** — this file — and leaving `tasks.json`
  carrying only present-tense truth. A historical record is not a claim about current state, and
  `tasks.json` is the machine-readable record the guard is entitled to read literally.

The second is what was done. **The guard defect is real and stands**, filed as **T554**: a
reconciliation that must state what was false has no way to say so in the record the guard reads.

**T537 later settled this from the other side and the two are ONE defect.** Reviewing T536, it drove
the laundering direction and found a note reading *"the claim that this landed X is WITHDRAWN and
FALSE"* **waives** the branch — 23 compiled regex patterns, zero containing a negation token, so
polarity has no place in the model by construction. T554 is re-scoped to depend on T537's F-1 repair,
on the reviewer's warning that a polarity patch shipped alone closes 2 of its 8 laundering cases and
would be reported as the class being closed.

---

# PART TWO — merging T536 turned CLEAN back into REFUSE(13), and what the 13 actually were

T536 tightened the classifier: a landing sha now proves only the branch(es) a task names in a
**branch field**, not any branch mentioned anywhere (T536/F-2). Merging it took STEP 0 from CLEAN to
**REFUSE — 13 claims**, which is exactly the nine lost waivers T537's F-3 measured (77 → 68) plus
this fire's own four. **None of the 13 was missing work.** Classified by measurement:

**CLASS A — the branch field named a ref pruned after merge, while the landing sha IS an ancestor of
`origin/main` (7 records).** `T353` `539a7201` · `T357` `85a30a79` · `T358` `aac9e12b` · `T361`
`b4bf2abf` · `T375` `2c1f5723` · `T476` `36e01f25` · `T477` `a6bf50a3`. Every one verified with
`git merge-base --is-ancestor`, and for T476/T477 the commit subject names the task. Repaired by
clearing the dead pointer and recording `landed_commit` — the pointer was stale, the work was not.

**CLASS B — the note MENTIONED a token the guard scored as this task's own landing claim (6
records).** `T476`/`T477` referenced the branch of the task they repair; `T312` named two shadow-group
commits *whose entire finding is that they are hidden and diverged*; `T335` named a WIP sha it
explicitly records as never dispatched; `T510` and this fire's own reconciliation notes named shas
they were declaring dead. The guard has no notion of **whose** branch a token names, nor of
**polarity** — a reference, a refutation and an assertion all score identically.

**Class B is T554 and T537/F-1, now measured at scale: 6 of 13 refusals were text about work, not
claims of work.** That is the strongest single piece of evidence either task has.

After reconciliation `ready-tasks.py` **exits 0, `check-branch-published: CLEAN`** — and this CLEAN
is worth more than the earlier one, because it holds under the *tightened* classifier.

## The two parks that were wrong, and wrong on a measurement nobody took

**T520 and T522 were unparked this fire.** Both were parked by fire `cloud-20260904-1200` as
`branch_unpushed`, on the stated ground that their subjects — T508 at `1abd3a11` and T515 at
`84dc208e` — *"exist on exactly one machine and were never pushed."* Both shas resolve, and both are
ancestors of `origin/main`. **The subjects were on origin the whole time.** The park was inherited
across three fires and re-asserted each time without being re-measured — including once by this fire,
before it checked. Two independent reviews of money-core work (the journal-entry INSERT schema, and
the savings classification rework) sat blocked on a fact nobody tested.

---

# APPENDIX — prior note wording, preserved verbatim

Moved out of `tasks.json` because it names branches and shas that `check-branch-published.py` scores
as fresh landing claims. Nothing here is an assertion that any of it landed.


### T312

> DONE, MERGED f327c8df. Reproduced the driver observation numbers from a DIFFERENT instrument - exactly 2 shadow groups, T297 hiding c1a3888a (4 commits) and T305 hiding 060f00330 (8), both diverged. Built branch_sweep.py reading loose and packed values SEPARATELY and never merged. The refusal is a git reference-transaction hook that aborts the ref CREATION - git branch, update-ref, worktree add -b and push each driven and each aborted - which answers P-45 rather than citing it. Demonstrated the

### T335

> NOT DISPATCHED in fire 20260828-140005 -- the fire spent itself on the four finished-but-unreviewed coder branches the killed 08:00 fire left behind, and on what those reviews found. Status is accurate: this task has WIP or is unstarted, and no worker is running. | worker killed mid-flight by fire 20260828-080001 -- OBSERVED: this wrapper stopped its own driver and is reconciling its own dispatches. -- the fire ended while this task was still in_progress, and a killed worker is dead, not paused

### T375

> worker killed mid-flight by fire 20260828-140005 -- OBSERVED: this wrapper stopped its own driver and is reconciling its own dispatches. -- the fire ended while this task was still in_progress, and a killed worker is dead, not paused (softhouse-program STEP 5.5, 'NEVER exit with live workers', item 4). Its branch softhouse/T375-t364-conditions has 8 commit(s) ahead of main, head 2422adc96. Uncommitted WIP left in its worktree was swept onto softhouse/rescued-agent-ac5a2db446e903ba0-20260828-140005 by this fire's worktree sweep. Completeness UNVERIFIED: no handoff was signed off and no reviewer

### T476

> local fire 20260829-080002 iter6: DISPATCHED at 2026-08-29T10:30:01Z as the T467 repair pass under T472's MAJOR. T467 held UNMERGED deliberately -- the driver does not merge a known guard regression. Branched from softhouse-T467-t464-conditions. || local fire 20260829-080002 iter6: DONE on softhouse-T476-t472-repair (tip 36e01f25, branched from T467 6a345e4a, carries T467 work plus the repair). REPAIR CHOSEN: UNION AND WIDEN, union FIRST, and the ORDER IS THE ARGUMENT -- it did not pick between

### T477

> local fire 20260829-080002 iter6: DISPATCHED at 2026-08-29T10:39:20Z as the T466 repair pass under T473's three MAJORs. T466 held UNMERGED deliberately -- the driver does not merge a change that opens a new forgery route while closing three. Branched from softhouse-T466-skipwt-smudge. || local fire 20260829-080002 iter6: DONE on softhouse-T477-t473-repair (6 commits on top of T466 11afb281, tip a6bf50a3). M-2 RE-DERIVED AND FOUND WORSE THAN T473 COULD SHOW: T473 shim was GLOBAL so its bar died a


---

## POSTSCRIPT — the class-B defect caught the driver a THIRD time, at the exit gate

After the fire had written its final `RESUME.md`, released its lock and pushed, the closing
`ready-tasks.py` came back **exit 5, 2 claims**. Both were **T523's own stale note** — the text
written when it was *parked*, which said *"this review's subject is T509 at commit `857dd4d8` on
branch `softhouse/T509-ledgerguard-blindspot`"*. The task was `done` and merged; the sentence was
history; the guard scored it as a fresh landing claim.

That is three times in one fire, in the driver's own record:

1. the first reconciliation pass (8 → 3, all three residuals refutations),
2. the 13 post-T536 refusals (6 of 13 class B),
3. this one — **a note nobody had reason to re-read, on a task whose status had already changed.**

The third is the most instructive, because it is the one no amount of care at writing time would
have caught: the sentence was *true and appropriate* when written, and became a false-positive
purely because the task's status moved on around it. Any repair that depends on authors phrasing
notes carefully is therefore already known to be insufficient — which is the argument for T556's
condition 1 (**proof from structured evidence, never prose**) in its strongest form.

Fixed by rewriting T523's note to record its outcome and pointing the stale subject reference here.
`ready-tasks.py` then exits **0**, `check-branch-published: CLEAN`.
