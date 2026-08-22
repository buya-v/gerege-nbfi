#!/usr/bin/env python3
"""T207 -- run T207's OWN AST counter against ARBITRARY REVISIONS, straight out of the object
store, so T185's published table can be REPRODUCED rather than quoted.

  python3 census-at-rev.py <repo-root> <rev> [<rev> ...]

P-33: count with two programs before believing a figure.  Here the second program is T207's
counter and the first is T185's (whose numbers are on `main` in
`.softhouse/reviews/T185-review-t175.md`).  If T207's counter reproduces T185's numbers at
T185's own commits, then the LIVE number this counter reports is directly comparable to
T185's -- and any difference is real drift (P-69), not two instruments disagreeing.
If it does NOT reproduce them, that is recorded as a discrepancy, not smoothed over.

Reads blobs with `git cat-file`; NEVER checks anything out, never touches the worktree.
READ-ONLY.  No float.
"""
import ast
import subprocess
import sys


def run(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, check=True).stdout


def files_at(root, rev):
    out = run(root, "ls-tree", "-r", "-z", "--name-only", rev).decode()
    return sorted(p for p in out.split("\0") if p.endswith(".py"))


def census(root, rev):
    files = files_at(root, rev)
    total = no_pf = 0
    files_with_call = set()
    files_with_gap = set()
    bad = []
    for rel in files:
        try:
            blob = run(root, "show", "%s:%s" % (rev, rel))
        except subprocess.CalledProcessError:
            bad.append((rel, "unreadable blob"))
            continue
        try:
            tree = ast.parse(blob, filename=rel)
        except SyntaxError as exc:
            bad.append((rel, "SyntaxError: %s" % exc))
            continue
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr in ("load", "loads")
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == "json"):
                total += 1
                files_with_call.add(rel)
                if "parse_float" not in {k.arg for k in n.keywords if k.arg}:
                    no_pf += 1
                    files_with_gap.add(rel)
    return len(files), total, no_pf, len(files_with_call), len(files_with_gap), bad


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    root, revs = argv[0], argv[1:]
    print("T207 -- T185's table, RE-RUN with T207's counter (P-33 second program, P-69 drift)")
    print()
    print("  %-14s %-10s %8s %8s %8s %9s %9s"
          % ("rev", "sha", ".py", "sites", "NO p_f", "files w/", "files w/"))
    print("  %-14s %-10s %8s %8s %8s %9s %9s"
          % ("", "", "files", "", "", "a call", "a gap"))
    rows = []
    for rev in revs:
        sha = run(root, "rev-parse", "--short", rev).decode().strip()
        nf, tot, no_pf, fwc, fwg, bad = census(root, rev)
        rows.append((rev, sha, nf, tot, no_pf, fwc, fwg, bad))
        print("  %-14s %-10s %8d %8d %8d %9d %9d" % (rev, sha, nf, tot, no_pf, fwc, fwg))
    print()
    for rev, sha, nf, tot, no_pf, fwc, fwg, bad in rows:
        if bad:
            print("  NOT INSPECTED at %s (%s): %d file(s)" % (rev, sha, len(bad)))
            for rel, why in bad:
                print("      %s  --  %s" % (rel, why))
        else:
            print("  every .py file at %s (%s) was parsed; 0 not inspected." % (rev, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
