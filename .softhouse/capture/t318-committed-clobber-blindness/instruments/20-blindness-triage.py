#!/usr/bin/env python3
"""T318 instrument 20 — which cleanliness gates are BLIND to a committed clobber?

Reads instrument 10's census and, for every LOAD-BEARING hit (EXEC-GATE or
PROSE-PROTOCOL), answers two questions:

  Q1  WHICH REPO does the gate interrogate?
        SELF     — this repo (no `-C`, or `-C` into a scratch clone of this repo)
        PINNED   — the pinned reference-oracle checkout (/Users/buv/fineract)
        WORKTREE — `-C "$W"` over a worker worktree of this repo
        OTHER    — anything else / unresolved

  Q2  Is the gate ACCOMPANIED, within +/- WINDOW lines, by a check that would
      SURVIVE a committed clobber — i.e. one that reads a REF rather than the
      index/worktree delta:
        rev-parse HEAD / rev-parse --verify / show-ref / for-each-ref /
        branch --contains / branch --format / reflog / cat-file / merge-base /
        rev-list / a literal 40-hex expected commit

A gate with a REF companion can still see a clobber that COMMITS, because the
commit moves HEAD or adds a ref. A gate with NO ref companion cannot: that is
the FU-T304-2 blind spot, and this instrument counts it.

P-66 binds (patterns.md:1921): *"'NOT FOUND' is a statement about the search,
never about the world."* Every figure below is printed beside its selector, and
the WINDOW is printed because a companion outside the window is invisible to
this instrument and would be scored as blind. That direction of error is
CONSERVATIVE-UNSAFE (over-reports blindness), so the sites it names are
hand-adjudicated in the handoff rather than trusted wholesale.
"""
import json
import os
import re
import subprocess
import sys

WINDOW = 40  # lines either side, printed beside the figure

REF_COMPANION = re.compile(
    r"rev-parse\b|show-ref\b|for-each-ref\b|branch\s+--contains\b|branch\s+--format\b"
    r"|\breflog\b|cat-file\b|merge-base\b|rev-list\b|\bgit\s+log\b|[0-9a-f]{40}"
)
PINNED_HINT = re.compile(r"FINERACT|ORACLE_SRC|PINNED|/Users/buv/fineract|fineract\b", re.I)
DASH_C = re.compile(r"git\s+-C\s+\"?\$?\{?([A-Za-z_][A-Za-z0-9_]*)\}?\"?")


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    census = json.load(open(os.path.join(here, "evidence", "10-census.json")))
    repo = census["repo"]

    rows = []
    cache = {}
    for h in census["hits"]:
        if h["class"] not in ("EXEC-GATE", "PROSE-PROTOCOL"):
            continue
        f = h["file"]
        if f not in cache:
            cache[f] = open(os.path.join(repo, f), encoding="utf-8",
                            errors="replace").read().split("\n")
        lines = cache[f]
        i = h["line"] - 1
        lo, hi = max(0, i - WINDOW), min(len(lines), i + WINDOW + 1)
        window = "\n".join(lines[lo:hi])

        # Q1 -- target repo
        m = DASH_C.search(h["text"])
        if PINNED_HINT.search(h["text"]):
            target = "PINNED"
        elif m and m.group(1) in ("W",):
            target = "WORKTREE"
        elif m:
            target = "SCRATCH-SELF"     # -C into a clone/scratch of THIS repo
        else:
            target = "SELF"

        # Q2 -- ref companion within the window
        has_ref = bool(REF_COMPANION.search(window))

        rows.append({**h, "target": target, "ref_companion": has_ref,
                     "verdict": "COVERED" if has_ref else "BLIND"})

    print(json.dumps({"window_lines": WINDOW,
                      "ref_companion_selector": REF_COMPANION.pattern,
                      "rows": rows}, indent=1))

    e = sys.stderr
    print("=" * 78, file=e)
    print("T318 INSTRUMENT 20 — BLINDNESS TRIAGE OF LOAD-BEARING CLEANLINESS GATES", file=e)
    print("=" * 78, file=e)
    print(f"WINDOW for a ref companion: +/- {WINDOW} lines (printed, per P-66)", file=e)
    print(f"REF-COMPANION SELECTOR: {REF_COMPANION.pattern}", file=e)
    print("-" * 78, file=e)
    grid = {}
    for r in rows:
        grid.setdefault((r["target"], r["verdict"]), []).append(r)
    print(f"{'TARGET REPO':16s} {'BLIND':>7s} {'COVERED':>9s}   {'files':>6s}", file=e)
    for t in ("SELF", "WORKTREE", "SCRATCH-SELF", "PINNED", "OTHER"):
        b = len(grid.get((t, "BLIND"), []))
        c = len(grid.get((t, "COVERED"), []))
        if b + c == 0:
            continue
        fs = {r["file"] for r in grid.get((t, "BLIND"), []) + grid.get((t, "COVERED"), [])}
        print(f"{t:16s} {b:7d} {c:9d}   {len(fs):6d}", file=e)
    tb = len([r for r in rows if r["verdict"] == "BLIND"])
    tc = len([r for r in rows if r["verdict"] == "COVERED"])
    print(f"{'TOTAL':16s} {tb:7d} {tc:9d}   {len({r['file'] for r in rows}):6d}", file=e)
    print("-" * 78, file=e)
    print("THE HEADLINE CONTRAST:", file=e)
    pin_b = len(grid.get(("PINNED", "BLIND"), []))
    pin_c = len(grid.get(("PINNED", "COVERED"), []))
    self_b = len(grid.get(("SELF", "BLIND"), []))
    self_c = len(grid.get(("SELF", "COVERED"), []))
    print(f"  gates over the PINNED reference-oracle checkout : "
          f"{pin_c}/{pin_c + pin_b} carry a REF check", file=e)
    print(f"  gates over THIS repo (SELF)                     : "
          f"{self_c}/{self_c + self_b} carry a REF check", file=e)
    print("-" * 78, file=e)
    print("EVERY *BLIND* SELF/WORKTREE SITE, NAMED:", file=e)
    for r in rows:
        if r["verdict"] == "BLIND" and r["target"] in ("SELF", "WORKTREE", "SCRATCH-SELF"):
            print(f"  [{r['class']:14s}] {r['file']}:{r['line']}", file=e)
            print(f"       {r['text'][:150]}", file=e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
