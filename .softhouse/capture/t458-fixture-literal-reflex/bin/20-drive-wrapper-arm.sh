#!/usr/bin/env bash
# =============================================================================================
# T458 -- RED AND GREEN DRIVE OF THE WRAPPER ARM'S REMEDY LINE.
#
# The guard prints one refusal; the harness wrapper that calls it prints ANOTHER, on the arm
# headed "THE FRONTIER MOVED IN A WAY NOBODY RECORDED". A reader can stop at that second message
# without ever reading the guard's transcript above it, so T458 put the one-line remedy there
# too. `10-drive-remedy-text.sh` drives the GUARD's message; this drives the WRAPPER's, which
# means running the whole bar, because that arm exists only inside it.
#
# SAME DISCIPLINE AS ITS SIBLING (P-103 applied to its own author):
#   * no repo-relative path is spelled as a quoted literal -- `S` holds the directory name;
#   * every location is a REQUIRED PARAMETER with no default and a HARD EXIT (2) if it does not
#     resolve;
#   * the negative reported by the GREEN arm is CALIBRATED first against the harness source, so
#     "the remedy line did not print" cannot be trivially true.
#
# WHAT "RED" MEANS HERE. The bar goes EXIT 2 WITH NO ORACLE PROBE LINE -- a failed HARD guard,
# which is the guard working and is NOT an oracle outage. That is precisely the shape five of
# the six workers saw, so this arm reproduces their transcript as well as the message.
#
# PARAMETERS: T458_SRC (repo under test), T458_OUT (transcript dir), T458_TMP (scratch, OUTSIDE
# the repo). EXIT: 0 both arms as specified; 1 an arm was not; 2 could not measure.
# PROBE LINE: `T458-WRAPPER-DRIVE:` -- printed only on a path that reaches a verdict.
# =============================================================================================
set -u

PROBE="T458-WRAPPER-DRIVE:"
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

BAR="$SRC/$S/conformance.sh"
[ -f "$BAR" ] || die2 "the harness under drive did not resolve: $BAR"
command -v git >/dev/null 2>&1 || die2 "git is not on PATH."

WRAPPER_LINE="THE REMEDY, in one line: build the path from a variable at run time"
ANCHOR="A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE"
ARM_HEAD="THE FRONTIER MOVED IN A WAY NOBODY RECORDED"

echo "== T458 WRAPPER-ARM DRIVE =="
echo "   git   : $(git --version)"
echo "   SRC   : $SRC"
SRC_HEAD=$(git -C "$SRC" rev-parse HEAD 2>/dev/null)
[ -n "$SRC_HEAD" ] || die2 "could not read HEAD of T458_SRC. An unreadable sha is an ERROR."
echo "   HEAD  : $SRC_HEAD"
echo

echo "-- CALIBRATION: the wrapper's remedy line and its arm head must exist in the harness source"
cal=0
for needle in "$WRAPPER_LINE" "$ANCHOR" "$ARM_HEAD"; do
  n=$(LC_ALL=C grep -c -F -- "$needle" "$BAR" || true); [ -n "$n" ] || n=0
  echo "   source hits = $n   for: $needle"
  [ "$n" -ge 1 ] || cal=1
done
[ "$cal" -eq 0 ] || die2 "the harness source does not contain the text this drive grades."
echo "   CALIBRATED."
echo

fail=0

# --- RED ARM: the whole bar, in a clone carrying one planted dead literal --------------------
echo "== RED ARM: full bar in a scratch clone with ONE planted dead literal =="
CLONE="$TMP/wrapper-clone"
rm -rf "$CLONE"
git clone --local --quiet "$SRC" "$CLONE" >"$OUT/39-clone.log" 2>&1 \
  || { cat "$OUT/39-clone.log"; die2 "could not clone the repository into scratch."; }

REL="$S/capture/t458-red-drive-specimen/planted-dead-literal.sh"
mkdir -p "$CLONE/$S/capture/t458-red-drive-specimen" || die2 "could not create the plant directory."
{
  printf '#!/usr/bin/env bash\n'
  printf '# PLANTED BY T458 IN A THROWAWAY CLONE. Never committed to this program.\n'
  printf 'SPECIMEN="%s/capture/t458-no-such-directory/no-such-file.txt"\n' "$S"
  printf 'echo "$SPECIMEN"\n'
} >"$CLONE/$REL" || die2 "could not write the planted specimen."
git -C "$CLONE" add -- "$REL" >"$OUT/39-plant.log" 2>&1 || { cat "$OUT/39-plant.log"; die2 "could not stage the specimen."; }
git -C "$CLONE" -c user.email=t458@local -c user.name=T458 commit -q -m "T458 wrapper red-drive plant" \
  >>"$OUT/39-plant.log" 2>&1 || { cat "$OUT/39-plant.log"; die2 "could not commit the specimen."; }
