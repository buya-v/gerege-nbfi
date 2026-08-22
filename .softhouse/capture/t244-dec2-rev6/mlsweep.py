#!/usr/bin/env python3
"""T244 MULTI-LINE sweep pass.

Every sweep in this program has been LINE-ORIENTED, and T234 found 743 matches
spanning a newline across 161 files. This is engine 3: python3 `re` with DOTALL,
reading each file whole so a pattern may cross line breaks.

Used two ways:
  mlsweep.py                    -> run the full multi-line pattern battery
  mlsweep.py --count <regex>    -> print the number of MATCHES for one regex
                                   (calibration / negative control)

Scope: the whole worktree on disk, excluding .git and excluding this task's own
capture directory when reporting (so the instrument does not find itself and
manufacture corroboration) -- self-hits are counted separately and shown.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SELF_DIR = os.path.abspath(os.path.dirname(__file__))

SKIP_DIRS = {".git"}
# Binary-ish extensions we will not try to decode.
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar",
            ".jar", ".class", ".so", ".dylib", ".ico", ".woff", ".woff2"}


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            yield os.path.join(dirpath, fn)


def read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (OSError, UnicodeError):
        return None


def scan(pattern):
    """Return (hits_outside_self, hits_inside_self). Each hit is (path, line, text)."""
    rx = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    outside, inside = [], []
    for path in iter_files():
        body = read(path)
        if body is None:
            continue
        for m in rx.finditer(body):
            line = body.count("\n", 0, m.start()) + 1
            text = " ".join(m.group(0).split())
            if len(text) > 200:
                text = text[:200] + " ..."
            rel = os.path.relpath(path, ROOT)
            (inside if path.startswith(SELF_DIR) else outside).append((rel, line, text))
    return outside, inside


PATTERNS = [
    # the exact concept, allowed to cross newlines
    r"corpus[\s\S]{0,60}?no[\s\S]{0,30}?revers",
    r"contains[\s\S]{0,40}?no[\s\S]{0,40}?revers",
    # the short form, newline-spanning: "no\n reversal"
    r"\bno\s+revers",
    # the claim restated as ungradeable-for-lack-of-evidence
    r"revers[\s\S]{0,80}?(ungraded|not graded|no vector|nothing to grade|no capture)",
    r"(ungraded|not graded|nothing to grade)[\s\S]{0,80}?revers",
    # I-5 discussed across a line break
    r"I-5[\s\S]{0,120}?revers",
    r"revers[\s\S]{0,120}?I-5",
]


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--count":
        outside, inside = scan(sys.argv[2])
        print(len(outside) + len(inside))
        return

    print("multi-line engine : python3 re, flags = IGNORECASE | DOTALL")
    print("root              : %s" % ROOT)
    print("files scanned     : %d" % sum(1 for _ in iter_files()))
    print("self-dir excluded from the headline list (shown separately): %s"
          % os.path.relpath(SELF_DIR, ROOT))
    print()
    for pat in PATTERNS:
        outside, inside = scan(pat)
        print("--- MULTILINE PATTERN: %s" % pat)
        print("    hits outside this task's capture dir: %d   (self-hits: %d)"
              % (len(outside), len(inside)))
        if not outside:
            print("    (no hits outside self)")
        else:
            for rel, line, text in outside:
                print("    %s:%d: %s" % (rel, line, text))
        print()


if __name__ == "__main__":
    main()
