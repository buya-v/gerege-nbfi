#!/usr/bin/env python3
"""T175 -- RE-DERIVE the Python swallow-site census across the whole repo.

P-37: a reviewer's site list is a STARTING POINT, never the sweep.  T169's P-26 census reported
"PY-SWALLOW: 11 sites" and singled out two as load-bearing.  This re-derives the census from the
tree rather than inheriting it, so the number can be agreed with or disagreed with on evidence.

DEFINITION USED HERE (stated, because the count is a function of it):
  A SWALLOW SITE is an `except ...:` handler whose OWN BODY -- read to its own dedent, so a
  statement belonging to later code is not credited to it -- contains no statement that RECORDS
  what was caught.  A body records if it prints/logs/writes, appends or otherwise stores, raises
  or re-raises, exits, asserts, or increments a counter that is later reported.  A body of only
  `pass` / `continue` / `break` / `return <constant>` records nothing.

  Bare `except:` and `except SomeError:` are both in scope; the narrowness of the clause is a
  different defect (T169's JAVA-NARROW family) and is not what this counts.

DENOMINATORS AND WHAT IS SKIPPED are printed at the end (P-40).

Read-only.  Writes nothing.  Constructs no float.
Usage:  python3 swallow-census.py [repo-root]
"""
import ast
import os
import sys

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", ".gradle",
             "toolchain"}

RECORDING_CALLS = {"print", "warn", "warning", "error", "log", "debug", "info", "exit",
                   "write", "append", "add", "extend", "setdefault", "update", "fail",
                   "bad", "note", "skip", "record", "die", "abort"}


def body_records(node):
    """Does this handler's own body record what it caught?"""
    # A handler that BINDS the exception (`as exc`) and then mentions that name anywhere in its
    # own body is carrying the identity of what it caught forward -- that is a record, even if
    # the call that consumes it has a project-local name this census has never heard of.  Added
    # after the first run flagged four such handlers as swallows, including one of this task's
    # own probes; the classifier was wrong, not the handlers.
    if node.name:
        for st in node.body:
            for sub in ast.walk(st):
                if isinstance(sub, ast.Name) and sub.id == node.name:
                    return True
    for st in node.body:
        for sub in ast.walk(st):
            if isinstance(sub, (ast.Raise, ast.Assert)):
                return True
            if isinstance(sub, ast.AugAssign):        # counter increment
                return True
            if isinstance(sub, ast.Call):
                f = sub.func
                name = getattr(f, "id", None) or getattr(f, "attr", None)
                if name and name.lower() in RECORDING_CALLS:
                    return True
                if name in ("exit", "_exit"):
                    return True
            if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                return True
    return False


def body_shape(node, src_lines):
    return "; ".join(
        src_lines[st.lineno - 1].strip() for st in node.body)[:70]


def main(argv):
    root = os.path.abspath(argv[0]) if argv else os.getcwd()
    files = []
    unreadable = []
    unparseable = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                files.append(os.path.join(dirpath, fn))
    files.sort()

    handlers = 0
    sites = []
    for p in files:
        try:
            src = open(p, encoding="utf-8").read()
        except Exception as exc:
            unreadable.append((p, type(exc).__name__, str(exc)))
            continue
        try:
            tree = ast.parse(src)
        except Exception as exc:
            # NAMED AND COUNTED -- this census refuses to do to itself what it is auditing.
            unparseable.append((p, type(exc).__name__, str(exc)))
            continue
        lines = src.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            handlers += 1
            if body_records(node):
                continue
            clause = "except:" if node.type is None else \
                "except %s:" % ast.get_source_segment(src, node.type)
            sites.append((os.path.relpath(p, root), node.lineno, clause,
                          body_shape(node, lines)))

    print("T175 -- re-derived Python swallow-site census")
    print("root: %s" % root)
    print()
    print("%-4s %-62s %-6s %-26s %s" % ("#", "file", "line", "clause", "body"))
    for i, (f, ln, clause, shape) in enumerate(sites, 1):
        print("%-4d %-62s %-6d %-26s %s" % (i, f, ln, clause, shape))

    print()
    print("=" * 100)
    print("DENOMINATORS (P-40)")
    print("=" * 100)
    print("  .py files walked                      : %d" % len(files))
    print("  .py files UNREADABLE (named below)    : %d" % len(unreadable))
    print("  .py files UNPARSEABLE (named below)   : %d" % len(unparseable))
    print("  except-handlers seen in total         : %d" % handlers)
    print("  ...of which SWALLOW SITES by the definition above : %d" % len(sites))
    for p, t, msg in unreadable:
        print("    UNREADABLE  %s  %s: %s" % (os.path.relpath(p, root), t, msg))
    for p, t, msg in unparseable:
        print("    UNPARSEABLE %s  %s: %s" % (os.path.relpath(p, root), t, msg))
    print()
    print("  WHAT THIS SWEEP STRUCTURALLY CANNOT FIND:")
    print("    * a swallow written in a language other than Python (Java/bash/Go/SQL);")
    print("    * a `try/finally` with no `except` that returns a default;")
    print("    * a handler that RECORDS to a variable nobody ever prints -- it counts as")
    print("      recording here, and is a weaker defect but still one;")
    print("    * a swallow implemented WITHOUT an except clause at all: `dict.get(k, 0)`,")
    print("      `re.match(...) or default`, `glob` matching nothing, a `continue` guarded by")
    print("      an `if` -- the same vacuity with no exception in sight. This is the largest")
    print("      blind spot and no AST net over `except` can close it;")
    print("    * files skipped by directory name: %s" % ", ".join(sorted(SKIP_DIRS)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
