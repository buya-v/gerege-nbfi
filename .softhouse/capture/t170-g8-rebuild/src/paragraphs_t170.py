#!/usr/bin/env python3
"""T170 — paragraph/row-level denominator for the G-8 scope rebuild.

`split_claims_t170.py` gives a LINE-level denominator, which over-counts because a
prose claim spans several wrapped lines. This gives the unit the rebuild is actually
judged at: one paragraph, one bullet, one table row, one heading.

Run against a given revision of gates.md (default: the working tree) so the BEFORE
and AFTER denominators can both be stated.

Usage:  paragraphs_t170.py [path-to-gates.md]
Output: out/paragraph-units-t170.json  (+ counts on stdout)
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT = os.path.join(ROOT, ".softhouse/gates.md")

START_MAIN = "## G-8 — TWO phenomena at the rounding floor"
END_MAIN = "## G-9 — CLOSED (chart of accounts)"
START_NOTICE = "## G-8 — NOTICE, local fire `20260821-134344`"


def units_in(lines, a, b, block):
    out, buf, start, in_fence = [], [], None, False
    def flush():
        nonlocal buf, start
        if buf:
            out.append({"block": block, "line": start, "kind": "prose",
                        "text": " ".join(buf)})
            buf, start = [], None
    for i in range(a, b):
        n, ln = i + 1, lines[i]
        s = ln.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not s:
            flush(); continue
        if s.startswith("#"):
            flush(); out.append({"block": block, "line": n, "kind": "heading", "text": s}); continue
        if re.fullmatch(r"\|[\s|:\-]+\|", s):
            continue
        if s.startswith("|"):
            flush(); out.append({"block": block, "line": n, "kind": "table_row", "text": s}); continue
        if s in ("---", "***", "___"):
            flush(); continue
        if re.match(r"^([-*>]|\d+\.)\s", s):
            flush()
            buf, start = [s], n
            continue
        if start is None:
            start = n
        buf.append(s)
    flush()
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    lines = open(path).read().split("\n")
    idx = {}
    for i, ln in enumerate(lines):
        if ln.startswith(START_MAIN):
            idx["main_start"] = i
        elif ln.startswith(END_MAIN):
            idx["main_end"] = i
        elif ln.startswith(START_NOTICE):
            idx["notice_start"] = i
    notice_end = len(lines)
    for i in range(idx["notice_start"] + 1, len(lines)):
        if lines[i].startswith("## ") and not lines[i].startswith("## G-8"):
            notice_end = i
            break
    units = (units_in(lines, idx["main_start"], idx["main_end"], "MAIN")
             + units_in(lines, idx["notice_start"], notice_end, "NOTICE"))
    counts = {}
    for u in units:
        counts[u["kind"]] = counts.get(u["kind"], 0) + 1
    counts["total"] = len(units)
    res = {"source": path, "counts": counts, "units": units}
    if path == DEFAULT:
        dest = os.path.join(ROOT, ".softhouse/capture/t170-g8-rebuild/out/paragraph-units-t170.json")
        with open(dest, "w") as f:
            json.dump(res, f, indent=1)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
