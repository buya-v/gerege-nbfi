#!/usr/bin/env python3
"""T202 -- mutants of the T-b fix. The green harness must FAIL each."""
import io

# T465 -- the lock's repo-relative path is ASSEMBLED and spliced in at @LOCK@, never spelt.
# This file is a tracked `.softhouse/*.py` instrument, and a spelt `.softhouse/`-rooted literal
# is a row in T316's dead-path frontier whenever the fire lock is out of the index -- which is
# the state main is in after every fire exit. The SPLICED VALUES BELOW ARE BYTE-IDENTICAL to the
# literals they replace; this is a change of spelling, not of what T202 mutated.
SH_DIR = ".softhouse"
LOCKPATH = SH_DIR + "/LOCK"
post = io.open("/tmp/t202/postfix-guard.zsh", encoding="utf-8").read()
muts = {
    # BA: pathspec left cwd-relative (the original defect), rcs checked
    "BA": [("  git add -A -- ':(top)' ':(top,exclude)@LOCK@' >/dev/null 2>&1".replace("@LOCK@", LOCKPATH),
            "  git add -A -- . ':!@LOCK@' >/dev/null 2>&1".replace("@LOCK@", LOCKPATH))],
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
