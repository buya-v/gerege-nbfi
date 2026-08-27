# Branch-name case collision silently shadows committed worker output

**Filed by** the driver of fire `20260827-230001`, after **worker T308 caught the driver's error**.
**Class:** evidence-destruction risk in the pipeline itself. Not a money defect; a defect in the thing
that decides whether money defects are ever seen.

## What happened

The driver's pre-flight declared, in `RESUME.md` and in a pushed commit message, that the eight
branches dispatched by fire `20260823-140001` were *"gone or empty"*, and re-dispatched six of them as
**fresh attempts**. That claim was inherited from the `140001` driver's record and the driver
**re-checked it with the wrong instrument**:

```
git branch -a --list 'softhouse/t2*' --list 'softhouse/t3*'     # ← lowercase glob
```

**The repo's convention is UPPERCASE**: `softhouse/T297-…`, `softhouse/T308-…`. Of ~200 `softhouse/*`
branches, essentially all carry an uppercase `T`. The lowercase glob matched only the handful of
lowercase branches and **returned nothing for T297–T309**, which the driver read as "no surviving
work". `git branch --list` globbing is case-sensitive; the *filesystem* is not. That gap is the whole
bug.

T308's worker did not accept its brief's branch name. It looked, found
`softhouse/T308-review-t292` with a **complete prior review already committed**, and continued that
branch instead of forking a case-variant. It then said so in its report. **The driver's pre-flight was
wrong and a worker corrected it** — the fourth time this program has recorded a worker refuting the
driver's stated facts.

## The measurement

Every one of the eight had commits. Measured at this fire, `git rev-list --count main..<branch>`:

| branch | commits ahead of main |
|---|---|
| `softhouse/T308-review-t292` | **32** |
| `softhouse/T309-sigterm-reconcile-bypass` | **11** |
| `softhouse/T298-review-t256` | **10** |
| `softhouse/T304-evidence-destruction` | **7** |
| `softhouse/T306-adjudicate-admit-widening` | **5** |
| `softhouse/T302-review-t288` | **4** |
| `softhouse/T297-review-t295` | 0 (loose) / **4 (packed — see below)** |
| `softhouse/T305-openingbalance-accepting-side` | 1 (loose) / **8 (packed)** |

`softhouse/T297-review-t295` was **not empty**. It carried four commits ending at `c1a3888a`,
including `2b99f69b "review scaffold - first commit before analysis (SIGTERM insurance)"` — a worker
doing exactly what the commit-early rule asks — and `060f0033` on T305 carried **a finished 274-line
handoff** declaring the accepting-side capture refused with its measurement.

## The second, worse mechanism: loose refs shadow packed refs across case

macOS's filesystem is case-insensitive. `refs/heads/softhouse/T297-review-t295` and
`refs/heads/softhouse/t297-review-t295` are **the same path**. But `packed-refs` is a text file and is
**case-SENSITIVE**, so it can hold an entry a loose ref of different case then shadows — git resolves
loose before packed, and the packed value becomes unreachable by name while remaining a live object.

Observed, not reasoned:

```
$ git rev-parse softhouse/T297-review-t295 softhouse/t297-review-t295
d189230bebebad9c0b9f72bae494bb4ef08c213a
d189230bebebad9c0b9f72bae494bb4ef08c213a      # ← both names, ONE ref

$ grep 'softhouse/T297-review-t295' .git/packed-refs
c1a3888aa2179689e59f0891a06d30699f99a88d refs/heads/softhouse/T297-review-t295   # ← shadowed
```

`git merge-base --is-ancestor c1a3888a d189230b` → **false**. The two lines had **diverged**: the
shadowed line reorganised the review into `probe/` and carried
`t297_strictport_test.go.txt` / `t297_declination_test.go.txt` — **the actual mutant ports as source** —
which the merged line does not contain. Same for T305: `060f0033` vs `37d4c5bb`, not an ancestor.

**So this is not merely "the driver looked in the wrong place".** Dispatching a lowercase branch name
into a repo whose convention is uppercase **creates a ref that shadows the one already holding work**,
on this filesystem, silently. The driver caused that by writing lowercase branch names into seven
worker prompts.

