#!/usr/bin/env bash
# =============================================================================================
# T457 -- INDEPENDENT RE-DERIVATION OF T452'S TWO FAIL-OPEN MEMBERS.
#
# T452 published a fail-OPEN count of 2 where T442 published 0 and T447 left it "not
# established". This drive re-derives BOTH members from scratch. The carrier set is measured
# with a primitive T452 did not use -- plain `grep -lF` over the file list, never `git grep` --
# because two derivations that share a primitive do not corroborate each other.
#
# WHAT IT DRIVES, and why each arm exists:
#
#   A3  the t388 probe's carrier set, over the corpus the subject's own pathspec names.
#   A1  the t388 casualty sweep, AS SHIPPED, in a scratch git repo containing NOTHING BUT THE
#       SCRIPT. If the P-72 positive calibration is self-satisfying, this run goes GREEN over a
#       corpus of one file. T452 asserted that outcome from a carrier count and never built the
#       specimen; P-22 says a guard you have not seen FAIL is not a guard, and a fail-open you
#       have not seen fail OPEN is in the same position. THIS ARM IS THAT SPECIMEN.
#   A2  the same script RELOCATED out of the corpus its own pathspec names. If the guard were
#       unfireable it would stay green. It does not -- it exits 3. So the finding is the same
#       NARROW shape T452 correctly assigned to a2-33, and the word "strictly vacuous" that
#       T452 used for this member and expressly disowned for the other one is too strong.
#   B1  the a2-33 sweep AS IT STOOD BEFORE THE REPAIR, same one-file specimen -> must go GREEN.
#   B2  the REPAIRED a2-33 sweep on that same specimen -> must ABORT at 94.
#   B3  the 34 `run` pattern rows before vs after -> byte-identical, WITH A MUTATION CONTROL and
#       a floor on the extraction, because a byte-compare of two EMPTY extractions also reports
#       "identical". T457's own first cut of this arm did exactly that and printed a green it
#       had not measured; the refusal below is why that cannot happen twice.
#   C   WINDOW SENSITIVITY. T452's direction/enforcement reader looks at a FIXED EIGHT LINES
#       after the search. This arm re-runs T452's own classifier with that window widened and
#       reports what moves. A cardinal that moves under a tuned parameter is a fact about the
#       parameter; the MEMBER buckets, which do not move, are the thing to quote.
#
# NO PATH UNDER THE PROGRAM'S INSTRUMENT TREE IS SPELLED AS A LITERAL STRING HERE. Every one is
# assembled from `$S`, and every scratch and relocated destination is built at run time -- the
# dead-path frontier guard has caught six workers this fire on exactly that reflex.
#
# BOTH INPUTS ARE REQUIRED PARAMETERS, never defaults: a subject tree or a ref that stops
# resolving must be a hard exit, never a silently skipped arm.
#
# EXIT 0 = every arm came out as declared. 1 = a disagreement. 2 = could not measure (NOT a pass).
# =============================================================================================
set -uo pipefail

S='.softhouse'

