#!/usr/bin/env bash
# =============================================================================================
# T452 -- F-T447-1.  IS `.softhouse/reviews/a2-33-dec2-rev5/sweep.sh:61` A REAL FAIL-OPEN?
# DRIVEN BOTH WAYS, and the answer is written down with the drive that produced it.
#
# THE ROW.  An ENFORCED (`exit 92`) P-72 PRESENT-assertion whose pattern is held in `$CAL_RE`,
# so T442's class census parsed it into the RUNTIME bucket and counted it safe on syntax alone.
# Its corpus is the searcher's OWN task directory; the sweep it certifies reads the whole tree.
# T447 hypothesised it was VACUOUS (satisfied by the searcher plus one sibling), drove it, and
# HAD ITS HYPOTHESIS FALSIFIED -- ten siblings carry the token independently. It kept that run
# and left the row: not falsified, NOT ESTABLISHED. This drive settles it.
#
# THE TWO DIRECTIONS, BOTH RUN:
#   FOR fail-open  (arm B) : a corpus can be degraded to ONE FILE -- this script -- and the
#                            calibration still certifies every negative. Exit 0, calibration=PASS.
#   AGAINST        (arm C) : the guard is NOT unfireable. Move the task directory and it exits
#                            92. It is a real guard; it is simply calibrated on the wrong corpus.
# VERDICT: **a real fail-open, narrowly, on the CORPUS-REACH limb** -- the exact limb the T238
# repair was written for. The engine and pattern-language limbs are sound and are kept.
#
# THE REPAIR IS DRIVEN TOO (P-22 -- a guard you have not seen FAIL is not a guard):
#   arm D : the repaired script on arm B's specimen must now ABORT 94.
#   arm E : the repaired script on the real tree must still exit 0 with both limbs PASS.
#   arm F : all 34 `run` patterns must be BYTE-IDENTICAL before and after.
#   arm G : arm B's specimen against the AS-SHIPPED copy proves the RED is not an artefact of
#           the specimen builder -- it is the same specimen, and only the script differs.
#
# THE BEFORE IMAGE IS PINNED BY CONTENT, NOT BY REF.  `F-T442-1` is the standing lesson: a drive
# whose BEFORE is `main` returns a different verdict on every tree. The as-shipped copy lives at
# evidence/sweep-AS-SHIPPED-19fcde77.sh and this drive REFUSES unless its sha256 matches.
#
# EXIT 0 = every arm as declared. EXIT 1 = a disagreement. EXIT 2 = could not measure.
# All scratch under $TMPDIR, OUTSIDE the repository; refuses otherwise.
# =============================================================================================
set -uo pipefail
REPO=${T452_REPO:-$(git rev-parse --show-toplevel 2>/dev/null)} || REPO=""
[ -n "$REPO" ] || { echo "REFUSED: not inside a git work tree" >&2; exit 2; }
cd "$REPO" || { echo "REFUSED: cannot cd $REPO" >&2; exit 2; }

SELF_DIR='.softhouse/reviews/a2-33-dec2-rev5'
LIVE="$SELF_DIR/sweep.sh"
SHIPPED=".softhouse/capture/t452-t447-conditions/evidence/sweep-AS-SHIPPED-19fcde77.sh"
SHIPPED_SHA='57a611fde83188ebfced6cb9471e1025462d4fbfe6b65fb6435596c5435b1d4a'
for f in "$LIVE" "$SHIPPED"; do
  [ -r "$f" ] || { echo "REFUSED: cannot read $f" >&2; exit 2; }
done
got_sha=$(shasum -a 256 "$SHIPPED" | awk '{print $1}')
if [ "$got_sha" != "$SHIPPED_SHA" ]; then
  echo "REFUSED: the pinned AS-SHIPPED image does not match its sha256." >&2
  echo "         want $SHIPPED_SHA" >&2
  echo "         got  $got_sha" >&2
  echo "         A BEFORE image that is not the image the finding was measured on makes every" >&2
  echo "         arm below uninterpretable (F-T442-1)." >&2
  exit 2
fi

