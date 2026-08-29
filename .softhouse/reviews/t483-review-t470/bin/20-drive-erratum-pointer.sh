#!/usr/bin/env bash
# =============================================================================================
# T483 -- THE ONE CHANGE THIS REVIEW PROPOSES, DRIVEN RATHER THAN ADVISED (C-T483-1, MINOR).
#
# THE FINDING. T470 corrects P-103 FORWARD, which is the only disposition the append-only rule
# leaves open and which follows the T334 CITATION ERRATUM precedent already in the file. The
# consequence it does not close: the guard's refusal still sends a refused worker to P-103 BY
# ITS SENTENCE, that sentence lands on the entry at patterns.md:3835, and that entry's closing
# paragraph still reads "do not add the row to the pin". Nothing at the landing site says an
# erratum exists. So the refusal now teaches the pin route on screen and then hands the reader a
# citation to the superseded text -- with the erratum ~130 lines further down, unannounced.
#
# T470 could not repair that at :3835: editing the entry in place is what append-only forbids.
# But it CAN be closed in the block T470 was already writing, in the file T470 was already
# editing, with echo lines and nothing else. That is what this drive measures.
#
# THREE ARMS:
#   A  BEFORE -- T470's tip as shipped, planted dead literal. Measures the GAP:
#      the anchor prints, and no pointer to the erratum prints.
#   B  AFTER  -- the same tree plus the proposed echo lines. The pointer prints, the anchor
#      still prints, and THE FORBIDDEN FOURTH is still byte-identical.
#   C  REGRESSION -- T458's own drive AND T470's own drive re-run on arm B's tree. Both must
#      still PASS, or the proposal is refuted by the same standard T470 held T468's patch to.
#
# THE PROPOSED CHANGE IS ECHO-ONLY: no control flow, no variable, no exit code, no cardinal,
# no pin, no register edit. It anchors by SENTENCE, never by line number (P-86).
#
# THIS INSTRUMENT OBEYS P-103, the rule under review: `S` holds the directory name and every
# path is BUILT from it; every location is a required parameter with a hard exit; every count is
# read from a FILE; every negative is calibrated before it is reported.
#
# NOTE: no apostrophe may appear inside a `${var:?word}` message -- bash 3.2 mis-pairs it across
# lines. Recorded in the sibling drive after it bit this reviewer once.
#
# PARAMETERS (all required, all hard-exit 2 on non-resolution):
#   T483_SRC  repository under review    T483_OUT  transcripts    T483_TMP  scratch OUTSIDE repo
#   T483_TIP  the tip sha of T470
#
# EXIT: 0 every arm behaved as specified; 1 an arm did not; 2 could not measure.
# PROBE LINE: `T483-ERRATUM-POINTER-DRIVE:` -- never printed on exit 2. PRESENCE before VALUE.
# =============================================================================================
set -u

PROBE="T483-ERRATUM-POINTER-DRIVE:"
PROBE_T458="T458-REMEDY-DRIVE:"
PROBE_T470="T470-PINROUTE-DRIVE:"
S=".softhouse"

die2() { printf 'ERROR: %s\n' "$*" >&2; printf 'ERROR: REFUSING (exit 2) -- not a finding.\n' >&2; exit 2; }

SRC="${T483_SRC:?T483_SRC is required: the repository under review. No default (P-103 remedy 2).}"
OUT="${T483_OUT:?T483_OUT is required: where transcripts are written. No default.}"
TMP="${T483_TMP:?T483_TMP is required: a scratch dir OUTSIDE the repo. No default.}"
TIP="${T483_TIP:?T483_TIP is required: the tip sha of T470. No default.}"
BASE="${T483_BASE:?T483_BASE is required: the fork-point sha, for the T470 drive control arm.}"

