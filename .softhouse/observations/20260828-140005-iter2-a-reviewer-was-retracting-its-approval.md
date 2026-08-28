# `T365` was merged on an APPROVED verdict its own reviewer was in the act of retracting

## What happened, in order

1. `T368` reviewed `T365` and returned **APPROVED**. It was a strong review — it proved `z07` was a real
   control by building its own mutation driver, and surveyed 143 `LOCK` commits to justify the skew bound.
2. It declared **one** thing it could not finish, honestly: *"the Alpine run to check whether
   `/usr/bin/mktemp` exists on busybox. Docker is available (29.6.2) but the image did not pull in time,
   so I report no off-BSD result."* Marked `[UNVERIFIED]` with the reason.
3. On that verdict the driver merged `T365` + `T368` into `main` (`e3eb73f9`), bar green.
4. **The Alpine image finished pulling later, and `T368` was re-invoked.** Its next words were:
   > *"That is a decisive result and it changes my verdict. Let me confirm it end-to-end and test the
   > candidate fix before I recommend it."*
5. It was then **killed by a session rate limit (HTTP 429)** before it could say what changed.

## What the retracted verdict almost certainly was

`T377` — working independently, on the follow-up task, without knowledge of step 4 — found exactly the
defect `T368` had gone to look for: **`/usr/bin/mktemp` does not exist on busybox** (it is `/bin/mktemp`),
and the shipped self-test refused with `rc 2` on Alpine+zsh+python3, meaning **the fire could not start
there at all**. The driver confirmed `main` hard-codes `/usr/bin/mktemp` at `fire-program.sh:549` and
`:815`.

So the outcome is fine — the defect is **already fixed on `T377`'s branch**, which resolves
`$FIRE_MKTEMP` from a fixed list of absolute candidates and produces the first non-BSD green in that
file's history. But the *process* fact stands on its own and is worth keeping.

## The lesson, and it is not "T368 was wrong"

`T368` did everything right. It ran what it could, it refused to guess, it named the gap, and when the gap
closed it went back and started retracting. **The pipeline has no mechanism for a reviewer to retract a
verdict after the driver has acted on it.** A verdict is read once, at merge time, and is thereafter
treated as settled.

**A review carrying an `[UNVERIFIED]` item is a PROVISIONAL verdict, and should be recorded as one.** The
merge was not wrong — waiting indefinitely for an image pull would be worse — but the driver should have
recorded `T365` as *merged on a verdict with one open `[UNVERIFIED]` item*, so that when the item closed,
the verdict was known to be re-openable.

Concretely, for next time: when a review's verdict is APPROVED but its handoff carries an `[UNVERIFIED]`
item **that could change the verdict**, the driver should record the merge as provisional and file the open
item as a task in the same commit — rather than relying on a later task to stumble into the same finding.
Here it worked only because `T377` was independently pointed at the same question.

## Also worth recording

The rate limit killed `T368` **mid-sentence**, after it had already published a verdict the program acted
on. That is the sharpest possible illustration of why workers must commit before they wait, and why a
handoff must state what was *not* done.
