#!/usr/bin/env python3
"""T145 json.load census -- independently written (P-33), not derived from T185/T207 code.

Counts, over a STATED population of tracked *.py files, every syntactic call to
json.load / json.loads (and `from json import load` aliases) and classifies each as
GUARDED (a parse_float= keyword is present on that call node) or UNGUARDED.

No money value is computed here. The only numbers are counts of source constructs,
so this instrument is itself inside the first non-negotiable trivially: it never
constructs a number from a money literal at all.

The selector is PRINTED beside every figure, so a figure never travels without the
thing that produced it (P-67 "a figure restated is a figure that rots",
P-69 "re-measure at dispatch"). "Not found" is a statement about the search.
"""
import ast
import json
import os
import subprocess
import sys


def population(root):
    out = subprocess.run(
        ["git", "ls-files", "--", ".softhouse"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout.split("\n")
    return sorted(p for p in out if p.endswith(".py"))


class V(ast.NodeVisitor):
    def __init__(self, path, src):
        self.path = path
        self.src = src.split("\n")
        self.hits = []
        self.aliases = set()

    def visit_ImportFrom(self, n):
        if n.module == "json":
            for a in n.names:
                if a.name in ("load", "loads"):
                    self.aliases.add(a.asname or a.name)
        self.generic_visit(n)

    def _name(self, f):
        if isinstance(f, ast.Attribute) and f.attr in ("load", "loads"):
            v = f.value
            if isinstance(v, ast.Name) and v.id in ("json", "simplejson"):
                return "%s.%s" % (v.id, f.attr)
        if isinstance(f, ast.Name) and f.id in self.aliases:
            return "json.%s" % f.id
        return None

    def visit_Call(self, n):
        nm = self._name(n.func)
        if nm:
            kw = set(k.arg for k in n.keywords if k.arg)
            line = self.src[n.lineno - 1].strip() if n.lineno - 1 < len(self.src) else ""
            self.hits.append({
                "file": self.path,
                "line": n.lineno,
                "call": nm,
                "guarded": "parse_float" in kw,
                "kwargs": sorted(kw),
                "src": line[:160],
            })
        self.generic_visit(n)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    files = population(root)
    hits, unparsable = [], []
    for f in files:
        p = os.path.join(root, f)
        try:
            src = open(p, encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except (SyntaxError, OSError) as e:
            unparsable.append((f, str(e)))
            continue
        v = V(f, src)
        v.visit(tree)
        hits.extend(v.hits)

    ung = [h for h in hits if not h["guarded"]]
    g = [h for h in hits if h["guarded"]]
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True).stdout.strip()

    print("SELECTOR (population): git ls-files -- .softhouse | grep '\\.py$'")
    print("SELECTOR (sites):      ast.parse -> ast.Call whose func is json.load/json.loads")
    print("                       (or a `from json import load[s]` alias); GUARDED iff a")
    print("                       parse_float= keyword is present on that call node.")
    print("REV: %s" % rev)
    print()
    print("DENOMINATOR  tracked .py files under .softhouse : %d" % len(files))
    print("             of which unparsable by ast.parse   : %d" % len(unparsable))
    for f, e in unparsable:
        print("               ! %s: %s" % (f, e))
    print("TOTAL        json.load/loads call sites          : %d" % len(hits))
    print("  GUARDED    (parse_float= present)              : %d   in %d files"
          % (len(g), len(set(h["file"] for h in g))))
    print("  UNGUARDED  (no parse_float=)                   : %d   in %d files"
          % (len(ung), len(set(h["file"] for h in ung))))
    print("NUMERATOR (files with >=1 unguarded site)        : %d of %d"
          % (len(set(h["file"] for h in ung)), len(files)))
    print()
    if "--sites" in sys.argv:
        for h in sorted(ung, key=lambda x: (x["file"], x["line"])):
            print("UNGUARDED %s:%d  %s" % (h["file"], h["line"], h["src"]))
    if "--json" in sys.argv:
        dest = sys.argv[sys.argv.index("--json") + 1]
        with open(dest, "w") as fh:
            json.dump({"rev": rev, "files": len(files), "hits": hits}, fh, indent=1)
    return 0


sys.exit(main())
