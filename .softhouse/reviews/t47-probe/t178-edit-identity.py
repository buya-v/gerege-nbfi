#!/usr/bin/env python3
"""T178: prove the EDIT ITSELF did not change.

T167's discipline for `t47_edit_1.py` was that hardening changes the head and
the tail and NEVER the edit.  This check enforces that for the other eight:
it extracts every (anchor, replacement) pair from the PRE-FIX AST (read from
the immutable fork-point commit, never from the moving ref `main`) and from the
POST-FIX AST in the working tree, and compares them literally.

Two call shapes exist in this family and both are collected:
  * `rep("anchor", "replacement")`      - seven of the eight, and the post-fix
    form `guard.rep(s, "anchor", "replacement")`;
  * two module-level triple-quoted string constants named `old` and `new`,
    with an inline `s.count(old)` gate - `t47_edit_4c.py` only.  Its post-fix
    form calls
    `guard.rep(s, old, new)` on the SAME two constants, so the pair is
    recovered from the constants rather than from the call.

This is a SECOND, independent check on the same property.  The first is
stronger and lives in `t178-redprobe.py` case R10: each post-fix script's
GREEN run reproduces an AFTER_SHA256 that was measured by running the PRE-FIX
script on the same input blob.  If a single byte of any replacement string had
moved, that sha would not match and the guard would refuse with exit 4.

Exit 0 = every edit is byte-identical to T47's.  Exit 1 = at least one moved.
"""
import ast
import io
import subprocess
import sys

REPO = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0d0a5c20aad048db"
FORK = "dfa1bfa96084a2175f0d89d0a401a8c105d9a35f"


def pairs(src):
    tree = ast.parse(src)
    env = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            env[n.targets[0].id] = n.value.value

    def val(a):
        if isinstance(a, ast.Name):
            return env.get(a.id)
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            return a.value
        return None

    out = []
    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.ClassDef)):
            continue
        for n in ast.walk(top):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name) and f.id == "rep" and len(n.args) == 2:
                out.append((val(n.args[0]), val(n.args[1])))
            elif isinstance(f, ast.Attribute) and f.attr == "rep" \
                    and getattr(f.value, "id", "") == "guard" \
                    and len(n.args) == 3:
                out.append((val(n.args[1]), val(n.args[2])))
    if not out and "old" in env and "new" in env:
        # t47_edit_4c.py's shape: two module-level constants and an inline
        # `s.count(old)` gate.  Recovered here rather than reported as zero
        # pairs, which would have read as "no edit" - P-40, count what you
        # could not resolve, never drop it.
        out.append((env["old"], env["new"]))
    return out


bad = 0
for sid in ("2", "3", "4", "4c", "5", "6", "7", "8"):
    rel = ".softhouse/reviews/t47-probe/t47_edit_%s.py" % sid
    pre = subprocess.check_output(
        ["git", "-C", REPO, "show", "%s:%s" % (FORK, rel)]).decode("utf-8")
    post = io.open("%s/%s" % (REPO, rel), encoding="utf-8").read()
    a, b = pairs(pre), pairs(post)
    ok = (a == b) and a
    print("t47_edit_%-3s pre-fix pairs %d  post-fix pairs %d  %s"
          % (sid, len(a), len(b), "IDENTICAL" if ok else "*** DIFFER ***"))
    if not ok:
        bad += 1
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print("   pair %d differs" % i)
print("\nscripts whose edit text changed: %d (expected 0)" % bad)
sys.exit(1 if bad else 0)
