# OWNER: **T258**. Not T255. This directory's name is wrong and is being kept anyway.

*Filed by **T258** itself, at first commit, because T299's guard refused the bar before this
directory had ever been committed — which is the guard working exactly as designed. The filename
answers the question without being opened, because the reader who needs it arrives here by `ls`
or by `grep t255`.*

---

## 1. The fact

| | |
|---|---|
| **Directory** | `.softhouse/capture/t255-frontier-rot/` |
| **Written by** | **T258** — *"The fail-open frontier COUNT is restated in places that rot, and TIER1B's rederive-provenance.sh is pinned but unrepaired"* |
| **Branch** | `softhouse/T258-frontier-rot-residuals`, forked at `fc23ad0b` |
| **Handoff** | `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T258.md` |
| **T255 is a different task** | *"Prepare AND LAND DEC-2 revision 8 in ONE fire"*, whose rig is `.softhouse/capture/t255-dec2-rev8/` and whose `files_hint` names that directory and `docs/adr/DEC-2-gl-accounting-adapter.md` [VERIFIED: `.softhouse/tasks.json`, T255 row] |

**Nothing in this directory is T255's work, and T255 never touched it.** `t255-dec2-rev8/` was
added by commits `ed686d79` / `b3347860` [VERIFIED: `git log --diff-filter=A -- .softhouse/capture/t255-dec2-rev8/`];
everything here arrived on T258's branch.

## 2. Why the name says `t255`

The same shape this whole task is about, in a different currency: **a task id restated in a second
place, which then rotted when the id moved.**

> *"RENUMBERED T255->T258 on merge: the cloud catch-up fire published a different T255 first.
> Two orchestrators held the lock at once (see P-84)."*
> — [VERIFIED: `.softhouse/tasks.json`, T258's `note`]

and `tasks.json`'s T258 row **still carries `.softhouse/capture/t255-frontier-rot/` in its
`files_hint`** — the dispatch artefact that minted the name is still sitting there. The worker was
dispatched to write into a directory named for an id it no longer has.

This is **P-86** (*an ID IS A CARDINAL; prefer the name over the number*) and it is the exact
mechanism T258 was dispatched to fix for the frontier count. A directory named `t255-` is a task
id restated in a path, and a path is the one restatement that cannot be corrected afterwards
without invalidating everything that cites it.

## 3. Why it was NOT renamed

T299 measured the cost of renaming a *committed* capture directory and recorded it in
`.softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md` §3–§4: 49 tracked files,
182 occurrences, two guards driven red, and a completion that requires editing eight other tasks'
committed evidence in place. That measurement is not re-run here and is not needed here, because
**this directory's situation is strictly weaker and the answer still comes out the same**:

* At the moment of writing, nothing outside it cites it — it is new. A rename would be cheap
  **today** and expensive on every day after, and there is no day on which anyone will re-open
  the question. The convention exists precisely so the decision is not re-litigated per directory.
* **The `files_hint` is the dispatch grant.** `.softhouse/capture/t258-frontier-rot/` is not in
  it. Creating a directory outside the grant to dodge a guard is worse than the misnaming: it
  trades a legible, documented name-vs-id mismatch for a silent scope violation.
* T299's guard states its own remedy in terms — *"THE FIX IS NOT A RENAME… Add
  `OWNER-IS-T<owner>-NOT-T<prefix>.md` inside each directory instead"* — and a worker that
  reaches for a different remedy than the guard names had better have a measurement, not a
  preference. I have none, so I follow the guard.

## 4. How this was found — by the guard, not by me

The bar refused before this directory had ever been committed:

```
namespace:   T255 -> 2 directories; ownership records required 1, present 0
namespace:       UNCLAIMED  capture/t255-dec2-rev8                       (record: <absent>)
namespace:       UNCLAIMED  capture/t255-frontier-rot                    (record: <absent>)
NAMESPACE-CENSUS: dirs=151 prefixed=130 unprefixed=21 collidingIds=2 declared=1 unclaimed=3 shortfallIds=1
namespace: REFUSED -- 1 task id(s) prefix more directories than they can own
conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass.
```

Worth recording plainly: **the collision was created by the dispatch and caught by the harness on
the first graded run of the branch.** No human noticed it and no worker declared it; a guard
written three fires earlier for a different collision refused this one on sight. That is the
argument for mechanism over discipline, observed once more, in the task whose entire subject is
that argument.

## 5. The convention

Unchanged, and quoted rather than restated, from
`.softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md` §5:

> **A capture or review directory is named for its SUBJECT. The task-id prefix is a CONVENIENCE,
> never the directory's identity. Identity lives in an `OWNER*.md` file inside the directory. The
> directory name is FROZEN AT FIRST COMMIT and is never renamed; when an id moves, the OWNER
> RECORD is corrected, because content can be superseded and a path cannot.**

The subject of this directory is **frontier-rot**. That word cannot collide, and it is the half of
the name worth reading.
