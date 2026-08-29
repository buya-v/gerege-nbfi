#!/usr/bin/env bash
# =============================================================================================
# T458 -- RED AND GREEN DRIVE OF THE NEW REMEDY TEXT IN THE DEAD-PATH FRONTIER GUARD'S REFUSAL.
#
# WHAT IS BEING DRIVEN. T458 added a REMEDY block to the refusal printed by the dead-path
# frontier guard when the frontier GROWS. Item 2 of the task requires that block driven RED (it
# prints when the frontier grows) and GREEN (it does NOT print when the frontier equals the pin).
# A message that is never observed printing is not a message; a message that prints
# unconditionally teaches nothing about the condition.
#
# THIS INSTRUMENT OBEYS THE PATTERN IT EXISTS TO DOCUMENT, and that is deliberate -- the author
# of a rule about fixture literals is the last person who may spell one.
#   * NO repo-relative path is spelled as a quoted literal. The directory name is held in `S`
#     and every path is BUILT from it. This is remedy 1 of the three the refusal now names.
#   * EVERY location this drive depends on is a REQUIRED PARAMETER with no default, and a value
#     that does not resolve is a HARD EXIT (2), never a skip and never a pass. Remedy 2.
#   * EVERY negative this drive reports is CALIBRATED first: before asserting "the remedy text
#     is ABSENT from the green transcript" it proves the text is PRESENT in the guard's source,
#     because otherwise the absence is trivially true and measures nothing. Remedy 3 -- an
#     instrument must not print a negative it did not establish it could have seen.
#
# PARAMETERS (all required, all hard-exit on non-resolution):
#   T458_SRC   absolute path of the repository under test (the COMMITTED tree)
#   T458_OUT   absolute path of a directory to write transcripts into
#   T458_TMP   absolute path of a SCRATCH directory OUTSIDE the repository, for the red clone
#
# EXIT: 0 both arms behaved as specified; 1 an arm did not; 2 this drive could not measure.
# PROBE LINE: `T458-REMEDY-DRIVE:` -- printed only on a path that REACHES A VERDICT, never on
# exit 2. Read its PRESENCE before its value.
# =============================================================================================
set -u

PROBE="T458-REMEDY-DRIVE:"
S=".softhouse"

die2() { printf 'ERROR: %s\n' "$*" >&2; printf 'ERROR: REFUSING (exit 2) -- not a finding.\n' >&2; exit 2; }

SRC="${T458_SRC:?T458_SRC is required: the repository under test. No default (P-103 remedy 2).}"
OUT="${T458_OUT:?T458_OUT is required: where transcripts are written. No default.}"
TMP="${T458_TMP:?T458_TMP is required: a scratch dir OUTSIDE the repo. No default.}"

[ -d "$SRC" ] || die2 "T458_SRC does not resolve to a directory: $SRC"
[ -d "$OUT" ] || die2 "T458_OUT does not resolve to a directory: $OUT"
[ -d "$TMP" ] || die2 "T458_TMP does not resolve to a directory: $TMP"

