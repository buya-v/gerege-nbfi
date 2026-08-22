# The fail-open rules `lint_failopen_t259.py` enforces

They live here, in prose, and not in the lint's own docstring. A lint whose description trips its
own patterns must either exempt itself or stay permanently red, and both are worse than writing
the tokens down once, here, where nothing scans them for enforcement.

The lint's regexes are assembled from string fragments at import time so that the lint file itself
is scanned like every other file and is expected to come back clean **on its own merits** —
nothing is excluded from the scan, and the file count printed on every run says so.

## Shell (`.sh`)

| banned | why |
|---|---|
| `\|\| true` | swallows the exit status; the script can no longer fail |
| `\|\| :` | same, spelled shorter |
| `\|\| echo …` | **P-80**: prints an absence over an error. `grep` exits 1 on NO MATCH and >1 on ERROR; `\|\| echo 0` makes those the same number |
| `2>/dev/null` | an error becomes an absence |
| `set +e` | the abort is disarmed |
| bare `grep` at command position | **P-75**: `grep` here is bundled ugrep 7.5.0 with six `--exclude-dir` flags silently prepended — 33 % recall, measured. Use `/usr/bin/grep` |
| `rg` | **P-75**: no binary in this environment, and `rg P F \| head` exits 0 |
| `git grep -E` | **P-75**: `\b` reads as a literal `b`, so it both misses and fabricates, and returns zero SILENTLY. `git grep -P` is fine |

**Required:** `set -euo pipefail` in every `.sh`.

## Python (`.py`)

| banned | why |
|---|---|
| a catch-all `except:` | swallows everything, including the bug |
| `except …: pass` | discards the failure |
| `2>/dev/null` in a string | same reason as the shell rule |

## The hatch

```
# lint-failopen: ok -- <reason>
```

on the offending line or the line immediately above it. **The reason is mandatory** — a bare
`# lint-failopen: ok` is itself a finding, checked before the comment-skip so it cannot hide in a
comment.

The hatch exists for a construct whose exit status is **captured and then classified explicitly**
within a line or two — which is a different thing from swallowing it. Using the hatch to silence
the detector while leaving the script able to lie is a rejection.

**The one hatch T259 uses**, in `red/drive-red.sh`'s `grep_count`: `set +e` is on for exactly one
line, so `/usr/bin/grep -c`'s status can be captured into `$rc` and then classified — 0 and 1 are
both real measurements, **>1 aborts the entire battery**. The banned alternative would have been
`|| echo 0`, which is precisely the shape that cannot tell a zero from a crash.

## Falsifiability

The lint is driven RED by `red/drive-red.sh` LEG `S2-lint-driven-red`, which plants a scratch shell
script carrying all of `|| echo 0`, `|| true`, `rg`, `2>/dev/null`, `git grep -E` and a missing
strict-mode preamble, and asserts the lint exits **1**. A lint nobody has watched fail is not a
lint. It is also driven GREEN, on T259's own instruments, in LEG `S-self-failopen-lint`.

**NIL COVERAGE is a refusal**: a scan that finds zero `.sh`/`.py` files exits 1, not 0. An empty
scan is not a clean scan.
