#!/usr/bin/env python3
"""T167 sibling census: t47_edit_1.py was ONE OF NINE scripts written from the
same template in the same directory, against the same ratified DEC-1 ADR and
against the FROZEN adapter contract.  T167's brief covers one of them.  This
census measures the other eight so the follow-up carries a measurement rather
than a suspicion.

NOTHING HERE IS EXECUTED.  Every question is answered from the AST and from
string membership in the target files.  Running one of these scripts to find
out what it does is the defect, not the test.

Three questions per file:
  1. Is the write unguarded and non-atomic?   (AST: try/finally/atexit, and the
     shape of the write call)
  2. What does it write?                       (the DOC / GO constant)
  3. WOULD IT WRITE IF RUN TODAY?              (every anchor it must find, and
     whether that anchor is still present exactly once in the live target)

Question 3 is the one that turns a latent hazard into a live one: these scripts
exit before writing when an anchor is missing, so a script whose anchors are all
gone is inert, and a script whose anchors all survive is a loaded gun.
"""
import ast
import glob
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"


def const_target(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if getattr(tgt, "id", "") == name:
                    return ast.unparse(n.value)
    return None


def anchors_of(tree):
    """Every string anchor that GATES the write, with the count of anchors this
    census could not resolve statically.

    Two gate shapes exist in this family:
      * `rep("literal", "replacement")` - a helper that sys.exit()s unless the
        anchor occurs exactly once;
      * `n = s.count(old); if n != 1: sys.exit(...)` - the same check written
        out, with the anchor held in a module-level variable.
    Both are collected.  `os.replace()` and the `.replace()` inside the helper
    are NOT anchors and are excluded.  Anything left unresolved is counted as
    UNDETERMINED rather than dropped: dropping it would understate the risk,
    which is the exact direction of error this whole task exists to correct."""
    env = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name):
            try:
                v = ast.literal_eval(n.value)
            except Exception:
                continue
            if isinstance(v, str):
                env[n.targets[0].id] = v

    def resolve(a):
        if isinstance(a, ast.Name):
            return env.get(a.id)
        try:
            v = ast.literal_eval(a)
        except Exception:
            return None
        return v if isinstance(v, str) else None

    # Only MODULE-LEVEL gates count.  The `s.count(old)` inside the rep()
    # helper takes a parameter, not an anchor, and including it would report a
    # spurious UNDETERMINED for every file in the family.
    nodes = []
    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef,
                            ast.ClassDef)):
            continue
        nodes.extend(ast.walk(top))
    out, undet = [], 0
    for n in nodes:
        if not isinstance(n, ast.Call) or not n.args:
            continue
        fn = n.func
        gate = False
        if isinstance(fn, ast.Name) and fn.id in ("rep", "sub", "replace_one"):
            gate = True
        if isinstance(fn, ast.Attribute) and fn.attr == "count":
            gate = True
        if not gate:
            continue
        v = resolve(n.args[0])
        if isinstance(v, str) and len(v) > 40:
            out.append((n.lineno, v))
        else:
            undet += 1
    # the same anchor can be both rep()'d and count()'d; de-duplicate by text
    seen, uniq = set(), []
    for ln, v in out:
        if v not in seen:
            seen.add(v)
            uniq.append((ln, v))
    return uniq, undet


adr = io.open(os.path.join(REPO, ADR_REL), encoding="utf-8").read()
go_path = os.path.join(REPO, GO_REL)
go = io.open(go_path, encoding="utf-8").read() if os.path.exists(go_path) else ""

print("target 1: %s   (%d bytes)" % (ADR_REL, len(adr)))
print("target 2: %s   (%d bytes)" % (GO_REL, len(go)))
print("\nBoth are hard `user` gates to amend: CLAUDE.md, \"Any change to a "
      "ratified DEC-n\n or the frozen adapter contract\".\n")
print("%-16s %-6s %-6s %-30s %-9s %s"
      % ("file", "try", "atomic", "writes", "anchors", "live anchors"))
print("-" * 100)

for p in sorted(glob.glob(os.path.join(
        REPO, ".softhouse/reviews/t47-probe/t47_edit_*.py"))):
    src = io.open(p, encoding="utf-8").read()
    tree = ast.parse(src)
    tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
    atomic = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "replace"
                 and getattr(n.func.value, "id", "") == "os"
                 for n in ast.walk(tree))
    doc = const_target(tree, "DOC")
    goc = const_target(tree, "GO")
    which = doc or goc or "(no DOC/GO constant)"
    target = go if goc and not doc else adr
    tgt_name = GO_REL if (goc and not doc) else ADR_REL
    anc, undet = anchors_of(tree)
    live = [ln for ln, a in anc if target.count(a) == 1]
    short = "contract.go" if tgt_name == GO_REL else "DEC-1 ADR"
    note = ""
    if anc and len(live) == len(anc) and not undet:
        note = "   <<< ALL ANCHORS LIVE - would rewrite the target TODAY"
    elif undet:
        note = "   (%d anchor(s) not statically resolvable - UNDETERMINED)" % undet
    print("%-16s %-6d %-6s %-30s %-9d %d%s"
          % (os.path.basename(p), len(tries), atomic, short, len(anc),
             len(live), note))

print("""
Reading:
  try     - count of ast.Try nodes.  0 means no guard of any kind.
  atomic  - does the file contain an os.replace() call.
  anchors - how many string anchors the script must find before it writes.
  live    - how many of those are still present EXACTLY ONCE in the live
            target.  live < anchors means the script exits before its write;
            live == anchors means it runs to completion and rewrites a
            ratified/frozen artefact in place, with no authorisation.""")
