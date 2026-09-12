# Repository notes

## Shared git repository / worktree contention
This worktree shares `/Users/buv/gerege-nbfi/.git` with other sessions and worktrees
that run `git reset --hard`, `git worktree add`, `git add` and `git commit` concurrently.

- `git commit` here can hang indefinitely when the process inherits an interactive or
  blocked stdin. Always bound it and detach stdin:
  `git commit -F <msg> </dev/null` (or `git commit </dev/null -m ... -m ...`).
- Message files written under `/tmp` have been observed to disappear between tool calls.
  Prefer inline `-m` flags, or write the message inside the worktree and delete it after.
- Signs of contention: a stale `<worktree>/.git/worktrees/<name>/index.lock`; a `git add`
  that does not return. Recover by interrupting, confirming the lock is gone, then retry.
- Never use `&`, `jobs`, `wait`, or `sleep > 60`. Give every long command a bound.

## Tier D capture rig
Reference capture/edit layout lives under
`.softhouse/capture/tierd-feasibility/`. The throwaway oracle (tenant `tierd`, port 8444)
is destroyed by `throwaway/down.sh`; isolation is proven against the 12 standing counters in
`throwaway/out/STANDING-baseline.txt`. Standing tenants `gerege` (8443) and `default` must
never be touched. Capture is PostgreSQL-only; Oracle is prohibited.
