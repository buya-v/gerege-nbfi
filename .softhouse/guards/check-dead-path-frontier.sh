#!/usr/bin/env bash
# T316 -- THE DEAD-PATH FRONTIER GUARD.
#
# WHAT IT ENFORCES, in one sentence: the set of tracked `.softhouse/` instruments that name a
# repo-relative path WHICH THE REPOSITORY DOES NOT CONTAIN is PINNED, and it may not grow.
#
# ===========================================================================================
# T326 -- "WHICH THE REPOSITORY DOES NOT CONTAIN", NOT "WHICH IS NOT ON THIS DISK".
# ===========================================================================================
# T316 wrote "WHICH DOES NOT EXIST" and the census implemented it with `os.path.exists()`. On
# first contact with a second machine that made the guard refuse, correctly:
#
#     T316-DEADPATH-FRONTIER: REFUSED rows=78 pinned=98 added=4 removed=24
#
# with the oracle probe line ABSENT, i.e. a FAILED HARD GUARD under P-84 ("'EXIT 2 WITH NO PROBE
# LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE"), which is what a driver is
# trained to read as a MONEY NON-NEGOTIABLE VIOLATION. THE GUARD WAS RIGHT; THE PIN WAS THE
# DEFECT. 23 of the 24 vanished rows named `.softhouse/toolchain` -- `.gitignore`d, zero tracked
# files, present in Buyan's main checkout and absent in every worktree -- and the 24th named
# untracked scratch left behind by an earlier run ON THE SAME MACHINE.
#
# The census now resolves against `git ls-files`. The frontier is a property of the COMMIT, so
# the launchd fire on Buyan's Mac and the cloud fire that never runs on that host cannot disagree
# about the colour of the bar. An untracked path is DEAD whether or not it happens to be there;
# the argument for that choice, and the two alternatives rejected, are in the pin's header.
#
# TWO PREDICATES, TWO FAIL-CLOSED DIRECTIONS, DELIBERATELY NOT MERGED (the shape T292 identified
# as the root of a five-fix losing streak):
#
#   * THIS GUARD'S OWN DEPENDENCIES -- the census script, the pin file, python3, the scratch dir
#     -- are checked ON DISK, with `[ -f ]`, and a miss is exit 2. That must stay a disk check:
#     you cannot execute a file that is not there, and the fail-closed direction is "if I cannot
#     REACH what I grade, I have not graded it."
#   * THE FRONTIER'S CLASSIFICATION is tracked-set membership, and never touches the disk. Its
#     fail-closed direction is "the verdict must be a property of the commit, on any host."
#
# Widening either predicate to serve the other would reintroduce exactly one of the two defects.
#
# WHY A FRONTIER AND NOT ZERO. The population at the commit that installs this guard is 70
# instruments naming 98 dead literals, measured (not estimated) by
# `.softhouse/capture/t316-dead-path-guards/census_dead_paths.py`, whose selector is printed on
# every run. Demanding zero would be red on its first run and would be pinned away within a fire.
# Demanding NO GROWTH costs nothing today and stops the next one silently arriving. This is the
# same shape, and deliberately the same terms, as `FAILOPEN_PIN_FILE_LIST` and
# `HOSTSTATE_PIN_TEMP_ASSIGN_LIST` in `conformance.sh`.
#
# THE PIN IS A FRONTIER, NOT AN AMNESTY -- `conformance.sh:1715`, quoted because the rule is
# theirs and not mine: "A '+' row is a NEW site: repair it ... rather than pinning it. A '-' row
# is a site that was REPAIRED or DELETED, which is good news, and the pin must lose that row IN
# THE SAME COMMIT or it starts excusing a weakness that is no longer there."
#
# WHAT A ROW DOES **NOT** MEAN. A pinned row is NOT an accusation that the instrument is
# fail-open. T316 measured that the two instruments FU-T299-2 named -- `guard_rvpa_floor_t290.py`
# and `red/drive-red-t290.py` -- name a dead path and are NOT fail-open: the dead literal is
# candidate #1 of an ordered two-candidate list, the second candidate resolves, and when NEITHER
# resolves both exit 2 with the probe line ABSENT. A dead literal is a SMELL that must be
# inspected once, by a human, and then either repaired or pinned with its reason. This guard
# counts; it does not judge.
#
# THE FAIL DIRECTION IS THE POINT, and this guard obeys the rule it enforces. Every path THIS
# guard depends on -- the census instrument, the pin file, the scratch destination -- is checked,
# and a path that does not resolve makes it exit 2. It refuses; it never passes for lack of
# anything to check. P-45's cousin, and P-45's own text is the reason:
#
#     "P-45 -- A test-only guard is not a guard. T154's float-literal census is called from
#      `Run`, not only from the Go test, because `conformance.sh` never invokes `go test` -- a
#      test-only fix would have left the third silent green standing while looking fixed. Rule:
#      when hardening a check, verify the path that actually executes in CI/conformance calls it,
#      not merely that a test does."
#
# A guard that runs, resolves nothing, and prints PASS is that same defect one step further on:
# it is not merely uncalled, it is called and hollow.
#
# NO PIPELINES (P-57/P-81): `cmd | sed` discards the producer's status unless `pipefail` happens
# to be set, and an instrument whose status depends on a shell option set elsewhere is one
# `set +o pipefail` from fail-open. Every read here is over a FILE.
#
# EXIT CODES, never conflated (P-80):
#   0  frontier == pin
#   1  a REAL measured violation: the frontier grew, or shrank without the pin being updated
#   2  ERROR -- a path this guard depends on did not resolve, or the census refused
#
# PROBE LINE: `T316-DEADPATH-FRONTIER:` -- printed on every path that REACHES A VERDICT, and
# never on exit 2. P-84 applies as written: "'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING.
# READ THE ABSENCE, NOT THE VALUE." Test for the line's PRESENCE before its value.

