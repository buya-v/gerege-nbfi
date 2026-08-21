#!/usr/bin/env python3
"""T170 — the DENOMINATOR for the sentence-by-sentence scope rebuild the G-8
STANDING RULE (rule 1) requires.

This does NOT judge anything. It only enumerates every claim-bearing unit of the
two G-8 blocks in `.softhouse/gates.md`, so that the rebuild has a denominator and
so that "what I skipped" (P-40) is a measured number rather than an impression.

A claim-bearing unit is:
  * one table row (a `|`-delimited line that is not a separator and not a header), or
  * one sentence of prose (split on `. ` / `.` at end of a paragraph), or
  * one bullet.

Blank lines, headings, fenced blocks and table separators are counted as SKIPPED,
with the reason recorded.

Output: out/claim-units-t170.json + a count on stdout.
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GATES = os.path.join(ROOT, ".softhouse/gates.md")

# The two G-8 blocks, by heading, resolved at run time so the ranges cannot go stale.
START_MAIN = "## G-8 — TWO phenomena at the rounding floor, under one gate id"
END_MAIN = "## G-9 — CLOSED (chart of accounts)"
START_NOTICE = "## G-8 — NOTICE, local fire `20260821-134344`"


def main():
    lines = open(GATES).read().split("\n")
    idx = {}
    for i, ln in enumerate(lines):
        if ln.startswith(START_MAIN):
            idx["main_start"] = i
        elif ln.startswith(END_MAIN):
            idx["main_end"] = i
        elif ln.startswith(START_NOTICE):
            idx["notice_start"] = i
    if "main_start" not in idx or "main_end" not in idx or "notice_start" not in idx:
        print("FATAL: could not locate the G-8 blocks by heading", file=sys.stderr)
        sys.exit(2)
    # the NOTICE block runs to the next top-level heading, or EOF
    notice_end = len(lines)
    for i in range(idx["notice_start"] + 1, len(lines)):
        if lines[i].startswith("## ") and not lines[i].startswith("## G-8"):
            notice_end = i
            break
    idx["notice_end"] = notice_end

    ranges = [("MAIN", idx["main_start"], idx["main_end"]),
              ("NOTICE", idx["notice_start"], idx["notice_end"])]

    units, skipped = [], []
    for block, a, b in ranges:
        in_fence = False
        for i in range(a, b):
            n = i + 1  # 1-based line number, matching sed -n / awk NR
            ln = lines[i]
            s = ln.strip()
            if s.startswith("```"):
                in_fence = not in_fence
                skipped.append({"line": n, "block": block, "why": "fence marker"})
                continue
            if in_fence:
                skipped.append({"line": n, "block": block, "why": "inside fenced block"})
                continue
            if not s:
                skipped.append({"line": n, "block": block, "why": "blank"})
                continue
            if s.startswith("#"):
                units.append({"line": n, "block": block, "kind": "heading", "text": s})
                continue
            if re.fullmatch(r"\|[\s|:\-]+\|", s):
                skipped.append({"line": n, "block": block, "why": "table separator"})
                continue
            if s.startswith("|"):
                units.append({"line": n, "block": block, "kind": "table_row", "text": s})
                continue
            if s in ("---", "***", "___"):
                skipped.append({"line": n, "block": block, "why": "horizontal rule"})
                continue
            units.append({"line": n, "block": block,
                          "kind": "bullet" if s.startswith(("-", "*", "1.", "2.", "3.", "4.",
                                                            "5.", "6.", ">"))
                          else "prose",
                          "text": s})

    out = {"ranges": {k: v + 1 for k, v in idx.items()},
           "units": units, "skipped": skipped,
           "counts": {"units": len(units), "skipped": len(skipped),
                      "by_kind": {}}}
    for u in units:
        out["counts"]["by_kind"][u["kind"]] = out["counts"]["by_kind"].get(u["kind"], 0) + 1
    dest = os.path.join(ROOT, ".softhouse/capture/t170-g8-rebuild/out/claim-units-t170.json")
    with open(dest, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out["counts"], indent=1))
    print(json.dumps(out["ranges"], indent=1))


if __name__ == "__main__":
    main()