W=$(mktemp -d "${TMPDIR:-/tmp}/t452-a233.XXXXXXXX") || exit 2
case "$W" in "$REPO"/*) echo "REFUSED: scratch inside the repo" >&2; exit 2 ;; esac
trap 'rm -rf "$W"' EXIT

FAILED=0
check() {
  printf '  %-58s expected=%-10s actual=%-10s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

# build a scratch git repo holding ONE file at a chosen path
# mkspec <dir> <script-source> <path-inside-repo>
mkspec() {
  local d="$1" src="$2" p="$3"
  mkdir -p "$d/$(dirname "$p")" || return 2
  cp "$src" "$d/$p" || return 2
  ( cd "$d" \
    && git init -q . \
    && git -c user.email=t452@local -c user.name=T452 add "$p" \
    && git -c user.email=t452@local -c user.name=T452 commit -q -m spec ) >/dev/null 2>&1
}

echo "=============================================================================="
echo "T452 A2-33 CALIBRATION FAIL-OPEN DRIVE   [F-T447-1]"
echo "repo    : $REPO"
echo "commit  : $(git rev-parse HEAD)"
echo "dirty   : $(git status --porcelain | grep -c '' | tr -d ' ') path(s)"
echo "live    : $LIVE            sha256 $(shasum -a 256 "$LIVE" | cut -c1-16)"
echo "shipped : $SHIPPED  sha256 ${SHIPPED_SHA:0:16}  (PINNED BY CONTENT)"
echo "=============================================================================="
echo

# --------------------------------------------------------------------------------- ARM A
echo "ARM A -- the row measured on the LIVE TREE, with the ROW'S OWN FLAGS (-c -I -i -E),"
echo "         not with the census's -l -F.  [that substitution is F-T447-5]"
cal_hits=$(git grep -c -I -i -E 'a2-33' -- "$SELF_DIR" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
cal_files=$(git grep -l -I -i -E 'a2-33' -- "$SELF_DIR" 2>/dev/null | grep -c '')
# outside, WITHIN THE ROW'S OWN CORPUS: 0 BY CONSTRUCTION, because the pathspec confines it.
row_out=$(git grep -l -I -i -E 'a2-33' -- "$SELF_DIR" 2>/dev/null | grep -vc "^$SELF_DIR/")
# outside, over the SWEEP'S corpus: what the row would have found had it looked where the sweep looks
tree_out=$(git grep -l -I -i -E 'a2-33' -- . ":(exclude)$SELF_DIR" 2>/dev/null | grep -c '')
self_hits=$(git grep -c -I -i -E 'a2-33' -- "$LIVE" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
census_files=$(git grep -l -F -e 'a2-33' -- "$SELF_DIR" 2>/dev/null | grep -c '')
cal_corpus=$(git ls-files -- "$SELF_DIR" | grep -c '')
sweep_corpus=$(git ls-files | grep -c '')
echo "   calibration matches (row's own flags)       : $cal_hits in $cal_files file(s)"
echo "   of those, files OUTSIDE the task dir        : $row_out   <-- FAMILY-ONLY, BY CONSTRUCTION"
echo "                                                  (the pathspec confines it; the corpus"
echo "                                                   cannot make it otherwise)"
echo "   files carrying the token in the SWEEP's     : $tree_out   <-- the row never looks here"
echo "     corpus but outside the task dir"
echo "   matches in the SEARCHER ALONE               : $self_hits   <-- would satisfy it by itself"
echo "   files the CENSUS reports for this row (-l -F): $census_files   <-- vs the row's own $cal_files [F-T447-5]"
echo "   calibration corpus / sweep corpus           : $cal_corpus / $sweep_corpus tracked files"
check "the row's own result set is FAMILY-ONLY"         "0"   "$row_out"
check "the searcher alone would satisfy it"             "yes" "$( [ "$self_hits" -ge 1 ] && echo yes || echo no )"
check "the calibration corpus is a STRICT SUBSET"       "yes" "$( [ "$cal_corpus" -lt "$sweep_corpus" ] && echo yes || echo no )"
check "T447 was right that it is NOT vacuous today"     "yes" "$( [ "$cal_files" -gt 1 ] && echo yes || echo no )"
check "the census's -l -F set differs from the row's"   "yes" "$( [ "$census_files" -ne "$cal_files" ] && echo yes || echo no )"
check "the token DOES exist outside the family"         "yes" "$( [ "$tree_out" -ge 1 ] && echo yes || echo no )"
echo

# --------------------------------------------------------------------------------- ARM B
echo "ARM B -- FOR the fail-open. A corpus of ONE FILE: the searcher itself. AS-SHIPPED script."
mkspec "$W/b" "$SHIPPED" "$LIVE" || { echo "REFUSED: could not build specimen B" >&2; exit 2; }
( cd "$W/b" && bash "$LIVE" REPO ) > "$W/b.out" 2>&1; b_rc=$?
b_corpus=$(sed -n 's/^SWEEP CORPUS *: *\([0-9]*\).*/\1/p' "$W/b.out" | head -1)
b_cal=$(grep -c '^SWEEP CALIBRATE+: PASS' "$W/b.out")
b_zero=$(grep -c 'MEASURED ZERO' "$W/b.out")
b_res=$(grep -F 'SWEEP-RESULT:' "$W/b.out" | tail -1)
echo "   exit                       : $b_rc"
echo "   SWEEP CORPUS               : ${b_corpus:-<none>} tracked file(s)"
echo "   positive calibration PASSed: $b_cal"
echo "   'MEASURED ZERO' lines       : $b_zero of 34 patterns"
echo "   $b_res"
check "B: as-shipped EXITS 0 over a 1-file corpus"      "0"  "$b_rc"
check "B: corpus really is one file"                    "1"  "${b_corpus:-x}"
check "B: the calibration CERTIFIED that run"           "1"  "$b_cal"
echo "   >>> THE FINDING: the P-72 calibration passes, and certifies 34 negatives, on a corpus"
echo "       consisting of the searcher and nothing else. Same reader-facing outcome as the"
echo "       deleted-worktree defect the T238 block was written to remove."
echo

