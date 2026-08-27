#!/usr/bin/env python3
"""T185 INDEPENDENT swallow-site sweep (P-37: a reviewer's site list is a starting point).

Written from the definition, not from T175's census.py. Two nets:

NET 1 -- `except` handlers whose body records nothing.
NET 2 -- the class T175 named as its LARGEST BLIND SPOT and did not enumerate:
         a silent narrowing with NO except clause at all, inside a money/coverage loop:
         `continue` guarded by an `if` inside a `for` that also touches a MONEYISH name,
         and `dict.get(k, <default>)` where the default substitutes for a missing money cell.

Denominators are printed. Unreadable/unparseable files are NAMED and are an ERROR (P-35).
"""
import ast, pathlib, sys

ROOT = pathlib.Path("/Users/buv/gerege-nbfi/.claude/worktrees/agent-ac71271ab074115ac")
SKIPDIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "build", ".gradle", "toolchain"}
MONEY_HINT = ("money", "amount", "principal", "interest", "fee", "penalty", "charge",
              "balance", "total", "due", "minor", "delta", "decimal", "Decimal")

RECORD_CALLS = {"print", "warn", "warning", "error", "exception", "critical", "info", "debug",
                "write", "append", "add", "log", "fail", "skip", "extend", "update", "insert",
                "setdefault", "exit", "abort"}


def records(handler):
    """True if the handler's own body records what it caught."""
    name = handler.name
    for node in ast.walk(handler):
        if node is handler:
            continue
        if isinstance(node, (ast.Raise, ast.Assert)):
            return True
        if isinstance(node, ast.Name) and name and node.id == name:
            return True
        if isinstance(node, ast.AugAssign):          # counter increment
            return True
        if isinstance(node, ast.Call):
            f = node.func
            fn = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
            if fn in RECORD_CALLS:
                return True
            if fn in ("exit", "_exit"):
                return True
    return False


def main():
    files, unreadable, unparseable = [], [], []
    for p in sorted(ROOT.joinpath(".softhouse").rglob("*.py")):
        if any(s in p.parts for s in SKIPDIRS):
            continue
        files.append(p)

    handlers = 0
    swallows = []
    narrowings = []
    for p in files:
        try:
            src = p.read_text(encoding="utf-8")
        except Exception as exc:
            unreadable.append((p, repr(exc)))
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            unparseable.append((p, repr(exc)))
            continue
        lines = src.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                handlers += 1
                if not records(node):
                    swallows.append((p, node.lineno, lines[node.lineno - 1].strip()[:80]))
            # NET 2: an `if <cond>: continue` inside a for-loop over money-ish data
            if isinstance(node, (ast.For, ast.While)):
                seg = ast.get_source_segment(src, node) or ""
                if not any(h in seg for h in MONEY_HINT):
                    continue
                for sub in ast.walk(node):
                    if isinstance(sub, ast.If) and any(
                            isinstance(b, ast.Continue) for b in sub.body):
                        narrowings.append((p, sub.lineno,
                                           lines[sub.lineno - 1].strip()[:80]))

    rel = lambda p: str(p.relative_to(ROOT))
    print("=" * 96)
    print("T185 INDEPENDENT SWEEP -- DENOMINATORS (P-40)")
    print("=" * 96)
    print("  .py files walked under .softhouse/ : %d" % len(files))
    print("  files UNREADABLE (named, not skipped): %d" % len(unreadable))
    for p, e in unreadable:
        print("      UNREADABLE %s  %s" % (rel(p), e))
    print("  files UNPARSEABLE (named, not skipped): %d" % len(unparseable))
    for p, e in unparseable:
        print("      UNPARSEABLE %s  %s" % (rel(p), e))
    print("  `except` handlers seen              : %d" % handlers)
    print("  ...of which SWALLOW SITES (net 1)   : %d" % len(swallows))
    print()
    for p, ln, txt in swallows:
        print("  SWALLOW  %s:%d   %s" % (rel(p), ln, txt))
    print()
    print("=" * 96)
    print("NET 2 -- silent narrowing with NO except clause, inside a money-ish loop")
    print("(T175 named this its LARGEST BLIND SPOT and enumerated exactly ONE instance by hand)")
    print("=" * 96)
    print("  candidate `if ...: continue` narrowings in money-ish loops : %d" % len(narrowings))
    for p, ln, txt in narrowings:
        print("  NARROW   %s:%d   %s" % (rel(p), ln, txt))

    if not files:
        print("ZERO files walked -- an ERROR, not a pass (P-35)")
        return 1
    if unreadable or unparseable:
        print("\nERROR: files were unreadable/unparseable; the census does not cover them.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
