# The overnight queue

Briefs placed here are run by `.softhouse/briefs/tools/nightq.sh`, one at a time in filename order,
each in its own worktree and branch; it never merges or pushes. A run brief is renamed `done-<name>`.
**Only oracle-free briefs belong here** — nobody watches the oracle overnight. The driver reviews every
resulting branch with `tools/review.sh` before merging anything. (Buyan, 2026-09-11.)
