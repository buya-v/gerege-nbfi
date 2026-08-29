#!/usr/bin/env bash
# =============================================================================================
# T470 -- RED AND GREEN DRIVE: THE PIN-WITH-ITS-REASON ROUTE SURVIVES AS A LEGITIMATE ROUTE.
#
# WHAT IS BEING DRIVEN. T458 gave the dead-path frontier guard's refusal a REMEDY block. T468
# found (C-T468-1, MAJOR) that the block, and the P-103 entry it wrote into the permanent
# register, FORECLOSE a disposition the SAME refusal message offers on the same screen, the
# guard's own header sanctions in terms, and this tree has already taken twice. T470 re-derived
# that and repaired both refusal sites. THIS DRIVE PROVES THE REPAIR, IN BOTH DIRECTIONS:
#
#   PRE-REPAIR CONTROL  the guard at the BASE commit, on the SAME planted clone, still prints
#                       the foreclosing strings and does NOT print the pin route. Without this
#                       arm every "ABSENT" below would be unfalsifiable -- a negative nobody
#                       established could have been a positive (the T446 defect, P-103 item 3).
#   RED ARM             the repaired guard, same plant: it refuses, and the refusal carries the
#                       pin route, the pre-existing "record why in the pin" offer, the header's
#                       own sanctioning sentence, and THE FORBIDDEN FOURTH -- while the two
#                       foreclosing strings are GONE.
#   GREEN ARM           clean committed tree: frontier == pin, exit 0, and NONE of that prints.
#                       A refusal that prints on a green run is decoration, not a refusal.
#   REGISTER ARM        the forward erratum is in the register, the pin route survives there in
#                       words, P-103 is still defined exactly once, and the P-number checker --
#                       a HARD guard -- is PASS with 0 fatal on these bytes.
#
# THIS INSTRUMENT OBEYS P-103, WHICH IS THE PATTERN IT EXISTS TO REPAIR, and that is the point:
#   * NO repo-relative path is spelled as a quoted literal. The directory name is held in `S`
#     and every path is BUILT from it (P-103 remedy 1).
#   * EVERY location is a REQUIRED PARAMETER with no default; a value that does not resolve is a
#     HARD EXIT 2 -- never a skip, never a warning, never a pass (P-103 remedy 2).
#   * EVERY negative is CALIBRATED before it is reported (P-103 remedy 3).
#   * NO PIPELINES whose producer status could be discarded (P-57/P-81). Every read is over a
#     FILE.
#
# PARAMETERS (all required, all hard-exit on non-resolution):
#   T470_SRC    absolute path of the repository under test (the COMMITTED tree)
#   T470_OUT    absolute path of a directory to write transcripts into
#   T470_TMP    absolute path of a SCRATCH directory OUTSIDE the repository
#   T470_BASE   the PRE-REPAIR commit-ish, for the control arm (T470's fork point)
#
# EXIT: 0 every arm behaved as specified; 1 an arm did not; 2 this drive could not measure.
# PROBE LINE: `T470-PINROUTE-DRIVE:` -- printed only on a path that REACHES A VERDICT, never on
# exit 2. Read its PRESENCE before its value (P-84).
# =============================================================================================
set -u

PROBE="T470-PINROUTE-DRIVE:"
S=".softhouse"

die2() { printf 'ERROR: %s\n' "$*" >&2; printf 'ERROR: REFUSING (exit 2) -- not a finding.\n' >&2; exit 2; }

SRC="${T470_SRC:?T470_SRC is required: the repository under test. No default (P-103 remedy 2).}"
OUT="${T470_OUT:?T470_OUT is required: where transcripts are written. No default.}"
TMP="${T470_TMP:?T470_TMP is required: a scratch dir OUTSIDE the repo. No default.}"
BASE="${T470_BASE:?T470_BASE is required: the PRE-REPAIR commit-ish for the control arm.}"