# --------------------------------------------------------------------------------- ARM C
echo "ARM C -- AGAINST. The guard is NOT unfireable: move the task directory and it aborts 92."
mkspec "$W/c" "$SHIPPED" ".softhouse/reviews/RENAMED-dec2-rev5/sweep.sh" \
  || { echo "REFUSED: could not build specimen C" >&2; exit 2; }
( cd "$W/c" && bash ".softhouse/reviews/RENAMED-dec2-rev5/sweep.sh" REPO ) > "$W/c.out" 2>&1; c_rc=$?
c_92=$(grep -c 'SWEEP ABORT (92)' "$W/c.out")
echo "   exit $c_rc ; 'SWEEP ABORT (92)' lines: $c_92"
check "C: the calibration CAN fire"                     "92" "$c_rc"
check "C: and says so"                                  "1"  "$c_92"
echo "   >>> So the row is a real guard on a real property -- the reachability of 17 files."
echo "       It was never a guard on the reachability of the ~9.7k the sweep reads."
echo

# --------------------------------------------------------------------------------- ARM D
echo "ARM D -- THE REPAIR, on the SAME specimen as arm B. Only the script differs."
mkspec "$W/d" "$LIVE" "$LIVE" || { echo "REFUSED: could not build specimen D" >&2; exit 2; }
( cd "$W/d" && bash "$LIVE" REPO ) > "$W/d.out" 2>&1; d_rc=$?
d_94=$(grep -c 'SWEEP ABORT (94)' "$W/d.out")
d_cal=$(grep -c '^SWEEP CALIBRATE+: PASS' "$W/d.out")
echo "   exit $d_rc ; 'SWEEP ABORT (94)' lines: $d_94 ; old positive limb still passed: $d_cal"
sed -n '/SWEEP ABORT (94)/,$p' "$W/d.out" | sed 's/^/       /'
check "D: the repaired script REFUSES the specimen"     "94" "$d_rc"
check "D: with the reach message"                       "1"  "$d_94"
check "D: and the OLD limb still passed on it"          "1"  "$d_cal"
echo "   >>> The old limb passing while the new one refuses is the whole finding, mechanised:"
echo "       the two limbs measure different properties and only one of them was being checked."
echo

# --------------------------------------------------------------------------------- ARM E
echo "ARM E -- the repaired script on the REAL tree must still measure, not refuse."
( bash "$LIVE" REPO ) > "$W/e.out" 2>&1; e_rc=$?
e_reach=$(grep -c '^SWEEP CALIBRATE+R: PASS' "$W/e.out")
e_cal=$(grep -c '^SWEEP CALIBRATE+: PASS' "$W/e.out")
e_neg=$(grep -c '^SWEEP CALIBRATE-: PASS' "$W/e.out")
e_pat=$(grep -c '^########## PATTERN ' "$W/e.out")
e_res=$(grep -F 'SWEEP-RESULT:' "$W/e.out" | tail -1)
echo "   exit $e_rc ; patterns run $e_pat ; limbs: pos=$e_cal neg=$e_neg reach=$e_reach"
echo "   $e_res"
check "E: real tree exits 0"                            "0"  "$e_rc"
check "E: positive limb PASS"                           "1"  "$e_cal"
check "E: anti-calibration PASS"                        "1"  "$e_neg"
check "E: NEW reach limb PASS"                          "1"  "$e_reach"
check "E: all 34 patterns ran"                          "34" "$e_pat"
echo

