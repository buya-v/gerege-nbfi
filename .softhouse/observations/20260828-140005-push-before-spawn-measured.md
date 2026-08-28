# Fire `20260828-140005` — push-before-spawn OBEYED, measured forward, second consecutive fire

STEP 0 of `softhouse-program` requires the LOCK, the dispatch record (`tasks.json` with every dispatched
task already flipped off `pending` and carrying its `branch`) and the in-flight `RESUME.md` to be **pushed
before the first `git worktree add`** — not before the end of the batch. The obligation has been missed
twice by drivers who had read it (2026-08-22, 101 s late, one of three artefacts; 2026-08-28 08:00,
135 s late, two of three).

## This fire — measured after the fact from directory mtimes, not from intent

| Event | Time (+08) |
|---|---|
| `LOCK` written by the wrapper | 14:00:22 |
| Bar on `main` run by the driver | 14:00:57 → 14:04:xx |
| **Dispatch record committed** `9ae2b01c` (tasks.json + RESUME.md, all 5 tasks `in_progress` with branches) | **14:05:39** |
| **Pushed to `origin/main`** | **14:05:46** |
| First `git worktree add` of the batch (`agent-a00dbfd6196b49bc0`, T339) | 14:06:52 |
| T340 | 14:07:10 |
| T346 | 14:07:41 |
| T347 | 14:08:13 |
| T323 | 14:08:27 |

**Minimum margin: +66 s.** All five worktrees created after the push. All three artefacts in ONE commit,
so there is no window in which any of them was published without the others.

## What this does and does not prove

It proves the window did not open **this time**. It does not make the obligation enforced: it is still a
convention with **zero mechanical backing**, which is **P-45** — *"a guard that only works when someone
remembers to run it enforces nothing"*. The candidate mechanisms have now both been driven and both failed:

- **post-checkout hook** (`.softhouse/capture/t279-lock-partition/post-checkout`, built, never installed) —
  T280's F-C and then T336 measured that on `/usr/bin/git` 2.50.1 the hook's `enforce` returns rc=1 and
  **git creates the worktree anyway**; and driven through the real harness route, **the hook does not run at
  all**.
- **`reference-transaction` in `prepared`** — genuinely aborts `git worktree add` (rc 255), and is useless
  here because the harness never invokes it.

T336's decision was therefore *install nothing*, and `T347` is reviewing whether that rejection was too
narrow. `T349` evaluates the remaining candidate, a `PreToolUse` deny hook, which is the only mechanism
left that sits on the harness's own spawn path rather than on git's.

**Until one of those lands, the enforcing mechanism is a driver reading STEP 0 before it dispatches.**
This file is evidence of one such read, not a substitute for the mechanism.
