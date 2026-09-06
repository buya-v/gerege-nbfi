# The five "stranded" commits were REPUBLISHED UNDER NEW HASHES — four of five, anyway

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
| **T509** | `done`, branch `softhouse/T509-ledgerguard-blindspot` | `857dd4d8` — **dead** | **PUBLISHED as `23966a65`**, ancestor of `origin/main` |
| **T508** | `done` | `1abd3a11` — **dead** | handoff `T508-journalentry-insert-schema.md` tracked on `origin/main` |
| **T515** | `done` | `84dc208e` — **dead** | handoff `T515-savings-classification-rework.md` tracked on `origin/main` |
| **T510** | `needs_retry`, branch `softhouse/T510-savings-fold-reversal` | `5c4233fc` | **PUBLISHED as `5c4233fc`**, ancestor of `origin/main`; handoff tracked |
| **T512** | `needs_conditions`, branch `softhouse/T512-scope-instrument` | `8ff5ff15` — **dead** | **NOTHING. UNRECOVERED.** |

**Four of the five were republished under new hashes.** The Mac evidently re-created the work as
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
