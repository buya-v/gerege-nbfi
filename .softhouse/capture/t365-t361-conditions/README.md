# T365 — T361's conditions C1..C5, C8, C9, C11 applied to `.softhouse/bin/fire-program.sh`

`fire-program.sh` sha256 **before** T365 `c55a9c8b3a56e894030f4dc68a2bc4c8597d43a0ba18fce048d11c327086e22d`
(the same file T361 reviewed and printed in every one of its instruments),
**after** `06c57d0e192fa1484b9c25ad5ac7995049471a98ddf4425d0d663561b034bf53`.

## Where T361's review came from

`.softhouse/reviews/t361-review-t353/` **is not on disk in any worktree** — merge `380f0d64`
landed it and revert `2fa4015b` removed the files while leaving the commits in main's history.
The review was read from git, at commit `b4bf2abf` = `380f0d64^2`, and both spellings plus the
(later restored) branch ref resolve to the same blob:

```
git show '380f0d64^2':.softhouse/reviews/t361-review-t353/REVIEW.md   # sha256 fb75133b…
git show b4bf2abf:.softhouse/reviews/t361-review-t353/REVIEW.md       # sha256 fb75133b…
git show softhouse/T361-review-t353:.../REVIEW.md                     # sha256 fb75133b…
```

Every condition below is quoted from that text, not from a task-text paraphrase.

## bin/

| file | what |
|---|---|
| `t361-reader-corpus.zsh` | **T361's 24-body corpus, byte-for-byte** (`git show b4bf2abf:.../bin/t361-reader-corpus.zsh`). Not edited. It is the independent instrument, and it is here so the AFTER run is reproducible now that the review's own directory is not on disk. |
| `t365-reader-corpus.zsh` | The same corpus with **one row repaired**, x11 — its instant was a fixed wall-clock literal, so its verdict depended on the hour of day. `diff` the two for the whole change. |
| `t365-red-drives.zsh` | P-22. Reverts each condition on a throwaway copy and requires the wired self-test to catch it, naming the direction. `CHECKS=17 WRONG=0`. |

## out/

`01`–`05` are the BEFORE baselines, `06` the first red-drive run (which caught two defects in
the red driver itself and is kept for that reason), `07` the final one, `08`–`18` the AFTER
runs. `06` is **not** superseded evidence to be ignored: it is where this task learned that an
epoch drifting HIGH cannot trip a `want=HELD` row, which is the argument for self-test group H.

## Fail directions

* **OPEN** = a lock held by a LIVE process reads as takeable. P-85 [`patterns.md:2822`]. The direction that destroys work.
* **SHUT** = a reclaimable lock is not reclaimed, or the fire refuses to start. Liveness only.

C1 closes OPEN at the cost of a bounded SHUT (a `released_at` more than `LOCK_RELEASE_SKEW_SECS`
ahead of this clock now reads as not-released). C2, C3, C9 are SHUT-side repairs. C4, C5 are
coverage, not live defects. C8 and C11 are text.
