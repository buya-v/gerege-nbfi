#!/usr/bin/env bash
# T299 -- DRIVE THE RENAME THAT WAS NOT TAKEN, IN A SCRATCH CLONE.
#
# The task offered two dispositions for the namespace collision and asked for a decision on
# the merits. "Renaming would break things" is an assertion until somebody renames it and
# watches. This does that, in a THROWAWAY CLONE -- a live fire is running against the real
# checkout -- and reports what breaks, with the transcripts.
#
# ENGINE (P-33/P-53): git 2.50.x (`git mv`, `git ls-files`, `git status --porcelain`) and
# python3; both are version-printed below. Path resolution is `test -e`, not a pattern match,
# so no regex escape class is involved.
#
# CALIBRATION (P-72): before the rename, every one of the referencing instruments selected
# below must RESOLVE its reference and the two guard scripts must EXIT 0. If a reference is
# already dead or a guard is already red at HEAD, this drive cannot attribute anything to the
# rename, and it aborts rather than reporting a difference it cannot own.
set -u

ROOT="$(git rev-parse --show-toplevel)" || exit 2
[ -n "$ROOT" ] || exit 2
cd "$ROOT" || exit 2
OLD=".softhouse/capture/t256-verdict-predicate"
NEW=".softhouse/capture/t259-verdict-predicate"
git ls-files --error-unmatch -- "$OLD/run.sh" >/dev/null || {
  echo "ABORT(2): $OLD is not tracked; this drive's premise is gone."; exit 2; }

echo "T299 RENAME-COST DRIVE  (in a throwaway clone -- the real checkout is NOT touched)"
echo "engine    : $(git --version) | $(python3 --version 2>&1)"
echo "HEAD      : $(git rev-parse HEAD)"
echo "old name  : $OLD"
echo "hypothetical new name : $NEW"
echo

SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/t299-rename.XXXXXXXX")" || exit 2
trap 'rm -rf "$SCRATCH"' EXIT
CLONE="$SCRATCH/clone"
git clone -q --no-hardlinks "$ROOT" "$CLONE" || { echo "ABORT(2): clone failed"; exit 2; }
echo "clone     : $CLONE"
echo

# The instruments that are RUN, not merely counted. Each was chosen because it NAMES the old
# path and does real work with it; two of them are guards.
PROBES="
.softhouse/capture/t290-review-t271/guard_rvpa_floor_t290.py
.softhouse/capture/t290-review-t271/prove_repair_inert.py
.softhouse/reviews/t262-verdict-predicate/pin_test_t262.py
"

> "$SCRATCH/probe-exits"

run_probes() {
  # $1 = label.  NO `timeout` WRAPPER: this drive's first version wrapped each probe in
  # `timeout`, which is ABSENT on this host (macOS, no coreutils). Every probe exited 127 --
  # "command not found" -- BEFORE and AFTER, identically, so the arm reported "the rename
  # changed nothing" while having executed nothing. That is the exact defect the T238 linter
  # exists to catch (C2: a construct whose failure is swallowed followed by a print the reader
  # takes as a measurement), committed in this task's own instrument, and it is why the
  # calibration below now REFUSES on a non-zero pre-rename exit instead of printing it.
  for p in $PROBES; do
    if [ ! -f "$CLONE/$p" ]; then
      echo "    ABSENT  $p"
      printf '%s absent 99\n' "$1" >>"$SCRATCH/probe-exits"
      continue
    fi
    ( cd "$CLONE" && python3 "$p" ) >"$SCRATCH/$1-$(basename "$p").txt" 2>&1
    rc=$?
    echo "    exit=$rc  $p"
    printf '%s %s %s\n' "$1" "$p" "$rc" >>"$SCRATCH/probe-exits"
  done
}