usage() {
  echo "usage: t457-failopen-redrive.sh <subject-tree> <pre-repair-ref>" >&2
  echo "  <subject-tree>   a git work tree carrying T452's work (the branch tip or the merge)" >&2
  echo "  <pre-repair-ref> a commit in that tree's repository from BEFORE the a2-33 repair," >&2
  echo "                   e.g.  git merge-base main softhouse/T452-t447-conditions" >&2
}
TREE="${1:-}"; BASE_REF="${2:-}"
[ -n "$TREE" ] && [ -n "$BASE_REF" ] || { echo "REFUSED (exit 2): both arguments are required." >&2; usage; exit 2; }
TREE=$(cd "$TREE" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || TREE=""
[ -n "$TREE" ] || { echo "REFUSED (exit 2): argument 1 is not inside a git work tree." >&2; usage; exit 2; }
git -C "$TREE" rev-parse --verify "$BASE_REF^{commit}" >/dev/null 2>&1 || {
  echo "REFUSED (exit 2): '$BASE_REF' does not resolve to a commit in $TREE." >&2; exit 2; }

T388_DIR="$S/capture/t388-accrual-capture"
T388_REL="$T388_DIR/30-casualty-sweep-t388.sh"
A233_REL="$S/reviews/a2-33-dec2-rev5/sweep.sh"
CLASSIFIER="$S/capture/t452-t447-conditions/instruments/t452-classify-v2.py"
for f in "$T388_REL" "$A233_REL" "$CLASSIFIER"; do
  [ -r "$TREE/$f" ] || { echo "REFUSED (exit 2): cannot read $f under $TREE" >&2; exit 2; }
done

W=$(mktemp -d "${TMPDIR:-/tmp}/t457-redrive.XXXXXXXX") || exit 2
case "$W" in "$TREE"/*) echo "REFUSED (exit 2): scratch $W is inside the subject tree" >&2; exit 2 ;; esac
trap 'rm -rf "$W"' EXIT

export GIT_AUTHOR_NAME=t457 GIT_AUTHOR_EMAIL=t457@local
export GIT_COMMITTER_NAME=t457 GIT_COMMITTER_EMAIL=t457@local

FAILED=0
check() {
  printf '  %-58s expected=%-9s actual=%-9s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

mkspec() {  # mkspec <dest> <rel-path-inside> <source-file> -- a git repo holding exactly one file
  local dest="$1" rel="$2" src="$3" n
  case "$dest" in "$TREE"/*) echo "REFUSED (exit 2): specimen inside the subject tree" >&2; exit 2 ;; esac
  rm -rf "$dest"; mkdir -p "$dest/$(dirname "$rel")"
  cp "$src" "$dest/$rel" || exit 2
  git -C "$dest" init -q || exit 2
  git -C "$dest" add -A || exit 2
  git -C "$dest" commit -qm specimen || exit 2
  n=$(git -C "$dest" ls-files | grep -c '')
  [ "$n" -eq 1 ] || { echo "REFUSED (exit 2): specimen tracks $n file(s), expected 1" >&2; exit 2; }
}

echo "=============================================================================="
echo "T457 FAIL-OPEN RE-DRIVE"
echo "subject tree : $TREE"
echo "commit       : $(git -C "$TREE" rev-parse HEAD)"
echo "dirty        : $(git -C "$TREE" status --porcelain | grep -c '' | tr -d ' ') path(s)"
echo "pre-repair   : $BASE_REF -> $(git -C "$TREE" rev-parse --short "$BASE_REF^{commit}")"
echo "scratch      : $W   (asserted outside the subject tree)"
echo "=============================================================================="
echo

# ------------------------------------------------------------------------------------ ARM A3
echo "ARM A3 -- the t388 probe's carrier set, measured with plain grep (NOT git grep)"
POS=$(LC_ALL=C sed -n "s/^CALIB_POS_STR='\(.*\)'\$/\1/p" "$TREE/$T388_REL" | head -1)
PTH=$(LC_ALL=C sed -n "s/^CALIB_POS_PATH='\(.*\)'\$/\1/p" "$TREE/$T388_REL" | head -1)
[ -n "$POS" ] && [ -n "$PTH" ] || {
  echo "REFUSED (exit 2): could not read CALIB_POS_STR/CALIB_POS_PATH out of the subject." >&2
  echo "  The subject has been edited; this drive would be grading something else." >&2; exit 2; }
echo "   probe  (read from the subject, never retyped) : '$POS'"
echo "   corpus (read from the subject)                : '$PTH'"
git -C "$TREE" ls-files -- "$PTH" >"$W/corpus.lst"
corpus_files=$(grep -c '' "$W/corpus.lst")
[ "$corpus_files" -gt 0 ] || { echo "REFUSED (exit 2): the calibration corpus lists 0 tracked files" >&2; exit 2; }
: >"$W/carriers.lst"
while IFS= read -r rel; do
  LC_ALL=C grep -qF "$POS" "$TREE/$rel" 2>/dev/null && printf '%s\n' "$rel" >>"$W/carriers.lst"
done <"$W/corpus.lst"
carriers=$(grep -c '' "$W/carriers.lst")
self=$(grep -c -x -F "$T388_REL" "$W/carriers.lst")
echo "   tracked files in the calibration corpus       : $corpus_files"
echo "   files carrying the probe IN that corpus       : $carriers"
sed 's/^/       /' "$W/carriers.lst"
echo "   of those, the searcher itself                 : $self"
ctrl=0
while IFS= read -r rel; do
  LC_ALL=C grep -qF 'SWEEP CALIBRATE' "$TREE/$rel" 2>/dev/null && ctrl=$((ctrl+1))
done < <(git -C "$TREE" ls-files -- "$S")
echo "   CONTROL: files carrying 'SWEEP CALIBRATE'     : $ctrl"
check "corpus is far larger than one file"          "yes" "$( [ "$corpus_files" -gt 100 ] && echo yes || echo no )"
check "exactly ONE carrier in the corpus"           "1"   "$carriers"
check "and that carrier is the searcher"            "1"   "$self"
check "CONTROL string is NOT self-only"             "yes" "$( [ "$ctrl" -gt 1 ] && echo yes || echo no )"
echo

# ------------------------------------------------------------------------------------ ARM A1
echo "ARM A1 -- t388 sweep AS SHIPPED, in a repo containing NOTHING but the script"
mkspec "$W/a1" "$T388_REL" "$TREE/$T388_REL"
( cd "$W/a1" && bash "$T388_REL" ) >"$W/a1.txt" 2>&1
a1_rc=$?
a1_cal=$(LC_ALL=C grep -c 'SWEEP CALIBRATE+: PASS' "$W/a1.txt")
echo "   exit                              : $a1_rc"
echo "   population reported by the sweep  : $(LC_ALL=C sed -n 's/^population: //p' "$W/a1.txt" | head -1)"
LC_ALL=C grep -m1 'SWEEP CALIBRATE+' "$W/a1.txt" | sed 's/^/       /'
LC_ALL=C grep -m1 '^selectors run:' "$W/a1.txt" | sed 's/^/       /'
check "the sweep runs GREEN over a corpus of one"    "0"  "$a1_rc"
check "and the positive calibration PASSES"          "1"  "$a1_cal"
echo

# ------------------------------------------------------------------------------------ ARM A2
echo "ARM A2 -- the same script RELOCATED out of the corpus its own pathspec names"
ALT_REL="$(dirname "$T388_DIR")/t457-relocated-$$/30-casualty-sweep-t388.sh"
case "$ALT_REL" in "$T388_DIR"/*) echo "REFUSED (exit 2): relocation stayed inside the corpus" >&2; exit 2 ;; esac
echo "   relocated to (assembled at run time) : $ALT_REL"
mkspec "$W/a2" "$ALT_REL" "$TREE/$T388_REL"
( cd "$W/a2" && bash "$ALT_REL" ) >"$W/a2.txt" 2>&1
a2_rc=$?
echo "   exit                              : $a2_rc"
LC_ALL=C grep -m1 'CALIBRATION MISSED' "$W/a2.txt" | cut -c1-100 | sed 's/^/       /'
check "the guard IS fireable, so not unfireable"     "3"  "$a2_rc"
echo

# --------------------------------------------------------------------------------- ARM B1/B2
echo "ARM B1/B2 -- the a2-33 sweep, PRE-REPAIR vs REPAIRED, on one and the same specimen"
git -C "$TREE" show "$BASE_REF:$A233_REL" >"$W/sweep-pre.sh" 2>/dev/null || {
  echo "REFUSED (exit 2): $A233_REL does not exist at $BASE_REF" >&2; exit 2; }
[ -s "$W/sweep-pre.sh" ] || { echo "REFUSED (exit 2): the pre-repair sweep came out empty" >&2; exit 2; }
if cmp -s "$W/sweep-pre.sh" "$TREE/$A233_REL"; then
  echo "REFUSED (exit 2): pre-repair and repaired sweeps are byte-identical at $BASE_REF." >&2
  echo "  There is no repair to grade, so this drive would report a green it did not measure." >&2
  exit 2
fi
mkspec "$W/b1" "$A233_REL" "$W/sweep-pre.sh"
( cd "$W/b1" && bash "$A233_REL" ) >"$W/b1.txt" 2>&1
b1_rc=$?
b1_pat=$(LC_ALL=C grep -c '^########## PATTERN ' "$W/b1.txt")
echo "   B1 pre-repair : exit=$b1_rc  patterns=$b1_pat"
LC_ALL=C grep -m1 '^SWEEP CORPUS' "$W/b1.txt" | sed 's/^/       /'
LC_ALL=C grep -m1 '^SWEEP CALIBRATE+' "$W/b1.txt" | sed 's/^/       /'
LC_ALL=C grep -m1 'SWEEP-RESULT' "$W/b1.txt" | cut -c1-110 | sed 's/^/       /'
mkspec "$W/b2" "$A233_REL" "$TREE/$A233_REL"
( cd "$W/b2" && bash "$A233_REL" ) >"$W/b2.txt" 2>&1
b2_rc=$?
echo "   B2 repaired   : exit=$b2_rc"
LC_ALL=C grep -m1 'CORPUS REACH FAILED' "$W/b2.txt" | cut -c1-100 | sed 's/^/       /'
check "PRE-REPAIR sweep certifies a one-file corpus" "0"  "$b1_rc"
check "and reports all 34 patterns while doing it"   "34" "$b1_pat"
check "REPAIRED sweep REFUSES the same specimen"     "94" "$b2_rc"
echo

# ------------------------------------------------------------------------------------ ARM B3
echo "ARM B3 -- the 34 pattern rows, pre-repair vs repaired, with a MUTATION CONTROL"
LC_ALL=C grep '^run ' "$W/sweep-pre.sh"  >"$W/pat-pre.txt"
LC_ALL=C grep '^run ' "$TREE/$A233_REL"  >"$W/pat-post.txt"
n_pre=$(grep -c '' "$W/pat-pre.txt"); n_post=$(grep -c '' "$W/pat-post.txt")
echo "   pattern rows extracted: pre=$n_pre  post=$n_post"
if [ "$n_pre" -lt 2 ] || [ "$n_post" -lt 2 ]; then
  echo "REFUSED (exit 2): the pattern extractor selected fewer than two rows on one side." >&2
  echo "  A byte-compare of two EMPTY extractions reports 'identical'. That is the fail-open" >&2
  echo "  this refusal exists for, and T457's own first cut of this arm printed exactly it." >&2
  exit 2
fi
same=$( if cmp -s "$W/pat-pre.txt" "$W/pat-post.txt"; then echo yes; else echo no; fi )
LC_ALL=C sed '1s/./X/' "$W/pat-pre.txt" >"$W/pat-mut.txt"
mut=$( if cmp -s "$W/pat-mut.txt" "$W/pat-post.txt"; then echo yes; else echo no; fi )
check "pattern rows are byte-identical"              "yes"    "$same"
check "and the two extractions agree in count"       "$n_pre" "$n_post"
check "CONTROL: a one-byte mutation IS detected"     "no"     "$mut"
echo

# ------------------------------------------------------------------------------------- ARM C
echo "ARM C -- is T452's fail-open cardinal stable under its own 8-line window?"
( cd "$TREE" && python3 "$CLASSIFIER" ) >"$W/c8.txt" 2>&1 || true
line8=$(LC_ALL=C grep -m1 '^T452-CLASSIFY-V2-RESULT:' "$W/c8.txt")
[ -n "$line8" ] || { echo "REFUSED (exit 2): the classifier printed no RESULT line" >&2; exit 2; }
sed 's/lines\[i:i + 8\]/lines[i:i + 24]/' "$TREE/$CLASSIFIER" >"$W/classify-w24.py"
if cmp -s "$TREE/$CLASSIFIER" "$W/classify-w24.py"; then
  echo "REFUSED (exit 2): the window selector matched nothing -- it has gone stale, and this" >&2
  echo "  arm would compare a file with itself and report a stability it did not measure." >&2
  exit 2
fi
( cd "$TREE" && python3 "$W/classify-w24.py" ) >"$W/c24.txt" 2>&1 || true
line24=$(LC_ALL=C grep -m1 '^T452-CLASSIFY-V2-RESULT:' "$W/c24.txt")
[ -n "$line24" ] || { echo "REFUSED (exit 2): the widened classifier printed no RESULT line" >&2; exit 2; }
res8=$(LC_ALL=C sed -n 's/.*\(fail_open=[0-9]*\).*/\1/p'  <<<"$line8")
res24=$(LC_ALL=C sed -n 's/.*\(fail_open=[0-9]*\).*/\1/p' <<<"$line24")
mem8=$(LC_ALL=C  sed -n 's/.*\(self_only=[0-9]*\) .*\(family_only=[0-9]*\).*/\1 \2/p' <<<"$line8")
mem24=$(LC_ALL=C sed -n 's/.*\(self_only=[0-9]*\) .*\(family_only=[0-9]*\).*/\1 \2/p' <<<"$line24")
echo "   window  8 : $res8   membership: $mem8"
echo "   window 24 : $res24   membership: $mem24"
echo "   full  w8  : $line8"
echo "   full  w24 : $line24"
check "the MEMBER buckets are window-INSENSITIVE"    "$mem8" "$mem24"
check "the mechanical fail_open CARDINAL is not"     "no"    "$( [ "$res8" = "$res24" ] && echo yes || echo no )"
echo

echo "=============================================================================="
echo "T457-REDRIVE-RESULT: t388_specimen_exit=$a1_rc t388_relocated_exit=$a2_rc t388_carriers=$carriers t388_self=$self t388_corpus=$corpus_files"
echo "T457-REDRIVE-RESULT: a2_33_pre_exit=$b1_rc a2_33_post_exit=$b2_rc patterns=$n_pre identical=$same"
echo "T457-REDRIVE-RESULT: $res8 (w8) $res24 (w24) members_w8='$mem8' members_w24='$mem24' disagreements=$FAILED"
echo "=============================================================================="
[ "$FAILED" -eq 0 ] || exit 1
exit 0
