#!/usr/bin/env python3
"""T260 — AUDIT T255'S INSTRUMENTS BEFORE ITS CONCLUSIONS.

Three workers last fire wrote fail-opens into instruments built to enforce the rule they broke.
So: before believing a single figure T255 reports, check the tools that produced them for the
known-bad shapes.

  P-75  no bare `grep` (bundled ugrep prepends six --exclude-dir flags silently; 33% recall
        measured), no `rg` (no binary; `rg P F | head` exits 0), `git grep -E` misses AND
        fabricates (`\\b` reads as a literal b, returning zero silently).
  P-80  `git grep` exits 1 on NO MATCH and >1 on ERROR. An instrument that maps any non-zero to
        "absent" fabricates absences.
  P-22/P-35  an instrument with no negative control cannot distinguish "found nothing" from
        "searched nothing".

Usage: 80-instrument-audit.py <dir-of-instruments> [more dirs...]
Exit 0 always (census).
"""
import os
import re
import sys

BAD = [
    ("bare `grep` invocation", re.compile(r"(?<![-\w.'\"])grep\b")),
    ("`rg` invocation", re.compile(r"(?<![-\w.'\"])rg\b")),
    ("`|| true` fail-open", re.compile(r"\|\|\s*true")),
    ("`|| echo` fail-open", re.compile(r"\|\|\s*echo")),
    ("`|| :` fail-open", re.compile(r"\|\|\s*:\s*$", re.M)),
    ("bare `except:`", re.compile(r"except\s*:")),
    ("`except ...: pass`", re.compile(r"except[^\n]*:\s*\n\s+pass\b")),
    ("linter amnesty hatch", re.compile(r"lint-failopen:\s*ok")),
    ("`shell=True`", re.compile(r"shell\s*=\s*True")),
    ("`check=False`", re.compile(r"check\s*=\s*False")),
    ("`\\b` inside a git-grep -E/-P pattern", re.compile(r"git\s+grep[^\n]*-[EP][^\n]*\\\\b")),
]

GOOD = [
    ("negative control", re.compile(r"MUST-NOT-MATCH|NEGATIVE CONTROL|CALIBRATION")),
    ("positive control", re.compile(r"positive control|POSITIVE", re.I)),
    ("exit-2 reserved for cannot-do-job", re.compile(r"exit 2|return 2")),
    ("classifies git-grep status", re.compile(r"returncode|rc\b|exit 1 on NO MATCH|>1 on ERROR")),
    ("uses str.count / exact substring", re.compile(r"\.count\(|\bin haystack\b|occurrences\(")),
]


def main():
    files = []
    for d in sys.argv[1:]:
        for root, _, names in os.walk(d):
            for nm in sorted(names):
                if nm.endswith((".py", ".sh")):
                    files.append(os.path.join(root, nm))
    print("T260 — instrument audit (P-75 / P-80 / P-22 known-bad shapes)")
    print("=" * 100)
    print(f"instruments audited: {len(files)}")
    total_bad = 0
    for f in sorted(files):
        t = open(f, encoding="utf-8", errors="replace").read()
        # strip python docstrings/comments? No -- a fail-open in a comment is not a fail-open, but
        # a bare grep NAMED in prose is not one either. So report line numbers and let the reader
        # see whether the hit is code or prose. Nothing is silently dropped (P-70).
        lines = t.split("\n")
        bad = []
        for label, pat in BAD:
            for m in pat.finditer(t):
                ln = t[: m.start()].count("\n") + 1
                src = lines[ln - 1]
                is_comment = src.lstrip().startswith("#") or src.lstrip().startswith('"')
                bad.append((label, ln, "PROSE/COMMENT" if is_comment else "*** CODE ***",
                            src.strip()[:110]))
        good = [g for g, p in GOOD if p.search(t)]
        print(f"\n  {os.path.basename(f)}  ({len(lines)} lines)")
        print(f"    controls present: {', '.join(good) if good else 'NONE'}")
        if not bad:
            print("    known-bad shapes: NONE")
        for label, ln, kind, src in bad:
            print(f"    [{kind}] L{ln} {label}: {src}")
            if kind == "*** CODE ***":
                total_bad += 1
    print()
    print(f"KNOWN-BAD SHAPES IN CODE (not prose): {total_bad}")


if __name__ == "__main__":
    main()
