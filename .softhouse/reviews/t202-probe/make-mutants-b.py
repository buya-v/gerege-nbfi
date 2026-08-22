#!/usr/bin/env python3
"""T202 -- mutants of the T-b fix. The green harness must FAIL each."""
import io
post = io.open("/tmp/t202/postfix-guard.zsh", encoding="utf-8").read()
muts = {
    # BA: pathspec left cwd-relative (the original defect), rcs checked
    "BA": [("  git add -A -- ':(top)' ':(top,exclude).softhouse/LOCK' >/dev/null 2>&1",
            "  git add -A -- . ':!.softhouse/LOCK' >/dev/null 2>&1")],
    # BB: pathspec anchored, but the commit rc is NOT checked -- "rescued" is
    #     printed unconditionally again
    "BB": [("    if (( COMMIT_RC == 0 )); then\n      log \"rescued: committed the leftovers so the next fire can see them\"\n    else",
            "    if true; then\n      log \"rescued: committed the leftovers so the next fire can see them\"\n    else")],
    # BC: rc captured from the wrong command
    "BC": [("  ADD_RC=$?\n", "  [[ -n \"$STAMP\" ]]\n  ADD_RC=$?\n")],
}
for name, pairs in muts.items():
    body = post
    for old, new in pairs:
        n = body.count(old)
        if n != 1:
            raise SystemExit(f"mutant {name}: anchor matched {n}, expected 1")
        body = body.replace(old, new)
    p = f"/tmp/t202/mut-{name}.zsh"
    io.open(p, "w", encoding="utf-8").write(body)
    print("wrote", p)
