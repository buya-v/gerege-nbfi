#!/usr/bin/env python3
"""T339 probe -- INDEPENDENT re-derivation of T270's "54 EXECUTED-IN-PLACE".

Deliberately NOT the same algorithm as census-superseded-invocations.py.  T270's
census resolves a spawn selector from each caller's own imports and walks the
Python AST.  This one is a line-oriented, exact-path matcher: it looks for the
artefact's basename preceded by a PATH SEPARATOR or a quote and preceded, on the
same line, by an interpreter word -- and it separates "the path resolves to the
rig" from "the path resolves to a scratch/temp copy".

If the two instruments agree on 54 that is corroboration by a different method.
If they disagree, the disagreement is the finding.

  python3 t339-recount-54.py <tree-root>
"""
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SH = os.path.join(ROOT, ".softhouse")

# The three artefacts T270 grades "STILL EXECUTED IN PLACE".  All 12 declared
# basenames are swept; these three are the ones with a non-zero count to beat.
ARTEFACTS = ["cap.sh", "cap9.sh", "resolve7.py", "prove-mkreq7-guard-red.py",
             "run-220-a2-7-runtime.sh", "t44_float_roundtrip.py",
             "t44_float_roundtrip_v2.py", "t44_float_roundtrip-output.txt",
             "T55-ANALYSIS.txt", "30-redB-mismatch-detected.sh",
             "t261-redB-attack.sh", "t261-redC-wrap.sh"]

INTERP_SH = re.compile(r"\b(?:bash|sh|zsh|source)\b")
INTERP_PY = re.compile(r"\b(?:python3?|python3\.\d+|sys\.executable)\b")

# a scratch/copy invocation: the path expression names a temp/scratch variable
COPYISH = re.compile(r"\b(?:TMPD?|TMPDIR|SCRATCH|WORK|d|td|tmp|tmpdir|clone|SANDBOX)\b"
                     r"|mkdtemp|tempfile|/tmp/")

callers = []
for dirpath, dirnames, filenames in os.walk(SH):
    dirnames[:] = [d for d in dirnames if d != ".git"]
    for fn in filenames:
        if fn.endswith((".py", ".sh", ".zsh")):
            callers.append(os.path.join(dirpath, fn))
bindir = os.path.join(SH, "bin")
if os.path.isdir(bindir):
    for dirpath, _dn, filenames in os.walk(bindir):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if p not in callers and not fn.endswith((".py", ".sh", ".zsh")):
                callers.append(p)
callers = sorted(set(callers))

ext = {}
for c in callers:
    ext[os.path.splitext(c)[1] or "(none)"] = ext.get(os.path.splitext(c)[1] or "(none)", 0) + 1
print("CALLER POPULATION: %d file(s)  %s" % (len(callers), sorted(ext.items())))
print()

inplace, ascopy, mentioned = {}, {}, {}
rows = []
for c in callers:
    try:
        text = open(c, errors="replace").read()
    except OSError:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        for a in ARTEFACTS:
            # exact basename: must be preceded by /, quote, space, ( or start;
            # must be followed by a non-name char.  Rules out cap8.sh matching cap.sh.
            if not re.search(r"(?:^|[\s\"'/(\[,=])" + re.escape(a) + r"(?:[\s\"')\],;|&:]|$)", line):
                continue
            is_comment = s.startswith("#")
            is_echo = bool(re.match(r"^\s*echo\b", s))
            interp = bool(INTERP_SH.search(line) or INTERP_PY.search(line))
            if is_comment or is_echo or not interp:
                mentioned[a] = mentioned.get(a, 0) + 1
                continue
            # is the artefact the thing being run, i.e. immediately after the
            # interpreter (allowing a $DIR/-style prefix and flags)?
            run = re.search(r"(?:bash|sh|zsh|source|python3?|python3\.\d+|sys\.executable)"
                            r"[\"'\],\s]+(?:-\S+\s+)*[\"']?\$?[A-Za-z0-9_{}$/.\-]*" +
                            re.escape(a), line)
            joined = re.search(r"(?:os\.path\.)?join\([^)]*[\"']" + re.escape(a) + r"[\"']", line)
            if not (run or joined):
                mentioned[a] = mentioned.get(a, 0) + 1
                continue
            if COPYISH.search(line):
                ascopy[a] = ascopy.get(a, 0) + 1
                rows.append(("EXEC-COPY", a, os.path.relpath(c, ROOT), i, s[:100]))
            else:
                inplace[a] = inplace.get(a, 0) + 1
                rows.append(("EXECUTED ", a, os.path.relpath(c, ROOT), i, s[:100]))

for r in rows:
    print("  %s %-28s %-62s :%-4d %s" % r)
print()
print("PER-ARTEFACT")
for a in ARTEFACTS:
    print("  %-32s in-place=%-4d as-copy=%-4d mentioned=%d"
          % (a, inplace.get(a, 0), ascopy.get(a, 0), mentioned.get(a, 0)))
print()
print("TOTAL EXECUTED-IN-PLACE: %d" % sum(inplace.values()))
print("TOTAL EXECUTED-AS-COPY : %d" % sum(ascopy.values()))
