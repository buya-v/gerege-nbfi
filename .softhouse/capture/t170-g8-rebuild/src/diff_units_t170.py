#!/usr/bin/env python3
"""T170 — mechanical verdict counts for SCOPE-TABLE-T170.md.

Compares the paragraph-level claim units of the two G-8 blocks BEFORE (a given
revision of gates.md, normally `main`'s) and AFTER (the working tree), and reports:

  * how many BEFORE units survive into AFTER byte-identical (left standing)
  * how many do not (changed or removed)
  * how many AFTER units are new

This is the denominator arithmetic for the rebuild, computed rather than counted by
hand — the whole reason this section has a STANDING RULE is that a hand count in it
has already been wrong.

Usage: diff_units_t170.py <before-gates.md> [after-gates.md]
Output: out/unit-diff-t170.json + counts on stdout
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paragraphs_t170 as P  # noqa: E402


def units(path):
    lines = open(path).read().split("\n")
    idx = {}
    for i, ln in enumerate(lines):
        if ln.startswith(P.START_MAIN):
            idx["ms"] = i
        elif ln.startswith(P.END_MAIN):
            idx["me"] = i
        elif ln.startswith(P.START_NOTICE):
            idx["ns"] = i
    ne = len(lines)
    for i in range(idx["ns"] + 1, len(lines)):
        if lines[i].startswith("## ") and not lines[i].startswith("## G-8"):
            ne = i
            break
    return (P.units_in(lines, idx["ms"], idx["me"], "MAIN")
            + P.units_in(lines, idx["ns"], ne, "NOTICE"))


def main():
    before = units(sys.argv[1])
    after = units(sys.argv[2] if len(sys.argv) > 2
                  else os.path.join(ROOT, ".softhouse/gates.md"))
    atext = {u["text"] for u in after}
    btext = {u["text"] for u in before}
    kept = [u for u in before if u["text"] in atext]
    gone = [u for u in before if u["text"] not in atext]
    new = [u for u in after if u["text"] not in btext]
    res = {
        "before_units": len(before),
        "after_units": len(after),
        "before_units_surviving_byte_identical": len(kept),
        "before_units_changed_or_removed": len(gone),
        "after_units_new": len(new),
        "changed_or_removed": [{"line": u["line"], "block": u["block"],
                                "kind": u["kind"], "text": u["text"][:200]} for u in gone],
        "new": [{"line": u["line"], "block": u["block"], "kind": u["kind"],
                 "text": u["text"][:200]} for u in new],
    }
    dest = os.path.join(ROOT, ".softhouse/capture/t170-g8-rebuild/out/unit-diff-t170.json")
    with open(dest, "w") as f:
        json.dump(res, f, indent=1)
    for k in ("before_units", "after_units", "before_units_surviving_byte_identical",
              "before_units_changed_or_removed", "after_units_new"):
        print("%-42s %d" % (k, res[k]))


if __name__ == "__main__":
    main()
