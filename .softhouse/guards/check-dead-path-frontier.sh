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
# THE PIN IS A FRONTIER, NOT AN AMNESTY -- the block in `conformance.sh` headed with that same
# sentence (P-86: GREP THE SENTENCE, the line moves. That citation read `conformance.sh:1715`
# until T326 measured it: the text is at :1727 and the cardinal was stale by 12 lines on main
# BEFORE this guard was written). Quoted because the rule is theirs and not mine: "A '+' row
# is a NEW site: repair it ... rather than pinning it. A '-' row
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
  # ---------------------------------------------------------------------------------------
  # T458 -- THE REFUSAL MUST TEACH THE FIX.
  # Six workers in local fire 20260829-080002 (T440, T446, T447, T448, T451, T452) each had
  # their FIRST committed bar refused by this reflex, and each rediscovered the same small
  # remedy from scratch -- four of them AFTER it had already been written down. A refusal
  # that names WHAT is wrong but not WHAT TO DO buys one lesson per worker and buys it
  # again every time. So the message names the remedy, and anchors to a SENTENCE rather
  # than a line number or a pattern id, because both of those move and the sentence does not.
  #
  # T470 -- THE REFUSAL MUST NOT ARGUE WITH ITSELF.
  # As T458 shipped it, this block read "Do ONE of these three, and never a fourth" and called
  # remedy 2 the arm asked for "in exchange for NOT PINNING the row". Neither is what this
  # guard asks. Immediately above the row listing, unchanged since T316, this same message
  # OFFERS the pin route ("record why in the pin"); the header block WHAT A ROW DOES **NOT**
  # MEAN sanctions it in terms ("either repaired or pinned with its reason");
  # `dead-path-frontier.pin` EXERCISES it
  # for the two FU-T299-2 ordered-fallback rows, with the reason recorded above them; and
  # `conformance.sh` exercises it again for T305's four red-drive rows ("They are pinned here,
  # with the reason"). So the shipped text forbade, inside one screen, a disposition the same
  # screen offers and the tree takes twice. That is the species of defect this file already
  # records at the `removed_n` arm in `conformance.sh` -- "[T358: ... a false statement inside
  # a refusal message.]" -- and T458 also carried the narrower half into the permanent register
  # as P-103's "forbidden fourth". Both sites are corrected; the register FORWARD, never in
  # place (see the T470 erratum at the foot of patterns.md).
  # THE PRESUMPTION IS UNCHANGED AND DELIBERATELY SO: a '+' row is a NEW site, REPAIR IT. The
  # pin is the documented exception, gated on ordered-fallback-or-dead-by-design PLUS the
  # refuse-when-nothing-resolves arm. Widening it to "pin anything awkward" is the amnesty this
  # frontier exists to prevent.
  # ---------------------------------------------------------------------------------------
  echo "conformance: !! ----------------------------------------------------------------"
  echo "conformance: !! THE REMEDY, because SIX workers in one fire each rediscovered it:"
  echo "conformance: !!   T440, T446, T447, T448, T451, T452 -- every one of them repaired"
  echo "conformance: !!   the INSTRUMENT, and not one of them grew the pin. THAT IS WHAT SIX"
  echo "conformance: !!   WORKERS DID; it is not the only disposition this guard sanctions."
  echo "conformance: !!   To REPAIR, do ONE of these three. If you are NOT repairing, there"
  echo "conformance: !!   is exactly ONE other sanctioned route, and it is named after them:"
  echo "conformance: !!   1. ASSEMBLE the path at run time from a variable -- S='.softhouse'"
  echo "conformance: !!      and build downward. This census reads QUOTED LITERALS ONLY, so"
  echo "conformance: !!      an assembled path is not a row. That is not evasion: it STATES"
  echo "conformance: !!      that the path is COMPUTED rather than REFERENCED, which is"
  echo "conformance: !!      exactly what a fixture or a scratch destination means."
  echo "conformance: !!   2. MAKE THE LOCATION A REQUIRED PARAMETER -- no default, and a"
  echo "conformance: !!      HARD EXIT when it does not resolve. Never a skipped case,"
  echo "conformance: !!      never a warning, never a pass. This is the arm this guard asks"
  echo "conformance: !!      for on EITHER route -- whether you repair the row away or pin"
  echo "conformance: !!      it. The sentence above requires it for the PIN route too."
  echo "conformance: !!   3. If the failure arm PRINTS instead of exiting, adopt T238's"
  echo "conformance: !!      sweeplib shape too, so the instrument cannot print a negative"
  echo "conformance: !!      it never measured. That is the sibling defect T446 was caught"
  echo "conformance: !!      by, in the same fire, for the same underlying reason."
  echo "conformance: !! ----------------------------------------------------------------"
  echo "conformance: !! THE ROUTE THAT IS NOT A REPAIR, AND IS STILL SANCTIONED:"
  echo "conformance: !!   PIN THE ROW WITH ITS REASON. Permitted ONLY where the reference is"
  echo "conformance: !!   a deliberate ORDERED-FALLBACK candidate, or is dead BY DESIGN, and"
  echo "conformance: !!   ONLY together with remedy 2's arm: the instrument must REFUSE when"
  echo "conformance: !!   NO candidate resolves. THIS REFUSAL ALREADY OFFERED IT ABOVE --"
  echo "conformance: !!   'record why in the pin'. This guard's own header SANCTIONS it: grep"
  echo "conformance: !!   this file for WHAT A ROW DOES **NOT** MEAN -- 'a dead literal is a"
  echo "conformance: !!   SMELL that must be inspected once, by a human, and then either"
  echo "conformance: !!   repaired or pinned with its reason. This guard counts; it does not"
  echo "conformance: !!   judge.' And this tree TAKES that route twice already: the pin holds"
  echo "conformance: !!   the two FU-T299-2 ordered-fallback rows with the reason written"
  echo "conformance: !!   above them, and conformance.sh holds T305's four red-drive rows on"
  echo "conformance: !!   the same terms -- 'They are pinned here, with the reason.'"
  echo "conformance: !!   It is the EXCEPTION, not the default -- six of six workers in fire"
  echo "conformance: !!   20260829-080002 repaired, and not one of them needed it."
  echo "conformance: !! ----------------------------------------------------------------"
  echo "conformance: !! THE FORBIDDEN FOURTH: do NOT split or concatenate the literal to"
  echo "conformance: !! slip past the selector. That leaves the false claim standing and"
  echo "conformance: !! removes the only instrument that would ever have found it."
  echo "conformance: !! (It is 'the FOURTH' because it is the fourth idea that occurs to a"
  echo "conformance: !! refused worker, not a fourth entry in a list. PINNING WITH A REASON"
  echo "conformance: !! IS NOT IT.)"
  echo "conformance: !! FULL RULE, the six measured row counts, and the three sub-classes:"
  echo "conformance: !! grep patterns.md for this SENTENCE -- the line number moves, and an"
  echo "conformance: !! id is a cardinal that rots, but the sentence relocates with its text:"
  echo "conformance: !!   A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE"
  echo "conformance: !! ----------------------------------------------------------------"
fi
if [ "$removed_n" -gt 0 ]; then
  echo "conformance: !! $removed_n row(s) GONE from the frontier. That is GOOD NEWS, and the pin"
  echo "conformance: !! must lose the row IN THE SAME COMMIT, or it starts excusing a weakness"
  echo "conformance: !! that is no longer there -- a frontier, not an amnesty. The rule is in"
  echo "conformance: !! conformance.sh; grep the sentence THE PIN IS A FRONTIER, NOT AN AMNESTY"
  echo "conformance: !! rather than a line number, because the line number moves."
  sed -n '1,40p' "$REMOVED"
fi
echo "conformance:   The pin is $PIN"
echo "$PROBE REFUSED rows=$obs_n pinned=$want_n added=$added_n removed=$removed_n"
exit 1
