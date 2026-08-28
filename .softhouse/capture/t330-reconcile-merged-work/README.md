# T330 — FU-RECONCILE-1 capture

The post-fire reconcile demoted `T324` (`in_progress` -> `needs_retry`) because its
recorded branch was absent. The branch was absent because the work had been MERGED and
the branch PRUNED (`a08a64e2` + merge `d36863ad`, 14 files / 2,338 insertions).

`_branch_wip_core` already printed the correct caveat (T319 F1) and demoted anyway.
**A caveat is not a control.** This capture holds the drive that turns branch-absence
into a multi-way verdict with an ACTION attached.

Contents:

* `design.md`        — the verdict table and the argued `merged` action
* `drive.py`         — the four-arm RED/GREEN driver (scratch clones only)
* `red.txt`          — the four arms against the CURRENT `_branch_wip_core`
* `green.txt`        — the four arms against the fixed `_branch_wip_core`
* `budget.py` / `budget.txt`   — measured added cost on the real 219-task `tasks.json`
* `failclosed.txt`   — exhausted-budget degradation proof
* `population.py` / `population.txt` — the archived-runs sweep (`.softhouse/runs/*.tasks.json`)
