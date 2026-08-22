#!/usr/bin/env python3
"""T255 / DEC-2 revision 8 — enumerate EVERY `path:NNNN` citation in DEC-2 and
resolve it against the tree, at whatever commit this is run at.

WHY THIS EXISTS AND WHY IT IS NOT `verify-line-numbers.py`.
`verify-line-numbers.py` (T247) checks a HAND-WRITTEN list of rows. Its
`SH_ROWS` holds FOUR conformance.sh rows. This instrument derives the
population FROM THE DOCUMENT, so a citation nobody remembered to list is still
counted. A checker whose population is a human's memory answers a question
about that memory, not about the document (P-66/P-70).

NO NETWORK, NO `cd`, NO `|| true`, NO `|| echo`. Every non-existence below is
printed together with WHERE it was searched. Exit status:
    0  every resolvable citation resolved and matched
    1  at least one MISMATCH (a real, measured negative)
    2  the instrument could not do its job (calibration failed / file absent)
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")

# Basename -> repo-relative path, for citations the document writes bare.
# EVERY entry here is an interpretation this instrument makes explicit rather
# than guesses silently; an unmapped basename is REPORTED, never skipped.
BASENAME_MAP = {
    "conformance.sh": ".softhouse/conformance.sh",
    ".softhouse/conformance.sh": ".softhouse/conformance.sh",
}

# Extensions whose citations are pinned to the Fineract checkout and do not
# drift with this repo (DEC-2 says so at its freshness rule). Reported, not checked.
PINNED_EXT = (".java",)

CITE = re.compile(r"`?(?:\.softhouse/|nexus/)?([A-Za-z0-9_./-]+\.(?:sh|go|java|py|json))`?:(\d+)(?:-(\d+))?")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def main():
    if not os.path.exists(ADR):
        print("REFUSE: DEC-2 not found at %s" % ADR)
        return 2
    adr = load(ADR)

    rows = []
    for i, line in enumerate(adr, 1):
        for m in CITE.finditer(line):
            rows.append((i, m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None, line))

    if not rows:
        print("CALIBRATION FAIL: zero citations found in a document known to carry them. Void.")
        return 2

    print("DEC-2 lines: %d" % len(adr))
    print("citations matched by the pattern: %d" % len(rows))
    print("")

    checked = matched = mismatched = 0
    unresolvable = []
    pinned = []
    cache = {}

    for adr_line, name, start, end, text in rows:
        if name.endswith(PINNED_EXT):
            pinned.append((adr_line, name, start))
            continue
        rel = BASENAME_MAP.get(name)
        if rel is None:
            for cand in (name, os.path.join("nexus", name)):
                if os.path.exists(os.path.join(ROOT, cand)):
                    rel = cand
                    break
        if rel is None:
            unresolvable.append((adr_line, name, start, end))
            continue
        full = os.path.join(ROOT, rel)
        if not os.path.exists(full):
            unresolvable.append((adr_line, name, start, end))
            continue
        if rel not in cache:
            cache[rel] = load(full)
        body = cache[rel]
        checked += 1
        if start > len(body):
            mismatched += 1
            print("  BEYOND-EOF  DEC-2:%-5d %s:%d  (file has %d lines)" % (adr_line, rel, start, len(body)))
            continue
        target = body[start - 1]
        print("  DEC-2:%-5d %s:%-5d -> %s" % (adr_line, rel, start, target.strip()[:96]))
        matched += 1

    print("")
    print("RESOLVED   : %d of %d citations (both terms counted, P-67)" % (checked, len(rows)))
    print("PINNED     : %d (Fineract checkout, do not drift)" % len(pinned))
    for adr_line, name, start in pinned:
        print("    DEC-2:%-5d %s:%d" % (adr_line, name, start))
    print("UNRESOLVED : %d (searched: BASENAME_MAP, then <name>, then nexus/<name>, under %s)" % (len(unresolvable), ROOT))
    for adr_line, name, start, end in unresolvable:
        print("    DEC-2:%-5d %s:%s" % (adr_line, name, start if end is None else "%d-%d" % (start, end)))
    print("BEYOND-EOF : %d" % mismatched)
    print("")
    print("NOTE: this instrument PRINTS what each line number resolves to. It cannot")
    print("decide whether that text is what the citing sentence meant -- that is a")
    print("human reading, and it is exactly the reading that has failed three times.")
    print("Revision 8 removes the need for it by citing CONTENT; see 20-verify-anchors.py.")
    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