case "$TMP" in
  "$SRC"|"$SRC"/*) die2 "T458_TMP is INSIDE the repository. Scratch must live outside it." ;;
esac

GUARD="$SRC/$S/guards/check-dead-path-frontier.sh"
[ -f "$GUARD" ] || die2 "the guard under drive did not resolve: $GUARD"

command -v git     >/dev/null 2>&1 || die2 "git is not on PATH."
command -v python3 >/dev/null 2>&1 || die2 "python3 is not on PATH; the census cannot run."

# The anchor sentence the refusal now points at. Held once, here, and compared against BOTH the
# guard's source and its output, so a reworded guard makes this drive REFUSE rather than pass.
ANCHOR="A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE"
REMEDY_HEAD="THE REMEDY, because SIX workers in one fire each rediscovered it"
FORBIDDEN="THE FORBIDDEN FOURTH"

echo "== T458 REMEDY-TEXT DRIVE =="
echo "   git      : $(git --version)"
echo "   python3  : $(python3 -V 2>&1)"
echo "   SRC      : $SRC"
SRC_HEAD=$(git -C "$SRC" rev-parse HEAD 2>/dev/null)
[ -n "$SRC_HEAD" ] || die2 "could not read HEAD of T458_SRC. An unreadable sha is an ERROR, never a blank."
echo "   HEAD     : $SRC_HEAD"
echo "   guard    : $GUARD"
echo

# --- CALIBRATION -----------------------------------------------------------------------------
# Prove the strings this drive looks for EXIST in the bytes under drive. Without this, every
# "ABSENT" below would be unfalsifiable and the green arm would pass on a guard that lost the
# message entirely.
echo "-- CALIBRATION: the three strings must be present in the guard's SOURCE"
cal=0
for needle in "$ANCHOR" "$REMEDY_HEAD" "$FORBIDDEN"; do
  n=$(LC_ALL=C grep -c -F -- "$needle" "$GUARD" || true)
  [ -n "$n" ] || n=0
  echo "   source hits = $n   for: $needle"
  [ "$n" -ge 1 ] || cal=1
done
[ "$cal" -eq 0 ] || die2 "the guard's source does not contain the remedy text this drive grades."
echo "   CALIBRATED: the drive can see the text it is about to report on."
echo

fail=0

# --- GREEN ARM -------------------------------------------------------------------------------
# The committed tree, unmodified. The frontier must equal the pin, and the remedy block must
# NOT print -- a refusal message that prints on a green run is decoration, not a refusal.
echo "== GREEN ARM: the committed tree, frontier == pin =="
GOUT="$OUT/20-GREEN-clean-tree.txt"
bash "$GUARD" >"$GOUT" 2>&1
grc=$?
gprobe=$(LC_ALL=C grep -c 'T316-DEADPATH-FRONTIER:' "$GOUT" || true); [ -n "$gprobe" ] || gprobe=0
echo "   exit           = $grc"
echo "   probe lines    = $gprobe      (PRESENCE read before VALUE)"
if [ "$gprobe" -lt 1 ]; then
  cat "$GOUT"
  die2 "the guard printed NO probe line on the green arm. Instrument failure, not a finding."
fi
gverdict=$(LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$GOUT" | tail -1)
echo "   probe line     = $gverdict"
ganchor=$(LC_ALL=C grep -c -F -- "$ANCHOR" "$GOUT" || true); [ -n "$ganchor" ] || ganchor=0
gremedy=$(LC_ALL=C grep -c -F -- "$REMEDY_HEAD" "$GOUT" || true); [ -n "$gremedy" ] || gremedy=0
echo "   anchor hits    = $ganchor      (expected 0 -- calibrated present in source above)"
echo "   remedy hits    = $gremedy      (expected 0)"
[ "$grc" -eq 0 ]     || { echo "   !! GREEN ARM: expected exit 0, got $grc"; fail=1; }
[ "$ganchor" -eq 0 ] || { echo "   !! GREEN ARM: the remedy anchor printed on a GREEN run"; fail=1; }
[ "$gremedy" -eq 0 ] || { echo "   !! GREEN ARM: the remedy head printed on a GREEN run"; fail=1; }
echo "   [$GOUT]"
echo

# --- RED ARM ---------------------------------------------------------------------------------
# A throwaway clone OUTSIDE the repository, carrying one planted instrument whose quoted string
# names a path the repository does not contain. The literal is ASSEMBLED here from `S`, never
# spelled -- if it were spelled, THIS file would join the frontier and the drive would become
# the defect it grades.
echo "== RED ARM: a scratch clone with ONE planted dead literal =="
CLONE="$TMP/red-clone"
rm -rf "$CLONE"
git clone --local --quiet "$SRC" "$CLONE" >"$OUT/09-clone.log" 2>&1 \
  || { cat "$OUT/09-clone.log"; die2 "could not clone the repository into scratch."; }

PLANT_DIR="$CLONE/$S/capture/t458-red-drive-specimen"
mkdir -p "$PLANT_DIR" || die2 "could not create the plant directory in the clone."
PLANT="$PLANT_DIR/planted-dead-literal.sh"
{
  printf '#!/usr/bin/env bash\n'
  printf '# PLANTED BY T458 IN A THROWAWAY CLONE. Never committed to this program.\n'
  printf '# The quoted string below is a repo-relative path the repository does not contain.\n'
  printf 'SPECIMEN="%s/capture/t458-no-such-directory/no-such-file.txt"\n' "$S"
  printf 'echo "$SPECIMEN"\n'
} >"$PLANT" || die2 "could not write the planted specimen."

git -C "$CLONE" add -- "$S/capture/t458-red-drive-specimen/planted-dead-literal.sh" \
  >"$OUT/09-plant.log" 2>&1 || { cat "$OUT/09-plant.log"; die2 "could not stage the specimen."; }
git -C "$CLONE" -c user.email=t458@local -c user.name=T458 \
  commit -q -m "T458 red-drive plant (throwaway clone)" >>"$OUT/09-plant.log" 2>&1 \
  || { cat "$OUT/09-plant.log"; die2 "could not commit the specimen in the clone."; }

# Prove the plant is actually TRACKED in the clone, or the red arm measures nothing.
tracked=$(git -C "$CLONE" ls-files -- "$S/capture/t458-red-drive-specimen/planted-dead-literal.sh" | LC_ALL=C grep -ac '' || true)
[ -n "$tracked" ] || tracked=0
echo "   planted file tracked in clone = $tracked   (must be 1, or the arm measures nothing)"
[ "$tracked" -eq 1 ] || die2 "the planted specimen is not tracked in the clone. The arm did not run."

ROUT="$OUT/30-RED-planted-literal.txt"
bash "$CLONE/$S/guards/check-dead-path-frontier.sh" >"$ROUT" 2>&1
rrc=$?
rprobe=$(LC_ALL=C grep -c 'T316-DEADPATH-FRONTIER:' "$ROUT" || true); [ -n "$rprobe" ] || rprobe=0
echo "   exit           = $rrc"
echo "   probe lines    = $rprobe      (PRESENCE read before VALUE)"
if [ "$rprobe" -lt 1 ]; then
  cat "$ROUT"
  die2 "the guard printed NO probe line on the red arm. Instrument failure, not a finding."
fi
rverdict=$(LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$ROUT" | tail -1)
echo "   probe line     = $rverdict"
ranchor=$(LC_ALL=C grep -c -F -- "$ANCHOR" "$ROUT" || true); [ -n "$ranchor" ] || ranchor=0
rremedy=$(LC_ALL=C grep -c -F -- "$REMEDY_HEAD" "$ROUT" || true); [ -n "$rremedy" ] || rremedy=0
rforbid=$(LC_ALL=C grep -c -F -- "$FORBIDDEN" "$ROUT" || true); [ -n "$rforbid" ] || rforbid=0
rplant=$(LC_ALL=C grep -c 't458-no-such-directory' "$ROUT" || true); [ -n "$rplant" ] || rplant=0
echo "   anchor hits    = $ranchor      (expected >= 1)"
echo "   remedy hits    = $rremedy      (expected >= 1)"
echo "   forbidden-4th  = $rforbid      (expected >= 1)"
echo "   planted row named in the listing = $rplant   (expected >= 1)"
[ "$rrc" -eq 1 ]     || { echo "   !! RED ARM: expected exit 1 (a real measured movement), got $rrc"; fail=1; }
[ "$ranchor" -ge 1 ] || { echo "   !! RED ARM: the refusal did NOT print the pattern anchor"; fail=1; }
[ "$rremedy" -ge 1 ] || { echo "   !! RED ARM: the refusal did NOT print the remedy"; fail=1; }
[ "$rforbid" -ge 1 ] || { echo "   !! RED ARM: the refusal did NOT print the forbidden fourth"; fail=1; }
[ "$rplant" -ge 1 ]  || { echo "   !! RED ARM: the refusal did not name the planted row; wrong cause"; fail=1; }
echo "   [$ROUT]"
echo

rm -rf "$CLONE"

if [ "$fail" -eq 0 ]; then
  echo "$PROBE PASS green=exit$grc/anchor$ganchor red=exit$rrc/anchor$ranchor/remedy$rremedy"
  exit 0
fi
echo "$PROBE FAIL green=exit$grc/anchor$ganchor red=exit$rrc/anchor$ranchor/remedy$rremedy"
exit 1
