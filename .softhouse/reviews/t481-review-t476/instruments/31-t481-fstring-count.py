#!/usr/bin/env python3
"""T481 -- WHICH READING OF "an interpolation BETWEEN two constants" GIVES T476's 1,033?

T476's §7.1 turns on a narrower count than T472's raw f-string reach: "of the 2,491
f-strings, only 1,033 in 158 files even have an interpolation BETWEEN two constants". The
raw reach (2,491 / 170) reproduces exactly under 30-t481-population.py. The narrow one does
not: the natural reading gives 1,031. This file enumerates four readings and reports each,
so the residual is a definition and not a mystery -- or is recorded as unreproduced.

  python3 31-t481-fstring-count.py <repo> <ref>
"""
import ast
import subprocess
import sys


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("REFUSED: usage: <repo> <ref>\n")
        return 3
    repo, ref = sys.argv[1:3]
    p = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", ref],
                       capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git ls-tree failed\n")
        return 3
    names = [f for f in p.stdout.decode().split("\n") if f.endswith(".py")]
    readings = {
        "A  FormattedValue with a Constant on BOTH sides": None,
        "B  any FormattedValue that is neither first nor last element": None,
        "C  >=1 FormattedValue and >=2 Constants anywhere in the JoinedStr": None,
        "D  >=1 FormattedValue and >=1 Constant before it and >=1 after": None,
    }
    counts = {k: 0 for k in readings}
    files = {k: set() for k in readings}
    total = 0
    for f in names:
        b = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (ref, f)],
                           capture_output=True).stdout.decode("utf-8", "replace")
        try:
            tree = ast.parse(b)
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue
            total += 1
            v = node.values
            a = any(isinstance(v[i], ast.FormattedValue)
                    and isinstance(v[i - 1], ast.Constant)
                    and isinstance(v[i + 1], ast.Constant) for i in range(1, len(v) - 1))
            bb = any(isinstance(v[i], ast.FormattedValue) for i in range(1, len(v) - 1))
            cc = (any(isinstance(x, ast.FormattedValue) for x in v)
                  and sum(1 for x in v if isinstance(x, ast.Constant)) >= 2)
            dd = any(isinstance(v[i], ast.FormattedValue)
                     and any(isinstance(x, ast.Constant) for x in v[:i])
                     and any(isinstance(x, ast.Constant) for x in v[i + 1:])
                     for i in range(len(v)))
            for key, val in (("A  FormattedValue with a Constant on BOTH sides", a),
                             ("B  any FormattedValue that is neither first nor last element", bb),
                             ("C  >=1 FormattedValue and >=2 Constants anywhere in the JoinedStr", cc),
                             ("D  >=1 FormattedValue and >=1 Constant before it and >=1 after", dd)):
                if val:
                    counts[key] += 1
                    files[key].add(f)
    print("  ref: %s   total JoinedStr nodes: %d" % (ref, total))
    for k in sorted(counts):
        print("  %-64s %5d f-strings in %3d files" % (k, counts[k], len(files[k])))
    print()
    print("  T476 publishes 1,033 in 158 files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
