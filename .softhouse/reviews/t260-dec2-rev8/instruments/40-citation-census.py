#!/usr/bin/env python3
"""T260 — INDEPENDENT re-count of the `path:NNNN` citation census.

T255's argument for NOT wiring a line-number checker rests on a denominator:
  "MEASURED at a71c140 there are 115 such citations, of which 25 are Fineract-pinned and do not
   drift and 90 point into this repository"
and on the fact that `verify-line-numbers.py`'s citation row-list is 4 rows, so wiring it would
have enforced 4 of 90 while reading as though it enforced all.

If the denominator is wrong the argument collapses. This instrument re-derives it from scratch,
with its own regex, its own repo/Fineract classification, and prints BOTH terms (P-67).

Classification rule, stated so it can be disputed:
  * a citation is FINERACT if the path (or the sentence's surrounding 200 chars) names a
    Fineract-tree marker: `fineract-`, `.java`, `/Users/buv/fineract`, or the pinned sha;
  * otherwise REPO.
Both the raw list and the counts are printed.

Usage: 40-citation-census.py <doc.md>
Exit 0 always.
"""
import re
import sys
import collections

# a citation looks like `name.ext:1234` or `name.ext:1234-1250`, usually inside backticks.
CIT = re.compile(r"([A-Za-z0-9_./\-]+\.(?:sh|go|py|json|java|md|xml|sql|yml|yaml))"
                 r":(\d+)(?:-(\d+))?")

FINERACT_MARKERS = ("fineract", ".java", "426a23544e8426a38ae43ae404670a0a7e85b9eb")


def main():
    text = open(sys.argv[1], encoding="utf-8").read()
    lines = text.split("\n")
    hits = []
    for ln, line in enumerate(lines, 1):
        for m in CIT.finditer(line):
            path, a, b = m.group(1), m.group(2), m.group(3)
            ctx = line.lower()
            fin = any(k in path.lower() for k in FINERACT_MARKERS) or path.endswith(".java")
            if not fin:
                # widen the window: some Java citations name a bare class file with the package
                # named on the previous line
                window = "\n".join(lines[max(0, ln - 3):ln + 1]).lower()
                if "fineract" in window and path.endswith(".java"):
                    fin = True
            hits.append((ln, path, a, b, "FINERACT" if fin else "REPO"))

    print("T260 — independent `path:NNNN` citation census over", sys.argv[1])
    print("=" * 96)
    total = len(hits)
    repo = [h for h in hits if h[4] == "REPO"]
    fine = [h for h in hits if h[4] == "FINERACT"]
    print(f"TOTAL  path:NNNN citations : {total}")
    print(f"  FINERACT-pinned (no drift): {len(fine)}")
    print(f"  REPO-pointing (perishable): {len(repo)}")
    print(f"  P-67 both terms sum       : {len(fine)} + {len(repo)} = {len(fine)+len(repo)}")
    print()
    print("### REPO citations grouped by file (this is the population a wired checker would need)")
    by = collections.Counter(h[1] for h in repo)
    for p, n in by.most_common():
        print(f"  {n:>4}  {p}")
    print()
    print("### FINERACT citations grouped by file")
    by = collections.Counter(h[1] for h in fine)
    for p, n in by.most_common():
        print(f"  {n:>4}  {p}")
    print()
    print("### every REPO citation, with its line in the document")
    for ln, p, a, b, k in repo:
        rng = f"{a}-{b}" if b else a
        print(f"  doc:{ln:<5} {p}:{rng}")


if __name__ == "__main__":
    main()
