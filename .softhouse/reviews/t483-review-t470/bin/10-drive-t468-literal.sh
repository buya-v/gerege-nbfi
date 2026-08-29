#!/usr/bin/env bash
# =============================================================================================
# T483 -- ADJUDICATION DRIVE FOR T470's CLAIM 2.
#
# THE CLAIM UNDER TEST, quoted from T470-handoff.md section 2a:
#   "T458's drive is re-run below and still passes on my bytes -- WHICH IT WOULD NOT HAVE UNDER
#    THE LITERAL section-6 TEXT."
# T470's first ground: T468's `Never a fifth` "de-synchronises the name THE FORBIDDEN FOURTH,
# which is asserted VERBATIM by T458's own drive (10-drive-remedy-text.sh:60,
# FORBIDDEN="THE FORBIDDEN FOURTH")".
#
# That is a falsifiable claim about bytes, so it is MEASURED rather than argued. T468's patch, as
# literally written, replaces ONE echo line -- `three, and never a fourth:` -- with two lines
# ending `Never a fifth:`. It does NOT touch the separate echo line that spells
# `THE FORBIDDEN FOURTH:`. So the question is whether T458's drive still finds that string.
#
# THREE ARMS, and the third is the control that makes the second meaningful:
#   A  T470's tip                             -> T458's drive expected PASS (exit 0)
#   B  T470's BASE + T468's patch VERBATIM    -> T458's drive: MEASURED
#   C  same as B, but ALSO renaming THE FORBIDDEN FOURTH -> THE FORBIDDEN FIFTH
#      -> T458's drive MUST exit 2 (its own CALIBRATION must refuse). Without arm C a PASS in
#         arm B would be unfalsifiable: it could mean "the drive is blind to that string".
#
# THIS INSTRUMENT OBEYS P-103, WHICH IS THE SUBJECT OF THE REVIEW IT SERVES.
#   * NO repo-relative path is spelled as a quoted literal. `S` holds the directory name and
#     every path is BUILT from it (remedy 1).
#   * EVERY location is a REQUIRED PARAMETER with no default; non-resolution is a HARD EXIT 2,
#     never a skip and never a pass (remedy 2).
#   * EVERY count is read from a FILE, never from a pipeline, and every negative is calibrated
#     before it is reported (P-22 / P-57 / P-81).
#
# PARAMETERS (all required, all hard-exit 2 on non-resolution):
#   T483_SRC   absolute path of the repository under review (a git repo carrying both shas)
#   T483_OUT   absolute path of a directory to write transcripts into
#   T483_TMP   absolute path of a SCRATCH directory OUTSIDE the repository
#   T483_TIP   the sha of T470's tip
#   T483_BASE  the sha of T470's fork point (T458 + T468 as delivered)
#
# EXIT: 0 all arms behaved as specified; 1 an arm did not; 2 this drive could not measure.
# PROBE LINE: `T483-T468LITERAL-DRIVE:` -- printed only on a path that REACHES A VERDICT, never
# on exit 2. Read its PRESENCE before its value (P-84).
# =============================================================================================
set -u

PROBE="T483-T468LITERAL-DRIVE:"
PROBE_T458="T458-REMEDY-DRIVE:"
S=".softhouse"

die2() { printf 'ERROR: %s\n' "$*" >&2; printf 'ERROR: REFUSING (exit 2) -- not a finding.\n' >&2; exit 2; }

SRC="${T483_SRC:?T483_SRC is required: the repository under review. No default (P-103 remedy 2).}"
OUT="${T483_OUT:?T483_OUT is required: where transcripts are written. No default.}"
TMP="${T483_TMP:?T483_TMP is required: a scratch dir OUTSIDE the repo. No default.}"
# NOTE, RECORDED RATHER THAN QUIETLY FIXED: no apostrophe may appear inside a `${var:?word}`
# message here. bash 3.2 -- the shell on this host -- mis-pairs a lone `'` inside such a word
# ACROSS LINES, and the first draft of this drive lost the whole BASE assignment into the TIP
# message because both said "T470's". The drive refused on its own second parameter and said so;
# an instrument that had defaulted instead would have run the wrong tree silently. Same family as
# the defects this review is about.
TIP="${T483_TIP:?T483_TIP is required: the tip sha of T470. No default.}"
BASE="${T483_BASE:?T483_BASE is required: the fork-point sha of T470. No default.}"

