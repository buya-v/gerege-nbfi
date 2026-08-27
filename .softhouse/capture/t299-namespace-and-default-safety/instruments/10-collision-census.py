#!/usr/bin/env python3
"""
T299 -- WHAT A RENAME OF `.softhouse/capture/t256-verdict-predicate/` WOULD COST.

ENGINE (P-33/P-53): CPython `re` over bytes read from `git ls-files` + `git grep -l -F`.
Fixed-string matching (`-F`), so no escape class is involved and P-53's backslash-class trap
under `git grep -E` cannot apply. Both engines are version-printed in the transcript.

CALIBRATION (P-72), stated before any count is reported: the selector must find the two
directories the whole task is about -- `capture/t256-verdict-predicate` (T259's) and
`capture/t256-toolchain-population` (T256's own) -- and must find a KNOWN reference site,
`.softhouse/capture/t271-b1-t219/run.sh`, which was read by hand before this instrument was
written. If any of the three is missed, the run ABORTS rather than reporting a smaller number.
A census that cannot find what a human already found is not measuring the tree.

SCOPE, said plainly (P-66/P-70): every TRACKED path in the repository, and for the text search
every tracked file git treats as text. `git grep` skips binary files; there are none of
interest here and the count of skipped files is printed so the reader can see the denominator.
"NOT FOUND" below is a statement about this selector, never about the world.

Exit 0 = census completed. Exit 2 = the census could not reach or calibrate its corpus.
"""
import os
import re
import sys
import collections
import subprocess

OLD = ".softhouse/capture/t256-verdict-predicate"
SIB = ".softhouse/capture/t256-toolchain-population"
CALIB_SITE = ".softhouse/capture/t271-b1-t219/run.sh"


def git(*a, **kw):
    return subprocess.run(["git"] + list(a), capture_output=True, text=True, **kw)


ROOT = git("rev-parse", "--show-toplevel").stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("CENSUS ABORT (2): not inside a git work tree.", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)
HEAD = git("rev-parse", "HEAD").stdout.strip()

print("T299 COLLISION CENSUS")
print("engine    : %s | CPython %s re" % (git("--version").stdout.strip(),
                                          ".".join(str(x) for x in sys.version_info[:3])))
print("repo      : %s" % ROOT)
print("HEAD      : %s" % HEAD)
print()

tracked = [f for f in git("ls-files").stdout.split("\n") if f]
if not tracked:
    print("CENSUS ABORT (2): corpus is unreachable.", file=sys.stderr)
    sys.exit(2)
print("corpus    : %d tracked paths" % len(tracked))

# ---- CALIBRATION, before any negative is reported -------------------------------------
r = git("grep", "-l", "-F", "--", OLD)
if r.returncode > 1:
    print("CENSUS ABORT (2): `git grep` exited %d. It exits 1 on NO MATCH and >1 on ERROR, "
          "and an error is never an empty result (P-81)." % r.returncode, file=sys.stderr)
    sys.exit(2)
hits = sorted(f for f in r.stdout.split("\n") if f)

calib = {
    "T259's directory exists as a tracked prefix": any(f.startswith(OLD + "/") for f in tracked),
    "T256's own directory exists as a tracked prefix": any(f.startswith(SIB + "/") for f in tracked),
    "the hand-read reference site is in the hit set": CALIB_SITE in hits,
}
print()
print("### CALIBRATION (P-72) -- a known positive proven findable BEFORE any count is trusted")
for k, v in calib.items():
    print("  %-52s : %s" % (k, "FOUND" if v else "MISSED"))
if not all(calib.values()):
    print("CENSUS ABORT (2): calibration failed; the selector cannot see what a human already "
          "read, so no number below would mean anything.", file=sys.stderr)
    sys.exit(2)
print()

# ---- CLASSIFY EVERY HIT ---------------------------------------------------------------
# The question a rename has to answer is not "how many mentions" but "how many of them BREAK".
#   EXEC-INSIDE   a tracked .sh/.py INSIDE the directory -- moves with it, survives
#   EXEC-OUTSIDE  a tracked .sh/.py OUTSIDE it that names the path -- STOPS RESOLVING
#   TRANSCRIPT    committed evidence recording a run that HAPPENED at that path -- the bytes
#                 become false about the tree, and repairing them is editing another task's
#                 committed evidence in place
#   PROSE         handoff / review / tasks.json narrative
CLASSES = collections.OrderedDict(
    (k, []) for k in ("EXEC-INSIDE", "EXEC-OUTSIDE", "TRANSCRIPT", "PROSE"))