set -u

PROBE="T316-DEADPATH-FRONTIER:"

# --- locate the repo root without a pipeline -------------------------------------------------
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SELF_DIR/.." && pwd)
REPO_ROOT=$(dirname -- "$REPO_ROOT")

if [ ! -d "$REPO_ROOT/.git" ] && [ ! -f "$REPO_ROOT/.git" ]; then
  echo "ERROR: no .git at the derived repo root: $REPO_ROOT" >&2
  echo "ERROR: this guard cannot establish where it is. REFUSING (exit 2)." >&2
  exit 2
fi

CENSUS="$REPO_ROOT/.softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
PIN="$REPO_ROOT/.softhouse/guards/dead-path-frontier.pin"

# --- EVERY DEPENDENCY IS CHECKED, AND A MISSING ONE IS A REFUSAL -----------------------------
# This is the whole point of the task that produced this guard. An instrument that shrugs at a
# missing dependency and exits 0 is indistinguishable, from the outside, from one that checked
# everything and found it well.
for dep in "$CENSUS" "$PIN"; do
  if [ ! -f "$dep" ]; then
    echo "ERROR: a path this guard DEPENDS ON does not resolve:" >&2
    echo "         $dep" >&2
    echo "ERROR: REFUSING (exit 2). A guard that cannot reach what it grades has not graded it," >&2
    echo "ERROR: and must never report PASS for lack of anything to check." >&2
    exit 2
  fi
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not on PATH. The census cannot run. REFUSING (exit 2)." >&2
  exit 2
fi

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t316-frontier.XXXXXX") || {
  echo "ERROR: could not create a scratch directory. REFUSING (exit 2)." >&2
  exit 2
}
trap 'rm -rf "$SCRATCH"' EXIT INT TERM

CJSON="$SCRATCH/census.json"
COUT="$SCRATCH/census.out"

# The census writes ONLY where it is told to (its bare run is read-only), so a graded run cannot
# dirty the tree it is grading -- the defect T299 repaired in the T238 linter.
python3 "$CENSUS" --json "$CJSON" >"$COUT" 2>&1
census_rc=$?

if [ "$census_rc" -ne 0 ]; then
  echo "ERROR: the census refused (exit $census_rc). Its output follows. This guard does NOT" >&2
  echo "ERROR: substitute a zero for a measurement it failed to take (P-81)." >&2
  sed -n '1,60p' "$COUT" >&2
  exit 2
fi

