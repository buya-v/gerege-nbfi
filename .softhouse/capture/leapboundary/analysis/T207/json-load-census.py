#!/usr/bin/env python3
"""T207 -- re-measure the `json.load(...)` / `json.loads(...)` population, BOTH TERMS.

  python3 .softhouse/capture/leapboundary/analysis/T207/json-load-census.py [repo-root]

WHY THIS EXISTS
---------------
T185 reported that T175 added **8** `json.load` sites carrying no `parse_float=`, taking a
running count from **193 to 201**.  P-67 says a ratio is only certifiable once BOTH its terms
have been counted; P-69 says a measured claim can go stale inside a single fire.  So this
script re-derives the numerator AND the denominator from the live tree, states the population
it walked, and prints the file list for the T175-added subset so the "+8" is auditable rather
than quoted.

METHOD -- AST, not grep.  `grep -c 'json.load'` cannot tell `json.load(f)` from
`json.load(f, parse_float=str)`, cannot see a call split across lines, and matches the string
"json.load" inside a docstring (this very file would score three hits).  Every figure below
comes from `ast.parse` + `ast.walk`, so a keyword argument is found wherever it sits.

WHAT COUNTS AS A SITE: an `ast.Call` whose callee is the attribute `load` or `loads` on the
bare name `json`.  `json.loads(...)` is included because it is the same hazard: without
`parse_float=`, CPython constructs a binary `float` for every non-integer JSON token.

READ-ONLY.  Writes nothing but stdout.  No float anywhere.
"""
import ast
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def git_tracked_py(root):
    out = subprocess.run(["git", "-C", root, "ls-files", "-z", "*.py"],
                         capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.split("\0") if p)


def sites(root, relpath):
    """-> list of (lineno, callee_text, has_parse_float)."""
    p = os.path.join(root, relpath)
    with open(p, "rb") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=relpath)
    except SyntaxError as exc:
        return None, exc
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not isinstance(f, ast.Attribute) or f.attr not in ("load", "loads"):
            continue
        if not isinstance(f.value, ast.Name) or f.value.id != "json":
            continue
        kw = {k.arg for k in node.keywords if k.arg}
        star = any(k.arg is None for k in node.keywords)   # **kwargs -- cannot decide statically
        found.append((node.lineno, "json." + f.attr, "parse_float" in kw, star))
    return found, None


def main(argv):
    root = os.path.abspath(argv[0]) if argv else os.getcwd()
    if not os.path.isfile(os.path.join(root, "CLAUDE.md")):
        print("ROOT=%s is not the repo root" % root)
        return 9

    files = git_tracked_py(root)
    print("T207 -- json.load/json.loads census, BOTH TERMS (P-67)")
    print("root      : %s" % root)
    print("commit    : %s" % subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                                            capture_output=True, text=True).stdout.strip())
    print()
    print("POPULATION INSPECTED -- stated, not implied:")
    print("  git-tracked *.py files in the whole repo : %d" % len(files))
    under_sh = [f for f in files if f.startswith(".softhouse/")]
    print("    of which under .softhouse/             : %d" % len(under_sh))
    print("    of which elsewhere                     : %d" % (len(files) - len(under_sh)))

    total = with_pf = without_pf = 0
    unparseable = []
    starred = []
    per_file_without = {}
    all_without = []
    for rel in files:
        found, exc = sites(root, rel)
        if found is None:
            unparseable.append((rel, exc))
            continue
        for lineno, callee, has_pf, star in found:
            total += 1
            if star:
                starred.append((rel, lineno, callee))
            if has_pf:
                with_pf += 1
            else:
                without_pf += 1
                per_file_without[rel] = per_file_without.get(rel, 0) + 1
                all_without.append((rel, lineno, callee))

    print()
    print("=" * 96)
    print("BOTH TERMS")
    print("=" * 96)
    print("  json.load / json.loads CALL SITES, total        : %d   <-- the DENOMINATOR" % total)
    print("  ... carrying parse_float=                       : %d" % with_pf)
    print("  ... carrying NO parse_float=                    : %d   <-- the NUMERATOR" % without_pf)
    print("  files that failed to AST-parse (NOT inspected)  : %d" % len(unparseable))
    for rel, exc in unparseable:
        print("      UNPARSEABLE  %s  --  %s" % (rel, exc))
    print("  sites passing **kwargs (undecidable statically) : %d" % len(starred))
    for rel, lineno, callee in starred:
        print("      **kwargs  %s:%d  %s" % (rel, lineno, callee))

    if total == 0:
        print()
        print("  NIL-COVERAGE -- inspected an empty population: zero json.load call sites were")
        print("  found in %d files. Either the population is wrong or the matcher is broken;" % len(files))
        print("  a census that counted nothing is an ERROR, not a clean report (P-35).")
        return 1

    # ----------------------------------------------------------- the T175-added subset
    print()
    print("=" * 96)
    print("THE T175-ADDED SUBSET -- T185 said '8', listed here so the figure is auditable")
    print("=" * 96)
    T175_FILES = [
        ".softhouse/capture/audit-t44/analysis/t44_float_roundtrip_v2.py",
        ".softhouse/capture/audit-t44/analysis/T175-red/census.py",
        ".softhouse/capture/leapboundary/analysis/T175-red/measure-other-sites.py",
        ".softhouse/capture/leapboundary/analysis/T175-red/drive-red.py",
        ".softhouse/capture/leapboundary/analysis/T175-red/field-census.py",
        ".softhouse/capture/leapboundary/analysis/T175-red/plant.py",
        ".softhouse/capture/leapboundary/analysis/T175-red/show-sites.py",
        ".softhouse/capture/leapboundary/analysis/T175-red/swallow-census.py",
    ]
    sub = 0
    for rel in T175_FILES:
        n = per_file_without.get(rel, 0)
        exists = os.path.isfile(os.path.join(root, rel))
        print("  %-3s %s%s" % (n, rel, "" if exists else "   (ABSENT)"))
        sub += n
    print("  T175-authored files, sites with NO parse_float  : %d" % sub)

    print()
    print("=" * 96)
    print("TOP FILES BY UNGUARDED SITE COUNT (the tail T145 owns, not T207)")
    print("=" * 96)
    for rel, n in sorted(per_file_without.items(), key=lambda kv: (-kv[1], kv[0]))[:15]:
        print("  %-4d %s" % (n, rel))
    print("  ... %d file(s) carry at least one unguarded site in total"
          % len(per_file_without))

    # ----------------------------------------------------------- the two named sites
    print()
    print("=" * 96)
    print("T207's OWN TWO NAMED SITES (F-2) -- measure-other-sites.py on the money-delta path")
    print("=" * 96)
    for rel in (".softhouse/capture/leapboundary/analysis/T175-red/measure-other-sites.py",
                ".softhouse/capture/leapboundary/analysis/T207/measure-other-sites-v2.py"):
        if not os.path.isfile(os.path.join(root, rel)):
            print("  (absent: %s)" % rel)
            continue
        found, exc = sites(root, rel)
        print("  %s" % rel)
        for lineno, callee, has_pf, star in found:
            print("      line %-4d %-11s parse_float=%s" % (lineno, callee, "YES" if has_pf else "NO"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
