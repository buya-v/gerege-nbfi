# RESUME manifest — gerege-nbfi Fineract→Go migration

## FIRE `20260828-140005`, chain iteration 2 — **IN FLIGHT. FOUR LIVE WORKERS.**

**If you are reading this and no driver session is running, four workers were killed mid-flight.**
Their branches below may hold partial work. Mark each `needs_retry`, do not read `in_progress` as
"work is happening".

| Task | Branch | Model | Grant |
|---|---|---|---|
| `T364` | `softhouse/T364-review-t358` | opus | `.softhouse/reviews/t364-review-t358/` |
| `T362` | `softhouse/T362-review-t357` | opus | `.softhouse/reviews/t362-review-t357/` |
| `T365` | `softhouse/T365-t361-conditions` | opus | `.softhouse/bin/fire-program.sh`, `.softhouse/capture/t365-t361-conditions/` |
| `T363` | `softhouse/T363-oracle-baseline` | opus | `.softhouse/capture/t363-oracle-baseline/`, `.softhouse/reference-oracle.md` |

Chosen so no two grants overlap. `T363`'s grant was **narrowed by the driver** from `.softhouse/reviews/`
(the whole review tree — it collided with both reviewers in this wave) to `.softhouse/reference-oracle.md`.

## State inherited from chain iteration 1 (unchanged, still true)

Bar GREEN on `main`: `bash .softhouse/conformance.sh` → exit 0, probe line PRESENT reading `up`,
46 parity vectors / 7884 cells / 0 FAIL / 0 inadmissible.

**`main` still carries the T323 bar-bricking hazard.** T323's merged `guard_guards_dir_registration`
uses a git pathspec `*` that crosses `/`, so any task adding an ordinary `.sh` fixture anywhere under
`.softhouse/guards` drives the whole bar to exit 2. Fail-CLOSED, so no false PASS. **`T358`
(`softhouse/T358-t323-conditions` @ `aac9e12b`) already fixes it.** `T364` is reviewing it now; merge
on a clean review.

### Complete, committed, NOT merged

| Task | Branch | Head | Waiting on |
|---|---|---|---|
| `T358` | `softhouse/T358-t323-conditions` | `aac9e12b` | `T364` (dispatched) |
| `T357` | `softhouse/T357-a2-11-section1-red` | `85a30a79` | `T362` (dispatched) |
| `T361` | `softhouse/T361-review-t353` | `b4bf2abf` | `T366` (next wave) |

### ⚠ The git trap — and a SECOND one the driver found underneath it

The driver merged T361 (`380f0d64`) and reverted it (`2fa4015b`). **The commits are in `main`'s history;
the files are not.** `git merge` will say "Already up to date" and restore nothing.

**AND THE BRANCH NAME THE PREVIOUS MANIFEST GAVE FOR RECOVERY DID NOT EXIST.** Measured this fire:
`softhouse/T361-review-t353` resolved to `fatal: Not a valid object name` — absent locally *and* on origin
(`git ls-remote --heads origin | grep -i t361` → 0 hits; only 34 of 243 local `softhouse/*` branches are
pushed at all, so absence from origin alone is normal — absence from both is not). The previous RESUME.md
and T366's task text both instructed the next reader to use that name. The driver restored it:

```
git branch softhouse/T361-review-t353 b4bf2abf
git merge-base --is-ancestor softhouse/T361-review-t353 main   →  TRUE
git ls-files | grep -c t361-review-t353                        →  0
git ls-tree -r --name-only softhouse/T361-review-t353 | grep -c t361-review-t353   →  40
```

**USE THE CLONE-PORTABLE SPELLING INSTEAD.** `b4bf2abf` is the second parent of the merge `380f0d64`, so it
is reachable from `origin/main`, can never be GC'd, and works in a fresh clone that has no local branches —
which a local branch ref demonstrably does not:

```
git ls-tree -r --name-only '380f0d64^2' | grep -c t361-review-t353   →  40
git show '380f0d64^2':.softhouse/reviews/t361-review-t353/REVIEW.md
```

**Verify by file count, never by merge output.** T366's task text has been patched with this correction, and
the live `T365` worker — which was dispatched with the broken command — was messaged directly.

## Next wave, after this one is awaited and merged
`T366` (land T361 without reddening the bar) → `T360` (a vector class for oracle-ACCEPTS/port-REFUSES)
→ `T354` → `T355` → `T356`. `T366` and `T360` both touch `conformance.sh`, as does the unmerged `T358`
— serialise them behind the T358 merge rather than running them alongside it.

## Open gate
`G-19` is OPEN for Buyan and **blocks nothing**.

## Pause reason
**Not paused.** Four workers dispatched and being awaited by chain iteration 2.
