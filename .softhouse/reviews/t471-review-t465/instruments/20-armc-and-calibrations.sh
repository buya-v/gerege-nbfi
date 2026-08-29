#!/usr/bin/env bash
# T471 -- ARM-C re-derived, plus MY OWN calibrations. The point of the calibrations is the one
# this program has had to relearn: A GREEN THAT COULD NOT HAVE GONE RED PROVES NOTHING. So each
# calibration is driven on the SAME materialised tree, in the SAME invocation, as the arm it
# calibrates, and its expected colour is asserted -- a calibration that comes out the wrong
# colour aborts the whole run instead of being reported as a curiosity.
#
# NO REAL REPO PATH IS SPELT AS A LITERAL (P-103): everything under the dot-directory is
# assembled from $S.
#
# ARMS, at one rev:
#   A   lock HELD,     pin as shipped                -> expect GREEN
#   B   lock RELEASED, pin as shipped                -> expect the frontier's own colour
#   C1  lock RELEASED, pin REWRITTEN to the released frontier -> expect GREEN
#   C2  lock HELD AGAIN, pin still at the released frontier   -> the fixed-point question
#   K+  lock HELD, pin as shipped, ONE planted dead literal   -> MUST refuse added=1
#   K-  lock HELD, pin as shipped, plant reverted             -> MUST return to GREEN
#
# EXIT 0 arms completed; 2 dependency/calibration failure.

set -u

S=".softhouse"
GUARD_REL="$S/guards/check-dead-path-frontier.sh"
PIN_REL="$S/guards/dead-path-frontier.pin"
CENSUS_REL="$S/capture/t316-dead-path-guards/census_dead_paths.py"
LOCK_REL="$S/LOCK"
PLANT_REL="$S/reviews/t471-review-t465/zz-calibration-plant.sh"
PROBE="T316-DEADPATH-FRONTIER:"

CLONE="${1:-}"; REV="${2:-}"; OUTDIR="${3:-}"; TAG="${4:-$REV}"
[ -n "$CLONE" ] && [ -n "$REV" ] && [ -n "$OUTDIR" ] || { echo "usage: $0 <clone> <rev> <outdir> [tag]" >&2; exit 2; }
case "$CLONE" in /Users/buv/gerege-nbfi*) echo "ERROR: clone must be OUTSIDE the graded repo." >&2; exit 2;; esac
[ -d "$OUTDIR" ] || { echo "ERROR: no outdir $OUTDIR" >&2; exit 2; }

WT=$(mktemp -d "${TMPDIR:-/tmp}/t471-armc.XXXXXX") || exit 2
rmdir "$WT"
git -C "$CLONE" worktree add --detach --quiet "$WT" "$REV" || { echo "ERROR: cannot materialise $REV" >&2; exit 2; }
git -C "$WT" config user.email t471@softhouse.local
git -C "$WT" config user.name "T471 reviewer"
for dep in "$WT/$GUARD_REL" "$WT/$PIN_REL" "$WT/$CENSUS_REL"; do
  [ -f "$dep" ] || { echo "ERROR: dependency missing: $dep -- REFUSING" >&2; exit 2; }
done

LAST_LINE=""
run_guard () {   # $1 arm label ; sets LAST_LINE
  local arm rc n f
  arm="$1"
  f="$OUTDIR/armc-$TAG-$arm.txt"
  bash "$WT/$GUARD_REL" >"$f" 2>&1; rc=$?
  n=$(grep -ac "$PROBE" "$f")
  printf 'ARM=%-28s exit=%s probe-lines=%s\n' "$arm" "$rc" "$n"
  if [ "$n" -eq 0 ]; then
    LAST_LINE=""
    echo "    NO PROBE LINE -- no verdict was reached; no value read."
    return 0
  fi
  LAST_LINE=$(grep -a "$PROBE" "$f")
  echo "    ${LAST_LINE#*"$PROBE" }"
  return 0
}

assert_colour () {  # $1 arm, $2 expected word
  case "$LAST_LINE" in
    *" $2 "*) : ;;
    *) echo "CALIBRATION FAILED: arm $1 expected $2, got: $LAST_LINE" >&2
       echo "REFUSING (exit 2). An arm whose calibration misbehaved cannot be read." >&2
       exit 2 ;;
  esac
}