# --------------------------------------------------------------------------------- ARM F
echo "ARM F -- the 34 patterns must be BYTE-IDENTICAL before and after the repair."
grep -n '^run ' "$SHIPPED" | sed 's/^[0-9]*://' > "$W/pat.before"
grep -n '^run ' "$LIVE"    | sed 's/^[0-9]*://' > "$W/pat.after"
nb=$(grep -c '' "$W/pat.before"); na=$(grep -c '' "$W/pat.after")
if diff -q "$W/pat.before" "$W/pat.after" >/dev/null 2>&1; then f_same=same; else f_same=DIFFERENT; fi
echo "   run-lines before/after: $nb / $na ; byte comparison: $f_same"
[ "$f_same" = same ] || diff -u "$W/pat.before" "$W/pat.after" | sed -n '3,30p' | sed 's/^/       /'
check "F: 34 patterns before"                           "34" "$nb"
check "F: 34 patterns after"                            "34" "$na"
check "F: patterns unchanged by the repair"             "same" "$f_same"
echo

# --------------------------------------------------------------------------------- ARM G
echo "ARM G -- the specimen builder is not the cause: same builder, both scripts."
echo "   B (as-shipped) exit $b_rc     D (repaired) exit $d_rc     on identical one-file corpora"
check "G: the two arms disagree, and only the script changed" "yes" \
  "$( [ "$b_rc" -ne "$d_rc" ] && echo yes || echo no )"
echo

# --------------------------------------------------------------------------------- ARM H
echo "ARM H -- ANTI-EVASION. The repair must not hide the repaired row from the instrument"
echo "         that found it. The repair hoists the task directory into SELF_DIR=, which makes"
echo "         the pathspec variable-indirect -- the SAME blind spot, one operand to the right."
CL=".softhouse/capture/t452-t447-conditions/instruments/t452-classify-v2.py"
[ -r "$CL" ] || { echo "REFUSED: cannot read $CL" >&2; exit 2; }
T452_ONLY="a2-33-dec2-rev5/sweep.sh" python3 "$CL" > "$W/h.out" 2>&1; h_rc=$?
h_row=$(grep -c "a2-33-dec2-rev5/sweep.sh.*probe 'a2-33'" "$W/h.out")
# the FAMILY-ONLY listing is the only one that prints "N file(s)  direction=" beside the row
h_fam=$(grep -c "a2-33-dec2-rev5/sweep.sh.*probe 'a2-33'.*file(s)  direction=" "$W/h.out")
grep -E "^FAMILY-ONLY rows|probe 'a2-33'" "$W/h.out" | sed 's/^/       /'
echo "   classifier exit $h_rc"
check "H: the repaired row is STILL VISIBLE to the classifier" "yes" \
  "$( [ "$h_row" -ge 1 ] && echo yes || echo no )"
check "H: and is still flagged FAMILY-ONLY"                    "yes" \
  "$( [ "$h_fam" -ge 1 ] && echo yes || echo no )"
# and the refusal arm of T452_ONLY itself, so this check cannot pass by selecting nothing
T452_ONLY="zzq-t452-no-such-script" python3 "$CL" > "$W/h2.out" 2>&1; h2_rc=$?
echo "   T452_ONLY selecting nothing -> exit $h2_rc"
check "H: an empty selection REFUSES, never reads clean"      "2" "$h2_rc"
echo

echo "=============================================================================="
echo "T452-A2-33-FAILOPEN-RESULT: verdict=REAL_FAIL_OPEN limb=corpus-reach family_only=1"
echo "  as_shipped_on_1_file_corpus=exit${b_rc}  repaired_on_same=exit${d_rc}  repaired_on_tree=exit${e_rc}"
echo "  disagreements=$FAILED"
echo "=============================================================================="
[ "$FAILED" -eq 0 ] || exit 1
exit 0
