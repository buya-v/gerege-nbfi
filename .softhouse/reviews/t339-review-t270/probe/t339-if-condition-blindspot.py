#!/usr/bin/env python3
"""T339 -- RED DRIVE against T270's census-superseded-invocations.py.

CLAIM UNDER TEST (T270 handoff sec.4.2): "54 EXECUTED-IN-PLACE ... cap.sh x 52,
resolve7.py x 1, cap9.sh x 1".

DEFECT: the census's shell command-start alternation is

    _CMD_START = r"(?:^|[;&|(`{]|\$\(|&&|\|\||\bthen\b|\bdo\b|\belse\b|\btime\b)\s*(?:exec\s+)?"
                                            census-superseded-invocations.py:142

It admits `then`, `do`, `else` and `time` as command-introducers but NOT `if`,
`elif`, `while`, `until` or `!`.  A superseded artefact invoked as the CONDITION
of an `if` is therefore graded MENTIONED, never EXECUTED -- an under-report, i.e.
an error in the direction of a FALSE GREEN.

This probe (1) proves the blindness on a synthetic file the census must refuse,
and (2) counts the real sites in the tree that the census misses for this reason.

  python3 t339-if-condition-blindspot.py <tree-root>

exit 0  no blind site found
exit 1  the census is blind to at least one REAL in-place invocation
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SH = os.path.join(ROOT, ".softhouse")
CENSUS = os.path.join(SH, "capture", "t270-superseded-trap",
                      "census-superseded-invocations.py")

# The census's own two regexes, copied verbatim from :141-147 so the probe tests
# the SHIPPED grammar, not a paraphrase of it.
_CMD_START = r"(?:^|[;&|(`{]|\$\(|&&|\|\||\bthen\b|\bdo\b|\belse\b|\btime\b)\s*(?:exec\s+)?"
_PATH_PREFIX = r"(?:[\w.$@{}/-]*/)?"
SH_EXEC = (_CMD_START + r"(?:python3|python|bash|sh|zsh|ksh|source|\.)\s+"
           r"(?:-[A-Za-z]+\s+)*[\"']?" + _PATH_PREFIX + r"%s[\"']?(?=$|[\s\"'`);&|])")
SH_DIRECT = (_CMD_START + r"[\"']?(?:\.{1,2}|\$\{?\w+\}?)/" + _PATH_PREFIX +
             r"%s[\"']?(?=$|[\s\"'`);&|])")

# The same grammar with the missing introducers restored.
_CMD_START_FIXED = (r"(?:^|[;&|(`{!]|\$\(|&&|\|\||\bthen\b|\bdo\b|\belse\b|\btime\b"
                    r"|\bif\b|\belif\b|\bwhile\b|\buntil\b)\s*(?:exec\s+)?")
SH_EXEC_FIXED = (_CMD_START_FIXED + r"(?:python3|python|bash|sh|zsh|ksh|source|\.)\s+"
                 r"(?:-[A-Za-z]+\s+)*[\"']?" + _PATH_PREFIX + r"%s[\"']?(?=$|[\s\"'`);&|])")
SH_DIRECT_FIXED = (_CMD_START_FIXED + r"[\"']?(?:\.{1,2}|\$\{?\w+\}?)/" + _PATH_PREFIX +
                   r"%s[\"']?(?=$|[\s\"'`);&|])")

ARTEFACTS = ["cap.sh", "cap9.sh", "resolve7.py", "prove-mkreq7-guard-red.py",
             "run-220-a2-7-runtime.sh", "t44_float_roundtrip.py",
             "t44_float_roundtrip_v2.py", "30-redB-mismatch-detected.sh",
             "t261-redB-attack.sh", "t261-redC-wrap.sh"]

print("=" * 78)
print("ARM 1 -- SYNTHETIC.  The census must grade `if sh $DIR/cap9.sh ...` EXECUTED.")
print("=" * 78)
probe_line = 'if sh "$DIR/cap9.sh" PROBE POST /journalentries req/x.json; then :; fi'
for name, ex, di in (("SHIPPED", SH_EXEC, SH_DIRECT),
                     ("WITH if/elif/while/until/! RESTORED", SH_EXEC_FIXED, SH_DIRECT_FIXED)):
    esc = re.escape("cap9.sh")
    hit = bool(re.search(ex % esc, probe_line)) or bool(re.search(di % esc, probe_line))
    print("  %-38s -> %s" % (name, "EXECUTED" if hit else "*** MISSED (graded MENTIONED) ***"))
control = 'sh "$DIR/cap9.sh" PROBE POST /journalentries req/x.json'
esc = re.escape("cap9.sh")
ctl = bool(re.search(SH_EXEC % esc, control)) or bool(re.search(SH_DIRECT % esc, control))
print("  CONTROL, same call NOT inside an `if` -> %s" % ("EXECUTED" if ctl else "MISSED"))
print("  (a probe whose control also missed would prove nothing -- the control must hit)")
assert ctl, "control did not hit: the probe is measuring the wrong thing"

print()
print("=" * 78)
print("ARM 2 -- REAL SITES IN THE TREE THAT THE SHIPPED GRAMMAR MISSES")
print("=" * 78)
callers = []
for dirpath, dirnames, filenames in os.walk(SH):
    dirnames[:] = [d for d in dirnames if d != ".git"]
    for fn in filenames:
        if fn.endswith((".sh", ".zsh", ".bash")):
            callers.append(os.path.join(dirpath, fn))
callers.sort()

missed = []
for c in callers:
    text = open(c, errors="replace").read()
    lower = text
    sandboxed = any(k in lower for k in ("mktemp -d", "mktemp -dt", "$(mktemp"))
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("#"):
            continue
        for a in ARTEFACTS:
            esc = re.escape(a)
            shipped = re.search(SH_EXEC % esc, line) or re.search(SH_DIRECT % esc, line)
            fixed = re.search(SH_EXEC_FIXED % esc, line) or re.search(SH_DIRECT_FIXED % esc, line)
            if fixed and not shipped:
                missed.append((os.path.relpath(c, ROOT), i, a, sandboxed, line.strip()[:110]))

print("caller shell scripts scanned: %d" % len(callers))
print("sites the FIXED grammar calls EXECUTED and the SHIPPED grammar misses: %d" % len(missed))
for m in missed:
    print("  MISSED  %s:%d  %s   [file uses mktemp: %s]" % (m[0], m[1], m[2], m[3]))
    print("          %s" % m[4])
print()
print("VERDICT: the census's published EXECUTED-IN-PLACE total is understated by %d "
      "shell site(s)." % len([m for m in missed if not m[3]]))
print("         (sites in files that also build a mktemp sandbox are listed but not "
      "counted in that total, because the census would arguably grade them AS-COPY.)")

print()
print("=" * 78)
print("ARM 3 -- END TO END.  Run the SHIPPED census over a scratch tree containing the")
print("         synthetic caller, and read its own totals.")
print("=" * 78)
if not os.path.exists(CENSUS):
    print("  SKIP: %s not on disk (statement about this path only)" % CENSUS)
else:
    with tempfile.TemporaryDirectory() as td:
        reg_dir = os.path.join(td, ".softhouse", "capture", "tierA-a2")
        os.makedirs(reg_dir)
        open(os.path.join(reg_dir, "SUPERSEDED.txt"), "w").write(
            "# scratch register\ncap9.sh -> cap10.sh\n")
        open(os.path.join(reg_dir, "cap9.sh"), "w").write("#!/bin/sh\nexit 0\n")
        open(os.path.join(reg_dir, "cap10.sh"), "w").write("#!/bin/sh\nexit 0\n")
        caller = os.path.join(reg_dir, "prove-if-condition.sh")
        open(caller, "w").write(
            '#!/bin/bash\nDIR="$(cd "$(dirname "$0")" && pwd)"\n'
            'if sh "$DIR/cap9.sh" PROBE; then echo ok; fi\n')
        p = subprocess.run([sys.executable, CENSUS, td], capture_output=True, text=True)
        out = p.stdout + p.stderr
        tot = [l for l in out.splitlines() if "TOTALS:" in l]
        exe = [l for l in out.splitlines() if "EXECUTED " in l]
        print("  census rc=%d" % p.returncode)
        for l in tot:
            print("  %s" % l.strip())
        print("  EXECUTED lines printed: %d" % len(exe))
        for l in exe:
            print("    %s" % l.strip())
        if not exe:
            print("  *** the SHIPPED census reports ZERO executions of cap9.sh in a tree whose")
            print("      ONLY caller invokes it as an `if` condition.  Blind spot confirmed")
            print("      end to end, not merely by regex inspection.")

sys.exit(1 if missed else 0)