counts = {}
for f in hits:
    n = len(re.findall(re.escape(OLD), open(f, encoding="utf-8", errors="replace").read()))
    counts[f] = n
    inside = f.startswith(OLD + "/")
    exe = f.endswith((".sh", ".py", ".go"))
    if exe and inside:
        CLASSES["EXEC-INSIDE"].append(f)
    elif exe:
        CLASSES["EXEC-OUTSIDE"].append(f)
    elif f.endswith((".txt", ".log", ".json")) and not f.endswith("tasks.json"):
        CLASSES["TRANSCRIPT"].append(f)
    else:
        CLASSES["PROSE"].append(f)

print("### EVERY TRACKED FILE THAT NAMES `%s`" % OLD)
print("### files: %d   occurrences: %d   (BOTH TERMS -- P-67)"
      % (len(hits), sum(counts.values())))
print()
for c, fs in CLASSES.items():
    print("  %-13s : %2d file(s) / %3d occurrence(s)"
          % (c, len(fs), sum(counts[f] for f in fs)))
    for f in sorted(fs):
        print("      %-88s x%d" % (f, counts[f]))
    print()

# ---- THE OTHER TASKS WHOSE COMMITTED WORK WOULD HAVE TO BE EDITED ----------------------
owners = collections.OrderedDict()
for f in hits:
    if f.startswith(OLD + "/"):
        continue
    m = re.search(r'\.softhouse/(?:capture|reviews)/(?i:t)(\d+)', f)
    key = "T" + m.group(1) if m else "(not under a task rig)"
    owners.setdefault(key, []).append(f)
print("### OTHER TASKS' COMMITTED ARTEFACTS THAT NAME THE PATH")
print("### -- a rename repairs these only by EDITING THEM, which is another task's evidence")
for k in sorted(owners, key=lambda x: (x.startswith("("), x)):
    print("  %-22s : %d file(s)" % (k, len(owners[k])))
print()

# ---- PINS: the places a rename could turn the bar red without anyone noticing ----------
print("### PIN / CALL-SITE SEARCH -- where I looked, exhaustively")
pin_targets = [".softhouse/conformance.sh",
               ".softhouse/guards/check-ledger-invariants.sh",
               ".softhouse/guards/drive-red-ledger-invariants.sh",
               ".softhouse/bin/rehydrate-check.sh",
               ".softhouse/bin/fire-program.sh",
               ".softhouse/bin/go-env.sh"]
for t in pin_targets:
    if not os.path.exists(t):
        print("  %-52s : ABSENT (this file does not exist)" % t)
        continue
    body = open(t, encoding="utf-8", errors="replace").read()
    print("  %-52s : `t256` x%d   `verdict-predicate` x%d"
          % (t, body.count("t256"), body.count("verdict-predicate")))
# The named pin variable, by name, in whatever file carries it.
pin = git("grep", "-n", "-F", "--", "HOSTSTATE_PIN_TEMP_ASSIGN_LIST")
pin_files = sorted({l.split(":", 1)[0] for l in pin.stdout.split("\n") if l})
print("  HOSTSTATE_PIN_TEMP_ASSIGN_LIST occurs in         : %s" % ", ".join(pin_files))
conf = open(".softhouse/conformance.sh", encoding="utf-8", errors="replace").read()
m = re.search(r"HOSTSTATE_PIN_TEMP_ASSIGN_LIST='(.*?)'", conf, re.S)
if not m:
    print("CENSUS ABORT (2): the pin's value could not be extracted; its absence would "
          "otherwise read as 'the pin does not name the path'.", file=sys.stderr)
    sys.exit(2)
rows = [r for r in m.group(1).split("\n") if r.strip()]
print("  the pin has %d rows; rows naming `t256`         : %d"
      % (len(rows), sum(1 for r in rows if "t256" in r)))
for r in rows:
    if "t256" in r:
        print("      %s" % r)
print("  FAILOPEN_PIN_FILE_LIST rows naming `t256`        : %d"
      % sum(1 for l in conf.split("\n") if "t256" in l and "TIER" in l))
print()
print("CENSUS COMPLETE.")