[ -d "$SRC" ] || die2 "T483_SRC does not resolve to a directory: $SRC"
[ -d "$OUT" ] || die2 "T483_OUT does not resolve to a directory: $OUT"
[ -d "$TMP" ] || die2 "T483_TMP does not resolve to a directory: $TMP"
case "$TMP" in
  "$SRC"|"$SRC"/*) die2 "T483_TMP is INSIDE the repository. Scratch must live outside it." ;;
esac
command -v git     >/dev/null 2>&1 || die2 "git is not on PATH."
command -v python3 >/dev/null 2>&1 || die2 "python3 is not on PATH; the census cannot run."

GUARD_REL="$S/guards/check-dead-path-frontier.sh"
DRIVE_REL="$S/capture/t458-fixture-literal-reflex/bin/10-drive-remedy-text.sh"

# The exact bytes T468 specifies. Held ONCE, here, so a typo cannot hide in three places.
OLD_LINE='  echo "conformance: !!   three, and never a fourth:"'
NEW_1='  echo "conformance: !!   three -- or, ONLY for a deliberate ordered-fallback candidate,"'
NEW_2='  echo "conformance: !!   the pin-with-a-reason route named four lines above. Never a fifth:"'
FORBIDDEN="THE FORBIDDEN FOURTH"

cnt() { LC_ALL=C grep -c -F -- "$1" "$2" 2>/dev/null || true; }

echo "== T483 ADJUDICATION DRIVE: does T468's LITERAL patch break T458's drive? =="
echo "   git     : $(git --version)"
echo "   python3 : $(python3 -V 2>&1)"
echo "   SRC     : $SRC"
echo "   TIP     : $TIP"
echo "   BASE    : $BASE"
echo

fail=0

# ---------------------------------------------------------------------------------------------
# prepare_tree <name> <sha> <mode>       mode: plain | t468literal | t468literal-renamed
# ---------------------------------------------------------------------------------------------
prepare_tree() {
  _name="$1"; _sha="$2"; _mode="$3"
  _dir="$TMP/$_name"
  rm -rf "$_dir"
  git clone --local --quiet "$SRC" "$_dir" >"$OUT/09-clone-$_name.log" 2>&1 \
    || { cat "$OUT/09-clone-$_name.log" >&2; die2 "could not clone into scratch for $_name."; }
  git -C "$_dir" checkout -q "$_sha" >>"$OUT/09-clone-$_name.log" 2>&1 \
    || die2 "could not check out $_sha in $_name."
  _g="$_dir/$GUARD_REL"
  [ -f "$_g" ] || die2 "the guard under drive did not resolve in $_name: $_g"
  [ -f "$_dir/$DRIVE_REL" ] || die2 "T458's drive did not resolve in $_name."

  if [ "$_mode" != "plain" ]; then
    _rename=0
    [ "$_mode" = "t468literal-renamed" ] && _rename=1
    T483_OLD="$OLD_LINE" T483_N1="$NEW_1" T483_N2="$NEW_2" T483_RENAME="$_rename" \
      python3 "$T483_PATCHER" "$_g" || die2 "could not apply the patch in $_name."
    git -C "$_dir" -c user.email=t483@local -c user.name=T483 \
      commit -aqm "T483 scratch tree: $_mode" >>"$OUT/09-clone-$_name.log" 2>&1 \
      || die2 "could not commit the patch in $_name."
  fi
  printf '%s' "$_dir"
}

# The patcher is written to SCRATCH, not shipped, and its absence is a hard exit.
T483_PATCHER="$TMP/apply-t468-literal.py"
cat >"$T483_PATCHER" <<'PYEOF'
import os, sys
p = sys.argv[1]
old = os.environ["T483_OLD"] + "\n"
new = os.environ["T483_N1"] + "\n" + os.environ["T483_N2"] + "\n"
t = open(p, encoding="utf-8").read()
if t.count(old) != 1:
    sys.stderr.write("ERROR: the T468 anchor line occurs %d time(s), expected exactly 1\n" % t.count(old))
    raise SystemExit(1)
t = t.replace(old, new)
if os.environ["T483_RENAME"] == "1":
    if "THE FORBIDDEN FOURTH" not in t:
        sys.stderr.write("ERROR: THE FORBIDDEN FOURTH absent; the control cannot be built\n")
        raise SystemExit(1)
    t = t.replace("THE FORBIDDEN FOURTH", "THE FORBIDDEN FIFTH")
open(p, "w", encoding="utf-8").write(t)
PYEOF
[ -f "$T483_PATCHER" ] || die2 "could not write the scratch patcher; the arms cannot be built."

# ---------------------------------------------------------------------------------------------
run_t458_drive() {
  _name="$1"; _dir="$2"
  _sub="$OUT/$_name-arm"; _scr="$TMP/$_name-t458tmp"
  rm -rf "$_sub" "$_scr"; mkdir -p "$_sub" "$_scr" || die2 "could not make arm dirs for $_name."
  T458_SRC="$_dir" T458_OUT="$_sub" T458_TMP="$_scr" \
    bash "$_dir/$DRIVE_REL" >"$OUT/$_name-t458drive.txt" 2>&1
  printf '%s' "$?"
}

report_arm() {
  _label="$1"; _name="$2"; _dir="$3"; _rc="$4"
  _t="$OUT/$_name-t458drive.txt"
  _g="$_dir/$GUARD_REL"
  _src_forbidden=$(cnt "$FORBIDDEN" "$_g")
  _fifth=$(cnt "Never a fifth:" "$_g")
  _fourth=$(cnt "three, and never a fourth:" "$_g")
  _probe=$(LC_ALL=C grep -c "$PROBE_T458" "$_t" 2>/dev/null || true); [ -n "$_probe" ] || _probe=0
  echo "== $_label =="
  echo "   guard SOURCE 'THE FORBIDDEN FOURTH'        = $_src_forbidden"
  echo "   guard SOURCE 'Never a fifth:'              = $_fifth"
  echo "   guard SOURCE 'three, and never a fourth:'  = $_fourth"
  echo "   T458 drive exit                            = $_rc"
  echo "   T458 drive probe lines                     = $_probe   (PRESENCE before VALUE)"
  if [ "$_probe" -ge 1 ]; then
    echo "   T458 drive probe line = $(LC_ALL=C sed -n "s/^$PROBE_T458 //p" "$_t" | tail -1)"
  fi
  echo "   [$_t]"
  echo
}

# --- ARM A: T470's tip, unmodified -----------------------------------------------------------
DIR_A=$(prepare_tree "armA-t470tip" "$TIP" "plain")
RC_A=$(run_t458_drive "armA-t470tip" "$DIR_A")
report_arm "ARM A -- T470's TIP: T458's own drive re-run on T470's bytes" "armA-t470tip" "$DIR_A" "$RC_A"
[ "$RC_A" -eq 0 ] || { echo "   !! ARM A: T458's drive did NOT pass on T470's tip (exit $RC_A)"; fail=1; }

# --- ARM B: BASE + T468's patch, VERBATIM ----------------------------------------------------
DIR_B=$(prepare_tree "armB-t468literal" "$BASE" "t468literal")
RC_B=$(run_t458_drive "armB-t468literal" "$DIR_B")
report_arm "ARM B -- BASE + T468's patch AS LITERALLY WRITTEN" "armB-t468literal" "$DIR_B" "$RC_B"

# --- ARM C: THE CONTROL ----------------------------------------------------------------------
DIR_C=$(prepare_tree "armC-control-renamed" "$BASE" "t468literal-renamed")
RC_C=$(run_t458_drive "armC-control-renamed" "$DIR_C")
report_arm "ARM C -- CONTROL: the patch PLUS renaming THE FORBIDDEN FOURTH to FIFTH" \
           "armC-control-renamed" "$DIR_C" "$RC_C"
[ "$RC_C" -eq 2 ] || { echo "   !! ARM C: expected exit 2 (T458's CALIBRATION must refuse), got $RC_C -- the control is not a control"; fail=1; }

# --- POSITIONAL CHECK: T468's "four lines above", measured in RENDERED output -----------------
# T470's SECOND ground. Measured on arm B's own RED transcript, which is the rendered refusal.
echo "== T470's SECOND GROUND: is 'four lines above' true in the RENDERED refusal? =="
RED_B="$OUT/armB-t468literal-arm/30-RED-planted-literal.txt"
if [ -f "$RED_B" ]; then
  OFFER_LN=$(LC_ALL=C grep -n -F -- "record why in the pin" "$RED_B" | head -1 | cut -d: -f1)
  FIFTH_LN=$(LC_ALL=C grep -n -F -- "Never a fifth:" "$RED_B" | head -1 | cut -d: -f1)
  [ -n "$OFFER_LN" ] || die2 "the pin OFFER did not print in arm B's RED transcript; cannot measure."
  [ -n "$FIFTH_LN" ] || die2 "'Never a fifth:' did not print in arm B's RED transcript; cannot measure."
  DIST=$((FIFTH_LN - OFFER_LN))
  echo "   'record why in the pin'  at rendered line $OFFER_LN"
  echo "   'Never a fifth:'         at rendered line $FIFTH_LN"
  echo "   distance                 = $DIST lines   (T468 asserts FOUR)"
  if [ "$DIST" -eq 4 ]; then
    echo "   => 'four lines above' is TRUE on this refusal. T470's second ground FAILS."
    POS="POSITIONAL=TRUE"
  else
    echo "   => 'four lines above' is FALSE on this refusal (it is $DIST). T470's second ground HOLDS."
    POS="POSITIONAL=FALSE-at-$DIST"
  fi
else
  die2 "arm B's RED transcript did not resolve: $RED_B"
fi
echo

# --- THE ADJUDICATION ------------------------------------------------------------------------
echo "== ADJUDICATION =="
if [ "$RC_B" -eq 0 ]; then
  echo "   T458's drive PASSES on T468's patch as literally written (exit $RC_B)."
  echo "   => T470's ground 1 -- 'T458's drive would NOT have passed under the literal text' --"
  echo "      is REFUTED. Arm C proves the drive IS sensitive to the name (exit $RC_C, a"
  echo "      CALIBRATION refusal), so arm B's pass is a measurement and not a blindness."
  echo "      T468's patch does not rename THE FORBIDDEN FOURTH; only T470's paraphrase does."
  VERDICT="T470-GROUND1=REFUTED"
else
  echo "   T458's drive did NOT pass on T468's patch as literally written (exit $RC_B)."
  echo "   => T470's ground 1 is UPHELD."
  VERDICT="T470-GROUND1=UPHELD"
fi
echo

if [ "$fail" -eq 0 ]; then
  echo "$PROBE PASS armA=$RC_A armB=$RC_B armC=$RC_C $VERDICT $POS"
  exit 0
fi
echo "$PROBE FAIL armA=$RC_A armB=$RC_B armC=$RC_C $VERDICT $POS"
exit 1