# Every literal reference to the old path, in tracked .sh/.py OUTSIDE the directory, tested
# for RESOLUTION rather than for presence.
resolve_census() {
  ( cd "$CLONE" && python3 - "$OLD" <<'PY'
import os, re, subprocess, sys
old = sys.argv[1]
r = subprocess.run(["git", "grep", "-l", "-F", "--", old], capture_output=True, text=True)
if r.returncode > 1:
    print("      CENSUS ERROR: git grep exited %d" % r.returncode); sys.exit(2)
alive = dead = 0
deadlist = []
seen = set()
for f in sorted(x for x in r.stdout.split("\n") if x):
    if not f.endswith((".sh", ".py")) or f.startswith(old + "/"):
        continue
    seen.add(f)
    body = open(f, encoding="utf-8", errors="replace").read()
    for m in re.finditer(re.escape(old) + r'[A-Za-z0-9_./-]*', body):
        p = m.group(0).rstrip('".\'/')
        if os.path.exists(p):
            alive += 1
        else:
            dead += 1
            deadlist.append((f, p))
# BOTH TERMS (P-67): the instruments and the references inside them are different numbers.
print("      referencing instruments in this selector : %d file(s)" % len(seen))
print("        of which at least one reference is dead : %d file(s)"
      % len({f for f, _ in deadlist}))
print("      path references that RESOLVE   : %d" % alive)
print("      path references that DO NOT    : %d" % dead)
for f, p in deadlist[:40]:
    print("        %-72s -> %s" % (f, p))
PY
  )
}

echo "=== BEFORE THE RENAME (calibration) ==="
echo "  probes:"
run_probes before
echo "  path resolution:"
resolve_census
echo
# THE CALIBRATION IS ENFORCED, NOT PRINTED. A probe that is already failing at HEAD cannot
# attribute anything to the rename, and a drive that reports "unchanged" over three probes
# that never ran is a fail-open. Any non-zero pre-rename exit ABORTS.
bad="$(awk '$1=="before" && $3!=0' "$SCRATCH/probe-exits" | wc -l | tr -d ' ')"
if [ "$bad" -ne 0 ]; then
  echo "  CALIBRATION FAILED: $bad of the pre-rename probe(s) exited non-zero at HEAD."
  awk '$1=="before" && $3!=0 {printf "    exit=%s  %s\n", $3, $2}' "$SCRATCH/probe-exits"
  echo "  Nothing measured after the rename could be attributed to it. ABORT(1)."
  exit 1
fi
echo "  CALIBRATED: all $(awk '$1=="before"' "$SCRATCH/probe-exits" | wc -l | tr -d ' ') probe(s) exited 0 at HEAD."
echo

echo "=== THE RENAME ==="
( cd "$CLONE" && git mv "$OLD" "$NEW" ) || { echo "ABORT(2): git mv failed"; exit 2; }
echo "  git mv $OLD -> $NEW"
echo "  files moved : $( cd "$CLONE" && git status --porcelain | grep -c '^R' )"
echo "  tree is now dirty on $( cd "$CLONE" && git status --porcelain | wc -l | tr -d ' ' ) path(s)"
echo

echo "=== AFTER THE RENAME ==="
echo "  probes:"
run_probes after
echo "  path resolution:"
resolve_census
echo

echo "=== WHAT REPAIRING IT WOULD COST -- the files a rename can only be COMPLETED by editing ==="
( cd "$CLONE" && python3 - "$OLD" <<'PY'
import re, subprocess, sys, collections
old = sys.argv[1]
r = subprocess.run(["git", "grep", "-l", "-F", "--", old], capture_output=True, text=True)
files = sorted(x for x in r.stdout.split("\n") if x)
occ = 0
owners = collections.Counter()
for f in files:
    n = len(re.findall(re.escape(old), open(f, encoding="utf-8", errors="replace").read()))
    occ += n
    m = re.search(r'\.softhouse/(?:capture|reviews)/(?i:t)(\d+)', f)
    owners["T" + m.group(1) if m else "(no task rig)"] += 1
print("      files still naming the OLD path AFTER the rename : %d" % len(files))
print("      occurrences inside them                          : %d" % occ)
print("      owning tasks whose COMMITTED evidence would have to be edited:")
for k, v in sorted(owners.items()):
    print("        %-16s %d file(s)" % (k, v))
PY
)
echo
echo "  (The clone is discarded on exit. The real checkout was never renamed.)"
echo "RENAME-COST DRIVE COMPLETE."
