#!/usr/bin/env python3
"""T471 -- CLAIM 3's occurrence cardinal, measured with the CENSUS'S OWN semantics.

T465 states "17 rows = 43 quoted literals; 43 removed, 0 remain". A naive count of quoted
literals mentioning the lock path gives a DIFFERENT number (69 at base), because the census
does two things before it classifies: it TRIMS each literal to its `<dot>/`-rooted tail, and it
throws whitespace-carrying tails into PROSE. So the only defensible way to check the cardinal is
to run the census's own `LITERAL_RE`, `classify()` and trim over the tree -- which is what this
does, by IMPORTING the census module out of the materialised tree under test rather than
re-implementing it (a re-implementation would prove agreement with a model, not with the file).

COUNTED: occurrences whose trimmed tail is CONCRETE and whose punctuation-stripped form is the
lock path. Those, and only those, are the occurrences that flip DEAD when the lock leaves the
index -- i.e. the population the repair had to empty.

NO REAL REPO PATH IS SPELT AS A LITERAL HERE (P-103): assembled from $S at run time.
Probe line: T471-OCCURRENCES:
"""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

PROBE = "T471-OCCURRENCES:"
DOT = "." + "softhouse"
LOCKPATH = DOT + "/" + "LOCK"


def load_census(tree: Path):
    p = tree / DOT / "capture" / "t316-dead-path-guards" / "census_dead_paths.py"
    if not p.is_file():
        print("ERROR: no census in %s -- REFUSING (exit 2)" % tree, file=sys.stderr)
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location("t471_census_%s" % abs(hash(str(tree))), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in ("LITERAL_RE", "classify", "TRAILING_PUNCT"):
        if not hasattr(mod, attr):
            print("ERROR: the census at %s has no %s -- its shape changed. REFUSING." % (p, attr),
                  file=sys.stderr)
            raise SystemExit(2)
    return mod


def corpus(tree: Path):
    r = subprocess.run(["git", "ls-files", DOT + "/*.py", DOT + "/*.sh"],
                       cwd=str(tree), capture_output=True, text=True)
    if r.returncode != 0:
        print("ERROR: git ls-files failed in %s" % tree, file=sys.stderr)
        raise SystemExit(2)
    files = [f for f in r.stdout.splitlines() if f.strip()]
    if not files:
        print("ERROR: EMPTY corpus in %s -- a selector failure, not a clean tree." % tree,
              file=sys.stderr)
        raise SystemExit(2)
    return files


def measure(tree: Path, label: str):
    c = load_census(tree)
    files = corpus(tree)
    per_file = {}
    total = 0
    for rel in files:
        try:
            text = (tree / rel).read_text(errors="replace")
        except OSError as exc:
            print("ERROR: unreadable corpus member %s: %s" % (rel, exc), file=sys.stderr)
            raise SystemExit(2)
        hits = []
        for m in c.LITERAL_RE.finditer(text):
            lit = m.group(2)
            idx = lit.find(DOT + "/")
            path = lit[idx:]
            if c.classify(path) != "CONCRETE":
                continue
            if path == LOCKPATH or path.rstrip(c.TRAILING_PUNCT) == LOCKPATH:
                hits.append(path)
        if hits:
            per_file[rel] = hits
            total += len(hits)
    print("=== %s  tree=%s" % (label, tree))
    print("    corpusFiles=%d" % len(files))
    for f in sorted(per_file):
        vals = sorted(set(per_file[f]))
        print("    %-72s occ=%d  values=%s" % (f, len(per_file[f]), vals))
    print("    FILES=%d OCCURRENCES=%d ROWS=%d"
          % (len(per_file), total, len({(f, v) for f, vs in per_file.items() for v in vs})))
    return per_file, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-tree", required=True)
    ap.add_argument("--head-tree", required=True)
    a = ap.parse_args()
    bper, bocc = measure(Path(a.base_tree), "BASE")
    print()
    hper, hocc = measure(Path(a.head_tree), "HEAD")
    print()
    brows = {(f, v) for f, vs in bper.items() for v in vs}
    hrows = {(f, v) for f, vs in hper.items() for v in vs}
    print("ROWS ONLY AT BASE (%d):" % len(brows - hrows))
    for f, v in sorted(brows - hrows):
        print("    %-72s | %s" % (f, v))
    print("ROWS ONLY AT HEAD (%d):" % len(hrows - brows))
    for f, v in sorted(hrows - brows):
        print("    %-72s | %s" % (f, v))
    print("%s baseFiles=%d baseOccurrences=%d baseRows=%d headFiles=%d headOccurrences=%d "
          "headRows=%d removedOccurrences=%d remain=%d"
          % (PROBE, len(bper), bocc, len(brows), len(hper), hocc, len(hrows), bocc - hocc, hocc))


if __name__ == "__main__":
    main()
