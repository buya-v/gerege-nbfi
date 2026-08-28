# Driver error, fire 20260828-140005 iter2 — a coordinator message was delivered to the wrong worker

## What happened

The driver dispatched T365 and T363 in one batch. The id→task mapping it derived at spawn time was
**correct**. It then sent each worker a mid-run correction and **addressed both to the wrong id**:

| Agent id | Actually running | Was sent | Should have been sent |
|---|---|---|---|
| `a0170054b87414aa1` | **T365** (lock protocol) | T363's message (oracle-moved records) | T361 branch-ref correction |
| `ad65dab4e80c74658` | **T363** (oracle baseline) | T365's message (T361 branch-ref) | oracle-moved records |

This was an **addressing slip, not a mapping confusion** — the driver had the mapping right and typed the
other id. That distinction matters for the fix: a better id→task table does not prevent it; only reading
the id back off the roster at send time does.

## How it was caught — by the worker, not the driver

T363's completion report ended:

> "a coordinator message addressed to **T365** (different write grant, different subject) was delivered
> into this task mid-run; I did not act on it."

**T363 behaved correctly**: it noticed the message named a different task, declined to act, and reported
it. Had it instead tried to be helpful and act on the contents, it would have written outside its grant
against instructions meant for a different file.

## The real cost

T363's message was an *addition* (a third `ORACLE-STATE-MOVED-BY-*` record). T365's was a **correction to
a broken command the driver had already given it** — `git show softhouse/T361-review-t353:...`, which
fatalled because the ref did not exist. So the worker that needed its correction **did not get it**, for
roughly 20 minutes, while the worker that did not need it got one it had to reason past.

## What was done

The correct message was re-sent to T365 (`a0170054b87414aa1`), explicitly flagged as a driver error, told
it to ignore the misrouted one, and — because the driver could not know how far T365 had got — instructed
it to **mark as `[UNVERIFIED]` any C1–C5 claim it had reconstructed from the driver's paraphrase rather
than read from T361's REVIEW.md**. A paraphrase presented as a reading is the honesty-rule violation this
program grades hardest.

## Standing fix

The roster now lives in `RESUME.md` under **Worker roster**, and the rule is: **read the id back off the
roster immediately before sending, and name the task in the message's first line** so a misrouted message
is self-identifying to its recipient. T363's report is the proof that this second half works — the message
named T365 in its first line, which is exactly how T363 knew to refuse it.
