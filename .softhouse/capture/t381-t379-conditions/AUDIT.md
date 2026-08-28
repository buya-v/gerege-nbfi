# T381 — the full `2>/dev/null` / discarded-pipe-status audit of `casualty-sweep.sh`

Ordered by T379's R2, which is a fail-open *inside* the fix for a fail-open. The remedy for R2
is worth nothing if a sixth instance of the same shape is sitting three lines away, so **every**
`2>/dev/null` and **every** pipeline in the file was classified, not just the two the review
named. Line numbers are as at commit `93e82869` in
`.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh`, and every one of them
was re-derived by running `grep -n` at that head rather than carried over from an earlier draft.

## 0. `set -o pipefail` — PRESENT, and it did not help

`set -uo pipefail` is at `:118`, and it was already on `main` (`:56` there). **Its presence is
exactly why R2 has to be stated carefully.** With `pipefail`, `n=$(git grep … | awk …)` *does*
propagate `git grep`'s 128 into the assignment's exit status — and the code never read the
assignment's status either, so the propagation went nowhere. `pipefail` makes a status
*available*; it cannot make anyone read it. Reporting the option as absent would have been
factually wrong; reporting it as "present, therefore fine" would have been the same error one
level up.

## 1. Every `2>/dev/null`

| line | site | verdict |
|---|---|---|
| 16, 77, 80 | inside the T371 / T381 header comments, quoting the defect | **prose.** Not executable. |
| 127 | `_top=$(git rev-parse --show-toplevel 2>/dev/null) \|\| _top=""` | **FAIL-CLOSED, correct.** The status *is* read, by the `\|\|`, and `:128` refuses with exit 2 if `_top` is empty or the `cd` fails. A silenced stderr whose status is read and whose failure is fatal is not a fail-open. |
| 302 | the word appearing inside the new comment that explains this audit | **prose.** |

**Both fail-open sites are GONE.** On `main` they were `:100` and `:108` — the `-F` positive and
`-F` anti calibration arms, each `2>/dev/null | awk`, neither status read. They are replaced by
`engine_count()` (`:186`–`:198`), which reads `git grep`'s status **and** `awk`'s status and
refuses a non-numeric tally.

## 2. Every pipeline on an executable line

Classified by the only question that matters: **is a fact inferred from this pipeline's output,
and if the pipeline failed, would that fact be wrong and silent?**

### 2a. MEASUREMENT pipelines — status now read. This is the class R1/R2 live in.

| line | site | verdict |
|---|---|---|
| 193 | `n=$(printf … \| awk …); arc=$?` inside `engine_count()` | **READ.** `arc` is checked, and `:195` `case "$n" in ''\|*[!0-9]*) return 3` refuses a non-numeric tally. Callers distinguish "did not run" (2) from "tally failed" (3). |
| 309 | `printf '%s' "$a" \| LC_ALL=C grep -q …; esc_rc=$?` — the new R3 backslash-class check | **READ.** Found by *this* audit, in T381's own new code. Written the obvious way — `if printf \| grep -q …; then` — it is the fifth instance of the shape: `grep` exits 2 on ERROR, an `if` reads a 2 as FALSE, and the selector sails past a check that never ran. `esc_rc >= 2` now refuses. Driven RED: **D-R5**. |
| 356 | `live=$(printf … \| grep -v -E "$ARCHIVE"); live_rc=$?` | **READ.** T379 R1. `>= 2` refuses at `:358`. |
| 357 | `arch=$(printf … \| grep -c -E "$ARCHIVE"); arch_rc=$?` | **READ.** T379 R1. `>= 2` refuses at `:358`. |

### 2b. NARRATION pipelines — status discarded, and discarding it is correct

None of these produces a fact anyone reasons from; they format bytes already counted elsewhere,
or they print. `grep .` returning 1 on empty input is the *expected* case for several of them,
so reading the status would manufacture false alarms rather than catch anything.

| line | site | why discarding is right |
|---|---|---|
| 206 | `printf '%s' "$ENGINE_ERR" \| grep . \| cut \| sed` — printing the engine's complaint on a calibration refusal | pure printer, on a path that has **already** decided to `exit 3` |
| 339 | the same shape, on the `SELECTOR DID NOT RUN` path | pure printer, on a path that has already set `SWEEP_RC=4` |
| 344 | the same shape, on the new `ENGINE STDERR` path (R4) | pure printer |
| 369 | `printf '%s' "$live" \| grep . \| cut \| sed` — listing the LIVE hits | pure printer; the *count* printed beside it is computed at `:368`, not here |

### 2c. COUNTING pipelines inside a `printf` / `echo` argument

| line | site | verdict |
|---|---|---|
| 348 | `"$(git ls-files .softhouse \| grep -c .)"` — the denominator in `MEASURED ZERO — engine ran over N tracked files …` | **ACCEPTED, WITH A STATED RESIDUAL.** If `git ls-files` failed this prints `0`, and "ran over 0 files and matched nothing" is a fail-open sentence. It is bounded by `:376`, which refuses (exit 2, P-35) if that same expression is `< 1` **before** any selector runs — so it can only reach `:348` as 0 if `git ls-files` broke *between* the two calls. Filed as **FU-T381-1** and deliberately not repaired: threading a fifth status through `sel()` to close a few-second window is not proportionate, and naming it is. |
| 362, 368 | `"$(printf '%s' "$all" \| grep -c .)"` — the hit total | `$all` is a shell variable already in memory; `grep -c .` over it cannot fail for a reason that would not also have killed the shell. |
| 374, 375 | `git ls-files … \| wc -l \| tr -d ' '` in the banner | banner narration. The load-bearing corpus assertion is `:376`, a separate and checked expression. |
| 376 | `if [ "$(git ls-files .softhouse \| grep -c .)" -lt 1 ]` — **the corpus assertion** | **FAIL-CLOSED.** A failed `git ls-files` leaves `grep -c .` printing `0`, the test is true, and the script exits 2 (P-35). The failure direction is refusal, which is the correct one. |
| 399 | `-E 'count\(\*\)…'` — S10's pattern | not a pipe; see 2d. |

### 2d. Not pipelines at all

`:155` (`ARCHIVE`), `:177`, `:178` (the two ERE calibration patterns) and the selector lines
`:385, :389, :390, :393, :395, :398, :399, :400, :418, :419, :420, :421, :422` contain `|`
**inside single-quoted regexes** — ERE alternation, not shell pipes. Listed explicitly so a
reader who greps the file for `|` and gets a long list knows which lines were dismissed and on
what ground, rather than having to trust that they were looked at.

## 3. Summary

- `2>/dev/null` on an executable line: **1 remaining** (`:127`), fail-closed, correct. Both
  fail-open ones are gone.
- Pipelines a fact depends on: **4**, all now read. Two of the four are the review's R1 and R2;
  the third (`:309`) was found by this audit inside T381's own repair and is driven by D-R5; the
  fourth is `engine_count()`'s own tally.
- Pipelines whose status is discarded: **10**, each classified above. One of them (`:348`)
  carries a bounded residual and is filed as FU-T381-1 rather than glossed over.