# PRESENCE BEFORE VALUE (P-84): if the census produced no probe line it did not reach a count,
# whatever its exit status said.
if ! grep -q "T316-DEADPATH-CENSUS:" "$COUT"; then
  echo "ERROR: the census exited 0 but printed NO probe line. It did not reach a count." >&2
  echo "ERROR: That is an INSTRUMENT FAILURE, not an absence of findings (P-84)." >&2
  exit 2
fi

if [ ! -s "$CJSON" ]; then
  echo "ERROR: the census wrote no JSON to $CJSON. REFUSING (exit 2)." >&2
  exit 2
fi

# --- derive the observed frontier -------------------------------------------------------------
OBS="$SCRATCH/observed.txt"
python3 - "$CJSON" >"$OBS" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
rows = []
for f in doc["deadFiles"]:
    for d in doc["perFile"][f]["dead"]:
        rows.append("%s | %s" % (f, d))
for r in sorted(set(rows)):
    print(r)
PY
if [ $? -ne 0 ]; then
  echo "ERROR: could not derive the frontier from the census JSON. REFUSING (exit 2)." >&2
  exit 2
fi

WANT="$SCRATCH/want.txt"
grep -v '^#' "$PIN" >"$WANT.raw" 2>/dev/null
grep -v '^[[:space:]]*$' "$WANT.raw" >"$WANT.stripped" 2>/dev/null
sort "$WANT.stripped" >"$WANT" 2>/dev/null

# A pin that reads as EMPTY is a broken read, not an empty frontier. Refuse.
if [ ! -s "$WANT" ]; then
  echo "ERROR: the pin file read as EMPTY: $PIN" >&2
  echo "ERROR: an empty pin is a failed READ, never an empty frontier. REFUSING (exit 2)." >&2
  exit 2
fi

obs_n=$(grep -ac '' "$OBS")
want_n=$(grep -ac '' "$WANT")

DIFF="$SCRATCH/diff.txt"
diff "$WANT" "$OBS" >"$DIFF" 2>&1
diff_rc=$?

echo "conformance: CENSUS dead repo-path references among tracked .softhouse/ instruments"
echo "conformance:   selector and per-bucket counts are printed by the census itself:"
grep "T316-DEADPATH-CENSUS:" "$COUT"
echo "conformance:   frontier $obs_n row(s), pinned at $want_n"
echo "conformance:   (both cardinals DERIVED by counting the files compared, never typed)"

if [ "$diff_rc" -eq 0 ]; then
  echo "conformance:   frontier == pinned (all $want_n row(s), by path AND by literal)"
  echo "$PROBE GREEN rows=$obs_n pinned=$want_n added=0 removed=0"
  exit 0
fi

ADDED="$SCRATCH/added.txt"
REMOVED="$SCRATCH/removed.txt"
grep '^>' "$DIFF" >"$ADDED" 2>/dev/null
grep '^<' "$DIFF" >"$REMOVED" 2>/dev/null
added_n=$(grep -ac '' "$ADDED")
removed_n=$(grep -ac '' "$REMOVED")

echo "conformance: !! THE DEAD-PATH FRONTIER MOVED."
if [ "$added_n" -gt 0 ]; then
  echo "conformance: !! $added_n NEW dead path reference(s). A '+' row is a NEW site: REPAIR it"
  echo "conformance: !! rather than pinning it. Either make the path resolve, or -- if the"
  echo "conformance: !! reference is a deliberate fallback candidate -- make the instrument"
  echo "conformance: !! REFUSE when no candidate resolves, and record why in the pin."
  sed -n '1,40p' "$ADDED"
fi
if [ "$removed_n" -gt 0 ]; then
  echo "conformance: !! $removed_n row(s) GONE from the frontier. That is GOOD NEWS, and the pin"
  echo "conformance: !! must lose the row IN THE SAME COMMIT, or it starts excusing a weakness"
  echo "conformance: !! that is no longer there (conformance.sh:1715 -- a frontier, not an amnesty)."
  sed -n '1,40p' "$REMOVED"
fi
echo "conformance:   The pin is $PIN"
echo "$PROBE REFUSED rows=$obs_n pinned=$want_n added=$added_n removed=$removed_n"
exit 1
