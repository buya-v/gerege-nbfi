# T302 working notes (incremental — committed as found)

## Verified so far

1. T309's finding CONFIRMED in passing [VERIFIED: `.softhouse/bin/fire-program.sh:422-433, 740, 1116`].
   `on_signal()` is `stop_driver; release_lock; exit $rc`. `run_exit_guard` (which contains
   `reconcile_tasks_json` at :1032) is called ONLY from the chain-loop body at :1116. A signal
   therefore never reaches the reconciler. Not re-derived further — T309 owns the write.

2. NEGATIVE RESULT (checked, found clean): the zsh `local`-in-loop stdout leak that T288
   documented and fixed inside `foreign_live_session_in_repo` does NOT recur in the worktree
   sweep loop T288 also edited. Measured on zsh 5.9 (arm64-apple-darwin25.0):
   - `local P` (no assignment) inside a loop PRINTS `P=<old value>` to stdout -> leaks
   - `local P="v"` (declaration WITH assignment) -> silent
   - `local -a A` and `local -a A=(...)` -> silent
   The sweep uses `local -a WS_LINES` and `local PRIOR="${WT_BRANCHES[$WI]}"`; both are silent forms.

3. MEASURED on this host during THIS live fire (`20260823-140001`):
   - `.softhouse/LOCK` pid `4627` = `/bin/zsh /Users/buv/gerege-nbfi/.softhouse/bin/fire-program.sh`
   - live claude = pid `4692`, ppid `4689`, and
     `/usr/sbin/lsof -w -a -d cwd -p 4692 -Fn` -> `n/Users/buv/gerege-nbfi`
   i.e. a driver's cwd IS `$REPO` exactly, not a subdirectory.