[ -d "$SRC" ] || die2 "T470_SRC does not resolve to a directory: $SRC"
[ -d "$OUT" ] || die2 "T470_OUT does not resolve to a directory: $OUT"
[ -d "$TMP" ] || die2 "T470_TMP does not resolve to a directory: $TMP"

case "$TMP" in
  "$SRC"|"$SRC"/*) die2 "T470_TMP is INSIDE the repository. Scratch must live outside it." ;;
esac

GUARD_REL="$S/guards/check-dead-path-frontier.sh"
REGISTER_REL="$S/patterns.md"
CHECKER_REL="$S/capture/t282-pnumber-drift/bin/check-pnumber-citations.py"

GUARD="$SRC/$GUARD_REL"
REGISTER="$SRC/$REGISTER_REL"
CHECKER="$SRC/$CHECKER_REL"
for f in "$GUARD" "$REGISTER" "$CHECKER"; do
  [ -f "$f" ] || die2 "a path this drive DEPENDS ON does not resolve: $f"
done

command -v git     >/dev/null 2>&1 || die2 "git is not on PATH."
command -v python3 >/dev/null 2>&1 || die2 "python3 is not on PATH; the census cannot run."

BASE_SHA=$(git -C "$SRC" rev-parse --verify "$BASE^{commit}" 2>/dev/null)
[ -n "$BASE_SHA" ] || die2 "T470_BASE does not resolve to a commit in T470_SRC: $BASE"

# --- THE STRINGS, HELD ONCE ------------------------------------------------------------------
# MUST BE PRESENT in the repaired refusal:
OFFER="record why in the pin"                                   # pre-existing, unchanged since T316
ROUTE_HEAD="THE ROUTE THAT IS NOT A REPAIR, AND IS STILL SANCTIONED"
ROUTE_BODY="PIN THE ROW WITH ITS REASON"
HEADER_SENT="repaired or pinned with its reason"                # the guard header's own sentence
FORBIDDEN="THE FORBIDDEN FOURTH"                                # name preserved on purpose
# MUST BE ABSENT from the repaired refusal -- the two foreclosing clauses:
FORECLOSE_A="three, and never a fourth"
FORECLOSE_B="in exchange for not pinning the row"

echo "== T470 PIN-ROUTE DRIVE =="
echo "   git      : $(git --version)"
echo "   python3  : $(python3 -V 2>&1)"
echo "   SRC      : $SRC"
SRC_HEAD=$(git -C "$SRC" rev-parse HEAD 2>/dev/null)
[ -n "$SRC_HEAD" ] || die2 "could not read HEAD of T470_SRC. An unreadable sha is an ERROR, never a blank."
echo "   HEAD     : $SRC_HEAD"
echo "   BASE     : $BASE_SHA   (pre-repair control)"
echo "   guard    : $GUARD"
echo

# Fixed-string count over a FILE. Never a pipeline (P-57/P-81), never a blank.
cnt() {
  local n
  n=$(LC_ALL=C grep -c -F -- "$1" "$2" 2>/dev/null || true)
  [ -n "$n" ] || n=0
  printf '%s' "$n"
}

fail=0

# --- CALIBRATION 1: the PRESENT strings exist in the bytes under drive ------------------------
echo "-- CALIBRATION 1: the five MUST-BE-PRESENT strings, in the repaired guard's SOURCE"
cal=0
for needle in "$OFFER" "$ROUTE_HEAD" "$ROUTE_BODY" "$HEADER_SENT" "$FORBIDDEN"; do
  n=$(cnt "$needle" "$GUARD")
  echo "   source hits = $n   for: $needle"
  [ "$n" -ge 1 ] || cal=1
done
[ "$cal" -eq 0 ] || die2 "the repaired guard does not contain the text this drive grades."

echo "-- CALIBRATION 2: the two MUST-BE-ABSENT strings are gone from the repaired guard SOURCE"
for needle in "$FORECLOSE_A" "$FORECLOSE_B"; do
  n=$(cnt "$needle" "$GUARD")
  echo "   source hits = $n   for: $needle      (expected 0)"
  [ "$n" -eq 0 ] || { echo "   !! the foreclosing clause is STILL IN THE SOURCE"; fail=1; }
done
echo

# --- BUILD THE PLANTED CLONES ----------------------------------------------------------------
# Two clones of the SAME repository with the SAME planted specimen: one left at HEAD (repaired),
# one checked out at BASE (pre-repair). The only difference between the two transcripts is the
# repair, which is what makes every assertion below falsifiable.
PLANT_RELDIR="$S/capture/t470-red-drive-specimen"
PLANT_REL="$PLANT_RELDIR/planted-dead-literal.sh"

plant_into() { # plant_into <clone-dir> <tag>
  local clone="$1" tag="$2" dir tracked
  dir="$clone/$PLANT_RELDIR"
  mkdir -p "$dir" || die2 "could not create the plant directory in the $tag clone."
  {
    printf '#!/usr/bin/env bash\n'
    printf '# PLANTED BY T470 IN A THROWAWAY CLONE. Never committed to this program.\n'
    printf '# The quoted string below names a repo-relative path the repository does not contain.\n'
    printf 'SPECIMEN="%s/capture/t470-no-such-directory/no-such-file.txt"\n' "$S"
    printf 'echo "$SPECIMEN"\n'
  } >"$clone/$PLANT_REL" || die2 "could not write the planted specimen into the $tag clone."
  git -C "$clone" add -- "$PLANT_REL" >>"$OUT/09-plant.log" 2>&1 \
    || { cat "$OUT/09-plant.log"; die2 "could not stage the specimen in the $tag clone."; }
  git -C "$clone" -c user.email=t470@local -c user.name=T470 \
    commit -q -m "T470 red-drive plant ($tag, throwaway clone)" >>"$OUT/09-plant.log" 2>&1 \
    || { cat "$OUT/09-plant.log"; die2 "could not commit the specimen in the $tag clone."; }
  git -C "$clone" ls-files -- "$PLANT_REL" >"$TMP/tracked.$tag.txt" 2>/dev/null
  tracked=$(LC_ALL=C grep -ac '' "$TMP/tracked.$tag.txt" 2>/dev/null || true)
  [ -n "$tracked" ] || tracked=0
  echo "   [$tag] planted file tracked in clone = $tracked   (must be 1, or the arm measures nothing)"
  [ "$tracked" -eq 1 ] || die2 "the planted specimen is not tracked in the $tag clone. The arm did not run."
}

: >"$OUT/09-plant.log"
: >"$OUT/09-clone.log"

echo "== PRE-REPAIR CONTROL: the BASE guard, same plant =="
CTL="$TMP/base-clone"
rm -rf "$CTL"
git clone --local --quiet "$SRC" "$CTL" >>"$OUT/09-clone.log" 2>&1 \
  || { cat "$OUT/09-clone.log"; die2 "could not clone the repository into scratch (base)."; }
git -C "$CTL" checkout --quiet -B t470-base-plant "$BASE_SHA" >>"$OUT/09-clone.log" 2>&1 \
  || { cat "$OUT/09-clone.log"; die2 "could not check out T470_BASE in the control clone."; }
plant_into "$CTL" "base"

COUT="$OUT/10-CONTROL-pre-repair-refusal.txt"
bash "$CTL/$GUARD_REL" >"$COUT" 2>&1
crc=$?
cprobe=$(cnt "T316-DEADPATH-FRONTIER:" "$COUT")
echo "   exit           = $crc"
echo "   probe lines    = $cprobe      (PRESENCE read before VALUE)"
if [ "$cprobe" -lt 1 ]; then
  cat "$COUT"
  die2 "the BASE guard printed NO probe line. Instrument failure, not a finding."
fi
c_fa=$(cnt "$FORECLOSE_A" "$COUT"); c_fb=$(cnt "$FORECLOSE_B" "$COUT")
c_rh=$(cnt "$ROUTE_HEAD" "$COUT");  c_rb=$(cnt "$ROUTE_BODY" "$COUT")
c_of=$(cnt "$OFFER" "$COUT")
echo "   foreclosure A  = $c_fa      (expected >= 1 -- this is the defect, before repair)"
echo "   foreclosure B  = $c_fb      (expected >= 1)"
echo "   pin-route head = $c_rh      (expected 0 -- not written yet)"
echo "   pin-route body = $c_rb      (expected 0)"
echo "   'record why in the pin' = $c_of   (expected >= 1 -- it was ALWAYS there; that is the finding)"
[ "$crc" -eq 1 ] || { echo "   !! CONTROL: expected exit 1, got $crc"; fail=1; }
[ "$c_fa" -ge 1 ] || { echo "   !! CONTROL: foreclosing clause A absent from the PRE-REPAIR bytes -- this drive cannot see the defect it claims to repair"; fail=1; }
[ "$c_fb" -ge 1 ] || { echo "   !! CONTROL: foreclosing clause B absent from the PRE-REPAIR bytes"; fail=1; }
[ "$c_rh" -eq 0 ] || { echo "   !! CONTROL: the pin-route head is already in the BASE bytes; the arms are not distinct"; fail=1; }
[ "$c_rb" -eq 0 ] || { echo "   !! CONTROL: the pin-route body is already in the BASE bytes"; fail=1; }
[ "$c_of" -ge 1 ] || { echo "   !! CONTROL: the pre-existing pin OFFER is not in the BASE refusal -- T468's premise fails"; fail=1; }
echo "   [$COUT]"
echo

echo "== RED ARM: the REPAIRED guard, the same plant =="
RCL="$TMP/head-clone"
rm -rf "$RCL"
git clone --local --quiet "$SRC" "$RCL" >>"$OUT/09-clone.log" 2>&1 \
  || { cat "$OUT/09-clone.log"; die2 "could not clone the repository into scratch (head)."; }
plant_into "$RCL" "head"

ROUT="$OUT/20-RED-repaired-refusal.txt"
bash "$RCL/$GUARD_REL" >"$ROUT" 2>&1
rrc=$?
rprobe=$(cnt "T316-DEADPATH-FRONTIER:" "$ROUT")
echo "   exit           = $rrc"
echo "   probe lines    = $rprobe      (PRESENCE read before VALUE)"
if [ "$rprobe" -lt 1 ]; then
  cat "$ROUT"
  die2 "the repaired guard printed NO probe line on the red arm. Instrument failure, not a finding."
fi
LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$ROUT" >"$TMP/rv.txt" 2>/dev/null
rverdict=$(LC_ALL=C tail -1 "$TMP/rv.txt")
echo "   probe line     = $rverdict"
r_of=$(cnt "$OFFER" "$ROUT");        r_rh=$(cnt "$ROUTE_HEAD" "$ROUT")
r_rb=$(cnt "$ROUTE_BODY" "$ROUT");   r_hs=$(cnt "$HEADER_SENT" "$ROUT")
r_fb4=$(cnt "$FORBIDDEN" "$ROUT")
r_fa=$(cnt "$FORECLOSE_A" "$ROUT");  r_fb=$(cnt "$FORECLOSE_B" "$ROUT")
r_plant=$(cnt "t470-no-such-directory" "$ROUT")
echo "   'record why in the pin'        = $r_of    (expected >= 1)"
echo "   pin-route head                 = $r_rh    (expected >= 1)"
echo "   pin-route body                 = $r_rb    (expected >= 1)"
echo "   header sentence quoted back    = $r_hs    (expected >= 1)"
echo "   THE FORBIDDEN FOURTH preserved = $r_fb4   (expected >= 1)"
echo "   foreclosure A                  = $r_fa    (expected 0)"
echo "   foreclosure B                  = $r_fb    (expected 0)"
echo "   planted row named              = $r_plant (expected >= 1)"
[ "$rrc" -eq 1 ]   || { echo "   !! RED ARM: expected exit 1 (a real measured movement), got $rrc"; fail=1; }
[ "$r_of" -ge 1 ]  || { echo "   !! RED ARM: the refusal lost the pre-existing pin OFFER"; fail=1; }
[ "$r_rh" -ge 1 ]  || { echo "   !! RED ARM: the sanctioned non-repair route did NOT print"; fail=1; }
[ "$r_rb" -ge 1 ]  || { echo "   !! RED ARM: PIN THE ROW WITH ITS REASON did NOT print"; fail=1; }
[ "$r_hs" -ge 1 ]  || { echo "   !! RED ARM: the guard's own sanctioning sentence was not quoted back"; fail=1; }
[ "$r_fb4" -ge 1 ] || { echo "   !! RED ARM: THE FORBIDDEN FOURTH was lost -- the split/disguise evasion is no longer forbidden"; fail=1; }
[ "$r_fa" -eq 0 ]  || { echo "   !! RED ARM: foreclosing clause A STILL PRINTS"; fail=1; }
[ "$r_fb" -eq 0 ]  || { echo "   !! RED ARM: foreclosing clause B STILL PRINTS"; fail=1; }
[ "$r_plant" -ge 1 ] || { echo "   !! RED ARM: the refusal did not name the planted row; wrong cause"; fail=1; }
echo "   [$ROUT]"
echo

echo "== GREEN ARM: the committed tree, frontier == pin =="
GOUT="$OUT/30-GREEN-clean-tree.txt"
bash "$GUARD" >"$GOUT" 2>&1
grc=$?
gprobe=$(cnt "T316-DEADPATH-FRONTIER:" "$GOUT")
echo "   exit           = $grc"
echo "   probe lines    = $gprobe      (PRESENCE read before VALUE)"
if [ "$gprobe" -lt 1 ]; then
  cat "$GOUT"
  die2 "the guard printed NO probe line on the green arm. Instrument failure, not a finding."
fi
LC_ALL=C sed -n 's/^T316-DEADPATH-FRONTIER: //p' "$GOUT" >"$TMP/gv.txt" 2>/dev/null
gverdict=$(LC_ALL=C tail -1 "$TMP/gv.txt")
echo "   probe line     = $gverdict"
g_rh=$(cnt "$ROUTE_HEAD" "$GOUT"); g_rb=$(cnt "$ROUTE_BODY" "$GOUT"); g_of=$(cnt "$OFFER" "$GOUT")
echo "   pin-route head = $g_rh      (expected 0 -- calibrated PRESENT in source above)"
echo "   pin-route body = $g_rb      (expected 0)"
echo "   pin OFFER      = $g_of      (expected 0)"
[ "$grc" -eq 0 ]  || { echo "   !! GREEN ARM: expected exit 0, got $grc"; fail=1; }
[ "$g_rh" -eq 0 ] || { echo "   !! GREEN ARM: the pin-route block printed on a GREEN run"; fail=1; }
[ "$g_rb" -eq 0 ] || { echo "   !! GREEN ARM: the pin-route body printed on a GREEN run"; fail=1; }
[ "$g_of" -eq 0 ] || { echo "   !! GREEN ARM: the refusal's pin OFFER printed on a GREEN run"; fail=1; }
echo "   [$GOUT]"
echo

echo "== REGISTER ARM: the forward correction, and the HARD P-number guard on these bytes =="
ERRATUM_HEAD="ERRATUM TO"
ERRATUM_TAIL="corrected FORWARD, never edited in place"
e_h=$(cnt "$ERRATUM_HEAD" "$REGISTER")
e_t=$(cnt "$ERRATUM_TAIL" "$REGISTER")
e_r=$(cnt "$ROUTE_BODY" "$REGISTER")
e_f=$(cnt "$FORBIDDEN" "$REGISTER")
e_s=$(cnt "$HEADER_SENT" "$REGISTER")
echo "   'ERRATUM TO' in register       = $e_h    (expected >= 1)"
echo "   'corrected FORWARD...'         = $e_t    (expected >= 2 -- T334's and mine)"
echo "   pin route survives in register = $e_r    (expected >= 1)"
echo "   THE FORBIDDEN FOURTH preserved = $e_f    (expected >= 1)"
echo "   header sentence quoted back    = $e_s    (expected >= 1)"
[ "$e_h" -ge 1 ] || { echo "   !! REGISTER: no erratum heading in patterns.md"; fail=1; }
[ "$e_t" -ge 2 ] || { echo "   !! REGISTER: the forward-correction erratum is not in patterns.md"; fail=1; }
[ "$e_r" -ge 1 ] || { echo "   !! REGISTER: the pin route does not survive in the register"; fail=1; }
[ "$e_f" -ge 1 ] || { echo "   !! REGISTER: THE FORBIDDEN FOURTH was lost from the register"; fail=1; }
[ "$e_s" -ge 1 ] || { echo "   !! REGISTER: the guard's sanctioning sentence is not quoted in the register"; fail=1; }

# The register is corrected FORWARD: P-103 must still be DEFINED EXACTLY ONCE. A second
# definition line would be an in-file collision and would move the checker's cardinals.
PDEF="$TMP/p103-defs.txt"
LC_ALL=C grep -n -E '^(#{2,4}[[:space:]]+|([-*>][[:space:]]+)?\*\*)P-103[[:space:]]*[.-]' "$REGISTER" >"$PDEF" 2>/dev/null
ndef=$(LC_ALL=C grep -ac '' "$PDEF" 2>/dev/null || true); [ -n "$ndef" ] || ndef=0
echo "   P-103 definition lines         = $ndef    (expected exactly 1 -- forward, not in place)"
[ "$ndef" -eq 1 ] || { echo "   !! REGISTER: P-103 is defined $ndef time(s); a forward correction must not redefine it"; fail=1; }

CKOUT="$OUT/40-pnumber-checker.txt"
python3 "$CHECKER" >"$CKOUT" 2>&1
ckrc=$?
ck_pass=$(cnt "VERDICT PASS" "$CKOUT")
ck_fatal=$(cnt "0 fatal" "$CKOUT")
echo "   checker exit                   = $ckrc"
echo "   VERDICT PASS lines             = $ck_pass  (expected >= 1)"
echo "   '0 fatal' lines                = $ck_fatal (expected >= 1)"
[ "$ckrc" -eq 0 ]     || { echo "   !! REGISTER: the P-number checker did not exit 0"; fail=1; }
[ "$ck_pass" -ge 1 ]  || { echo "   !! REGISTER: the P-number checker did not print VERDICT PASS"; fail=1; }
[ "$ck_fatal" -ge 1 ] || { echo "   !! REGISTER: the P-number checker did not report 0 fatal"; fail=1; }
LC_ALL=C grep -F -- "PNUMBER-CITATIONS: register=" "$CKOUT"
LC_ALL=C grep -F -- "PNUMBER-CITATIONS: VERDICT" "$CKOUT"
echo "   [$CKOUT]"
echo

rm -rf "$CTL" "$RCL"

if [ "$fail" -eq 0 ]; then
  echo "$PROBE PASS control=exit$crc/fa$c_fa/route$c_rh red=exit$rrc/route$r_rh/offer$r_of/fa$r_fa green=exit$grc/route$g_rh register=erratum$e_t/defs$ndef"
  exit 0
fi
echo "$PROBE FAIL control=exit$crc/fa$c_fa/route$c_rh red=exit$rrc/route$r_rh/offer$r_of/fa$r_fa green=exit$grc/route$g_rh register=erratum$e_t/defs$ndef"
exit 1
