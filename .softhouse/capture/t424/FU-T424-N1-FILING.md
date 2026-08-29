# `FU-T424-N1` — filed as work, with its evidence

**Raised as** `F-T424-N1` by T424 · **re-raised as `C-T440-3` (MINOR)** by T440 because it was
filed nowhere · **filed here, with a re-measurement, by T442.**

> **T442 could not file this in `.softhouse/tasks.json` and did not edit `conformance.sh`.** Its
> grant is `.softhouse/capture/t424/` only, and **`.softhouse/conformance.sh` is held by `T445`
> (`in_progress`, branch `softhouse/T445-case-route`, `conformance.sh` in its `files_hint`)
> [VERIFIED: `.softhouse/tasks.json`, read at `97bad8ed`]. This file is the filing: it carries the
> defect, the evidence, the exact repair and the acceptance test, so that adding it to
> `tasks.json` is a paste, not an investigation.

## The defect

`.softhouse/conformance.sh:1299-1300` states, **in the present tense and carrying its own
reproduction recipe**:

```
# `CONFORMANCE_REPO_ROOT` and `-repo-root` each occur ZERO times in it (measured on this
# file with /usr/bin/grep, BSD 2.6.0-FreeBSD, `LC_ALL=C grep -c`; both returned 0, exit 1).
```

Run that recipe today and it contradicts itself.

## The re-measurement — T442, at `97bad8ed`

| recipe, exactly as the sentence gives it | then | **now** |
|---|---|---|
| `LC_ALL=C /usr/bin/grep -c 'CONFORMANCE_REPO_ROOT' conformance.sh` | 0, exit 1 | **22**, exit 0 |
| the same, executable (non-comment) lines only | 0 | **16** |
| `LC_ALL=C /usr/bin/grep -c -- '-repo-root' conformance.sh` | 0, exit 1 | **2**, exit 0 |
| the same, executable (non-comment) lines only | 0 | **0** |

[VERIFIED: run on the worktree at `97bad8ed`. Reproduced independently by
`instruments/t424-comment-claims-drive.sh` CLAIM 2, transcript `out/T424-comment-claims.txt`,
which prints the same four numbers on every run and deliberately does not pin them (P-86).]

## Why it is not a harness regression

**The sentence was true when it was written, and the repair it argues for is what made it false.**
The paragraph at `:1293-1304` describes the **pre-repair** hole: `ResolveRepoRoot` preferred
`-repo-root`, then `CONFORMANCE_REPO_ROOT`, then the build anchor, and `conformance.sh` named
neither lever — so an exported environment variable moved the graded tree out from under every
guard in the file. `T201` closed that (`softhouse/T201-repo-root-bypass`), and closing it required
`conformance.sh` to start naming `CONFORMANCE_REPO_ROOT`. Hence 22 occurrences, 16 of them
executable.

`-repo-root` remains absent from executable lines (**0**); its 2 whole-file occurrences are this
same sentence and its neighbour. So the claim is *half* still true, and only of the code.

**Cause right, TENSE wrong** — the same shape as `F-2`, where the mechanism was right and the
attribution wrong, and the same shape as `C-T440-1`, where the record outlived the code it
described. A reader who runs the recipe today gets a contradiction and no way to tell a stale
sentence from a regressed harness.

## The repair — one sentence, past tense, anchored to a commit

Replace `conformance.sh:1299-1300` with, in substance:

```
# At the time of the hole, this script named NEITHER lever: `CONFORMANCE_REPO_ROOT` and
# `-repo-root` each occurred ZERO times in it (measured then with `LC_ALL=C grep -c`; both
# returned 0, exit 1). T201's repair is what changed that: `CONFORMANCE_REPO_ROOT` is now
# named by the guard below, so re-running that count today returns a NON-ZERO number and is
# expected to. `-repo-root` is still absent from every executable line.
```

Do not re-pin the counts: they move whenever the guard is edited, and a pinned count in a comment
is the next stale measurement (P-86).

## Acceptance test for whoever takes it

1. The sentence is past-tense and names the commit or task (`T201`) at which the zero held.
2. `git grep -c 'occur ZERO times in it' -- .softhouse/conformance.sh` → **0** afterwards.
3. `bash .softhouse/conformance.sh` still ends `EXIT 0` with the probe line present.
4. `bash .softhouse/capture/t424/instruments/t424-comment-claims-drive.sh` still exits **0** —
   its CLAIM 2 locates the paragraph **by content** on the anchor `each occur ZERO times in it`,
   so **that anchor must be kept or the drive's `locate` will REFUSE with exit 2**. If the phrase
   is dropped entirely, CLAIM 2's anchor must be updated in the same commit.

## Status

* **Not fixed by T442** — out of grant, and the file is contended by `T445` this wave.
* **T431 has merged**, so T431 no longer holds the region; `T445` does.
* Nothing about money, vectors or the ledger is affected. It is a comment whose measurement went
  stale in the direction of *"the thing it warned about was fixed"*.
