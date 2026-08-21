#!/usr/bin/env python3
"""T178 OUT-OF-SCOPE measurement: the nine `t47_edit_*.py` files are NOT the
population.

T178's brief scopes it to `.softhouse/reviews/t47-probe/t47_edit_{1..8}.py`
plus `t47_edit_4c.py`.  This script asks the same question of the whole
`.softhouse/` tree, because "we hardened the nine we were told about" is a
statement about the brief and not about the repository, and P-40 requires a
task to count what it did not cover.

It is READ-ONLY and executes nothing.  Every answer comes from the AST and
from string membership in the two live protected artefacts.  Running one of
these scripts to find out what it does is the defect, not the test.

Reported per file: `try` node count, whether it contains an `os.replace`
(atomic) call, which protected artefact it names, how many string anchors gate
its write, how many of those are still present EXACTLY ONCE in the live
artefact, how many anchors could not be resolved statically (UNDETERMINED,
counted and never dropped), and how many write sites it has.

A file with `try 0`, `atomic False`, at least one write site, and ALL anchors
live is a LIVE gate bypass: run it and a ratified DEC-n or the frozen adapter
contract is amended in place, unauthorised, non-atomically.

This script writes nothing and is safe to re-run at any time.  It is the
tripwire for the population T178 could not fix under its own scope guard."""
import ast
import hashlib
import io
import os
import sys

REPO = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0d0a5c20aad048db"
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"
adr = io.open(os.path.join(REPO, ADR_REL), encoding="utf-8").read()
go = io.open(os.path.join(REPO, GO_REL), encoding="utf-8").read()

rows, unparsed = [], []
for root, dirs, files in os.walk(os.path.join(REPO, ".softhouse")):
    dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, REPO)
        try:
            src = io.open(p, encoding="utf-8").read()
            tree = ast.parse(src)
        except (IOError, OSError, SyntaxError, UnicodeDecodeError) as e:
            unparsed.append("%s: %s" % (rel, e))
            continue
        # does it name a protected artefact at all?
        if ADR_REL not in src and GO_REL not in src:
            continue
        writes = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                nm = f.id if isinstance(f, ast.Name) else (
                    f.attr if isinstance(f, ast.Attribute) else None)
                if nm == "open" and len(n.args) > 1:
                    m = n.args[1]
                    if isinstance(m, ast.Constant) and isinstance(m.value, str) \
                            and ("w" in m.value or "a" in m.value):
                        writes.append(n.lineno)
                elif nm in ("write_text", "write_bytes"):
                    writes.append(n.lineno)
        if not writes:
            continue
        atomic = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "replace"
                     and getattr(n.func.value, "id", "") == "os"
                     for n in ast.walk(tree))
        tries = len([n for n in ast.walk(tree) if isinstance(n, ast.Try)])
        tgt = GO_REL if (GO_REL in src and ADR_REL not in src) else ADR_REL
        target = go if tgt == GO_REL else adr
        # anchors: rep()/sub()/count()-style gates.  Module-level string
        # constants are resolved, because this family holds its anchors in
        # `ANCHOR = "..."` / `old = """..."""` as often as inline.  Anything
        # still unresolved is COUNTED as undetermined, never dropped (P-40).
        env = {}
        for n in tree.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                    and isinstance(n.targets[0], ast.Name) \
                    and isinstance(n.value, ast.Constant) \
                    and isinstance(n.value.value, str):
                env[n.targets[0].id] = n.value.value
        anc, undet = [], 0
        for top in tree.body:
            if isinstance(top, (ast.FunctionDef, ast.ClassDef)):
                continue
            for n in ast.walk(top):
                if isinstance(n, ast.Call) and n.args:
                    f = n.func
                    if (isinstance(f, ast.Name)
                            and f.id in ("rep", "sub", "replace_one")) or \
                       (isinstance(f, ast.Attribute) and f.attr == "count"):
                        a = n.args[0]
                        v = None
                        if isinstance(a, ast.Constant) \
                                and isinstance(a.value, str):
                            v = a.value
                        elif isinstance(a, ast.Name):
                            v = env.get(a.id)
                        if isinstance(v, str) and len(v) > 20:
                            anc.append(v)
                        else:
                            undet += 1
        anc = list(dict.fromkeys(anc))
        live = [a for a in anc if target.count(a) == 1]
        rows.append((rel, tries, atomic, tgt, len(anc), len(live), len(writes), undet))

rows.sort(key=lambda r: (-(r[4] > 0 and r[4] == r[5] and not r[7]), r[0]))
print("%-52s %-5s %-6s %-12s %-7s %-5s %-6s %s"
      % ("file", "try", "atomic", "target", "anchors", "live", "undet",
         "write sites"))
print("-" * 118)
live_now = 0
undet_files = 0
for rel, tries, atomic, tgt, na, nl, nw, ud in rows:
    flag = ""
    if na and na == nl and not ud:
        flag = "  <<< ALL ANCHORS LIVE TODAY"
        live_now += 1
    if ud:
        undet_files += 1
    print("%-52s %-5d %-6s %-12s %-7d %-5d %-6d %d%s"
          % (rel, tries, atomic, "contract.go" if tgt == GO_REL else "DEC-1",
             na, nl, ud, nw, flag))
print("\nfiles that write AND name a protected artefact: %d" % len(rows))
print("of those, ALL anchors live today:               %d" % live_now)
print("files with at least one UNDETERMINED anchor:     %d" % undet_files)
print("files that could not be parsed (counted, not dropped): %d%s"
      % (len(unparsed), (" - " + "; ".join(unparsed)) if unparsed else ""))
