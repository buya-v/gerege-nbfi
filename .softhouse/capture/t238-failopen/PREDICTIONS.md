# T238 — PRE-PROBE PREDICTIONS

Registered **before** any instrument was executed and before any population count was taken.
Written at fork point `477dc2da0f9edf3922e7d29e689bc6473289befc` (== `origin/main`, MEASURED, not asserted).

At the time of writing I had READ (not run):
`.softhouse/reviews/a2-33-dec2-rev5/sweep.sh`,
`.softhouse/capture/t234-sweep-instrument-audit/instruments/12-sweep-census.py`,
and §3.2–§5 of `.softhouse/capture/t234-sweep-instrument-audit/HANDOFF.md`.
I had NOT read `A2-11/enumerate-corpus.py`, `t184-census.sh`, `t184-sweep.sh`,
`a2-31-dec2-rev4/probe-sweep.sh` or `A2-32-evidence/sweep.sh`.

| # | prediction | falsifier |
|---|---|---|
| **PR-1** | The population of tracked `.sh`+`.py` files under `.softhouse/` at this commit is between **100 and 250**. | a count outside that range |
| **PR-2** | `reviews/A2-11/enumerate-corpus.py` fails **CLOSED** — Python `os.chdir()` on a missing directory raises `FileNotFoundError`, which is an uncaught traceback and a non-zero exit. | it exits 0, or prints an empty/complete-looking result |
| **PR-3** | At least ONE of `T184-evidence/t184-census.sh` / `t184-sweep.sh` fails **OPEN** (exit 0 with a result that reads like a real negative). | both fail closed |
| **PR-4** | T234's dead-`cd` detector is **too narrow**: it only matches the literal string `/Users/buv/gerege-nbfi/.claude/worktrees/`. I predict my broader enumeration finds **at least one** fail-open instrument by a mechanism that is NOT a dead worktree path (empty glob, `for f in $(...)` over an empty list, or a swallowed producer in a pipeline). | zero such instruments found |
| **PR-5** | `a2-31-dec2-rev4/probe-sweep.sh` and `A2-32-evidence/sweep.sh` fail **CLOSED**, as T234 reports. | either fails open |
| **PR-6** | A2-33's **81-vs-86** unique-line engine divergence (T234's L-1b) **IS** explainable from the committed artefacts alone, without re-running the dead sweep. | the artefacts prove insufficient |
| **PR-7** | A multi-line (`perl -0777`) matcher over the fail-open class will find **at least one** additional instrument whose defect straddles a line break and is therefore invisible to every line-oriented sweep in this program. | zero |

**Non-prediction, stated so it cannot be retro-fitted:** I do NOT predict anything about DEC-2 rev 5 or
G-11. This task is about REPRODUCIBILITY of an instrument, not about the ratification it supported.
A2-33's committed transcript (34 patterns, 0 `(no hits)`, 6334 hit lines) stands.