[ -d "$SRC" ] || die2 "T483_SRC does not resolve to a directory: $SRC"
[ -d "$OUT" ] || die2 "T483_OUT does not resolve to a directory: $OUT"
[ -d "$TMP" ] || die2 "T483_TMP does not resolve to a directory: $TMP"
case "$TMP" in
  "$SRC"|"$SRC"/*) die2 "T483_TMP is INSIDE the repository. Scratch must live outside it." ;;
esac
command -v git     >/dev/null 2>&1 || die2 "git is not on PATH."
command -v python3 >/dev/null 2>&1 || die2 "python3 is not on PATH; the census cannot run."

GUARD_REL="$S/guards/check-dead-path-frontier.sh"
REGISTER_REL="$S/patterns.md"
T458_DRIVE_REL="$S/capture/t458-fixture-literal-reflex/bin/10-drive-remedy-text.sh"
T470_DRIVE_REL="$S/capture/t470-refusal-forecloses/bin/10-drive-pin-route.sh"

ANCHOR="A TRACKED INSTRUMENT'S QUOTED PATH IS A CLAIM ABOUT THIS TREE"
ERRATUM_ANCHOR="ERRATUM TO"
POINTER_MARK="THAT ENTRY IS CORRECTED FORWARD"
FORBIDDEN="THE FORBIDDEN FOURTH"
STALE_CLAUSE="do **not**"

cnt() { n=$(LC_ALL=C grep -c -F -- "$1" "$2" 2>/dev/null || true); [ -n "$n" ] || n=0; printf '%s' "$n"; }

echo "== T483 ERRATUM-POINTER DRIVE (the one change this review proposes) =="
echo "   git     : $(git --version)"
echo "   python3 : $(python3 -V 2>&1)"
echo "   SRC     : $SRC"
echo "   TIP     : $TIP"
echo

fail=0

# --- the proposed echo lines, held ONCE ------------------------------------------------------
PATCHER="$TMP/apply-pointer.py"
cat >"$PATCHER" <<'PYEOF'
import sys
p = sys.argv[1]
anchor = '  echo "conformance: !!   A TRACKED INSTRUMENT\'S QUOTED PATH IS A CLAIM ABOUT THIS TREE"\n'
added = (
 '  echo "conformance: !! THAT ENTRY IS CORRECTED FORWARD, and this file is APPEND-ONLY, so"\n'
 '  echo "conformance: !! its own closing paragraph still reads \'do not add the row to the"\n'
 '  echo "conformance: !! pin\'. That half is SUPERSEDED. Read it together with the erratum at"\n'
 '  echo "conformance: !! the foot of the same file -- grep it for: ERRATUM TO"\n'
)
t = open(p, encoding='utf-8').read()
if t.count(anchor) != 1:
    sys.stderr.write("ERROR: the anchor echo line occurs %d time(s), expected 1\n" % t.count(anchor))
    raise SystemExit(1)
t = t.replace(anchor, anchor + added)
open(p, 'w', encoding='utf-8').write(t)
PYEOF
[ -f "$PATCHER" ] || die2 "could not write the scratch patcher."

prepare() {
  _name="$1"; _patched="$2"
  _dir="$TMP/$_name"
  rm -rf "$_dir"
  git clone --local --quiet "$SRC" "$_dir" >"$OUT/09-clone-$_name.log" 2>&1 \
    || { cat "$OUT/09-clone-$_name.log" >&2; die2 "could not clone into scratch for $_name."; }
  git -C "$_dir" checkout -q "$TIP" >>"$OUT/09-clone-$_name.log" 2>&1 \
    || die2 "could not check out $TIP in $_name."
  [ -f "$_dir/$GUARD_REL" ] || die2 "the guard did not resolve in $_name."
  if [ "$_patched" = "yes" ]; then
    python3 "$PATCHER" "$_dir/$GUARD_REL" || die2 "could not apply the proposed lines in $_name."
    git -C "$_dir" -c user.email=t483@local -c user.name=T483 \
      commit -aqm "T483 scratch: proposed erratum pointer" >>"$OUT/09-clone-$_name.log" 2>&1 \
      || die2 "could not commit the proposal in $_name."
  fi
  printf '%s' "$_dir"
}

# Plant one dead literal in a throwaway clone of the tree under test, and run the guard there.
refuse() {
  _dir="$1"; _tag="$2"
  _clone="$TMP/$_tag-redclone"
  rm -rf "$_clone"
  git clone --local --quiet "$_dir" "$_clone" >"$OUT/09-plant-$_tag.log" 2>&1 \
    || die2 "could not clone $_tag for the plant."
  _pd="$_clone/$S/capture/t483-red-drive-specimen"
  mkdir -p "$_pd" || die2 "could not create the plant directory for $_tag."
  {
    printf '#!/usr/bin/env bash\n'
    printf '# PLANTED BY T483 IN A THROWAWAY CLONE. Never committed to this program.\n'
    printf 'SPECIMEN="%s/capture/t483-no-such-directory/no-such-file.txt"\n' "$S"
    printf 'echo "$SPECIMEN"\n'
  } >"$_pd/planted-dead-literal.sh" || die2 "could not write the plant for $_tag."
  git -C "$_clone" add -- "$S/capture/t483-red-drive-specimen/planted-dead-literal.sh" \
    >>"$OUT/09-plant-$_tag.log" 2>&1 || die2 "could not stage the plant for $_tag."
  git -C "$_clone" -c user.email=t483@local -c user.name=T483 \
    commit -qm "T483 plant" >>"$OUT/09-plant-$_tag.log" 2>&1 || die2 "could not commit the plant for $_tag."
  _tracked=$(git -C "$_clone" ls-files -- "$S/capture/t483-red-drive-specimen/planted-dead-literal.sh" | LC_ALL=C grep -ac '' || true)
  [ -n "$_tracked" ] || _tracked=0
  [ "$_tracked" -eq 1 ] || die2 "the plant is not tracked in $_tag; the arm would measure nothing."
  bash "$_clone/$GUARD_REL" >"$OUT/$_tag-refusal.txt" 2>&1
  printf '%s' "$?"
}

# --- CALIBRATION: the register's landing site really does still carry the stale half ----------
echo "-- CALIBRATION: what a reader meets AT the anchor's landing site in the register"
DIR_A=$(prepare "before" "no")
REG="$DIR_A/$REGISTER_REL"
[ -f "$REG" ] || die2 "the register did not resolve: $REG"
LAND=$(LC_ALL=C grep -n -F -- "$ANCHOR" "$REG" | head -1 | cut -d: -f1)
[ -n "$LAND" ] || die2 "the anchor sentence does not resolve in the register; cannot measure."
ERRLN=$(LC_ALL=C grep -n -F -- "$ERRATUM_ANCHOR" "$REG" | head -1 | cut -d: -f1)
[ -n "$ERRLN" ] || die2 "the erratum heading does not resolve in the register; cannot measure."
ENTRY="$TMP/p103-entry.txt"
LC_ALL=C sed -n "${LAND},$((LAND + 90))p" "$REG" >"$ENTRY"
stale=$(cnt "add the row to the pin" "$ENTRY")
fwd=$(cnt "$ERRATUM_ANCHOR" "$ENTRY")
echo "   anchor lands at register line          = $LAND"
echo "   erratum heading at register line       = $ERRLN   (distance $((ERRLN - LAND)) lines below)"
echo "   'add the row to the pin' in the entry  = $stale   (>=1 means the stale half is what a reader meets)"
echo "   pointer to the erratum in the entry    = $fwd     (0 means the reader is not told it exists)"
[ "$stale" -ge 1 ] || die2 "the stale clause is NOT at the landing site; this finding does not exist. Refusing to report it."
echo

# --- ARM A: BEFORE ---------------------------------------------------------------------------
RC_A=$(refuse "$DIR_A" "10-BEFORE")
TA="$OUT/10-BEFORE-refusal.txt"
pa=$(LC_ALL=C grep -c 'T316-DEADPATH-FRONTIER:' "$TA" || true); [ -n "$pa" ] || pa=0
a_anchor=$(cnt "$ANCHOR" "$TA"); a_ptr=$(cnt "$POINTER_MARK" "$TA"); a_err=$(cnt "$ERRATUM_ANCHOR" "$TA")
a_forbid=$(cnt "$FORBIDDEN" "$TA")
echo "== ARM A -- BEFORE: T470's tip as shipped =="
echo "   exit                                   = $RC_A"
echo "   probe lines                            = $pa   (PRESENCE before VALUE)"
[ "$pa" -ge 1 ] || { cat "$TA"; die2 "no probe line on arm A. Instrument failure, not a finding."; }
echo "   probe line = $(LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$TA" | tail -1)"
echo "   register anchor printed                = $a_anchor   (expected >= 1)"
echo "   pointer to the erratum printed         = $a_ptr      (expected 0 -- THE GAP)"
echo "   the word ERRATUM printed at all        = $a_err      (expected 0)"
echo "   THE FORBIDDEN FOURTH printed           = $a_forbid   (expected >= 1)"
[ "$RC_A" -eq 1 ]      || { echo "   !! ARM A: expected exit 1"; fail=1; }
[ "$a_anchor" -ge 1 ]  || { echo "   !! ARM A: the anchor did not print; the finding cannot be stated"; fail=1; }
[ "$a_ptr" -eq 0 ]     || { echo "   !! ARM A: the pointer already prints -- the finding does not exist"; fail=1; }
echo "   [$TA]"
echo

# --- ARM B: AFTER ----------------------------------------------------------------------------
DIR_B=$(prepare "after" "yes")
RC_B=$(refuse "$DIR_B" "20-AFTER")
TB="$OUT/20-AFTER-refusal.txt"
pb=$(LC_ALL=C grep -c 'T316-DEADPATH-FRONTIER:' "$TB" || true); [ -n "$pb" ] || pb=0
b_anchor=$(cnt "$ANCHOR" "$TB"); b_ptr=$(cnt "$POINTER_MARK" "$TB"); b_err=$(cnt "$ERRATUM_ANCHOR" "$TB")
b_forbid=$(cnt "$FORBIDDEN" "$TB")
b_route=$(cnt "PIN THE ROW WITH ITS REASON" "$TB")
echo "== ARM B -- AFTER: the same tree plus the proposed echo lines =="
echo "   exit                                   = $RC_B"
echo "   probe lines                            = $pb   (PRESENCE before VALUE)"
[ "$pb" -ge 1 ] || { cat "$TB"; die2 "no probe line on arm B. Instrument failure, not a finding."; }
echo "   probe line = $(LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$TB" | tail -1)"
echo "   register anchor printed                = $b_anchor   (expected >= 1 -- unchanged)"
echo "   pointer to the erratum printed         = $b_ptr      (expected >= 1 -- THE REPAIR)"
echo "   the erratum grep-anchor printed        = $b_err      (expected >= 1)"
echo "   THE FORBIDDEN FOURTH printed           = $b_forbid   (expected >= 1 -- byte-identical)"
echo "   T470's pin route still printed         = $b_route    (expected >= 1 -- not disturbed)"
[ "$RC_B" -eq 1 ]     || { echo "   !! ARM B: expected exit 1"; fail=1; }
[ "$b_anchor" -ge 1 ] || { echo "   !! ARM B: the anchor stopped printing"; fail=1; }
[ "$b_ptr" -ge 1 ]    || { echo "   !! ARM B: the proposed pointer did NOT print"; fail=1; }
[ "$b_forbid" -ge 1 ] || { echo "   !! ARM B: THE FORBIDDEN FOURTH was disturbed"; fail=1; }
[ "$b_route" -ge 1 ]  || { echo "   !! ARM B: T470's pin-route block was disturbed"; fail=1; }
echo "   [$TB]"
echo

# --- ARM C: REGRESSION -- both predecessors' drives on arm B's tree ---------------------------
echo "== ARM C -- REGRESSION: T458's drive AND T470's drive on the PROPOSED tree =="
SUB458="$OUT/30-t458-on-proposal"; SCR458="$TMP/t458scr"
rm -rf "$SUB458" "$SCR458"; mkdir -p "$SUB458" "$SCR458" || die2 "could not make T458 arm dirs."
T458_SRC="$DIR_B" T458_OUT="$SUB458" T458_TMP="$SCR458" \
  bash "$DIR_B/$T458_DRIVE_REL" >"$OUT/30-T458-drive-on-proposal.txt" 2>&1
RC458=$?
p458=$(LC_ALL=C grep -c "$PROBE_T458" "$OUT/30-T458-drive-on-proposal.txt" || true); [ -n "$p458" ] || p458=0
echo "   T458 drive exit  = $RC458   probe lines = $p458"
[ "$p458" -ge 1 ] && echo "   T458 probe line  = $(LC_ALL=C sed -n "s/^$PROBE_T458 //p" "$OUT/30-T458-drive-on-proposal.txt" | tail -1)"
[ "$RC458" -eq 0 ] || { echo "   !! REGRESSION: T458's drive no longer passes"; fail=1; }

SUB470="$OUT/40-t470-on-proposal"; SCR470="$TMP/t470scr"
rm -rf "$SUB470" "$SCR470"; mkdir -p "$SUB470" "$SCR470" || die2 "could not make T470 arm dirs."
T470_SRC="$DIR_B" T470_OUT="$SUB470" T470_TMP="$SCR470" T470_BASE="$BASE" \
  bash "$DIR_B/$T470_DRIVE_REL" >"$OUT/40-T470-drive-on-proposal.txt" 2>&1
RC470=$?
p470=$(LC_ALL=C grep -c "$PROBE_T470" "$OUT/40-T470-drive-on-proposal.txt" || true); [ -n "$p470" ] || p470=0
echo "   T470 drive exit  = $RC470   probe lines = $p470"
[ "$p470" -ge 1 ] && echo "   T470 probe line  = $(LC_ALL=C sed -n "s/^$PROBE_T470 //p" "$OUT/40-T470-drive-on-proposal.txt" | tail -1)"
[ "$RC470" -eq 0 ] || { echo "   !! REGRESSION: T470's own drive no longer passes"; fail=1; }
echo

if [ "$fail" -eq 0 ]; then
  echo "$PROBE PASS before=ptr$a_ptr after=ptr$b_ptr t458=$RC458 t470=$RC470 gap=$((ERRLN - LAND))lines"
  exit 0
fi
echo "$PROBE FAIL before=ptr$a_ptr after=ptr$b_ptr t458=$RC458 t470=$RC470"
exit 1
