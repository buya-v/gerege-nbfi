#!/usr/bin/env python3
"""T202 -- derive three MUTANTS of the shipped fix from the shipped bytes.
Each is a plausible way to get the fix *wrong*; the green harness must FAIL
every one of them, or it is only detecting the original defect (P-50)."""
import io

post = io.open("/tmp/t202/postfix-sweep.zsh", encoding="utf-8").read()

muts = {
    # A: rc test inverted -- refuses on SUCCESS, trusts on FAILURE
    "A": [("if (( WS_RC != 0 )); then", "if (( WS_RC == 0 )); then")],
    # B: rc captured from the WRONG command (the `[[ -n ... ]]` test below it),
    #    so WS_RC never reflects git at all
    "B": [("  WS=$(git -C \"$W\" status --porcelain)\n  WS_RC=$?\n",
           "  WS=$(git -C \"$W\" status --porcelain)\n  [[ -n \"$W\" ]]\n  WS_RC=$?\n")],
    # C: notices the failure but still SILENTLY skips -- the fail-open survives
    #    behind a log line nobody branches on
    "C": [("    log \"ERROR: worktree sweep could not read git status for $W (rc=$WS_RC)",
           "    : \"silently skipped: (rc=$WS_RC)"),
          ("  log \"ERROR: worktree sweep could not enumerate worktrees (git worktree list rc=$WT_RC)",
           "  : \"silently skipped enumeration: (rc=$WT_RC)")],
}
for name, pairs in muts.items():
    body = post
    for old, new in pairs:
        n = body.count(old)
        if n != 1:
            raise SystemExit(f"mutant {name}: anchor matched {n} times, expected 1")
        body = body.replace(old, new)
    p = f"/tmp/t202/mut-{name}.zsh"
    io.open(p, "w", encoding="utf-8").write(body)
    print("wrote", p)