## What was done about it, this fire

Nothing was deleted and nothing was rewritten. Every divergent line was pinned under an
**unambiguous, collision-proof namespace** and pushed:

```
refs/rescue/20260827-230001/t297-packed-line   c1a3888a
refs/rescue/20260827-230001/t297-loose-line    d189230b
refs/rescue/20260827-230001/t305-packed-line   060f0033
refs/rescue/20260827-230001/t305-loose-line    37d4c5bb
refs/rescue/20260827-230001/packedref-*        (every packed T29x/T30x value)
…and one per branch for T298/T302/T304/T306/T308/T309
```

`refs/rescue/…` cannot collide with `refs/heads/softhouse/…`, and the names are already lowercased, so
the namespace is closed under the very defect it is rescuing.

## Why this belongs beside P-45 and P-66, not in a footnote

- **P-66** — *"'Not found' is a statement about the search, never about the world. Before recording
  that a dependency, file, vector or citation does not exist, state where you looked."* That rule was
  written after seven dependency edges were declared unresolvable while sitting `done` in an archive.
  **This is the identical failure against a different index**: branches instead of `tasks.json`, a
  case-sensitive glob instead of a single-file lookup. The driver recorded an absence and did not state
  its selector. Had it printed `git branch -a | grep -i softhouse`, the eight would have been on screen.
- **P-45** — *"a guard that only works when someone remembers to run it enforces nothing."* The corpse
  sweep is a guard the driver runs by hand, by eye, with an ad-hoc glob it retypes each fire. It has
  now produced a false "all empty" once. `ready-tasks.py` already exists to answer *dependency*
  questions mechanically; there is **no equivalent instrument for "does this task's branch hold work?"**,
  which is why the question got answered by a shell glob typed from memory.

## What must change (filed as T312)

1. **The corpse sweep must be an instrument, not a glob.** Case-insensitive, and it must resolve
   *both* the loose and the packed value for every candidate name and report when they differ.
2. **Branch names must be canonical-case at dispatch.** The driver must derive the branch name with the
   repo's existing convention, and refuse to dispatch a name that differs from an existing branch only
   by case — that is the shadowing precondition, and it is cheap to detect.
3. **`ready-tasks.py` already flags "`in_progress` with no `branch`" as a suspected isolation
   violation.** It should also flag *"branch named, and a case-variant of it exists"*, because the
   current check passes cleanly in exactly this situation.

## Honest limits of this note

- `[UNVERIFIED]` **which** mechanism wrote the lowercase loose refs for T297/T305 while T298/T308/T309
  ended up uppercase. Both cases appeared under `.git/refs/heads/softhouse/` this fire and the driver
  did not instrument ref creation while workers were live. The *consequence* is measured; the
  *provenance* is not, and is not guessed at here.
- `[UNVERIFIED]` whether any earlier fire lost work to this. The `140001` driver's record —
  *"4 branches at dispatch commit with zero commits ahead, 4 never created"* — is now **suspect for the
  same reason**, but re-deriving it needs the reflog state of that fire and this note does not claim it.

---

## Addendum, same fire: the driver reproduced the backtick-injection defect it already had on record

While writing the T309 merge message the driver wrote a word in backticks inside a double-quoted
`git commit -m` argument. zsh command-substituted it:

```
(eval):96: command not found: fire
```

and the committed message reads **`"But  is stamped at FIRST dispatch"`** — the word silently deleted.
This is the identical defect recorded against fire `20260823-080016`, where backticks in a commit
message executed and injected a 6,733-line file listing. That one was caught before push; **this one
was not**, so `2dfbe422` on `main` carries the hole.

**Not repaired by rewriting history.** Amending a pushed merge commit on `main` while workers hold
forks of it trades a cosmetic defect for a hard-to-reverse published-history rewrite, which is a worse
trade. The correction is recorded here and forward in the log instead.

**The rule, since twice is a pattern:** *no backticks in a commit message, ever.* Use plain words or
single quotes. The shell does not care that the backticks were "obviously" meant as markdown.
