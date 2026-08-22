#!/usr/bin/env python3
"""T251: does every hunk's `— BEFORE —` block still match the live ADR?

T247's verify-line-numbers.py checks 46 single-line ANCHORS. That is weaker than
it looks: an anchor can hold while the surrounding block the hunk actually
REPLACES has drifted. This checks the replaced text itself.

For each `### H-n — ... Replaces lines **A-B**` with a `#### — BEFORE —` fenced
block, compare the block to ADR[A-1:B] after whitespace normalisation. Hunks
whose BEFORE is explicitly abbreviated (H-1 says so) or which replace only a
table CELL are reported as NOT-MECHANICALLY-CHECKABLE rather than silently
passed — P-35: a check that inspected nothing is not a pass.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")
REV = os.path.join(ROOT, ".softhouse/capture/t247-dec2-rev7/REVISION-7-PROPOSED.md")

ADR_LINES = open(ADR, encoding="utf-8").read().split("\n")
REV_TEXT = open(REV, encoding="utf-8").read()

HUNK = re.compile(r"^### (H-\d+\w?) — (.*)$", re.M)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def blocks_after(idx, end):
    """Return list of (label, fenced_body) appearing between idx and end."""
    seg = REV_TEXT[idx:end]
    out = []
    for m in re.finditer(r"^#### — (BEFORE|AFTER)[^\n]*—?[^\n]*$\n+```[a-z]*\n(.*?)^```",
                         seg, re.M | re.S):
        out.append((m.group(1), m.group(2)))
    return out


def main():
    print("COMMIT:", os.popen("git -C %s rev-parse HEAD" % ROOT).read().strip())
    hs = list(HUNK.finditer(REV_TEXT))
    print("hunks found: %d\n" % len(hs))
    checked = ok = drift = skipped = 0
    for i, m in enumerate(hs):
        name, title = m.group(1), m.group(2)
        end = hs[i + 1].start() if i + 1 < len(hs) else len(REV_TEXT)
        span = re.search(r"lines?\s+\*\*(\d+)(?:-(\d+))?\*\*", title)
        bl = [b for lbl, b in blocks_after(m.start(), end) if lbl == "BEFORE"]
        reason = None
        if not span:
            reason = "no explicit line span in the hunk title"
        elif not bl:
            reason = "no fenced BEFORE block (AFTER-only / append-only hunk)"
        elif "abbreviated" in title or "cell only" in title or "last cell" in title:
            reason = "BEFORE is a partial quote (abbreviated, or a table cell)"
        if reason:
            skipped += 1
            print("  %-6s SKIP   %s" % (name, reason))
            continue
        a = int(span.group(1))
        b = int(span.group(2) or span.group(1))
        live = "\n".join(ADR_LINES[a - 1:b])
        checked += 1
        if norm(live) == norm(bl[0]):
            ok += 1
            print("  %-6s OK     L%d-%d matches byte-for-byte (ws-normalised)" % (name, a, b))
        else:
            drift += 1
            print("  %-6s DRIFT  L%d-%d does NOT match the quoted BEFORE" % (name, a, b))
            print("         live : %r" % norm(live)[:150])
            print("         quoted: %r" % norm(bl[0])[:150])
    print("\nSUMMARY: %d checked, %d match, %d DRIFTED, %d not mechanically checkable"
          % (checked, ok, drift, skipped))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