# derive the observed frontier the way the guard does, and write it as a pin
rewrite_pin_to_observed () {
  local j="$WT/.t471-census.json"
  python3 "$WT/$CENSUS_REL" --json "$j" >/dev/null 2>&1 || { echo "ERROR: census refused" >&2; exit 2; }
  python3 - "$j" >"$WT/$PIN_REL.new" <<'PY'
import json,sys
doc=json.load(open(sys.argv[1]))
rows=set()
for f in doc["deadFiles"]:
    for d in doc["perFile"][f]["dead"]:
        rows.add("%s | %s"%(f,d))
for r in sorted(rows): print(r)
PY
  mv "$WT/$PIN_REL.new" "$WT/$PIN_REL"
  rm -f "$j"
  echo "    (pin rewritten to the OBSERVED frontier: $(grep -c '' "$WT/$PIN_REL") rows)"
}

echo "===== ARM-C / CALIBRATIONS, rev $TAG ($REV) ====="

echo "--- ARM-A: lock HELD, shipped pin"
run_guard "A-LOCK-HELD"; assert_colour A GREEN

echo "--- K+ CALIBRATION: plant ONE dead literal in a tracked instrument, same tree"
# the planted literal is assembled at WRITE time so this script itself never spells it
PLANT_DEAD="$S/this-path-does-not-exist-t471/absent.txt"
mkdir -p "$(dirname -- "$WT/$PLANT_REL")"
{
  echo '#!/usr/bin/env bash'
  echo '# T471 CALIBRATION PLANT -- deliberately names a path the repository does not contain.'
  echo "cat \"$PLANT_DEAD\""
} >"$WT/$PLANT_REL"
git -C "$WT" add -- "$PLANT_REL" >/dev/null
git -C "$WT" commit -q -m "T471 K+ calibration plant" >/dev/null
run_guard "Kplus-PLANTED"; assert_colour K+ REFUSED
case "$LAST_LINE" in
  *added=1*) echo "    K+ ok: the guard attributed exactly one new row." ;;
  *) echo "CALIBRATION FAILED: K+ refused but not with added=1: $LAST_LINE" >&2; exit 2 ;;
esac

echo "--- K- CALIBRATION: revert the plant, same tree"
git -C "$WT" rm -q -- "$PLANT_REL" >/dev/null
git -C "$WT" commit -q -m "T471 K- revert the plant" >/dev/null
run_guard "Kminus-REVERTED"; assert_colour K- GREEN
echo "    K-/K+ together: this tree's GREEN COULD have gone RED. The arms below are readable."

echo "--- ARM-B: lock RELEASED (rm, stage, commit), shipped pin"
if [ -f "$WT/$LOCK_REL" ]; then
  rm -f "$WT/$LOCK_REL"
  git -C "$WT" add -A -- "$LOCK_REL" >/dev/null 2>&1
  git -C "$WT" commit -q -m "T471 arm B: release the lock" >/dev/null 2>&1
fi
run_guard "B-LOCK-RELEASED"

case "$LAST_LINE" in
  *GREEN*)
    echo "--- ARM-C SKIPPED: arm B is GREEN, so the released state has no separate frontier"
    echo "    to pin. There is nothing for a pin value to be a fixed point OF."
    ;;
  *)
    echo "--- ARM-C1: pin REWRITTEN to the released-state frontier"
    rewrite_pin_to_observed
    run_guard "C1-PIN-AT-RELEASED"; assert_colour C1 GREEN
    echo "--- ARM-C2: the lock comes BACK (the next fire starts), pin still at the released value"
    git -C "$WT" checkout -q "$REV" -- "$LOCK_REL"
    git -C "$WT" commit -q -m "T471 arm C2: the next fire takes the lock" >/dev/null
    run_guard "C2-PIN-AT-RELEASED-LOCK-BACK"
    echo "    ^ THIS is the fixed-point question: if C1 and C2 cannot both be GREEN,"
    echo "      no STATIC pin value is green in both lock states."
    ;;
esac

echo "WT_KEPT=$WT"