tracked=$(git -C "$CLONE" ls-files -- "$REL" | LC_ALL=C grep -ac '' || true); [ -n "$tracked" ] || tracked=0
echo "   planted file tracked in clone = $tracked   (must be 1, or the arm measures nothing)"
[ "$tracked" -eq 1 ] || die2 "the planted specimen is not tracked. The arm did not run."

ROUT="$OUT/40-RED-wrapper-arm-full-bar.txt"
bash "$CLONE/$S/conformance.sh" >"$ROUT" 2>&1
rrc=$?
rprobe=$(LC_ALL=C grep -c 'probe = ' "$ROUT" || true); [ -n "$rprobe" ] || rprobe=0
rarm=$(LC_ALL=C grep -c -F -- "$ARM_HEAD" "$ROUT" || true); [ -n "$rarm" ] || rarm=0
rrem=$(LC_ALL=C grep -c -F -- "$WRAPPER_LINE" "$ROUT" || true); [ -n "$rrem" ] || rrem=0
ranc=$(LC_ALL=C grep -c -F -- "$ANCHOR" "$ROUT" || true); [ -n "$ranc" ] || ranc=0
echo "   bar exit          = $rrc     (2 expected: a failed HARD guard, NOT an oracle outage)"
echo "   'probe = ' lines  = $rprobe     (0 expected -- read the ABSENCE, not a value)"
echo "   wrapper arm head  = $rarm     (expected >= 1)"
echo "   wrapper remedy    = $rrem     (expected >= 1)"
echo "   pattern anchor    = $ranc     (expected >= 2: guard message AND wrapper arm)"
[ "$rrc" -eq 2 ] || { echo "   !! RED ARM: expected bar exit 2, got $rrc"; fail=1; }
[ "$rarm" -ge 1 ] || { echo "   !! RED ARM: the wrapper arm did not fire"; fail=1; }
[ "$rrem" -ge 1 ] || { echo "   !! RED ARM: the wrapper printed no remedy"; fail=1; }
[ "$ranc" -ge 2 ] || { echo "   !! RED ARM: the anchor did not print at BOTH sites"; fail=1; }
echo "   [$ROUT]"
echo

rm -rf "$CLONE"

# --- GREEN ARM ------------------------------------------------------------------------------
# The wrapper arm must be SILENT when the frontier equals the pin. The green full-bar transcript
# is the one taken on the committed tree by the handoff's own bar run; this arm re-reads it
# rather than paying for a second bar. It is a REQUIRED parameter, so a missing transcript is a
# refusal and never a silently-skipped arm.
GBAR="${T458_GREEN_BAR:?T458_GREEN_BAR is required: the green full-bar transcript on the committed tree.}"
[ -f "$GBAR" ] || die2 "T458_GREEN_BAR does not resolve to a file: $GBAR"
echo "== GREEN ARM: the same harness, frontier == pin =="
gprobe=$(LC_ALL=C grep -c 'probe = ' "$GBAR" || true); [ -n "$gprobe" ] || gprobe=0
garm=$(LC_ALL=C grep -c -F -- "$ARM_HEAD" "$GBAR" || true); [ -n "$garm" ] || garm=0
grem=$(LC_ALL=C grep -c -F -- "$WRAPPER_LINE" "$GBAR" || true); [ -n "$grem" ] || grem=0
ganc=$(LC_ALL=C grep -c -F -- "$ANCHOR" "$GBAR" || true); [ -n "$ganc" ] || ganc=0
gfront=$(LC_ALL=C grep -c 'dead-path frontier: GREEN' "$GBAR" || true); [ -n "$gfront" ] || gfront=0
echo "   'probe = ' lines  = $gprobe     (PRESENCE read before VALUE)"
echo "   frontier GREEN    = $gfront     (expected >= 1 -- proves the arm HAD the chance to fire)"
echo "   wrapper arm head  = $garm     (expected 0)"
echo "   wrapper remedy    = $grem     (expected 0)"
echo "   pattern anchor    = $ganc     (expected 0)"
[ "$gprobe" -ge 1 ] || { echo "   !! GREEN ARM: no probe line in the green transcript; it is not a green bar"; fail=1; }
[ "$gfront" -ge 1 ] || { echo "   !! GREEN ARM: the transcript does not show a GREEN frontier; nothing was measured"; fail=1; }
[ "$garm" -eq 0 ] || { echo "   !! GREEN ARM: the wrapper arm fired on a green frontier"; fail=1; }
[ "$grem" -eq 0 ] || { echo "   !! GREEN ARM: the wrapper remedy printed on a green frontier"; fail=1; }
[ "$ganc" -eq 0 ] || { echo "   !! GREEN ARM: the anchor printed on a green frontier"; fail=1; }
echo "   [$GBAR]"
echo

if [ "$fail" -eq 0 ]; then
  echo "$PROBE PASS red=exit$rrc/arm$rarm/remedy$rrem/anchor$ranc green=arm$garm/remedy$grem/anchor$ganc"
  exit 0
fi
echo "$PROBE FAIL red=exit$rrc/arm$rarm/remedy$rrem/anchor$ranc green=arm$garm/remedy$grem/anchor$ganc"
exit 1
