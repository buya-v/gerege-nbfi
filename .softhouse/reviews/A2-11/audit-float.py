#!/usr/bin/env python3
"""A2-11 (d) — P-25 float audit of the scripts A2-7 ADDED, plus the whole A2 capture rig.

P-40: this enumerator COUNTS WHAT IT SKIPS and names it. There is no bare
`except: continue` anywhere; a file that cannot be parsed is REPORTED, not dropped.

It parses each file with the `ast` module (not regex) so that a `json.load` reached
through an alias or a nested call is still seen, and reports:
  - every json.load / json.loads call and whether it carries parse_float=
  - every float literal and every `float(` call
  - every use of the `decimal` module
"""
import os
import ast
import subprocess
import sys
from pathlib import Path

# T357 REPAIR -- was a hard-coded absolute path into the worktree
#   /Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da
# which was RETIRED, so this script aborted with a traceback in every later checkout
# and the committed transcript stopped being re-derivable from the script that made
# it. Derived from __file__ instead: this file sits three levels below the checkout
# root, under reviews/A2-11, so parents[3] IS that root. In the ORIGINAL worktree it
# resolved to agent-a3ac3d56d665ff7da, so the substitution is OUTPUT-NEUTRAL there --
# it restores the evidence rather than altering it, and that claim is MEASURED in
# .softhouse/capture/t357-a2-11-section1-red/ (BEFORE/AFTER, and a diff against the
# committed transcript), not asserted. A2_11_ROOT overrides for a cross-checkout run.
ROOT = Path(os.environ.get("A2_11_ROOT") or Path(__file__).resolve().parents[3])
CAP = ROOT / ".softhouse/capture/tierA-a2"
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
BRANCH = "softhouse/A2-7-capture-mandatory-accounts"

added = subprocess.run(
    ["git", "-C", str(ROOT), "diff", "--name-only", "--diff-filter=A", f"{FORK}...{BRANCH}"],
    capture_output=True, text=True, check=True).stdout.split()
a2_7_py = sorted(p for p in added if p.endswith(".py"))
print("=== files A2-7 ADDED that are Python (from the literal fork sha, three dots) ===")
for p in a2_7_py:
    print("   " + p)
print()


class Visit(ast.NodeVisitor):
    # Matching the BARE names `load`/`loads` as well as `json.load` catches a load
    # reached through an alias — but it also matches a call to a LOCAL helper the file
    # itself defines (analyze7.py and show.py both define `def load(...)` that wraps
    # json.load WITH parse_float). `local_defs` is collected first so those calls are
    # attributed to the wrapper, not counted as naked loads. Stated because the first
    # run of this auditor reported three false positives on exactly that shape.
    def __init__(self, local_defs):
        self.local_defs = local_defs
        self.loads = []       # (line, name, has_parse_float, value)
        self.floats = []      # (line, literal)
        self.floatcalls = []  # line
        self.decimal = False

    def visit_Call(self, node):
        name = None
        f = node.func
        if isinstance(f, ast.Attribute):
            name = f.attr
            if isinstance(f.value, ast.Name):
                name = f.value.id + "." + f.attr
        elif isinstance(f, ast.Name):
            name = f.id
        if name in ("json.load", "json.loads") or (name in ("load", "loads") and name not in self.local_defs):
            has = any(k.arg == "parse_float" for k in node.keywords)
            # what it is set to
            val = None
            for k in node.keywords:
                if k.arg == "parse_float":
                    val = ast.unparse(k.value)
            self.loads.append((node.lineno, name, has, val))
        if name == "float":
            self.floatcalls.append(node.lineno)
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, float):
            self.floats.append((node.lineno, repr(node.value)))
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            if a.name.split(".")[0] == "decimal":
                self.decimal = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] == "decimal":
            self.decimal = True
        self.generic_visit(node)


def audit(paths, label):
    print("=== %s ===" % label)
    bad = []
    unparseable = []
    total_loads = 0
    for rel in paths:
        p = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
        try:
            tree = ast.parse(p.read_bytes().decode("utf-8"), filename=str(p))
        except Exception as exc:                      # NOT swallowed — reported (P-40)
            unparseable.append((rel, repr(exc)))
            continue
        local_defs = {n.name for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        v = Visit(local_defs)
        v.visit(tree)
        total_loads += len(v.loads)
        naked = [l for l in v.loads if not l[2]]
        flags = []
        if naked:
            flags.append("json.load WITHOUT parse_float at lines " + ",".join(str(l[0]) for l in naked))
        if v.floats:
            flags.append("FLOAT LITERAL at " + ",".join("%d:%s" % f for f in v.floats))
        if v.floatcalls:
            flags.append("float() call at " + ",".join(str(x) for x in v.floatcalls))
        status = "CLEAN" if not flags else "FLAG"
        print("  %-5s %-58s loads=%d decimal_imported=%s %s"
              % (status, rel.replace(".softhouse/capture/tierA-a2/", "").replace(".softhouse/", ""),
                 len(v.loads), v.decimal, "; ".join(flags)))
        for l in v.loads:
            if l[2]:
                print("            line %-5d %s(parse_float=%s)" % (l[0], l[1], l[3]))
        if flags:
            bad.append(rel)
    print("  --- enumerated %d files, %d json.load call sites, %d FLAGGED, %d UNPARSEABLE"
          % (len(paths), total_loads, len(bad), len(unparseable)))
    for rel, exc in unparseable:
        print("      UNPARSEABLE (named, not skipped): %s  %s" % (rel, exc))
    print()
    return bad


bad1 = audit(a2_7_py, "(d) the Python A2-7 ADDED — this is the task's question")

all_py = sorted(str(p.relative_to(ROOT)) for p in CAP.rglob("*.py"))
bad2 = audit(all_py, "context: EVERY .py in the A2 capture rig (A2-7's and everyone else's)")

print("SUMMARY")
print("  A2-7-added Python with a float defect: %d %s" % (len(bad1), bad1))
print("  whole-rig Python with a float defect : %d %s" % (len(bad2), bad2))
sys.exit(0)
