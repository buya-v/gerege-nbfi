#!/usr/bin/env python3
"""T368 independent mutation driver over T365's fire-program.sh.

For each mutation: apply, ABORT-as-VOID if the text did not change, run the
self-test with zsh, and report rc plus every row that is not `ok`.
Nothing here reads T365's transcripts; expectations are typed here and graded
against what the file actually does.
"""
import subprocess, sys, os, re, shutil, tempfile

SRC = sys.argv[1]
base = open(SRC).read()

SKEW = '  (( _e <= _now + LOCK_RELEASE_SKEW_SECS )) || return 0\n'
POS  = '  (( _e > 0 )) || return 0\n'
HOST = None
EPOCH_PRINT = '  print -r -- $(( days * 86400 + hh * 3600 + mi * 60 + ss ))\n'
LEAP = '  (( (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 )) && leap=1\n'

# locate the host guard line in lock_pid_state
for line in base.splitlines(True):
    if 'hostname -s' in line and 'other_host' in line:
        HOST = line
assert HOST, "could not locate the host guard line"

MUTS = [
    ("m00", "control: unmutated shipped file", None, "rc 0, every row ok"),
    ("m01", "C1 predicate 1 REMOVED: (( _e > 0 ))", (POS, ""), "z01 z02 z03 FAIL-OPEN"),
    ("m02", "C1 predicate 2 REMOVED: the skew bound", (SKEW, ""), "z04 z05 z06 FAIL-OPEN"),
    ("m03", "C1 skew bound TIGHTENED TO A BAN ON ANY FUTURE INSTANT (_e <= _now)",
     (SKEW, '  (( _e <= _now )) || return 0\n'), "z07 FAIL-SHUT -- proves z07 is a live control"),
    ("m04", "C1 turned into a TOTAL BAN: no released_at is ever believed",
     (POS, '  (( 0 )) || return 0\n'), "d01 AND z07 FAIL-SHUT -- a ban is caught, twice"),
    ("m05", "the P-85 host guard DELETED from lock_pid_state", (HOST, ""), "e01 FAIL-OPEN"),
    ("m06", "century non-leap rule broken: leap = (y % 4 == 0)",
     (LEAP, '  (( y % 4 == 0 )) && leap=1\n'), "h04 FAIL-OPEN and -- per T365 -- NO body row"),
    ("m07lo", "_iso8601_epoch drifts ONE DAY LOW",
     (EPOCH_PRINT, '  print -r -- $(( days * 86400 + hh * 3600 + mi * 60 + ss - 86400 ))\n'),
     "g01 FAIL-OPEN (arm 3 fires on a live holder) and group H red"),
    ("m07hi", "_iso8601_epoch drifts ONE DAY HIGH",
     (EPOCH_PRINT, '  print -r -- $(( days * 86400 + hh * 3600 + mi * 60 + ss + 86400 ))\n'),
     "g01 STAYS GREEN (T365 FINDING 2) and group H red"),
    ("m08", "the day-of-month bound dropped", ('  (( d >= 1 && d <= maxd )) || return 1\n', ""),
     "g02 FAIL-OPEN"),
    ("m09", "the ROWS= tally line deleted (P-83 presence-before-value on this driver)",
     ('  print -r -- "ROWS=$_n FAIL_OPEN=$_open FAIL_SHUT=$_shut SKIPPED=$_skipped"\n', ""),
     "no ROWS= line -> this driver must say ABSENT, not pass"),
]

tmp = tempfile.mkdtemp(prefix="t368-mut.")
fails = 0
print("T368 independent mutation drive over", SRC)
print("sha256:", subprocess.run(["shasum","-a","256",SRC],capture_output=True,text=True).stdout.split()[0])
print()
for mid, what, sub, expect in MUTS:
    if sub is None:
        text = base
    else:
        old, new = sub
        if base.count(old) != 1:
            print(f"{mid}  *** VOID: anchor appears {base.count(old)} times, not once")
            fails += 1
            continue
        text = base.replace(old, new)
        if text == base:
            print(f"{mid}  *** VOID: mutation did not change the file")
            fails += 1
            continue
    p = os.path.join(tmp, f"fire-{mid}.sh")
    open(p, "w").write(text)
    os.chmod(p, 0o755)
    r = subprocess.run(["/bin/zsh", p, "--self-test-lock-readers"],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    bad = [l.split()[0] for l in out.splitlines() if "FAIL-OPEN" in l or "FAIL-SHUT" in l]
    tally = [l for l in out.splitlines() if l.startswith("ROWS=")]
    print(f"{mid}  {what}")
    print(f"      expected : {expect}")
    print(f"      rc={r.returncode}  tally={tally[0] if tally else '*** ABSENT ***'}")
    print(f"      red rows : {' '.join(bad) if bad else '(none)'}")
    print()
print("VOID/anchor failures:", fails)
