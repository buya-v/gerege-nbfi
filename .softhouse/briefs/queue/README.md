# The overnight queue

Briefs placed here are run by `.softhouse/briefs/tools/nightq.sh`, one at a time in filename order,
each in its own worktree and branch; it never merges or pushes. A run brief is renamed `done-<name>`.
**Never a brief that writes to the STANDING oracle** (tenants `gerege` / `default`) — nobody watches it overnight. A Tier D
replay on the THROWAWAY instance is allowed: its rig writes the standing counters fail-closed before starting and proves them
unchanged after teardown (`.softhouse/capture/tierd-feasibility/throwaway/`), and a queue run tears down even when a step fails. The driver reviews every
resulting branch with `tools/review.sh` before merging anything. (Buyan, 2026-09-11.)
