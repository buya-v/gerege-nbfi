#!/usr/bin/env python3
"""T368 — is the WIRED FATAL control able to fail, and does SKIPPED tell the truth?

The fire runs `--self-test-lock-readers` fatally BEFORE it reads the lock, and inspects
ONLY the exit status (fire-program.sh:1139-1145 — `grep -n 'ROWS=' <file>` finds the tally
printed at :727 and referenced in one comment, and nowhere in the wiring). So the two
questions a reviewer must answer with a measurement, not an argument, are:

  m10  if the rows were gutted, would the control still pass?   (P-22: a control that
       cannot fail is worse than none, because it is believed)
  m11  when rows ARE skipped, does SKIPPED report the right number?  (T365 changed
       `_skipped=3` to `_skipped+=3`; group E can also skip, so an assignment would
       have erased group B's count)

Every mutation is applied by exact string replacement and ABORTS as VOID if the anchor is
not present exactly once — a mutation that silently did not apply is a green that means
nothing.

Usage: t368-control-integrity.py <path-to-fire-program.sh>
"""
import os, subprocess, sys, tempfile

SRC = sys.argv[1]
base = open(SRC).read()
tmp = tempfile.mkdtemp(prefix="t368-ci.")

print("T368 control-integrity drive over", SRC)
print("sha256:", subprocess.run(["shasum", "-a", "256", SRC],
                                capture_output=True, text=True).stdout.split()[0])
print()


def run(mid, what, text, expect):
    p = os.path.join(tmp, "fire-%s.sh" % mid)
    open(p, "w").write(text)
    os.chmod(p, 0o755)
    r = subprocess.run(["/bin/zsh", p, "--self-test-lock-readers"],
                       capture_output=True, text=True)
    tally = [l for l in r.stdout.splitlines() if l.startswith("ROWS=")]
    warns = [l.strip() for l in r.stdout.splitlines() if "SKIPPED" in l and "WARNING" in l]
    print("%s  %s" % (mid, what))
    print("      expected : %s" % expect)
    print("      rc=%d  tally=%s" % (r.returncode, tally[0] if tally else "*** ABSENT ***"))
    for w in warns:
        print("      warn     : %s" % w)
    print()


# --- m10: gut every row, leave the tally and the exit test standing -------------------
import re
kept, killed = [], 0
for line in base.splitlines(True):
    if re.match(r"\s*_(row|arow)\s+[a-z]\d", line):
        killed += 1
        continue
    kept.append(line)
if killed < 40:
    sys.exit("VOID: expected to delete >=40 row invocations, deleted %d" % killed)
run("m10", "all %d _row/_arow invocations DELETED — can the wired control fail?" % killed,
    "".join(kept),
    "if this exits 0 the fire starts on a self-test that graded NOTHING (P-22)")

# --- m11: force the reaped-pid acquisition to fail ------------------------------------
ANCHOR = """  _DEAD=0
  for _i in 1 2 3 4 5; do
    sleep 0 & _cand=$!; wait $_cand 2>/dev/null
    kill -0 $_cand 2>/dev/null || { _DEAD=$_cand; break; }
  done
"""
if base.count(ANCHOR) != 1:
    sys.exit("VOID: reaped-pid anchor appears %d times, not once" % base.count(ANCHOR))
run("m11", "reaped-pid acquisition forced to fail (_DEAD=0) — does SKIPPED tell the truth?",
    base.replace(ANCHOR, "  _DEAD=0\n"),
    "ROWS drops by 4 (group B's 3 + e01) and SKIPPED reports 4, not 3")
