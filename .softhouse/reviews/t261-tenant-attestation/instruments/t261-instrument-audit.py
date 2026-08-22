#!/usr/bin/env python3
"""T261 -- audit T250's OWN instruments against T250's OWN claims (handoff s.1 / s.8).

Claims under test:
  (a) `python3 re` only -- NO grep, NO rg, NO git grep anywhere in the instruments;
  (b) EVERY instrument calibrates on a POSITIVE and a NEGATIVE and ABORTS
      (exit 4 / exit 5) rather than reporting an error as a zero.

Last fire three workers wrote fail-opens into instruments built to enforce the
very rule they broke, so (b) is checked by READING each file for a calibration
construct AND an abort, per file, and reporting the ones that have neither.

Engine: python3 `re` over the files handed to it.
"""
import os
import re
import sys

D = sys.argv[1]

BAD_ENGINE = [
    ("bare grep", re.compile(r"(?<![-\w./])grep\b")),
    ("ripgrep", re.compile(r"(?<![-\w./])rg\b")),
    ("git grep", re.compile(r"git\s+grep\b")),
]
ALLOWED_GREP = re.compile(r"/usr/bin/grep|type grep|no bare `?grep|No `?grep|no grep|"
                          r"NO grep|grep\b[^\n]*P-75|#.*grep")
CALIB = re.compile(r"def calibrate|CALIBRATION|calibrat", re.I)
ABORT4 = re.compile(r"sys\.exit\(4\)|exit 4\b|exit\s+4\b")
ABORT5 = re.compile(r"sys\.exit\(5\)|exit 5\b|exit\s+5\b")
POSNEG = re.compile(r"positive.{0,40}negative|negative.{0,40}positive|"
                    r"POSITIVE.{0,60}NEGATIVE|pos\b.{0,40}neg\b", re.S | re.I)

rows = []
for fn in sorted(os.listdir(D)):
    p = os.path.join(D, fn)
    if not os.path.isfile(p):
        continue
    with open(p, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    engine_hits = []
    for label, pat in BAD_ENGINE:
        for m in pat.finditer(text):
            line = text[text.rfind("\n", 0, m.start()) + 1:
                        text.find("\n", m.end())]
            ln = text.count("\n", 0, m.start()) + 1
            # a mention inside a comment / a fully-qualified /usr/bin/grep is not
            # the engine being USED for a sweep; both are reported, classified.
            stripped = line.strip()
            comment = stripped.startswith("#") or stripped.startswith('"""') \
                or '"""' in text[:m.start()].split("\n")[-1]
            qualified = "/usr/bin/grep" in line
            engine_hits.append((label, ln, "COMMENT" if comment else
                                ("ABSOLUTE-PATH" if qualified else "*** LIVE ***"),
                                stripped[:110]))
    rows.append((fn,
                 bool(CALIB.search(text)),
                 bool(POSNEG.search(text)),
                 bool(ABORT4.search(text)),
                 bool(ABORT5.search(text)),
                 engine_hits))

print("%-46s %-6s %-7s %-7s %-7s" % ("instrument", "calib", "pos+neg", "exit4", "exit5"))
print("-" * 84)
for fn, c, pn, a4, a5, eh in rows:
    print("%-46s %-6s %-7s %-7s %-7s" % (fn, c, pn, a4, a5))
print("")
print("ENGINE HITS (grep / rg / git grep):")
any_live = False
for fn, c, pn, a4, a5, eh in rows:
    for label, ln, kind, line in eh:
        print("  %-44s %-9s L%-5d %-15s %s" % (fn, label, ln, kind, line))
        if kind == "*** LIVE ***":
            any_live = True
if not any_live:
    print("  no LIVE use of grep / rg / git grep in any instrument")
print("")
missing = [fn for fn, c, pn, a4, a5, _ in rows if not (c and (a4 or a5))]
print("INSTRUMENTS WITHOUT BOTH A CALIBRATION AND AN ABORT: %d" % len(missing))
for m in missing:
    print("    %s" % m)
